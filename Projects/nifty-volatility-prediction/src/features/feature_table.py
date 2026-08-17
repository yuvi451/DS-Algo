"""Daily feature table: sentiment aggregates (same-day + rolling) joined to
price/autoregressive features.

Volatility is highly autocorrelated, so the naive baseline ("tomorrow's vol
~= today's vol") is already strong. The price-based lags are included here
as *features*, not just as a baseline to beat -- sentiment has to earn its
keep on top of them.
"""

import numpy as np
import pandas as pd

PRICE_FEATURE_COLS = [
    "gk_vol", "gk_vol_lag1", "gk_vol_ma5", "gk_vol_ma10", "log_return", "day_of_week",
]

SENTIMENT_BASE_COLS = [
    "sent_mean", "sent_std", "article_count", "pct_positive", "pct_negative",
]


def aggregate_daily_sentiment(scored_news: pd.DataFrame) -> pd.DataFrame:
    """Aggregate FinBERT-scored, trading-day-bucketed news into one row per
    trading day: mean/std polarity, article count, %positive, %negative."""
    if scored_news.empty:
        return pd.DataFrame(columns=["trading_day"] + SENTIMENT_BASE_COLS)

    news = scored_news.copy()
    news["is_positive"] = news["positive"] > news["negative"]
    news["is_negative"] = news["negative"] > news["positive"]

    grouped = news.groupby("trading_day")
    daily = grouped.agg(
        sent_mean=("polarity", "mean"),
        sent_std=("polarity", "std"),
        article_count=("polarity", "size"),
        pct_positive=("is_positive", "mean"),
        pct_negative=("is_negative", "mean"),
    ).reset_index()
    daily["sent_std"] = daily["sent_std"].fillna(0.0)
    return daily


def add_rolling_sentiment(daily_sentiment: pd.DataFrame) -> pd.DataFrame:
    """Add 3-day and 5-day rolling means of the sentiment aggregates --
    news effects aren't always priced in same-day."""
    out = daily_sentiment.sort_values("trading_day").reset_index(drop=True)
    for col in SENTIMENT_BASE_COLS:
        out[f"{col}_roll3"] = out[col].rolling(3, min_periods=1).mean()
        out[f"{col}_roll5"] = out[col].rolling(5, min_periods=1).mean()
    return out


def build_feature_table(price_features: pd.DataFrame, scored_news: pd.DataFrame) -> pd.DataFrame:
    """Join sentiment features to price features on trading day.

    `price_features` is expected to already have `target_next_gk_vol` /
    `target_next_log_gk_vol` columns (see src/data/price_data.py).
    """
    daily_sentiment = aggregate_daily_sentiment(scored_news)
    daily_sentiment = add_rolling_sentiment(daily_sentiment)

    prices = price_features.reset_index().rename(columns={"date": "trading_day"})
    merged = prices.merge(daily_sentiment, on="trading_day", how="left")

    sentiment_cols = [c for c in merged.columns
                       if c.startswith(tuple(SENTIMENT_BASE_COLS))]
    for col in sentiment_cols:
        if col == "article_count" or col.startswith("article_count"):
            merged[col] = merged[col].fillna(0)
        else:
            merged[col] = merged[col].fillna(0.0)

    merged["has_news"] = (merged["article_count"] > 0).astype(int)
    merged = merged.set_index("trading_day")
    merged.index.name = "date"
    return merged


def get_feature_columns(feature_table: pd.DataFrame) -> list[str]:
    exclude = {"open", "high", "low", "close", "volume", "target_next_gk_vol", "target_next_log_gk_vol"}
    return [c for c in feature_table.columns if c not in exclude]
