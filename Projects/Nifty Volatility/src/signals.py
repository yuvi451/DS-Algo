"""Directional signals -- what you need before you can short anything.

A volatility model cannot tell you which way to bet. It forecasts |r|, not r,
and the sign is exactly the information it throws away. So "add shorting" is
really "add a return forecast", and that is a different and much harder
problem: realized volatility is strongly autocorrelated and therefore
forecastable, while daily index returns are close to a martingale.

Set expectations accordingly. Everything in this module has a documented
out-of-sample information coefficient in the 0.02-0.05 range at daily horizon.
That is small but not zero, and it is the honest ceiling. Anything claiming
much more on an index this liquid is overfit.

Three signals, all cheap, all causal:

* **Time-series momentum.** Distance from a moving average, normalised by the
  volatility accumulated over that lookback. The most robust directional
  anomaly in the literature and the only one here you would trade on its own.
* **Variance risk premium.** A wide VRP predicts higher subsequent equity
  returns (Bollerslev-Tauchen-Zhou 2009) -- it is a risk-appetite proxy. Free,
  since India VIX is already loaded for the vol model.
* **News sentiment.** Signed mean polarity: useless for forecasting volatility
  (section 3 of CRITICAL_ANALYSIS.md) because good and bad news both raise it,
  but direction is the one question the sign is actually about. This is where
  the FinBERT work belongs.

Every statistic here is computed on a trailing window. Z-scoring against
full-sample mean and standard deviation is lookahead bias and would inflate
every number in this file.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _rolling_z(series: pd.Series, window: int = TRADING_DAYS,
               min_periods: int = 60, clip: float = 3.0) -> pd.Series:
    """Trailing z-score. Causal by construction."""
    mu = series.rolling(window, min_periods=min_periods).mean()
    sd = series.rolling(window, min_periods=min_periods).std()
    return ((series - mu) / sd.replace(0, np.nan)).clip(-clip, clip)


def trend_score(close: pd.Series, daily_vol: pd.Series,
                spans: tuple[int, ...] = (20, 60, 200)) -> pd.Series:
    """Multi-horizon time-series momentum, volatility-normalised, in [-1, 1].

    For each lookback ``n``: ``log(P_t / MA_n) / (sigma * sqrt(n))``. The
    ``sqrt(n)`` matters -- over ``n`` days the price accumulates about
    ``sigma * sqrt(n)`` of noise, so without it the long lookbacks dominate
    purely by scale rather than by information. ``tanh`` then caps each
    horizon's vote so one runaway trend cannot swamp the blend.
    """
    votes = []
    for n in spans:
        ma = close.rolling(n, min_periods=n // 2).mean()
        z = np.log(close / ma) / (daily_vol * np.sqrt(n)).replace(0, np.nan)
        votes.append(np.tanh(z))
    return pd.concat(votes, axis=1).mean(axis=1)


def vrp_score(log_vrp: pd.Series, window: int = TRADING_DAYS) -> pd.Series:
    """Risk-appetite proxy in [-1, 1]. Wide premium -> higher expected returns."""
    return np.tanh(_rolling_z(log_vrp, window) / 2.0)


def sentiment_score(sent_mean: pd.Series, window: int = TRADING_DAYS) -> pd.Series:
    """Signed news polarity, trailing-standardised, in [-1, 1].

    NaN on days with no news -- filled with 0 (neutral) here rather than left
    NaN, because unlike the tree model this is an arithmetic blend and a NaN
    would poison the whole score.
    """
    return np.tanh(_rolling_z(sent_mean, window) / 2.0).fillna(0.0)


def build_direction(table: pd.DataFrame,
                    weights: dict[str, float] | None = None,
                    allow_short: bool = True,
                    short_floor: float = -1.0,
                    target_exposure: float = 0.7) -> pd.DataFrame:
    """Blend the available signals into one directional score per day.

    Returns a frame with the individual components plus ``direction``, the
    weighted blend clipped to ``[short_floor, 1]``. With ``allow_short=False``
    the floor is 0 and the strategy degenerates to the long-only overlay.

    Weights are *not* fitted. Fitting three signal weights on the same sample
    you then report is how a 0.03 information coefficient becomes an imaginary
    0.15; the defaults lean on momentum because that is the one with decades of
    out-of-sample evidence behind it.

    ``target_exposure`` rescales the blend so its trailing mean absolute value
    is about that much. Three ``tanh``-squashed components averaged together
    sit near zero most of the time, which would leave the book ~3% invested and
    ~97% in cash -- a strategy whose returns are almost entirely the risk-free
    rate, wearing a flattering Sharpe. The rescaling is done on a trailing
    window so it stays causal.
    """
    weights = weights or {"trend": 0.6, "vrp": 0.25, "sentiment": 0.15}

    out = pd.DataFrame(index=table.index)
    out["trend"] = trend_score(table["close"], table["rv"])

    if "log_vrp" in table and table["log_vrp"].notna().any():
        out["vrp"] = vrp_score(table["log_vrp"])
    else:
        out["vrp"] = np.nan

    if "sent_mean" in table and table["sent_mean"].notna().any():
        out["sentiment"] = sentiment_score(table["sent_mean"])
    else:
        out["sentiment"] = np.nan

    # Renormalise over whichever components actually exist, so a missing VIX or
    # missing news feed rescales the blend instead of silently shrinking it.
    w = pd.Series({k: weights.get(k, 0.0) for k in ["trend", "vrp", "sentiment"]})
    available = out[["trend", "vrp", "sentiment"]].notna()
    wsum = available.mul(w, axis=1).sum(axis=1).replace(0, np.nan)
    blend = out[["trend", "vrp", "sentiment"]].fillna(0.0).mul(w, axis=1).sum(axis=1) / wsum

    scale = blend.abs().rolling(TRADING_DAYS, min_periods=60).mean()
    blend = blend * (target_exposure / scale.replace(0, np.nan))

    lo = short_floor if allow_short else 0.0
    out["direction"] = blend.clip(lo, 1.0).fillna(0.0)
    return out


# --------------------------------------------------------------------------
# does the signal actually predict anything?
# --------------------------------------------------------------------------

def information_coefficient(signal: pd.Series, next_return: pd.Series,
                            lag: int | None = None) -> dict:
    """Rank correlation between signal and next-day return, with a t-stat.

    Run this *before* backtesting. A directional signal with an insignificant
    IC will still produce an equity curve -- it just will not produce one that
    means anything, and the backtest's Sharpe will be a draw from noise. The
    t-stat uses Newey-West standard errors because both the signal and the
    returns are serially correlated.
    """
    df = pd.DataFrame({"s": signal, "r": next_return}).dropna()
    if len(df) < 60:
        return {"ic": np.nan, "t_stat": np.nan, "p_value": np.nan, "n": len(df)}

    ic = float(df["s"].corr(df["r"], method="spearman"))

    # t-stat on the per-period contribution, Newey-West corrected.
    x = df["s"].rank(pct=True) - 0.5
    y = df["r"].rank(pct=True) - 0.5
    prod = (x * y).to_numpy()
    T = len(prod)
    if lag is None:
        lag = int(np.floor(4 * (T / 100.0) ** (2.0 / 9.0)))
    dbar = prod.mean()
    dc = prod - dbar
    var = float(dc @ dc / T)
    for k in range(1, lag + 1):
        var += 2.0 * (1.0 - k / (lag + 1.0)) * float(dc[k:] @ dc[:-k] / T)
    var = max(var, 1e-18)
    t = dbar / np.sqrt(var / T)

    from math import erfc, sqrt
    return {
        "ic": ic,
        "t_stat": float(t),
        "p_value": float(erfc(abs(t) / sqrt(2.0))),
        "n": T,
        "verdict": ("has predictive power" if abs(t) > 1.96
                    else "NOT distinguishable from noise"),
    }


def signal_report(direction_df: pd.DataFrame, next_return: pd.Series) -> pd.DataFrame:
    """IC table for every component and the blend. Read it before trading."""
    rows = []
    for col in direction_df.columns:
        stats = information_coefficient(direction_df[col], next_return)
        rows.append({"signal": col, **stats})
    return pd.DataFrame(rows).set_index("signal")
