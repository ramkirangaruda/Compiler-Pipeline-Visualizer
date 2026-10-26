"""Semantic analysis of real C (on pycparser's AST).

Mirrors what the MiniC analyzer does, so the same diagnosis machinery can run on C:
scoped symbol tables, a type checker for the mistakes beginners actually make, and -
for an undeclared name - the facts the classifier needs (nearest in-scope names,
declared later?, declared in a scope that has closed?, what type the use implies).

C-specific checks: calls to library functions whose header is not #included, calls
with the wrong number of arguments, `%` on floating-point operands, pointer/integer mix-ups.
"""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field
from typing import Optional

from pycparser import c_ast as C

from minic.tokens import Diagnostic, Token
from minic.util import edit_distance

from . import ctypes_ as T
from .prelude import HEADER_OF

USER = "user.c"
PRINTF_FAMILY = {"printf": 0, "fprintf": 1, "sprintf": 1, "snprintf": 2}
SPEC_TYPE = {"d": "int", "i": "int", "u": "unsigned int", "c": "char", "s": "char*", "f": "double", "lf": "double",
             "e": "double", "g": "double", "x": "unsigned int", "X": "unsigned int", "o": "unsigned int", "p": "void*",
             "ld": "long", "lu": "unsigned long", "lld": "long long", "zu": "unsigned long", "hd": "short"}
_SPEC = re.compile(r"%[-+ #0]*\d*(?:\.\d+)?(hh|h|ll|l|z)?([diuoxXfeEgGcsp%])")


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
    kind: str = "var"           # var | param | func | enumconst | macro | lib
    used: bool = False
    ret: str = ""
    params: Optional[list] = None
    variadic: bool = False

    @property
    def uid(self) -> str:
        return self.name


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
    kind: str = "var"


@dataclass
class StmtInfo:
    start: int
    end: int
    kind: str
    names: set = field(default_factory=set)


@dataclass
class CSemantic:
    errors: list
    warnings: list
    scopes: list
    symbols: list
    decls: list
    uses: list              # (name, start, end, line)
    stmts: dict             # scope id -> [StmtInfo]
    functions: list         # (name, start, end) of function definitions

    def table(self) -> list[dict]:
        out = []
        for s in self.scopes:
            rows = []
            for y in s.symbols.values():
                if y.kind in ("lib", "macro", "enumconst"):
                    continue
                t = y.type if y.kind != "func" else f"{y.ret}({', '.join(p[0] for p in (y.params or []))}{', ...' if y.variadic else ''})"
                rows.append({"name": y.name, "type": t, "line": y.line, "used": y.used or y.kind == "func", "uid": y.name})
            out.append({"id": s.id, "parent": s.parent, "kind": s.kind, "start": s.start, "end": s.end, "symbols": rows})
        return out


