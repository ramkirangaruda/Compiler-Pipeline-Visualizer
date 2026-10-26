"""FastAPI service exposing the compiler, the ML repair engine, the model
metrics and the labelled dataset to the web UI."""
from __future__ import annotations

import csv
import json
import sys
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cfront.pipeline import compile_source as compile_c
from minic import compile_source
from repair import langs
from repair.engine import Engine
from repair.labels import LABELS

from .examples import all_examples

# Deeply nested source recurses deeply in the parser/analyzer: allow a generous
# depth and give worker threads a big stack so it never crashes the interpreter.
sys.setrecursionlimit(8000)
threading.stack_size(64 * 1024 * 1024)

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "datasets"
MODELS = ROOT / "models"
MAX_SOURCE = 20_000

app = FastAPI(title="Compiler Pipeline Visualizer API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(RecursionError)
def too_deep(_: Request, __: RecursionError):
    return JSONResponse(status_code=422, content={"detail": "Program is nested too deeply to analyse."})


engine = Engine()

SESSION = {
    "started": time.time(),
    "compiles": 0,
    "failed": 0,
    "diagnoses": 0,
    "autofixes": 0,
    "autofix_ok": 0,
    "by_label": Counter(),
    "stage_ms": Counter(),
}
RL_METRICS = MODELS / "rl_metrics.json"


class SourceIn(BaseModel):
    source: str = Field(max_length=MAX_SOURCE)
    optimize: bool = True
    mode: Literal["ml", "baseline"] = "ml"
    ranker: Literal["heuristic", "rl"] = "rl"  # who orders the candidate fixes
    language: Literal["minic", "c"] = "minic"


class FeedbackIn(BaseModel):
    decision_id: str = Field(max_length=64)
    candidate_id: str = Field(max_length=32)
    reward: float = Field(ge=-1.0, le=1.0)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _check(source: str) -> None:
    if len(source) > MAX_SOURCE:
        raise HTTPException(413, "source too large")


def _record(diag: dict) -> None:
    SESSION["diagnoses"] += len(diag["entries"])
    for e in diag["entries"]:
        if e.get("prediction"):
            SESSION["by_label"][e["prediction"]["label"]] += 1


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": engine.model_loaded,
            "model": engine.clf.model_name if engine.clf else None,
            "languages": {k: c.model_name if c else None for k, c in engine.clfs.items()}}


@app.get("/api/examples")
def examples():
    return all_examples()


@app.get("/api/labels")
def labels(language: Literal["minic", "c"] = "minic"):
    return [{"label": k, **v} for k, v in langs.get(language).labels.items()]


@app.post("/api/compile")
def compile_(body: SourceIn):
    _check(body.source)
    if body.language == "c":
        result = compile_c(body.source)
    else:
        result = compile_source(body.source, run_optimizer=body.optimize)
        result["language"] = "minic"
    SESSION["compiles"] += 1
    for s in result["stages"]:
        SESSION["stage_ms"][s["key"]] += s["ms"]
    diagnosis = None
    if not result["ok"]:
        SESSION["failed"] += 1
        diagnosis = engine.diagnose(body.source, mode=body.mode, ranker=body.ranker, language=body.language)
        _record(diagnosis)
    result["diagnosis"] = diagnosis
    return result


@app.post("/api/diagnose")
def diagnose(body: SourceIn):
    _check(body.source)
    diag = engine.diagnose(body.source, mode=body.mode, ranker=body.ranker, language=body.language)
    _record(diag)
    return diag


@app.post("/api/autofix")
def autofix(body: SourceIn):
    _check(body.source)
    res = engine.autofix(body.source, mode=body.mode, ranker=body.ranker, language=body.language)
    SESSION["autofixes"] += 1
    SESSION["autofix_ok"] += int(res["ok"])
    return res


@app.get("/api/rl")
def rl():
    """Reinforcement-learning fix policy: training results + live online-learning status."""
    return {"status": engine.rl_status(), "metrics": _read_json(RL_METRICS)}


@app.post("/api/rl/feedback")
def rl_feedback(body: FeedbackIn):
    """One online policy-gradient step: +1 when the user accepts a fix, -1 when they undo it."""
    res = engine.feedback(body.decision_id, body.candidate_id, body.reward)
    if res is None:
        raise HTTPException(404, "unknown decision (it may have expired) or no policy loaded")
    return res


@app.post("/api/rl/reset")
def rl_reset():
    engine.reset_policy()
    return engine.rl_status()


@app.get("/api/model")
def model(language: Literal["minic", "c"] = "minic"):
    lang = langs.get(language)
    return {
        "language": lang.key,
        "loaded": engine.clfs[lang.key] is not None,
        "metrics": _read_json(lang.metrics_path),
        "repair_eval": _read_json(lang.eval_path),
        "dataset": _read_json(lang.data_dir / "processed" / "dataset_stats.json"),
    }


@app.get("/api/session")
def session():
    return {
        **{k: v for k, v in SESSION.items() if k not in ("by_label", "stage_ms")},
        "uptime_s": round(time.time() - SESSION["started"]),
        "by_label": dict(SESSION["by_label"]),
        "stage_ms": {k: round(v, 2) for k, v in SESSION["stage_ms"].items()},
    }


def _manifest() -> list[dict]:
    path = DATASETS / "manifest.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


@app.get("/api/dataset")
def dataset():
    rows = _manifest()
    stats = _read_json(DATASETS / "processed" / "dataset_stats.json") or {}
    per = Counter(r["label"] for r in rows)
    return {
        "n_samples": len(rows),
        "n_seeds": stats.get("n_seeds", 0),
        "n_handwritten": stats.get("n_handwritten", 0),
        "classes": [
            {
                "label": k,
                "title": v["title"],
                "family": v["family"],
                "explain": v["explain"],
                "count": per[k],
                "folder": f"datasets/labeled/{k}/",
                "split": (stats.get("per_label_split") or {}).get(k, {}),
                "handwritten": (stats.get("handwritten_per_label") or {}).get(k, 0),
            }
            for k, v in LABELS.items()
        ],
    }


@app.get("/api/dataset/samples")
def dataset_samples(label: str, offset: int = 0, limit: int = Query(8, le=50)):
    if label not in LABELS:
        raise HTTPException(404, "unknown label")
    rows = [r for r in _manifest() if r["label"] == label]
    out = []
    for r in rows[offset : offset + limit]:
        src = (DATASETS / r["file"]).read_text(encoding="utf-8")
        seed_path = DATASETS / "seeds" / "valid" / f"{r['seed_id']}.mc"
        out.append(
            {
                "sample_id": r["sample_id"],
                "file": r["file"],
                "split": r["split"],
                "seed_id": r["seed_id"],
                "error_line": int(r["error_line"]),
                "compiler_message": r["compiler_message"],
                "mutation": r["mutation"],
                "source": src,
                "original": seed_path.read_text(encoding="utf-8") if seed_path.exists() else "",
            }
        )
    return {"label": label, "total": len(rows), "offset": offset, "samples": out}


# Serve the production UI (npm run build) from the same process when it exists.
UI_DIST = ROOT / "frontend" / "dist"
if UI_DIST.exists():
    app.mount("/", StaticFiles(directory=UI_DIST, html=True), name="ui")
