import React, { useEffect, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import CountUp from '../reactbits/CountUp.jsx';
import SpotlightCard from '../reactbits/SpotlightCard.jsx';
import FadeContent from '../reactbits/FadeContent.jsx';
import { api } from '../api.js';
import { SHORT, featureLabel, pct } from '../lib/format.js';
import './dashboard.css';

const C = { ml: '#5423E7', rule: '#E7D623', mint: '#2CF7A4', coral: '#FF6B8B', ink: '#0A041A', grid: 'rgba(84,35,231,0.12)' };
const axis = { fontSize: 11, fill: '#4A4A4F', fontFamily: 'DM Sans Variable, sans-serif' };

function Kpi({ title, ml, base, sub, decimals = 1 }) {
  const delta = base != null ? (ml - base) * 100 : null;
  return (
    <SpotlightCard theme="light" className="kpi" intensity={0.2}>
      <div className="kpi-title">{title}</div>
      <div className="kpi-num"><CountUp to={+(ml * 100).toFixed(decimals)} decimals={decimals} suffix="%" duration={1.6} trigger="load" /></div>
      {base != null && (
        <div className="kpi-cmp">
          <span>rule baseline <b>{pct(base)}</b></span>
          <span className="kpi-delta">+{delta.toFixed(1)} pts</span>
        </div>
      )}
      <div className="kpi-sub">{sub}</div>
    </SpotlightCard>
  );
}

function Card({ title, sub, children, className = '' }) {
  return (
    <FadeContent blur duration={500}>
      <section className={`card dcard ${className}`}>
        <h3>{title}</h3>
        {sub && <p className="dsub">{sub}</p>}
        {children}
      </section>
    </FadeContent>
  );
}

function Confusion({ data }) {
  const { labels, matrix } = data;
  const [hover, setHover] = useState(null);
  return (
    <div className="cm-wrap">
      <div className="cm" style={{ gridTemplateColumns: `128px repeat(${labels.length}, 1fr)` }}>
        <div />
        {labels.map((l) => <div key={l} className="cm-col" title={l}><span>{SHORT[l]}</span></div>)}
        {matrix.map((row, i) => {
          const sum = row.reduce((a, b) => a + b, 0) || 1;
          return (
            <React.Fragment key={labels[i]}>
              <div className="cm-row" title={labels[i]}>{SHORT[labels[i]]}</div>
              {row.map((v, j) => {
                const f = v / sum;
                const diag = i === j;
                const bg = v === 0 ? 'transparent' : diag ? `rgba(84,35,231,${0.18 + f * 0.82})` : `rgba(255,107,139,${0.35 + f * 0.65})`;
                return (
                  <div key={j} className={`cm-cell ${diag ? 'diag' : ''}`} style={{ background: bg, color: v && (diag ? f > 0.5 : f > 0.5) ? '#fff' : C.ink }}
                    onMouseEnter={() => setHover({ i, j, v })} onMouseLeave={() => setHover(null)}
                    title={`actual: ${labels[i]}\npredicted: ${labels[j]}\ncount: ${v}`}>{v || ''}</div>
                );
              })}
            </React.Fragment>
          );
        })}
      </div>
      <div className="cm-foot">
        {hover ? <>actual <b>{SHORT[labels[hover.i]]}</b> → predicted <b>{SHORT[labels[hover.j]]}</b>: {hover.v}</> : 'rows = actual cause · columns = predicted cause · violet diagonal = correct · red = confusions'}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState(null);
  const [live, setLive] = useState(null);

  useEffect(() => { api.model().then(setD).catch((e) => setErr(e.message)); }, []);
  useEffect(() => {
    let alive = true;
    const tick = () => api.session().then((s) => alive && setLive(s)).catch(() => {});
    tick();
    const t = setInterval(tick, 4000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  if (err) return <div className="container page-head"><h1>Dashboard</h1><div className="banner bad">API unreachable: {err}</div></div>;
  if (!d) return <div className="container page-head"><h1>Dashboard</h1><div className="empty"><span className="loader" /> Loading model metrics…</div></div>;
  if (!d.metrics) return <div className="container page-head"><h1>Dashboard</h1><div className="banner warn">No trained model found. Run <code>python -m ml.train</code> in the backend folder.</div></div>;

  const m = d.metrics;
  const re = d.repair_eval;
  const base = m.baseline;
  const hw = m.handwritten;
  const models = m.models.map((x) => ({
    name: x.name.replace('Logistic Regression', 'Logistic Reg.').replace('Gradient Boosting', 'Grad. Boosting'),
    'CV macro-F1': x.cv_macro_f1, 'Test accuracy': x.test_accuracy,
  }));
  const perClass = m.test.per_class.map((c, i) => ({
    name: SHORT[c.label], ML: c.f1, 'Rule baseline': base.test.per_class[i].f1,
  }));
  const imp = m.feature_importance.slice(0, 12).map((f) => ({ name: featureLabel(f.feature), value: f.importance }));
  const repair = re ? re.ml.per_label.map((c, i) => ({
    name: SHORT[c.label], 'ML verified': c.verified_fix_rate, 'Baseline verified': re.baseline.per_label[i].verified_fix_rate, 'ML exact': c.exact_recovery_rate,
  })) : [];
  const dist = Object.entries(m.dataset.per_label_split).map(([k, v]) => ({ name: SHORT[k], Train: v.train, Test: v.test }));
  const rel = m.reliability.filter((b) => b.n > 0).map((b) => ({ name: b.range, Accuracy: b.accuracy, n: b.n }));
  const byLabel = live ? Object.entries(live.by_label).map(([k, v]) => ({ name: SHORT[k] || k, count: v })).sort((a, b) => b.count - a.count) : [];

  return (
    <div className="dash">
      <div className="container page-head">
        <span className="eyebrow">Model · {m.selected_model} · trained {new Date(m.trained_at).toLocaleDateString()}</span>
        <h1 style={{ marginTop: 16 }}>Model <span className="hl">Dashboard</span></h1>
        <p>How well does the ML layer diagnose compiler errors - measured on {m.dataset.n_test} held-out programs, {hw?.n ?? 0} hand-written ones, and end-to-end against the real compiler.</p>
      </div>

      <div className="container kpis">
        <Kpi title="Cause accuracy" ml={m.test.accuracy} base={base.test.accuracy} sub={`${m.dataset.n_test} held-out programs · 12 causes`} />
        <Kpi title="Macro F1" ml={m.test.macro_f1} base={base.test.macro_f1} sub="every cause weighted equally" />
        <Kpi title="Verified fix rate" ml={re?.ml.overall.verified_fix_rate ?? 0} base={re?.baseline.overall.verified_fix_rate} sub="top-ranked fix recompiles cleanly" />
        {hw && <Kpi title="Hand-written set" ml={hw.accuracy} base={base.handwritten?.accuracy} sub={`${hw.n} programs unlike the generator`} />}
      </div>

      <div className="section-light dash-body">
        <div className="container dgrid">
          <Card title="Model comparison" sub="Four classifiers, 5-fold cross-validation grouped by seed program (no leakage). Near-ties are broken by log-loss - the quality of the confidence the UI displays." className="span2">
            <div className="two">
              <div style={{ height: 260 }}>
                <ResponsiveContainer>
                  <BarChart data={models} margin={{ top: 8, right: 8, left: -14, bottom: 0 }}>
                    <CartesianGrid stroke={C.grid} vertical={false} />
                    <XAxis dataKey="name" tick={axis} /><YAxis domain={[0.9, 1]} tick={axis} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                    <Tooltip formatter={(v) => pct(v, 2)} /><Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="CV macro-F1" fill={C.ml} radius={[6, 6, 0, 0]} /><Bar dataKey="Test accuracy" fill={C.mint} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <table className="mtable">
                <thead><tr><th>Model</th><th>CV F1</th><th>Test acc</th><th>Log-loss</th><th>Train</th></tr></thead>
                <tbody>
                  {m.models.map((x) => (
                    <tr key={x.name} className={x.name === m.selected_model ? 'sel' : ''}>
                      <td>{x.name}{x.name === m.selected_model && <span className="chip sel-chip">selected</span>}</td>
                      <td>{pct(x.cv_macro_f1, 2)}</td><td>{pct(x.test_accuracy, 2)}</td><td>{x.test_log_loss}</td><td>{x.train_seconds}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="ML vs hand-written rules - F1 per cause" sub="The rule baseline reads the same compiler facts with first-match if/else rules." className="span2">
            <div style={{ height: 330 }}>
              <ResponsiveContainer>
                <BarChart data={perClass} layout="vertical" margin={{ left: 36, right: 12 }}>
                  <CartesianGrid stroke={C.grid} horizontal={false} />
                  <XAxis type="number" domain={[0, 1]} tick={axis} tickFormatter={(v) => `${v * 100}%`} /><YAxis type="category" dataKey="name" tick={axis} width={110} />
                  <Tooltip formatter={(v) => pct(v, 1)} /><Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="ML" fill={C.ml} radius={[0, 5, 5, 0]} barSize={9} /><Bar dataKey="Rule baseline" fill={C.rule} radius={[0, 5, 5, 0]} barSize={9} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Confusion matrix" sub={`Held-out test set · ${m.dataset.n_test} programs`}>
            <Confusion data={m.test.confusion} />
          </Card>

          <Card title="What the model looks at" sub="Permutation importance: accuracy lost when a feature is shuffled.">
            <div style={{ height: 380 }}>
              <ResponsiveContainer>
                <BarChart data={imp} layout="vertical" margin={{ left: 40, right: 14 }}>
                  <CartesianGrid stroke={C.grid} horizontal={false} />
                  <XAxis type="number" tick={axis} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} /><YAxis type="category" dataKey="name" tick={axis} width={170} />
                  <Tooltip formatter={(v) => pct(v, 1)} />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={14}>{imp.map((_, i) => <Cell key={i} fill={i < 3 ? C.ml : '#8E78F2'} />)}</Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {re && (
            <Card title="End-to-end repair outcomes" sub="Full engine on held-out programs: features → classifier → candidates → compiler validation. 'Exact' means the fix reproduces the original program token-for-token." className="span2">
              <div className="rtiles">
                {[['Label accuracy', re.ml.overall.label_accuracy, re.baseline.overall.label_accuracy],
                  ['Verified fix', re.ml.overall.verified_fix_rate, re.baseline.overall.verified_fix_rate],
                  ['Exact recovery', re.ml.overall.exact_recovery_rate, re.baseline.overall.exact_recovery_rate]].map(([t, a, b]) => (
                  <div className="rtile" key={t}><span>{t}</span><b>{pct(a)}</b><small>rules {pct(b)} · <em>+{((a - b) * 100).toFixed(1)} pts</em></small></div>
                ))}
              </div>
              <div style={{ height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={repair} margin={{ left: -14, right: 8, bottom: 30 }}>
                    <CartesianGrid stroke={C.grid} vertical={false} />
                    <XAxis dataKey="name" tick={{ ...axis, fontSize: 10 }} interval={0} angle={-25} textAnchor="end" height={60} />
                    <YAxis domain={[0, 1]} tick={axis} tickFormatter={(v) => `${v * 100}%`} />
                    <Tooltip formatter={(v) => pct(v, 1)} /><Legend wrapperStyle={{ fontSize: 12 }} verticalAlign="top" />
                    <Bar dataKey="ML verified" fill={C.ml} radius={[5, 5, 0, 0]} /><Bar dataKey="Baseline verified" fill={C.rule} radius={[5, 5, 0, 0]} /><Bar dataKey="ML exact" fill={C.mint} radius={[5, 5, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          <Card title="Is the confidence honest?" sub="Accuracy of the top prediction, bucketed by the confidence the model reported.">
            <div style={{ height: 230 }}>
              <ResponsiveContainer>
                <BarChart data={rel} margin={{ left: -14, right: 8 }}>
                  <CartesianGrid stroke={C.grid} vertical={false} /><XAxis dataKey="name" tick={axis} /><YAxis domain={[0, 1]} tick={axis} tickFormatter={(v) => `${v * 100}%`} />
                  <Tooltip formatter={(v, n, p) => [`${pct(v, 1)} (n=${p.payload.n})`, 'accuracy']} />
                  <Bar dataKey="Accuracy" fill={C.ml} radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Dataset composition" sub={`${m.dataset.n_samples} labelled programs from ${m.dataset.n_seeds} valid seeds, split by seed.`}>
            <div style={{ height: 230 }}>
              <ResponsiveContainer>
                <BarChart data={dist} margin={{ left: -14, right: 8, bottom: 28 }}>
                  <CartesianGrid stroke={C.grid} vertical={false} /><XAxis dataKey="name" tick={{ ...axis, fontSize: 9 }} interval={0} angle={-30} textAnchor="end" height={56} />
                  <YAxis tick={axis} /><Tooltip /><Legend wrapperStyle={{ fontSize: 12 }} verticalAlign="top" />
                  <Bar dataKey="Train" stackId="a" fill={C.ml} /><Bar dataKey="Test" stackId="a" fill={C.mint} radius={[5, 5, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Live session" sub="Counters from this API process - compile something in the Studio and watch them move." className="span2">
            {live ? (
              <div className="live">
                <div className="ltiles">
                  <div><b>{live.compiles}</b><span>compiles</span></div>
                  <div><b>{live.failed}</b><span>failed</span></div>
                  <div><b>{live.diagnoses}</b><span>diagnoses</span></div>
                  <div><b>{live.autofixes}</b><span>auto-fixes ({live.autofix_ok} ok)</span></div>
                  <div><b>{live.compiles ? (live.stage_ms.parser / live.compiles).toFixed(2) : '0'} ms</b><span>avg parse</span></div>
                </div>
                <div style={{ height: 200 }}>
                  {byLabel.length === 0 ? <div className="empty dark">No diagnoses yet.</div> : (
                    <ResponsiveContainer>
                      <BarChart data={byLabel} layout="vertical" margin={{ left: 30 }}>
                        <XAxis type="number" tick={axis} allowDecimals={false} /><YAxis type="category" dataKey="name" tick={axis} width={110} /><Tooltip />
                        <Bar dataKey="count" fill={C.ml} radius={[0, 6, 6, 0]} barSize={14} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            ) : <div className="empty dark">Waiting for the API…</div>}
          </Card>
        </div>
      </div>
    </div>
  );
}
