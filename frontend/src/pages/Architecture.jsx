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
  ['Reinforcement learning (REINFORCE policy)', 'repair/rl/ + ml/rl/', 'Dashboard (RL section) · fix order toggle'],
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
    <svg viewBox="0 0 1000 530" className="arch-svg" role="img" aria-label="Architecture diagram">
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
      <text x="10" y="196" className="lane err">ON FAILURE (ML classifier + RL policy are components inside this loop)</text>
      {arrow('M390,104 C390,165 125,150 125,220', 'err')}{arrow('M555,104 C555,175 175,168 175,220', 'err')}
      <text x="250" y="150" className="lbl err">error + compiler facts</text>
      {box(30, 222, 170, 76, 'Feature extractor', 'parse state · tokens · symbols', 'err')}
      {box(235, 222, 170, 76, 'ML classifier', '12 causes + confidence', 'ml')}
      {box(440, 222, 190, 76, 'Repair generator', 'candidate edits per cause', 'mint')}
      {box(665, 222, 190, 76, 'RL policy', 'REINFORCE · picks the fix', 'rl')}
      {arrow('M200,260 L233,260', 'err')}{arrow('M405,260 L438,260', 'err')}{arrow('M630,260 L663,260', 'err')}
      {box(665, 380, 190, 76, 'Compiler validator', 're-run lexer·parser·semantic', 'yellow')}
      {arrow('M760,298 L760,378', 'err')}
      {arrow('M855,418 C955,418 955,262 857,262', 'loop')}
      <text x="868" y="338" className="lbl loop">rejected →</text>
      <text x="868" y="353" className="lbl loop">next candidate</text>
      {box(440, 380, 170, 76, 'Verified fix', 'shown to the user', 'ok')}
      {arrow('M663,418 L612,418', 'err')}
      {box(205, 380, 190, 76, 'Auto-fix loop', 'apply best, re-compile', 'src')}
      {arrow('M438,418 L397,418', 'err')}
      {arrow('M205,418 C-12,430 -12,150 195,106', 'loop')}
      <text x="8" y="352" className="lbl loop">re-enter</text>
      <text x="8" y="367" className="lbl loop">at the Lexer</text>
      {arrow('M760,456 C760,500 960,500 960,470', 'loop')}
      <text x="780" y="506" className="lbl loop">user accept (+1) / undo (−1) → online policy update</text>
    </svg>
  );
}

export default function Architecture() {
  return (
    <div>
      <div className="container page-head">
        <span className="eyebrow">Architecture · design decisions · honesty notes</span>
        <h1 style={{ marginTop: 16 }}>How it is <span className="hl">built</span></h1>
        <p>Compiler techniques are the backbone. ML ranks the cause, reinforcement learning picks the fix - and the compiler has the last word.</p>
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
              ['Reinforcement learning picks the fix', 'When several fixes are possible, which to apply first is a sequential decision. A REINFORCE policy over candidate-fix features is trained on programs with 1-3 faults: the compiler supplies the reward (does it compile? is it closer to the intended program?) and the policy is compared with the heuristic order and a random chooser on held-out programs. It keeps learning online from the fixes users accept (+1) or undo (-1).'],
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
  repair/rl/  candidate features · softmax policy
  ml/rl/      repair MDP · multi-fault generator
              REINFORCE training + evaluation
  ml/         seeds · mutators · build_dataset
              train · evaluate_repair
  app/        FastAPI (examples, compile, autofix…)
  tests/      212 tests
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
