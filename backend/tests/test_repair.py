"""Feature extraction, candidate generation, validation and the engine."""
import pytest

from app.examples import BROKEN, all_examples
from minic import run_frontend
from repair import baseline
from repair.candidates import Edit, apply_edits
from repair.engine import Engine
from repair.features import FEATURE_COLUMNS, extract
from repair.validator import validate


@pytest.fixture(scope="module")
def engine():
    e = Engine()
    assert e.model_loaded, "run `python -m ml.train` first"
    return e


def test_feature_vector_shape_and_content():
    fe = run_frontend("int x = 10\nint y = 20;")
    f = extract(fe.errors[0], fe)
    assert set(f) == set(FEATURE_COLUMNS)
    assert f["expected"] == ";" and f["found"] == "int" and f["prev1"] == "INT" and f["nl_before_found"] == 1


def test_baseline_rules_basic():
    fe = run_frontend("int x = 10\nint y = 20;")
    assert baseline.predict(extract(fe.errors[0], fe)) == "MISSING_SEMICOLON"


def test_apply_edits_and_overlap():
    assert apply_edits("abcdef", [Edit(1, 2, "X"), Edit(4, 4, "Y")]) == "aXcdYef"
    with pytest.raises(ValueError):
        apply_edits("abcdef", [Edit(1, 4, ""), Edit(2, 3, "")])


def test_validator_rejects_a_wrong_fix():
    src = "int x = 5\nint y = 6;"
    fe = run_frontend(src)
    good = validate(src, [Edit(9, 9, ";")], fe, fe.errors[0])
    bad = validate(src, [Edit(0, 0, "(")], fe, fe.errors[0])
    assert good["status"] == "verified"
    assert bad["status"] == "rejected"


@pytest.mark.parametrize("label,title,src", BROKEN)
def test_each_broken_example_is_diagnosed_and_repaired(engine, label, title, src):
    res = engine.diagnose(src)
    entry = res["entries"][0]
    assert entry["prediction"]["label"] == label
    best = next(c for c in entry["candidates"] if c["id"] == entry["best"])
    assert best["status"] == "verified"
    assert not run_frontend(best["new_source"]).errors  # the compiler really accepts it


def test_ml_never_offers_an_unvalidated_fix(engine):
    for ex in all_examples():
        if ex["category"] != "broken":
            continue
        for entry in engine.diagnose(ex["source"])["entries"]:
            best = next((c for c in entry["candidates"] if c["id"] == entry["best"]), None)
            assert best is None or best["status"] in ("verified", "partial")


def test_autofix_repairs_multiple_errors(engine):
    multi = next(e for e in all_examples() if e["id"] == "multi")
    res = engine.autofix(multi["source"])
    assert res["ok"] and len(res["steps"]) == 3 and not run_frontend(res["final_source"]).errors


def test_duplicate_undeclared_uses_are_grouped(engine):
    res = engine.diagnose("int a = 1;\nprint(zz);\nprint(zz);\nprint(zz);")
    assert len(res["entries"]) == 1 and res["entries"][0]["duplicates"] == 2


def test_rule_handled_errors_have_no_ml_prediction(engine):
    res = engine.diagnose("int x = 3 @;")
    e = res["entries"][0]
    assert e["handled_by"] == "rules" and e["prediction"] is None and e["best"]


def test_explanation_is_returned(engine):
    res = engine.diagnose("int x = 5\nint y = 6;")
    assert res["entries"][0]["explanation"]
