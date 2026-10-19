"""Abstract syntax tree for MiniC. Every node records its source span so that
later phases (semantic analysis, repair generation) can patch the source text."""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Optional


@dataclass
class Node:
    line: int = 0
    col: int = 0
    start: int = 0
    end: int = 0

    def to_dict(self) -> dict:
        out: dict[str, Any] = {"node": type(self).__name__, "line": self.line, "start": self.start, "end": self.end}
        for f in fields(self):
            if f.name in ("line", "col", "start", "end") or f.name.startswith("_"):
                continue
            out[f.name] = _ser(getattr(self, f.name))
        return out


def _ser(v: Any) -> Any:
    if isinstance(v, Node):
        return v.to_dict()
    if isinstance(v, list):
        return [_ser(x) for x in v]
    return v


@dataclass(kw_only=True)
class Expr(Node):
    ty: str = ""  # filled in by the semantic analyzer


@dataclass(kw_only=True)
class Literal(Expr):
    kind: str = "INT"  # INT FLOAT STRING BOOL
    value: str = ""


@dataclass(kw_only=True)
class Ident(Expr):
    name: str = ""
    uid: str = ""  # unique (scope-resolved) variable name, set by semantic analysis


@dataclass(kw_only=True)
class Unary(Expr):
    op: str = ""
    operand: Optional[Expr] = None


@dataclass(kw_only=True)
class Binary(Expr):
    op: str = ""
    left: Optional[Expr] = None
    right: Optional[Expr] = None


@dataclass(kw_only=True)
class VarDecl(Node):
    vtype: str = "int"
    name: str = ""
    init: Optional[Expr] = None
    type_start: int = 0
    type_end: int = 0
    name_start: int = 0
    name_end: int = 0
    uid: str = ""


@dataclass(kw_only=True)
class Assign(Node):
    name: str = ""
    value: Optional[Expr] = None
    name_start: int = 0
    name_end: int = 0
    uid: str = ""


@dataclass(kw_only=True)
class Print(Node):
    value: Optional[Expr] = None


@dataclass(kw_only=True)
class Block(Node):
    body: list = field(default_factory=list)


@dataclass(kw_only=True)
class If(Node):
    cond: Optional[Expr] = None
    then: Optional[Block] = None
    alt: Optional[Node] = None  # Block or If (else-if chain)


@dataclass(kw_only=True)
class While(Node):
    cond: Optional[Expr] = None
    body: Optional[Block] = None


@dataclass(kw_only=True)
class Program(Node):
    body: list = field(default_factory=list)
