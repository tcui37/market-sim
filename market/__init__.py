"""market-sim core: data, strategies, simulation, metrics, plots.

Typical use:
    from market import fetch_ohlcv, load_strategies, run_backtest, SimConfig

    strategies = load_strategies()
    ohlcv = fetch_ohlcv("AAPL", start="2015-01-01")
    result = run_backtest(strategies["sma_crossover"], ohlcv, {"fast": 10, "slow": 30})
    print(result.summary())
"""

from market.data import fetch_ohlcv
from market.sim.config import SimConfig
from market.sim.engine import BacktestResult, run_backtest
from market.strategies import Strategy, load_strategies

__all__ = [
    "fetch_ohlcv",
    "load_strategies",
    "run_backtest",
    "BacktestResult",
    "SimConfig",
    "Strategy",
]
