"""Trains the reinforcement-learning fix policy (REINFORCE with a baseline) and evaluates it
against the hand-written heuristic and a random chooser on held-out multi-fault programs.

    python -m ml.rl.train_rl                 # ~10 minutes
    python -m ml.rl.train_rl --episodes 300 --eval-episodes 60     # quick smoke run

Outputs: models/rl_policy.json (weights) and models/rl_metrics.json (dashboard data).
"""
from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from repair.engine import Engine
from repair.rl.features import DIM
from repair.rl.policy import POLICY_PATH, Policy

from .env import (COMPILE_BONUS, EXACT_BONUS, STEP_COST, TIMEOUT_PENALTY, RepairEnv, argmax_allowed)
from .multifault import make_multifault

ROOT = Path(__file__).resolve().parents[3]
GAMMA = 0.95
K_WEIGHTS = ([1, 2, 3], [0.35, 0.4, 0.25])


def load_seeds() -> tuple[list[str], list[str]]:
    train, test = [], []
    for p in sorted((ROOT / "datasets" / "seeds" / "valid").glob("seed_*.mc")):
        (test if int(p.stem.split("_")[1]) % 5 == 0 else train).append(p.read_text(encoding="utf-8"))
    return train, test


def sample_episode(seeds: list[str], rng: random.Random):
    for _ in range(50):
        original = rng.choice(seeds)
        k = rng.choices(*K_WEIGHTS)[0]
        mf = make_multifault(original, k, rng)
        if mf is not None:
            return original, mf[0], k, mf[1]
    raise RuntimeError("could not generate a faulty program")


def run_episode(env: RepairEnv, broken: str, original: str, choose, collect=False):
    """Play one episode. `choose(X, cands) -> action`. Returns (rewards, trajectory)."""
    env.reset(broken, original)
    rewards, traj = [], []
    if env.state is None or env.state[1] is None:
        return rewards, traj
    while not env.done:
        cands, X = env.state
        a = choose(X, cands)
        if collect:
            traj.append((X, a))
        rewards.append(env.step(a))
    return rewards, traj


def returns_to_go(rewards: list[float]) -> list[float]:
    g, out = 0.0, []
    for r in reversed(rewards):
        g = r + GAMMA * g
        out.append(g)
    return out[::-1]


# ---------------------------------------------------------------------------- evaluation
def paired_bootstrap(a: list[dict], b: list[dict], seed: int, n_boot: int = 4000) -> dict:
    """Mean per-episode difference a - b with a 95% bootstrap confidence interval (same episodes)."""
    rng = np.random.default_rng(seed)
    res = {}
    for key, name in (("exact", "exact_rate_diff"), ("dist", "distance_diff"), ("ret", "return_diff")):
        d = np.array([float(x[key]) - float(y[key]) for x, y in zip(a, b)])
        boots = rng.choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        res[name] = {"mean": round(float(d.mean()), 4), "ci_low": round(float(lo), 4), "ci_high": round(float(hi), 4),
                     "significant": bool(lo > 0 or hi < 0)}
    return res

def evaluate(env: RepairEnv, policy: Policy, episodes: list[tuple], seed: int) -> dict:
    rng = np.random.default_rng(seed)
    methods = {
        "heuristic": lambda X, c: next((i for i, x in enumerate(c) if x["status"] != "rejected"), 0),
        "rl": lambda X, c: argmax_allowed(policy.probs(X), c),
        "random": lambda X, c: argmax_allowed(rng.random(len(c)), c),
    }
    out, per_episode = {}, {}
    for name, choose in methods.items():
        rows = []
        for original, broken, k, _plan in episodes:
            rewards, _ = run_episode(env, broken, original, choose)
            rows.append({"k": k, "success": env.success, "exact": env.exact, "steps": env.steps,
                         "dist": env.dist, "ret": sum(rewards)})

        def agg(sel):
            n = max(1, len(sel))
            ok = [r for r in sel if r["success"]]
            return {
                "n": len(sel),
                "success_rate": round(sum(r["success"] for r in sel) / n, 4),
                "exact_rate": round(sum(r["exact"] for r in sel) / n, 4),
                "mean_steps": round(sum(r["steps"] for r in ok) / max(1, len(ok)), 3),
                "mean_distance": round(sum(r["dist"] for r in sel) / n, 3),
                "mean_return": round(sum(r["ret"] for r in sel) / n, 4),
            }

        per_episode[name] = rows
        out[name] = {"overall": agg(rows), "by_faults": {str(k): agg([r for r in rows if r["k"] == k]) for k in (1, 2, 3)}}
        print(f"  {name:10s}", out[name]["overall"])
    out["paired_vs_heuristic"] = paired_bootstrap(per_episode["rl"], per_episode["heuristic"], seed)
    print("  paired RL - heuristic:", out["paired_vs_heuristic"])
    return out


