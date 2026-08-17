"""Volatility-targeting backtest.

Position size is scaled inversely to predicted volatility: a larger
position when the model predicts low volatility, a smaller one when it
predicts high volatility, capped at `max_leverage`. Transaction costs are
charged on every change in position -- a backtest without costs is not a
credible backtest.
"""

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def vol_target_positions(predicted_vol: pd.Series, target_daily_vol: float = 0.01,
                          max_leverage: float = 2.0) -> pd.Series:
    """position_t = clip(target_daily_vol / predicted_vol_t, 0, max_leverage)."""
    raw = target_daily_vol / predicted_vol.replace(0, np.nan)
    return raw.clip(lower=0, upper=max_leverage).fillna(0.0)


def run_backtest(predicted_vol: pd.Series, realized_return: pd.Series,
                  target_daily_vol: float = 0.01, max_leverage: float = 2.0,
                  cost_bps: float = 7.5) -> pd.DataFrame:
    """Run the vol-targeting strategy and a buy-and-hold benchmark side by side.

    `predicted_vol` and `realized_return` must be aligned on the same date
    index (`realized_return` is the *next* trading day's actual log return,
    i.e. the return realized while holding the position sized off
    `predicted_vol`).
    """
    idx = predicted_vol.index.intersection(realized_return.index)
    pred_vol = predicted_vol.loc[idx]
    ret = realized_return.loc[idx]

    positions = vol_target_positions(pred_vol, target_daily_vol, max_leverage)
    position_change = positions.diff().abs().fillna(positions.abs())
    cost = position_change * (cost_bps / 10_000)

    strategy_return = positions * ret - cost
    buy_hold_return = ret

    out = pd.DataFrame({
        "position": positions,
        "realized_return": ret,
        "strategy_return": strategy_return,
        "buy_hold_return": buy_hold_return,
        "transaction_cost": cost,
    })
    out["strategy_equity"] = (1 + out["strategy_return"]).cumprod()
    out["buy_hold_equity"] = (1 + out["buy_hold_return"]).cumprod()
    return out


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    excess = returns - risk_free_rate / TRADING_DAYS_PER_YEAR
    if excess.std() == 0 or excess.empty:
        return 0.0
    return float(np.sqrt(TRADING_DAYS_PER_YEAR) * excess.mean() / excess.std())


def max_drawdown(equity_curve: pd.Series) -> float:
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0
    return float(drawdown.min())


def backtest_summary(backtest_df: pd.DataFrame) -> dict:
    return {
        "strategy_sharpe": sharpe_ratio(backtest_df["strategy_return"]),
        "buy_hold_sharpe": sharpe_ratio(backtest_df["buy_hold_return"]),
        "strategy_max_drawdown": max_drawdown(backtest_df["strategy_equity"]),
        "buy_hold_max_drawdown": max_drawdown(backtest_df["buy_hold_equity"]),
        "strategy_total_return": float(backtest_df["strategy_equity"].iloc[-1] - 1),
        "buy_hold_total_return": float(backtest_df["buy_hold_equity"].iloc[-1] - 1),
        "strategy_annualized_vol": float(backtest_df["strategy_return"].std() * np.sqrt(TRADING_DAYS_PER_YEAR)),
        "total_transaction_cost": float(backtest_df["transaction_cost"].sum()),
    }
