"""SHAP attribution, and a fairer test of whether sentiment contributes.

v1 reported "sentiment contributes 0.0% of total feature importance" and left
it there. Two things are wrong with stopping at that number.

First, |SHAP| share is a statement about *this fitted model*, not about the
data. When sentiment features are collinear with price features and arrive
second in the tree-building order, LightGBM will simply never split on them and
their SHAP mass is zero by construction. That is a fact about greedy splitting,
not evidence that news carries no information.

Second, the decision-useful question is not "what share of importance" but
"does out-of-sample error get worse if I remove these features". That is a
one-line experiment and it is the one that settles the argument.
``incremental_value`` runs it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SENTIMENT_PREFIXES = ("sent_", "news_vol", "article_count", "pct_", "has_news")
VIX_PREFIXES = ("log_iv", "log_vrp", "vix_")


def compute_shap(model, X: pd.DataFrame):
    import shap
    return shap.TreeExplainer(model)(X)


def importance(shap_values, feature_names: list[str]) -> pd.DataFrame:
    mean_abs = np.abs(shap_values.values).mean(axis=0)
    return (pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs})
            .sort_values("mean_abs_shap", ascending=False)
            .reset_index(drop=True))


def _group(name: str) -> str:
    if name.startswith(SENTIMENT_PREFIXES):
        return "sentiment"
    if name.startswith(VIX_PREFIXES):
        return "implied_vol"
    return "price"


def group_shares(importance_df: pd.DataFrame) -> pd.Series:
    g = importance_df.assign(group=importance_df["feature"].map(_group))
    total = g["mean_abs_shap"].sum()
    if total == 0:
        return pd.Series(dtype=float)
    return (100 * g.groupby("group")["mean_abs_shap"].sum() / total
            ).sort_values(ascending=False)


def incremental_value(table: pd.DataFrame, base_cols: list[str],
                      extra_cols: list[str], target_col: str = "target_log_rv_h1",
                      **wf_kwargs) -> dict:
    """Does adding ``extra_cols`` reduce walk-forward RMSE? With a p-value.

    This is the honest replacement for "sentiment contributes 0.0% of SHAP".
    Runs the same walk-forward twice -- once without the extra block, once with
    it -- and Diebold-Mariano tests the difference in squared error. If the
    p-value is not small, the extra features do not help, and that is a real
    finding worth reporting rather than something to hide.
    """
    import validation

    wf_kwargs.setdefault("verbose", False)
    base = validation.stack_predictions(
        validation.run_walk_forward(table, base_cols, target_col, **wf_kwargs))
    full = validation.stack_predictions(
        validation.run_walk_forward(table, base_cols + extra_cols, target_col,
                                    **wf_kwargs))

    joined = pd.DataFrame({
        "y_true": base["y_true"],
        "base": base["model"],
        "full": full["model"].reindex(base.index),
    }).dropna()

    rmse_base = float(np.sqrt(((joined["base"] - joined["y_true"]) ** 2).mean()))
    rmse_full = float(np.sqrt(((joined["full"] - joined["y_true"]) ** 2).mean()))
    dm = validation.diebold_mariano(joined, "full", "base")

    return {
        "rmse_without": rmse_base,
        "rmse_with": rmse_full,
        "improvement_pct": 100 * (rmse_base - rmse_full) / rmse_base,
        "dm_statistic": dm["statistic"],
        "p_value": dm["p_value"],
        "n": dm["n"],
        "verdict": ("adds real information" if dm["statistic"] < 0 and dm["p_value"] < 0.05
                    else "no significant contribution"),
    }
