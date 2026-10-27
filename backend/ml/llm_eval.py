"""How much does "Ask an LLM" add? Take the programs the built-in repair could NOT fix in the stress test, ask the model,
and count the answers gcc accepts. Needs an API key; sends the (synthetic) test programs to the provider.

    python -m ml.llm_eval            # writes models/llm_eval.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    sys.setrecursionlimit(8000)
    from cfront.pipeline import run_frontend
    from repair import llm

    if not llm.status()["configured"]:
        raise SystemExit("no API key configured")
    fails = json.loads((ROOT / "models" / "stress_c.json").read_text(encoding="utf-8"))["failures"]
    rows = []
    for i, f in enumerate(fails, 1):
        t0 = time.time()
        r = llm.suggest(f["source"], run_frontend)
        for wait in (20, 40, 60):                       # a rate limit is not a failed repair: back off and ask again
            if not (r.get("error") and "429" in r.get("message", "")):
                break
            time.sleep(wait)
            r = llm.suggest(f["source"], run_frontend)
        sugg = r.get("suggestions", [])
        verified = [s for s in sugg if s["status"] == "verified"]
        rows.append({"op": f["op"], "message": f["message"], "verified": bool(verified), "partial": bool(sugg and not verified),
                     "rejected": r.get("rejected", 0), "error": r.get("error", False), "seconds": round(time.time() - t0, 1)})
        print(f"{i:3d}/{len(fails)} {'FIXED' if verified else 'no fix':7s} {f['op']:15s} {rows[-1]['seconds']}s {r.get('message', '')[:70]}", flush=True)
        time.sleep(4)         # stay under the provider's rate limit
    n = len(rows)
    fixed = sum(r["verified"] for r in rows)
    out = {"n": n, "fixed_by_llm": fixed, "rate": round(fixed / n, 4) if n else None, "model": llm.status(), "rows": rows}
    (ROOT / "models" / "llm_eval.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nthe built-in repair failed on {n} programs; the LLM + gcc fixed {fixed} of them ({out['rate']:.0%})")


if __name__ == "__main__":
    main()
