"""Recursive-descent parser for the MiniC grammar (LL(1) apart from the
`else if` chain). On the first syntax error it raises ParseError carrying a
Diagnostic whose `extra` field records what the parser knew at that moment:
expected tokens, the parse context (which production we were inside) and the
index of the offending token. Those facts are the raw material of the ML
feature extractor.

    program   -> stmt* EOF
    stmt      -> decl | assign | print | if | while | block
    decl      -> TYPE IDENT ( '=' expr )? ';'
    assign    -> IDENT '=' expr ';'
    print     -> 'print' '(' expr ')' ';'
    if        -> 'if' '(' expr ')' block ( 'else' ( if | block ) )?
    while     -> 'while' '(' expr ')' block
    block     -> '{' stmt* '}'
    expr      -> or ; or -> and ('||' and)* ; and -> eq ('&&' eq)*
    eq        -> rel (('=='|'!=') rel)* ; rel -> add (('<'|'>'|'<='|'>=') add)*
    add       -> mul (('+'|'-') mul)* ; mul -> unary (('*'|'/'|'%') unary)*
    unary     -> ('-'|'!') unary | primary
    primary   -> INT | FLOAT | STRING | BOOL | IDENT | '(' expr ')'
"""
from __future__ import annotations

from . import ast as A
from .tokens import Diagnostic, Token


class ParseError(Exception):
    def __init__(self, diag: Diagnostic):
        super().__init__(diag.message)
        self.diag = diag


