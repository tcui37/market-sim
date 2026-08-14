"""Dollar-cost-averaging portfolio simulator with rebalancing and taxes.

Simulates contributing a fixed amount every month into a multi-asset portfolio:
  - Contributions BUY toward target weights (never sell).
  - On the rebalance schedule the portfolio fully trades back to target.
  - Optional capital-gains tax: FIFO lots classify every sale as short-term
    (held <= 1 year) or long-term; net gains are taxed once a year, losses
    offset gains and carry forward. Dividend taxes are not modeled (prices are
    total-return adjusted for every strategy alike).

Fractional shares are allowed (as at modern brokers).
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TaxConfig:
    st_rate: float = 0.24  # short-term gains: ordinary income (assumed bracket)
    lt_rate: float = 0.15  # long-term gains (held > 1 year)


@dataclass
class DCAResult:
    name: str
    value: pd.Series           # daily portfolio value, net of taxes paid so far
    contributions: pd.Series   # cash added per day
    unit_index: pd.Series      # growth of $1, contributions stripped out (TWR)
    total_contributed: float
    final_value: float
    metrics: dict              # profit, multiple, irr, twr_cagr, max_drawdown, taxes_paid

    def summary(self) -> dict:
        return {
            "name": self.name,
            "start": str(self.value.index[0].date()),
            "end": str(self.value.index[-1].date()),
            "total_contributed": round(self.total_contributed, 2),
            "final_value": round(self.final_value, 2),
            **{k: (round(v, 4) if v is not None else None) for k, v in self.metrics.items()},
        }


class _Ledger:
    """FIFO tax lots + realized-gain bookkeeping."""

    def __init__(self) -> None:
        self.lots: dict[str, deque] = defaultdict(deque)  # asset -> [date, shares, cost]
        self.st_gains = 0.0
        self.lt_gains = 0.0
        self.carryforward = 0.0  # accumulated net losses (stored positive)
        self.taxes_paid = 0.0

    def buy(self, asset: str, day: pd.Timestamp, shares: float, cost: float) -> None:
        if shares > 0:
            self.lots[asset].append([day, shares, cost])

    def sell(self, asset: str, day: pd.Timestamp, shares: float, proceeds: float) -> None:
        if shares <= 0:
            return
        price = proceeds / shares
        remaining = shares
        lots = self.lots[asset]
        while remaining > 1e-12 and lots:
            lot_day, lot_shares, lot_cost = lots[0]
            take = min(lot_shares, remaining)
            cost_taken = lot_cost * take / lot_shares
            gain = take * price - cost_taken
            if (day - lot_day).days <= 365:
                self.st_gains += gain
            else:
                self.lt_gains += gain
            lots[0][1] -= take
            lots[0][2] -= cost_taken
            remaining -= take
            if lots[0][1] <= 1e-12:
                lots.popleft()

    def settle(self, tax: TaxConfig) -> float:
        """Tax due on the gains realized since the last settlement."""
        st, lt = self.st_gains, self.lt_gains
        self.st_gains = self.lt_gains = 0.0

        # Losses offset the other bucket's gains, then carry forward.
        if st < 0 and lt > 0:
            offset = min(-st, lt); lt -= offset; st += offset
        if lt < 0 and st > 0:
            offset = min(-lt, st); st -= offset; lt += offset
        if st < 0:
            self.carryforward += -st; st = 0.0
        if lt < 0:
            self.carryforward += -lt; lt = 0.0
        used = min(self.carryforward, st); st -= used; self.carryforward -= used
        used = min(self.carryforward, lt); lt -= used; self.carryforward -= used

        due = st * tax.st_rate + lt * tax.lt_rate
        self.taxes_paid += due
        return due


def simulate_dca(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    monthly: float = 600.0,
    fees: float = 0.0,
    rebalance: str = "W-MON",
    name: str = "portfolio",
    tax: TaxConfig | None = None,
) -> DCAResult:
    """`prices`: daily adjusted close, columns = assets. `weights`: daily target
    weights on the same index/columns, rows sum to <= 1."""
    prices = prices.dropna(how="all")
    weights = weights.reindex(prices.index).ffill().fillna(0.0)[prices.columns]
    index = prices.index

    contribution_days = _period_starts(index, "MS")
    rebalance_days = _period_starts(index, rebalance)
    year_starts = _period_starts(index, "YS")

    ledger = _Ledger() if tax else None
    holdings = pd.Series(0.0, index=prices.columns)
    cash = 0.0

    # Event-driven: holdings and cash only change on these days; the value
    # series between events is a vectorized dot product.
    position = {day: i for i, day in enumerate(index)}
    events = contribution_days | rebalance_days
    if ledger:
        events = events | year_starts | {index[-1]}
    event_positions = sorted(position[d] for d in events)

    price_matrix = np.nan_to_num(prices.to_numpy())  # NaN price -> worth 0, as before
    values = np.zeros(len(index))
    contribs = np.zeros(len(index))
    filled = 0

    for p in event_positions:
        if p > filled:
            values[filled:p] = price_matrix[filled:p] @ holdings.to_numpy() + cash
            filled = p
        day = index[p]
        px = prices.iloc[p]
        if ledger and p > 0 and day in year_starts:
            cash -= ledger.settle(tax)
        added = 0.0
        if day in contribution_days:
            added = monthly
            cash += monthly
            contribs[p] = monthly
        if day in rebalance_days:
            cash = _rebalance_to_target(holdings, weights.iloc[p], px, cash, fees, ledger, day)
        elif added and cash > 0:
            cash = _buy_only(holdings, weights.iloc[p], px, cash, fees, ledger, day)
        if ledger and p == len(index) - 1:
            cash -= ledger.settle(tax)  # last (partial) year's gains
    values[filled:] = price_matrix[filled:] @ holdings.to_numpy() + cash

    value = pd.Series(values, index=index, name=name)
    contributions = pd.Series(contribs, index=index)
    unit = _unit_index(value, contributions)
    total = float(contributions.sum())
    final = float(value.iloc[-1])
    years = max((prices.index[-1] - prices.index[0]).days, 1) / 365.25

    return DCAResult(
        name=name,
        value=value,
        contributions=contributions,
        unit_index=unit,
        total_contributed=total,
        final_value=final,
        metrics={
            "profit": final - total,
            "multiple": final / total if total else None,
            "irr": _irr(contributions, final),
            "twr_cagr": float(unit.iloc[-1]) ** (1 / years) - 1,
            "max_drawdown": float((unit / unit.cummax() - 1).min()),
            "taxes_paid": ledger.taxes_paid if ledger else 0.0,
        },
    )


def _period_starts(index: pd.DatetimeIndex, freq: str) -> set:
    """First trading day of each period (month, week, year, ...) in index."""
    return set(index.to_series().resample(freq).first().dropna())


def _rebalance_to_target(holdings, target, px, cash, fees, ledger, day) -> float:
    """Trade fully to target weights; returns remaining cash."""
    tradeable = px.notna() & (px > 0)
    total = float((holdings[tradeable] * px[tradeable]).sum() + cash)
    if total <= 0:
        return cash
    target_value = target.where(tradeable, 0.0) * total
    delta_value = target_value - (holdings * px).where(tradeable, 0.0).fillna(0.0)
    for asset in delta_value.index[tradeable & (delta_value.abs() > 1e-9)]:
        delta = delta_value[asset]
        shares = delta / px[asset]
        if ledger:
            if delta > 0:
                ledger.buy(asset, day, shares, delta * (1 + fees))
            else:
                ledger.sell(asset, day, -shares, -delta * (1 - fees))
        holdings[asset] += shares
    fee_paid = float(delta_value.abs().sum()) * fees
    return cash - float(delta_value.sum()) - fee_paid


def _buy_only(holdings, target, px, cash, fees, ledger, day) -> float:
    """Invest available cash at target weights without selling anything."""
    tradeable = px.notna() & (px > 0)
    weights_sum = float(target.where(tradeable, 0.0).sum())
    if weights_sum <= 0:
        return cash
    spend = cash / (1 + fees)
    buy_value = target.where(tradeable, 0.0) / weights_sum * spend
    for asset in buy_value.index[tradeable & (buy_value > 1e-9)]:
        shares = buy_value[asset] / px[asset]
        if ledger:
            ledger.buy(asset, day, shares, buy_value[asset] * (1 + fees))
        holdings[asset] += shares
    return cash - spend * (1 + fees)


def _unit_index(value: pd.Series, flows: pd.Series) -> pd.Series:
    """Time-weighted growth of $1: performance with contributions stripped out."""
    prev = value.shift(1)
    daily_return = (value / (prev + flows)).fillna(1.0)
    daily_return.iloc[0] = 1.0
    return daily_return.cumprod()


def _irr(flows: pd.Series, final_value: float) -> float | None:
    """Annualized money-weighted return: contributions in, final value out."""
    end = flows.index[-1]
    years_left = np.array([(end - t).days / 365.25 for t in flows.index[flows > 0]])
    amounts = flows[flows > 0].to_numpy()
    if len(amounts) == 0 or final_value <= 0:
        return None

    def npv(rate: float) -> float:
        return float((amounts * (1 + rate) ** years_left).sum()) - final_value

    lo, hi = -0.95, 5.0
    if npv(lo) * npv(hi) > 0:
        return None
    for _ in range(100):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    result = (lo + hi) / 2
    return result if math.isfinite(result) else None
