# Datasets

All data used to train and evaluate the error-cause classifier. Everything here is **generated and verified by
the project's own compiler** except `handwritten/`, which was written by hand. Rebuild with
`python -m ml.build_dataset` from `backend/`.

```
datasets/
├─ seeds/valid/                 700 valid MiniC programs (seed_0001.mc …)
├─ labeled/                     ONE FOLDER PER CAUSE - the folder name is the class label
│  ├─ MISSING_SEMICOLON/        260 programs + labels.csv
│  ├─ MISSING_RPAREN/
│  ├─ MISSING_LPAREN/
│  ├─ MISSING_RBRACE/
│  ├─ MISSING_LBRACE/
│  ├─ MISSPELLED_KEYWORD/
│  ├─ ASSIGN_EQ_CONFUSION/
│  ├─ TYPO_IDENTIFIER/
│  ├─ MISSING_DECLARATION/
│  ├─ USE_BEFORE_DECLARATION/
│  ├─ OUT_OF_SCOPE_USE/
│  └─ TYPE_MISMATCH/
├─ handwritten/<CAUSE>/         36 hand-written programs (3 per cause) - out-of-distribution test set
├─ manifest.csv                 every labelled sample, one row each
└─ processed/
   ├─ features.csv              compiler-extracted feature vectors + label + split
   ├─ handwritten_features.csv  same for the hand-written set
   ├─ label_map.json            class id, title, family, explanation
   └─ dataset_stats.json        counts per class and split
```

## How a labelled sample is made

1. `ml/seeds.py` generates a type-correct, terminating program (a *seed*).
2. The mutator for one cause (`ml/mutators.py`) corrupts a copy in exactly one way - e.g. deletes a `;`, renames a
   use of a variable with a typo, moves a declaration into an inner block.
3. The **real compiler** runs on the mutant. It is kept only if the first diagnostic is the one the cause should
   produce (e.g. for `USE_BEFORE_DECLARATION`: an undeclared identifier that is declared *later* in the same scope).
4. The compiler's facts at the failure point are extracted as the feature vector (`repair/features.py`).

## Files

`labeled/<CAUSE>/<CAUSE>_NNNN.mc` - the corrupted program.
`labeled/<CAUSE>/labels.csv` and `manifest.csv` columns:

| column | meaning |
|---|---|
| `sample_id` | e.g. `TYPO_IDENTIFIER_0042` |
| `file` | path relative to `datasets/` |
| `label` | the true cause (= folder name) |
| `seed_id` | the valid program it came from (`seeds/valid/<seed_id>.mc` is the ground-truth fix) |
| `split` | `train` or `test` - **assigned per seed**, so a test program never shares an origin with a training program |
| `error_line`, `compiler_code`, `compiler_message` | what the compiler reported |
| `mutation` | what was done to the seed |
| `error_line_text` | the source line the compiler flagged |

## Classes

| Label | Family | Meaning |
|---|---|---|
| `MISSING_SEMICOLON` | syntax | statement not terminated with `;` |
| `MISSING_RPAREN` | syntax | `(` never closed |
| `MISSING_LPAREN` | syntax | `)` without its `(` |
| `MISSING_RBRACE` | syntax | block opened but never closed |
| `MISSING_LBRACE` | syntax | `if/while/else` header without a `{ }` block |
| `MISSPELLED_KEYWORD` | syntax | `whlie`, `pritn`, `itn` … |
| `ASSIGN_EQ_CONFUSION` | syntax | `=` where `==` was meant, or the reverse |
| `TYPO_IDENTIFIER` | semantic | undeclared name a few edits from an in-scope variable |
| `MISSING_DECLARATION` | semantic | variable used but never declared |
| `USE_BEFORE_DECLARATION` | semantic | declared later in the same scope |
| `OUT_OF_SCOPE_USE` | semantic | declared in a block that has already closed |
| `TYPE_MISMATCH` | semantic | value type incompatible with variable, operator or condition |

## Caveat

The labelled programs are synthetic. The hand-written set exists so that accuracy is also reported on programs
that were not produced by the generator; real student programs would be the natural next dataset.
