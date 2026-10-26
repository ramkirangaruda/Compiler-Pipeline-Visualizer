"""The diagnosis engine: compiler failure -> features -> ML cause ranking ->
candidate repairs -> compiler validation -> ranked, verified fixes."""
from __future__ import annotations

import difflib
import threading
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from minic.tokens import Diagnostic

from . import langs
from .classifier import MODEL_PATH, Classifier
from .rl.features import candidate_matrix
from .rl.policy import POLICY_PATH, Policy
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
        # one classifier per language; "minic" is the original model (self.clf)
        self.clfs: dict[str, Optional[Classifier]] = {"minic": self.clf, "c": None}
        c = langs.get("c")
        if load and c.model_path.exists():
            self.clfs["c"] = Classifier(c.model_path, c.columns)
        # reinforcement-learning fix policy (optional; trained by `python -m ml.rl.train_rl`)
        self.policy: Optional[Policy] = None
        self._lock = threading.Lock()
        self._decisions: OrderedDict = OrderedDict()
        self._online = {"updates": 0, "reward_sum": 0.0, "history": []}
        if load and POLICY_PATH.exists():
            try:
                self.policy = Policy.load()
            except (ValueError, OSError):
                self.policy = None
        self._trained_theta = self.policy.theta.copy() if self.policy else None

    @property
    def model_loaded(self) -> bool:
        return self.clf is not None

    @staticmethod
    def _constrain(probs: dict[str, float], code: str, causes: dict) -> dict[str, float]:
        """Keep only the causes the compiler's own error code leaves possible, renormalised."""
        allowed = causes.get(code)
        if not allowed:
            return probs
        kept = {l: p for l, p in probs.items() if l in allowed}
        total = sum(kept.values())
        if total < 1e-9:
            return {l: 1.0 / len(allowed) for l in allowed}
        return {l: p / total for l, p in kept.items()}

    # ----------------------------------------------------------- one diag
    def diagnose_one(self, d: Diagnostic, fe, mode: str = "ml", ranker: str = "heuristic",
                     explain: bool = True) -> dict:
        source = fe.source
        lang = langs.get(fe.lang)
        LABELS, clf = lang.labels, self.clfs[lang.key]
        entry: dict = {"diagnostic": d.to_dict(), "duplicates": 0}

        if d.code not in lang.ml_codes:
            entry["handled_by"] = "rules"
            raw = lang.gen_rules(d, fe)
            entry["prediction"] = None
            probs = None
        else:
            feats = lang.extract(d, fe)
            base_label = lang.baseline_predict(feats)
            if mode == "baseline" or clf is None:
                probs = {base_label: 1.0}
                entry["handled_by"] = "baseline" if mode == "baseline" else "rules-fallback"
            else:
                probs = self._constrain(clf.predict_proba(feats), d.code, lang.candidate_causes)
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
            if explain and clf is not None and mode == "ml":
                entry["explanation"] = clf.explain(feats, top_label)
            raw = []
            for l, p in ranked[:3]:
                if p < 0.02 and raw:
                    break
                for c in lang.generate(l, d, fe):
                    c["prob"] = p
                    raw.append(c)

        if lang.extras is not None and mode != "baseline":
            raw = list(raw) + lang.extras(d, fe)         # the compiler's own suggestions and the repair search

        uniq, seen = [], set()
        for c in raw:
            key = tuple((e.start, e.end, e.text) for e in c["edits"])
            if key not in seen:
                seen.add(key)
                uniq.append(c)
        if getattr(fe, "judged_by_gcc", False) and len(uniq) > 1:
            with ThreadPoolExecutor(min(8, len(uniq))) as pool:    # gcc runs in separate processes: validate in parallel
                verdicts = list(pool.map(lambda c: validate(source, c["edits"], fe, d), uniq))
        else:
            verdicts = [validate(source, c["edits"], fe, d) for c in uniq]
        titles = {**LABELS, **lang.extra_labels}

        cands = []
        for c, v in zip(uniq, verdicts):
            p = c.get("prob", 1.0)
            cands.append(
                {
                    "label": c["label"],
                    "label_title": titles.get(c["label"], {}).get("title", "Rule-based fix"),
                    "strategy": c.get("strategy", "default"),
                    "title": c["title"],
                    "description": c["description"],
                    "edits": [e.to_dict() for e in c["edits"]],
                    "prob": round(p, 4),
                    "local_score": c["local_score"],
                    "score": round(p * c["local_score"], 4),
                    "status": v["status"],
                    "reason": v["reason"],
                    "errors_after": v["errors_after"],
                    "progress": v.get("progress", 0),
                    "new_source": v["new_source"],
                    "diff": diff_hunks(source, v["new_source"]),
                }
            )
        # verified first, then partial. Among gcc-judged fixes the one that gets the compiler furthest wins; the
        # last-resort edit is always behind the real fixes of its status
        cands.sort(key=lambda c: (-STATUS_RANK[c["status"]], c["label"] == "LAST_RESORT", -c["progress"],
                                  c["errors_after"] if c["progress"] else 0, -c["score"]))
        cands = cands[:10]
        entry["ranker"] = "heuristic"
        if self.policy is not None and cands:
            # the RL policy scores every candidate; with ranker="rl" it also decides the order.
            # rejected fixes always stay last: nothing the compiler refused is ever offered.
            X = candidate_matrix(cands, len(fe.errors), d.stage)
            pr = self.policy.probs(X)
            for i, c in enumerate(cands):
                c["_row"] = i
                c["rl_prob"] = round(float(pr[i]), 4)
            if ranker == "rl":
                cands.sort(key=lambda c: (c["status"] == "rejected", -c["rl_prob"]))
                entry["ranker"] = "rl"
            for i, c in enumerate(cands):
                c["id"] = f"fix-{i + 1}"
            decision = uuid.uuid4().hex[:12]
            with self._lock:
                self._decisions[decision] = (X, {c["id"]: c.pop("_row") for c in cands})
                while len(self._decisions) > 2000:
                    self._decisions.popitem(last=False)
            entry["decision_id"] = decision
        else:
            for i, c in enumerate(cands):
                c["id"] = f"fix-{i + 1}"
        entry["candidates"] = cands
        # the last-resort fix (comment the line out) is listed but never chosen automatically
        best = next((c for c in cands if c["status"] != "rejected" and c["label"] != "LAST_RESORT"), None)
        entry["best"] = best["id"] if best else None
        entry["last_resort"] = next((c["id"] for c in cands if c["label"] == "LAST_RESORT" and c["status"] != "rejected"), None)
        if best:
            entry["localized"] = offset_to_pos(source, min(e["start"] for e in best["edits"]))
        return entry

    # ---------------------------------------------------------- whole file
    def diagnose(self, source: str, mode: str = "ml", only_first: bool = False, ranker: str = "heuristic",
                 explain: bool = True, language: str = "minic", max_entries: int = 6) -> dict:
        lang = langs.get(language)
        fe = lang.run_frontend(source)
        errors = fe.errors
        entries, seen = [], {}
        for d in errors:
            if len(entries) >= max_entries:      # later errors are usually knock-on effects of the first ones
                break
            key = None
            if d.code == "E_UNDECLARED":
                key = ("E_UNDECLARED", d.extra["name"])
            elif d.code == "E_MISSING_INCLUDE":
                key = ("E_MISSING_INCLUDE", d.extra["header"])
            if key in seen:
                seen[key]["duplicates"] += 1
                continue
            entry = self.diagnose_one(d, fe, mode, ranker, explain)
            if key is not None:
                seen[key] = entry
            entries.append(entry)
            if only_first:
                break
        return {
            "language": lang.key,
            "model_loaded": self.clfs[lang.key] is not None,
            "mode": mode,
            "ranker": ranker if self.policy is not None else "heuristic",
            "errors": len(errors),
            "entries": entries,
        }

    # ------------------------------------------------------------- autofix
    def autofix(self, source: str, max_steps: int = 20, mode: str = "ml", ranker: str = "heuristic",
                language: str = "minic", allow_last_resort: bool = False, search: bool = True, budget: float = 25.0,
                total_budget: float = 40.0) -> dict:
        """Apply the best fix, re-check, repeat. If that greedy walk gets stuck, fall back to a best-first search that
        can back out of a wrong turn (every state it visits is judged by the compiler)."""
        import time
        t0 = time.time()
        res = self._greedy(source, max_steps, mode, ranker, language, allow_last_resort, deadline=t0 + total_budget * 0.5)
        if res["ok"] or not search:
            return res
        left = total_budget - (time.time() - t0)
        if left < 3:
            return res
        found = self._best_first(source, mode, ranker, language, allow_last_resort, min(budget, left))
        return found if found["ok"] else res

    def _best_first(self, source: str, mode: str, ranker: str, language: str, allow_last_resort: bool, budget: float,
                    width: int = 3, max_depth: int = 10) -> dict:
        import heapq
        import itertools
        import time
        lang = langs.get(language)
        t0, tick = time.time(), itertools.count()
        visited = {source}
        heap = [(len(lang.run_frontend(source).errors), 0, next(tick), source, [])]
        best = (heap[0][0], source, [])
        while heap and time.time() - t0 < budget:
            errs, cost, _, cur, steps = heapq.heappop(heap)
            if len(steps) >= max_depth:
                continue
            res = self.diagnose(cur, mode=mode, only_first=True, ranker=ranker, explain=False, language=lang.key)
            if not res["entries"]:
                continue
            e = res["entries"][0]
            opts = [c for c in e["candidates"] if c["status"] != "rejected" and c["new_source"] not in visited
                    and (allow_last_resort or c["label"] != "LAST_RESORT")]
            for c in opts[:width]:
                visited.add(c["new_source"])
                pred = e.get("prediction")
                step = {"iteration": len(steps) + 1, "message": e["diagnostic"]["message"], "line": e["diagnostic"]["line"],
                        "label": c["label"], "label_title": c["label_title"], "confidence": pred["confidence"] if pred else None,
                        "title": c["title"], "status": c["status"], "diff": c["diff"]}
                new_steps = steps + [step]
                if c["status"] == "verified":
                    return {"language": lang.key, "ok": True, "steps": new_steps, "final_source": c["new_source"], "remaining": [], "searched": True}
                n = c["errors_after"] if c["errors_after"] >= 0 else 99
                heapq.heappush(heap, (n, cost + 1, next(tick), c["new_source"], new_steps))
                if n < best[0]:
                    best = (n, c["new_source"], new_steps)
        final = lang.run_frontend(best[1])
        return {"language": lang.key, "ok": not final.errors, "steps": best[2], "final_source": best[1],
                "remaining": [d.message for d in final.errors], "searched": True}

    def _greedy(self, source: str, max_steps: int, mode: str, ranker: str, language: str, allow_last_resort: bool,
                deadline: Optional[float] = None) -> dict:
        import time
        lang = langs.get(language)
        steps, cur, visited = [], source, {source}
        for i in range(max_steps):
            if deadline is not None and time.time() > deadline:
                break
            fe = lang.run_frontend(cur)
            if not fe.errors:
                break
            res = self.diagnose(cur, mode=mode, only_first=True, ranker=ranker, explain=False, language=lang.key)
            if not res["entries"]:
                break
            e = res["entries"][0]
            pick = e["best"] or (e.get("last_resort") if allow_last_resort else None)
            best = next((c for c in e["candidates"] if c["id"] == pick), None)
            if best is not None and best["new_source"] in visited:      # never go round in circles
                best = next((c for c in e["candidates"] if c["status"] != "rejected" and c["new_source"] not in visited
                             and (allow_last_resort or c["label"] != "LAST_RESORT")), None)
            if best is not None:
                visited.add(best["new_source"])
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
        final = lang.run_frontend(cur)
        return {
            "language": lang.key,
            "ok": not final.errors,
            "steps": steps,
            "final_source": cur,
            "remaining": [d.message for d in final.errors],
        }

    # ------------------------------------------------- online reinforcement
    def feedback(self, decision_id: str, candidate_id: str, reward: float) -> Optional[dict]:
        """Apply one policy-gradient step from user feedback (+1 accepted, -1 undone)."""
        with self._lock:
            rec = self._decisions.get(decision_id)
            if rec is None or self.policy is None:
                return None
            X, rows = rec
            a = rows.get(candidate_id)
            if a is None:
                return None
            reward = max(-1.0, min(1.0, float(reward)))
            before = float(self.policy.probs(X)[a])
            after = self.policy.online_update(X, a, reward)
            self._online["updates"] += 1
            self._online["reward_sum"] += reward
            self._online["history"] = (self._online["history"] + [reward])[-60:]
            return {"before": round(before, 4), "after": round(after, 4), "updates": self._online["updates"]}

    def reset_policy(self) -> None:
        with self._lock:
            if POLICY_PATH.exists():
                try:
                    self.policy = Policy.load()
                except (ValueError, OSError):
                    pass
            self._online = {"updates": 0, "reward_sum": 0.0, "history": []}
            self._trained_theta = self.policy.theta.copy() if self.policy else None

    def rl_status(self) -> dict:
        n = self._online["updates"]
        shift = 0.0
        if self.policy is not None and self._trained_theta is not None:
            shift = float(((self.policy.theta - self._trained_theta) ** 2).sum() ** 0.5)
        return {
            "loaded": self.policy is not None,
            "online_updates": n,
            "mean_reward": round(self._online["reward_sum"] / n, 3) if n else None,
            "history": self._online["history"],
            "weight_shift": round(shift, 4),
            "top_weights": self.policy.top_weights() if self.policy else [],
        }
