import pytest

from market.dca import TaxConfig
from market.tax import TaxProfile


def test_flat_rates_when_no_profile():
    assert TaxConfig(st_rate=0.3, lt_rate=0.2).due(1000, 1000) == pytest.approx(500.0)


def test_short_term_costs_more_than_long_term():
    profile = TaxProfile(income=150_000, filing="single", state="NONE")
    assert profile.tax_on(50_000, 0) > profile.tax_on(0, 50_000)


def test_federal_only_matches_hand_computed_bill():
    # $150k income, $50k long-term gain: 15% bracket, and MAGI lands exactly on
    # the $200k net investment income threshold, so no NIIT yet.
    profile = TaxProfile(income=150_000, filing="single", state="NONE")
    assert profile.tax_on(0, 50_000) == pytest.approx(7_500.0)


def test_niit_applies_above_the_threshold():
    profile = TaxProfile(income=150_000, filing="single", state="NONE")
    without = profile.tax_on(0, 50_000)
    with_more = profile.tax_on(0, 60_000)
    # The extra $10k is taxed at 15% plus the 3.8% investment surtax.
    assert with_more - without == pytest.approx(10_000 * (0.15 + 0.038))


def test_large_gain_crosses_into_higher_brackets():
    profile = TaxProfile(income=50_000, filing="single", state="NONE")
    small = profile.tax_on(0, 10_000) / 10_000
    huge = profile.tax_on(0, 2_000_000) / 2_000_000
    assert huge > small
    assert huge > 0.20  # 20% bracket plus NIIT


def test_state_tax_adds_on_top():
    federal = TaxProfile(income=150_000, state="NONE").tax_on(0, 100_000)
    california = TaxProfile(income=150_000, state="CA").tax_on(0, 100_000)
    texas = TaxProfile(income=150_000, state="TX").tax_on(0, 100_000)
    assert california > federal
    assert texas == pytest.approx(federal)


def test_washington_taxes_only_large_long_term_gains():
    profile = TaxProfile(income=150_000, state="WA")
    plain = TaxProfile(income=150_000, state="NONE")
    assert profile.tax_on(0, 100_000) == pytest.approx(plain.tax_on(0, 100_000))
    assert profile.tax_on(0, 500_000) > plain.tax_on(0, 500_000)


def test_standard_deduction_shelters_a_small_gain():
    assert TaxProfile(income=0, state="NONE").tax_on(5_000, 0) == 0.0


def test_zero_gain_is_zero_tax():
    assert TaxProfile(income=500_000, state="CA").tax_on(0, 0) == 0.0
    assert TaxProfile(income=500_000, state="CA").tax_on(-1_000, 0) == 0.0


def test_marginal_rates_are_reported():
    st, lt = TaxProfile(income=150_000, filing="single", state="CA").rates()
    assert st == pytest.approx(0.24 + 0.093, abs=1e-3)
    assert lt == pytest.approx(0.15 + 0.093, abs=1e-3)


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        TaxProfile(state="ZZ")
    with pytest.raises(ValueError):
        TaxProfile(filing="joint")


def test_profile_overrides_flat_rates_in_tax_config():
    profile = TaxProfile(income=150_000, state="NONE")
    config = TaxConfig(st_rate=0.99, lt_rate=0.99, profile=profile)
    assert config.due(0, 50_000) == pytest.approx(profile.tax_on(0, 50_000))
