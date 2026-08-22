"""Feature construction.

Three changes from v1, in descending order of how much they matter:

1. **India VIX is now a feature.** Its absence was the single biggest miss in
   v1. Implied volatility is a forward-looking, market-consensus volatility
   forecast; it is the strongest known predictor of next-day realized vol and
   it subsumes most of what news sentiment could ever tell you. A vol model
   that does not use it is competing with one hand tied.

2. **Targets are gap-inclusive and multi-horizon.** See src/volatility.py for
   why. ``h=1`` keeps the error metrics comparable with v1; ``h=5`` is what the
   tradeable weekly-expiry strategy actually needs.

3. **Sentiment features measure intensity and surprise, not direction.**
   v1 fed the model ``mean(polarity)`` -- a *signed* quantity -- and asked it to
   predict a *magnitude*. Good news and bad news both raise volatility, so the
   sign is close to irrelevant and averaging ~50 headlines crushes what little
   variance remains. What actually moves volatility is how much is being
   written, how extreme it is, and how much the outlets disagree. Missing days
   are also left as NaN rather than filled with 0.0: in v1, "no news" and
   "perfectly balanced news" were encoded identically, which is a contaminated
   feature. LightGBM routes NaN natively.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from volatility import (
    TRADING_DAYS,
    deannualize,
    garman_klass_variance,
    realized_vol,
)

EPS = 1e-8

PRICE_FEATURES = [
    "log_rv", "log_rv_w", "log_rv_m", "log_rv_q",
    "log_gk", "log_gap_share",
    "ret_1d", "ret_5d", "neg_ret_1d",
    "rv_trend", "rv_of_rv",
    "day_of_week",
]

VIX_FEATURES = [
    "log_iv", "log_vrp", "vix_chg_1d", "vix_chg_5d", "log_iv_slope",
]

SENTIMENT_FEATURES = [
    "sent_abs_mean", "sent_disp", "sent_tail_share", "sent_neg_share",
    "sent_skew", "news_vol_z", "sent_abs_shock", "sent_disp_roll3",
    "sent_abs_mean_roll5", "has_news",
]


# --------------------------------------------------------------------------
# price / autoregressive block
# --------------------------------------------------------------------------

def build_price_features(prices: pd.DataFrame) -> pd.DataFrame:
    """Realized-vol, HAR-style and return features, all known at date t's close."""
    out = prices.copy()

    out["log_return"] = np.log(out["close"] / out["close"].shift(1))
    out["rv"] = realized_vol(out, "total")      # gap-inclusive -- what we trade
    out["gk_vol"] = realized_vol(out, "gk")     # intraday only -- kept for reference
    out["log_rv"] = np.log(out["rv"] + EPS)
    out["log_gk"] = np.log(out["gk_vol"] + EPS)

    # Share of the day's variance that came from the overnight gap. Regime
    # information: gap-heavy periods are event-driven, range-heavy are grind.
    gk_var = garman_klass_variance(out)
    out["log_gap_share"] = np.log(
        ((out["rv"] ** 2 - gk_var).clip(lower=0) + EPS) / (out["rv"] ** 2 + EPS)
    )

    # HAR (Corsi 2009) cascade: daily / weekly / monthly / quarterly log-RV.
    out["log_rv_w"] = out["log_rv"].rolling(5).mean()
    out["log_rv_m"] = out["log_rv"].rolling(22).mean()
    out["log_rv_q"] = out["log_rv"].rolling(66).mean()

    out["ret_1d"] = out["log_return"]
    out["ret_5d"] = out["log_return"].rolling(5).sum()
    # Leverage effect: downside returns raise future vol far more than upside.
    out["neg_ret_1d"] = out["log_return"].clip(upper=0.0)

    out["rv_trend"] = out["log_rv_w"] - out["log_rv_m"]
    out["rv_of_rv"] = out["log_rv"].rolling(22).std()

    out["day_of_week"] = out.index.dayofweek
    return out


def add_vix_features(df: pd.DataFrame, vix_close: pd.Series | None) -> pd.DataFrame:
    """Join India VIX and derive the implied-vs-realized spread.

    ``vix_close`` is the India VIX closing level in annualized percent (the way
    it is quoted). The close at date t is known at t's close, so using it to
    forecast t+1 is not leakage.
    """
    out = df.copy()
    if vix_close is None or len(vix_close) == 0:
        for col in VIX_FEATURES:
            out[col] = np.nan
        out["iv_daily"] = np.nan
        return out

    vix = vix_close.reindex(out.index).ffill(limit=3)
    out["vix"] = vix
    out["iv_daily"] = deannualize(vix / 100.0)
    out["log_iv"] = np.log(out["iv_daily"] + EPS)

    # The variance risk premium in log space -- implied vol richness over
    # trailing realized. Strongly mean-reverting, and the core trading signal.
    out["log_vrp"] = out["log_iv"] - out["log_rv_w"]

    out["vix_chg_1d"] = out["log_iv"].diff()
    out["vix_chg_5d"] = out["log_iv"].diff(5)
    # Term-structure proxy: spot IV vs its own recent average.
    out["log_iv_slope"] = out["log_iv"] - out["log_iv"].rolling(22).mean()
    return out


# --------------------------------------------------------------------------
# sentiment block
# --------------------------------------------------------------------------

