"""Charts for top-N market-cap simulations."""

from __future__ import annotations

import plotly.graph_objects as go

from market.plots.theme import BENCHMARK_COLOR, LAYOUT, SERIES_COLORS, axes
from market.topn import TopNResult


def value_chart(results: list[TopNResult], benchmark: TopNResult | None = None,
                after_tax: bool = True, title: str | None = None) -> go.Figure:
    """Portfolio value over time, one line per strategy."""
    fig = go.Figure()
    for i, result in enumerate(results):
        series = result.net_value if after_tax else result.value
        fig.add_scatter(
            x=series.index, y=series, name=result.name, mode="lines",
            line=dict(color=SERIES_COLORS[i % len(SERIES_COLORS)], width=2),
            hovertemplate="$%{y:,.0f}<extra>%{fullData.name}</extra>",
        )
    if benchmark is not None:
        fig.add_scatter(
            x=benchmark.net_value.index, y=benchmark.net_value, name=benchmark.name,
            mode="lines", line=dict(color=BENCHMARK_COLOR, width=2, dash="dash"),
            hovertemplate="$%{y:,.0f}<extra>%{fullData.name}</extra>",
        )
    heading = title or "Portfolio value" + (" (net of tax paid)" if after_tax else "")
    fig.update_layout(title=heading, **LAYOUT)
    return axes(fig, "Value ($)", ",.0f")
