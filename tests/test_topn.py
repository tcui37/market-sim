import numpy as np
import pandas as pd
import pytest

from market.dca import TaxConfig
from market.tax import TaxProfile
from market.topn import buy_and_hold, simulate_top_n

INDEX = pd.date_range("2020-01-01", "2024-12-31", freq="B")


def frame(**columns) -> pd.DataFrame:
    return pd.DataFrame({k: np.asarray(v, dtype=float) for k, v in columns.items()},
                        index=INDEX)


def flat_prices() -> pd.DataFrame:
    return frame(A=[100.0] * len(INDEX), B=[100.0] * len(INDEX), C=[100.0] * len(INDEX))


def ranked_caps(order=("A", "B", "C")) -> pd.DataFrame:
    sizes = {symbol: 300.0 - 100 * i for i, symbol in enumerate(order)}
    return frame(**{k: [v] * len(INDEX) for k, v in sizes.items()})[["A", "B", "C"]]


def test_stable_ranking_never_trades():
    result = simulate_top_n(flat_prices(), ranked_caps(), n=2, per_stock=1000)
    assert result.metrics["changes"] == 0
    assert result.holdings == ["A", "B"]
    assert result.metrics["final_value"] == pytest.approx(2000.0)
    assert result.metrics["total_tax"] == 0.0


def test_initial_stake_is_per_stock_times_n():
    result = simulate_top_n(flat_prices(), ranked_caps(), n=3, per_stock=2500)
    assert result.invested == pytest.approx(7500.0)
    assert result.value.iloc[0] == pytest.approx(7500.0)


def test_swap_sells_only_the_name_that_dropped_out():
    caps = ranked_caps()
    caps.loc["2022-06-15":, "C"] = 1000.0  # C overtakes A and B
    result = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="monthly")

    swaps = result.trades[result.trades.kind == "swap"]
    assert len(swaps) == 1
    assert swaps.iloc[0]["sold"] == "B"      # only the evicted name is sold
    assert swaps.iloc[0]["bought"] == "C"
    assert result.holdings == ["C", "A"]


def test_check_lands_on_the_first_trading_day_of_a_month():
    caps = ranked_caps()
    caps.loc["2022-06-15":, "C"] = 1000.0
    result = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="monthly")
    swap_date = pd.Timestamp(result.trades.iloc[-1]["date"])
    assert swap_date == pd.Timestamp("2022-07-01")


def test_annual_check_reacts_later_than_monthly():
    caps = ranked_caps()
    caps.loc["2022-06-15":, "C"] = 1000.0
    monthly = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="monthly")
    annual = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="annual")
    assert pd.Timestamp(annual.trades.iloc[-1]["date"]) == pd.Timestamp("2023-01-02")
    assert pd.Timestamp(monthly.trades.iloc[-1]["date"]) < pd.Timestamp("2023-01-02")


def test_rising_prices_produce_gains_and_a_cagr():
    prices = frame(A=np.linspace(100, 200, len(INDEX)),
                   B=np.linspace(100, 200, len(INDEX)),
                   C=np.linspace(100, 200, len(INDEX)))
    result = simulate_top_n(prices, ranked_caps(), n=2, per_stock=1000)
    assert result.metrics["final_value"] == pytest.approx(4000.0)
    assert result.metrics["cagr"] > 0
    assert result.metrics["after_tax_irr"] == pytest.approx(result.metrics["cagr"], rel=1e-6)


def test_untouched_positions_are_never_taxed():
    prices = frame(A=np.linspace(100, 400, len(INDEX)),
                   B=np.linspace(100, 400, len(INDEX)),
                   C=np.linspace(100, 400, len(INDEX)))
    result = simulate_top_n(prices, ranked_caps(), n=2, per_stock=1000, tax=TaxConfig())
    assert result.metrics["total_tax"] == 0.0
    assert result.net_value.iloc[-1] == pytest.approx(result.value.iloc[-1])


def test_swapping_a_winner_realizes_tax():
    prices = frame(A=np.linspace(100, 400, len(INDEX)),
                   B=np.linspace(100, 400, len(INDEX)),
                   C=np.linspace(100, 400, len(INDEX)))
    caps = ranked_caps()
    caps.loc["2022-06-15":, "C"] = 1000.0
    result = simulate_top_n(prices, caps, n=2, per_stock=1000, check="monthly",
                            tax=TaxConfig(st_rate=0.24, lt_rate=0.15))
    assert result.metrics["total_tax"] > 0
    assert result.yearly.loc[2022, "realized_lt"] > 0
    # Tax is paid from outside, so holdings (and gross value) are untouched.
    untaxed = simulate_top_n(prices, caps, n=2, per_stock=1000, check="monthly")
    assert result.value.iloc[-1] == pytest.approx(untaxed.value.iloc[-1])
    assert result.net_value.iloc[-1] < result.value.iloc[-1]


def test_liquidate_taxes_the_unrealized_gain():
    prices = frame(A=np.linspace(100, 400, len(INDEX)),
                   B=np.linspace(100, 400, len(INDEX)),
                   C=np.linspace(100, 400, len(INDEX)))
    held = simulate_top_n(prices, ranked_caps(), n=2, per_stock=1000, tax=TaxConfig())
    sold = simulate_top_n(prices, ranked_caps(), n=2, per_stock=1000, tax=TaxConfig(),
                          liquidate=True)
    assert held.metrics["total_tax"] == 0.0
    assert sold.metrics["total_tax"] == pytest.approx(0.15 * (sold.value.iloc[-1] - 2000))


