"""Hand-written, first-match rule baseline for C: what a compiler author would write without ML."""
from __future__ import annotations


def predict(f: dict) -> str:
    code = f["err_code"]
    if code in ("E_TYPE_MISMATCH", "E_BAD_OPERAND"):
        return "TYPE_MISMATCH"
    if code == "E_MISSING_INCLUDE":
        return "MISSING_INCLUDE"
    if code == "E_WRONG_ARGC":
        return "WRONG_ARG_COUNT"
    if code == "E_UNDECLARED":
        if 0 <= f["sem_min_dist_visible"] <= 2:
            return "TYPO_IDENTIFIER"
        if f["sem_declared_later"]:
            return "USE_BEFORE_DECLARATION"
        if f["sem_closed_scope"]:
            return "OUT_OF_SCOPE_USE"
        return "MISSING_DECLARATION"

    if code == "E_UNEXPECTED_EOF":
        return "MISSING_RBRACE"
    expected = set(f["expected"].split("|")) if f["expected"] != "NA" else set()
    found = f["found"]
    if ";" in expected:
        return "ASSIGN_EQ_CONFUSION" if found == "==" else "MISSING_SEMICOLON"
    if ")" in expected:
        return "ASSIGN_EQ_CONFUSION" if found == "=" else "MISSING_RPAREN"
    if "(" in expected:
        return "MISSING_LPAREN"
    if "}" in expected:
        return "MISSING_RBRACE"
    if "{" in expected:
        return "MISSING_LBRACE"
    if "=" in expected:
        return "ASSIGN_EQ_CONFUSION" if found == "==" else "MISSPELLED_KEYWORD"
    if found == "else":
        return "MISSING_RBRACE"
    return "MISSING_SEMICOLON"
