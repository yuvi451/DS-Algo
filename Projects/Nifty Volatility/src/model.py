"""LightGBM volatility model.

One real bug fixed from v1. v1 tuned hyperparameters with early stopping on a
validation tail, took ``n_estimators`` straight out of the trial's *suggested*
value, and then refit on the full training window **with no early stopping**:

    best_params = tune_hyperparameters(X_tr, y_tr, X_val, y_val, ...)
    model = train_lgbm(train_df[feature_cols], train_df[target], params=best_params)

So the number of trees that survived early stopping during tuning was thrown
away, and the refit ran the full suggested ``n_estimators`` -- up to 500 -- on
data it had never been validated against. The tuned configuration and the
deployed model were not the same model. Here the surviving iteration count is
carried through and rescaled for the larger refit sample.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RANDOM_SEED = 42

BASE_PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "verbosity": -1,
    "seed": RANDOM_SEED,
    "n_jobs": -1,
}


def _search_space(trial) -> dict:
    return {
        "num_leaves": trial.suggest_int("num_leaves", 7, 63),
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "n_estimators": 2000,  # capped by early stopping, not by the search
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 60),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "subsample_freq": 1,
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
    }


def tune(X_tr, y_tr, X_val, y_val, n_trials: int = 25) -> dict:
    """Optuna search; returns params including the early-stopped tree count."""
    import lightgbm as lgb
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    best_iters: dict[int, int] = {}

    def objective(trial):
        params = {**BASE_PARAMS, **_search_space(trial)}
        model = lgb.LGBMRegressor(**params)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)],
                  callbacks=[lgb.early_stopping(50, verbose=False)])
        best_iters[trial.number] = int(model.best_iteration_ or params["n_estimators"])
        pred = model.predict(X_val, num_iteration=model.best_iteration_)
        return float(np.sqrt(np.mean((pred - np.asarray(y_val)) ** 2)))

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED),
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    params = {**BASE_PARAMS, **_search_space_from_dict(study.best_params)}
    params["n_estimators"] = best_iters.get(study.best_trial.number, 200)
    return params


def _search_space_from_dict(d: dict) -> dict:
    out = dict(d)
    out["subsample_freq"] = 1
    return out


def fit(X, y, params: dict, val_fraction: float = 0.0):
    """Fit LightGBM, rescaling the tree count for the larger refit sample.

    ``params['n_estimators']`` arrives as the count that survived early stopping
    on ``val_fraction``-smaller data; scaling it up keeps the effective amount
    of boosting roughly constant on the full window.
    """
    import lightgbm as lgb

    p = dict(params)
    if val_fraction > 0:
        p["n_estimators"] = max(20, int(p.get("n_estimators", 200) / (1 - val_fraction)))
    model = lgb.LGBMRegressor(**p)
    model.fit(X, y)
    return model


def fit_quantiles(X, y, params: dict, quantiles=(0.1, 0.5, 0.9),
                  val_fraction: float = 0.0) -> dict:
    """One model per quantile for a cheap predictive band."""
    models = {}
    for q in quantiles:
        p = dict(params)
        p["objective"] = "quantile"
        p["alpha"] = q
        p.pop("metric", None)
        models[q] = fit(X, y, p, val_fraction)
    return models
