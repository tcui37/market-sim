# Holding the top companies by market cap: 10 years and 20 years compared

What $10,000 spread across the N largest US companies by market cap would have done, when the portfolio trades only on the days that top-N list actually changes. Seven variants and one benchmark, over 10 years and 20 years, all starting from the same money.

## How each strategy works

On day one, $10,000 is split equally across the N largest companies by market cap. On the first trading day of every month (or every January, for the annual variants) the list is ranked again using the previous day's market caps. If the top N is unchanged, nothing happens. If it changed, only the names that dropped out are sold, and their proceeds are split across the names that replaced them. A company that stays on the list is never trimmed, so it keeps compounding and never realizes a gain.

## Assumptions

| | |
|---|---|
| Stake | $10,000 on day one, split equally across the N positions, no further contributions |
| Universe | 50 of the largest US companies |
| Tax | federal + CA brackets, single, other income $120,000; next dollar of gain: 33.3% short-term, 24.3% long-term (each year is taxed on its own realized gains, so big years cost more) |
| Benchmark | S&P 500 bought once and held, same $10,000 |
| Data | 54 symbols, 2000-01-03 to 2026-09-04, built 2026-09-06 |

Tax is settled every calendar year on the gains that year's trades actually realized, with short-term and long-term lots tracked first in, first out and losses carried forward. It is paid from outside the portfolio, so no holding is ever sold to cover a tax bill. Gains still unrealized at the end are untaxed, so every final value below carries a future liability.

## Results

### 10-year window

2016-09-06 to 2026-09-04 (10.0 years), $10,000 split across the top N on the first day.

- **Top-2 annual** had the highest after-tax annual return, +26.8%, against +15.2% for S&P 500.
- The best monthly variant was **Top-3 monthly** at +25.0% after tax, 1.7 points behind Top-2 annual, and it traded 10 times to that strategy's 2.
- All 7 beat the index, and 3 of them fell further than it did at their worst.
- Tax ranged from $187 (Top-5 monthly) to $20,672 (Top-1 annual); a strategy only owes anything in a year its top N actually changed.

Ranked by after-tax annual return:

| Strategy | Final value | Profit | Tax paid | After tax | Annual return | After-tax annual return | Max drawdown | Changes |
|---|---|---|---|---|---|---|---|---|
| Top-2 annual | $112,766 | $102,766 | $5,750 | $107,016 | +27.4% | +26.8% | -33.4% | 2 |
| Top-3 monthly | $101,063 | $91,063 | $7,869 | $93,194 | +26.0% | +25.0% | -34.0% | 10 |
| Top-1 annual | $111,902 | $101,902 | $20,672 | $91,230 | +27.3% | +24.8% | -36.5% | 3 |
| Top-3 annual | $92,084 | $82,084 | $8,261 | $83,824 | +24.9% | +23.7% | -33.4% | 6 |
| Top-5 monthly | $81,286 | $71,286 | $187 | $81,099 | +23.3% | +23.3% | -37.8% | 22 |
| Top-2 monthly | $95,599 | $85,599 | $15,041 | $80,559 | +25.3% | +23.2% | -32.0% | 18 |
| Top-1 monthly | $88,152 | $78,152 | $13,287 | $74,866 | +24.3% | +22.3% | -33.4% | 12 |
| S&P 500 buy & hold | $41,281 | $31,281 | $0 | $41,281 | +15.2% | +15.2% | -33.7% | 0 |

By strategy:

| Strategy | Final value | Profit | Tax paid | After tax | Annual return | After-tax annual return | Max drawdown | Changes |
|---|---|---|---|---|---|---|---|---|
| Top-1 monthly | $88,152 | $78,152 | $13,287 | $74,866 | +24.3% | +22.3% | -33.4% | 12 |
| Top-2 monthly | $95,599 | $85,599 | $15,041 | $80,559 | +25.3% | +23.2% | -32.0% | 18 |
| Top-3 monthly | $101,063 | $91,063 | $7,869 | $93,194 | +26.0% | +25.0% | -34.0% | 10 |
| Top-5 monthly | $81,286 | $71,286 | $187 | $81,099 | +23.3% | +23.3% | -37.8% | 22 |
| Top-1 annual | $111,902 | $101,902 | $20,672 | $91,230 | +27.3% | +24.8% | -36.5% | 3 |
| Top-2 annual | $112,766 | $102,766 | $5,750 | $107,016 | +27.4% | +26.8% | -33.4% | 2 |
| Top-3 annual | $92,084 | $82,084 | $8,261 | $83,824 | +24.9% | +23.7% | -33.4% | 6 |
| S&P 500 buy & hold | $41,281 | $31,281 | $0 | $41,281 | +15.2% | +15.2% | -33.7% | 0 |

