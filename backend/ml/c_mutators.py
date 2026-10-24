"""Programmatic error injection for C. Each mutator corrupts a *valid* seed program in exactly one way and so
produces a labelled example whose true cause is known. A mutant is kept only if the project's C front end
reports the intended kind of error first (the dataset builder additionally requires gcc to reject it)."""
from __future__ import annotations

import random
import string
from typing import Callable, Optional

from cfront.lexer import RESERVED
from cfront.pipeline import CFrontend, run_frontend
from minic.tokens import Diagnostic
from minic.util import edit_distance
from repair.candidates import Edit, apply_edits, indent_str, line_end, line_start, stmt_removal_span
from repair.features_c import extract

WRONG_LITERALS = {
    "int": ['"text"', '"3"', "&n"],
    "double": ['"text"', '"2.5"'],
    "char*": ["5", "42", "7.5"],
}
Result = Optional[tuple[str, dict]]
ARITY_LIBS = {"strlen", "strcmp", "sqrt"}


def typo(word: str, rng: random.Random) -> Optional[str]:
    for _ in range(12):
        op = rng.choice(["swap", "delete", "insert", "sub", "double"])
        i = rng.randrange(len(word))
        if op == "swap" and len(word) >= 2:
            i = rng.randrange(len(word) - 1)
            if word[i] == word[i + 1]:
                continue
            out = word[:i] + word[i + 1] + word[i] + word[i + 2:]
        elif op == "delete" and len(word) >= 3:
            out = word[:i] + word[i + 1:]
        elif op == "insert":
            out = word[:i] + rng.choice(string.ascii_lowercase) + word[i:]
        elif op == "sub":
            out = word[:i] + rng.choice(string.ascii_lowercase) + word[i + 1:]
        elif op == "double":
            out = word[: i + 1] + word[i] + word[i + 1:]
        else:
            continue
        if out != word and out.isidentifier() and out not in RESERVED and 1 <= edit_distance(word, out) <= 2:
            return out
    return None


def _remove_token(fe, rng, pred, what: str) -> Result:
    cands = [t for t in fe.tokens if pred(fe, t)]
    if not cands:
        return None
    t = rng.choice(cands)
    return fe.source[: t.start] + fe.source[t.end:], {"line": t.line, "mutation": f"removed {what}", "name": None}


def m_semicolon(fe, rng) -> Result:
    return _remove_token(fe, rng, lambda f, t: t.kind == "PUNCT" and t.value == ";", "';'")


def m_rparen(fe, rng) -> Result:
    return _remove_token(fe, rng, lambda f, t: t.kind == "PUNCT" and t.value == ")", "')'")


def _header_parens(toks):
    heads = []
    for i, t in enumerate(toks[:-1]):
        if t.kind == "KEYWORD" and t.value in ("if", "while", "for", "switch") and toks[i + 1].value == "(":
            depth = 0
            for j in range(i + 1, len(toks)):
                if toks[j].kind == "PUNCT" and toks[j].value == "(":
                    depth += 1
                elif toks[j].kind == "PUNCT" and toks[j].value == ")":
                    depth -= 1
                    if depth == 0:
                        heads.append((t, toks[i + 1], toks[j]))
                        break
    return heads


def m_lparen(fe, rng) -> Result:
    if rng.random() < 0.2:   # `if x > 3 {` - both header parentheses missing
        heads = [h for h in _header_parens(fe.tokens) if h[0].value in ("if", "while")]
        if heads:
            _, lp, rp = rng.choice(heads)
            src = fe.source
            return (src[: lp.start] + src[lp.end: rp.start] + src[rp.end:],
                    {"line": lp.line, "mutation": "removed both header parentheses", "name": None})
    return _remove_token(fe, rng, lambda f, t: t.kind == "PUNCT" and t.value == "(", "'('")


def m_rbrace(fe, rng) -> Result:
    return _remove_token(fe, rng, lambda f, t: t.kind == "PUNCT" and t.value == "}", "'}'")


