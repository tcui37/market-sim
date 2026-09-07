#!/usr/bin/env python3
"""Hold the top-N US companies by market cap, and only trade when that list changes.

    python simulate.py --top 3 --per-stock 10000 --years 10 --check monthly

Puts `--per-stock` dollars into each of the N largest companies by market cap
`--years` ago, re-ranks on the first trading day of every month (or year), and
swaps only the names that fell out of the top N. Reports gains, taxes, APY and
drawdown for every year and for the whole window, from real historical prices.

Any of --top, --years and --check accept comma-separated lists, which runs the
whole grid and prints one comparison table.

Data comes from data/market-snapshot.parquet, a committed offline copy of
prices and market caps. Build or refresh it with:

    python simulate.py snapshot
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from market import snapshot as snap
from market.dca import TaxConfig
from market.tax import FILINGS, STATES, TaxProfile
from market.topn import CHECK_FREQ, MONTHS, TopNResult, buy_and_hold, simulate_top_n

HERE = Path(__file__).resolve().parent

MONEY = ("invested", "final", "profit", "tax", "net_final", "net_profit",
         "start_value", "end_value", "gain", "net_gain", "realized_st", "realized_lt")
PERCENT = ("cagr", "after_tax_cagr", "after_tax_irr", "max_dd", "return",
           "max_drawdown", "benchmark")

# The strategies written out by `simulate.py report`.
REPORT_STRATEGIES = [(1, "monthly"), (2, "monthly"), (3, "monthly"), (5, "monthly"),
                     (1, "annual"), (2, "annual"), (3, "annual")]


# ------------------------------------------------------------------ simulation

def strategy_name(n: int, check: str, anchor: str) -> str:
    if check == "annual" and anchor != "JAN":
        return f"Top-{n} annual ({anchor})"
    return f"Top-{n} {check}"


def average_anchors(runs: dict[str, TopNResult], name: str) -> TopNResult:
    """Collapse one result per anchor month into their average.

    Trades and holdings cannot be averaged, so they come from the January run.
    """
    base = runs["JAN"]
    def stack(attr):
        return pd.concat([getattr(r, attr) for r in runs.values()], axis=1)
    value = stack("value").mean(axis=1)
    net_value = stack("net_value").mean(axis=1)
    taxes = pd.concat([r.taxes.reindex(base.value.index).fillna(0.0)
                       for r in runs.values()], axis=1).mean(axis=1)
    yearly = pd.concat([r.yearly for r in runs.values()]).groupby(level=0).mean()
    return TopNResult(
        name=name, value=value, net_value=net_value, taxes=taxes[taxes != 0.0],
        trades=base.trades, yearly=yearly, invested=base.invested,
        metrics=_average_metrics([r.metrics for r in runs.values()]),
        holdings=base.holdings,
    )


def _average_metrics(metrics: list[dict]) -> dict:
    averaged = {}
    for key in metrics[0]:
        values = [m[key] for m in metrics if m[key] is not None]
        averaged[key] = sum(values) / len(values) if values else None
    return averaged


def run_grid(data: snap.Snapshot, args) -> tuple[pd.DataFrame, dict, dict]:
    """Simulate every (years, top, check) cell. Returns summary, results, benchmarks."""
    end = pd.Timestamp(args.end) if args.end else data.prices.index[-1]
    tax = build_tax(args)
    rows, results, benchmarks = [], {}, {}

    for years in args.years:
        start = pd.Timestamp(args.start) if args.start else end - pd.DateOffset(years=years)
        window = data.window(start, end)
        if window.prices.empty:
            raise SystemExit(f"No snapshot data between {start.date()} and {end.date()}.")
        reference = window.prices[args.benchmark]

        for n in args.top:
            per_stock = args.total / n if args.total else args.per_stock
            invested = n * per_stock
            bench = buy_and_hold(reference, invested, f"{args.benchmark} buy & hold",
                                 tax, args.liquidate)
            benchmarks[(years, n)] = bench
            for check in args.check:
                result = simulate_top_n(
                    window.prices[window.universe], window.caps, n=n,
                    per_stock=per_stock, check=check, anchor=args.anchor, tax=tax,
                    fees=args.fees, liquidate=args.liquidate, benchmark=reference,
                    name=strategy_name(n, check, args.anchor),
                )
                results[(years, n, check)] = result
                rows.append(_summary_row(years, n, result))
            rows.append(_summary_row(years, n, bench))

    return pd.DataFrame(rows), results, benchmarks


def _summary_row(years: int, n: int, result) -> dict:
    m = result.metrics
    return {
        "years": years,
        "top": n,
        "strategy": result.name,
        "start": str(result.value.index[0].date()),
        "invested": m["invested"],
        "final": m["final_value"],
        "profit": m["profit"],
        "tax": m["total_tax"],
        "net_final": m["net_final_value"],
        "cagr": m["cagr"],
        "after_tax_cagr": m["after_tax_cagr"],
        "after_tax_irr": m["after_tax_irr"],
        "max_dd": m["max_drawdown"],
        "changes": m["changes"],
    }


def build_tax(args) -> TaxConfig | None:
    if args.tax_free:
        return None
    if args.st_rate is not None or args.lt_rate is not None:
        return TaxConfig(st_rate=args.st_rate if args.st_rate is not None else 0.24,
                         lt_rate=args.lt_rate if args.lt_rate is not None else 0.15)
    return TaxConfig(profile=TaxProfile(args.income, args.filing, args.state))


def describe_tax(args, tax: TaxConfig | None) -> list[str]:
    if tax is None:
        return ["tax-free account (Roth IRA, 401k): no capital-gains tax modeled"]
    if tax.profile is None:
        return [f"flat rates: {tax.st_rate:.1%} short-term, {tax.lt_rate:.1%} long-term"]
    profile = tax.profile
    st, lt = profile.rates()
    where = "federal only" if profile.state == "NONE" else f"federal + {profile.state}"
    lines = [f"{where} brackets, {profile.filing}, other income ${profile.income:,.0f}",
             f"next dollar of gain: {st:.1%} short-term, {lt:.1%} long-term "
             f"(each year is taxed on its own realized gains, so big years cost more)"]
    if not args.income_given:
        lines.append("pass --income / --state to model your own bracket")
    return lines


def describe_rule(args) -> str:
    cadence = " and ".join("every month" if c == "monthly" else f"every {args.anchor}"
                           for c in args.check)
    return f"re-rank on the 1st trading day of {cadence}, sell only the names that dropped out"


def benchmark_label(ticker: str) -> str:
    return "sp500" if ticker in {"SPY", "VOO", "IVV"} else ticker.lower()


# ------------------------------------------------------------------ formatting

def changes_text(value: float) -> str:
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.1f}"


def fmt(df: pd.DataFrame, percent: tuple[str, ...] = ()) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col in MONEY:
            out[col] = out[col].map(lambda v: "-" if pd.isna(v) else f"${v:,.0f}")
        elif col == "changes":
            out[col] = out[col].map(lambda v: "-" if pd.isna(v) else changes_text(v))
        elif col in PERCENT or col in percent:
            out[col] = out[col].map(lambda v: "-" if pd.isna(v) else f"{v:+.1%}")
    return out


def yearly_view(result, benchmark: str) -> pd.DataFrame:
    """The year-by-year table with display names and a stable column order."""
    columns = ["start_value", "end_value", "gain", "return", "benchmark", "realized_st",
               "realized_lt", "tax", "net_gain", "max_drawdown", "changes"]
    table = result.yearly[[c for c in columns if c in result.yearly.columns]]
    return table.rename(columns={"max_drawdown": "max_dd", "benchmark": benchmark})


def print_header(data: snap.Snapshot, args, tax) -> None:
    universe = ", ".join(data.universe[:6])
    print("\ntop-N by market cap, traded only when the list changes\n")
    print(f"  data      {data.describe()}")
    print(f"  universe  {len(data.universe)} names: {universe}, ...")
    stake = (f"${args.total:,.0f} split equally across the top N" if args.total
             else f"${args.per_stock:,.0f} per stock")
    print(f"  stake     {stake} at the start, no further contributions")
    print(f"  rule      {describe_rule(args)}")
    for i, line in enumerate(describe_tax(args, tax)):
        print(f"  {'tax' if i == 0 else '   ':<9} {line}")
    if args.liquidate:
        print("  exit      everything sold on the final day, so the tax bill is complete")
    print()


def print_yearly(result, args, title: str) -> None:
    print(f"\n{title}")
    label = benchmark_label(args.benchmark)
    print(fmt(yearly_view(result, label), (label,)).to_string())
    print(f"  final holdings: {', '.join(result.holdings)}")


def print_trades(result) -> None:
    if len(result.trades) <= 1:
        print("\n  the top list never changed over this window")
        return
    trades = result.trades.copy()
    trades["proceeds"] = trades["proceeds"].map(lambda v: f"${v:,.0f}")
    print("\nportfolio changes")
    print(trades.to_string(index=False))


# ------------------------------------------------------------------ markdown

def as_money(df: pd.DataFrame) -> pd.DataFrame:
    return df.map(lambda v: "-" if pd.isna(v) else f"${v:,.0f}")


def as_percent(df: pd.DataFrame) -> pd.DataFrame:
    return df.map(lambda v: "-" if pd.isna(v) else f"{v:+.1%}")


def md_table(shown: pd.DataFrame, index_label: str | None = None) -> str:
    """Render an already-formatted DataFrame as a GitHub-flavored markdown table."""
    header = list(shown.columns)
    if index_label:
        header = [index_label, *header]
    lines = ["| " + " | ".join(str(h) for h in header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    for key, row in shown.iterrows():
        cells = [str(v) for v in row]
        if index_label:
            cells = [str(key), *cells]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


SUMMARY_NAMES = {
    "final": "Final value", "profit": "Profit", "tax": "Tax paid",
    "net_final": "After tax", "cagr": "Annual return",
    "after_tax_cagr": "After-tax annual return", "max_dd": "Max drawdown",
    "changes": "Changes",
}


def _summary_frame(results: dict, benchmark, label: str, years: int) -> pd.DataFrame:
    rows = [_summary_row(years, 0, r) for r in results.values()]
    rows.append({**_summary_row(years, 0, benchmark), "strategy": f"{label} buy & hold"})
    return pd.DataFrame(rows).set_index("strategy")[list(SUMMARY_NAMES)]


def _verdict(summary: pd.DataFrame, benchmark, label: str) -> list[str]:
    """Scannable bullets: who won, monthly versus annual, and what it cost."""
    strategies = summary.iloc[:-1]
    best = strategies["after_tax_cagr"].idxmax()
    monthly = strategies[[n.endswith("monthly") for n in strategies.index]]
    annual = strategies[[not n.endswith("monthly") for n in strategies.index]]
    top_monthly, top_annual = monthly["after_tax_cagr"].idxmax(), annual["after_tax_cagr"].idxmax()
    gap = monthly.loc[top_monthly, "after_tax_cagr"] - annual.loc[top_annual, "after_tax_cagr"]

    bench_cagr, bench_dd = benchmark.metrics["cagr"], benchmark.metrics["max_drawdown"]
    beat = int((strategies["cagr"] > bench_cagr).sum())
    deeper = int((strategies["max_dd"] < bench_dd).sum())
    count = len(strategies)
    cheapest, dearest = strategies["tax"].idxmin(), strategies["tax"].idxmax()

    bullets = [f"**{best}** had the highest after-tax annual return, "
               f"{strategies.loc[best, 'after_tax_cagr']:+.1%}, against {bench_cagr:+.1%} "
               f"for {label}."]
    if best != top_annual:
        bullets.append(f"**{top_annual}** led the annual variants at "
                       f"{annual.loc[top_annual, 'after_tax_cagr']:+.1%}.")
    bullets.append(
        f"The best monthly variant was **{top_monthly}** at "
        f"{monthly.loc[top_monthly, 'after_tax_cagr']:+.1%} after tax, "
        f"{abs(gap) * 100:.1f} points {'ahead of' if gap > 0 else 'behind'} {top_annual}, "
        f"and it traded {changes_text(monthly.loc[top_monthly, 'changes'])} times to that "
        f"strategy's {changes_text(annual.loc[top_annual, 'changes'])}."
    )
    bullets.append(
        ("All " + str(count) if beat == count else f"{beat} of the {count}")
        + " beat the index, and "
        + ("all of them" if deeper == count else
           "none of them" if deeper == 0 else f"{deeper} of them")
        + " fell further than it did at their worst."
    )
    bullets.append(
        f"Tax ranged from ${strategies.loc[cheapest, 'tax']:,.0f} ({cheapest}) to "
        f"${strategies.loc[dearest, 'tax']:,.0f} ({dearest}); a strategy only owes "
        "anything in a year its top N actually changed."
    )
    return bullets


def anchor_section(per_anchor: dict) -> list[str]:
    """How much the month of the annual check mattered, behind the averages."""
    spread = pd.DataFrame({
        name: {anchor: run.metrics["after_tax_cagr"] for anchor, run in runs.items()}
        for name, runs in per_anchor.items()
    })
    rows = {}
    for name in spread.columns:
        column = spread[name]
        rows[name] = {"Best month": f"{column.idxmax()} {column.max():+.1%}",
                      "Worst month": f"{column.idxmin()} {column.min():+.1%}",
                      "Spread": f"{(column.max() - column.min()) * 100:.1f} points",
                      "Average": f"{column.mean():+.1%}"}
    table = pd.DataFrame(rows).T

    return [
        "The month an annual check falls in changes the outcome. After-tax annual "
        "return by that month:",
        "",
        md_table(table, "Strategy"),
        "",
        "<details><summary>All 12 configurations, after-tax annual return</summary>",
        "",
        md_table(as_percent(spread), "Check month"),
        "",
        "</details>",
        "",
    ]


def results_section(results: dict, benchmark, args, years: int, label: str,
                    per_anchor: dict) -> list[str]:
    """One window's headline: the bullets, then both orderings of the same table."""
    first = next(iter(results.values()))
    summary = _summary_frame(results, benchmark, label, years)
    ranked = summary.sort_values("after_tax_cagr", ascending=False)

    return [
        f"### {years}-year window",
        "",
        f"{first.value.index[0].date()} to {first.value.index[-1].date()} "
        f"({first.metrics['years']:.1f} years), ${args.total:,.0f} split across the top N "
        f"on the first day. Every annual row is the average of the 12 configurations, "
        f"one for each month the yearly check can fall in.",
        "",
        *[f"- {bullet}" for bullet in _verdict(summary, benchmark, label)],
        "",
        "By strategy:",
        "",
        md_table(fmt(summary).rename(columns=SUMMARY_NAMES), "Strategy"),
        "",
        "Ranked by after-tax annual return:",
        "",
        md_table(fmt(ranked).rename(columns=SUMMARY_NAMES), "Strategy"),
        "",
        *anchor_section(per_anchor),
    ]


