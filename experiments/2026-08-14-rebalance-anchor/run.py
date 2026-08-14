"""Does the annual-rebalancing recommendation survive the calendar?

Extends the rolling-window study with (a) QUARTERLY rebalancing and (b) every
possible rebalance ANCHOR: annual rebalancing anchored to each of the 12
months, quarterly to each of its 3 phases — so "annual wins" can be separated
from "January got lucky", and the anchor-timing variance of the strategy is
measured directly.

Grid: N in {1,2,3} x {monthly, quarterly x3 anchors, annual x12 anchors},
pre-tax (Roth) and after-tax (24% ST / 15% LT), across 41 rolling 10-year
windows ($600/month). SPYG baseline per window.

Run:  .venv/bin/python experiments/2026-08-14-rebalance-anchor/run.py
Writes results.csv, freq_summary.csv, anchor_summary.csv, luck_summary.csv,
chart_anchors_top2.html, chart_freq.html next to this file.
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
FIRST_START, LAST_START = "2006-08-13", "2016-08-13"
YEARS = 10
NS = (1, 2, 3)
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
CELLS = (
    [("monthly", "MS", "—")]
    + [("quarterly", f"QS-{m}", m) for m in MONTHS[:3]]
    + [("annual", f"YS-{m}", m) for m in MONTHS]
)
WORKERS = max(1, (os.cpu_count() or 2) // 2)

_DATA: dict = {}


def _init_worker(universe: pd.DataFrame, spyg: pd.Series, weights: dict) -> None:
    _DATA.update(universe=universe, spyg=spyg, weights=weights)


def _run_window(start: pd.Timestamp) -> list[dict]:
    end = start + pd.DateOffset(years=YEARS)
    prices = _DATA["universe"].loc[start:end]
    rows = []

    p = _DATA["spyg"].loc[start:end].to_frame("SPYG")
    w = pd.DataFrame(1.0, index=p.index, columns=["SPYG"])
    res = simulate_dca(p, w, MONTHLY, rebalance="YS", name="SPYG")
    rows.append(_row(start, None, "buy & hold", "—", res, res))

    for n in NS:
        for freq_label, freq, anchor in CELLS:
            weights = _DATA["weights"][(n, freq)].loc[start:end]
            name = f"Top-{n} {freq_label} {anchor}"
            pre = simulate_dca(prices, weights, MONTHLY, rebalance=freq, name=name)
            post = simulate_dca(prices, weights, MONTHLY, rebalance=freq, name=name, tax=TAX)
            rows.append(_row(start, n, freq_label, anchor, pre, post))
    return rows


def _row(start, n, freq, anchor, pre, post) -> dict:
    return {
        "window": str(start.date()),
        "n": n,
        "freq": freq,
        "anchor": anchor,
        "irr": pre.metrics["irr"],
        "after_tax_irr": post.metrics["irr"],
        "taxes_paid": round(post.metrics["taxes_paid"], 2),
        "final": round(pre.final_value, 2),
        "after_tax_final": round(post.final_value, 2),
        "max_drawdown": pre.metrics["max_drawdown"],
    }


def window_starts() -> list[pd.Timestamp]:
    starts, current = [], pd.Timestamp(FIRST_START)
    while current <= pd.Timestamp(LAST_START):
        starts.append(current)
        current += pd.DateOffset(months=3)
    return starts


def main() -> None:
    caps_all = market_caps(start=FIRST_START)
    spyg = fetch_ohlcv("SPYG", start=FIRST_START)["Close"]
    universe_all = pd.DataFrame(
        {s: fetch_ohlcv(s, start=FIRST_START)["Close"] for s in DEFAULT_UNIVERSE}
    ).dropna(how="all")

    grid = [(n, freq) for n in NS for _, freq, _ in CELLS]
    weights_all = {
        (n, freq): top_n_weights(caps_all, n, rebalance=freq)
        for n, freq in tqdm(grid, desc="ranking top-N weights", unit="cell")
    }

    starts = window_starts()
    rows = []
    with ProcessPoolExecutor(max_workers=WORKERS, initializer=_init_worker,
                             initargs=(universe_all, spyg, weights_all)) as pool:
        futures = {pool.submit(_run_window, s): s for s in starts}
        progress = tqdm(as_completed(futures), total=len(starts),
                        desc=f"simulating 10y windows ({WORKERS} workers)", unit="window")
        for future in progress:
            progress.set_postfix_str(str(futures[future].date()))
            rows.extend(future.result())

    results = pd.DataFrame(rows).sort_values(["window", "n", "freq", "anchor"])
    results.to_csv(HERE / "results.csv", index=False)
    topn = results[results.n.notna()]

    # 1. Frequency ladder, anchors pooled: is quarterly a middle ground?
    freq_summary = (
        topn.groupby(["n", "freq"])
        .agg(median_irr=("irr", "median"),
             median_after_tax_irr=("after_tax_irr", "median"),
             worst_after_tax_irr=("after_tax_irr", "min"),
             median_taxes=("taxes_paid", "median"))
        .round(4)
    )
    freq_summary.to_csv(HERE / "freq_summary.csv")
    print("\nFrequency ladder (all anchors pooled):\n")
    print(_pct(freq_summary).to_string())

    # 2. Annual anchors: does the January choice matter?
    annual = topn[topn.freq == "annual"]
    anchor_summary = (
        annual.groupby(["n", "anchor"])
        .agg(median_irr=("irr", "median"),
             median_after_tax_irr=("after_tax_irr", "median"),
             worst_after_tax_irr=("after_tax_irr", "min"))
        .round(4)
        .reindex(MONTHS, level="anchor")
    )
    anchor_summary.to_csv(HERE / "anchor_summary.csv")
    print("\nAnnual rebalancing by anchor month:\n")
    print(_pct(anchor_summary).to_string())

    # 3. Anchor luck: within one window, how far apart can the 12 anchors land?
    luck = (
        annual.groupby(["n", "window"])["after_tax_irr"]
        .agg(spread=lambda s: s.max() - s.min())
        .groupby("n")["spread"]
        .agg(median_anchor_spread="median", worst_anchor_spread="max")
        .round(4)
    )
    luck.to_csv(HERE / "luck_summary.csv")
    print("\nAnchor luck (after-tax IRR spread across the 12 anchors, per window):\n")
    print(_pct(luck).to_string())
    spyg_median = results[results.freq == "buy & hold"]["irr"].median()
    print(f"\nSPYG baseline median IRR: {spyg_median:+.1%}")

    _charts(topn)
    print(f"\nWrote results + summaries + charts in {HERE}")


def _pct(df: pd.DataFrame) -> pd.DataFrame:
    shown = df.copy()
    for col in shown.columns:
        shown[col] = shown[col].map(("${:,.0f}" if "tax" in col and "irr" not in col
                                     else "{:+.1%}").format)
    return shown


def _charts(topn: pd.DataFrame) -> None:
    import plotly.graph_objects as go

    from market.plots.charts import _LAYOUT, _axes

    # Anchor chart for the recommended N=2: 12 annual anchors vs monthly/quarterly
    fig = go.Figure()
    sub = topn[(topn.n == 2) & (topn.freq == "monthly")]
    fig.add_box(y=sub.after_tax_irr, name="monthly", marker_color="#898781",
                boxpoints="all", jitter=0.4, pointpos=0, marker_size=3, line_width=2)
    sub = topn[(topn.n == 2) & (topn.freq == "quarterly")]
    fig.add_box(y=sub.after_tax_irr, name="quarterly (all)", marker_color="#1baf7a",
                boxpoints="all", jitter=0.4, pointpos=0, marker_size=3, line_width=2)
    for month in MONTHS:
        sub = topn[(topn.n == 2) & (topn.freq == "annual") & (topn.anchor == month)]
        fig.add_box(y=sub.after_tax_irr, name=f"annual {month}", marker_color="#2a78d6",
                    boxpoints="all", jitter=0.4, pointpos=0, marker_size=3, line_width=2)
    layout = {**_LAYOUT, "hovermode": "closest"}
    fig.update_layout(title="Top-2 after-tax IRR by rebalance schedule "
                            "(41 rolling 10-year windows)", showlegend=False, **layout)
    _axes(fig, "After-tax IRR", ".0%")
    fig.write_html(HERE / "chart_anchors_top2.html", include_plotlyjs="cdn")

    # Frequency ladder chart across N
    fig = go.Figure()
    colors = {"monthly": "#898781", "quarterly": "#1baf7a", "annual": "#2a78d6"}
    for freq in ("monthly", "quarterly", "annual"):
        sub = topn[topn.freq == freq]
        fig.add_box(x=sub.n, y=sub.after_tax_irr, name=freq,
                    marker_color=colors[freq], line_width=2)
    fig.update_layout(title="After-tax IRR by N and rebalance frequency "
                            "(anchors pooled)", boxmode="group", **_LAYOUT)
    _axes(fig, "After-tax IRR", ".0%")
    fig.update_xaxes(title="N (top-N by market cap)", dtick=1)
    fig.write_html(HERE / "chart_freq.html", include_plotlyjs="cdn")


if __name__ == "__main__":
    main()
