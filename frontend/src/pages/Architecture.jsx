import React from 'react';
import SpotlightCard from '../reactbits/SpotlightCard.jsx';
import FadeContent from '../reactbits/FadeContent.jsx';
import './architecture.css';

const GRAMMAR = `program  → stmt* EOF
stmt     → decl | assign | print | if | while | block
decl     → TYPE IDENT ( '=' expr )? ';'
assign   → IDENT '=' expr ';'
print    → 'print' '(' expr ')' ';'
if       → 'if' '(' expr ')' block ( 'else' ( if | block ) )?
while    → 'while' '(' expr ')' block
block    → '{' stmt* '}'
expr     → or        or  → and ('||' and)*     and → eq ('&&' eq)*
eq       → rel (('=='|'!=') rel)*              rel → add (('<'|'>'|'<='|'>=') add)*
add      → mul (('+'|'-') mul)*                mul → unary (('*'|'/'|'%') unary)*
unary    → ('-'|'!') unary | primary
primary  → INT | FLOAT | STRING | BOOL | IDENT | '(' expr ')'`;

const SYLLABUS = [
  ['Regular expressions, DFA / NFA', 'minic/lexer.py', 'Tokens tab (DFA animation)'],
  ['Lexical analysis, lexical errors', 'minic/lexer.py', 'Tokens tab · rule-based fixes'],
  ['Context-free grammar', 'minic/parser.py (docstring grammar)', 'Architecture page'],
  ['Top-down / recursive-descent parsing', 'minic/parser.py', 'Pipeline strip · Diagnosis'],
  ['Parse tree / AST', 'minic/ast.py', 'Syntax Tree tab (2D + 3D)'],
  ['Syntax error recovery & reporting', 'Parser.fail(): expected set + context', 'AI Diagnosis'],
  ['Symbol table, scopes', 'minic/semantic.py', 'Symbols tab'],
  ['Type checking', 'semantic.py: binary_type / assignable', 'Problems list'],
  ['Syntax-directed translation', 'minic/tac.py (post-order walk)', '3-Address Code tab'],
  ['Three-address code, short-circuit jumps', 'minic/tac.py', '3-Address Code tab'],
  ['Basic blocks, control-flow graph', 'minic/cfg.py', 'CFG tab'],
  ['Data-flow analysis (live variables)', 'cfg.liveness()', 'CFG tab (live-in / live-out)'],
  ['Code optimization', 'minic/optimizer.py', 'Optimizer tab (before / after diff)'],
  ['Code generation / target machine', 'minic/vm.py', 'Execute tab (stepper)'],
  ['Machine learning for diagnostics', 'repair/ + ml/', 'Dashboard · AI Diagnosis'],
];

const FEATURES = [
  ['Parser state', 'err_code, ctx (production being parsed), expected token set, token found'],
  ['Token context', 'previous 5 tokens, next token, newline before error, error token starts a line'],
  ['Balance', "'(' and '{' balance before the error and over the whole file"],
  ['Keyword proximity', 'edit distance from the previous identifier to every keyword / type'],
  ['Symbol table', 'nearest in-scope names (edit distance, ratio), names in scope, nearest name type-compatible with the use'],
  ['Scope facts', 'declared later in the same scope? declared in a closed scope? used as assignment target?'],
  ['Type facts', 'error kind (init / assign / operand / condition), target type, value type, both numeric, literal'],
];

const SYMPTOMS = [
  ['undeclared identifier \'nam\'', 'Misspelled variable', 'Missing declaration', 'Used before declaration', 'Used outside its scope'],
  ['expected \')\' but found \'=\'', 'Missing closing paren', '= instead of ==', '', ''],
  ['expected \'{\' but found \')\'', 'Missing opening brace', 'Missing opening paren', '', ''],
  ['expected \'=\' but found \'(\'', 'Misspelled keyword', 'Missing opening paren (print(x) fused)', '', ''],
];

function Diagram() {
  const box = (x, y, w, h, t, s, cls = '') => (
    <g className={`ab ${cls}`} transform={`translate(${x},${y})`}>
      <rect width={w} height={h} rx="16" />
      <text x={w / 2} y={h / 2 - (s ? 3 : -4)} textAnchor="middle" className="ab-t">{t}</text>
      {s && <text x={w / 2} y={h / 2 + 14} textAnchor="middle" className="ab-s">{s}</text>}
    </g>
  );
  const arrow = (d, cls = '') => <path d={d} className={`aa ${cls}`} markerEnd="url(#arr)" />;
  return (
    <svg viewBox="0 0 1000 520" className="arch-svg" role="img" aria-label="Architecture diagram">
      <defs>
        <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#ffffff" /></marker>
      </defs>
      <text x="10" y="22" className="lane">COMPILER (the backbone)</text>
      {box(10, 40, 120, 64, 'Source', 'MiniC text', 'src')}
      {box(170, 40, 120, 64, 'Lexer', 'tokens')}
      {box(330, 40, 120, 64, 'Parser', 'AST + context')}
      {box(490, 40, 130, 64, 'Semantic', 'symbols, types', 'mint')}
      {box(660, 40, 120, 64, 'IR gen', '3-address')}
      {box(820, 40, 170, 64, 'Optimizer → VM', 'folding · liveness', 'yellow')}
      {arrow('M130,72 L168,72')}{arrow('M290,72 L328,72')}{arrow('M450,72 L488,72')}{arrow('M620,72 L658,72')}{arrow('M780,72 L818,72')}
      <text x="10" y="196" className="lane err">ON FAILURE (ML is one component inside this loop)</text>
      {arrow('M390,104 C390,150 250,170 250,222', 'err')}{arrow('M555,104 C555,150 330,170 330,222', 'err')}
      <text x="296" y="160" className="lbl err">error + compiler facts</text>
      {box(170, 222, 220, 76, 'Feature extractor', 'parse state · tokens · symbols', 'err')}
      {box(430, 222, 200, 76, 'ML classifier', '12 causes + confidence', 'ml')}
      {box(670, 222, 200, 76, 'Repair generator', 'candidate edits per cause', 'mint')}
      {arrow('M390,260 L428,260', 'err')}{arrow('M630,260 L668,260', 'err')}
      {box(670, 380, 200, 76, 'Compiler validator', 're-run lexer·parser·semantic', 'yellow')}
      {arrow('M770,298 L770,378', 'err')}
      {arrow('M870,418 C960,418 960,262 872,262', 'loop')}
      <text x="880" y="345" className="lbl loop">rejected →</text>
      <text x="880" y="360" className="lbl loop">next candidate</text>
      {box(430, 380, 150, 76, 'Verified fix', 'shown to the user', 'ok')}
      {arrow('M668,430 L582,430', 'err')}
      {box(170, 380, 200, 76, 'Auto-fix loop', 'apply best, re-compile', 'src')}
      {arrow('M428,418 L372,418', 'err')}
      {arrow('M270,380 C150,300 30,200 70,106', 'loop')}
      <text x="40" y="320" className="lbl loop">re-enter at the Lexer</text>
    </svg>
  );
}

