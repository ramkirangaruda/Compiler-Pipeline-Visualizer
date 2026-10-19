"""Programmatic error injection. Each mutator corrupts a *valid* seed program in
exactly one way and so produces a labelled training example whose true cause
is known. Every mutant is verified by the real compiler before it is kept."""
from __future__ import annotations

import random
import string
from dataclasses import fields
from typing import Callable, Optional

from minic import ast as A
from minic.pipeline import Frontend, run_frontend
from minic.semantic import assignable
from minic.tokens import ALL_RESERVED, BOOL_LITERALS, Diagnostic
from minic.util import edit_distance
from repair.candidates import Edit, apply_edits, indent_str, line_end, line_start, stmt_removal_span
from repair.features import extract

WRONG_LITERALS = {
    "int": ["3.5", '"text"', "true", "2.75"],
    "float": ['"text"', "true", '"3.5"'],
    "bool": ["5", "2.5", '"yes"', "0"],
    "string": ["5", "1.5", "true", "42"],
}
TYPES = ["int", "float", "bool", "string"]


# ------------------------------------------------------------------ AST utils
def iter_nodes(node):
    if isinstance(node, A.Node):
        yield node
        for f in fields(node):
            yield from iter_nodes(getattr(node, f.name))
    elif isinstance(node, list):
        for x in node:
            yield from iter_nodes(x)


def uses_name(node: A.Node, name: str) -> bool:
    for n in iter_nodes(node):
        if isinstance(n, A.Ident) and n.name == name:
            return True
        if isinstance(n, A.Assign) and n.name == name:
            return True
    return False


def stmt_lists(program: A.Program):
    yield program.body
    for n in iter_nodes(program):
        if isinstance(n, A.Block):
            yield n.body


def typo(word: str, rng: random.Random) -> Optional[str]:
    for _ in range(12):
        op = rng.choice(["swap", "delete", "insert", "sub", "double"])
        i = rng.randrange(len(word))
        if op == "swap" and len(word) >= 2:
            i = rng.randrange(len(word) - 1)
            if word[i] == word[i + 1]:
                continue
            out = word[:i] + word[i + 1] + word[i] + word[i + 2 :]
        elif op == "delete" and len(word) >= 3:
            out = word[:i] + word[i + 1 :]
        elif op == "insert":
            out = word[:i] + rng.choice(string.ascii_lowercase) + word[i:]
        elif op == "sub":
            out = word[:i] + rng.choice(string.ascii_lowercase) + word[i + 1 :]
        elif op == "double":
            out = word[: i + 1] + word[i] + word[i + 1 :]
        else:
            continue
        if out != word and out.isidentifier() and out not in ALL_RESERVED and out not in BOOL_LITERALS:
            if 1 <= edit_distance(word, out) <= 2:
                return out
    return None


# ------------------------------------------------------------------- mutators
Result = Optional[tuple[str, dict]]


def _remove_token(fe: Frontend, rng, pred, what: str) -> Result:
    cands = [t for t in fe.tokens if pred(fe, t)]
    if not cands:
        return None
    t = rng.choice(cands)
    return fe.source[: t.start] + fe.source[t.end :], {"line": t.line, "mutation": f"removed {what}", "name": None}


def m_semicolon(fe, rng) -> Result:
    return _remove_token(fe, rng, lambda f, t: t.kind == "PUNCT" and t.value == ";", "';'")


def m_rparen(fe, rng) -> Result:
    return _remove_token(fe, rng, lambda f, t: t.kind == "PUNCT" and t.value == ")", "')'")


def m_lparen(fe, rng) -> Result:
    return _remove_token(fe, rng, lambda f, t: t.kind == "PUNCT" and t.value == "(", "'('")


def m_rbrace(fe, rng) -> Result:
    return _remove_token(fe, rng, lambda f, t: t.kind == "PUNCT" and t.value == "}", "'}'")


