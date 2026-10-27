# Compiler Pipeline Visualizer

**A C compiler front end that diagnoses its own errors with machine learning - and has the real C compiler (gcc) verify every fix before it shows it to you.**

The project works on **real C**. When a program fails, features produced by the compiler itself (parser state, expected tokens, token
context, symbol-table facts) go to a classifier that ranks the **cause** of the error and proposes a repair. For anything outside the
causes the model was trained on, the compiler's own *fix-its* and a small repair search supply the candidates. **gcc is the judge**: a fix
is shown only if gcc accepts the result, and a reinforcement-learning policy decides which valid fix comes first. (MiniC, the small
teaching language the project started from, is still in the Studio as a second tab.)

> Compiler techniques are the backbone; ML is one component inside the system - and the compiler has the last word.

```
C source -> Lexer -> Parser -> Semantic -> gcc (the judge) -> Run
                 |
                 +-- on failure: Feature extractor -> ML classifier -> Repair generators (own + gcc fix-its + search)
                                 -> RL policy -> gcc validator --(rejected: next candidate)--+
                                                       |                                      |
                                                       +--> verified fix shown <--------------+
```

## What is in the box

| Part | Where | What |
|---|---|---|
| MiniC compiler | `backend/minic/` | the teaching language (with `if`, `while`, `for`): lexer, recursive-descent parser, AST, scoped symbol table + type checker, three-address code, optimizer (folding, algebraic, copy/constant propagation, branch folding, unreachable code, liveness-based DCE), basic blocks + CFG + live-variable analysis, VM with execution trace |
| Real C | `backend/cfront/` | tokenizer, pycparser grammar, header-aware prelude, C scope/type checker, **gcc as the judge** (diagnostics, fix-its, link check), tree-walking interpreter (output matches gcc) |
| ML repair | `backend/repair/` | compiler-derived features (40 for MiniC, 50 for C), classifiers (12 / 14 causes), candidate generators incl. gcc fix-its and a repair search, gcc validation loop, backtracking auto-fix, rule baseline, feature-occlusion explanations |
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
python -m ml.stress_c             # random-damage stress test judged by gcc -> models/stress_c.json
python -m pytest                  # 244 tests
```

Production build of the UI: `npm run build` (output in `frontend/dist`).

## The web app

* **Home** - the 3D pipeline scene and a short explanation of how it works.
* **Studio** - type C (or MiniC, from the switch) and it is checked as you type. When the program fails you get one clear diagnosis: the
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

## Any error, not just the trained ones

A classifier can only recognise what it was trained on. So the pipeline does not rely on it alone:

1. **gcc decides what is an error.** Every program goes through gcc (`-std=gnu11 -Wall`, JSON diagnostics, plus a link check for
   "no `main()`" and undefined references). A program gcc accepts is never reported as broken, whatever our own front end thinks.
2. **Two sources of candidate fixes.** (a) Our own front end + ML for the 14 trained causes (typos, missing declarations, scope, types,
   missing `#include`, wrong argument count, missing `;` `)` `}` ...). (b) For everything else: gcc's own fix-its ("did you mean ...?",
   "insert `;`"), the right `#include` for a library name, a prototype for a function defined later, a repair search around the point where
   gcc stopped, operator and type swaps, struct-member and `const` fixes, a stub for an undefined function, a missing `main()`.
3. **gcc validates every candidate** (in parallel) as verified / partial / rejected; partial fixes are ranked by how far gcc gets.
4. **Auto-fix backtracks.** A greedy walk first; if it gets stuck, a best-first search can back out of a wrong turn.
5. **Ask an LLM (optional).** When the built-in fixes are weak guesses or absent, an **Ask an LLM** button sends the program and gcc's
   errors to a language model (Groq by default, `openai/gpt-oss-120b`). The model only *proposes* a corrected program; gcc rebuilds it,
   a wrong answer is thrown away (its new errors are fed back for one retry), and only builds that pass are offered with a diff and
   Apply. Off until a key exists: put `GROQ_API_KEY=...` in the git-ignored `backend/.env` (see `.env.example`) or the environment.
   The key stays on the server; the program is sent to the provider only when you click.
