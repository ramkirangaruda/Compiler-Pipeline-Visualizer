"""Repair-candidate generation for real C. The syntax-level generators are shared with MiniC (they work on
the token stream); the semantic ones know about C: block scopes, for-loop scopes, headers, call arity,
pointer/array types."""
from __future__ import annotations

from cfront import ctypes_ as T
from minic.tokens import Diagnostic
from minic.util import similarity

from . import candidates as base
from .candidates import Edit, indent_str, line_end, line_start, make, stmt_removal_span, _short


# ----------------------------------------------------------------- scope helpers
def _fn_scope(fe, sid: int) -> int:
    scopes = fe.sem.scopes
    while sid and scopes[sid].kind != "function" and scopes[sid].parent is not None:
        sid = scopes[sid].parent
    return sid


def _stmts(fe, sid: int) -> list:
    return sorted(fe.sem.stmts.get(sid, []), key=lambda s: s.start) if fe.sem else []


def _global_top(fe) -> int:
    """Offset just after the program's last #include/#define line (where file-scope declarations go)."""
    src, pos = fe.source, 0
    for dr in fe.directives:
        if dr.name in ("include", "define"):
            pos = max(pos, line_end(src, dr.end) + 1)
    return min(pos, len(src))


def _placements(fe, sid: int) -> dict[str, tuple[int, str]]:
    """Plausible insertion points in a scope: its first line, or after the run of declarations it opens with."""
    src, body = fe.source, _stmts(fe, sid)
    if not body:
        return {}
    out = {"top": (line_start(src, body[0].start), indent_str(src, body[0].start))}
    last = None
    for st in body:
        if st.kind == "decl":
            last = st
        else:
            break
    if last is not None and src.find("\n", last.end) >= 0:
        out["after_decls"] = (line_end(src, last.end) + 1, indent_str(src, last.start))
    return out


def _containing(fe, sid: int, off: int):
    """The statement of scope `sid` that contains offset `off`."""
    return next((s for s in _stmts(fe, sid) if s.start <= off < s.end), None)


def _plain(ty: str) -> str:
    ty = T.decay(ty or "int")
    return "int" if ty in ("unknown", "function", "initlist", "void") or ty.startswith(("struct ", "union ")) else ty


# --------------------------------------------------------------- semantic fixes
def gen_missing_decl(d: Diagnostic, fe) -> list[dict]:
    ex, src, name = d.extra, fe.source, d.extra["name"]
    if d.code != "E_UNDECLARED":
        return []
    ty = _plain(ex.get("hint_type") or "int")
    out, seen = [], set()
    if ex.get("is_call"):
        pos = _global_top(fe)
        out.append(make("MISSING_DECLARATION", f"Declare a prototype `{ty} {name}();`",
                        f"`{name}` is called but no declaration is visible; a prototype before its first use declares it.",
                        [Edit(pos, pos, f"{ty} {name}();\n")], 0.6, "default"))
        return out

    def add(ty_, pos, indent, score, why, strategy):
        key = (pos, ty_)
        if key in seen:
            return
        seen.add(key)
        out.append(make("MISSING_DECLARATION", f"Declare `{T.decl_text(ty_, name)}`", why,
                        [Edit(pos, pos, indent + T.decl_text(ty_, name) + "\n")], score, strategy))

    fn = _fn_scope(fe, ex["use_scope"])
    anchor = _containing(fe, fn, d.start)
    if anchor is not None:
        add(ty, line_start(src, anchor.start), indent_str(src, anchor.start), 0.9,
            f"Declared before the statement that uses `{name}` so every later use can see it (type inferred from usage: {ty}).",
            "before_use")
    use = ex["use_stmt_start"]
    add(ty, line_start(src, use), indent_str(src, use), 0.6, "Declared immediately before the statement that uses it.", "before_use")
    for strat, (pos, ind) in _placements(fe, fn).items():
        add(ty, pos, ind, 0.55 if strat == "after_decls" else 0.45,
            "Declared with the function's other declarations." if strat == "after_decls" else "Declared on the first line of the function.",
            strat)
    add(ty, _global_top(fe), "", 0.4, "Declared at file scope, visible to every function.", "default")
    if T.is_num(ty):
        add("double" if T.is_int(ty) else "int", line_start(src, use), indent_str(src, use), 0.35, "Alternative numeric type.", "before_use")
    return out


