"""Walk-forward validation.

Train on an expanding window of ~1 year, test on the next ~2 months, slide
forward and repeat. Never a random shuffle split -- that's the single most
common way this kind of project quietly leaks future information into
training. Errors are reported on log-volatility (right-skewed, strictly
positive target), and the headline result is the margin by which the model
beats naive persistence and GARCH(1,1), not a standalone error number.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from src.models.lightgbm_model import train_lgbm, tune_hyperparameters


@dataclass
class FoldResult:
    fold: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    n_train: int
    n_test: int
    rmse_model: float
    mae_model: float
    rmse_naive: float
    mae_naive: float
    rmse_garch: float
    mae_garch: float
    predictions: pd.DataFrame = field(repr=False)


def add_naive_forecast_column(feature_table: pd.DataFrame, col_name: str = "naive_log_vol") -> pd.DataFrame:
    """Naive persistence forecast for tomorrow's log-vol = log(today's realized GK vol)."""
    out = feature_table.copy()
    out[col_name] = np.log(out["gk_vol"] + 1e-8)
    return out


def generate_walk_forward_folds(dates: pd.DatetimeIndex, train_years: int = 1,
                                 test_months: int = 2, step_months: int = 2):
    """Yield (train_mask, test_mask) boolean arrays over `dates`."""
    dates = pd.DatetimeIndex(dates)
    start = dates.min()
    train_end = start + relativedelta(years=train_years)

    while True:
        test_end = train_end + relativedelta(months=test_months)
        train_mask = (dates >= start) & (dates < train_end)
        test_mask = (dates >= train_end) & (dates < test_end)
        if test_mask.sum() == 0:
            break
        yield train_mask, test_mask
        train_end = train_end + relativedelta(months=step_months)
        if train_end >= dates.max():
            break


def _rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def _mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))


def run_walk_forward(feature_table: pd.DataFrame, feature_cols: list[str],
                      naive_log_vol_col: str, garch_log_vol: pd.Series,
                      train_years: int = 1, test_months: int = 2, step_months: int = 2,
                      n_optuna_trials: int = 20) -> list[FoldResult]:
    """Run the full walk-forward loop, tuning + training a fresh LightGBM
    model on each expanding training window and comparing against naive
    persistence and GARCH(1,1) on the held-out test window.

    `garch_log_vol` must already be indexed like `feature_table` (i.e. the
    value at feature date T is the forecast for T+1's log-vol) -- see
    `fit_garch_forecast`'s docstring for the `.shift(-1)` needed to get
    there from its raw output.
    """
    df = feature_table.dropna(subset=["target_next_log_gk_vol"]).copy()
    dates = df.index

    results = []
    for fold_id, (train_mask, test_mask) in enumerate(
            generate_walk_forward_folds(dates, train_years, test_months, step_months)):

        train_df = df.loc[train_mask]
        test_df = df.loc[test_mask]
        if len(train_df) < 60 or len(test_df) == 0:
            continue

        # Hold out the tail of the training window for early stopping / Optuna validation.
        val_cut = int(len(train_df) * 0.85)
        X_tr, y_tr = train_df[feature_cols].iloc[:val_cut], train_df["target_next_log_gk_vol"].iloc[:val_cut]
        X_val, y_val = train_df[feature_cols].iloc[val_cut:], train_df["target_next_log_gk_vol"].iloc[val_cut:]
        X_test, y_test = test_df[feature_cols], test_df["target_next_log_gk_vol"]

        best_params = tune_hyperparameters(X_tr, y_tr, X_val, y_val, n_trials=n_optuna_trials)
        model = train_lgbm(train_df[feature_cols], train_df["target_next_log_gk_vol"], params=best_params)
        preds = model.predict(X_test)

        naive_preds = test_df[naive_log_vol_col].values
        garch_preds = garch_log_vol.reindex(test_df.index).values
        garch_valid = ~np.isnan(garch_preds)

        pred_frame = pd.DataFrame({
            "date": test_df.index,
            "y_true_log": y_test.values,
            "y_pred_model_log": preds,
            "y_pred_naive_log": naive_preds,
            "y_pred_garch_log": garch_preds,
        })

        results.append(FoldResult(
            fold=fold_id,
            train_start=train_df.index.min(), train_end=train_df.index.max(),
            test_start=test_df.index.min(), test_end=test_df.index.max(),
            n_train=len(train_df), n_test=len(test_df),
            rmse_model=_rmse(y_test, preds), mae_model=_mae(y_test, preds),
            rmse_naive=_rmse(y_test, naive_preds), mae_naive=_mae(y_test, naive_preds),
            rmse_garch=_rmse(y_test.values[garch_valid], garch_preds[garch_valid]) if garch_valid.any() else np.nan,
            mae_garch=_mae(y_test.values[garch_valid], garch_preds[garch_valid]) if garch_valid.any() else np.nan,
            predictions=pred_frame,
        ))

    return results


def summarize_folds(results: list[FoldResult]) -> pd.DataFrame:
    rows = [{
        "fold": r.fold, "test_start": r.test_start.date(), "test_end": r.test_end.date(),
        "n_test": r.n_test,
        "rmse_model": r.rmse_model, "rmse_naive": r.rmse_naive, "rmse_garch": r.rmse_garch,
        "mae_model": r.mae_model, "mae_naive": r.mae_naive, "mae_garch": r.mae_garch,
        "rmse_improvement_vs_naive_pct": 100 * (r.rmse_naive - r.rmse_model) / r.rmse_naive,
        "rmse_improvement_vs_garch_pct": 100 * (r.rmse_garch - r.rmse_model) / r.rmse_garch if not np.isnan(r.rmse_garch) else np.nan,
    } for r in results]
    return pd.DataFrame(rows)


def overall_metrics(results: list[FoldResult]) -> dict:
    all_preds = pd.concat([r.predictions for r in results], ignore_index=True)
    garch_valid = all_preds["y_pred_garch_log"].notna()
    return {
        "rmse_model": _rmse(all_preds["y_true_log"], all_preds["y_pred_model_log"]),
        "mae_model": _mae(all_preds["y_true_log"], all_preds["y_pred_model_log"]),
        "rmse_naive": _rmse(all_preds["y_true_log"], all_preds["y_pred_naive_log"]),
        "mae_naive": _mae(all_preds["y_true_log"], all_preds["y_pred_naive_log"]),
        "rmse_garch": _rmse(all_preds.loc[garch_valid, "y_true_log"], all_preds.loc[garch_valid, "y_pred_garch_log"]),
        "mae_garch": _mae(all_preds.loc[garch_valid, "y_true_log"], all_preds.loc[garch_valid, "y_pred_garch_log"]),
        "n_predictions": len(all_preds),
    }
