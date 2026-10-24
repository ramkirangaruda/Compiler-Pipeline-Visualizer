import React, { useEffect, useMemo, useRef, useState } from 'react';

/* ------------------------------------------------------------- DFA drawings */
const DFAS = {
  ident: {
    title: 'Identifier / keyword', regex: '[A-Za-z_][A-Za-z0-9_]*',
    states: [{ id: 's0', x: 50, y: 62 }, { id: 's1', x: 190, y: 62, accept: true }],
    edges: [{ a: 's0', b: 's1', label: 'letter | _' }, { a: 's1', b: 's1', label: 'letter | digit | _', loop: true }],
  },
  number: {
    title: 'Number', regex: '[0-9]+ ( . [0-9]+ )?',
    states: [{ id: 's0', x: 36, y: 62 }, { id: 's1', x: 118, y: 62, accept: true }, { id: 's2', x: 200, y: 62 }, { id: 's3', x: 282, y: 62, accept: true }],
    edges: [
      { a: 's0', b: 's1', label: 'digit' }, { a: 's1', b: 's1', label: 'digit', loop: true },
      { a: 's1', b: 's2', label: '.' }, { a: 's2', b: 's3', label: 'digit' }, { a: 's3', b: 's3', label: 'digit', loop: true },
    ],
  },
  string: {
    title: 'String', regex: '" ( [^"\\n] | \\\\. )* "',
    states: [{ id: 's0', x: 40, y: 62 }, { id: 's1', x: 150, y: 62 }, { id: 's2', x: 260, y: 62, accept: true }],
    edges: [{ a: 's0', b: 's1', label: '"' }, { a: 's1', b: 's1', label: 'not " or newline', loop: true }, { a: 's1', b: 's2', label: '"' }],
  },
};
const R = 17;

