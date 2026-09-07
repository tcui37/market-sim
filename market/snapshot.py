"""A committable, offline copy of everything a simulation needs.

`.data_cache/` is a 24-hour scratch cache that a fresh clone starts without. A
snapshot instead freezes the two series the top-N simulator reads, adjusted
close and market cap, into one parquet file under `data/` that can be checked
into a private repo. After that every simulation runs offline and instantly,
and the numbers stay reproducible until the snapshot is rebuilt.

Rebuild it with `python simulate.py snapshot`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from market.data import fetch_ohlcv
from market.marketcap import DEFAULT_UNIVERSE, market_caps

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SNAPSHOT_PATH = DATA_DIR / "market-snapshot.parquet"
META_PATH = DATA_DIR / "market-snapshot.json"

BENCHMARKS = ["SPY", "QQQ", "VOO", "SPYG"]
DEFAULT_START = "2000-01-01"


@dataclass
class Snapshot:
    prices: pd.DataFrame     # adjusted close, columns = symbols
    caps: pd.DataFrame       # market cap, universe symbols only
    meta: dict

    @property
    def universe(self) -> list[str]:
        return list(self.caps.columns)

    def window(self, start=None, end=None) -> Snapshot:
        return Snapshot(self.prices.loc[start:end], self.caps.loc[start:end], self.meta)

    def describe(self) -> str:
        return (f"{len(self.prices.columns)} symbols, "
                f"{self.prices.index[0].date()} to {self.prices.index[-1].date()}, "
                f"built {self.meta.get('built_at', '?')[:10]}")


def build(universe: list[str] | None = None, benchmarks: list[str] | None = None,
          start: str = DEFAULT_START, path: Path | None = None) -> Snapshot:
    """Fetch prices and market caps from the network and write the snapshot."""
    universe = universe or DEFAULT_UNIVERSE
    benchmarks = BENCHMARKS if benchmarks is None else benchmarks
    path = path or SNAPSHOT_PATH

    caps, skipped = {}, []
    for symbol in universe:
        try:
            caps[symbol] = market_caps([symbol], start=start)[symbol]
        except Exception as error:  # no share history, delisting, SEC gap
            skipped.append(symbol)
            print(f"  skipping {symbol}: {error}")
    caps = pd.DataFrame(caps)
    universe = [s for s in universe if s not in skipped]

    prices = pd.DataFrame(
        {s: fetch_ohlcv(s, start=start)["Close"] for s in dict.fromkeys(universe + benchmarks)}
    ).dropna(how="all").sort_index()
    caps = caps.reindex(prices.index)

    long = (prices.stack(future_stack=True).rename("price").to_frame()
            .join(caps.stack(future_stack=True).rename("cap")))
    long.index.names = ["date", "symbol"]
    long = long.dropna(subset=["price"]).reset_index()

    path.parent.mkdir(parents=True, exist_ok=True)
    long.to_parquet(path, compression="zstd", index=False)
    meta = {
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "universe": list(universe),
        "skipped": skipped,
        "benchmarks": list(benchmarks),
        "start": str(prices.index[0].date()),
        "end": str(prices.index[-1].date()),
        "rows": len(long),
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n")
    return Snapshot(prices, caps.dropna(how="all", axis=1), meta)


def load(path: Path | None = None) -> Snapshot:
    """Read the committed snapshot. Raises if it has not been built yet."""
    path = path or SNAPSHOT_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"No market snapshot at {path}. Build one with: python simulate.py snapshot"
        )
    long = pd.read_parquet(path)
    long["date"] = pd.to_datetime(long["date"])
    prices = long.pivot(index="date", columns="symbol", values="price").sort_index()
    caps = long.pivot(index="date", columns="symbol", values="cap").dropna(how="all", axis=1)
    meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
    return Snapshot(prices, caps.reindex(prices.index), meta)


def exists(path: Path | None = None) -> bool:
    return (path or SNAPSHOT_PATH).exists()
