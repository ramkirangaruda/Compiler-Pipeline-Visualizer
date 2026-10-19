import React, { useEffect, useMemo, useRef, useState } from 'react';

/* ------------------------------------------------------------- DFA drawings */
const DFAS = {
  ident: {
    title: 'Identifier / keyword DFA', regex: '[A-Za-z_][A-Za-z0-9_]*',
    states: [{ id: 's0', x: 50, y: 62 }, { id: 's1', x: 190, y: 62, accept: true }],
    edges: [{ a: 's0', b: 's1', label: 'letter | _' }, { a: 's1', b: 's1', label: 'letter | digit | _', loop: true }],
  },
  number: {
    title: 'Number literal DFA', regex: '[0-9]+ ( . [0-9]+ )?',
    states: [{ id: 's0', x: 36, y: 62 }, { id: 's1', x: 118, y: 62, accept: true }, { id: 's2', x: 200, y: 62 }, { id: 's3', x: 282, y: 62, accept: true }],
    edges: [
      { a: 's0', b: 's1', label: 'digit' }, { a: 's1', b: 's1', label: 'digit', loop: true },
      { a: 's1', b: 's2', label: '.' }, { a: 's2', b: 's3', label: 'digit' }, { a: 's3', b: 's3', label: 'digit', loop: true },
    ],
  },
  string: {
    title: 'String literal DFA', regex: '" ( [^"\\n] | \\\\. )* "',
    states: [{ id: 's0', x: 40, y: 62 }, { id: 's1', x: 150, y: 62 }, { id: 's2', x: 260, y: 62, accept: true }],
    edges: [{ a: 's0', b: 's1', label: '"' }, { a: 's1', b: 's1', label: 'not " or newline', loop: true }, { a: 's1', b: 's2', label: '"' }],
  },
};
const R = 17;

