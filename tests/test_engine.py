import json
import math

import pytest

from market import SimConfig, load_strategies, run_backtest

STRATEGIES = load_strategies()

EXPECTED_METRICS = ["total_return", "cagr", "sharpe", "max_drawdown", "num_trades", "win_rate"]


@pytest.mark.parametrize("key", sorted(STRATEGIES))
def test_backtest_smoke(key, ohlcv):
    result = run_backtest(STRATEGIES[key], ohlcv)

    for name in EXPECTED_METRICS:
        assert name in result.metrics
        assert f"benchmark_{name}" in result.metrics

    for name, value in result.metrics.items():
        if value is not None and not isinstance(value, int):
            assert math.isfinite(value), name

    assert len(result.equity) == len(ohlcv)
    assert len(result.benchmark_equity) == len(ohlcv)
    assert (result.drawdown <= 1e-9).all()


def test_buy_and_hold_matches_benchmark(ohlcv):
    # Identity check: buy-and-hold as a strategy ≈ the built-in benchmark
    # (only slippage on the entry differs).
    config = SimConfig(slippage=0.0)
    result = run_backtest(STRATEGIES["buy_and_hold"], ohlcv, config=config)
    assert result.metrics["total_return"] == pytest.approx(
        result.metrics["benchmark_total_return"], rel=1e-6
    )


def test_summary_is_json_safe(ohlcv):
    result = run_backtest(STRATEGIES["sma_crossover"], ohlcv)
    json.dumps(result.summary())  # raises if anything non-serializable leaks in


def test_params_override_defaults(ohlcv):
    result = run_backtest(STRATEGIES["sma_crossover"], ohlcv, {"fast": 5, "slow": 15})
    assert result.params == {"fast": 5, "slow": 15}