6. **Last resort, never automatic.** "Comment out the statement" is offered when nothing else works; it is always labelled and never chosen
   by Fix / Fix all.

### How well does it do? (stress test, `python -m ml.stress_c`)

Twenty textbook programs and generated ones are damaged by **random edits unrelated to the training mutators** (delete / insert / replace /
swap a token, delete or duplicate a line, delete or insert a character, misspell a name, drop an `#include`, change a type, cut the file
short). Only programs gcc rejects are kept. The numbers below are from a fresh random seed that was never used while tuning.

| 720 broken programs | repaired to a program gcc builds | exactly the original program |
|---|---|---|
| **all** | **95.3 %** (98.2 % if the last resort is allowed) | 48 % |
| small slips (one token or character) | 96.5 % | 59 % |
| structural damage (a line or the end of the file) | 91.7 % | 14 % |

**What the LLM button adds** (`python -m ml.llm_eval`): on the 34 stress-test programs the built-in repair could *not* fix, the model plus
gcc produced a build for **34 of 34**. That is a small, synthetic sample, and "builds" is not "is what the programmer meant" - but it shows the
button covers the long tail the trained parts miss.

**There is no promise that every possible error can be fixed.** A fix has to be both accepted by gcc *and* what the programmer meant, and
the second part cannot be known: delete a line of a program and there are many valid programs that compile, but only one was intended.
What is guaranteed: (1) a fix marked *verified* really builds with gcc, (2) nothing crashes or hangs on hostile input (empty, binary,
huge, deeply nested, macro bombs, `#include "/etc/passwd"`, infinite loops - see `tests/test_c.py`), and (3) every error shows gcc's
exact message even when no fix is found. Code that is logically wrong but compiles is not an error and is not touched.

### The parts

* **Own front end** (`backend/cfront/`) - tokenizer, [pycparser](https://github.com/eliben/pycparser) for the grammar (its LALR tables tell us which
  tokens it *would* have accepted), and our own scope/type analysis. Library declarations are fed to the parser only if the matching
  `#include` is present, so forgetting `<stdio.h>` is a genuine, diagnosable error.
* **gcc layer** (`cfront/gcc.py`) - runs the compiler, parses its diagnostics and fix-its, never executes the program, and refuses
  `#include` of local or absolute paths. If no C compiler is on `PATH` the system falls back to the own front end alone.
* **Interpreter** (`cfront/interp.py`) - runs checked programs for the Run tab (32-bit wrap-around, pointers, `printf`, common libc) with
  a step trace; matches gcc's output on every generated seed. Real execution of anything else is off by default
  (`PIPELINE_NATIVE_RUN=1` builds and runs it with gcc; only enable it on your own machine).
* **ML** - 14 causes, 50 features, its own classifier (98.2 % on 569 held-out programs, rules 67.8 %; hand-written 97.6 % vs 76.2 %).
  The reinforcement-learning policy is shared with MiniC.
* **Data** (`datasets/c/`) - 600 valid seeds, 2,800 labelled broken programs in one folder per cause, 42 hand-written programs; every
  sample is rejected by gcc (it agreed on 2,800 / 2,800 candidates before filtering).

Rebuild: `python -m ml.build_dataset_c`, `python -m ml.train --lang c`, `python -m ml.evaluate_repair --lang c`, `python -m ml.stress_c`.
Needs gcc (or clang) on `PATH`; on Windows install MSYS2 / MinGW-w64.
Not supported by the interpreter: `goto`, function pointers, unions, `scanf` input (gcc still judges such programs).

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

## Results (MiniC classifier; the C numbers are in the section above)

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
