"""Keyword relevance filtering.

GDELT and Google News RSS return a lot of noise for broad market queries,
so we keep only headlines that mention Nifty/Sensex/macro terms or a top
Nifty50 constituent name.
"""

import re

import pandas as pd


def _compile_keyword_pattern(keywords: list[str]) -> re.Pattern:
    escaped = [re.escape(k.lower()) for k in keywords]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b")


def filter_relevant(df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    """Keep only rows whose `headline` contains one of `keywords` (case-insensitive)."""
    if df.empty:
        return df
    pattern = _compile_keyword_pattern(keywords)
    mask = df["headline"].str.lower().apply(lambda h: bool(pattern.search(h)))
    return df[mask].reset_index(drop=True)
