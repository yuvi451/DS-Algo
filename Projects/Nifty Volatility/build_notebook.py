#!/usr/bin/env python3
"""Generate the Colab/Kaggle notebook by inlining the src/ modules.

Keeps the v1 convention of a single self-contained notebook while the real
source of truth stays in src/, tested. Regenerate with:  python build_notebook.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.strip("\n").splitlines(keepends=True)}


# In the notebook everything lands in one namespace, so qualified cross-module
# references have to be flattened.
QUALIFIERS = ("baselines.", "model_mod.", "validation.", "vol.")

DROP = ("import baselines", "import model as model_mod", "import validation",
        "from volatility import", "import volatility as vol",
        "from __future__ import")


def module(name):
    """Inline a module: drop intra-package imports and flatten qualified refs."""
    lines = (SRC / f"{name}.py").read_text().splitlines(keepends=True)
    out, skip = [], False
    for ln in lines:
        stripped = ln.lstrip()
        if stripped.startswith("from volatility import ("):
            skip = True
            continue
        if skip:
            if stripped.rstrip().endswith(")"):
                skip = False
            continue
        if any(stripped.startswith(d) for d in DROP):
            continue
        out.append(ln)
    text = "".join(out)
    for q in QUALIFIERS:
        # word boundary on the left, or `pred_vol.index` becomes `pred_index`
        text = re.sub(r"(?<![\w.])" + re.escape(q), "", text)
    # collapse the blank line left where an inner import was removed
    text = re.sub(r"\n{3,}(\s+)([a-z])", r"\n\n\1\2", text)
    return f"# ===== src/{name}.py =====\n" + text


cells = [
    md("""
# Sentiment-Driven Nifty Volatility Prediction — v2

Rebuild after a critical review of v1's backtest. The full diagnosis is in
`CRITICAL_ANALYSIS.md`; the three-line version:

- v1 sized positions by dividing a target vol by a **Garman-Klass** forecast,
  which measures intraday vol only. The traded return is close-to-close and
  includes the overnight gap → every position ~1.24x too big.
- `exp(mean of log vol)` is the median, not the mean → another ~1.09x.
- Daily rebalancing off a noisy daily forecast at 7.5 bps cost ~3.5%/yr.

Predicted over-leverage 1.35x; leverage backed out of v1's own reported
results 1.31x. That accounts for the loss to buy-and-hold.

**And fixing it is not enough.** Sharpe is invariant to leverage, so a
long-only index position sized by a vol forecast has no expected-return edge.
The forecast has to be traded against a *price* for volatility — **India VIX**
— which is what section 10 does.
"""),
    md("## 0. Setup"),
    code("!pip install -q feedparser optuna shap arch lightgbm yfinance --upgrade"),
    code("""
import warnings
warnings.filterwarnings("ignore")

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta

pd.set_option("display.width", 120)
RANDOM_SEED = 42
"""),
    md("""
## 1. Volatility estimators and unit conventions

The single most important cell in the notebook. There are two different daily
volatilities and v1 conflated them: **intraday** (what Garman-Klass measures)
and **total close-to-close** (what you actually trade). Everything downstream
works in total units, which is also what India VIX quotes in — that is what
makes the two comparable and the VRP strategy possible.
"""),
    code(module("volatility")),
    md("""
## 2. Data

`^NSEI` for prices and **`^INDIAVIX` for implied volatility**. The VIX was
missing from v1 entirely and is the biggest single omission in the project:
it is a forward-looking, market-consensus volatility forecast, published
daily and free, and it already impounds most of what news sentiment could
carry.

`simulate_market` is here so the notebook runs end to end offline.
"""),
    code(module("data")),
    code("""
prices = load_prices("^NSEI", years=8)
vix = load_india_vix(years=8)
print(prices.shape, prices.index.min().date(), "->", prices.index.max().date())
print("India VIX:", vix.shape, f"mean {vix.mean():.1f}")
prices.tail()
"""),
    md("""
## 3. News collection and FinBERT scoring

Unchanged from v1 — GDELT DOC 2.0 for backfill, live RSS going forward,
dedupe, keyword relevance filter, trading-day bucketing on the
(prev close 15:30 IST, open 09:15 IST] window, then `ProsusAI/finbert`
inference to a `polarity = P(pos) - P(neg)` score per headline.