def m_lbrace(fe, rng) -> Result:
    toks = fe.tokens
    cands = [t for i, t in enumerate(toks) if t.kind == "PUNCT" and t.value == "{" and i > 0 and toks[i - 1].value in (")", "else")
             and toks[i - 1].line == t.line]
    if not cands:
        return None
    t = rng.choice(cands)
    return fe.source[: t.start] + fe.source[t.end:], {"line": t.line, "mutation": "removed '{'", "name": None}


def m_keyword(fe, rng) -> Result:
    cands = [t for t in fe.tokens if t.kind in ("KEYWORD", "TYPE") and t.value not in ("void",)]
    if not cands:
        return None
    t = rng.choice(cands)
    bad = typo(t.value, rng)
    if bad is None:
        return None
    return (fe.source[: t.start] + bad + fe.source[t.end:],
            {"line": t.line, "mutation": f"misspelled keyword '{t.value}' as '{bad}'", "name": bad})


def m_assign_eq(fe, rng) -> Result:
    """`int x = 5;` written `int x == 5;` (a comparison where an initialiser belongs)."""
    toks, variants = fe.tokens, []
    starts = {t.start: i for i, t in enumerate(toks)}
    for d in fe.sem.decls:
        if d.kind != "var":
            continue
        i = starts.get(d.name_start)
        if i is not None and i + 1 < len(toks) and toks[i + 1].kind == "OP" and toks[i + 1].value == "=":
            variants.append(toks[i + 1])
    if not variants:
        return None
    t = rng.choice(variants)
    return (fe.source[: t.start] + "==" + fe.source[t.end:], {"line": t.line, "mutation": "replaced '=' with '=='", "name": None})


def m_typo(fe, rng) -> Result:
    uses = [u for u in fe.sem.uses if len(u[0]) >= 2]
    if not uses:
        return None
    name, s, e, line = rng.choice(uses)
    bad = typo(name, rng)
    if bad is None:
        return None
    return (fe.source[:s] + bad + fe.source[e:],
            {"line": line, "mutation": f"misspelled '{name}' as '{bad}'", "name": bad, "orig_name": name})


def _plain_decls(fe):
    """Variable declarations that declare exactly one name, with the offset where each later use starts."""
    out = []
    names_per_stmt: dict[int, int] = {}
    for d in fe.sem.decls:
        if d.kind == "var":
            names_per_stmt[d.stmt_start] = names_per_stmt.get(d.stmt_start, 0) + 1
    for d in fe.sem.decls:
        if d.kind != "var" or names_per_stmt[d.stmt_start] != 1 or fe.sem.scopes[d.scope_id].kind == "for":
            continue
        if not fe.source[d.stmt_start: d.stmt_end].rstrip().endswith(";"):
            continue
        out.append(d)
    return out


def m_missing_decl(fe, rng) -> Result:
    uses = fe.sem.uses
    opts = [d for d in _plain_decls(fe) if any(u[0] == d.name and u[1] >= d.stmt_end for u in uses)]
    if not opts:
        return None
    d = rng.choice(opts)
    s, e = stmt_removal_span(fe.source, d.stmt_start, d.stmt_end)
    return fe.source[:s] + fe.source[e:], {"line": fe.source.count("\n", 0, d.stmt_start) + 1,
                                           "mutation": f"removed declaration of '{d.name}'", "name": d.name}


def m_use_before(fe, rng) -> Result:
    src, opts = fe.source, []
    plain = {d.stmt_start: d for d in _plain_decls(fe)}
    for sid, infos in fe.sem.stmts.items():
        infos = sorted(infos, key=lambda x: x.start)
        for i, st in enumerate(infos):
            d = plain.get(st.start)
            if d is None or d.scope_id != sid:
                continue
            for later in infos[i + 1:]:
                if d.name in later.names:
                    if later.kind in ("decl", "Assignment", "FuncCall", "UnaryOp"):
                        opts.append((d, later))
                    break
    if not opts:
        return None
    d, use = rng.choice(opts)
    ds, de = stmt_removal_span(src, d.stmt_start, d.stmt_end)
    pos = line_end(src, use.end) + 1
    pos = min(pos, len(src))
    text = indent_str(src, use.start) + src[d.stmt_start: d.stmt_end] + "\n"
    new = apply_edits(src if pos < len(src) or src.endswith("\n") else src + "\n", [Edit(ds, de, ""), Edit(pos, pos, text)])
    return new, {"line": src.count("\n", 0, use.start) + 1, "mutation": f"moved declaration of '{d.name}' below its first use",
                 "name": d.name}