export default function Architecture() {
  return (
    <div>
      <div className="container page-head">
        <span className="eyebrow">Architecture · design decisions · honesty notes</span>
        <h1 style={{ marginTop: 16 }}>How it is <span className="hl">built</span></h1>
        <p>Compiler techniques are the backbone. ML is one intelligent component inside the system - and the compiler has the last word.</p>
      </div>

      <div className="container">
        <div className="panel arch-panel"><Diagram /></div>
      </div>

      <div className="section-light arch-body">
        <div className="container">
          <h2 className="a-h">Why ML at all? Because a symptom has several causes.</h2>
          <p className="a-sub">The compiler reliably reports <em>what</em> failed. It cannot tell what the programmer <em>meant</em>. The same message is produced by different mistakes that need different fixes:</p>
          <div className="sym-table">
            {SYMPTOMS.map(([sym, ...causes]) => (
              <div className="sym-row" key={sym}>
                <code className="sym">{sym}</code>
                <div className="sym-causes">{causes.filter(Boolean).map((c) => <span key={c} className="chip">{c}</span>)}</div>
              </div>
            ))}
          </div>

          <div className="dec-grid">
            {[
              ['The compiler validates the ML', 'Every candidate repair is applied to the source and re-run through lexer → parser → semantic analysis. A fix is shown as "verified" only if the compiler accepts it. Wrong predictions are rescued: a mis-ranked typo fix is rejected because it creates a type error, and the correct declaration fix still surfaces.'],
              ['Explainable by construction', 'The classifier never sees raw text. It sees 40 features the compiler computed - parse context, expected tokens, scope facts, edit distances. A feature-occlusion explanation shows which of them drove each prediction.'],
              ['A fair baseline', 'A hand-written rule classifier reads the same facts. The dashboard reports both, on the held-out set, on a hand-written set, and end-to-end - so the value added by ML is measured, not asserted.'],
              ['Honest limits', 'Training data is synthetic (mutated programs). Single-fault programs are the target; programs with several interacting faults are repaired one fault at a time. The language is a restricted C subset: no functions, arrays or pointers.'],
            ].map(([t, d], i) => (
              <FadeContent key={t} blur duration={500} delay={i * 80}>
                <SpotlightCard theme="light" className="dec" intensity={0.2}><h3>{t}</h3><p>{d}</p></SpotlightCard>
              </FadeContent>
            ))}
          </div>

          <h2 className="a-h">Feature vector</h2>
          <p className="a-sub">40 features, all produced by compiler phases (14 categorical, 26 numeric).</p>
          <div className="feat-grid">
            {FEATURES.map(([g, d]) => <div className="feat" key={g}><b>{g}</b><span>{d}</span></div>)}
          </div>

          <h2 className="a-h">Compiler-design syllabus coverage</h2>
          <div className="card syl">
            <table>
              <thead><tr><th>Topic</th><th>Where in the code</th><th>Where to see it</th></tr></thead>
              <tbody>{SYLLABUS.map(([a, b, c]) => <tr key={a}><td className="topic">{a}</td><td><code>{b}</code></td><td>{c}</td></tr>)}</tbody>
            </table>
          </div>

          <div className="two-col">
            <div>
              <h2 className="a-h">MiniC grammar</h2>
              <pre className="codeblock gram">{GRAMMAR}</pre>
              <p className="a-sub small">Types: <code>int float bool string</code> · <code>int → float</code> widening only · conditions must be <code>bool</code> · <code>+</code> concatenates strings.</p>
            </div>
            <div>
              <h2 className="a-h">Project layout</h2>
              <pre className="codeblock gram">{`backend/
  minic/      lexer · parser · ast · semantic · tac
              optimizer · cfg · vm · pipeline
  repair/     features · classifier · candidates
              validator · engine · baseline · labels
  ml/         seeds · mutators · build_dataset
              train · evaluate_repair
  app/        FastAPI (examples, compile, autofix…)
  tests/      191 tests
datasets/     seeds · labeled/<CAUSE>/ · handwritten
models/       error_classifier.joblib · metrics.json
frontend/     React + Vite + React Bits + three.js
docs/         architecture · review notes`}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
