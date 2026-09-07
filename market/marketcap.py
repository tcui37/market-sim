"""Historical market caps and top-N-by-market-cap portfolio weights.

Market cap = unadjusted close price x shares outstanding (yfinance shares
history, forward-filled between filings). Approximations to be aware of:
  - The candidate universe is hand-picked (mega caps of the era) — a name that
    briefly cracked the top N but isn't listed here would be missed.
  - Share counts come from irregular filings; between filings they're ffilled,
    and before the first observation the earliest known count is used.
  - Rankings use the PREVIOUS day's market cap, so a rebalance trades on
    information that was available at the time (no look-ahead).
"""

from __future__ import annotations

import pandas as pd
import requests
import yfinance as yf

from market.data import cache

# US large caps that plausibly held a top-50 market-cap spot since ~2006.
# Citigroup and Bank of America (top-5-ish in 2006-07) are deliberately
# excluded: their crisis-era dilution predates SEC XBRL share data, so their
# early market caps cannot be computed reliably.
DEFAULT_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "XOM", "JNJ", "WMT", "JPM", "V", "UNH", "AVGO", "LLY",
    "GE", "PG", "T", "CVX", "IBM", "KO", "INTC", "CSCO", "ORCL", "PFE",
    "MA", "HD", "COST", "ABBV", "MRK", "ADBE", "NFLX", "CRM", "AMD", "PEP",
    "TMO", "MCD", "ACN", "LIN", "ABT", "DIS", "VZ", "NKE", "PM", "TXN",
    "QCOM", "HON", "AMGN", "WFC",
]

SEC_USER_AGENT = "market-sim/0.1 (open-source backtesting tool)"
SEC_CIK_OVERRIDES = {
    "XOM": "0000034088",    # current ticker map points at a re-registered CIK with no history
    "GOOGL": "0001288776",  # pre-2015 filings are under Google Inc, not Alphabet
}
SEC_SKIP = {"BRK-B"}        # multi-class share reporting is unreliable for Berkshire

# Approximate pre-XBRL share counts (annual reports), raw basis of the time.
# Only names where buyback drift vs the 2009 SEC count is large enough to
# affect top-5 rankings in 2006-2008.
PRE_XBRL_ANCHORS: dict[str, dict[str, float]] = {
    "XOM": {"2006-01-01": 6.05e9, "2008-12-31": 5.0e9},
    "MSFT": {"2006-01-01": 10.6e9},
    "PG": {"2006-01-01": 3.25e9},
}


def _raw_close(symbol: str) -> pd.Series:
    """Daily close without dividend adjustment (split-adjusted, as yfinance
    always is) — the actual price level, which paired with split-basis share
    counts yields a correct market cap."""
    df = cache.load("yf_raw", symbol, "1d")
    if df is None:
        df = yf.download(symbol, period="max", interval="1d",
                         auto_adjust=False, progress=False)
        if df is None or df.empty:
            raise ValueError(f"yfinance returned no data for {symbol!r}.")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.DatetimeIndex(df.index).tz_localize(None)
        df = df.sort_index()
        cache.save(df, "yf_raw", symbol, "1d")
    return df["Close"]


def _sec_cik(symbol: str) -> str | None:
    if symbol in SEC_CIK_OVERRIDES:
        return SEC_CIK_OVERRIDES[symbol]
    df = cache.load("sec", "cik_map", "meta")
    if df is None:
        data = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": SEC_USER_AGENT}, timeout=30,
        ).json()
        df = pd.DataFrame(
            [(v["ticker"], str(v["cik_str"]).zfill(10)) for v in data.values()],
            columns=["ticker", "cik"],
        ).set_index("ticker")
        cache.save(df, "sec", "cik_map", "meta")
    ticker = symbol.replace("-", ".")  # SEC uses BRK.B style
    for candidate in (symbol, ticker):
        if candidate in df.index:
            return df.loc[candidate, "cik"]
    return None