### 20-year window

2006-09-05 to 2026-09-04 (20.0 years), $10,000 split across the top N on the first day.

- **Top-1 annual** had the highest after-tax annual return, +16.1%, against +11.3% for S&P 500.
- The best monthly variant was **Top-5 monthly** at +14.6% after tax, 1.5 points behind Top-1 annual, and it traded 73 times to that strategy's 4.
- All 7 beat the index, and none of them fell further than it did at their worst.
- Tax ranged from $93 (Top-5 monthly) to $51,265 (Top-1 annual); a strategy only owes anything in a year its top N actually changed.

Ranked by after-tax annual return:

| Strategy | Final value | Profit | Tax paid | After tax | Annual return | After-tax annual return | Max drawdown | Changes |
|---|---|---|---|---|---|---|---|---|
| Top-1 annual | $247,486 | $237,486 | $51,265 | $196,221 | +17.4% | +16.1% | -37.3% | 4 |
| Top-5 monthly | $151,895 | $141,895 | $93 | $151,802 | +14.6% | +14.6% | -50.1% | 73 |
| Top-2 annual | $152,586 | $142,586 | $8,690 | $143,896 | +14.6% | +14.3% | -51.5% | 6 |
| Top-1 monthly | $169,228 | $159,228 | $27,741 | $141,486 | +15.2% | +14.2% | -37.7% | 15 |
| Top-3 annual | $146,125 | $136,125 | $12,312 | $133,813 | +14.4% | +13.8% | -49.4% | 12 |
| Top-2 monthly | $143,548 | $133,548 | $24,841 | $118,707 | +14.3% | +13.2% | -49.6% | 30 |
| Top-3 monthly | $124,853 | $114,853 | $7,497 | $117,356 | +13.5% | +13.1% | -54.7% | 46 |
| S&P 500 buy & hold | $84,474 | $74,474 | $0 | $84,474 | +11.3% | +11.3% | -55.2% | 0 |

By strategy:

| Strategy | Final value | Profit | Tax paid | After tax | Annual return | After-tax annual return | Max drawdown | Changes |
|---|---|---|---|---|---|---|---|---|
| Top-1 monthly | $169,228 | $159,228 | $27,741 | $141,486 | +15.2% | +14.2% | -37.7% | 15 |
| Top-2 monthly | $143,548 | $133,548 | $24,841 | $118,707 | +14.3% | +13.2% | -49.6% | 30 |
| Top-3 monthly | $124,853 | $114,853 | $7,497 | $117,356 | +13.5% | +13.1% | -54.7% | 46 |
| Top-5 monthly | $151,895 | $141,895 | $93 | $151,802 | +14.6% | +14.6% | -50.1% | 73 |
| Top-1 annual | $247,486 | $237,486 | $51,265 | $196,221 | +17.4% | +16.1% | -37.3% | 4 |
| Top-2 annual | $152,586 | $142,586 | $8,690 | $143,896 | +14.6% | +14.3% | -51.5% | 6 |
| Top-3 annual | $146,125 | $136,125 | $12,312 | $133,813 | +14.4% | +13.8% | -49.4% | 12 |
| S&P 500 buy & hold | $84,474 | $74,474 | $0 | $84,474 | +11.3% | +11.3% | -55.2% | 0 |

## Inside the 10-year window

### Return by year

