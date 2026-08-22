# Critical analysis of the v1 Nifty volatility strategy

Reported result under review:

```
Walk-forward folds: 24
RMSE (log-vol)  model=0.4103  naive=0.4825  garch=0.5928
MAE  (log-vol)  model=0.3283  naive=0.3817  garch=0.4877
Model vs naive:  +15.0% RMSE
Model vs GARCH:  +30.8% RMSE
Backtest Sharpe   strategy=0.37  buy&hold=0.60
Max drawdown      strategy=-28.5%  buy&hold=-16.1%
Total return      strategy=24.7%  buy&hold=31.1%
SHAP: sentiment contributes 0.0% of total feature importance
```

**Verdict.** The forecasting half is sound in structure and the walk-forward is
honestly constructed — that part of the project does what it claims. The
backtest is broken by two unit bugs and one cost bug, which together explain
essentially the entire shortfall. But fixing them will *not* make the strategy
profitable, because the strategy is the wrong shape: a long-only index position
sized by a volatility forecast has no expected-return edge no matter how good
the forecast is. The forecast has to be pointed at something that pays for
volatility. Section 5 does that.

---

## 1. The backtest lost for three attributable reasons

### 1.1 Unit mismatch: the target is intraday vol, the traded return is not

`garman_klass_volatility` estimates variance from one session's own O/H/L/C. It
measures **open-to-close** variation and is structurally blind to the overnight
gap. But the backtest holds positions overnight and earns
`log_return = log(C_t / C_{t-1})`, whose variance includes that gap.

For the Nifty the overnight gap is roughly a third of total daily variance, so

```
sigma_GK / sigma_total  ~  sqrt(0.65)  =  0.81
```

Position sizing divides by the forecast:

```python
raw = target_daily_vol / predicted_vol      # src/backtest.py in v1
```

so a denominator that is 19% too small makes every position ~1.24x too large.
This is not a modelling judgement call; it is a units error.

### 1.2 The log-space forecast was never converted back correctly

The model is trained on `target_next_log_gk_vol` and the backtest does:

```python
predicted_vol = np.exp(all_preds_sorted["y_pred_model_log"])
```

`exp(E[log v])` is the **median** of `v`, not the mean. For a right-skewed
target the level is understated by roughly `exp(sigma_resid^2 / 2)`. With the
reported residual spread of 0.4103:

```
exp(0.4103^2 / 2) = 1.088
```

Another 8.8% too small in the denominator, so another 1.09x on every position.

### 1.3 The two compound, and the compounded figure is observable

```
1.24 x 1.09 = 1.35x expected average leverage
```

Backing the actual leverage out of the reported numbers, independently:

| | value |
|---|---|
| backtest span (24 folds x 2 months) | ~4.0 years |
| buy & hold CAGR | 7.00% |
| strategy CAGR | 5.67% |
| implied buy & hold ann. vol (CAGR / Sharpe) | 11.7% |
| implied strategy ann. vol | 15.3% |
| **implied average leverage** | **1.31x** |

Predicted 1.35x from the two unit bugs, observed 1.31x. The strategy was
running about a third more risk than intended, for reasons that are entirely
arithmetic.

### 1.4 Turnover ate the rest

At 1.31x average exposure, a return-neutral leverage effect would have produced
`1.31 x 7.00% = 9.20%` CAGR. Actual was 5.67%. **3.53%/yr was destroyed.**

The strategy rebalances to a fresh target every single day off a *daily*
volatility forecast, which is an intrinsically noisy signal, and pays 7.5 bps on
every wiggle. To account for the full 3.53%/yr:

```
mean |delta position| = 0.0353 / (252 x 0.00075) = 0.187 per day
```

which is about 47x position turnover per year — entirely plausible for a
position that is a ratio with a noisy daily estimate in the denominator. Cost
drag is the single largest term, and it is larger than any realistic vol-timing
benefit.

### 1.5 Leverage was free, and still lost

`run_backtest` charges transaction costs but no financing on the borrowed
portion above 1.0x, and credits no cash yield on the un-invested portion below
it. At Indian rates (~6.5%) a persistently 1.3x-levered book should be paying
roughly 2%/yr. The strategy was handed free money and still underperformed.

### 1.6 Why the drawdown was disproportionately worse

Drawdown ratio 1.77x against a vol ratio of only 1.31x. If leverage were
uncorrelated with subsequent returns the two would be similar. They are not,
because of how the signal behaves: predicted volatility is dominated by recent
realized volatility, so the position is **largest after calm periods** — which
is exactly the state markets crash out of — and only de-levers *after* the vol
spike has already been realized. The overlay is structurally late. It levers
into the drawdown and de-levers into the recovery.

---

## 2. The forecasting margins are softer than they look

The walk-forward itself is correctly built — expanding window, no shuffle, no
lookahead in the features. Three problems are with what it is measured against.

