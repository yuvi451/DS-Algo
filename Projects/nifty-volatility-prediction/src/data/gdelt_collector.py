"""Historical news backfill via the GDELT 2.0 DOC API.

We use the DOC API (article search) rather than raw GKG export files: GKG
files are large daily dumps meant for bulk download, while the DOC API lets
us search directly for Nifty/Sensex/RBI-relevant coverage and get back
headline + timestamp + source, which is exactly what the feature pipeline
needs. Its own tone score is aggregate-only (not per article) so we skip it
here and score every headline -- GDELT and RSS alike -- with FinBERT for a
single, consistent sentiment signal (see src/sentiment/finbert.py).
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import requests

GDELT_DOC_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


def _query_gdelt_window(query: str, start: datetime, end: datetime, max_records: int = 250,
                         source_country: str | None = None, timeout: int = 30) -> list[dict]:
    """Query GDELT DOC API for one time window. Returns a list of article dicts."""
    full_query = query
    if source_country:
        full_query = f"{query} sourcecountry:{source_country}"

    params = {
        "query": full_query,
        "mode": "artlist",
        "maxrecords": max_records,
        "format": "json",
        "startdatetime": start.strftime("%Y%m%d%H%M%S"),
        "enddatetime": end.strftime("%Y%m%d%H%M%S"),
        "sort": "datedesc",
    }
    try:
        resp = requests.get(GDELT_DOC_ENDPOINT, params=params, timeout=timeout,
                             headers={"User-Agent": "Mozilla/5.0 (research; nifty-vol-pipeline)"})
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return []
    return data.get("articles", [])


def collect_gdelt_history(query: str, start_date: str, end_date: str,
                           source_country: str | None = "India",
                           chunk_days: int = 7, sleep_sec: float = 1.0,
                           max_records: int = 250) -> pd.DataFrame:
    """Backfill historical news by walking `start_date`..`end_date` in
    `chunk_days`-sized windows, one GDELT DOC API request per window.

    Returns a DataFrame with columns: headline, source, published_at, url
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    rows = []
    cursor = start
    while cursor < end:
        window_end = min(cursor + timedelta(days=chunk_days), end)
        articles = _query_gdelt_window(query, cursor, window_end, max_records=max_records,
                                        source_country=source_country)
        for art in articles:
            seendate = art.get("seendate")
            try:
                published_at = datetime.strptime(seendate, "%Y%m%dT%H%M%SZ")
            except (TypeError, ValueError):
                continue
            rows.append({
                "headline": art.get("title", "").strip(),
                "source": art.get("domain", "gdelt"),
                "published_at": published_at,
                "url": art.get("url", ""),
            })
        cursor = window_end
        time.sleep(sleep_sec)

    df = pd.DataFrame(rows, columns=["headline", "source", "published_at", "url"])
    df = df.dropna(subset=["headline"])
    df = df[df["headline"].str.len() > 0]
    return df.drop_duplicates(subset=["url"]).reset_index(drop=True)