| Year | S&P 500 | Top-1 monthly | Top-2 monthly | Top-3 monthly | Top-5 monthly | Top-1 annual | Top-2 annual | Top-3 annual |
|---|---|---|---|---|---|---|---|---|
| 2016 | +3.2% | +8.1% | +3.1% | +4.9% | +3.3% | +8.1% | +3.1% | +4.9% |
| 2017 | +21.7% | +48.5% | +41.1% | +41.0% | +31.8% | +48.5% | +41.1% | +41.0% |
| 2018 | -4.6% | +0.4% | -2.9% | +0.2% | +7.1% | -5.4% | -3.3% | +5.0% |
| 2019 | +31.2% | +54.0% | +69.5% | +58.9% | +43.0% | +58.4% | +75.5% | +57.7% |
| 2020 | +18.3% | +77.3% | +68.4% | +66.7% | +57.3% | +81.5% | +65.7% | +55.7% |
| 2021 | +28.7% | +22.0% | +41.5% | +34.7% | +32.6% | +34.6% | +41.1% | +35.4% |
| 2022 | -18.2% | -26.4% | -27.1% | -29.4% | -33.9% | -26.4% | -27.0% | -28.6% |
| 2023 | +26.2% | +49.0% | +52.7% | +54.0% | +56.3% | +49.0% | +52.5% | +53.9% |
| 2024 | +24.9% | +15.7% | +21.5% | +28.8% | +33.0% | +30.7% | +23.6% | +23.8% |
| 2025 | +17.7% | +4.6% | +9.4% | +17.5% | +21.4% | +9.1% | +18.1% | +15.1% |
| 2026 | +13.5% | +23.7% | +13.2% | +16.2% | +12.0% | +21.7% | +20.3% | +14.0% |

### Value at each year end

| Year | Top-1 monthly | Top-2 monthly | Top-3 monthly | Top-5 monthly | Top-1 annual | Top-2 annual | Top-3 annual |
|---|---|---|---|---|---|---|---|
| 2016 | $10,809 | $10,308 | $10,492 | $10,330 | $10,809 | $10,308 | $10,492 |
| 2017 | $16,048 | $14,542 | $14,789 | $13,617 | $16,048 | $14,542 | $14,789 |
| 2018 | $16,120 | $14,120 | $14,824 | $14,586 | $15,183 | $14,058 | $15,525 |
| 2019 | $24,830 | $23,933 | $23,548 | $20,860 | $24,056 | $24,673 | $24,482 |
| 2020 | $44,013 | $40,310 | $39,244 | $32,812 | $43,670 | $40,873 | $38,123 |
| 2021 | $53,711 | $57,027 | $52,879 | $43,499 | $58,801 | $57,659 | $51,625 |
| 2022 | $39,529 | $41,588 | $37,342 | $28,759 | $43,275 | $42,071 | $36,846 |
| 2023 | $58,902 | $63,525 | $57,493 | $44,956 | $64,484 | $64,173 | $56,706 |
| 2024 | $68,126 | $77,171 | $74,036 | $59,791 | $84,284 | $79,333 | $70,222 |
| 2025 | $71,281 | $84,456 | $86,988 | $72,599 | $91,914 | $93,699 | $80,807 |
| 2026 | $88,152 | $95,599 | $101,063 | $81,286 | $111,902 | $112,766 | $92,084 |

### Tax by year

| Year | Top-1 monthly | Top-2 monthly | Top-3 monthly | Top-5 monthly | Top-1 annual | Top-2 annual | Top-3 annual |
|---|---|---|---|---|---|---|---|
| 2016 | $0 | $0 | $0 | $0 | $0 | $0 | $0 |
| 2017 | $0 | $0 | $0 | $0 | $0 | $0 | $0 |
| 2018 | $1,893 | $463 | $997 | $0 | $0 | $0 | $0 |
| 2019 | $1,258 | $1,267 | $131 | $0 | $1,264 | $371 | $247 |
| 2020 | $2,837 | $1,970 | $242 | $0 | $3,097 | $0 | $338 |
| 2021 | $4,818 | $0 | $895 | $187 | $0 | $0 | $341 |
| 2022 | $0 | $0 | $0 | $0 | $0 | $0 | $157 |
| 2023 | $0 | $0 | $0 | $0 | $0 | $0 | $0 |
| 2024 | $2,481 | $3,571 | $38 | $0 | $0 | $0 | $0 |
| 2025 | $0 | $7,770 | $5,565 | $0 | $0 | $5,379 | $547 |
| 2026 | $0 | $0 | $0 | $0 | $16,311 | $0 | $6,631 |

A quiet row means the top N did not change that year, so nothing was sold and nothing was owed.

### Deepest fall within each year

