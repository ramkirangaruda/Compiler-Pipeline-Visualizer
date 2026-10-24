import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Editor from '../components/studio/Editor.jsx';
import PipelineStrip from '../components/studio/PipelineStrip.jsx';
import DiagnosisView from '../components/studio/DiagnosisView.jsx';
import { TreeView, CfgView } from '../components/studio/GraphViews.jsx';
import { TokensView, SymbolsView, CodeView, RunView } from '../components/studio/StageViews.jsx';
import { api } from '../api.js';
import './studio.css';

const FALLBACK = 'int width = 10;\nint height = 20\nint area = width * height;\nprint(area);\n';
const LABEL = {
  diagnosis: 'Diagnosis', run: 'Run', tokens: 'Tokens', tree: 'Syntax tree', symbols: 'Symbols', code: 'Code', flow: 'Flow graph',
};
// a failing program has no code or flow graph; a working one has no diagnosis
const TABS_FAILING = ['diagnosis', 'tokens', 'tree', 'symbols'];
const TABS_OK = ['run', 'tokens', 'tree', 'symbols', 'code', 'flow'];

export default function Studio() {
  const [examples, setExamples] = useState([]);
  const [source, setSource] = useState(() => sessionStorage.getItem('studio:source') || FALLBACK);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('diagnosis');
  const [applied, setApplied] = useState(null); // {note, source, previous, decision?}
  const [toast, setToast] = useState(null);
  const [execLine, setExecLine] = useState(0);
  const [fixing, setFixing] = useState(false);
  const seq = useRef(0);

  useEffect(() => { api.examples().then(setExamples).catch((e) => setError(e.message)); }, []);

  const run = useCallback(async (src) => {
    const my = ++seq.current;
    setBusy(true);
    try {
      const r = await api.compile(src);
      if (my !== seq.current) return;
      setResult(r);
      setError(null);
      const tabs = r.ok ? TABS_OK : TABS_FAILING;
      setTab((t) => (tabs.includes(t) ? t : tabs[0]));
    } catch (e) {
      if (my === seq.current) setError(`Cannot reach the API (${e.message}). Start the backend: python -m uvicorn app.main:app --port 8010`);
    } finally {
      if (my === seq.current) setBusy(false);
    }
  }, []);

  // compile as you type (debounced) - no Run button needed
  const first = useRef(true);
  useEffect(() => {
    sessionStorage.setItem('studio:source', source);
    if (first.current) { first.current = false; run(source); return undefined; }
    const t = setTimeout(() => run(source), 600);
    return () => clearTimeout(t);
  }, [source, run]);

  // when the program changes because of something other than a fix, forget the undo banner
  useEffect(() => { if (applied && source !== applied.source) setApplied(null); }, [source]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!toast) return undefined;
    const t = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(t);
  }, [toast]);

  // reinforcement signal for the RL fix policy: +1 for an accepted fix, -1 for an undone one
  const feedback = (decision, candidate, reward) => {
    if (!decision) return;
    api.rlFeedback(decision, candidate, reward)
      .then(() => setToast(reward > 0 ? 'Thanks - the RL policy learned from that.' : 'Noted - the RL policy will rank that fix lower.'))
      .catch(() => {});
  };

  const applyFix = (newSource, cand, entry) => {
    setApplied({ note: cand?.title || 'fix', source: newSource, previous: source, decision: entry?.decision_id, candidate: cand?.id });
    setSource(newSource);
    feedback(entry?.decision_id, cand?.id, 1);
  };

  const undo = () => {
    if (!applied) return;
    feedback(applied.decision, applied.candidate, -1);
    setSource(applied.previous);
    setApplied(null);
  };

  const fixAll = async () => {
    setFixing(true);
    try {
      const res = await api.autofix(source);
      setApplied({ note: `${res.steps.length} fix${res.steps.length === 1 ? '' : 'es'}`, source: res.final_source, previous: source });
      setSource(res.final_source);
    } catch (e) {
      setError(e.message);
    } finally {
      setFixing(false);
    }
  };

  const dx = result?.diagnosis;
  const diags = result?.diagnostics || [];
  const warns = result?.warnings || [];
  const ok = !!result?.ok;

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

  const tabs = ok ? TABS_OK : TABS_FAILING;
  let body = <div className="empty"><span className="loader" /> Compiling…</div>;
  if (result) {
    if (tab === 'diagnosis') body = <DiagnosisView diagnosis={dx} onApply={applyFix} />;
    else if (tab === 'tokens') body = <TokensView tokens={result.tokens} source={source} />;
    else if (tab === 'tree') body = <TreeView ast={result.ast} />;
    else if (tab === 'symbols') body = <SymbolsView symbols={result.symbols} />;
    else if (tab === 'code') body = <CodeView tac={result.tac} optimized={result.optimized} verify={result.verify} />;
    else if (tab === 'flow') body = <CfgView cfg={result.cfg} />;
    else if (tab === 'run') body = <RunView execution={result.execution} code={result.optimized?.code || []} onLine={setExecLine} />;
  }

  const broken = examples.filter((e) => e.category === 'broken');
  const working = examples.filter((e) => e.category === 'valid');
  const status = !result ? 'Compiling…' : ok ? '✓ Compiles' : `${diags.length} error${diags.length === 1 ? '' : 's'}`;

  return (
    <div className="studio">
      <div className="container-wide">
        <header className="studio-head">
          <h1>Studio</h1>
          <span className={`status ${!result || busy ? 'busy' : ok ? 'ok' : 'bad'}`}>{busy && result ? 'Compiling…' : status}</span>
          <select className="ex-select" value="" aria-label="Load an example program"
            onChange={(e) => { const ex = examples.find((x) => x.id === e.target.value); if (ex) { setApplied(null); setSource(ex.source); } }}>
            <option value="" disabled>Load an example…</option>
            <optgroup label="Broken programs">{broken.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}</optgroup>
            <optgroup label="Working programs">{working.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}</optgroup>
          </select>
        </header>

        {error && <div className="banner bad">{error}</div>}
        {applied && (
          <div className="banner good">
            Applied: {applied.note}
            <button className="btn-flat" onClick={undo}>Undo</button>
          </div>
        )}
        {toast && <div className="banner note" role="status">{toast}</div>}

        <div className="studio-grid">
          <section className="panel editor-panel" aria-label="Program">
            <div className="editor-wrap">
              <Editor value={source} onChange={setSource} diagnostics={editorDiags} errLines={errLines} mlLines={mlLines}
                execLine={tab === 'run' ? execLine : 0} onRun={() => run(source)} />
            </div>
            {(diags.length > 0 || warns.length > 0) && (
              <div className="problems">
                <div className="problems-head">
                  <b>Problems</b>
                  {diags.length > 1 && <button className="btn btn-sm btn-yellow" onClick={fixAll} disabled={fixing}>{fixing ? 'Fixing…' : 'Fix all'}</button>}
                </div>
                {diags.map((d, i) => {
                  const e = entryFor(d);
                  const best = e?.candidates?.find((c) => c.id === e.best);
                  return (
                    <div className="prob err" key={`e${i}`}>
                      <span className="pl">{d.line}</span>
                      <span className="pm">{d.message.replace(/ \(line \d+\)| on line \d+/, '')}</span>
                      {best && <button className="btn-flat" onClick={() => applyFix(best.new_source, best, e)}>Fix</button>}
                    </div>
                  );
                })}
                {warns.map((d, i) => (
                  <div className="prob warn" key={`w${i}`}><span className="pl">{d.line}</span><span className="pm">{d.message.replace(/ \(line \d+\)/, '')}</span></div>
                ))}
              </div>
            )}
          </section>

          <section className="studio-right">
            <PipelineStrip stages={result?.stages} diagnosis={dx} onSelect={(t) => tabs.includes(t) && setTab(t)} />
            <div className="panel tabs-panel">
              <div className="tabs" role="tablist">
                {tabs.map((id) => (
                  <button key={id} role="tab" aria-selected={tab === id} className={`tab ${tab === id ? 'active' : ''} ${id === 'diagnosis' ? 'ai' : ''}`} onClick={() => setTab(id)}>{LABEL[id]}</button>
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