def aggregate_daily_sentiment(scored_news: pd.DataFrame) -> pd.DataFrame:
    """One row per trading day of *volatility-relevant* sentiment aggregates.

    Expects the columns produced by the v1 FinBERT step: ``trading_day``,
    ``polarity`` (= P(pos) - P(neg)), ``positive``, ``negative``.
    """
    cols = ["trading_day", "sent_mean", "sent_abs_mean", "sent_disp",
            "sent_tail_share", "sent_neg_share", "sent_skew", "article_count"]
    if scored_news is None or len(scored_news) == 0:
        return pd.DataFrame(columns=cols)

    news = scored_news.copy()
    news["abs_polarity"] = news["polarity"].abs()
    # "Tail" = an unambiguously charged headline. Averaging polarity over a day
    # hides these; their *count* is what tracks volatility.
    news["is_tail"] = (news["abs_polarity"] > 0.8).astype(float)
    news["is_negative"] = (news["negative"] > news["positive"]).astype(float)

    g = news.groupby("trading_day")
    daily = g.agg(
        sent_mean=("polarity", "mean"),
        sent_abs_mean=("abs_polarity", "mean"),
        sent_disp=("polarity", "std"),
        sent_tail_share=("is_tail", "mean"),
        sent_neg_share=("is_negative", "mean"),
        sent_skew=("polarity", "skew"),
        article_count=("polarity", "size"),
    ).reset_index()

    # std/skew are undefined for a 1-headline day; 0 dispersion is the honest
    # reading, but skew is genuinely unknown.
    daily["sent_disp"] = daily["sent_disp"].fillna(0.0)
    return daily[cols]


def add_sentiment_dynamics(daily: pd.DataFrame, baseline_window: int = 60) -> pd.DataFrame:
    """Turn level features into *stationary* surprise features.

    Raw ``article_count`` drifts with outlet coverage and with GDELT's own
    indexing over the years, so a tree that learns "count > 80 means high vol"
    in fold 3 is learning a date proxy, not a signal. What is stationary is the
    count relative to its own recent baseline -- a news-volume shock.
    """
    out = daily.sort_values("trading_day").reset_index(drop=True)

    log_count = np.log1p(out["article_count"])
    roll_mu = log_count.rolling(baseline_window, min_periods=10).mean()
    roll_sd = log_count.rolling(baseline_window, min_periods=10).std()
    out["news_vol_z"] = (log_count - roll_mu) / roll_sd.replace(0, np.nan)

    abs_mu = out["sent_abs_mean"].rolling(baseline_window, min_periods=10).mean()
    abs_sd = out["sent_abs_mean"].rolling(baseline_window, min_periods=10).std()
    out["sent_abs_shock"] = (out["sent_abs_mean"] - abs_mu) / abs_sd.replace(0, np.nan)

    out["sent_disp_roll3"] = out["sent_disp"].rolling(3, min_periods=1).mean()
    out["sent_abs_mean_roll5"] = out["sent_abs_mean"].rolling(5, min_periods=1).mean()
    return out


def build_feature_table(prices: pd.DataFrame,
                        scored_news: pd.DataFrame | None = None,
                        vix_close: pd.Series | None = None,
                        horizons: tuple[int, ...] = (1, 5),
                        baseline_window: int = 60) -> pd.DataFrame:
    """Assemble the full daily feature table plus targets for each horizon."""
    table = build_price_features(prices)
    table = add_vix_features(table, vix_close)

    daily = aggregate_daily_sentiment(scored_news)
    if len(daily) > 0:
        daily = add_sentiment_dynamics(daily, baseline_window)
        table = table.merge(
            daily.set_index("trading_day"),
            left_index=True, right_index=True, how="left",
        )
        table["has_news"] = table["article_count"].notna().astype(float)
        # Deliberately NOT filling the sentiment columns: NaN means "no news",
        # which is different information from "neutral news".
    else:
        for col in SENTIMENT_FEATURES:
            table[col] = np.nan
        table["has_news"] = 0.0

    return add_targets(table, horizons)


def add_targets(table: pd.DataFrame, horizons: tuple[int, ...] = (1, 5)) -> pd.DataFrame:
    """Forward realized volatility over the next ``h`` trading days.

    Two targets per horizon, because they are used for different things and
    conflating them is a real source of error:

    ``target_log_rv_h{h}``
        Mean of forward *log* vol. This is the modelling target -- log-vol is
        near-Gaussian and homoscedastic, which is what a squared-error
        objective wants.

    ``target_rvar_h{h}``
        Mean of forward *variance*, i.e. arithmetic realized variance. This is
        what a variance swap actually settles against, and it is strictly
        larger than the squared geometric mean by Jensen. Using the log-mean
        target to settle the VRP payoff understates realized variance on
        exactly the spiky days that hurt a short-vol book, which flatters the
        strategy precisely where it should be punished.
    """
    out = table.copy()
    var = out["rv"] ** 2
    for h in horizons:
        out[f"target_log_rv_h{h}"] = (
            out["log_rv"].shift(-1).rolling(h, min_periods=h).mean().shift(-(h - 1)))
        out[f"target_rvar_h{h}"] = (
            var.shift(-1).rolling(h, min_periods=h).mean().shift(-(h - 1)))
    return out


def feature_columns(table: pd.DataFrame, use_sentiment: bool = True,
                    use_vix: bool = True) -> list[str]:
    cols = [c for c in PRICE_FEATURES if c in table.columns]
    if use_vix:
        cols += [c for c in VIX_FEATURES if c in table.columns
                 and table[c].notna().any()]
    if use_sentiment:
        cols += [c for c in SENTIMENT_FEATURES if c in table.columns
                 and table[c].notna().any()]
    return cols
