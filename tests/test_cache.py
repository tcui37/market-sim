import os
import time

from market.data import cache


def test_roundtrip(tmp_path, ohlcv, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)

    assert cache.load("test", "FAKE", "1d") is None
    cache.save(ohlcv, "test", "FAKE", "1d")
    loaded = cache.load("test", "FAKE", "1d")
    assert loaded is not None
    assert loaded.equals(ohlcv)


def test_stale_cache_is_ignored(tmp_path, ohlcv, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    cache.save(ohlcv, "test", "FAKE", "1d")

    path = cache._path("test", "FAKE", "1d")
    stale = time.time() - cache.MAX_AGE.total_seconds() - 60
    os.utime(path, (stale, stale))
    assert cache.load("test", "FAKE", "1d") is None


def test_symbol_sanitized_in_path(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    path = cache._path("test", "../evil/BTC/USD", "1d")
    assert path.parent == tmp_path
