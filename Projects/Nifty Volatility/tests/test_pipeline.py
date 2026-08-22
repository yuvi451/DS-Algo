"""Tests. These verify the *code*, and pin down the two unit bugs from v1.

Run with:  python -m pytest tests/ -q     (from the project root)
"""

import sys
import pathlib

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import backtest
import baselines
import data
import features
import validation
import volatility as vol


@pytest.fixture(scope="module")
def market():
    prices, vix = data.simulate_market(n_days=1600, seed=3, gap_share=0.35)
    return prices, vix


# --------------------------------------------------------------------------
# the unit bug that caused v1's over-leverage
# --------------------------------------------------------------------------

def test_gk_understates_total_vol(market):
    """Garman-Klass measures intraday vol only; the traded return includes the gap."""
    prices, _ = market
    gk = vol.realized_vol(prices, "gk")
    total = vol.realized_vol(prices, "total")
    ratio = (gk.mean() / total.mean())
    # with a 35% overnight variance share the ratio should be near sqrt(0.65)
    assert 0.72 < ratio < 0.88, ratio


def test_total_variance_matches_close_to_close(market):
    """The gap-inclusive estimator must reproduce close-to-close variance."""
    prices, _ = market
    est = vol.total_daily_variance(prices).dropna().mean()
    actual = np.log(prices["close"] / prices["close"].shift(1)).dropna().var()
    assert abs(est - actual) / actual < 0.15, (est, actual)


def test_sizing_off_gk_over_levers(market):
    """Reproduce v1's bug: same target, wrong denominator, ~1.3x too much risk."""
    prices, _ = market
    ret = np.log(prices["close"] / prices["close"].shift(1)).shift(-1)
    target_daily = 0.12 / np.sqrt(252)

    pos_gk = (target_daily / vol.realized_vol(prices, "gk")).clip(0, 3)
    pos_total = (target_daily / vol.realized_vol(prices, "total")).clip(0, 3)

    vol_gk = (pos_gk * ret).std()
    vol_total = (pos_total * ret).std()
    assert vol_gk / vol_total > 1.15, vol_gk / vol_total


def test_smearing_corrects_log_bias():
    """exp(mean of log) is the median; smearing recovers the mean."""
    rng = np.random.default_rng(0)
    true_level = 0.01
    resid = rng.standard_normal(20000) * 0.41
    observed = true_level * np.exp(resid)

    naive = np.exp(np.log(observed).mean())
    smeared = naive * vol.smearing_factor(np.log(observed) - np.log(observed).mean())

    assert naive < observed.mean() * 0.96           # v1's bias: forecast too low
    assert abs(smeared - observed.mean()) / observed.mean() < 0.03


# --------------------------------------------------------------------------
# features and targets
# --------------------------------------------------------------------------

def test_targets_are_forward_looking_only(market):
    """target_log_rv_h1 at t must equal log_rv at t+1 -- no leakage, no off-by-one."""
    prices, vix = market
    table = features.build_feature_table(prices, None, vix, horizons=(1, 5))
    shifted = table["log_rv"].shift(-1)
    ok = table["target_log_rv_h1"].notna() & shifted.notna()
    assert np.allclose(table.loc[ok, "target_log_rv_h1"], shifted[ok])


def test_h5_target_is_forward_mean(market):
    prices, vix = market
    table = features.build_feature_table(prices, None, vix, horizons=(5,))
    i = 300
    expected = table["log_rv"].iloc[i + 1: i + 6].mean()
    assert abs(table["target_log_rv_h5"].iloc[i] - expected) < 1e-10


def test_variance_target_exceeds_squared_log_target(market):
    """Jensen: arithmetic realized variance > the squared geometric mean.

    Settling a variance swap on the log-mean target understates realized
    variance on exactly the spiky periods that hurt a short-vol book.
    """
    prices, vix = market
    table = features.build_feature_table(prices, None, vix, horizons=(5,))
    ok = table["target_rvar_h5"].notna()
    geo = np.exp(2 * table.loc[ok, "target_log_rv_h5"])
    ari = table.loc[ok, "target_rvar_h5"]
    assert (ari >= geo - 1e-18).all()
    assert ari.mean() > geo.mean() * 1.05


