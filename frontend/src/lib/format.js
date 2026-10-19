export const pct = (x, d = 1) => (x == null ? '-' : `${(x * 100).toFixed(d)}%`);
export const titleCase = (s) => s.toLowerCase().replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
export const FEATURE_LABELS = {
  err_stage: 'error stage', err_code: 'compiler error code', ctx: 'parser context', expected: 'expected token',
  found: 'token found', prev1: 'previous token', prev2: '2nd previous token', prev3: '3rd previous token',
  prev4: '4th previous token', prev5: '5th previous token', next1: 'next token', ty_kind: 'type-error kind',
  ty_target: 'target type', ty_expr: 'value type', nl_before_found: 'newline before error token',
  found_first_on_line: 'error token starts a line', line_ratio: 'relative line position',
  token_ratio: 'relative token position', paren_bal_before: "'(' balance before error",
  brace_bal_before: "'{' balance before error", paren_bal_total: "'(' balance (whole file)",
  brace_bal_total: "'{' balance (whole file)", prev1_kw_dist: 'edit distance to a keyword',
  prev1_len: 'previous token length', prev1_is_ident: 'previous token is identifier',
  sem_name_len: 'identifier length', sem_min_dist_visible: 'edit distance to nearest in-scope name',
  sem_min_ratio_visible: 'relative distance to nearest name', sem_n_close_visible: 'close names in scope',
  sem_min_dist_all: 'edit distance to any declared name', sem_declared_later: 'declared later in scope',
  sem_closed_scope: 'declared in a closed scope', sem_n_visible: 'names in scope',
  sem_min_dist_keyword: 'edit distance to a keyword', sem_lvalue: 'used as assignment target',
  sem_same_first_char: 'same first letter as nearest', sem_len_diff_nearest: 'length gap to nearest name',
  sem_nearest_compat: 'nearest name is type-compatible', ty_both_numeric: 'both types numeric',
  ty_expr_literal: 'value is a literal',
};
export const featureLabel = (f) => FEATURE_LABELS[f] || f.replace(/_/g, ' ');

export const FAMILY_COLOR = { syntax: '#E7D623', semantic: '#2CF7A4' };
export const STATUS_COLOR = { ok: '#2CF7A4', error: '#FF6B8B', skipped: '#8E78F2' };

export const SHORT = {
  MISSING_SEMICOLON: 'Missing ;', MISSING_RPAREN: 'Missing )', MISSING_LPAREN: 'Missing (',
  MISSING_RBRACE: 'Missing }', MISSING_LBRACE: 'Missing {', MISSPELLED_KEYWORD: 'Keyword typo',
  ASSIGN_EQ_CONFUSION: '= vs ==', TYPO_IDENTIFIER: 'Variable typo', MISSING_DECLARATION: 'No declaration',
  USE_BEFORE_DECLARATION: 'Use before decl', OUT_OF_SCOPE_USE: 'Out of scope', TYPE_MISMATCH: 'Type mismatch',
};
