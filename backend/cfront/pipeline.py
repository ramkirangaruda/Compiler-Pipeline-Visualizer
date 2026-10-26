"""The C driver: tokenize -> parse -> analyze, with the real C compiler (gcc) as the judge.

`run_frontend` is the part the repair validator re-runs for every candidate fix. Our own front end supplies the rich facts
the ML layer learns from; gcc decides whether a program is correct. When both see the same problem the detailed own
diagnostics are used; when gcc sees a problem our front end cannot (a construct we do not model, any rarer error), the
gcc diagnostic is used as-is (code E_GCC) and the generic gcc-driven repair takes over.

`compile_source` produces the JSON the Studio renders, in the same shape as MiniC's."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional

from pycparser import c_ast as C

from minic.tokens import Diagnostic, Token

from . import gcc as G
from .astjson import to_tree
from .lexer import RESERVED, lex
from .parser import parse
from .semantic import CSemantic, analyze

_SYNTAX_MSG = re.compile(
    r"^(expected|stray|missing terminating|unterminated|extra tokens|invalid preprocessing|unknown type name|'else' without|"
    r"case label not within|break statement not within|continue statement not within|expected .* at end of input|"
    r".* at end of input|empty character constant|multi-character|invalid suffix|invalid digit|missing binary operator|"
    r"unbalanced|#(if|else|endif|elif))", re.I)


def gcc_diagnostic(g: G.GDiag, tokens: list[Token]) -> Diagnostic:
    stage = "syntax" if (g.kind == "error" and _SYNTAX_MSG.match(g.message)) else "semantic"
    idx = next((i for i, t in enumerate(tokens) if t.end > g.start), max(0, len(tokens) - 1))
    first = tokens[idx] if tokens else None
    prev = tokens[idx - 1] if idx > 0 else None
    extra = {
        "gcc": True, "kind": g.kind, "gcc_message": g.message, "option": g.option,
        "fixits": [list(f) for f in g.fixits], "notes": [{"message": n["message"], "fixits": [list(f) for f in n["fixits"]]} for n in g.notes],
        "found_index": idx, "ctx": "gcc", "expected": [], "name": None,
        "found": first.cls if first else "EOF", "found_value": first.value if first else "",
        "prev_end": prev.end if prev else 0, "prev_line": prev.line if prev else 1,
    }
    suffix = "" if g.kind == "link" else f" (line {g.line})"
    return Diagnostic(stage, "E_GCC", f"gcc: {g.message}{suffix}", g.line, g.col, g.start, max(g.end, g.start + 1), extra=extra)


@dataclass
class CFrontend:
    source: str
    tokens: list[Token]
    lex_errors: list[Diagnostic]
    directives: list
    program: Optional[C.FileAST]
    parse_error: Optional[Diagnostic]
    sem: Optional[CSemantic]
    gcc: Optional[G.GccResult] = None
    lang: str = "c"
    keywords: tuple = field(default=RESERVED)

    @property
    def own_errors(self) -> list[Diagnostic]:
        out = list(self.lex_errors)
        if self.parse_error:
            out.append(self.parse_error)
        if self.sem:
            out.extend(self.sem.errors)
        return out

    @property
    def errors(self) -> list[Diagnostic]:
        own = self.own_errors
        g = self.gcc
        if g is None or not g.available:
            return own
        if not g.errors:
            return []                      # a real compiler accepts it: that is the verdict
        first = g.errors[0]
        if own and any(d.line == first.line or (d.code == "E_UNEXPECTED_EOF" and "end of input" in first.message) for d in own):
            return own                     # both see it: the own diagnostics carry the ML features
        return [gcc_diagnostic(e, self.tokens) for e in g.errors]

    @property
    def warnings(self) -> list[Diagnostic]:
        g = self.gcc
        if g is not None and g.available:
            return [Diagnostic("semantic", "W_GCC", f"Warning: {w.message} (line {w.line})", w.line, w.col, w.start, max(w.end, w.start + 1),
                               "warning", {"option": w.option}) for w in g.warnings]
        return list(self.sem.warnings) if self.sem else []

    @property
    def judged_by_gcc(self) -> bool:
        return self.gcc is not None and self.gcc.available

    def rerun(self, source: str) -> "CFrontend":
        return run_frontend(source)


def run_frontend(source: str, use_gcc: bool = True) -> CFrontend:
    tokens, lex_errors, directives, clean = lex(source)
    included = {d.header for d in directives if d.name == "include" and d.header}
    try:
        program, perr, _ = parse(source, clean, tokens, included)
        sem = analyze(source, tokens, directives, program) if program is not None else None
    except Exception:                      # a construct our own front end cannot model: gcc still judges it
        program, perr, sem = None, None, None
    g = None
    if use_gcc and G.available():
        g = G.run(source)
        if g.ok:
            g = G.run(source, link=True)   # also catches "no main" and undefined references
    return CFrontend(source, tokens, lex_errors, directives, program, perr, sem, g)


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 2)


def compile_source(source: str, **_ignored) -> dict:
    stages = []
    t0 = time.perf_counter()
    fe = run_frontend(source)
    tokens, program, sem = fe.tokens, fe.program, fe.sem
    errors = fe.errors
    own_bad = bool(fe.own_errors)
    judge_ok = fe.judged_by_gcc and not errors

    def st(key, label, bad, skipped=False):
        status = "skipped" if skipped else ("ok" if (judge_ok or not bad) else "error")
        stages.append({"key": key, "label": label, "status": status, "ms": 0 if skipped else round(_ms(t0) / 3, 2)})

    st("lexer", "Lexer", bool(fe.lex_errors))
    st("parser", "Parser", fe.parse_error is not None, skipped=False)
    st("semantic", "Semantic", bool(sem and sem.errors), skipped=program is None and fe.parse_error is not None and not judge_ok)
    if fe.judged_by_gcc:
        stages.append({"key": "gcc", "label": "gcc", "status": "ok" if not errors else "error", "ms": 0})
    # the compiler-stage strip should show where the first real problem is
    if errors and all(s["status"] == "ok" for s in stages[:3]):
        stages[2]["status"] = "error"

    result: dict = {
        "language": "c",
        "ok": not errors,
        "tokens": [t.to_dict() for t in tokens],
        "ast": None,
        "ast_tree": to_tree(program) if program is not None else None,
        "symbols": sem.table() if sem else None,
        "diagnostics": [d.to_dict() for d in errors],
        "warnings": [d.to_dict() for d in fe.warnings],
        "tac": [], "optimized": None, "cfg": None, "execution": None, "verify": None,
        "compiler": {"name": G.COMPILER, "available": G.available(), "judge": fe.judged_by_gcc,
                     "own_front_end_agrees": (not own_bad) == (not errors) if fe.judged_by_gcc else None},
    }
    if errors:
        stages.append({"key": "vm", "label": "Execute", "status": "skipped", "ms": 0})
        result["stages"] = stages
        result["stats"] = {"tokens": len(tokens) - 1, "errors": len(errors), "warnings": len(fe.warnings)}
        return result

    t0 = time.perf_counter()
    exe = None
    if program is not None:
        from .interp import run_program
        exe = run_program(program, source)
    if exe is None or (exe["halted"] == "error" and ("not available" in (exe["error"] or "") or "unsupported" in (exe["error"] or ""))):
        native = G.native_run(source)
        if native is not None:
            exe = native
        elif exe is None:
            exe = {"language": "c", "output": [], "raw_output": "", "vars": {}, "steps": 0, "halted": "error", "trace": [],
                   "trace_truncated": False, "exit_code": 0,
                   "error": "gcc accepts this program, but the built-in interpreter cannot run it (it uses a construct outside its subset)."}
    stages.append({"key": "vm", "label": "Execute", "status": "error" if exe["halted"] == "error" else "ok", "ms": _ms(t0)})
    result["execution"] = exe
    result["stages"] = stages
    result["stats"] = {"tokens": len(tokens) - 1, "errors": 0, "warnings": len(fe.warnings),
                       "scopes": len(sem.scopes) if sem else 0, "symbols": len(sem.symbols) if sem else 0}
    return result
