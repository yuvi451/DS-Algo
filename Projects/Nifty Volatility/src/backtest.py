"""Backtests.

Two strategies, for two different reasons.

``vol_target_backtest`` is v1's idea, repaired. It will not make money and it
is not supposed to -- a long-only position sized by a volatility forecast has
no expected-return edge, because Sharpe is invariant to leverage. The most it
can do is reshape risk: shallower drawdowns for a similar return. v1 reported
it as a profit strategy and lost to buy-and-hold on every axis; fixed, it
should land at a modestly better Sharpe and a much better drawdown, with the
honest caveat attached.

``vrp_backtest`` is where a volatility forecast actually pays. India VIX prices
*implied* volatility; the model forecasts *realized* volatility; the spread
between them is the variance risk premium, which on the Nifty is large and
persistently positive. Selling variance harvests it, and the model's job is to
tell you when the premium is unusually rich (size up) or thin/negative (stand
aside, or buy). This converts the volatility forecast from a position-sizing
input, where its skill is nearly worthless, into a pricing input, where its
skill is the whole trade.

The short-variance leg has severe negative skew. Everything here is capped and
limited, and the caveats are in CRITICAL_ANALYSIS.md section 5 -- read them
before believing any Sharpe this file prints.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


# --------------------------------------------------------------------------
# shared metrics
# --------------------------------------------------------------------------

def sharpe(returns: pd.Series, rf_annual: float = 0.0) -> float:
    r = pd.Series(returns).dropna()
    if len(r) < 2 or r.std() == 0:
        return 0.0
    excess = r - rf_annual / TRADING_DAYS
    return float(np.sqrt(TRADING_DAYS) * excess.mean() / r.std())


def max_drawdown(equity: pd.Series) -> float:
    eq = pd.Series(equity).dropna()
    if eq.empty:
        return 0.0
    return float((eq / eq.cummax() - 1.0).min())


def summarize(returns: pd.Series, rf_annual: float = 0.0,
              label: str = "") -> dict:
    r = pd.Series(returns).dropna()
    equity = (1 + r).cumprod()
    years = len(r) / TRADING_DAYS
    cagr = float(equity.iloc[-1] ** (1 / years) - 1) if years > 0 and len(equity) else 0.0

    # Sortino must use the same excess return as Sharpe. Comparing an
    # excess-return Sharpe against a raw-return Sortino produces contradictory
    # signs on the same series and makes a cash-heavy book look good.
    excess = r - rf_annual / TRADING_DAYS
    downside = excess[excess < 0].std()
    return {
        "label": label,
        "cagr": cagr,
        "ann_vol": float(r.std() * np.sqrt(TRADING_DAYS)),
        "sharpe": sharpe(r, rf_annual),
        "sortino": float(np.sqrt(TRADING_DAYS) * excess.mean() / downside) if downside else 0.0,
        "max_drawdown": max_drawdown(equity),
        "total_return": float(equity.iloc[-1] - 1) if len(equity) else 0.0,
        "skew": float(r.skew()),
        "worst_day": float(r.min()),
    }


def _apply_deadband(raw: pd.Series, deadband: float) -> pd.Series:
    """No-trade band with partial adjustment to the band edge.

    v1 rebalanced to a fresh target every single day off a noisy daily forecast
    and paid 7.5 bps on every wiggle. Backing out v1's own reported numbers,
    that cost drag was ~2-3.5%/yr -- larger than any plausible vol-timing
    benefit, and the single biggest reason the strategy lost to buy-and-hold.

    Snapping to the full target whenever the band is breached barely helps,
    because a noisy target breaches it most days. Trading only to the *edge* of
    the band is the classic no-trade-region result (Leland; Davis-Norman): the
    book tracks the target with a lag, turnover collapses, and the tracking
    error costs far less than the spread it saves.
    """
    if deadband <= 0:
        return raw.ffill().fillna(0.0)

    out = np.empty(len(raw))
    current = float(raw.iloc[0]) if len(raw) else 0.0
    for i, target in enumerate(raw.to_numpy()):
        if np.isfinite(target):
            if target > current + deadband:
                current = float(target) - deadband
            elif target < current - deadband:
                current = float(target) + deadband
        out[i] = current
    return pd.Series(out, index=raw.index)


# --------------------------------------------------------------------------
# strategy 1: volatility-targeted index exposure (the repaired v1 idea)
# --------------------------------------------------------------------------

def vol_target_backtest(pred_vol: pd.Series, next_return: pd.Series,
                        target_ann_vol: float = 0.12,
                        max_leverage: float = 1.5,
                        cost_bps: float = 7.5,
                        rf_annual: float = 0.065,
                        deadband: float = 0.10) -> pd.DataFrame:
    """Long-only index exposure scaled inversely to predicted volatility.

    ``pred_vol`` must be a **gap-inclusive daily** vol forecast with the
    smearing correction already applied -- the same units as the close-to-close
    returns in ``next_return``. Getting this wrong is what produced v1's
    persistent 1.3x leverage.

    Unlike v1 this charges financing on borrowed exposure and credits cash on
    un-invested capital. v1 handed the strategy free leverage, which flatters
    it, and it still lost.
    """
    idx = pred_vol.index.intersection(next_return.index)
    pv = pred_vol.loc[idx].astype(float)
    ret = next_return.loc[idx].astype(float)

    target_daily = target_ann_vol / np.sqrt(TRADING_DAYS)
    raw = (target_daily / pv.replace(0, np.nan)).clip(0.0, max_leverage)
    pos = _apply_deadband(raw.ffill().fillna(0.0), deadband)

    traded = pos.diff().abs().fillna(pos.abs())
    cost = traded * (cost_bps / 1e4)
    # borrow above 1x, earn cash below 1x
    financing = (pos - 1.0) * (rf_annual / TRADING_DAYS)

    strat = pos * ret - cost - financing

    out = pd.DataFrame({
        "predicted_vol": pv,
        "position": pos,
        "target_position": raw,
        "next_return": ret,
        "cost": cost,
        "financing": financing,
        "strategy_return": strat,
        "buy_hold_return": ret,
    })
    out["strategy_equity"] = (1 + out["strategy_return"]).cumprod()
    out["buy_hold_equity"] = (1 + out["buy_hold_return"]).cumprod()
    return out


def futures_carry(position: pd.Series, rf_annual: float = 0.065,
                  div_yield: float = 0.012) -> pd.Series:
    """Daily carry for a fully-collateralised Nifty futures position.

    You cannot short the cash index in India; shorting means futures. That
    changes the financing arithmetic and it is worth getting right rather than
    bolting a minus sign onto the long-only version.

    A futures price is ``F = S * exp((r - q) * T)``, so holding the future to
    expiry earns the *price* return minus ``(r - q)``. Meanwhile the cash that
    is not posted as margin earns ``r``. Netting the two:

        carry = position * q / 252  +  (1 - position) * r / 252

    Read off the cases: at ``position = 1`` you earn the dividend yield on top
    of the price return, which correctly reconstructs the total return of the
    index (``^NSEI`` is a price index and excludes dividends). At
    ``position = 0`` you earn the risk-free rate on all of it. At
    ``position = -1`` you pay the dividend yield away on the short and collect
    ``r`` on both your own capital and the short proceeds.

    That last line is the one that matters for shorting: the carry is a
    *headwind*, because you are giving up the dividend yield and fighting the
    index's positive drift. A short has to overcome roughly ``q + drift``
    before it breaks even, which is why the long/short version below usually
    looks worse than long-only unless the directional signal is genuinely good.
    """
    return position * (div_yield / TRADING_DAYS) + (1 - position) * (rf_annual / TRADING_DAYS)


def long_short_backtest(direction: pd.Series, pred_vol: pd.Series,
                        next_return: pd.Series,
                        target_ann_vol: float = 0.12,
                        max_long: float = 1.5, max_short: float = -1.0,
                        cost_bps: float = 5.0,
                        rf_annual: float = 0.065, div_yield: float = 0.012,
                        deadband: float = 0.10,
                        stop_drawdown: float | None = -0.25) -> pd.DataFrame:
    """Long/short index exposure: direction from signals, size from the vol model.

    ``position = direction * (target_vol / predicted_vol)``, so the two models
    do separate jobs -- the directional signal picks the side, the volatility
    forecast decides how much risk that side is worth. This is the only
    arrangement in which a volatility forecast contributes to *return* rather
    than only to risk, and it does so indirectly: it makes each unit of
    directional conviction carry constant risk.

    ``cost_bps`` defaults to 5 rather than the 7.5 used for the cash overlay:
    Nifty futures are cheaper to trade (STT on the sell side is 2 bps, spread
    and brokerage roughly another 1-3).

    ``stop_drawdown`` flattens the book if equity falls that far below its high
    water mark, re-entering when the signal next flips. A short book without a
    stop is how accounts get closed; losses on a short are unbounded and margin
    calls arrive at the worst possible moment.
    """
    idx = (direction.index.intersection(pred_vol.index)
           .intersection(next_return.index))
    d = direction.loc[idx].astype(float)
    pv = pred_vol.loc[idx].astype(float)
    ret = next_return.loc[idx].astype(float)

    target_daily = target_ann_vol / np.sqrt(TRADING_DAYS)
    scalar = (target_daily / pv.replace(0, np.nan)).clip(0.0, abs(max_long))
    raw = (d * scalar).clip(max_short, max_long)
    pos = _apply_deadband(raw.ffill().fillna(0.0), deadband)

    if stop_drawdown is not None:
        pos = _apply_drawdown_stop(pos, ret, stop_drawdown, rf_annual, div_yield,
                                   cost_bps)

    traded = pos.diff().abs().fillna(pos.abs())
    cost = traded * (cost_bps / 1e4)
    carry = futures_carry(pos, rf_annual, div_yield)

    strat = pos * ret + carry - cost

    out = pd.DataFrame({
        "direction": d,
        "vol_scalar": scalar,
        "position": pos,
        "next_return": ret,
        "carry": carry,
        "cost": cost,
        "strategy_return": strat,
        "buy_hold_return": ret + div_yield / TRADING_DAYS,
    })
    out["strategy_equity"] = (1 + out["strategy_return"]).cumprod()
    out["buy_hold_equity"] = (1 + out["buy_hold_return"]).cumprod()
    out["gross_exposure"] = pos.abs()
    out["is_short"] = (pos < 0).astype(int)
    return out


def _apply_drawdown_stop(pos: pd.Series, ret: pd.Series, limit: float,
                         rf_annual: float, div_yield: float,
                         cost_bps: float) -> pd.Series:
    """Flatten the book while equity is more than ``limit`` below its peak.

    Walked forward one day at a time because the stop depends on the equity
    curve the stop itself produces -- deriving it from the unstopped curve
    would be a lookahead.

    Re-entry is deliberately conservative: once halted, the book stays flat
    until the target position changes sign relative to what was held when the
    stop fired. Re-entering on the same side that just lost 25% is how a stop
    becomes a formality.
    """
    out = np.zeros(len(pos))
    p = pos.to_numpy()
    r = np.nan_to_num(ret.to_numpy())

    equity, peak = 1.0, 1.0
    halted = False
    halted_side = 0.0
    prev = 0.0

    for i in range(len(p)):
        want = p[i]
        if halted:
            # only wake up when the signal has flipped to the other side
            if halted_side != 0.0 and np.sign(want) == -np.sign(halted_side):
                halted = False
            else:
                want = 0.0

        traded = abs(want - prev)
        carry = (want * (div_yield / TRADING_DAYS)
                 + (1 - want) * (rf_annual / TRADING_DAYS))
        day = want * r[i] + carry - traded * (cost_bps / 1e4)

        equity *= (1 + day)
        peak = max(peak, equity)
        out[i] = want
        prev = want

        if not halted and equity / peak - 1.0 <= limit:
            halted = True
            halted_side = np.sign(want) if want != 0 else np.sign(p[i])

    return pd.Series(out, index=pos.index)


def vol_matched(returns: pd.Series, benchmark: pd.Series) -> pd.Series:
    """Rescale ``returns`` to the benchmark's realized vol.

    The only fair way to compare total return between a levered and an
    unlevered book. v1 compared a ~1.3x-levered strategy's return against 1x
    buy-and-hold and presented the shortfall as a strategy result.
    """
    a, b = returns.dropna(), benchmark.dropna()
    if a.std() == 0:
        return returns
    return returns * (b.std() / a.std())


# --------------------------------------------------------------------------
# strategy 2: variance risk premium carry (where the forecast actually pays)
# --------------------------------------------------------------------------

def vrp_signal(iv_daily: pd.Series, pred_rv_daily: pd.Series) -> pd.Series:
    """Log richness of implied vol over the model's realized-vol forecast.

    Positive => the market is charging more for volatility than the model
    expects to be delivered => selling variance is favourably priced.
    """
    idx = iv_daily.index.intersection(pred_rv_daily.index)
    return np.log(iv_daily.loc[idx]) - np.log(pred_rv_daily.loc[idx])


def vrp_backtest(iv_daily: pd.Series, pred_rv_daily: pd.Series,
                 realized_var_fwd: pd.Series,
                 entry_z: float = 0.0, max_position: float = 1.0,
                 scale: float = 3.0,
                 allow_long_vol: bool = True,
                 hold_days: int = 5,
                 cost_vol_pts: float = 0.005,
                 risk_fraction: float = 0.15,
                 cap_multiple: float = 3.0) -> pd.DataFrame:
    """Short/long variance against the model's realized-vol forecast.

    Payoff is the standard variance-swap P&L expressed in vega terms:

        pnl_vol_points = (K^2 - RV^2) / (2K)

    with ``K`` the implied vol struck at entry and ``RV`` the volatility
    actually realized over the holding period, both annualized. ``cap_multiple``
    caps the loss at ``cap_multiple * K`` realized vol, which is what buying
    wings (a strangle overlay instead of a naked short) actually buys you --
    without it the downside is unbounded and the backtest is fiction.

    Positions are held ``hold_days`` (Nifty options expire weekly) rather than
    rebalanced daily, so the bid-ask is paid once per position, not 252 times a
    year.

    Parameters
    ----------
    realized_var_fwd
        Forward-looking: the value at ``t`` must be the *arithmetic mean daily
        variance* over ``(t, t+hold_days]`` -- ``target_rvar_h{hold_days}`` from
        features.add_targets. A variance swap settles on realized variance, not
        on the geometric mean of daily vols.
    cost_vol_pts
        Round-trip bid-ask in annualized vol points (0.005 = 0.5 vol pts).
    risk_fraction
        Position sizing, expressed as the fraction of capital a full-size
        position loses if realized vol runs all the way to the cap. 0.15 means
        the worst case on a maximal position is a 15% loss. Sharpe is invariant
        to this; the equity curve and the drawdown are not.
    """
    idx = (iv_daily.index
           .intersection(pred_rv_daily.index)
           .intersection(realized_var_fwd.index))
    iv = iv_daily.loc[idx].astype(float)
    pred = pred_rv_daily.loc[idx].astype(float)
    rvar = realized_var_fwd.loc[idx].astype(float)

    sig = np.log(iv) - np.log(pred)

    # Short variance when implied is rich, long when cheap, flat in between.
    pos = np.clip((sig - entry_z) * scale, -max_position, max_position)
    if not allow_long_vol:
        pos = pos.clip(lower=0.0)
    pos = pd.Series(pos, index=idx).fillna(0.0)

    # Enter only on rebalance dates; hold the book in between.
    active = pd.Series(0.0, index=idx)
    entry = pd.Series(False, index=idx)
    held = 0.0
    for i in range(len(idx)):
        if i % hold_days == 0:
            held = float(pos.iloc[i])
            entry.iloc[i] = True
        active.iloc[i] = held

    K = iv * np.sqrt(TRADING_DAYS)                          # annualized strike vol
    R = np.sqrt(rvar * TRADING_DAYS).clip(upper=cap_multiple * K)
    pnl_vol_pts = (K**2 - R**2) / (2 * K)                # per unit vega, short variance

    # Cost charged once per entry, on the size actually traded.
    prev = active.shift(hold_days).fillna(0.0)
    traded = (active - prev).abs().where(entry, 0.0)
    cost = traded * cost_vol_pts

    gross = active * pnl_vol_pts
    # Size so that a full position losing all the way to the cap costs
    # `risk_fraction` of capital: max loss per unit vega is
    # ((cap*K)^2 - K^2)/(2K) = K(cap^2 - 1)/2.
    max_loss_per_vega = K * (cap_multiple**2 - 1) / 2
    vega_notional = risk_fraction / max_loss_per_vega
    # A position entered at t pays over (t, t+hold_days]; spread the P&L evenly
    # so the return series is daily and Sharpe is not inflated by lumpiness.
    strat_return = (gross - cost) * vega_notional / hold_days

    out = pd.DataFrame({
        "iv_ann": K,
        "pred_rv_ann": pred * np.sqrt(TRADING_DAYS),
        "realized_rv_ann": np.sqrt(rvar * TRADING_DAYS),
        "realized_rv_ann_capped": R,
        "signal": sig,
        "position": active,
        "pnl_vol_points": gross,
        "cost": cost,
        "strategy_return": strat_return,
    })
    out["strategy_equity"] = (1 + out["strategy_return"]).cumprod()
    return out


def vrp_naive_benchmark(iv_daily: pd.Series, trailing_rv: pd.Series,
                        realized_var_fwd: pd.Series, **kwargs) -> pd.DataFrame:
    """Same trade, but sized off trailing realized vol instead of the model.

    This is the baseline the ML model has to beat *as a trading signal*. Simply
    always-short-variance harvests the premium too; the question is whether the
    forecast adds anything over that, and this is how you find out.
    """
    return vrp_backtest(iv_daily, trailing_rv, realized_var_fwd, **kwargs)


# --------------------------------------------------------------------------
# combining
# --------------------------------------------------------------------------

def combine(returns: dict[str, pd.Series],
            weights: dict[str, float] | None = None) -> pd.Series:
    """Weighted blend of strategy return streams on their shared dates.

    The vol-targeted index leg and the VRP carry leg are close to uncorrelated
    day to day -- one is long equity beta, the other is short a variance
    premium -- so blending them is the cheapest Sharpe improvement available.
    """
    df = pd.DataFrame(returns).dropna()
    if weights is None:
        weights = {k: 1.0 / len(returns) for k in returns}
    w = pd.Series(weights).reindex(df.columns).fillna(0.0)
    return (df * w).sum(axis=1)
