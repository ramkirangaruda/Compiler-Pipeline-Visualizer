# Architecture

## 1. Pipeline

```
 source ──► Lexer ──► Parser ──► Semantic analysis ──► IR (3AC) ──► Optimizer ──► VM
              │          │              │
              │          │              └─ symbol table, scopes, types
              │          └─ AST + parse context (expected tokens, production)
              └─ tokens (+ lexical errors)

 on failure:  error ──► Feature extractor ──► ML classifier ──► Repair generator ──► Validator
                                                                      ▲                  │
                                                                      └── rejected ◄─────┘
```

`minic.pipeline.run_frontend` (lex → parse → analyze) is the cheap front half. The validator calls it
once per candidate fix. `compile_source` is the full pipeline whose JSON the web UI renders.

## 2. Compiler (`backend/minic/`)

| Module | Responsibility |
|---|---|
| `lexer.py` | Hand-written scanner. Token classes correspond to `IDENT [A-Za-z_]\w*`, `INT [0-9]+`, `FLOAT [0-9]+.[0-9]+`, `STRING "…"`. Lexical errors are collected, not raised, so the parser can still run. |
| `parser.py` | Recursive descent, LL(1) apart from the `else if` chain. On the first syntax error it raises a `Diagnostic` whose `extra` holds the **expected token set**, the **parse context** (which production was active, e.g. `decl_end`, `if_close`) and the failing token index. |
| `ast.py` | Dataclass nodes, each with a source span (`start`/`end`) so repairs can be expressed as text edits. |
| `semantic.py` | Pre-pass builds the scope tree and a table of every declaration. Main pass resolves names in order, checks types, and annotates nodes (`ty`, `uid`). For an undeclared identifier it records the facts the ML model needs: nearest in-scope names with edit distance and type, *declared later in the chain?*, *declared in a closed scope?*, pooled type hints from every use. |
| `tac.py` | Post-order, syntax-directed translation to three-address code. `&&`/`||` become short-circuit jumps; int→float is an explicit `itof`. Shadowed variables get unique names (`x#2`). |
| `optimizer.py` | Constant folding · algebraic simplification · block-local copy/constant propagation (correctly invalidated on redefinition) · branch folding · jump threading · unreachable code · dead-label removal · **dead-code elimination driven by global live-variable analysis**. Iterated to a fixed point. |
| `cfg.py` | Leaders → basic blocks → edges, plus iterative live-variable analysis (`in = use ∪ (out − def)`). |
| `vm.py` | Label-addressed interpreter that records a step trace (pc, source line, variable written, output). |
| `ops.py` | Single definition of operator semantics shared by the folder and the VM, so compile-time and run-time evaluation cannot disagree (C-style truncating `/` and `%`). |

Correctness check: the optimizer is verified by running the unoptimized and optimized TAC and comparing output
(on every compile in the UI, and on 150 random programs in the test suite).

## 3. ML repair (`backend/repair/`)

1. **Features** (`features.py`) - 40 values, 14 categorical + 26 numeric, all produced by compiler phases:
   parser state (`err_code`, `ctx`, `expected`, `found`), token context (5 previous tokens, next token,
   newline-before-error, line start), bracket balance before the error and over the file, edit distance of the
   previous identifier to every keyword, symbol-table facts (nearest names, distances, type compatibility of the
   nearest name with the use), scope facts (declared later / in closed scope / lvalue) and type facts.
2. **Classifier** (`classifier.py`, trained by `ml/train.py`) - scikit-learn pipeline (one-hot + model). Four
   models are compared with 5-fold CV grouped by seed program; near-ties are broken by log-loss because the UI
   displays the model's confidence.
3. **Explanation** - model-agnostic feature occlusion: replace one feature at a time by its training-set mode and
   measure the drop in the predicted cause's probability.
4. **Candidates** (`candidates.py`) - per-cause edit generators (insert `;`, insert `}` using the indentation
   heuristic, rename to the nearest in-scope name, infer a declaration's type from every use, move a declaration
   above its first use, hoist a variable out of a closed block, change a declared type, …). Candidates are text
   edits `(start, end, replacement)`.
5. **Validation** (`validator.py`) - apply the edits, re-run lexer/parser/semantic analysis. `verified` = 0 errors;
   `partial` = this error is gone but others remain (or the parser got further); `rejected` otherwise.
6. **Engine** (`engine.py`) - ranks candidates by status, then `P(cause) × plausibility`; localises the fault to the
   best fix's edit position (so for a missing `;` the compiler says line 3 and the ML says line 2); groups repeated
   undeclared-identifier errors; `autofix` loops apply-best-and-recompile.

Errors that are not ambiguous (stray characters, unterminated strings, redeclarations) are handled by rules and
labelled as such in the UI - ML is used where it adds information.

## 4. Data (`datasets/`, `backend/ml/`)

* `seeds.py` writes type-correct, terminating programs (loop counters are protected), including *near-name*
  variables of different types - the hard cases that separate a typo from a genuinely new variable.
* `mutators.py` has one mutator per cause. A mutant is kept only if the **real compiler** fails on it for the
  expected reason (first diagnostic checked per cause).
* Layout: one folder per cause under `datasets/labeled/`, each with a `labels.csv`; `manifest.csv` lists everything;
  `processed/` holds feature CSVs, label map and statistics.
* Train/test split is by seed program (20 % of seeds held out) - no program shares an origin across the split.
* `datasets/handwritten/` has 36 programs written by hand in a different style as an out-of-distribution test.

## 5. Service and UI

`backend/app/main.py` exposes `/api/compile`, `/api/diagnose`, `/api/autofix`, `/api/examples`, `/api/model`,
`/api/dataset`, `/api/dataset/samples`, `/api/session`, `/api/health`. The UI (`frontend/`) is React + Vite;
three.js (via react-three-fiber) draws the hero scene and the 3D syntax tree; React Bits provides animated
components; CodeMirror 6 is the editor (red wavy line = compiler-detected error, mint line = ML-localised fault,
yellow line = instruction being executed).

## 6. Limits

Single-fault programs are the target; synthetic training data; no functions/arrays/pointers; the repair for a
missing `}` relies on consistent indentation; exact recovery of the original program is not always possible
because several fixes can be valid.
