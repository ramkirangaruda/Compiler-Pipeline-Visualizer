"""A tree-walking interpreter for the C subset teaching programs use.

Supported: int/char/short/long/unsigned/float/double, pointers and arrays (incl. multi-dimensional and
pointer arithmetic), structs and typedefs, functions and recursion, if/for/while/do/switch, break/continue/return,
string literals, printf-family formatting and the common <string.h>/<math.h>/<stdlib.h>/<ctype.h> functions.
Integer arithmetic wraps at the width of the C type. There is no standard input (scanf reads nothing).

It records a trace of (source line, variable written, text printed) so the Studio can step through the program.
"""
from __future__ import annotations

import math
import re
from typing import Any, Optional

from pycparser import c_ast as C

from . import ctypes_ as T

USER = "user.c"
MAX_STEPS = 200_000
TRACE_LIMIT = 4000
MAX_DEPTH = 400
MAX_ALLOC = 2_000_000


class CRuntimeError(Exception):
    pass


class _Return(Exception):
    def __init__(self, value):
        self.value = value


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


class _Exit(Exception):
    def __init__(self, code):
        self.code = code


class Ptr:
    """A pointer into a list (an array, a malloc'd block, or a one-element cell holding a variable)."""
    __slots__ = ("obj", "idx")

    def __init__(self, obj: list, idx: int = 0):
        self.obj, self.idx = obj, idx

    def key(self):
        return (id(self.obj), self.idx)


class Var:
    __slots__ = ("ty", "cell", "elem")

    def __init__(self, ty: str, cell, elem: str = ""):
        self.ty, self.cell, self.elem = ty, cell, elem   # cell: [value] for scalars, the list itself for arrays


ESC = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\", "'": "'", '"': '"', "a": "\a", "b": "\b", "f": "\f", "v": "\v"}


def decode(lit: str) -> str:
    body, out, i = lit[1:-1], [], 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            n = body[i + 1]
            if n == "x":
                m = re.match(r"[0-9a-fA-F]{1,2}", body[i + 2:])
                if m:
                    out.append(chr(int(m.group(0), 16)))
                    i += 2 + len(m.group(0))
                    continue
            if n in "01234567":
                m = re.match(r"[0-7]{1,3}", body[i + 1:])
                out.append(chr(int(m.group(0), 8)))
                i += 1 + len(m.group(0))
                continue
            out.append(ESC.get(n, n))
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def wrap(v: int, ty: str) -> int:
    bits = T.BITS.get(ty)
    if bits is None:
        return v
    if ty.startswith("unsigned") or ty in ("bool", "_Bool"):
        m = (1 << bits) - 1
        return (v & m) if ty not in ("bool", "_Bool") else (1 if v else 0)
    half = 1 << (bits - 1)
    return ((v + half) % (1 << bits)) - half


