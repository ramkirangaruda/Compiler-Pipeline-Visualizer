"""FastAPI service exposing the compiler, the ML repair engine, the model
metrics and the labelled dataset to the web UI."""
from __future__ import annotations

import csv
import json
import time
from collections import Counter
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from minic import compile_source
from repair.engine import Engine
from repair.labels import LABELS

from .examples import all_examples

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "datasets"
MODELS = ROOT / "models"
MAX_SOURCE = 20_000

app = FastAPI(title="Compiler Pipeline Visualizer API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
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


class SourceIn(BaseModel):
    source: str = Field(max_length=MAX_SOURCE)
    optimize: bool = True
    mode: Literal["ml", "baseline"] = "ml"


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
            "model": engine.clf.model_name if engine.clf else None}


@app.get("/api/examples")
def examples():
    return all_examples()


@app.get("/api/labels")
def labels():
    return [{"label": k, **v} for k, v in LABELS.items()]


@app.post("/api/compile")
def compile_(body: SourceIn):
    _check(body.source)
    result = compile_source(body.source, run_optimizer=body.optimize)
    SESSION["compiles"] += 1
    for s in result["stages"]:
        SESSION["stage_ms"][s["key"]] += s["ms"]
    diagnosis = None
    if not result["ok"]:
        SESSION["failed"] += 1
        diagnosis = engine.diagnose(body.source, mode=body.mode)
        _record(diagnosis)
    result["diagnosis"] = diagnosis
    return result


@app.post("/api/diagnose")
def diagnose(body: SourceIn):
    _check(body.source)
    diag = engine.diagnose(body.source, mode=body.mode)
    _record(diag)
    return diag


@app.post("/api/autofix")
def autofix(body: SourceIn):
    _check(body.source)
    res = engine.autofix(body.source, mode=body.mode)
    SESSION["autofixes"] += 1
    SESSION["autofix_ok"] += int(res["ok"])
    return res


@app.get("/api/model")
def model():
    metrics = _read_json(MODELS / "metrics.json")
    return {
        "loaded": engine.model_loaded,
        "metrics": metrics,
        "repair_eval": _read_json(MODELS / "repair_eval.json"),
        "dataset": _read_json(DATASETS / "processed" / "dataset_stats.json"),
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