def gen_use_before_decl(d: Diagnostic, fe) -> list[dict]:
    ex = d.extra
    if d.code != "E_UNDECLARED" or not ex.get("later_decl"):
        return []
    src, ld, name = fe.source, ex["later_decl"], ex["name"]
    sid = ld["scope_id"]
    st = _containing(fe, sid, d.start) if sid else None
    anchor = st.start if st is not None else (ex["top_stmt_start"] if sid == 0 else ex["use_stmt_start"])
    text = src[ld["stmt_start"]: ld["stmt_end"]]
    ds, de = stmt_removal_span(src, ld["stmt_start"], ld["stmt_end"])
    out = []

    def add(pos, indent, score, why, strategy):
        if ds <= pos < de or pos == ds:
            return
        out.append(make("USE_BEFORE_DECLARATION", f"Move the declaration of `{name}` {why}",
                        f"`{name}` is declared later in the same scope; its declaration is moved ({why}).",
                        [Edit(pos, pos, indent + text + "\n"), Edit(ds, de, "")], score, strategy))

    add(line_start(src, anchor), indent_str(src, anchor), 0.9, "above its first use", "before_use")
    if sid:
        for strat, (pos, ind) in _placements(fe, sid).items():
            add(pos, ind, 0.5 if strat == "after_decls" else 0.4,
                "to the end of the scope's leading declarations" if strat == "after_decls" else "to the top of its scope", strat)
    else:
        add(_global_top(fe), "", 0.4, "to the top of the file", "top")
    return out


def _for_type_start(fe, name_start: int) -> int:
    """First token of the declaration specifiers of the for-loop variable declared at `name_start`."""
    toks = fe.tokens
    j = next((i for i, t in enumerate(toks) if t.start == name_start), None)
    if j is None:
        return name_start
    while j > 0 and toks[j - 1].value not in ("(", ";", ","):
        j -= 1
    return toks[j].start


def gen_out_of_scope(d: Diagnostic, fe) -> list[dict]:
    ex = d.extra
    if d.code != "E_UNDECLARED" or not ex.get("closed_decl") or fe.sem is None:
        return []
    scopes = fe.sem.scopes
    decl, name, src = ex["closed_decl"], ex["name"], fe.source
    path, sc = [], decl["scope_id"]
    while sc is not None:
        path.append(sc)
        sc = scopes[sc].parent
    use_stack = set(ex["use_stack"])
    nca = next((i for i, c in enumerate(path) if c in use_stack), None)
    if not nca:
        return []
    owner = scopes[path[nca - 1]].owner_start
    ty = decl["type"]
    in_for = scopes[decl["scope_id"]].kind == "for"
    out = []
    spots = {"before_block": (line_start(src, owner), indent_str(src, owner))}
    spots.update(_placements(fe, path[nca]) if path[nca] else {})
    if in_for:
        ts = _for_type_start(fe, decl["name_start"])
        for strat, (pos, ind) in spots.items():
            where = {"before_block": "in front of the loop", "top": "at the top of the enclosing scope",
                     "after_decls": "with the enclosing scope's other declarations"}[strat]
            bonus = {"before_block": 0.0, "after_decls": -0.2, "top": -0.3}[strat]
            out.append(make("OUT_OF_SCOPE_USE", f"Hoist the loop variable `{name}` {where}",
                            f"Declare `{name}` {where}, and let the for-loop reuse it.",
                            [Edit(pos, pos, ind + T.decl_text(ty, name) + "\n"), Edit(ts, decl["name_start"], "")],
                            0.9 + bonus, f"split:{strat}"))
        return out

    stmt = src[decl["stmt_start"]: decl["stmt_end"]]
    has_init = "=" in stmt
    ds, de = stmt_removal_span(src, decl["stmt_start"], decl["stmt_end"])
    for strat, (pos, ind) in spots.items():
        if ds <= pos < de:
            continue
        where = {"before_block": "in front of the block", "top": "at the top of the enclosing scope",
                 "after_decls": "with the enclosing scope's other declarations"}[strat]
        bonus = {"before_block": 0.0, "after_decls": -0.2, "top": -0.3}[strat]
        if has_init and not ty.endswith("[]"):
            out.append(make("OUT_OF_SCOPE_USE", f"Hoist `{name}` {where}",
                            f"Declare `{name}` {where}, and turn the inner declaration into an assignment.",
                            [Edit(pos, pos, ind + T.decl_text(ty, name) + "\n"), Edit(decl["type_start"], decl["name_start"], "")],
                            0.9 + bonus, f"split:{strat}"))
        out.append(make("OUT_OF_SCOPE_USE", f"Move the whole declaration of `{name}` {where}",
                        "The full declaration (with initialiser) is moved out of its block.",
                        [Edit(pos, pos, ind + stmt + "\n"), Edit(ds, de, "")], 0.55 + bonus, f"whole:{strat}"))
    return out