Paste those cells from the v1 notebook here. The only thing v2 needs out of
them is a DataFrame with columns `trading_day`, `polarity`, `positive`,
`negative`. If you don't have it yet, leave `scored_news = None` — the
pipeline runs price + VIX only.
"""),
    code("""
scored_news = None   # <- v1's FinBERT output goes here
"""),
    md("""
## 4. Features

Three changes from v1, in descending order of impact:

1. **India VIX is a feature** (see above).
2. **Targets are gap-inclusive and multi-horizon.** `h=1` keeps the error
   metrics comparable with v1; `h=5` is what the weekly-expiry VRP trade needs.
   Two flavours per horizon: mean forward *log-vol* for modelling, and
   arithmetic forward *variance* for settling the variance swap.
3. **Sentiment measures intensity and surprise, not direction.** v1 fed a
   *signed* mean polarity to predict a *magnitude* — good and bad news both
   raise vol, so the sign is nearly irrelevant, and averaging ~50 headlines
   crushes the remaining variance. Missing days stay NaN instead of being
   filled with 0.0, which in v1 made "no news" indistinguishable from
   "perfectly balanced news".
"""),
    code(module("features")),
    code("""
table = build_feature_table(prices, scored_news, vix, horizons=(1, 5))
cols = feature_columns(table)
print(f"{len(cols)} features, {len(table)} rows")
print(cols)
table[["rv", "gk_vol", "iv_daily", "log_vrp", "target_log_rv_h1"]].tail()
"""),
    code("""
# The v1 bug, measured on your own data rather than assumed.
share = (table["gk_vol"] / table["rv"]).median()
print(f"median sigma_GK / sigma_total = {share:.3f}")
print(f"-> sizing off Garman-Klass over-levers by {1/share:.2f}x")
"""),
    md("""
## 5. Baselines

**HAR-RV** (Corsi 2009) is the bar that matters, not naive persistence.
`log(sigma_t)` from a single day's range is a very noisy level estimate, so
v1's "+15% vs naive" is close to free — a 5-day moving average captures most
of it with no model.

GARCH is also fixed: v1 fit close-to-close returns (forecasting *total* vol)
and scored it against a Garman-Klass *intraday* target, a near-constant log
offset of ~+0.21 that inflated its RMSE. Most of "+30.8% vs GARCH" was that
unit error.
"""),
    code(module("baselines")),
    md("## 6. Model\n\nOne real bug fixed — see the docstring."),
    code(module("model")),
    md("""
## 7. Walk-forward validation

Adds a **Diebold-Mariano test** with Newey-West standard errors, so "the model
beats HAR" becomes a claim with a p-value rather than a bare percentage over
24 noisy folds. Also **purges** overlapping multi-day targets at the
train/test boundary, without which the `h=5` model trains on labels built from
the data it is about to be scored on.
"""),
    code(module("validation")),
    code("""
folds = run_walk_forward(table, cols, target_col="target_log_rv_h1",
                          train_years=2, test_months=2, step_months=2,
                          n_trials=25)
preds = stack_predictions(folds)
errs = error_table(preds)
print(errs)

base = errs.loc["har", "rmse"]
print(f"\\nModel vs HAR-RV: {100*(base-errs.loc['model','rmse'])/base:+.1f}% RMSE")
dm = diebold_mariano(preds, "model", "har")
print(f"Diebold-Mariano: stat={dm['statistic']:+.2f}  p={dm['p_value']:.4f}")
print("->", "significant" if dm["p_value"] < 0.05 and dm["statistic"] < 0
      else "NOT significant -- the model does not beat HAR")
"""),
    code("""
folds5 = run_walk_forward(table, cols, target_col="target_log_rv_h5",
                           train_years=2, n_trials=25, verbose=False)
preds5 = stack_predictions(folds5)
print(error_table(preds5))
"""),
    code("""
fig, ax = plt.subplots(figsize=(13, 4))
ax.plot(preds.index, np.exp(preds["y_true"]) * np.sqrt(252), lw=1.1, label="Realized")
ax.plot(preds.index, np.exp(preds["model"]) * preds["smearing"] * np.sqrt(252),
        lw=1.1, label="LightGBM")
ax.plot(table["iv_daily"].reindex(preds.index) * np.sqrt(252), lw=0.9,
        alpha=0.7, label="India VIX (implied)")
ax.set_title("Walk-forward forecast vs realized, annualized")
ax.legend(); ax.grid(alpha=0.3); plt.show()
"""),
    md("""
