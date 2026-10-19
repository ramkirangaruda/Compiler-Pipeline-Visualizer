"""Machine-independent optimizations over three-address code.

Passes (iterated to a fixed point):
  1. constant folding            2. algebraic simplification
  3. local copy/constant propagation (per basic block, correctly invalidated)
  4. branch folding + unreachable code + jump threading
  5. dead-code elimination driven by global live-variable analysis
"""
from __future__ import annotations

import difflib

from .cfg import build_blocks, liveness
from .ops import apply_binary, apply_unary, is_literal, lit_format, lit_value
from .tac import BINOPS, BRANCHES, DEFINES, UNOPS, Instr, defs, uses

Result = tuple[list[Instr], int]


def fold_constants(code: list[Instr]) -> Result:
    n, out = 0, []
    for ins in code:
        folded = None
        try:
            if ins.op in BINOPS and is_literal(ins.arg1) and is_literal(ins.arg2):
                folded = lit_format(apply_binary(ins.op, lit_value(ins.arg1), lit_value(ins.arg2)))
            elif ins.op in UNOPS and is_literal(ins.arg1):
                folded = lit_format(apply_unary(ins.op, lit_value(ins.arg1)))
        except (ZeroDivisionError, OverflowError, TypeError, ValueError):
            folded = None
        if folded is not None:
            out.append(Instr("=", folded, None, ins.result, ins.line))
            n += 1
        else:
            out.append(ins)
    return out, n


def simplify_algebra(code: list[Instr]) -> Result:
    n, out = 0, []
    for ins in code:
        new = None
        a, b = ins.arg1, ins.arg2
        if ins.op == "+" and b == "0":
            new = a
        elif ins.op == "+" and a == "0":
            new = b
        elif ins.op == "-" and b == "0":
            new = a
        elif ins.op == "*" and b == "1":
            new = a
        elif ins.op == "*" and a == "1":
            new = b
        elif ins.op == "/" and b == "1":
            new = a
        if new is not None:
            out.append(Instr("=", new, None, ins.result, ins.line))
            n += 1
        else:
            out.append(ins)
    return out, n


def propagate(code: list[Instr]) -> Result:
    """Block-local copy and constant propagation."""
    n, out = 0, []
    known: dict[str, str] = {}
    for ins in code:
        if ins.op == "label":
            known.clear()
            out.append(ins)
            continue
        new = ins.copy()
        if new.op in DEFINES or new.op in ("iffalse", "iftrue", "print"):
            if new.arg1 in known:
                new.arg1 = known[new.arg1]
                n += 1
            if new.arg2 in known:
                new.arg2 = known[new.arg2]
                n += 1
        d = defs(new)
        if d is not None:
            known.pop(d, None)
            for k in [k for k, v in known.items() if v == d]:
                del known[k]
            if new.op == "=" and new.arg1 != d:
                known[d] = new.arg1
        out.append(new)
        if new.op in BRANCHES:
            known.clear()
    return out, n


def fold_branches(code: list[Instr]) -> tuple[list[Instr], dict[str, int]]:
    counts = {"Branch folding": 0, "Unreachable code removal": 0, "Jump threading": 0, "Dead label removal": 0}
    cur: list[Instr] = []
    for ins in code:
        if ins.op in ("iffalse", "iftrue") and ins.arg1 in ("true", "false"):
            taken = (ins.arg1 == "false") == (ins.op == "iffalse")
            counts["Branch folding"] += 1
            if taken:
                cur.append(Instr("goto", None, None, ins.result, ins.line))
            continue
        cur.append(ins)

    # jump threading: goto L where L: goto M  ->  goto M
    first_real: dict[str, Instr | None] = {}
    for i, ins in enumerate(cur):
        if ins.op == "label":
            j = i
            while j < len(cur) and cur[j].op == "label":
                j += 1
            first_real[ins.result] = cur[j] if j < len(cur) else None
    for i, ins in enumerate(cur):
        if ins.op in BRANCHES:
            seen = set()
            tgt = ins.result
            while tgt not in seen:
                seen.add(tgt)
                nxt = first_real.get(tgt)
                if nxt is not None and nxt.op == "goto" and nxt.result != tgt:
                    tgt = nxt.result
                else:
                    break
            if tgt != ins.result:
                cur[i] = ins.copy(result=tgt)
                counts["Jump threading"] += 1

    # unreachable code after an unconditional jump, up to the next label
    out: list[Instr] = []
    dead = False
    for ins in cur:
        if ins.op == "label":
            dead = False
        elif dead:
            counts["Unreachable code removal"] += 1
            continue
        out.append(ins)
        if ins.op == "goto":
            dead = True

    # goto L immediately followed by L:
    out2: list[Instr] = []
    for i, ins in enumerate(out):
        if ins.op == "goto":
            j = i + 1
            while j < len(out) and out[j].op == "label":
                if out[j].result == ins.result:
                    counts["Jump threading"] += 1
                    break
                j += 1
            else:
                out2.append(ins)
                continue
            continue
        out2.append(ins)

    referenced = {ins.result for ins in out2 if ins.op in BRANCHES}
    final = []
    for ins in out2:
        if ins.op == "label" and ins.result not in referenced:
            counts["Dead label removal"] += 1
            continue
        final.append(ins)
    return final, counts


def eliminate_dead_code(code: list[Instr]) -> Result:
    blocks = build_blocks(code)
    if not blocks:
        return code, 0
    info = liveness(code, blocks)
    keep = [True] * len(code)
    n = 0
    for b in blocks:
        live = set(info[b["id"]]["out"])
        for i in range(b["end"] - 1, b["start"] - 1, -1):
            ins = code[i]
            d = defs(ins)
            if d is not None and d not in live:
                keep[i] = False
                n += 1
                continue
            if d is not None:
                live.discard(d)
            live |= set(uses(ins))
    return [ins for ins, k in zip(code, keep) if k], n


PASS_ORDER = [
    "Constant folding",
    "Algebraic simplification",
    "Copy / constant propagation",
    "Branch folding",
    "Unreachable code removal",
    "Jump threading",
    "Dead label removal",
    "Dead code elimination (liveness)",
]


def optimize(code: list[Instr], max_rounds: int = 12) -> dict:
    totals = {name: 0 for name in PASS_ORDER}
    cur = [i.copy() for i in code]
    rounds = 0
    for rounds in range(1, max_rounds + 1):
        before = [i.text() for i in cur]
        cur, c = fold_constants(cur)
        totals["Constant folding"] += c
        cur, c = simplify_algebra(cur)
        totals["Algebraic simplification"] += c
        cur, c = propagate(cur)
        totals["Copy / constant propagation"] += c
        cur, counts = fold_branches(cur)
        for k, v in counts.items():
            totals[k] += v
        cur, c = eliminate_dead_code(cur)
        totals["Dead code elimination (liveness)"] += c
        if [i.text() for i in cur] == before:
            break
    return {"code": cur, "report": [{"name": k, "count": v} for k, v in totals.items()], "rounds": rounds}


def diff(orig: list[Instr], opt: list[Instr]) -> list[dict]:
    a, b = [i.text() for i in orig], [i.text() for i in opt]
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        ops.append({"tag": tag, "a": [i1, i2], "b": [j1, j2]})
    return ops
