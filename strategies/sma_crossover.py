import pandas as pd

NAME = "SMA Crossover"
DESCRIPTION = "Long when the fast SMA crosses above the slow SMA; exit on the cross below."
PARAMS = {
    "fast": {"default": 20, "min": 2, "max": 200, "step": 1},
    "slow": {"default": 50, "min": 5, "max": 400, "step": 1},
}


def generate_signals(
    ohlcv: pd.DataFrame, fast: int = 20, slow: int = 50
) -> tuple[pd.Series, pd.Series]:
    close = ohlcv["Close"]
    fast_sma = close.rolling(fast).mean()
    slow_sma = close.rolling(slow).mean()
    entries = (fast_sma > slow_sma) & (fast_sma.shift(1) <= slow_sma.shift(1))
    exits = (fast_sma < slow_sma) & (fast_sma.shift(1) >= slow_sma.shift(1))
    return entries.fillna(False), exits.fillna(False)