def cdiv(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


class Interp:
    def __init__(self, ast: C.FileAST, source: str):
        self.ast, self.src = ast, source
        self.funcs: dict[str, C.FuncDef] = {}
        self.typedefs: dict[str, str] = {}
        self.structs: dict[str, list[tuple[str, Any]]] = {}
        self.globals: dict[str, Var] = {}
        self.statics: dict[int, Var] = {}
        self.out: list[str] = []
        self.trace: list[dict] = []
        self.steps = 0
        self.depth = 0
        self.line = 0
        self.rand_state = 1
        self.frames: list[dict[str, Var]] = []
        self.lib = self._lib()

    # ------------------------------------------------------------------ types
    def tstr(self, n) -> str:
        if isinstance(n, C.TypeDecl):
            return self.tstr(n.type)
        if isinstance(n, C.IdentifierType):
            t = T.canonical(n.names)
            return self.resolve(t)
        if isinstance(n, C.PtrDecl):
            return self.tstr(n.type) + "*"
        if isinstance(n, C.ArrayDecl):
            return self.tstr(n.type) + "[]"
        if isinstance(n, C.FuncDecl):
            return "function"
        if isinstance(n, C.Struct):
            self.reg_struct(n)
            return f"struct {n.name or id(n)}"
        if isinstance(n, C.Union):
            self.reg_struct(n)
            return f"union {n.name or id(n)}"
        if isinstance(n, C.Enum):
            return "int"
        if isinstance(n, C.Typename):
            return self.tstr(n.type)
        return "int"

    def resolve(self, t: str) -> str:
        for _ in range(8):
            if t in self.typedefs:
                t = self.typedefs[t]
            else:
                break
        return t

    def reg_struct(self, n) -> None:
        if n.decls:
            key = f"{'struct' if isinstance(n, C.Struct) else 'union'} {n.name or id(n)}"
            if key not in self.structs:
                self.structs[key] = [(d.name, d.type) for d in n.decls if d.name]

    def zero(self, ty: str, node=None):
        if ty in self.structs or ty.startswith(("struct ", "union ")):
            return {name: self.zero_node(t) for name, t in self.structs.get(ty, [])}
        if T.is_float(ty):
            return 0.0
        return 0 if not ty.endswith("*") else None

    def zero_node(self, tnode):
        """Zero value for a declared type node (arrays become zero-filled lists)."""
        if isinstance(tnode, C.ArrayDecl):
            n = self.const_int(tnode.dim) if tnode.dim is not None else 0
            n = max(0, min(n, MAX_ALLOC))
            return [self.zero_node(tnode.type) for _ in range(n)]
        return self.zero(self.tstr(tnode))

    def const_int(self, n) -> int:
        v = self.ev(n)
        if not isinstance(v, (int, float)):
            raise CRuntimeError("array size is not a number")
        return int(v)

    def conv(self, v, ty: str):
        ty = self.resolve(ty)
        if isinstance(v, dict) or ty.startswith(("struct ", "union ")):
            return dict(v) if isinstance(v, dict) else v
        if ty.endswith("[]"):
            return v
        if ty.endswith("*"):
            return v
        if T.is_float(ty):
            if isinstance(v, (Ptr, type(None))):
                raise CRuntimeError("cannot convert a pointer to a floating-point value")
            return float(v)
        if T.is_int(ty):
            if isinstance(v, float):
                if math.isnan(v) or math.isinf(v):
                    return 0
                v = int(v)
            elif isinstance(v, Ptr):
                v = id(v.obj) + v.idx
            elif v is None:
                v = 0
            return wrap(int(v), ty)
        return v

    def sty(self, n) -> str:
        """Static type of an expression, as far as arithmetic needs it."""
        if isinstance(n, C.Constant):
            if n.type == "string":
                return "char*"
            if n.type in ("float", "double"):
                return "double"
            if n.type == "char":
                return "char"
            v = n.value.lower()
            return "long" if v.endswith("l") else "unsigned int" if v.endswith("u") else "int"
        if isinstance(n, C.ID):
            v = self.lookup(n.name, quiet=True)
            return v.ty if v else "int"
        if isinstance(n, C.BinaryOp):
            if n.op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                return "int"
            a, b = T.decay(self.sty(n.left)), T.decay(self.sty(n.right))
            if a.endswith("*"):
                return "long" if b.endswith("*") else a
            if b.endswith("*"):
                return b
            return self.promote(a, b)
        if isinstance(n, C.UnaryOp):
            if n.op == "!":
                return "int"
            if n.op == "sizeof":
                return "unsigned long"
            t = self.sty(n.expr)
            if n.op == "&":
                return T.decay(t) + "*"
            if n.op == "*":
                return T.pointee(t)
            return t if n.op in ("++", "--", "p++", "p--") else self.promote(t, "int")
        if isinstance(n, C.Assignment):
            return self.sty(n.lvalue)
        if isinstance(n, C.Cast):
            return self.tstr(n.to_type)
        if isinstance(n, C.FuncCall) and isinstance(n.name, C.ID):
            fd = self.funcs.get(n.name.name)
            if fd is not None:
                return self.tstr(fd.decl.type.type)
            return "double" if n.name.name in ("sqrt", "pow", "sin", "cos", "tan", "fabs", "floor", "ceil", "log", "log10", "exp", "fmod", "round", "atan", "atan2", "atof") else "int"
        if isinstance(n, C.ArrayRef):
            return T.pointee(self.sty(n.name))
        if isinstance(n, C.StructRef):
            base = self.sty(n.name)
            if n.type == "->":
                base = T.pointee(base)
            for fname, fnode in self.structs.get(self.resolve(base), []):
                if fname == n.field.name:
                    return self.tstr(fnode)
            return "int"
        if isinstance(n, C.TernaryOp):
            return self.sty(n.iftrue)
        return "int"

    @staticmethod
    def promote(a: str, b: str) -> str:
        if T.is_float(a) or T.is_float(b):
            return "double"
        for t in ("unsigned long long", "long long", "unsigned long", "long"):
            if t in (a, b):
                return t
        if "unsigned int" in (a, b) or "unsigned" in (a, b):
            return "unsigned int"
        return "int"

    # ---------------------------------------------------------------- scopes
    def lookup(self, name: str, quiet: bool = False) -> Optional[Var]:
        for fr in reversed(self.frames):
            if name in fr:
                return fr[name]
        if name in self.globals:
            return self.globals[name]
        if quiet:
            return None
        raise CRuntimeError(f"'{name}' is not defined")

    # ----------------------------------------------------------- trace/steps
    def tick(self) -> None:
        self.steps += 1
        if self.steps > MAX_STEPS:
            raise _StepLimit()

    def event(self, line: int, set_: Optional[list] = None, out: Optional[str] = None) -> None:
        if len(self.trace) < TRACE_LIMIT:
            self.trace.append({"pc": max(0, line - 1), "line": line, "set": set_, "out": out})

    def show(self, v) -> str:
        if isinstance(v, float):
            return repr(round(v, 6)) if v != int(v) or abs(v) > 1e15 else f"{v:.1f}"
        if isinstance(v, Ptr):
            return "<pointer>"
        if v is None:
            return "NULL"
        if isinstance(v, dict):
            return "{" + ", ".join(f"{k}={self.show(x)}" for k, x in v.items()) + "}"
        if isinstance(v, list):
            return "[" + ", ".join(self.show(x) for x in v[:12]) + (", …" if len(v) > 12 else "") + "]"
        return str(v)

    def line_of(self, n) -> int:
        c = getattr(n, "coord", None)
        if c is not None and c.file == USER:
            self.line = c.line
        return self.line

    # ---------------------------------------------------------------- program
    def run(self) -> dict:
        halted, error, code = "done", None, 0
        try:
            self.globals["NULL"] = Var("void*", [None])
            for name in ("EOF",):
                self.globals[name] = Var("int", [-1])
            self.globals["INT_MAX"] = Var("int", [2147483647])
            self.globals["INT_MIN"] = Var("int", [-2147483648])
            self.globals["M_PI"] = Var("double", [math.pi])
            self.globals["RAND_MAX"] = Var("int", [32767])
            self.globals["EXIT_SUCCESS"] = Var("int", [0])
            self.globals["EXIT_FAILURE"] = Var("int", [1])
            self.globals["true"] = Var("int", [1])
            self.globals["false"] = Var("int", [0])
            for ext in self.ast.ext:
                if getattr(ext, "coord", None) is None or ext.coord.file != USER:
                    continue
                if isinstance(ext, C.FuncDef):
                    self.funcs[ext.decl.name] = ext
                elif isinstance(ext, C.Typedef):
                    self.typedefs[ext.name] = self.tstr(ext.type)
            self.frames = []
            for ext in self.ast.ext:
                if getattr(ext, "coord", None) is not None and ext.coord.file == USER and isinstance(ext, C.Decl):
                    self.declare(ext, self.globals)
            if "main" not in self.funcs:
                raise CRuntimeError("the program has no main() function")
            ret = self.call(self.funcs["main"], [])
            code = ret if isinstance(ret, int) else 0
        except _StepLimit:
            halted = "step_limit"
        except _Exit as e:
            code = e.code
        except CRuntimeError as e:
            halted, error = "error", f"Runtime error: {e} (line {self.line})"
        except ZeroDivisionError:
            halted, error = "error", f"Runtime error: division by zero (line {self.line})"
        except RecursionError:
            halted, error = "error", f"Runtime error: stack overflow (line {self.line})"
        except (IndexError, TypeError, KeyError, AttributeError, ValueError, OverflowError) as e:
            halted, error = "error", f"Runtime error: invalid memory access or unsupported operation ({type(e).__name__}) (line {self.line})"
        raw = "".join(self.out)
        return {
            "language": "c", "output": raw.split("\n")[:-1] if raw.endswith("\n") else raw.split("\n") if raw else [],
            "raw_output": raw, "vars": {}, "steps": self.steps, "halted": halted, "error": error,
            "trace": self.trace, "trace_truncated": self.steps > TRACE_LIMIT, "exit_code": code,
        }

    # -------------------------------------------------------------- functions
    def call(self, fd: C.FuncDef, args: list):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise RecursionError()
        frame: dict[str, Var] = {}
        params = fd.decl.type.args.params if fd.decl.type.args else []
        params = [p for p in params if isinstance(p, C.Decl) and p.name]
        for p, a in zip(params, args):
            ty = self.tstr(p.type)
            if isinstance(a, list):
                a = Ptr(a, 0)
            frame[p.name] = Var(ty, [self.conv(a, ty)])
        self.frames.append(frame)
        saved = self.frames
        ret_ty = self.tstr(fd.decl.type.type)
        try:
            self.block(fd.body, new_scope=False)
            value = 0
        except _Return as r:
            value = r.value
        finally:
            self.frames = saved
            self.frames.pop()
            self.depth -= 1
        return self.conv(value, ret_ty) if ret_ty != "void" and value is not None else value

    # ------------------------------------------------------------ declarations
    def declare(self, d: C.Decl, scope: dict) -> None:
        if not d.name or isinstance(d.type, C.FuncDecl):
            self.tstr(self._drill(d.type)) if isinstance(self._drill(d.type), (C.Struct, C.Union)) else None
            return
        line = self.line_of(d)
        if "static" in (d.storage or []) and id(d) in self.statics:
            scope[d.name] = self.statics[id(d)]
            return
        tnode = d.type
        if isinstance(tnode, C.ArrayDecl):
            elem = self.tstr(self._elem(tnode))
            if tnode.dim is None and isinstance(d.init, (C.InitList, C.Constant)):
                n = len(d.init.exprs) if isinstance(d.init, C.InitList) else len(decode(d.init.value)) + 1
                arr = [self.zero_node(tnode.type) for _ in range(n)]
            else:
                arr = self.zero_node(tnode)
            if d.init is not None:
                self.init_array(arr, d.init, tnode)
            var = Var(self.tstr(tnode), arr, elem)
        else:
            ty = self.tstr(tnode)
            val = self.zero(ty)
            if d.init is not None:
                if isinstance(d.init, C.InitList):
                    val = self.init_struct(ty, d.init)
                else:
                    val = self.conv(self.ev(d.init), ty)
                    if isinstance(val, list):
                        val = Ptr(val, 0)
            var = Var(ty, [val])
            if d.init is not None and not isinstance(val, (dict, list)):
                self.event(line, [d.name, self.show(val)])
        scope[d.name] = var
        if "static" in (d.storage or []):
            self.statics[id(d)] = var

    @staticmethod
    def _drill(t):
        while isinstance(t, (C.TypeDecl, C.PtrDecl, C.ArrayDecl)):
            t = t.type
        return t

    @staticmethod
    def _elem(t):
        while isinstance(t, C.ArrayDecl):
            t = t.type
        return t

    def init_array(self, arr: list, init, tnode) -> None:
        if isinstance(init, C.Constant) and init.type == "string" and isinstance(arr, list):
            chars = [ord(c) for c in decode(init.value)] + [0]
            for i in range(min(len(arr), len(chars))):
                arr[i] = chars[i]
            return
        if isinstance(init, C.InitList):
            inner = tnode.type if isinstance(tnode, C.ArrayDecl) else tnode
            for i, e in enumerate(init.exprs):
                if i >= len(arr):
                    break
                if isinstance(e, C.InitList) and isinstance(arr[i], list):
                    self.init_array(arr[i], e, inner)
                else:
                    ty = self.tstr(self._elem(tnode))
                    arr[i] = self.conv(self.ev(e), ty)

    def init_struct(self, ty: str, init: C.InitList):
        val = self.zero(ty)
        if isinstance(val, dict):
            for (name, tn), e in zip(self.structs.get(ty, []), init.exprs):
                val[name] = self.conv(self.ev(e), self.tstr(tn))
        return val

    # ------------------------------------------------------------- statements
    def block(self, n: C.Compound, new_scope: bool = True) -> None:
        if new_scope:
            self.frames.append({})
        try:
            for it in n.block_items or []:
                self.exec(it)
        finally:
            if new_scope:
                self.frames.pop()

    def exec(self, n) -> None:
        self.tick()
        self.line_of(n)
        if isinstance(n, C.Decl):
            self.declare(n, self.frames[-1])
        elif isinstance(n, C.Compound):
            self.block(n)
        elif isinstance(n, C.If):
            if self.truth(self.ev(n.cond)):
                self.exec(n.iftrue)
            elif n.iffalse is not None:
                self.exec(n.iffalse)
        elif isinstance(n, C.While):
            while self.truth(self.ev(n.cond)):
                try:
                    self.exec(n.stmt)
                except _Continue:
                    pass
                except _Break:
                    break
                self.tick()
        elif isinstance(n, C.DoWhile):
            while True:
                try:
                    self.exec(n.stmt)
                except _Continue:
                    pass
                except _Break:
                    break
                self.tick()
                if not self.truth(self.ev(n.cond)):
                    break
        elif isinstance(n, C.For):
            self.frames.append({})
            try:
                if isinstance(n.init, C.DeclList):
                    for d in n.init.decls:
                        self.declare(d, self.frames[-1])
                elif n.init is not None:
                    self.ev(n.init)
                while n.cond is None or self.truth(self.ev(n.cond)):
                    try:
                        self.exec(n.stmt)
                    except _Continue:
                        pass
                    except _Break:
                        break
                    self.tick()
                    if n.next is not None:
                        self.ev(n.next)
            finally:
                self.frames.pop()
        elif isinstance(n, C.Switch):
            self.switch(n)
        elif isinstance(n, C.Return):
            raise _Return(self.ev(n.expr) if n.expr is not None else None)
        elif isinstance(n, C.Break):
            raise _Break()
        elif isinstance(n, C.Continue):
            raise _Continue()
        elif isinstance(n, (C.EmptyStatement, C.Pragma, C.Typedef)):
            if isinstance(n, C.Typedef):
                self.typedefs[n.name] = self.tstr(n.type)
        elif isinstance(n, C.Label):
            self.exec(n.stmt)
        elif isinstance(n, C.Goto):
            raise CRuntimeError("goto is not supported by the interpreter")
        else:
            self.ev(n)

    def switch(self, n: C.Switch) -> None:
        v = self.ev(n.cond)
        body = n.stmt.block_items if isinstance(n.stmt, C.Compound) else [n.stmt]
        start = None
        for i, it in enumerate(body):
            if isinstance(it, C.Case) and self.ev(it.expr) == v:
                start = i
                break
        if start is None:
            start = next((i for i, it in enumerate(body) if isinstance(it, C.Default)), None)
        if start is None:
            return
        self.frames.append({})
        try:
            for it in body[start:]:
                for st in (it.stmts if isinstance(it, (C.Case, C.Default)) else [it]):
                    self.exec(st)
        except _Break:
            pass
        finally:
            self.frames.pop()

    @staticmethod
    def truth(v) -> bool:
        if isinstance(v, Ptr):
            return True
        return bool(v)

    # ------------------------------------------------------------ expressions
    def ev(self, n):
        self.tick()
        m = getattr(self, "x_" + type(n).__name__, None)
        if m is None:
            raise CRuntimeError(f"unsupported construct: {type(n).__name__}")
        return m(n)

    def x_Constant(self, n: C.Constant):
        if n.type == "string":
            return Ptr([ord(c) for c in decode(n.value)] + [0], 0)
        if n.type == "char":
            s = decode(n.value)
            return ord(s[0]) if s else 0
        if n.type in ("float", "double"):
            return float(n.value.rstrip("fFlL"))
        v = n.value.rstrip("uUlL")
        return int(v, 16) if v.lower().startswith("0x") else int(v, 2) if v.lower().startswith("0b") else int(v, 8) if len(v) > 1 and v.startswith("0") else int(v)

    def x_ID(self, n: C.ID):
        v = self.lookup(n.name)
        if isinstance(v.cell, list) and v.ty.endswith("[]"):
            return Ptr(v.cell, 0)
        return v.cell[0]

    def ref(self, n):
        """(container, key) of an lvalue."""
        if isinstance(n, C.ID):
            v = self.lookup(n.name)
            if v.ty.endswith("[]"):
                raise CRuntimeError("cannot assign to an array")
            return v.cell, 0
        if isinstance(n, C.ArrayRef):
            base = self.ev(n.name)
            i = int(self.ev(n.subscript))
            if isinstance(base, Ptr):
                j = base.idx + i
                if j < 0 or j >= len(base.obj):
                    raise CRuntimeError("array index out of bounds (invalid memory access)")
                return base.obj, j
            raise CRuntimeError("subscript of a non-pointer")
        if isinstance(n, C.UnaryOp) and n.op == "*":
            p = self.ev(n.expr)
            if not isinstance(p, Ptr):
                raise CRuntimeError("dereference of a null or invalid pointer")
            if p.idx < 0 or p.idx >= len(p.obj):
                raise CRuntimeError("invalid memory access")
            return p.obj, p.idx
        if isinstance(n, C.StructRef):
            base = self.ev(n.name)
            if n.type == "->":
                if not isinstance(base, Ptr):
                    raise CRuntimeError("-> applied to a null or invalid pointer")
                base = base.obj[base.idx]
            if not isinstance(base, dict):
                raise CRuntimeError("member access on a non-struct")
            return base, n.field.name
        raise CRuntimeError("expression is not assignable")

    def get(self, n):
        obj, key = self.ref(n)
        v = obj[key]
        return Ptr(v, 0) if isinstance(v, list) else v

    def x_ArrayRef(self, n):
        return self.get(n)

    def x_StructRef(self, n):
        return self.get(n)

    def assign_to(self, n, v) -> None:
        obj, key = self.ref(n)
        ty = self.sty(n)
        v = self.conv(v, ty) if not isinstance(v, (Ptr, dict)) or isinstance(obj, list) and False else v
        if isinstance(v, list):
            v = Ptr(v, 0)
        if not isinstance(v, (Ptr, dict)):
            v = self.conv(v, ty)
        elif isinstance(v, dict):
            v = dict(v)
        obj[key] = v
        name = n.name if isinstance(n, C.ID) else None
        if name is None and isinstance(n, C.ArrayRef) and isinstance(n.name, C.ID):
            try:
                name = f"{n.name.name}[{int(self.ev(n.subscript))}]"
            except CRuntimeError:
                name = None
        if name and not isinstance(v, (dict, Ptr)):
            self.event(self.line, [name, self.show(v)])

    def x_Assignment(self, n: C.Assignment):
        rhs = self.ev(n.rvalue)
        if n.op != "=":
            cur = self.get(n.lvalue)
            rhs = self.binop(n.op[:-1], cur, rhs, n)
        self.assign_to(n.lvalue, rhs)
        return self.get(n.lvalue)

    def x_UnaryOp(self, n: C.UnaryOp):
        op = n.op
        if op == "sizeof":
            return self.sizeof(n.expr)
        if op in ("++", "--", "p++", "p--"):
            cur = self.get(n.expr)
            new = self.binop("+" if "+" in op else "-", cur, 1, n)
            self.assign_to(n.expr, new)
            return cur if op.startswith("p") else self.get(n.expr)
        if op == "&":
            obj, key = self.ref(n.expr) if not (isinstance(n.expr, C.ID) and self.lookup(n.expr.name).ty.endswith("[]")) else (None, None)
            if obj is None:
                return Ptr(self.lookup(n.expr.name).cell, 0)
            return Ptr(obj, key) if isinstance(obj, list) else Ptr([obj[key]], 0)
        v = self.ev(n.expr)
        if op == "*":
            p = v
            if not isinstance(p, Ptr) or p.idx < 0 or p.idx >= len(p.obj):
                raise CRuntimeError("dereference of a null or invalid pointer")
            x = p.obj[p.idx]
            return Ptr(x, 0) if isinstance(x, list) else x
        if op == "!":
            return 0 if self.truth(v) else 1
        if op == "-":
            return self.fix(-v, n)
        if op == "+":
            return v
        if op == "~":
            return self.fix(~int(v), n)
        raise CRuntimeError(f"unsupported operator {op}")

    def sizeof(self, e) -> int:
        if isinstance(e, C.Typename):
            return self.size_of(self.tstr(e.type))
        if isinstance(e, C.ID):
            v = self.lookup(e.name)
            if v.ty.endswith("[]"):
                return len(v.cell) * self.size_of(v.elem or "int")
            return self.size_of(v.ty)
        return self.size_of(self.sty(e))

    def size_of(self, ty: str) -> int:
        ty = self.resolve(ty)
        if ty.endswith("*"):
            return 8
        if ty in T.SIZEOF:
            return T.SIZEOF[ty]
        if ty in self.structs:
            return sum(self.size_of(self.tstr(t)) for _, t in self.structs[ty])
        return 4

    def fix(self, v, n):
        if isinstance(v, int) and not isinstance(v, bool):
            return wrap(v, self.sty(n))
        return v

    def binop(self, op: str, a, b, n):
        if isinstance(a, Ptr) or isinstance(b, Ptr):
            if op in ("+", "-") and isinstance(a, Ptr) and not isinstance(b, Ptr):
                return Ptr(a.obj, a.idx + (int(b) if op == "+" else -int(b)))
            if op == "+" and isinstance(b, Ptr):
                return Ptr(b.obj, b.idx + int(a))
            if op == "-" and isinstance(a, Ptr) and isinstance(b, Ptr):
                return a.idx - b.idx
            ka = a.key() if isinstance(a, Ptr) else (0, 0) if a in (0, None) else (-1, a)
            kb = b.key() if isinstance(b, Ptr) else (0, 0) if b in (0, None) else (-1, b)
            return int({"==": ka == kb, "!=": ka != kb, "<": ka < kb, ">": ka > kb, "<=": ka <= kb, ">=": ka >= kb}[op])
        a = 0 if a is None else a
        b = 0 if b is None else b
        if op in ("==", "!=", "<", ">", "<=", ">="):
            return int({"==": a == b, "!=": a != b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op])
        fl = isinstance(a, float) or isinstance(b, float)
        if op == "+":
            r = a + b
        elif op == "-":
            r = a - b
        elif op == "*":
            r = a * b
        elif op == "/":
            if fl:
                r = (a / b) if b != 0 else (math.inf if a > 0 else -math.inf if a < 0 else math.nan)
            else:
                if b == 0:
                    raise CRuntimeError("division by zero")
                r = cdiv(a, b)
        elif op == "%":
            if b == 0:
                raise CRuntimeError("division by zero")
            r = abs(int(a)) % abs(int(b))
            r = r if a >= 0 else -r
        elif op == "<<":
            r = int(a) << (int(b) & 63)
        elif op == ">>":
            r = int(a) >> (int(b) & 63)
        elif op == "&":
            r = int(a) & int(b)
        elif op == "|":
            r = int(a) | int(b)
        elif op == "^":
            r = int(a) ^ int(b)
        else:
            raise CRuntimeError(f"unsupported operator {op}")
        return self.fix(r, n) if not fl else float(r)

    def x_BinaryOp(self, n: C.BinaryOp):
        if n.op == "&&":
            return 1 if self.truth(self.ev(n.left)) and self.truth(self.ev(n.right)) else 0
        if n.op == "||":
            return 1 if self.truth(self.ev(n.left)) or self.truth(self.ev(n.right)) else 0
        return self.binop(n.op, self.ev(n.left), self.ev(n.right), n)

    def x_TernaryOp(self, n):
        return self.ev(n.iftrue) if self.truth(self.ev(n.cond)) else self.ev(n.iffalse)

    def x_Cast(self, n):
        v = self.ev(n.expr)
        return self.conv(v, self.tstr(n.to_type))

    def x_ExprList(self, n):
        v = None
        for e in n.exprs:
            v = self.ev(e)
        return v

    def x_DeclList(self, n):
        for d in n.decls:
            self.declare(d, self.frames[-1])

    def x_FuncCall(self, n: C.FuncCall):
        if not isinstance(n.name, C.ID):
            raise CRuntimeError("calls through function pointers are not supported")
        name = n.name.name
        self.line_of(n)
        args = [self.ev(a) for a in (n.args.exprs if n.args else [])]
        if name in self.funcs:
            return self.call(self.funcs[name], args)
        if name in self.lib:
            return self.lib[name](*args)
        raise CRuntimeError(f"function '{name}' is not available in the interpreter")

    # ------------------------------------------------------------- C library
    def cstr(self, p) -> str:
        if p is None:
            return "(null)"
        if not isinstance(p, Ptr):
            return str(p)
        out = []
        for i in range(p.idx, len(p.obj)):
            c = p.obj[i]
            if c == 0:
                break
            out.append(chr(c & 255))
        return "".join(out)

    def write_str(self, p: Ptr, s: str) -> None:
        data = [ord(c) for c in s] + [0]
        for k, c in enumerate(data):
            if p.idx + k >= len(p.obj):
                raise CRuntimeError("buffer overflow (invalid memory access)")
            p.obj[p.idx + k] = c

    def fmt(self, f: str, args: list) -> str:
        out, ai = [], 0
        pos = 0
        for m in re.finditer(r"%([-+ #0]*)(\d+|\*)?(?:\.(\d+|\*))?(hh|h|ll|l|z|L)?([diouxXfeEgGcsp%])", f):
            out.append(f[pos:m.start()])
            pos = m.end()
            flags, width, prec, length, conv = m.groups()
            if conv == "%":
                out.append("%")
                continue
            if width == "*":
                width = str(int(args[ai])); ai += 1
            if prec == "*":
                prec = str(int(args[ai])); ai += 1
            if ai >= len(args):
                out.append("")
                continue
            a = args[ai]; ai += 1
            spec = "%" + flags + (width or "") + ("." + prec if prec is not None else "")
            if conv in "di":
                v = int(a) if not isinstance(a, Ptr) else id(a.obj)
                out.append((spec + "d") % v)
            elif conv in "ouxX":
                v = int(a) if not isinstance(a, (Ptr, type(None))) else 0
                bits = 64 if length in ("l", "ll", "z") else 8 if length == "hh" else 16 if length == "h" else 32
                v &= (1 << bits) - 1
                out.append((spec + conv) % v)
            elif conv in "fFeEgG":
                out.append((spec + conv) % float(a))
            elif conv == "c":
                out.append((("%" + flags + (width or "") + "s") % chr(int(a) & 255)))
            elif conv == "s":
                out.append((spec + "s") % self.cstr(a))
            elif conv == "p":
                out.append("0x" + format((id(a.obj) + a.idx) & 0xFFFFFFFFFFFF if isinstance(a, Ptr) else 0, "x"))
        out.append(f[pos:])
        return "".join(out)

    def emit(self, s: str) -> int:
        self.out.append(s)
        self.event(self.line, None, s)
        return len(s)

    def _lib(self) -> dict:
        I = self
        def printf(fmt, *a): return I.emit(I.fmt(I.cstr(fmt), list(a)))
        def fprintf(stream, fmt, *a): return I.emit(I.fmt(I.cstr(fmt), list(a))) if stream is not None else 0
        def sprintf(buf, fmt, *a):
            s = I.fmt(I.cstr(fmt), list(a)); I.write_str(buf, s); return len(s)
        def snprintf(buf, n, fmt, *a):
            s = I.fmt(I.cstr(fmt), list(a)); I.write_str(buf, s[: max(0, int(n) - 1)]); return len(s)
        def puts(s): I.emit(I.cstr(s) + "\n"); return 1
        def putchar(c): I.emit(chr(int(c) & 255)); return int(c)
        def malloc(n):
            n = int(n)
            if n < 0 or n > MAX_ALLOC: return None
            return Ptr([0] * max(1, n), 0)
        def calloc(n, size): return malloc(int(n) * int(size))
        def realloc(p, n):
            q = malloc(n)
            if isinstance(p, Ptr) and q is not None:
                for i in range(min(len(p.obj) - p.idx, len(q.obj))): q.obj[i] = p.obj[p.idx + i]
            return q
        def exit_(code): raise _Exit(int(code))
        def rand_():
            I.rand_state = (I.rand_state * 1103515245 + 12345) & 0x7FFFFFFF
            return (I.rand_state >> 16) & 0x7FFF
        def srand(seed): I.rand_state = int(seed) & 0x7FFFFFFF
        def atoi(s):
            m = re.match(r"\s*[-+]?\d+", I.cstr(s)); return int(m.group(0)) if m else 0
        def atof(s):
            m = re.match(r"\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?", I.cstr(s)); return float(m.group(0)) if m else 0.0
        def strlen(s): return len(I.cstr(s))
        def strcpy(d, s): I.write_str(d, I.cstr(s)); return d
        def strncpy(d, s, n):
            t = I.cstr(s)[: int(n)]; I.write_str(d, t.ljust(int(n), "\0")[: int(n)] if len(t) < int(n) else t); return d
        def strcat(d, s):
            I.write_str(Ptr(d.obj, d.idx + len(I.cstr(d))), I.cstr(s)); return d
        def strcmp(a, b):
            x, y = I.cstr(a), I.cstr(b); return (x > y) - (x < y)
        def strncmp(a, b, n):
            x, y = I.cstr(a)[: int(n)], I.cstr(b)[: int(n)]; return (x > y) - (x < y)
        def strchr(s, c):
            t = I.cstr(s); k = t.find(chr(int(c) & 255)); return Ptr(s.obj, s.idx + k) if k >= 0 else None
        def strstr(a, b):
            k = I.cstr(a).find(I.cstr(b)); return Ptr(a.obj, a.idx + k) if k >= 0 else None
        def memset(p, c, n):
            for i in range(int(n)):
                if p.idx + i < len(p.obj): p.obj[p.idx + i] = int(c) & 255
            return p
        def memcpy(d, s, n):
            for i in range(int(n)):
                if d.idx + i < len(d.obj) and s.idx + i < len(s.obj): d.obj[d.idx + i] = s.obj[s.idx + i]
            return d
        ch = lambda f: (lambda c: int(f(chr(int(c) & 255))))
        lib = {
            "printf": printf, "fprintf": fprintf, "sprintf": sprintf, "snprintf": snprintf, "puts": puts, "putchar": putchar,
            "getchar": lambda: -1, "scanf": lambda *a: -1, "sscanf": lambda *a: 0, "fscanf": lambda *a: -1,
            "fgets": lambda *a: None, "fputs": lambda s, st: I.emit(I.cstr(s)) and 1, "fopen": lambda *a: None, "fclose": lambda *a: 0,
            "malloc": malloc, "calloc": calloc, "realloc": realloc, "free": lambda p: None, "exit": exit_,
            "abs": lambda x: abs(int(x)), "labs": lambda x: abs(int(x)), "rand": rand_, "srand": srand, "atoi": atoi,
            "atol": atoi, "atof": atof, "strlen": strlen, "strcpy": strcpy, "strncpy": strncpy, "strcat": strcat,
            "strcmp": strcmp, "strncmp": strncmp, "strchr": strchr, "strstr": strstr, "memset": memset, "memcpy": memcpy,
            "sqrt": lambda x: math.sqrt(x) if x >= 0 else math.nan, "pow": lambda x, y: float(math.pow(x, y)),
            "sin": math.sin, "cos": math.cos, "tan": math.tan, "fabs": lambda x: abs(float(x)), "floor": lambda x: float(math.floor(x)),
            "ceil": lambda x: float(math.ceil(x)), "log": lambda x: math.log(x) if x > 0 else -math.inf, "log10": lambda x: math.log10(x) if x > 0 else -math.inf,
            "exp": math.exp, "fmod": math.fmod, "round": lambda x: float(math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)),
            "atan": math.atan, "atan2": math.atan2,
            "isalpha": ch(str.isalpha), "isdigit": ch(str.isdigit), "isalnum": ch(str.isalnum), "isspace": ch(str.isspace),
            "isupper": ch(str.isupper), "islower": ch(str.islower),
            "toupper": lambda c: ord(chr(int(c) & 255).upper()), "tolower": lambda c: ord(chr(int(c) & 255).lower()),
            "time": lambda *a: 0, "clock": lambda: 0,
        }
        return lib


class _StepLimit(Exception):
    pass


def run_program(ast: C.FileAST, source: str) -> dict:
    return Interp(ast, source).run()
