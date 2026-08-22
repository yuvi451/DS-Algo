#!/usr/bin/env python3
"""Generate the self-contained Kaggle training notebook.

The src/ modules stay the tested source of truth; this inlines them so the
notebook runs on Kaggle with no repo checkout. Regenerate with:

    python build_kaggle_notebook.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"

QUALIFIERS = ("baselines.", "model_mod.", "validation.", "vol.", "signals.")
DROP = ("import baselines", "import model as model_mod", "import validation",
        "import signals", "from volatility import", "import volatility as vol",
        "from __future__ import")


def md(t):
    return {"cell_type": "markdown", "metadata": {},
            "source": t.strip().splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": t.strip("\n").splitlines(keepends=True)}


def module(name):
    lines = (SRC / f"{name}.py").read_text().splitlines(keepends=True)
    out, skip = [], False
    for ln in lines:
        st = ln.lstrip()
        if st.startswith("from volatility import ("):
            skip = True
            continue
        if skip:
            if st.rstrip().endswith(")"):
                skip = False
            continue
        if any(st.startswith(d) for d in DROP):
            continue
        out.append(ln)
    text = "".join(out)
    for q in QUALIFIERS:
        text = re.sub(r"(?<![\w.])" + re.escape(q), "", text)
    return f"# ===== src/{name}.py =====\n" + text


NEWS_PIPELINE = r'''
# ===== news collection: GDELT backfill + live RSS =====
GDELT_DOC_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


def _query_gdelt_window(query, start, end, max_records=250,
                        source_country=None, timeout=30):
    full = f"{query} sourcecountry:{source_country}" if source_country else query
    params = {"query": full, "mode": "artlist", "maxrecords": max_records,
              "format": "json", "sort": "datedesc",
              "startdatetime": start.strftime("%Y%m%d%H%M%S"),
              "enddatetime": end.strftime("%Y%m%d%H%M%S")}
    try:
        r = requests.get(GDELT_DOC_ENDPOINT, params=params, timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0 (research; nifty-vol)"})
        r.raise_for_status()
        return r.json().get("articles", [])
    except (requests.RequestException, ValueError):
        return []


def collect_gdelt_history(query, start_date, end_date, source_country="India",
                          chunk_days=7, sleep_sec=1.0, max_records=250,
                          progress_every=20):
    """Walk the date range in windows, one DOC API request each.

    GDELT caps a single response at 250 articles, so a shorter `chunk_days`
    buys more coverage at the cost of more requests. The DOC API only indexes
    back to roughly 2017 -- earlier windows come back empty rather than error.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    rows, cursor, n = [], start, 0
    total = max(1, (end - start).days // chunk_days)

    while cursor < end:
        window_end = min(cursor + timedelta(days=chunk_days), end)
        for art in _query_gdelt_window(query, cursor, window_end,
                                       max_records, source_country):
            try:
                ts = datetime.strptime(art.get("seendate"), "%Y%m%dT%H%M%SZ")
            except (TypeError, ValueError):
                continue
            rows.append({"headline": (art.get("title") or "").strip(),
                         "source": art.get("domain", "gdelt"),
                         "published_at": ts, "url": art.get("url", "")})
        cursor = window_end
        n += 1
        if n % progress_every == 0:
            print(f"    GDELT window {n}/{total}  ({len(rows)} articles so far)")
        time.sleep(sleep_sec)

    df = pd.DataFrame(rows, columns=["headline", "source", "published_at", "url"])
    df = df[df["headline"].str.len() > 0]
    return df.drop_duplicates(subset=["url"]).reset_index(drop=True)


def collect_rss_news(feeds):
    frames = []
    for name, url in feeds.items():
        try:
            parsed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
        except Exception:
            continue
        rows = []
        for e in parsed.entries:
            h = getattr(e, "title", "").strip()
            if not h:
                continue
            t = None
            for key in ("published_parsed", "updated_parsed"):
                v = getattr(e, key, None)
                if v is not None:
                    t = datetime(*v[:6])
                    break
            rows.append({"headline": h, "source": name,
                         "published_at": t or datetime.utcnow(),
                         "url": getattr(e, "link", "")})
        if rows:
            frames.append(pd.DataFrame(rows))
    if not frames:
        return pd.DataFrame(columns=["headline", "source", "published_at", "url"])
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["url"]).reset_index(drop=True)


# ===== preprocessing =====
_WS_PUNCT_RE = re.compile(r"[^a-z0-9\s]")


