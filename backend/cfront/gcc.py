"""The real C compiler as the judge.

Our own front end (pycparser + a scope/type checker) produces the rich facts the ML layer learns from, but a
program is only "correct" if a real compiler accepts it. This module runs gcc (or clang/cc, whichever is on
PATH) and returns its diagnostics as data - message, position, option, and the compiler's own *fix-its*.

    run(source)          compile only (-fsyntax-only): fast, used for every candidate fix
    run(source, link=True) full build to a throw-away executable: also reports linker errors (no main, undefined reference)

The source is never executed here. Programs are single-file: `#include "..."` of local or absolute paths is refused,
so a submitted program cannot make the compiler read arbitrary files.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional

COMPILER = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")
STD = "-std=gnu11"
TIMEOUT = 10
_BAD_INCLUDE = re.compile(
    r'^\s*#\s*(?:include|include_next|embed|import)\s*(?:"|<\s*(?:[/\\]|[A-Za-z]:|\.\.))|__has_include(?:_next)?\s*\(\s*["<]', re.M)


@dataclass
class GDiag:
    kind: str                       # error | warning | note | link
    message: str
    line: int = 1
    col: int = 1
    start: int = 0
    end: int = 0
    option: Optional[str] = None
    fixits: list = field(default_factory=list)   # [(start, end, text)] in source offsets
    notes: list = field(default_factory=list)    # [{"message": str, "fixits": [(s, e, t)], "start": int}]

    def to_dict(self) -> dict:
        return {"kind": self.kind, "message": self.message, "line": self.line, "col": self.col, "start": self.start,
                "end": self.end, "option": self.option, "fixits": [list(f) for f in self.fixits],
                "notes": [{"message": n["message"], "fixits": [list(f) for f in n["fixits"]]} for n in self.notes]}


@dataclass
class GccResult:
    available: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    raw: str = ""
    linked: bool = False

    @property
    def ok(self) -> bool:
        return self.available and not self.errors


class _Offsets:
    """Maps gcc's (line, byte-column) to character offsets in the original string."""

    def __init__(self, source: str):
        self.b = source.encode("utf-8")
        self.starts = [0]
        for i, c in enumerate(self.b):
            if c == 10:
                self.starts.append(i + 1)
        self.ascii = len(self.b) == len(source)

    def off(self, line: int, bcol: int) -> int:
        line = max(1, min(line, len(self.starts)))
        bo = min(self.starts[line - 1] + max(bcol, 1) - 1, len(self.b))
        return bo if self.ascii else len(self.b[:bo].decode("utf-8", "ignore"))


def available() -> bool:
    return COMPILER is not None


def _loc(o: _Offsets, loc: dict) -> int:
    return o.off(loc.get("line", 1), loc.get("byte-column", loc.get("column", 1)))


def _fixits(o: _Offsets, items: list) -> list:
    out = []
    for f in items or []:
        s, e = _loc(o, f["start"]), _loc(o, f["next"])
        out.append((s, e, f.get("string", "")))
    return out


def _parse_json(text: str, o: _Offsets) -> tuple[list, list]:
    errors, warnings = [], []
    i = text.find("[")
    data = []
    while i >= 0:
        try:
            data, _ = json.JSONDecoder().raw_decode(text[i:])
            break
        except ValueError:
            i = text.find("[", i + 1)
    for d in data if isinstance(data, list) else []:
        kind = d.get("kind", "error")
        if kind not in ("error", "fatal error", "warning"):
            continue
        locs = d.get("locations") or [{}]
        caret = locs[0].get("caret") or {}
        finish = locs[0].get("finish") or caret
        start = _loc(o, caret) if caret else 0
        end = _loc(o, finish) + 1 if finish else start + 1
        notes = [{"message": c.get("message", ""), "fixits": _fixits(o, c.get("fixits")),
                  "start": _loc(o, (c.get("locations") or [{}])[0].get("caret") or {}) if (c.get("locations") or [{}])[0].get("caret") else 0}
                 for c in d.get("children", [])]
        g = GDiag("warning" if kind == "warning" else "error", d.get("message", ""), caret.get("line", 1),
                  caret.get("display-column", caret.get("column", 1)), start, max(end, start + 1), d.get("option"),
                  _fixits(o, d.get("fixits")), notes)
        (warnings if kind == "warning" else errors).append(g)
    return errors, warnings


NM = shutil.which("nm") or (os.path.join(os.path.dirname(COMPILER), "nm.exe") if COMPILER and os.path.exists(os.path.join(os.path.dirname(COMPILER), "nm.exe")) else None)


def _link_diag(msg: str, source: str, name: str = "") -> GDiag:
    end = len(source)
    return GDiag("link", msg, max(1, source.count("\n") + 1), 1, end, end, "link", [], [{"message": name, "fixits": [], "start": 0}])


