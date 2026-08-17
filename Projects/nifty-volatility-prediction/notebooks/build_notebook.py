"""Assembles the reusable src/ modules into a single self-contained Kaggle
notebook (no local imports -- Kaggle only uploads the .ipynb itself, so
every module's source is inlined as a code cell).

Run from the project root:
    python notebooks/build_notebook.py
"""

import pathlib

import nbformat as nbf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT_PATH = ROOT / "notebooks" / "nifty_volatility_prediction.ipynb"


def read(rel_path: str) -> str:
    return (SRC / rel_path).read_text()


def strip_local_imports(code: str) -> str:
    """Drop `from src...import` lines -- the notebook inlines everything in
    dependency order in one flat namespace instead."""
    lines = [ln for ln in code.splitlines() if not ln.strip().startswith("from src.")]
    return "\n".join(lines).strip() + "\n"


nb = nbf.v4.new_notebook()
cells = []


def md(text: str):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text: str):
    cells.append(nbf.v4.new_code_cell(text.strip() + "\n"))


# ---------------------------------------------------------------------------
md(r"""# Sentiment-Driven Nifty Volatility Prediction

Predicts next-day realized (Garman-Klass) volatility of the Nifty 50 index
from sentiment features extracted from Indian financial news, validated
with **walk-forward** backtesting against naive persistence and GARCH(1,1)
baselines.

**Framing:** for each trading day, aggregate all news published between the
previous close (3:30 PM IST) and today's market open (9:15 AM IST) into a
feature vector, and predict that day's realized volatility with LightGBM.

**Before running:** in the notebook's right-hand Settings panel, turn on
**Internet** (required for `yfinance`, GDELT, RSS, and downloading FinBERT)
and set the **Accelerator** to **GPU T4 x2** or **GPU T4 x1** (FinBERT
inference is much faster on GPU, though it will fall back to CPU
automatically if none is available). Then **Run All**.

## Pipeline

```
News (GDELT historical + live RSS)        Price data (yfinance, ^NSEI OHLC)
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
                  LightGBM (Optuna-tuned)
                                |
                                v
         Walk-forward validation & backtest
      (vs. naive persistence + GARCH, Sharpe/drawdown)
```
""")

# ---------------------------------------------------------------------------
md("## 0. Setup")
code(r"""
!pip install -q feedparser optuna shap arch lightgbm yfinance --upgrade
""")

code(r"""
import warnings
warnings.filterwarnings("ignore")

import re
import time
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pytz
import requests
import feedparser
import torch
import lightgbm as lgb
import optuna
import shap
from dateutil.relativedelta import relativedelta
from arch import arch_model
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import yfinance as yf

optuna.logging.set_verbosity(optuna.logging.WARNING)
pd.set_option("display.width", 140)
plt.rcParams["figure.figsize"] = (11, 4.5)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
""")

code(f"""
# --- config (src/config.py) ---
{strip_local_imports(read('config.py'))}
""")

code(r"""
# News backfill matches the price lookback (PRICE_LOOKBACK_YEARS, see config
# cell above) so sentiment features are available across the full training
# history -- otherwise the years without matching news just fall back to
# price-only features, which undercuts the whole point of this project.
# GDELT backfill walks this range in weekly chunks (~1 request/chunk), so
# this takes longer to collect (~10-15 min for 5 years) than a shorter
# window would; shrink PRICE_LOOKBACK_YEARS in the config cell for a faster
# smoke-test run.
GDELT_START_DATE = (datetime.utcnow() - timedelta(days=PRICE_LOOKBACK_YEARS * 365)).strftime("%Y-%m-%d")
GDELT_END_DATE = datetime.utcnow().strftime("%Y-%m-%d")
""")

# ---------------------------------------------------------------------------
md("""## 1. Price data

5+ years of Nifty 50 daily OHLC from `yfinance` (free, no key, avoids
fighting NSE's own bot protection). We derive the **Garman-Klass**
volatility target here too, since it only needs OHLC:

```
sigma^2_GK = 0.5 * (ln(H/L))^2 - (2*ln2 - 1) * (ln(C/O))^2
```

more informative than a plain `std(returns)` estimate.""")
code(strip_local_imports(read("data/price_data.py")))
code(r"""
prices_raw = fetch_price_data(TICKER, PRICE_LOOKBACK_YEARS)
price_features = build_price_features(prices_raw)
print(price_features.shape)
price_features.tail()
""")

