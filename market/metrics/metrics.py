"""Performance metrics computed from vectorbt portfolios.

Metrics are read from individual portfolio methods (total_return, sharpe_ratio,
...) rather than parsed out of pf.stats(), whose row labels vary by version.
"""

from __future__ import annotations

import math


def compute_metrics(pf, benchmark_pf) -> dict:
    """Return strategy metrics plus the same fields prefixed benchmark_."""
    metrics = _portfolio_metrics(pf)
    metrics.update({f"benchmark_{k}": v for k, v in _portfolio_metrics(benchmark_pf).items()})
    return metrics


def _portfolio_metrics(pf) -> dict:
    index = pf.wrapper.index
    days = max((index[-1] - index[0]).days, 1)
    total_return = float(pf.total_return())
    cagr = (1 + total_return) ** (365.25 / days) - 1

    return {
        "total_return": total_return,
        "cagr": cagr,
        "sharpe": _finite(pf.sharpe_ratio()),
        "max_drawdown": float(pf.max_drawdown()),
        "num_trades": int(pf.trades.count()),
        "win_rate": _finite(pf.trades.win_rate()),
    }


def _finite(value) -> float | None:
    """NaN/inf → None (e.g. win rate with zero trades), so results stay JSON-safe."""
    value = float(value)
    return value if math.isfinite(value) else None