def insight_section(results: dict, args, years: int, label: str) -> list[str]:
    """The year-by-year detail, kept to a single window so the page stays readable."""
    first = next(iter(results.values()))
    returns = pd.DataFrame({label: first.yearly["benchmark"]}
                           | {r.name: r.yearly["return"] for r in results.values()})
    values = pd.DataFrame({r.name: r.yearly["end_value"] for r in results.values()})
    taxes = pd.DataFrame({r.name: r.yearly["tax"] for r in results.values()})
    drawdowns = pd.DataFrame({r.name: r.yearly["max_drawdown"] for r in results.values()})

    parts = [
        f"## Inside the {years}-year window",
        "",
        "Annual columns are the average of the 12 check-month configurations; the trade "
        "logs below show one of them.",
        "",
        "### Return by year",
        "",
        md_table(as_percent(returns), "Year"),
        "",
        "### Value at each year end",
        "",
        md_table(as_money(values), "Year"),
        "",
        "### Tax by year",
        "",
        md_table(as_money(taxes), "Year"),
        "",
        "A quiet row means the top N did not change that year, so nothing was sold and "
        "nothing was owed.",
        "",
        "### Deepest fall within each year",
        "",
        md_table(as_percent(drawdowns), "Year"),
        "",
        "### What each strategy traded",
        "",
    ]

    for (_, check), result in results.items():
        trades = result.trades[result.trades.kind == "swap"]
        label = (f"{result.name}, January check" if check == "annual" else result.name)
        parts += [
            f"<details><summary><b>{label}</b> — "
            f"{len(trades)} changes, ending in "
            f"{', '.join(result.holdings)}</summary>",
            "",
        ]
        if trades.empty:
            parts.append("The list never changed.")
        else:
            log = trades[["date", "sold", "bought", "proceeds"]].copy()
            log["proceeds"] = as_money(log[["proceeds"]])["proceeds"]
            log.columns = ["Date", "Sold", "Bought", "Proceeds"]
            parts.append(md_table(log.set_index("Date"), "Date"))
        parts += ["", "</details>", ""]
    return parts


