"""Feature extraction for real C. Same idea as repair/features.py - everything the compiler knew at the
moment of failure - with the C-specific facts (header map, call arity, pointer/array types) added."""
from __future__ import annotations

from cfront import ctypes_ as T
from cfront.lexer import RESERVED
from cfront.prelude import HEADER_OF
from minic.tokens import Diagnostic, Token
from minic.util import edit_distance

from .features import token_index_at

CAT_COLUMNS = [
    "err_stage", "err_code", "ctx", "expected", "found",
    "prev1", "prev2", "prev3", "prev4", "prev5", "next1",
    "ty_kind", "ty_target", "ty_expr", "c_header",
]
NUM_COLUMNS = [
    "nl_before_found", "found_first_on_line", "line_ratio", "token_ratio",
    "paren_bal_before", "brace_bal_before", "paren_bal_total", "brace_bal_total",
    "prev1_kw_dist", "prev1_len", "prev1_is_ident",
    "sem_name_len", "sem_min_dist_visible", "sem_min_ratio_visible", "sem_n_close_visible",
    "sem_min_dist_all", "sem_declared_later", "sem_closed_scope", "sem_n_visible",
    "sem_min_dist_keyword", "sem_lvalue", "sem_same_first_char", "sem_len_diff_nearest", "sem_nearest_compat",
    "ty_both_numeric", "ty_expr_literal",
    "n_expected", "expects_ident", "bracket_bal_before", "c_is_call", "c_header_known",
    "c_argc_given", "c_argc_expected", "c_argc_diff", "c_closed_in_for",
]
FEATURE_COLUMNS = CAT_COLUMNS + NUM_COLUMNS


def _cls(tok: Token | None) -> str:
    return tok.cls if tok is not None else "NONE"


def _compatible(a: str, b: str) -> bool:
    return a == b or (T.is_num(a) and T.is_num(b)) or (T.is_pointer(a) and T.is_pointer(b))


def extract(d: Diagnostic, fe) -> dict:
    toks = fe.tokens
    ex = d.extra
    idx = ex["found_index"] if d.stage == "syntax" else token_index_at(toks, d.start)
    idx = max(0, min(idx, len(toks) - 1))
    found = toks[idx]
    prevs = [toks[idx - k] if idx - k >= 0 else None for k in range(1, 6)]
    nxt = toks[idx + 1] if idx + 1 < len(toks) else None
    last_line = max(1, toks[-1].line)

    f: dict = {c: "NA" for c in CAT_COLUMNS}
    f.update({c: -1 for c in NUM_COLUMNS})

    f["err_stage"] = d.stage
    f["err_code"] = d.code
    f["ctx"] = ex.get("ctx", "semantic")
    f["expected"] = "|".join(ex["expected"]) if ex.get("expected") else "NA"
    f["found"] = _cls(found)
    for k, p in enumerate(prevs, start=1):
        f[f"prev{k}"] = _cls(p)
    f["next1"] = _cls(nxt)

    p1 = prevs[0]
    f["nl_before_found"] = int(p1 is not None and found.line > p1.line)
    f["found_first_on_line"] = int(p1 is None or found.line != p1.line)
    f["line_ratio"] = round(found.line / last_line, 4)
    f["token_ratio"] = round(idx / max(1, len(toks) - 1), 4)

    def balance(upto: int, op: str, cl: str) -> int:
        return sum(1 if t.value == op else -1 if t.value == cl else 0 for t in toks[:upto] if t.kind == "PUNCT")

    f["paren_bal_before"] = balance(idx, "(", ")")
    f["brace_bal_before"] = balance(idx, "{", "}")
    f["bracket_bal_before"] = balance(idx, "[", "]")
    f["paren_bal_total"] = balance(len(toks), "(", ")")
    f["brace_bal_total"] = balance(len(toks), "{", "}")

    is_ident = p1 is not None and p1.kind == "IDENT"
    f["prev1_is_ident"] = int(is_ident)
    f["prev1_len"] = len(p1.value) if p1 is not None else 0
    f["prev1_kw_dist"] = min(edit_distance(p1.value, k) for k in RESERVED) if is_ident else 99
    if d.stage == "syntax":
        f["n_expected"] = ex.get("n_expected", -1)
        f["expects_ident"] = int(bool(ex.get("expects_ident")))

    if d.code in ("E_UNDECLARED", "E_MISSING_INCLUDE"):
        name = ex["name"]
        f["sem_name_len"] = len(name)
        f["sem_lvalue"] = int(ex["lvalue"])
        f["c_is_call"] = int(bool(ex.get("is_call")))
        f["c_header_known"] = int(name in HEADER_OF)
        f["sem_min_dist_keyword"] = min(edit_distance(name, k) for k in RESERVED)
    if d.code == "E_MISSING_INCLUDE":
        f["c_header"] = ex["header"]
    elif d.code == "E_UNDECLARED":
        vis = ex["visible"]
        f["sem_n_visible"] = ex["n_visible"]
        name = ex["name"]
        if vis:
            nearest, dist = vis[0]
            f["sem_min_dist_visible"] = dist
            f["sem_min_ratio_visible"] = round(dist / max(len(name), len(nearest)), 4)
            f["sem_same_first_char"] = int(nearest[:1] == name[:1])
            f["sem_len_diff_nearest"] = abs(len(nearest) - len(name))
        else:
            f["sem_min_dist_visible"] = 99
            f["sem_min_ratio_visible"] = 1.0
            f["sem_same_first_char"] = 0
            f["sem_len_diff_nearest"] = len(name)
        hint = ex.get("hint_type")
        if vis and hint and ex.get("hint_strong"):
            f["sem_nearest_compat"] = int(_compatible(ex["visible_types"][vis[0][0]], hint))
        f["sem_n_close_visible"] = sum(1 for _, dist in vis if dist <= 2)
        f["sem_min_dist_all"] = ex["min_dist_all"]
        f["sem_declared_later"] = int(ex["declared_later"])
        f["sem_closed_scope"] = int(ex["closed_scope"])
        cd = ex.get("closed_decl")
        if cd and fe.sem is not None:
            f["c_closed_in_for"] = int(fe.sem.scopes[cd["scope_id"]].kind == "for")
        f["c_argc_given"] = ex.get("argc", -1) if ex.get("is_call") else -1
    elif d.code == "E_WRONG_ARGC":
        f["c_is_call"] = 1
        f["c_argc_given"] = ex["given"]
        f["c_argc_expected"] = ex["n_params"]
        f["c_argc_diff"] = ex["given"] - ex["n_params"]
        f["sem_name_len"] = len(ex["name"])
    elif d.code == "E_TYPE_MISMATCH":
        f["ty_kind"] = ex["kind"]
        f["ty_target"] = ex["target_type"]
        f["ty_expr"] = ex["expr_type"]
        f["ty_both_numeric"] = int(T.is_num(ex["target_type"]) and T.is_num(ex["expr_type"]))
        f["ty_expr_literal"] = int(ex["expr_literal"])
    elif d.code == "E_BAD_OPERAND":
        f["ty_kind"] = "operand:" + ex["op"]
        f["ty_target"] = ex["left_type"]
        f["ty_expr"] = ex["right_type"] or "NA"
        f["ty_both_numeric"] = int(T.is_num(ex["left_type"]) and T.is_num(ex["right_type"] or "x"))
        f["ty_expr_literal"] = int(bool(ex.get("left_literal") or ex.get("right_literal")))
    return f
