import numpy as np
import pandas as pd
import pytest

from market.dca import simulate_dca
from market.marketcap import top_n_weights

INDEX = pd.date_range("2020-01-01", periods=500, freq="B")


def constant_weights(columns, index, weight_map):
    weights = pd.DataFrame(0.0, index=index, columns=columns)
    for col, w in weight_map.items():
        weights[col] = w
    return weights


def test_flat_prices_no_fees_preserves_contributions():
    prices = pd.DataFrame({"X": 100.0}, index=INDEX)
    weights = constant_weights(["X"], INDEX, {"X": 1.0})
    res = simulate_dca(prices, weights, monthly=600, fees=0.0)

    assert res.final_value == pytest.approx(res.total_contributed)
    assert res.metrics["multiple"] == pytest.approx(1.0)
    assert res.metrics["irr"] == pytest.approx(0.0, abs=1e-3)
    assert res.unit_index.to_numpy() == pytest.approx(1.0)


def test_fees_reduce_final_value():
    prices = pd.DataFrame({"X": 100.0}, index=INDEX)
    weights = constant_weights(["X"], INDEX, {"X": 1.0})
    with_fees = simulate_dca(prices, weights, monthly=600, fees=0.005)
    assert with_fees.final_value < with_fees.total_contributed


def test_rising_prices_positive_irr():
    prices = pd.DataFrame({"X": np.linspace(100, 200, len(INDEX))}, index=INDEX)
    weights = constant_weights(["X"], INDEX, {"X": 1.0})
    res = simulate_dca(prices, weights, monthly=600)
    assert res.final_value > res.total_contributed
    assert res.metrics["irr"] > 0
    assert res.metrics["twr_cagr"] > 0


def test_two_asset_rebalance_splits_evenly():
    prices = pd.DataFrame({"A": 100.0, "B": 50.0}, index=INDEX)
    weights = constant_weights(["A", "B"], INDEX, {"A": 0.5, "B": 0.5})
    res = simulate_dca(prices, weights, monthly=1000, fees=0.0)
    # Flat prices + even split + no fees: value equals contributions.
    assert res.final_value == pytest.approx(res.total_contributed)


def test_monthly_contribution_count():
    prices = pd.DataFrame({"X": 100.0}, index=INDEX)
    weights = constant_weights(["X"], INDEX, {"X": 1.0})
    res = simulate_dca(prices, weights, monthly=600, fees=0.0)
    months = len(INDEX.to_period("M").unique())
    assert res.total_contributed == pytest.approx(600 * months)


def test_top_n_weights_rank_and_switch():
    index = pd.date_range("2021-01-04", periods=60, freq="B")  # starts a Monday
    caps = pd.DataFrame({"A": 300.0, "B": 200.0, "C": 100.0}, index=index)
    caps.loc[index[30]:, "C"] = 400.0  # C becomes #1 mid-way

    top1 = top_n_weights(caps, 1)
    assert top1.loc[index[10], "A"] == 1.0
    assert top1.loc[index[-1], "C"] == 1.0

    top2 = top_n_weights(caps, 2)
    row = top2.loc[index[-1]]
    assert row.sum() == pytest.approx(1.0)
    assert row["C"] == pytest.approx(0.5) and row["A"] == pytest.approx(0.5)


def test_top_n_weights_no_lookahead():
    # Cap flips on a Monday; that Monday's rebalance must still use Friday's caps.
    index = pd.date_range("2021-01-04", periods=15, freq="B")
    caps = pd.DataFrame({"A": 200.0, "B": 100.0}, index=index)
    flip = index[5]  # a Monday
    assert flip.dayofweek == 0
    caps.loc[flip:, "B"] = 500.0

    top1 = top_n_weights(caps, 1)
    assert top1.loc[flip, "A"] == 1.0          # still A on flip day
    assert top1.loc[index[10], "B"] == 1.0     # B after the next rebalance


# ---------------------------------------------------------------- taxes

