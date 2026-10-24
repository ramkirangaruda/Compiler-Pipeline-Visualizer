"""Lexer, parser, semantic analysis, IR, optimizer and VM."""
import random

import pytest

from minic import compile_source, run_frontend
from minic.lexer import lex
from ml.seeds import generate_seed


def codes(src):
    return [d.code for d in run_frontend(src).errors]


def test_lexer_tokens_and_positions():
    toks, errs = lex('int x = 3.5; // c\nprint("a\\"b");')
    assert not errs
    assert [t.kind for t in toks][:5] == ["TYPE", "IDENT", "OP", "FLOAT", "PUNCT"]
    assert toks[-2].value == ";" and toks[-1].kind == "EOF"
    assert any(t.kind == "STRING" and t.line == 2 for t in toks)


def test_lexer_errors():
    assert "E_UNEXPECTED_CHAR" in codes("int x = 3 @ 4;")
    assert "E_UNTERMINATED_STRING" in codes('string s = "abc;\n')


def test_parser_reports_expected_token_and_context():
    d = run_frontend("int x = 5\nint y = 6;").errors[0]
    assert d.code == "E_EXPECTED_TOKEN" and d.extra["expected"] == [";"] and d.extra["ctx"] == "decl_end"
    assert d.line == 2  # detected at the next statement, not where the fault is


def test_parser_eof_and_block_errors():
    assert codes("int x = 1;\nwhile (x < 3) {\n x = x + 1;\n") == ["E_UNEXPECTED_EOF"]
    assert codes("if (true) print(1);") == ["E_EXPECTED_TOKEN"]


def test_semantic_scopes_and_facts():
    d = run_frontend("int n = 1;\nif (n > 0) {\n int z = 2;\n}\nprint(z);").errors[0]
    assert d.code == "E_UNDECLARED" and d.extra["closed_scope"] and not d.extra["declared_later"]
    d = run_frontend("print(q);\nint q = 3;").errors[0]
    assert d.extra["declared_later"] and not d.extra["closed_scope"]
    d = run_frontend("int total = 1;\nprint(totl);").errors[0]
    assert d.extra["visible"][0] == ["total", 1]


def test_type_system():
    assert "E_TYPE_MISMATCH" in codes("int x = 2.5;")
    assert "E_TYPE_MISMATCH" in codes("bool b = 1;")
    assert not codes("float f = 3;")  # widening is allowed
    assert "E_BAD_OPERAND" in codes('int x = 1 + "a";')
    assert "E_BAD_CONDITION" in codes("int n = 1;\nif (n) { }")
    assert not codes('string s = "a" + "b";\nbool ok = s == "ab";')


def test_shadowing_gets_unique_names():
    r = compile_source("int x = 1;\nif (true) {\n int x = 2;\n print(x);\n}\nprint(x);")
    assert r["ok"] and r["execution"]["output"] == ["2", "1"]


def test_redeclaration_is_an_error():
    assert "E_REDECLARED" in codes("int x = 1;\nint x = 2;")


def test_execution_semantics():
    r = compile_source("int a = 7 / 2;\nint b = -7 / 2;\nint c = -7 % 3;\nfloat d = 7 / 2.0;\nprint(a);print(b);print(c);print(d);")
    assert r["execution"]["output"] == ["3", "-3", "-1", "3.5"]
    r = compile_source("bool t = true || (1 / 0 == 1);\nprint(t);")  # short-circuit: no division executed
    assert r["execution"]["output"] == ["true"]


def test_int_is_32_bit_and_wraps():
    r = compile_source("int x = 2147483647;\nx = x + 1;\nprint(x);\nint y = 65536 * 65536;\nprint(y);")
    assert r["execution"]["output"] == ["-2147483648", "0"] and r["verify"]["match"]


def test_infinite_loop_is_cut_off_safely():
    r = compile_source("int x = 1;\nwhile (true) {\n x = x * 3;\n}\n")
    assert r["execution"]["halted"] == "step_limit" and r["verify"]["match"] is not None


def test_runtime_error_is_reported_not_raised():
    r = compile_source("int z = 0;\nprint(10 / z);")
    assert r["execution"]["halted"] == "error" and "division by zero" in r["execution"]["error"]


def test_optimizer_does_real_work():
    src = "int a = 2 * 3;\nint dead = a * 9;\nint b = a + 0;\nif (true) { print(b); } else { print(0); }"
    r = compile_source(src)
    rep = {x["name"]: x["count"] for x in r["optimized"]["report"]}
    assert rep["Constant folding"] >= 1 and rep["Branch folding"] == 1
    assert rep["Dead code elimination (liveness)"] >= 1
    assert r["stats"]["tac_after"] < r["stats"]["tac_before"]
    assert r["verify"]["match"] and r["execution"]["output"] == ["6"]


def test_copy_propagation_respects_redefinition():
    # regression: `b = a; a = 5; print(b)` must still print the OLD value of a
    r = compile_source("int a = 1;\nint b = a;\na = 5;\nprint(b);\nprint(a);")
    assert r["execution"]["output"] == ["1", "5"] and r["verify"]["match"]


def test_cfg_and_liveness():
    r = compile_source("int i = 0;\nwhile (i < 3) {\n i = i + 1;\n}\nprint(i);")
    blocks = r["cfg"]["blocks"]
    assert len(blocks) >= 3
    assert any("i" in b["live_in"] for b in blocks)
    assert any(s["kind"] == "jump" for b in blocks for s in b["succ"])


@pytest.mark.parametrize("seed", range(150))
def test_optimizer_preserves_semantics_on_random_programs(seed):
    src = generate_seed(random.Random(seed))
    r = compile_source(src)
    assert r["ok"], r["diagnostics"]
    assert r["execution"]["halted"] == "done"
    assert r["verify"]["match"], src


# ------------------------------------------------------------------ for loops
def test_for_loop_runs_and_scopes_its_counter():
    from minic import compile_source
    r = compile_source("int total = 0;\nfor (int i = 1; i <= 4; i = i + 1) {\n  total = total + i;\n}\nprint(total);\n")
    assert r["ok"] and r["execution"]["output"] == ["10"]
    r = compile_source("for (int i = 0; i < 3; i = i + 1) { }\nprint(i);\n")
    assert not r["ok"] and r["diagnostics"][0]["code"] == "E_UNDECLARED"
    r = compile_source("int i;\nfor (i = 0; i < 3; i = i + 1) { print(i); }\nprint(i);\n")
    assert r["ok"] and r["execution"]["output"] == ["0", "1", "2", "3"]


def test_for_loop_syntax_errors_and_repair():
    from repair.engine import Engine
    e = Engine()
    src = "for (int i = 0; i < 3; i = i + 1 {\n  print(i);\n}\n"
    res = e.diagnose(src)
    assert res["entries"][0]["prediction"]["label"] == "MISSING_RPAREN"
    assert e.autofix(src)["ok"]
    out_of_scope = "for (int i = 0; i < 3; i = i + 1) { print(i); }\nprint(i);\n"
    fixed = e.autofix(out_of_scope)
    assert fixed["ok"] and "int i = 0;\nfor (i = 0" in fixed["final_source"]
