"""Runtime semantics of MiniC operators. Shared by the constant folder and the
VM so that compile-time and run-time evaluation can never disagree."""
from __future__ import annotations

import json
import re

_NUM = re.compile(r"^-?\d+(\.\d+)?$")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "'": "'", "0": "\0"}


def is_literal(x) -> bool:
    return isinstance(x, str) and (x in ("true", "false") or x.startswith('"') or bool(_NUM.match(x)))


def decode_string(lit: str) -> str:
    try:
        v = json.loads(lit)
        if isinstance(v, str):
            return v
    except ValueError:
        pass
    body, out, i = lit[1:-1], [], 0
    while i < len(body):
        if body[i] == "\\" and i + 1 < len(body):
            out.append(_ESCAPES.get(body[i + 1], body[i + 1]))
            i += 2
        else:
            out.append(body[i])
            i += 1
    return "".join(out)


def lit_value(s: str):
    if s == "true":
        return True
    if s == "false":
        return False
    if s.startswith('"'):
        return decode_string(s)
    if "." in s:
        return float(s)
    return int(s)


def lit_format(v) -> str | None:
    """Source-level spelling of a runtime value, or None if it cannot be a literal."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        r = repr(v)
        return r if _NUM.match(r) else None
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    return None


def fmt_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return repr(v)
    return str(v)


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def apply_binary(op: str, a, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if _is_int(a) and _is_int(b):
            q = abs(a) // abs(b)
            return q if (a < 0) == (b < 0) else -q
        return a / b
    if op == "%":
        r = abs(a) % abs(b)
        return r if a >= 0 else -r
    if op == "<":
        return a < b
    if op == ">":
        return a > b
    if op == "<=":
        return a <= b
    if op == ">=":
        return a >= b
    if op == "==":
        return a == b
    if op == "!=":
        return a != b
    raise ValueError(op)


def apply_unary(op: str, a):
    if op == "neg":
        return -a
    if op == "not":
        return not a
    if op == "itof":
        return float(a)
    raise ValueError(op)