def _expr_tokens(fe, lo: int, hi: int) -> list:
    return [t for t in fe.tokens if t.start >= lo and t.end <= hi]


def gen_type_mismatch(d: Diagnostic, fe) -> list[dict]:
    ex, src = d.extra, fe.source
    out = []
    if d.code == "E_TYPE_MISMATCH":
        tgt, val = ex["target_type"], T.decay(ex["expr_type"])
        txt = src[ex["expr_start"]: ex["expr_end"]]
        if ex["kind"] in ("init", "assign") and ex["type_end"] > ex["type_start"] and val not in ("unknown", "function") \
                and not val.startswith(("struct ", "union ")) and val != tgt and "void" not in val:
            new = val if not val.endswith("*") else val[:-1].rstrip() + " *"
            out.append(make("TYPE_MISMATCH", f"Change the declared type of `{ex['name']}` to `{val}`",
                            f"The value has type `{val}`; the variable was declared `{tgt}`.",
                            [Edit(ex["type_start"], ex["type_end"], new)], 0.85))
        if T.is_pointer(tgt) and T.is_num(val) and txt.replace("_", "a").isalnum() and not txt[0].isdigit() and T.pointee(tgt) == val:
            out.append(make("TYPE_MISMATCH", f"Take the address: `&{txt}`", f"`{tgt}` expects an address, not the `{val}` value.",
                            [Edit(ex["expr_start"], ex["expr_start"], "&")], 0.75))
        if T.is_num(tgt) and val.endswith("*") and T.pointee(val) == tgt:
            out.append(make("TYPE_MISMATCH", f"Dereference the pointer: `*{txt}`", f"The value is a `{val}`; `*` reads the `{tgt}` it points to.",
                            [Edit(ex["expr_start"], ex["expr_start"], "*")], 0.7))
        out.append(make("TYPE_MISMATCH", f"Replace the value with a `{tgt}` default ({T.default_value(tgt)})",
                        f"Substitute a literal of the declared type `{tgt}`.",
                        [Edit(ex["expr_start"], ex["expr_end"], T.default_value(tgt))], 0.4))
    elif d.code == "E_BAD_OPERAND":
        op, lt, rt = ex["op"], ex["left_type"], ex.get("right_type") or ""
        toks = _expr_tokens(fe, d.start, d.end)
        if op == "*" and toks and toks[0].value == "*":
            out.append(make("TYPE_MISMATCH", "Remove the `*`", f"`{lt}` is not a pointer, so it cannot be dereferenced.",
                            [Edit(toks[0].start, toks[0].end, "")], 0.6))
        elif op == "[]":
            lb = next((t for t in toks if t.value == "["), None)
            rb = next((t for t in reversed(toks) if t.value == "]"), None)
            if lb is not None and rb is not None:
                if T.is_float(rt):
                    out.append(make("TYPE_MISMATCH", "Cast the subscript to int", "An array index must be an integer.",
                                    [Edit(lb.end, lb.end, "(int)("), Edit(rb.start, rb.start, ")")], 0.8))
                else:
                    out.append(make("TYPE_MISMATCH", "Remove the subscript", f"`{lt}` is not an array or pointer, so it cannot be indexed.",
                                    [Edit(lb.start, rb.end, "")], 0.55))
        else:
            depth, cuts = 0, []
            for i, t in enumerate(toks):
                if t.value in "([" and t.kind == "PUNCT":
                    depth += 1
                elif t.value in ")]" and t.kind == "PUNCT":
                    depth -= 1
                elif depth == 0 and t.value == op and t.kind == "OP" and 0 < i < len(toks) - 1:
                    cuts.append(i)
            if cuts:
                i = cuts[-1]
                edits = []
                if T.is_float(lt):
                    edits += [Edit(toks[0].start, toks[0].start, "(int)("), Edit(toks[i - 1].end, toks[i - 1].end, ")")]
                if T.is_float(rt):
                    edits += [Edit(toks[i + 1].start, toks[i + 1].start, "(int)("), Edit(toks[-1].end, toks[-1].end, ")")]
                if edits:
                    out.append(make("TYPE_MISMATCH", f"Cast the floating-point operand to int for `{op}`",
                                    f"`{op}` works on integers; the floating-point operand is converted with a cast.", edits, 0.8))
    return out


