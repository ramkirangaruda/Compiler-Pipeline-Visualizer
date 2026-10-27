import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Editor from '../components/studio/Editor.jsx';
import PipelineStrip from '../components/studio/PipelineStrip.jsx';
import DiagnosisView from '../components/studio/DiagnosisView.jsx';
import { TreeView, CfgView } from '../components/studio/GraphViews.jsx';
import { TokensView, SymbolsView, CodeView, RunView } from '../components/studio/StageViews.jsx';
import { api } from '../api.js';
import './studio.css';

const FALLBACK = {
  minic: 'int width = 10;\nint height = 20\nint area = width * height;\nprint(area);\n',
  c: '#include <stdio.h>\n\nint main(void) {\n    int width = 10;\n    int height = 20\n    printf("%d\\n", width * height);\n    return 0;\n}\n',
};
const LANGS = [['c', 'C'], ['minic', 'MiniC']];
const store = (k, v) => { try { sessionStorage.setItem(k, v); } catch { /* storage unavailable */ } };
const load = (k) => { try { return sessionStorage.getItem(k); } catch { return null; } };
const LABEL = {
  diagnosis: 'Diagnosis', run: 'Run', tokens: 'Tokens', tree: 'Syntax tree', symbols: 'Symbols', code: 'Code', flow: 'Flow graph',
};
// a failing program has no code or flow graph; a working one has no diagnosis. C is interpreted straight from its syntax tree.
const TABS_FAILING = ['diagnosis', 'tokens', 'tree', 'symbols'];
const TABS_OK = { minic: ['run', 'tokens', 'tree', 'symbols', 'code', 'flow'], c: ['run', 'tokens', 'tree', 'symbols'] };

export default function Studio() {
  const [examples, setExamples] = useState([]);
  const [language, setLanguage] = useState(() => (load('studio:lang') === 'minic' ? 'minic' : 'c'));
  const [sources, setSources] = useState(() => ({ minic: load('studio:source') || FALLBACK.minic, c: load('studio:source:c') || FALLBACK.c }));
  const source = sources[language];
  const setSource = useCallback((v) => setSources((s) => ({ ...s, [language]: typeof v === 'function' ? v(s[language]) : v })), [language]);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('diagnosis');
  const [applied, setApplied] = useState(null); // {note, source, previous, decision?}
  const [toast, setToast] = useState(null);
  const [execLine, setExecLine] = useState(0);
  const [fixing, setFixing] = useState(false);
  const seq = useRef(0);
  const [llm, setLlm] = useState({ busy: false, result: null, error: null });

  useEffect(() => { api.examples().then(setExamples).catch((e) => setError(e.message)); }, []);

  const run = useCallback(async (src) => {
    const my = ++seq.current;
    setBusy(true);
    try {
      const r = await api.compile(src, language);
      if (my !== seq.current) return;
      setResult(r);
      setError(null);
      const tabs = r.ok ? TABS_OK[language] : TABS_FAILING;
      setTab((t) => (tabs.includes(t) ? t : tabs[0]));
    } catch (e) {
      if (my === seq.current) setError(`Cannot reach the API (${e.message}). Start the backend: python -m uvicorn app.main:app --port 8010`);
    } finally {
      if (my === seq.current) setBusy(false);
    }
  }, [language]);

  // compile as you type (debounced) - no Run button needed; switching language compiles at once
  const lastLang = useRef(null);
  useEffect(() => {
    store('studio:lang', language);
    store(language === 'c' ? 'studio:source:c' : 'studio:source', source);
    if (lastLang.current !== language) { lastLang.current = language; run(source); return undefined; }
    const t = setTimeout(() => run(source), 600);
    return () => clearTimeout(t);
  }, [source, language, run]);

  // when the program changes because of something other than a fix, forget the undo banner
  useEffect(() => { if (applied && source !== applied.source) setApplied(null); }, [source]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { setLlm({ busy: false, result: null, error: null }); }, [source, language]);
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

  const askLlm = async () => {
    setLlm({ busy: true, result: null, error: null });
    setTab('diagnosis');
    try {
      setLlm({ busy: false, result: await api.llmFix(source), error: null });
    } catch (e) {
      setLlm({ busy: false, result: null, error: e.message });
    }
  };

  const fixAll = async () => {
    setFixing(true);
    try {
      const res = await api.autofix(source, language);
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

  const hasFix = (dx?.entries || []).some((e) => { const b = e.candidates?.find((c) => c.id === e.best); return b && b.score >= 0.5; });
  const tabs = ok ? TABS_OK[language] : TABS_FAILING;
  const srcLines = useMemo(() => source.split('\n').map((text) => ({ op: 'src', text })), [source]);
  let body = <div className="empty"><span className="loader" /> Compiling…</div>;
  if (result) {
    if (tab === 'diagnosis') body = <DiagnosisView diagnosis={dx} onApply={applyFix} llm={language === 'c' ? llm : null} onAskLlm={askLlm} />;
    else if (tab === 'tokens') body = <TokensView tokens={result.tokens} source={source} />;
    else if (tab === 'tree') body = <TreeView ast={result.ast ?? result.ast_tree} />;
    else if (tab === 'symbols') body = <SymbolsView symbols={result.symbols} />;
    else if (tab === 'code') body = <CodeView tac={result.tac} optimized={result.optimized} verify={result.verify} />;
    else if (tab === 'flow') body = <CfgView cfg={result.cfg} />;
    else if (tab === 'run') body = <RunView execution={result.execution} code={language === 'c' ? srcLines : (result.optimized?.code || [])} base={language === 'c' ? 1 : 0} onLine={setExecLine} />;
  }

  const mine = examples.filter((e) => (e.language || 'minic') === language);
  const broken = mine.filter((e) => e.category === 'broken');
  const working = mine.filter((e) => e.category === 'valid');
  const status = !result ? 'Compiling…' : ok ? '✓ Compiles' : `${diags.length} error${diags.length === 1 ? '' : 's'}`;

  return (
    <div className="studio">
      <div className="container-wide">
        <header className="studio-head">
          <h1>Studio</h1>
          <div className="lang-seg" role="group" aria-label="Language">
            {LANGS.map(([id, name]) => (
              <button key={id} aria-pressed={language === id} onClick={() => { setApplied(null); setResult(null); setLanguage(id); }}>{name}</button>
            ))}
          </div>
          <span className={`status ${!result || busy ? 'busy' : ok ? 'ok' : 'bad'}`}>{busy && result ? 'Compiling…' : status}</span>
          <select className="ex-select" value="" aria-label="Load an example program" key={language}
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
              <Editor language={language} value={source} onChange={setSource} diagnostics={editorDiags} errLines={errLines} mlLines={mlLines}
                execLine={tab === 'run' ? execLine : 0} onRun={() => run(source)} />
            </div>
            {(diags.length > 0 || warns.length > 0) && (
              <div className="problems">
                <div className="problems-head">
                  <b>Problems</b>
                  {diags.length > 1 && <button className="btn btn-sm btn-yellow" onClick={fixAll} disabled={fixing}>{fixing ? 'Fixing…' : 'Fix all'}</button>}
                  {language === 'c' && !hasFix && <button className="btn btn-sm" onClick={askLlm} disabled={llm.busy}>{llm.busy ? 'Asking…' : 'Ask an LLM'}</button>}
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
            <PipelineStrip language={language} stages={result?.stages} diagnosis={dx} onSelect={(t) => tabs.includes(t) && setTab(t)} />
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
