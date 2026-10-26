"""Generator of valid C seed programs. Every seed is type-correct and terminating by construction; both the
project's own C front end and gcc must accept it before it is used, and the error mutators later corrupt copies."""
from __future__ import annotations

import random

POOL = {
    "int": ["count", "total", "sum", "i", "j", "n", "k", "score", "age", "items", "limit", "steps", "result", "a", "b",
            "x", "y", "z", "num", "value", "idx", "size", "lives", "level", "points", "width", "height", "base",
            "days", "years", "rounds", "first", "second", "stock", "tickets", "marks", "seats", "len", "step"],
    "double": ["price", "rate", "avg", "tax", "balance", "temp", "ratio", "speed", "area", "weight", "discount",
               "salary", "distance", "mean", "voltage"],
    "char*": ["name", "msg", "label", "title", "city", "word", "text", "greeting", "course", "owner"],
}
STRINGS = ["hello", "world", "compiler", "robot", "ok", "done", "alice", "bob", "yudu", "pipeline", "token", "parse"]
CMP = ["<", ">", "<=", ">=", "==", "!="]
BANNED = {"if", "else", "while", "for", "do", "int", "double", "char", "float", "void", "return", "main", "printf", "sizeof",
          "len2", "exp", "log", "index", "time", "div", "abs", "rand", "round"}
HELPERS = ["compute", "scale", "combine", "clamp", "bump", "mix", "weigh", "blend"]
DHELPERS = ["average", "ratio_of", "blend_d", "lerp", "scaled"]


