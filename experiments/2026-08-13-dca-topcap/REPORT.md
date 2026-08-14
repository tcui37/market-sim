# $600/Month for 10 Years — Strategy Comparison

**Question:** Investing $600/month (Aug 2016 → Aug 2026, $72,600 total contributed), which strategy wins?

**Setup:** Commission-free fractional shares (Robinhood-style). Contributions invested on the first trading day of each month. Top-N strategies re-rank by market cap and rebalance to equal weight every Monday, using only information available at the time (no look-ahead). Prices are split/dividend-adjusted; market caps are computed from historical share counts.

## Results

| Strategy | Final value | Profit | Return (IRR) | Max drawdown |
|---|---:|---:|---:|---:|
| Buy & hold VOO | $171,821 | $99,221 | +16.4%/yr | −34.1% |
| Buy & hold SPYG | $195,613 | $123,013 | +18.8%/yr | −32.7% |
| Top-1 market cap, weekly | $207,823 | $135,223 | +20.0%/yr | −41.2% |
| **Top-3 market cap, weekly** 🏆 | **$298,192** | **$225,592** | **+26.6%/yr** | −35.1% |
| Top-5 market cap, weekly | $294,299 | $221,699 | +26.4%/yr | −40.2% |

With 0.1%/trade costs the ranking is unchanged (top-3 loses ~$5k to turnover).

## Key findings

- **Top-3 equal-weight won decisively** — $126k more than VOO on identical contributions, while drawing down *less* than top-1 or top-5.
- **Top-1 is strictly dominated**: it whipsaws during leadership changes (2019, 2024–25) for more risk and less return.
- **SPYG beat VOO by $24k** — growth tilt paid off this decade — with zero maintenance.
- The computed #1-market-cap timeline matches history (AAPL 2016–18 → MSFT/AMZN 2019 → AAPL 2020–24 → NVDA from late 2024), validating the rankings.

## Recommendation

- **Tax-advantaged account (IRA) + tolerance for 3-stock concentration and ~40% drawdowns:** top-3 market cap is what the data supports.
- **Taxable account:** buy & hold SPYG — weekly rebalancing realizes short-term gains that would erode most of top-3's edge after taxes.
- **Middle path:** SPYG core + top-3 satellite.

## Caveats

This is a backtest of an exceptional decade, not an expectation — the top-3 edge *is* the era of mega-cap dominance, and VOO's 15.4%/yr is itself well above the ~10% long-run average (at 10%, this plan ends near $124k). The candidate universe is hand-picked mega caps (mild hindsight bias), and taxes are not modeled. Not investment advice.

---

*Generated with [market-sim](../../README.md) · reproduce: `.venv/bin/python experiments/2026-08-13-dca-topcap/run.py` · raw data: [results.csv](results.csv) · interactive chart: [chart.html](chart.html)*