def test_no_feature_uses_future_information(market):
    """Every feature at t must be computable from data up to and including t."""
    prices, vix = market
    full = features.build_feature_table(prices, None, vix)
    cutoff = 900
    truncated = features.build_feature_table(
        prices.iloc[:cutoff], None, vix.iloc[:cutoff])
    cols = features.feature_columns(full)
    a = full[cols].iloc[cutoff - 1]
    b = truncated[cols].iloc[cutoff - 1]
    pd.testing.assert_series_equal(a, b, check_names=False, rtol=1e-9)


def test_sentiment_missing_days_stay_nan(market):
    """'No news' must not be encoded as 'neutral news' -- that was a v1 bug."""
    prices, vix = market
    news = data.simulate_news(prices.index[:400], prices)
    table = features.build_feature_table(prices, news, vix)
    assert table["sent_abs_mean"].iloc[500:].isna().all()
    assert table["has_news"].iloc[500:].eq(0).all()


def test_news_volume_feature_is_stationary(market):
    """A raw article count drifts and becomes a date proxy; the z-score must not."""
    prices, _ = market
    news = data.simulate_news(prices.index, prices)
    daily = features.add_sentiment_dynamics(features.aggregate_daily_sentiment(news))
    z = daily["news_vol_z"].dropna()
    first, second = z.iloc[: len(z) // 2], z.iloc[len(z) // 2:]
    assert abs(first.mean() - second.mean()) < 0.35


# --------------------------------------------------------------------------
# baselines
# --------------------------------------------------------------------------

def test_har_beats_naive(market):
    """The bar v1 should have used. HAR must beat single-day persistence."""
    prices, _ = market
    table = features.build_feature_table(prices, None, None, horizons=(1,))
    df = table.dropna(subset=["target_log_rv_h1", "log_rv_m"])
    X = baselines.har_design(df["log_rv"])
    y = df["target_log_rv_h1"]
    cut = len(df) // 2

    har = baselines.HARModel().fit(X.iloc[:cut], y.iloc[:cut])
    rmse_har = np.sqrt(np.mean((har.predict(X.iloc[cut:]) - y.iloc[cut:]) ** 2))
    rmse_naive = np.sqrt(np.mean((df["log_rv"].iloc[cut:] - y.iloc[cut:]) ** 2))
    assert rmse_har < rmse_naive


def test_diebold_mariano_detects_a_real_difference():
    rng = np.random.default_rng(1)
    n = 1200
    y = rng.standard_normal(n)
    preds = pd.DataFrame({
        "y_true": y,
        "good": y + rng.standard_normal(n) * 0.5,
        "bad": y + rng.standard_normal(n) * 1.0,
    }, index=pd.bdate_range("2020-01-01", periods=n))
    dm = validation.diebold_mariano(preds, "good", "bad")
    assert dm["statistic"] < 0        # 'good' has lower loss
    assert dm["p_value"] < 0.01


def test_diebold_mariano_finds_nothing_when_there_is_nothing():
    rng = np.random.default_rng(2)
    n = 1200
    y = rng.standard_normal(n)
    preds = pd.DataFrame({
        "y_true": y,
        "a": y + rng.standard_normal(n) * 0.7,
        "b": y + rng.standard_normal(n) * 0.7,
    }, index=pd.bdate_range("2020-01-01", periods=n))
    assert validation.diebold_mariano(preds, "a", "b")["p_value"] > 0.05


# --------------------------------------------------------------------------
# backtest mechanics
# --------------------------------------------------------------------------

def test_deadband_cuts_turnover(market):
    prices, _ = market
    pv = vol.realized_vol(prices, "total").dropna()
    ret = np.log(prices["close"] / prices["close"].shift(1)).shift(-1).reindex(pv.index)

    loose = backtest.vol_target_backtest(pv, ret, deadband=0.0)
    tight = backtest.vol_target_backtest(pv, ret, deadband=0.10)
    turn_loose = loose["position"].diff().abs().sum()
    turn_tight = tight["position"].diff().abs().sum()
    assert turn_tight < 0.65 * turn_loose


def test_financing_is_actually_charged(market):
    """v1 handed the strategy free leverage. Leverage must cost something."""
    prices, _ = market
    pv = pd.Series(0.004, index=prices.index)   # low vol -> pinned at max leverage
    ret = np.log(prices["close"] / prices["close"].shift(1)).shift(-1)
    bt = backtest.vol_target_backtest(pv, ret, max_leverage=1.5, rf_annual=0.065)
    assert bt["position"].mean() > 1.4
    assert bt["financing"].sum() > 0


def test_vrp_payoff_sign_and_cap():
    """Short variance profits when realized comes in under implied."""
    idx = pd.bdate_range("2020-01-01", periods=200)
    iv = pd.Series(0.20 / np.sqrt(252), index=idx)
    pred = pd.Series(0.14 / np.sqrt(252), index=idx)     # model says calm -> sell

    # realized *variance* over the holding period, which is what settles
    calm = pd.Series((0.10 / np.sqrt(252)) ** 2, index=idx)
    storm = pd.Series((0.90 / np.sqrt(252)) ** 2, index=idx)

    win = backtest.vrp_backtest(iv, pred, calm, cost_vol_pts=0.0)
    lose = backtest.vrp_backtest(iv, pred, storm, cost_vol_pts=0.0)

    assert win["position"].mean() > 0                    # short variance
    assert win["pnl_vol_points"].mean() > 0
    assert lose["pnl_vol_points"].mean() < 0
    # the cap must bound the loss at cap_multiple * strike
    assert lose["realized_rv_ann_capped"].max() <= 3.0 * 0.20 + 1e-9


def test_vrp_costs_charged_once_per_holding_period():
    idx = pd.bdate_range("2020-01-01", periods=100)
    iv = pd.Series(0.20 / np.sqrt(252), index=idx)
    pred = pd.Series(0.14 / np.sqrt(252), index=idx)
    rvar = pd.Series((0.12 / np.sqrt(252)) ** 2, index=idx)
    bt = backtest.vrp_backtest(iv, pred, rvar, hold_days=5, cost_vol_pts=0.005)
    assert (bt["cost"] > 0).sum() <= len(idx) // 5 + 1


def test_vol_matched_equalizes_risk(market):
    prices, _ = market
    a = pd.Series(np.random.default_rng(5).standard_normal(500) * 0.02)
    b = pd.Series(np.random.default_rng(6).standard_normal(500) * 0.01)
    assert abs(backtest.vol_matched(a, b).std() - b.std()) < 1e-12


# --------------------------------------------------------------------------
# walk-forward hygiene
# --------------------------------------------------------------------------

def test_walk_forward_folds_never_overlap(market):
    prices, _ = market
    idx = prices.index
    for train_mask, test_mask in validation.generate_folds(idx, train_years=2):
        assert not (train_mask & test_mask).any()
        assert idx[train_mask].max() < idx[test_mask].min()


# --------------------------------------------------------------------------
# directional signals and shorting
# --------------------------------------------------------------------------

import signals  # noqa: E402


def test_signals_are_causal(market):
    """A signal at t must not change when future data is appended."""
    prices, vix = market
    full = features.build_feature_table(prices, None, vix)
    cut = 900
    trunc = features.build_feature_table(prices.iloc[:cut], None, vix.iloc[:cut])
    a = signals.build_direction(full).iloc[cut - 1]
    b = signals.build_direction(trunc).iloc[cut - 1]
    pd.testing.assert_series_equal(a, b, check_names=False, rtol=1e-9)


def test_direction_is_bounded(market):
    prices, vix = market
    table = features.build_feature_table(prices, None, vix)
    d = signals.build_direction(table)["direction"]
    assert d.between(-1.0, 1.0).all()
    assert d.notna().all()


def test_allow_short_false_never_goes_negative(market):
    prices, vix = market
    table = features.build_feature_table(prices, None, vix)
    d = signals.build_direction(table, allow_short=False)["direction"]
    assert (d >= 0).all()
    assert signals.build_direction(table, allow_short=True)["direction"].min() < 0


def test_information_coefficient_detects_a_planted_signal():
    rng = np.random.default_rng(4)
    n = 2000
    idx = pd.bdate_range("2015-01-01", periods=n)
    sig = pd.Series(rng.standard_normal(n), index=idx)
    ret = pd.Series(0.20 * sig.to_numpy() + rng.standard_normal(n), index=idx)
    good = signals.information_coefficient(sig, ret)
    noise = signals.information_coefficient(
        pd.Series(rng.standard_normal(n), index=idx), ret)
    assert good["ic"] > 0 and good["p_value"] < 0.05
    assert noise["p_value"] > 0.05


def test_futures_carry_cases():
    """Long earns the dividend yield; flat earns the risk-free rate; short pays."""
    rf, q = 0.065, 0.012
    pos = pd.Series([1.0, 0.0, -1.0])
    c = backtest.futures_carry(pos, rf, q)
    assert abs(c.iloc[0] - q / 252) < 1e-12          # long: price return + q
    assert abs(c.iloc[1] - rf / 252) < 1e-12         # flat: earns cash
    assert abs(c.iloc[2] - (-q + 2 * rf) / 252) < 1e-12   # short: pays q, earns rf twice


def test_short_positions_actually_occur_and_profit_when_market_falls():
    idx = pd.bdate_range("2020-01-01", periods=400)
    down = pd.Series(-0.003, index=idx)               # steady decline
    pv = pd.Series(0.01, index=idx)
    short = pd.Series(-1.0, index=idx)
    bt = backtest.long_short_backtest(short, pv, down, deadband=0.0,
                                      stop_drawdown=None, max_short=-1.0)
    assert (bt["position"] < 0).all()
    assert bt["strategy_return"].mean() > 0            # short profits as it falls
    assert bt["buy_hold_return"].mean() < 0


def test_drawdown_stop_bounds_the_loss():
    idx = pd.bdate_range("2020-01-01", periods=400)
    ret = pd.Series(-0.004, index=idx)
    pv = pd.Series(0.01, index=idx)
    always_long = pd.Series(1.0, index=idx)

    stopped = backtest.long_short_backtest(always_long, pv, ret, deadband=0.0,
                                           stop_drawdown=-0.20)
    unstopped = backtest.long_short_backtest(always_long, pv, ret, deadband=0.0,
                                             stop_drawdown=None)
    assert backtest.max_drawdown(stopped["strategy_equity"]) > -0.30
    assert (backtest.max_drawdown(stopped["strategy_equity"])
            > backtest.max_drawdown(unstopped["strategy_equity"]))


def test_long_short_reduces_to_long_only_when_direction_is_one(market):
    """Sanity: direction == 1 everywhere should track the long-only overlay."""
    prices, vix = market
    table = features.build_feature_table(prices, None, vix)
    pv = table["rv"].dropna()
    ret = table["log_return"].shift(-1).reindex(pv.index)
    ones = pd.Series(1.0, index=pv.index)

    ls = backtest.long_short_backtest(ones, pv, ret, target_ann_vol=0.12,
                                      max_long=1.5, cost_bps=7.5, div_yield=0.0,
                                      stop_drawdown=None, deadband=0.10)
    lo = backtest.vol_target_backtest(pv, ret, target_ann_vol=0.12,
                                      max_leverage=1.5, cost_bps=7.5,
                                      deadband=0.10)
    pd.testing.assert_series_equal(ls["position"], lo["position"],
                                   check_names=False, rtol=1e-9)
