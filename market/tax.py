"""Federal and state tax on realized capital gains.

A TaxProfile turns a real situation (ordinary income, filing status, state)
into the tax owed on a year of realized gains, computed as the tax on
"income + gains" minus the tax on "income" alone. That handles bracket
crossing, which a single flat rate cannot: a large realized gain pushes part
of itself into higher brackets.

Modeled: federal ordinary brackets (short-term gains are ordinary income),
federal preferential long-term brackets stacked on top of ordinary income,
the 3.8% net investment income tax, and state income tax.

Simplifications, all of which push the estimate around by a few points:
  - 2025 brackets and standard deduction for every year (no indexing, no law
    changes), standard deduction only, no credits, no other deductions.
  - State tax uses real brackets for CA and NY, the flat rate for flat-tax
    states, and the top marginal rate everywhere else, so low incomes in a
    progressive state are overstated. No local income tax (NYC, MD counties).
  - Washington's 7% long-term capital gains excise tax is modeled; its
    standard deduction is applied per year.
  - No AMT, no qualified small business stock, no $3,000 capital loss
    deduction against ordinary income (losses only offset future gains).
"""

from __future__ import annotations

from dataclasses import dataclass

INF = float("inf")

FILINGS = ("single", "married", "hoh")

# 2025 federal ordinary income brackets: (upper bound of taxable income, rate).
FEDERAL_ORDINARY: dict[str, list[tuple[float, float]]] = {
    "single": [(11_925, 0.10), (48_475, 0.12), (103_350, 0.22), (197_300, 0.24),
               (250_525, 0.32), (626_350, 0.35), (INF, 0.37)],
    "married": [(23_850, 0.10), (96_950, 0.12), (206_700, 0.22), (394_600, 0.24),
                (501_050, 0.32), (751_600, 0.35), (INF, 0.37)],
    "hoh": [(17_000, 0.10), (64_850, 0.12), (103_350, 0.22), (197_300, 0.24),
            (250_500, 0.32), (626_350, 0.35), (INF, 0.37)],
}

# 2025 federal long-term capital gains brackets, by total taxable income.
FEDERAL_LTCG: dict[str, list[tuple[float, float]]] = {
    "single": [(48_350, 0.0), (533_400, 0.15), (INF, 0.20)],
    "married": [(96_700, 0.0), (600_050, 0.15), (INF, 0.20)],
    "hoh": [(64_750, 0.0), (566_700, 0.15), (INF, 0.20)],
}

STANDARD_DEDUCTION = {"single": 15_000.0, "married": 30_000.0, "hoh": 22_500.0}

NIIT_RATE = 0.038
NIIT_THRESHOLD = {"single": 200_000.0, "married": 250_000.0, "hoh": 200_000.0}

# States with no tax on capital gains (NH taxes neither wages nor, since 2025,
# interest and dividends). WA is handled separately: no income tax, but a 7%
# excise tax on large long-term gains.
NO_INCOME_TAX = {"AK", "FL", "NV", "NH", "SD", "TN", "TX", "WY"}

NO_STATE = "NONE"  # federal tax only

WA_LTCG_RATE = 0.07
WA_LTCG_DEDUCTION = 270_000.0

# Flat-rate states, and top marginal rate for the remaining progressive ones.
STATE_RATES: dict[str, float] = {
    "AL": 0.0500, "AR": 0.0390, "AZ": 0.0250, "CO": 0.0440, "CT": 0.0699,
    "DC": 0.1075, "DE": 0.0660, "GA": 0.0539, "HI": 0.1100, "IA": 0.0380,
    "ID": 0.05695, "IL": 0.0495, "IN": 0.0300, "KS": 0.0558, "KY": 0.0400,
    "LA": 0.0300, "MA": 0.0500, "MD": 0.0575, "ME": 0.0715, "MI": 0.0425,
    "MN": 0.0985, "MO": 0.0470, "MS": 0.0440, "MT": 0.0590, "NC": 0.0425,
    "ND": 0.0250, "NE": 0.0520, "NJ": 0.1075, "NM": 0.0590, "OH": 0.0350,
    "OK": 0.0475, "OR": 0.0990, "PA": 0.0307, "RI": 0.0599, "SC": 0.0620,
    "UT": 0.0455, "VA": 0.0575, "VT": 0.0875, "WI": 0.0765, "WV": 0.0482,
}

