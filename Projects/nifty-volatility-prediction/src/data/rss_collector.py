"""Live RSS collection from Indian financial news outlets + Google News.

Meant to be run on a schedule (e.g. a daily Kaggle/cron job) so that it
extends the GDELT-backed historical dataset going forward, and doubles as a
genuine out-of-sample test on news collected *after* the model was built.
"""

from datetime import datetime

import feedparser
import pandas as pd


def _parse_entry_time(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        t = getattr(entry, key, None)
        if t is not None:
            return datetime(*t[:6])
    return None


def fetch_rss_feed(name: str, url: str, timeout: int = 15) -> pd.DataFrame:
    """Fetch and parse a single RSS feed into headline rows."""
    parsed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
    rows = []
    for entry in parsed.entries:
        headline = getattr(entry, "title", "").strip()
        if not headline:
            continue
        published_at = _parse_entry_time(entry) or datetime.utcnow()
        rows.append({
            "headline": headline,
            "source": name,
            "published_at": published_at,
            "url": getattr(entry, "link", ""),
        })
    return pd.DataFrame(rows, columns=["headline", "source", "published_at", "url"])


def collect_rss_news(feeds: dict) -> pd.DataFrame:
    """Fetch all configured RSS feeds and return a combined, deduped frame."""
    frames = [fetch_rss_feed(name, url) for name, url in feeds.items()]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame(columns=["headline", "source", "published_at", "url"])
    df = pd.concat(frames, ignore_index=True)
    return df.drop_duplicates(subset=["url"]).reset_index(drop=True)
