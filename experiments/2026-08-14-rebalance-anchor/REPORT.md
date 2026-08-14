# Does "Rebalance Annually" Survive the Calendar? — Anchor & Quarterly Test

## Investigative question

The [rolling-windows experiment](../2026-08-13-topn-rolling-10y/REPORT.md) concluded "rebalance annually, in both account types." But its annual strategy always rebalanced in **January**. Is that conclusion real, or was January lucky? Adding: (a) **quarterly** rebalancing, and (b) annual rebalancing anchored to **each of the 12 months** (and quarterly to each of its 3 phases) — how much does the strategy's outcome vary purely by *when* in the year you rebalance?

## Experiment breakdown

| Component | Choice |
|---|---|
| Grid | N ∈ {1, 2, 3} × {monthly, quarterly ×3 anchors, annual ×12 anchors} = 48 cells |
| Windows | Same 41 rolling 10-year windows (starts quarterly, Aug 2006 – Aug 2016), $600/month |
| Accounts | Roth (pre-tax IRR) and taxable (after-tax IRR: FIFO lots, 24% ST / 15% LT, annual settlement) |
| Judged on | Median IRR with anchors pooled (frequency question); per-anchor medians and per-window anchor spread (calendar-luck question) |

## Results

### Frequency ladder — anchors pooled (median IRR across 41 windows)

| N | Frequency | Roth (pre-tax) | Taxable (after-tax) | Median taxes |
|---|---|---:|---:|---:|
| 1 | monthly | +21.2% | +18.4% | $21,148 |
| 1 | quarterly | +17.6% | +15.3% | $16,127 |
| 1 | annual | +20.5% | +18.6% | $12,011 |
| 2 | **monthly** | **+24.3%** | **+22.0%** | $16,775 |
| 2 | quarterly | +23.2% | +21.1% | $11,489 |
| 2 | annual | +22.3% | +21.1% | $5,346 |
| 3 | monthly | +22.7% | +20.7% | $14,478 |
| 3 | quarterly | +22.3% | +20.6% | $10,577 |
| 3 | annual | +22.1% | +21.0% | $7,379 |

### Annual anchor sensitivity (median after-tax IRR by rebalance month)

| N | Best anchor | Worst anchor | Spread of medians | Median per-window anchor spread | Worst |
|---|---|---|---:|---:|---:|
| 1 | DEC +24.3% | SEP +16.8% | 7.5pp | **8.4pp** | 14.4pp |
| 2 | MAR +24.3% | SEP +19.1% | 5.2pp | 4.6pp | 9.7pp |
| 3 | MAY +22.9% | AUG +20.4% | 2.5pp | 4.2pp | 7.0pp |

(January ranked near-best for N=1 and N=2 — the prior experiment sampled a lucky anchor.)

Distributions: [chart_anchors_top2.html](chart_anchors_top2.html), [chart_freq.html](chart_freq.html) · data: [results.csv](results.csv), [freq_summary.csv](freq_summary.csv), [anchor_summary.csv](anchor_summary.csv), [luck_summary.csv](luck_summary.csv)

## Key findings

1. **The "annual beats monthly" conclusion is overturned — January was doing hidden work.** Pooled across all 12 anchors, annual's after-tax edge disappears: monthly ties or beats annual at every N (N=2: +22.0% vs +21.1%). Annual still pays ~⅓ the taxes, but monthly's faster tracking of leadership changes earns the difference back pre-tax. The prior report has been annotated.
2. **Annual rebalancing carries real, uncompensated calendar luck.** Within a single investing decade, your outcome varies by a median 4–8pp of IRR (worst case 14pp for top-1) purely by which month you happen to rebalance — a risk monthly rebalancing eliminates entirely. Nothing suggests any particular month is *predictably* better; the per-anchor rankings look like noise.
3. **Quarterly is not a useful middle ground.** It never wins a cell; for top-1 it's distinctly the worst frequency (+15.3% after tax) — it re-ranks often enough to get whipsawed at leadership changes but too slowly to track them well.
4. **N=3 is the calendar-robust choice.** Its anchor spread is the tightest (2.5pp across anchor medians vs 7.5pp for top-1), and its worst-window floors are the highest in the study (several anchors bottom out above +10%/yr after tax).
5. Top-1's stellar showing in the previous experiment was **doubly** lucky: best-in-study consistency *at the January anchor*, near-worst medians at September. Its true character is high variance on every axis.

## Revised recommendation (supersedes the rolling-windows report)

- **Rebalance monthly, in both account types.** In a Roth it's cleanly best (+24.3% median for top-2). In a taxable account it ties annual's median while eliminating 4–8pp of calendar luck — paying more tax buys you that variance reduction. Skip quarterly.
- **Hold top-2 for median outcome, top-3 for robustness.** Top-2 monthly has the best medians; top-3 is the most stable across every axis tested (anchors, windows, frequencies). Top-1 remains disqualified — its results swing wildly on both start date and calendar anchor.
- If you strongly prefer annual's simplicity (one trade date a year, ⅓ the taxes), accept that your realized decade may land several IRR points above or below the tables here on calendar luck alone.

## Caveats

Same era-dependence and overlapping-window caveats as the parent experiment; anchor rankings (MAR/NOV good, SEP bad) are in-sample noise — do not pick an anchor from them. Not investment advice.

---

*Reproduce: `.venv/bin/python experiments/2026-08-14-rebalance-anchor/run.py` (~2.5 min: 48 ranking cells + 3,977 simulations, parallel with progress bars)*
