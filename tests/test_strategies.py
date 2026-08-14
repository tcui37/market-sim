import pandas as pd
import pytest

from market.strategies import load_strategies

STRATEGIES = load_strategies()


def test_discovery_finds_shipped_strategies():
    assert {"buy_and_hold", "sma_crossover", "rsi_mean_reversion"} <= set(STRATEGIES)


@pytest.mark.parametrize("key", sorted(STRATEGIES))
def test_signals_are_valid(key, ohlcv):
    strategy = STRATEGIES[key]
    entries, exits = strategy.generate_signals(ohlcv, **strategy.default_params())

    for signals in (entries, exits):
        assert isinstance(signals, pd.Series)
        assert signals.dtype == bool
        assert signals.index.equals(ohlcv.index)


@pytest.mark.parametrize("key", sorted(STRATEGIES))
def test_param_specs_are_well_formed(key):
    for name, spec in STRATEGIES[key].params.items():
        assert {"default", "min", "max", "step"} <= set(spec), (key, name)
        assert spec["min"] <= spec["default"] <= spec["max"], (key, name)


def test_buy_and_hold_enters_once(ohlcv):
    entries, exits = STRATEGIES["buy_and_hold"].generate_signals(ohlcv)
    assert entries.sum() == 1 and entries.iloc[0]
    assert exits.sum() == 0
