"""Compiler-driven repair candidates for C: the fixes that do not depend on our own front end recognising the error.

Sources of candidates, all of them *proposals* that gcc must accept before they are shown:
  1. the compiler's own fix-its ("did you mean 'count'?", "insert ';'", "include <string.h>")
  2. the right #include for a library function / type used without its header
  3. a repair search around the point where gcc stopped: insert or delete one punctuation token
  4. the common semantic slips gcc names precisely: undeclared name, call before definition, redefinition,
     wrong argument count, assignment to a const, no main(), undefined reference
  5. a clearly labelled last resort: comment out the offending line (never chosen automatically)
"""
from __future__ import annotations

import re

from cfront.headers import HEADER_OF
from minic.util import edit_distance

from .candidates import Edit, indent_str, line_end, line_start, make

TYPE_WORDS = ["int", "char", "float", "double", "long", "short", "unsigned", "signed", "void", "bool", "size_t"]
_NAME_PATTERNS = [
    r"implicit declaration of function '(\w+)'", r"'(\w+)' undeclared", r"unknown type name '(\w+)'",
    r"incompatible implicit declaration of built-in function '(\w+)'", r"'(\w+)' undeclared here",
    r"type of '(\w+)' defaults to", r"'(\w+)' redeclared as different kind of symbol",
]
KEYWORD_WORDS = ["if", "else", "while", "for", "do", "switch", "case", "default", "break", "continue", "return", "goto", "sizeof",
                 "struct", "union", "enum", "typedef", "static", "extern", "const", "volatile", "unsigned", "signed"]