# States worth modeling properly: steep brackets and lots of shareholders.
STATE_BRACKETS: dict[str, dict[str, list[tuple[float, float]]]] = {
    "CA": {
        "single": [(10_756, 0.01), (25_499, 0.02), (40_245, 0.04), (55_866, 0.06),
                   (70_606, 0.08), (360_659, 0.093), (432_787, 0.103),
                   (721_314, 0.113), (1_000_000, 0.123), (INF, 0.133)],
        "married": [(21_512, 0.01), (50_998, 0.02), (80_490, 0.04), (111_732, 0.06),
                    (141_212, 0.08), (721_318, 0.093), (865_574, 0.103),
                    (1_442_628, 0.113), (INF, 0.123)],
    },
    "NY": {
        "single": [(8_500, 0.04), (11_700, 0.045), (13_900, 0.0525), (80_650, 0.055),
                   (215_400, 0.06), (1_077_550, 0.0685), (5_000_000, 0.0965),
                   (25_000_000, 0.103), (INF, 0.109)],
        "married": [(17_150, 0.04), (23_600, 0.045), (27_900, 0.0525), (161_550, 0.055),
                    (323_200, 0.06), (2_155_350, 0.0685), (5_000_000, 0.0965),
                    (25_000_000, 0.103), (INF, 0.109)],
    },
}

STATES = sorted(NO_INCOME_TAX | set(STATE_RATES) | set(STATE_BRACKETS) | {"WA", NO_STATE})


@dataclass(frozen=True)
class TaxProfile:
    """Ordinary income, filing status and state, resolved into a tax bill."""

    income: float = 0.0
    filing: str = "single"
    state: str = NO_STATE

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", (self.state or NO_STATE).upper())
        if self.filing not in FILINGS:
            raise ValueError(f"filing must be one of {FILINGS}, got {self.filing!r}")
        if self.state not in STATES:
            raise ValueError(f"Unknown state {self.state!r}. Known: {', '.join(STATES)}")

    def tax_on(self, st_gain: float, lt_gain: float) -> float:
        """Tax owed on one year of realized gains, on top of ordinary income."""
        st_gain, lt_gain = max(st_gain, 0.0), max(lt_gain, 0.0)
        if st_gain == 0.0 and lt_gain == 0.0:
            return 0.0
        return self._total(st_gain, lt_gain) - self._total(0.0, 0.0)

    def rates(self) -> tuple[float, float]:
        """Marginal rate on the next dollar of short-term and long-term gain."""
        probe = 100.0
        return self.tax_on(probe, 0.0) / probe, self.tax_on(0.0, probe) / probe

    def _total(self, st_gain: float, lt_gain: float) -> float:
        return self._federal(st_gain, lt_gain) + self._state(st_gain, lt_gain)

    def _federal(self, st_gain: float, lt_gain: float) -> float:
        ordinary = self.income + st_gain - STANDARD_DEDUCTION[self.filing]
        if ordinary < 0:
            lt_taxable, lt_floor = max(lt_gain + ordinary, 0.0), 0.0
            ordinary = 0.0
        else:
            lt_taxable, lt_floor = lt_gain, ordinary

        tax = _bracket_tax(ordinary, FEDERAL_ORDINARY[self.filing])
        tax += _stacked_tax(lt_floor, lt_taxable, FEDERAL_LTCG[self.filing])

        investment_income = st_gain + lt_gain
        over = max(self.income + investment_income - NIIT_THRESHOLD[self.filing], 0.0)
        return tax + NIIT_RATE * min(investment_income, over)

    def _state(self, st_gain: float, lt_gain: float) -> float:
        if self.state in NO_INCOME_TAX or self.state == NO_STATE:
            return 0.0
        if self.state == "WA":
            return WA_LTCG_RATE * max(lt_gain - WA_LTCG_DEDUCTION, 0.0)
        brackets = STATE_BRACKETS.get(self.state)
        if brackets:
            table = brackets.get(self.filing) or brackets["single"]
            return _bracket_tax(self.income + st_gain + lt_gain, table)
        return STATE_RATES[self.state] * (self.income + st_gain + lt_gain)


def _bracket_tax(taxable: float, brackets: list[tuple[float, float]]) -> float:
    tax, lower = 0.0, 0.0
    for upper, rate in brackets:
        if taxable <= lower:
            break
        tax += (min(taxable, upper) - lower) * rate
        lower = upper
    return tax


def _stacked_tax(base: float, amount: float, brackets: list[tuple[float, float]]) -> float:
    """Tax on `amount` when it sits on top of `base` of other taxable income."""
    return _bracket_tax(base + amount, brackets) - _bracket_tax(base, brackets)