function Dfa({ spec, active }) {
  const S = Object.fromEntries(spec.states.map((s) => [s.id, s]));
  return (
    <div className="dfa">
      <div className="dfa-title">{spec.title}</div>
      <code className="dfa-re">{spec.regex}</code>
      <svg viewBox="0 0 320 120" role="img" aria-label={spec.title}>
        <defs><marker id={`dfa-${spec.title}`} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#c9bcff" /></marker></defs>
        <path d={`M${S.s0.x - 34},${S.s0.y} L${S.s0.x - R - 2},${S.s0.y}`} className="dfa-edge" markerEnd={`url(#dfa-${spec.title})`} />
        {spec.edges.map((e, i) => {
          const A = S[e.a], B = S[e.b];
          if (e.loop) {
            return (
              <g key={i}>
                <path d={`M${A.x - 9},${A.y - R + 1} C${A.x - 26},${A.y - 48} ${A.x + 26},${A.y - 48} ${A.x + 9},${A.y - R + 1}`} className="dfa-edge" markerEnd={`url(#dfa-${spec.title})`} />
                <text x={A.x} y={A.y - 44} textAnchor="middle" className="dfa-lbl">{e.label}</text>
              </g>
            );
          }
          return (
            <g key={i}>
              <path d={`M${A.x + R + 1},${A.y} L${B.x - R - 3},${B.y}`} className="dfa-edge" markerEnd={`url(#dfa-${spec.title})`} />
              <text x={(A.x + B.x) / 2} y={A.y - 8} textAnchor="middle" className="dfa-lbl">{e.label}</text>
            </g>
          );
        })}
        {spec.states.map((s) => (
          <g key={s.id}>
            <circle cx={s.x} cy={s.y} r={R} className={`dfa-state ${active === s.id ? 'active' : ''}`} />
            {s.accept && <circle cx={s.x} cy={s.y} r={R + 4} className="dfa-accept" />}
            <text x={s.x} y={s.y + 4} textAnchor="middle" className="dfa-sid">{s.id.toUpperCase()}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function dfaFor(tok) {
  if (!tok) return {};
  if (['IDENT', 'KEYWORD', 'TYPE', 'BOOL'].includes(tok.kind)) return { ident: 's1' };
  if (tok.kind === 'INT') return { number: 's1' };
  if (tok.kind === 'FLOAT') return { number: 's3' };
  if (tok.kind === 'STRING') return { string: 's2' };
  return {};
}

/* ------------------------------------------------------------------ tokens */
export function TokensView({ tokens, source }) {
  const toks = useMemo(() => tokens.filter((t) => t.kind !== 'EOF'), [tokens]);
  const [n, setN] = useState(toks.length);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(6);
  useEffect(() => { setN(toks.length); setPlaying(false); }, [toks]);
  useEffect(() => {
    if (!playing) return undefined;
    const t = setInterval(() => setN((x) => { if (x >= toks.length) { setPlaying(false); return x; } return x + 1; }), (11 - speed) * 70);
    return () => clearInterval(t);
  }, [playing, speed, toks.length]);

  const segments = useMemo(() => {
    const out = [];
    let at = 0;
    toks.forEach((t, i) => {
      if (t.start > at) out.push({ text: source.slice(at, t.start), gap: true });
      out.push({ text: source.slice(t.start, t.end), kind: t.kind, i });
      at = t.end;
    });
    if (at < source.length) out.push({ text: source.slice(at), gap: true });
    return out;
  }, [toks, source]);

  const cur = n > 0 ? toks[n - 1] : null;
  const act = dfaFor(cur);
  const replay = () => { setN(0); setPlaying(true); };
  return (
    <div>
      <div className="vm-controls">
        <button className="btn btn-sm" onClick={replay}>▶ Replay scan</button>
        <button className="btn-flat" onClick={() => setPlaying(!playing)} disabled={n >= toks.length && !playing}>{playing ? '⏸ Pause' : '▶ Resume'}</button>
        <button className="btn-flat" onClick={() => { setPlaying(false); setN(Math.min(toks.length, n + 1)); }}>Step</button>
        <button className="btn-flat" onClick={() => { setPlaying(false); setN(toks.length); }}>All</button>
        <label className="speed">Speed <input type="range" min="1" max="10" value={speed} onChange={(e) => setSpeed(+e.target.value)} /></label>
        <span className="muted mono">{n}/{toks.length} tokens</span>
      </div>
      <pre className="scan">
        {segments.map((s, k) => (s.gap ? <span key={k} className="gap">{s.text}</span>
          : <span key={k} className={`tk ${s.i < n ? `on k-${s.kind}` : ''} ${s.i === n - 1 ? 'cur' : ''}`}>{s.text}</span>))}
      </pre>
      <div className="dfa-row">
        <Dfa spec={DFAS.ident} active={act.ident} />
        <Dfa spec={DFAS.number} active={act.number} />
        <Dfa spec={DFAS.string} active={act.string} />
      </div>
      <div className="tbl-wrap">
        <table>
          <thead><tr><th>#</th><th>Kind</th><th>Lexeme</th><th>Line:Col</th></tr></thead>
          <tbody>
            {toks.slice(0, n).map((t, i) => (
              <tr key={i} className={i === n - 1 ? 'cur' : ''}><td>{i + 1}</td><td><span className={`kind k-${t.kind}`}>{t.kind}</span></td><td>{t.value}</td><td>{t.line}:{t.col}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- symbols */
export function SymbolsView({ symbols }) {
  if (!symbols) return <div className="empty">No symbol table - the parser did not produce a syntax tree.</div>;
  const depth = (s) => { let d = 0, p = s.parent; while (p != null) { d++; p = symbols[p].parent; } return d; };
  return (
    <div className="scopes">
      <p className="hint">Each block opens a new scope. A name resolves to the innermost enclosing declaration; shadowed variables get unique internal names (<code>x#2</code>).</p>
      {symbols.map((s) => (
        <div key={s.id} className="scope" style={{ marginLeft: depth(s) * 22 }}>
          <div className="scope-head"><b>scope {s.id}</b><span className="badge neutral">{s.kind}</span><span className="muted mono">{s.parent == null ? 'root' : `parent ${s.parent}`}</span></div>
          {s.symbols.length === 0 ? <div className="muted mono small">no declarations</div> : (
            <table><thead><tr><th>name</th><th>type</th><th>declared</th><th>read?</th><th>internal</th></tr></thead>
              <tbody>{s.symbols.map((y) => (
                <tr key={y.uid}><td>{y.name}</td><td><span className="kind k-TYPE">{y.type}</span></td><td>line {y.line}</td>
                  <td>{y.used ? <span className="badge ok">used</span> : <span className="badge partial">unused</span>}</td><td>{y.uid}</td></tr>
              ))}</tbody></table>
          )}
        </div>
      ))}
    </div>
  );
}

/* --------------------------------------------------------------------- TAC */
function Ins({ ins, idx, cls = '' }) {
  const label = ins.op === 'label';
  return (
    <div className={`ins ${label ? 'label' : ''} ${cls}`}>
      <span className="ix">{label ? '' : idx}</span>
      <code>{ins.text}</code>
      {ins.line > 0 && !label && <span className="src">L{ins.line}</span>}
    </div>
  );
}

export function TacView({ tac }) {
  if (!tac?.length) return <div className="empty">Three-address code is generated only for programs that compile.</div>;
  return (
    <div>
      <p className="hint">Generated by a post-order (syntax-directed) walk of the typed AST. <code>t1, t2…</code> are temporaries, <code>L1, L2…</code> are jump targets, <code>&amp;&amp;</code> and <code>||</code> become short-circuit jumps, and int→float widening is an explicit <code>(float)</code> conversion.</p>
      <div className="ins-list">{tac.map((i, k) => <Ins key={k} ins={i} idx={k} />)}</div>
    </div>
  );
}

/* --------------------------------------------------------------- optimizer */
function diffRows(a, b, ops) {
  const rows = [];
  for (const o of ops) {
    const [i1, i2] = o.a, [j1, j2] = o.b;
    const len = Math.max(i2 - i1, j2 - j1);
    for (let k = 0; k < len; k++) {
      rows.push({ tag: o.tag, l: i1 + k < i2 ? a[i1 + k] : null, li: i1 + k, r: j1 + k < j2 ? b[j1 + k] : null, ri: j1 + k });
    }
  }
  return rows;
}

export function OptimizerView({ tac, optimized, verify }) {
  if (!optimized) return <div className="empty">The optimizer runs only on programs that compile.</div>;
  const rows = diffRows(tac, optimized.code, optimized.diff);
  const active = optimized.report.filter((r) => r.count > 0);
  return (
    <div>
      <div className="tiles">
        {active.length === 0 && <div className="tile"><b>0</b><span>nothing to optimize</span></div>}
        {active.map((r) => <div className="tile" key={r.name}><b>{r.count}</b><span>{r.name}</span></div>)}
        <div className="tile hot"><b>{tac.length} → {optimized.code.length}</b><span>static instructions</span></div>
        {verify && <div className="tile hot"><b>{verify.unoptimized_steps} → {verify.optimized_steps}</b><span>executed instructions</span></div>}
        {verify && <div className={`tile ${verify.match ? 'good' : 'bad'}`}><b>{verify.match ? '✓ identical' : '✗ differs'}</b><span>program output before vs after</span></div>}
      </div>
      <p className="hint">{optimized.rounds} optimization round{optimized.rounds === 1 ? '' : 's'} until a fixed point. Both versions are executed and their outputs compared, so semantic preservation is checked on every compile.</p>
      <div className="diff2">
        <div className="d2-head">Unoptimized</div><div className="d2-head">Optimized</div>
        {rows.map((r, k) => (
          <React.Fragment key={k}>
            <div className={`d2 l ${r.tag} ${r.l ? '' : 'blank'}`}>{r.l && <><span className="ix">{r.l.op === 'label' ? '' : r.li}</span><code>{r.l.text}</code></>}</div>
            <div className={`d2 r ${r.tag} ${r.r ? '' : 'blank'}`}>{r.r && <><span className="ix">{r.r.op === 'label' ? '' : r.ri}</span><code>{r.r.text}</code></>}</div>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

/* --------------------------------------------------------------- execution */
const isTemp = (n) => /^t\d+$/.test(n);

export function ExecView({ execution, code, onLine }) {
  const trace = execution?.trace || [];
  const [pos, setPos] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(7);
  const listRef = useRef(null);
  useEffect(() => { setPos(0); setPlaying(false); }, [execution]);
  useEffect(() => {
    if (!playing) return undefined;
    const t = setInterval(() => setPos((p) => { if (p >= trace.length) { setPlaying(false); return p; } return p + 1; }), (11 - speed) * 60);
    return () => clearInterval(t);
  }, [playing, speed, trace.length]);

  const state = useMemo(() => {
    const vars = {}, out = [];
    let changed = null;
    for (let i = 0; i < pos; i++) {
      const s = trace[i];
      if (s.set) { vars[s.set[0]] = s.set[1]; changed = s.set[0]; }
      if (s.out != null) out.push(s.out);
      else if (i === pos - 1) changed = changed && s.set ? changed : null;
    }
    return { vars, out, changed };
  }, [trace, pos]);

  const curPc = pos > 0 ? trace[pos - 1].pc : -1;
  useEffect(() => {
    onLine?.(pos > 0 ? trace[pos - 1].line : 0);
    const el = listRef.current?.querySelector('.ins.cur');
    el?.scrollIntoView({ block: 'nearest' });
    return () => {};
  }, [pos]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => onLine?.(0), []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!execution) return <div className="empty">Only programs that compile can be executed.</div>;
  const done = pos >= trace.length;
  const names = Object.keys(state.vars).filter((k) => !isTemp(k));
  return (
    <div className="vm">
      <div>
        <div className="vm-controls">
          <button className="btn btn-sm" onClick={() => { if (done) setPos(0); setPlaying(!playing); }}>{playing ? '⏸ Pause' : done ? '↻ Run again' : '▶ Run'}</button>
          <button className="btn-flat" onClick={() => { setPlaying(false); setPos(Math.min(trace.length, pos + 1)); }}>Step</button>
          <button className="btn-flat" onClick={() => { setPlaying(false); setPos(0); }}>Reset</button>
          <button className="btn-flat" onClick={() => { setPlaying(false); setPos(trace.length); }}>End</button>
          <label className="speed">Speed <input type="range" min="1" max="10" value={speed} onChange={(e) => setSpeed(+e.target.value)} /></label>
        </div>
        <div className="vm-sub">Executing the <b>optimized</b> code · step {pos}/{trace.length}{execution.trace_truncated ? '+' : ''}</div>
        <div className="ins-list vm-code" ref={listRef}>
          {code.map((i, k) => <Ins key={k} ins={i} idx={k} cls={k === curPc ? 'cur' : ''} />)}
        </div>
      </div>
      <div>
        <div className="vm-sub">Variables</div>
        <table className="vars">
          <thead><tr><th>name</th><th>value</th></tr></thead>
          <tbody>
            {names.length === 0 && <tr><td colSpan="2" className="muted">no variables yet</td></tr>}
            {names.map((n) => <tr key={n} className={n === state.changed ? 'flash' : ''}><td>{n}</td><td>{state.vars[n]}</td></tr>)}
          </tbody>
        </table>
        <div className="vm-sub">Console</div>
        <div className="console">
          {state.out.length === 0 ? <span className="muted">(no output yet)</span> : state.out.map((o, i) => <div key={i}>&gt; {o}</div>)}
          {done && execution.halted === 'error' && <div className="rt-err">{execution.error}</div>}
          {done && execution.halted === 'step_limit' && <div className="rt-err">Stopped after the step limit (possible infinite loop).</div>}
        </div>
        {done && <div className="vm-end">Finished in <b>{execution.steps}</b> executed instructions.</div>}
      </div>
    </div>
  );
}
