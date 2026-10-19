"""Token and diagnostic data types shared by every compiler phase."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

KEYWORDS = ("if", "else", "while", "print")
TYPES = ("int", "float", "bool", "string")
BOOL_LITERALS = ("true", "false")
ALL_RESERVED = KEYWORDS + TYPES


@dataclass
class Token:
    kind: str  # KEYWORD TYPE IDENT INT FLOAT STRING BOOL OP PUNCT EOF
    value: str
    line: int
    col: int
    start: int
    end: int

    @property
    def cls(self) -> str:
        """Coarse token class used as an ML feature: reserved words and
        operators keep their spelling, everything else collapses to its kind."""
        if self.kind in ("KEYWORD", "TYPE", "OP", "PUNCT"):
            return self.value
        return self.kind

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "value": self.value,
            "line": self.line,
            "col": self.col,
            "start": self.start,
            "end": self.end,
        }


@dataclass
class Diagnostic:
    stage: str  # lexical | syntax | semantic
    code: str
    message: str
    line: int
    col: int
    start: int
    end: int
    severity: str = "error"
    # JSON-safe facts gathered by the compiler (expected tokens, parse context,
    # nearest symbols, ...). These become the ML feature inputs.
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "col": self.col,
            "start": self.start,
            "end": self.end,
            "severity": self.severity,
            "extra": self.extra,
        }


def token_cls(tok: Token | None) -> str:
    return tok.cls if tok is not None else "NONE"


JSON = Any