def comparison_document(windows: list[tuple], data: snap.Snapshot, args, tax) -> str:
    """One markdown page comparing every strategy over each requested window."""
    label = "S&P 500" if args.benchmark in {"SPY", "VOO", "IVV"} else args.benchmark
    spans = " and ".join(f"{y} years" for y, *_ in windows)

    parts = [
        f"# Holding the top companies by market cap: {spans} compared",
        "",
        f"What ${args.total:,.0f} spread across the N largest US companies by market cap "
        f"would have done, when the portfolio trades only on the days that top-N list "
        f"actually changes. Seven variants and one benchmark, over {spans}, all starting "
        f"from the same money.",
        "",
        "## How each strategy works",
        "",
        f"On day one, ${args.total:,.0f} is split equally across the N largest companies "
        "by market cap. On the first trading day of every month, or of every year for "
        "the annual variants, the list is ranked again using the previous day's market "
        "caps. If the top N is unchanged, nothing happens. If it changed, only the names "
        "that dropped out are sold, and their proceeds are split across the names that "
        "replaced them. A company that stays on the list is never trimmed, so it keeps "
        "compounding and never realizes a gain.",
        "",
        "An annual check can fall in any month, and which one it is turns out to matter, "
        "so every annual strategy is run 12 times, once per check month, and every number "
        "reported for it is the average of those 12 runs. Monthly strategies have no such "
        "choice to make and are run once.",
        "",
        "## Assumptions",
        "",
        "| | |",
        "|---|---|",
        f"| Stake | ${args.total:,.0f} on day one, split equally across the N positions, "
        f"no further contributions |",
        f"| Universe | {len(data.universe)} of the largest US companies |",
        "| Annual variants | averaged over 12 runs, one per month the yearly check "
        "falls in |",
        f"| Tax | {'; '.join(describe_tax(args, tax)[:2])} |",
        f"| Benchmark | {label} bought once and held, same ${args.total:,.0f} |",
        f"| Data | {data.describe()} |",
        "",
        "Tax is settled every calendar year on the gains that year's trades actually "
        "realized, with short-term and long-term lots tracked first in, first out and "
        "losses carried forward. It is paid from outside the portfolio, so no holding is "
        "ever sold to cover a tax bill. Gains still unrealized at the end are untaxed, so "
        "every final value below carries a future liability.",
        "",
    ]

    parts += ["## Results", ""]
    for years, results, benchmark, per_anchor in windows:
        parts += results_section(results, benchmark, args, years, label, per_anchor)
    parts += insight_section(windows[0][1], args, windows[0][0], label)

    parts += [
        "## Caveats",
        "",
        f"- The candidate pool is {len(data.universe)} large US companies, so a company "
        "that reached the top N without being in that pool would be missed. Citigroup "
        "and Bank of America are absent because their crisis-era share counts predate "
        "usable filings.",
        "- Market caps use unadjusted prices times share counts merged from SEC EDGAR, "
        "yfinance and a few documented pre-2009 anchors. Share feeds glitch around split "
        "dates and are filtered, not perfect, so a ranking near a boundary can be off by "
        "a day or a place.",
        "- Prices include reinvested dividends, but dividend income tax is not modeled.",
        "- Tax uses 2025 brackets for every year, the standard deduction only, and a "
        "simplified state model.",
        "- Rankings use the previous day's caps, so there is no look-ahead, but trades "
        "fill at the close with no slippage and "
        + (f"a {args.fees:.2%} fee." if args.fees else "no commission."),
        "- Annual results average 12 check months, so no single one of them is what any "
        "one investor would have experienced; the spread table shows how wide that is.",
        "- Two overlapping windows of one universe, in one ordering of history. A "
        "different decade would rank these differently.",
        "",
        "Past results do not predict future results. Not investment advice.",
        "",
        "---",
        "",
        "Regenerate with:",
        "",
        "```bash",
        f"python simulate.py report --years {','.join(str(y) for y, *_ in windows)} "
        f"--total {args.total:,.0f}".replace(",000", "000"),
        "```",
        "",
    ]
    return "\n".join(parts)


