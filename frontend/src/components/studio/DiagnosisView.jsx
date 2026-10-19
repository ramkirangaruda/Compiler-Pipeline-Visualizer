import React, { useState } from 'react';
import Diff from './Diff.jsx';
import { featureLabel, pct } from '../../lib/format.js';

function Bar({ value, color = 'var(--mint)', label, right, dim }) {
  return (
    <div className={`bar ${dim ? 'dim' : ''}`}>
      <i style={{ width: `${Math.max(1.5, value * 100)}%`, background: color }} />
      <span>{label}</span>
      <b>{right ?? pct(value, 0)}</b>
    </div>
  );
}

function Evidence({ items }) {
  if (!items?.length) return null;
  const max = Math.max(...items.map((i) => Math.abs(i.contribution)), 0.001);
  return (
    <div className="evidence">
      <h5>Why the model thinks so <small>(feature occlusion: probability drop when the feature is neutralised)</small></h5>
      {items.map((it) => (
        <div className="ev-row" key={it.feature} title={`${it.feature} = ${String(it.value)}`}>
          <span className="ev-name">{featureLabel(it.feature)} <code>= {String(it.value)}</code></span>
          <span className="ev-bar">
            <i className={it.contribution >= 0 ? 'pos' : 'neg'} style={{ width: `${(Math.abs(it.contribution) / max) * 100}%` }} />
          </span>
          <b className={it.contribution >= 0 ? 'pos' : 'neg'}>{it.contribution >= 0 ? '+' : '−'}{(Math.abs(it.contribution) * 100).toFixed(0)}%</b>
        </div>
      ))}
    </div>
  );
}

function Candidate({ c, best, onApply }) {
  const [open, setOpen] = useState(best && c.status !== 'rejected');
  return (
    <div className={`cand ${c.status} ${best ? 'best' : ''}`}>
      <div className="cand-head" onClick={() => setOpen(!open)} role="button" tabIndex={0}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setOpen(!open)}>
        <span className={`badge ${c.status === 'verified' ? 'ok' : c.status}`}>
          {c.status === 'verified' ? '✓ verified' : c.status === 'partial' ? '◐ partial' : '✗ rejected'}
        </span>
        <span className="cand-title">{c.title}</span>
        {best && <span className="badge neutral">best</span>}
        <span className="cand-score" title="P(cause) × fix plausibility">{pct(c.score, 0)}</span>
        <span className="cand-caret">{open ? '▾' : '▸'}</span>
      </div>
      {open && (
        <div className="cand-body">
          <p>{c.description}</p>
          <p className="cand-reason"><b>Compiler says:</b> {c.reason}</p>
          <div className="cand-meta"><span className="chip chip-dark">{c.label_title}</span>
            <span className="chip chip-dark">P(cause) {pct(c.prob, 0)}</span>
            <span className="chip chip-dark">plausibility {pct(c.local_score, 0)}</span></div>
          <Diff hunks={c.diff} />
          {c.status !== 'rejected' && (
            <button className="btn btn-sm" onClick={() => onApply(c.new_source)}>Apply this fix</button>
          )}
        </div>
      )}
    </div>
  );
}

