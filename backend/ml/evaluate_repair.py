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

import argparse

from repair import langs
from repair.engine import Engine

ROOT = Path(__file__).resolve().parents[2]


def toks(src: str, lang) -> list:
    return [(t.kind, t.value) for t in lang.run_frontend(src).tokens]


def evaluate(engine: Engine, rows: list[dict], mode: str, ranker: str = "heuristic", lang=None) -> dict:
    lang = lang or langs.get("minic")
    per = defaultdict(lambda: {"n": 0, "label_ok": 0, "verified": 0, "exact": 0, "top3_verified": 0, "autofix": 0})
    for r in rows:
        src = (lang.data_dir / r["file"]).read_text(encoding="utf-8")
        seed = (lang.data_dir / "seeds" / "valid" / f"{r['seed_id']}{lang.ext}").read_text(encoding="utf-8")
        res = engine.diagnose(src, mode=mode, only_first=True, ranker=ranker, explain=False, language=lang.key)
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
            if toks(cands[0]["new_source"], lang) == toks(seed, lang):
                p["exact"] += 1
        if any(c["status"] == "verified" for c in e["candidates"][:3]):
            p["top3_verified"] += 1
        if engine.autofix(src, mode=mode, ranker=ranker, language=lang.key)["ok"]:
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
            for l in lang.label_names
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="minic", choices=["minic", "c"])
    lang = langs.get(ap.parse_args().lang)
    engine = Engine()
    assert engine.clfs[lang.key] is not None, "train the model first: python -m ml.train" + (" --lang c" if lang.key == "c" else "")
    rows = [r for r in csv.DictReader((lang.data_dir / "manifest.csv").open(encoding="utf-8")) if r["split"] == "test"]
    print(f"evaluating {len(rows)} held-out {lang.title} programs")
    out = {"ml": evaluate(engine, rows, "ml", lang=lang), "baseline": evaluate(engine, rows, "baseline", lang=lang)}
    if engine.policy is not None:  # same single-fault programs, fixes ordered by the RL policy instead of the heuristic
        out["ml_rl"] = evaluate(engine, rows, "ml", ranker="rl", lang=lang)
    lang.eval_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    for k in out:
        print(k, out[k]["overall"])


if __name__ == "__main__":
    main()
