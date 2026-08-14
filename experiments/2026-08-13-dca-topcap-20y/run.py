"""$600/month for 20 years: index ETFs vs top-N market-cap portfolios,
across weekly / monthly / annual rebalancing, before and after capital-gains
taxes from rebalancing.

Strategies:
  Buy & hold SPY (VOO tracks the same index but only exists since 2010)
  Buy & hold SPYG
  Top-{1,3,5} market cap, equal weight, rebalanced {weekly, monthly, annually}

Run:  .venv/bin/python experiments/2026-08-13-dca-topcap-20y/run.py
Writes results.csv and chart.html next to this file.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from market import fetch_ohlcv
from market.dca import TaxConfig, simulate_dca
from market.marketcap import DEFAULT_UNIVERSE, market_caps, top_n_weights

MONTHLY = 600.0
REBALANCE = {"weekly": "W-MON", "monthly": "MS", "annual": "YS"}

GLOSSARY = """
What each column means
  total_contributed  Cash you put in: $600 x every month in the window.
  final_value        Market value at the end, before any rebalancing taxes.
  profit             final_value - total_contributed.
  multiple           final_value / total_contributed.
  irr                Money-weighted annual return on your actual monthly cash
                     flows - "what rate did MY dollars earn?" (dollars invested
                     later count less).
  twr_cagr           Time-weighted annual growth of $1 - pure strategy
                     performance, independent of contribution timing.
  max_drawdown       Worst peak-to-trough fall of strategy performance.
  taxes_paid         Capital-gains tax on gains REALIZED by rebalancing sales,
                     settled yearly: 24% if the sold lot was held <= 1 year
                     (short-term), 15% if longer (long-term); losses offset
                     gains and carry forward. Buy & hold sells nothing, so 0.
  after_tax_final    final_value of the same strategy with those taxes taken
                     out as they occur (lost money also loses its compounding).
  after_tax_profit   after_tax_final - total_contributed.
  after_tax_irr      Money-weighted annual return after rebalancing taxes.
Not modeled for any strategy: dividend taxes, and tax owed on final liquidation.
"""


def close_matrix(symbols: list[str], start: str) -> pd.DataFrame:
    return pd.DataFrame({s: fetch_ohlcv(s, start=start)["Close"] for s in symbols}).dropna(how="all")


def run_pair(prices, weights, rebalance, name, fees, tax):
    """Same strategy without and with taxes; merge into one summary row."""
    pre = simulate_dca(prices, weights, MONTHLY, fees, rebalance, name)
    post = simulate_dca(prices, weights, MONTHLY, fees, rebalance, name, tax=tax)
    row = pre.summary()
    row.pop("taxes_paid")
    row.update({
        "taxes_paid": round(post.metrics["taxes_paid"], 2),
        "after_tax_final": round(post.final_value, 2),
        "after_tax_profit": round(post.final_value - post.total_contributed, 2),
        "after_tax_irr": round(post.metrics["irr"], 4) if post.metrics["irr"] is not None else None,
    })
    return row, pre, post


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fees", type=float, default=0.0)
    parser.add_argument("--years", type=int, default=20)
    parser.add_argument("--st-rate", type=float, default=0.24)
    parser.add_argument("--lt-rate", type=float, default=0.15)
    args = parser.parse_args()

    tax = TaxConfig(st_rate=args.st_rate, lt_rate=args.lt_rate)
    start = str(date.today() - timedelta(days=int(args.years * 365.25)))
    print(f"Window: {start} → {date.today()}   ${MONTHLY:.0f}/month   "
          f"fees={args.fees}/trade   tax ST {tax.st_rate:.0%} / LT {tax.lt_rate:.0%}\n")

    caps = market_caps(start=start)
    universe_prices = close_matrix(DEFAULT_UNIVERSE, start)

    rows, charted = [], {}
    for etf in ("SPY", "SPYG"):
        prices = close_matrix([etf], start)
        weights = pd.DataFrame(1.0, index=prices.index, columns=[etf])
        row, pre, post = run_pair(prices, weights, "YS", f"Buy & hold {etf}", args.fees, tax)
        rows.append(row)
        charted[f"Buy & hold {etf}"] = post

    for n in (1, 3, 5):
        weights = top_n_weights(caps, n)
        for label, freq in REBALANCE.items():
            name = f"Top-{n} cap, {label}"
            row, pre, post = run_pair(universe_prices, weights, freq, name, args.fees, tax)
            rows.append(row)
            if n == 3:
                charted[name] = post

    table = pd.DataFrame(rows).set_index("name")
    table.to_csv(HERE / "results.csv")

    shown = table.copy()
    for col in ("final_value", "profit", "taxes_paid", "after_tax_final", "after_tax_profit"):
        shown[col] = shown[col].map("${:,.0f}".format)
    for col in ("irr", "twr_cagr", "max_drawdown", "after_tax_irr"):
        shown[col] = shown[col].map("{:+.1%}".format)
    print(shown[["final_value", "profit", "irr", "max_drawdown",
                 "taxes_paid", "after_tax_final", "after_tax_profit", "after_tax_irr"]].to_string())
    print(GLOSSARY)

    top1 = top_n_weights(caps, 1)
    leader = top1.idxmax(axis=1)[top1.sum(axis=1) > 0]
    changes = leader[leader != leader.shift(1)]
    print("#1 market-cap timeline:")
    for day, symbol in changes.items():
        print(f"  {day.date()}  {symbol}")

    _write_chart(charted, HERE / "chart.html")
    print(f"\nWrote {HERE / 'results.csv'} and {HERE / 'chart.html'}")


def _write_chart(results: dict, path: Path) -> None:
    import plotly.graph_objects as go

    from market.plots.charts import _LAYOUT, _axes

    palette = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
    fig = go.Figure()
    for (name, res), color in zip(results.items(), palette):
        fig.add_scatter(x=res.value.index, y=res.value, name=name,
                        mode="lines", line=dict(color=color, width=2),
                        hovertemplate="$%{y:,.0f}<extra>%{fullData.name}</extra>")
    contributed = next(iter(results.values())).contributions.cumsum()
    fig.add_scatter(x=contributed.index, y=contributed, name="contributed",
                    mode="lines", line=dict(color="#898781", width=2, dash="dot"),
                    hovertemplate="$%{y:,.0f}<extra>contributed</extra>")
    fig.update_layout(
        title="$600/month for 20 years — after-tax portfolio value", **_LAYOUT
    )
    _axes(fig, "Value ($)", ",.0f")
    fig.write_html(path, include_plotlyjs="cdn")


if __name__ == "__main__":
    main()