class Gen:
    def __init__(self, rng: random.Random):
        self.r = rng
        self.used: set[str] = set()
        self.vars: list[list[tuple[str, str]]] = [[]]
        self.arrays: dict[str, int] = {}
        self.lines: list[str] = []
        self.ind = 1
        self.protected: set[str] = set()
        self.includes = {"stdio.h"}
        self.funcs: list[tuple[str, str, list[str]]] = []   # (name, return type, param types)
        self.helper_src: list[str] = []
        self.macros: dict[str, int] = {}

    # ----------------------------------------------------------- names
    def near_name(self, ty: str) -> str | None:
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
            if cand not in self.used and cand.isidentifier() and cand not in BANNED:
                self.used.add(cand)
                return cand
        return None

    def fresh(self, ty: str) -> str:
        if self.r.random() < 0.15:
            n = self.near_name(ty)
            if n:
                return n
        for _ in range(30):
            n = self.r.choice(POOL[ty])
            if self.r.random() < 0.25:
                n += str(self.r.randint(1, 3))
            if n not in self.used and n not in BANNED:
                self.used.add(n)
                return n
        n = f"{ty[0]}v{len(self.used)}"
        self.used.add(n)
        return n

    def visible(self, *types: str) -> list[str]:
        return [n for scope in self.vars for n, t in scope if t in types]

    def emit(self, text: str) -> None:
        self.lines.append("  " * self.ind + text)

    # ----------------------------------------------------- expressions
    def lit(self, ty: str) -> str:
        if ty == "double":
            return f"{self.r.randint(0, 30)}.{self.r.randint(1, 9)}"
        return str(self.r.randint(0, 40))

    def expr(self, ty: str, depth: int = 2) -> str:
        r = self.r
        if ty == "int":
            vs = self.visible("int")
            roll = r.random()
            if depth <= 0 or roll < 0.28:
                return r.choice(vs) if vs and r.random() < 0.6 else self.lit("int")
            if roll < 0.38:
                fs = [f for f in self.funcs if f[1] == "int"]
                if fs:
                    name, _, params = r.choice(fs)
                    return f"{name}({', '.join(self.expr(p, depth - 1) for p in params)})"
            if roll < 0.45 and self.arrays:
                name = r.choice(list(self.arrays))
                return f"{name}[{r.randrange(self.arrays[name])}]"
            if roll < 0.5 and "string.h" in self.includes:
                sv = self.visible("char*")
                if sv:
                    return f"(int)strlen({r.choice(sv)})"
            op = r.choice(["+", "-", "*", "+", "%", "/"])
            right = str(r.randint(1, 9)) if op in "%/" else self.expr("int", depth - 1)
            left = self.expr("int", depth - 1)
            e = f"{left} {op} {right}"
            return f"({e})" if depth < 2 and r.random() < 0.5 else e
        if ty == "double":
            dv = self.visible("double")
            roll = r.random()
            if depth <= 0 or roll < 0.3:
                return r.choice(dv) if dv and r.random() < 0.6 else self.lit("double")
            if roll < 0.4 and "math.h" in self.includes:
                return f"sqrt({self.expr('double', depth - 1)} * {self.expr('double', depth - 1)})"
            fs = [f for f in self.funcs if f[1] == "double"]
            if roll < 0.5 and fs:
                name, _, params = r.choice(fs)
                return f"{name}({', '.join(self.expr(p, depth - 1) for p in params)})"
            op = r.choice(["+", "-", "*"])
            left = r.choice(dv) if dv and r.random() < 0.7 else self.lit("double")
            right = self.expr(r.choice(["int", "double"]), depth - 1)
            if " " in right:
                right = f"({right})"
            return f"{left} {op} {right}"
        if ty == "cond":
            roll = r.random()
            if roll < 0.12 and depth > 0:
                return f"{self.expr('cond', depth - 1)} {r.choice(['&&', '||'])} {self.expr('cond', depth - 1)}"
            sv = self.visible("char*")
            if roll < 0.25 and sv and "string.h" in self.includes:
                return f'strcmp({r.choice(sv)}, "{r.choice(STRINGS)}") {r.choice(["==", "!="])} 0'
            if roll < 0.3 and self.visible("int"):
                return f"!{r.choice(self.visible('int'))}" if r.random() < 0.3 else r.choice(self.visible("int"))
            nt = r.choice(["int", "int", "double"])
            return f"{self.expr(nt, 1)} {r.choice(CMP[:4] + ['!='])} {self.expr(nt, 1)}"
        return f'"{r.choice(STRINGS)}"'

    # ------------------------------------------------------ statements
    def declare(self, ty: str | None = None, no_init: bool = False) -> str:
        r = self.r
        ty = ty or r.choices(["int", "double", "char*"], [6, 2.5, 1.5])[0]
        name = self.fresh(ty)
        star = "*" if ty == "char*" else ""
        base = "char" if ty == "char*" else ty
        space = " " if not star else " *"
        if ty == "char*":
            self.emit(f'{base}{space}{name} = "{r.choice(STRINGS)}";')
        elif no_init:
            self.emit(f"{base} {name};")
        else:
            self.emit(f"{base} {name} = {self.expr(ty, 1)};")
        self.vars[-1].append((name, ty))
        return name

    def array_decl(self) -> None:
        r = self.r
        name = self.fresh("int")
        size = r.randint(3, 6)
        if r.random() < 0.5:
            items = ", ".join(str(r.randint(0, 20)) for _ in range(size))
            self.emit(f"int {name}[{size}] = {{{items}}};")
        else:
            self.emit(f"int {name}[{size}];")
            ctr = self.fresh("int")
            self.emit(f"int {ctr};")
            self.vars[-1].append((ctr, "int"))
            self.protected.add(ctr)
            self.emit(f"for ({ctr} = 0; {ctr} < {size}; {ctr}++) {{")
            self.ind += 1
            self.emit(f"{name}[{ctr}] = {ctr} * {r.randint(1, 5)} + {r.randint(0, 3)};")
            self.ind -= 1
            self.emit("}")
        self.arrays[name] = size
        self.protected.add(name)

    def assign(self) -> None:
        r = self.r
        cands = [(n, t) for scope in self.vars for n, t in scope if n not in self.protected and t != "char*"]
        if not cands:
            return
        name, ty = r.choice(cands)
        if r.random() < 0.2 and ty == "int":
            self.emit(r.choice([f"{name}++;", f"{name} += {self.expr('int', 1)};", f"{name} -= {r.randint(1, 5)};"]))
        else:
            self.emit(f"{name} = {self.expr(ty, 2)};")

    def printf_stmt(self) -> None:
        r = self.r
        names = [(n, t) for scope in self.vars for n, t in scope if t in ("int", "double", "char*")]
        k = r.choice([1, 1, 2])
        picks = r.sample(names, min(k, len(names))) if names else []
        if picks and r.random() < 0.8:
            fmt = " ".join(f"{n}=" + {"int": "%d", "double": "%.2f", "char*": "%s"}[t] for n, t in picks)
            self.emit(f'printf("{fmt}\\n", {", ".join(n for n, _ in picks)});')
        else:
            ty = r.choice(["int", "double"])
            self.emit(f'printf("{"%d" if ty == "int" else "%.2f"}\\n", {self.expr(ty, 1)});')

    def call_stmt(self) -> None:
        voids = [f for f in self.funcs if f[1] == "void"]
        if not voids:
            return self.printf_stmt()
        name, _, params = self.r.choice(voids)
        self.emit(f"{name}({', '.join(self.expr(p, 1) for p in params)});")

    def pointer_use(self) -> None:
        r = self.r
        ints = [n for n in self.visible("int") if n not in self.protected]
        if not ints:
            return
        target = r.choice(ints)
        p = self.fresh("int")
        self.emit(f"int *{p} = &{target};")
        self.vars[-1].append((p, "int*"))
        self.protected.add(p)
        self.emit(f"*{p} = *{p} + {r.randint(1, 9)};")
        self.emit(f'printf("%d\\n", *{p});')

    def simple(self) -> None:
        roll = self.r.random()
        if roll < 0.3:
            self.assign()
        elif roll < 0.72:
            self.printf_stmt()
        elif roll < 0.8:
            self.call_stmt()
        elif roll < 0.86:
            self.pointer_use()
        else:
            self.declare()

    def body(self, n: int, depth: int) -> None:
        self.vars.append([])
        self.ind += 1
        if self.r.random() < 0.45:
            tmp = self.declare("int")
            self.emit(f'printf("%d\\n", {tmp});')
        for _ in range(n):
            self.stmt(depth)
        self.ind -= 1
        self.vars.pop()

    def if_stmt(self, depth: int) -> None:
        r = self.r
        self.emit(f"if ({self.expr('cond', 1)}) {{")
        self.body(r.randint(1, 3), depth + 1)
        while r.random() < 0.2:
            self.emit(f"}} else if ({self.expr('cond', 1)}) {{")
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
        self.emit(f"while ({counter} < {r.randint(2, 6)}) {{")
        self.vars.append([])
        self.ind += 1
        for _ in range(r.randint(1, 3)):
            self.stmt(depth + 1, allow_loops=False)
        self.emit(f"{counter}++;")
        self.ind -= 1
        self.vars.pop()
        self.emit("}")

    def for_stmt(self, depth: int) -> None:
        r = self.r
        counter = self.fresh("int")
        limit = r.randint(2, 6)
        outer = r.random() < 0.4          # counter declared before the loop and still usable afterwards
        if outer:
            self.emit(f"int {counter};")
            self.vars[-1].append((counter, "int"))
            head = f"for ({counter} = 0; {counter} < {limit}; {counter}++)"
        else:
            head = f"for (int {counter} = 0; {counter} < {limit}; {counter}++)"
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
            self.emit(f'printf("%d\\n", {counter});')

    def stmt(self, depth: int, allow_loops: bool = True) -> None:
        roll = self.r.random()
        if depth < 2 and roll < 0.2:
            self.if_stmt(depth)
        elif depth < 2 and allow_loops and roll < 0.34:
            self.while_stmt(depth)
        elif depth < 2 and allow_loops and roll < 0.5:
            self.for_stmt(depth)
        else:
            self.simple()

    # -------------------------------------------------------- helpers
    def make_helper(self) -> None:
        r = self.r
        kind = r.choices(["int", "double", "void"], [5, 2, 2])[0]
        pool = HELPERS if kind != "double" else DHELPERS
        name = next((n for n in r.sample(pool, len(pool)) if n not in self.used), None)
        if name is None:
            return
        self.used.add(name)
        n = r.randint(1, 3)
        ptypes = [("double" if kind == "double" and r.random() < 0.7 else "int") for _ in range(n)]
        pnames = r.sample(["a", "b", "c", "p", "q", "m", "w"], n)
        params = ", ".join(f"{t} {pn}" for t, pn in zip(ptypes, pnames))
        if kind == "void":
            body = [f'printf("{pnames[0]}=%{"d" if ptypes[0] == "int" else ".2f"}\\n", {pnames[0]});']
        else:
            terms = [pnames[0]] + [f"{r.choice(pnames)} {r.choice(['+', '*', '-'])} {r.randint(1, 5)}" for _ in range(r.randint(0, 1))]
            expr = " + ".join(terms)
            if kind == "int":
                body = [f"return {expr};"]
            else:
                body = [f"return {expr} / 2.0;"]
        text = [f"{kind} {name}({params}) {{"] + [f"  {b}" for b in body] + ["}", ""]
        self.helper_src.extend(text)
        self.funcs.append((name, kind, ptypes))

    def program(self) -> str:
        r = self.r
        if r.random() < 0.3:
            m = r.choice(["LIMIT", "SIZE", "MAXN", "ROUNDS"])
            self.macros[m] = r.randint(3, 9)
            self.used.add(m)
        if r.random() < 0.3:
            self.includes.add("stdlib.h")
        if r.random() < 0.35:
            self.includes.add("string.h")
        if r.random() < 0.3:
            self.includes.add("math.h")
        for _ in range(r.choices([0, 1, 2], [4, 4, 2])[0]):
            self.make_helper()
        for _ in range(r.randint(3, 6)):
            self.declare()
        if "string.h" in self.includes and not self.visible("char*"):
            self.declare("char*")
        if r.random() < 0.35:
            self.array_decl()
        for _ in range(r.randint(5, 10)):
            self.stmt(0)
        if r.random() < 0.8:
            self.printf_stmt()
        self.emit("return 0;")
        head = [f"#include <{h}>" for h in sorted(self.includes, key=lambda h: (h != "stdio.h", h))]
        head += [f"#define {k} {v}" for k, v in self.macros.items()]
        out = head + [""] + self.helper_src + ["int main(void) {"] + self.lines + ["}"]
        text = "\n".join(out) + "\n"
        for k in self.macros:   # a macro is only useful if something uses it
            if text.count(k) == 1:
                text = text.replace(f"#define {k} {self.macros[k]}\n", "")
        return text


def generate_seed(rng: random.Random) -> str:
    return Gen(rng).program()
