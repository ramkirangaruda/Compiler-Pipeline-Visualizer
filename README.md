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
| Real C | `backend/cfront/` | tokenizer, pycparser grammar, header-aware prelude, C scope/type checker, tree-walking interpreter (output matches gcc) |
| ML repair | `backend/repair/` | 40 compiler-derived features, 12-cause classifier, candidate repair generators, compiler validation loop, auto-fix, rule baseline, feature-occlusion explanations |
| Reinforcement learning | `backend/repair/rl/`, `backend/ml/rl/` | REINFORCE fix-selection policy over compiler-validated candidates, repair MDP, multi-fault generator, online learning from user accepts/undos |
| Training | `backend/ml/` | seed-program generator, 12 error mutators, dataset builder, model comparison + training, end-to-end repair evaluation |
| API | `backend/app/` | FastAPI: compile, diagnose, autofix, examples, model metrics, dataset browser |
| Web UI | `frontend/` | React + Vite, [React Bits](https://reactbits.dev) components, three.js 3D scenes, CodeMirror editor, Recharts dashboard |
| Data | `datasets/`, `datasets/c/` | MiniC: 700 valid seeds, **3,120 labelled error programs in one folder per cause**, 36 hand-written test programs. C: 600 seeds, **2,800 labelled programs** verified against gcc, 42 hand-written programs |
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
python -m ml.build_dataset_c      # real C: datasets/c/ (every sample cross-checked with gcc)
python -m ml.train --lang c       # C classifier -> models/error_classifier_c.joblib, metrics_c.json
python -m ml.evaluate_repair --lang c
python -m pytest                  # 231 tests
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
| Exact recovery of the intended program | 38.5 % | **39.1 %** | 28.2 % |
| Ends in a program that compiles | 98.6 % | 98.6 % | 94.7 % |
| Mean tokens still differing from the intended program | 9.27 | **9.15** | 9.08 |

Paired bootstrap, RL minus heuristic: exact recovery **+0.5 pts** (95 % CI +0.2 to +0.9), distance **-0.12 tokens** (CI -0.16 to -0.08) -
the intervals exclude zero, so the improvement is real, but it is **small**. On single-fault programs the RL ordering barely moves exact
recovery (69.8 % to 70.0 %). The gain comes from choices the heuristic cannot rank well, mainly where a declaration should be placed; the policy
can only choose among the candidates the repair generators propose, which caps what it can achieve.

## Real C, not just MiniC

The Studio has a **MiniC | C** switch. C is the real language: the same diagnose-and-repair loop runs on ordinary C programs.

* **Front end** (`backend/cfront/`) - own tokenizer + preprocessor-directive handling, [pycparser](https://github.com/eliben/pycparser)
  for the grammar (its LALR tables tell us which tokens it *would* have accepted - the C counterpart of MiniC's expected-token set),
  and our own scope/type analysis with real C rules (pointers, arrays, structs, typedefs, enums, for-loop scope, call arity).
  Standard-library declarations are fed to the parser **only if the matching `#include` is present**, so forgetting `<stdio.h>`
  is a genuine, diagnosable error exactly as in a real compiler.
* **Interpreter** (`backend/cfront/interp.py`) - runs the checked program (32-bit integer wrap-around, pointer arithmetic, `printf`, the
  common `<string.h>`/`<math.h>`/`<stdlib.h>`/`<ctype.h>` functions) with a step trace for the Run tab. It matches gcc's output on every seed program.
* **14 causes** - the 12 MiniC causes plus *missing `#include`* and *wrong argument count*; 50 features; its own classifier, candidate
  generators (hoist a loop variable out of a `for`, add `&`/`*`, cast a float operand of `%`, add the missing header …) and gcc-style validation loop.
  The reinforcement-learning policy is shared: it ranks candidates by generic features, so it works for either language.
* **Data** (`datasets/c/`) - 600 valid seed programs, **2,800 labelled broken programs in one folder per cause**, 42 hand-written textbook-style
  programs. **gcc (`-std=c11`) is the independent oracle**: every seed compiles with gcc, and every labelled mutant is rejected by gcc
  (it agreed on 2,800/2,800 candidates before filtering).

Rebuild: `python -m ml.build_dataset_c`, `python -m ml.train --lang c`, `python -m ml.evaluate_repair --lang c`.
**C results** (569 held-out programs, split by seed): cause accuracy **98.2 %** (rule baseline 67.8 %); hand-written programs 97.6 % (baseline 76.2 %); top-ranked fix recompiles cleanly **91.4 %** (baseline 66.4 %); auto-fix ends in a clean program **95.6 %** (baseline 71.2 %); exact recovery of the original program 64.5 % (65.6 % with the RL ordering). Selected model: Logistic Regression.
Not supported: the preprocessor beyond `#include`/`#define` constants, `goto`, function pointers, unions/bit-fields in the interpreter, `scanf` input.

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
blocks have their own scope. Statements: declaration, assignment, `print`, `if`/`else`, `while` and `for` (the loop variable lives only inside the loop). The grammar is on the Architecture page and in `backend/minic/parser.py`.

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
| Cause accuracy (653 held-out programs) | **98.9 %** | 87.9 % |
| Hand-written programs (36) | **100 %** | 88.9 % |
| Top-ranked fix recompiles cleanly | **95.9 %** | 87.6 % |
| Auto-fix ends in a clean program | **98.2 %** | 90.1 % |

**Honesty notes.** The training data is synthetic (valid programs corrupted by mutators), which is why
the hand-written set exists. Programs are assumed to contain one fault at a time; several faults are repaired
one after another. Exact-recovery of the original program is lower than "recompiles cleanly" (70 %) because
several different fixes can be valid. MiniC itself has no functions, arrays or pointers - the C mode covers those.

## Project layout

```
backend/   minic/ cfront/ repair/ ml/ app/ tests/
datasets/  seeds/valid/  labeled/<CAUSE>/*.mc  handwritten/<CAUSE>/  processed/   c/ (same layout, *.c)
models/    error_classifier.joblib  metrics.json  repair_eval.json  (+ *_c.* for C)
frontend/  src/{pages,components,reactbits,lib}  scripts/fetch-reactbits.mjs
docs/      ARCHITECTURE.md  REVIEW_NOTES.md
legacy/    pipeline.html
```

## Credits

UI components are from [React Bits](https://reactbits.dev) (vendored under `frontend/src/reactbits/`,
re-fetchable with `npm run fetch:reactbits`). The visual design takes its palette from the Yudu Robotics website.
