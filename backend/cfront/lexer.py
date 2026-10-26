"""Tokenizer for real C (C99 subset used by teaching programs).

Besides tokens it returns the preprocessor directives it saw and a *cleaned copy of
the source* - same length, same line breaks - in which comments, directives and
illegal characters are blanked out. That copy is what the parser sees, so every
offset in a parser message maps straight back to the user's text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from minic.tokens import Diagnostic, Token

C_KEYWORDS = frozenset({
    "if", "else", "while", "for", "do", "switch", "case", "default", "break", "continue", "return", "goto",
    "sizeof", "struct", "union", "enum", "typedef", "static", "extern", "const", "volatile", "register",
    "auto", "inline", "restrict",
})
C_TYPES = frozenset({"int", "char", "float", "double", "void", "long", "short", "signed", "unsigned", "_Bool"})
RESERVED = tuple(sorted(C_KEYWORDS | C_TYPES))

_OPS3 = ("<<=", ">>=", "...")
_OPS2 = ("->", "++", "--", "<<", ">>", "<=", ">=", "==", "!=", "&&", "||", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=")
_OPS1 = "+-*/%&|^~!<>=?:."
_PUNCT = "(){}[];,"

_NUM = re.compile(
    r"""(?:0[xX][0-9a-fA-F]+|0[bB][01]+|(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)[uUlLfF]*""", re.X)
_IDENT = re.compile(r"[A-Za-z_]\w*")


@dataclass
class Directive:
    name: str          # include, define, ifdef, ...
    text: str          # everything after '#name'
    line: int
    start: int
    end: int
    header: str | None = None   # for #include <x.h> / "x.h"


def lex(source: str):
    """-> (tokens, errors, directives, clean_text)"""
    n = len(source)
    tokens: list[Token] = []
    errors: list[Diagnostic] = []
    directives: list[Directive] = []
    clean = list(source)
    i, line, line_start = 0, 1, 0
    at_line_start = True

    def blank(a: int, b: int) -> None:
        for k in range(a, min(b, n)):
            if clean[k] != "\n":
                clean[k] = " "

    def col(pos: int) -> int:
        return pos - line_start + 1

    while i < n:
        c = source[i]
        if c == "\n":
            line += 1
            i += 1
            line_start = i
            at_line_start = True
            continue
        if c in " \t\r\f\v":
            i += 1
            continue

        # ---- comments
        if c == "/" and source[i + 1 : i + 2] == "/":
            j = source.find("\n", i)
            j = n if j < 0 else j
            blank(i, j)
            i = j
            continue
        if c == "/" and source[i + 1 : i + 2] == "*":
            j = source.find("*/", i + 2)
            if j < 0:
                errors.append(Diagnostic("lexical", "E_UNTERMINATED_COMMENT",
                                         f"Lexical error: unterminated comment starting on line {line}", line, col(i), i, n))
                blank(i, n)
                i = n
                continue
            blank(i, j + 2)
            seg = source[i : j + 2]
            line += seg.count("\n")
            if "\n" in seg:
                line_start = i + seg.rfind("\n") + 1
            i = j + 2
            continue

        # ---- preprocessor directive (only at the start of a line)
        if c == "#" and at_line_start:
            j = i
            while True:
                e = source.find("\n", j)
                e = n if e < 0 else e
                if e > i and source[e - 1] == "\\" and e < n:
                    j = e + 1
                    continue
                break
            text = source[i + 1 : e]
            m = re.match(r"\s*(\w+)\s*(.*)", text, re.S)
            name, rest = (m.group(1), m.group(2).strip()) if m else ("", text.strip())
            header = None
            if name == "include":
                hm = re.match(r'[<"]([^>"]+)[>"]', rest)
                header = hm.group(1) if hm else None
            directives.append(Directive(name, rest, line, i, e, header))
            blank(i, e)
            line += source.count("\n", i, e)
            i = e
            continue

        at_line_start = False

        # ---- identifiers / keywords
        if c.isalpha() or c == "_":
            m = _IDENT.match(source, i)
            word = m.group(0)
            kind = "KEYWORD" if word in C_KEYWORDS else "TYPE" if word in C_TYPES else "IDENT"
            tokens.append(Token(kind, word, line, col(i), i, m.end()))
            i = m.end()
            continue

        # ---- numbers
        if c.isdigit() or (c == "." and source[i + 1 : i + 2].isdigit()):
            m = _NUM.match(source, i)
            text = m.group(0)
            is_float = (not text.lower().startswith(("0x", "0b"))) and (
                "." in text or re.search(r"[eE]", text) or text[-1] in "fF")
            tokens.append(Token("FLOAT" if is_float else "INT", text, line, col(i), i, m.end()))
            i = m.end()
            continue

        # ---- string / char literals
        if c in "\"'":
            j = i + 1
            closed = False
            while j < n and source[j] != "\n":
                if source[j] == "\\" and j + 1 < n and source[j + 1] != "\n":
                    j += 2
                    continue
                if source[j] == c:
                    closed = True
                    j += 1
                    break
                j += 1
            if not closed:
                what = "string" if c == '"' else "character"
                errors.append(Diagnostic(
                    "lexical", "E_UNTERMINATED_STRING" if c == '"' else "E_UNTERMINATED_CHAR",
                    f"Lexical error: unterminated {what} literal on line {line}", line, col(i), i, j,
                    extra={"quote_start": i, "line_end": j, "quote": c}))
                blank(i, j)
                i = j
                continue
            tokens.append(Token("STRING" if c == '"' else "CHAR", source[i:j], line, col(i), i, j))
            i = j
            continue

        # ---- operators / punctuation
        three, two = source[i : i + 3], source[i : i + 2]
        if three in _OPS3:
            tokens.append(Token("OP", three, line, col(i), i, i + 3))
            i += 3
            continue
        if two in _OPS2:
            tokens.append(Token("OP", two, line, col(i), i, i + 2))
            i += 2
            continue
        if c in _OPS1:
            tokens.append(Token("OP", c, line, col(i), i, i + 1))
            i += 1
            continue
        if c in _PUNCT:
            tokens.append(Token("PUNCT", c, line, col(i), i, i + 1))
            i += 1
            continue

        errors.append(Diagnostic("lexical", "E_UNEXPECTED_CHAR", f"Lexical error: unexpected character {c!r} on line {line}",
                                 line, col(i), i, i + 1, extra={"char": c}))
        blank(i, i + 1)
        i += 1

    tokens.append(Token("EOF", "", line, col(n), n, n))
    return tokens, errors, directives, "".join(clean)
