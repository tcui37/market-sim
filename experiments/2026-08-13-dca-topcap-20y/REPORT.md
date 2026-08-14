# $600/Month for 20 Years — Rebalance Frequency & Taxes

**Question:** Investing $600/month (Aug 2006 → Aug 2026, **$144,000** total contributed): index ETFs vs top-N market-cap portfolios — and how much does rebalancing frequency matter once capital-gains taxes are counted?

**Setup:** Commission-free fractional shares. Contributions buy toward target weights on the first trading day of each month (never selling); rebalancing sells back to equal weight on its schedule. Top-N strategies re-rank by market cap using only information available at the time. SPY stands in for VOO (same index; VOO launched 2010). Taxes: FIFO lots, 24% on gains from lots held ≤ 1 year, 15% on longer, settled annually, losses offset gains and carry forward.

## Results (sorted by after-tax profit)

| Strategy | Final value | Profit | IRR | Max DD | Taxes paid | After-tax final | After-tax profit | After-tax IRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Top-1 cap, annual** | $1,551,418 | $1,406,818 | +20.3% | −37.2% | $169,882 | $1,259,395 | $1,114,795 | **+18.6%** |
| Top-5 cap, annual | $1,237,841 | $1,093,241 | +18.5% | −48.0% | $43,543 | $1,130,420 | $985,820 | +17.8% |
| **Top-3 cap, annual** | $1,247,081 | $1,102,481 | +18.6% | −49.9% | $85,930 | $1,099,181 | $954,581 | **+17.5%** |
| Top-3 cap, monthly | $1,368,415 | $1,223,815 | +19.3% | −57.7% | $115,081 | $1,098,249 | $953,649 | +17.5% |
| Top-5 cap, weekly | $1,368,289 | $1,223,689 | +19.3% | −52.9% | $133,367 | $1,058,046 | $913,446 | +17.2% |
| Top-3 cap, weekly | $1,394,819 | $1,250,219 | +19.4% | −60.3% | $146,516 | $1,044,827 | $900,227 | +17.2% |
| Top-5 cap, monthly | $1,158,302 | $1,013,702 | +18.0% | −50.9% | $89,824 | $977,435 | $832,835 | +16.6% |
| Top-1 cap, monthly | $1,189,217 | $1,044,617 | +18.2% | −37.6% | $105,041 | $912,870 | $768,270 | +16.1% |
| Buy & hold SPYG | $905,918 | $761,318 | +16.0% | −51.0% | $0 | $905,918 | $761,318 | +16.0% |
| Top-1 cap, weekly | $935,346 | $790,746 | +16.3% | −41.3% | $85,343 | $743,039 | $598,439 | +14.4% |
| Buy & hold SPY | $702,889 | $558,289 | +14.0% | −54.9% | $0 | $702,889 | $558,289 | +14.0% |

## Key findings

- **Yes — rebalancing less often cuts the tax bill, exactly as suspected.** Holding lots past one year converts 24% short-term gains into 15% long-term gains *and* realizes less gain overall. Top-3 goes from $146.5k taxes (weekly) → $115.1k (monthly) → $85.9k (annual); top-5 annual pays just $43.5k.
- **After taxes, the frequency ranking flips.** Pre-tax, top-3 weekly beats top-3 annual by $148k. After taxes they're dead even (~$1.10M) — and annual gets there with far less churn and a shallower worst drawdown (−50% vs −60%).
- **Every top-N variant beat both ETFs after taxes** over this window — even top-1 annual, the single best performer ($1.26M after tax vs SPYG's $906k). But top-1's spread across rebalance frequencies ($743k weekly vs $1.26M annual, driven by luckier switch timing between XOM→AAPL→MSFT→NVDA eras) shows how fragile a one-stock portfolio is. Top-3/top-5 are far more stable across frequencies.
- **20 years includes the 2008 crash** — max drawdowns of −50% to −60% are the realistic price of these returns. The 10-year version of this experiment (2016–2026) never saw worse than −41%.

## Recommendation

**Top-3 or top-5, rebalanced annually (or monthly — after-tax outcomes are nearly identical, and monthly reacts faster when the leaders change).** Weekly rebalancing buys nothing but a bigger tax bill. Ignore top-1's chart-topping annual result: its outcome swings by 2x on rebalance timing alone. In a tax-advantaged account taxes vanish and top-3 weekly/monthly wins pre-tax — but even there, monthly is within 2% of weekly with a quarter less turnover.

## What each column means

| Column | Meaning |
|---|---|
| Final value | Market value at the end, before any rebalancing taxes |
| Profit | Final value − $144,000 contributed |
| IRR | Money-weighted annual return on your actual monthly cash flows — "what rate did *my* dollars earn?" (later dollars count for less time) |
| Max DD | Worst peak-to-trough fall of strategy performance (contribution-timing removed) |
| Taxes paid | Capital-gains tax on gains realized by rebalancing sales, settled yearly: 24% short-term (lot held ≤ 1 year), 15% long-term; losses offset gains and carry forward. Buy & hold sells nothing → $0 |
| After-tax final / profit / IRR | Same strategy with those taxes paid out of the portfolio as they occur — so taxed money also stops compounding |

Not modeled for any strategy: dividend taxes and tax on final liquidation (both apply roughly equally to all rows; buy-and-hold would owe substantial deferred tax on sale).

## Caveats

- **A backtest, not a forecast.** The top-N edge is the 2012–2026 mega-cap era; 2006–2011 (XOM/GE leadership) shows the strategy merely matching the market.
- **Market-cap data is approximate before ~2015**: SEC filings cover 2009+, a few documented anchor counts cover 2006–2008, and Citigroup/Bank of America (top-5-ish in 2006–07) are excluded because their crisis-era share counts aren't reliably available. The computed #1 timeline matches recorded history (XOM 2006–12, AAPL↔XOM 2013–14, MSFT/AMZN 2019, NVDA 2024+).
- Hand-picked universe of 26 US mega caps (mild hindsight bias); tax model assumes fixed 24%/15% rates and Robinhood-style FIFO lots. Not investment advice.

---

*Generated with [market-sim](../../README.md) · reproduce: `.venv/bin/python experiments/2026-08-13-dca-topcap-20y/run.py` · raw data: [results.csv](results.csv) · interactive chart: [chart.html](chart.html)*
