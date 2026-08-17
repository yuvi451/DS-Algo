# Sentiment-Driven Nifty Volatility Prediction

Predicts next-day realized volatility of the Nifty 50 index from sentiment
features extracted from Indian financial news, validated with a proper
walk-forward backtest against naive persistence and GARCH(1,1) baselines.

For each trading day, all news published between the previous close
(3:30 PM IST) and today's market open (9:15 AM IST) is aggregated into a
feature vector and used to predict that day's realized (Garman-Klass)
volatility with a LightGBM model tuned by Optuna.

See `nifty_volatility_prediction_plan.md` (project root of this task) for
the full design rationale. This directory implements it.

## Getting the trained model + evaluations

The primary deliverable is a **self-contained Kaggle notebook**:
[`notebooks/nifty_volatility_prediction.ipynb`](notebooks/nifty_volatility_prediction.ipynb).
Upload it to Kaggle, turn on **Internet** and a **GPU (T4)** accelerator in
the notebook's settings, and run all cells top to bottom. It:

1. Downloads 5 years of Nifty 50 OHLC via `yfinance`
2. Backfills historical news via the GDELT DOC 2.0 API and pulls today's
   live headlines via RSS (Moneycontrol, Economic Times, LiveMint,
   Business Standard, Google News)
3. Dedupes, relevance-filters, and buckets news into trading-day windows
4. Scores every headline with FinBERT (`ProsusAI/finbert`) on GPU
5. Builds the daily sentiment + price feature table and the Garman-Klass
   volatility target
6. Fits naive persistence and GARCH(1,1) baselines
7. Tunes and trains LightGBM with Optuna, plus optional quantile models
   for an uncertainty band
8. Runs walk-forward validation (expanding ~1yr train / ~2mo test windows)
   and reports RMSE/MAE on log-volatility, with the % improvement over
   each baseline
9. Runs a volatility-targeting backtest with transaction costs, reporting
   Sharpe ratio and max drawdown vs. buy-and-hold
10. Runs TreeSHAP to show which features (sentiment vs. price lags)
    actually drive predictions

The notebook is generated from the reusable modules in `src/` (see below)
by `notebooks/build_notebook.py`, so the two never drift apart — regenerate
the notebook after changing anything under `src/` by re-running that
script.

## Repository layout

```
src/
  config.py                  Shared constants (tickers, keywords, RSS feeds, FinBERT model)
  data/
    price_data.py            yfinance OHLC + Garman-Klass volatility target/features
    gdelt_collector.py       Historical news backfill via GDELT DOC 2.0 API
    rss_collector.py         Live RSS collection (Moneycontrol, ET, LiveMint, BS, Google News)
  preprocessing/
    dedupe.py                Exact + fuzzy near-duplicate headline removal
    relevance_filter.py      Keyword relevance filter
    bucketing.py             Trading-day windowing (prev close -> today's open, IST)
  sentiment/
    finbert.py                FinBERT batch inference -> polarity score
  features/
    feature_table.py         Daily sentiment aggregates + rolling windows, joined to price features
  models/
    baselines.py             Naive persistence + rolling GARCH(1,1)
    lightgbm_model.py        LightGBM + Optuna tuning + quantile models
  validation/
    walk_forward.py          Walk-forward fold generation, evaluation, summary metrics
  backtest/
    strategy.py               Vol-targeting position sizing, costs, Sharpe, max drawdown
  explain/
    shap_explain.py          TreeSHAP feature importance
notebooks/
  build_notebook.py          Assembles the src/ modules into the self-contained Kaggle notebook
  nifty_volatility_prediction.ipynb   The Kaggle notebook itself
```

## Running locally instead of on Kaggle

```bash
pip install -r requirements.txt
python -c "
from src.data.price_data import fetch_price_data, build_price_features
from src.config import TICKER, PRICE_LOOKBACK_YEARS
prices = build_price_features(fetch_price_data(TICKER, PRICE_LOOKBACK_YEARS))
print(prices.tail())
"
```

Every stage in `src/` is a plain, importable function — the notebook is
just glue code and markdown around them, so the same modules work in a
script, a different notebook, or a scheduled job (e.g. a daily cron run of
`src/data/rss_collector.py` to keep extending the live dataset).

## Honest-metrics checklist

- RMSE/MAE reported on **log-volatility**, not a fabricated "accuracy %"
- **Walk-forward validation** only — never a random shuffle split
- Beats **named baselines** (naive persistence, GARCH(1,1)) by a stated
  margin, not just "outperforms a baseline"
- **SHAP-based feature importance** showing sentiment's contribution
  beyond price autocorrelation
- **Real backtest**: Sharpe ratio, max drawdown, and transaction costs
