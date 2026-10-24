"""Real-C support: front end, interpreter, repair engine and API (gcc is not needed; expectations are fixed)."""
import pytest
from fastapi.testclient import TestClient

from app.examples_c import BROKEN, VALID, c_examples
from app.main import app
from cfront.pipeline import compile_source, run_frontend
from repair.engine import Engine

H = "#include <stdio.h>\n"


@pytest.fixture(scope="module")
def engine():
    e = Engine()
    assert e.clfs["c"] is not None, "run `python -m ml.train --lang c` first"
    return e


def run(src: str) -> str:
    r = compile_source(src)
    assert r["ok"], [d["message"] for d in r["diagnostics"]]
    return r["execution"]["raw_output"]


# ----------------------------------------------------------------- front end
@pytest.mark.parametrize("body,code", [
    ("int a = 1\n  return a;", "E_EXPECTED_TOKEN"),
    ("return b;", "E_UNDECLARED"),
    ('int x = "s"; return x;', "E_TYPE_MISMATCH"),
    ("double d = 1.5; return d % 2;", "E_BAD_OPERAND"),
    ("int a = 1; int a = 2; return a;", "E_REDECLARED"),
])
def test_errors_are_detected(body, code):
    fe = run_frontend(H + "int main(void) {\n  " + body + "\n}\n")
    assert fe.errors and fe.errors[0].code == code


def test_missing_include_is_a_real_error():
    fe = run_frontend('int main(void) { printf("x"); return 0; }\n')
    assert [d.code for d in fe.errors] == ["E_MISSING_INCLUDE"]
    assert fe.errors[0].extra["header"] == "stdio.h"


def test_wrong_argument_count():
    fe = run_frontend(H + "int f(int a, int b) { return a; }\nint main(void) { return f(1); }\n")
    assert fe.errors[0].code == "E_WRONG_ARGC" and fe.errors[0].extra["n_params"] == 2


def test_else_if_chain_and_for_scope():
    src = H + "int main(void) {\n  int a = 1;\n  if (a > 1) {\n    a = 2;\n  } else if (a > 0) {\n    a = 3;\n  } else {\n    a = 4;\n  }\n  for (int i = 0; i < 2; i++) { a += i; }\n  return a;\n}\n"
    assert not run_frontend(src).errors
    assert run_frontend(src.replace("return a;", "return i;")).errors[0].extra["closed_scope"]


# --------------------------------------------------------------- interpreter
def test_arithmetic_and_wraparound():
    assert run(H + 'int main(void){ printf("%d %d %d\\n", 7/2, -7/2, -7%3); int x=2147483647; x=x+1; printf("%d\\n", x); return 0; }') == "3 -3 -1\n-2147483648\n"


def test_pointers_arrays_structs():
    src = H + ('struct P { int x; double y; };\n'
               'void swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }\n'
               'int main(void) { int a[3] = {1,2,3}; int *p = a; int s = 0; while (p < a + 3) { s += *p; p++; }\n'
               '  int x = 1, y = 2; swap(&x, &y); struct P q; q.x = 4; q.y = 2.5; struct P *r = &q; r->x += 1;\n'
               '  printf("%d %d %d %d %.1f\\n", s, x, y, q.x, q.y); return 0; }')
    assert run(src) == "6 2 1 5 2.5\n"


def test_recursion_and_string_functions():
    src = "#include <stdio.h>\n#include <string.h>\nint fib(int n){ return n < 2 ? n : fib(n-1) + fib(n-2); }\nint main(void){ char b[16]; strcpy(b, \"ab\"); strcat(b, \"cd\"); printf(\"%d %s %d\\n\", fib(10), b, (int)strlen(b)); return 0; }"
    assert run(src) == "55 abcd 4\n"


def test_runtime_error_and_step_limit():
    r = compile_source(H + "int main(void){ int a[2]; a[5] = 1; return 0; }")
    assert r["execution"]["halted"] == "error"
    r = compile_source(H + "int main(void){ while (1) { } return 0; }")
    assert r["execution"]["halted"] == "step_limit"


def test_every_valid_example_runs():
    for _, name, _, src in VALID:
        r = compile_source(src)
        assert r["ok"] and r["execution"]["halted"] == "done", name


# -------------------------------------------------------------------- repair
def test_every_broken_example_is_diagnosed_and_fixed(engine):
    for label, title, src in BROKEN:
        res = engine.diagnose(src, language="c", only_first=True)
        e = res["entries"][0]
        assert e["prediction"]["label"] == label, (title, e["prediction"]["label"])
        assert e["best"], title
        fixed = engine.autofix(src, language="c")
        assert fixed["ok"], (title, fixed["remaining"])
        assert not run_frontend(fixed["final_source"]).errors


def test_multi_error_program_autofix(engine):
    src = next(e for e in c_examples() if e["id"] == "c_multi")["source"]
    assert engine.autofix(src, language="c")["ok"]


def test_every_verified_fix_really_compiles(engine):
    for _, _, src in BROKEN:
        for e in engine.diagnose(src, language="c")["entries"]:
            for c in e["candidates"]:
                if c["status"] == "verified":
                    assert not run_frontend(c["new_source"]).errors


# ----------------------------------------------------------------------- api
def test_api_language_switch():
    c = TestClient(app)
    assert c.get("/api/health").json()["languages"]["c"]
    r = c.post("/api/compile", json={"source": H + 'int main(void){ printf("hi\\n"); return 0; }', "language": "c"}).json()
    assert r["ok"] and r["language"] == "c" and r["execution"]["raw_output"] == "hi\n"
    bad = c.post("/api/compile", json={"source": "int main(void) { return 0 }", "language": "c"}).json()
    assert not bad["ok"] and bad["diagnosis"]["language"] == "c"
    assert c.get("/api/model?language=c").json()["metrics"]["language"] == "c"
    assert any(e["language"] == "c" for e in c.get("/api/examples").json())
