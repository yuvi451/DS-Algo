"""Data loading, plus a synthetic market for testing without network access.

**On sourcing the data.** yfinance is the convenient path and usually works,
but Yahoo rate-limits datacenter IP ranges hard, and Kaggle/Colab runners sit
squarely in those ranges. A run can fail with 429 or an empty frame on a day
when the same call works fine from a laptop. So the loader tries several
sources in order of reliability rather than assuming one:

1. **Local CSV** -- a Kaggle dataset mounted into the notebook. No internet
   required at all, so it cannot be rate-limited. This is the only route that
   is guaranteed to work, and it is the one to use if a run matters.
2. **yfinance** -- convenient, usually fine, occasionally throttled.
3. **Stooq** -- a different host with a friendlier attitude to datacenter IPs.
   It carries the Nifty index but *not* India VIX.

India VIX is the dependency that actually matters. Without it there is no
implied-vol series, and without that the variance-risk-premium strategy -- the
only leg with a real expected-return edge -- cannot run at all. The vol
forecasting and the directional book still work on price data alone.

``simulate_market`` generates a series with the structural properties this
project depends on -- volatility clustering, a leverage effect, a realistic
overnight-gap share of variance, and an implied vol carrying a positive
variance risk premium -- so the pipeline can be exercised end to end offline.
Synthetic results verify that the *code* is correct. They say nothing about
whether the strategy works on the Nifty.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

from volatility import realized_vol

TRADING_DAYS = 252

_OHLC_ALIASES = {
    "date": "date", "datetime": "date", "timestamp": "date", "time": "date",
    "open": "open", "high": "high", "low": "low",
    "close": "close", "adj close": "close", "adj_close": "close",
    "price": "close", "ltp": "close", "closing value": "close",
    "shares traded": "volume", "volume": "volume", "vol": "volume",
    "turnover": "turnover",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map the many spellings CSV exports use onto our canonical names.

    NSE's own exports, Kaggle datasets and Yahoo CSVs all differ; normalising
    here is cheaper than making every caller guess.
    """
    out = df.copy()
    out.columns = [_OHLC_ALIASES.get(str(c).strip().lower(), str(c).strip().lower())
                   for c in out.columns]
    return out.loc[:, ~out.columns.duplicated()]


def load_ohlc_csv(path: str | pathlib.Path) -> pd.DataFrame:
    """Read an OHLC CSV with tolerant column naming and a parsed date index."""
    df = _normalize_columns(pd.read_csv(path))
    if "date" not in df.columns:
        raise ValueError(f"{path}: no recognisable date column in {list(df.columns)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["date"]).set_index("date").sort_index()
    df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    df.index.name = "date"

    missing = {"open", "high", "low", "close"} - set(df.columns)
    if missing:
        raise ValueError(f"{path}: missing {sorted(missing)}")

    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            # Indian exports frequently carry thousands separators.
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "", regex=False),
                errors="coerce")
    if "volume" not in df.columns:
        df["volume"] = np.nan

    return df[["open", "high", "low", "close", "volume"]].dropna(
        subset=["open", "high", "low", "close"])


def load_vix_csv(path: str | pathlib.Path) -> pd.Series:
    """Read an India VIX CSV; returns the closing level in annualized percent."""
    df = load_ohlc_csv(path) if _has_ohlc(path) else _load_single_series_csv(path)
    s = df["close"] if isinstance(df, pd.DataFrame) else df
    return s.rename("vix").dropna()


def _has_ohlc(path) -> bool:
    cols = set(_normalize_columns(pd.read_csv(path, nrows=1)).columns)
    return {"open", "high", "low", "close"}.issubset(cols)


def _load_single_series_csv(path) -> pd.Series:
    df = _normalize_columns(pd.read_csv(path))
    if "date" not in df.columns:
        raise ValueError(f"{path}: no recognisable date column")
    value_cols = [c for c in df.columns if c != "date"]
    if not value_cols:
        raise ValueError(f"{path}: no value column")
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["date"]).set_index("date").sort_index()
    return pd.to_numeric(
        df[value_cols[-1]].astype(str).str.replace(",", "", regex=False),
        errors="coerce")


def _from_yfinance(ticker: str, years: int):
    try:
        import yfinance as yf
        df = yf.download(ticker, period=f"{years}y", interval="1d",
                         auto_adjust=False, progress=False, threads=False)
    except Exception:
        return None
    if df is None or len(df) == 0:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    if "close" not in df.columns:
        return None
    if "volume" not in df.columns:
        df["volume"] = np.nan
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    return df[keep].dropna(subset=["close"])


def _from_stooq(candidates: tuple[str, ...], years: int):
    """Stooq via pandas-datareader. Carries the Nifty index; not India VIX."""
    try:
        from pandas_datareader import data as pdr
    except Exception:
        return None
    start = pd.Timestamp.today() - pd.DateOffset(years=years)
    for sym in candidates:
        try:
            df = pdr.DataReader(sym, "stooq", start=start)
        except Exception:
            continue
        if df is None or len(df) < 200:
            continue
        df = df.rename(columns=str.lower).sort_index()
        if "volume" not in df.columns:
            df["volume"] = np.nan
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "date"
        return df[["open", "high", "low", "close", "volume"]].dropna(
            subset=["open", "high", "low", "close"])
    return None


