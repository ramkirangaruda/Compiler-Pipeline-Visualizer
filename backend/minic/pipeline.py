"""Compiler driver: lex -> parse -> semantic analysis -> IR -> optimize -> execute.

`run_frontend` is the cheap part (lex+parse+analyze) that the repair validator
re-runs for every candidate fix; `compile_source` is the full pipeline that
produces the JSON consumed by the web UI."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from . import ast as A
from .cfg import cfg_json
from .lexer import lex
from .optimizer import diff as opt_diff
from .optimizer import optimize
from .parser import parse
from .semantic import SemanticResult, analyze
from .tac import generate
from .tokens import Diagnostic, Token
from .vm import run as vm_run


@dataclass
class Frontend:
    source: str
    tokens: list[Token]
    lex_errors: list[Diagnostic]
    program: Optional[A.Program]
    parse_error: Optional[Diagnostic]
    sem: Optional[SemanticResult]

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


def run_frontend(source: str) -> Frontend:
    tokens, lex_errors = lex(source)
    program, perr = parse(tokens)
    sem = analyze(program) if program is not None else None
    return Frontend(source, tokens, lex_errors, program, perr, sem)


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 2)


def compile_source(source: str, run_optimizer: bool = True) -> dict:
    stages = []
    t0 = time.perf_counter()
    tokens, lex_errors = lex(source)
    stages.append({"key": "lexer", "label": "Lexer", "status": "error" if lex_errors else "ok", "ms": _ms(t0)})

    t0 = time.perf_counter()
    program, perr = parse(tokens)
    stages.append({"key": "parser", "label": "Parser", "status": "error" if perr else "ok", "ms": _ms(t0)})

    sem: Optional[SemanticResult] = None
    if program is not None:
        t0 = time.perf_counter()
        sem = analyze(program)
        stages.append({"key": "semantic", "label": "Semantic", "status": "error" if sem.errors else "ok", "ms": _ms(t0)})
    else:
        stages.append({"key": "semantic", "label": "Semantic", "status": "skipped", "ms": 0})

    fe = Frontend(source, tokens, lex_errors, program, perr, sem)
    errors = fe.errors
    result: dict = {
        "ok": not errors,
        "tokens": [t.to_dict() for t in tokens],
        "ast": program.to_dict() if program is not None else None,
        "symbols": sem.table() if sem else None,
        "diagnostics": [d.to_dict() for d in errors],
        "warnings": [d.to_dict() for d in fe.warnings],
        "tac": [],
        "optimized": None,
        "cfg": None,
        "execution": None,
        "verify": None,
    }

    if errors:
        for key, label in (("ir", "IR Gen"), ("optimizer", "Optimizer"), ("vm", "Execute")):
            stages.append({"key": key, "label": label, "status": "skipped", "ms": 0})
        result["stages"] = stages
        result["stats"] = {"tokens": len(tokens) - 1, "errors": len(errors), "warnings": len(fe.warnings)}
        return result

    t0 = time.perf_counter()
    code = generate(program, sem.var_types)
    stages.append({"key": "ir", "label": "IR Gen", "status": "ok", "ms": _ms(t0)})
    result["tac"] = [i.to_dict() for i in code]

    t0 = time.perf_counter()
    opt = optimize(code) if run_optimizer else {"code": code, "report": [], "rounds": 0}
    optimized = opt["code"]
    stages.append({"key": "optimizer", "label": "Optimizer", "status": "ok", "ms": _ms(t0)})
    result["optimized"] = {
        "code": [i.to_dict() for i in optimized],
        "report": opt["report"],
        "rounds": opt["rounds"],
        "diff": opt_diff(code, optimized),
    }
    result["cfg"] = cfg_json(optimized)
    result["cfg_unoptimized"] = cfg_json(code)

    t0 = time.perf_counter()
    exe = vm_run(optimized, sem.var_types)
    stages.append(
        {"key": "vm", "label": "Execute", "status": "error" if exe["halted"] == "error" else "ok", "ms": _ms(t0)}
    )
    result["execution"] = exe
    base = vm_run(code, sem.var_types, trace_limit=0)
    result["verify"] = {
        "match": base["output"] == exe["output"] and base["halted"] == exe["halted"],
        "unoptimized_output": base["output"],
        "optimized_output": exe["output"],
        "unoptimized_steps": base["steps"],
        "optimized_steps": exe["steps"],
    }
    result["stats"] = {
        "tokens": len(tokens) - 1,
        "errors": 0,
        "warnings": len(fe.warnings),
        "tac_before": len(code),
        "tac_after": len(optimized),
        "blocks": len(result["cfg"]["blocks"]),
        "scopes": len(sem.scopes),
        "symbols": len(sem.symbols),
    }
    result["stages"] = stages
    return result
