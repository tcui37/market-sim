"""Local parquet cache for OHLCV data.

One file per (provider, symbol, interval) under .data_cache/. A file younger
than MAX_AGE is served as-is; otherwise the caller refetches and overwrites.
"""

from __future__ import annotations

import re
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parents[2] / ".data_cache"
MAX_AGE = timedelta(hours=24)


def _path(provider: str, symbol: str, interval: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", f"{provider}_{symbol}_{interval}")
    return CACHE_DIR / f"{safe}.parquet"


def load(provider: str, symbol: str, interval: str) -> pd.DataFrame | None:
    """Return the cached DataFrame if present and fresh, else None."""
    path = _path(provider, symbol, interval)
    if not path.exists():
        return None
    age_seconds = time.time() - path.stat().st_mtime
    if age_seconds > MAX_AGE.total_seconds():
        return None
    return pd.read_parquet(path)


def save(df: pd.DataFrame, provider: str, symbol: str, interval: str) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    df.to_parquet(_path(provider, symbol, interval))


def clear() -> int:
    """Delete all cached files. Returns the number removed."""
    files = list(CACHE_DIR.glob("*.parquet")) if CACHE_DIR.exists() else []
    for f in files:
        f.unlink()
    return len(files)