| Year | Top-1 monthly | Top-2 monthly | Top-3 monthly | Top-5 monthly | Top-1 annual | Top-2 annual | Top-3 annual |
|---|---|---|---|---|---|---|---|
| 2016 | -10.1% | -9.8% | -8.1% | -6.8% | -10.1% | -9.8% | -8.1% |
| 2017 | -8.9% | -7.9% | -7.2% | -6.3% | -8.9% | -7.9% | -7.2% |
| 2018 | -32.9% | -31.9% | -28.8% | -25.2% | -36.5% | -29.4% | -25.2% |
| 2019 | -7.9% | -10.6% | -12.5% | -12.5% | -7.9% | -12.8% | -12.4% |
| 2020 | -28.4% | -29.2% | -25.5% | -26.4% | -31.4% | -29.2% | -29.4% |
| 2021 | -18.6% | -12.3% | -11.6% | -10.6% | -18.6% | -12.7% | -11.3% |
| 2022 | -30.3% | -29.9% | -31.9% | -36.7% | -30.3% | -29.9% | -31.4% |
| 2023 | -14.9% | -12.3% | -9.9% | -9.8% | -14.9% | -12.3% | -10.3% |
| 2024 | -15.3% | -12.4% | -15.3% | -15.3% | -15.4% | -12.4% | -13.3% |
| 2025 | -31.1% | -31.3% | -26.7% | -25.4% | -31.1% | -31.9% | -25.5% |
| 2026 | -19.3% | -18.3% | -13.3% | -15.5% | -19.3% | -12.4% | -13.7% |

### What each strategy traded

<details><summary><b>Top-1 monthly</b> — 12 changes, ending in NVDA</summary>

| Date | Sold | Bought | Proceeds |
|---|---|---|---|
| 2018-12-03 | AAPL | MSFT | $17,789 |
| 2019-02-01 | MSFT | AMZN | $16,312 |
| 2019-03-01 | AMZN | MSFT | $16,768 |
| 2019-11-01 | MSFT | AAPL | $21,567 |
| 2020-03-02 | AAPL | MSFT | $25,326 |
| 2020-07-01 | MSFT | AAPL | $30,087 |
| 2021-11-01 | AAPL | MSFT | $49,641 |
| 2021-12-01 | MSFT | AAPL | $49,839 |
| 2024-02-01 | AAPL | MSFT | $57,167 |
| 2024-08-01 | MSFT | AAPL | $59,270 |
| 2025-06-02 | AAPL | MSFT | $55,004 |
| 2025-07-01 | MSFT | NVDA | $58,585 |

</details>

<details><summary><b>Top-2 monthly</b> — 18 changes, ending in NVDA, AAPL</summary>

| Date | Sold | Bought | Proceeds |
|---|---|---|---|
| 2018-05-01 | GOOGL | AMZN | $6,440 |
| 2018-11-01 | AMZN | MSFT | $6,779 |
| 2019-02-01 | AAPL | AMZN | $8,014 |
| 2019-03-01 | AMZN | AAPL | $8,238 |
| 2019-05-01 | AAPL | AMZN | $9,912 |
| 2019-08-01 | AMZN | AAPL | $9,621 |
| 2020-08-03 | MSFT | AMZN | $14,203 |
| 2020-10-01 | AMZN | MSFT | $14,702 |
| 2024-11-01 | MSFT | NVDA | $29,395 |
| 2025-02-03 | NVDA | MSFT | $25,329 |
| 2025-03-03 | MSFT | NVDA | $23,994 |
| 2025-04-01 | NVDA | MSFT | $23,174 |
| 2025-06-02 | AAPL | NVDA | $38,767 |
| 2025-11-03 | MSFT | AAPL | $31,459 |
| 2026-02-02 | AAPL | GOOGL | $31,602 |
| 2026-03-02 | GOOGL | AAPL | $28,184 |
| 2026-05-01 | AAPL | GOOGL | $29,826 |
| 2026-08-03 | GOOGL | AAPL | $28,901 |

</details>

<details><summary><b>Top-3 monthly</b> — 10 changes, ending in NVDA, AAPL, GOOGL</summary>

