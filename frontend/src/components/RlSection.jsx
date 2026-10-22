import React, { useEffect, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import FadeContent from '../reactbits/FadeContent.jsx';
import { api } from '../api.js';
import { pct } from '../lib/format.js';

const COLORS = { heuristic: '#E7D623', rl: '#5423E7', random: '#A3B3C2', mint: '#2CF7A4', grid: 'rgba(84,35,231,0.12)' };
const NAMES = { heuristic: 'Heuristic', rl: 'RL policy', random: 'Random' };
const axis = { fontSize: 11, fill: '#4A4A4F', fontFamily: 'DM Sans Variable, sans-serif' };

function Mdp({ mdp }) {
  const rows = [['State', mdp.state], ['Action', mdp.action], ['Reward', mdp.reward], ['Policy', mdp.policy], ['Algorithm', mdp.algorithm]];
  return (
    <div className="mdp">
      {rows.map(([k, v]) => <div key={k}><b>{k}</b><span>{v}</span></div>)}
    </div>
  );
}

function Online({ st, onReset }) {
  const h = st.history || [];
  return (
    <div className="online">
      <div className="ltiles">
        <div><b>{st.online_updates}</b><span>online updates</span></div>
        <div><b>{st.mean_reward == null ? '–' : st.mean_reward}</b><span>mean reward (+1 accept / −1 undo)</span></div>
        <div><b>{st.weight_shift}</b><span>weight shift from trained policy</span></div>
      </div>
      <div className="spark" aria-label="recent rewards">
        {h.length === 0 ? <span className="muted-dark">No feedback yet. In the Studio, apply a suggested fix (reward +1) or undo it (reward −1) and watch the policy change.</span>
          : h.map((r, i) => <i key={i} className={r > 0 ? 'up' : 'down'} style={{ height: 10 + Math.abs(r) * 18 }} />)}
      </div>
      <button className="btn btn-sm btn-dark" onClick={onReset} disabled={!st.online_updates}>Reset policy to trained weights</button>
    </div>
  );
}

export default function RlSection() {
  const [d, setD] = useState(null);
  const refresh = () => api.rl().then(setD).catch(() => {});
  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 4000);
    return () => clearInterval(t);
  }, []);
  if (!d?.metrics) return null;
  const m = d.metrics;
  const ev = m.eval;
  const order = ['heuristic', 'rl', 'random'];
  const bars = [
    { name: 'Exact recovery', ...Object.fromEntries(order.map((k) => [NAMES[k], ev[k].overall.exact_rate])) },
    { name: 'Compiles', ...Object.fromEntries(order.map((k) => [NAMES[k], ev[k].overall.success_rate])) },
  ];
  // 50-episode windows are noisy: show a 5-point (250-episode) moving average
  const smooth = (key, i, w = 5) => {
    const win = m.curve.slice(Math.max(0, i - w + 1), i + 1);
    return win.reduce((a, x) => a + x[key], 0) / win.length;
  };
  const curve = m.curve.map((c, i) => ({
    name: c.episode, avg_return: smooth('avg_return', i), exact_rate: smooth('exact_rate', i), success_rate: smooth('success_rate', i),
  }));
  const dExact = (ev.rl.overall.exact_rate - ev.heuristic.overall.exact_rate) * 100;
  const dDist = ev.heuristic.overall.mean_distance - ev.rl.overall.mean_distance;
  const maxW = Math.max(...m.top_weights.map((w) => Math.abs(w.weight)), 1);

  return (
    <>
      <FadeContent blur duration={500}>
        <section className="card dcard span2 rl-card">
          <div className="rl-head">
            <div>
              <span className="chip">Reinforcement learning</span>
              <h3>The fix-selection policy</h3>
              <p className="dsub">When several fixes are possible - and when a program has several faults - <em>which fix to apply first</em> is a sequential decision. A policy learns it by trial and error, rewarded by the compiler and by how close each step moves the program to what the author meant.</p>
            </div>
            <div className={`rl-verdict ${dExact >= 0 ? 'good' : 'bad'}`}>
              <b>{dExact >= 0 ? '+' : ''}{dExact.toFixed(1)} pts</b>
              <span>exact recovery vs heuristic ({ev.rl.overall.n} held-out multi-fault programs)</span>
            </div>
          </div>
          <Mdp mdp={m.mdp} />
          <div className="two rl-charts">
            <div>
              <h4 className="rl-h">Learning curve <small>{m.config.episodes.toLocaleString()} training episodes, 250-episode moving average</small></h4>
              <div style={{ height: 260 }}>
                <ResponsiveContainer>
                  <LineChart data={curve} margin={{ left: -10, right: 10, top: 6 }}>
                    <CartesianGrid stroke={COLORS.grid} vertical={false} />
                    <XAxis dataKey="name" tick={axis} /><YAxis yAxisId="l" domain={[0, 1]} tick={axis} tickFormatter={(v) => `${v * 100}%`} />
                    <YAxis yAxisId="r" orientation="right" tick={axis} />
                    <Tooltip formatter={(v, n) => (n === 'Avg return' ? v.toFixed(2) : pct(v, 0))} /><Legend wrapperStyle={{ fontSize: 12 }} />
                    <Line yAxisId="r" type="monotone" dataKey="avg_return" name="Avg return" stroke={COLORS.rl} strokeWidth={2.5} dot={false} />
                    <Line yAxisId="l" type="monotone" dataKey="exact_rate" name="Exact recovery" stroke={COLORS.mint} strokeWidth={2} dot={false} />
                    <Line yAxisId="l" type="monotone" dataKey="success_rate" name="Compiles" stroke={COLORS.heuristic} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div>
              <h4 className="rl-h">Held-out comparison <small>same programs, three ways of choosing</small></h4>
              <div style={{ height: 260 }}>
                <ResponsiveContainer>
                  <BarChart data={bars} margin={{ left: -10, right: 8, top: 6 }}>
                    <CartesianGrid stroke={COLORS.grid} vertical={false} /><XAxis dataKey="name" tick={axis} />
                    <YAxis domain={[0, 1]} tick={axis} tickFormatter={(v) => `${v * 100}%`} />
                    <Tooltip formatter={(v) => pct(v, 1)} /><Legend wrapperStyle={{ fontSize: 12 }} />
                    {order.map((k) => <Bar key={k} dataKey={NAMES[k]} fill={COLORS[k]} radius={[6, 6, 0, 0]} />)}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
          <div className="table-scroll">
            <table className="mtable">
              <thead><tr><th>Faults in program</th><th>Heuristic exact</th><th>RL exact</th><th>Heuristic distance</th><th>RL distance</th><th>RL steps</th></tr></thead>
              <tbody>
                {['1', '2', '3'].map((k) => (
                  <tr key={k}><td>{k} fault{k === '1' ? '' : 's'} (n={ev.rl.by_faults[k].n})</td>
                    <td>{pct(ev.heuristic.by_faults[k].exact_rate)}</td><td><b>{pct(ev.rl.by_faults[k].exact_rate)}</b></td>
                    <td>{ev.heuristic.by_faults[k].mean_distance}</td><td><b>{ev.rl.by_faults[k].mean_distance}</b></td><td>{ev.rl.by_faults[k].mean_steps}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          {ev.paired_vs_heuristic && (
            <p className="rl-note sig">
              <b>Is it just luck?</b> Paired bootstrap over the same {ev.rl.overall.n} programs, RL minus heuristic:{' '}
              exact recovery <b>{ev.paired_vs_heuristic.exact_rate_diff.mean >= 0 ? '+' : ''}{(ev.paired_vs_heuristic.exact_rate_diff.mean * 100).toFixed(1)} pts</b>{' '}
              (95% CI {(ev.paired_vs_heuristic.exact_rate_diff.ci_low * 100).toFixed(1)} to {(ev.paired_vs_heuristic.exact_rate_diff.ci_high * 100).toFixed(1)}),
              distance <b>{ev.paired_vs_heuristic.distance_diff.mean.toFixed(2)} tokens</b>{' '}
              (CI {ev.paired_vs_heuristic.distance_diff.ci_low.toFixed(2)} to {ev.paired_vs_heuristic.distance_diff.ci_high.toFixed(2)}) -{' '}
              {ev.paired_vs_heuristic.exact_rate_diff.significant && ev.paired_vs_heuristic.distance_diff.significant
                ? 'both intervals exclude zero, so the gain is statistically real - but modest.' : 'not conclusive.'}
            </p>
          )}
          <p className="rl-note">Distance = tokens still differing from the intended program (lower is better; heuristic → RL: {dDist >= 0 ? '−' : '+'}{Math.abs(dDist).toFixed(2)} on average). The original program is used only as a training reward - at run time the policy sees candidate features alone.</p>
        </section>
      </FadeContent>

      <FadeContent blur duration={500}>
        <section className="card dcard rl-card">
          <h3>What the policy learned</h3>
          <p className="dsub">Largest weights of the linear softmax policy (positive = prefer, negative = avoid).</p>
          <div className="weights">
            {m.top_weights.map((w) => (
              <div className="w-row" key={w.feature}>
                <span>{w.feature}</span>
                <span className="w-bar"><i className={w.weight >= 0 ? 'pos' : 'neg'} style={{ width: `${(Math.abs(w.weight) / maxW) * 100}%` }} /></span>
                <b>{w.weight > 0 ? '+' : ''}{w.weight}</b>
              </div>
            ))}
          </div>
        </section>
      </FadeContent>

      <FadeContent blur duration={500}>
        <section className="card dcard rl-card">
          <h3>Online learning from you</h3>
          <p className="dsub">Every fix you accept in the Studio is a +1 reward and every undo a −1; each one is a live policy-gradient step on the running policy (session-only, resettable).</p>
          <Online st={d.status} onReset={() => api.rlReset().then(refresh)} />
        </section>
      </FadeContent>
    </>
  );
}