def _block_open(fe, st):
    """The `{` of an if/while/for statement's own block, if it has one."""
    depth = 0
    for t in fe.tokens:
        if t.start < st.start:
            continue
        if t.start >= st.end:
            break
        if t.kind == "PUNCT" and t.value == "(":
            depth += 1
        elif t.kind == "PUNCT" and t.value == ")":
            depth -= 1
        elif t.kind == "PUNCT" and t.value == "{" and depth == 0:
            return t
    return None


def m_out_of_scope(fe, rng) -> Result:
    src, uses, opts = fe.source, fe.sem.uses, []
    plain = {d.stmt_start: d for d in _plain_decls(fe)}
    for sid, infos in fe.sem.stmts.items():
        infos = sorted(infos, key=lambda x: x.start)
        for i, st in enumerate(infos):
            d = plain.get(st.start)
            if d is None or d.scope_id != sid:
                continue
            for hi in range(i + 1, len(infos)):
                h = infos[hi]
                if h.kind in ("If", "While", "For") and d.name not in h.names - set() and False:
                    pass
                if h.kind not in ("If", "While", "For"):
                    if d.name in h.names:
                        break
                    continue
                lb = _block_open(fe, h)
                after = any(u[0] == d.name and u[1] >= h.end for u in uses)
                header_use = lb is not None and any(u[0] == d.name and h.start <= u[1] < lb.start for u in uses)
                if lb is not None and after and not header_use:
                    opts.append(("block", d, h, lb))
                if d.name in h.names:
                    break
    # a for-loop counter declared outside and used after the loop becomes loop-local
    toks = fe.tokens
    for d in _plain_decls(fe):
        text = src[d.stmt_start: d.stmt_end]
        if "=" in text:
            continue
        for i, t in enumerate(toks[:-4]):
            if t.value == "for" and toks[i + 1].value == "(" and toks[i + 2].value == d.name and toks[i + 3].value == "=" and t.start > d.stmt_end:
                loop_end = None
                depth = 0
                for j in range(i + 1, len(toks)):
                    if toks[j].value == "(":
                        depth += 1
                    elif toks[j].value == ")":
                        depth -= 1
                        if depth == 0 and toks[j + 1].value == "{":
                            k, bd = j + 1, 0
                            while k < len(toks):
                                bd += (toks[k].value == "{") - (toks[k].value == "}")
                                if bd == 0:
                                    break
                                k += 1
                            loop_end = toks[k].end
                            break
                if loop_end is not None and any(u[0] == d.name and u[1] >= loop_end for u in uses):
                    opts.append(("for", d, toks[i], toks[i + 2]))
                break
    if not opts:
        return None
    kind, d, h, anchor = rng.choice(opts)
    ds, de = stmt_removal_span(src, d.stmt_start, d.stmt_end)
    if kind == "block":
        pos = line_end(src, anchor.end) + 1
        text = indent_str(src, h.start) + "  " + src[d.stmt_start: d.stmt_end] + "\n"
        new = apply_edits(src, [Edit(ds, de, ""), Edit(pos, pos, text)])
        what = "moved declaration of '%s' into an inner block" % d.name
    else:
        new = apply_edits(src, [Edit(ds, de, ""), Edit(anchor.start, anchor.start, d.type + " ")])
        what = "made '%s' a for-loop-local variable" % d.name
    return new, {"line": d.stmt_start and src.count("\n", 0, d.stmt_start) + 1, "mutation": what, "name": d.name, "variant": kind}


