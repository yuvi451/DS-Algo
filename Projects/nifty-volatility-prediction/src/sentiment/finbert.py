"""FinBERT sentiment scoring for news headlines.

Uses ProsusAI/finbert (pretrained, inference only) to score each headline's
positive/negative/neutral probabilities, then collapses that triple into a
single polarity score: P(positive) - P(negative). Runs fine in batches on a
free Colab/Kaggle T4 GPU, and falls back to CPU automatically if no GPU is
available.
"""

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.config import FINBERT_MODEL_NAME


class FinBertScorer:
    def __init__(self, model_name: str = FINBERT_MODEL_NAME, device: str | None = None, batch_size: int = 32):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()
        # ProsusAI/finbert label order: 0=positive, 1=negative, 2=neutral
        self.id2label = self.model.config.id2label

    @torch.no_grad()
    def score_batch(self, headlines: list[str]) -> np.ndarray:
        inputs = self.tokenizer(headlines, padding=True, truncation=True, max_length=64,
                                 return_tensors="pt").to(self.device)
        logits = self.model(**inputs).logits
        probs = torch.softmax(logits, dim=-1).cpu().numpy()
        return probs

    def score_all(self, headlines: pd.Series) -> pd.DataFrame:
        headlines = headlines.fillna("").astype(str).tolist()
        label_order = [self.id2label[i].lower() for i in range(len(self.id2label))]
        pos_idx = label_order.index("positive")
        neg_idx = label_order.index("negative")

        all_probs = []
        for start in range(0, len(headlines), self.batch_size):
            batch = headlines[start:start + self.batch_size]
            if not batch:
                continue
            all_probs.append(self.score_batch(batch))
        probs = np.concatenate(all_probs, axis=0) if all_probs else np.zeros((0, len(label_order)))

        result = pd.DataFrame(probs, columns=label_order)
        result["polarity"] = result["positive"] - result["negative"]
        return result


def score_headlines(df: pd.DataFrame, scorer: FinBertScorer | None = None, batch_size: int = 32) -> pd.DataFrame:
    """Score a news DataFrame's `headline` column, returning the frame with
    `positive`, `negative`, `neutral`, `polarity` columns appended."""
    scorer = scorer or FinBertScorer(batch_size=batch_size)
    scores = scorer.score_all(df["headline"])
    out = df.reset_index(drop=True).copy()
    for col in ("positive", "negative", "neutral", "polarity"):
        out[col] = scores[col].values
    return out
