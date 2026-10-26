"""The compiler validates the ML: every candidate fix is applied to the source
and pushed back through lexer -> parser -> semantic analysis. A suggestion is
only presented as a fix if the compiler accepts it."""
from __future__ import annotations

from minic.tokens import Diagnostic

from .candidates import Edit, apply_edits


def _signature(d: Diagnostic) -> tuple:
    return (d.code, d.extra.get("name"), d.extra.get("kind"))


def validate(source: str, edits: list[Edit], before, target: Diagnostic) -> dict:
    try:
        new_source = apply_edits(source, edits)
    except ValueError:
        return {"status": "rejected", "reason": "edits overlap", "errors_after": -1, "new_source": source}
    after = before.rerun(new_source)
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