# --------------------------------------------------------- C-only semantic fixes
def gen_missing_include(d: Diagnostic, fe) -> list[dict]:
    if d.code != "E_MISSING_INCLUDE":
        return []
    header, src = d.extra["header"], fe.source
    last = None
    for dr in fe.directives:
        if dr.name == "include":
            last = dr
    pos = line_end(src, last.end) + 1 if last is not None else 0
    pos = min(pos, len(src))
    text = f"#include <{header}>\n"
    if pos == len(src) and src and not src.endswith("\n"):
        text = "\n" + text
    return [make("MISSING_INCLUDE", f"Add `#include <{header}>`", f"`{d.extra['name']}` is declared in <{header}>.",
                 [Edit(pos, pos, text)], 0.98)]


def gen_wrong_argc(d: Diagnostic, fe) -> list[dict]:
    ex = d.extra
    if d.code != "E_WRONG_ARGC":
        return []
    expected, given, spans = ex["n_params"], ex["given"], ex["arg_spans"]
    if given < expected:
        fill = ", ".join(T.default_value(t) for t in ex["param_types"][given:])
        pos = spans[-1][1] if spans else ex["lparen_end"]
        text = (", " + fill) if spans else fill
        return [make("WRONG_ARG_COUNT", f"Pass the {expected - given} missing argument(s) to `{ex['name']}`",
                     f"`{ex['name']}` takes {expected} argument(s); default values are appended for the missing ones.",
                     [Edit(pos, pos, text)], 0.9)]
    if given > expected:
        if expected > 0:
            lo, hi = spans[expected - 1][1], spans[-1][1]
        else:
            lo, hi = ex["lparen_end"], ex["rparen_start"]
        return [make("WRONG_ARG_COUNT", f"Remove the {given - expected} extra argument(s) from the call to `{ex['name']}`",
                     f"`{ex['name']}` takes only {expected} argument(s).", [Edit(lo, hi, "")], 0.9)]
    return []


