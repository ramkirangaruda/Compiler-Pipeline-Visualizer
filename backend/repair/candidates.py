"""Repair-candidate generation. For a predicted cause (label) this module
proposes concrete source edits. Candidates are *proposals only* - the
validator re-compiles each one before it is ever shown as a fix."""
from __future__ import annotations

import re
from dataclasses import dataclass

from minic.pipeline import Frontend
from minic.tokens import ALL_RESERVED, Diagnostic
from minic.util import edit_distance, similarity

DEFAULTS = {"int": "0", "float": "0.0", "bool": "false", "string": '""'}


@dataclass
class Edit:
    start: int
    end: int
    text: str

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "text": self.text}


def apply_edits(source: str, edits: list[Edit]) -> str:
    ordered = sorted(edits, key=lambda e: (e.start, e.end))
    for a, b in zip(ordered, ordered[1:]):
        if a.end > b.start:
            raise ValueError("overlapping edits")
    for e in reversed(ordered):
        source = source[: e.start] + e.text + source[e.end :]
    return source


# ----------------------------------------------------------------- helpers
def line_start(src: str, off: int) -> int:
    return src.rfind("\n", 0, off) + 1


def line_end(src: str, off: int) -> int:
    j = src.find("\n", off)
    return len(src) if j < 0 else j


def indent_str(src: str, off: int) -> str:
    m = re.match(r"[ \t]*", src[line_start(src, off) :])
    return m.group(0) if m else ""


def stmt_removal_span(src: str, s: int, e: int) -> tuple[int, int]:
    """Span to delete so a whole-line statement vanishes cleanly."""
    ls, le = line_start(src, s), line_end(src, e)
    if src[ls:s].strip() == "" and src[e:le].strip() == "":
        return ls, min(le + 1, len(src))
    return s, e


def make(label: str, title: str, desc: str, edits: list[Edit], score: float) -> dict:
    return {"label": label, "title": title, "description": desc, "edits": edits, "local_score": round(score, 3)}


def _short(text: str, n: int = 24) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "…"


# -------------------------------------------------------------- syntax fixes
def gen_semicolon(d: Diagnostic, fe: Frontend) -> list[dict]:
    idx = d.extra.get("found_index", 0)
    if d.stage != "syntax" or idx == 0:
        return []
    prev = fe.tokens[idx - 1]
    found = fe.tokens[idx]
    return [
        make(
            "MISSING_SEMICOLON",
            f"Insert ';' after `{_short(prev.value)}`",
            f"The statement ending at line {prev.line} is not terminated before `{_short(found.value) or 'end of file'}`.",
            [Edit(prev.end, prev.end, ";")],
            0.97,
        )
    ]


def gen_rparen(d: Diagnostic, fe: Frontend) -> list[dict]:
    idx = d.extra.get("found_index", 0)
    if d.stage != "syntax" or idx == 0:
        return []
    prev = fe.tokens[idx - 1]
    return [
        make(
            "MISSING_RPAREN",
            f"Insert ')' after `{_short(prev.value)}`",
            f"A '(' opened before line {prev.line} is never closed.",
            [Edit(prev.end, prev.end, ")")],
            0.95,
        )
    ]


_OPERAND = ("IDENT", "INT", "FLOAT", "STRING", "BOOL")


def gen_lparen(d: Diagnostic, fe: Frontend) -> list[dict]:
    idx = d.extra.get("found_index", 0)
    if d.stage != "syntax":
        return []
    toks = fe.tokens
    found = toks[idx]
    pre = []
    prev = toks[idx - 1] if idx > 0 else None
    if prev is not None and prev.kind == "IDENT":
        # `print(x)` with the '(' deleted lexes as one identifier: `printx)`
        for kw in ("print", "while", "if"):
            if prev.value.startswith(kw) and len(prev.value) > len(kw):
                pos = prev.start + len(kw)
                pre.append(make("MISSING_LPAREN", f"Split `{prev.value}` into `{kw}(`",
                                f"`{prev.value}` is the keyword `{kw}` fused with its argument - the '(' is missing.",
                                [Edit(pos, pos, "(")], 0.97))
                break
    if found.value != ")":
        return pre + [
            make(
                "MISSING_LPAREN",
                f"Insert '(' before `{_short(found.value)}`",
                f"The condition starting at line {found.line} is missing its opening '('.",
                [Edit(found.start, found.start, "(")],
                0.95,
            )
        ]
    # A stray ')' closes a group that was never opened: try each operand start
    # in the current statement as the place the '(' belongs.
    starts = []
    j = idx - 1
    while j >= 0:
        t = toks[j]
        if t.kind == "KEYWORD" or (t.kind == "PUNCT" and t.value in ";{}"):
            break
        prev = toks[j - 1] if j > 0 else None
        prev_is_operand_end = prev is not None and (prev.kind in _OPERAND or (prev.kind == "PUNCT" and prev.value == ")"))
        if t.kind in _OPERAND and not prev_is_operand_end:
            starts.append(j)
        j -= 1
    starts.reverse()  # leftmost first
    out = []
    for rank, j in enumerate(starts[:4]):
        t = toks[j]
        after_mul = j > 0 and toks[j - 1].value in ("*", "/", "%")
        out.append(
            make("MISSING_LPAREN", f"Insert '(' before `{_short(t.value)}`",
                 f"The ')' on line {found.line} has no matching '('; the group is assumed to start here.",
                 [Edit(t.start, t.start, "(")], 0.85 - 0.08 * rank + (0.05 if after_mul else 0))
    )
    return pre + out


