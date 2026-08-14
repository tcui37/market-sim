"""Compare $600/month DCA strategies over the last 10 years.

  1. Buy & hold VOO            2. Buy & hold SPYG
  3. Top-1 market cap company  4. Top-3 equal weight  5. Top-5 equal weight
  (3-5 re-ranked weekly)

Run:  .venv/bin/python experiments/2026-08-13-dca-topcap/run.py [--fees 0.001]
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
from market.dca import simulate_dca
from market.marketcap import DEFAULT_UNIVERSE, market_caps, top_n_weights

MONTHLY = 600.0


def close_matrix(symbols: list[str], start: str) -> pd.DataFrame:
    return pd.DataFrame({s: fetch_ohlcv(s, start=start)["Close"] for s in symbols}).dropna(how="all")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fees", type=float, default=0.0, help="fraction per trade (default 0 = Robinhood)")
    parser.add_argument("--years", type=int, default=10)
    args = parser.parse_args()

    start = str(date.today() - timedelta(days=int(args.years * 365.25)))
    print(f"Window: {start} → {date.today()}   ${MONTHLY:.0f}/month   fees={args.fees:.4f}/trade\n")

    caps = market_caps(start=start)
    universe_prices = close_matrix(DEFAULT_UNIVERSE, start)

    results = []
    for etf in ("VOO", "SPYG"):
        prices = close_matrix([etf], start)
        weights = pd.DataFrame(1.0, index=prices.index, columns=[etf])
        results.append(simulate_dca(prices, weights, MONTHLY, args.fees, name=f"Buy & hold {etf}"))

    for n in (1, 3, 5):
        weights = top_n_weights(caps, n)
        results.append(
            simulate_dca(universe_prices, weights, MONTHLY, args.fees,
                         name=f"Top-{n} market cap (weekly)")
        )

    raw = pd.DataFrame([r.summary() for r in results]).set_index("name")
    raw.to_csv(HERE / "results.csv")

    table = raw.copy()
    table["final_value"] = table["final_value"].map("${:,.0f}".format)
    table["profit"] = table["profit"].map("${:,.0f}".format)
    for col in ("irr", "twr_cagr", "max_drawdown"):
        table[col] = table[col].map("{:+.1%}".format)
    print(table[["total_contributed", "final_value", "profit", "multiple",
                 "irr", "twr_cagr", "max_drawdown"]].to_string())

    # Who was #1 over time (sanity check on the rankings)
    top1 = top_n_weights(caps, 1)
    leader = top1.idxmax(axis=1)[top1.sum(axis=1) > 0]
    changes = leader[leader != leader.shift(1)]
    print("\n#1 market-cap timeline:")
    for day, symbol in changes.items():
        print(f"  {day.date()}  {symbol}")

    _write_chart(results, HERE / "chart.html")
    print(f"\nWrote {HERE / 'results.csv'} and {HERE / 'chart.html'}")


def _write_chart(results, path: Path) -> None:
    import plotly.graph_objects as go

    from market.plots.charts import _LAYOUT, _axes

    palette = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
    fig = go.Figure()
    for res, color in zip(results, palette):
        fig.add_scatter(x=res.value.index, y=res.value, name=res.name,
                        mode="lines", line=dict(color=color, width=2),
                        hovertemplate="$%{y:,.0f}<extra>%{fullData.name}</extra>")
    contributed = results[0].contributions.cumsum()
    fig.add_scatter(x=contributed.index, y=contributed, name="contributed",
                    mode="lines", line=dict(color="#898781", width=2, dash="dot"),
                    hovertemplate="$%{y:,.0f}<extra>contributed</extra>")
    fig.update_layout(title="$600/month for 10 years — portfolio value", **_LAYOUT)
    _axes(fig, "Value ($)", ",.0f")
    fig.write_html(path, include_plotlyjs="cdn")


if __name__ == "__main__":
    main()
