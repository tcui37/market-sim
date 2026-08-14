"""Yahoo Finance provider — free daily OHLCV for US stocks and ETFs."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from market.data.base import OHLCV_COLUMNS, DataProvider


class YFinanceProvider(DataProvider):
    name = "yfinance"

    def fetch(self, symbol: str, interval: str = "1d") -> pd.DataFrame:
        # auto_adjust=True gives split/dividend-adjusted prices — the right
        # default for signal backtests.
        df = yf.download(
            symbol,
            period="max",
            interval=interval,
            auto_adjust=True,
            progress=False,
        )
        if df is None or df.empty:
            raise ValueError(f"yfinance returned no data for {symbol!r}.")

        # yfinance returns MultiIndex columns (field, ticker) even for a
        # single ticker — flatten to plain field names.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[[c for c in OHLCV_COLUMNS if c in df.columns]]
        df.index = pd.DatetimeIndex(df.index).tz_localize(None)
        df.index.name = "Date"
        return df.sort_index()
