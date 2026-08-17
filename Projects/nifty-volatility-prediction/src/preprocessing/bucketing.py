"""Trading-day bucketing.

A news item published at time `ts` (assumed UTC, the norm for GDELT
`seendate` and feedparser's `*_parsed` fields) is assigned to the trading
day `D` such that `ts` falls in the window `(D-1's 15:30 IST close, D's
09:15 IST open]`.

Rather than explicitly computing "previous close", we use an equivalent
and simpler rule: `D` is the *earliest* trading day whose 09:15 IST open is
at or after `ts`. This is exactly the same window (news during trading
hours or after a trading day's close is deferred to the *next* trading
day's pre-market window), and it is robust to weekends/holidays because it
only ever matches against real trading days pulled from the price index.
"""

import numpy as np
import pandas as pd
import pytz

IST = pytz.timezone("Asia/Kolkata")
OPEN_HOUR, OPEN_MINUTE = 9, 15


def _trading_day_opens(trading_days: pd.DatetimeIndex) -> pd.DatetimeIndex:
    days = pd.DatetimeIndex(sorted(pd.to_datetime(trading_days)))
    opens = days + pd.Timedelta(hours=OPEN_HOUR, minutes=OPEN_MINUTE)
    return opens.tz_localize(IST)


def bucket_news_to_trading_days(news_df: pd.DataFrame, trading_days: pd.DatetimeIndex) -> pd.DataFrame:
    """Assign each news row to a trading day (added as a `trading_day` column).

    Rows published after the open of the last available trading day (i.e.
    with no future trading day to bucket into yet) are dropped.
    """
    if news_df.empty:
        out = news_df.copy()
        out["trading_day"] = pd.Series(dtype="datetime64[ns]")
        return out

    out = news_df.copy()
    ts = pd.to_datetime(out["published_at"])
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("UTC")
    ts_ist = ts.dt.tz_convert(IST)

    opens = _trading_day_opens(trading_days)
    days = pd.DatetimeIndex(sorted(pd.to_datetime(trading_days)))

    positions = np.searchsorted(opens.values, ts_ist.values, side="left")
    valid = positions < len(days)

    out = out.loc[valid].copy()
    out["trading_day"] = days[positions[valid]]
    return out.reset_index(drop=True)
