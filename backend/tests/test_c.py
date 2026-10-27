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


# ------------------------------------------------------- gcc as the judge
from cfront import gcc as _gcc  # noqa: E402

needs_gcc = pytest.mark.skipif(not _gcc.available(), reason="no C compiler on PATH")

USER_PROGRAM = r'''#include <stdio.h>

int main() {
    int a = 10;
    int b = 20;
    int c;

    c = a + b;

    if (c > 25) {
        printf("Sum is greater than 25\n");
    } else {
        printf("Sum is less than or equal to 25\n");
    }

    return 0;
}
'''


@needs_gcc
def test_ordinary_program_is_accepted_and_runs():
    r = compile_source(USER_PROGRAM)
    assert r["ok"] and r["compiler"]["judge"]
    assert r["execution"]["raw_output"] == "Sum is greater than 25\n"


@needs_gcc
def test_no_false_alarms_on_valid_real_programs():
    from ml.realworld_c import PROGRAMS
    for name, src in PROGRAMS.items():
        assert not run_frontend(src).errors, name


@needs_gcc
@pytest.mark.parametrize("name,src", [
    ("union", H + "union U { int i; float f; };\nint main(void) {\n    union U u;\n    u.i = 3\n    return u.i;\n}\n"),
    ("function pointer", H + "int add(int a, int b) { return a + b; }\nint main(void) {\n    int (*fp)(int, int) = add;\n    printf(\"%d\", fp(1, 2);\n    return 0;\n}\n"),
    ("typo function", H + "int main(void) {\n    prntf(\"hi\");\n    return 0;\n}\n"),
    ("call before definition", H + "int main(void) {\n    printf(\"%d\", twice(4));\n    return 0;\n}\nint twice(int x) { return 2 * x; }\n"),
    ("const assignment", H + "int main(void) {\n    const int k = 3;\n    k = 4;\n    return k;\n}\n"),
    ("struct member typo", H + "struct P { int x; };\nint main(void) {\n    struct P p;\n    p.y = 3;\n    return 0;\n}\n"),
    ("no main", H + "int helper(int x) { return x + 1; }\n"),
    ("undefined function", H + "int foo(int);\nint main(void) { printf(\"%d\", foo(2)); return 0; }\n"),
    ("swapped tokens", H + "int main(void) {\n    int a = 1;\n    printf(\"%d\", a);\n    return 0\n}\n"),
])
def test_errors_outside_the_trained_causes_are_repaired(engine, name, src):
    res = engine.autofix(src, language="c")
    assert res["ok"], (name, res["remaining"])
    assert not _gcc.run(res["final_source"], link=True).errors


@needs_gcc
def test_a_wrong_fix_is_never_called_verified(engine):
    src = H + "int main(void) {\n    int x = \"text\";\n    return x;\n}\n"
    for e in engine.diagnose(src, language="c")["entries"]:
        for c in e["candidates"]:
            if c["status"] == "verified":
                assert not _gcc.run(c["new_source"], link=True).errors


def test_local_includes_are_refused():
    if not _gcc.available():
        pytest.skip("no C compiler")
    r = _gcc.run('#include "/etc/passwd"\nint main(void) { return 0; }\n')
    assert r.errors and "single files" in r.errors[0].message


# ------------------------------------------------ hostile and degenerate input
NL = chr(10)
HOSTILE = {
    "empty": "",
    "whitespace": "   " + NL + chr(9) + NL,
    "null bytes": "int main(void){return 0;}" + chr(0) * 3,
    "binary garbage": "".join(chr(i) for i in range(1, 128)) * 5,
    "deep parentheses": "int main(void){ int a = " + "(" * 2500 + "1" + ")" * 2500 + "; return a; }",
    "infinite loop": "int main(void){ while (1) { } return 0; }",
    "infinite recursion": "int f(int n){ return f(n + 1); } int main(void){ return f(0); }",
    "include a system file": '#include "/etc/passwd"' + NL + "int main(void){ return 0; }",
    "has_include probe": '#if __has_include("/etc/passwd")' + NL + "int x;" + NL + "#endif" + NL + "int main(void){return 0;}",
    "error directive": "#error stop" + NL + "int main(void){ return 0; }",
    "unterminated comment": "/* never closed" + NL + "int main(void){ return 0; }",
}