def m_type(fe, rng) -> Result:
    src, variants = fe.source, []
    toks = fe.tokens
    starts = {t.start: i for i, t in enumerate(toks)}
    for d in fe.sem.decls:
        if d.kind != "var" or d.type not in WRONG_LITERALS:
            continue
        i = starts.get(d.name_start)
        if i is None or i + 1 >= len(toks) or toks[i + 1].value != "=":
            continue
        # initialiser = tokens up to the ';' or ',' at depth 0
        j, depth = i + 2, 0
        while j < len(toks) and not (depth == 0 and toks[j].value in (";", ",")):
            depth += (toks[j].value in "([{") - (toks[j].value in ")]}")
            j += 1
        lo, hi = toks[i + 2].start, toks[j - 1].end
        variants.append(("literal", d.name, Edit(lo, hi, rng.choice(WRONG_LITERALS[d.type]))))
        if d.type in ("int", "double") and not src[d.type_start: d.type_end].strip().endswith("*"):
            variants.append(("decltype", d.name, Edit(d.type_start, d.type_end, "char *")))
    for u_i, t in enumerate(toks[:-3]):    # plain assignment `x = expr;`
        if t.kind == "IDENT" and toks[u_i + 1].value == "=" and t.start > 0:
            d = next((x for x in fe.sem.decls if x.name == t.value and x.kind == "var" and x.name_end <= t.start), None)
            if d is not None and d.type in WRONG_LITERALS and u_i > 0 and toks[u_i - 1].value in (";", "{", "}", ")"):
                j = u_i + 2
                while j < len(toks) and toks[j].value != ";":
                    j += 1
                variants.append(("assign", t.value, Edit(toks[u_i + 2].start, toks[j - 1].end, rng.choice(WRONG_LITERALS[d.type]))))
    for i, t in enumerate(toks[:-2]):      # `%` on a floating-point operand, `*x` on an int, `x[0]` on an int
        if t.kind == "OP" and t.value == "%" and toks[i + 1].kind == "INT":
            variants.append(("float_mod", None, Edit(toks[i + 1].start, toks[i + 1].end, toks[i + 1].value + ".5")))
    ints = [d for d in fe.sem.decls if d.kind == "var" and d.type == "int"]
    for name, s, e, line in fe.sem.uses:
        if any(d.name == name for d in ints) and fe.source[max(0, s - 1):s] in (" ", "(") and fe.source[e:e + 1] in (";", ")", " ", ","):
            ti = starts.get(s)
            if ti is not None and ti > 1 and toks[ti - 1].value in ("=", "(", "+", "-", "*", ",") and toks[ti - 2].value != "printf":
                variants.append(("deref_int", name, Edit(s, s, "*")))
                variants.append(("subscript_int", name, Edit(e, e, "[0]")))
    # wrong argument type to a user function
    funcs = {d.name for d in fe.sem.decls if d.kind == "func"}
    for i, t in enumerate(toks[:-3]):
        if t.kind == "IDENT" and t.value in funcs and toks[i + 1].value == "(" and toks[i - 1].kind != "TYPE":
            a = toks[i + 2]
            if a.kind in ("INT", "IDENT") and toks[i + 3].value in (",", ")"):
                variants.append(("arg", t.value, Edit(a.start, a.end, '"text"')))
    if not variants:
        return None
    kind, name, edit = rng.choice(variants)
    return apply_edits(src, [edit]), {"line": src.count("\n", 0, edit.start) + 1, "mutation": f"type mutation ({kind})",
                                       "name": name, "variant": kind}


def m_include(fe, rng) -> Result:
    inc = [d for d in fe.directives if d.name == "include" and d.header]
    if not inc:
        return None
    d = rng.choice(inc)
    s, e = stmt_removal_span(fe.source, d.start, d.end)
    return fe.source[:s] + fe.source[e:], {"line": d.line, "mutation": f"removed #include <{d.header}>", "name": d.header}


def _call_args(toks, i):
    """Argument spans of the call whose name token is toks[i]; None if it is not a plain call."""
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


