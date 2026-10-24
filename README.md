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
| Reinforcement learning | `backend/repair/rl/`, `backend/ml/rl/` | REINFORCE fix-selection policy over compiler-validated candidates, repair MDP, multi-fault generator, online learning from user accepts/undos |
| Training | `backend/ml/` | seed-program generator, 12 error mutators, dataset builder, model comparison + training, end-to-end repair evaluation |
| API | `backend/app/` | FastAPI: compile, diagnose, autofix, examples, model metrics, dataset browser |
| Web UI | `frontend/` | React + Vite, [React Bits](https://reactbits.dev) components, three.js 3D scenes, CodeMirror editor, Recharts dashboard |
| Data | `datasets/` | 700 valid seeds, **3,120 labelled error programs in one folder per cause**, 36 hand-written test programs, extracted feature CSVs |
| Models | `models/` | trained classifier (`.joblib`), `metrics.json`, `repair_eval.json` |
| Original | `legacy/pipeline.html` | the first single-file prototype this grew out of |

## Run it

Requirements: Python 3.11+ (developed on 3.12) and Node 18+ (developed on 20).

**One click:** double-click `start.bat` (Windows) or run `./start.sh` (macOS/Linux). On first run it creates the
Python environment, installs packages and builds the UI; then everything is served on **http://localhost:8010**.

**Development mode** (hot reload, two terminals):

```bash
# 1. backend (from the repository root)
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows   (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8010

# 2. frontend (second terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173  (proxies /api to :8010)
```

The trained model and datasets are committed, so everything works straight after install.
To reproduce them from scratch:

```bash
cd backend
python -m ml.build_dataset        # writes datasets/ (seeds, labeled/<CAUSE>/, features CSVs)
python -m ml.train                # compares 4 models, writes models/*.joblib + metrics.json
python -m ml.evaluate_repair      # end-to-end repair evaluation -> models/repair_eval.json
python -m ml.rl.train_rl          # trains + evaluates the RL fix policy -> models/rl_policy.json, rl_metrics.json
python -m pytest                  # 212 tests
```

Production build of the UI: `npm run build` (output in `frontend/dist`).

## The web app

* **Home** - the 3D pipeline scene and a short explanation of how it works.
* **Studio** - type MiniC and it compiles as you type. When the program fails you get one clear diagnosis: the
  likely cause, how sure the model is, and a suggested fix (checked by the compiler) with a diff and an **Apply fix**
  button; **Undo** reverts it. When it compiles, tabs show the program's output and every compiler phase
  (tokens, syntax tree, symbols, optimized code, flow graph). The example menu has working and broken programs.
* **Dashboard** - four headline numbers and four charts: ML vs rules, the four models, and the reinforcement
  learning results.
* **Architecture** - the system diagram.

The labelled datasets live in `datasets/` (one folder per error cause); see `datasets/README.md`.

## Reinforcement learning: the fix-selection policy

The classifier says *why* the program failed; reinforcement learning decides *which fix to apply first*.

* **MDP.** State = the broken program (summarised by its compiler-validated candidate fixes); action = apply one candidate;
  reward = progress toward the intended program + a bonus when it compiles (and a larger one when it equals the original) - a step cost.
* **Learning.** A linear-softmax policy over candidate features, trained with REINFORCE (baseline + entropy bonus) on
  programs with 1-3 faults, warm-started from the hand-written ordering.
* **Online.** In the Studio, accepting a suggested fix is a +1 reward and undoing it a -1: each triggers a live policy-gradient step.
* **Safe by construction.** The policy only orders candidates; the compiler still validates each one and rejected fixes stay last.
* **Results** on held-out multi-fault programs and the learning curve are on the Dashboard (RL section) and in `models/rl_metrics.json`.

| Held-out programs with 1-3 faults (1,500) | Heuristic order | **RL policy** | Random |
|---|---|---|---|
| Exact recovery of the intended program | 37.5 % | **39.0 %** | 29.2 % |
| Ends in a program that compiles | 98.3 % | 98.3 % | 95.9 % |
| Mean tokens still differing from the intended program | 9.59 | **8.24** | 9.22 |

Paired bootstrap, RL minus heuristic: exact recovery **+1.5 pts** (95 % CI +0.9 to +2.2), distance **-1.36 tokens** (CI -1.51 to -1.21) -
the intervals exclude zero, so the improvement is real, but it is **modest**. On single-fault programs the RL ordering lifts exact recovery
from 70.2 % to 71.5 %. The gain comes from choices the heuristic cannot rank well, mainly where a declaration should be placed; the policy
can only choose among the candidates the repair generators propose, which caps what it can achieve.

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
| Cause accuracy (650 held-out programs) | **98.6 %** | 87.5 % |
| Hand-written programs (36) | **100 %** | 88.9 % |
| Top-ranked fix recompiles cleanly | **96.2 %** | 87.1 % |
| Auto-fix ends in a clean program | **98.8 %** | 89.7 % |

**Honesty notes.** The training data is synthetic (valid programs corrupted by mutators), which is why
the hand-written set exists. Programs are assumed to contain one fault at a time; several faults are repaired
one after another. Exact-recovery of the original program is lower than "recompiles cleanly" (70 %) because
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
