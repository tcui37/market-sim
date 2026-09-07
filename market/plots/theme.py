"""Shared chart palette and layout, so every figure in the repo reads as one system.

Validated palette from the dataviz skill: one categorical ramp, muted ink for
reference series, status colors reserved for good/bad.
"""

from __future__ import annotations

import plotly.graph_objects as go

STRATEGY_COLOR = "#2a78d6"   # categorical slot 1 (blue)
BENCHMARK_COLOR = "#898781"  # muted ink, recessive reference line
ENTRY_COLOR = "#0ca30c"      # status: good
EXIT_COLOR = "#d03b3b"       # status: critical
PRICE_COLOR = "#52514e"      # secondary ink
GRID_COLOR = "#e1e0d9"
AXIS_INK = "#898781"

# Categorical ramp for multi-series charts, in order of use.
SERIES_COLORS = ["#2a78d6", "#1baf7a", "#d9822b", "#8b5cf6", "#d03b3b", "#0e9ec4"]

LAYOUT = dict(
    template="none",
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color="#52514e"),
    margin=dict(l=60, r=20, t=48, b=40),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)


def axes(fig: go.Figure, y_title: str, y_format: str | None = None) -> go.Figure:
    fig.update_xaxes(showgrid=False, linecolor=GRID_COLOR, tickcolor=GRID_COLOR,
                     tickfont=dict(color=AXIS_INK))
    fig.update_yaxes(title=y_title, gridcolor=GRID_COLOR, zeroline=False,
                     linecolor=GRID_COLOR, tickcolor=GRID_COLOR,
                     tickfont=dict(color=AXIS_INK), tickformat=y_format)
    return fig
