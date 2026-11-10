"""Price data collection and Garman-Klass volatility target construction."""

import numpy as np
import pandas as pd
import yfinance as yf


def fetch_price_data(ticker: str, years: int = 5) -> pd.DataFrame:
    """Download daily OHLC data for `ticker` from yfinance.

    Returns a DataFrame indexed by date with columns:
    open, high, low, close, volume
    """
    df = yf.download(ticker, period=f"{years}y", interval="1d", auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    df = df[["open", "high", "low", "close", "volume"]].dropna()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    return df


def garman_klass_volatility(df: pd.DataFrame) -> pd.Series:
    """Garman-Klass variance estimator for each row's own OHLC, annualization-free.

    sigma^2_GK = 0.5*(ln(H/L))^2 - (2*ln2 - 1)*(ln(C/O))^2

    Returns the volatility (sqrt of the variance estimate), floored at 0 to
    avoid sqrt of small negative numbers caused by numerical noise.
    """
    log_hl = np.log(df["high"] / df["low"])
    log_co = np.log(df["close"] / df["open"])
    gk_var = 0.5 * log_hl ** 2 - (2 * np.log(2) - 1) * log_co ** 2
    gk_var = gk_var.clip(lower=0)
    return np.sqrt(gk_var)


def build_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add return, Garman-Klass vol, rolling vol, and day-of-week features.

    `target_next_gk_vol` is the Garman-Klass volatility realized on the
    *next* trading day — this is the regression target. Everything else is
    computed from information available as of the close of `date`, so it is
    safe to use as a same-day feature.
    """
    out = df.copy()
    out["log_return"] = np.log(out["close"] / out["close"].shift(1))
    # gk_vol at row `date` is computed from that day's own OHLC, so it is
    # only known at that day's close -- it is a valid *same-day* feature
    # for predicting the *next* day's volatility (i.e. "yesterday's vol"
    # relative to the day being forecast).
    out["gk_vol"] = garman_klass_volatility(out)
    out["gk_vol_lag1"] = out["gk_vol"].shift(1)
    out["gk_vol_ma5"] = out["gk_vol"].rolling(5).mean()
    out["gk_vol_ma10"] = out["gk_vol"].rolling(10).mean()
    out["day_of_week"] = out.index.dayofweek

    # Target: next day's realized Garman-Klass volatility.
    out["target_next_gk_vol"] = out["gk_vol"].shift(-1)
    out["target_next_log_gk_vol"] = np.log(out["target_next_gk_vol"] + 1e-8)

    return out
