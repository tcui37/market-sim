"""Buy the top-N companies by market cap, then only trade when that list changes.

The strategy this module simulates:
  1. On day one, put `per_stock` dollars into each of the N largest US
     companies by market cap.
  2. On the first trading day of every month (or of every year), re-rank the
     universe. If the top N is unchanged, do nothing at all.
  3. If it changed, sell only the names that fell out and split the proceeds
     equally across the names that took their place. Positions that stayed in
     the top N are never trimmed, so they compound untouched and never realize
     a gain.

Taxes are settled once per calendar year on that year's net realized gains
(FIFO lots, short-term vs long-term), and are paid from outside the portfolio,
the way an investor pays the April bill out of salary. Holdings are therefore
never sold to raise tax money, and `net_value` is simply the portfolio value
minus the tax paid to date.

Rankings use the previous day's market caps, so a check only acts on
information that existed at the time.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from market.dca import TaxConfig, _irr, _Ledger

CHECK_FREQ = {"monthly": "MS", "annual": "YS"}
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


@dataclass
class TopNResult:
    name: str
    value: pd.Series            # gross portfolio value, taxes not deducted
    net_value: pd.Series        # value minus cumulative tax paid
    taxes: pd.Series            # tax settled on each year-end
    trades: pd.DataFrame        # one row per membership change
    yearly: pd.DataFrame        # per calendar year breakdown
    invested: float
    metrics: dict
    holdings: list[str] = field(default_factory=list)  # final positions

    def summary(self) -> dict:
        return {
            "name": self.name,
            "start": str(self.value.index[0].date()),
            "end": str(self.value.index[-1].date()),
            "invested": round(self.invested, 2),
            **{k: (round(v, 4) if isinstance(v, float) else v)
               for k, v in self.metrics.items()},
        }


def simulate_top_n(
    prices: pd.DataFrame,
    caps: pd.DataFrame,
    n: int = 3,
    per_stock: float = 10_000.0,
    check: str = "monthly",
    anchor: str = "JAN",
    tax: TaxConfig | None = None,
    fees: float = 0.0,
    liquidate: bool = False,
    benchmark: pd.Series | None = None,
    name: str | None = None,
) -> TopNResult:
    """`prices`: daily adjusted close. `caps`: daily market cap, same columns.

    `check` is "monthly" or "annual"; both land on the first trading day of a
    month, and `anchor` picks which month an annual check falls in. `liquidate`
    sells everything on the final day so the tax bill includes the gains still
    unrealized at the end. `benchmark` adds that series' calendar-year return
    to the yearly table.
    """
    if check not in CHECK_FREQ:
        raise ValueError(f"check must be one of {sorted(CHECK_FREQ)}, got {check!r}")
    anchor = anchor.upper()
    if anchor not in MONTHS:
        raise ValueError(f"anchor must be one of {MONTHS}, got {anchor!r}")
    prices = prices.dropna(how="all")
    index = prices.index
    if len(index) < 2:
        raise ValueError("Need at least two trading days of prices.")

    ranks = caps.shift(1).reindex(index).ffill()[prices.columns]
    if ranks.iloc[0].isna().any():  # nothing precedes day one, so rank on it
        ranks.iloc[0] = ranks.iloc[0].fillna(caps.reindex(index)[prices.columns].iloc[0])
    freq = CHECK_FREQ[check] + (f"-{anchor}" if check == "annual" else "")
    check_days = _period_starts(index, freq) | {index[0]}
    settle_days = _period_ends(index, "YE") | {index[-1]}

    ledger = _Ledger()
    holdings = pd.Series(0.0, index=prices.columns)
    price_matrix = np.nan_to_num(prices.to_numpy())
    values = np.zeros(len(index))
    taxes = np.zeros(len(index))
    realized = {}  # settle day -> (short-term, long-term) taxable gains that year

    position = {day: i for i, day in enumerate(index)}
    events = sorted(position[d] for d in check_days | settle_days)

    current: list[str] = []
    invested = 0.0
    trades: list[dict] = []
    filled = 0

    for p in events:
        if p > filled:
            values[filled:p] = price_matrix[filled:p] @ holdings.to_numpy()
            filled = p
        day, px = index[p], prices.iloc[p]

        if day in check_days:
            target = _top_names(ranks.iloc[p], px, n)
            if not current:
                if len(target) < n:
                    raise ValueError(
                        f"Only {len(target)} of {n} names have market caps and prices "
                        f"on {day.date()}; start later or lower --top."
                    )
                for symbol in target:
                    shares = per_stock / (1 + fees) / px[symbol]
                    holdings[symbol] += shares
                    ledger.buy(symbol, day, shares, per_stock)
                invested = per_stock * n
                current = target
                trades.append({"date": day.date(), "sold": "", "bought": ",".join(target),
                               "proceeds": invested, "kind": "open"})
            elif len(target) == n and set(target) != set(current):
                trades.append(_swap(holdings, px, current, target, fees, ledger, day))
                current = target

        if day in settle_days:
            before = (ledger.st_realized, ledger.lt_realized)
            if liquidate and p == len(index) - 1:
                _sell_all(holdings, px, fees, ledger, day)
            taxes[p] = ledger.settle(tax) if tax else 0.0
            realized[day] = (ledger.st_realized - before[0], ledger.lt_realized - before[1])

    values[filled:] = price_matrix[filled:] @ holdings.to_numpy()

    value = pd.Series(values, index=index, name=name or f"top-{n} {check}")
    tax_series = pd.Series(taxes, index=index)
    net_value = value - tax_series.cumsum()
    trades_df = pd.DataFrame(trades)

    return TopNResult(
        name=str(value.name),
        value=value,
        net_value=net_value,
        taxes=tax_series[tax_series != 0.0],
        trades=trades_df,
        yearly=_yearly_table(value, tax_series, trades_df, realized, invested, benchmark),
        invested=invested,
        metrics=_metrics(value, net_value, tax_series, invested, len(trades_df) - 1),
        holdings=current,
    )


def buy_and_hold(prices: pd.Series, amount: float, name: str,
                 tax: TaxConfig | None = None, liquidate: bool = False) -> TopNResult:
    """Same accounting for a single ticker bought once and never sold."""
    frame = prices.dropna().to_frame(name)
    caps = pd.DataFrame(1.0, index=frame.index, columns=[name])
    return simulate_top_n(frame, caps, n=1, per_stock=amount, check="annual",
                          tax=tax, liquidate=liquidate, benchmark=prices, name=name)


def _top_names(caps_row: pd.Series, price_row: pd.Series, n: int) -> list[str]:
    investable = caps_row[caps_row.notna() & price_row.notna() & (price_row > 0)]
    return list(investable.nlargest(n).index)


def _swap(holdings, px, current, target, fees, ledger, day) -> dict:
    """Sell the names that dropped out, split the proceeds across the new ones."""
    dropped = [s for s in current if s not in target]
    added = [s for s in target if s not in current]
    proceeds = 0.0
    for symbol in dropped:
        shares = float(holdings[symbol])
        gross = shares * float(px[symbol]) * (1 - fees)
        ledger.sell(symbol, day, shares, gross)
        holdings[symbol] = 0.0
        proceeds += gross

    each = proceeds / (1 + fees) / len(added)
    for symbol in added:
        holdings[symbol] += each / float(px[symbol])
        ledger.buy(symbol, day, each / float(px[symbol]), each * (1 + fees))

    return {"date": day.date(), "sold": ",".join(dropped), "bought": ",".join(added),
            "proceeds": proceeds, "kind": "swap"}


def _sell_all(holdings, px, fees, ledger, day) -> None:
    for symbol in holdings.index[holdings > 0]:
        shares = float(holdings[symbol])
        ledger.sell(symbol, day, shares, shares * float(px[symbol]) * (1 - fees))


def _period_starts(index: pd.DatetimeIndex, freq: str) -> set:
    return set(index.to_series().resample(freq).first().dropna())


def _period_ends(index: pd.DatetimeIndex, freq: str) -> set:
    return set(index.to_series().resample(freq).last().dropna())


def _metrics(value, net_value, taxes, invested, changes) -> dict:
    days = max((value.index[-1] - value.index[0]).days, 1)
    years = days / 365.25
    final = float(value.iloc[-1])
    net_final = float(net_value.iloc[-1])
    total_tax = float(taxes.sum())

    flows = taxes.copy()
    flows.iloc[0] += invested  # money in: the initial buy, then each tax bill
    return {
        "invested": invested,
        "final_value": final,
        "profit": final - invested,
        "total_tax": total_tax,
        "net_final_value": net_final,
        "net_profit": net_final - invested,
        "multiple": final / invested if invested else None,
        "cagr": (final / invested) ** (1 / years) - 1 if invested and final > 0 else None,
        "after_tax_cagr": ((net_final / invested) ** (1 / years) - 1
                           if invested and net_final > 0 else None),
        "after_tax_irr": _irr(flows, final),
        "max_drawdown": float((value / value.cummax() - 1).min()),
        "tax_drag": (final - net_final) / (final - invested) if final > invested else None,
        "changes": changes,
        "years": years,
    }


def _yearly_table(value, taxes, trades, realized, invested, benchmark=None) -> pd.DataFrame:
    """One row per calendar year: value, gain, realized gains, tax, drawdown."""
    bench = _benchmark_yearly(benchmark, value.index) if benchmark is not None else {}
    rows = []
    trade_years = (pd.to_datetime(trades["date"]).dt.year.value_counts()
                   if len(trades) else pd.Series(dtype=int))
    previous = invested
    for year, chunk in value.groupby(value.index.year):
        settle = [d for d in realized if d.year == year]
        st, lt = realized[settle[0]] if settle else (0.0, 0.0)
        end = float(chunk.iloc[-1])
        peak = chunk.cummax().clip(lower=previous)
        tax_paid = float(taxes[taxes.index.year == year].sum())
        rows.append({
            "year": year,
            "start_value": previous,
            "end_value": end,
            "gain": end - previous,
            "return": end / previous - 1 if previous else None,
            "realized_st": st,
            "realized_lt": lt,
            "tax": tax_paid,
            "benchmark": bench.get(year),
            "net_gain": end - previous - tax_paid,
            "max_drawdown": float((chunk / peak - 1).min()),
            "changes": int(trade_years.get(year, 0)) - (1 if year == value.index[0].year else 0),
        })
        previous = end
    table = pd.DataFrame(rows).set_index("year")
    return table.drop(columns=["benchmark"]) if benchmark is None else table


def _benchmark_yearly(series: pd.Series, index: pd.DatetimeIndex) -> dict:
    """Calendar-year return of a reference series, chained from the start date."""
    aligned = series.reindex(index).ffill().dropna()
    if aligned.empty:
        return {}
    ends = aligned.groupby(aligned.index.year).last()
    starts = ends.shift(1)
    starts.iloc[0] = aligned.iloc[0]
    return (ends / starts - 1).to_dict()
