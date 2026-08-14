from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimConfig:
    """Trading-cost and account settings shared by every backtest."""

    cash: float = 10_000.0
    fees: float = 0.001      # 10 bps commission per trade
    slippage: float = 0.0005  # 5 bps
    freq: str = "1D"
