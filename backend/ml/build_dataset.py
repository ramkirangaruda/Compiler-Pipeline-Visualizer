"""Builds the labelled dataset on disk.

    datasets/
      seeds/valid/seed_0001.mc ...            valid programs the errors are injected into
      labeled/<LABEL>/<LABEL>_0001.mc ...     one folder per error cause (the class label)
      labeled/<LABEL>/labels.csv              per-sample metadata for that class
      handwritten/<LABEL>/*.mc                hand-written out-of-distribution test programs
      manifest.csv                            every labelled sample, one row each
      processed/features.csv                  compiler-extracted feature vectors (+ train/test split)
      processed/handwritten_features.csv
      processed/label_map.json, dataset_stats.json

Run from backend/:  python -m ml.build_dataset
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
from collections import Counter
from pathlib import Path

from minic import run_frontend
from repair.features import FEATURE_COLUMNS, extract
from repair.labels import LABEL_NAMES, LABELS

from .mutators import MUTATORS, make_sample
from .seeds import generate_seed

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "datasets"


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def build_seeds(n_seeds: int) -> list[tuple[str, str]]:
    seeds, seen, i = [], set(), 0
    while len(seeds) < n_seeds and i < n_seeds * 4:
        src = generate_seed(random.Random(1000 + i))
        i += 1
        if src in seen or run_frontend(src).errors:
            continue
        seen.add(src)
        seeds.append((f"seed_{len(seeds) + 1:04d}", src))
    return seeds


def split_of(seed_id: str) -> str:
    return "test" if int(seed_id.split("_")[1]) % 5 == 0 else "train"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=700)
    ap.add_argument("--per-class", type=int, default=260)
    args = ap.parse_args()

    for sub in ("seeds", "labeled", "processed"):
        shutil.rmtree(DATASETS / sub, ignore_errors=True)
    (DATASETS / "seeds" / "valid").mkdir(parents=True)

    seeds = build_seeds(args.seeds)
    for sid, src in seeds:
        (DATASETS / "seeds" / "valid" / f"{sid}.mc").write_text(src, encoding="utf-8")
    print(f"seeds: {len(seeds)}")

    manifest_header = ["sample_id", "file", "label", "seed_id", "split", "error_line", "compiler_code",
                       "compiler_message", "mutation", "error_line_text"]
    feat_header = ["sample_id", "label", "split", "seed_id"] + FEATURE_COLUMNS
    manifest_rows, feat_rows, counts = [], [], Counter()

    for label in LABEL_NAMES:
        folder = DATASETS / "labeled" / label
        folder.mkdir(parents=True, exist_ok=True)
        seen: set[str] = set()
        rows = []
        order = list(range(len(seeds)))
        for pass_no in range(14):
            random.Random(f"order-{label}-{pass_no}").shuffle(order)
            for si in order:
                if len(rows) >= args.per_class:
                    break
                sid, seed_src = seeds[si]
                s = make_sample(label, seed_src, random.Random(f"{label}-{sid}-{pass_no}"))
                if s is None or s["source"] in seen:
                    continue
                seen.add(s["source"])
                n = len(rows) + 1
                sample_id = f"{label}_{n:04d}"
                fname = f"{sample_id}.mc"
                (folder / fname).write_text(s["source"], encoding="utf-8")
                d = s["diag"]
                line_text = s["source"].splitlines()[d.line - 1].strip() if 0 < d.line <= len(s["source"].splitlines()) else ""
                row = [sample_id, f"labeled/{label}/{fname}", label, sid, split_of(sid), d.line, d.code,
                       d.message, s["meta"]["mutation"], line_text]
                rows.append(row)
                feat_rows.append([sample_id, label, split_of(sid), sid] + [s["features"][c] for c in FEATURE_COLUMNS])
            if len(rows) >= args.per_class:
                break
        write_csv(folder / "labels.csv", manifest_header, rows)
        manifest_rows.extend(rows)
        counts[label] = len(rows)
        print(f"{label:24s} {len(rows)}")

    write_csv(DATASETS / "manifest.csv", manifest_header, manifest_rows)
    write_csv(DATASETS / "processed" / "features.csv", feat_header, feat_rows)

    # ---- hand-written out-of-distribution set
    hw_rows, hw_counts = [], Counter()
    hw_dir = DATASETS / "handwritten"
    for label in LABEL_NAMES:
        for p in sorted((hw_dir / label).glob("*.mc")) if (hw_dir / label).exists() else []:
            src = p.read_text(encoding="utf-8")
            fe = run_frontend(src)
            errs = fe.errors
            if not errs:
                print(f"WARNING: handwritten {p.name} compiles cleanly - skipped")
                continue
            d0 = errs[0]
            f = extract(d0, fe)
            hw_rows.append([p.stem, label, "handwritten", p.stem] + [f[c] for c in FEATURE_COLUMNS])
            hw_counts[label] += 1
    write_csv(DATASETS / "processed" / "handwritten_features.csv", feat_header, hw_rows)

    split_counts = Counter((r[2], r[4]) for r in manifest_rows)
    stats = {
        "n_seeds": len(seeds),
        "n_samples": len(manifest_rows),
        "per_label": {k: counts[k] for k in LABEL_NAMES},
        "per_label_split": {
            k: {"train": split_counts[(k, "train")], "test": split_counts[(k, "test")]} for k in LABEL_NAMES
        },
        "handwritten_per_label": {k: hw_counts[k] for k in LABEL_NAMES},
        "n_handwritten": sum(hw_counts.values()),
        "feature_columns": FEATURE_COLUMNS,
    }
    (DATASETS / "processed").mkdir(parents=True, exist_ok=True)
    (DATASETS / "processed" / "dataset_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    (DATASETS / "processed" / "label_map.json").write_text(
        json.dumps({k: {"id": i, **{kk: vv for kk, vv in LABELS[k].items()}} for i, k in enumerate(LABEL_NAMES)}, indent=2),
        encoding="utf-8",
    )
    print(f"total labelled samples: {len(manifest_rows)}  handwritten: {sum(hw_counts.values())}")


if __name__ == "__main__":
    main()