## 8. Explainability — and a better question than SHAP share

v1 reported "sentiment contributes 0.0% of total feature importance" and
stopped. But SHAP share describes *this fitted model*, not the data: when
sentiment features are noisy and partly collinear with price features, greedy
tree splitting simply never selects them and their SHAP mass is zero by
construction.

The decision-useful question is whether out-of-sample error gets worse when
you remove them. `incremental_value` runs that ablation and attaches a
p-value. It may still come back negative — that is a respectable finding, and
a tested negative beats an untestable SHAP share.
"""),
    code(module("explain")),
    code("""
final = table.dropna(subset=["target_log_rv_h1"])
cut = int(len(final) * 0.85)
params = tune(final[cols].iloc[:cut], final["target_log_rv_h1"].iloc[:cut],
              final[cols].iloc[cut:], final["target_log_rv_h1"].iloc[cut:], n_trials=30)
final_model = fit(final[cols], final["target_log_rv_h1"], params, val_fraction=0.15)

imp = importance(compute_shap(final_model, final[cols].iloc[-500:]), cols)
print(group_shares(imp).round(1).to_string(), "\\n")
print(imp.head(12).to_string(index=False))
"""),
    code("""
sent_cols = [c for c in cols if c.startswith(("sent_", "news_vol", "has_news"))]
if sent_cols:
    base_cols = [c for c in cols if c not in sent_cols]
    print(incremental_value(table, base_cols, sent_cols, n_trials=10, train_years=2))
else:
    print("No sentiment features wired in -- see section 3.")
"""),
    md("""
## 9. Backtest 1 — volatility-targeted index exposure

v1's idea, repaired: correct units, smearing applied, financing charged on
borrowed exposure and cash credited when under-invested, and a no-trade band
with partial adjustment instead of chasing a noisy daily target.

**This will not make money and is not supposed to.** Sharpe is invariant to
leverage, so the only thing that moves it is `Cov(1/sigma_hat, r_next)` — and
the model forecasts volatility, not returns. Treat it as a risk overlay and
claim the drawdown, not the return.
"""),
    code(module("backtest")),
    code("""
next_ret = table["log_return"].shift(-1)
pred_vol = pd.Series(np.exp(preds["model"]) * preds["smearing"], index=preds.index)

# v1's configuration, for comparison: GK units, no smearing, daily rebalance,
# free leverage.
gk_ratio = (table["gk_vol"] / table["rv"]).reindex(preds.index).median()
pred_vol_v1 = pred_vol * gk_ratio / preds["smearing"]

bt_v1 = vol_target_backtest(pred_vol_v1, next_ret, target_ann_vol=0.16,
                             max_leverage=2.0, rf_annual=0.0, deadband=0.0)
bt_v2 = vol_target_backtest(pred_vol, next_ret, target_ann_vol=0.12,
                             max_leverage=1.5, rf_annual=0.065, deadband=0.10)

print(pd.DataFrame([
    summarize(bt_v1["strategy_return"], label="v1 config"),
    summarize(bt_v2["strategy_return"], label="v2 config"),
    summarize(bt_v2["buy_hold_return"], label="buy & hold"),
]).set_index("label")[["cagr", "ann_vol", "sharpe", "max_drawdown", "total_return"]])

print(f"\\nmean position  v1={bt_v1['position'].mean():.2f}x  v2={bt_v2['position'].mean():.2f}x")
print(f"cost drag/yr   v1={252*bt_v1['cost'].mean():.2%}  v2={252*bt_v2['cost'].mean():.2%}")
"""),
    code("""
fig, ax = plt.subplots(figsize=(13, 4))
ax.plot(bt_v1["strategy_equity"], label="v1 config", lw=1.2)
ax.plot(bt_v2["strategy_equity"], label="v2 config", lw=1.2)
ax.plot(bt_v2["buy_hold_equity"], label="Buy & hold", lw=1.2)
ax.set_title("Vol-targeted index exposure, net of costs and financing")
ax.legend(); ax.grid(alpha=0.3); plt.show()
"""),
    md("""
## 10. Backtest 2 — variance risk premium carry

Where the forecast actually pays. India VIX prices *implied* volatility, the
model forecasts *realized* volatility, and the spread between them is the
variance risk premium. Selling variance harvests it; the model's job is to
size the trade by how rich the premium is relative to the forecast.