class Analyzer:
    def __init__(self, source: str, tokens: list[Token], directives: list, ast: C.FileAST):
        self.src, self.toks, self.ast = source, tokens, ast
        self.starts = [t.start for t in tokens]
        self.line_off = [0] + [m.end() for m in re.finditer("\n", source)]
        self.included = {d.header for d in directives if d.name == "include" and d.header}
        self.errors: list[Diagnostic] = []
        self.warnings: list[Diagnostic] = []
        self.scopes: list[Scope] = []
        self.decls: list[DeclRec] = []
        self.symbols: list[Symbol] = []
        self.uses: list[tuple] = []
        self.stmts: dict[int, list[StmtInfo]] = {}
        self.functions: list[tuple] = []
        self.typedefs: dict[str, str] = {}
        self.structs: dict[str, dict[str, str]] = {}
        self.lib: dict[str, Symbol] = {}
        self.defs: dict[str, Symbol] = {}
        self.sid_of: dict[int, int] = {}
        self.diag_of: dict[int, Diagnostic] = {}
        self.und: dict[str, list[Diagnostic]] = {}
        self.hint_pool: dict[str, list[tuple[str, bool]]] = {}
        self.stack: list[int] = []
        self.stmt_start = 0
        self.top_stmt_start = 0
        self.cur_ret = "int"
        self.cur_info: Optional[StmtInfo] = None
        self._macros(directives)

    # ------------------------------------------------------------- positions
    def off(self, coord) -> Optional[int]:
        if coord is None or getattr(coord, "file", None) != USER:
            return None
        return self.line_off[coord.line - 1] + coord.column - 1

    def tidx(self, off: Optional[int]) -> Optional[int]:
        if off is None:
            return None
        i = bisect.bisect_left(self.starts, off)
        return i if i < len(self.toks) and self.starts[i] == off else None

    def stmt_head(self, ti: int) -> int:
        at = ti
        while ti > 0 and self.toks[ti - 1].value not in (";", "{", "}"):
            ti -= 1
        while ti < at and self.toks[ti].value == "else":   # `else` belongs to the previous `if`
            ti += 1
        return ti

    def match(self, ti: int) -> int:
        """Index of the bracket matching the opener at ti (or last token)."""
        pairs = {"(": ")", "[": "]", "{": "}"}
        op, cl = self.toks[ti].value, pairs[self.toks[ti].value]
        depth = 0
        for j in range(ti, len(self.toks)):
            v = self.toks[j].value
            if v == op:
                depth += 1
            elif v == cl:
                depth -= 1
                if depth == 0:
                    return j
        return len(self.toks) - 1

    def simple_end(self, ti: int) -> int:
        """Index of the ';' ending the statement that contains token ti."""
        depth = 0
        for j in range(ti, len(self.toks)):
            v = self.toks[j].value
            if v in "([{" and self.toks[j].kind == "PUNCT":
                depth += 1
            elif v in ")]}" and self.toks[j].kind == "PUNCT":
                depth -= 1
            elif v == ";" and depth <= 0:
                return j
        return len(self.toks) - 1

    def construct_end(self, ti: int) -> int:
        """Index of the last token of the statement starting at token ti."""
        v = self.toks[ti].value
        n = len(self.toks)
        if v == "{":
            return self.match(ti)
        if v in ("if", "while", "for", "switch") and ti + 1 < n and self.toks[ti + 1].value == "(":
            j = self.match(ti + 1) + 1
            e = self.construct_end(j) if j < n else n - 1
            if v == "if" and e + 1 < n and self.toks[e + 1].value == "else":
                e = self.construct_end(e + 2) if e + 2 < n else e + 1
            return e
        if v == "do":
            e = self.construct_end(ti + 1)
            if e + 1 < n and self.toks[e + 1].value == "while":
                return self.simple_end(e + 1)
            return e
        return self.simple_end(ti)

    def stmt_bounds(self, off: int) -> tuple[int, int, int]:
        """(start offset, end offset, start token index) of the statement containing offset `off`."""
        ti = self.tidx(off)
        if ti is None:
            ti = min(bisect.bisect_left(self.starts, off), len(self.toks) - 1)
        s = self.stmt_head(ti)
        e = self.construct_end(s)
        return self.toks[s].start, self.toks[e].end, s

    # --------------------------------------------------------------- macros
    def _macros(self, directives) -> None:
        for d in directives:
            if d.name != "define":
                continue
            m = re.match(r"([A-Za-z_]\w*)(\()?", d.text)
            if not m:
                continue
            name, fn = m.group(1), bool(m.group(2))
            body = d.text[m.end():].strip() if not fn else d.text.split(")", 1)[-1].strip()
            ty = "macrofunc" if fn else (
                "int" if re.fullmatch(r"-?\d+[uUlL]*|0[xX][0-9a-fA-F]+", body) else
                "double" if re.fullmatch(r"-?\d*\.\d+[fF]?|-?\d+\.\d*[fF]?", body) else
                "char*" if body.startswith('"') else "char" if body.startswith("'") else "int")
            self.defs[name] = Symbol(name, ty, d.line, d.start, d.end, d.start, d.end, d.start, d.start, 0, "macro")

    # ----------------------------------------------------------------- types
    def resolve(self, t: str) -> str:
        suffix = ""
        while t.endswith("*") or t.endswith("[]"):
            suffix = t[-1] + suffix if t.endswith("*") else "[]" + suffix
            t = t[:-1] if t.endswith("*") else t[:-2]
        for _ in range(8):
            if t in self.typedefs:
                t = self.typedefs[t]
                while t.endswith("*") or t.endswith("[]"):
                    suffix = t[-1] + suffix if t.endswith("*") else "[]" + suffix
                    t = t[:-1] if t.endswith("*") else t[:-2]
            else:
                break
        return t + suffix

    def tstr(self, n) -> str:
        if isinstance(n, C.TypeDecl):
            return self.tstr(n.type)
        if isinstance(n, C.IdentifierType):
            return self.resolve(T.canonical(n.names))
        if isinstance(n, C.PtrDecl):
            return self.tstr(n.type) + "*"
        if isinstance(n, C.ArrayDecl):
            return self.tstr(n.type) + "[]"
        if isinstance(n, C.FuncDecl):
            return "function"
        if isinstance(n, C.Struct):
            return f"struct {n.name or '<anon>'}"
        if isinstance(n, C.Union):
            return f"union {n.name or '<anon>'}"
        if isinstance(n, C.Enum):
            return f"enum {n.name or '<anon>'}"
        if isinstance(n, C.Typename):
            return self.tstr(n.type)
        return "unknown"

    def signature(self, fd: C.FuncDecl) -> tuple[str, list, bool]:
        ret = self.tstr(fd.type)
        params, variadic = [], False
        if fd.args:
            for p in fd.args.params:
                if isinstance(p, C.EllipsisParam):
                    variadic = True
                elif isinstance(p, (C.Decl, C.Typename)):
                    params.append((self.tstr(p.type), getattr(p, "name", None)))
        if len(params) == 1 and params[0][0] == "void" and not params[0][1]:
            params = []
        return ret, params, variadic

    def register_struct(self, node, alias: str | None = None) -> None:
        if isinstance(node, (C.Struct, C.Union)) and node.decls:
            kind = "struct" if isinstance(node, C.Struct) else "union"
            fields = {d.name: self.tstr(d.type) for d in node.decls if getattr(d, "name", None)}
            for nm in {node.name, alias} - {None}:
                self.structs[f"{kind} {nm}"] = fields
            if not node.name and alias:
                self.typedefs[alias] = f"{kind} {alias}"

    def _drill(self, t):
        while isinstance(t, (C.TypeDecl, C.PtrDecl, C.ArrayDecl)):
            t = t.type
        return t

    # ----------------------------------------------------------- scope setup
    def new_scope(self, kind: str, parent, start: int, end: int, owner: int) -> int:
        sid = len(self.scopes)
        self.scopes.append(Scope(sid, parent, kind, start, end, owner))
        return sid

    def brace_scope(self, node: C.Compound, kind: str, parent: int, owner: int, at_ti: Optional[int]) -> int:
        """Scope for a `{ }` block. pycparser's column for blocks is unreliable, so the `{` is located
        from the token stream (`at_ti` is where the block must begin)."""
        if at_ti is not None and at_ti < len(self.toks) and self.toks[at_ti].value == "{":
            start, end = self.toks[at_ti].start, self.toks[self.match(at_ti)].end
        else:
            start = end = owner
        sid = self.new_scope(kind, parent, start, end, owner)
        self.sid_of[id(node)] = sid
        return sid

    # -------------------------------------------------------------- pre-pass
    def collect(self) -> None:
        self.scopes.append(Scope(0, None, "global", 0, len(self.src), 0))
        for ext in self.ast.ext:
            if self.off(getattr(ext, "coord", None)) is None and not isinstance(ext, C.FuncDef):
                self.lib_item(ext)
        for ext in self.ast.ext:
            if isinstance(ext, C.FuncDef):
                self.collect_func(ext)
            elif self.off(getattr(ext, "coord", None)) is None:
                continue
            elif isinstance(ext, C.Decl):
                self.collect_decl(ext, 0)
            elif isinstance(ext, C.Typedef):
                self.typedefs[ext.name] = self.tstr(ext.type)
                self.register_struct(self._drill(ext.type), ext.name)

    def lib_item(self, ext) -> None:
        if isinstance(ext, C.Typedef):
            self.typedefs[ext.name] = self.tstr(ext.type)
        elif isinstance(ext, C.Decl) and ext.name:
            if isinstance(ext.type, C.FuncDecl):
                ret, params, var = self.signature(ext.type)
                self.lib[ext.name] = Symbol(ext.name, "function", 0, 0, 0, 0, 0, 0, 0, 0, "lib", ret=ret, params=params, variadic=var)
            else:
                self.lib[ext.name] = Symbol(ext.name, self.tstr(ext.type), 0, 0, 0, 0, 0, 0, 0, 0, "lib")

    def collect_func(self, fd: C.FuncDef) -> None:
        d = fd.decl
        name_off = self.off(d.coord)
        if name_off is None:
            return
        _, _, head = self.stmt_bounds(name_off)
        ni = self.tidx(name_off)
        ret, params, var = self.signature(d.type)
        # the body's `{` is the token after the parameter list's closing parenthesis
        body_ti = self.match(ni + 1) + 1 if ni is not None and ni + 1 < len(self.toks) and self.toks[ni + 1].value == "(" else None
        s = self.toks[head].start
        end = self.toks[self.match(body_ti)].end if body_ti is not None and self.toks[body_ti].value == "{" else s
        spec_end = self.spec_end(head, ni)
        self.decls.append(DeclRec(d.name, "function", 0, s, end, self.toks[head].start, self.toks[spec_end].end,
                                  name_off, name_off + len(d.name), "func"))
        self.functions.append((d.name, s, end))
        sid = self.brace_scope(fd.body, "function", 0, s, body_ti)
        if d.type.args:
            for p in d.type.args.params:
                if isinstance(p, C.Decl) and p.name:
                    po = self.off(p.coord) or 0
                    self.decls.append(DeclRec(p.name, self.tstr(p.type), sid, po, po + len(p.name), po, po, po, po + len(p.name), "param"))
        self.collect_items(fd.body.block_items or [], sid, first_ti=(body_ti + 1) if body_ti is not None else None)

    def spec_end(self, head: int, name_ti: Optional[int]) -> int:
        """Index of the last token of the type specifier of a declaration whose first token is `head`."""
        if name_ti is None:
            return head
        j = head
        while j < name_ti and self.toks[j].value != "*":
            j += 1
        return max(head, j - 1)

    def collect_decl(self, d: C.Decl, sid: int, in_for: bool = False) -> None:
        t = self._drill(d.type)
        if isinstance(t, (C.Struct, C.Union)) and t.decls:
            self.register_struct(t, None)
        if not d.name:
            return
        no = self.off(d.coord)
        if no is None:
            return
        s, e, head = self.stmt_bounds(no)
        ni = self.tidx(no)
        se = self.spec_end(head, ni)
        kind = "func" if isinstance(d.type, C.FuncDecl) else "var"
        if in_for and ni is not None:
            e = self.toks[self.simple_end(ni)].end
        self.decls.append(DeclRec(d.name, "function" if kind == "func" else self.tstr(d.type), sid, s, e, self.toks[head].start,
                                  self.toks[se].end, no, no + len(d.name), kind))

    def collect_items(self, items: list, sid: int, register: bool = True, first_ti: Optional[int] = None) -> None:
        pos = first_ti  # token index where the next statement begins (used to place nested `{ }` blocks)
        for it in items:
            o = self.off(getattr(it, "coord", None))
            if isinstance(it, C.Compound):
                at = pos
                s_ti = pos if pos is not None else 0
                e_ti = self.construct_end(s_ti) if pos is not None else s_ti
                s, e = self.toks[s_ti].start, self.toks[e_ti].end
            elif o is None:
                continue
            else:
                s, e, s_ti = self.stmt_bounds(o)
                e_ti = self.construct_end(s_ti)
                at = None
            pos = e_ti + 1
            if register:
                self.stmts.setdefault(sid, []).append(StmtInfo(s, e, "decl" if isinstance(it, C.Decl) else type(it).__name__))
            if isinstance(it, C.Decl):
                self.collect_decl(it, sid)
            elif isinstance(it, C.Typedef):
                self.typedefs[it.name] = self.tstr(it.type)
                self.register_struct(self._drill(it.type), it.name)
            else:
                self.collect_stmt(it, sid, s, s_ti, at)

    def collect_body(self, node, sid: int, owner: int, at_ti: Optional[int]) -> None:
        if node is None:
            return
        if isinstance(node, C.Compound):
            nsid = self.brace_scope(node, "block", sid, owner, at_ti)
            self.collect_items(node.block_items or [], nsid, first_ti=(at_ti + 1) if at_ti is not None else None)
        else:
            self.collect_items([node], sid, register=False, first_ti=at_ti)

    def collect_stmt(self, n, sid: int, start: int, s_ti: int, at: Optional[int]) -> None:
        toks = self.toks
        header_end = lambda: self.match(s_ti + 1) + 1 if s_ti + 1 < len(toks) and toks[s_ti + 1].value == "(" else None
        if isinstance(n, C.Compound):
            nsid = self.brace_scope(n, "block", sid, start, at)
            self.collect_items(n.block_items or [], nsid, first_ti=(at + 1) if at is not None else None)
        elif isinstance(n, C.If):
            after = header_end()
            self.collect_body(n.iftrue, sid, start, after)
            if n.iffalse is not None and after is not None:
                else_ti = self.construct_end(after) + 1
                self.collect_body(n.iffalse, sid, start, else_ti + 1)
        elif isinstance(n, (C.While, C.Switch)):
            self.collect_body(n.stmt, sid, start, header_end())
        elif isinstance(n, C.DoWhile):
            self.collect_body(n.stmt, sid, start, s_ti + 1)
        elif isinstance(n, C.For):
            fsid = self.new_scope("for", sid, start, start, start)
            self.sid_of[id(n)] = fsid
            if isinstance(n.init, C.DeclList):
                for d in n.init.decls:
                    self.collect_decl(d, fsid, in_for=True)
            self.collect_body(n.stmt, fsid, start, header_end())
        elif isinstance(n, (C.Case, C.Default)):
            self.collect_items(n.stmts or [], sid, register=False)
        elif isinstance(n, C.Label):
            self.collect_items([n.stmt], sid, register=False)

    # --------------------------------------------------------------- helpers
    def err(self, code: str, msg: str, start: int, end: int, extra: dict | None = None) -> Diagnostic:
        line = self.src.count("\n", 0, start) + 1
        col = start - (self.src.rfind("\n", 0, start) + 1) + 1
        d = Diagnostic("semantic", code, f"{msg} (line {line})", line, col, start, max(end, start + 1), extra=extra or {})
        self.errors.append(d)
        return d

    def warn(self, code: str, msg: str, start: int, end: int) -> None:
        line = self.src.count("\n", 0, start) + 1
        self.warnings.append(Diagnostic("semantic", code, f"Warning: {msg} (line {line})", line, 1, start, max(end, start + 1), "warning"))

    def lookup(self, name: str) -> Optional[Symbol]:
        for sid in reversed(self.stack):
            sym = self.scopes[sid].symbols.get(name)
            if sym is not None:
                return sym
        return self.defs.get(name) or self.lib.get(name)

    def declare(self, sym: Symbol) -> None:
        self.scopes[self.stack[-1]].symbols[sym.name] = sym
        if sym.kind in ("var", "param", "func"):
            self.symbols.append(sym)

    def hint(self, node, ty: str, weak: bool = False) -> None:
        d = self.diag_of.get(id(node))
        if d is not None and ty and ty != "unknown":
            self.hint_pool.setdefault(d.extra["name"], []).append((ty, weak))

    def resolve_hints(self) -> None:
        for name, diags in self.und.items():
            pool = self.hint_pool.get(name, [])
            strong = [t for t, w in pool if not w]
            weak = [t for t, w in pool if w]
            pick = None
            if strong:
                pick = "double" if "double" in strong and all(T.is_num(x) for x in strong) else max(set(strong), key=strong.count)
            elif weak:
                pick = weak[0]
            for d in diags:
                d.extra["hint_type"] = pick
                d.extra["hint_strong"] = bool(strong)

    def visible_symbols(self) -> dict[str, Symbol]:
        vis: dict[str, Symbol] = {}
        vis.update(self.lib)
        vis.update(self.defs)
        for sid in self.stack:
            vis.update(self.scopes[sid].symbols)
        return vis

    def rec(self, d: DeclRec) -> dict:
        return {"stmt_start": d.stmt_start, "stmt_end": d.stmt_end, "type": d.type, "scope_id": d.scope_id,
                "type_start": d.type_start, "type_end": d.type_end, "name_start": d.name_start, "kind": d.kind}

    def undeclared(self, name: str, start: int, end: int, lvalue: bool, is_call: bool = False, argc: int = 0) -> Diagnostic:
        header = HEADER_OF.get(name)
        if header and header not in self.included and name not in self.lib:
            d = self.err("E_MISSING_INCLUDE", f"Semantic error: '{name}' is used but <{header}> is not included", start, end,
                         {"name": name, "header": header, "is_call": is_call, "lvalue": lvalue,
                          "use_stmt_start": self.stmt_start, "top_stmt_start": self.top_stmt_start})
            return d
        vis = self.visible_symbols()
        dists = sorted((edit_distance(name, n), n) for n in vis if n != name)
        chain = set(self.stack)
        later = [x for x in self.decls if x.name == name and x.scope_id in chain and x.stmt_start > start and x.kind != "param"]
        closed = [x for x in self.decls if x.name == name and x.scope_id not in chain]
        allnames = {x.name for x in self.decls}
        extra = {
            "name": name, "lvalue": lvalue, "is_call": is_call, "argc": argc,
            "visible": [[n, d] for d, n in dists[:5]],
            "visible_types": {n: vis[n].type for _, n in dists[:5]},
            "n_visible": len(vis),
            "declared_later": bool(later), "later_decl": self.rec(later[0]) if later else None,
            "closed_scope": bool(closed), "closed_decl": self.rec(closed[0]) if closed else None,
            "min_dist_all": min((edit_distance(name, n) for n in allnames if n != name), default=99),
            "use_scope": self.stack[-1], "use_stack": list(self.stack),
            "use_stmt_start": self.stmt_start, "top_stmt_start": self.top_stmt_start, "hint_type": None,
        }
        d = self.err("E_UNDECLARED", f"Semantic error: undeclared {'function' if is_call else 'identifier'} '{name}'", start, end, extra)
        self.und.setdefault(name, []).append(d)
        return d

    # ------------------------------------------------------------ expressions
    def arg_spans(self, call_off: int) -> Optional[dict]:
        ti = self.tidx(call_off)
        if ti is None or ti + 1 >= len(self.toks) or self.toks[ti + 1].value != "(":
            return None
        close = self.match(ti + 1)
        spans, depth, cur = [], 0, None
        for j in range(ti + 2, close):
            t = self.toks[j]
            if t.value in "([{" and t.kind == "PUNCT":
                depth += 1
            elif t.value in ")]}" and t.kind == "PUNCT":
                depth -= 1
            if t.value == "," and depth == 0 and t.kind == "PUNCT":
                if cur:
                    spans.append(cur)
                cur = None
                continue
            cur = [t.start, t.end] if cur is None else [cur[0], t.end]
        if cur:
            spans.append(cur)
        return {"arg_spans": spans, "lparen_end": self.toks[ti + 1].end, "rparen_start": self.toks[close].start}

    def expr_span(self, n) -> tuple[Optional[int], Optional[int]]:
        """Start/end offsets of an expression node (start from the AST, end by scanning tokens)."""
        o = self.off(getattr(n, "coord", None))
        ti = self.tidx(o)
        if ti is None:
            return o, o
        ti = self.expr_head(ti)
        depth = 0
        for j in range(ti, len(self.toks)):
            t = self.toks[j]
            if t.kind == "PUNCT" and t.value in "([{":
                depth += 1
            elif t.kind == "PUNCT" and t.value in ")]}":
                if depth == 0:
                    return self.toks[ti].start, self.toks[j - 1].end
                depth -= 1
            elif t.kind == "PUNCT" and t.value in ",;" and depth == 0:
                return self.toks[ti].start, self.toks[j - 1].end
        return self.toks[ti].start, self.toks[-1].start

    def expr_head(self, ti: int) -> int:
        """Back up over a unary prefix operator the AST coordinate skips (e.g. `-x`, `++i`, `&v`, `*p`)."""
        while ti > 0 and self.toks[ti - 1].kind == "OP" and self.toks[ti - 1].value in ("-", "+", "!", "~", "++", "--", "&", "*") \
                and (ti - 1 == 0 or self.toks[ti - 2].value in ("=", "(", ",", "return", "==", "!=", "<", ">", "+", "-", "*", "/", "[", "?", ":", "&&", "||")):
            ti -= 1
        return ti

    def is_zero(self, n) -> bool:
        return isinstance(n, C.Constant) and n.type == "int" and n.value in ("0", "0L", "0u")

    def check_assign(self, kind: str, target_t: str, tnode, vnode, vt: str, name: str, type_span: tuple[int, int]) -> None:
        reason = T.compat(target_t, vt, self.is_zero(vnode), isinstance(vnode, C.Constant) and vnode.type == "string")
        if reason is None:
            return
        s, e = self.expr_span(vnode)
        if s is None:
            return
        self.err("E_TYPE_MISMATCH", f"Type error: cannot {'initialise' if kind == 'init' else 'assign'} '{vt}' to '{target_t}' ({reason})",
                 s, e, {"kind": kind, "name": name, "target_type": target_t, "expr_type": vt, "type_start": type_span[0],
                        "type_end": type_span[1], "expr_start": s, "expr_end": e,
                        "expr_literal": isinstance(vnode, C.Constant)})

    def expr(self, n, mark_used: bool = True) -> str:
        if n is None:
            return "unknown"
        m = getattr(self, "e_" + type(n).__name__, None)
        if m is not None:
            return m(n, mark_used) if type(n).__name__ == "ID" else m(n)
        for _, c in n.children():
            self.expr(c)
        return "unknown"

    def e_Constant(self, n: C.Constant) -> str:
        t = n.type
        if t == "string":
            return "char*"
        if t in ("int",):
            v = n.value.lower()
            return "long" if v.endswith("l") else "unsigned int" if v.endswith("u") else "int"
        if t == "long int":
            return "long"
        return {"char": "char", "float": "float", "double": "double", "unsigned int": "unsigned int"}.get(t, "int")

    def e_ID(self, n: C.ID, mark_used: bool = True) -> str:
        o = self.off(n.coord)
        name = n.name
        sym = self.lookup(name)
        if o is not None:
            self.uses.append((name, o, o + len(name), self.src.count("\n", 0, o) + 1))
            if self.cur_info is not None:
                self.cur_info.names.add(name)
        if sym is None:
            if o is None:
                return "unknown"
            self.diag_of[id(n)] = self.undeclared(name, o, o + len(name), lvalue=not mark_used)
            return "unknown"
        if mark_used:
            sym.used = True
        return "function" if sym.kind in ("func", "lib") and sym.type == "function" else sym.type

    def e_BinaryOp(self, n: C.BinaryOp) -> str:
        lt, rt = self.expr(n.left), self.expr(n.right)
        op = n.op
        logical = op in ("&&", "||")
        if "unknown" in (lt, rt) and lt != rt:
            known = rt if lt == "unknown" else lt
            tgt = "int" if logical else (known if T.is_num(known) or T.is_pointer(known) else None)
            if tgt:
                self.hint(n.left if lt == "unknown" else n.right, tgt)
        lt, rt = T.decay(lt), T.decay(rt)
        if op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
            return "int"
        if op in ("%", "<<", ">>", "&", "|", "^"):
            if T.is_float(lt) or T.is_float(rt):
                s, e = self.expr_span(n)
                if s is not None:
                    self.err("E_BAD_OPERAND", f"Type error: operator '{op}' cannot be applied to '{lt}' and '{rt}'", s, e,
                             {"op": op, "left_type": lt, "right_type": rt, "left_literal": isinstance(n.left, C.Constant),
                              "right_literal": isinstance(n.right, C.Constant)})
            return "int"
        if op in ("+", "-", "*", "/"):
            if lt.endswith("*") and T.is_int(rt):
                return lt
            if rt.endswith("*") and T.is_int(lt) and op == "+":
                return rt
            if lt.endswith("*") and rt.endswith("*") and op == "-":
                return "long"
            if op == "/" and isinstance(n.right, C.Constant) and n.right.value in ("0", "0.0"):
                s, e = self.expr_span(n)
                if s is not None:
                    self.warn("W_DIV_ZERO", "division by zero", s, e)
            if T.is_float(lt) or T.is_float(rt):
                return "double"
            if "long" in lt or "long" in rt:
                return "long"
            if T.is_num(lt) and T.is_num(rt):
                return "int"
        return "unknown"

    def e_UnaryOp(self, n: C.UnaryOp) -> str:
        op = n.op
        if op == "sizeof":
            if not isinstance(n.expr, C.Typename):
                self.expr(n.expr)
            return "unsigned long"
        if op in ("++", "--", "p++", "p--"):
            return self.expr(n.expr)
        t = self.expr(n.expr)
        if op == "&":
            if isinstance(n.expr, C.ID):
                s = self.lookup(n.expr.name)
                if s:
                    s.used = True
            return "unknown" if t == "unknown" else T.decay(t) + "*" if not t.endswith("[]") else t[:-2] + "*"
        if op == "*":
            if T.is_num(t):
                s, e = self.expr_span(n)
                if s is not None:
                    self.err("E_BAD_OPERAND", f"Type error: cannot dereference a value of type '{t}'", s, e,
                             {"op": "*", "left_type": t, "right_type": "", "left_literal": False, "right_literal": False})
                return "unknown"
            return T.pointee(t)
        if op == "!":
            return "int"
        return t if t != "unknown" else "unknown"

    def e_Assignment(self, n: C.Assignment) -> str:
        plain_id = isinstance(n.lvalue, C.ID)
        lt = self.expr(n.lvalue, mark_used=not (plain_id and n.op == "="))
        rt = self.expr(n.rvalue)
        if n.op == "=":
            if plain_id and id(n.lvalue) in self.diag_of and rt != "unknown":
                self.hint_pool.setdefault(n.lvalue.name, []).append((rt, False))
            elif plain_id:
                sym = self.lookup(n.lvalue.name)
                if sym is not None and sym.kind in ("var", "param"):
                    self.hint(n.rvalue, sym.type)
                    self.check_assign("assign", lt, n.lvalue, n.rvalue, rt, n.lvalue.name, (sym.type_start, sym.type_end))
            elif isinstance(n.lvalue, (C.ArrayRef, C.StructRef, C.UnaryOp)) and lt != "unknown":
                pass
        return lt

    def e_ArrayRef(self, n: C.ArrayRef) -> str:
        bt, st = self.expr(n.name), self.expr(n.subscript)
        if T.is_float(st):
            s, e = self.expr_span(n.subscript)
            if s is not None:
                self.err("E_BAD_OPERAND", "Type error: array subscript is not an integer", s, e,
                         {"op": "[]", "left_type": bt, "right_type": st, "left_literal": False, "right_literal": False})
        if T.is_num(bt):
            s, e = self.expr_span(n)
            if s is not None:
                self.err("E_BAD_OPERAND", f"Type error: subscripted value has type '{bt}', not an array or pointer", s, e,
                         {"op": "[]", "left_type": bt, "right_type": st, "left_literal": False, "right_literal": False})
            return "unknown"
        return T.pointee(bt)

    def e_StructRef(self, n: C.StructRef) -> str:
        bt = self.expr(n.name)
        if n.type == "->":
            bt = T.pointee(bt)
        fields = self.structs.get(bt)
        return fields.get(n.field.name, "unknown") if fields else "unknown"

    def e_Cast(self, n: C.Cast) -> str:
        self.expr(n.expr)
        return self.tstr(n.to_type)

    def e_TernaryOp(self, n: C.TernaryOp) -> str:
        self.expr(n.cond)
        a, b = self.expr(n.iftrue), self.expr(n.iffalse)
        return a if a != "unknown" else b

    def e_ExprList(self, n: C.ExprList) -> str:
        t = "unknown"
        for x in n.exprs:
            t = self.expr(x)
        return t

    def e_InitList(self, n: C.InitList) -> str:
        for x in n.exprs:
            self.expr(x)
        return "initlist"

    def e_Typename(self, n) -> str:
        return "unknown"

    def e_FuncCall(self, n: C.FuncCall) -> str:
        args = n.args.exprs if n.args else []
        name_node = n.name
        co = self.off(n.coord)
        sym = None
        if isinstance(name_node, C.ID):
            name = name_node.name
            sym = self.lookup(name)
            if co is not None:
                self.uses.append((name, co, co + len(name), self.src.count("\n", 0, co) + 1))
                if self.cur_info is not None:
                    self.cur_info.names.add(name)
            if sym is None and co is not None:
                for a in args:
                    self.expr(a)
                self.undeclared(name, co, co + len(name), lvalue=False, is_call=True, argc=len(args))
                return "unknown"
            if sym is not None:
                sym.used = True
        else:
            self.expr(name_node)
        arg_types = []
        # printf-style calls: the format string tells us what an undeclared argument must be
        spec_types: list[str] = []
        if isinstance(name_node, C.ID) and name_node.name in PRINTF_FAMILY:
            fi = PRINTF_FAMILY[name_node.name]
            if len(args) > fi and isinstance(args[fi], C.Constant) and args[fi].type == "string":
                spec_types = [SPEC_TYPE.get((m.group(1) or "") + m.group(2), None) for m in _SPEC.finditer(args[fi].value)
                              if m.group(2) != "%"]
                spec_types = [s for s in spec_types]
        for i, a in enumerate(args):
            at = self.expr(a)
            arg_types.append(at)
            fmt_i = i - (PRINTF_FAMILY.get(name_node.name, 0) + 1) if isinstance(name_node, C.ID) and name_node.name in PRINTF_FAMILY else -1
            if 0 <= fmt_i < len(spec_types) and spec_types[fmt_i]:
                self.hint(a, spec_types[fmt_i])
        if sym is None or sym.kind not in ("func", "lib") or sym.params is None:
            return "unknown" if sym is None or sym.kind == "macro" or sym.type.startswith("function") else sym.type
        if isinstance(name_node, C.ID) and name_node.name in PRINTF_FAMILY and spec_types:
            fi = PRINTF_FAMILY[name_node.name]
            given = len(args) - fi - 1
            if given != len(spec_types) and co is not None:
                self.warn("W_FORMAT", f"format string expects {len(spec_types)} argument(s) but {given} given", co, co + len(name_node.name))
        expected = len(sym.params)
        if not sym.variadic and len(args) != expected and co is not None:
            extra = {"name": name_node.name if isinstance(name_node, C.ID) else "", "n_params": expected, "given": len(args)}
            extra.update(self.arg_spans(co) or {"arg_spans": [], "lparen_end": co, "rparen_start": co})
            extra["param_types"] = [p[0] for p in sym.params]
            self.err("E_WRONG_ARGC", f"Call error: '{extra['name']}' takes {expected} argument(s) but {len(args)} given",
                     co, co + len(extra["name"]), extra)
        elif sym.variadic is False or len(args) >= expected:
            for (pt, _), at, a in zip(sym.params, arg_types, args):
                reason = T.compat(pt, at, self.is_zero(a), isinstance(a, C.Constant) and a.type == "string")
                if reason:
                    s, e = self.expr_span(a)
                    if s is not None:
                        self.err("E_TYPE_MISMATCH", f"Type error: argument of type '{at}' passed to parameter of type '{pt}' ({reason})",
                                 s, e, {"kind": "arg", "name": "", "target_type": pt, "expr_type": at, "type_start": s, "type_end": s,
                                        "expr_start": s, "expr_end": e, "expr_literal": isinstance(a, C.Constant)})
        return sym.ret or "unknown"

    # ------------------------------------------------------------ statements
    def items(self, items: list, top: bool = False) -> None:
        for it in items:
            o = self.off(getattr(it, "coord", None))
            if o is None:
                self.stmt(it)
                continue
            s, e, _ = self.stmt_bounds(o)
            prev, prev_info = self.stmt_start, self.cur_info
            self.stmt_start = s
            if top:
                self.top_stmt_start = s
            sid = self.stack[-1]
            info = next((x for x in self.stmts.get(sid, []) if x.start == s), None)
            self.cur_info = info or prev_info
            self.stmt(it)
            self.stmt_start, self.cur_info = prev, prev_info

    def body(self, node) -> None:
        if node is None:
            return
        if isinstance(node, C.Compound):
            self.stack.append(self.sid_of[id(node)])
            self.items(node.block_items or [])
            self.stack.pop()
        else:
            self.items([node])

    def declare_enum(self, t) -> None:
        if isinstance(t, C.Enum) and t.values:
            for k, en in enumerate(t.values.enumerators):
                o = self.off(en.coord) or 0
                self.declare(Symbol(en.name, "int", 0, o, o + len(en.name), o, o, o, o, self.stack[-1], "enumconst"))
                if en.value is not None:
                    self.expr(en.value)

    def decl(self, d: C.Decl) -> None:
        t = self._drill(d.type)
        self.declare_enum(t)
        if not d.name:
            return
        no = self.off(d.coord)
        if isinstance(d.type, C.FuncDecl):
            ret, params, var = self.signature(d.type)
            if self.scopes[self.stack[-1]].symbols.get(d.name) is None or self.scopes[self.stack[-1]].symbols[d.name].kind != "func":
                self.declare(Symbol(d.name, "function", 0, no or 0, (no or 0) + len(d.name), 0, 0, 0, 0, self.stack[-1], "func",
                                    ret=ret, params=params, variadic=var))
            return
        ty = self.tstr(d.type)
        rec = next((x for x in self.decls if x.name == d.name and x.name_start == no and x.scope_id == self.stack[-1]), None)
        # array dimensions are expressions too
        tn = d.type
        while isinstance(tn, (C.PtrDecl, C.TypeDecl, C.ArrayDecl)):
            if isinstance(tn, C.ArrayDecl) and tn.dim is not None:
                self.expr(tn.dim)
            tn = tn.type
        if d.init is not None:
            it = self.expr(d.init)
            if not isinstance(d.init, C.InitList) and rec is not None and not ty.endswith("[]"):
                self.hint(d.init, ty)
                self.check_assign("init", ty, d, d.init, it, d.name, (rec.type_start, rec.type_end))
            elif ty.endswith("[]") and isinstance(d.init, C.Constant) and d.init.type == "string" and not ty.startswith("char"):
                self.check_assign("init", ty, d, d.init, it, d.name, (rec.type_start if rec else 0, rec.type_end if rec else 0))
        existing = self.scopes[self.stack[-1]].symbols.get(d.name)
        if existing is not None and existing.kind in ("var", "param") and self.stack[-1] != 0 and rec is not None:
            self.err("E_REDECLARED", f"Semantic error: '{d.name}' is already declared in this scope", no or 0, (no or 0) + len(d.name),
                     {"name": d.name, "type_start": rec.type_start, "type_end": rec.type_end, "name_start": rec.name_start,
                      "has_init": d.init is not None})
        sym = Symbol(d.name, ty, self.src.count("\n", 0, no or 0) + 1, no or 0, (no or 0) + len(d.name),
                     rec.stmt_start if rec else 0, rec.stmt_end if rec else 0, rec.type_start if rec else 0, rec.type_end if rec else 0,
                     self.stack[-1], "var")
        self.declare(sym)

    def stmt(self, n) -> None:
        if n is None:
            return
        if isinstance(n, C.Decl):
            self.decl(n)
        elif isinstance(n, C.Typedef):
            self.declare_enum(self._drill(n.type))
        elif isinstance(n, C.Compound):
            self.body(n)
        elif isinstance(n, C.If):
            self.expr(n.cond)
            self.body(n.iftrue)
            self.body(n.iffalse)
        elif isinstance(n, (C.While, C.DoWhile)):
            self.expr(n.cond)
            self.body(n.stmt)
        elif isinstance(n, C.For):
            self.stack.append(self.sid_of[id(n)])
            if isinstance(n.init, C.DeclList):
                for d in n.init.decls:
                    self.decl(d)
            elif n.init is not None:
                self.expr(n.init)
            self.expr(n.cond)
            self.expr(n.next)
            self.body(n.stmt)
            self.stack.pop()
        elif isinstance(n, C.Switch):
            self.expr(n.cond)
            self.body(n.stmt)
        elif isinstance(n, C.Case):
            self.expr(n.expr)
            self.items(n.stmts or [])
        elif isinstance(n, C.Default):
            self.items(n.stmts or [])
        elif isinstance(n, C.Return):
            if n.expr is not None:
                rt = self.expr(n.expr)
                reason = T.compat(self.cur_ret, rt, self.is_zero(n.expr), isinstance(n.expr, C.Constant) and n.expr.type == "string")
                if reason and self.cur_ret != "void":
                    s, e = self.expr_span(n.expr)
                    if s is not None:
                        self.err("E_TYPE_MISMATCH", f"Type error: returning '{rt}' from a function returning '{self.cur_ret}' ({reason})", s, e,
                                 {"kind": "return", "name": "", "target_type": self.cur_ret, "expr_type": rt, "type_start": 0, "type_end": 0,
                                  "expr_start": s, "expr_end": e, "expr_literal": isinstance(n.expr, C.Constant)})
        elif isinstance(n, C.Label):
            self.stmt(n.stmt)
        elif isinstance(n, (C.Break, C.Continue, C.Goto, C.EmptyStatement, C.Pragma)):
            pass
        else:
            self.expr(n)

    def func(self, fd: C.FuncDef) -> None:
        d = fd.decl
        ret, params, var = self.signature(d.type)
        no = self.off(d.coord) or 0
        rec = next((x for x in self.decls if x.name == d.name and x.kind == "func" and x.name_start == no), None)
        self.stack = [0]
        self.declare(Symbol(d.name, "function", self.src.count("\n", 0, no) + 1, no, no + len(d.name), rec.stmt_start if rec else 0,
                            rec.stmt_end if rec else 0, rec.type_start if rec else 0, rec.type_end if rec else 0, 0, "func",
                            ret=ret, params=params, variadic=var, used=d.name == "main"))
        sid = self.sid_of[id(fd.body)]
        self.stack.append(sid)
        self.cur_ret = ret
        if d.type.args:
            for p in d.type.args.params:
                if isinstance(p, C.Decl) and p.name:
                    po = self.off(p.coord) or 0
                    self.declare(Symbol(p.name, self.tstr(p.type), self.src.count("\n", 0, po) + 1, po, po + len(p.name), po, po + len(p.name),
                                        po, po, sid, "param", used=True))
        self.items(fd.body.block_items or [], top=True)
        self.stack = [0]

    def run(self) -> CSemantic:
        self.collect()
        self.stack = [0]
        for ext in self.ast.ext:
            o = self.off(getattr(ext, "coord", None))
            if o is None and not isinstance(ext, C.FuncDef):
                continue
            if isinstance(ext, C.FuncDef):
                self.func(ext)
            elif isinstance(ext, C.Decl):
                self.stmt_start = self.top_stmt_start = o or 0
                self.stmt(ext)
            elif isinstance(ext, C.Typedef):
                self.stmt(ext)
        for sym in self.symbols:
            if sym.kind == "var" and sym.scope_id != 0 and not sym.used:
                self.warn("W_UNUSED", f"variable '{sym.name}' is never read", sym.start, sym.end)
        self.resolve_hints()
        self.warnings.sort(key=lambda d: d.start)
        self.errors.sort(key=lambda d: d.start)
        return CSemantic(self.errors, self.warnings, self.scopes, self.symbols, self.decls, self.uses, self.stmts, self.functions)


def analyze(source: str, tokens: list[Token], directives: list, ast: C.FileAST) -> CSemantic:
    return Analyzer(source, tokens, directives, ast).run()