# ---------------------------------------------------------------------------
md("""## 2. News collection

- **GDELT DOC 2.0 API** for historical backfill (headline + timestamp +
  source; its own tone score is aggregate-only, so every headline --
  GDELT and RSS alike -- gets scored by FinBERT below for one consistent
  signal).
- **Live RSS** (Moneycontrol, Economic Times, LiveMint, Business Standard,
  Google News) for ongoing collection. Re-running this cell on a schedule
  (e.g. a daily Kaggle job) extends the dataset going forward and doubles
  as a genuine out-of-sample test on news collected *after* the model was
  built.""")
code(strip_local_imports(read("data/gdelt_collector.py")))
code(strip_local_imports(read("data/rss_collector.py")))
code(r"""
gdelt_news = collect_gdelt_history(
    query=GDELT_QUERY,
    start_date=GDELT_START_DATE,
    end_date=GDELT_END_DATE,
    source_country=GDELT_SOURCE_COUNTRY,
    chunk_days=7,
)
print(f"GDELT: {len(gdelt_news)} articles")

rss_news = collect_rss_news(RSS_FEEDS)
print(f"RSS (live, today): {len(rss_news)} articles")

raw_news = pd.concat([gdelt_news, rss_news], ignore_index=True).drop_duplicates(subset=["url"])
print(f"Combined: {len(raw_news)} articles")
raw_news.tail()
""")

# ---------------------------------------------------------------------------
md("""## 3. Preprocessing

- **Dedupe** near-identical headlines (wire content gets republished
  across outlets; without deduping, "article count" mostly measures
  republishing, not distinct news).
- **Relevance filter** on Nifty/Sensex/RBI/budget/inflation/FII-DII/top
  constituent names.
- **Trading-day bucketing**: news published between previous close
  (3:30 PM IST) and today's open (9:15 AM IST) is assigned to *today*.""")
code(strip_local_imports(read("preprocessing/dedupe.py")))
code(strip_local_imports(read("preprocessing/relevance_filter.py")))
code(strip_local_imports(read("preprocessing/bucketing.py")))
code(r"""
news_deduped = dedupe_headlines(raw_news)
news_relevant = filter_relevant(news_deduped, RELEVANCE_KEYWORDS)
news_bucketed = bucket_news_to_trading_days(news_relevant, price_features.index)

print(f"raw={len(raw_news)}  deduped={len(news_deduped)}  relevant={len(news_relevant)}  bucketed={len(news_bucketed)}")
news_bucketed.tail()
""")

# ---------------------------------------------------------------------------
md("""## 4. Sentiment scoring (FinBERT)

`ProsusAI/finbert`, pretrained, inference only. Collapses the
positive/negative/neutral triple into a single polarity score:
`P(positive) - P(negative)`.""")
code(strip_local_imports(read("sentiment/finbert.py")))
code(r"""
finbert = FinBertScorer(batch_size=32)
scored_news = score_headlines(news_bucketed, scorer=finbert)
print(f"Device: {finbert.device}")
scored_news[["headline", "positive", "negative", "neutral", "polarity"]].tail()
""")

# ---------------------------------------------------------------------------
md("""## 5. Feature table

Sentiment: mean/std polarity, article count, %positive, %negative, plus
3-day and 5-day rolling means (news effects aren't always priced in
same-day). Price/autoregressive: yesterday's Garman-Klass vol, 5/10-day
average vol, yesterday's return, day-of-week (documented Monday effect in
Indian markets).

Volatility is highly autocorrelated, so naive persistence is already a
strong baseline -- the price lags are included as *features*, not just a
baseline to beat, so sentiment has to earn its place on top of them.""")
code(strip_local_imports(read("features/feature_table.py")))
code(r"""
feature_table = build_feature_table(price_features, scored_news)
feature_cols = get_feature_columns(feature_table)
print(f"{len(feature_cols)} features, {len(feature_table)} rows")
print(feature_cols)
feature_table[feature_cols + ["target_next_gk_vol"]].tail()
""")

