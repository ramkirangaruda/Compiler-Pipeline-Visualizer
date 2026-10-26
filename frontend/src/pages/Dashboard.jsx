import React, { useEffect, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import CountUp from '../reactbits/CountUp.jsx';
import SpotlightCard from '../reactbits/SpotlightCard.jsx';
import { api } from '../api.js';
import { SHORT, pct } from '../lib/format.js';
import './dashboard.css';

const C = { ml: '#5423E7', rule: '#E7D623', mint: '#2CF7A4', gray: '#A3B3C2', grid: 'rgba(84,35,231,0.12)' };
const axis = { fontSize: 11, fill: '#4A4A4F', fontFamily: 'DM Sans Variable, sans-serif' };
const pctTick = (v) => `${Math.round(v * 100)}%`;

const OP_NAME = {
  delete_token: 'Delete a token', insert_token: 'Insert a token', replace_token: 'Replace a token', swap_tokens: 'Swap two tokens',
  delete_line: 'Delete a line', duplicate_line: 'Duplicate a line', delete_char: 'Delete a character', insert_char: 'Insert a character',
  typo_ident: 'Misspell a name', drop_include: 'Drop an #include', truncate: 'Cut the file short', wrong_type: 'Change a type',
};

function Kpi({ title, value, base, baseLabel, sub }) {
  const delta = base == null ? null : (value - base) * 100;
  return (
    <SpotlightCard theme="light" className="kpi" intensity={0.2}>
      <div className="kpi-title">{title}</div>
      <div className="kpi-num"><CountUp to={+(value * 100).toFixed(1)} decimals={1} suffix="%" duration={1.4} trigger="load" /></div>
      {base != null && (
        <div className="kpi-cmp">
          <span>{baseLabel} <b>{pct(base)}</b></span>
          <span className={`kpi-delta ${delta < 0 ? 'neg' : ''}`}>{delta >= 0 ? '+' : ''}{delta.toFixed(1)} pts</span>
        </div>
      )}
      <div className="kpi-sub">{sub}</div>
    </SpotlightCard>
  );
}

function Chart({ title, note, height = 300, children }) {
  return (
    <section className="chart-card">
      <h3>{title}</h3>
      {note && <p className="chart-note">{note}</p>}
      <div style={{ height }}>
        <ResponsiveContainer>{children}</ResponsiveContainer>
      </div>
    </section>
  );
}

export default function Dashboard() {
  const [d, setD] = useState(null);
  const [rl, setRl] = useState(null);
  const [st, setSt] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.model().then(setD).catch((e) => setErr(e.message));
    api.rl().then(setRl).catch(() => {});
    api.stress().then((x) => setSt(x.stress)).catch(() => {});
  }, []);

  const head = (
    <div className="container page-head">
      <h1>Dashboard</h1>
      <p>How well the system diagnoses and repairs errors, measured on programs it never saw during training.</p>
    </div>
  );
  if (err) return <div>{head}<div className="container"><div className="banner bad">API unreachable: {err}</div></div></div>;
  if (!d) return <div>{head}<div className="container empty"><span className="loader" /> Loading…</div></div>;
  if (!d.metrics) return <div>{head}<div className="container"><div className="banner warn">No trained model found. Run <code>python -m ml.train</code> in the backend folder.</div></div></div>;

  const m = d.metrics;
  const re = d.repair_eval;
  const hw = m.handwritten;
  const ev = rl?.metrics?.eval;

  const perCause = m.test.per_class.map((c, i) => ({ name: SHORT[c.label] || c.label, ML: c.f1, Rules: m.baseline.test.per_class[i].f1 }));
  const models = m.models.map((x) => ({ name: x.name.replace('Logistic Regression', 'Logistic Reg.').replace('Gradient Boosting', 'Grad. Boosting'), f1: x.cv_macro_f1, selected: x.name === m.selected_model }));
  const smooth = (key, i, w = 5) => {
    const win = rl.metrics.curve.slice(Math.max(0, i - w + 1), i + 1);
    return win.reduce((a, x) => a + x[key], 0) / win.length;
  };
  const curve = rl?.metrics?.curve.map((c, i) => ({ episode: c.episode, reward: smooth('avg_return', i) }));
  const byFaults = ev && ['1', '2', '3'].map((k) => ({
    name: `${k} fault${k === '1' ? '' : 's'}`,
    Heuristic: ev.heuristic.by_faults[k].exact_rate, 'RL policy': ev.rl.by_faults[k].exact_rate, Random: ev.random.by_faults[k].exact_rate,
  }));
  const ci = ev?.paired_vs_heuristic?.exact_rate_diff;
  const stressBars = st && Object.entries(st.per_operator).map(([k, v]) => ({ name: OP_NAME[k] || k, Repaired: v.repaired, 'Exactly as before': v.exact }));

  return (
    <div>
      {head}
      <div className="container kpis">
        <Kpi title="Cause accuracy" value={m.test.accuracy} base={m.baseline.test.accuracy} baseLabel="rules" sub={`${m.dataset.n_test} held-out programs`} />
        {re && <Kpi title="Auto-fix success" value={re.ml.overall.autofix_success_rate} base={re.baseline.overall.autofix_success_rate} baseLabel="rules" sub="ends in a program that compiles" />}
        {hw && <Kpi title="Hand-written programs" value={hw.accuracy} base={m.baseline.handwritten.accuracy} baseLabel="rules" sub={`${hw.n} programs written by hand`} />}
        {st && <Kpi title="Any error, repaired" value={st.repaired} sub={`${st.n} randomly damaged programs gcc rejects`} />}
      </div>

      <div className="section-light dash-body">
        <div className="container charts">
          <Chart title="Accuracy per error type: ML vs hand-written rules" height={380}>
            <BarChart data={perCause} layout="vertical" margin={{ left: 30, right: 12 }}>
              <CartesianGrid stroke={C.grid} horizontal={false} />
              <XAxis type="number" domain={[0, 1]} tick={axis} tickFormatter={pctTick} />
              <YAxis type="category" dataKey="name" tick={axis} width={110} />
              <Tooltip formatter={(v) => pct(v, 1)} /><Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="ML" fill={C.ml} radius={[0, 5, 5, 0]} barSize={9} />
              <Bar dataKey="Rules" fill={C.rule} radius={[0, 5, 5, 0]} barSize={9} />
            </BarChart>
          </Chart>

          {st && (
            <Chart title="Beyond the trained causes: random damage, judged by gcc" height={420}
              note={`${st.n} broken programs; ${pct(st.repaired, 0)} end in a program gcc builds, ${pct(st.exact_recovery, 0)} come back exactly as they were. A repair counts only if gcc accepts it.`}>
              <BarChart data={stressBars} layout="vertical" margin={{ left: 30, right: 12 }}>
                <CartesianGrid stroke={C.grid} horizontal={false} />
                <XAxis type="number" domain={[0, 1]} tick={axis} tickFormatter={pctTick} />
                <YAxis type="category" dataKey="name" tick={axis} width={120} />
                <Tooltip formatter={(v) => pct(v, 1)} /><Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="Repaired" fill={C.ml} radius={[0, 5, 5, 0]} barSize={9} />
                <Bar dataKey="Exactly as before" fill={C.mint} radius={[0, 5, 5, 0]} barSize={9} />
              </BarChart>
            </Chart>
          )}

          <Chart title="Four models compared" note="Cross-validated macro-F1. Gradient Boosting was chosen for the most trustworthy confidence." height={380}>
            <BarChart data={models} margin={{ left: -10, right: 8, top: 10 }}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="name" tick={axis} /><YAxis domain={[0.9, 1]} tick={axis} tickFormatter={pctTick} />
              <Tooltip formatter={(v) => pct(v, 2)} />
              <Bar dataKey="f1" name="Macro-F1" radius={[8, 8, 0, 0]} barSize={46}>
                {models.map((x) => <Cell key={x.name} fill={x.selected ? C.ml : C.gray} />)}
              </Bar>
            </BarChart>
          </Chart>

          {ev && (
            <>
              <Chart title="Reinforcement learning: reward while training" note={`${rl.metrics.config.episodes.toLocaleString()} episodes, 250-episode moving average`} height={300}>
                <LineChart data={curve} margin={{ left: -10, right: 10, top: 10 }}>
                  <CartesianGrid stroke={C.grid} vertical={false} />
                  <XAxis dataKey="episode" tick={axis} /><YAxis tick={axis} domain={['auto', 'auto']} tickFormatter={(v) => v.toFixed(1)} />
                  <Tooltip formatter={(v) => v.toFixed(2)} labelFormatter={(l) => `episode ${l}`} />
                  <Line type="monotone" dataKey="reward" name="Average reward" stroke={C.ml} strokeWidth={3} dot={false} />
                </LineChart>
              </Chart>

              <Chart title="RL policy vs heuristic vs random"
                note={ci ? `Exact recovery on unseen programs. RL gain over the heuristic: ${ci.mean >= 0 ? '+' : ''}${(ci.mean * 100).toFixed(1)} pts (95% CI ${(ci.ci_low * 100).toFixed(1)} to ${(ci.ci_high * 100).toFixed(1)}).` : 'Exact recovery on unseen programs.'}
                height={300}>
                <BarChart data={byFaults} margin={{ left: -10, right: 8, top: 10 }}>
                  <CartesianGrid stroke={C.grid} vertical={false} />
                  <XAxis dataKey="name" tick={axis} /><YAxis domain={[0, 0.8]} tick={axis} tickFormatter={pctTick} />
                  <Tooltip formatter={(v) => pct(v, 1)} /><Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="Heuristic" fill={C.rule} radius={[5, 5, 0, 0]} />
                  <Bar dataKey="RL policy" fill={C.ml} radius={[5, 5, 0, 0]} />
                  <Bar dataKey="Random" fill={C.gray} radius={[5, 5, 0, 0]} />
                </BarChart>
              </Chart>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
