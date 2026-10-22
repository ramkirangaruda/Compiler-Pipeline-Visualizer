"""Reinforcement-learning fix policy: maths, environment, engine integration, API."""
import random

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from minic.pipeline import run_frontend
from ml.rl.env import RepairEnv, argmax_allowed, token_distance
from ml.rl.multifault import make_multifault
from repair.engine import Engine
from repair.rl.features import DIM, FEATURE_NAMES, IDX, candidate_matrix
from repair.rl.policy import Policy, softmax, warm_start

SRC = "int width = 10;\nint height = 20\nint area = width * height;\nprint(area);\n"


def cand(label="MISSING_SEMICOLON", status="verified", score=0.9, after=0, prob=0.9, edits=None):
    return {"label": label, "status": status, "prob": prob, "local_score": 0.9, "score": score,
            "errors_after": after, "edits": edits or [{"start": 5, "end": 5, "text": ";"}]}


def test_feature_names_and_dim_are_consistent():
    assert len(FEATURE_NAMES) == DIM == len(set(FEATURE_NAMES))


def test_softmax_is_a_distribution():
    p = softmax(np.array([1.0, 2.0, -3.0, 50.0]))
    assert p.sum() == pytest.approx(1.0) and (p >= 0).all()


def test_candidate_matrix_encodes_label_status_and_edit():
    X = candidate_matrix([cand(), cand("TYPE_MISMATCH", "rejected", after=2, edits=[{"start": 0, "end": 3, "text": ""}])], 2, "syntax")
    assert X.shape == (2, DIM)
    assert X[0, IDX["label=MISSING_SEMICOLON"]] == 1 and X[0, IDX["status=verified"]] == 1 and X[0, IDX["pure_insert"]] == 1
    assert X[1, IDX["status=rejected"]] == 1 and X[1, IDX["pure_delete"]] == 1 and X[1, IDX["is_heuristic_top"]] == 0


def test_policy_gradient_matches_finite_differences():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(4, DIM))
    pol = Policy(rng.normal(size=DIM) * 0.3)
    a = 2
    g = pol.grad_logp(X, a)
    for j in rng.choice(DIM, 8, replace=False):
        e = np.zeros(DIM)
        e[j] = 1e-5
        hi = np.log(softmax(X @ (pol.theta + e))[a])
        lo = np.log(softmax(X @ (pol.theta - e))[a])
        assert g[j] == pytest.approx((hi - lo) / 2e-5, abs=1e-5)


def test_reinforce_raises_prob_of_rewarded_action_and_lowers_penalised_one():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(5, DIM))
    up, down = Policy(np.zeros(DIM)), Policy(np.zeros(DIM))
    p0 = up.probs(X)[3]
    for _ in range(40):
        up.reinforce([(X, 3)], [1.0], lr=0.2, entropy=0.0)
        down.reinforce([(X, 3)], [-1.0], lr=0.2, entropy=0.0)
    assert up.probs(X)[3] > p0 + 0.2 and down.probs(X)[3] < p0 - 0.1


def test_warm_start_prefers_verified_high_score_and_avoids_rejected():
    cands = [cand(status="verified", score=0.8), cand("TYPO_IDENTIFIER", "partial", 0.5, after=1),
             cand("MISSING_DECLARATION", "rejected", 0.95, after=3)]
    X = candidate_matrix(cands, 2, "semantic")
    assert int(np.argmax(Policy(warm_start()).probs(X))) == 0
    assert Policy().probs(X)[2] < 0.05


def test_argmax_allowed_never_picks_a_rejected_fix_when_an_alternative_exists():
    cands = [cand(status="rejected"), cand(status="partial"), cand(status="verified")]
    assert argmax_allowed(np.array([9.0, 0.1, 0.2]), cands) == 2


def test_policy_roundtrip(tmp_path):
    pol = Policy(np.arange(DIM, dtype=float), {"episodes": 3})
    path = tmp_path / "p.json"
    pol.save(path)
    again = Policy.load(path)
    assert np.allclose(again.theta, pol.theta) and again.meta["episodes"] == 3


def test_token_distance():
    assert token_distance("int a = 1;", "int a = 1;") == 0
    assert token_distance("int a = 1", "int a = 1;") == 1


