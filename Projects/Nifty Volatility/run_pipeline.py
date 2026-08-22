#!/usr/bin/env python3
"""End-to-end run: walk-forward validation, then both backtests side by side.

    python run_pipeline.py                 # live data if reachable, else synthetic
    python run_pipeline.py --synthetic     # force the synthetic market
    python run_pipeline.py --no-sentiment  # price + VIX only

The v1 configuration is reproduced alongside the v2 one so the difference is
attributable rather than asserted.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

RF = 0.065          # risk-free rate used for financing and excess-return Sharpe

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

import backtest
import baselines
import data as data_mod
import features
import model as model_mod
import signals
import validation
import volatility as vol

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda x: f"{x:,.4f}")


def _rule(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def load(args):
    if not args.synthetic:
        try:
            prices = data_mod.load_prices(years=args.years)
            vix = data_mod.load_india_vix(years=args.years)
            if len(prices) > 500:
                print(f"Live data: {len(prices)} sessions, "
                      f"{prices.index.min().date()} -> {prices.index.max().date()}")
                return prices, vix, False
        except Exception as exc:
            print(f"Live download failed ({type(exc).__name__}: {exc}); "
                  f"falling back to the synthetic market.")
    prices, vix = data_mod.simulate_market(n_days=args.years * 252, seed=args.seed)
    print(f"SYNTHETIC market: {len(prices)} sessions. "
          f"Verifies the code end to end; says nothing about the Nifty.")
    return prices, vix, True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--no-sentiment", action="store_true")
    ap.add_argument("--years", type=int, default=8)
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--garch", action="store_true", help="also fit the GARCH baseline (slow)")
    ap.add_argument("--short", action="store_true",
                    help="enable the short leg (off by default; check the IC first)")
    args = ap.parse_args()

    prices, vix, is_synth = load(args)

    news = None
    if not args.no_sentiment:
        if is_synth:
            news = data_mod.simulate_news(prices.index, prices, seed=args.seed + 1)
        else:
            print("No scored-news file wired in; running price + VIX only. "
                  "Point this at the FinBERT output to include sentiment.")

    table = features.build_feature_table(prices, news, vix, horizons=(1, 5))
    cols = features.feature_columns(table)
    print(f"\n{len(cols)} features: {cols}")

    garch_log = None
    if args.garch:
        print("\nFitting rolling GARCH(1,1) (slow)...")
        garch_log = baselines.garch_forecast(table["log_return"], refit_every=10)

    # ---------------------------------------------------------------- h=1
    _rule("WALK-FORWARD  (target: next-day log realized vol, gap-inclusive)")
    folds = validation.run_walk_forward(
        table, cols, target_col="target_log_rv_h1", garch_log=garch_log,
        train_years=2, test_months=2, step_months=2, n_trials=args.trials)
    preds = validation.stack_predictions(folds)

    _rule("FORECAST ERROR")
    errs = validation.error_table(preds)
    print(errs)
    base = errs.loc["har", "rmse"]
    print(f"\nModel vs HAR-RV : {100*(base-errs.loc['model','rmse'])/base:+.1f}% RMSE")
    nb = errs.loc["naive", "rmse"]
    print(f"Model vs naive  : {100*(nb-errs.loc['model','rmse'])/nb:+.1f}% RMSE  "
          f"(the weak baseline v1 headlined)")

    dm = validation.diebold_mariano(preds, "model", "har")
    verdict = ("model significantly better" if dm["statistic"] < 0 and dm["p_value"] < 0.05
               else "NOT significant -- the model does not beat HAR")
    print(f"\nDiebold-Mariano vs HAR: stat={dm['statistic']:+.2f}  "
          f"p={dm['p_value']:.4f}  n={dm['n']}  ->  {verdict}")

    # ---------------------------------------------------------------- h=5
    folds5 = validation.run_walk_forward(
        table, cols, target_col="target_log_rv_h5",
        train_years=2, test_months=2, step_months=2, n_trials=args.trials,
        verbose=False)
    preds5 = validation.stack_predictions(folds5)

    # ------------------------------------------------------------ backtests
    next_ret = table["log_return"].shift(-1)

    pred_vol_v2 = pd.Series(
        vol.log_to_level(preds["model"], 1.0) * preds["smearing"], index=preds.index)
    # v1: Garman-Klass units, no smearing correction -- the two unit bugs.
    gk_ratio = (table["gk_vol"] / table["rv"]).reindex(preds.index).median()
    pred_vol_v1 = pred_vol_v2 * gk_ratio / preds["smearing"]

    _rule("BACKTEST 1  --  volatility-targeted index exposure")
    v1 = backtest.vol_target_backtest(
        pred_vol_v1, next_ret, target_ann_vol=0.16, max_leverage=2.0,
        cost_bps=7.5, rf_annual=0.0, deadband=0.0)
    v2 = backtest.vol_target_backtest(
        pred_vol_v2, next_ret, target_ann_vol=0.12, max_leverage=1.5,
        cost_bps=7.5, rf_annual=0.065, deadband=0.10)

    rows = [
        backtest.summarize(v1["strategy_return"], label="v1 config (GK units, no smearing, 16% target, 2.0x cap, daily rebal, free leverage)"),
        backtest.summarize(v2["strategy_return"], label="v2 config (total-vol units, smeared, 12% target, 1.5x cap, deadband, financed)"),
        backtest.summarize(v2["buy_hold_return"], label="buy & hold"),
    ]
    print(pd.DataFrame(rows).set_index("label")[
        ["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "total_return"]])
    print(f"\nmean position   v1={v1['position'].mean():.2f}x   v2={v2['position'].mean():.2f}x")
    print(f"turnover        v1={v1['position'].diff().abs().sum():.0f}   "
          f"v2={v2['position'].diff().abs().sum():.0f}")
    print(f"cost drag /yr   v1={252*v1['cost'].mean():.2%}   v2={252*v2['cost'].mean():.2%}")
    print("\nNote: a long-only position sized by a vol forecast has no expected-return")
    print("edge -- Sharpe is invariant to leverage. This leg is a risk overlay, and")
    print("the honest claim is the drawdown, not the return.")

    # ------------------------------------------------------ long/short
    _rule("BACKTEST 1b  --  DIRECTIONAL: side from signals, size from the vol model")
    direction = signals.build_direction(table, allow_short=True)
    d_raw = direction["direction"].reindex(preds.index)
    nr = next_ret.reindex(preds.index)

    print("Information coefficient vs next-day return "
          "(read this before any equity curve):")
    print(signals.signal_report(direction.reindex(preds.index), nr).round(4))

    d_lo = signals.build_direction(table, allow_short=False)["direction"].reindex(preds.index)
    lo = backtest.long_short_backtest(
        d_lo, pred_vol_v2, next_ret, target_ann_vol=0.12, max_long=1.5,
        cost_bps=5.0, rf_annual=RF, deadband=0.10, stop_drawdown=-0.25)

    rows = [
        backtest.summarize(v2["strategy_return"], RF, label="overlay, no direction"),
        backtest.summarize(lo["strategy_return"], RF, label="directional, long-only"),
    ]

    ic = signals.information_coefficient(d_raw, nr)
    if args.short:
        ls = backtest.long_short_backtest(
            d_raw, pred_vol_v2, next_ret, target_ann_vol=0.12, max_long=1.5,
            max_short=-1.0, cost_bps=5.0, rf_annual=RF, deadband=0.10,
            stop_drawdown=-0.25)
        rows.append(backtest.summarize(ls["strategy_return"], RF,
                                       label="directional, LONG/SHORT"))
    else:
        ls = lo
        print(f"\nShorting off (pass --short to enable). Blended-signal IC t-stat "
              f"{ic['t_stat']:+.2f} (p={ic['p_value']:.3f}).")
        print("Above 2 means the direction signal is real and the short leg is worth")
        print("switching on. Below it, shorting buys turnover, financing drag and")
        print("tail risk in exchange for noise.")

    rows.append(backtest.summarize(lo["buy_hold_return"], RF,
                                   label="buy & hold (total return)"))
    print()
    print(pd.DataFrame(rows).set_index("label")[
        ["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "total_return"]])
    print(f"\ndays short {100*ls['is_short'].mean():.0f}%   "
          f"mean gross exposure {ls['gross_exposure'].mean():.2f}x   "
          f"mean net {ls['position'].mean():+.2f}x")
    print("Sharpe is EXCESS of the risk-free rate -- a book that parks in cash would")
    print("otherwise post a flattering ratio earned on T-bills.")

    # ---------------------------------------------------------------- VRP
    _rule("BACKTEST 2  --  variance risk premium carry (the profitable leg)")
    if table["iv_daily"].notna().sum() < 100:
        print("No India VIX available; skipping.")
        return

    if is_synth:
        print("!! SYNTHETIC IMPLIED VOL -- THESE NUMBERS ARE NOT A PERFORMANCE ESTIMATE.")
        print("!! The simulator's variance premium is a persistent AR(1) that any signal")
        print("!! can read off, so every row below prints an implausible Sharpe. This block")
        print("!! is here to prove the payoff arithmetic and the plumbing are right.")
        print("!! Run against real ^INDIAVIX for a number worth quoting; expect a Sharpe")
        print("!! around 0.8-1.3 with a deep left tail, not what you are about to see.\n")

    hold = 5
    pred_rv5 = pd.Series(np.exp(preds5["model"]) * preds5["smearing"], index=preds5.index)
    realized_fwd5 = table["target_rvar_h5"].reindex(pred_rv5.index)
    iv = table["iv_daily"].reindex(pred_rv5.index)
    trailing = np.exp(table["log_rv_w"]).reindex(pred_rv5.index)

    ok = iv.notna() & pred_rv5.notna() & realized_fwd5.notna() & trailing.notna()
    iv, pred_rv5, realized_fwd5, trailing = (
        iv[ok], pred_rv5[ok], realized_fwd5[ok], trailing[ok])

    kw = dict(hold_days=hold, cost_vol_pts=0.005, risk_fraction=0.15,
              cap_multiple=3.0, max_position=1.0, scale=3.0)

    always = backtest.vrp_backtest(iv, iv, realized_fwd5, entry_z=-1e9, **kw)
    naive_sig = backtest.vrp_naive_benchmark(iv, trailing, realized_fwd5, **kw)
    modelled = backtest.vrp_backtest(iv, pred_rv5, realized_fwd5, **kw)

    rows = [
        backtest.summarize(always["strategy_return"], label="always short variance (harvest only)"),
        backtest.summarize(naive_sig["strategy_return"], label="sized off trailing 5d realized vol"),
        backtest.summarize(modelled["strategy_return"], label="sized off the model's RV forecast"),
    ]
    print(pd.DataFrame(rows).set_index("label")[
        ["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown", "skew", "worst_day"]])
    print("\nThe model earns its keep here only if it beats BOTH rows above it: the")
    print("premium itself is free, timing it is the claim. Note the negative skew on")
    print("the untimed row -- short variance is picking up nickels in front of a")
    print("steamroller. See CRITICAL_ANALYSIS.md section 5 before quoting any of this.")

    # -------------------------------------------------------------- blend
    _rule("BLEND  --  vol-targeted index + VRP carry")
    blended = backtest.combine(
        {"index": v2["strategy_return"], "vrp": modelled["strategy_return"]},
        {"index": 0.7, "vrp": 0.3})
    corr = pd.DataFrame({"a": v2["strategy_return"], "b": modelled["strategy_return"]}
                        ).dropna().corr().iloc[0, 1]
    rows = [
        backtest.summarize(v2["strategy_return"], label="index leg only"),
        backtest.summarize(modelled["strategy_return"], label="VRP leg only"),
        backtest.summarize(blended, label="70/30 blend"),
        backtest.summarize(v2["buy_hold_return"], label="buy & hold"),
    ]
    print(pd.DataFrame(rows).set_index("label")[
        ["cagr", "ann_vol", "sharpe", "sortino", "max_drawdown"]])
    print(f"\nleg correlation = {corr:+.3f}")


if __name__ == "__main__":
    main()
