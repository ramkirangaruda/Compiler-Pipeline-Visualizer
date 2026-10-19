"""The error-cause taxonomy the classifier predicts. A compiler *symptom*
(e.g. "undeclared identifier") can have several different *causes*; the ML
model's job is to tell the causes apart."""

LABELS = {
    "MISSING_SEMICOLON": {
        "title": "Missing semicolon",
        "family": "syntax",
        "explain": "A statement was not terminated with ';' before the next statement began.",
    },
    "MISSING_RPAREN": {
        "title": "Missing closing parenthesis",
        "family": "syntax",
        "explain": "An opening '(' was never matched by a closing ')'.",
    },
    "MISSING_LPAREN": {
        "title": "Missing opening parenthesis",
        "family": "syntax",
        "explain": "A ')' appears without its matching '(' - the condition or argument list is not opened.",
    },
    "MISSING_RBRACE": {
        "title": "Missing closing brace",
        "family": "syntax",
        "explain": "A block was opened with '{' but never closed with '}'.",
    },
    "MISSING_LBRACE": {
        "title": "Missing opening brace",
        "family": "syntax",
        "explain": "An if/while/else header must be followed by a '{ ... }' block.",
    },
    "MISSPELLED_KEYWORD": {
        "title": "Misspelled keyword or type",
        "family": "syntax",
        "explain": "An identifier sits where a keyword or type name was expected and is within a few edits of one.",
    },
    "ASSIGN_EQ_CONFUSION": {
        "title": "'=' and '==' confused",
        "family": "syntax",
        "explain": "Assignment '=' and comparison '==' were swapped.",
    },
    "TYPO_IDENTIFIER": {
        "title": "Misspelled variable name",
        "family": "semantic",
        "explain": "The identifier is not declared, but it is a few edits away from a variable that is in scope.",
    },
    "MISSING_DECLARATION": {
        "title": "Missing declaration",
        "family": "semantic",
        "explain": "The variable is used but never declared anywhere in the program.",
    },
    "USE_BEFORE_DECLARATION": {
        "title": "Used before declaration",
        "family": "semantic",
        "explain": "The variable is declared later in the same scope - the use comes first.",
    },
    "OUT_OF_SCOPE_USE": {
        "title": "Used outside its scope",
        "family": "semantic",
        "explain": "The variable was declared inside a block that has already closed, so it is not visible here.",
    },
    "TYPE_MISMATCH": {
        "title": "Type mismatch",
        "family": "semantic",
        "explain": "The value's type is incompatible with the variable, operator or condition it is used in.",
    },
}

LABEL_NAMES = list(LABELS.keys())

# Compiler error codes that the ML model diagnoses; everything else is rule-handled.
ML_CODES = {
    "E_EXPECTED_TOKEN", "E_UNEXPECTED_TOKEN", "E_UNEXPECTED_EOF",
    "E_UNDECLARED", "E_TYPE_MISMATCH", "E_BAD_OPERAND", "E_BAD_CONDITION",
}
