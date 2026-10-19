# Review notes

## One-line pitch
A compiler for a C-like language that, when compilation fails, uses compiler-generated features plus an ML
classifier to identify the *cause* of the error and propose a repair - and re-compiles every proposed fix so
nothing unverified is ever shown.

## Problem statement
Compilers report where they got stuck, not what the programmer meant. `error: expected ';'` and
`undeclared identifier 'nam'` are symptoms; each can have several causes needing different fixes. Beginners
lose time translating symptoms into fixes.

## Objectives
1. Implement a complete compiler pipeline for a restricted C-like language (lexer → parser → semantic analysis →
   IR → optimization → execution).
2. Capture, at the point of failure, the facts only the compiler knows (parse context, expected tokens,
   symbol-table state) as ML features.
3. Classify the cause among 12 error types and rank candidate repairs.
4. Validate every candidate by re-running the compiler front end.
5. Evaluate honestly against a rule baseline.

## Related work
* **DeepFix** (Gupta, Pal, Kanade, Shevade - AAAI 2017): a sequence-to-sequence neural network that repairs
  common C compilation errors end-to-end from raw token sequences. It iterates with the compiler, but the model
  is a black box and needs a large corpus.
* **Classical error recovery** (Aho, Lam, Sethi, Ullman, *Compilers: Principles, Techniques, and Tools*, ch. 4):
  panic-mode, phrase-level recovery and error productions - they let the parser *continue*, not explain *why*.
* **Difference here:** lightweight classical ML on **compiler-derived features** (explainable, trains in
  seconds), and a **compiler-validated** repair loop.

## Architecture (one slide)
Compiler pipeline on top; on failure a branch: feature extractor → ML classifier → repair generator → validator,
with rejected candidates returning to the generator. See `docs/ARCHITECTURE.md` or the Architecture page.

## Syllabus mapping
Regular expressions/DFA (lexer) · CFG and recursive-descent parsing · parse tree/AST · syntax-error handling ·
symbol table and scopes · type checking · syntax-directed translation · three-address code · basic blocks and CFG ·
live-variable data-flow analysis · optimization (folding, propagation, DCE, branch folding) · code generation target
(VM) · plus ML-assisted diagnostics.

## Results to quote
| | ML | Rule baseline |
|---|---|---|
| Cause accuracy, 650 held-out programs | 98.6 % | 87.5 % |
| Hand-written programs (n = 36) | 100 % | 88.9 % |
| Top-ranked fix recompiles cleanly | 96.2 % | 87.1 % |
| Auto-fix ends in a clean program | 98.8 % | 89.7 % |
| Top fix reproduces the original program | 70.2 % | 65.9 % |

(Re-generate with `python -m ml.train` and `python -m ml.evaluate_repair`; current numbers are on the Dashboard.)

## Five-minute demo script
1. **Home** - show the 3D pipeline; point at the ML node and the validator loop.
2. **Studio → "Missing semicolon"** - the compiler flags line 3 (red); the ML-localised fault is line 2 (mint).
   Open *AI Diagnosis*: ranked causes, evidence, the rule baseline agreeing, *verified* fix. Click *Quick fix*.
3. **Studio → "Missing declaration"** (`name = "John";`) - the model says missing declaration, not typo, because the
   nearest in-scope name `age` is type-incompatible. Show the typo candidate being **rejected** by the compiler.
4. **Studio → "Several errors at once"** → *Auto-fix all*, then *Undo*.
5. **Studio → "Optimizer showcase"** - CFG with live-in/live-out, optimizer diff, "output identical" check, stepping VM.
6. **Dashboard** - ML vs rules per cause, confusion matrix, end-to-end repair outcomes.
7. **Dataset** - one folder per cause; sample next to its ground truth.

## Questions you will be asked
**Why not just rules?** The rules exist as the baseline and reach 87.5 %. They fail where evidence must be combined:
typo vs missing declaration on short names, `)` vs `=`, `}` vs `else`, fused `printx)`. ML closes that gap, and
the Dashboard shows it per cause.

**What if the ML is wrong?** It cannot do damage: candidates are only shown if the compiler accepts them, and
wrong causes are often rescued because their candidates are rejected.

**Is the data real?** It is synthetic - valid programs corrupted by mutators, each verified by the compiler. That is
stated openly; the hand-written set and the grouped split are the safeguards. Real student data would be future work.

**How do you know the optimizer is correct?** Unoptimized and optimized code are both executed and compared on every
compile, and on 150 randomly generated programs in the test suite. A copy-propagation bug found early (stale copies
after redefinition) is covered by a regression test.

**Why gradient boosting / why these features?** All four models score within 0.5 points, so the choice is made on
log-loss (confidence quality). Features are compiler facts, so predictions are explainable.

**What is the time complexity?** Lexing and parsing are linear; semantic analysis is linear plus edit-distance over
visible names; liveness converges in a few passes over the CFG; each repair candidate costs one front-end run.

**Limitations?** Single-fault target, synthetic training data, small language, brace repair depends on indentation.