# ------------------------------------------------------------------ commands

def load_data(args) -> snap.Snapshot:
    data = snap.load()
    if args.universe:
        missing = [s for s in args.universe if s not in data.caps.columns]
        if missing:
            raise SystemExit(f"Not in the snapshot: {', '.join(missing)}. "
                             f"Rebuild with: python simulate.py snapshot --universe ...")
        data = snap.Snapshot(data.prices, data.caps[args.universe], data.meta)
    if args.benchmark not in data.prices.columns:
        raise SystemExit(f"Benchmark {args.benchmark} is not in the snapshot.")
    return data


def cmd_run(args) -> None:
    data = load_data(args)
    tax = build_tax(args)
    print_header(data, args, tax)
    summary, results, benchmarks = run_grid(data, args)

    columns = ["years", "top", "strategy", "start", "invested", "final", "profit",
               "tax", "net_final", "cagr", "after_tax_cagr", "max_dd", "changes"]
    print(fmt(summary[columns]).to_string(index=False))

    single = len(results) == 1
    if single or args.yearly:
        for (years, _, _), result in results.items():
            print_yearly(result, args, f"year by year: {result.name}, {years}-year window")
            if single or args.trades:
                print_trades(result)

    if args.out:
        write_outputs(Path(args.out), summary, results, benchmarks, args)
    print()