That converts the volatility model from a position-sizing input — where
section 9 shows its skill is nearly worthless — into a **pricing** input,
where every improvement in forecast RMSE maps onto P&L.

The model must beat **both** benchmarks below. The premium itself is free to
anyone willing to be short vol; timing it is the claim.
"""),
    code("""
hold = 5
pred_rv5 = pd.Series(np.exp(preds5["model"]) * preds5["smearing"], index=preds5.index)
realized_var = table["target_rvar_h5"].reindex(pred_rv5.index)
iv = table["iv_daily"].reindex(pred_rv5.index)
trailing = np.exp(table["log_rv_w"]).reindex(pred_rv5.index)

ok = iv.notna() & pred_rv5.notna() & realized_var.notna() & trailing.notna()
iv, pred_rv5, realized_var, trailing = iv[ok], pred_rv5[ok], realized_var[ok], trailing[ok]

kw = dict(hold_days=hold, cost_vol_pts=0.005, risk_fraction=0.15, cap_multiple=3.0)
always = vrp_backtest(iv, iv, realized_var, entry_z=-1e9, **kw)
naive_timed = vrp_backtest(iv, trailing, realized_var, **kw)
modelled = vrp_backtest(iv, pred_rv5, realized_var, **kw)

print(pd.DataFrame([
    summarize(always["strategy_return"], label="always short variance"),
    summarize(naive_timed["strategy_return"], label="timed off trailing realized vol"),
    summarize(modelled["strategy_return"], label="timed off the model"),
]).set_index("label")[["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "skew", "worst_day"]])
"""),
    md("""
**Before quoting any of this.** Short variance is a negatively-skewed carry
trade: many small gains, rare very large losses. A Sharpe computed over a
sample with no volatility crisis in it is close to meaningless here — check
that your window spans March 2020 and look at the drawdown through it. Report
skew and worst day alongside the Sharpe, and note that `cap_multiple` assumes
you are buying wings, which costs real premium the backtest only approximates.
"""),
    code("""
fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
axes[0].plot(modelled["iv_ann"], label="India VIX (implied)", lw=1)
axes[0].plot(modelled["pred_rv_ann"], label="Model forecast RV", lw=1)
axes[0].plot(modelled["realized_rv_ann"], label="Realized RV", lw=0.9, alpha=0.7)
axes[0].set_title("Implied vs forecast vs realized"); axes[0].legend(); axes[0].grid(alpha=0.3)
axes[1].plot(modelled["position"], lw=1, color="tab:purple")
axes[1].axhline(0, color="k", lw=0.6)
axes[1].set_title("Position (+ = short variance)"); axes[1].grid(alpha=0.3)
plt.tight_layout(); plt.show()
"""),
    md("""
## 11. Blend

The two legs are close to uncorrelated — one is long equity beta, the other is
short a variance premium — so blending them is the cheapest Sharpe improvement
available here.
"""),
    code("""
blended = combine({"index": bt_v2["strategy_return"], "vrp": modelled["strategy_return"]},
                  {"index": 0.7, "vrp": 0.3})
corr = pd.DataFrame({"a": bt_v2["strategy_return"],
                     "b": modelled["strategy_return"]}).dropna().corr().iloc[0, 1]

print(pd.DataFrame([
    summarize(bt_v2["strategy_return"], label="index leg"),
    summarize(modelled["strategy_return"], label="VRP leg"),
    summarize(blended, label="70/30 blend"),
    summarize(bt_v2["buy_hold_return"], label="buy & hold"),
]).set_index("label")[["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown"]])
print(f"\\nleg correlation = {corr:+.3f}")
"""),
    md("""
## 12. What to claim

Claimable:

- forecast error against **HAR-RV** with a DM p-value — not against a
  single-day persistence strawman;
- the vol-target overlay as a **risk overlay**: drawdown reduction at
  comparable return, financing charged, turnover controlled;
- the VRP strategy against **both** the untimed and the trailing-vol-timed
  benchmarks;
- sentiment's contribution as an ablation with a p-value, whichever way it
  goes.

Not claimable:

- that vol targeting beats buy-and-hold on return — section 9 explains why it
  structurally cannot;
- a short-variance Sharpe from a sample with no volatility crisis in it;
- anything at all from `simulate_market`.
"""),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = ROOT / "nifty_volatility_v2.ipynb"
out.write_text(json.dumps(nb, indent=1))
print(f"wrote {out} ({len(cells)} cells)")
