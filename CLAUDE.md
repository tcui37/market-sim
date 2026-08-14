# market-sim

Backtest market strategies against real historical data. One core (`market/`),
consumed by: the Streamlit app, pytest, the `experiments/` folder, and Claude
Code sessions answering investigative questions (see the `investigate` skill).

## Environment

Always use the project venv: `.venv/bin/python` (or `source .venv/bin/activate`).
Python 3.13 · vectorbt 1.x · pandas 3.x. No API keys needed anywhere.
Never put personal information (emails, names) in code, headers, or reports.

## Toolkit API (use this — don't reimplement)

### Signal backtests (single asset, entry/exit strategies)

```python
from market import fetch_ohlcv, load_strategies, run_backtest, SimConfig

strategies = load_strategies()                      # dict[key, Strategy]
ohlcv = fetch_ohlcv("AAPL", start="2015-01-01")     # daily OHLCV DataFrame, cached
result = run_backtest(strategies["sma_crossover"], ohlcv, {"fast": 10, "slow": 30})
result.summary()   # JSON-safe metrics incl. benchmark_* (buy & hold, automatic)
result.metrics     # total_return, cagr, sharpe, max_drawdown, num_trades, win_rate
result.equity / result.drawdown / result.trades     # pandas objects for analysis
```

### DCA / multi-asset portfolios (contributions, rebalancing, taxes)

```python
from market.dca import simulate_dca, TaxConfig
from market.marketcap import market_caps, top_n_weights, DEFAULT_UNIVERSE

caps = market_caps(start="2006-01-01")              # daily market cap per symbol
weights = top_n_weights(caps, n=3, rebalance="MS")  # equal-weight top-3, monthly re-rank
res = simulate_dca(prices, weights, monthly=600, rebalance="MS",
                   tax=TaxConfig(st_rate=0.24, lt_rate=0.15))  # tax=None → pre-tax
res.summary()      # final_value, profit, irr, twr_cagr, max_drawdown, taxes_paid
```

Semantics: monthly contributions BUY toward target weights (never sell);
rebalancing sells back to target on its schedule (`"W-MON"`, `"MS"`, `"YS"`).
Taxes: FIFO lots, short-term (≤1y) vs long-term rates, settled annually,
losses carry forward. For Roth IRA / tax-advantaged questions use `tax=None`.

### Plots

`market.plots.charts` returns plotly figures (`equity_vs_benchmark`,
`drawdown_chart`, `price_with_signals`); `fig.write_html(path,
include_plotlyjs="cdn")` keeps files small. Follow the dataviz skill for any
new chart.

## Experiments — how analysis work is preserved

Any substantial investigation (multi-strategy comparison, parameter study)
becomes a folder under `experiments/` — read `experiments/README.md` for the
convention. In short: `experiments/YYYY-MM-DD-slug/` containing `run.py`
(writes `results.csv` + charts into its own folder), and `REPORT.md` with the
investigative question, an experiment-breakdown table, results, findings,
recommendation, column glossary, and caveats. Do NOT include conversation
prompts in reports. Add each new experiment to the index table in
`experiments/README.md`. Quick throwaway analyses can run as scratch scripts
in /tmp; promote them to an experiment when the user wants to keep or share.

## Data — what to know before trusting it

- `fetch_ohlcv` caches full history as parquet in `.data_cache/` for 24h;
  fetching repeatedly is free. Prices are split/dividend-adjusted
  (`auto_adjust=True`) — good for returns, wrong for market caps.
- Market caps use dividend-UNadjusted prices × split-consistent share counts
  merged from SEC EDGAR filings (2009+), yfinance (2015+), and documented
  anchors (2006-08) in `PRE_XBRL_ANCHORS`. Share feeds contain glitches around
  split dates; an outlier filter handles them. If rankings look wrong, print
  the top-1 timeline and sanity-check against recorded history first.
- Citigroup/BofA are excluded from `DEFAULT_UNIVERSE` (crisis-era share counts
  unavailable). VOO only exists since Sep 2010 — use SPY for older windows.
- After changing shares-data code, bust the cache: `rm .data_cache/shares_adj*`.
- SEC requests must use the generic `SEC_USER_AGENT` — never a personal email.

## Strategies

One file per strategy in `strategies/`, auto-discovered. Each defines `NAME`,
`DESCRIPTION`, `PARAMS` (per-param `{"default","min","max","step"}`), and
`generate_signals(ohlcv, **params) -> (entries, exits)` boolean Series aligned
to `ohlcv.index`. Files starting with `_` are skipped. New strategy = new file.

## Commands

```bash
.venv/bin/pytest -q                 # test suite (synthetic data, no network)
.venv/bin/streamlit run app.py      # interactive workbench
.venv/bin/python experiments/<name>/run.py   # reproduce an experiment
```

## Conventions

- `market/` stays UI-free (no Streamlit imports); keep files small (~150 lines).
- Metrics come from portfolio methods, never parsed from `pf.stats()`.
- Tests must not touch the network — use the synthetic `ohlcv` fixture; every
  new `market/` capability ships with tests.
- Reports state every assumption (window, costs, tax model, data
  approximations) and end with "not investment advice".
