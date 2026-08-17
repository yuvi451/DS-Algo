"""Near-duplicate headline removal.

Wire content gets republished verbatim (or near-verbatim) across outlets, so
naive article counts mostly measure republishing rather than distinct news.
We normalize text and drop exact normalized duplicates cheaply, then run a
fuzzy pass with difflib *within each same-day bucket only* -- comparing
every headline in the whole corpus pairwise would be O(n^2) and is not
needed since near-duplicates of the same story appear on the same day.
"""

import re
from difflib import SequenceMatcher

import pandas as pd

_WS_PUNCT_RE = re.compile(r"[^a-z0-9\s]")


def normalize_headline(text: str) -> str:
    text = text.lower().strip()
    text = _WS_PUNCT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def dedupe_headlines(df: pd.DataFrame, fuzzy_threshold: float = 0.9) -> pd.DataFrame:
    """Drop exact and near-duplicate headlines.

    Expects a `headline` column and a `published_at` (datetime) column.
    """
    if df.empty:
        return df

    out = df.copy()
    out["_norm"] = out["headline"].map(normalize_headline)
    out = out.drop_duplicates(subset=["_norm"])

    out["_date"] = pd.to_datetime(out["published_at"]).dt.date
    keep_mask = pd.Series(True, index=out.index)

    for _, group in out.groupby("_date"):
        seen: list[tuple] = []  # (index, normalized text)
        for idx, norm in group["_norm"].items():
            is_dup = False
            for _, seen_norm in seen:
                if SequenceMatcher(None, norm, seen_norm).ratio() >= fuzzy_threshold:
                    is_dup = True
                    break
            if is_dup:
                keep_mask.loc[idx] = False
            else:
                seen.append((idx, norm))

    out = out[keep_mask].drop(columns=["_norm", "_date"])
    return out.reset_index(drop=True)