def normalize_headline(text):
    text = _WS_PUNCT_RE.sub(" ", str(text).lower().strip())
    return re.sub(r"\s+", " ", text).strip()


def dedupe_headlines(df, fuzzy_threshold=0.9):
    """Exact dedupe on normalised text, then a fuzzy pass within each day.

    Wire copy gets republished across outlets, so without this an article
    count mostly measures syndication rather than distinct news. The fuzzy
    pass is restricted to same-day buckets because near-duplicates of a story
    appear on the same day, and an all-pairs comparison would be O(n^2).
    """
    if df.empty:
        return df
    out = df.copy()
    out["_norm"] = out["headline"].map(normalize_headline)
    out = out.drop_duplicates(subset=["_norm"])
    out["_date"] = pd.to_datetime(out["published_at"]).dt.date

    keep = pd.Series(True, index=out.index)
    for _, grp in out.groupby("_date"):
        seen = []
        for idx, norm in grp["_norm"].items():
            if any(SequenceMatcher(None, norm, s).ratio() >= fuzzy_threshold for s in seen):
                keep.loc[idx] = False
            else:
                seen.append(norm)
    return out[keep].drop(columns=["_norm", "_date"]).reset_index(drop=True)


def filter_relevant(df, keywords):
    if df.empty:
        return df
    pat = re.compile(r"\b(" + "|".join(re.escape(k.lower()) for k in keywords) + r")\b")
    mask = df["headline"].str.lower().apply(lambda h: bool(pat.search(h)))
    return df[mask].reset_index(drop=True)


def bucket_news_to_trading_days(news_df, trading_days):
    """Assign each item to the trading day whose pre-open window contains it.

    A story published at `ts` belongs to the earliest trading day `D` whose
    09:15 IST open is at or after `ts` -- equivalently the window
    (D-1 close 15:30, D open 09:15]. Stated that way it handles weekends and
    holidays automatically, because it only ever matches real trading days.
    Nothing is discarded: intraday news simply rolls into the next session,
    which is the first point at which you could have traded on it.
    """
    if news_df.empty:
        out = news_df.copy()
        out["trading_day"] = pd.Series(dtype="datetime64[ns]")
        return out

    out = news_df.copy()
    ts = pd.to_datetime(out["published_at"])
    ts = ts.dt.tz_localize("UTC") if ts.dt.tz is None else ts
    ts_ist = ts.dt.tz_convert(IST)

    days = pd.DatetimeIndex(sorted(pd.to_datetime(trading_days)))
    opens = (days + pd.Timedelta(hours=9, minutes=15)).tz_localize(IST)

    pos = np.searchsorted(opens.values, ts_ist.values, side="left")
    valid = pos < len(days)
    out = out.loc[valid].copy()
    out["trading_day"] = days[pos[valid]]
    return out.reset_index(drop=True)


