---
name: investigate
description: Answer investigative questions about trading strategies and markets with computed evidence — run backtests and analyses via the market toolkit instead of speculating. Triggers on questions like "why did X underperform…", "which strategy is best on…", "compare strategy A and B…", "how does X behave in bear markets…", "what if I change parameter Y…".
---

# Investigate: evidence-first strategy research

You are answering a quantitative research question inside the market-sim repo.
The deliverable is a conclusion backed by numbers you computed, never speculation.

## Workflow

1. **Compute, don't guess.** Run analyses with `.venv/bin/python` one-liners or a
   short scratch script (put scratch files in /tmp, not the repo). The toolkit:

   ```python
   from market import fetch_ohlcv, load_strategies, run_backtest, SimConfig
   from market.dca import simulate_dca, TaxConfig          # DCA + rebalancing + taxes
   from market.marketcap import market_caps, top_n_weights  # historical top-N rankings
   ```

   Typical moves:
   - `load_strategies()` to enumerate strategies and their params.
   - `run_backtest(strategy, ohlcv, params).summary()` for standard runs
     (includes buy-and-hold `benchmark_*` metrics automatically).
   - Sub-period / regime analysis: slice `ohlcv` or `result.equity` /
     `result.trades` with pandas (e.g. yearly returns, performance in
     drawdown regimes, per-trade stats).
   - Comparisons: loop strategies × symbols × param grids; collect
     `result.metrics` into a DataFrame and print it.
   - Data is cached (parquet, 24h) — fetch as often as you like.

2. **Web search only for external facts** — market events, macro context, news
   ("what happened in March 2020"). Never search for numbers you can compute
   locally from the data.

3. **Answer with the numbers.** Lead with the conclusion, cite the specific
   metrics that support it (e.g. "SMA crossover returned −12.3% in 2022 vs
   −27.6% for buy-and-hold"), and show a compact table when comparing.

4. **Plots on request:** build figures with
   `market.plots.charts` (`equity_vs_benchmark`, `drawdown_chart`,
   `price_with_signals`), `fig.write_html(...)`, and tell the user the path.

5. **Brief caveats where they matter:** backtests are hypothetical (overfitting
   risk on tuned params, no survivorship handling, simplified costs). One
   sentence, only when relevant — this is research tooling, not investment advice.

6. **Preserve substantial work as an experiment.** When an investigation is
   worth keeping or sharing (multi-strategy comparison, parameter study),
   create `experiments/YYYY-MM-DD-slug/` per `experiments/README.md`: a
   `run.py` that writes `results.csv` + charts into its own folder, and a
   `REPORT.md` with the investigative question, experiment breakdown, results,
   findings, recommendation, column glossary, and caveats (never include
   conversation prompts). Update the index in `experiments/README.md`.
