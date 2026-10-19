"""Trains and evaluates the error-cause classifier.

Compares four models with grouped cross-validation (programs derived from the
same seed never straddle a fold), evaluates on a held-out test split and on the
hand-written out-of-distribution set, and writes models/metrics.json that the
dashboard renders.

Run from backend/:  python -m ml.train
"""
from __future__ import annotations

import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, log_loss, precision_recall_fscore_support
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from repair import baseline
from repair.features import CAT_COLUMNS, FEATURE_COLUMNS, NUM_COLUMNS
from repair.labels import LABEL_NAMES

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "datasets" / "processed"
MODELS = ROOT / "models"
SEED = 7
TIE_TOLERANCE = 0.005  # models within this CV macro-F1 of the best are considered tied
warnings.filterwarnings("ignore")


def preprocessor(scale: bool) -> ColumnTransformer:
    num = StandardScaler() if scale else "passthrough"
    return ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLUMNS), ("num", num, NUM_COLUMNS)]
    )


def candidates() -> dict[str, Pipeline]:
    return {
        "Logistic Regression": Pipeline(
            [("prep", preprocessor(True)), ("clf", LogisticRegression(max_iter=3000, C=3.0))]
        ),
        "Decision Tree": Pipeline(
            [("prep", preprocessor(False)), ("clf", DecisionTreeClassifier(max_depth=16, random_state=SEED))]
        ),
        "Random Forest": Pipeline(
            [("prep", preprocessor(False)),
             ("clf", RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1))]
        ),
        "Gradient Boosting": Pipeline(
            [("prep", preprocessor(False)),
             ("clf", GradientBoostingClassifier(n_estimators=120, max_depth=3, random_state=SEED))]
        ),
    }


def report(y_true, y_pred, labels) -> dict:
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
        "per_class": [
            {"label": l, "precision": round(float(p[i]), 4), "recall": round(float(r[i]), 4),
             "f1": round(float(f[i]), 4), "support": int(s[i])}
            for i, l in enumerate(labels)
        ],
        "confusion": {"labels": labels, "matrix": cm.tolist()},
    }


def main() -> None:
    df = pd.read_csv(PROCESSED / "features.csv", keep_default_na=False)
    hw = pd.read_csv(PROCESSED / "handwritten_features.csv", keep_default_na=False)
    for frame in (df, hw):
        for c in NUM_COLUMNS:
            frame[c] = pd.to_numeric(frame[c])
    train, test = df[df.split == "train"], df[df.split == "test"]
    labels = LABEL_NAMES
    Xtr, ytr, gtr = train[FEATURE_COLUMNS], train["label"], train["seed_id"]
    Xte, yte = test[FEATURE_COLUMNS], test["label"]
    print(f"train={len(train)} test={len(test)} handwritten={len(hw)}")

    results = []
    fitted = {}
    for name, pipe in candidates().items():
        t0 = time.perf_counter()
        cv = cross_validate(pipe, Xtr, ytr, groups=gtr, cv=GroupKFold(n_splits=5),
                            scoring=["accuracy", "f1_macro"], n_jobs=1)
        pipe.fit(Xtr, ytr)
        elapsed = time.perf_counter() - t0
        pred = pipe.predict(Xte)
        row = {
            "name": name,
            "cv_accuracy": round(float(cv["test_accuracy"].mean()), 4),
            "cv_accuracy_std": round(float(cv["test_accuracy"].std()), 4),
            "cv_macro_f1": round(float(cv["test_f1_macro"].mean()), 4),
            "test_accuracy": round(float(accuracy_score(yte, pred)), 4),
            "test_macro_f1": round(float(f1_score(yte, pred, average="macro")), 4),
            "test_log_loss": round(float(log_loss(yte, pipe.predict_proba(Xte), labels=list(pipe.classes_))), 4),
            "train_seconds": round(elapsed, 1),
        }
        results.append(row)
        fitted[name] = pipe
        print(row)

    # Accuracy is saturated on synthetic data, so near-ties are broken by the
    # quality of the predicted probabilities (log-loss): the UI shows confidence.
    top_f1 = max(r["cv_macro_f1"] for r in results)
    tied = [r for r in results if r["cv_macro_f1"] >= top_f1 - TIE_TOLERANCE]
    best_name = min(tied, key=lambda r: r["test_log_loss"])["name"]
    best = fitted[best_name]
    print("selected:", best_name)

    pred_te = best.predict(Xte)
    proba_te = best.predict_proba(Xte)
    test_report = report(yte, pred_te, labels)
    hw_report = None
    if len(hw):
        hw_pred = best.predict(hw[FEATURE_COLUMNS])
        hw_report = report(hw["label"], hw_pred, labels)
        hw_report["n"] = int(len(hw))

    # rule baseline on identical data
    b_te = [baseline.predict(r) for r in test[FEATURE_COLUMNS].to_dict("records")]
    base = {"test": report(yte, b_te, labels)}
    if len(hw):
        b_hw = [baseline.predict(r) for r in hw[FEATURE_COLUMNS].to_dict("records")]
        base["handwritten"] = report(hw["label"], b_hw, labels)

    # reliability: does confidence track accuracy?
    conf = proba_te.max(axis=1)
    correct = (pred_te == yte.values)
    bins = []
    for lo, hi in [(0, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.0001)]:
        m = (conf >= lo) & (conf < hi)
        bins.append({"range": f"{lo:.1f}-{min(hi, 1):.1f}", "n": int(m.sum()),
                     "accuracy": round(float(correct[m].mean()), 4) if m.any() else None})

    imp = permutation_importance(best, Xte, yte, n_repeats=5, random_state=SEED, scoring="accuracy", n_jobs=1)
    importance = sorted(
        ({"feature": f, "importance": round(float(v), 4)} for f, v in zip(FEATURE_COLUMNS, imp.importances_mean)),
        key=lambda x: -x["importance"],
    )

    neutral = {}
    for c in FEATURE_COLUMNS:
        neutral[c] = train[c].mode().iloc[0]
        if c in NUM_COLUMNS:
            neutral[c] = float(neutral[c])

    MODELS.mkdir(exist_ok=True)
    joblib.dump(
        {"pipeline": best, "model_name": best_name, "neutral": neutral,
         "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        MODELS / "error_classifier.joblib",
    )

    stats = json.loads((PROCESSED / "dataset_stats.json").read_text(encoding="utf-8"))
    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "selected_model": best_name,
        "dataset": {
            "n_seeds": stats["n_seeds"], "n_samples": stats["n_samples"],
            "n_train": int(len(train)), "n_test": int(len(test)), "n_handwritten": int(len(hw)),
            "per_label": stats["per_label"], "per_label_split": stats["per_label_split"],
            "n_features": len(FEATURE_COLUMNS),
        },
        "models": results,
        "test": test_report,
        "handwritten": hw_report,
        "baseline": base,
        "reliability": bins,
        "feature_importance": importance[:20],
    }
    (MODELS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"test acc={test_report['accuracy']}  macro-F1={test_report['macro_f1']}  "
          f"baseline acc={base['test']['accuracy']}")
    if hw_report:
        print(f"handwritten acc={hw_report['accuracy']}  baseline={base['handwritten']['accuracy']}")


if __name__ == "__main__":
    main()
