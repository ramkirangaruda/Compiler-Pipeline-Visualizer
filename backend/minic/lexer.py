"""Lexical analysis: a hand-written scanner whose token classes correspond to
the regular expressions / DFAs documented in docs/ARCHITECTURE.md.

    IDENT   : [A-Za-z_][A-Za-z0-9_]*
    INT     : [0-9]+
    FLOAT   : [0-9]+ '.' [0-9]+
    STRING  : '"' ( [^"\\\n] | '\\' . )* '"'
"""
from __future__ import annotations

from .tokens import BOOL_LITERALS, KEYWORDS, TYPES, Diagnostic, Token

TWO_CHAR_OPS = ("==", "!=", "<=", ">=", "&&", "||")
ONE_CHAR_OPS = "+-*/%=<>!"
PUNCT = "(){};"


def lex(source: str) -> tuple[list[Token], list[Diagnostic]]:
    tokens: list[Token] = []
    errors: list[Diagnostic] = []
    i, line, line_start, n = 0, 1, 0, len(source)

    def col_of(pos: int) -> int:
        return pos - line_start + 1

    while i < n:
        c = source[i]
        if c == "\n":
            line += 1
            i += 1
            line_start = i
            continue
        if c in " \t\r":
            i += 1
            continue
        if c == "/" and source[i + 1 : i + 2] == "/":  # line comment
            while i < n and source[i] != "\n":
                i += 1
            continue

        if c.isdigit():
            j = i
            while j < n and source[j].isdigit():
                j += 1
            kind = "INT"
            if j < n - 1 and source[j] == "." and source[j + 1].isdigit():
                kind = "FLOAT"
                j += 1
                while j < n and source[j].isdigit():
                    j += 1
            tokens.append(Token(kind, source[i:j], line, col_of(i), i, j))
            i = j
            continue

        if c.isalpha() or c == "_":
            j = i
            while j < n and (source[j].isalnum() or source[j] == "_"):
                j += 1
            word = source[i:j]
            if word in KEYWORDS:
                kind = "KEYWORD"
            elif word in TYPES:
                kind = "TYPE"
            elif word in BOOL_LITERALS:
                kind = "BOOL"
            else:
                kind = "IDENT"
            tokens.append(Token(kind, word, line, col_of(i), i, j))
            i = j
            continue

        if c == '"':
            j = i + 1
            closed = False
            while j < n and source[j] != "\n":
                if source[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if source[j] == '"':
                    closed = True
                    j += 1
                    break
                j += 1
            if not closed:
                errors.append(
                    Diagnostic(
                        "lexical", "E_UNTERMINATED_STRING",
                        f"Lexical error: unterminated string literal on line {line}",
                        line, col_of(i), i, j,
                        extra={"quote_start": i, "line_end": j},
                    )
                )
                i = j
                continue
            tokens.append(Token("STRING", source[i:j], line, col_of(i), i, j))
            i = j
            continue

        two = source[i : i + 2]
        if two in TWO_CHAR_OPS:
            tokens.append(Token("OP", two, line, col_of(i), i, i + 2))
            i += 2
            continue
        if c in ONE_CHAR_OPS:
            tokens.append(Token("OP", c, line, col_of(i), i, i + 1))
            i += 1
            continue
        if c in PUNCT:
            tokens.append(Token("PUNCT", c, line, col_of(i), i, i + 1))
            i += 1
            continue

        errors.append(
            Diagnostic(
                "lexical", "E_UNEXPECTED_CHAR",
                f"Lexical error: unexpected character {c!r} on line {line}",
                line, col_of(i), i, i + 1,
                extra={"char": c},
            )
        )
        i += 1

    tokens.append(Token("EOF", "", line, col_of(n), n, n))
    return tokens, errors