def load_market_data(price_ticker: str = "^NSEI",
                     vix_ticker: str = "^INDIAVIX",
                     years: int = 10,
                     price_csv: str | pathlib.Path | None = None,
                     vix_csv: str | pathlib.Path | None = None,
                     verbose: bool = True) -> tuple[pd.DataFrame, pd.Series | None, dict]:
    """Load Nifty OHLC and India VIX, trying CSV then yfinance then Stooq.

    Returns ``(prices, vix, provenance)``. ``vix`` is None when no implied-vol
    series could be sourced -- the caller must handle that rather than get a
    silently empty column, because it decides whether the VRP strategy can run.
    """
    prov = {}

    prices = None
    if price_csv and pathlib.Path(price_csv).exists():
        prices = load_ohlc_csv(price_csv)
        prov["prices"] = f"csv:{price_csv}"
    if prices is None:
        prices = _from_yfinance(price_ticker, years)
        if prices is not None:
            prov["prices"] = f"yfinance:{price_ticker}"
    if prices is None:
        prices = _from_stooq(("^NSEI", "^nsei"), years)
        if prices is not None:
            prov["prices"] = "stooq:^NSEI"
    if prices is None:
        raise RuntimeError(
            "Could not load Nifty prices from CSV, yfinance or Stooq. On Kaggle: "
            "check Settings -> Internet is On, or attach a Nifty dataset and pass "
            "price_csv=<path>.")

    vix = None
    if vix_csv and pathlib.Path(vix_csv).exists():
        vix = load_vix_csv(vix_csv)
        prov["vix"] = f"csv:{vix_csv}"
    if vix is None:
        v = _from_yfinance(vix_ticker, years)
        if v is not None:
            vix = v["close"].rename("vix")
            prov["vix"] = f"yfinance:{vix_ticker}"
    if vix is None:
        prov["vix"] = "UNAVAILABLE"

    if verbose:
        print(f"prices <- {prov['prices']}: {len(prices)} sessions  "
              f"{prices.index.min().date()} -> {prices.index.max().date()}")
        if vix is None:
            print("vix    <- UNAVAILABLE. The VRP strategy cannot run without an "
                  "implied-vol series; forecasting and the directional book still can.")
        else:
            print(f"vix    <- {prov['vix']}: {len(vix)} sessions  mean {vix.mean():.1f}")

    return prices, vix, prov


# Backwards-compatible thin wrappers.
def load_prices(ticker: str = "^NSEI", years: int = 8) -> pd.DataFrame:
    df = _from_yfinance(ticker, years)
    if df is None:
        raise RuntimeError(f"yfinance returned nothing for {ticker}")
    return df


def load_india_vix(years: int = 8) -> pd.Series:
    df = _from_yfinance("^INDIAVIX", years)
    if df is None:
        raise RuntimeError("yfinance returned nothing for ^INDIAVIX")
    return df["close"].rename("vix")