class Parser:
    def __init__(self, tokens: list[Token]):
        self.toks = tokens
        self.i = 0

    # ------------------------------------------------------------ helpers
    @property
    def cur(self) -> Token:
        return self.toks[self.i]

    def at(self, kind: str, value: str | None = None) -> bool:
        t = self.cur
        return t.kind == kind and (value is None or t.value == value)

    def advance(self) -> Token:
        t = self.toks[self.i]
        if t.kind != "EOF":
            self.i += 1
        return t

    def fail(self, expected: list[str], ctx: str, unexpected: bool = False) -> ParseError:
        t = self.cur
        found = "end of file" if t.kind == "EOF" else repr(t.value)
        if t.kind == "EOF":
            code = "E_UNEXPECTED_EOF"
        elif unexpected:
            code = "E_UNEXPECTED_TOKEN"
        else:
            code = "E_EXPECTED_TOKEN"
        exp = " or ".join(repr(e) if not e[0].isalpha() or e in ("else",) else e for e in expected)
        msg = f"Syntax error: expected {exp} but found {found} on line {t.line}"
        prev = self.toks[self.i - 1] if self.i > 0 else None
        return ParseError(
            Diagnostic(
                "syntax", code, msg, t.line, t.col, t.start, max(t.end, t.start + 1),
                extra={
                    "expected": expected,
                    "ctx": ctx,
                    "found_index": self.i,
                    "found": t.cls,
                    "found_value": t.value,
                    "prev_end": prev.end if prev else 0,
                    "prev_line": prev.line if prev else 1,
                },
            )
        )

    def expect(self, kind: str, value: str | None = None, ctx: str = "") -> Token:
        if not self.at(kind, value):
            raise self.fail([value or kind], ctx)
        return self.advance()

    @staticmethod
    def span(node: A.Node, first: Token, last: Token) -> A.Node:
        node.line, node.col, node.start, node.end = first.line, first.col, first.start, last.end
        return node

    # --------------------------------------------------------- statements
    def parse_program(self) -> A.Program:
        body = []
        first = self.cur
        while not self.at("EOF"):
            body.append(self.parse_statement())
        prog = A.Program(body=body)
        prog.line, prog.start, prog.end = 1, 0, self.cur.end
        return prog

    def parse_statement(self) -> A.Node:
        t = self.cur
        if t.kind == "TYPE":
            return self.parse_decl()
        if t.kind == "KEYWORD":
            if t.value == "if":
                return self.parse_if()
            if t.value == "while":
                return self.parse_while()
            if t.value == "print":
                return self.parse_print()
            raise self.fail(["statement"], "statement", unexpected=True)  # stray 'else'
        if t.kind == "PUNCT" and t.value == "{":
            return self.parse_block()
        if t.kind == "IDENT":
            return self.parse_assign()
        raise self.fail(["statement"], "statement", unexpected=True)

    def parse_decl(self) -> A.VarDecl:
        ty = self.advance()
        name = self.expect("IDENT", ctx="decl_name")
        init = None
        if self.at("OP", "="):
            self.advance()
            init = self.parse_expr()
        semi = self.expect("PUNCT", ";", ctx="decl_end")
        node = A.VarDecl(
            vtype=ty.value, name=name.value, init=init,
            type_start=ty.start, type_end=ty.end, name_start=name.start, name_end=name.end,
        )
        return self.span(node, ty, semi)

    def parse_assign(self) -> A.Assign:
        name = self.advance()
        self.expect("OP", "=", ctx="assign_op")
        value = self.parse_expr()
        semi = self.expect("PUNCT", ";", ctx="assign_end")
        node = A.Assign(name=name.value, value=value, name_start=name.start, name_end=name.end)
        return self.span(node, name, semi)

    def parse_print(self) -> A.Print:
        kw = self.advance()
        self.expect("PUNCT", "(", ctx="print_open")
        value = self.parse_expr()
        self.expect("PUNCT", ")", ctx="print_close")
        semi = self.expect("PUNCT", ";", ctx="print_end")
        return self.span(A.Print(value=value), kw, semi)

    def parse_block(self, ctx: str = "block_open") -> A.Block:
        lb = self.expect("PUNCT", "{", ctx=ctx)
        body = []
        while not self.at("PUNCT", "}"):
            if self.at("EOF"):
                raise self.fail(["}"], "block_close")
            body.append(self.parse_statement())
        rb = self.advance()
        return self.span(A.Block(body=body), lb, rb)

    def parse_cond(self, kw: str) -> A.Expr:
        self.expect("PUNCT", "(", ctx=f"{kw}_open")
        cond = self.parse_expr()
        self.expect("PUNCT", ")", ctx=f"{kw}_close")
        return cond

    def parse_if(self) -> A.If:
        kw = self.advance()
        cond = self.parse_cond("if")
        then = self.parse_block()
        alt = None
        last = then
        if self.at("KEYWORD", "else"):
            self.advance()
            alt = self.parse_if() if self.at("KEYWORD", "if") else self.parse_block("else_block_open")
            last = alt
        node = A.If(cond=cond, then=then, alt=alt)
        node.line, node.col, node.start, node.end = kw.line, kw.col, kw.start, last.end
        return node

    def parse_while(self) -> A.While:
        kw = self.advance()
        cond = self.parse_cond("while")
        body = self.parse_block()
        node = A.While(cond=cond, body=body)
        node.line, node.col, node.start, node.end = kw.line, kw.col, kw.start, body.end
        return node

    # -------------------------------------------------------- expressions
    def parse_expr(self) -> A.Expr:
        return self._binary(self.parse_and, ("||",))

    def parse_and(self) -> A.Expr:
        return self._binary(self.parse_eq, ("&&",))

    def parse_eq(self) -> A.Expr:
        return self._binary(self.parse_rel, ("==", "!="))

    def parse_rel(self) -> A.Expr:
        return self._binary(self.parse_add, ("<", ">", "<=", ">="))

    def parse_add(self) -> A.Expr:
        return self._binary(self.parse_mul, ("+", "-"))

    def parse_mul(self) -> A.Expr:
        return self._binary(self.parse_unary, ("*", "/", "%"))

    def _binary(self, sub, ops) -> A.Expr:
        left = sub()
        while self.cur.kind == "OP" and self.cur.value in ops:
            op = self.advance()
            right = sub()
            node = A.Binary(op=op.value, left=left, right=right)
            node.line, node.col, node.start, node.end = left.line, left.col, left.start, right.end
            left = node
        return left

    def parse_unary(self) -> A.Expr:
        if self.cur.kind == "OP" and self.cur.value in ("-", "!"):
            op = self.advance()
            operand = self.parse_unary()
            node = A.Unary(op=op.value, operand=operand)
            node.line, node.col, node.start, node.end = op.line, op.col, op.start, operand.end
            return node
        return self.parse_primary()

    def parse_primary(self) -> A.Expr:
        t = self.cur
        if t.kind in ("INT", "FLOAT", "STRING", "BOOL"):
            self.advance()
            return self.span(A.Literal(kind=t.kind, value=t.value), t, t)
        if t.kind == "IDENT":
            self.advance()
            return self.span(A.Ident(name=t.value), t, t)
        if t.kind == "PUNCT" and t.value == "(":
            lp = self.advance()
            e = self.parse_expr()
            self.expect("PUNCT", ")", ctx="paren_close")
            return e
        raise self.fail(["expression"], "expr", unexpected=True)


def parse(tokens: list[Token]) -> tuple[A.Program | None, Diagnostic | None]:
    try:
        return Parser(tokens).parse_program(), None
    except ParseError as e:
        return None, e.diag