function Dfa({ spec, active }) {
  const S = Object.fromEntries(spec.states.map((s) => [s.id, s]));
  const mk = `dfa-${spec.title}`;
  return (
    <div className="dfa">
      <div className="dfa-title">{spec.title} <code className="dfa-re">{spec.regex}</code></div>
      <svg viewBox="0 0 320 120" role="img" aria-label={`${spec.title} automaton`}>
        <defs><marker id={mk} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#c9bcff" /></marker></defs>
        <path d={`M${S.s0.x - 34},${S.s0.y} L${S.s0.x - R - 2},${S.s0.y}`} className="dfa-edge" markerEnd={`url(#${mk})`} />
        {spec.edges.map((e, i) => {
          const A = S[e.a], B = S[e.b];
          if (e.loop) {
            return (
              <g key={i}>
                <path d={`M${A.x - 9},${A.y - R + 1} C${A.x - 26},${A.y - 48} ${A.x + 26},${A.y - 48} ${A.x + 9},${A.y - R + 1}`} className="dfa-edge" markerEnd={`url(#${mk})`} />
                <text x={A.x} y={A.y - 44} textAnchor="middle" className="dfa-lbl">{e.label}</text>
              </g>
            );
          }
          return (
            <g key={i}>
              <path d={`M${A.x + R + 1},${A.y} L${B.x - R - 3},${B.y}`} className="dfa-edge" markerEnd={`url(#${mk})`} />
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
  useEffect(() => { setN(toks.length); setPlaying(false); }, [toks]);
  useEffect(() => {
    if (!playing) return undefined;
    const t = setInterval(() => setN((x) => { if (x >= toks.length) { setPlaying(false); return x; } return x + 1; }), 90);
    return () => clearInterval(t);
  }, [playing, toks.length]);

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

  const act = dfaFor(n > 0 ? toks[n - 1] : null);
  return (
    <div className="view">
      <div className="view-bar">
        <span className="muted">{toks.length} tokens</span>
        <button className="btn-flat" onClick={() => { setN(0); setPlaying(true); }}>▶ Replay scan</button>
      </div>
      <pre className="scan">
        {segments.map((s, k) => (s.gap ? <span key={k} className="gap">{s.text}</span>
          : <span key={k} className={`tk ${s.i < n ? `on k-${s.kind}` : ''} ${s.i === n - 1 ? 'cur' : ''}`}>{s.text}</span>))}
      </pre>
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
      <details className="more">
        <summary>Show the finite automata behind the scanner</summary>
        <div className="dfa-row">
          <Dfa spec={DFAS.ident} active={act.ident} /><Dfa spec={DFAS.number} active={act.number} /><Dfa spec={DFAS.string} active={act.string} />
        </div>
      </details>
    </div>
  );
}

/* ----------------------------------------------------------------- symbols */
export function SymbolsView({ symbols }) {
  if (!symbols) return <div className="empty">No symbol table: the parser stopped on a syntax error.</div>;
  const depth = (s) => { let d = 0, p = s.parent; while (p != null) { d++; p = symbols[p].parent; } return d; };
  return (
    <div className="view scopes">
      {symbols.map((s) => (
        <div key={s.id} className="scope" style={{ marginLeft: depth(s) * 22 }}>
          <div className="scope-head"><b>scope {s.id}</b><span className="badge neutral">{s.kind}</span></div>
          {s.symbols.length === 0 ? <div className="muted mono small">no declarations</div> : (
            <table><thead><tr><th>name</th><th>type</th><th>declared</th><th>read?</th></tr></thead>
              <tbody>{s.symbols.map((y) => (
                <tr key={y.uid}><td>{y.name}</td><td><span className="kind k-TYPE">{y.type}</span></td><td>line {y.line}</td>
                  <td>{y.used ? <span className="badge ok">used</span> : <span className="badge partial">unused</span>}</td></tr>
              ))}</tbody></table>
          )}
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------ intermediate code */
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

export function CodeView({ tac, optimized, verify }) {
  if (!optimized) return <div className="empty">Intermediate code is generated only for programs that compile.</div>;
  const rows = diffRows(tac, optimized.code, optimized.diff);
  const passes = optimized.report.filter((r) => r.count > 0);
  return (
    <div className="view">
      <div className="code-sum">
        <b>{tac.length} → {optimized.code.length}</b> instructions
        {verify && <> · <b>{verify.unoptimized_steps} → {verify.optimized_steps}</b> executed</>}
        {verify && <span className={`badge ${verify.match ? 'ok' : 'error'}`}>{verify.match ? 'same output ✓' : 'output differs'}</span>}
      </div>
      {passes.length > 0 && (
        <div className="pass-chips">{passes.map((r) => <span key={r.name} className="chip chip-dark">{r.name} ×{r.count}</span>)}</div>
      )}
      <div className="diff2">
        <div className="d2-head">Generated</div><div className="d2-head">After optimization</div>
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

/* --------------------------------------------------------------------- run */
const isTemp = (n) => /^t\d+$/.test(n);

export function RunView({ execution, code, onLine, base = 0 }) {
  const trace = execution?.trace || [];
  const [pos, setPos] = useState(trace.length);
  const [playing, setPlaying] = useState(false);
  const listRef = useRef(null);
  useEffect(() => { setPos(trace.length); setPlaying(false); }, [execution]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!playing) return undefined;
    const t = setInterval(() => setPos((p) => { if (p >= trace.length) { setPlaying(false); return p; } return p + 1; }), 70);
    return () => clearInterval(t);
  }, [playing, trace.length]);

  const state = useMemo(() => {
    const vars = {}, out = [];
    let changed = null;
    for (let i = 0; i < pos; i++) {
      const s = trace[i];
      if (s.set) { vars[s.set[0]] = s.set[1]; changed = s.set[0]; }
      if (s.out != null) out.push(s.out);
    }
    return { vars, out, changed };
  }, [trace, pos]);

  const done = pos >= trace.length;
  const curPc = pos > 0 && !done ? trace[pos - 1].pc : -1;
  useEffect(() => {
    onLine?.(pos > 0 && !done ? trace[pos - 1].line : 0);
    listRef.current?.querySelector('.ins.cur')?.scrollIntoView({ block: 'nearest' });
  }, [pos]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => onLine?.(0), []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!execution) return <div className="empty">Only programs that compile can run.</div>;
  const names = Object.keys(state.vars).filter((k) => !isTemp(k));
  return (
    <div className="view run">
      <div className="run-out">
        <div className="vm-sub">Output</div>
        <div className="console">
          {state.out.length === 0 ? <span className="muted">(the program printed nothing{done ? '' : ' yet'})</span>
            : execution.language === 'c' ? <pre className="c-out">{state.out.join('')}</pre>
              : state.out.map((o, i) => <div key={i}>&gt; {o}</div>)}
          {done && execution.halted === 'error' && <div className="rt-err">{execution.error}</div>}
          {done && execution.halted === 'step_limit' && <div className="rt-err">Stopped after the step limit (possible infinite loop).</div>}
        </div>
        <div className="vm-sub">Variables</div>
        <table className="vars">
          <tbody>
            {names.length === 0 && <tr><td className="muted">none yet</td></tr>}
            {names.map((n) => <tr key={n} className={n === state.changed && !done ? 'flash' : ''}><td>{n}</td><td>{state.vars[n]}</td></tr>)}
          </tbody>
        </table>
      </div>
      <div className="run-code">
        <div className="view-bar">
          <span className="vm-sub" style={{ margin: 0 }}>Step through the code</span>
          <span className="bar-btns">
            <button className="btn-flat" onClick={() => { if (done) setPos(0); setPlaying(!playing); }}>{playing ? '⏸ Pause' : '▶ Run'}</button>
            <button className="btn-flat" onClick={() => { setPlaying(false); setPos(Math.min(trace.length, pos + 1)); }}>Step</button>
            <button className="btn-flat" onClick={() => { setPlaying(false); setPos(0); }}>Reset</button>
          </span>
        </div>
        <div className="ins-list" ref={listRef}>
          {code.map((i, k) => (
            <div key={k} className={`ins ${i.op === 'label' ? 'label' : ''} ${k === curPc ? 'cur' : ''}`}>
              <span className="ix">{i.op === 'label' ? '' : k + base}</span><code>{i.text}</code>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