def _sec_shares(symbol: str) -> pd.Series:
    """Shares-outstanding observations from SEC XBRL filings (~2009 onward)."""
    cik = _sec_cik(symbol)
    if cik is None:
        return pd.Series(dtype=float)
    url = (f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/dei/"
           "EntityCommonStockSharesOutstanding.json")
    response = requests.get(url, headers={"User-Agent": SEC_USER_AGENT}, timeout=30)
    if response.status_code != 200:
        return pd.Series(dtype=float)
    observations = response.json().get("units", {}).get("shares", [])
    if not observations:
        return pd.Series(dtype=float)
    series = pd.Series(
        {pd.Timestamp(o["end"]): float(o["val"]) for o in observations}
    ).sort_index()
    return series[~series.index.duplicated(keep="last")]


def _shares(symbol: str) -> pd.Series:
    """Shares outstanding on the CURRENT split basis.

    Sources, merged: SEC XBRL filings (2009+), yfinance shares history (2015+),
    and a few documented pre-XBRL anchors. All sources report the raw counts of
    the time, while yfinance prices are split-adjusted — so each observation is
    multiplied by all split ratios that came after it, making price x shares a
    valid market cap.
    """
    df = cache.load("shares_adj", symbol, "1d")
    if df is None:
        ticker = yf.Ticker(symbol)
        parts = []

        yf_series = ticker.get_shares_full(start="2005-01-01")
        if yf_series is not None and len(yf_series):
            yf_series.index = pd.DatetimeIndex(yf_series.index).tz_localize(None)
            parts.append(yf_series.astype(float))

        if symbol not in SEC_SKIP:
            try:
                parts.append(_sec_shares(symbol))
            except requests.RequestException:
                pass  # offline or SEC hiccup — proceed with yfinance data

        anchors = PRE_XBRL_ANCHORS.get(symbol, {})
        if anchors:
            parts.append(pd.Series({pd.Timestamp(d): v for d, v in anchors.items()}))

        series = pd.concat(parts).astype(float).sort_index()
        series = series[~series.index.duplicated(keep="last")].dropna()
        if series.empty:
            raise ValueError(f"No shares-outstanding history for {symbol!r}.")

        splits = ticker.splits
        for split_date, ratio in splits.items():
            split_date = pd.Timestamp(split_date).tz_localize(None)
            series.loc[series.index < split_date] *= float(ratio)

        # Feeds mix bases around split dates (e.g. a count of old x 25 on
        # TSLA's split day). Real counts move slowly, so drop observations far
        # from the local median.
        median = series.rolling(7, center=True, min_periods=1).median()
        series = series[(series / median).between(0.7, 1.4)]

        df = series.to_frame("shares")
        cache.save(df, "shares_adj", symbol, "1d")
    return df["shares"]


def market_caps(universe: list[str] | None = None, start: str | None = None) -> pd.DataFrame:
    """Daily market cap (USD) per symbol. Columns = symbols."""
    universe = universe or DEFAULT_UNIVERSE
    caps = {}
    for symbol in universe:
        close = _raw_close(symbol)
        shares = _shares(symbol).reindex(close.index).ffill().bfill()
        caps[symbol] = close * shares
    df = pd.DataFrame(caps)
    return df.loc[start:] if start else df


def top_n_weights(caps: pd.DataFrame, n: int, rebalance: str = "W-MON") -> pd.DataFrame:
    """Equal weights on the top-n caps, re-ranked on each rebalance date.

    Returns a daily DataFrame (rows sum to 1) aligned to caps.index. Ranking on
    each rebalance date uses the prior day's caps; weights hold steady between
    rebalances.
    """
    ranked = caps.shift(1)  # information available at the open of each day
    marks = ranked.resample(rebalance).first().index  # rebalance period starts
    weights = pd.DataFrame(0.0, index=caps.index, columns=caps.columns)

    current: list[str] | None = None
    next_mark = 0
    for day in caps.index:
        if next_mark < len(marks) and day >= marks[next_mark]:
            row = ranked.loc[day].dropna()
            if len(row) >= n:
                current = list(row.nlargest(n).index)
            while next_mark < len(marks) and day >= marks[next_mark]:
                next_mark += 1
        if current:
            weights.loc[day, current] = 1.0 / n
    return weights
