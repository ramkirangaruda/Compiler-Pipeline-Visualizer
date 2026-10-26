"""The C driver: tokenize -> parse -> analyze (-> interpret).

`run_frontend` is the part the repair validator re-runs for every candidate fix;
`compile_source` produces the JSON the Studio renders, in the same shape as MiniC's."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from pycparser import c_ast as C

from minic.tokens import Diagnostic, Token

from .astjson import to_tree
from .lexer import RESERVED, lex
from .parser import parse
from .semantic import CSemantic, analyze


@dataclass
class CFrontend:
    source: str
    tokens: list[Token]
    lex_errors: list[Diagnostic]
    directives: list
    program: Optional[C.FileAST]
    parse_error: Optional[Diagnostic]
    sem: Optional[CSemantic]
    lang: str = "c"
    keywords: tuple = field(default=RESERVED)

    @property
    def errors(self) -> list[Diagnostic]:
        out = list(self.lex_errors)
        if self.parse_error:
            out.append(self.parse_error)
        if self.sem:
            out.extend(self.sem.errors)
        return out

    @property
    def warnings(self) -> list[Diagnostic]:
        return list(self.sem.warnings) if self.sem else []

    def rerun(self, source: str) -> "CFrontend":
        return run_frontend(source)


def run_frontend(source: str) -> CFrontend:
    tokens, lex_errors, directives, clean = lex(source)
    included = {d.header for d in directives if d.name == "include" and d.header}
    program, perr, _ = parse(source, clean, tokens, included)
    sem = analyze(source, tokens, directives, program) if program is not None else None
    return CFrontend(source, tokens, lex_errors, directives, program, perr, sem)


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 2)


def compile_source(source: str, **_ignored) -> dict:
    stages = []
    t0 = time.perf_counter()
    tokens, lex_errors, directives, clean = lex(source)
    stages.append({"key": "lexer", "label": "Lexer", "status": "error" if lex_errors else "ok", "ms": _ms(t0)})

    t0 = time.perf_counter()
    included = {d.header for d in directives if d.name == "include" and d.header}
    program, perr, _ = parse(source, clean, tokens, included)
    stages.append({"key": "parser", "label": "Parser", "status": "error" if perr else "ok", "ms": _ms(t0)})

    sem = None
    if program is not None:
        t0 = time.perf_counter()
        sem = analyze(source, tokens, directives, program)
        stages.append({"key": "semantic", "label": "Semantic", "status": "error" if sem.errors else "ok", "ms": _ms(t0)})
    else:
        stages.append({"key": "semantic", "label": "Semantic", "status": "skipped", "ms": 0})

    fe = CFrontend(source, tokens, lex_errors, directives, program, perr, sem)
    errors = fe.errors
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
    }
    if errors:
        stages.append({"key": "vm", "label": "Execute", "status": "skipped", "ms": 0})
        result["stages"] = stages
        result["stats"] = {"tokens": len(tokens) - 1, "errors": len(errors), "warnings": len(fe.warnings)}
        return result

    from .interp import run_program
    t0 = time.perf_counter()
    exe = run_program(program, source)
    stages.append({"key": "vm", "label": "Execute", "status": "error" if exe["halted"] == "error" else "ok", "ms": _ms(t0)})
    result["execution"] = exe
    result["stages"] = stages
    result["stats"] = {"tokens": len(tokens) - 1, "errors": 0, "warnings": len(fe.warnings), "scopes": len(sem.scopes),
                       "symbols": len(sem.symbols)}
    return result
