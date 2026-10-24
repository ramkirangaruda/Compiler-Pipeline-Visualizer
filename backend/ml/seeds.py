"""Generator of valid MiniC seed programs. Every seed is type-correct and
terminating by construction; the error mutators later corrupt copies of them."""
from __future__ import annotations

import random

POOL = {
    "int": ["count", "total", "sum", "i", "j", "n", "k", "score", "age", "items", "limit", "steps", "result", "a", "b",
            "x", "y", "z", "num", "value", "index", "size", "lives", "level", "points", "width", "height", "base",
            "days", "years", "rounds", "first", "second", "stock", "tickets", "marks", "seats"],
    "float": ["price", "rate", "avg", "tax", "balance", "temp", "ratio", "speed", "area", "weight", "discount",
              "salary", "distance", "mean", "voltage"],
    "bool": ["flag", "done", "found", "ready", "active", "valid", "ok", "is_even", "has_more", "passed", "enabled"],
    "string": ["name", "msg", "label", "title", "city", "word", "text", "greeting", "course", "owner"],
}
STRINGS = ["hello", "world", "compiler", "robot", "ok", "done", "alice", "bob", "yudu", "pipeline", "token", "parse"]
CMP = ["<", ">", "<=", ">=", "==", "!="]
RESERVED = {"if", "else", "while", "for", "print", "int", "float", "bool", "string", "true", "false"}


