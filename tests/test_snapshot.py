import json

import pandas as pd
import pytest

from market import snapshot


@pytest.fixture
def snapshot_files(tmp_path, monkeypatch):
    monkeypatch.setattr(snapshot, "SNAPSHOT_PATH", tmp_path / "snap.parquet")
    monkeypatch.setattr(snapshot, "META_PATH", tmp_path / "snap.json")
    return tmp_path


def write_snapshot(path, meta_path):
    index = pd.date_range("2020-01-01", periods=10, freq="B")
    rows = []
    for symbol, price, cap in (("AAA", 100.0, 5e11), ("BBB", 50.0, 2e11), ("SPY", 300.0, None)):
        for day in index:
            rows.append({"date": day, "symbol": symbol, "price": price, "cap": cap})
    pd.DataFrame(rows).to_parquet(path, index=False)
    meta_path.write_text(json.dumps({"built_at": "2026-01-01T00:00:00+00:00"}))


def test_load_roundtrips_prices_and_caps(snapshot_files):
    write_snapshot(snapshot.SNAPSHOT_PATH, snapshot.META_PATH)
    data = snapshot.load()

    assert list(data.prices.columns) == ["AAA", "BBB", "SPY"]
    assert data.universe == ["AAA", "BBB"]  # SPY has no market cap, so it never ranks
    assert data.prices.loc["2020-01-01", "AAA"] == 100.0
    assert len(data.prices) == 10


def test_window_slices_both_frames(snapshot_files):
    write_snapshot(snapshot.SNAPSHOT_PATH, snapshot.META_PATH)
    window = snapshot.load().window("2020-01-06", "2020-01-08")
    assert len(window.prices) == 3
    assert len(window.caps) == 3


def test_missing_snapshot_says_how_to_build_one(snapshot_files):
    assert not snapshot.exists()
    with pytest.raises(FileNotFoundError, match="simulate.py snapshot"):
        snapshot.load()


def test_describe_mentions_range_and_build_date(snapshot_files):
    write_snapshot(snapshot.SNAPSHOT_PATH, snapshot.META_PATH)
    text = snapshot.load().describe()
    assert "3 symbols" in text and "2020-01-01" in text and "2026-01-01" in text
