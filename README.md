# market-sim

Backtest market strategies against real historical data — simple to use, easy to
extend, and built around one shared core with three surfaces:

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
strategies/        one file per strategy
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
(configurable). Results are hypothetical: watch for overfitting when tuning
parameters, and remember daily-bar fills are approximations. Not investment advice.