# ---------------------------------------------------------------------------- training
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=2500)
    ap.add_argument("--eval-episodes", type=int, default=300)
    ap.add_argument("--lr", type=float, default=0.08)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--eval-only", action="store_true", help="re-evaluate the saved policy (keeps its learning curve)")
    args = ap.parse_args()

    train_seeds, test_seeds = load_seeds()
    print(f"seeds: train={len(train_seeds)} test={len(test_seeds)}")
    engine = Engine()
    env = RepairEnv(engine)
    policy = Policy.load() if args.eval_only else Policy()
    rng = random.Random(args.seed)
    baseline = np.zeros(RepairEnvMax := 8)
    window, curve = [], []
    t0 = time.perf_counter()

    for ep in range(1, 1 if args.eval_only else args.episodes + 1):
        original, broken, k, _ = sample_episode(train_seeds, rng)
        sampler = np.random.default_rng(rng.randrange(2**32))
        rewards, traj = run_episode(env, broken, original, lambda X, c: policy.act(X, sampler), collect=True)
        if not traj:
            continue
        G = returns_to_go(rewards)
        adv = [g - baseline[min(t, len(baseline) - 1)] for t, g in enumerate(G)]
        for t, g in enumerate(G):
            i = min(t, len(baseline) - 1)
            baseline[i] += 0.03 * (g - baseline[i])
        frac = ep / args.episodes
        policy.reinforce(traj, adv, lr=args.lr * (1 - 0.75 * frac), entropy=0.02 * (1 - 0.8 * frac))
        window.append((sum(rewards), env.success, env.exact))
        if ep % 50 == 0:
            w = window[-50:]
            curve.append({"episode": ep, "avg_return": round(sum(x[0] for x in w) / len(w), 4),
                          "success_rate": round(sum(x[1] for x in w) / len(w), 4),
                          "exact_rate": round(sum(x[2] for x in w) / len(w), 4)})
            if ep % 250 == 0:
                print(f"  ep {ep:5d}  return {curve[-1]['avg_return']:+.3f}  success {curve[-1]['success_rate']:.2f}  "
                      f"exact {curve[-1]['exact_rate']:.2f}  ({time.perf_counter() - t0:.0f}s)")

    print("evaluating on held-out seeds ...")
    erng = random.Random(args.seed + 1000)
    per_k = args.eval_episodes // 3
    episodes = []
    for k in (1, 2, 3):
        while sum(1 for e in episodes if e[2] == k) < per_k:
            original = erng.choice(test_seeds)
            mf = make_multifault(original, k, erng)
            if mf is not None:
                episodes.append((original, mf[0], k, mf[1]))
    results = evaluate(env, policy, episodes, args.seed)

    if args.eval_only:
        old = json.loads((ROOT / "models" / "rl_metrics.json").read_text(encoding="utf-8"))
        old.update({"eval": results, "top_weights": policy.top_weights(16)})
        old["config"]["eval_episodes"] = len(episodes)
        (ROOT / "models" / "rl_metrics.json").write_text(json.dumps(old, indent=2), encoding="utf-8")
        print("re-evaluated saved policy; curve kept")
        return
    policy.meta = {"episodes": args.episodes, "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "algorithm": "REINFORCE + baseline + entropy bonus", "gamma": GAMMA}
    policy.save()
    metrics = {
        "trained_at": policy.meta["trained_at"],
        "config": {"episodes": args.episodes, "gamma": GAMMA, "lr": args.lr, "feature_dim": DIM,
                   "train_seeds": len(train_seeds), "test_seeds": len(test_seeds), "eval_episodes": len(episodes)},
        "mdp": {
            "state": "broken program, summarised by the compiler-validated candidate fixes for its first error",
            "action": "apply one candidate fix (up to 10 per state)",
            "reward": f"progress toward the intended program (token distance) - {STEP_COST} per step; "
                      f"+{COMPILE_BONUS} if it compiles, +{EXACT_BONUS} more if it equals the original, "
                      f"-{TIMEOUT_PENALTY} on timeout",
            "policy": "linear softmax over candidate features, warm-started from the heuristic ranking",
            "algorithm": "REINFORCE with a per-step baseline and entropy bonus",
        },
        "curve": curve,
        "eval": results,
        "top_weights": policy.top_weights(16),
    }
    (ROOT / "models" / "rl_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"saved {POLICY_PATH.name} and rl_metrics.json  ({time.perf_counter() - t0:.0f}s total)")


if __name__ == "__main__":
    main()