BINARY_OPS = ["+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "=", "&", "|"]


def _gdiag(d, fe):
    g = getattr(fe, "gcc", None)
    if g is None or not g.available or not g.errors:
        return None
    return next((e for e in g.errors if e.line == d.line), g.errors[0])


def _tok_index(fe, off: int) -> int:
    for i, t in enumerate(fe.tokens):
        if t.end > off:
            return i
    return max(0, len(fe.tokens) - 1)


def _short(t: str, n: int = 30) -> str:
    t = t.strip().replace("\n", " ")
    return t if len(t) <= n else t[: n - 1] + "…"


def _include_pos(fe) -> int:
    src, pos = fe.source, 0
    for dr in getattr(fe, "directives", []):
        if dr.name in ("include", "define"):
            pos = max(pos, line_end(src, dr.end) + 1)
    return min(pos, len(src))


def _has_include(fe, header: str) -> bool:
    return any(d.name == "include" and d.header == header for d in getattr(fe, "directives", []))


def _name_in(msg: str):
    for p in _NAME_PATTERNS:
        m = re.search(p, msg)
        if m:
            return m.group(1)
    return None


def _describe(edits: list[Edit], src: str) -> str:
    if len(edits) == 1:
        e = edits[0]
        old = src[e.start:e.end]
        if e.start == e.end:
            return f"Insert `{_short(e.text)}`"
        if not e.text:
            return f"Delete `{_short(old)}`"
        return f"Replace `{_short(old)}` with `{_short(e.text)}`"
    return "Apply the compiler's suggestion (" + ", ".join(_describe([e], src) for e in edits[:3]) + ")"


# ------------------------------------------------------------------- 1. fix-its
def _fixits(g, fe) -> list[dict]:
    out, src = [], fe.source
    groups = [g.fixits] if g.fixits else []
    groups += [n["fixits"] for n in g.notes if n["fixits"]]
    for grp in groups:
        edits = [Edit(s, e, t) for s, e, t in grp]
        text = " ".join(e.text for e in edits)
        label = "MISSING_INCLUDE" if "#include" in text else "GCC_FIXIT"
        out.append(make(label, _describe(edits, src), "This is the compiler's own suggestion for the error.", edits, 0.93))
    return out


# --------------------------------------------------------- 2. headers and typos
def _headers(g, fe, name) -> list[dict]:
    hdr = HEADER_OF.get(name or "")
    if not hdr or _has_include(fe, hdr):
        return []
    pos = _include_pos(fe)
    return [make("MISSING_INCLUDE", f"Add `#include <{hdr}>`", f"`{name}` is declared in <{hdr}>.", [Edit(pos, pos, f"#include <{hdr}>\n")], 0.95)]


def _typos(g, fe, name) -> list[dict]:
    if not name:
        return []
    t = fe.tokens[_tok_index(fe, g.start)]
    if t.value != name:
        t = next((x for x in fe.tokens if x.start <= g.start < x.end or x.start == g.start), t)
    if t.value != name:
        # gcc sometimes points at a neighbouring token (e.g. `main` for a misspelled parameter type): use the named one on that line
        same = sorted((x for x in fe.tokens if x.value == name and abs(x.line - g.line) <= 0), key=lambda x: abs(x.start - g.start))
        if not same:
            return []
        t = same[0]
    is_type = "unknown type name" in g.message
    pool = set(TYPE_WORDS) | ({x.value for x in fe.tokens if x.kind == "IDENT"} | set(HEADER_OF) | set(KEYWORD_WORDS))
    if is_type:
        pool = set(TYPE_WORDS) | {x.value for x in fe.tokens if x.kind == "IDENT"}
    pool.discard(name)
    limit = 1 if len(name) <= 3 else 2
    scored = sorted(((edit_distance(name, c), c) for c in pool), key=lambda x: (x[0], x[1]))
    out = []
    for dist, c in scored[:3]:
        if dist <= limit:
            out.append(make("TYPO_IDENTIFIER", f"Rename `{name}` to `{c}`", f"`{c}` is {dist} edit(s) away from `{name}`.",
                            [Edit(t.start, t.end, c)], 0.8 - 0.1 * dist))
    return out


def _declare(g, fe, name) -> list[dict]:
    """An undeclared variable: declare it just before the statement that uses it."""
    if not name or "implicit declaration" in g.message or "unknown type" in g.message:
        return []
    src = fe.source
    pos, ind = line_start(src, g.start), indent_str(src, g.start)
    return [make("MISSING_DECLARATION", f"Declare `{ty} {name} = {init};`", "Declared in front of the statement that uses it.",
                 [Edit(pos, pos, f"{ind}{ty} {name} = {init};\n")], sc, "before_use")
            for ty, init, sc in (("int", "0", 0.55), ("double", "0.0", 0.35), ("char *", '""', 0.3))]


def _top_level_definition(fe, name):
    """(header_text, start_off) of a top-level function definition `type name(params) {`, if the file has one."""
    toks = fe.tokens
    depth = 0
    for i, t in enumerate(toks):
        if t.value == "{" and t.kind == "PUNCT":
            depth += 1
        elif t.value == "}" and t.kind == "PUNCT":
            depth = max(0, depth - 1)
        elif depth == 0 and t.kind == "IDENT" and t.value == name and i + 1 < len(toks) and toks[i + 1].value == "(":
            j, pd = i + 1, 0
            while j < len(toks):
                pd += (toks[j].value == "(") - (toks[j].value == ")")
                if pd == 0:
                    break
                j += 1
            if j + 1 < len(toks) and toks[j + 1].value == "{":
                k = i
                while k > 0 and toks[k - 1].value not in (";", "}", "{") and toks[k - 1].kind != "EOF":
                    k -= 1
                if k < i:
                    return fe.source[toks[k].start:toks[j].end], toks[k].start
    return None


def _prototype(g, fe, name) -> list[dict]:
    if not name or "implicit declaration of function" not in g.message:
        return []
    found = _top_level_definition(fe, name)
    if not found:
        return []
    header, defn = found
    if defn < g.start:
        return []
    pos = _include_pos(fe)
    return [make("MISSING_DECLARATION", f"Declare `{_short(header, 40)};` before its first use",
                 f"`{name}` is defined later in the file; a prototype lets earlier code call it.",
                 [Edit(pos, pos, header + ";\n")], 0.92)]


# ------------------------------------------------------------- 3. repair search
_EXPECT = re.compile(r"expected ((?:'[^']+'(?:, | or )?)+)")


def _search(g, fe) -> list[dict]:
    src, toks = fe.source, fe.tokens
    i = _tok_index(fe, g.start)
    tok = toks[i]
    prev = toks[i - 1] if i > 0 else None
    out = []

    def add(edits, title, desc, score, label="SEARCH_FIX"):
        out.append(make(label, title, desc, edits, score))

    msg = g.message
    m = _EXPECT.search(msg)
    wanted = re.findall(r"'([^']+)'", m.group(1)) if m else []
    if "at end of input" in msg or tok.kind == "EOF":
        for w in wanted or ["}"]:
            if w in ("}", ")", "]", ";", "{"):
                add([Edit(len(src), len(src), ("\n" if not src.endswith("\n") else "") + w + "\n")], f"Insert `{w}` at the end of the file",
                    "The file ends while something is still open.", 0.8)
        if not wanted:
            add([Edit(len(src), len(src), ("\n" if not src.endswith("\n") else "") + "}\n")], "Insert `}` at the end of the file",
                "The file ends while a block is still open.", 0.75)
    if prev is not None:
        for w in wanted:
            if w in (";", ")", "]", "}", "{", "(", ",", ":", "="):
                add([Edit(prev.end, prev.end, w)], f"Insert `{w}` after `{_short(prev.value)}`", f"gcc expected `{w}` here.", 0.85)
    for w in wanted:
        if w in (";", ")", "]", "}", "{", "(", ",", ":", "="):
            add([Edit(tok.start, tok.start, w + (" " if w in ("{", "(", "=") else ""))], f"Insert `{w}` before `{_short(tok.value)}`", f"gcc expected `{w}` here.", 0.6)
    if "stray" in msg:
        add([Edit(g.start, g.start + 1, "")], "Delete the stray character", "That character is not valid C here.", 0.9)
    m2 = re.match(r"missing terminating (.) character", msg)
    if m2:
        q = m2.group(1)
        pos = line_end(src, g.start)
        while pos > g.start and src[pos - 1] in " \t\r;),":
            pos -= 1
        add([Edit(pos, pos, q)], f"Close the literal with {q}", "A string or character literal must end on the same line.", 0.85)
    if "unterminated comment" in msg:
        add([Edit(len(src), len(src), "\n*/\n")], "Close the comment with `*/`", "A /* comment was never closed.", 0.85)
    if "expected expression" in msg:
        add([Edit(tok.start, tok.start, "0")], "Insert a value `0`", "An expression is missing here.", 0.4)
    if "'else' without a previous 'if'" in msg:
        add([Edit(tok.start, tok.end, "")], "Delete the stray `else`", "There is no `if` for this `else`.", 0.4)
    # generic single-token edits around the failure point (gcc will tell us which one works)
    base = 0.3
    if prev is not None:
        for w in (";", ")", "}", "]", ",", "{", "("):
            add([Edit(prev.end, prev.end, w)], f"Insert `{w}` after `{_short(prev.value)}`", "Tried because the parser stopped here.", base)
        for w in ("=", "+", "-", "*", "==", "<", ">", "&&", "||"):
            add([Edit(prev.end, prev.end, " " + w)], f"Insert `{w}` after `{_short(prev.value)}`", "An operator may be missing here.", 0.2)
        if prev.kind == "PUNCT" or prev.value in ("else", "return"):
            pass
        add([Edit(prev.start, prev.end, "")], f"Delete `{_short(prev.value)}`", "Tried because the parser stopped after it.", 0.2)
    if tok.kind != "EOF":
        add([Edit(tok.start, tok.end, "")], f"Delete `{_short(tok.value)}`", "Tried because the parser stopped on it.", 0.25)
        if tok.value in (",", ")", "]", ":"):
            add([Edit(tok.start, tok.end, ";")], f"Replace `{tok.value}` with `;`", "Tried because the parser stopped on it.", 0.25)
    return out


# --------------------------------------------------------------- 4. semantic slips
def _redefinition(g, fe) -> list[dict]:
    m = re.search(r"(?:redefinition of|conflicting types for|redeclaration of) '(\w+)'", g.message)
    if not m:
        return []
    src, name = fe.source, m.group(1)
    toks = fe.tokens
    i = _tok_index(fe, g.start)
    j = next((k for k in range(max(0, i - 2), min(len(toks), i + 3)) if toks[k].value == name), None)
    if j is None:
        return []
    k = j
    while k > 0 and toks[k - 1].kind == "TYPE" or (k > 0 and toks[k - 1].value in ("*", "const", "unsigned", "static")):
        k -= 1
    out = []
    after = toks[j + 1] if j + 1 < len(toks) else None
    if after is not None and after.value == "=" and k < j:
        out.append(make("SEARCH_FIX", f"Turn the redeclaration of `{name}` into an assignment", "A name can be declared only once.",
                        [Edit(toks[k].start, toks[j].start, "")], 0.75))
    if after is not None and after.value in (";", "=", ","):
        e = j
        while e < len(toks) and toks[e].value != ";":
            e += 1
        if e < len(toks):
            s0, e0 = line_start(src, toks[k].start), line_end(src, toks[e].end) + 1
            out.append(make("SEARCH_FIX", f"Delete the repeated declaration of `{name}`", "A name can be declared only once.",
                            [Edit(s0, min(e0, len(src)), "")], 0.55))
    out.append(make("SEARCH_FIX", f"Rename the second `{name}` to `{name}2`", "Give the second one its own name.",
                    [Edit(toks[j].start, toks[j].end, name + "2")], 0.25))
    return out


def _arg_spans(fe, i):
    toks = fe.tokens
    if i + 1 >= len(toks) or toks[i + 1].value != "(":
        return None
    depth, spans, cur, close = 0, [], None, None
    for j in range(i + 1, len(toks)):
        t = toks[j]
        if t.kind == "PUNCT" and t.value in "([{":
            depth += 1
            if depth == 1:
                continue
        elif t.kind == "PUNCT" and t.value in ")]}":
            depth -= 1
            if depth == 0:
                close = j
                break
        if t.value == "," and depth == 1:
            spans.append(cur)
            cur = None
            continue
        cur = [t.start, t.end] if cur is None else [cur[0], t.end]
    if close is None:
        return None
    if cur:
        spans.append(cur)
    return spans, toks[i + 1].end, toks[close].start


def _param_count(fe, name):
    toks = fe.tokens
    for i, t in enumerate(toks):
        if t.kind == "IDENT" and t.value == name and i + 1 < len(toks) and toks[i + 1].value == "(" and (i == 0 or toks[i - 1].kind in ("TYPE", "IDENT") or toks[i - 1].value == "*"):
            a = _arg_spans(fe, i)
            if a is None:
                continue
            close = next((k for k in range(i + 1, len(toks)) if toks[k].start == a[2]), None)
            if close is not None and close + 1 < len(toks) and toks[close + 1].value in ("{", ";"):
                if len(a[0]) == 1 and fe.source[a[0][0][0]:a[0][0][1]] == "void":
                    return 0
                return len(a[0])
    return None


def _argcount(g, fe) -> list[dict]:
    m = re.search(r"too (many|few) arguments to function '(\w+)'", g.message)
    if not m:
        return []
    name = m.group(2)
    want = _param_count(fe, name)
    toks = fe.tokens
    i0 = _tok_index(fe, g.start)
    cands = [k for k, t in enumerate(toks) if t.kind == "IDENT" and t.value == name and k + 1 < len(toks) and toks[k + 1].value == "(" and t.line == g.line]
    if not cands or want is None:
        return []
    i = cands[0]
    spans, lp_end, rp_start = _arg_spans(fe, i)
    if len(spans) > want:
        lo = spans[want - 1][1] if want > 0 else lp_end
        hi = spans[-1][1] if want > 0 else rp_start
        return [make("WRONG_ARG_COUNT", f"Remove the {len(spans) - want} extra argument(s) from the call to `{name}`",
                     f"`{name}` takes {want} argument(s).", [Edit(lo, hi, "")], 0.9)]
    if len(spans) < want:
        fill = ", ".join(["0"] * (want - len(spans)))
        pos = spans[-1][1] if spans else lp_end
        return [make("WRONG_ARG_COUNT", f"Pass the {want - len(spans)} missing argument(s) to `{name}`",
                     f"`{name}` takes {want} argument(s); defaults are added.", [Edit(pos, pos, (", " + fill) if spans else fill)], 0.85)]
    return []


def _const(g, fe) -> list[dict]:
    m = re.search(r"(?:assignment|increment|decrement) of read-only variable '(\w+)'", g.message)
    if not m:
        return []
    name = m.group(1)
    toks = fe.tokens
    for k, t in enumerate(toks):
        if t.value == "const" and any(x.value == name for x in toks[k + 1:k + 5]):
            return [make("SEARCH_FIX", f"Remove `const` from `{name}`", f"`{name}` is read-only, so it cannot be assigned.",
                         [Edit(t.start, min(t.end + 1, len(fe.source)), "")], 0.8)]
    return []


def _prototype_of(fe, name):
    """(return type text, [param texts]) of a top-level prototype `type name(params);`."""
    toks = fe.tokens
    depth = 0
    for i, t in enumerate(toks):
        if t.value == "{" and t.kind == "PUNCT":
            depth += 1
        elif t.value == "}" and t.kind == "PUNCT":
            depth = max(0, depth - 1)
        elif depth == 0 and t.kind == "IDENT" and t.value == name and i > 0 and i + 1 < len(toks) and toks[i + 1].value == "(":
            a = _arg_spans(fe, i)
            if a is None:
                continue
            close = next((k for k in range(i + 1, len(toks)) if toks[k].start == a[2]), None)
            if close is None or close + 1 >= len(toks) or toks[close + 1].value != ";":
                continue
            k = i
            while k > 0 and toks[k - 1].value not in (";", "}", "{"):
                k -= 1
            ret = fe.source[toks[k].start:t.start].strip()
            params = [fe.source[s:e] for s, e in a[0]]
            return ret or "int", ([] if params == ["void"] else params)
    return None


def _stub_definition(fe, name: str) -> str:
    proto = _prototype_of(fe, name)
    if proto is None:
        return f"int {name}() {{\n    return 0;\n}}\n"
    ret, params = proto
    named = []
    for n, p in enumerate(params):
        p = p.strip()
        if p == "..." or re.search(r"[A-Za-z_]\w*\s*(\[[^\]]*\])*$", p) and not re.fullmatch(r"(const |unsigned |signed |struct \w+|long |short |\w+\s*\*?\s*)*(int|char|float|double|long|short|void|size_t|bool)", p):
            named.append(p)
        else:
            named.append(f"{p} p{n}" if not p.endswith("*") else f"{p}p{n}")
    body = "    return 0;\n" if ret.replace("static", "").replace("extern", "").strip() not in ("void",) else ""
    if "*" in ret:
        body = "    return 0;\n"
    elif re.search(r"\b(double|float)\b", ret):
        body = "    return 0.0;\n"
    return f"{ret} {name}({', '.join(named) if named else 'void'}) {{\n{body}}}\n"


def _link(g, fe) -> list[dict]:
    src = fe.source
    sep = "" if src.endswith("\n") else "\n"
    if g.kind != "link":
        return []
    name = (g.notes[0]["message"] if g.notes else "")
    if name == "main":
        return [make("SEARCH_FIX", "Add an empty `main()`", "A program needs a main() function to run.",
                     [Edit(len(src), len(src), sep + "\nint main(void) {\n    return 0;\n}\n")], 0.6)]
    if name:
        return [make("SEARCH_FIX", f"Add a stub definition of `{name}`", f"`{name}` is called but never defined; this stub makes it link (replace it with the real code).",
                     [Edit(len(src), len(src), sep + "\n" + _stub_definition(fe, name))], 0.15)]
    return []


def _members(g, fe) -> list[dict]:
    m = re.search(r"'((?:struct|union) \w+)' has no member named '(\w+)'", g.message) or re.search(r"request for member '(\w+)' in something", g.message)
    if not m or m.re.groups < 2:
        return []
    tag, bad = m.group(1), m.group(2)
    toks, src = fe.tokens, fe.source
    kw, name = tag.split()
    out = []
    for i, t in enumerate(toks):
        if t.value == kw and i + 2 < len(toks) and toks[i + 1].value == name and toks[i + 2].value == "{":
            close, depth = None, 0
            for j in range(i + 2, len(toks)):
                depth += (toks[j].value == "{") - (toks[j].value == "}")
                if depth == 0:
                    close = j
                    break
            if close is None:
                break
            fields = []
            for j in range(i + 3, close):
                if toks[j].kind == "IDENT" and toks[j + 1].value in (";", ",", "[", ":") and toks[j - 1].value != ".":
                    fields.append(toks[j].value)
            use = next((x for x in toks if x.start <= g.start < x.end and x.value == bad), None) or next((x for x in toks if x.start >= g.start and x.value == bad), None)
            if use is not None:
                for dist, f in sorted((edit_distance(bad, f), f) for f in set(fields))[:3]:
                    out.append(make("TYPO_IDENTIFIER", f"Rename the member `{bad}` to `{f}`", f"`{f}` is a member of `{tag}`.",
                                    [Edit(use.start, use.end, f)], 0.8 - 0.1 * min(dist, 4)))
            out.append(make("MISSING_DECLARATION", f"Add a member `int {bad};` to `{tag}`", f"`{tag}` has no member `{bad}`; this adds one.",
                            [Edit(toks[close].start, toks[close].start, f"    int {bad};\n")], 0.45))
            break
    return out


def _statement_range(fe, off: int):
    """(first line start, last line end) of the statement around `off`: up to the next `;`, or the whole `{ ... }` block of
    an if/for/while/function header. None if the brackets do not balance."""
    toks, src = fe.tokens, fe.source
    i = _tok_index(fe, off)
    j = i
    while j > 0 and toks[j - 1].value not in (";", "{", "}"):
        j -= 1
    head = toks[j].value if j < len(toks) else ""
    depth_p = 0
    k = j
    while k < len(toks) and toks[k].kind != "EOF":
        t = toks[k]
        if t.value == "(":
            depth_p += 1
        elif t.value == ")":
            depth_p -= 1
        elif t.value == ";" and depth_p <= 0:
            break
        elif t.value == "{" and depth_p <= 0:
            d = 0
            while k < len(toks):
                d += (toks[k].value == "{") - (toks[k].value == "}")
                if d == 0:
                    break
                k += 1
            break
        k += 1
    if k >= len(toks) or toks[k].kind == "EOF":
        return None
    return line_start(src, toks[j].start), line_end(src, toks[k].end)


def _last_resort(g, fe) -> list[dict]:
    src = fe.source
    if g.kind == "link":
        return []
    ls = line_start(src, min(g.start, len(src)))
    if not src[ls:line_end(src, ls)].strip():
        return []
    why = "Removes code from the program (its behaviour is lost): only use it to get past an error you cannot fix."
    out = []
    rng = _statement_range(fe, g.start)
    if rng is not None and src.count("\n", rng[0], rng[1]) >= 1:
        starts, pos = [], rng[0]
        while pos <= rng[1]:
            starts.append(pos)
            nl = src.find("\n", pos)
            if nl < 0 or nl >= rng[1]:
                break
            pos = nl + 1
        n_lines = len(starts)
        out.append(make("LAST_RESORT", f"Last resort: comment out the statement ({n_lines} lines)", why,
                        [Edit(p, p, "// ") for p in starts if src[p:line_end(src, p)].strip()], 0.03))
    out.append(make("LAST_RESORT", f"Last resort: comment out line {g.line}", why, [Edit(ls, ls, "// ")], 0.02))
    return out


# ------------------------------------------------------- operators, swaps, fills
def _operators(g, fe) -> list[dict]:
    toks = fe.tokens
    i = _tok_index(fe, g.start)
    out = []
    if "lvalue required as left operand of assignment" in g.message:
        t = next((x for x in toks[max(0, i - 1):i + 5] if x.value == "="), None)
        if t is not None:
            out.append(make("SEARCH_FIX", "Replace `=` with `==`", "The left side is not something that can be assigned to.", [Edit(t.start, t.end, "==")], 0.5))
        return out
    m = re.search(r"invalid operands to binary (\S+)", g.message)
    if m:
        op = m.group(1)
        near = sorted((x for x in toks if x.kind == "OP" and x.value == op and abs(x.line - g.line) <= 0), key=lambda x: abs(x.start - g.start))
        if near:
            t = near[0]
            for o in BINARY_OPS:
                if o != op:
                    out.append(make("SEARCH_FIX", f"Replace `{op}` with `{o}`", f"`{op}` does not fit these operands.", [Edit(t.start, t.end, o)], 0.3))
    return out


def _swaps(g, fe) -> list[dict]:
    toks = fe.tokens
    i = _tok_index(fe, g.start)
    out = []
    for a, b in ((i - 1, i), (i, i + 1)):
        if 0 <= a and b < len(toks) and toks[b].kind != "EOF":
            x, y = toks[a], toks[b]
            out.append(make("SEARCH_FIX", f"Swap `{_short(x.value)}` and `{_short(y.value)}`", "Two neighbouring tokens look to be in the wrong order.",
                            [Edit(x.start, x.end, y.value), Edit(y.start, y.end, x.value)], 0.3))
    return out


def _fills(g, fe) -> list[dict]:
    if not any(w in g.message for w in ("expected expression", "expected identifier", "expected primary")):
        return []
    toks = fe.tokens
    i = _tok_index(fe, g.start)
    tok = toks[i]
    freq: dict[str, int] = {}
    for x in toks:
        if x.kind == "IDENT":
            freq[x.value] = freq.get(x.value, 0) + 1
    names = [n for n, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:6]] + ["0", "1"]
    out = []
    for n in names:
        out.append(make("SEARCH_FIX", f"Put `{n}` here", "A value is missing.", [Edit(tok.start, tok.start, n + " ")], 0.22))
        if tok.kind in ("PUNCT", "OP") and tok.value not in (")", ";", "}"):
            out.append(make("SEARCH_FIX", f"Replace `{tok.value}` with `{n}`", "A value is missing.", [Edit(tok.start, tok.end, n)], 0.22))
    return out


