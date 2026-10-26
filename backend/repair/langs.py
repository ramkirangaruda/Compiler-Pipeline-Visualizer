"""Everything the repair engine needs to know about one source language, in one place.

MiniC is the teaching language the project was built around; C is the real thing (pycparser front end,
gcc as the correctness oracle). Both share the engine, the validator and the reinforcement-learning policy;
each has its own feature set, classifier, taxonomy and candidate generators."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Lang:
    key: str                      # "minic" | "c"
    title: str
    ext: str                      # file extension of dataset programs
    run_frontend: Callable
    extract: Callable
    generate: Callable
    gen_rules: Callable
    baseline_predict: Callable
    labels: dict
    label_names: list
    ml_codes: set
    candidate_causes: dict
    cat_columns: list
    num_columns: list
    model_path: Path
    metrics_path: Path
    eval_path: Path
    data_dir: Path
    extras: Optional[Callable] = None          # candidates that do not depend on our own front end (C: gcc fix-its + search)
    extra_labels: dict = field(default_factory=dict)

    @property
    def columns(self) -> list:
        return self.cat_columns + self.num_columns


_CACHE: dict[str, Lang] = {}


def get(key: str = "minic") -> Lang:
    key = "c" if key == "c" else "minic"
    if key in _CACHE:
        return _CACHE[key]
    if key == "c":
        from cfront.pipeline import run_frontend
        from . import baseline_c, candidates_c, candidates_gcc, features_c, labels_c
        lang = Lang("c", "C", ".c", run_frontend, features_c.extract, candidates_c.generate, candidates_c.gen_rules,
                    baseline_c.predict, labels_c.LABELS, labels_c.LABEL_NAMES, labels_c.ML_CODES, labels_c.CANDIDATE_CAUSES,
                    features_c.CAT_COLUMNS, features_c.NUM_COLUMNS, ROOT / "models" / "error_classifier_c.joblib",
                    ROOT / "models" / "metrics_c.json", ROOT / "models" / "repair_eval_c.json", ROOT / "datasets" / "c",
                    extras=candidates_gcc.extras, extra_labels=labels_c.EXTRA_LABELS)
    else:
        from minic.pipeline import run_frontend
        from . import baseline, candidates, features, labels
        lang = Lang("minic", "MiniC", ".mc", run_frontend, features.extract, candidates.generate, candidates.gen_rules,
                    baseline.predict, labels.LABELS, labels.LABEL_NAMES, labels.ML_CODES, labels.CANDIDATE_CAUSES,
                    features.CAT_COLUMNS, features.NUM_COLUMNS, ROOT / "models" / "error_classifier.joblib",
                    ROOT / "models" / "metrics.json", ROOT / "models" / "repair_eval.json", ROOT / "datasets")
    _CACHE[key] = lang
    return lang