@pytest.mark.parametrize("name", list(HOSTILE))
def test_hostile_input_never_crashes_the_api(name):
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/compile", json={"source": HOSTILE[name], "language": "c"})
    assert r.status_code == 200, name
    body = r.json()
    assert "ok" in body and "diagnostics" in body
    if name in ("include a system file", "has_include probe"):
        assert not body["ok"] and "single files" in body["diagnostics"][0]["message"]


def test_oversized_source_is_refused():
    c = TestClient(app, raise_server_exceptions=False)
    assert c.post("/api/compile", json={"source": "x" * 20001, "language": "c"}).status_code in (413, 422)


@needs_gcc
def test_autofix_respects_its_time_budget(engine):
    import time
    src = "#pragma GCC poison printf" + NL + H + "int main(void){ printf(" + chr(34) + "x" + chr(34) + "); return 0; }" + NL
    t0 = time.time()
    res = engine.autofix(src, language="c", total_budget=8)
    assert time.time() - t0 < 40 and "ok" in res


@needs_gcc
def test_last_resort_is_never_chosen_automatically(engine):
    src = H + "int main(void) {" + NL + "    int x = ;;;" + NL + "    return x;" + NL + "}" + NL
    res = engine.diagnose(src, language="c")
    for e in res["entries"]:
        best = next((c for c in e["candidates"] if c["id"] == e["best"]), None)
        assert best is None or best["label"] != "LAST_RESORT"


# ------------------------------------------------------------ "Ask an LLM" (network mocked)
from repair import llm as _llm  # noqa: E402

BROKEN_CALL = H + "int main(void) {" + NL + "    printf(" + chr(34) + "%d" + chr(34) + ", average(1, 3));" + NL + "    return 0;" + NL + "}" + NL


def _fake_reply(code, title="Define average"):
    import json
    return json.dumps({"fixes": [{"title": title, "explanation": "adds it", "code": code}]})


@needs_gcc
def test_llm_suggestions_are_checked_by_gcc(monkeypatch):
    good = "int average(int a, int b) { return (a + b) / 2; }" + NL + BROKEN_CALL
    still_broken = BROKEN_CALL.replace("average(1, 3)", "average(1, 3, 4)")
    replies = iter([_fake_reply(still_broken, "wrong"), _fake_reply(good)])
    monkeypatch.setattr(_llm, "provider", lambda: {"name": "fake", "url": "", "key": "x", "model": "m"})
    monkeypatch.setattr(_llm, "chat", lambda messages, max_tokens=0: next(replies))
    res = _llm.suggest(BROKEN_CALL, run_frontend)
    assert res["configured"] and res["suggestions"]
    assert all(not run_frontend(s["new_source"]).errors for s in res["suggestions"] if s["status"] == "verified")
    assert res["suggestions"][0]["status"] == "verified"
    assert res["rejected"] >= 1                      # the first, wrong answer was thrown away by gcc


@needs_gcc
def test_llm_answer_that_does_not_build_is_never_offered(monkeypatch):
    monkeypatch.setattr(_llm, "provider", lambda: {"name": "fake", "url": "", "key": "x", "model": "m"})
    monkeypatch.setattr(_llm, "chat", lambda messages, max_tokens=0: _fake_reply(BROKEN_CALL.replace("average", "avrage")))
    res = _llm.suggest(BROKEN_CALL, run_frontend)
    assert res["suggestions"] == []


def test_llm_is_off_without_a_key(monkeypatch):
    monkeypatch.setattr(_llm, "provider", lambda: None)
    res = _llm.suggest(BROKEN_CALL, run_frontend)
    assert res["configured"] is False and res["suggestions"] == []


def test_llm_endpoint_never_returns_the_key(monkeypatch):
    monkeypatch.setattr(_llm, "provider", lambda: None)
    c = TestClient(app)
    body = c.post("/api/llm-fix", json={"source": BROKEN_CALL}).text
    health = c.get("/api/health").text
    secret = __import__("os").environ.get("GROQ_API_KEY", "")
    assert not secret or (secret not in body and secret not in health)