def _void_variable(g, fe) -> list[dict]:
    m = re.search(r"variable or field '(\w+)' declared void", g.message)
    if not m:
        return []
    name = m.group(1)
    toks = fe.tokens
    out = []
    for k, t in enumerate(toks):
        if t.value == name and t.line == g.line and k > 0:
            j = k - 1
            while j > 0 and toks[j].value != "void" and toks[j - 1].value in ("*", "const", "unsigned", "static"):
                j -= 1
            if toks[j].value == "void":
                for n, ty in enumerate(("int", "char", "double", "float", "long")):
                    out.append(make("TYPE_MISMATCH", f"Change `void` to `{ty}`", "A variable cannot have type void.", [Edit(toks[j].start, toks[j].end, ty)], 0.6 - 0.08 * n))
            break
    return out


def _header_name(g, fe) -> list[dict]:
    m = re.match(r"([\w./]+\.h): No such file or directory", g.message)
    if not m:
        return []
    bad, src = m.group(1), fe.source
    ls = line_start(src, min(g.start, len(src)))
    le = line_end(src, ls)
    line = src[ls:le]
    k = line.find(bad)
    if k < 0:
        return []
    known = sorted(set(HEADER_OF.values()))
    out = []
    for dist, h in sorted((edit_distance(bad, h), h) for h in known)[:2]:
        if dist <= 3:
            out.append(make("TYPO_IDENTIFIER", f"Rename the header `{bad}` to `{h}`", f"`{h}` is a standard header.", [Edit(ls + k, ls + k + len(bad), h)], 0.8 - 0.1 * dist))
    out.append(make("SEARCH_FIX", f"Delete the `#include <{bad}>` line", "That header does not exist.", [Edit(ls, min(le + 1, len(src)), "")], 0.3))
    return out


