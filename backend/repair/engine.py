"""The diagnosis engine: compiler failure -> features -> ML cause ranking ->
candidate repairs -> compiler validation -> ranked, verified fixes."""
from __future__ import annotations

import difflib
from typing import Optional

from minic.pipeline import Frontend, run_frontend
from minic.tokens import Diagnostic

from . import baseline
from .candidates import generate, gen_rules
from .classifier import MODEL_PATH, Classifier
from .features import extract
from .labels import CANDIDATE_CAUSES, LABELS, ML_CODES
from .validator import validate

STATUS_RANK = {"verified": 2, "partial": 1, "rejected": 0}


def offset_to_pos(source: str, off: int) -> dict:
    off = max(0, min(off, len(source)))
    line = source.count("\n", 0, off) + 1
    col = off - (source.rfind("\n", 0, off) + 1) + 1
    return {"line": line, "col": col, "offset": off}


def diff_hunks(old: str, new: str) -> list[dict]:
    a, b = old.splitlines(), new.splitlines()
    hunks = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag != "equal":
            hunks.append({"tag": tag, "old_start": i1 + 1, "old": a[i1:i2], "new_start": j1 + 1, "new": b[j1:j2]})
    return hunks


class Engine:
    def __init__(self, classifier: Optional[Classifier] = None, load: bool = True):
        self.clf = classifier
        if self.clf is None and load and MODEL_PATH.exists():
            self.clf = Classifier()

    @property
    def model_loaded(self) -> bool:
        return self.clf is not None

    @staticmethod
    def _constrain(probs: dict[str, float], code: str) -> dict[str, float]:
        """Keep only the causes the compiler's own error code leaves possible, renormalised."""
        allowed = CANDIDATE_CAUSES.get(code)
        if not allowed:
            return probs
        kept = {l: p for l, p in probs.items() if l in allowed}
        total = sum(kept.values())
        if total < 1e-9:
            return {l: 1.0 / len(allowed) for l in allowed}
        return {l: p / total for l, p in kept.items()}

    # ----------------------------------------------------------- one diag
    def diagnose_one(self, d: Diagnostic, fe: Frontend, mode: str = "ml") -> dict:
        source = fe.source
        entry: dict = {"diagnostic": d.to_dict(), "duplicates": 0}

        if d.code not in ML_CODES:
            entry["handled_by"] = "rules"
            raw = gen_rules(d, fe)
            entry["prediction"] = None
            probs = None
        else:
            feats = extract(d, fe)
            base_label = baseline.predict(feats)
            if mode == "baseline" or self.clf is None:
                probs = {base_label: 1.0}
                entry["handled_by"] = "baseline" if mode == "baseline" else "rules-fallback"
            else:
                probs = self._constrain(self.clf.predict_proba(feats), d.code)
                entry["handled_by"] = "ml"
            ranked = sorted(probs.items(), key=lambda kv: -kv[1])
            top_label, top_p = ranked[0]
            entry["features"] = feats
            entry["baseline"] = {"label": base_label, "title": LABELS[base_label]["title"], "agrees": base_label == top_label}
            entry["prediction"] = {
                "label": top_label,
                "title": LABELS[top_label]["title"],
                "explain": LABELS[top_label]["explain"],
                "family": LABELS[top_label]["family"],
                "confidence": round(top_p, 4),
                "low_confidence": top_p < 0.5,
                "probs": [{"label": l, "title": LABELS[l]["title"], "prob": round(p, 4)} for l, p in ranked[:6]],
            }
            if self.clf is not None and mode == "ml":
                entry["explanation"] = self.clf.explain(feats, top_label)
            raw = []
            for l, p in ranked[:3]:
                if p < 0.02 and raw:
                    break
                for c in generate(l, d, fe):
                    c["prob"] = p
                    raw.append(c)

        cands, seen = [], set()
        for c in raw:
            key = tuple((e.start, e.end, e.text) for e in c["edits"])
            if key in seen:
                continue
            seen.add(key)
            v = validate(source, c["edits"], fe, d)
            p = c.get("prob", 1.0)
            cands.append(
                {
                    "label": c["label"],
                    "label_title": LABELS.get(c["label"], {}).get("title", "Rule-based fix"),
                    "title": c["title"],
                    "description": c["description"],
                    "edits": [e.to_dict() for e in c["edits"]],
                    "prob": round(p, 4),
                    "local_score": c["local_score"],
                    "score": round(p * c["local_score"], 4),
                    "status": v["status"],
                    "reason": v["reason"],
                    "errors_after": v["errors_after"],
                    "new_source": v["new_source"],
                    "diff": diff_hunks(source, v["new_source"]),
                }
            )
        cands.sort(key=lambda c: (-STATUS_RANK[c["status"]], -c["score"]))
        for i, c in enumerate(cands):
            c["id"] = f"fix-{i + 1}"
        entry["candidates"] = cands[:10]
        best = next((c for c in cands if c["status"] != "rejected"), None)
        entry["best"] = best["id"] if best else None
        if best:
            entry["localized"] = offset_to_pos(source, min(e["start"] for e in best["edits"]))
        return entry

    # ---------------------------------------------------------- whole file
    def diagnose(self, source: str, mode: str = "ml", only_first: bool = False) -> dict:
        fe = run_frontend(source)
        errors = fe.errors
        entries, undeclared_seen = [], {}
        for d in errors:
            if d.code == "E_UNDECLARED":
                name = d.extra["name"]
                if name in undeclared_seen:
                    undeclared_seen[name]["duplicates"] += 1
                    continue
            entry = self.diagnose_one(d, fe, mode)
            if d.code == "E_UNDECLARED":
                undeclared_seen[d.extra["name"]] = entry
            entries.append(entry)
            if only_first:
                break
        return {
            "model_loaded": self.model_loaded,
            "mode": mode,
            "errors": len(errors),
            "entries": entries,
        }

    # ------------------------------------------------------------- autofix
    def autofix(self, source: str, max_steps: int = 12, mode: str = "ml") -> dict:
        steps, cur = [], source
        for i in range(max_steps):
            fe = run_frontend(cur)
            if not fe.errors:
                break
            res = self.diagnose(cur, mode=mode, only_first=True)
            if not res["entries"]:
                break
            e = res["entries"][0]
            best = next((c for c in e["candidates"] if c["id"] == e["best"]), None)
            if best is None:
                steps.append({"iteration": i + 1, "stuck": True, "message": e["diagnostic"]["message"], "line": e["diagnostic"]["line"]})
                break
            pred = e.get("prediction")
            steps.append(
                {
                    "iteration": i + 1,
                    "message": e["diagnostic"]["message"],
                    "line": e["diagnostic"]["line"],
                    "label": best["label"],
                    "label_title": best["label_title"],
                    "confidence": pred["confidence"] if pred else None,
                    "title": best["title"],
                    "status": best["status"],
                    "diff": best["diff"],
                }
            )
            cur = best["new_source"]
        final = run_frontend(cur)
        return {
            "ok": not final.errors,
            "steps": steps,
            "final_source": cur,
            "remaining": [d.message for d in final.errors],
        }