def test_bracket_profile_taxes_more_at_a_higher_income():
    prices = frame(A=np.linspace(100, 400, len(INDEX)),
                   B=np.linspace(100, 400, len(INDEX)),
                   C=np.linspace(100, 400, len(INDEX)))
    caps = ranked_caps()
    caps.loc["2022-06-15":, "C"] = 1000.0
    low = simulate_top_n(prices, caps, n=2, per_stock=10_000, check="monthly",
                         tax=TaxConfig(profile=TaxProfile(40_000, "single", "NONE")))
    high = simulate_top_n(prices, caps, n=2, per_stock=10_000, check="monthly",
                          tax=TaxConfig(profile=TaxProfile(400_000, "single", "CA")))
    assert high.metrics["total_tax"] > low.metrics["total_tax"]


def test_fees_reduce_the_final_value():
    caps = ranked_caps()
    caps.loc["2022-06-15":, "C"] = 1000.0
    free = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="monthly")
    costly = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="monthly", fees=0.01)
    assert costly.metrics["final_value"] < free.metrics["final_value"]


def test_yearly_table_chains_and_covers_every_year():
    result = simulate_top_n(flat_prices(), ranked_caps(), n=2, per_stock=1000)
    yearly = result.yearly
    assert list(yearly.index) == [2020, 2021, 2022, 2023, 2024]
    assert yearly.loc[2020, "start_value"] == pytest.approx(result.invested)
    assert yearly["end_value"].iloc[:-1].to_numpy() == pytest.approx(
        yearly["start_value"].iloc[1:].to_numpy())
    assert yearly.loc[2024, "end_value"] == pytest.approx(result.metrics["final_value"])


def test_max_drawdown_is_negative_when_prices_fall():
    dip = np.concatenate([np.linspace(100, 100, 200), np.linspace(100, 50, 200),
                          np.linspace(50, 120, len(INDEX) - 400)])
    prices = frame(A=dip, B=dip, C=dip)
    result = simulate_top_n(prices, ranked_caps(), n=2, per_stock=1000)
    assert result.metrics["max_drawdown"] == pytest.approx(-0.5, abs=0.01)


def test_buy_and_hold_helper_never_trades():
    prices = pd.Series(np.linspace(100, 300, len(INDEX)), index=INDEX)
    result = buy_and_hold(prices, 10_000, "SPY", tax=TaxConfig())
    assert result.metrics["changes"] == 0
    assert result.metrics["total_tax"] == 0.0
    assert result.metrics["final_value"] == pytest.approx(30_000.0)


def test_unknown_check_frequency_rejected():
    with pytest.raises(ValueError):
        simulate_top_n(flat_prices(), ranked_caps(), n=2, check="weekly")


def test_too_few_investable_names_is_a_clear_error():
    with pytest.raises(ValueError, match="Only"):
        simulate_top_n(flat_prices(), ranked_caps(), n=5)


def test_anchor_moves_the_annual_check():
    caps = ranked_caps()
    caps.loc["2022-06-15":, "C"] = 1000.0
    january = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="annual")
    july = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="annual",
                          anchor="JUL")
    assert pd.Timestamp(january.trades.iloc[-1]["date"]) == pd.Timestamp("2023-01-02")
    assert pd.Timestamp(july.trades.iloc[-1]["date"]) == pd.Timestamp("2022-07-01")


def test_anchor_is_ignored_by_a_monthly_check():
    caps = ranked_caps()
    caps.loc["2022-06-15":, "C"] = 1000.0
    plain = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="monthly")
    anchored = simulate_top_n(flat_prices(), caps, n=2, per_stock=1000, check="monthly",
                              anchor="SEP")
    assert plain.trades.equals(anchored.trades)


def test_unknown_anchor_rejected():
    with pytest.raises(ValueError, match="anchor"):
        simulate_top_n(flat_prices(), ranked_caps(), n=2, check="annual", anchor="SMARCH")


def test_benchmark_yearly_returns_are_added():
    reference = pd.Series(np.linspace(100, 200, len(INDEX)), index=INDEX)
    without = simulate_top_n(flat_prices(), ranked_caps(), n=2, per_stock=1000)
    with_bench = simulate_top_n(flat_prices(), ranked_caps(), n=2, per_stock=1000,
                                benchmark=reference)
    assert "benchmark" not in without.yearly.columns
    assert with_bench.yearly["benchmark"].notna().all()
    # A steadily rising reference gains every year.
    assert (with_bench.yearly["benchmark"] > 0).all()


def test_benchmark_first_year_is_measured_from_the_start_date():
    reference = pd.Series(100.0, index=INDEX)
    reference.loc["2020-07-01":] = 150.0
    result = simulate_top_n(flat_prices(), ranked_caps(), n=2, per_stock=1000,
                            benchmark=reference)
    assert result.yearly.loc[2020, "benchmark"] == pytest.approx(0.5)
    assert result.yearly.loc[2021, "benchmark"] == pytest.approx(0.0)
