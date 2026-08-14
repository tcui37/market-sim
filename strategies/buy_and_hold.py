import pandas as pd

NAME = "Buy & Hold"
DESCRIPTION = "Enter on the first bar and never exit. The benchmark every strategy is measured against."
PARAMS = {}


def generate_signals(ohlcv: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    entries = pd.Series(False, index=ohlcv.index)
    entries.iloc[0] = True
    exits = pd.Series(False, index=ohlcv.index)
    return entries, exits