def test_multifault_generator_injects_faults_deterministically():
    seed = "int a = 1;\nint b = a + 2;\nint c = b * 3;\nprint(c);\nprint(a);\n"
    out = [make_multifault(seed, 2, random.Random(s)) for s in range(30)]
    ok = [o for o in out if o]
    assert len(ok) >= 5
    for broken, plan in ok:
        assert broken != seed and run_frontend(broken).errors and len(plan) == 2
    assert make_multifault(seed, 2, random.Random(4)) == make_multifault(seed, 2, random.Random(4))


@pytest.fixture(scope="module")
def engine():
    e = Engine()
    assert e.policy is not None, "train the policy first: python -m ml.rl.train_rl"
    return e


def test_environment_rewards_progress_and_exact_recovery(engine):
    original = SRC.replace("height = 20\n", "height = 20;\n")
    env = RepairEnv(Engine())
    env.reset(SRC, original)
    assert env.state is not None and env.d0 == 1
    best = next(i for i, c in enumerate(env.state[0]) if c["status"] == "verified")
    r = env.step(best)
    assert env.done and env.success and env.exact and r > 1.0  # compile bonus + exact bonus + progress


def test_environment_penalises_a_useless_fix():
    env = RepairEnv(Engine(), max_steps=1)
    env.reset(SRC, SRC.replace("height = 20\n", "height = 20;\n"))
    worst = max(range(len(env.state[0])), key=lambda i: env.state[0][i]["errors_after"])
    if env.state[0][worst]["status"] == "rejected":
        assert env.step(worst) < 0.5


def test_rl_ranker_keeps_rejected_fixes_last_and_best_is_never_rejected(engine):
    for src in [SRC, "int a = 1;\nprint(b);\n", "name = \"x\";\nint n = 2.5;\n"]:
        res = engine.diagnose(src, ranker="rl")
        for e in res["entries"]:
            statuses = [c["status"] for c in e["candidates"]]
            assert "rejected" not in statuses[: statuses.count("verified") + statuses.count("partial")]
            best = next((c for c in e["candidates"] if c["id"] == e["best"]), None)
            assert best is None or best["status"] != "rejected"
            assert all("rl_prob" in c for c in e["candidates"]) and e["decision_id"]


def test_online_feedback_moves_the_policy_and_reset_restores_it(engine):
    engine.reset_policy()
    res = engine.diagnose("int a = 1;\nprint(zq);\n", ranker="rl")
    e = res["entries"][0]
    cid = e["candidates"][-1]["id"]  # reward a candidate the policy currently ranks low
    out = engine.feedback(e["decision_id"], cid, 1.0)
    for _ in range(5):
        out = engine.feedback(e["decision_id"], cid, 1.0)
    assert out["after"] > out["before"]
    st = engine.rl_status()
    assert st["online_updates"] == 6 and st["weight_shift"] > 0 and st["mean_reward"] == 1.0
    assert engine.feedback("nope", cid, 1.0) is None
    engine.reset_policy()
    assert engine.rl_status()["online_updates"] == 0 and engine.rl_status()["weight_shift"] == 0


client = TestClient(app)


def test_api_rl_status_and_feedback_flow():
    client.post("/api/rl/reset")
    r = client.post("/api/compile", json={"source": SRC, "ranker": "rl"}).json()
    entry = r["diagnosis"]["entries"][0]
    assert r["diagnosis"]["ranker"] == "rl" and entry["decision_id"]
    ok = client.post("/api/rl/feedback", json={"decision_id": entry["decision_id"], "candidate_id": entry["best"], "reward": 1})
    assert ok.status_code == 200 and ok.json()["updates"] == 1
    assert client.post("/api/rl/feedback", json={"decision_id": "expired", "candidate_id": "fix-1", "reward": 1}).status_code == 404
    assert client.post("/api/rl/feedback", json={"decision_id": entry["decision_id"], "candidate_id": "fix-1", "reward": 9}).status_code == 422
    st = client.get("/api/rl").json()
    assert st["status"]["loaded"] and st["status"]["online_updates"] == 1 and st["metrics"]["eval"]["rl"]
    assert client.post("/api/rl/reset").json()["online_updates"] == 0


def test_api_heuristic_ranker_still_available():
    r = client.post("/api/diagnose", json={"source": SRC, "ranker": "heuristic"}).json()
    assert r["ranker"] == "heuristic" and r["entries"][0]["best"] == "fix-1"