| Date | Sold | Bought | Proceeds |
|---|---|---|---|
| 2018-03-01 | MSFT | AMZN | $5,555 |
| 2018-04-02 | AMZN | MSFT | $5,104 |
| 2018-05-01 | GOOGL | AMZN | $4,293 |
| 2018-06-01 | MSFT | GOOGL | $5,836 |
| 2018-09-04 | GOOGL | MSFT | $6,229 |
| 2019-12-02 | AMZN | GOOGL | $4,834 |
| 2020-02-03 | GOOGL | AMZN | $5,561 |
| 2021-08-02 | AMZN | GOOGL | $9,244 |
| 2024-03-01 | GOOGL | NVDA | $9,400 |
| 2025-12-01 | MSFT | GOOGL | $29,131 |

</details>

<details><summary><b>Top-5 monthly</b> — 22 changes, ending in AAPL, MSFT, GOOGL, AMZN, NVDA</summary>

| Date | Sold | Bought | Proceeds |
|---|---|---|---|
| 2016-10-03 | BRK-B | XOM | $1,911 |
| 2016-11-01 | XOM | BRK-B | $1,837 |
| 2016-12-01 | AMZN | XOM | $1,885 |
| 2017-02-01 | XOM | AMZN | $1,792 |
| 2017-06-01 | BRK-B | META | $2,131 |
| 2017-07-03 | META | BRK-B | $2,088 |
| 2017-08-01 | BRK-B | META | $2,142 |
| 2018-01-02 | META | BRK-B | $2,288 |
| 2018-06-01 | BRK-B | META | $2,230 |
| 2018-08-01 | META | BRK-B | $1,973 |
| 2019-08-01 | BRK-B | META | $2,012 |
| 2019-10-01 | META | BRK-B | $1,835 |
| 2019-12-02 | BRK-B | META | $1,956 |
| 2020-02-03 | META | BRK-B | $2,000 |
| 2020-03-02 | BRK-B | META | $1,948 |
| 2021-02-01 | META | TSLA | $2,598 |
| 2021-03-01 | TSLA | META | $2,222 |
| 2021-11-01 | META | TSLA | $2,768 |
| 2022-12-01 | TSLA | BRK-B | $1,338 |
| 2023-04-03 | BRK-B | NVDA | $1,314 |
| 2023-05-01 | NVDA | BRK-B | $1,359 |
| 2023-06-01 | BRK-B | NVDA | $1,330 |

</details>

<details><summary><b>Top-1 annual</b> — 3 changes, ending in NVDA</summary>

| Date | Sold | Bought | Proceeds |
|---|---|---|---|
| 2019-01-02 | AAPL | MSFT | $15,200 |
| 2020-01-02 | MSFT | AAPL | $24,501 |
| 2026-01-02 | AAPL | NVDA | $91,626 |

</details>

<details><summary><b>Top-2 annual</b> — 2 changes, ending in AAPL, NVDA</summary>

| Date | Sold | Bought | Proceeds |
|---|---|---|---|
| 2019-01-02 | GOOGL | MSFT | $6,526 |
| 2025-01-02 | MSFT | NVDA | $28,662 |

</details>

<details><summary><b>Top-3 annual</b> — 6 changes, ending in NVDA, AAPL, GOOGL</summary>

| Date | Sold | Bought | Proceeds |
|---|---|---|---|
| 2019-01-02 | GOOGL | AMZN | $4,351 |
| 2020-01-02 | AMZN | GOOGL | $5,365 |
| 2021-01-04 | GOOGL | AMZN | $6,767 |
| 2022-01-03 | AMZN | GOOGL | $7,237 |
| 2025-01-02 | GOOGL | NVDA | $9,489 |
| 2026-01-02 | MSFT | GOOGL | $30,623 |

</details>

## Caveats

- The candidate pool is 50 large US companies, so a company that reached the top N without being in that pool would be missed. Citigroup and Bank of America are absent because their crisis-era share counts predate usable filings.
- Market caps use unadjusted prices times share counts merged from SEC EDGAR, yfinance and a few documented pre-2009 anchors. Share feeds glitch around split dates and are filtered, not perfect, so a ranking near a boundary can be off by a day or a place.
- Prices include reinvested dividends, but dividend income tax is not modeled.
- Tax uses 2025 brackets for every year, the standard deduction only, and a simplified state model.
- Rankings use the previous day's caps, so there is no look-ahead, but trades fill at the close with no slippage and no commission.
- Two overlapping windows of one universe, in one ordering of history. A different decade would rank these differently.

Past results do not predict future results. Not investment advice.

---

Regenerate with:

```bash
python simulate.py report --years 10,20 --total 10000
```