class Gen:
    def __init__(self, rng: random.Random):
        self.r = rng
        self.used: set[str] = set()
        self.vars: list[list[tuple[str, str]]] = [[]]  # scope stack of (name, type)
        self.lines: list[str] = []
        self.ind = 0
        self.protected: set[str] = set()  # loop counters: never assigned by random statements

    # ----------------------------------------------------------- names
    def near_name(self, ty: str) -> str | None:
        """A new name 1-2 edits away from an existing variable of a *different*
        type - the hard cases that separate typos from genuinely new variables."""
        r = self.r
        existing = [n for scope in self.vars for n, t in scope if t != ty and len(n) >= 3]
        if not existing:
            return None
        base = r.choice(existing)
        for _ in range(10):
            i = r.randrange(len(base))
            op = r.choice(["insert", "sub", "suffix"])
            if op == "insert":
                cand = base[:i] + r.choice("aeiorstn") + base[i:]
            elif op == "sub":
                cand = base[:i] + r.choice("aeiorstn") + base[i + 1:]
            else:
                cand = base + r.choice("sx")
            if cand not in self.used and cand.isidentifier() and cand not in RESERVED:
                self.used.add(cand)
                return cand
        return None

    def fresh(self, ty: str) -> str:
        if self.r.random() < 0.18:
            n = self.near_name(ty)
            if n:
                return n
        for _ in range(30):
            n = self.r.choice(POOL[ty])
            if self.r.random() < 0.25:
                n += str(self.r.randint(1, 3))
            if n not in self.used:
                self.used.add(n)
                return n
        n = f"{ty[0]}{len(self.used)}"
        self.used.add(n)
        return n

    def visible(self, *types: str) -> list[str]:
        return [n for scope in self.vars for n, t in scope if t in types]

    def emit(self, text: str) -> None:
        self.lines.append("  " * self.ind + text)

    # ----------------------------------------------------- expressions
    def num_lit(self, ty: str) -> str:
        if ty == "float":
            return f"{self.r.randint(0, 30)}.{self.r.randint(1, 9)}"
        return str(self.r.randint(0, 40))

    def expr(self, ty: str, depth: int = 2) -> str:
        r = self.r
        if ty == "int":
            vs = self.visible("int")
            if depth <= 0 or r.random() < 0.3:
                return r.choice(vs) if vs and r.random() < 0.6 else self.num_lit("int")
            op = r.choice(["+", "-", "*", "+", "%", "/"])
            right = str(r.randint(1, 9)) if op in "%/" else self.expr("int", depth - 1)
            left = self.expr("int", depth - 1)
            e = f"{left} {op} {right}"
            return f"({e})" if depth < 2 and r.random() < 0.5 else e
        if ty == "float":
            fv = self.visible("float")
            if depth <= 0 or r.random() < 0.3:
                return r.choice(fv) if fv and r.random() < 0.6 else self.num_lit("float")
            op = r.choice(["+", "-", "*"])
            left = r.choice(fv) if fv and r.random() < 0.7 else self.num_lit("float")
            right = self.expr(r.choice(["int", "float"]), depth - 1)
            return f"{left} {op} {right}"
        if ty == "bool":
            bv = self.visible("bool")
            roll = r.random()
            if bv and roll < 0.2:
                return r.choice(bv)
            if roll < 0.28:
                return r.choice(["true", "false"])
            if roll < 0.4 and depth > 0:
                return f"{self.expr('bool', depth - 1)} {r.choice(['&&', '||'])} {self.expr('bool', depth - 1)}"
            if roll < 0.45 and bv:
                return f"!{r.choice(bv)}"
            sv = self.visible("string")
            if sv and roll < 0.5:
                return f'{r.choice(sv)} {r.choice(["==", "!="])} "{r.choice(STRINGS)}"'
            nt = r.choice(["int", "int", "float"])
            return f"{self.expr(nt, 1)} {r.choice(CMP)} {self.expr(nt if nt == 'int' else 'int', 1)}"
        sv = self.visible("string")  # string
        if sv and r.random() < 0.4:
            return r.choice(sv) + (f' + "{r.choice(STRINGS)}"' if r.random() < 0.4 else "")
        return f'"{r.choice(STRINGS)}"'

    # ------------------------------------------------------ statements
    def declare(self, ty: str | None = None, no_init: bool = False) -> str:
        r = self.r
        ty = ty or r.choices(["int", "float", "bool", "string"], [5, 2, 1.5, 1.5])[0]
        name = self.fresh(ty)
        if no_init:
            self.emit(f"{ty} {name};")
        else:
            self.emit(f"{ty} {name} = {self.expr(ty, 1)};")
        self.vars[-1].append((name, ty))
        return name

    def assign(self) -> None:
        r = self.r
        cands = [(n, t) for scope in self.vars for n, t in scope if n not in self.protected]
        if not cands:
            return
        name, ty = r.choice(cands)
        src_ty = "float" if ty == "float" and r.random() < 0.3 else ty
        if ty == "float":
            e = self.expr(r.choice(["float", "int"]), 1)
        else:
            e = self.expr(src_ty, 2)
        self.emit(f"{name} = {e};")

    def print_stmt(self) -> None:
        r = self.r
        names = [n for scope in self.vars for n, _ in scope]
        if names and r.random() < 0.7:
            self.emit(f"print({r.choice(names)});")
        else:
            ty = r.choice(["int", "string", "bool"])
            self.emit(f"print({self.expr(ty, 1)});")

    def simple(self) -> None:
        roll = self.r.random()
        if roll < 0.35:
            self.assign()
        elif roll < 0.8:
            self.print_stmt()
        else:
            self.declare()

    def body(self, n: int, depth: int) -> None:
        self.vars.append([])
        self.ind += 1
        if self.r.random() < 0.45:
            tmp = self.declare("int")
            self.emit(f"print({tmp});")
        for _ in range(n):
            self.stmt(depth)
        self.ind -= 1
        self.vars.pop()

    def if_stmt(self, depth: int) -> None:
        r = self.r
        self.emit(f"if ({self.expr('bool', 1)}) {{")
        self.body(r.randint(1, 3), depth + 1)
        while r.random() < 0.2:
            self.emit(f"}} else if ({self.expr('bool', 1)}) {{")
            self.body(r.randint(1, 2), depth + 1)
        if r.random() < 0.55:
            self.emit("} else {")
            self.body(r.randint(1, 3), depth + 1)
        self.emit("}")

    def while_stmt(self, depth: int) -> None:
        r = self.r
        counter = self.fresh("int")
        self.emit(f"int {counter} = 0;")
        self.vars[-1].append((counter, "int"))
        self.protected.add(counter)
        limit = r.randint(2, 6)
        self.emit(f"while ({counter} < {limit}) {{")
        self.vars.append([])
        self.ind += 1
        for _ in range(r.randint(1, 3)):
            self.stmt(depth + 1, allow_loops=False)
        self.emit(f"{counter} = {counter} + 1;")
        self.ind -= 1
        self.vars.pop()
        self.emit("}")

    def for_stmt(self, depth: int) -> None:
        r = self.r
        counter = self.fresh("int")
        limit = r.randint(2, 6)
        outer = r.random() < 0.4        # counter declared before the loop (and usable after it)
        if outer:
            self.emit(f"int {counter} = 0;")
            self.vars[-1].append((counter, "int"))
            head = f"for ({counter} = 0; {counter} < {limit}; {counter} = {counter} + 1)"
        else:
            head = f"for (int {counter} = 0; {counter} < {limit}; {counter} = {counter} + 1)"
        self.protected.add(counter)
        self.emit(head + " {")
        self.vars.append([] if outer else [(counter, "int")])
        self.ind += 1
        for _ in range(r.randint(1, 3)):
            self.stmt(depth + 1, allow_loops=False)
        self.ind -= 1
        self.vars.pop()
        self.emit("}")
        if outer and r.random() < 0.6:
            self.emit(f"print({counter});")

    def stmt(self, depth: int, allow_loops: bool = True) -> None:
        r = self.r
        roll = r.random()
        if depth < 2 and roll < 0.22:
            self.if_stmt(depth)
        elif depth < 2 and allow_loops and roll < 0.34:
            self.while_stmt(depth)
        elif depth < 2 and allow_loops and roll < 0.43:
            self.for_stmt(depth)
        else:
            self.simple()

    def program(self) -> str:
        r = self.r
        for _ in range(r.randint(3, 6)):
            self.declare(no_init=r.random() < 0.04)
        for ty in ("bool", "string"):
            if r.random() < 0.5:
                self.declare(ty)
        for _ in range(r.randint(5, 10)):
            self.stmt(0)
        if r.random() < 0.8:
            self.print_stmt()
        return "\n".join(self.lines) + "\n"


def generate_seed(rng: random.Random) -> str:
    return Gen(rng).program()
