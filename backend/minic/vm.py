"""A label-addressed virtual machine for three-address code. Produces a
step-by-step trace so the front-end can replay execution."""
from __future__ import annotations

from .ops import apply_binary, apply_unary, fmt_value, is_literal, lit_value
from .tac import BINOPS, Instr


def run(code: list[Instr], var_types: dict[str, str], max_steps: int = 200_000, trace_limit: int = 4000) -> dict:
    labels = {ins.result: i for i, ins in enumerate(code) if ins.op == "label"}
    env: dict[str, object] = {}
    output: list[str] = []
    trace: list[dict] = []
    pc = steps = 0
    halted, error = "done", None

    def val(x):
        if x is None:
            return None
        if is_literal(x):
            return lit_value(x)
        return env.get(x, 0)

    def assign(name: str, v) -> None:
        if var_types.get(name) == "float" and isinstance(v, int) and not isinstance(v, bool):
            v = float(v)
        env[name] = v

    while pc < len(code):
        if steps >= max_steps:
            halted = "step_limit"
            break
        ins = code[pc]
        steps += 1
        step = {"pc": pc, "line": ins.line, "set": None, "out": None} if steps <= trace_limit else None
        nxt = pc + 1
        try:
            if ins.op == "label":
                pass
            elif ins.op == "=":
                assign(ins.result, val(ins.arg1))
            elif ins.op in BINOPS:
                assign(ins.result, apply_binary(ins.op, val(ins.arg1), val(ins.arg2)))
            elif ins.op in ("neg", "not", "itof"):
                assign(ins.result, apply_unary(ins.op, val(ins.arg1)))
            elif ins.op == "goto":
                nxt = labels[ins.result]
            elif ins.op == "iffalse":
                if not val(ins.arg1):
                    nxt = labels[ins.result]
            elif ins.op == "iftrue":
                if val(ins.arg1):
                    nxt = labels[ins.result]
            elif ins.op == "print":
                text = fmt_value(val(ins.arg1))
                output.append(text)
                if step is not None:
                    step["out"] = text
        except ZeroDivisionError:
            halted, error = "error", f"Runtime error: division by zero (line {ins.line})"
            if step is not None:
                trace.append(step)
            break
        if step is not None:
            if ins.op in ("=", "neg", "not", "itof") or ins.op in BINOPS:
                step["set"] = [ins.result, fmt_value(env[ins.result])]
            trace.append(step)
        pc = nxt

    visible = {k: fmt_value(v) for k, v in env.items() if not (len(k) > 1 and k[0] == "t" and k[1:].isdigit())}
    return {
        "output": output,
        "vars": visible,
        "steps": steps,
        "halted": halted,
        "error": error,
        "trace": trace,
        "trace_truncated": steps > trace_limit,
    }
