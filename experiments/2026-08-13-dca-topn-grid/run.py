"""$600/month DCA grid: VOO & SPYG vs top-1..5 market cap x {monthly, annual}
rebalancing, pre-tax and after-tax, over a 10-year and a 20-year window
(the 20-year window uses SPY for VOO, which launched Sep 2010).

Run:  .venv/bin/python experiments/2026-08-13-dca-topn-grid/run.py
Writes results.csv and one bar chart per window next to this file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from market import fetch_ohlcv
from market.dca import TaxConfig, simulate_dca
from market.marketcap import DEFAULT_UNIVERSE, market_caps, top_n_weights

MONTHLY = 600.0
TAX = TaxConfig(st_rate=0.24, lt_rate=0.15)
REBALANCE = {"monthly": "MS", "annual": "YS"}
WINDOWS = {
    "10y (2016-2026)": ("2016-08-13", "2026-08-13", "VOO"),
    "20y (2006-2026)": ("2006-08-13", "2026-08-13", "SPY"),  # VOO launched Sep 2010
}


def close_matrix(symbols: list[str], start: str, end: str) -> pd.DataFrame:
    return pd.DataFrame(
        {s: fetch_ohlcv(s, start=start, end=end)["Close"] for s in symbols}
    ).dropna(how="all")


def run_pair(prices, weights, rebalance, name) -> dict:
    pre = simulate_dca(prices, weights, MONTHLY, rebalance=rebalance, name=name)
    post = simulate_dca(prices, weights, MONTHLY, rebalance=rebalance, name=name, tax=TAX)
    return {
        "name": name,
        "contributed": pre.total_contributed,
        "final_value": round(pre.final_value, 2),
        "profit": round(pre.final_value - pre.total_contributed, 2),
        "irr": round(pre.metrics["irr"], 4),
        "max_drawdown": round(pre.metrics["max_drawdown"], 4),
        "taxes_paid": round(post.metrics["taxes_paid"], 2),
        "after_tax_final": round(post.final_value, 2),
        "after_tax_profit": round(post.final_value - post.total_contributed, 2),
        "after_tax_irr": round(post.metrics["irr"], 4),
    }


def run_window(label: str, start: str, end: str, index_etf: str) -> pd.DataFrame:
    print(f"\n=== {label}  ({start} → {end}, ${MONTHLY:.0f}/month) ===")
    caps = market_caps(start=start).loc[:end]
    universe_prices = close_matrix(DEFAULT_UNIVERSE, start, end)

    rows = []
    for etf in (index_etf, "SPYG"):
        prices = close_matrix([etf], start, end)
        weights = pd.DataFrame(1.0, index=prices.index, columns=[etf])
        rows.append(run_pair(prices, weights, "YS", f"Buy & hold {etf}"))
    for n in (1, 2, 3, 4, 5):
        weights = top_n_weights(caps, n)
        for freq_label, freq in REBALANCE.items():
            rows.append(run_pair(universe_prices, weights, freq, f"Top-{n}, {freq_label}"))

    table = pd.DataFrame(rows).set_index("name")
    table.insert(0, "window", label)

    shown = table.copy()
    for col in ("final_value", "profit", "taxes_paid", "after_tax_final", "after_tax_profit"):
        shown[col] = shown[col].map("${:,.0f}".format)
    for col in ("irr", "max_drawdown", "after_tax_irr"):
        shown[col] = shown[col].map("{:+.1%}".format)
    print(shown[["final_value", "profit", "irr", "max_drawdown",
                 "taxes_paid", "after_tax_final", "after_tax_profit", "after_tax_irr"]].to_string())
    return table


def bar_chart(table: pd.DataFrame, label: str, path: Path) -> None:
    import plotly.graph_objects as go

    from market.plots.charts import _LAYOUT, _axes

    fig = go.Figure()
    fig.add_bar(x=table.index, y=table["profit"], name="pre-tax profit",
                marker_color="#2a78d6", hovertemplate="$%{y:,.0f}<extra>pre-tax</extra>")
    fig.add_bar(x=table.index, y=table["after_tax_profit"], name="after-tax profit",
                marker_color="#eb6834", hovertemplate="$%{y:,.0f}<extra>after-tax</extra>")
    contributed = table["contributed"].iloc[0]
    layout = {**_LAYOUT, "hovermode": "x"}
    fig.update_layout(title=f"$600/month, {label} — profit on ${contributed:,.0f} contributed",
                      barmode="group", bargap=0.25, **layout)
    _axes(fig, "Profit ($)", ",.0f")
    fig.write_html(path, include_plotlyjs="cdn")


def main() -> None:
    tables = []
    for label, (start, end, index_etf) in WINDOWS.items():
        table = run_window(label, start, end, index_etf)
        tables.append(table)
        slug = label.split(" ")[0]
        bar_chart(table, label, HERE / f"chart_{slug}.html")
    pd.concat(tables).to_csv(HERE / "results.csv")
    print(f"\nWrote {HERE / 'results.csv'} and per-window charts")


if __name__ == "__main__":
    main()