**Naive persistence is a strawman.** `log(sigma_t)` from a single day's range is
a very noisy estimator of the current volatility level. Beating it by 15% is
close to free — a 5-day moving average of the same quantity captures most of
that margin with no model at all. The genuine bar for daily realized-volatility
forecasting is **HAR-RV** (Corsi 2009): OLS of tomorrow's log-RV on the daily,
weekly and monthly averages of log-RV. Three lines, no hyperparameters, and
hard to beat. If LightGBM + FinBERT cannot clear HAR, the headline does not
survive contact with anyone who has forecast volatility before.

**GARCH was scored in the wrong units.** `fit_garch_forecast` fits close-to-close
returns, so it forecasts *total* volatility, but it was scored against the
Garman-Klass *intraday* target. On a log scale that is a near-constant offset of
about `log(1/0.81) = +0.21`. A constant bias of 0.21 against an error of ~0.4
inflates RMSE substantially on its own. Most of the "+30.8% vs GARCH" is that
offset, not skill. A baseline should be given its best shot; this one was
handicapped by an accounting error.

**No significance test.** "+15.0%" over 24 folds of a noisy daily series has no
error bar attached. The fix is a Diebold-Mariano test on the squared-error
differential with Newey-West standard errors, which turns the claim into one
with a p-value.

---

## 3. Why sentiment came out at exactly 0.0%

Four separate reasons, all fixable, and one of them is not about sentiment at
all.

**The feature answers the wrong question.** v1 feeds the model `sent_mean`, a
*signed* average polarity, and asks it to predict a *magnitude*. Good news and
bad news both raise volatility. The sign is close to irrelevant to the target,
and averaging polarity over ~50 headlines drives the daily value toward zero
with very little variance left. What actually tracks volatility is intensity
(`mean |polarity|`), disagreement (`std(polarity)`), the share of unambiguously
charged headlines, and news *volume*.

**Article count is non-stationary.** Raw counts drift with outlet coverage and
with GDELT's own indexing behaviour over the years. A tree that learns
"count > 80 implies high vol" in an early fold is learning a date proxy, and it
will not transfer. The stationary version is a z-score against a trailing
60-day baseline — a news-volume *shock*.

**"No news" was encoded as "neutral news."** In `build_feature_table`, missing
sentiment days are filled with `0.0` — numerically identical to a day of
perfectly balanced coverage. Those are different states and the fill destroys
the distinction. LightGBM routes NaN natively; leaving the gaps as NaN is both
simpler and correct.

**India VIX is missing entirely, and it dominates.** This is the biggest single
miss in the whole project. India VIX is a forward-looking, market-consensus
volatility forecast published daily and freely available (`^INDIAVIX` on
yfinance). It is the strongest known predictor of near-term realized volatility
and it already impounds whatever the news flow contains, faster and more
accurately than a FinBERT average over headlines. A volatility model that omits
implied volatility is competing with one hand tied — and it makes the sentiment
question harder to answer honestly, because sentiment is being asked to add
information on top of a feature set that is missing the obvious one.

**Finally, "0.0% of SHAP" is the wrong measurement.** SHAP share describes *this
fitted model*, not the data. When sentiment features are noisy and partially
collinear with price features, greedy tree splitting will simply never select
them and their SHAP mass is zero by construction. That is a fact about LightGBM,
not evidence about news. The decision-useful question is: *does out-of-sample
error get worse when I remove them?* That is a two-line ablation with a
Diebold-Mariano test attached (`src/explain.py: incremental_value`). It may well
still come back "no significant contribution" — that is a perfectly respectable
finding, and stating it with a p-value is stronger than reporting a SHAP share
that cannot support the interpretation being put on it.

---

## 4. The structural problem: this is not an alpha strategy

Even with every bug above repaired, the vol-targeting overlay will not
meaningfully beat buy-and-hold, and it is worth being clear about why rather
than tuning parameters in the hope that it will.

For a constant leverage `L`, returns are `L*r`: mean scales by `L`, standard
deviation scales by `L`, and **Sharpe is unchanged**. Leverage cannot create
risk-adjusted return. With *time-varying* leverage the only thing that moves
Sharpe is the covariance between the position and subsequent returns —

```
the entire edge  =  Cov( 1 / sigma_hat_t ,  r_{t+1} )
```

— and the model is not forecasting `r_{t+1}` at all. It is forecasting
`sigma_{t+1}`. The published literature on equity vol-targeting finds a Sharpe
improvement in the 0.1–0.2 range, arriving mostly as tail and drawdown
reduction rather than return, and it largely disappears at daily rebalancing
frequency once realistic costs are applied. That is the ceiling here, and v1's
cost drag alone (3.5%/yr) exceeds it several times over.

So: keep the overlay, but demote the claim. It is a **risk overlay**, and its
honest selling point is the drawdown, not the return.

