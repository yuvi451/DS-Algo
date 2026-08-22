"""Walk-forward validation, with a significance test instead of a bare percentage.

v1's headline was "+15.0% RMSE vs naive". Across 24 folds of a noisy daily
series that number carries no error bar, and a percentage improvement over a
deliberately weak baseline is the easiest kind of result to produce by
accident. This module adds:

  * **HAR-RV** as the baseline that actually matters (see src/baselines.py);
  * a **Diebold-Mariano test** on the squared-error differential, with
    Newey-West standard errors, so "the model beats HAR" becomes a claim with a
    p-value attached;
  * per-fold smearing factors estimated on training residuals, so the level
    forecasts handed to the backtest are unbiased in the mean rather than the
    median (this is the correction v1 omitted -- see volatility.smearing_factor).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

import baselines
import model as model_mod
from volatility import smearing_factor


@dataclass
class Fold:
    fold: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    n_train: int
    n_test: int
    smearing: float
    predictions: pd.DataFrame = field(repr=False)


def generate_folds(dates: pd.DatetimeIndex, train_years: int = 2,
                   test_months: int = 2, step_months: int = 2,
                   purge: int = 0):
    """Expanding-window folds. Never a shuffle split.

    ``purge`` drops the last ``purge`` rows of each training window. With a
    multi-day target this is mandatory: the target at the final training date
    is an average over days that fall inside the test window, so without
    purging the model is trained on labels built from the data it is about to
    be scored on. For ``target_*_h{h}`` the correct value is ``h - 1``.
    """
    dates = pd.DatetimeIndex(dates)
    start = dates.min()
    train_end = start + relativedelta(years=train_years)
    while True:
        test_end = train_end + relativedelta(months=test_months)
        train_mask = (dates >= start) & (dates < train_end)
        test_mask = (dates >= train_end) & (dates < test_end)
        if purge > 0 and train_mask.sum() > purge:
            keep = np.flatnonzero(train_mask)[:-purge]
            purged = np.zeros_like(train_mask)
            purged[keep] = True
            train_mask = purged
        if test_mask.sum() == 0:
            break
        if train_mask.sum() > 0:
            yield train_mask, test_mask
        train_end = train_end + relativedelta(months=step_months)
        if train_end >= dates.max():
            break


def run_walk_forward(table: pd.DataFrame, feature_cols: list[str],
                     target_col: str = "target_log_rv_h1",
                     garch_log: pd.Series | None = None,
                     train_years: int = 2, test_months: int = 2,
                     step_months: int = 2, n_trials: int = 25,
                     retune_every: int = 4, val_fraction: float = 0.15,
                     purge: int | None = None,
                     verbose: bool = True) -> list[Fold]:
    """Expanding walk-forward over LightGBM, HAR, naive and (optionally) GARCH.

    ``retune_every`` re-runs Optuna only every k folds and reuses the params in
    between. v1 ran a fresh 20-trial study on all 24 folds, which is both slow
    and a source of fold-to-fold noise that has nothing to do with the signal.

    ``purge`` defaults to ``h - 1`` inferred from ``target_col``, which is what
    a multi-day overlapping target requires. See generate_folds.
    """
    if purge is None:
        m = re.search(r"_h(\d+)$", target_col)
        purge = (int(m.group(1)) - 1) if m else 0
    df = table.dropna(subset=[target_col]).copy()
    dates = df.index
    log_rv = df["log_rv"]
    har_X = baselines.har_design(log_rv)

    folds: list[Fold] = []
    params: dict | None = None

    for i, (train_mask, test_mask) in enumerate(
            generate_folds(dates, train_years, test_months, step_months, purge)):
        train_df, test_df = df.loc[train_mask], df.loc[test_mask]
        if len(train_df) < 120 or len(test_df) == 0:
            continue

        X_tr_all, y_tr_all = train_df[feature_cols], train_df[target_col]
        cut = int(len(train_df) * (1 - val_fraction))
        X_tr, y_tr = X_tr_all.iloc[:cut], y_tr_all.iloc[:cut]
        X_val, y_val = X_tr_all.iloc[cut:], y_tr_all.iloc[cut:]

        if params is None or i % retune_every == 0:
            params = model_mod.tune(X_tr, y_tr, X_val, y_val, n_trials=n_trials)

        lgbm = model_mod.fit(X_tr_all, y_tr_all, params, val_fraction=val_fraction)

        # Smearing estimated on the held-out validation tail of the *training*
        # window -- in-sample residuals would understate it badly.
        val_resid = np.asarray(y_val) - lgbm.predict(X_val)
        smear = smearing_factor(val_resid)

        har = baselines.HARModel().fit(har_X.loc[train_mask], y_tr_all)

        preds = pd.DataFrame({
            "date": test_df.index,
            "y_true": test_df[target_col].to_numpy(),
            "model": lgbm.predict(test_df[feature_cols]),
            "naive": baselines.naive_forecast(log_rv.loc[test_mask]).to_numpy(),
            "har": har.predict(har_X.loc[test_mask]),
        })

        if garch_log is not None:
            offset = baselines.garch_bias_correction(
                garch_log.reindex(df.index), df[target_col], train_mask)
            preds["garch"] = garch_log.reindex(test_df.index).to_numpy() + offset
        else:
            preds["garch"] = np.nan

        folds.append(Fold(
            fold=len(folds),
            train_start=train_df.index.min(), train_end=train_df.index.max(),
            test_start=test_df.index.min(), test_end=test_df.index.max(),
            n_train=len(train_df), n_test=len(test_df),
            smearing=smear, predictions=preds,
        ))
        if verbose:
            print(f"  fold {folds[-1].fold:2d}  "
                  f"test {preds['date'].min().date()} -> {preds['date'].max().date()}  "
                  f"n={len(test_df):3d}  smearing={smear:.3f}")

    return folds


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------

def stack_predictions(folds: list[Fold]) -> pd.DataFrame:
    out = pd.concat([f.predictions for f in folds], ignore_index=True)
    smear = pd.concat([
        pd.Series(f.smearing, index=range(len(f.predictions))) for f in folds
    ], ignore_index=True)
    out["smearing"] = smear.to_numpy()
    return out.set_index("date").sort_index()


def error_table(preds: pd.DataFrame,
                cols=("model", "har", "naive", "garch")) -> pd.DataFrame:
    rows = []
    for c in cols:
        if c not in preds or preds[c].isna().all():
            continue
        mask = preds[c].notna() & preds["y_true"].notna()
        err = preds.loc[mask, c] - preds.loc[mask, "y_true"]
        rows.append({
            "forecast": c,
            "rmse": float(np.sqrt((err**2).mean())),
            "mae": float(err.abs().mean()),
            "n": int(mask.sum()),
        })
    return pd.DataFrame(rows).set_index("forecast")


def diebold_mariano(preds: pd.DataFrame, a: str = "model", b: str = "har",
                    lag: int | None = None) -> dict:
    """DM test on the squared-error differential ``e_a^2 - e_b^2``.

    Negative statistic => forecast ``a`` has the lower loss. Newey-West
    standard errors, since daily volatility errors are serially correlated and
    a naive t-stat would overstate significance.
    """
    mask = preds[a].notna() & preds[b].notna() & preds["y_true"].notna()
    ea = (preds.loc[mask, a] - preds.loc[mask, "y_true"]).to_numpy()
    eb = (preds.loc[mask, b] - preds.loc[mask, "y_true"]).to_numpy()
    d = ea**2 - eb**2
    T = len(d)
    if T < 30:
        return {"statistic": np.nan, "p_value": np.nan, "n": T}

    if lag is None:
        lag = int(np.floor(4 * (T / 100.0) ** (2.0 / 9.0)))
    dbar = d.mean()
    dc = d - dbar
    gamma0 = float(dc @ dc / T)
    var = gamma0
    for k in range(1, lag + 1):
        gk = float(dc[k:] @ dc[:-k] / T)
        var += 2.0 * (1.0 - k / (lag + 1.0)) * gk
    var = max(var, 1e-18)

    stat = dbar / np.sqrt(var / T)
    # two-sided normal p-value
    from math import erfc, sqrt
    p = erfc(abs(stat) / sqrt(2.0))
    return {"statistic": float(stat), "p_value": float(p), "n": T,
            "mean_loss_diff": float(dbar), "lag": lag}