def m_lbrace(fe, rng) -> Result:
    cands = [
        t for i, t in enumerate(fe.tokens)
        if t.kind == "PUNCT" and t.value == "{" and i > 0 and fe.tokens[i - 1].value in (")", "else")
    ]
    if not cands:
        return None
    t = rng.choice(cands)
    return fe.source[: t.start] + fe.source[t.end :], {"line": t.line, "mutation": "removed '{'", "name": None}


def m_keyword(fe, rng) -> Result:
    cands = [t for t in fe.tokens if t.kind in ("KEYWORD", "TYPE")]
    if not cands:
        return None
    t = rng.choice(cands)
    bad = typo(t.value, rng)
    if bad is None:
        return None
    return (
        fe.source[: t.start] + bad + fe.source[t.end :],
        {"line": t.line, "mutation": f"misspelled keyword '{t.value}' as '{bad}'", "name": bad},
    )


def m_assign_eq(fe, rng) -> Result:
    toks, variants = fe.tokens, []
    for i, t in enumerate(toks):
        if t.kind == "KEYWORD" and t.value in ("if", "while") and i + 1 < len(toks) and toks[i + 1].value == "(":
            depth, j = 0, i + 1
            while j < len(toks):
                if toks[j].value == "(":
                    depth += 1
                elif toks[j].value == ")":
                    depth -= 1
                    if depth == 0:
                        break
                elif toks[j].value == "==" and toks[j].kind == "OP":
                    variants.append((toks[j], "="))
                j += 1
    for n in iter_nodes(fe.program):
        end = None
        if isinstance(n, A.Assign):
            end = n.name_end
        elif isinstance(n, A.VarDecl) and n.init is not None:
            end = n.name_end
        if end is not None:
            for t in toks:
                if t.start >= end:
                    if t.kind == "OP" and t.value == "=":
                        variants.append((t, "=="))
                    break
    if not variants:
        return None
    t, repl = rng.choice(variants)
    return (
        fe.source[: t.start] + repl + fe.source[t.end :],
        {"line": t.line, "mutation": f"replaced '{t.value}' with '{repl}'", "name": None},
    )


def _ident_uses(fe: Frontend):
    uses = []
    for n in iter_nodes(fe.program):
        if isinstance(n, A.Ident):
            uses.append((n.name, n.start, n.end, n.line))
        elif isinstance(n, A.Assign):
            uses.append((n.name, n.name_start, n.name_end, n.line))
    return uses


def m_typo(fe, rng) -> Result:
    uses = [u for u in _ident_uses(fe) if len(u[0]) >= 2]
    if not uses:
        return None
    name, s, e, line = rng.choice(uses)
    bad = typo(name, rng)
    if bad is None:
        return None
    return (
        fe.source[:s] + bad + fe.source[e:],
        {"line": line, "mutation": f"misspelled variable '{name}' as '{bad}'", "name": bad, "orig_name": name},
    )


def m_missing_decl(fe, rng) -> Result:
    uses = _ident_uses(fe)
    decls = [
        n for n in iter_nodes(fe.program)
        if isinstance(n, A.VarDecl) and any(u[0] == n.name and u[1] > n.end for u in uses)
    ]
    if not decls:
        return None
    d = rng.choice(decls)
    s, e = stmt_removal_span(fe.source, d.start, d.end)
    return fe.source[:s] + fe.source[e:], {"line": d.line, "mutation": f"removed declaration of '{d.name}'", "name": d.name}


def m_use_before(fe, rng) -> Result:
    src, options = fe.source, []
    for body in stmt_lists(fe.program):
        for di, d in enumerate(body):
            if not isinstance(d, A.VarDecl):
                continue
            for s in body[di + 1 :]:
                if uses_name(s, d.name):
                    if isinstance(s, (A.VarDecl, A.Assign, A.Print)):
                        options.append((d, s))
                    break
    if not options:
        return None
    d, s = rng.choice(options)
    ds, de = stmt_removal_span(src, d.start, d.end)
    pos = line_end(src, s.end) + 1
    text = indent_str(src, s.start) + src[d.start : d.end] + "\n"
    new = apply_edits(src if pos <= len(src) else src + "\n", [Edit(ds, de, ""), Edit(min(pos, len(src)), min(pos, len(src)), text)])
    return new, {"line": s.line, "mutation": f"moved declaration of '{d.name}' below its first use", "name": d.name}


