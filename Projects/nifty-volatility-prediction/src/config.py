"""Shared configuration constants for the Nifty volatility prediction pipeline."""

import pytz

TICKER = "^NSEI"
PRICE_LOOKBACK_YEARS = 5

IST = pytz.timezone("Asia/Kolkata")
PREV_CLOSE_TIME = "15:30"
TODAY_OPEN_TIME = "09:15"

# Keywords used both for GDELT queries and the local relevance filter.
RELEVANCE_KEYWORDS = [
    "nifty", "sensex", "rbi", "reserve bank of india", "budget", "inflation",
    "fii", "dii", "foreign institutional investor", "domestic institutional investor",
    "sebi", "repo rate", "gdp india", "indian rupee", "bse", "nse india",
    "reliance industries", "hdfc bank", "icici bank", "infosys", "tcs",
    "tata consultancy", "kotak mahindra", "larsen", "itc limited", "axis bank",
    "state bank of india", "bharti airtel", "bajaj finance", "hindustan unilever",
    "maruti suzuki", "sun pharma", "asian paints", "adani",
]

GDELT_QUERY = "(Nifty OR Sensex OR \"RBI\" OR \"Union Budget\" OR \"Indian rupee\" OR FII OR DII)"
GDELT_SOURCE_COUNTRY = "India"

RSS_FEEDS = {
    "moneycontrol": "https://www.moneycontrol.com/rss/marketreports.xml",
    "economic_times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "livemint": "https://www.livemint.com/rss/markets",
    "business_standard": "https://www.business-standard.com/rss/markets-106.rss",
    "google_news_nifty": "https://news.google.com/rss/search?q=Nifty+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
}

FINBERT_MODEL_NAME = "ProsusAI/finbert"

RANDOM_SEED = 42
