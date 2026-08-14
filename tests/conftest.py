import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    """Deterministic synthetic daily OHLCV (~2 years) — no network needed."""
    rng = np.random.default_rng(42)
    index = pd.date_range("2020-01-01", periods=500, freq="B")
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, len(index)))), index=index)
    spread = close * rng.uniform(0.0, 0.02, len(index))
    return pd.DataFrame(
        {
            "Open": close.shift(1).fillna(close.iloc[0]),
            "High": close + spread,
            "Low": close - spread,
            "Close": close,
            "Volume": rng.integers(1_000_000, 5_000_000, len(index)).astype(float),
        },
        index=index,
    )
