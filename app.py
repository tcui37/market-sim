"""Streamlit backtesting workbench.

Run with:  streamlit run app.py
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from market import SimConfig, fetch_ohlcv, load_strategies, run_backtest
from market.plots.charts import drawdown_chart, equity_vs_benchmark, price_with_signals

st.set_page_config(page_title="market-sim", layout="wide")


@st.cache_resource
def strategies():
    return load_strategies()


@st.cache_data(ttl=3600, show_spinner="Fetching market data…")
def cached_fetch(symbol: str, start: str, end: str) -> pd.DataFrame:
    return fetch_ohlcv(symbol, start=start, end=end)


# ---------------------------------------------------------------- sidebar
st.sidebar.title("market-sim")

strats = strategies()
key = st.sidebar.selectbox(
    "Strategy", options=sorted(strats), format_func=lambda k: strats[k].name
)
strategy = strats[key]
st.sidebar.caption(strategy.description)

symbol = st.sidebar.text_input("Ticker", value="AAPL").strip().upper()
start, end = st.sidebar.date_input(
    "Date range",
    value=(date.today() - timedelta(days=3650), date.today()),
    max_value=date.today(),
)

params = {}
if strategy.params:
    st.sidebar.subheader("Parameters")
    for name, spec in strategy.params.items():
        params[name] = st.sidebar.slider(
            name,
            min_value=spec["min"],
            max_value=spec["max"],
            value=spec["default"],
            step=spec["step"],
        )

with st.sidebar.expander("Costs & account"):
    cash = st.number_input("Initial cash ($)", value=10_000.0, min_value=100.0, step=1000.0)
    fees = st.number_input("Fees (fraction per trade)", value=0.001, min_value=0.0,
                           max_value=0.05, step=0.0005, format="%.4f")
    slippage = st.number_input("Slippage (fraction)", value=0.0005, min_value=0.0,
                               max_value=0.05, step=0.0005, format="%.4f")

# ---------------------------------------------------------------- main pane
st.title(f"{strategy.name} · {symbol}")

try:
    ohlcv = cached_fetch(symbol, str(start), str(end))
except Exception as exc:  # bad ticker, network down, etc.
    st.error(f"Could not load data for {symbol!r}: {exc}")
    st.stop()

if len(ohlcv) < 2:
    st.warning("Not enough data in the selected date range.")
    st.stop()

result = run_backtest(
    strategy, ohlcv, params, SimConfig(cash=cash, fees=fees, slippage=slippage)
)
m = result.metrics

ROWS = [
    ("Total return", "total_return", "{:+.1%}"),
    ("CAGR", "cagr", "{:+.1%}"),
    ("Sharpe", "sharpe", "{:.2f}"),
    ("Max drawdown", "max_drawdown", "{:.1%}"),
    ("Trades", "num_trades", "{:d}"),
    ("Win rate", "win_rate", "{:.0%}"),
]


def fmt(value, pattern):
    return "—" if value is None else pattern.format(value)


st.dataframe(
    pd.DataFrame(
        {
            "Metric": [label for label, *_ in ROWS],
            strategy.name: [fmt(m[k], p) for _, k, p in ROWS],
            "Buy & Hold": [fmt(m[f"benchmark_{k}"], p) for _, k, p in ROWS],
        }
    ),
    hide_index=True,
    width="content",
)

st.plotly_chart(equity_vs_benchmark(result), width="stretch")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(drawdown_chart(result), width="stretch")
with col2:
    st.plotly_chart(price_with_signals(ohlcv, result), width="stretch")

with st.expander(f"Trades ({len(result.trades)})"):
    st.dataframe(result.trades, hide_index=True, width="stretch")
