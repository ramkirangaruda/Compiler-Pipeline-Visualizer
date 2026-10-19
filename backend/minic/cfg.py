"""Basic blocks, control-flow graph and iterative live-variable analysis."""
from __future__ import annotations

from .tac import BRANCHES, Instr, defs, uses


def build_blocks(code: list[Instr]) -> list[dict]:
    n = len(code)
    if n == 0:
        return []
    label_at = {ins.result: i for i, ins in enumerate(code) if ins.op == "label"}
    leaders = {0}
    for i, ins in enumerate(code):
        if ins.op == "label":
            leaders.add(i)
        if ins.op in BRANCHES:
            if i + 1 < n:
                leaders.add(i + 1)
            if ins.result in label_at:
                leaders.add(label_at[ins.result])
    starts = sorted(leaders)
    blocks = []
    for bi, s in enumerate(starts):
        e = starts[bi + 1] if bi + 1 < len(starts) else n
        blocks.append({"id": f"B{bi}", "start": s, "end": e, "succ": []})
    block_of = {}
    for b in blocks:
        for i in range(b["start"], b["end"]):
            block_of[i] = b["id"]
    for bi, b in enumerate(blocks):
        last = code[b["end"] - 1]
        nxt = blocks[bi + 1]["id"] if bi + 1 < len(blocks) else None
        target = block_of.get(label_at.get(last.result)) if last.op in BRANCHES else None
        if last.op == "goto":
            if target:
                b["succ"].append({"to": target, "kind": "jump"})
        elif last.op in ("iffalse", "iftrue"):
            fall_kind, jump_kind = ("true", "false") if last.op == "iffalse" else ("false", "true")
            if nxt:
                b["succ"].append({"to": nxt, "kind": fall_kind})
            if target:
                b["succ"].append({"to": target, "kind": jump_kind})
        elif nxt:
            b["succ"].append({"to": nxt, "kind": "fall"})
    return blocks


def liveness(code: list[Instr], blocks: list[dict]) -> dict[str, dict]:
    """Classic backward data-flow: in[B] = use[B] | (out[B] - def[B])."""
    info = {}
    for b in blocks:
        use, dfn = set(), set()
        for i in range(b["start"], b["end"]):
            for u in uses(code[i]):
                if u not in dfn:
                    use.add(u)
            d = defs(code[i])
            if d:
                dfn.add(d)
        info[b["id"]] = {"use": use, "def": dfn, "in": set(), "out": set()}
    changed = True
    while changed:
        changed = False
        for b in reversed(blocks):
            rec = info[b["id"]]
            out = set()
            for s in b["succ"]:
                out |= info[s["to"]]["in"]
            inn = rec["use"] | (out - rec["def"])
            if out != rec["out"] or inn != rec["in"]:
                rec["out"], rec["in"] = out, inn
                changed = True
    return info


def cfg_json(code: list[Instr]) -> dict:
    blocks = build_blocks(code)
    live = liveness(code, blocks)
    out = []
    for b in blocks:
        rec = live[b["id"]]
        out.append(
            {
                "id": b["id"],
                "start": b["start"],
                "end": b["end"],
                "instrs": [code[i].text() for i in range(b["start"], b["end"])],
                "succ": b["succ"],
                "use": sorted(rec["use"]),
                "def": sorted(rec["def"]),
                "live_in": sorted(rec["in"]),
                "live_out": sorted(rec["out"]),
            }
        )
    return {"blocks": out, "edges": sum(len(b["succ"]) for b in out)}
