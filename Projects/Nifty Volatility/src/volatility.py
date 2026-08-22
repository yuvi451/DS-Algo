"""Volatility estimators, and the unit conventions the rest of the pipeline depends on.

The single most important idea in this module is that there are *two different*
daily volatilities and v1 of this project conflated them:

  * **Intraday (open-to-close) vol** -- what Garman-Klass measures. It is built
    from that session's O/H/L/C and knows nothing about the gap between
    yesterday's close and today's open.
  * **Total (close-to-close) vol** -- what you actually trade. A position held
    overnight earns ``log(C_t / C_{t-1})``, whose variance includes the
    overnight gap.

For the Nifty the overnight gap is a large minority of total daily variance
(roughly a third), so ``sigma_GK`` systematically understates the risk of a
close-to-close position by ~20%. Sizing a position as
``target_vol / predicted_GK_vol`` therefore over-levers by ~1/0.8 = 1.25x
*before* anything else goes wrong. See CRITICAL_ANALYSIS.md section 1.

Everything downstream of this module works in **total** vol units, which are
also the units India VIX quotes in -- that is what makes the two comparable
and the variance-risk-premium strategy possible at all.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252
_GK_CO_COEF = 2.0 * np.log(2.0) - 1.0


def garman_klass_variance(df: pd.DataFrame) -> pd.Series:
    """Garman-Klass *intraday* variance from one session's own OHLC.

        sigma^2_GK = 0.5 * ln(H/L)^2 - (2 ln2 - 1) * ln(C/O)^2

    Floored at zero: the estimator is unbiased but not guaranteed positive on
    any single observation.
    """
    log_hl = np.log(df["high"] / df["low"])
    log_co = np.log(df["close"] / df["open"])
    return (0.5 * log_hl**2 - _GK_CO_COEF * log_co**2).clip(lower=0.0)


def gap_variance(df: pd.DataFrame) -> pd.Series:
    """Overnight variance contribution, ``ln(O_t / C_{t-1})^2``.

    A one-observation estimator of the overnight component, exactly analogous
    to using ``r_t^2`` as a one-observation estimator of daily variance: noisy
    per day, unbiased in expectation, which is all we need since it is being
    summed into a target that gets modelled in logs.
    """
    return np.log(df["open"] / df["close"].shift(1)) ** 2


def total_daily_variance(df: pd.DataFrame) -> pd.Series:
    """Gap-inclusive daily variance = overnight variance + intraday variance.

    This is the decomposition of a close-to-close return into its two legs. It
    is the correct target for anything that sizes or prices an *overnight*
    position, and it is directly comparable to India VIX (de-annualized).
    """
    return gap_variance(df) + garman_klass_variance(df)


def realized_vol(df: pd.DataFrame, kind: str = "total") -> pd.Series:
    """Daily volatility (not variance, not annualized) for the given estimator."""
    if kind == "total":
        var = total_daily_variance(df)
    elif kind == "gk":
        var = garman_klass_variance(df)
    elif kind == "close":
        var = np.log(df["close"] / df["close"].shift(1)) ** 2
    else:
        raise ValueError(f"unknown estimator kind: {kind!r}")
    return np.sqrt(var)


def annualize(daily_vol: pd.Series | float, periods: int = TRADING_DAYS):
    return daily_vol * np.sqrt(periods)


def deannualize(annual_vol: pd.Series | float, periods: int = TRADING_DAYS):
    return annual_vol / np.sqrt(periods)


# --------------------------------------------------------------------------
# log-space -> level-space conversion
# --------------------------------------------------------------------------

def smearing_factor(log_residuals: np.ndarray | pd.Series) -> float:
    """Duan's smearing estimate of ``E[exp(residual)]``.

    Models are fit on ``log`` volatility because volatility is right-skewed and
    strictly positive. But ``exp(E[log v])`` is the *median*, not the mean --
    it understates the level by roughly ``exp(sigma_resid^2 / 2)``. With the
    residual spread this model actually achieves (~0.41 in log units) that is
    an 8-9% low bias, which feeds straight into over-leverage when you divide
    by it.

    Duan's smearing estimator is the non-parametric version of that correction
    and does not assume the residuals are Gaussian. It MUST be estimated on
    training residuals only.
    """
    resid = np.asarray(log_residuals, dtype=float)
    resid = resid[np.isfinite(resid)]
    if resid.size == 0:
        return 1.0
    return float(np.mean(np.exp(resid)))


def log_to_level(log_pred: pd.Series | np.ndarray, smearing: float = 1.0):
    """Convert a log-vol forecast to a vol level, applying the mean correction."""
    return np.exp(log_pred) * smearing
