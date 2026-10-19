# Compiler Pipeline Visualizer

**A compiler that diagnoses its own errors with machine learning - and verifies every fix before it shows it to you.**

MiniC is a small, statically-typed, C-like language. This project implements its complete compiler
pipeline and adds an ML layer to the *error-diagnosis* phase: when compilation fails, features produced
by the compiler itself (parser state, expected tokens, token context, symbol-table facts) are fed to a
classifier that ranks the **cause** of the error and proposes a repair. The compiler then re-runs
lexer → parser → semantic analysis on every candidate fix, and only fixes it accepts are offered.

> Compiler techniques are the backbone; ML is one component inside the system - and the compiler has the last word.

```
Source → Lexer → Parser → Semantic → IR (3AC) → Optimizer → VM
              ╲        ╲        ╲
               └── on failure: Feature extractor → ML classifier → Repair generator → Compiler validator ↺
```

## What is in the box

| Part | Where | What |
|---|---|---|
| Compiler | `backend/minic/` | lexer, recursive-descent parser, AST, scoped symbol table + type checker, three-address code, optimizer (folding, algebraic, copy/constant propagation, branch folding, unreachable code, liveness-based DCE), basic blocks + CFG + live-variable analysis, VM with execution trace |
| ML repair | `backend/repair/` | 40 compiler-derived features, 12-cause classifier, candidate repair generators, compiler validation loop, auto-fix, rule baseline, feature-occlusion explanations |
| Training | `backend/ml/` | seed-program generator, 12 error mutators, dataset builder, model comparison + training, end-to-end repair evaluation |
| API | `backend/app/` | FastAPI: compile, diagnose, autofix, examples, model metrics, dataset browser |
| Web UI | `frontend/` | React + Vite, [React Bits](https://reactbits.dev) components, three.js 3D scenes, CodeMirror editor, Recharts dashboard |
| Data | `datasets/` | 700 valid seeds, **3,120 labelled error programs in one folder per cause**, 36 hand-written test programs, extracted feature CSVs |
| Models | `models/` | trained classifier (`.joblib`), `metrics.json`, `repair_eval.json` |
| Original | `legacy/pipeline.html` | the first single-file prototype this grew out of |

## Run it

Requirements: Python 3.10+ and Node 18+.

```bash
# 1. backend (from the repository root)
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows   (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000

# 2. frontend (second terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173  (proxies /api to :8000)
```

The trained model and datasets are committed, so everything works straight after install.
To reproduce them from scratch:

```bash
cd backend
python -m ml.build_dataset        # writes datasets/ (seeds, labeled/<CAUSE>/, features CSVs)
python -m ml.train                # compares 4 models, writes models/*.joblib + metrics.json
python -m ml.evaluate_repair      # end-to-end repair evaluation -> models/repair_eval.json
python -m pytest                  # 191 tests
```

Production build of the UI: `npm run build` (output in `frontend/dist`).

## The web app

* **Home** - animated 3D pipeline scene, how it works, syllabus coverage.
* **Studio** - edit MiniC with live compile. Every phase has its own view: animated lexer with DFA diagrams,
  2D/3D syntax tree, symbol/scope table, three-address code, control-flow graph with live-in/live-out sets,
  optimizer before/after diff, and a stepping VM. When a program fails, **AI Diagnosis** shows the ranked causes,
  the features that drove the prediction, the compiler-detected line versus the ML-localised line, and
  candidate fixes badged *verified / partial / rejected*. One-click quick fix or auto-fix-all (with undo).
* **Dashboard** - model comparison, ML vs rule-baseline per cause, confusion matrix, feature importance,
  end-to-end repair outcomes, confidence calibration, dataset composition, live session counters.
* **Dataset** - browse every labelled folder; each sample is shown beside its ground-truth program.
* **Architecture** - the full diagram, design decisions, feature vector, syllabus-to-code mapping, grammar.

## The language (MiniC)

```c
int n = 10;
float avg = 0;
string label = "total=";
while (n > 0) {
  avg = avg + n * 1.5;
  n = n - 1;
}
if (avg > 50.0 && n == 0) { print(label + "big"); } else { print("small"); }
```

Types `int float bool string`; `int → float` widening only; conditions must be `bool`; `&&`/`||` short-circuit;
blocks have their own scope. The grammar is on the Architecture page and in `backend/minic/parser.py`.

## The 12 causes the classifier distinguishes

Syntax: missing `;` · missing `)` · missing `(` · missing `}` · missing `{` · misspelled keyword · `=` vs `==`.
Semantic: misspelled variable · missing declaration · use before declaration · use outside scope · type mismatch.

A compiler *symptom* is ambiguous: `undeclared identifier 'nam'` can be a typo, a missing declaration, a
use-before-declaration or a scope error - each needs a different fix. That ambiguity is where ML earns its place.

## Results

Measured on held-out programs (train/test split by seed program, so no leakage), on a hand-written set, and
end-to-end against the real compiler. Exact numbers are on the Dashboard and in `models/metrics.json`.

| | ML (Gradient Boosting) | Rule baseline |
|---|---|---|
| Cause accuracy (650 held-out programs) | **98.6 %** | 86.2 % |
| Hand-written programs (36) | **100 %** | 88.9 % |
| Top fix recompiles cleanly | **99.1 %** | 88.1 % |

**Honesty notes.** The training data is synthetic (valid programs corrupted by mutators), which is why
the hand-written set exists. Programs are assumed to contain one fault at a time; several faults are repaired
one after another. Exact-recovery of the original program is lower than "recompiles cleanly" (73 %) because
several different fixes can be valid. The language has no functions, arrays or pointers.

## Project layout

```
backend/   minic/ repair/ ml/ app/ tests/
datasets/  seeds/valid/  labeled/<CAUSE>/*.mc  handwritten/<CAUSE>/  processed/
models/    error_classifier.joblib  metrics.json  repair_eval.json
frontend/  src/{pages,components,reactbits,lib}  scripts/fetch-reactbits.mjs
docs/      ARCHITECTURE.md  REVIEW_NOTES.md
legacy/    pipeline.html
```

## Credits

UI components are from [React Bits](https://reactbits.dev) (vendored under `frontend/src/reactbits/`,
re-fetchable with `npm run fetch:reactbits`). The visual design takes its palette from the Yudu Robotics website.
