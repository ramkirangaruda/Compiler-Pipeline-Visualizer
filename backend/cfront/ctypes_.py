"""C types as normalised strings, and the compatibility rules the checker uses.

Types are plain strings: 'int', 'unsigned int', 'double', 'char*', 'int[]', 'struct P', 'function' ...
Qualifiers (const, volatile) are dropped; arrays are kept as 'T[]' and decay to pointers when compared.
"""
from __future__ import annotations

INT_TYPES = {
    "char", "signed char", "unsigned char", "short", "unsigned short", "int", "unsigned int", "unsigned",
    "long", "unsigned long", "long long", "unsigned long long", "bool", "_Bool",
}
FLOAT_TYPES = {"float", "double", "long double"}
NUMERIC = INT_TYPES | FLOAT_TYPES

# size in bytes (used by sizeof in the interpreter) and bit width for integer wrap-around
SIZEOF = {"char": 1, "signed char": 1, "unsigned char": 1, "short": 2, "unsigned short": 2, "int": 4, "unsigned int": 4,
          "unsigned": 4, "long": 8, "unsigned long": 8, "long long": 8, "unsigned long long": 8, "float": 4, "double": 8,
          "long double": 16, "bool": 1, "_Bool": 1}
BITS = {"char": 8, "signed char": 8, "unsigned char": 8, "short": 16, "unsigned short": 16, "int": 32, "unsigned int": 32,
        "unsigned": 32, "long": 64, "unsigned long": 64, "long long": 64, "unsigned long long": 64, "bool": 8, "_Bool": 8}


_QUALS = ("const", "volatile", "register", "static", "extern", "auto", "inline", "restrict")


def canonical(names: list[str]) -> str:
    """['unsigned', 'int'] -> 'unsigned int', ['long', 'long', 'int'] -> 'long long', ['size_t'] -> 'size_t'."""
    n = [x for x in names if x not in _QUALS]
    unsigned, signed = "unsigned" in n, "signed" in n
    longs = n.count("long")
    n = [x for x in n if x not in ("unsigned", "signed", "long")]
    if len(n) > 1:
        n = [x for x in n if x != "int"]
    base = n[0] if n else "int"
    if longs and base == "double":
        return "long double"
    if base == "int":
        base = "long long" if longs >= 2 else "long" if longs == 1 else "int"
    if unsigned:
        return f"unsigned {base}"
    if signed and base == "char":
        return "signed char"
    return base


def is_pointer(t: str) -> bool:
    return t.endswith("*") or t.endswith("[]")


def decay(t: str) -> str:
    return t[:-2] + "*" if t.endswith("[]") else t


def is_int(t: str) -> bool:
    return t in INT_TYPES or (t.startswith("enum ") and not t.endswith(("*", "[]")))


def is_float(t: str) -> bool:
    return t in FLOAT_TYPES


def is_num(t: str) -> bool:
    return is_int(t) or is_float(t)


def pointee(t: str) -> str:
    t = decay(t)
    return t[:-1] if t.endswith("*") else "unknown"


def default_value(t: str) -> str:
    t = decay(t)
    if t in ("float", "double", "long double"):
        return "0.0"
    if t == "char*":
        return '""'
    if t.endswith("*"):
        return "NULL"
    if t in ("bool", "_Bool"):
        return "0"
    return "0"


def decl_text(t: str, name: str) -> str:
    """`int x = 0;` / `char *s = "";` / `double d = 0.0;`"""
    t = decay(t)
    if t.endswith("*"):
        return f"{t[:-1].rstrip()} *{name} = {default_value(t)};"
    return f"{t} {name} = {default_value(t)};"


def compat(target: str, value: str, literal_zero: bool = False, is_string_literal: bool = False) -> str | None:
    """None if `value` may be assigned to `target`, else a short reason."""
    if "unknown" in (target, value) or target == "function" or value == "function" or target == "initlist" or value == "initlist":
        return None
    target, value = decay(target), decay(value)
    if target == value:
        return None
    if is_num(target) and is_num(value):
        return None
    if (target.startswith(("struct ", "union ")) and not target.endswith("*")) or (value.startswith(("struct ", "union ")) and not value.endswith("*")):
        return None if target == value else "incompatible aggregate types"
    if target.endswith("*"):
        if is_int(value):
            return None if literal_zero else "integer to pointer without a cast"
        if value.endswith("*"):
            if "void*" in (target, value) or pointee(target) == pointee(value):
                return None
            if is_string_literal and pointee(target) in ("char", "unsigned char", "signed char"):
                return None
            return "incompatible pointer types"
        if is_float(value):
            return "floating-point to pointer"
        return None
    if value.endswith("*"):
        if is_num(target):
            return "pointer to integer without a cast"
        return None
    return None