def gen_lbrace(d: Diagnostic, fe: Frontend) -> list[dict]:
    idx = d.extra.get("found_index", 0)
    if d.stage != "syntax" or idx == 0:
        return []
    prev = fe.tokens[idx - 1]
    return [
        make(
            "MISSING_LBRACE",
            f"Insert '{{' after `{_short(prev.value)}`",
            f"The block after `{_short(prev.value)}` (line {prev.line}) is missing its opening brace.",
            [Edit(prev.end, prev.end, " {")],
            0.95,
        )
    ]


def gen_rbrace(d: Diagnostic, fe: Frontend) -> list[dict]:
    if d.stage != "syntax":
        return []
    toks, src = fe.tokens, fe.source
    idx = d.extra.get("found_index", len(toks) - 1)
    stack = []
    for t in toks[:idx]:
        if t.kind == "PUNCT" and t.value == "{":
            stack.append(t)
        elif t.kind == "PUNCT" and t.value == "}" and stack:
            stack.pop()
    if not stack:
        return []
    opener = stack[-1]
    base = indent_str(src, opener.start)
    width = len(base.replace("\t", "    "))
    found = toks[idx]

    out = []
    # 1) indentation heuristic: the block ends where indentation falls back
    off = line_end(src, opener.start) + 1
    pos = None
    while off < len(src):
        end = line_end(src, off)
        text = src[off:end]
        if text.strip():
            lead = len(re.match(r"[ \t]*", text).group(0).replace("\t", "    "))
            if lead <= width:
                pos = off
                break
        off = end + 1
    eof_edit = Edit(len(src), len(src), (base + "}\n") if src.endswith("\n") else ("\n" + base + "}"))
    if pos is not None:
        indent_edit = Edit(pos, pos, base + "}\n")
    else:
        indent_edit = eof_edit
    where = f"block opened at line {opener.line}"
    is_else = found.kind == "KEYWORD" and found.value == "else"
    out.append(make("MISSING_RBRACE", f"Insert '}}' to close the {where}",
                    "Closed where the indentation falls back to the block's level.", [indent_edit], 0.7 if is_else else 0.92))
    if found.kind != "EOF":
        out.append(make("MISSING_RBRACE", f"Insert '}}' before `{_short(found.value)}`",
                        "Closed immediately before the token the parser choked on.", [Edit(found.start, found.start, "} ")],
                        0.96 if is_else else 0.5))
    if eof_edit.start != indent_edit.start or eof_edit.text != indent_edit.text:
        out.append(make("MISSING_RBRACE", "Insert '}' at the end of the file",
                        "Closed at end of file.", [eof_edit], 0.4))
    return out


def gen_keyword(d: Diagnostic, fe: Frontend) -> list[dict]:
    idx = d.extra.get("found_index", 0)
    if d.stage != "syntax" or idx == 0:
        return []
    bad = fe.tokens[idx - 1]
    if bad.kind != "IDENT":
        return []
    found = fe.tokens[idx]
    out = []
    for kw in ALL_RESERVED:
        dist = edit_distance(bad.value, kw)
        if dist > 3:
            continue
        bonus = 0.0
        if found.value == "(" and kw in ("if", "while", "print"):
            bonus = 0.15
        elif found.kind == "IDENT" and kw in ("int", "float", "bool", "string"):
            bonus = 0.15
        elif found.value == "{" and kw == "else":
            bonus = 0.15
        score = min(1.0, max(0.05, similarity(bad.value, kw) + bonus))
        out.append(
            make("MISSPELLED_KEYWORD", f"Replace `{bad.value}` with `{kw}`",
                 f"`{bad.value}` is {dist} edit(s) away from the keyword `{kw}`.", [Edit(bad.start, bad.end, kw)], score)
        )
    out.sort(key=lambda c: -c["local_score"])
    return out[:3]


