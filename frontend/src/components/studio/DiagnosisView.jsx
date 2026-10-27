import React from 'react';
import Diff from './Diff.jsx';
import { featureLabel, pct } from '../../lib/format.js';

function Entry({ e, onApply }) {
  const d = e.diagnostic;
  const p = e.prediction;
  const best = e.candidates.find((c) => c.id === e.best);
  const others = e.candidates.filter((c) => c.id !== e.best && c.status !== 'rejected');
  const lastResort = e.candidates.find((c) => c.id === e.last_resort);
  const rejected = e.candidates.filter((c) => c.status === 'rejected').length;
  const also = p ? p.probs.slice(1).filter((x) => x.prob >= 0.03).slice(0, 2) : [];
  const why = (e.explanation || []).filter((x) => x.contribution > 0).slice(0, 3);

  return (
    <article className="dx-card fade-in">
      <div className="dx-top">
        <span className="badge error">line {d.line}</span>
        <span className="dx-msg">{d.message}</span>
      </div>
      {e.localized && e.localized.line !== d.line && (
        <p className="dx-shift">The compiler stopped on line {d.line}, but the problem is on line {e.localized.line}.</p>
      )}

      {p ? (
        <div className="dx-cause">
          <div>
            <span className="dx-label">Likely cause</span>
            <h4>{p.title}</h4>
            <p>{p.explain}</p>
            {also.length > 0 && <p className="dx-also">Also possible: {also.map((x) => `${x.title} ${pct(x.prob, 0)}`).join(' · ')}</p>}
            {why.length > 0 && <p className="dx-also">Because: {why.map((x) => `${featureLabel(x.feature)} = ${String(x.value)}`).join(' · ')}</p>}
          </div>
          <div className="dx-conf" title="model confidence">{pct(p.confidence, 0)}</div>
        </div>
      ) : (
        <p className="dx-also">
          {d.code === 'E_GCC'
            ? 'The compiler reported this error. It is outside the causes the model was trained on, so the suggestions below come from gcc itself and a repair search - and every one was re-checked by gcc.'
            : 'This error is handled by a fixed rule, so no model is involved.'}
        </p>
      )}

      {best ? (
        <div className="dx-fix">
          <div className="dx-fix-head">
            <span className={`badge ${best.status === 'verified' ? 'ok' : 'partial'}`}>{best.status === 'verified' ? '✓ checked by the compiler' : '◐ partial fix'}</span>
            <b>{best.title}</b>
          </div>
          <p>{best.description}</p>
          <Diff hunks={best.diff} />
          <button className="btn btn-sm" onClick={() => onApply(best.new_source, best, e)}>Apply fix</button>
        </div>
      ) : (
        <p className="dx-none">
          No safe automatic fix for this error - the message above says what gcc found.
          {lastResort ? ' As a last resort you can comment the line out (the code on it is lost).' : ''}
        </p>
      )}

      {others.length > 0 && (
        <details className="more">
          <summary>{others.length} other option{others.length === 1 ? '' : 's'}</summary>
          {others.map((c) => (
            <div className="dx-other" key={c.id}>
              <div><b>{c.title}</b><small>{c.description}</small></div>
              <button className="btn-flat" onClick={() => onApply(c.new_source, c, e)}>Apply</button>
            </div>
          ))}
        </details>
      )}
      {rejected > 0 && <p className="dx-rej">{rejected} other idea{rejected === 1 ? ' was' : 's were'} rejected because the compiler did not accept {rejected === 1 ? 'it' : 'them'}.</p>}
    </article>
  );
}

function LlmBox({ llm, onAsk, onApply, noFix }) {
  const r = llm.result;
  if (!noFix && !llm.busy && !r && !llm.error) {
    return <p className="dx-more"><button className="btn-flat" onClick={onAsk}>Not what you meant? Ask an LLM</button></p>;
  }
  return (
    <section className="dx-card dx-llm fade-in">
      <div className="dx-top"><span className="badge partial">LLM</span><span className="dx-msg">Ask a language model</span></div>
      {!r && !llm.busy && !llm.error && (
        <>
          <p className="dx-also">
            {noFix ? 'The built-in fixes are weak guesses for this error (or there is none). ' : ''}
            A language model can suggest a fix; gcc rebuilds every suggestion and only builds that pass are offered. Clicking sends your program to the model provider.
          </p>
          <button className="btn btn-sm" onClick={onAsk}>Ask an LLM</button>
        </>
      )}
      {llm.busy && <p className="dx-also"><span className="loader" /> Asking the model, then checking its answer with gcc…</p>}
      {llm.error && <p className="dx-none">{llm.error}</p>}
      {r && r.message && <p className={r.suggestions?.length ? 'dx-also' : 'dx-none'}>{r.message}</p>}
      {r && (r.suggestions || []).map((c) => (
        <div className="dx-fix" key={c.id}>
          <div className="dx-fix-head">
            <span className={`badge ${c.status === 'verified' ? 'ok' : 'partial'}`}>{c.status === 'verified' ? '✓ checked by gcc' : '◐ partial: gcc still reports errors'}</span>
            <b>{c.title}</b>
          </div>
          <p>{c.description}</p>
          <Diff hunks={c.diff} />
          <button className="btn btn-sm" onClick={() => onApply(c.new_source, c, null)}>Apply fix</button>
        </div>
      ))}
      {r && r.configured && (r.suggestions || []).length === 0 && !llm.busy && <button className="btn-flat" onClick={onAsk}>Try again</button>}
    </section>
  );
}

export default function DiagnosisView({ diagnosis, onApply, llm, onAskLlm }) {
  if (!diagnosis?.entries?.length) return <div className="empty">No diagnosis available.</div>;
  // a built-in fix only counts as strong if it is a confident one: a low score means the search was guessing
  const strong = diagnosis.entries.some((e) => { const b = e.candidates.find((c) => c.id === e.best); return b && b.score >= 0.5; });
  const noFix = !strong;
  return (
    <div className="dx">
      {diagnosis.entries.map((e, i) => <Entry key={i} e={e} onApply={onApply} />)}
      {llm && <LlmBox llm={llm} onAsk={onAskLlm} onApply={onApply} noFix={noFix} />}
    </div>
  );
}