---

## 5. Where a volatility forecast actually pays: the variance risk premium

A volatility forecast is worth money when you can trade *against a price for
volatility*. That price exists and is published daily: **India VIX**.

Implied volatility trades systematically above subsequently realized
volatility — the variance risk premium — because option sellers demand
compensation for taking gap and crash risk. Selling variance harvests it. The
premium alone is not an edge, though: it is freely available to anyone willing
to be short volatility, and it is paid for in the tail.

**The model's job is to time it.** The forecast gives a conditional estimate of
what realized volatility will actually be, so the signal is

```
signal_t = log(IV_t) - log(E[RV_{t+1..t+h}])
```

Size up when the premium is unusually rich relative to the forecast, stand aside
when it is thin, and take the other side when it is negative. That converts the
volatility model from a position-sizing input — where section 4 shows its skill
is nearly worthless — into a **pricing** input, where its skill is the entire
trade. Every improvement in forecast RMSE now maps directly onto P&L.

Implementation is in `src/backtest.py: vrp_backtest`, with three things the
naive version of this trade gets wrong:

- **Settlement on arithmetic realized variance**, not the geometric mean of
  daily vols. A variance swap pays on `mean(sigma^2)`; using `exp(mean(log
  sigma))^2` understates realized variance by Jensen, and it does so worst on
  exactly the spiky periods that hurt a short-vol book. This flatters the
  strategy precisely where it should be punished.
- **A capped payoff.** Naked short variance has unbounded downside and any
  backtest of it is fiction. `cap_multiple` bounds the loss at
  `cap_multiple x strike`, which is what buying wings (a strangle overlay rather
  than a naked straddle) actually buys you. The cost of those wings is real and
  is what the cap is standing in for.
- **Weekly holding, not daily rebalancing.** Nifty options expire weekly. The
  bid-ask is paid once per position, not 252 times a year.

### What must be measured before believing any of it

The benchmark for the model is **not** buy-and-hold. It is:

1. **always short variance** — harvest the premium with no timing at all; and
2. **short variance sized off trailing realized vol** — timing with no model.

The model has to beat both, or the honest conclusion is that the premium is
real and the ML is decoration. `run_pipeline.py` prints all three rows
side by side for exactly this reason.

### Risk warnings that belong in the writeup

Short variance is a negatively-skewed carry trade: many small gains, rare very
large losses. A Sharpe ratio computed over a period without a volatility crisis
is close to meaningless for this strategy, and the 2020 drawdown is the single
most informative part of any Nifty backtest that spans it. Report skew, worst
day, and the drawdown through the crisis alongside the Sharpe, and size the
position off the capped worst case rather than off volatility.

---

## 5b. Adding shorting

Shorting was requested, so it is in. Two things have to be said plainly about
it.

**Shorting is off by default.** `ALLOW_SHORT = False`; the IC test below is the
gate that decides whether to turn it on. The code is kept rather than deleted
because whether it earns its place depends on data this analysis has not been
run against, and deleting it would remove the ability to check. One flag is not
complexity.

**A volatility model cannot tell you which way to bet.** It forecasts `|r|`;
the sign is precisely the information it discards. "Add shorting" is therefore
really "add a return forecast", and that is a much harder problem. Realized
volatility is strongly autocorrelated and genuinely forecastable; daily index
returns are close to a martingale. `src/signals.py` adds three cheap, causal
directional signals — time-series momentum, the variance risk premium as a
risk-appetite proxy, and signed news polarity (which is finally being asked the
question its sign is about). Their documented out-of-sample information
coefficients sit in the 0.02–0.05 range at daily horizon. Small, not zero, and
that is the honest ceiling.

**So check the IC before looking at the equity curve.**
`signals.information_coefficient` reports rank correlation against next-day
returns with a Newey-West t-stat. If the blend's t-stat is below 2, the
long/short backtest is a draw from noise regardless of how good its Sharpe
looks. On the synthetic market — which has no directional predictability built
into it — the report correctly returns "NOT distinguishable from noise" for
every component, which is the behaviour you want from the check.

Three implementation details that are easy to get wrong:

- **You cannot short the cash index in India; shorting means futures**, and the
  carry arithmetic differs. `futures_carry` uses
  `position * q / 252 + (1 - position) * r / 252`, which reads correctly in all
  three cases: long earns the dividend yield on top of the price return
  (reconstructing total return, since `^NSEI` is a price index), flat earns the
  risk-free rate, and short pays the dividend away while collecting `r` on both
  its own capital and the short proceeds. The short side is a structural
  headwind — it must overcome roughly `q + drift` before breaking even.
- **A short book needs a stop.** Losses on a short are unbounded and margin
  calls arrive at the worst moment. `stop_drawdown` flattens the book at a
  configurable drawdown from the high water mark and only re-enters when the
  signal flips to the other side. It is walked forward one day at a time,
  because the stop depends on the equity curve the stop itself produces.
