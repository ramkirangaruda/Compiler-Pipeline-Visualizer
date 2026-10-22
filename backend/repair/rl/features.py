"""Candidate features for the reinforcement-learning fix policy.

The RL agent's *action* is "apply candidate i". Each candidate is described by a
fixed-length numeric vector (what kind of fix it is, how the compiler judged it,
how big the edit is, where the heuristic ranked it), so a single weight vector
can score any candidate set - the standard way to handle a variable action space.
"""
from __future__ import annotations

import numpy as np

from ..labels import LABEL_NAMES

LABEL_SLOTS = LABEL_NAMES + ["RULE_BASED"]
STATUSES = ["verified", "partial", "rejected"]
# where/how a declaration-related fix puts the declaration (see repair/candidates.py)
STRATEGIES = ["default", "before_use", "top", "after_decls", "before_block",
              "split:before_block", "split:top", "split:after_decls",
              "whole:before_block", "whole:top", "whole:after_decls"]
PLACEMENT_LABELS = ["MISSING_DECLARATION", "USE_BEFORE_DECLARATION", "OUT_OF_SCOPE_USE"]
MAX_CANDS = 10

FEATURE_NAMES: list[str] = (
    [f"label={l}" for l in LABEL_SLOTS]
    + [f"status={s}" for s in STATUSES]
    + ["ml_prob", "plausibility", "heuristic_score", "errors_after", "errors_removed",
       "edit_size", "n_edits", "pure_insert", "pure_delete", "heuristic_rank", "is_heuristic_top",
       "stage_syntax", "errors_before", "n_candidates"]
    + [f"verified&label={l}" for l in LABEL_SLOTS]
    + [f"strategy={s}" for s in STRATEGIES]
    + [f"{l}&strategy={s}" for l in PLACEMENT_LABELS for s in STRATEGIES]
)
DIM = len(FEATURE_NAMES)
IDX = {n: i for i, n in enumerate(FEATURE_NAMES)}


def edit_stats(edits: list[dict]) -> tuple[int, bool, bool]:
    chars = sum(len(e["text"]) + (e["end"] - e["start"]) for e in edits)
    return chars, all(e["end"] == e["start"] for e in edits), all(e["text"] == "" for e in edits)


def candidate_matrix(cands: list[dict], n_errors_before: int, stage: str) -> np.ndarray:
    """One row per candidate. `cands` must be in heuristic order (best first)."""
    X = np.zeros((len(cands), DIM), dtype=np.float64)
    n = len(cands)
    for i, c in enumerate(cands):
        x = X[i]
        slot = c["label"] if c["label"] in LABEL_SLOTS else "RULE_BASED"
        x[IDX[f"label={slot}"]] = 1.0
        x[IDX[f"status={c['status']}"]] = 1.0
        if c["status"] == "verified":
            x[IDX[f"verified&label={slot}"]] = 1.0
        strategy = c.get("strategy", "default")
        if strategy not in STRATEGIES:
            strategy = "default"
        x[IDX[f"strategy={strategy}"]] = 1.0
        if slot in PLACEMENT_LABELS:
            x[IDX[f"{slot}&strategy={strategy}"]] = 1.0
        after = max(c.get("errors_after", 0), 0)
        chars, pure_ins, pure_del = edit_stats(c["edits"])
        x[IDX["ml_prob"]] = c.get("prob", 1.0)
        x[IDX["plausibility"]] = c["local_score"]
        x[IDX["heuristic_score"]] = c.get("score", 0.0)
        x[IDX["errors_after"]] = min(after, 5) / 5
        x[IDX["errors_removed"]] = max(-3, min(n_errors_before - after, 5)) / 5
        x[IDX["edit_size"]] = np.log1p(chars) / 5
        x[IDX["n_edits"]] = min(len(c["edits"]), 3) / 3
        x[IDX["pure_insert"]] = float(pure_ins)
        x[IDX["pure_delete"]] = float(pure_del)
        x[IDX["heuristic_rank"]] = i / MAX_CANDS
        x[IDX["is_heuristic_top"]] = float(i == 0)
        x[IDX["stage_syntax"]] = float(stage in ("syntax", "lexical"))
        x[IDX["errors_before"]] = min(n_errors_before, 5) / 5
        x[IDX["n_candidates"]] = n / MAX_CANDS
    return X
