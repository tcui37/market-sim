# market-sim

Backtest market strategies against real historical data — simple to use, easy to
extend, and built around one shared core with three surfaces:

- **`simulate.py`** — one command that answers "what if I had put $Y into each
  of the top X companies by market cap Z years ago?", with year-by-year gains,
  taxes, APY and drawdown.
- **Streamlit app** — pick a strategy, ticker, dates, and parameters; get metrics
  vs buy-and-hold and interactive charts.
- **Claude Code** — ask investigative questions in a Claude Code session
  ("why did SMA crossover underperform on QQQ in 2022?") and get answers backed
  by real backtests. No API key needed — it uses your Claude Code subscription.
- **Python** — `from market import ...` for scripts and notebooks.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Top-N by market cap, from the command line

```bash
python simulate.py snapshot                    # once: freeze prices + market caps into data/
python simulate.py --top 3 --per-stock 10000 --years 10 --check monthly \
                   --income 150000 --state CA  # your bracket, for the tax column
```

Buys `--per-stock` dollars of each of the N largest US companies `--years` ago,
re-ranks on the first trading day of every month (`--check annual` for once a
year), and trades **only when the top N actually changes** — selling just the
names that dropped out and moving that money into the ones that replaced them.
Positions that stay on the list are never trimmed, so they compound untaxed.

| Flag | What it does |
|---|---|
| `--top 1,2,3,5` | comma lists on `--top`, `--years` and `--check` run the whole grid |
| `--anchor JUL` | which month an annual check falls in (default January) |
| `--income / --filing / --state` | places each year's realized gains in real federal + state brackets |
| `--st-rate / --lt-rate` | flat rates instead, for quick what-ifs |
| `--tax-free` | Roth IRA / 401k: no capital-gains tax |
| `--liquidate` | sell everything on the last day, so unrealized gains are taxed too |
| `--out DIR` | writes summary.csv, yearly.csv, trades.csv and an interactive chart |
| `--yearly`, `--trades` | print the per-year table and every portfolio change |

Taxes are settled per calendar year on that year's net realized gains (FIFO
lots, short vs long term, losses carried forward) and paid from outside the
portfolio, so holdings are never sold to cover the bill.

The year-by-year table carries an `sp500` column, the benchmark's return over
the same calendar year, next to the portfolio's.

`python simulate.py report` writes `results/README.md`, a single page comparing
seven variants side by side over 10- and 20-year windows; `python simulate.py
states` lists the `--state` codes.

## Use

```bash
streamlit run app.py     # interactive workbench
pytest -q                # tests (synthetic data, no network)
claude                   # then ask: "Compare sma_crossover and rsi_mean_reversion on SPY over 5 years"
```

Or from Python:

```python
from market import fetch_ohlcv, load_strategies, run_backtest

strategies = load_strategies()
ohlcv = fetch_ohlcv("AAPL", start="2015-01-01")
result = run_backtest(strategies["sma_crossover"], ohlcv, {"fast": 10, "slow": 30})
print(result.summary())
```

## Layout

```
market/            core package (UI-free)
  data/            pluggable providers (yfinance) + 24h parquet cache
  sim/             vectorbt engine + SimConfig
  metrics/         performance metrics (always vs buy-and-hold benchmark)
  plots/           interactive plotly charts
  strategies.py    auto-discovery of strategies/
  dca.py           $X/month simulator: contributions, rebalancing, FIFO capital-gains taxes
  marketcap.py     historical market caps (SEC + yfinance) and top-N-by-cap weights
  topn.py          lump-sum top-N portfolio traded only when the top N changes
  tax.py           federal + state brackets: what a year of realized gains costs
  snapshot.py      offline, committable copy of prices and market caps
strategies/        one file per strategy
data/              market-snapshot.parquet: the committed offline dataset
results/           generated markdown comparison of the strategies
simulate.py        command-line top-N simulator
experiments/       self-contained analyses: question, run.py, results, REPORT (see its README)
tests/             pytest suite (no network)
app.py             Streamlit app
CLAUDE.md          guide for Claude Code sessions working in this repo
```

## Add a strategy (~20 lines)

Create `strategies/my_strategy.py` — it appears in the app and tests automatically:

```python
import pandas as pd

NAME = "My Strategy"
DESCRIPTION = "One line about when it buys and sells."
PARAMS = {"window": {"default": 20, "min": 2, "max": 200, "step": 1}}

def generate_signals(ohlcv: pd.DataFrame, window: int = 20) -> tuple[pd.Series, pd.Series]:
    close = ohlcv["Close"]
    sma = close.rolling(window).mean()
    entries = (close > sma) & (close.shift(1) <= sma.shift(1))
    exits = (close < sma) & (close.shift(1) >= sma.shift(1))
    return entries.fillna(False), exits.fillna(False)
```

Contract: `ohlcv` has `Open/High/Low/Close/Volume` and a DatetimeIndex; return
two boolean Series aligned to `ohlcv.index` (entry and exit signals).

## Add a data provider

1. New file in `market/data/` implementing `DataProvider` (`name` + `fetch()`).
2. `register(YourProvider())` in `market/data/__init__.py`.

Everything else — engine, app, agent — goes through `fetch_ohlcv()` unchanged.

## Notes on accuracy

Prices are split/dividend-adjusted. Backtests include commissions and slippage
(configurable). The tax model uses 2025 brackets for every year, the standard
deduction only, and simplifies state tax to real brackets for CA and NY and a
single marginal rate elsewhere, so treat the tax column as an estimate. Results are hypothetical: watch for overfitting when tuning
parameters, and remember daily-bar fills are approximations. Not investment advice.
