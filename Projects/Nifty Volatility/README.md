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
src/signals.py      directional signals + information-coefficient test
src/backtest.py     vol overlay, directional (futures carry), VRP carry
src/explain.py      SHAP, and an ablation test with a p-value
src/data.py         yfinance loaders + a synthetic market for offline runs
tests/              35 tests; several pin the v1 bugs directly
run_pipeline.py     end-to-end: validation, all three backtests, the blend

kaggle_nifty_volatility_v2.ipynb   <- run this on Kaggle, on real data
nifty_volatility_v2.ipynb          same pipeline, Colab-oriented
build_kaggle_notebook.py           regenerates the Kaggle notebook from src/
```

## Training on real data (Kaggle)

Upload `kaggle_nifty_volatility_v2.ipynb`, then in the right-hand panel:

1. **Settings → Internet → On** (needed for yfinance, GDELT, HuggingFace;
   Kaggle asks for phone verification).
2. **Settings → Accelerator → GPU T4 x2** — only for the FinBERT step. Set
   `RUN_NEWS = False` in the config cell to skip it and run on CPU.

Runtime is ~5 minutes without news, 25–40 with the full GDELT backfill. Scored
headlines are cached to `/kaggle/working/scored_news.parquet`, so re-runs skip
the slow part. Results land in `results_summary.csv` and
`walk_forward_predictions.csv`.

### If yfinance fails

It usually works on Kaggle, but Yahoo rate-limits datacenter IP ranges and
Kaggle runners sit in those ranges — a run can return 429 or an empty frame on
a day when the same call succeeds from a laptop. The loader tries three sources
in order: **mounted CSV → yfinance → Stooq** (Stooq carries the Nifty index but
not India VIX).

The CSV route is the only one that cannot be throttled, so use it if the run
matters: *Add Data* → search for a Nifty 50 and an India VIX dataset → set
`NIFTY_CSV` / `VIX_CSV` in the config cell to the mounted paths. Column naming
is handled tolerantly — Yahoo's `Adj Close`, NSE's `dd-mm-yyyy` dates and
`"21,880.90"` thousands separators all parse.

**India VIX is the dependency that matters.** Without it the VRP strategy — the
only leg with a real expected-return edge — cannot run at all. The notebook
detects this and skips that section rather than producing a silently empty one.

## The three strategies

| | What it is | Honest expectation |
|---|---|---|
| **A. Volatility overlay** | Long-only index, sized inversely to predicted vol | Will **not** beat buy-and-hold on return. Sharpe is invariant to leverage. Claim the drawdown. |
| **B. Directional** | Side from momentum + VRP + sentiment; size from the vol model. **Long-only by default** | Only as good as the directional signal. Check the IC t-stat first — under 2 and the curve is noise. |
| **C. VRP carry** | Sell variance when India VIX is rich vs the model's forecast | The only leg with a real expected-return edge. Negatively skewed; needs a crisis in the sample to be believed. |

### On shorting — off by default

`ALLOW_SHORT = False` in the notebook, `--short` to enable in `run_pipeline.py`.

The short leg rides entirely on the directional signals, whose realistic daily
information coefficients are 0.02–0.05. The notebook prints an **IC table with
a Newey-West t-stat before any equity curve**; if the blended signal's t-stat is
below 2, shorting buys turnover, financing drag and tail risk in exchange for
noise, and the default keeps it switched off.

The code is kept rather than deleted because that call depends on data this
repo has not been run against. One flag is not complexity; deleting it would
mean you cannot check.

If you do enable it: you cannot short the cash index in India, so shorting means
futures. A short gives up the dividend yield and collects the risk-free rate on
both its capital and the short proceeds, while fighting the index's positive
drift — `futures_carry` models this, and it is a structural headwind. A short
book also gets a drawdown stop, because losses on a short are unbounded.

Sharpe and Sortino are reported **in excess of the risk-free rate**. A
directional book sits in cash much of the time, and without that subtraction a
strategy that is mostly T-bills posts a spectacular-looking ratio.

## Running it

```bash
pip install yfinance lightgbm optuna shap arch scikit-learn pandas numpy pytest

python -m pytest tests/ -q          # 35 tests, no network needed
python run_pipeline.py              # live data; falls back to synthetic
python run_pipeline.py --synthetic  # force the offline market
python run_pipeline.py --garch      # add the GARCH baseline (slow)
python run_pipeline.py --short      # enable the short leg
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
- the long/short book **only if** its information coefficient is significant;
- sentiment's contribution as an ablation result with a p-value, whichever way
  it comes out.

Not claimable:

- any Sharpe from `--synthetic`, and the VRP one especially — the simulator's
  premium is trivially timeable and the output says so;
- that vol targeting beats buy-and-hold on return;
- a short-variance Sharpe from a sample with no volatility crisis in it;
- a long/short result whose underlying signal has a t-stat below 2.

## Status

Not run on live market data. Yahoo Finance is blocked by network policy in the
environment this was built in, so every number here comes from either the
arithmetic in CRITICAL_ANALYSIS.md section 1 or the synthetic market. The code
is tested; the strategy is not yet validated. Run it on Colab or Kaggle, where
`^NSEI` and `^INDIAVIX` are reachable.
