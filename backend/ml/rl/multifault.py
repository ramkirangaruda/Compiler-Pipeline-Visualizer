"""Programs with several faults at once - the setting where *choosing* the right fix
at each step matters, and so where reinforcement learning has something to learn."""
from __future__ import annotations

import random
from typing import Optional

from minic.pipeline import run_frontend

from ..mutators import MUTATORS

SEMANTIC = ["TYPO_IDENTIFIER", "MISSING_DECLARATION", "USE_BEFORE_DECLARATION", "OUT_OF_SCOPE_USE", "TYPE_MISMATCH"]
SYNTAX = ["MISSING_SEMICOLON", "MISSING_RPAREN", "MISSING_LPAREN", "MISSING_RBRACE", "MISSING_LBRACE",
          "MISSPELLED_KEYWORD", "ASSIGN_EQ_CONFUSION"]


def make_multifault(seed_src: str, k: int, rng: random.Random) -> Optional[tuple[str, list[str]]]:
    """Inject k faults into a valid program. Semantic faults go first (the program must still
    parse for the next mutator to work); an optional syntax fault goes last."""
    if k == 1:
        plan = [rng.choice(SEMANTIC + SYNTAX)]
    else:
        n_syntax = 1 if rng.random() < 0.4 else 0
        plan = [rng.choice(SEMANTIC) for _ in range(k - n_syntax)] + [rng.choice(SYNTAX) for _ in range(n_syntax)]
    cur = seed_src
    for label in plan:
        fe = run_frontend(cur)
        if fe.program is None:
            return None
        res = MUTATORS[label](fe, rng)
        if res is None:
            return None
        cur = res[0]
    if cur == seed_src or not run_frontend(cur).errors:
        return None
    return cur, plan