def gen_assign_eq(d: Diagnostic, fe: Frontend) -> list[dict]:
    idx = d.extra.get("found_index", 0)
    if d.stage != "syntax":
        return []
    found = fe.tokens[idx]
    if found.value == "=":
        return [make("ASSIGN_EQ_CONFUSION", "Replace '=' with '=='",
                     "'=' assigns a value; use '==' to compare in a condition.", [Edit(found.start, found.end, "==")], 0.95)]
    if found.value == "==":
        return [make("ASSIGN_EQ_CONFUSION", "Replace '==' with '='",
                     "'==' compares values; use '=' to assign.", [Edit(found.start, found.end, "=")], 0.95)]
    return []


# ------------------------------------------------------------ semantic fixes
def gen_typo(d: Diagnostic, fe: Frontend) -> list[dict]:
    if d.code != "E_UNDECLARED":
        return []
    name = d.extra["name"]
    out = []
    for cand, dist in d.extra["visible"][:3]:
        out.append(
            make("TYPO_IDENTIFIER", f"Rename `{name}` to `{cand}`",
                 f"`{cand}` is in scope and {dist} edit(s) away from `{name}`.",
                 [Edit(d.start, d.end, cand)], similarity(name, cand))
        )
    return out


def _decl_text(ty: str, name: str) -> str:
    return f"{ty} {name} = {DEFAULTS[ty]};"


def gen_missing_decl(d: Diagnostic, fe: Frontend) -> list[dict]:
    if d.code != "E_UNDECLARED":
        return []
    ex, src, name = d.extra, fe.source, d.extra["name"]
    ty = ex.get("hint_type") or "int"
    out, seen = [], set()

    def add(ty_, anchor, score, why):
        pos = line_start(src, anchor)
        key = (pos, ty_)
        if key in seen:
            return
        seen.add(key)
        text = indent_str(src, anchor) + _decl_text(ty_, name) + "\n"
        out.append(make("MISSING_DECLARATION", f"Declare `{_decl_text(ty_, name)}`", why, [Edit(pos, pos, text)], score))

    add(ty, ex["top_stmt_start"], 0.9, f"Declared at the top level so every later use of `{name}` can see it (type inferred from usage: {ty}).")
    add(ty, ex["use_stmt_start"], 0.6, "Declared immediately before the statement that uses it.")
    if ty in ("int", "float"):
        add("float" if ty == "int" else "int", ex["top_stmt_start"], 0.35, "Alternative numeric type.")
    return out


def gen_use_before_decl(d: Diagnostic, fe: Frontend) -> list[dict]:
    ex = d.extra
    if d.code != "E_UNDECLARED" or not ex.get("later_decl"):
        return []
    src, ld, name = fe.source, ex["later_decl"], d.extra["name"]
    anchor = ex["top_stmt_start"] if ld["scope_id"] == 0 else ex["use_stmt_start"]
    pos = line_start(src, anchor)
    text = src[ld["stmt_start"] : ld["stmt_end"]]
    ds, de = stmt_removal_span(src, ld["stmt_start"], ld["stmt_end"])
    if ds <= pos < de:
        return []
    return [
        make("USE_BEFORE_DECLARATION", f"Move the declaration of `{name}` above its first use",
             f"`{name}` is declared later in the same scope; the declaration is moved before line {d.line}.",
             [Edit(pos, pos, indent_str(src, anchor) + text + "\n"), Edit(ds, de, "")], 0.9)
    ]


