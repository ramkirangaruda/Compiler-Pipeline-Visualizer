"""End-to-end repair evaluation on the held-out test programs.

For each corrupted program the full engine runs (features -> classifier ->
candidates -> compiler validation) and the top-ranked fix is compared with the
original, uncorrupted seed. The same candidates are also generated from the
rule baseline's label so the dashboard can show what the ML layer adds.

Run from backend/:  python -m ml.evaluate_repair
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from minic.lexer import lex
from minic.pipeline import run_frontend
from repair.engine import Engine
from repair.labels import LABEL_NAMES

ROOT = Path(__file__).resolve().parents[2]


def toks(src: str) -> list:
    return [(t.kind, t.value) for t in lex(src)[0]]


def evaluate(engine: Engine, rows: list[dict], mode: str, ranker: str = "heuristic") -> dict:
    per = defaultdict(lambda: {"n": 0, "label_ok": 0, "verified": 0, "exact": 0, "top3_verified": 0, "autofix": 0})
    for r in rows:
        src = (ROOT / "datasets" / r["file"]).read_text(encoding="utf-8")
        seed = (ROOT / "datasets" / "seeds" / "valid" / f"{r['seed_id']}.mc").read_text(encoding="utf-8")
        res = engine.diagnose(src, mode=mode, only_first=True, ranker=ranker, explain=False)
        p = per[r["label"]]
        p["n"] += 1
        if not res["entries"]:
            continue
        e = res["entries"][0]
        if e["prediction"] and e["prediction"]["label"] == r["label"]:
            p["label_ok"] += 1
        cands = [c for c in e["candidates"] if c["status"] != "rejected"]
        if cands and cands[0]["status"] == "verified":
            p["verified"] += 1
            if toks(cands[0]["new_source"]) == toks(seed):
                p["exact"] += 1
        if any(c["status"] == "verified" for c in e["candidates"][:3]):
            p["top3_verified"] += 1
        if engine.autofix(src, mode=mode, ranker=ranker)["ok"]:
            p["autofix"] += 1
    total = {k: sum(v[k] for v in per.values()) for k in ("n", "label_ok", "verified", "exact", "top3_verified", "autofix")}
    rate = lambda a, b: round(a / b, 4) if b else 0.0
    return {
        "overall": {
            "n": total["n"],
            "label_accuracy": rate(total["label_ok"], total["n"]),
            "verified_fix_rate": rate(total["verified"], total["n"]),
            "exact_recovery_rate": rate(total["exact"], total["n"]),
            "top3_verified_rate": rate(total["top3_verified"], total["n"]),
            "autofix_success_rate": rate(total["autofix"], total["n"]),
        },
        "per_label": [
            {
                "label": l,
                "n": per[l]["n"],
                "label_accuracy": rate(per[l]["label_ok"], per[l]["n"]),
                "verified_fix_rate": rate(per[l]["verified"], per[l]["n"]),
                "exact_recovery_rate": rate(per[l]["exact"], per[l]["n"]),
                "autofix_success_rate": rate(per[l]["autofix"], per[l]["n"]),
            }
            for l in LABEL_NAMES
        ],
    }


def main() -> None:
    engine = Engine()
    assert engine.model_loaded, "train the model first: python -m ml.train"
    rows = [r for r in csv.DictReader((ROOT / "datasets" / "manifest.csv").open(encoding="utf-8")) if r["split"] == "test"]
    print(f"evaluating {len(rows)} held-out programs")
    out = {"ml": evaluate(engine, rows, "ml"), "baseline": evaluate(engine, rows, "baseline")}
    if engine.policy is not None:  # same single-fault programs, fixes ordered by the RL policy instead of the heuristic
        out["ml_rl"] = evaluate(engine, rows, "ml", ranker="rl")
    (ROOT / "models" / "repair_eval.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for k in out:
        print(k, out[k]["overall"])


if __name__ == "__main__":
    main()
