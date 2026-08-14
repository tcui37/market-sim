# Experiments

One folder per experiment, named `YYYY-MM-DD-short-slug/`. Each experiment is
self-contained: the question, the code that answers it, the data it produced,
and the conclusion — anyone can read the report or rerun the script years later.

## Contents of an experiment

| File | Purpose |
|---|---|
| `REPORT.md` | The shareable summary: question, setup, results, recommendation, caveats |
| `run.py` | Reproduces everything: `.venv/bin/python experiments/<name>/run.py` |
| `results.csv` | The raw comparison table the report is built from |
| `chart.html` | Interactive chart (self-contained, open in a browser) |

## Conventions

- `run.py` writes its outputs (`results.csv`, `chart.html`) into its own folder,
  so rerunning refreshes the experiment in place.
- Use the `market` toolkit (`fetch_ohlcv`, `simulate_dca`, `run_backtest`, ...) —
  if an experiment needs a new capability, add it to `market/` with tests so the
  next experiment gets it for free.
- Record every assumption in `REPORT.md` (window, costs, rebalance schedule,
  data approximations). A result nobody can interrogate is not a result.

## Index

| Experiment | Question | Winner |
|---|---|---|
| [2026-08-13-dca-topcap](2026-08-13-dca-topcap/REPORT.md) | $600/mo for 10y: index ETFs vs top-N market-cap portfolios? | Top-3 market cap (IRA); SPYG (taxable) |
| [2026-08-13-dca-topcap-20y](2026-08-13-dca-topcap-20y/REPORT.md) | Same over 20y, across weekly/monthly/annual rebalancing, after capital-gains taxes | Top-3/5 annual — less rebalancing ≈ same after-tax result, far less tax |
| [2026-08-13-dca-topn-grid](2026-08-13-dca-topn-grid/REPORT.md) | Full grid: top-1…5 × monthly/annual × pre/after-tax, 10y and 20y windows | Top-2–4 annual (taxable); top-3/4 monthly (Roth); exact N is noise |
| [2026-08-13-topn-rolling-10y](2026-08-13-topn-rolling-10y/REPORT.md) | Which N and which frequency, judged across 41 rolling 10-year windows? | Top-2/3, annual rebalancing — in Roth AND taxable; monthly never helps |
