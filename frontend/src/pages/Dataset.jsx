import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SpotlightCard from '../reactbits/SpotlightCard.jsx';
import FadeContent from '../reactbits/FadeContent.jsx';
import { api } from '../api.js';
import './dataset.css';

const PAGE = 8;

function Code({ source, mark, markClass }) {
  const lines = source.replace(/\n$/, '').split('\n');
  return (
    <pre className="dscode">
      {lines.map((l, i) => (
        <div key={i} className={`dl ${mark?.(l, i + 1) ? markClass : ''}`}>
          <span className="ln">{i + 1}</span><code>{l || ' '}</code>
        </div>
      ))}
    </pre>
  );
}

export default function Dataset() {
  const nav = useNavigate();
  const [ds, setDs] = useState(null);
  const [err, setErr] = useState(null);
  const [label, setLabel] = useState(null);
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState(null);
  const [sel, setSel] = useState(0);

  useEffect(() => { api.dataset().then((d) => { setDs(d); setLabel(d.classes[0]?.label); }).catch((e) => setErr(e.message)); }, []);
  useEffect(() => {
    if (!label) return;
    setPage(null);
    api.samples(label, offset, PAGE).then((p) => { setPage(p); setSel(0); }).catch((e) => setErr(e.message));
  }, [label, offset]);

  const cls = ds?.classes.find((c) => c.label === label);
  const sample = page?.samples[sel];
  const origSet = useMemo(() => new Set((sample?.original || '').split('\n').map((l) => l.trim())), [sample]);
  const corrSet = useMemo(() => new Set((sample?.source || '').split('\n').map((l) => l.trim())), [sample]);

  const tryInStudio = () => { sessionStorage.setItem('studio:source', sample.source); nav('/studio'); };

  if (err) return <div className="container page-head"><h1>Dataset</h1><div className="banner bad">API unreachable: {err}</div></div>;
  if (!ds) return <div className="container page-head"><h1>Dataset</h1><div className="empty"><span className="loader" /> Loading…</div></div>;

  return (
    <div>
      <div className="container page-head">
        <span className="eyebrow">datasets/ · {ds.n_samples.toLocaleString()} labelled programs</span>
        <h1 style={{ marginTop: 16 }}>Labelled <span className="hl">Dataset</span></h1>
        <p>Every training example is a real MiniC program that fails to compile for one known reason. Programs live in one folder per cause - the folder name <em>is</em> the label - and each was verified by the compiler.</p>
      </div>

      <div className="container ds-top">
        <div className="panel tree-panel">
          <div className="panel-head"><span className="panel-title">Folder layout</span></div>
          <pre className="ftree">{`datasets/
├─ seeds/valid/          ${ds.n_seeds} seed programs
├─ labeled/<CAUSE>/      one folder per class
│  ├─ ${(label || 'MISSING_SEMICOLON')}/
│  │  ├─ *.mc            ${cls?.count ?? 0} programs
│  │  └─ labels.csv
│  └─ …11 more classes
├─ handwritten/<CAUSE>/  ${ds.n_handwritten} programs
├─ manifest.csv          all samples
└─ processed/
   ├─ features.csv
   ├─ handwritten_features.csv
   ├─ dataset_stats.json
   └─ label_map.json`}</pre>
          <div className="ds-notes">
            <p><b>How samples are made.</b> A generator writes type-correct, terminating programs; one of 12 mutators corrupts a copy in exactly one way; the real compiler must then fail for the expected reason or the sample is discarded.</p>
            <p><b>No leakage.</b> Train/test split is by <em>seed program</em>, so a test program never shares an origin with a training program.</p>
            <p><b>Honesty note.</b> The data is synthetic. That is why a separate hand-written set exists - and why its accuracy is reported on the Dashboard.</p>
          </div>
        </div>

        <div className="cls-grid">
          {ds.classes.map((c, i) => (
            <FadeContent key={c.label} blur duration={450} delay={(i % 3) * 70}>
              <SpotlightCard theme="light" className={`cls ${c.label === label ? 'on' : ''}`} intensity={0.22}>
                <button className="cls-btn" onClick={() => { setLabel(c.label); setOffset(0); }} aria-pressed={c.label === label}>
                  <div className="cls-top"><span className={`fam ${c.family}`}>{c.family}</span><span className="cls-count">{c.count}</span></div>
                  <h3>{c.title}</h3>
                  <code className="cls-folder">{c.folder}</code>
                  <p>{c.explain}</p>
                  <div className="cls-split">train {c.split.train ?? '-'} · test {c.split.test ?? '-'} · hand-written {c.handwritten}</div>
                </button>
              </SpotlightCard>
            </FadeContent>
          ))}
        </div>
      </div>

      <div className="section-light browser">
        <div className="container">
          <div className="br-head">
            <div>
              <span className="chip">Sample browser</span>
              <h2>{cls?.title}</h2>
              <p className="br-sub">{cls?.explain}</p>
            </div>
            <div className="pager">
              <button className="btn-flat dark" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>← Prev</button>
              <span>{page ? `${offset + 1}–${Math.min(offset + PAGE, page.total)} of ${page.total}` : '…'}</span>
              <button className="btn-flat dark" disabled={!page || offset + PAGE >= page.total} onClick={() => setOffset(offset + PAGE)}>Next →</button>
            </div>
          </div>

          {!page && <div className="empty dark"><span className="loader" /></div>}
          {page && (
            <>
              <div className="sel-row">
                {page.samples.map((s, i) => (
                  <button key={s.sample_id} className={`sel-chip2 ${i === sel ? 'on' : ''}`} onClick={() => setSel(i)}>{s.sample_id.split('_').pop()}</button>
                ))}
              </div>
              {sample && (
                <div className="br-grid fade-in" key={sample.sample_id}>
                  <div>
                    <div className="br-label"><b>Training sample</b> <code>{sample.file}</code> <span className={`badge ${sample.split === 'test' ? 'partial' : 'ok'}`}>{sample.split}</span></div>
                    <Code source={sample.source} mark={(l, n) => n === sample.error_line || !origSet.has(l.trim())} markClass="bad" />
                    <div className="br-meta">
                      <div><span>Compiler says</span><code>{sample.compiler_message}</code></div>
                      <div><span>Injected fault</span><code>{sample.mutation}</code></div>
                      <div><span>Origin</span><code>{sample.seed_id}</code></div>
                    </div>
                    <button className="btn btn-sm" onClick={tryInStudio}>Open in Studio</button>
                  </div>
                  <div>
                    <div className="br-label"><b>Ground truth</b> <code>datasets/seeds/valid/{sample.seed_id}.mc</code></div>
                    <Code source={sample.original} mark={(l) => !corrSet.has(l.trim())} markClass="good" />
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
