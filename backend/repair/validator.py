"""The compiler validates the ML: every candidate fix is applied to the source
and pushed back through lexer -> parser -> semantic analysis. A suggestion is
only presented as a fix if the compiler accepts it."""
from __future__ import annotations

import re

from minic.tokens import Diagnostic

from .candidates import Edit, apply_edits


def _sig(g) -> str:
    return re.sub(r"'[^']*'", "'_'", g.message)


def _to_old(new_off: int, edits: list) -> int:
    """Where an offset of the repaired program sits in the original program."""
    adj = 0
    for e in sorted(edits, key=lambda x: (x.start, x.end)):
        new_start = e.start + adj
        new_end = new_start + len(e.text)
        if new_off < new_start:
            break
        if new_off < new_end:
            return e.start
        adj += len(e.text) - (e.end - e.start)
    return new_off - adj


def _validate_gcc(source: str, new_source: str, edits: list, before, after, target: Diagnostic) -> dict:
    """The real compiler is the judge: a fix is verified when gcc builds the result, partial when it resolves
    the targeted error (or gets gcc past it) without causing a pile of new ones, rejected otherwise."""
    ge_b, ge_a = before.gcc.errors, after.gcc.errors
    n_b, n_a = len(ge_b), len(ge_a)
    if not ge_a:
        return {"status": "verified", "reason": "gcc builds it with 0 errors", "errors_after": 0, "new_source": new_source,
                "progress": len(source) + 1}
    tgt = next((g for g in ge_b if g.line == target.line), ge_b[0]) if ge_b else None
    status, reason = "rejected", f"Still fails: {ge_a[0].message}"
    if tgt is not None:
        shift = sum(e.text.count("\n") - source[e.start:e.end].count("\n") for e in edits if e.end <= tgt.start)
        persists = any(_sig(a) == _sig(tgt) and a.line == tgt.line + shift for a in ge_a)
        if not persists and n_a <= n_b + 2:
            status, reason = "partial", f"That error is gone; {n_a} other error(s) remain"
        elif persists and ge_a[0].line > ge_b[0].line + shift and ge_a[0].line != tgt.line + shift:
            status, reason = "partial", f"gcc gets past this point; next problem on line {ge_a[0].line}"
        elif n_a < n_b:
            status, reason = "partial", f"{n_b - n_a} fewer error(s)"
    return {"status": status, "reason": reason, "errors_after": n_a, "new_source": new_source,
            "progress": _to_old(ge_a[0].start, edits)}


def _signature(d: Diagnostic) -> tuple:
    return (d.code, d.extra.get("name"), d.extra.get("kind"))


def validate(source: str, edits: list[Edit], before, target: Diagnostic) -> dict:
    try:
        new_source = apply_edits(source, edits)
    except ValueError:
        return {"status": "rejected", "reason": "edits overlap", "errors_after": -1, "new_source": source}
    after = before.rerun(new_source)
    if getattr(before, "judged_by_gcc", False) and getattr(after, "judged_by_gcc", False):
        return _validate_gcc(source, new_source, edits, before, after, target)
    errs = after.errors
    n_before, n_after = len(before.errors), len(errs)

    if not errs:
        return {"status": "verified", "reason": "Recompiles with 0 errors", "errors_after": 0, "new_source": new_source}

    status, reason = "rejected", f"Still fails: {errs[0].message}"
    if after.lex_errors and len(after.lex_errors) > len(before.lex_errors):
        reason = "Introduces a lexical error"
    elif target.stage in ("lexical", "syntax"):
        if before.parse_error is not None and after.parse_error is None:
            status, reason = "partial", f"Syntax error fixed; {n_after} semantic error(s) remain"
        elif before.parse_error is not None and after.parse_error is not None:
            delta = len(after.tokens) - len(before.tokens)
            old_i = before.parse_error.extra["found_index"]
            new_i = after.parse_error.extra["found_index"]
            if new_i > old_i + max(delta, 0):
                status, reason = "partial", f"Parser gets past this error; next problem on line {after.parse_error.line}"
        elif before.lex_errors and len(after.lex_errors) < len(before.lex_errors):
            status, reason = "partial", "Lexical error fixed"
    else:  # semantic target
        if after.parse_error is None:
            gone = _signature(target) not in {_signature(e) for e in errs} or all(
                e.start != target.start for e in errs if _signature(e) == _signature(target)
            )
            names_after = [e.extra.get("name") for e in errs if e.code == target.code]
            if target.extra.get("name") is not None and target.extra["name"] not in names_after and n_after < n_before:
                status, reason = "partial", f"Error resolved; {n_after} other error(s) remain"
            elif target.extra.get("name") is None and n_after < n_before and gone:
                status, reason = "partial", f"Error resolved; {n_after} other error(s) remain"
    return {"status": status, "reason": reason, "errors_after": n_after, "new_source": new_source}