# -------------------------------------------------------------------- rule fixes
def gen_rules(d: Diagnostic, fe) -> list[dict]:
    src = fe.source
    if d.code == "E_UNEXPECTED_CHAR":
        return [make("RULE_BASED", f"Delete the stray character {d.extra['char']!r}",
                     "Characters outside the language alphabet are removed.", [Edit(d.start, d.end, "")], 0.8)]
    if d.code in ("E_UNTERMINATED_STRING", "E_UNTERMINATED_CHAR"):
        pos, quote = d.extra["line_end"], d.extra["quote"]
        while pos > d.start and src[pos - 1] in " \t\r;)":
            pos -= 1
        what = "string" if quote == '"' else "character"
        return [make("RULE_BASED", f"Close the {what} literal with {quote}",
                     f"A {what} literal must end with a closing quote on the same line.", [Edit(pos, pos, quote)], 0.8)]
    if d.code == "E_UNTERMINATED_COMMENT":
        return [make("RULE_BASED", "Close the comment with `*/`", "A /* comment must be closed with */.",
                     [Edit(len(src), len(src), "\n*/\n")], 0.8)]
    if d.code == "E_REDECLARED":
        ex = d.extra
        if ex.get("has_init"):
            return [make("RULE_BASED", f"Turn the redeclaration of `{ex['name']}` into an assignment",
                         "A name can be declared only once per scope.", [Edit(ex["type_start"], ex["name_start"], "")], 0.7)]
        semi = next((t for t in fe.tokens if t.start >= ex["name_start"] and t.value == ";"), None)
        if semi is not None:
            s, e = stmt_removal_span(src, ex["type_start"], semi.end)
            return [make("RULE_BASED", f"Delete the repeated declaration of `{ex['name']}`",
                         "A name can be declared only once per scope.", [Edit(s, e, "")], 0.6)]
    return []


def gen_lbrace(d: Diagnostic, fe) -> list[dict]:
    """In C a missing `{` shows up as a stray `}` later on: look back for control headers whose body has no brace."""
    if d.stage != "syntax":
        return []
    toks, idx = fe.tokens, d.extra.get("found_index", 0)
    out, rank = [], 0
    open_at = {}
    depth_stack = []
    for j in range(idx):
        t = toks[j]
        if t.kind == "PUNCT" and t.value == "(":
            depth_stack.append(j)
        elif t.kind == "PUNCT" and t.value == ")" and depth_stack:
            open_at[j] = depth_stack.pop()
    for j in range(idx - 1, -1, -1):
        t = toks[j]
        header = None
        if t.kind == "KEYWORD" and t.value == "else" and j + 1 < len(toks) and toks[j + 1].value not in ("{", "if"):
            header = t
        elif t.kind == "PUNCT" and t.value == ")" and j in open_at:
            k = open_at[j] - 1
            if k >= 0 and toks[k].value in ("if", "while", "for") and j + 1 < len(toks) and toks[j + 1].value != "{":
                header = t
        if header is None:
            continue
        out.append(make("MISSING_LBRACE", f"Insert '{{' after `{_short(header.value)}` (line {header.line})",
                        f"The body after the header on line {header.line} needs braces to hold several statements.",
                        [Edit(header.end, header.end, " {")], max(0.3, 0.95 - 0.12 * rank)))
        rank += 1
        if rank >= 4:
            break
    return out or base.gen_lbrace(d, fe)


GENERATORS = dict(base.GENERATORS)
GENERATORS.update({
    "MISSING_LBRACE": gen_lbrace,
    "MISSING_DECLARATION": gen_missing_decl,
    "USE_BEFORE_DECLARATION": gen_use_before_decl,
    "OUT_OF_SCOPE_USE": gen_out_of_scope,
    "TYPE_MISMATCH": gen_type_mismatch,
    "MISSING_INCLUDE": gen_missing_include,
    "WRONG_ARG_COUNT": gen_wrong_argc,
})


def generate(label: str, d: Diagnostic, fe) -> list[dict]:
    gen = GENERATORS.get(label)
    return gen(d, fe) if gen else []