def simulate_market(n_days: int = 2200, seed: int = 7,
                    gap_share: float = 0.35,
                    vrp: float = 0.15,
                    drift_annual: float = 0.10,
                    jump_prob: float = 0.005,
                    jump_size: float = 1.0,
                    intraday_steps: int = 200,
                    start: str = "2016-01-04") -> tuple[pd.DataFrame, pd.Series]:
    """GJR-GARCH-like synthetic index with OHLC and a matching implied vol.

    Three properties matter, because the tests and the demo depend on them:

    * The close-to-close return is ``gap + intraday``, with the legs drawn
      independently so ``var(gap) = gap_share * var(total)`` holds exactly.
    * High and low come from a simulated intraday path, not a made-up range,
      so Garman-Klass is an unbiased estimator of the intraday leg. Otherwise
      the tests would be checking the simulator's arithmetic.
    * **Implied vol is causal.** It is built from an EWMA of past returns --
      what a market maker could actually know at ``t`` -- marked up by a
      persistent, time-varying premium that sometimes goes negative. An IV
      built from the *realized* forward vol would hand the VRP strategy a
      risk-free arbitrage and print a meaningless Sharpe.

    Parameters
    ----------
    gap_share
        Fraction of total daily variance arriving overnight. ~0.35 is in the
        right range for the Nifty and is exactly the quantity that makes a
        Garman-Klass target the wrong denominator for position sizing.
    vrp
        Mean level of the variance risk premium: implied vol averages
        ``(1 + vrp)`` times the market maker's own vol estimate.
    jump_prob, jump_size
        Poisson variance jumps. A vol process without jumps has no left tail,
        which would delete precisely the risk that defines short-volatility
        trading and make the VRP backtest print a fantasy Sharpe. These are
        what stop the premium from looking free.
    """
    rng = np.random.default_rng(seed)

    omega, alpha, gamma, beta = 3.0e-6, 0.05, 0.08, 0.88
    mu = drift_annual / TRADING_DAYS
    var = np.empty(n_days)
    ret = np.empty(n_days)
    gap = np.empty(n_days)
    intra = np.empty(n_days)
    var[0] = omega / (1 - alpha - gamma / 2 - beta)

    t_scale = np.sqrt(6 / 4)  # unit-variance Student-t(6)
    for t in range(n_days):
        if t > 0:
            shock = ret[t - 1] - mu
            var[t] = (omega + alpha * shock**2
                      + gamma * shock**2 * (shock < 0) + beta * var[t - 1])
            if rng.random() < jump_prob:
                var[t] *= 1.0 + rng.exponential(jump_size)
        sd = np.sqrt(var[t])
        # the drift is carried in the overnight leg, as it is in practice
        gap[t] = mu + sd * np.sqrt(gap_share) * rng.standard_normal()
        intra[t] = sd * np.sqrt(1 - gap_share) * rng.standard_t(df=6) / t_scale
        ret[t] = gap[t] + intra[t]

    sigma = np.sqrt(var)
    intra_sd = sigma * np.sqrt(1 - gap_share)

    close = 10000 * np.exp(np.cumsum(ret))
    prev_close = np.concatenate([[10000.0], close[:-1]])
    open_ = prev_close * np.exp(gap)

    # Intraday path as a Brownian bridge pinned to the realized open->close
    # move, so H/L are consistent with the intraday variance by construction.
    m = intraday_steps
    steps = rng.standard_normal((n_days, m)) * (intra_sd[:, None] / np.sqrt(m))
    walk = np.cumsum(steps, axis=1)
    tgrid = np.arange(1, m + 1) / m
    bridge = walk - tgrid * walk[:, -1][:, None] + tgrid * intra[:, None]
    bridge = np.concatenate([np.zeros((n_days, 1)), bridge], axis=1)

    high = open_ * np.exp(bridge.max(axis=1))
    low = open_ * np.exp(bridge.min(axis=1))

    idx = pd.bdate_range(start=start, periods=n_days, name="date")
    prices = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close,
         "volume": rng.integers(1e5, 5e5, n_days)}, index=idx)

    # --- causal implied vol -------------------------------------------------
    # A market maker's own vol estimate: EWMA of squared returns up to t.
    lam = 0.94
    ewma = np.empty(n_days)
    ewma[0] = var[0]
    for t in range(1, n_days):
        ewma[t] = lam * ewma[t - 1] + (1 - lam) * (ret[t - 1] - mu) ** 2

    # Persistent, mean-reverting premium that dips negative after vol shocks.
    prem = np.empty(n_days)
    prem[0] = vrp
    for t in range(1, n_days):
        prem[t] = 0.97 * prem[t - 1] + 0.03 * vrp + rng.standard_normal() * 0.035
    prem = np.clip(prem, -0.25, 0.70)

    # Idiosyncratic, persistent quoting noise. Real implied vol is not a clean
    # function of trailing realized vol -- log-IV regressed on log trailing RV
    # leaves ~25-30% of the variance unexplained. Without that residual the
    # model can invert the premium exactly and the VRP backtest becomes an
    # arbitrage rather than a risk premium.
    iv_noise = np.empty(n_days)
    iv_noise[0] = 0.0
    for t_ in range(1, n_days):
        iv_noise[t_] = 0.85 * iv_noise[t_ - 1] + rng.standard_normal() * 0.06
    iv_ann = np.sqrt(ewma * TRADING_DAYS) * (1 + prem) * np.exp(iv_noise)
    vix = pd.Series(iv_ann * 100, index=idx, name="vix")
    return prices, vix


def simulate_news(index: pd.DatetimeIndex, prices: pd.DataFrame,
                  seed: int = 11, signal_strength: float = 0.35) -> pd.DataFrame:
    """Synthetic FinBERT-scored headlines with a weak genuine vol linkage.

    Article volume and sentiment intensity are tied to the *next* day's
    volatility with ``signal_strength``, so a working pipeline should be able
    to extract something. Set ``signal_strength=0`` to confirm the model
    correctly finds nothing.
    """
    rng = np.random.default_rng(seed)
    rv = realized_vol(prices, "total").reindex(index)
    z = ((np.log(rv + 1e-8) - np.log(rv + 1e-8).mean())
         / np.log(rv + 1e-8).std()).fillna(0.0)
    z_fwd = z.shift(-1).fillna(0.0)

    rows = []
    for day in index:
        drive = signal_strength * z_fwd.loc[day] + rng.standard_normal() * 0.5
        n = max(1, int(np.exp(3.0 + 0.35 * drive + rng.standard_normal() * 0.25)))
        intensity = np.clip(0.35 + 0.15 * drive, 0.05, 0.95)
        pol = np.clip(rng.standard_normal(n) * intensity, -1, 1)
        pos = np.clip(0.5 + pol / 2, 0, 1)
        rows.append(pd.DataFrame({
            "trading_day": day,
            "polarity": pol,
            "positive": pos,
            "negative": 1 - pos,
        }))
    return pd.concat(rows, ignore_index=True)
