from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_examples():
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["model_loaded"]
    ex = client.get("/api/examples").json()
    assert len(ex) >= 15 and {"id", "name", "source", "category"} <= set(ex[0])


def test_compile_valid_program():
    r = client.post("/api/compile", json={"source": "int a = 2 + 3;\nprint(a);"}).json()
    assert r["ok"] and r["execution"]["output"] == ["5"] and r["diagnosis"] is None
    assert [s["status"] for s in r["stages"]] == ["ok"] * 6


def test_compile_broken_program_includes_diagnosis():
    r = client.post("/api/compile", json={"source": "int w = 1\nint h = 2;"}).json()
    assert not r["ok"] and r["diagnosis"]["entries"][0]["prediction"]["label"] == "MISSING_SEMICOLON"
    assert [s["status"] for s in r["stages"]][:2] == ["ok", "error"]


def test_autofix_and_modes():
    r = client.post("/api/autofix", json={"source": "int w = 1\nint h = 2;"}).json()
    assert r["ok"]
    r = client.post("/api/diagnose", json={"source": "int w = 1\nint h = 2;", "mode": "baseline"}).json()
    assert r["mode"] == "baseline" and r["entries"][0]["handled_by"] == "baseline"


def test_source_size_limit():
    assert client.post("/api/compile", json={"source": "x" * 30000}).status_code == 422


def test_model_and_dataset_endpoints():
    m = client.get("/api/model").json()
    assert m["loaded"] and m["metrics"]["test"]["accuracy"] > 0.9 and m["repair_eval"]["ml"]["overall"]["n"] > 0
    d = client.get("/api/dataset").json()
    assert len(d["classes"]) == 12 and d["n_samples"] > 3000
    s = client.get("/api/dataset/samples", params={"label": "TYPO_IDENTIFIER", "limit": 2}).json()
    assert len(s["samples"]) == 2 and s["samples"][0]["original"]
    assert client.get("/api/dataset/samples", params={"label": "../etc"}).status_code == 404


def test_session_counters():
    assert client.get("/api/session").json()["compiles"] >= 2