# ---------------------------------------------------------------------------
md("""## 6. Baselines: naive persistence + GARCH(1,1)

Reported on **log-volatility** (right-skewed, strictly positive target).
These are the bars the LightGBM model has to clear.""")
code(strip_local_imports(read("models/baselines.py")))
code(r"""
returns_pct_full = (feature_table["log_return"] * 100).dropna()
garch_vol_forecast = fit_garch_forecast(returns_pct_full, refit_every=5)
# fit_garch_forecast(...) at date d forecasts d's own vol from history
# before d; shift(-1) realigns it to the *feature* date (T -> forecast
# for T+1), matching target_next_log_gk_vol and the naive/model forecasts.
garch_log_vol_forecast = np.log(garch_vol_forecast + 1e-8).shift(-1)
garch_log_vol_forecast.tail()
""")

# ---------------------------------------------------------------------------
md("## 7. LightGBM model + Optuna tuning")
code(strip_local_imports(read("models/lightgbm_model.py")))

# ---------------------------------------------------------------------------
md("""## 8. Walk-forward validation

Train on an expanding ~1yr window, test on the next ~2 months, slide
forward, repeat -- never a random shuffle split. Headline result: the %
improvement in RMSE over naive persistence and GARCH(1,1), not a
standalone error number.""")
code(strip_local_imports(read("validation/walk_forward.py")))
code(r"""
feature_table_wf = add_naive_forecast_column(feature_table)

wf_results = run_walk_forward(
    feature_table_wf, feature_cols,
    naive_log_vol_col="naive_log_vol",
    garch_log_vol=garch_log_vol_forecast,
    train_years=1, test_months=2, step_months=2,
    n_optuna_trials=20,
)

fold_summary = summarize_folds(wf_results)
overall = overall_metrics(wf_results)

print(f"Ran {len(wf_results)} walk-forward folds\n")
display(fold_summary)
print("\nOverall (all folds pooled):")
for k, v in overall.items():
    print(f"  {k}: {v:.5f}" if isinstance(v, float) else f"  {k}: {v}")

print(f"\nModel beats naive persistence by "
      f"{100*(overall['rmse_naive']-overall['rmse_model'])/overall['rmse_naive']:.1f}% RMSE")
print(f"Model beats GARCH(1,1) by "
      f"{100*(overall['rmse_garch']-overall['rmse_model'])/overall['rmse_garch']:.1f}% RMSE")
""")
code(r"""
fig, ax = plt.subplots()
all_preds = pd.concat([r.predictions for r in wf_results], ignore_index=True).set_index("date").sort_index()
ax.plot(all_preds.index, np.exp(all_preds["y_true_log"]), label="Realized GK vol", lw=1.5)
ax.plot(all_preds.index, np.exp(all_preds["y_pred_model_log"]), label="LightGBM forecast", lw=1)
ax.plot(all_preds.index, np.exp(all_preds["y_pred_naive_log"]), label="Naive persistence", lw=0.8, alpha=0.6)
ax.set_title("Walk-forward: predicted vs. realized next-day volatility (all test folds)")
ax.legend()
plt.show()
""")

# ---------------------------------------------------------------------------
md("""## 9. Final model (most recent window) + quantile bands

Refit on the most recent training window for the backtest and SHAP
sections below, plus a cheap 10/50/90th-percentile quantile ensemble for
an uncertainty band.""")
code(r"""
final_train = feature_table_wf.dropna(subset=["target_next_log_gk_vol"])
val_cut = int(len(final_train) * 0.85)
X_tr, y_tr = final_train[feature_cols].iloc[:val_cut], final_train["target_next_log_gk_vol"].iloc[:val_cut]
X_val, y_val = final_train[feature_cols].iloc[val_cut:], final_train["target_next_log_gk_vol"].iloc[val_cut:]

final_params = tune_hyperparameters(X_tr, y_tr, X_val, y_val, n_trials=30)
final_model = train_lgbm(final_train[feature_cols], final_train["target_next_log_gk_vol"], params=final_params)

quantile_models = train_quantile_ensemble(X_tr, y_tr, X_val, y_val, final_params)
print("Final params:", final_params)
""")