function Entry({ e, onApply }) {
  const d = e.diagnostic;
  const p = e.prediction;
  return (
    <article className="dx-entry fade-in">
      <header className="dx-head">
        <span className="badge error">{d.stage}</span>
        <code className="dx-code">{d.code}</code>
        {e.duplicates > 0 && <span className="badge neutral">+{e.duplicates} more uses</span>}
      </header>
      <p className="dx-msg">{d.message}</p>
      <div className="dx-loc">
        <span>Compiler detected at <b>line {d.line}</b></span>
        {e.localized && <span className={e.localized.line !== d.line ? 'shift' : ''}>→ ML-localised fault <b>line {e.localized.line}:{e.localized.col}</b></span>}
      </div>

      {p ? (
        <div className="dx-pred">
          <div className="dx-pred-top">
            <div>
              <div className="dx-kicker">{e.handled_by === 'baseline' ? 'Rule baseline prediction' : 'ML prediction'} · {p.family}</div>
              <h4>{p.title}</h4>
              <p className="dx-explain">{p.explain}</p>
            </div>
            <div className="dx-conf" style={{ '--c': `${p.confidence * 100}%` }}>
              <svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="15.5" /><circle className="arc" cx="18" cy="18" r="15.5" pathLength="100" strokeDasharray={`${p.confidence * 100} 100`} /></svg>
              <span>{pct(p.confidence, 0)}</span>
            </div>
          </div>
          {p.low_confidence && <div className="dx-warn">Low confidence - several causes are plausible; check the candidates below.</div>}
          <div className="dx-grid">
            <div>
              <h5>Ranked causes</h5>
              {p.probs.filter((x, i) => i === 0 || x.prob >= 0.01).map((x, i) => (
                <Bar key={x.label} value={x.prob} label={x.title} color={i === 0 ? 'var(--mint)' : 'rgba(255,255,255,0.45)'} dim={i > 0} />
              ))}
              {e.baseline && (
                <div className={`dx-base ${e.baseline.agrees ? 'agree' : 'differ'}`}>
                  Rule baseline says <b>{e.baseline.title}</b> {e.baseline.agrees ? '✓ agrees' : '✗ differs'}
                </div>
              )}
            </div>
            <Evidence items={e.explanation} />
          </div>
        </div>
      ) : (
        <div className="dx-pred rules"><h4>Rule-based fix</h4><p className="dx-explain">This lexical / structural error is handled by deterministic rules - no ML needed.</p></div>
      )}

      <h5 className="dx-cands-title">Candidate fixes <small>every candidate was re-compiled before being shown</small></h5>
      {e.candidates.length === 0 && <div className="empty">No automatic repair available for this error.</div>}
      {e.candidates.map((c) => <Candidate key={c.id} c={c} best={c.id === e.best} onApply={onApply} />)}
    </article>
  );
}

export default function DiagnosisView({ diagnosis, onApply, onAutofix, autofix, busy }) {
  if (!diagnosis) return <div className="empty">Compile a program with an error to see the ML diagnosis.</div>;
  return (
    <div className="dx">
      <div className="dx-bar">
        <div>
          <b>{diagnosis.errors} compiler error{diagnosis.errors === 1 ? '' : 's'}</b>
          <span className="muted"> · {diagnosis.mode === 'baseline' ? 'rule baseline (no ML)' : diagnosis.model_loaded ? 'ML diagnosis' : 'model not loaded - rules fallback'}</span>
        </div>
        <button className="btn btn-yellow btn-sm" onClick={onAutofix} disabled={busy}>{busy ? 'Fixing…' : 'Auto-fix all'}</button>
      </div>
      {autofix && (
        <div className={`autofix ${autofix.ok ? 'ok' : 'bad'}`}>
          <b>{autofix.ok ? '✓ Program now compiles' : '✗ Could not fully repair'}</b> after {autofix.steps.length} step{autofix.steps.length === 1 ? '' : 's'}
          <ol>
            {autofix.steps.map((s) => (
              <li key={s.iteration}>
                {s.stuck ? `Stuck on line ${s.line}: ${s.message}` : (
                  <><span className="badge ok">{s.label_title}{s.confidence != null ? ` · ${pct(s.confidence, 0)}` : ''}</span> line {s.line}: {s.title}</>
                )}
              </li>
            ))}
          </ol>
          {!autofix.ok && autofix.remaining.length > 0 && <div className="dx-warn">{autofix.remaining[0]}</div>}
        </div>
      )}
      {diagnosis.entries.map((e, i) => <Entry key={i} e={e} onApply={onApply} />)}
    </div>
  );
}
