"""Stress test: can the system repair *any* error, not just the 14 it was trained on?

Take valid programs (the generated seeds plus twenty hand-written textbook programs), damage each one in a way that
has nothing to do with the training mutators (delete/insert/replace/swap a token, delete or duplicate a line, delete or
insert a character, drop an #include, cut the file short), keep only the damaged programs that gcc rejects, and run the
auto-fix. A repair counts only if gcc then builds the program.

    python -m ml.stress_c --per-op 100          # writes models/stress_c.json

Reported: how many were repaired, how many recovered the original program exactly, and - for the failures - which
compiler messages the system could not yet repair.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUNCT = list(";,(){}[]=+-*/<>!&|.:?#\"'")
KEYWORDS = ["int", "char", "double", "if", "else", "while", "for", "return", "struct", "void", "static", "const", "break"]


def tokens(src: str):
    from cfront.lexer import lex
    return lex(src)[0][:-1]


def op_delete_token(src, rng):
    t = rng.choice(tokens(src))
    return src[: t.start] + src[t.end:], f"delete token {t.value!r}"


def op_insert_token(src, rng):
    toks = tokens(src)
    t = rng.choice(toks)
    pool = PUNCT + KEYWORDS + [x.value for x in rng.sample(toks, min(8, len(toks))) if x.kind == "IDENT"]
    ins = rng.choice(pool)
    return src[: t.start] + ins + " " + src[t.start:], f"insert {ins!r}"


def op_replace_token(src, rng):
    toks = tokens(src)
    t = rng.choice(toks)
    pool = [x.value for x in toks if x.value != t.value] + PUNCT + KEYWORDS
    new = rng.choice(pool)
    return src[: t.start] + new + src[t.end:], f"replace {t.value!r} by {new!r}"


def op_swap_tokens(src, rng):
    toks = tokens(src)
    i = rng.randrange(len(toks) - 1)
    a, b = toks[i], toks[i + 1]
    return src[: a.start] + b.value + src[a.end:b.start] + a.value + src[b.end:], f"swap {a.value!r} {b.value!r}"


def op_delete_line(src, rng):
    lines = src.split("\n")
    i = rng.choice([k for k, l in enumerate(lines) if l.strip()])
    return "\n".join(lines[:i] + lines[i + 1:]), f"delete line {i + 1}"


def op_duplicate_line(src, rng):
    lines = src.split("\n")
    i = rng.choice([k for k, l in enumerate(lines) if l.strip() and not l.lstrip().startswith("#")] or [0])
    return "\n".join(lines[: i + 1] + [lines[i]] + lines[i + 1:]), f"duplicate line {i + 1}"


def op_delete_char(src, rng):
    i = rng.randrange(len(src))
    return src[:i] + src[i + 1:], f"delete char {src[i]!r}"


def op_insert_char(src, rng):
    i = rng.randrange(len(src))
    c = rng.choice(PUNCT + list("abcxyz019@$`~"))
    return src[:i] + c + src[i:], f"insert char {c!r}"


def op_typo_ident(src, rng):
    ids = [t for t in tokens(src) if t.kind == "IDENT" and len(t.value) >= 2]
    t = rng.choice(ids)
    w = t.value
    i = rng.randrange(len(w))
    bad = rng.choice([w[:i] + w[i + 1:], w[:i] + w[i] + w[i:], w[:i] + rng.choice("aeioutsn") + w[i + 1:], w[:i] + w[i + 1:i + 2] + w[i:i + 1] + w[i + 2:]])
    return src[: t.start] + bad + src[t.end:], f"typo {w!r} -> {bad!r}"


def op_drop_include(src, rng):
    lines = src.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("#include")]
    i = rng.choice(idx)
    return "\n".join(lines[:i] + lines[i + 1:]), f"drop {lines[i]}"


def op_truncate(src, rng):
    cut = rng.randrange(len(src) // 3, len(src) - 1)
    return src[:cut], f"truncate at {cut}"


def op_wrong_type(src, rng):
    toks = [t for t in tokens(src) if t.kind == "TYPE" and t.value in ("int", "char", "double", "float", "long")]
    t = rng.choice(toks)
    new = rng.choice([x for x in ("int", "char", "double", "float", "long", "void") if x != t.value])
    return src[: t.start] + new + src[t.end:], f"type {t.value} -> {new}"


OPS = {
    "delete_token": op_delete_token, "insert_token": op_insert_token, "replace_token": op_replace_token, "swap_tokens": op_swap_tokens,
    "delete_line": op_delete_line, "duplicate_line": op_duplicate_line, "delete_char": op_delete_char, "insert_char": op_insert_char,
    "typo_ident": op_typo_ident, "drop_include": op_drop_include, "truncate": op_truncate, "wrong_type": op_wrong_type,
}


def norm(msg: str) -> str:
    msg = re.sub(r"'[^']*'", "'_'", msg)
    msg = re.sub(r"\d+", "N", msg)
    return msg.replace("gcc: ", "").strip()


_ENGINE = None


def _engine():
    global _ENGINE
    if _ENGINE is None:
        sys.setrecursionlimit(8000)
        from repair.engine import Engine
        _ENGINE = Engine()
    return _ENGINE


def work(job: dict) -> dict:
    from cfront.pipeline import run_frontend, CFrontend  # noqa: F401
    from cfront import gcc
    eng = _engine()
    src, orig = job["source"], job["original"]
    t0 = time.time()
    fe = run_frontend(src)
    first = fe.errors[0].message if fe.errors else ""
    res = eng.autofix(src, language="c")
    res_lr = res if res["ok"] else eng.autofix(src, language="c", allow_last_resort=True)
    toks = lambda s: [(t.kind, t.value) for t in tokens(s)]
    from ml.realworld_c import PROGRAMS
    return {**{k: job[k] for k in ("op", "name", "what")}, "group": "textbook" if job["name"] in PROGRAMS else "generated", "ok": res["ok"], "ok_with_last_resort": res_lr["ok"],
            "exact": res["ok"] and toks(res["final_source"]) == toks(orig),
            "steps": len(res["steps"]), "seconds": round(time.time() - t0, 1), "first": norm(first), "message": first,
            "remaining": [norm(m) for m in res["remaining"][:2]], "source": src if not res["ok"] else None}


def make_jobs(per_op: int, seed: int) -> list[dict]:
    from cfront import gcc
    from ml.realworld_c import PROGRAMS
    sys.setrecursionlimit(8000)
    rng = random.Random(seed)
    base = [(n, s) for n, s in PROGRAMS.items()]
    seeds_dir = ROOT / "datasets" / "c" / "seeds" / "valid"
    seeds = sorted(seeds_dir.glob("*.c"))
    base += [(p.stem, p.read_text(encoding="utf-8")) for p in rng.sample(seeds, min(80, len(seeds)))]
    base = [(n, s) for n, s in base if gcc.run(s, link=True).ok]
    jobs = []
    for op_name, op in OPS.items():
        made, tries = 0, 0
        while made < per_op and tries < per_op * 25:
            tries += 1
            name, src = rng.choice(base)
            try:
                new, what = op(src, rng)
            except (IndexError, ValueError):
                continue
            if new == src or not new.strip():
                continue
            g = gcc.run(new, link=True)
            if g.ok or not g.errors:
                continue                       # gcc accepts it: not an error
            jobs.append({"op": op_name, "name": name, "what": what, "source": new, "original": src})
            made += 1
    return jobs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-op", type=int, default=60)
    ap.add_argument("--seed", type=int, default=2024)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=str(ROOT / "models" / "stress_c.json"))
    args = ap.parse_args()
    t0 = time.time()
    jobs = make_jobs(args.per_op, args.seed)
    print(f"{len(jobs)} broken programs that gcc rejects (built in {time.time() - t0:.0f}s)", flush=True)
    results = []
    with ProcessPoolExecutor(args.workers) as pool:
        for i, r in enumerate(pool.map(work, jobs, chunksize=2), 1):
            results.append(r)
            if i % 50 == 0:
                ok = sum(x["ok"] for x in results)
                print(f"  {i}/{len(jobs)}  repaired {ok / i:.1%}", flush=True)
    n = len(results)
    ok = sum(r["ok"] for r in results)
    per_op = {}
    for op in OPS:
        rs = [r for r in results if r["op"] == op]
        if rs:
            per_op[op] = {"n": len(rs), "repaired": round(sum(r["ok"] for r in rs) / len(rs), 4),
                          "exact": round(sum(r["exact"] for r in rs) / len(rs), 4)}
    STRUCTURAL = {"delete_line", "duplicate_line", "truncate"}
    def rate(rs, key):
        return round(sum(x[key] for x in rs) / len(rs), 4) if rs else None
    per_group = {}
    for name, rs in (("textbook programs", [x for x in results if x["group"] == "textbook"]),
                     ("generated programs", [x for x in results if x["group"] == "generated"]),
                     ("small slips (one token or character)", [x for x in results if x["op"] not in STRUCTURAL]),
                     ("structural damage (lines or whole file)", [x for x in results if x["op"] in STRUCTURAL])):
        per_group[name] = {"n": len(rs), "repaired": rate(rs, "ok"), "exact": rate(rs, "exact"), "repaired_with_last_resort": rate(rs, "ok_with_last_resort")}
    fails = Counter(r["first"] for r in results if not r["ok"])
    summary = {
        "n": n, "repaired": round(ok / n, 4), "exact_recovery": round(sum(r["exact"] for r in results) / n, 4),
        "repaired_with_last_resort": round(sum(r["ok_with_last_resort"] for r in results) / n, 4),
        "mean_seconds": round(sum(r["seconds"] for r in results) / n, 2), "per_operator": per_op, "per_group": per_group,
        "unrepaired_messages": fails.most_common(25),
        "failures": [{"op": r["op"], "message": r["message"], "source": r["source"]} for r in results if not r["ok"]][:60],
    }
    Path(args.out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("failures", "unrepaired_messages")}, indent=2))
    print("most common unrepaired gcc messages:")
    for m, c in fails.most_common(15):
        print(f"  {c:3d}  {m}")


if __name__ == "__main__":
    main()
