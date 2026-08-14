"""Run a strategy against market data with vectorbt."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import vectorbt as vbt

from market.metrics.metrics import compute_metrics
from market.sim.config import SimConfig
from market.strategies import Strategy


@dataclass
class BacktestResult:
    """Everything the app and the investigative agent need from one backtest."""

    strategy_key: str
    params: dict
    config: SimConfig
    metrics: dict            # strategy metrics + benchmark_* fields
    equity: pd.Series        # portfolio value over time
    benchmark_equity: pd.Series
    drawdown: pd.Series      # fraction below running peak (<= 0)
    trades: pd.DataFrame     # human-readable trade records
    entries: pd.Series = field(repr=False)
    exits: pd.Series = field(repr=False)

    def summary(self) -> dict:
        """JSON-safe summary: metrics plus a compact trades overview."""
        return {
            "strategy": self.strategy_key,
            "params": self.params,
            "start": str(self.equity.index[0].date()),
            "end": str(self.equity.index[-1].date()),
            "metrics": self.metrics,
            "num_trades": len(self.trades),
            "first_trades": self.trades.head(3).to_dict("records"),
            "last_trades": self.trades.tail(3).to_dict("records"),
        }


def run_backtest(
    strategy: Strategy,
    ohlcv: pd.DataFrame,
    params: dict | None = None,
    config: SimConfig = SimConfig(),
) -> BacktestResult:
    """Backtest `strategy` on `ohlcv`, always alongside a buy-and-hold benchmark."""
    params = {**strategy.default_params(), **(params or {})}
    entries, exits = strategy.generate_signals(ohlcv, **params)
    close = ohlcv["Close"]

    pf = vbt.Portfolio.from_signals(
        close=close,
        entries=entries,
        exits=exits,
        init_cash=config.cash,
        fees=config.fees,
        slippage=config.slippage,
        freq=config.freq,
    )
    benchmark = vbt.Portfolio.from_holding(
        close, init_cash=config.cash, fees=config.fees, freq=config.freq
    )

    trades = pf.trades.records_readable
    # Timestamps → strings so trades (and summary()) serialize cleanly.
    for col in trades.columns:
        if pd.api.types.is_datetime64_any_dtype(trades[col]):
            trades[col] = trades[col].astype(str)

    return BacktestResult(
        strategy_key=strategy.key,
        params=params,
        config=config,
        metrics=compute_metrics(pf, benchmark),
        equity=pf.value(),
        benchmark_equity=benchmark.value(),
        drawdown=pf.drawdown(),
        trades=trades,
        entries=entries,
        exits=exits,
    )
