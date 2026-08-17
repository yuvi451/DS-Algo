# Sentiment-Driven Nifty Volatility Prediction — Project Plan

## 1. Objective

Predict next-day realized volatility of the Nifty 50 index using sentiment features extracted from Indian financial news, and validate the signal with a proper walk-forward backtest — not just a static error metric.

**Framing:** for each trading day, aggregate all news published between the previous close (3:30 PM IST) and today's market open (9:15 AM IST) into a feature vector, and predict that day's realized volatility using gradient boosting.

This is deliberately scoped to volatility (not price direction) because volatility is a well-established, tractable forecasting target in quant finance, and because a single index avoids the entity-linking problem of matching news to specific stocks.

---

## 2. Pipeline overview

```
News sources (GDELT + live RSS)        Price data (yfinance, ^NSEI OHLC)
            |                                       |
            v                                       |
Preprocess & sentiment (filter, dedupe, FinBERT)     |
            |                                       |
            +-------------------+-------------------+
                                v
                   Daily feature table
              (sentiment features + price/vol lags)
                                |
                                v
                  Gradient boosting model
                  (LightGBM, Optuna-tuned)
                                |
                                v
              Walk-forward validation & backtest
           (vs. naive persistence + GARCH baseline,
                  Sharpe / drawdown vs buy-hold)
```

---

## 3. Data sources

### Price data
- **Source:** `yfinance`, ticker `^NSEI`
- **Range:** 5+ years of daily OHLC
- **Why yfinance:** free, no key required, avoids fighting NSE's own bot protection/session tokens

### News data

| Source | Use | Limitation |
|---|---|---|
| GDELT Project | Historical backfill, includes a built-in tone/sentiment score for cross-checking | Coverage of Indian outlets is decent but not exhaustive |
| Moneycontrol / Economic Times / LiveMint / Business Standard RSS | Live, ongoing collection, headline + timestamp | RSS only shows recent items — no historical backfill |
| Google News RSS (query-filtered, e.g. `?q=Nifty`) | Broad supplementary live source | Noisier, mixes unrelated mentions |

**Practical approach:** use GDELT to build the historical training set (past years of Nifty-relevant news + tone), then run RSS feeds live going forward — this both extends the dataset and creates a genuine out-of-sample test on data collected *after* the model was built.

### Storage
SQLite (or Parquet), two tables:
- `prices(date, open, high, low, close, volume)`
- `news(headline, source, published_at, url)`

---

## 4. Preprocessing

- **Dedupe** near-identical headlines — wire content gets republished across outlets; without deduping, "article count" mostly measures republishing, not distinct news.
- **Relevance filter:** keyword filter on Nifty, Sensex, RBI, budget, inflation, FII/DII flows, and top Nifty50 constituent names — GDELT and Google News otherwise return a lot of noise.
- **Trading-day bucketing:** news published between previous close (3:30 PM IST) and today's open (9:15 AM IST) is assigned to *today*.

---

## 5. Sentiment scoring

- **Model:** FinBERT via HuggingFace `transformers` — pretrained, inference only, no training required
- **Output:** collapse the positive/negative/neutral probability triple into a single polarity score: `P(positive) − P(negative)`
- Runs fine on a free Colab T4 GPU for batch inference

---

## 6. Feature table (per trading day)

**Sentiment features:**
- Mean sentiment, sentiment std/dispersion
- Article count, % positive, % negative
- 3-day and 5-day rolling means (news effects aren't always same-day)

**Price / autoregressive features:**
- Yesterday's Garman-Klass volatility
- 5-day average volatility
- Yesterday's return
- Day-of-week (documented Monday effect in Indian markets)

> Volatility is highly autocorrelated, so the naive baseline ("tomorrow's vol ≈ today's vol") is already strong. Sentiment features need to earn their place *on top of* the autoregressive features, not instead of them — this is why the price-based lags are included as features, not just as a baseline to beat.

---

## 7. Target variable

**Garman-Klass volatility**, computed from next day's OHLC (no intraday/tick data needed):

```
σ²_GK = 0.5 · (ln(H/L))² − (2·ln2 − 1) · (ln(C/O))²
```

More informative than a plain `std(returns)` estimate, and a good detail to know cold in an interview.

---

## 8. Model

- **Algorithm:** LightGBM (or XGBoost — either is fine; LightGBM is the more common current default and handles categorical features more natively)
- **Hyperparameter tuning:** Optuna (Bayesian search) rather than Grid Search
- **Optional:** `objective='quantile'` at a few quantiles (0.1 / 0.5 / 0.9) to get an uncertainty band — cheap to add for gradient boosting, unlike for deep learning

---

## 9. Validation strategy

- **Walk-forward validation:** train on year 1, test on the next ~2 months, slide forward, repeat. Never a random shuffle split — that's the single most common way this kind of project quietly leaks future information into training.
- **Baselines to beat:**
  - Naive persistence (tomorrow's vol = today's vol)
  - GARCH(1,1), via the `arch` package
- Report RMSE/MAE on **log-volatility** (volatility is right-skewed and strictly positive) — and report the margin by which the model beats both baselines. That margin is the actual headline result, not a standalone error number.

---

## 10. Backtest

- **Strategy:** simple volatility-targeting rule — position size scaled inversely to predicted volatility (larger position when low vol predicted, smaller when high vol predicted)
- **Metrics:** Sharpe ratio and max drawdown vs. buy-and-hold Nifty
- **Costs:** apply a reasonable transaction cost assumption (e.g. 5–10 bps per trade) — a backtest without costs is not a credible backtest

---

## 11. Explainability

- **TreeSHAP** via the `shap` package — fast and near-free for gradient boosting (unlike SHAP on deep nets)
- Shows which features (which sentiment lag, which price lag) actually drive predictions — useful both for the writeup and for sanity-checking that the model isn't just learning volatility persistence and ignoring sentiment entirely

---

## 12. Tech stack

| Purpose | Tool |
|---|---|
| Data manipulation | pandas, numpy |
| Price data | yfinance |
| News collection | feedparser (RSS), GDELT export |
| Sentiment | transformers (FinBERT) |
| Model | lightgbm |
| Hyperparameter tuning | optuna |
| Explainability | shap |
| Stats / baselines | statsmodels (ADF test), arch (GARCH) |
| Storage | SQLite / Parquet |
| Compute | Google Colab (free T4 tier is sufficient) |

---

## 13. Timeline (solo, part-time, ~4 weeks)

| Week | Focus |
|---|---|
| 1 | Collection pipeline: price data + GDELT historical backfill + live RSS collector running |
| 2 | Preprocessing, relevance filtering, sentiment scoring, feature table, target construction |
| 3 | Baselines (naive + GARCH), LightGBM model, Optuna tuning, walk-forward validation |
| 4 | Backtest, SHAP explainability, writeup |

---

## 14. What makes this credible on a resume (vs. the earlier three projects)

- **Honest metrics:** RMSE/MAE on log-volatility, not a fabricated "accuracy %" that conflates regression and classification
- **Proper walk-forward validation**, explicitly stated — not a random train/test split
- **Beats named baselines** (naive persistence, GARCH) by a stated margin, not just "outperformed baseline models"
- **SHAP-based feature importance**, showing sentiment actually contributes beyond price autocorrelation
- **A real backtest** with Sharpe ratio, max drawdown, and transaction costs — not just a prediction error number
