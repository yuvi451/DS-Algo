"""LightGBM volatility model with Optuna hyperparameter tuning.

Trained on log-volatility (`target_next_log_gk_vol`) since realized
volatility is right-skewed and strictly positive -- see src/validation for
where RMSE/MAE are reported on this same log scale.
"""

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

from src.config import RANDOM_SEED

optuna.logging.set_verbosity(optuna.logging.WARNING)

DEFAULT_PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "verbosity": -1,
    "seed": RANDOM_SEED,
}


def _objective(trial, X_train, y_train, X_val, y_val):
    params = {
        **DEFAULT_PARAMS,
        "num_leaves": trial.suggest_int("num_leaves", 7, 63),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 50, 500),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
    }
    model = lgb.LGBMRegressor(**params)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
              callbacks=[lgb.early_stopping(30, verbose=False)])
    preds = model.predict(X_val, num_iteration=model.best_iteration_)
    return float(np.sqrt(np.mean((preds - y_val) ** 2)))


def tune_hyperparameters(X_train, y_train, X_val, y_val, n_trials: int = 30) -> dict:
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED))
    study.optimize(lambda t: _objective(t, X_train, y_train, X_val, y_val), n_trials=n_trials, show_progress_bar=False)
    return {**DEFAULT_PARAMS, **study.best_params}


def train_lgbm(X_train, y_train, X_val=None, y_val=None, params: dict | None = None,
                objective: str = "regression", alpha: float | None = None) -> lgb.LGBMRegressor:
    """Train a single LightGBM regressor.

    Set `objective="quantile"` with `alpha` in {0.1, 0.5, 0.9} to fit one
    quantile of the predictive distribution -- cheap uncertainty bands for
    gradient boosting, unlike for a deep net.
    """
    fit_params = {**DEFAULT_PARAMS, **(params or {})}
    fit_params["objective"] = objective
    if objective == "quantile":
        fit_params["alpha"] = alpha
    model = lgb.LGBMRegressor(**fit_params)
    if X_val is not None:
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                  callbacks=[lgb.early_stopping(30, verbose=False)])
    else:
        model.fit(X_train, y_train)
    return model


def train_quantile_ensemble(X_train, y_train, X_val, y_val, params: dict,
                             quantiles=(0.1, 0.5, 0.9)) -> dict:
    """Train one LightGBM model per quantile, sharing tuned point-forecast params."""
    models = {}
    for q in quantiles:
        models[q] = train_lgbm(X_train, y_train, X_val, y_val, params=params,
                                objective="quantile", alpha=q)
    return models
