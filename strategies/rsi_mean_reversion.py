import pandas as pd

NAME = "RSI Mean Reversion"
DESCRIPTION = "Buy when RSI drops below the oversold level; sell when it rises above the overbought level."
PARAMS = {
    "period": {"default": 14, "min": 2, "max": 100, "step": 1},
    "oversold": {"default": 30, "min": 5, "max": 50, "step": 1},
    "overbought": {"default": 70, "min": 50, "max": 95, "step": 1},
}


def generate_signals(
    ohlcv: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70
) -> tuple[pd.Series, pd.Series]:
    close = ohlcv["Close"]
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - 100 / (1 + rs)

    entries = (rsi < oversold) & (rsi.shift(1) >= oversold)
    exits = (rsi > overbought) & (rsi.shift(1) <= overbought)
    return entries.fillna(False), exits.fillna(False)