def _link_errors(obj: str, d: str, source: str) -> list:
    """Linker problems, found without depending on the linker's (platform-dependent) messages:
    ask `nm` which symbols the object file defines and which it needs, then confirm with a real link."""
    from .headers import HEADER_OF
    defined, needed = set(), set()
    if NM:
        out = subprocess.run([NM, obj], capture_output=True, timeout=TIMEOUT, cwd=d).stdout.decode("utf-8", "replace")
        for ln in out.splitlines():
            parts = ln.split()
            if len(parts) >= 2 and parts[-2] == "U":
                needed.add(parts[-1])
            elif len(parts) >= 3 and parts[-2] in "TtDdBbRrCc":
                defined.add(parts[-1])
    suspicious = sorted(n for n in needed if not n.startswith("_") and n not in HEADER_OF and "@" not in n)
    no_main = NM is not None and "main" not in defined
    if NM and not suspicious and not no_main:
        return []
    exe = os.path.join(d, "main.exe")
    r = subprocess.run([COMPILER, obj, "-o", exe, "-lm"], capture_output=True, timeout=TIMEOUT, cwd=d)
    if r.returncode == 0:
        return []
    if no_main:
        return [_link_diag("no main() function: the program has nothing to run (undefined reference to 'main')", source, "main")]
    if suspicious:
        return [_link_diag(f"undefined reference to '{n}': it is called but never defined", source, n) for n in suspicious]
    return [_link_diag("the linker failed: " + ((r.stderr or b"").decode("utf-8", "replace").strip().splitlines() or ["unknown error"])[-1][:200], source)]


def run(source: str, link: bool = False) -> GccResult:
    if COMPILER is None:
        return GccResult(False)
    if _BAD_INCLUDE.search(source):
        m = _BAD_INCLUDE.search(source)
        line = source.count("\n", 0, m.start()) + 1
        g = GDiag("error", "#include of a local or absolute path is not supported: programs are single files", line, 1,
                  m.start(), m.end(), "include")
        return GccResult(True, [g], [], "", False)
    o = _Offsets(source)
    env = dict(os.environ, LC_ALL="C", LANG="C", GCC_COLORS="")
    with tempfile.TemporaryDirectory(prefix="cpv_") as d:
        src = os.path.join(d, "main.c")
        with open(src, "wb") as f:
            f.write(o.b)
        obj = os.path.join(d, "main.o")
        cmd = [COMPILER, STD, "-Wall", "-fdiagnostics-format=json", "-fno-diagnostics-show-caret"]
        cmd += ["-c", src, "-o", obj] if link else ["-fsyntax-only", src]
        try:
            p = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT, cwd=d, env=env)
        except subprocess.TimeoutExpired:
            g = GDiag("error", "the compiler timed out (the program is too complex to analyse)", 1, 1, 0, 1)
            return GccResult(True, [g])
        text = (p.stderr or b"").decode("utf-8", "replace")
        errors, warnings = _parse_json(text, o)
        if link and not errors and p.returncode == 0:
            try:
                errors = _link_errors(obj, d, source)
            except subprocess.TimeoutExpired:
                errors = []
    if link and not errors and p.returncode != 0:
        errors = [GDiag("error", (text.strip().splitlines() or ["the compiler rejected the program"])[-1][:200], 1, 1, 0, 1)]
    elif not link and not errors and p.returncode != 0:
        errors = [GDiag("error", (text.strip().splitlines() or ["the compiler rejected the program"])[-1][:200], 1, 1, 0, 1)]
    return GccResult(True, errors, warnings, text, link)


def native_run(source: str, timeout: float = 5.0, limit: int = 65536) -> Optional[dict]:
    """Build and run the program for real. Only used when PIPELINE_NATIVE_RUN=1 (it executes user code)."""
    if COMPILER is None or os.environ.get("PIPELINE_NATIVE_RUN") != "1" or _BAD_INCLUDE.search(source):
        return None
    with tempfile.TemporaryDirectory(prefix="cpv_run_") as d:
        src, exe = os.path.join(d, "main.c"), os.path.join(d, "main.exe")
        open(src, "w", encoding="utf-8").write(source)
        c = subprocess.run([COMPILER, STD, src, "-o", exe, "-lm"], capture_output=True, timeout=TIMEOUT, cwd=d)
        if c.returncode != 0:
            return None
        try:
            r = subprocess.run([exe], capture_output=True, timeout=timeout, cwd=d, stdin=subprocess.DEVNULL)
            out, halted, err, code = r.stdout[:limit].decode("utf-8", "replace"), "done", None, r.returncode
        except subprocess.TimeoutExpired as e:
            out, halted, err, code = (e.stdout or b"")[:limit].decode("utf-8", "replace"), "step_limit", None, -1
    lines = out.split("\n")
    return {"language": "c", "output": lines[:-1] if out.endswith("\n") else lines, "raw_output": out, "vars": {}, "steps": 0,
            "halted": halted, "error": err, "trace": [], "trace_truncated": False, "exit_code": code, "native": True}