def m_out_of_scope(fe, rng) -> Result:
    src, body, options = fe.source, fe.program.body, []
    for di, d in enumerate(body):
        if not isinstance(d, A.VarDecl):
            continue
        for hi in range(di + 1, len(body)):
            h = body[hi]
            if not isinstance(h, (A.If, A.While)):
                if uses_name(h, d.name):
                    break
                continue
            if uses_name(h.cond, d.name):
                break
            block = h.then if isinstance(h, A.If) else h.body
            if any(uses_name(s, d.name) for s in body[hi + 1 :]):
                options.append((d, h, block))
            if uses_name(h, d.name):
                break
    if not options:
        return None
    d, h, block = rng.choice(options)
    ds, de = stmt_removal_span(src, d.start, d.end)
    pos = line_end(src, block.start) + 1
    text = indent_str(src, h.start) + "  " + src[d.start : d.end] + "\n"
    new = apply_edits(src, [Edit(ds, de, ""), Edit(pos, pos, text)])
    return new, {"line": d.line, "mutation": f"moved declaration of '{d.name}' into an inner block", "name": d.name}


def m_type(fe, rng) -> Result:
    src, variants = fe.source, []
    vt = fe.sem.var_types
    for n in iter_nodes(fe.program):
        if isinstance(n, A.VarDecl) and n.init is not None:
            wrong = [w for w in WRONG_LITERALS[n.vtype]]
            variants.append(("literal", n.line, Edit(n.init.start, n.init.end, rng.choice(wrong)), n.name))
            other = [u for u in TYPES if not assignable(u, n.init.ty)]
            if other:
                variants.append(("decltype", n.line, Edit(n.type_start, n.type_end, rng.choice(other)), n.name))
        elif isinstance(n, A.Assign):
            ty = vt.get(n.uid)
            if ty:
                variants.append(("assign", n.line, Edit(n.value.start, n.value.end, rng.choice(WRONG_LITERALS[ty])), n.name))
        elif isinstance(n, (A.If, A.While)):
            c = n.cond
            if isinstance(c, A.Binary) and c.op in ("<", ">", "<=", ">=") and c.left.ty in ("int", "float"):
                variants.append(("cond", n.line, Edit(c.start, c.end, src[c.left.start : c.left.end]), None))
    if not variants:
        return None
    kind, line, edit, name = rng.choice(variants)
    return apply_edits(src, [edit]), {"line": line, "mutation": f"type mutation ({kind})", "name": name, "variant": kind}


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
}


# --------------------------------------------------------------- verification
def accept(label: str, meta: dict, d0: Diagnostic) -> bool:
    ex = d0.extra
    if label in ("MISSING_SEMICOLON", "MISSING_RPAREN", "MISSING_LPAREN", "MISSING_RBRACE", "MISSING_LBRACE",
                 "MISSPELLED_KEYWORD", "ASSIGN_EQ_CONFUSION"):
        return d0.stage == "syntax"
    if label in ("TYPO_IDENTIFIER", "MISSING_DECLARATION", "USE_BEFORE_DECLARATION", "OUT_OF_SCOPE_USE"):
        if d0.code != "E_UNDECLARED" or ex["name"] != meta["name"]:
            return False
        if label == "TYPO_IDENTIFIER":
            return not ex["declared_later"] and not ex["closed_scope"]
        if label == "MISSING_DECLARATION":
            return not ex["declared_later"] and not ex["closed_scope"]
        if label == "USE_BEFORE_DECLARATION":
            return ex["declared_later"]
        return ex["closed_scope"] and not ex["declared_later"]
    if label == "TYPE_MISMATCH":
        return d0.code in ("E_TYPE_MISMATCH", "E_BAD_CONDITION")
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
        return {
            "label": label,
            "source": new_src,
            "meta": meta,
            "diag": d0,
            "fe": after,
            "features": extract(d0, after),
        }
    return None
