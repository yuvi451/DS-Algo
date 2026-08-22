"""Baselines the model has to beat -- and the reason v1's margins were inflated.

v1 reported "+15.0% RMSE vs naive" and "+30.8% vs GARCH". Both numbers are
softer than they look:

* **Naive persistence** is ``log(sigma_t)`` from a *single day's* range. As an
  estimator of the current vol level it is extremely noisy, so beating it by
  15% is close to free -- a 5-day moving average of the same quantity does most
  of it. It is a sanity check, not a competitor.

* **GARCH was scored in the wrong units.** ``fit_garch_forecast`` fits
  close-to-close returns, so it forecasts *total* (gap-inclusive) vol, but it
  was scored against a Garman-Klass *intraday* target. On a log scale that is a
  near-constant offset of ``log(sigma_total / sigma_GK) ~ +0.2``, which inflates
  GARCH's RMSE by roughly that amount regardless of how good the model is. Most
  of the "+30.8%" is a unit error, not skill.

The honest bar for a daily realized-volatility forecast is **HAR-RV**
(Corsi 2009): an OLS regression of tomorrow's log-RV on daily, weekly and
monthly averages of log-RV. It is three lines of code, has no hyperparameters,
and is genuinely hard to beat. If LightGBM plus FinBERT cannot beat HAR, the
project's headline claim does not survive.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

HAR_LAGS = {"d": 1, "w": 5, "m": 22}


# --------------------------------------------------------------------------
# naive persistence
# --------------------------------------------------------------------------

def naive_forecast(log_rv: pd.Series) -> pd.Series:
    """Tomorrow's log-vol = today's log-vol."""
    return log_rv.copy()


# --------------------------------------------------------------------------
# HAR-RV
# --------------------------------------------------------------------------

def har_design(log_rv: pd.Series) -> pd.DataFrame:
    """HAR regressors at date t (all known at t's close)."""
    return pd.DataFrame({
        "har_d": log_rv,
        "har_w": log_rv.rolling(HAR_LAGS["w"]).mean(),
        "har_m": log_rv.rolling(HAR_LAGS["m"]).mean(),
    }, index=log_rv.index)


class HARModel:
    """OLS HAR-RV, fit by least squares with an intercept."""

    def __init__(self) -> None:
        self.coef_: np.ndarray | None = None
        self.columns_ = ["har_d", "har_w", "har_m"]

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "HARModel":
        design = X[self.columns_]
        mask = design.notna().all(axis=1) & y.notna()
        A = np.column_stack([np.ones(mask.sum()), design.loc[mask].to_numpy()])
        self.coef_, *_ = np.linalg.lstsq(A, y.loc[mask].to_numpy(), rcond=None)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.coef_ is None:
            raise RuntimeError("HARModel.fit must be called before predict")
        design = X[self.columns_].to_numpy()
        A = np.column_stack([np.ones(len(design)), design])
        # Rows with a NaN regressor fall back to the intercept-only prediction.
        out = A @ self.coef_
        bad = ~np.isfinite(A).all(axis=1)
        out[bad] = self.coef_[0]
        return out


# --------------------------------------------------------------------------
# GARCH(1,1)
# --------------------------------------------------------------------------

def garch_forecast(log_returns: pd.Series, refit_every: int = 5,
                   min_history: int = 250) -> pd.Series:
    """Rolling one-step-ahead GARCH(1,1) forecast of *total* daily log-vol.

    Indexed so that the value at date t is the forecast for t+1 -- the same
    convention as every other forecast in this project, so no caller-side
    ``shift`` is required (v1 pushed that onto the caller, which is exactly the
    kind of thing that silently goes wrong).

    Returns log-vol in the same close-to-close units as ``target_log_rv_h1``,
    so the comparison is now apples to apples.
    """
    from arch import arch_model

    rets = (log_returns.dropna() * 100.0)
    out = pd.Series(index=rets.index, dtype=float)

    last_params = None
    for i in range(min_history, len(rets)):
        history = rets.iloc[:i]
        try:
            model = arch_model(history, vol="GARCH", p=1, q=1, mean="Zero",
                               rescale=False)
            if last_params is None or (i - min_history) % refit_every == 0:
                res = model.fit(disp="off")
                last_params = res.params
            else:
                res = model.fix(last_params)
            var = res.forecast(horizon=1, reindex=False).variance.values[-1, 0]
            # forecast made from data strictly before rets.index[i] is a
            # forecast *for* rets.index[i]; store it at i-1 so the index
            # convention is "value at t forecasts t+1".
            out.iloc[i - 1] = np.log(np.sqrt(var) / 100.0)
        except Exception:
            continue

    return out.reindex(log_returns.index)


def garch_bias_correction(garch_log: pd.Series, target_log: pd.Series,
                          train_mask: np.ndarray) -> float:
    """Mean log offset between GARCH and the target, estimated on training data.

    Even with matched units a one-observation realized-vol target sits below a
    conditional-vol forecast in expectation (Jensen, plus estimator noise). We
    remove that offset using training data only, so GARCH is scored on its
    *shape*, which is what a baseline comparison is supposed to test.
    """
    a = garch_log[train_mask]
    b = target_log[train_mask]
    mask = a.notna() & b.notna()
    if mask.sum() < 30:
        return 0.0
    return float((b[mask] - a[mask]).mean())
