"""Error-cause taxonomy for real C: the twelve MiniC causes plus two that only exist in C
(a forgotten `#include`, a call with the wrong number of arguments)."""
from .labels import LABELS as _MINIC

LABELS = {k: dict(v) for k, v in _MINIC.items()}
LABELS["MISSING_INCLUDE"] = {
    "title": "Missing #include",
    "family": "semantic",
    "explain": "A standard-library function or constant is used, but the header that declares it is not included.",
}
LABELS["WRONG_ARG_COUNT"] = {
    "title": "Wrong number of arguments",
    "family": "semantic",
    "explain": "The call passes more or fewer arguments than the function's declaration accepts.",
}
LABELS["OUT_OF_SCOPE_USE"]["explain"] = "The variable was declared inside a block (or a for-loop header) that has already ended."
LABELS["MISSPELLED_KEYWORD"]["explain"] = "An identifier sits where a C keyword or type name was expected and is within a few edits of one."

LABEL_NAMES = list(LABELS.keys())

ML_CODES = {
    "E_EXPECTED_TOKEN", "E_UNEXPECTED_TOKEN", "E_UNEXPECTED_EOF",
    "E_UNDECLARED", "E_TYPE_MISMATCH", "E_BAD_OPERAND", "E_MISSING_INCLUDE", "E_WRONG_ARGC",
}

SYNTAX_CAUSES = [k for k, v in LABELS.items() if v["family"] == "syntax"]

CANDIDATE_CAUSES = {
    "E_EXPECTED_TOKEN": SYNTAX_CAUSES,
    "E_UNEXPECTED_TOKEN": SYNTAX_CAUSES,
    "E_UNEXPECTED_EOF": SYNTAX_CAUSES,
    "E_UNDECLARED": ["TYPO_IDENTIFIER", "MISSING_DECLARATION", "USE_BEFORE_DECLARATION", "OUT_OF_SCOPE_USE"],
    "E_TYPE_MISMATCH": ["TYPE_MISMATCH"],
    "E_BAD_OPERAND": ["TYPE_MISMATCH"],
    "E_MISSING_INCLUDE": ["MISSING_INCLUDE"],
    "E_WRONG_ARGC": ["WRONG_ARG_COUNT"],
}
