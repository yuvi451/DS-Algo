"""Baselines the LightGBM model has to beat: naive persistence and GARCH(1,1)."""

import numpy as np
import pandas as pd
from arch import arch_model


def naive_persistence_forecast(gk_vol_today: pd.Series) -> pd.Series:
    """Tomorrow's vol forecast = today's realized vol."""
    return gk_vol_today


def fit_garch_forecast(returns_pct: pd.Series, refit_every: int = 1) -> pd.Series:
    """Rolling one-step-ahead GARCH(1,1) volatility forecast.

    `returns_pct` should be percentage log returns (e.g. 100 * log_return)
    -- `arch` is numerically happier with returns scaled to roughly O(1).
    Refits the model at every step by default (set `refit_every` > 1 to
    refit less often and reuse the last fitted params in between, which is
    much faster over long walk-forward windows).

    Returns a Series of one-step-ahead conditional volatility forecasts,
    indexed like `returns_pct`: the value at date d is a forecast of date
    d's own return volatility, made using only history strictly before d.
    To compare against `target_next_gk_vol` (indexed by the *feature* date
    T, holding the forecast for T+1) the caller must shift this series by
    -1, e.g. `fit_garch_forecast(...).shift(-1)`.
    """
    returns_pct = returns_pct.dropna()
    forecasts = pd.Series(index=returns_pct.index, dtype=float)

    last_params = None
    for i in range(1, len(returns_pct)):
        history = returns_pct.iloc[:i]
        if len(history) < 30:
            continue
        try:
            if last_params is None or i % refit_every == 0:
                model = arch_model(history, vol="GARCH", p=1, q=1, mean="Zero", rescale=False)
                res = model.fit(disp="off")
                last_params = res.params
            else:
                model = arch_model(history, vol="GARCH", p=1, q=1, mean="Zero", rescale=False)
                res = model.fix(last_params)
            fcast = res.forecast(horizon=1, reindex=False)
            vol_forecast = np.sqrt(fcast.variance.values[-1, 0]) / 100.0
        except Exception:
            vol_forecast = np.nan
        forecasts.iloc[i] = vol_forecast

    return forecasts