def gen_out_of_scope(d: Diagnostic, fe: Frontend) -> list[dict]:
    ex = d.extra
    if d.code != "E_UNDECLARED" or not ex.get("closed_decl") or fe.sem is None:
        return []
    scopes = fe.sem.scopes
    decl, name, src = ex["closed_decl"], ex["name"], fe.source
    path, s = [], decl["scope_id"]
    while s is not None:
        path.append(s)
        s = scopes[s].parent
    use_stack = set(ex["use_stack"])
    nca = next((i for i, sc in enumerate(path) if sc in use_stack), None)
    if not nca:
        return []
    owner = scopes[path[nca - 1]].owner_start
    pos = line_start(src, owner)
    ind = indent_str(src, owner)
    ty = decl["type"]
    stmt = src[decl["stmt_start"] : decl["stmt_end"]]
    ds, de = stmt_removal_span(src, decl["stmt_start"], decl["stmt_end"])
    out = []
    if "=" in stmt:
        out.append(
            make("OUT_OF_SCOPE_USE", f"Hoist `{name}` into the enclosing scope",
                 f"Declare `{name}` before the block that currently owns it, and turn the inner declaration into an assignment.",
                 [Edit(pos, pos, ind + _decl_text(ty, name) + "\n"), Edit(decl["type_start"], decl["name_start"], "")], 0.9)
        )
    out.append(
        make("OUT_OF_SCOPE_USE", f"Move the whole declaration of `{name}` out of its block",
             "The full declaration (with initialiser) is moved in front of the block.",
             [Edit(pos, pos, ind + stmt + "\n"), Edit(ds, de, "")], 0.55)
    )
    return out


def gen_type_mismatch(d: Diagnostic, fe: Frontend) -> list[dict]:
    ex, src = d.extra, fe.source
    out = []
    if d.code == "E_TYPE_MISMATCH":
        tgt, val = ex["target_type"], ex["expr_type"]
        if val in DEFAULTS:
            out.append(
                make("TYPE_MISMATCH", f"Change the declared type of `{ex['name']}` to `{val}`",
                     f"The value has type `{val}`; the variable was declared `{tgt}`.",
                     [Edit(ex["type_start"], ex["type_end"], val)], 0.85)
            )
        out.append(
            make("TYPE_MISMATCH", f"Replace the value with a `{tgt}` default ({DEFAULTS[tgt]})",
                 f"Substitute a literal of the declared type `{tgt}`.",
                 [Edit(ex["expr_start"], ex["expr_end"], DEFAULTS[tgt])], 0.4)
        )
    elif d.code == "E_BAD_CONDITION":
        ct = ex["cond_type"]
        txt = src[ex["expr_start"] : ex["expr_end"]]
        zero = '""' if ct == "string" else ("0.0" if ct == "float" else "0")
        out.append(
            make("TYPE_MISMATCH", f"Compare against {zero}: `{_short(txt)} != {zero}`",
                 f"Conditions must be `bool`; `{ct}` is turned into a comparison.",
                 [Edit(ex["expr_start"], ex["expr_end"], f"{txt} != {zero}")], 0.8)
        )
    return out


# -------------------------------------------------------------- rule fixes
def gen_rules(d: Diagnostic, fe: Frontend) -> list[dict]:
    src = fe.source
    if d.code == "E_UNEXPECTED_CHAR":
        return [make("RULE_BASED", f"Delete the stray character {d.extra['char']!r}",
                     "Characters outside the language alphabet are removed.", [Edit(d.start, d.end, "")], 0.8)]
    if d.code == "E_UNTERMINATED_STRING":
        pos = d.extra["line_end"]
        while pos > d.start and src[pos - 1] in " \t\r;)":
            pos -= 1
        return [make("RULE_BASED", "Close the string literal with '\"'",
                     "A string literal must end with a closing quote on the same line.", [Edit(pos, pos, '"')], 0.8)]
    if d.code == "E_REDECLARED":
        return [make("RULE_BASED", f"Turn the redeclaration of `{d.extra['name']}` into an assignment",
                     "A name can be declared only once per scope.", [Edit(d.extra["type_start"], _name_start(src, d), "")], 0.7)]
    return []


def _name_start(src: str, d: Diagnostic) -> int:
    m = re.compile(r"\s+").match(src, d.extra["type_end"])
    return m.end() if m else d.extra["type_end"]


GENERATORS = {
    "MISSING_SEMICOLON": gen_semicolon,
    "MISSING_RPAREN": gen_rparen,
    "MISSING_LPAREN": gen_lparen,
    "MISSING_LBRACE": gen_lbrace,
    "MISSING_RBRACE": gen_rbrace,
    "MISSPELLED_KEYWORD": gen_keyword,
    "ASSIGN_EQ_CONFUSION": gen_assign_eq,
    "TYPO_IDENTIFIER": gen_typo,
    "MISSING_DECLARATION": gen_missing_decl,
    "USE_BEFORE_DECLARATION": gen_use_before_decl,
    "OUT_OF_SCOPE_USE": gen_out_of_scope,
    "TYPE_MISMATCH": gen_type_mismatch,
}


def generate(label: str, d: Diagnostic, fe: Frontend) -> list[dict]:
    gen = GENERATORS.get(label)
    return gen(d, fe) if gen else []
