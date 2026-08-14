"""Pluggable data providers and the single entry point for fetching OHLCV data.

To add a new data source (e.g. a crypto exchange):
  1. Create a file in market/data/ with a class implementing DataProvider.
  2. Call register(YourProvider()) in market/data/__init__.py.
Everything else (engine, app, agent) goes through fetch_ohlcv() unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from market.data import cache

OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


class DataProvider(ABC):
    """A source of OHLCV market data."""

    name: str

    @abstractmethod
    def fetch(self, symbol: str, interval: str = "1d") -> pd.DataFrame:
        """Return the full available history for `symbol`.

        Must return a DataFrame with columns Open/High/Low/Close/Volume
        and a sorted, tz-naive DatetimeIndex.
        """


PROVIDERS: dict[str, DataProvider] = {}


def register(provider: DataProvider) -> None:
    PROVIDERS[provider.name] = provider


def fetch_ohlcv(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
    provider: str = "yfinance",
) -> pd.DataFrame:
    """Fetch OHLCV data, using the local parquet cache when fresh (<24h).

    The full history is always cached; `start`/`end` slicing happens in memory.
    A full refresh (rather than incremental append) is used because adjusted
    prices are rewritten retroactively by splits/dividends.
    """
    if provider not in PROVIDERS:
        raise KeyError(f"Unknown provider {provider!r}. Available: {sorted(PROVIDERS)}")

    df = cache.load(provider, symbol, interval)
    if df is None:
        df = PROVIDERS[provider].fetch(symbol, interval)
        _validate(df, symbol)
        cache.save(df, provider, symbol, interval)

    return df.loc[start:end]


def _validate(df: pd.DataFrame, symbol: str) -> None:
    if df.empty:
        raise ValueError(f"No data returned for {symbol!r} — check the symbol.")
    missing = [c for c in OHLCV_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Data for {symbol!r} is missing columns: {missing}")
