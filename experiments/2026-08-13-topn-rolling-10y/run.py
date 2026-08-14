"""Which top-N, and monthly or annual rebalancing, for a 10-year $600/month
plan — judged across ALL rolling 10-year windows, not one lucky start date.

Grid: N = 1..5 x {monthly, annual} + SPY & SPYG baselines, pre-tax (Roth IRA)
and after-tax (taxable: 24% short-term / 15% long-term), over 41 ten-year
windows starting quarterly from 2006-08 to 2016-08.

Run:  .venv/bin/python experiments/2026-08-13-topn-rolling-10y/run.py
Writes results.csv (per window), summary.csv (aggregates), chart_roth.html,
chart_taxable.html next to this file.
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from tqdm import tqdm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from market import fetch_ohlcv
from market.dca import TaxConfig, simulate_dca
from market.marketcap import DEFAULT_UNIVERSE, market_caps, top_n_weights

MONTHLY = 600.0
TAX = TaxConfig(st_rate=0.24, lt_rate=0.15)
REBALANCE = {"monthly": "MS", "annual": "YS"}
FIRST_START, LAST_START = "2006-08-13", "2016-08-13"
YEARS = 10
GRID = [(n, label, freq) for n in (1, 2, 3, 4, 5) for label, freq in REBALANCE.items()]
WORKERS = max(1, (os.cpu_count() or 2) // 2)

_DATA: dict = {}  # per-worker globals, set once by _init_worker


def _init_worker(universe: pd.DataFrame, etfs: dict, weights: dict) -> None:
    _DATA.update(universe=universe, etfs=etfs, weights=weights)


def _run_window(start: pd.Timestamp) -> list[dict]:
    end = start + pd.DateOffset(years=YEARS)
    prices = _DATA["universe"].loc[start:end]
    rows = []
    for etf, series in _DATA["etfs"].items():
        p = series.loc[start:end].to_frame(etf)
        w = pd.DataFrame(1.0, index=p.index, columns=[etf])
        res = simulate_dca(p, w, MONTHLY, rebalance="YS", name=etf)
        rows.append(_row(start, etf, None, "buy & hold", res, res))  # untaxed = taxed
    for n, freq_label, freq in GRID:
        weights = _DATA["weights"][(n, freq_label)].loc[start:end]
        name = f"Top-{n} {freq_label}"
        pre = simulate_dca(prices, weights, MONTHLY, rebalance=freq, name=name)
        post = simulate_dca(prices, weights, MONTHLY, rebalance=freq, name=name, tax=TAX)
        rows.append(_row(start, name, n, freq_label, pre, post))
    return rows


def window_starts() -> list[pd.Timestamp]:
    starts = []
    current = pd.Timestamp(FIRST_START)
    while current <= pd.Timestamp(LAST_START):
        starts.append(current)
        current += pd.DateOffset(months=3)
    return starts


def main() -> None:
    caps_all = market_caps(start=FIRST_START)
    etf_prices = {s: fetch_ohlcv(s, start=FIRST_START)["Close"] for s in ("SPY", "SPYG")}
    universe_all = pd.DataFrame(
        {s: fetch_ohlcv(s, start=FIRST_START)["Close"] for s in DEFAULT_UNIVERSE}
    ).dropna(how="all")

    # Rank once over the full history per (N, frequency); windows slice it.
    weights_all = {
        (n, label): top_n_weights(caps_all, n, rebalance=freq)
        for n, label, freq in tqdm(GRID, desc="ranking top-N weights", unit="cell")
    }

    starts = window_starts()
    rows = []
    with ProcessPoolExecutor(
        max_workers=WORKERS,
        initializer=_init_worker,
        initargs=(universe_all, etf_prices, weights_all),
    ) as pool:
        futures = {pool.submit(_run_window, start): start for start in starts}
        progress = tqdm(as_completed(futures), total=len(starts),
                        desc=f"simulating 10y windows ({WORKERS} workers)", unit="window")
        for future in progress:
            progress.set_postfix_str(str(futures[future].date()))
            rows.extend(future.result())

    results = pd.DataFrame(rows).sort_values(["window", "strategy"])  # as_completed is unordered
    results.to_csv(HERE / "results.csv", index=False)

    summary = (
        results.groupby("strategy")
        .agg(
            median_irr=("irr", "median"),
            worst_irr=("irr", "min"),
            best_irr=("irr", "max"),
            median_after_tax_irr=("after_tax_irr", "median"),
            worst_after_tax_irr=("after_tax_irr", "min"),
            median_taxes=("taxes_paid", "median"),
        )
        .round(4)
    )
    spyg = results[results.strategy == "SPYG"].set_index("window")
    for strategy in summary.index:
        sub = results[results.strategy == strategy].set_index("window")
        summary.loc[strategy, "beats_spyg_roth"] = float((sub["irr"] > spyg["irr"]).mean())
        summary.loc[strategy, "beats_spyg_taxable"] = float(
            (sub["after_tax_irr"] > spyg["irr"]).mean()
        )
    summary = summary.sort_values("median_after_tax_irr", ascending=False)
    summary.to_csv(HERE / "summary.csv")

    shown = summary.copy()
    for col in shown.columns:
        shown[col] = shown[col].map(("{:+.1%}" if "irr" in col else
                                     "{:.0%}" if "beats" in col else "${:,.0f}").format)
    print(f"\nAggregates over {len(starts)} rolling 10-year windows "
          f"(${MONTHLY:.0f}/month, tax ST {TAX.st_rate:.0%} / LT {TAX.lt_rate:.0%}):\n")
    print(shown.to_string())

    _charts(results)
    print(f"\nWrote results.csv, summary.csv, chart_roth.html, chart_taxable.html in {HERE}")


def _row(start, strategy, n, freq, pre, post) -> dict:
    return {
        "window": str(start.date()),
        "strategy": strategy,
        "n": n,
        "rebalance": freq,
        "contributed": pre.total_contributed,
        "final": round(pre.final_value, 2),
        "irr": pre.metrics["irr"],
        "max_drawdown": pre.metrics["max_drawdown"],
        "taxes_paid": round(post.metrics["taxes_paid"], 2),
        "after_tax_final": round(post.final_value, 2),
        "after_tax_irr": post.metrics["irr"],
    }


def _charts(results: pd.DataFrame) -> None:
    import plotly.graph_objects as go

    from market.plots.charts import _LAYOUT, _axes

    order = ["SPY", "SPYG"] + [f"Top-{n} {f}" for n in (1, 2, 3, 4, 5)
                               for f in ("monthly", "annual")]
    colors = {"buy & hold": "#898781", "monthly": "#2a78d6", "annual": "#eb6834"}

    for account, column, path in (
        ("Roth IRA (pre-tax)", "irr", HERE / "chart_roth.html"),
        ("taxable (after tax)", "after_tax_irr", HERE / "chart_taxable.html"),
    ):
        fig = go.Figure()
        seen_groups = set()
        for strategy in order:
            sub = results[results.strategy == strategy]
            group = sub["rebalance"].iloc[0]
            fig.add_box(
                y=sub[column], name=strategy, marker_color=colors[group],
                legendgroup=group, showlegend=group not in seen_groups,
                legendgrouptitle_text=group if group not in seen_groups else None,
                boxpoints="all", jitter=0.4, pointpos=0, marker_size=4,
                line_width=2,
            )
            seen_groups.add(group)
        layout = {**_LAYOUT, "hovermode": "closest"}
        fig.update_layout(
            title=f"IRR across 41 rolling 10-year windows — {account}", **layout
        )
        _axes(fig, "Annualized IRR", ".0%")
        fig.write_html(path, include_plotlyjs="cdn")


if __name__ == "__main__":
    main()
