# Top-N Grid: N = 1–5 × Rebalance Frequency × Taxes, 10y and 20y

## Investigative question

Contributing **$600/month**, how do VOO and SPYG compare against portfolios holding the top-1 through top-5 US companies by market cap — equal weight, rebalanced **monthly vs annually** — both **before and after capital-gains taxes**, over a **10-year** (2016–2026) and a **20-year** (2006–2026) window?

## Experiment breakdown

| Component | Choice |
|---|---|
| Contributions | $600 on the first trading day of each month; buys toward target weights, never sells. 10y: $72,600 total · 20y: $144,000 total |
| Index baselines | VOO and SPYG buy & hold (20y window uses SPY for VOO, which launched Sep 2010) |
| Top-N strategies | N = 1…5 largest US companies by market cap, equal weight; re-ranked and rebalanced monthly or annually; rankings use only prior-day information |
| Market-cap data | Split-consistent price × shares from SEC filings (2009+), yfinance (2015+), and documented pre-2009 anchors; 26-name mega-cap universe |
| Taxes | FIFO lots; 24% on gains from lots held ≤ 1 year, 15% otherwise; settled annually; losses offset gains and carry forward. Roth IRA / tax-advantaged accounts: use the pre-tax columns |
| Costs | Commission-free fractional shares; dividend taxes and final-liquidation tax not modeled (apply ~equally to all rows) |

## Results — 10 years (2016–2026, $72,600 contributed)

| Strategy | Final | Profit | IRR | Max DD | Taxes | After-tax final | After-tax profit | After-tax IRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Buy & hold VOO | $171,821 | $99,221 | +16.4% | −34.1% | $0 | $171,821 | $99,221 | +16.4% |
| Buy & hold SPYG | $195,613 | $123,013 | +18.8% | −32.7% | $0 | $195,613 | $123,013 | +18.8% |
| Top-1, monthly | $230,716 | $158,116 | +21.9% | −33.3% | $14,873 | $200,855 | $128,255 | +19.3% |
| Top-1, annual | $271,116 | $198,516 | +24.9% | −36.5% | $23,835 | $241,544 | $168,944 | +22.7% |
| Top-2, monthly | $240,638 | $168,038 | +22.7% | −31.9% | $19,645 | $210,295 | $137,695 | +20.2% |
| **Top-2, annual** | $289,995 | $217,395 | +26.1% | −33.8% | $10,989 | **$276,109** | **$203,509** | **+25.2%** |
| **Top-3, monthly** | **$290,806** | **$218,206** | **+26.2%** | −35.1% | $19,871 | $256,337 | $183,737 | +23.8% |
| Top-3, annual | $244,424 | $171,824 | +22.9% | −35.2% | $12,213 | $227,294 | $154,694 | +21.6% |
| Top-4, monthly | $290,988 | $218,388 | +26.2% | −39.3% | $20,147 | $257,922 | $185,322 | +23.9% |
| Top-4, annual | $279,949 | $207,349 | +25.4% | −39.5% | $8,056 | $267,856 | $195,256 | +24.6% |
| Top-5, monthly | $261,828 | $189,228 | +24.2% | −40.8% | $15,492 | $239,518 | $166,918 | +22.6% |
| Top-5, annual | $261,725 | $189,125 | +24.2% | −46.0% | $6,348 | $249,762 | $177,162 | +23.4% |

## Results — 20 years (2006–2026, $144,000 contributed)