def _bad_directive(g, fe) -> list[dict]:
    m = re.search(r"invalid preprocessing directive #(\w+)", g.message)
    if not m:
        return []
    src = fe.source
    ls = line_start(src, min(g.start, len(src)))
    mm = re.compile(r"#\s*" + re.escape(m.group(1))).search(src, ls)
    k = mm.start() if mm else -1
    if k < 0:
        return []
    return [make("SEARCH_FIX", "Delete the stray `#`", f"`#{m.group(1)}` is not a preprocessor directive.", [Edit(k, k + 1, "")], 0.8)]


def _unterminated_include(g, fe) -> list[dict]:
    m = re.search(r"missing terminating (['\"])?([>\"])(['\"])? character", g.message)
    if not m:
        return []
    closer = ">" if ">" in g.message.split("terminating", 1)[1][:6] else '"'
    src = fe.source
    ls = line_start(src, min(g.start, len(src)))
    le = line_end(src, ls)
    line = src[ls:le]
    if not re.match(r"\s*#\s*include", line):
        return []
    end = ls + len(line.rstrip())
    return [make("SEARCH_FIX", f"Close the header name with `{closer}`", f"The `#include` on line {g.line} is missing its closing `{closer}`.",
                 [Edit(end, end, closer)], 0.9)]


# ------------------------------------------------------------------------- entry
def extras(d, fe, limit: int = 60) -> list[dict]:
    g = _gdiag(d, fe)
    if g is None:
        return []
    name = _name_in(g.message)
    cands = (_fixits(g, fe) + _headers(g, fe, name) + _prototype(g, fe, name) + _typos(g, fe, name) + _declare(g, fe, name)
             + _redefinition(g, fe) + _argcount(g, fe) + _const(g, fe) + _link(g, fe) + _members(g, fe) + _operators(g, fe)
             + _void_variable(g, fe) + _header_name(g, fe) + _bad_directive(g, fe) + _unterminated_include(g, fe))
    if g.kind != "link":
        cands += _search(g, fe) + _swaps(g, fe) + _fills(g, fe)
    seen, uniq = set(), []
    for c in sorted(cands, key=lambda c: -c["local_score"]):
        key = tuple((e.start, e.end, e.text) for e in c["edits"])
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    uniq = uniq[:limit]
    return uniq + _last_resort(g, fe)
