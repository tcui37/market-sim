# Which Top-N, and Monthly vs Annual? — 41 Rolling 10-Year Windows

## Investigative question

For a **10-year, $600/month** plan: which **N** (top-N market cap, equal weight) should you hold, and should you rebalance **monthly or annually** — in a **Roth IRA** (no taxes) and in a **taxable account** (capital-gains taxes)? Judged not on one lucky start date, but across **every rolling 10-year window** the data supports.

## Experiment breakdown

| Component | Choice |
|---|---|
| Windows | 41 ten-year windows, starts every 3 months from Aug 2006 to Aug 2016 (ends Aug 2016 – Aug 2026) |
| Strategies | Top-N for N = 1…5, equal weight, re-ranked & rebalanced monthly or annually; SPY and SPYG buy & hold baselines |
| Contributions | $600 on each month's first trading day (~$72,600/window); buys toward targets, never sells |
| Accounts | Roth IRA → pre-tax IRR (rebalancing is tax-free); Taxable → after-tax IRR (FIFO lots, 24% short-term ≤ 1y / 15% long-term, settled annually, loss carryforward) |
| Data | Market caps from split-consistent price × shares (SEC 2009+, yfinance 2015+, documented 2006-08 anchors); 26-name mega-cap universe; no look-ahead |
| Judged on | Median IRR across windows, worst-window IRR, % of windows beating SPYG, taxes paid, drawdowns |

## Results — aggregates over 41 windows (sorted by after-tax median IRR)

| Strategy | Median IRR (Roth) | Median IRR (taxable) | Worst window (taxable) | Beats SPYG (Roth) | Beats SPYG (taxable) | Median taxes | Median max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Top-2 annual** | **+24.5%** | **+23.8%** | +6.1% | 71% | 71% | $3,587 | −32% |
| **Top-1 annual** | +24.3% | +23.1% | **+9.1%** | **95%** | **93%** | $10,817 | −37% |
| Top-2 monthly | +24.3% | +22.0% | +7.7% | 83% | 73% | $16,775 | −32% |
| Top-4 annual | +22.5% | +21.8% | +8.1% | 85% | 83% | $5,223 | −40% |
| Top-4 monthly | +22.1% | +20.8% | +6.8% | 83% | 78% | $10,765 | −39% |
| Top-3 annual | +22.0% | +20.7% | +8.2% | 85% | 85% | $8,122 | −35% |
| Top-3 monthly | +22.7% | +20.7% | +6.0% | 76% | 71% | $14,478 | −35% |
| Top-1 monthly | +21.2% | +18.4% | +7.0% | 88% | 78% | $21,148 | −38% |
| Top-5 annual | +19.3% | +18.3% | +8.4% | 80% | 78% | $5,495 | −46% |
| Top-5 monthly | +18.5% | +17.3% | +7.5% | 83% | 73% | $10,126 | −41% |
| Buy & hold SPYG | +15.1% | +15.1% | **+11.5%** | — | — | $0 | −33% |
| Buy & hold SPY | +13.3% | +13.3% | +10.5% | — | — | $0 | −34% |

Per-window data: [results.csv](results.csv) · aggregates: [summary.csv](summary.csv) · distributions: [chart_roth.html](chart_roth.html), [chart_taxable.html](chart_taxable.html)

## Key findings

1. **Annual rebalancing wins in both account types.** In the taxable account it wins every N (roughly half the taxes of monthly — e.g. top-2: $3.6k vs $16.8k median). The surprise: even in a **Roth, where taxes don't exist, monthly still doesn't help** — annual's median IRR matches or beats monthly for N = 1, 2, 4, 5 (top-3 is the lone exception, +0.7pp for monthly, within noise). Faster tracking of leadership changes bought nothing on average.
2. **N = 2 has the best median; N = 1 the best consistency.** Top-1 annual beat SPYG in 95% of windows with the highest worst-window IRR (+9.1%) — but a backtest cannot price single-company risk (fraud, disruption, regulation) that simply never struck a #1 mega cap in this sample. Treat its stats as flattered.
3. **N = 5 is reliably the worst basket** (lowest medians, deepest drawdowns at −46%) and top-3/top-4 sit in between. Within N = 2–4, differences are era-noise — don't over-fit the exact N.
4. **Every top-N cell beat SPYG in only 71–95% of windows** — meaning in up to 3 windows out of 10 you'd have trailed a simple ETF after ten years of extra effort. And SPYG's worst window (+11.5%) beats every top-N strategy's worst window: the ETF has the higher floor, the baskets the higher ceiling.
5. **These are overlapping windows of one mega-cap era** — 41 windows ≈ only two independent decades, all of which ended in mega-cap dominance. The medians are era-conditional, not timeless expectations.

## Recommendation

- **Rebalance annually — both accounts.** Taxable: it's strictly better (same or better returns, half the taxes). Roth: monthly buys nothing; annual is one calendar reminder a year.
- **N: hold the top 2 or top 3.** Top-2 annual had the best median outcome ($256k median after-tax on $72.6k contributed, vs SPYG's $160k); top-3 annual gives a bit more diversification at a modest median cost and the same 85% win rate as top-4. Avoid N = 1 (unpriceable single-name risk despite its backtest stats) and N = 5 (consistently worst).
- **Roth vs taxable changes nothing about the choice** — only the expected outcome (taxable keeps ~95% of the Roth result under annual rebalancing, vs ~90% under monthly).
- If a 3-in-10 chance of trailing SPYG after a decade — or a −35% drawdown — would shake you out, hold SPYG (or split core/satellite). Not investment advice.

## Caveats

Overlapping windows overstate sample size; the whole period is one mega-cap regime. Universe is hand-picked (26 names, mild hindsight); market caps approximate pre-2015; fixed 24%/15% tax rates; dividend and liquidation taxes unmodeled (≈equal across rows).

---

*Reproduce: `.venv/bin/python experiments/2026-08-13-topn-rolling-10y/run.py` (parallel, ~40s; progress bars included)*
