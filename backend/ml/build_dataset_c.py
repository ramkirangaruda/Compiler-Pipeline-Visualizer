"""Builds the labelled dataset of real C programs on disk, verified by two independent compilers
(this project's C front end and gcc).

    datasets/c/
      seeds/valid/seed_0001.c ...             valid programs the errors are injected into (gcc compiles them too)
      labeled/<LABEL>/<LABEL>_0001.c ...      one folder per error cause (the class label); gcc rejects every one
      labeled/<LABEL>/labels.csv              per-sample metadata for that class
      handwritten/<LABEL>/*.c                 hand-written out-of-distribution test programs
      manifest.csv                            every labelled sample, one row each
      processed/features.csv                  compiler-extracted feature vectors (+ train/test split)
      processed/handwritten_features.csv
      processed/label_map.json, dataset_stats.json

Run from backend/:  python -m ml.build_dataset_c
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import shutil
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cfront.pipeline import run_frontend
from repair.features_c import FEATURE_COLUMNS, extract
from repair.labels_c import LABEL_NAMES, LABELS

from .build_dataset import split_of, write_csv
from .c_mutators import make_sample
from .c_seeds import generate_seed

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "datasets" / "c"
GCC = shutil.which("gcc")


def gcc_rejects(src: str) -> bool | None:
    """True if gcc (-std=c11) refuses the program, False if it accepts it, None if gcc is unavailable."""
    if GCC is None:
        return None
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "a.c")
        Path(p).write_text(src, encoding="utf-8")
        return subprocess.run([GCC, "-std=c11", "-fsyntax-only", "-w", p], capture_output=True).returncode != 0


def build_seeds(n_seeds: int) -> list[tuple[str, str]]:
    cands, seen = [], set()
    for i in range(n_seeds * 3):
        src = generate_seed(random.Random(1000 + i))
        if src not in seen and not run_frontend(src).errors:
            seen.add(src)
            cands.append(src)
    with ThreadPoolExecutor(8) as ex:
        verdicts = list(ex.map(gcc_rejects, cands[: n_seeds + 40]))
    good = [s for s, rej in zip(cands, verdicts) if rej is not True][:n_seeds]
    return [(f"seed_{i + 1:04d}", s) for i, s in enumerate(good)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=600)
    ap.add_argument("--per-class", type=int, default=200)
    args = ap.parse_args()

    for sub in ("seeds", "labeled", "processed"):
        shutil.rmtree(DATASETS / sub, ignore_errors=True)
    (DATASETS / "seeds" / "valid").mkdir(parents=True)
    print("gcc:", GCC or "not found (the gcc cross-check is skipped)")

    seeds = build_seeds(args.seeds)
    for sid, src in seeds:
        (DATASETS / "seeds" / "valid" / f"{sid}.c").write_text(src, encoding="utf-8")
    print(f"seeds: {len(seeds)} (accepted by both compilers)")

    manifest_header = ["sample_id", "file", "label", "seed_id", "split", "error_line", "compiler_code",
                       "compiler_message", "mutation", "error_line_text", "gcc_rejects"]
    feat_header = ["sample_id", "label", "split", "seed_id"] + FEATURE_COLUMNS
    manifest_rows, feat_rows, counts = [], [], Counter()
    gcc_checked = gcc_agree = 0

    for label in LABEL_NAMES:
        folder = DATASETS / "labeled" / label
        folder.mkdir(parents=True, exist_ok=True)
        seen: set[str] = set()
        rows = []
        order = list(range(len(seeds)))
        for pass_no in range(14):
            random.Random(f"order-{label}-{pass_no}").shuffle(order)
            batch = []
            for si in order:
                if len(rows) + len(batch) >= args.per_class + 20:
                    break
                sid, seed_src = seeds[si]
                s = make_sample(label, seed_src, random.Random(f"{label}-{sid}-{pass_no}"))
                if s is None or s["source"] in seen:
                    continue
                seen.add(s["source"])
                batch.append((sid, s))
            with ThreadPoolExecutor(8) as ex:
                verdicts = list(ex.map(lambda b: gcc_rejects(b[1]["source"]), batch))
            for (sid, s), rej in zip(batch, verdicts):
                if len(rows) >= args.per_class:
                    break
                if rej is not None:
                    gcc_checked += 1
                    gcc_agree += bool(rej)
                if rej is False:      # gcc accepts the "broken" program: not a trustworthy example
                    continue
                n = len(rows) + 1
                sample_id = f"{label}_{n:04d}"
                fname = f"{sample_id}.c"
                (folder / fname).write_text(s["source"], encoding="utf-8")
                d = s["diag"]
                lines = s["source"].splitlines()
                line_text = lines[d.line - 1].strip() if 0 < d.line <= len(lines) else ""
                rows.append([sample_id, f"labeled/{label}/{fname}", label, sid, split_of(sid), d.line, d.code,
                             d.message, s["meta"]["mutation"], line_text, "" if rej is None else int(rej)])
                feat_rows.append([sample_id, label, split_of(sid), sid] + [s["features"][c] for c in FEATURE_COLUMNS])
            if len(rows) >= args.per_class:
                break
        write_csv(folder / "labels.csv", manifest_header, rows)
        manifest_rows.extend(rows)
        counts[label] = len(rows)
        print(f"{label:24s} {len(rows)}")

    write_csv(DATASETS / "manifest.csv", manifest_header, manifest_rows)
    write_csv(DATASETS / "processed" / "features.csv", feat_header, feat_rows)

    hw_rows, hw_counts = [], Counter()
    for label in LABEL_NAMES:
        hw_dir = DATASETS / "handwritten" / label
        for p in sorted(hw_dir.glob("*.c")) if hw_dir.exists() else []:
            src = p.read_text(encoding="utf-8")
            fe = run_frontend(src)
            if not fe.errors:
                print(f"WARNING: handwritten {p.name} compiles cleanly - skipped")
                continue
            f = extract(fe.errors[0], fe)
            hw_rows.append([p.stem, label, "handwritten", p.stem] + [f[c] for c in FEATURE_COLUMNS])
            hw_counts[label] += 1
    write_csv(DATASETS / "processed" / "handwritten_features.csv", feat_header, hw_rows)

    split_counts = Counter((r[2], r[4]) for r in manifest_rows)
    stats = {
        "language": "c",
        "n_seeds": len(seeds),
        "n_samples": len(manifest_rows),
        "per_label": {k: counts[k] for k in LABEL_NAMES},
        "per_label_split": {k: {"train": split_counts[(k, "train")], "test": split_counts[(k, "test")]} for k in LABEL_NAMES},
        "handwritten_per_label": {k: hw_counts[k] for k in LABEL_NAMES},
        "n_handwritten": sum(hw_counts.values()),
        "gcc_cross_check": {"available": GCC is not None, "mutants_checked": gcc_checked, "gcc_also_rejects": gcc_agree},
        "feature_columns": FEATURE_COLUMNS,
    }
    (DATASETS / "processed").mkdir(parents=True, exist_ok=True)
    (DATASETS / "processed" / "dataset_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    (DATASETS / "processed" / "label_map.json").write_text(
        json.dumps({k: {"id": i, **LABELS[k]} for i, k in enumerate(LABEL_NAMES)}, indent=2), encoding="utf-8")
    print(f"total labelled samples: {len(manifest_rows)}  handwritten: {sum(hw_counts.values())}  "
          f"gcc agreed on {gcc_agree}/{gcc_checked} mutants before filtering")


if __name__ == "__main__":
    main()