# ---------------------------------------------------------------------------
md("""## 10. Backtest

Simple volatility-targeting rule: position size scaled inversely to
predicted volatility, capped, with a 7.5 bps transaction cost per unit of
position change. Reports Sharpe ratio and max drawdown vs. buy-and-hold.""")
code(strip_local_imports(read("backtest/strategy.py")))
code(r"""
all_preds_sorted = all_preds.sort_index()
predicted_vol = np.exp(all_preds_sorted["y_pred_model_log"])
# The return realized *while holding* the position sized off predicted_vol
# for day t is the next trading day's return.
realized_next_return = feature_table_wf["log_return"].shift(-1).reindex(all_preds_sorted.index)

backtest_df = run_backtest(predicted_vol, realized_next_return,
                            target_daily_vol=0.01, max_leverage=2.0, cost_bps=7.5)
summary = backtest_summary(backtest_df)
for k, v in summary.items():
    print(f"  {k}: {v:.4f}")
""")
code(r"""
fig, ax = plt.subplots()
ax.plot(backtest_df.index, backtest_df["strategy_equity"], label="Vol-targeting strategy")
ax.plot(backtest_df.index, backtest_df["buy_hold_equity"], label="Buy & hold")
ax.set_title("Backtest equity curve (net of transaction costs)")
ax.set_ylabel("Equity (starting = 1.0)")
ax.legend()
plt.show()
""")

# ---------------------------------------------------------------------------
md("""## 11. Explainability (SHAP)

TreeSHAP on the final model, checking whether sentiment features
meaningfully contribute alongside price autocorrelation -- not just
sanity-checking that the model learned volatility persistence and ignored
sentiment.""")
code(strip_local_imports(read("explain/shap_explain.py")))
code(r"""
X_explain = final_train[feature_cols].iloc[-500:]
shap_values = compute_shap_values(final_model, X_explain)
importance = shap_feature_importance(shap_values, feature_cols)
contribution = sentiment_vs_price_contribution(importance)

print(f"Sentiment features: {contribution['sentiment_share_pct']:.1f}% of total |SHAP|")
print(f"Price features:     {contribution['price_share_pct']:.1f}% of total |SHAP|")
display(importance.head(15))

shap.summary_plot(shap_values, X_explain, show=True)
""")

# ---------------------------------------------------------------------------
md("""## 12. Results summary

Re-run cells above with more Optuna trials, or a longer `PRICE_LOOKBACK_YEARS`
(which also widens the GDELT news backfill to match), for a stronger final
result -- the defaults above are tuned for a reasonable first end-to-end
Kaggle run.""")
code(r"""
print("=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)
print(f"Walk-forward folds: {len(wf_results)}")
print(f"RMSE (log-vol)  model={overall['rmse_model']:.4f}  naive={overall['rmse_naive']:.4f}  garch={overall['rmse_garch']:.4f}")
print(f"MAE  (log-vol)  model={overall['mae_model']:.4f}  naive={overall['mae_naive']:.4f}  garch={overall['mae_garch']:.4f}")
print(f"Model vs naive:  {100*(overall['rmse_naive']-overall['rmse_model'])/overall['rmse_naive']:+.1f}% RMSE")
print(f"Model vs GARCH:  {100*(overall['rmse_garch']-overall['rmse_model'])/overall['rmse_garch']:+.1f}% RMSE")
print()
print(f"Backtest Sharpe   strategy={summary['strategy_sharpe']:.2f}  buy&hold={summary['buy_hold_sharpe']:.2f}")
print(f"Max drawdown      strategy={summary['strategy_max_drawdown']:.1%}  buy&hold={summary['buy_hold_max_drawdown']:.1%}")
print(f"Total return      strategy={summary['strategy_total_return']:.1%}  buy&hold={summary['buy_hold_total_return']:.1%}")
print()
print(f"SHAP: sentiment contributes {contribution['sentiment_share_pct']:.1f}% of total feature importance")
""")

nb["cells"] = cells
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w") as f:
    nbf.write(nb, f)

print(f"Wrote {OUT_PATH} ({len(cells)} cells)")