# ===== FinBERT =====
class FinBertScorer:
    """ProsusAI/finbert, inference only. polarity = P(pos) - P(neg)."""

    def __init__(self, model_name="ProsusAI/finbert", device=None, batch_size=64):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model = self.model.to(self.device).eval()
        self.id2label = self.model.config.id2label

    def score_all(self, headlines):
        torch = self.torch
        texts = headlines.fillna("").astype(str).tolist()
        labels = [self.id2label[i].lower() for i in range(len(self.id2label))]

        chunks = []
        with torch.no_grad():
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                enc = self.tokenizer(batch, padding=True, truncation=True,
                                     max_length=64, return_tensors="pt").to(self.device)
                probs = torch.softmax(self.model(**enc).logits, dim=-1)
                chunks.append(probs.cpu().numpy())
                if (i // self.batch_size) % 200 == 0 and i:
                    print(f"    FinBERT {i}/{len(texts)}")
        arr = np.concatenate(chunks) if chunks else np.zeros((0, len(labels)))
        out = pd.DataFrame(arr, columns=labels)
        out["polarity"] = out["positive"] - out["negative"]
        return out


def score_headlines(df, scorer=None, batch_size=64):
    scorer = scorer or FinBertScorer(batch_size=batch_size)
    scores = scorer.score_all(df["headline"])
    out = df.reset_index(drop=True).copy()
    for c in ("positive", "negative", "neutral", "polarity"):
        out[c] = scores[c].to_numpy()
    return out
'''

cells = [
    md("""
# Nifty Volatility — v2, trained on real data

Forecasts next-day realized volatility of the Nifty 50 from price, **India VIX**
and news-sentiment features, then trades it three ways: a volatility-targeted
index overlay, a **long/short** directional book, and a variance-risk-premium
carry strategy.

This is a rebuild after a critical review of a first version whose backtest lost
to buy-and-hold. That version's three bugs, all fixed here:

| Bug | Effect |
|---|---|
| Sized positions off a **Garman-Klass** forecast (intraday vol) while trading close-to-close returns (includes the overnight gap) | every position ~1.24x too large |
| `exp(mean of log vol)` is the **median**, not the mean | a further ~1.09x |
| Rebalanced daily off a noisy daily forecast, and charged no financing on leverage | ~3.5%/yr of cost drag |

Predicted over-leverage 1.35x; leverage backed out of the original results 1.31x.

---

### Kaggle setup — do this first

In the right-hand panel:

1. **Settings → Internet → On.** Required for yfinance, GDELT and HuggingFace.
   Kaggle asks for phone verification to enable it.
2. **Settings → Accelerator → GPU T4 x2.** Only needed for the FinBERT step;
   skip it if you set `RUN_NEWS = False` below.

Runtime is roughly 5 minutes without news, 25–40 with the full GDELT backfill.
Intermediate results are cached to `/kaggle/working` so a re-run is fast.
"""),
    md("## 0. Setup"),
    code("""
!pip install -q yfinance arch optuna shap feedparser lightgbm --upgrade 2>&1 | tail -2
"""),
    code("""
import os, re, time, json, pathlib, warnings
warnings.filterwarnings("ignore")

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
import requests
import feedparser
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta

try:
    import pytz
    IST = pytz.timezone("Asia/Kolkata")
except ImportError:
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)
pd.set_option("display.float_format", lambda x: f"{x:,.4f}")

WORK = pathlib.Path("/kaggle/working") if pathlib.Path("/kaggle/working").exists() else pathlib.Path(".")
print("output dir:", WORK)
"""),
    md("## 1. Config"),
    code('''
# ---- data -----------------------------------------------------------------
TICKER          = "^NSEI"
VIX_TICKER      = "^INDIAVIX"
PRICE_YEARS     = 10

# ---- news -----------------------------------------------------------------
RUN_NEWS        = True     # False -> price + VIX only (fast, still a full run)
GDELT_CHUNK_DAYS = 7       # smaller = more coverage, more requests (250/response cap)
GDELT_START_MIN = "2017-01-01"   # the DOC API does not index reliably before this

# ---- market assumptions ---------------------------------------------------
RF_ANNUAL       = 0.065    # ~MIBOR; financing and the excess-return Sharpe
DIV_YIELD       = 0.012    # ^NSEI is a PRICE index -- dividends are not in it
COST_BPS_CASH   = 7.5
COST_BPS_FUT    = 5.0      # Nifty futures: 2 bps STT on the sell side + spread
TARGET_ANN_VOL  = 0.12

# ---- model ----------------------------------------------------------------
N_TRIALS        = 25
TRAIN_YEARS     = 3
TEST_MONTHS     = 2
RANDOM_SEED     = 42

RELEVANCE_KEYWORDS = [
    "nifty", "sensex", "rbi", "reserve bank of india", "budget", "inflation",
    "fii", "dii", "foreign institutional investor", "domestic institutional investor",
    "sebi", "repo rate", "gdp india", "indian rupee", "bse", "nse india",
    "reliance industries", "hdfc bank", "icici bank", "infosys", "tcs",
    "tata consultancy", "kotak mahindra", "larsen", "itc limited", "axis bank",
    "state bank of india", "bharti airtel", "bajaj finance", "hindustan unilever",
    "maruti suzuki", "sun pharma", "asian paints", "adani",
]
GDELT_QUERY = '(Nifty OR Sensex OR "RBI" OR "Union Budget" OR "Indian rupee" OR FII OR DII)'
RSS_FEEDS = {
    "moneycontrol": "https://www.moneycontrol.com/rss/marketreports.xml",
    "economic_times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "livemint": "https://www.livemint.com/rss/markets",
    "business_standard": "https://www.business-standard.com/rss/markets-106.rss",
    "google_news_nifty": "https://news.google.com/rss/search?q=Nifty+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
}
'''),
    md("""
## 2. Volatility estimators — the unit conventions everything depends on

Two different daily volatilities, and v1 conflated them:

- **Intraday** (open-to-close) — what Garman-Klass measures.
- **Total** (close-to-close) — what you actually trade, gap included.

Everything downstream works in total units, which is also what India VIX quotes
in. That is what makes the two comparable and the VRP strategy possible.
"""),
    code(module("volatility")),
    md("""
## 3. Price data and India VIX

India VIX was absent from v1 entirely and is the biggest single omission: it is
a forward-looking, market-consensus volatility forecast, published daily and
free, and it already impounds most of what news sentiment could carry.
"""),
    code('''
import yfinance as yf


def load_yf(ticker, years):
    df = yf.download(ticker, period=f"{years}y", interval="1d",
                     auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    return df


prices = load_yf(TICKER, PRICE_YEARS)[["open", "high", "low", "close", "volume"]].dropna()
vix = load_yf(VIX_TICKER, PRICE_YEARS)["close"].dropna().rename("vix")

assert len(prices) > 500, "price download failed -- is Internet enabled in Settings?"
print(f"{TICKER}: {len(prices)} sessions  {prices.index.min().date()} -> {prices.index.max().date()}")
print(f"{VIX_TICKER}: {len(vix)} sessions  mean {vix.mean():.1f}  max {vix.max():.1f}")
prices.tail(3)
'''),
    code('''
# The v1 bug, measured on your own data rather than assumed.
gk = realized_vol(prices, "gk")
total = realized_vol(prices, "total")
share = (gk / total).median()
cc_vol = np.log(prices["close"] / prices["close"].shift(1)).std() * np.sqrt(252)

print(f"Nifty annualized close-to-close vol : {cc_vol:.1%}")
print(f"median sigma_GK / sigma_total       : {share:.3f}")
print(f"-> sizing off Garman-Klass over-levers by {1/share:.2f}x")
print(f"overnight share of daily variance   : {1 - (gk**2).mean()/(total**2).mean():.1%}")
'''),
    md("""
## 4. News: GDELT backfill, dedupe, relevance filter, FinBERT

Carried over from v1 and unchanged in substance. The only thing the rest of the
pipeline needs out of this section is a frame with `trading_day`, `polarity`,
`positive`, `negative`.

Bucketing rule: a story belongs to the trading day whose **pre-open window**
(previous close 15:30 IST → open 09:15 IST) contains it. Nothing is thrown
away — intraday news rolls into the next session, which is the first moment you
could have traded on it.
"""),
    code(NEWS_PIPELINE),
    code('''
NEWS_CACHE = WORK / "scored_news.parquet"
scored_news = None

if RUN_NEWS and NEWS_CACHE.exists():
    scored_news = pd.read_parquet(NEWS_CACHE)
    print(f"loaded cached news: {len(scored_news)} scored headlines")

elif RUN_NEWS:
    start = max(prices.index.min().strftime("%Y-%m-%d"), GDELT_START_MIN)
    end = prices.index.max().strftime("%Y-%m-%d")
    print(f"GDELT backfill {start} -> {end} (this is the slow part)")

    gdelt = collect_gdelt_history(GDELT_QUERY, start, end,
                                  chunk_days=GDELT_CHUNK_DAYS)
    rss = collect_rss_news(RSS_FEEDS)
    raw = pd.concat([gdelt, rss], ignore_index=True)
    print(f"  raw: {len(raw)}  (gdelt {len(gdelt)}, rss {len(rss)})")

    if len(raw):
        deduped = dedupe_headlines(raw)
        relevant = filter_relevant(deduped, RELEVANCE_KEYWORDS)
        bucketed = bucket_news_to_trading_days(relevant, prices.index)
        print(f"  deduped {len(deduped)} -> relevant {len(relevant)} -> bucketed {len(bucketed)}")

        if len(bucketed):
            scored_news = score_headlines(bucketed, batch_size=64)
            scored_news.to_parquet(NEWS_CACHE)
            print(f"  scored {len(scored_news)}; cached to {NEWS_CACHE}")

if scored_news is not None and len(scored_news):
    per_day = scored_news.groupby("trading_day").size()
    print(f"\\ncoverage: {len(per_day)} trading days, median {per_day.median():.0f} headlines/day")
    print(f"date range: {per_day.index.min().date()} -> {per_day.index.max().date()}")
    display(scored_news[["headline", "polarity"]].tail(5))
else:
    print("\\nRunning price + VIX only.")
'''),
    md("""
## 5. Features

The sentiment block is rebuilt around what actually moves volatility. v1 fed a
*signed* mean polarity to predict a *magnitude* — but good news and bad news
both raise volatility, so the sign is nearly irrelevant, and averaging ~50
headlines crushes the remaining variance. What matters is intensity, disagreement
and news-volume shocks. Missing days stay NaN rather than being filled with 0.0,
which in v1 made "no news" indistinguishable from "perfectly balanced news".

The signed polarity is not wasted — it reappears in section 9 as a *directional*
signal, which is the question its sign is actually about.
"""),
    code(module("features")),
    code('''
table = build_feature_table(prices, scored_news, vix, horizons=(1, 5))
cols = feature_columns(table)
print(f"{len(cols)} features, {len(table)} rows\\n")
print(cols)
table[["close", "rv", "gk_vol", "iv_daily", "log_vrp", "target_log_rv_h1"]].tail()
'''),
    md("""
## 6. Baselines

**HAR-RV** (Corsi 2009) is the bar that matters. v1 compared against naive
persistence — `log(sigma_t)` from a single day's range, a very noisy level
estimate — and beating it by 15% is close to free.

GARCH is also repaired: v1 fit close-to-close returns (forecasting *total* vol)
and scored the result against a Garman-Klass *intraday* target, a near-constant
log offset of about +0.21. Most of v1's "+30.8% vs GARCH" was that unit error.
"""),
    code(module("baselines")),
    code(module("model")),
    md("""
## 7. Walk-forward validation

Expanding window, never a shuffle. Two additions over v1:

- **Diebold-Mariano** with Newey-West standard errors, so "beats HAR" is a claim
  with a p-value rather than a bare percentage over noisy folds.
- **Purging** of overlapping multi-day targets at the train/test boundary —
  without it the `h=5` model trains on labels built from the data it is about to
  be scored on.
"""),
    code(module("validation")),
    code('''
RUN_GARCH = False   # rolling GARCH over 10y is slow; flip on for the full table
garch_log = garch_forecast(table["log_return"], refit_every=25) if RUN_GARCH else None

folds = run_walk_forward(table, cols, target_col="target_log_rv_h1",
                          garch_log=garch_log, train_years=TRAIN_YEARS,
                          test_months=TEST_MONTHS, step_months=TEST_MONTHS,
                          n_trials=N_TRIALS)
preds = stack_predictions(folds)
errs = error_table(preds)
print("\\n", errs, "\\n")

for name in ["har", "naive"]:
    if name in errs.index:
        b = errs.loc[name, "rmse"]
        print(f"Model vs {name:>5}: {100*(b-errs.loc['model','rmse'])/b:+.1f}% RMSE")

dm = diebold_mariano(preds, "model", "har")
print(f"\\nDiebold-Mariano vs HAR-RV: stat={dm['statistic']:+.2f}  p={dm['p_value']:.4f}  n={dm['n']}")
print("->", "model significantly better" if dm["p_value"] < 0.05 and dm["statistic"] < 0
      else "NOT significant -- the model does not beat HAR")
'''),
    code('''
folds5 = run_walk_forward(table, cols, target_col="target_log_rv_h5",
                           train_years=TRAIN_YEARS, test_months=TEST_MONTHS,
                           step_months=TEST_MONTHS, n_trials=N_TRIALS, verbose=False)
preds5 = stack_predictions(folds5)
print(error_table(preds5))
'''),
    code('''
fig, ax = plt.subplots(figsize=(14, 4.5))
ax.plot(preds.index, np.exp(preds["y_true"]) * np.sqrt(252) * 100,
        lw=1.0, alpha=0.75, label="Realized (gap-inclusive)")
ax.plot(preds.index, np.exp(preds["model"]) * preds["smearing"] * np.sqrt(252) * 100,
        lw=1.2, label="LightGBM forecast")
ax.plot(preds.index, table["iv_daily"].reindex(preds.index) * np.sqrt(252) * 100,
        lw=1.0, alpha=0.8, label="India VIX (implied)")
ax.set_title("Walk-forward: forecast vs realized vs implied (annualized %)")
ax.set_ylabel("vol %"); ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout(); plt.show()
'''),
    md("""
## 8. Does sentiment contribute? (ablation, not SHAP share)

v1 reported "sentiment contributes 0.0% of SHAP" and stopped there. But SHAP
share describes *this fitted model*, not the data — when sentiment features are
noisy and partly collinear with price features, greedy tree splitting never
selects them and their SHAP mass is zero by construction.

The decision-useful question is whether out-of-sample error gets worse without
them. That is an ablation with a p-value. It may still come back negative, and
a tested negative is a better result than an untestable SHAP share.
"""),
    code(module("explain")),
    code('''
final = table.dropna(subset=["target_log_rv_h1"])
cut = int(len(final) * 0.85)
params = tune(final[cols].iloc[:cut], final["target_log_rv_h1"].iloc[:cut],
              final[cols].iloc[cut:], final["target_log_rv_h1"].iloc[cut:],
              n_trials=N_TRIALS)
final_model = fit(final[cols], final["target_log_rv_h1"], params, val_fraction=0.15)

imp = importance(compute_shap(final_model, final[cols].iloc[-500:]), cols)
print(group_shares(imp).round(1).to_string(), "\\n")
print(imp.head(15).to_string(index=False))
'''),
    code('''
sent_cols = [c for c in cols if c.startswith(("sent_", "news_vol", "has_news"))]
if sent_cols:
    base_cols = [c for c in cols if c not in sent_cols]
    print("SENTIMENT ablation:", incremental_value(
        table, base_cols, sent_cols, n_trials=10, train_years=TRAIN_YEARS))
else:
    print("No sentiment features (RUN_NEWS was False).")

vix_cols = [c for c in cols if c.startswith(("log_iv", "log_vrp", "vix_"))]
if vix_cols:
    base_cols = [c for c in cols if c not in vix_cols]
    print("\\nINDIA VIX ablation:", incremental_value(
        table, base_cols, vix_cols, n_trials=10, train_years=TRAIN_YEARS))
'''),
    md("""
## 9. Directional signals — the prerequisite for shorting

A volatility model cannot tell you which way to bet: it forecasts `|r|`, and the
sign is exactly what it discards. So "add shorting" means "add a return
forecast", which is a harder problem — realized volatility is strongly
autocorrelated and forecastable, daily index returns are close to a martingale.

Three cheap causal signals: time-series momentum (the only one with decades of
out-of-sample evidence), the variance risk premium as a risk-appetite proxy, and
signed news polarity.

**Read the IC table before you look at any equity curve.** If the blend's t-stat
is under 2, the long/short backtest below is a draw from noise no matter how
good its Sharpe looks.
"""),
    code(module("signals")),
    code('''
next_ret = table["log_return"].shift(-1)
direction = build_direction(table, allow_short=True)

print("Information coefficient vs next-day return:\\n")
print(signal_report(direction.reindex(preds.index), next_ret.reindex(preds.index)).round(4))
'''),
    md("""
## 10. Backtests

Three strategies, and they are not equal.

**A — volatility overlay (no direction).** v1's idea, repaired. It will not make
money and is not supposed to: Sharpe is invariant to leverage, so the only thing
that moves it is `Cov(1/sigma_hat, r_next)` — and the model forecasts volatility,
not returns. Claim the drawdown, not the return.

**B — long/short.** Direction from section 9, size from the volatility model.
This is the only arrangement where the volatility forecast contributes to return,
and it does so indirectly: it makes each unit of directional conviction carry
constant risk. Shorting is via futures, so the carry arithmetic differs — you
give up the dividend yield and fight the index's drift.

**C — variance risk premium carry.** Where a volatility forecast genuinely pays.
India VIX prices implied vol, the model forecasts realized vol, and the spread is
tradeable. This converts the model from a position-sizing input into a *pricing*
input, where every RMSE improvement maps onto P&L.
"""),
    code(module("backtest")),
    code('''
pred_vol = pd.Series(np.exp(preds["model"]) * preds["smearing"], index=preds.index)

# v1's configuration for comparison: GK units, no smearing, daily rebalance, free leverage
gk_ratio = (table["gk_vol"] / table["rv"]).reindex(preds.index).median()
pred_vol_v1 = pred_vol * gk_ratio / preds["smearing"]

bt_v1 = vol_target_backtest(pred_vol_v1, next_ret, target_ann_vol=0.16,
                             max_leverage=2.0, cost_bps=COST_BPS_CASH,
                             rf_annual=0.0, deadband=0.0)
bt_v2 = vol_target_backtest(pred_vol, next_ret, target_ann_vol=TARGET_ANN_VOL,
                             max_leverage=1.5, cost_bps=COST_BPS_CASH,
                             rf_annual=RF_ANNUAL, deadband=0.10)

print("A -- VOLATILITY OVERLAY\\n")
print(pd.DataFrame([
    summarize(bt_v1["strategy_return"], label="v1 config (the bugs)"),
    summarize(bt_v2["strategy_return"], label="v2 config (fixed)"),
    summarize(bt_v2["buy_hold_return"], label="buy & hold"),
]).set_index("label")[["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "total_return"]])

print(f"\\nmean position  v1={bt_v1['position'].mean():.2f}x   v2={bt_v2['position'].mean():.2f}x")
print(f"turnover       v1={bt_v1['position'].diff().abs().sum():.0f}   v2={bt_v2['position'].diff().abs().sum():.0f}")
print(f"cost drag/yr   v1={252*bt_v1['cost'].mean():.2%}   v2={252*bt_v2['cost'].mean():.2%}")
'''),
    code('''
d_ls = direction["direction"].reindex(preds.index)
d_lo = build_direction(table, allow_short=False)["direction"].reindex(preds.index)

ls = long_short_backtest(d_ls, pred_vol, next_ret, target_ann_vol=TARGET_ANN_VOL,
                          max_long=1.5, max_short=-1.0, cost_bps=COST_BPS_FUT,
                          rf_annual=RF_ANNUAL, div_yield=DIV_YIELD,
                          deadband=0.10, stop_drawdown=-0.25)
lo = long_short_backtest(d_lo, pred_vol, next_ret, target_ann_vol=TARGET_ANN_VOL,
                          max_long=1.5, cost_bps=COST_BPS_FUT,
                          rf_annual=RF_ANNUAL, div_yield=DIV_YIELD,
                          deadband=0.10, stop_drawdown=-0.25)

print("B -- LONG/SHORT   (Sharpe is EXCESS of the risk-free rate)\\n")
print(pd.DataFrame([
    summarize(bt_v2["strategy_return"], RF_ANNUAL, label="overlay, no direction"),
    summarize(lo["strategy_return"], RF_ANNUAL, label="directional, long-only"),
    summarize(ls["strategy_return"], RF_ANNUAL, label="directional, LONG/SHORT"),
    summarize(ls["buy_hold_return"], RF_ANNUAL, label="buy & hold (total return)"),
]).set_index("label")[["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "total_return"]])

print(f"\\ndays short {100*ls['is_short'].mean():.0f}%   "
      f"mean gross exposure {ls['gross_exposure'].mean():.2f}x   "
      f"mean net {ls['position'].mean():+.2f}x")
print("Excess-of-cash Sharpe matters here: a book that sits in cash half the time")
print("would otherwise post a flattering ratio earned on T-bills.")
'''),
    code('''
hold = 5
pred_rv5 = pd.Series(np.exp(preds5["model"]) * preds5["smearing"], index=preds5.index)
realized_var = table["target_rvar_h5"].reindex(pred_rv5.index)
iv = table["iv_daily"].reindex(pred_rv5.index)
trailing = np.exp(table["log_rv_w"]).reindex(pred_rv5.index)

ok = iv.notna() & pred_rv5.notna() & realized_var.notna() & trailing.notna()
iv, pred_rv5, realized_var, trailing = iv[ok], pred_rv5[ok], realized_var[ok], trailing[ok]

kw = dict(hold_days=hold, cost_vol_pts=0.005, risk_fraction=0.15, cap_multiple=3.0)
always   = vrp_backtest(iv, iv, realized_var, entry_z=-1e9, **kw)
naive_t  = vrp_backtest(iv, trailing, realized_var, **kw)
modelled = vrp_backtest(iv, pred_rv5, realized_var, **kw)

print("C -- VARIANCE RISK PREMIUM CARRY\\n")
print(pd.DataFrame([
    summarize(always["strategy_return"],   label="always short variance (no timing)"),
    summarize(naive_t["strategy_return"],  label="timed off trailing realized vol"),
    summarize(modelled["strategy_return"], label="timed off the model"),
]).set_index("label")[["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "skew", "worst_day"]])

print(f"\\nmean IV/realized ratio: {(modelled['iv_ann']/modelled['realized_rv_ann']).mean():.3f}")
print(f"periods where realized exceeded implied: {(modelled['realized_rv_ann']>modelled['iv_ann']).mean():.1%}")
print("\\nThe model must beat BOTH rows above it. The premium itself is free to")
print("anyone willing to be short vol; timing it is the only claim being made.")
'''),
    md("""
Short variance is a negatively-skewed carry trade: many small gains, rare very
large losses. Check the `skew` and `worst_day` columns, and check whether your
sample spans **March 2020** — a Sharpe computed over a period with no volatility
crisis in it is close to meaningless for this strategy. The `cap_multiple`
assumes you buy wings (a strangle, not a naked straddle); those wings cost real
premium that this backtest only approximates.
"""),
    code('''
crisis = slice("2020-02-01", "2020-05-31")
if modelled.loc[crisis].shape[0] > 10:
    print("MARCH 2020 STRESS TEST\\n")
    print(pd.DataFrame([
        summarize(modelled["strategy_return"].loc[crisis], label="VRP leg"),
        summarize(ls["strategy_return"].loc[crisis],       label="long/short"),
        summarize(bt_v2["strategy_return"].loc[crisis],    label="vol overlay"),
        summarize(bt_v2["buy_hold_return"].loc[crisis],    label="buy & hold"),
    ]).set_index("label")[["total_return", "max_drawdown", "worst_day"]])
else:
    print("Sample does not span the 2020 crisis -- raise PRICE_YEARS before trusting the VRP leg.")
'''),
    md("## 11. Blend, and save everything"),
    code('''
blended = combine({"ls": ls["strategy_return"], "vrp": modelled["strategy_return"]},
                  {"ls": 0.6, "vrp": 0.4})
corr = pd.DataFrame({"a": ls["strategy_return"],
                     "b": modelled["strategy_return"]}).dropna().corr().iloc[0, 1]

results = pd.DataFrame([
    summarize(bt_v1["strategy_return"], RF_ANNUAL,  label="A. overlay, v1 config"),
    summarize(bt_v2["strategy_return"], RF_ANNUAL,  label="A. overlay, v2 config"),
    summarize(lo["strategy_return"], RF_ANNUAL,     label="B. directional long-only"),
    summarize(ls["strategy_return"], RF_ANNUAL,     label="B. directional long/short"),
    summarize(modelled["strategy_return"],          label="C. VRP carry"),
    summarize(blended,                              label="60/40 blend of B and C"),
    summarize(ls["buy_hold_return"], RF_ANNUAL,     label="buy & hold"),
]).set_index("label")

print(results[["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "total_return"]])
print(f"\\ncorrelation between the long/short and VRP legs: {corr:+.3f}")

results.to_csv(WORK / "results_summary.csv")
preds.to_csv(WORK / "walk_forward_predictions.csv")
print(f"\\nsaved to {WORK}")
'''),
    code('''
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=False)

for name, s in [("A. overlay (v1 bugs)", bt_v1), ("A. overlay (fixed)", bt_v2),
                ("B. long/short", ls)]:
    axes[0].plot(s["strategy_equity"], lw=1.3, label=name)
axes[0].plot(bt_v2["buy_hold_equity"], lw=1.3, ls="--", color="k", label="buy & hold")
axes[0].set_title("Index strategies, net of costs, financing and carry")
axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].plot(modelled["strategy_equity"], lw=1.3, label="C. VRP, model-timed")
axes[1].plot(always["strategy_equity"], lw=1.1, alpha=0.8, label="C. always short variance")
axes[1].set_title("Variance risk premium carry")
axes[1].legend(); axes[1].grid(alpha=0.3)

plt.tight_layout(); plt.show()
'''),
    md("""
## 12. What you can and cannot claim from this

**Claimable:**

- forecast error against **HAR-RV** with a Diebold-Mariano p-value — not against
  a single-day persistence strawman;
- the volatility overlay as a **risk overlay**: drawdown reduction at comparable
  return, financing charged, turnover controlled;
- the long/short book **only if** the IC table in section 9 shows a t-stat above
  2. Otherwise its Sharpe is a draw from noise and you should say so;
- the VRP strategy against **both** the untimed and the trailing-vol-timed
  benchmarks;
- sentiment's contribution as an ablation with a p-value, whichever way it lands.

**Not claimable:**

- that volatility targeting beats buy-and-hold on return — section 10A explains
  why it structurally cannot;
- a short-variance Sharpe from a sample with no volatility crisis in it;
- a long/short result whose underlying signal is not statistically significant.

**Not modelled here:** slippage beyond a fixed bps assumption, futures roll and
basis risk, margin calls, the real bid-ask on Nifty option strikes, and the cost
of the wings the `cap_multiple` stands in for. Each of these moves the answer in
the same direction: worse.
"""),
]

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python", "version": "3.11"}},
      "nbformat": 4, "nbformat_minor": 5}

out = ROOT / "kaggle_nifty_volatility_v2.ipynb"
out.write_text(json.dumps(nb, indent=1))
print(f"wrote {out} ({len(cells)} cells)")
