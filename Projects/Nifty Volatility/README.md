# Nifty Volatility — v2

Rebuild of a sentiment-driven Nifty 50 volatility forecasting project after a
critical review of its first backtest. **Read [CRITICAL_ANALYSIS.md](CRITICAL_ANALYSIS.md)
first** — it explains what was wrong and why the strategy was changed rather
than tuned.

## The short version

The v1 backtest lost to buy-and-hold (Sharpe 0.37 vs 0.60, drawdown -28.5% vs
-16.1%) for three attributable reasons:

1. Positions were sized by dividing a target vol by a **Garman-Klass** forecast,
   which measures intraday volatility only. The traded return is close-to-close
   and includes the overnight gap, so every position was ~1.24x too big.
2. `exp(mean of log vol)` is the median, not the mean — a further ~1.09x
   over-sizing.
3. Rebalancing daily off a noisy daily forecast at 7.5 bps cost ~3.5%/yr.

Predicted over-leverage from (1) and (2): **1.35x**. Leverage backed out of the
reported results: **1.31x**.

But fixing all three does not make it profitable, because the strategy is the
wrong shape. Sharpe is invariant to leverage, so a long-only index position
sized by a volatility forecast has no expected-return edge — only a risk
overlay's drawdown benefit. To make a volatility forecast pay, trade it against
a *price for volatility*: **India VIX**, and the variance risk premium.

## Layout

```
src/volatility.py   estimators, unit conventions, smearing correction
src/features.py     price/HAR + India VIX + volatility-relevant sentiment
src/baselines.py    naive, HAR-RV (Corsi 2009), GARCH(1,1) in matched units
src/model.py        LightGBM + Optuna
src/validation.py   walk-forward, purging, Diebold-Mariano
src/backtest.py     vol-target overlay (repaired) + VRP carry (the edge)
src/explain.py      SHAP, and an ablation test with a p-value
src/data.py         yfinance loaders + a synthetic market for offline runs
tests/              19 tests; several pin the v1 bugs directly
run_pipeline.py     end-to-end: validation, both backtests, the blend
```

## Running it

```bash
pip install yfinance lightgbm optuna shap arch scikit-learn pandas numpy pytest

python -m pytest tests/ -q          # 19 tests, no network needed
python run_pipeline.py              # live data; falls back to synthetic
python run_pipeline.py --synthetic  # force the offline market
python run_pipeline.py --garch      # add the GARCH baseline (slow)
```

`run_pipeline.py` prints forecast error against HAR-RV with a Diebold-Mariano
p-value, then both backtests, then the blend.

### Wiring in sentiment

The GDELT + FinBERT collection and scoring steps are unchanged from v1. Produce
a DataFrame with `trading_day`, `polarity`, `positive`, `negative` and pass it
as the `scored_news` argument to `features.build_feature_table`. Then settle the
question with an ablation rather than a SHAP share:

```python
import explain
explain.incremental_value(table, base_cols, sentiment_cols)
# -> {'rmse_without':…, 'rmse_with':…, 'p_value':…, 'verdict':…}
```

Verified on synthetic data to detect a planted signal (p = 3e-23) and to
correctly find nothing when the news is pure noise (p = 0.17).

## What to claim, and what not to

Claimable, once you have run it on real data:

- forecast error against **HAR-RV** with a DM p-value, not against a
  single-day persistence strawman;
- the vol-target overlay as a **risk overlay** — drawdown reduction at
  comparable return, with financing charged and turnover controlled;
- the VRP strategy against **both** the untimed short-variance benchmark and a
  trailing-realized-vol-timed one;
- sentiment's contribution as an ablation result with a p-value, whichever way
  it comes out.

Not claimable:

- any Sharpe from `--synthetic`, and the VRP one especially — the simulator's
  premium is trivially timeable and the output says so;
- that vol targeting beats buy-and-hold on return;
- a short-variance Sharpe from a sample with no volatility crisis in it.

## Status

Not run on live market data. Yahoo Finance is blocked by network policy in the
environment this was built in, so every number here comes from either the
arithmetic in CRITICAL_ANALYSIS.md section 1 or the synthetic market. The code
is tested; the strategy is not yet validated. Run it on Colab or Kaggle, where
`^NSEI` and `^INDIAVIX` are reachable.