def write_outputs(out: Path, summary, results, benchmarks, args) -> None:
    out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out / "summary.csv", index=False)
    yearly = pd.concat(
        [r.yearly.assign(window=f"{k[0]}y", strategy=r.name) for k, r in results.items()]
    )
    yearly.to_csv(out / "yearly.csv")
    trades = pd.concat(
        [r.trades.assign(window=f"{k[0]}y", strategy=r.name) for k, r in results.items()]
    )
    trades.to_csv(out / "trades.csv", index=False)

    from market.plots.topn import value_chart

    # One chart, so plot the longest window; shorter ones live in the CSVs.
    longest = max(k[0] for k in results)
    plotted = {k: r for k, r in results.items() if k[0] == longest}
    widest = max(k[1] for k in plotted)
    figure = value_chart(list(plotted.values()), benchmarks[(longest, widest)],
                         title=f"Portfolio value over {longest} years (net of tax paid)")
    figure.write_html(out / "chart.html", include_plotlyjs="cdn")
    print(f"\nwrote summary.csv, yearly.csv, trades.csv, chart.html to {out}")


def cmd_report(args) -> None:
    if args.total is None:
        args.total = args.per_stock  # every strategy starts from the same money
    data = load_data(args)
    tax = build_tax(args)
    out = Path(args.dir)
    out.mkdir(parents=True, exist_ok=True)

    windows = []
    for years in args.years:
        results, per_anchor = {}, {}
        for n, check in REPORT_STRATEGIES:
            anchors = MONTHS if check == "annual" else ("JAN",)
            runs = {}
            for anchor in anchors:
                cell = argparse.Namespace(**{**vars(args), "top": [n], "check": [check],
                                             "years": [years], "anchor": anchor})
                _, cells, _ = run_grid(data, cell)
                runs[anchor] = cells[(years, n, check)]
            name = strategy_name(n, check, "JAN")
            results[(n, check)] = (average_anchors(runs, name) if check == "annual"
                                   else runs["JAN"])
            if check == "annual":
                per_anchor[name] = runs
        span = next(iter(results.values())).value.index
        benchmark = buy_and_hold(data.window(span[0], span[-1]).prices[args.benchmark],
                                 args.total, args.benchmark, tax, args.liquidate)
        windows.append((years, results, benchmark, per_anchor))

    path = out / "README.md"
    path.write_text(comparison_document(windows, data, args, tax))
    for stale in out.glob("top-*.md"):
        stale.unlink()
    print(f"wrote {path}")


