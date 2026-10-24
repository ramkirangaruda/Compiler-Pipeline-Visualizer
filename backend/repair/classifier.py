"""Inference wrapper around the trained scikit-learn pipeline, including a
model-agnostic local explanation (feature occlusion)."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from .features import FEATURE_COLUMNS

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "error_classifier.joblib"


class Classifier:
    def __init__(self, path: Path = MODEL_PATH, columns: list | None = None):
        self.columns = list(columns) if columns else FEATURE_COLUMNS
        art = joblib.load(path)
        self.pipeline = art["pipeline"]
        self.classes: list[str] = list(self.pipeline.classes_)
        self.neutral: dict = art["neutral"]
        self.model_name: str = art["model_name"]
        self.trained_at: str = art.get("trained_at", "")

    def _frame(self, rows: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(rows, columns=self.columns)

    def predict_proba(self, feats: dict) -> dict[str, float]:
        p = self.pipeline.predict_proba(self._frame([feats]))[0]
        return {c: float(x) for c, x in zip(self.classes, p)}

    def explain(self, feats: dict, label: str, k: int = 6) -> list[dict]:
        """How much does each raw feature support `label`? Replace one feature at
        a time by its training-set mode and measure the drop in probability."""
        rows = [dict(feats)]
        for col in self.columns:
            r = dict(feats)
            r[col] = self.neutral[col]
            rows.append(r)
        probs = self.pipeline.predict_proba(self._frame(rows))
        li = self.classes.index(label)
        base = probs[0][li]
        contrib = []
        for i, col in enumerate(self.columns, start=1):
            delta = float(base - probs[i][li])
            if abs(delta) > 1e-4 and feats[col] != self.neutral[col]:
                contrib.append({"feature": col, "value": feats[col], "contribution": round(delta, 4)})
        contrib.sort(key=lambda c: -abs(c["contribution"]))
        return contrib[:k]
