import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Editor from '../components/studio/Editor.jsx';
import PipelineStrip from '../components/studio/PipelineStrip.jsx';
import DiagnosisView from '../components/studio/DiagnosisView.jsx';
import { TreeView, CfgView } from '../components/studio/GraphViews.jsx';
import { TokensView, SymbolsView, TacView, OptimizerView, ExecView } from '../components/studio/StageViews.jsx';
import { api } from '../api.js';
import { pct } from '../lib/format.js';
import './studio.css';

const FALLBACK = 'int width = 10;\nint height = 20\nint area = width * height;\nprint(area);\n';
const STAGE_TAB = { lexer: 'tokens', parser: 'tree', semantic: 'symbols', ir: 'tac', optimizer: 'optimizer', vm: 'exec' };
const TABS = [
  ['diagnosis', 'AI Diagnosis'], ['tokens', 'Tokens'], ['tree', 'Syntax Tree'], ['symbols', 'Symbols'],
  ['tac', '3-Address Code'], ['cfg', 'CFG'], ['optimizer', 'Optimizer'], ['exec', 'Execute'],
];

export default function Studio() {
  const [examples, setExamples] = useState([]);
  const [source, setSource] = useState(() => sessionStorage.getItem('studio:source') || FALLBACK);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [fixing, setFixing] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('ml');
  const [ranker, setRanker] = useState('rl');
  const [lastDecision, setLastDecision] = useState(null);
  const [applied, setApplied] = useState(null);
  const [toast, setToast] = useState(null);
  const [optimize, setOptimize] = useState(true);
  const [live, setLive] = useState(true);
  const [tab, setTab] = useState('diagnosis');
  const [autofix, setAutofix] = useState(null);
  const [undoSrc, setUndoSrc] = useState(null);
  const [execLine, setExecLine] = useState(0);
  const [active, setActive] = useState(null);
  const seq = useRef(0);
  const first = useRef(true);

  useEffect(() => { api.examples().then(setExamples).catch((e) => setError(e.message)); }, []);

  const run = useCallback(async (src, opts = {}) => {
    const my = ++seq.current;
    setBusy(true);
    try {
      const r = await api.compile(src, opts.optimize ?? optimize, opts.mode ?? mode, opts.ranker ?? ranker);
      if (my !== seq.current) return;
      setResult(r);
      setError(null);
      setTab((t) => (r.ok ? (t === 'diagnosis' ? 'tokens' : t) : 'diagnosis'));
    } catch (e) {
      if (my === seq.current) setError(`Could not reach the API (${e.message}). Start the backend: uvicorn app.main:app --port 8000`);
    } finally {
      if (my === seq.current) setBusy(false);
    }
  }, [mode, optimize, ranker]);

  // initial compile + live compile (debounced) on edits / option changes
  useEffect(() => {
    sessionStorage.setItem('studio:source', source);
    if (first.current) { first.current = false; run(source); return undefined; }
    if (!live) return undefined;
    const t = setTimeout(() => run(source), 650);
    return () => clearTimeout(t);
  }, [source, live, run]);

  const loadExample = (ex) => {
    setActive(ex.id);
    setAutofix(null);
    setApplied(null);
    setUndoSrc(null);
    setSource(ex.source);
    if (!live) run(ex.source);
  };

  // reinforcement signal for the RL fix policy: +1 when a suggested fix is accepted, -1 when it is undone
  const sendFeedback = (decisionId, candidateId, reward) => {
    api.rlFeedback(decisionId, candidateId, reward)
      .then((r) => setToast(`RL policy updated from your ${reward > 0 ? 'accept' : 'undo'}: π(this fix) ${(r.before * 100).toFixed(0)}% → ${(r.after * 100).toFixed(0)}%`))
      .catch(() => {});
  };

  const applyFix = (newSource, cand, entry) => {
    setUndoSrc(source);
    setAutofix(null);
    setApplied({ title: cand?.title || 'fix', source: newSource });
    setSource(newSource);
    if (cand && entry?.decision_id) {
      setLastDecision({ decision: entry.decision_id, candidate: cand.id });
      sendFeedback(entry.decision_id, cand.id, 1);
    } else {
      setLastDecision(null);
    }
    if (!live) run(newSource);
  };

  const doAutofix = async () => {
    setFixing(true);
    try {
      const res = await api.autofix(source, mode, ranker);
      setUndoSrc(source);
      setApplied(null);
      setAutofix(res);
      setSource(res.final_source);
      if (!live) run(res.final_source);
    } catch (e) {
      setError(e.message);
    } finally {
      setFixing(false);
    }
  };

  const undo = () => {
    if (lastDecision) { sendFeedback(lastDecision.decision, lastDecision.candidate, -1); setLastDecision(null); }
    setSource(undoSrc); setUndoSrc(null); setAutofix(null); setApplied(null); if (!live) run(undoSrc);
  };

  useEffect(() => {
    if (!toast) return undefined;
    const t = setTimeout(() => setToast(null), 4200);
    return () => clearTimeout(t);
  }, [toast]);

  const dx = result?.diagnosis;
  const diags = result?.diagnostics || [];
  const warns = result?.warnings || [];

  const editorDiags = useMemo(() => [
    ...diags.map((d) => ({ from: d.start, to: d.end, severity: 'error', message: d.message })),
    ...warns.map((d) => ({ from: d.start, to: d.end, severity: 'warning', message: d.message })),
  ], [diags, warns]);
  const errLines = useMemo(() => [...new Set(diags.map((d) => d.line))], [diags]);
  const mlLines = useMemo(
    () => (dx?.entries || []).filter((e) => e.localized && e.localized.line !== e.diagnostic.line).map((e) => e.localized.line),
    [dx],
  );

  const entryFor = (d) => dx?.entries?.find((e) => e.diagnostic.start === d.start && e.diagnostic.code === d.code);
  const quickFix = (e) => {
    const best = e?.candidates?.find((c) => c.id === e.best);
    if (best) applyFix(best.new_source, best, e);
  };

  const tabs = TABS.filter(([id]) => id !== 'diagnosis' || (result && !result.ok));

  let body = <div className="empty"><span className="loader" /> Compiling…</div>;
  if (result) {
    switch (tab) {
      case 'diagnosis': body = <DiagnosisView diagnosis={dx} onApply={applyFix} onAutofix={doAutofix} autofix={autofix} busy={fixing} />; break;
      case 'tokens': body = <TokensView tokens={result.tokens} source={source} />; break;
      case 'tree': body = <TreeView ast={result.ast} />; break;
      case 'symbols': body = <SymbolsView symbols={result.symbols} />; break;
      case 'tac': body = <TacView tac={result.tac} />; break;
      case 'cfg': body = <CfgView cfg={result.cfg} cfgBefore={result.cfg_unoptimized} />; break;
      case 'optimizer': body = <OptimizerView tac={result.tac} optimized={result.optimized} verify={result.verify} />; break;
      case 'exec': body = <ExecView execution={result.execution} code={result.optimized?.code || []} onLine={setExecLine} />; break;
      default: break;
    }
  }

  const groups = [['Working programs', examples.filter((e) => e.category === 'valid')], ['Broken programs - try the ML repair', examples.filter((e) => e.category === 'broken')]];

  return (
    <div className="studio">
      <div className="container-wide">
        <div className="studio-top">
          <div>
            <h1 className="studio-h">Compiler <span className="hl">Studio</span></h1>
            <p className="muted">Edit MiniC, watch every phase, and break things on purpose. Live compile is {live ? 'on' : 'off'} · <kbd>Ctrl</kbd>+<kbd>Enter</kbd> compiles.</p>
          </div>
          <div className="studio-actions">
            <span className="ctl-label">Diagnosis</span>
            <div className="seg-ctl" role="group" aria-label="Diagnosis mode">
              <button className={mode === 'ml' ? 'on' : ''} onClick={() => setMode('ml')} title="Machine-learning classifier">ML</button>
              <button className={mode === 'baseline' ? 'on' : ''} onClick={() => setMode('baseline')} title="Hand-written rules only">Rules</button>
            </div>
            <span className="ctl-label">Fix order</span>
            <div className="seg-ctl" role="group" aria-label="Fix ordering">
              <button className={ranker === 'rl' ? 'on' : ''} onClick={() => setRanker('rl')} title="Reinforcement-learning policy orders the candidate fixes">RL</button>
              <button className={ranker === 'heuristic' ? 'on' : ''} onClick={() => setRanker('heuristic')} title="Hand-written score ordering">Heuristic</button>
            </div>
            <label className="toggle"><input type="checkbox" checked={optimize} onChange={(e) => setOptimize(e.target.checked)} /> Optimizer</label>
            <label className="toggle"><input type="checkbox" checked={live} onChange={(e) => setLive(e.target.checked)} /> Live</label>
            <button className="btn btn-sm" onClick={() => run(source)} disabled={busy}>{busy ? 'Compiling…' : 'Compile & run'}</button>
          </div>
        </div>

        <div className="examples">
          {groups.map(([title, list]) => (
            <div className="ex-group" key={title}>
              <span className="ex-title">{title}</span>
              <div className="ex-chips">
                {list.map((ex) => (
                  <button key={ex.id} className={`ex-chip ${active === ex.id ? 'on' : ''} ${ex.category}`} onClick={() => loadExample(ex)} title={ex.description || ex.name}>{ex.name}</button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {error && <div className="banner bad">{error}</div>}
        {toast && <div className="banner good toast" role="status">🎯 {toast}</div>}
        {autofix && undoSrc != null && (
          <div className={`banner ${autofix.ok ? 'good' : 'warn'}`}>
            Auto-fix applied {autofix.steps.length} step{autofix.steps.length === 1 ? '' : 's'}: {autofix.ok ? 'the program now compiles.' : 'some errors remain.'}
            <button className="btn-flat" onClick={undo}>Undo</button>
          </div>
        )}

        {applied && undoSrc != null && !autofix && source === applied.source && (
          <div className="banner good">
            Applied: {applied.title}
            <button className="btn-flat" onClick={undo}>Undo</button>
            <span className="muted">accept = +1 and undo = −1 reward for the RL policy</span>
          </div>
        )}

        <div className="studio-grid">
          <section className="panel editor-panel" aria-label="Source editor">
            <div className="panel-head">
              <span className="panel-title">Source · MiniC</span>
              <span className="legend"><i className="lg err" /> compiler error <i className="lg ml" /> ML-localised fault <i className="lg ex" /> executing</span>
            </div>
            <div className="editor-wrap">
              <Editor value={source} onChange={setSource} diagnostics={editorDiags} errLines={errLines} mlLines={mlLines}
                execLine={tab === 'exec' ? execLine : 0} onRun={() => run(source)} />
            </div>
            <div className="problems">
              <div className="problems-head">
                <b>Problems</b>
                <span className={`badge ${diags.length ? 'error' : 'ok'}`}>{diags.length} error{diags.length === 1 ? '' : 's'}</span>
                <span className={`badge ${warns.length ? 'partial' : 'neutral'}`}>{warns.length} warning{warns.length === 1 ? '' : 's'}</span>
              </div>
              <div className="problems-list">
                {diags.length === 0 && warns.length === 0 && result && <div className="prob ok">✓ No problems - the program compiled.</div>}
                {diags.map((d, i) => {
                  const e = entryFor(d);
                  const p = e?.prediction;
                  const best = e?.candidates?.find((c) => c.id === e.best);
                  return (
                    <div className="prob err" key={`e${i}`}>
                      <span className="pl">L{d.line}</span>
                      <span className="pm">{d.message}</span>
                      {p && <span className="badge ok" title={p.explain}>{p.title} · {pct(p.confidence, 0)}</span>}
                      {best && <button className="btn-flat" onClick={() => quickFix(e)}>Quick fix</button>}
                    </div>
                  );
                })}
                {warns.map((d, i) => (
                  <div className="prob warn" key={`w${i}`}><span className="pl">L{d.line}</span><span className="pm">{d.message}</span></div>
                ))}
              </div>
            </div>
          </section>

          <section className="studio-right">
            <PipelineStrip stages={result?.stages} diagnosis={dx} onSelect={(k) => setTab(STAGE_TAB[k])} />
            {result?.stats && (
              <div className="stat-chips">
                {['tokens', 'scopes', 'symbols', 'blocks'].filter((k) => result.stats[k] != null).map((k) => (
                  <span key={k} className="chip chip-dark">{result.stats[k]} {k}</span>
                ))}
                {result.stats.tac_before != null && <span className="chip chip-dark">{result.stats.tac_before} → {result.stats.tac_after} TAC</span>}
              </div>
            )}
            <div className="panel tabs-panel">
              <div className="tabs" role="tablist">
                {tabs.map(([id, label]) => (
                  <button key={id} role="tab" aria-selected={tab === id} className={`tab ${tab === id ? 'active' : ''} ${id === 'diagnosis' ? 'ai' : ''}`} onClick={() => setTab(id)}>{label}</button>
                ))}
              </div>
              <div className="tab-body">{body}</div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