def cmd_snapshot(args) -> None:
    universe = args.universe or None
    print("fetching prices and share counts (yfinance + SEC EDGAR), this takes a minute ...")
    data = snap.build(universe=universe, start=args.since)
    print(f"wrote {snap.SNAPSHOT_PATH.relative_to(HERE)} "
          f"({snap.SNAPSHOT_PATH.stat().st_size / 1e6:.1f} MB): {data.describe()}")


def cmd_states(args) -> None:
    print("known --state values (NONE = federal tax only):")
    print("  " + "  ".join(STATES))


# ------------------------------------------------------------------ arguments

def symbols(value: str) -> list[str]:
    return [s.strip().upper() for s in value.split(",") if s.strip()]


def ints(value: str) -> list[int]:
    return [int(v) for v in value.replace(" ", "").split(",") if v]


def checks(value: str) -> list[str]:
    picked = [v.strip().lower() for v in value.split(",") if v.strip()]
    if picked == ["both"]:
        return list(CHECK_FREQ)
    unknown = [p for p in picked if p not in CHECK_FREQ]
    if unknown:
        raise argparse.ArgumentTypeError("--check must be monthly, annual or both")
    return picked


def add_simulation_arguments(parser: argparse.ArgumentParser, grid: bool = True) -> None:
    if grid:
        parser.add_argument("-n", "--top", type=ints, default=[3],
                            help="how many top-cap stocks to hold, e.g. 3 or 1,2,3,5")
        parser.add_argument("-c", "--check", type=checks, default=["monthly"],
                            help="how often to re-rank: monthly, annual or both")
    parser.add_argument("-y", "--per-stock", type=float, default=10_000.0,
                        help="dollars invested in each stock at the start")
    parser.add_argument("-t", "--total", type=float,
                        help="total dollars split equally across the top N, "
                             "instead of --per-stock")
    parser.add_argument("-z", "--years", type=ints, default=[10],
                        help="how far back to start, e.g. 10 or 5,10,15,20")
    parser.add_argument("--anchor", default="JAN", choices=MONTHS,
                        help="month an annual check falls in (default JAN)")
    parser.add_argument("--start", help="explicit start date, overrides --years")
    parser.add_argument("--end", help="end date (default: last day in the snapshot)")

    tax = parser.add_argument_group("tax")
    tax.add_argument("--income", type=float, default=120_000.0,
                     help="your other taxable income, used to place gains in brackets")
    tax.add_argument("--filing", choices=FILINGS, default="single")
    tax.add_argument("--state", default="CA",
                     help="two-letter state, or NONE for federal only (see: states)")
    tax.add_argument("--st-rate", type=float, help="flat short-term rate, overrides brackets")
    tax.add_argument("--lt-rate", type=float, help="flat long-term rate, overrides brackets")
    tax.add_argument("--tax-free", action="store_true",
                     help="Roth IRA / 401k: no capital-gains tax at all")
    tax.add_argument("--liquidate", action="store_true",
                     help="sell everything on the last day so unrealized gains are taxed too")

    other = parser.add_argument_group("other")
    other.add_argument("--fees", type=float, default=0.0,
                       help="per-trade cost as a fraction, e.g. 0.001")
    other.add_argument("--benchmark", default="SPY", help="ticker to compare against")
    other.add_argument("--universe", type=symbols, help="restrict the candidate stocks")


def parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="simulate.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="simulate the strategy (default command)")
    add_simulation_arguments(run)
    run.add_argument("--yearly", action="store_true",
                     help="print the year-by-year table for every cell of the grid")
    run.add_argument("--trades", action="store_true", help="print every portfolio change")
    run.add_argument("--out", help="directory for summary.csv, yearly.csv, trades.csv, chart.html")

    report = sub.add_parser("report", help="write one markdown report per strategy")
    add_simulation_arguments(report, grid=False)
    report.add_argument("--dir", default="results", help="directory to write the reports into")
    report.set_defaults(years=[10, 20])

    build = sub.add_parser("snapshot", help="rebuild the offline price/market-cap file")
    build.add_argument("--universe", type=symbols, help="symbols to include")
    build.add_argument("--since", default=snap.DEFAULT_START, help="earliest date to fetch")

    sub.add_parser("states", help="list the state codes accepted by --state")

    commands = {"run", "report", "snapshot", "states", "-h", "--help"}
    if not argv or argv[0] not in commands:
        argv = ["run", *argv]
    args = parser.parse_args(argv)
    args.income_given = any(a.startswith("--income") for a in argv)
    args.tax_given = any(a.startswith(("--income", "--state", "--filing", "--st-rate",
                                       "--lt-rate", "--tax-free")) for a in argv)
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse(list(sys.argv[1:] if argv is None else argv))
    pd.set_option("display.width", 220, "display.max_columns", 40)
    {"run": cmd_run, "report": cmd_report,
     "snapshot": cmd_snapshot, "states": cmd_states}[args.command](args)


if __name__ == "__main__":
    main()
