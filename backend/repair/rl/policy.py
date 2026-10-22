"""A linear-softmax policy over candidate fixes, trained with REINFORCE.

    pi(a | s) = softmax_i( theta . phi(candidate_i) )

The policy is deliberately small and numpy-only: it is trained in minutes on a
laptop, its weights are human-readable (the Dashboard lists them), and the
same update rule is reused for *online* learning from user feedback.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .features import DIM, FEATURE_NAMES, IDX

POLICY_PATH = Path(__file__).resolve().parents[3] / "models" / "rl_policy.json"


def warm_start() -> np.ndarray:
    """Prior that mimics the hand-written ranking: prefer verified fixes with a high
    heuristic score and avoid rejected ones. RL then fine-tunes it from reward."""
    th = np.zeros(DIM)
    th[IDX["status=verified"]] = 2.0
    th[IDX["status=partial"]] = 0.5
    th[IDX["status=rejected"]] = -4.0
    th[IDX["heuristic_score"]] = 3.0
    th[IDX["is_heuristic_top"]] = 0.5
    return th


def softmax(z: np.ndarray) -> np.ndarray:
    e = np.exp(z - z.max())
    return e / e.sum()


class Policy:
    def __init__(self, theta: np.ndarray | None = None, meta: dict | None = None):
        self.theta = warm_start() if theta is None else np.asarray(theta, dtype=np.float64)
        self.meta = meta or {}

    # --------------------------------------------------------------- acting
    def probs(self, X: np.ndarray) -> np.ndarray:
        return softmax(X @ self.theta)

    def act(self, X: np.ndarray, rng: np.random.Generator | None = None, greedy: bool = False) -> int:
        p = self.probs(X)
        if greedy or rng is None:
            return int(np.argmax(p))
        return int(rng.choice(len(p), p=p))

    # ------------------------------------------------------------- learning
    def grad_logp(self, X: np.ndarray, a: int) -> np.ndarray:
        p = self.probs(X)
        return X[a] - p @ X

    def entropy_grad(self, X: np.ndarray) -> np.ndarray:
        p = self.probs(X)
        h = -(p * np.log(p + 1e-12))
        mean_phi = p @ X
        # d/dtheta H(pi) = - sum_i p_i (log p_i + H) (phi_i - mean_phi)
        return -((p * (np.log(p + 1e-12) + h.sum()))[:, None] * (X - mean_phi)).sum(axis=0)

    def reinforce(self, trajectory: list[tuple[np.ndarray, int]], advantages: list[float],
                  lr: float = 0.05, entropy: float = 0.01, l2: float = 1e-4) -> None:
        g = np.zeros(DIM)
        for (X, a), adv in zip(trajectory, advantages):
            g += adv * self.grad_logp(X, a) + entropy * self.entropy_grad(X)
        self.theta += lr * g / max(1, len(trajectory)) - lr * l2 * self.theta

    def online_update(self, X: np.ndarray, a: int, reward: float, lr: float = 0.4) -> float:
        """One-step policy-gradient update from a single piece of user feedback."""
        self.theta += lr * reward * self.grad_logp(X, a)
        return float(self.probs(X)[a])

    # ------------------------------------------------------------ persistence
    def copy(self) -> "Policy":
        return Policy(self.theta.copy(), dict(self.meta))

    def top_weights(self, k: int = 14) -> list[dict]:
        order = np.argsort(-np.abs(self.theta))[:k]
        return [{"feature": FEATURE_NAMES[i], "weight": round(float(self.theta[i]), 3)} for i in order]

    def save(self, path: Path = POLICY_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"features": FEATURE_NAMES, "theta": self.theta.tolist(), "meta": self.meta}, indent=1),
                        encoding="utf-8")

    @classmethod
    def load(cls, path: Path = POLICY_PATH) -> "Policy":
        d = json.loads(path.read_text(encoding="utf-8"))
        if d["features"] != FEATURE_NAMES:
            raise ValueError("policy file was trained with a different feature set - retrain with python -m ml.rl.train_rl")
        return cls(np.array(d["theta"]), d.get("meta"))
