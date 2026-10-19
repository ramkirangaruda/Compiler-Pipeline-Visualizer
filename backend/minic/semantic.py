"""Semantic analysis: scoped symbol table, type checking and the scope facts
(declared later? declared in a closed scope? nearest visible names?) that
turn a bare "undeclared identifier" error into something the ML model can
reason about."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import ast as A
from .tokens import Diagnostic
from .util import edit_distance

NUMERIC = ("int", "float")
LITERAL_TYPES = {"INT": "int", "FLOAT": "float", "STRING": "string", "BOOL": "bool"}


@dataclass
class Symbol:
    name: str
    type: str
    line: int
    start: int
    end: int
    decl_start: int
    decl_end: int
    type_start: int
    type_end: int
    scope_id: int
    uid: str
    used: bool = False


@dataclass
class Scope:
    id: int
    parent: Optional[int]
    kind: str
    start: int
    end: int
    owner_start: int
    symbols: dict = field(default_factory=dict)


@dataclass
class DeclRec:
    name: str
    type: str
    scope_id: int
    stmt_start: int
    stmt_end: int
    type_start: int
    type_end: int
    name_start: int
    name_end: int


@dataclass
class SemanticResult:
    errors: list
    warnings: list
    scopes: list
    symbols: list
    decls: list
    var_types: dict

    def table(self) -> list[dict]:
        out = []
        for s in self.scopes:
            out.append(
                {
                    "id": s.id,
                    "parent": s.parent,
                    "kind": s.kind,
                    "start": s.start,
                    "end": s.end,
                    "symbols": [
                        {"name": y.name, "type": y.type, "line": y.line, "used": y.used, "uid": y.uid}
                        for y in s.symbols.values()
                    ],
                }
            )
        return out


def assignable(target: str, value: str) -> bool:
    return value == "error" or target == value or (target == "float" and value == "int")


def binary_type(op: str, lt: str, rt: str) -> Optional[str]:
    if op == "+":
        if lt in NUMERIC and rt in NUMERIC:
            return "float" if "float" in (lt, rt) else "int"
        if lt == rt == "string":
            return "string"
        return None
    if op in ("-", "*", "/"):
        if lt in NUMERIC and rt in NUMERIC:
            return "float" if "float" in (lt, rt) else "int"
        return None
    if op == "%":
        return "int" if lt == rt == "int" else None
    if op in ("<", ">", "<=", ">="):
        return "bool" if lt in NUMERIC and rt in NUMERIC else None
    if op in ("==", "!="):
        if (lt in NUMERIC and rt in NUMERIC) or lt == rt:
            return "bool"
        return None
    if op in ("&&", "||"):
        return "bool" if lt == rt == "bool" else None
    return None


class Analyzer:
    def __init__(self, program: A.Program):
        self.program = program
        self.scopes: list[Scope] = []
        self.decls: list[DeclRec] = []
        self.errors: list[Diagnostic] = []
        self.warnings: list[Diagnostic] = []
        self.all_symbols: list[Symbol] = []
        self.stack: list[int] = []
        self.uid_counts: dict[str, int] = {}
        self.var_types: dict[str, str] = {}
        self.stmt_start = 0
        self.top_stmt_start = 0
        self.und: dict[str, list[Diagnostic]] = {}
        self.hint_pool: dict[str, list[tuple[str, bool]]] = {}

    # ------------------------------------------------------------ pre-pass
    def new_scope(self, kind: str, node: A.Node, parent: Optional[int], owner_start: int) -> int:
        sid = len(self.scopes)
        self.scopes.append(Scope(sid, parent, kind, node.start, node.end, owner_start))
        return sid

    def collect(self, stmts: list, scope_id: int) -> None:
        for s in stmts:
            if isinstance(s, A.VarDecl):
                self.decls.append(
                    DeclRec(s.name, s.vtype, scope_id, s.start, s.end, s.type_start, s.type_end, s.name_start, s.name_end)
                )
            elif isinstance(s, A.Block):
                s._sid = self.new_scope("block", s, scope_id, s.start)
                self.collect(s.body, s._sid)
            elif isinstance(s, A.If):
                self.collect_if(s, scope_id, s.start)
            elif isinstance(s, A.While):
                s.body._sid = self.new_scope("while", s.body, scope_id, s.start)
                self.collect(s.body.body, s.body._sid)

    def collect_if(self, s: A.If, scope_id: int, owner: int) -> None:
        s.then._sid = self.new_scope("if", s.then, scope_id, owner)
        self.collect(s.then.body, s.then._sid)
        if isinstance(s.alt, A.If):
            self.collect_if(s.alt, scope_id, owner)
        elif isinstance(s.alt, A.Block):
            s.alt._sid = self.new_scope("else", s.alt, scope_id, owner)
            self.collect(s.alt.body, s.alt._sid)

    # ------------------------------------------------------------ helpers
    def err(self, code: str, msg: str, node_or_span, extra: dict | None = None) -> Diagnostic:
        if isinstance(node_or_span, A.Node):
            line, col, start, end = node_or_span.line, node_or_span.col, node_or_span.start, node_or_span.end
        else:
            line, col, start, end = node_or_span
        d = Diagnostic("semantic", code, f"{msg} (line {line})", line, col, start, end, extra=extra or {})
        self.errors.append(d)
        return d

    def lookup(self, name: str) -> Optional[Symbol]:
        for sid in reversed(self.stack):
            sym = self.scopes[sid].symbols.get(name)
            if sym is not None:
                return sym
        return None

    def declare(self, node: A.VarDecl) -> Symbol:
        n = self.uid_counts.get(node.name, 0) + 1
        self.uid_counts[node.name] = n
        uid = node.name if n == 1 else f"{node.name}#{n}"
        sym = Symbol(
            node.name, node.vtype, node.line, node.name_start, node.name_end, node.start, node.end,
            node.type_start, node.type_end, self.stack[-1], uid,
        )
        self.scopes[self.stack[-1]].symbols[node.name] = sym
        self.all_symbols.append(sym)
        self.var_types[uid] = node.vtype
        node.uid = uid
        return sym

    def hint(self, node: Optional[A.Expr], ty: str, weak: bool = False) -> None:
        d = getattr(node, "_diag", None)
        if d is not None and ty and ty != "error":
            self.hint_pool.setdefault(d.extra["name"], []).append((ty, weak))

    def resolve_hints(self) -> None:
        """Merge the type evidence from *every* use of an undeclared name."""
        for name, diags in self.und.items():
            pool = self.hint_pool.get(name, [])
            strong = [t for t, w in pool if not w]
            weak = [t for t, w in pool if w]
            pick = None
            if strong:
                pick = "float" if "float" in strong and set(strong) <= {"int", "float"} else max(set(strong), key=strong.count)
            elif weak:
                pick = weak[0]
            for d in diags:
                d.extra["hint_type"] = pick
                d.extra["hint_strong"] = bool(strong)

    # -------------------------------------------------------- undeclared
    def undeclared(self, name: str, node: A.Node, lvalue: bool, name_span=None) -> Diagnostic:
        start = name_span[0] if name_span else node.start
        end = name_span[1] if name_span else node.end
        visible: dict[str, Symbol] = {}
        for sid in self.stack:
            visible.update(self.scopes[sid].symbols)
        dists = sorted((edit_distance(name, n), n) for n in visible)
        chain = set(self.stack)
        later = [d for d in self.decls if d.name == name and d.scope_id in chain and d.stmt_start > start]
        closed = [d for d in self.decls if d.name == name and d.scope_id not in chain]
        all_names = {d.name for d in self.decls}
        min_all = min((edit_distance(name, n) for n in all_names), default=99)

        def rec(d: DeclRec) -> dict:
            return {
                "stmt_start": d.stmt_start, "stmt_end": d.stmt_end, "type": d.type, "scope_id": d.scope_id,
                "type_start": d.type_start, "type_end": d.type_end, "name_start": d.name_start,
            }

        extra = {
            "name": name,
            "lvalue": lvalue,
            "visible": [[n, d] for d, n in dists[:5]],
            "visible_types": {n: visible[n].type for _, n in dists[:5]},
            "n_visible": len(visible),
            "declared_later": bool(later),
            "later_decl": rec(later[0]) if later else None,
            "closed_scope": bool(closed),
            "closed_decl": rec(closed[0]) if closed else None,
            "min_dist_all": min_all,
            "use_scope": self.stack[-1],
            "use_stack": list(self.stack),
            "use_stmt_start": self.stmt_start,
            "top_stmt_start": self.top_stmt_start,
            "hint_type": None,
        }
        line = node.line
        d = Diagnostic(
            "semantic", "E_UNDECLARED", f"Semantic error: undeclared identifier '{name}' (line {line})",
            line, node.col, start, end, extra=extra,
        )
        self.errors.append(d)
        self.und.setdefault(name, []).append(d)
        return d

    # --------------------------------------------------------- expressions
    def expr(self, e: A.Expr) -> str:
        ty = self._expr(e)
        e.ty = ty
        return ty

    def _expr(self, e: A.Expr) -> str:
        if isinstance(e, A.Literal):
            return LITERAL_TYPES[e.kind]
        if isinstance(e, A.Ident):
            sym = self.lookup(e.name)
            if sym is None:
                e._diag = self.undeclared(e.name, e, lvalue=False)
                return "error"
            sym.used = True
            e.uid = sym.uid
            return sym.type
        if isinstance(e, A.Unary):
            t = self.expr(e.operand)
            if e.op == "!":
                self.hint(e.operand, "bool")
                if t not in ("bool", "error"):
                    self.err("E_BAD_OPERAND", f"Type error: operator '!' cannot be applied to '{t}'", e,
                             {"op": "!", "left_type": t, "right_type": ""})
                    return "error"
                return "bool"
            self.hint(e.operand, "int", weak=True)
            if t not in NUMERIC + ("error",):
                self.err("E_BAD_OPERAND", f"Type error: unary '-' cannot be applied to '{t}'", e,
                         {"op": "-", "left_type": t, "right_type": ""})
                return "error"
            return t
        if isinstance(e, A.Binary):
            lt, rt = self.expr(e.left), self.expr(e.right)
            logical = e.op in ("&&", "||")
            if lt == "error" or rt == "error":
                known = rt if lt == "error" else lt
                tgt = "bool" if logical else known
                if lt == "error":
                    self.hint(e.left, tgt)
                if rt == "error":
                    self.hint(e.right, tgt)
                return "bool" if logical or e.op in ("<", ">", "<=", ">=", "==", "!=") else "error"
            res = binary_type(e.op, lt, rt)
            if res is None:
                self.err(
                    "E_BAD_OPERAND",
                    f"Type error: operator '{e.op}' cannot be applied to '{lt}' and '{rt}'",
                    e,
                    {
                        "op": e.op, "left_type": lt, "right_type": rt,
                        "left_literal": isinstance(e.left, A.Literal), "right_literal": isinstance(e.right, A.Literal),
                    },
                )
                return "error"
            if e.op in ("/", "%") and isinstance(e.right, A.Literal) and e.right.value in ("0", "0.0"):
                self.warnings.append(
                    Diagnostic("semantic", "W_DIV_ZERO", f"Warning: division by zero (line {e.line})",
                               e.line, e.col, e.start, e.end, "warning")
                )
            return res
        return "error"

    # ---------------------------------------------------------- statements
    def stmts(self, body: list) -> None:
        for s in body:
            prev = self.stmt_start
            self.stmt_start = s.start
            if len(self.stack) == 1:
                self.top_stmt_start = s.start
            self.stmt(s)
            self.stmt_start = prev

    def block(self, b: A.Block) -> None:
        self.stack.append(b._sid)
        self.stmts(b.body)
        self.stack.pop()

    def cond(self, e: A.Expr) -> None:
        t = self.expr(e)
        self.hint(e, "bool")
        if t not in ("bool", "error"):
            self.err("E_BAD_CONDITION", f"Type error: condition must be 'bool' but found '{t}'", e,
                     {"cond_type": t, "expr_start": e.start, "expr_end": e.end})

    def stmt(self, s: A.Node) -> None:
        if isinstance(s, A.VarDecl):
            existing = self.scopes[self.stack[-1]].symbols.get(s.name)
            vt = self.expr(s.init) if s.init is not None else None
            if vt is not None:
                self.hint(s.init, s.vtype)
                if not assignable(s.vtype, vt):
                    self.err(
                        "E_TYPE_MISMATCH",
                        f"Type error: cannot initialise '{s.vtype}' variable '{s.name}' with '{vt}'",
                        s.init,
                        {
                            "kind": "init", "name": s.name, "target_type": s.vtype, "expr_type": vt,
                            "type_start": s.type_start, "type_end": s.type_end,
                            "expr_start": s.init.start, "expr_end": s.init.end,
                            "expr_literal": isinstance(s.init, A.Literal),
                        },
                    )
            if existing is not None:
                self.err(
                    "E_REDECLARED", f"Semantic error: '{s.name}' is already declared in this scope", s,
                    {"name": s.name, "type_start": s.type_start, "type_end": s.type_end},
                )
            self.declare(s)
        elif isinstance(s, A.Assign):
            vt = self.expr(s.value)
            sym = self.lookup(s.name)
            if sym is None:
                d = self.undeclared(s.name, s, lvalue=True, name_span=(s.name_start, s.name_end))
                if vt != "error":
                    self.hint_pool.setdefault(s.name, []).append((vt, False))
            else:
                s.uid = sym.uid
                self.hint(s.value, sym.type)
                if not assignable(sym.type, vt):
                    self.err(
                        "E_TYPE_MISMATCH",
                        f"Type error: cannot assign '{vt}' to '{sym.type}' variable '{s.name}'",
                        s.value,
                        {
                            "kind": "assign", "name": s.name, "target_type": sym.type, "expr_type": vt,
                            "type_start": sym.type_start, "type_end": sym.type_end,
                            "expr_start": s.value.start, "expr_end": s.value.end,
                            "expr_literal": isinstance(s.value, A.Literal),
                        },
                    )
        elif isinstance(s, A.Print):
            t = self.expr(s.value)
            self.hint(s.value, "int", weak=True)
        elif isinstance(s, A.Block):
            self.block(s)
        elif isinstance(s, A.If):
            self.cond(s.cond)
            self.block(s.then)
            if isinstance(s.alt, A.If):
                prev = self.stmt_start
                self.stmt_start = s.alt.start
                self.stmt(s.alt)
                self.stmt_start = prev
            elif isinstance(s.alt, A.Block):
                self.block(s.alt)
        elif isinstance(s, A.While):
            self.cond(s.cond)
            self.block(s.body)

    # ---------------------------------------------------------------- run
    def run(self) -> SemanticResult:
        self.scopes.append(Scope(0, None, "global", self.program.start, self.program.end, 0))
        self.collect(self.program.body, 0)
        self.stack = [0]
        self.stmts(self.program.body)
        for sym in self.all_symbols:
            if not sym.used:
                self.warnings.append(
                    Diagnostic("semantic", "W_UNUSED", f"Warning: variable '{sym.name}' is never read (line {sym.line})",
                               sym.line, 0, sym.start, sym.end, "warning")
                )
        self.resolve_hints()
        self.warnings.sort(key=lambda d: d.start)
        return SemanticResult(self.errors, self.warnings, self.scopes, self.all_symbols, self.decls, self.var_types)


def analyze(program: A.Program) -> SemanticResult:
    return Analyzer(program).run()
