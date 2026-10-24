"""Parsing real C with pycparser, plus the facts the ML layer needs.

pycparser is an LALR parser. When it fails we read its state tables to learn *which
tokens it would have accepted* - the C equivalent of the expected-token set the MiniC
recursive-descent parser reports - and we record the grammar symbols on its stack
(what construct it was in the middle of).
"""
from __future__ import annotations

import re
import threading

from pycparser import c_parser
from pycparser.plyparser import ParseError

from minic.tokens import Diagnostic, Token

from .prelude import build_prelude

_SYMBOL = {
    "SEMI": ";", "COMMA": ",", "LPAREN": "(", "RPAREN": ")", "LBRACE": "{", "RBRACE": "}", "LBRACKET": "[",
    "RBRACKET": "]", "EQUALS": "=", "COLON": ":",
}
DELIMS = [";", ",", "(", ")", "{", "}", "[", "]", "=", ":"]


class _DiagParser(c_parser.CParser):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.err = None

    def p_error(self, p):
        try:
            state = self.cparser.statestack[-1]
            expected = sorted(self.cparser.action.get(state, {}).keys())
            stack = [getattr(s, "type", None) for s in self.cparser.symstack[-4:]]
        except Exception:  # pragma: no cover - defensive: never let diagnostics hide the real error
            expected, stack = [], []
        self.err = {"tok": None if p is None else (p.type, p.value, p.lineno, p.lexpos), "expected": expected, "stack": stack}
        super().p_error(p)


_LOCK = threading.Lock()
_PARSER: _DiagParser | None = None


def _parser() -> _DiagParser:
    global _PARSER
    if _PARSER is None:
        _PARSER = _DiagParser()
    return _PARSER


def parse(source: str, clean: str, tokens: list[Token], included: set[str]):
    """-> (FileAST | None, Diagnostic | None, prelude_length)"""
    prelude = build_prelude(included)
    text = prelude + clean
    base = len(prelude)
    with _LOCK:
        parser = _parser()
        parser.err = None
        try:
            ast = parser.parse(text, filename="<lib>")
            return ast, None, base
        except ParseError as e:
            diag = _diagnostic(str(e), parser.err, tokens, source, base)
            return None, diag, base
        except Exception as e:  # pragma: no cover - pycparser internal failure on odd input
            last = tokens[-1]
            return None, Diagnostic("syntax", "E_UNEXPECTED_EOF", f"Syntax error: could not parse the program ({type(e).__name__})",
                                    last.line, last.col, last.start, max(last.end, last.start + 1),
                                    extra=_extra(len(tokens) - 1, tokens, [], "internal", [], 0)), base


def _extra(idx: int, tokens: list[Token], expected: list[str], ctx: str, stack: list, n_expected: int, found_type: str = "") -> dict:
    found = tokens[idx]
    prev = tokens[idx - 1] if idx > 0 else None
    return {
        "expected": expected,
        "n_expected": n_expected,
        "expects_ident": False,
        "ctx": ctx,
        "stack": stack,
        "found_index": idx,
        "found": found.cls,
        "found_value": found.value,
        "found_type": found_type,
        "prev_end": prev.end if prev else 0,
        "prev_line": prev.line if prev else 1,
    }


def _context(stack: list[str]) -> str:
    """Name of what the parser was in the middle of: its two most recent grammar symbols."""
    names = [s for s in stack if s and s != "$end"][-2:]
    return ">".join(names) if names else "start"


def _diagnostic(message: str, err: dict | None, tokens: list[Token], source: str, base: int) -> Diagnostic:
    if not err:  # pycparser's own semantic complaint (e.g. a typedef redefinition)
        m = re.match(r".*?:(\d+):(\d+): (.*)", message)
        line = int(m.group(1)) if m else 1
        tok = next((t for t in tokens if t.line == line), tokens[-1])
        idx = tokens.index(tok)
        ex = _extra(idx, tokens, [], "declaration", [], 0)
        return Diagnostic("syntax", "E_UNEXPECTED_TOKEN", f"Syntax error: {m.group(3) if m else message} (line {tok.line})",
                          tok.line, tok.col, tok.start, max(tok.end, tok.start + 1), extra=ex)

    expected_syms = {_SYMBOL[t] for t in err["expected"] if t in _SYMBOL}
    delims = [d for d in DELIMS if d in expected_syms]
    ctx = _context(err["stack"])
    if err["tok"] is None:
        idx = len(tokens) - 1
        tok = tokens[idx]
        ex = _extra(idx, tokens, delims, ctx, err["stack"], len(err["expected"]))
        ex["expects_ident"] = "ID" in err["expected"]
        hint = f"; expected {' or '.join(repr(d) for d in delims[:3])}" if delims else ""
        return Diagnostic("syntax", "E_UNEXPECTED_EOF", f"Syntax error: unexpected end of file{hint}",
                          tok.line, tok.col, tok.start, max(tok.end, tok.start + 1), extra=ex)

    ttype, value, _line, lexpos = err["tok"]
    off = lexpos - base
    idx = next((i for i, t in enumerate(tokens) if t.start >= off), len(tokens) - 1)
    tok = tokens[idx]
    ex = _extra(idx, tokens, delims, ctx, err["stack"], len(err["expected"]), ttype)
    ex["expects_ident"] = "ID" in err["expected"]
    code = "E_EXPECTED_TOKEN" if delims else "E_UNEXPECTED_TOKEN"
    if delims and len(delims) <= 3:
        msg = f"Syntax error: expected {' or '.join(repr(d) for d in delims)} before '{tok.value}' on line {tok.line}"
    else:
        msg = f"Syntax error: unexpected '{tok.value}' on line {tok.line}"
    return Diagnostic("syntax", code, msg, tok.line, tok.col, tok.start, max(tok.end, tok.start + 1), extra=ex)