def m_argc(fe, rng) -> Result:
    toks, src, opts = fe.tokens, fe.source, []
    funcs = {d.name for d in fe.sem.decls if d.kind == "func"}
    defs = {d.name_start for d in fe.sem.decls if d.kind == "func"}
    for i, t in enumerate(toks):
        if t.kind != "IDENT" or t.start in defs or not (t.value in funcs or t.value in ARITY_LIBS):
            continue
        call = _call_args(toks, i)
        if call is None:
            continue
        spans, lp_end, rp_start = call
        if spans:
            opts.append(("drop", t, Edit(spans[-2][1] if len(spans) > 1 else lp_end, spans[-1][1] if len(spans) > 1 else rp_start, "")))
        opts.append(("add", t, Edit(spans[-1][1] if spans else lp_end, spans[-1][1] if spans else lp_end, ", 1" if spans else "1")))
    if not opts:
        return None
    kind, t, edit = rng.choice(opts)
    return apply_edits(src, [edit]), {"line": t.line, "mutation": f"{kind} an argument of the call to '{t.value}'", "name": t.value}


MUTATORS: dict[str, Callable] = {
    "MISSING_SEMICOLON": m_semicolon,
    "MISSING_RPAREN": m_rparen,
    "MISSING_LPAREN": m_lparen,
    "MISSING_RBRACE": m_rbrace,
    "MISSING_LBRACE": m_lbrace,
    "MISSPELLED_KEYWORD": m_keyword,
    "ASSIGN_EQ_CONFUSION": m_assign_eq,
    "TYPO_IDENTIFIER": m_typo,
    "MISSING_DECLARATION": m_missing_decl,
    "USE_BEFORE_DECLARATION": m_use_before,
    "OUT_OF_SCOPE_USE": m_out_of_scope,
    "TYPE_MISMATCH": m_type,
    "MISSING_INCLUDE": m_include,
    "WRONG_ARG_COUNT": m_argc,
}


def accept(label: str, meta: dict, d0: Diagnostic) -> bool:
    ex = d0.extra
    if label in ("MISSING_SEMICOLON", "MISSING_RPAREN", "MISSING_LPAREN", "MISSING_RBRACE", "MISSING_LBRACE",
                 "MISSPELLED_KEYWORD", "ASSIGN_EQ_CONFUSION"):
        return d0.stage == "syntax"
    if label in ("TYPO_IDENTIFIER", "MISSING_DECLARATION", "USE_BEFORE_DECLARATION", "OUT_OF_SCOPE_USE"):
        if d0.code != "E_UNDECLARED" or ex["name"] != meta["name"]:
            return False
        if label in ("TYPO_IDENTIFIER", "MISSING_DECLARATION"):
            return not ex["declared_later"] and not ex["closed_scope"]
        if label == "USE_BEFORE_DECLARATION":
            return ex["declared_later"]
        return ex["closed_scope"] and not ex["declared_later"]
    if label == "TYPE_MISMATCH":
        return d0.code in ("E_TYPE_MISMATCH", "E_BAD_OPERAND")
    if label == "MISSING_INCLUDE":
        return d0.code == "E_MISSING_INCLUDE"
    if label == "WRONG_ARG_COUNT":
        return d0.code == "E_WRONG_ARGC" and ex["name"] == meta["name"]
    return False


def make_sample(label: str, seed_src: str, rng: random.Random, attempts: int = 8) -> Optional[dict]:
    fe = run_frontend(seed_src)
    if fe.errors:
        return None
    mut = MUTATORS[label]
    for _ in range(attempts):
        res = mut(fe, rng)
        if res is None:
            return None
        new_src, meta = res
        after = run_frontend(new_src)
        errs = after.errors
        if not errs or after.lex_errors:
            continue
        d0 = errs[0]
        if not accept(label, meta, d0):
            continue
        return {"label": label, "source": new_src, "meta": meta, "diag": d0, "fe": after, "features": extract(d0, after)}
    return None
