"""pycparser AST -> the generic {label, sub, kind, children} tree the UI draws."""
from __future__ import annotations

from pycparser import c_ast as C

USER = "user.c"


def _t(label, sub, kind, children=None, line=None):
    return {"label": str(label), "sub": sub, "kind": kind, "children": children or [], "line": line}


def _line(n):
    c = getattr(n, "coord", None)
    return c.line if c is not None and c.file == USER else None


def _type_text(t) -> str:
    if isinstance(t, C.TypeDecl):
        return _type_text(t.type)
    if isinstance(t, C.IdentifierType):
        return " ".join(t.names)
    if isinstance(t, C.PtrDecl):
        return _type_text(t.type) + "*"
    if isinstance(t, C.ArrayDecl):
        return _type_text(t.type) + "[]"
    if isinstance(t, (C.Struct, C.Union)):
        return f"{'struct' if isinstance(t, C.Struct) else 'union'} {t.name or ''}".strip()
    if isinstance(t, C.Enum):
        return f"enum {t.name or ''}".strip()
    if isinstance(t, C.FuncDecl):
        return _type_text(t.type) + "()"
    return "?"


def to_tree(n) -> dict | None:
    if n is None:
        return None
    k = lambda xs: [c for c in (to_tree(x) for x in xs) if c]
    line = _line(n)
    if isinstance(n, C.FileAST):
        return _t("Program", "translation unit", "root", k([e for e in n.ext if _line(e) is not None or isinstance(e, C.FuncDef) and _line(e.decl)]))
    if isinstance(n, C.FuncDef):
        params = []
        if n.decl.type.args:
            params = [_t(f"{_type_text(p.type)} {p.name}", "parameter", "id") for p in n.decl.type.args.params if isinstance(p, C.Decl) and p.name]
        return _t(f"{n.decl.name}()", f"function → {_type_text(n.decl.type.type)}", "stmt", params + k([n.body]), _line(n.decl))
    if isinstance(n, C.Decl):
        if isinstance(n.type, C.FuncDecl):
            return _t(f"{n.name}()", "prototype", "stmt", [], _line(n))
        kids = k([n.init]) if n.init is not None else []
        return _t(f"{_type_text(n.type)} {n.name or ''}".strip(), "declaration", "stmt", kids, _line(n))
    if isinstance(n, C.Typedef):
        return _t(f"typedef {n.name}", "type definition", "stmt", [], _line(n))
    if isinstance(n, C.Compound):
        return _t("{ }", "block", "block", k(n.block_items or []), line)
    if isinstance(n, C.If):
        kids = [_t("cond", "", "block", k([n.cond])), _t("then", "", "block", k([n.iftrue]))]
        if n.iffalse is not None:
            kids.append(_t("else", "", "block", k([n.iffalse])))
        return _t("if", "statement", "stmt", kids, line)
    if isinstance(n, C.For):
        kids = [x for x in (to_tree(n.init), to_tree(n.cond), to_tree(n.next)) if x] + k([n.stmt])
        return _t("for", "loop", "stmt", kids, line)
    if isinstance(n, (C.While, C.DoWhile)):
        return _t("while" if isinstance(n, C.While) else "do-while", "loop", "stmt", k([n.cond, n.stmt]), line)
    if isinstance(n, C.Switch):
        return _t("switch", "statement", "stmt", k([n.cond, n.stmt]), line)
    if isinstance(n, C.Case):
        return _t("case", "label", "stmt", k([n.expr] + list(n.stmts or [])), line)
    if isinstance(n, C.Default):
        return _t("default", "label", "stmt", k(n.stmts or []), line)
    if isinstance(n, C.Return):
        return _t("return", "statement", "stmt", k([n.expr]) if n.expr is not None else [], line)
    if isinstance(n, (C.Break, C.Continue)):
        return _t("break" if isinstance(n, C.Break) else "continue", "statement", "stmt", [], line)
    if isinstance(n, C.Assignment):
        return _t(n.op, "assignment", "op", k([n.lvalue, n.rvalue]), line)
    if isinstance(n, C.BinaryOp):
        return _t(n.op, "binary", "op", k([n.left, n.right]), line)
    if isinstance(n, C.UnaryOp):
        return _t(n.op, "unary", "op", k([n.expr]), line)
    if isinstance(n, C.TernaryOp):
        return _t("?:", "ternary", "op", k([n.cond, n.iftrue, n.iffalse]), line)
    if isinstance(n, C.Cast):
        return _t(f"({_type_text(n.to_type.type)})", "cast", "op", k([n.expr]), line)
    if isinstance(n, C.FuncCall):
        name = n.name.name if isinstance(n.name, C.ID) else "call"
        return _t(f"{name}()", "call", "op", k(n.args.exprs) if n.args else [], line)
    if isinstance(n, C.ArrayRef):
        return _t("[ ]", "index", "op", k([n.name, n.subscript]), line)
    if isinstance(n, C.StructRef):
        return _t(n.type, "member", "op", k([n.name]) + [_t(n.field.name, "field", "id")], line)
    if isinstance(n, C.Constant):
        return _t(n.value, n.type, "lit", [], line)
    if isinstance(n, C.ID):
        return _t(n.name, "identifier", "id", [], line)
    if isinstance(n, C.ExprList):
        return _t(",", "expression list", "op", k(n.exprs), line)
    if isinstance(n, C.InitList):
        return _t("{ , }", "initializer", "op", k(n.exprs), line)
    if isinstance(n, C.DeclList):
        return _t("decls", "declarations", "stmt", k(n.decls), line)
    if isinstance(n, C.EmptyStatement):
        return None
    return _t(type(n).__name__, "", "op", k([c for _, c in n.children()]), line)
