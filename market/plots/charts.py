"""Interactive plotly charts for backtest results.

Pure functions: BacktestResult (+ ohlcv) in, go.Figure out. No Streamlit here —
the same figures can be written to HTML by scripts or the investigative agent.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from market.plots.theme import (
    AXIS_INK, BENCHMARK_COLOR, ENTRY_COLOR, EXIT_COLOR, GRID_COLOR, LAYOUT as _LAYOUT,
    PRICE_COLOR, STRATEGY_COLOR, axes as _axes,
)
from market.sim.engine import BacktestResult


def equity_vs_benchmark(result: BacktestResult) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(
        x=result.equity.index, y=result.equity, name=result.strategy_key,
        mode="lines", line=dict(color=STRATEGY_COLOR, width=2),
        hovertemplate="$%{y:,.0f}<extra>%{fullData.name}</extra>",
    )
    fig.add_scatter(
        x=result.benchmark_equity.index, y=result.benchmark_equity, name="buy & hold",
        mode="lines", line=dict(color=BENCHMARK_COLOR, width=2, dash="dash"),
        hovertemplate="$%{y:,.0f}<extra>buy & hold</extra>",
    )
    fig.update_layout(title="Portfolio value", **_LAYOUT)
    return _axes(fig, "Value ($)", ",.0f")


def drawdown_chart(result: BacktestResult) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(
        x=result.drawdown.index, y=result.drawdown, name="drawdown",
        mode="lines", line=dict(color=EXIT_COLOR, width=2),
        fill="tozeroy", fillcolor="rgba(208, 59, 59, 0.15)",
        hovertemplate="%{y:.1%}<extra>drawdown</extra>",
    )
    fig.update_layout(title="Drawdown from peak", showlegend=False, **_LAYOUT)
    return _axes(fig, "Drawdown", ".0%")


def price_with_signals(ohlcv: pd.DataFrame, result: BacktestResult) -> go.Figure:
    close = ohlcv["Close"]
    fig = go.Figure()
    fig.add_scatter(
        x=close.index, y=close, name="close",
        mode="lines", line=dict(color=PRICE_COLOR, width=2),
        hovertemplate="$%{y:,.2f}<extra>close</extra>",
    )
    for signals, name, color, symbol in (
        (result.entries, "entry", ENTRY_COLOR, "triangle-up"),
        (result.exits, "exit", EXIT_COLOR, "triangle-down"),
    ):
        points = close[signals]
        fig.add_scatter(
            x=points.index, y=points, name=name, mode="markers",
            marker=dict(color=color, symbol=symbol, size=10,
                        line=dict(color="#ffffff", width=2)),
            hovertemplate="$%{y:,.2f}<extra>" + name + "</extra>",
        )
    fig.update_layout(title="Price with entry / exit signals", **_LAYOUT)
    return _axes(fig, "Price ($)", ",.2f")
