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

## Reinforcement learning (what to say)
* **Why RL?** Picking a fix is a *sequential* decision under delayed feedback: a fix changes the program, and the next error depends on it.
  The compiler gives a natural reward signal, so no human labels are needed.
* **MDP:** state = broken program (via candidate fixes), action = apply one fix, reward = progress toward the intended program,
  +bonus for compiling / exact recovery, step cost. **Algorithm:** REINFORCE with baseline + entropy bonus; linear softmax policy.
* **Evidence:** learning curve and held-out comparison against the heuristic and a random chooser (Dashboard, RL section).
* **Online RL:** every accepted fix (+1) and every undo (-1) in the Studio updates the running policy - show it live in the Dashboard.
* **Honest limits:** the policy can only choose among the candidates the repair generators propose; the reward during training uses the
  known original program; the policy learns the conventions of the training corpus (e.g. declarations grouped at the top).

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
| *RL ordering, single fault:* top fix reproduces the original | 71.5 % | |

**RL policy vs heuristic, 1,500 held-out programs with 1-3 faults:** exact recovery 39.0 % vs 37.5 % (paired bootstrap +1.5 pts, 95 % CI +0.9 to +2.2);
mean distance to the intended program 8.24 vs 9.59 tokens (CI of the difference -1.51 to -1.21); a random chooser gets 29.2 % / 9.22. Real but modest.

(Re-generate with `python -m ml.train` and `python -m ml.evaluate_repair`; current numbers are on the Dashboard.)

## Five-minute demo script
1. **Home** - show the 3D pipeline; point at the ML node and the validator loop.
2. **Studio → "Missing semicolon"** - the compiler flags line 3 (red); the ML-localised fault is line 2 (mint).
   Open the *Diagnosis* tab: likely cause, confidence, the checked fix with its diff. Click *Apply fix*, then *Undo*.
3. **Studio → "Missing declaration"** (`name = "John";`) - the model says missing declaration, not a typo, because the
   nearest in-scope name `age` is type-incompatible. Show the typo candidate being **rejected** by the compiler.
4. **Studio → "Several errors at once"** → *Fix all* in the Problems box, then *Undo*.
5. **Studio → "Optimizer showcase"** - CFG with live-in/live-out, optimizer diff, "output identical" check, stepping VM.
6. **Dashboard** - the four headline numbers, ML vs rules per error type, the RL results.
7. **datasets/ folder** - one folder per error cause, each program verified by the compiler.

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

**Where exactly is the reinforcement learning?** The fix-selection policy (`backend/repair/rl`, trained by `backend/ml/rl/train_rl.py`): REINFORCE on a repair MDP,
plus online updates from user accept/undo feedback. The classifier is supervised; the policy is RL.

**Why is the RL gain modest on single faults?** On one fault the heuristic is already near the ceiling of what the candidates can reach. The gain
appears where choices interact: declaration placement and programs with several faults.

**Limitations?** Single-fault target, synthetic training data, small language, brace repair depends on indentation.