- **Report Sharpe in excess of the risk-free rate.** A long/short book sits in
  cash a large fraction of the time. Without subtracting `r`, a strategy that is
  90% T-bills posts a spectacular ratio on money-market returns. The same
  applies to Sortino, which must use the same excess series — reporting an
  excess-return Sharpe next to a raw-return Sortino produces contradictory signs
  on one return stream.

The division of labour is worth stating, because it is the only arrangement in
which the volatility forecast contributes to *return* rather than only to risk:
the directional signal picks the side, and the volatility model decides how much
that side is worth, so each unit of conviction carries constant risk. That is an
indirect contribution, and it is still bounded by how good the direction signal
is.

---

## 6. What changed

| File | Purpose |
|---|---|
| `src/volatility.py` | Gap-inclusive `total_daily_variance`; Duan smearing correction. Fixes 1.1 and 1.2. |
| `src/features.py` | India VIX block; intensity/dispersion/volume-shock sentiment features; NaN preserved for no-news days; multi-horizon targets, both log-vol and arithmetic variance. Fixes section 3. |
| `src/baselines.py` | HAR-RV; GARCH in matched units with a training-set bias offset. Fixes section 2. |
| `src/model.py` | Carries the early-stopped tree count into the refit — v1 tuned with early stopping and then refit with the raw suggested `n_estimators`, so the tuned config and the deployed model were different models. |
| `src/validation.py` | Diebold-Mariano with Newey-West SEs; purging of overlapping multi-day targets at the train/test boundary; per-fold smearing from validation residuals. |
| `src/backtest.py` | Corrected units, financing charged, no-trade band with partial adjustment, vol-matched comparison; and `vrp_backtest`, the strategy from section 5. |
| `src/signals.py` | Directional signals (momentum, VRP, sentiment polarity) and an information-coefficient test. Prerequisite for shorting -- see section 5b. |
| `src/explain.py` | `incremental_value` — ablation with a p-value, replacing the SHAP-share argument. |
| `src/data.py` | Multi-source loaders (mounted CSV -> yfinance -> Stooq, since Yahoo rate-limits datacenter IPs), plus a synthetic market for offline testing. |
| `tests/test_pipeline.py` | 35 tests. Several pin the v1 bugs directly. |

### Expected effect of each fix on the backtest

| Fix | Effect |
|---|---|
| Gap-inclusive vol units | average leverage 1.31x -> ~1.0x |
| Smearing correction | removes a further ~9% systematic over-sizing |
| No-trade band (partial adjustment to band edge) | turnover down ~55-75%; cost drag ~3.5%/yr -> ~0.9%/yr |
| Financing charged | strategy stops being flattered by free leverage |
| HAR-RV baseline + DM test | headline margin drops from +15% to something defensible |
| India VIX features | the largest expected RMSE improvement of anything here |
| VRP strategy | the only component with an actual expected-return edge |
| Long/short direction | bounded by an IC of ~0.02-0.05; check the t-stat before believing the curve |

---

## 7. Limitations of this analysis, stated plainly

**Nothing here has been re-run on real market data.** The environment this was
written in blocks Yahoo Finance at the network policy level, so `^NSEI` and
`^INDIAVIX` are unreachable. Consequently:

- Section 1 is arithmetic on the reported numbers, and the 1.35x-predicted vs
  1.31x-observed agreement is genuine evidence. That part stands on its own.
- The code is verified by a 35-test suite and an end-to-end run against a
  synthetic market (`run_pipeline.py --synthetic`), which confirms the pipeline
  is correct and reproduces the v1 over-leverage mechanism (1.39x average
  position, 3.65%/yr cost drag against v2's 0.89x and 0.87%/yr).
- **The synthetic VRP Sharpe is meaningless and is labelled as such in the
  output.** The simulator's variance premium is a persistent AR(1) process that
  any signal can read off, so it prints an implausible Sharpe above 10. It
  demonstrates that the payoff arithmetic and plumbing are right, nothing more.
  Run against real India VIX before quoting a number; expect something in the
  0.8–1.3 range with a deep left tail, and expect it to be sensitive to whether
  the sample includes March 2020.
- The 65% intraday-variance share used in section 1.1 is a reasonable figure for
  the Nifty but was not measured here. Measure it on your own data — it is one
  line, and `tests/test_pipeline.py::test_gk_understates_total_vol` shows how.

**Sentiment may still turn out to be worthless.** Nothing in this rewrite
guarantees that news adds information once India VIX is in the feature set —
and in fact VIX is the most likely reason it will not. The ablation in
`src/explain.py` is built to give that answer credibly either way. A clean
negative result, properly tested, is a better project outcome than a positive
one that rests on a SHAP share.