from market.dca import TaxConfig, _Ledger  # noqa: E402


def test_ledger_classifies_short_vs_long_term():
    ledger = _Ledger()
    buy_day = pd.Timestamp("2020-01-02")
    ledger.buy("X", buy_day, shares=10, cost=1000.0)

    ledger.sell("X", buy_day + pd.Timedelta(days=200), shares=5, proceeds=700.0)   # ST
    ledger.sell("X", buy_day + pd.Timedelta(days=500), shares=5, proceeds=900.0)   # LT
    assert ledger.st_gains == pytest.approx(200.0)
    assert ledger.lt_gains == pytest.approx(400.0)

    due = ledger.settle(TaxConfig(st_rate=0.24, lt_rate=0.15))
    assert due == pytest.approx(200 * 0.24 + 400 * 0.15)
    assert ledger.taxes_paid == pytest.approx(due)


def test_ledger_losses_offset_and_carry_forward():
    ledger = _Ledger()
    day = pd.Timestamp("2020-01-02")
    ledger.buy("X", day, 10, 1000.0)
    ledger.sell("X", day + pd.Timedelta(days=30), 10, 400.0)  # -600 ST loss
    assert ledger.settle(TaxConfig()) == 0.0
    assert ledger.carryforward == pytest.approx(600.0)

    ledger.buy("Y", day, 10, 1000.0)
    ledger.sell("Y", day + pd.Timedelta(days=90), 10, 1500.0)  # +500 ST gain
    assert ledger.settle(TaxConfig()) == 0.0                   # absorbed by carryforward
    assert ledger.carryforward == pytest.approx(100.0)


def test_flat_prices_incur_no_tax():
    prices = pd.DataFrame({"X": 100.0}, index=INDEX)
    weights = constant_weights(["X"], INDEX, {"X": 1.0})
    res = simulate_dca(prices, weights, monthly=600, tax=TaxConfig())
    assert res.metrics["taxes_paid"] == pytest.approx(0.0)
    assert res.final_value == pytest.approx(res.total_contributed)


def test_buy_and_hold_never_pays_rebalancing_tax():
    prices = pd.DataFrame({"X": np.linspace(100, 300, len(INDEX))}, index=INDEX)
    weights = constant_weights(["X"], INDEX, {"X": 1.0})
    res = simulate_dca(prices, weights, monthly=600, tax=TaxConfig())
    assert res.metrics["taxes_paid"] == pytest.approx(0.0, abs=1e-6)


def test_rebalancing_gains_are_taxed_and_reduce_final_value():
    rng = np.random.default_rng(7)
    trend = np.linspace(100, 300, len(INDEX))
    prices = pd.DataFrame(
        {"A": trend * (1 + 0.3 * np.sin(np.arange(len(INDEX)) / 20)),
         "B": trend},
        index=INDEX,
    )
    weights = constant_weights(["A", "B"], INDEX, {"A": 0.5, "B": 0.5})
    taxed = simulate_dca(prices, weights, monthly=600, tax=TaxConfig())
    untaxed = simulate_dca(prices, weights, monthly=600)
    assert taxed.metrics["taxes_paid"] > 0
    assert taxed.final_value == pytest.approx(untaxed.final_value - taxed.metrics["taxes_paid"], rel=0.05)


def test_annual_rebalance_realizes_less_st_gains_than_weekly():
    trend = np.linspace(100, 400, len(INDEX))
    prices = pd.DataFrame(
        {"A": trend * (1 + 0.3 * np.sin(np.arange(len(INDEX)) / 15)),
         "B": trend},
        index=INDEX,
    )
    weights = constant_weights(["A", "B"], INDEX, {"A": 0.5, "B": 0.5})
    weekly = simulate_dca(prices, weights, monthly=600, rebalance="W-MON", tax=TaxConfig())
    annual = simulate_dca(prices, weights, monthly=600, rebalance="YS", tax=TaxConfig())
    assert annual.metrics["taxes_paid"] < weekly.metrics["taxes_paid"]
