"""The repair MDP.

state   : a broken program (summarised by the candidate fixes the engine proposes for its first error)
action  : apply one of those candidate fixes
reward  : +progress toward the program the user meant (token distance to the original), a step cost,
          a bonus when the program finally compiles, a larger bonus when it equals the original,
          and a penalty for running out of steps.
episode : ends when the program compiles or after `max_steps` fixes.

During training the original program is known (the dataset generated the faults), which is what makes
the reward informative. At run time the policy only sees candidate features, never the original.
"""
from __future__ import annotations

from difflib import SequenceMatcher

import numpy as np

from minic.lexer import lex
from repair.engine import Engine
from repair.rl.features import candidate_matrix

STEP_COST = 0.05
COMPILE_BONUS = 0.5
EXACT_BONUS = 1.0
TIMEOUT_PENALTY = 0.5


def tokens(src: str) -> list[tuple[str, str]]:
    return [(t.kind, t.value) for t in lex(src)[0]]


def token_distance(a_src: str, b_src: str) -> int:
    a, b = tokens(a_src), tokens(b_src)
    sm = SequenceMatcher(None, a, b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal")


class RepairEnv:
    def __init__(self, engine: Engine, max_steps: int = 6):
        engine.policy = None  # candidates come out in heuristic order; the agent chooses
        self.engine = engine
        self.max_steps = max_steps
        self._cache: dict[str, tuple | None] = {}

    def _state(self, src: str):
        if src not in self._cache:
            if len(self._cache) > 6000:
                self._cache.clear()
            res = self.engine.diagnose(src, mode="ml", only_first=True, explain=False)
            if not res["entries"]:
                self._cache[src] = None
            else:
                e = res["entries"][0]
                cands = e["candidates"]
                X = candidate_matrix(cands, res["errors"], e["diagnostic"]["stage"]) if cands else None
                self._cache[src] = (cands, X)
        return self._cache[src]

    def reset(self, broken: str, original: str):
        self.src, self.original = broken, original
        self.dist = self.d0 = token_distance(broken, original)
        self.steps = 0
        self.done = False
        self.state = self._state(broken)
        self.success = self.state is None
        return self.state

    def step(self, a: int) -> float:
        cands, _ = self.state
        c = cands[a]
        new = c["new_source"]
        prev, self.dist = self.dist, token_distance(new, self.original)
        errors_after = c["errors_after"] if c["errors_after"] >= 0 else 99
        self.steps += 1
        reward = (prev - self.dist) / max(1, self.d0) - STEP_COST
        self.src = new
        if errors_after == 0:
            reward += COMPILE_BONUS + (EXACT_BONUS if self.dist == 0 else 0.0)
            self.done = self.success = True
            self.state = None
        else:
            self.state = self._state(new)
            if self.state is None:  # compiled after all
                self.done = self.success = True
            elif self.steps >= self.max_steps or self.state[1] is None:
                reward -= TIMEOUT_PENALTY
                self.done = True
        return reward

    @property
    def exact(self) -> bool:
        return self.success and self.dist == 0


def argmax_allowed(scores: np.ndarray, cands: list[dict]) -> int:
    """Highest-scoring candidate that the compiler did not reject (any, if all were rejected)."""
    order = np.argsort(-scores)
    for i in order:
        if cands[int(i)]["status"] != "rejected":
            return int(i)
    return int(order[0])