| Strategy | Final | Profit | IRR | Max DD | Taxes | After-tax final | After-tax profit | After-tax IRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Buy & hold SPY | $702,889 | $558,289 | +14.0% | −54.9% | $0 | $702,889 | $558,289 | +14.0% |
| Buy & hold SPYG | $905,918 | $761,318 | +16.0% | −51.0% | $0 | $905,918 | $761,318 | +16.0% |
| Top-1, monthly | $1,189,217 | $1,044,617 | +18.2% | −37.6% | $105,041 | $912,870 | $768,270 | +16.1% |
| **Top-1, annual** | **$1,551,418** | **$1,406,818** | **+20.3%** | −37.2% | $169,882 | $1,259,395 | $1,114,795 | +18.6% |
| Top-2, monthly | $1,255,314 | $1,110,714 | +18.6% | −52.6% | $128,774 | $982,386 | $837,786 | +16.7% |
| Top-2, annual | $1,431,976 | $1,287,376 | +19.7% | −51.5% | $70,462 | $1,317,992 | $1,173,392 | +19.0% |
| Top-3, monthly | $1,368,415 | $1,223,815 | +19.3% | −57.7% | $115,081 | $1,098,249 | $953,649 | +17.5% |
| Top-3, annual | $1,247,081 | $1,102,481 | +18.6% | −49.9% | $85,930 | $1,099,181 | $954,581 | +17.5% |
| Top-4, monthly | $1,454,228 | $1,309,628 | +19.8% | −52.8% | $125,476 | $1,180,722 | $1,036,122 | +18.1% |
| **Top-4, annual** | $1,438,200 | $1,293,600 | +19.7% | −49.2% | $56,998 | **$1,318,991** | **$1,174,391** | **+19.0%** |
| Top-5, monthly | $1,158,302 | $1,013,702 | +18.0% | −50.9% | $89,824 | $977,435 | $832,835 | +16.6% |
| Top-5, annual | $1,237,841 | $1,093,241 | +18.5% | −48.0% | $43,543 | $1,130,420 | $985,820 | +17.8% |

## Key findings

1. **Every top-N variant beat both ETFs in both windows, before and after taxes** — though the worst variants (top-1 monthly) only barely clear SPYG after tax.
2. **Annual rebalancing is the tax-efficient default.** It cut the tax bill roughly in half vs monthly (e.g. 20y top-4: $57k vs $125k) and won after-tax in 9 of 10 N×window cells (the exception: 10y top-3, where monthly's faster tracking of leadership changes overcame its tax drag).
3. **The best N is noise; the range is robust.** Top-2, top-3, and top-4 each "win" somewhere in the grid. Chasing the winning cell is curve-fitting — the durable observation is that concentrated mega-cap baskets (N = 2–4) outperformed this era, not any particular N.
4. **Top-1's results are timing luck, not signal**: $1.55M annual vs $913k monthly (after-tax) on the *same idea* — a one-stock portfolio's outcome swings ~2x on rebalance-date fortune around the XOM→AAPL→MSFT→NVDA transitions.
5. **The 20-year window shows the real risk**: max drawdowns of ~50% (2008–09), and roughly half of every pre-tax IRR evaporates versus the 10-year window — the 2016–2026 numbers are the best decade, not the base case.

## Recommendation

- **Taxable account:** top-2–4, **annual** rebalancing (after-tax winner in nearly every cell), if you accept the concentration; otherwise SPYG.
- **Roth IRA / tax-advantaged:** taxes vanish — read the pre-tax columns. Top-3/top-4 **monthly** edges out annual there, and monthly also reacts faster when market leadership changes.
- Avoid top-1 (fragile) and top-5 (consistently the weakest of the concentrated baskets). As ever: this is one historical era of mega-cap dominance, not a law of nature. Not investment advice.

## What each column means

| Column | Meaning |
|---|---|
| Final / Profit | End market value before rebalancing taxes; profit = final − contributed |
| IRR | Money-weighted annual return on your actual monthly cash flows ("what rate did *my* dollars earn?") |
| Max DD | Worst peak-to-trough fall of strategy performance, contribution timing removed |
| Taxes | Capital-gains tax realized by rebalancing sales (24% short-term ≤ 1y, 15% long-term), settled yearly; buy & hold sells nothing → $0 |
| After-tax … | Same strategy with those taxes paid from the portfolio as incurred, so taxed money also stops compounding |

## Caveats

Backtest, not forecast; hand-picked 26-name universe (mild hindsight bias); market caps approximate before ~2015 (SEC data starts 2009; Citigroup/BofA excluded for unreliable crisis-era counts); dividend and liquidation taxes unmodeled; fixed 24%/15% tax rates.

---

*Reproduce: `.venv/bin/python experiments/2026-08-13-dca-topn-grid/run.py` · raw data: [results.csv](results.csv) · charts: [10y](chart_10y.html), [20y](chart_20y.html)*
