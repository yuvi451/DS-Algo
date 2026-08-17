"""TreeSHAP explainability for the LightGBM volatility model.

Fast and near-free for gradient boosting (unlike SHAP on deep nets). Shows
which features -- which sentiment lag, which price lag -- actually drive
predictions, useful both for the writeup and for sanity-checking that the
model isn't just learning volatility persistence and ignoring sentiment
entirely.
"""

import numpy as np
import pandas as pd
import shap


def compute_shap_values(model, X: pd.DataFrame):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X)
    return shap_values


def shap_feature_importance(shap_values, feature_names: list[str]) -> pd.DataFrame:
    mean_abs = np.abs(shap_values.values).mean(axis=0)
    return (pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs})
            .sort_values("mean_abs_shap", ascending=False)
            .reset_index(drop=True))


def sentiment_vs_price_contribution(importance_df: pd.DataFrame) -> dict:
    """Split total |SHAP| mass between sentiment-derived and price-derived
    features, to sanity-check the model isn't ignoring sentiment."""
    sentiment_mask = importance_df["feature"].str.startswith(
        ("sent_", "article_count", "pct_positive", "pct_negative", "has_news"))
    total = importance_df["mean_abs_shap"].sum()
    sentiment_share = importance_df.loc[sentiment_mask, "mean_abs_shap"].sum()
    return {
        "sentiment_share_pct": 100 * sentiment_share / total if total else 0.0,
        "price_share_pct": 100 * (total - sentiment_share) / total if total else 0.0,
    }
