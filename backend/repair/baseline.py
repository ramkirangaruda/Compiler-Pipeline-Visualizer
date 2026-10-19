"""Hand-written, first-match rule baseline. This is what a compiler author would
write without ML; the dashboard compares it against the learned classifier."""
from __future__ import annotations


def predict(f: dict) -> str:
    code = f["err_code"]
    if code in ("E_TYPE_MISMATCH", "E_BAD_OPERAND", "E_BAD_CONDITION"):
        return "TYPE_MISMATCH"
    if code == "E_UNDECLARED":
        if 0 <= f["sem_min_dist_visible"] <= 2:
            return "TYPO_IDENTIFIER"
        if f["sem_declared_later"]:
            return "USE_BEFORE_DECLARATION"
        if f["sem_closed_scope"]:
            return "OUT_OF_SCOPE_USE"
        return "MISSING_DECLARATION"

    expected, found = f["expected"], f["found"]
    if expected == ";":
        return "ASSIGN_EQ_CONFUSION" if found == "==" else "MISSING_SEMICOLON"
    if expected == ")":
        return "ASSIGN_EQ_CONFUSION" if found == "=" else "MISSING_RPAREN"
    if expected == "(":
        return "MISSING_LPAREN"
    if expected == "}":
        return "MISSING_RBRACE"
    if expected == "{":
        return "MISSING_LBRACE"
    if expected == "=":
        return "ASSIGN_EQ_CONFUSION" if found == "==" else "MISSPELLED_KEYWORD"
    if found == "else":
        return "MISSING_RBRACE"
    return "MISSING_SEMICOLON"
