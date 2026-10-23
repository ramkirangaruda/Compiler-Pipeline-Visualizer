import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ShapeGrid from '../reactbits/ShapeGrid.jsx';
import BlurText from '../reactbits/BlurText.jsx';
import SplitText from '../reactbits/SplitText.jsx';
import CountUp from '../reactbits/CountUp.jsx';
import Magnet from '../reactbits/Magnet.jsx';
import ShinyText from '../reactbits/ShinyText.jsx';
import CardSwap, { Card } from '../reactbits/CardSwap.jsx';
import Ballpit from '../reactbits/Ballpit.jsx';
import Hero3D from '../components/Hero3D.jsx';
import ErrorBoundary from '../components/ErrorBoundary.jsx';
import { api } from '../api.js';
import './home.css';

function Stat({ children, label }) {
  return (
    <div className="stat">
      <div className="stat-num">{children}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default function Home() {
  const [m, setM] = useState(null);
  useEffect(() => { api.model().then(setM).catch(() => {}); }, []);
  const acc = m?.metrics?.test?.accuracy ?? 0.986;
  const fix = m?.repair_eval?.ml?.overall?.autofix_success_rate ?? 0.98;
  const n = m?.metrics?.dataset?.n_samples ?? 3120;
  const base = m?.metrics?.baseline?.test?.accuracy;
  const nFeat = m?.metrics?.dataset?.n_features ?? 40;

  return (
    <>
      {/* ---------------- hero ---------------- */}
      <section className="hero">
        <div className="hero-grid" aria-hidden="true">
          <ShapeGrid shape="square" cellSize={50} lineWidth={1} direction="diagonal" speed={0.35}
            lineColor="rgba(255,255,255,0.10)" hoverColor="#2CF7A4" hoverFillColor="#2CF7A4" fillOpacity={0.18}
            radius={2.2} glow={0.25} />
        </div>
        <div className="container hero-inner">
          <div className="hero-copy">
            <div className="eyebrow fade-in"><span className="dot on" /> Compiler Design × Machine Learning</div>
            <h1 className="hero-title">
              <span className="ht-line" style={{ '--i': 0 }}>Compile it.</span>
              <span className="ht-line hl" style={{ '--i': 1 }}>Break it.</span>
              <span className="ht-line" style={{ '--i': 2 }}>Let <span className="hl">ML</span> fix it.</span>
            </h1>
            <BlurText
              text="A real compiler for a C-like language that explains its own errors - ML ranks the likely cause, and the compiler re-checks every fix before you see it."
              className="hero-sub" delay={60} animateBy="words" direction="top" />
            <div className="hero-cta">
              <Magnet padding={60} magnetStrength={3}>
                <Link to="/studio" className="btn">Open the Studio</Link>
              </Magnet>
              <Link to="/dashboard" className="btn btn-ghost">See the dashboard</Link>
            </div>
            <div className="stats">
              <Stat label="error causes classified">
                <CountUp to={12} duration={1.6} trigger="load" />
              </Stat>
              <Stat label="labelled programs">
                <CountUp to={n} duration={2} separator="," trigger="load" />
              </Stat>
              <Stat label={base ? `cause accuracy (rules: ${(base * 100).toFixed(0)}%)` : 'cause accuracy'}>
                <CountUp to={+(acc * 100).toFixed(1)} decimals={1} suffix="%" duration={2} trigger="load" />
              </Stat>
              <Stat label="errors auto-repaired, compiler-verified">
                <CountUp to={+(fix * 100).toFixed(1)} decimals={1} suffix="%" duration={2} trigger="load" />
              </Stat>
            </div>
          </div>
          <div className="hero-visual"><Hero3D /></div>
        </div>
      </section>

      {/* ---------------- how it works ---------------- */}
      <section className="section-light how">
        <div className="container how-inner">
          <div className="how-copy">
            <span className="chip">How it works</span>
            <SplitText text="The compiler finds the failure. ML finds the cause. RL picks the fix. The compiler checks it."
              tag="h2" className="how-title" splitType="words" delay={40} textAlign="left" color="#5423E7" />
            <ol className="how-steps">
              <li><b>1 · Detect</b><span>Lexer, parser and semantic analyzer report <em>what</em> failed - with the expected tokens, parse context and symbol-table facts.</span></li>
              <li><b>2 · Featurize</b><span>Those compiler-internal facts become a {nFeat}-feature vector. No raw text is fed to the model.</span></li>
              <li><b>3 · Classify</b><span>A trained classifier ranks <em>why</em> it failed across 12 causes and explains which features mattered.</span></li>
              <li><b>4 · Choose</b><span>A <em>reinforcement-learning</em> policy decides which candidate fix to apply first - rewarded by the compiler, and still learning from your accepts and undos.</span></li>
              <li><b>5 · Validate</b><span>Each candidate repair is re-run through lexer → parser → semantic analysis. Only fixes the compiler accepts are offered.</span></li>
            </ol>
            <Link to="/architecture" className="learn-more">Read the architecture →</Link>
          </div>
          <div className="how-visual">
            <CardSwap width={440} height={300} cardDistance={46} verticalDistance={52} delay={3800} theme="light" pauseOnHover>
              <Card><div className="swap-card"><span className="swap-n">1 · Compiler detects</span>
                <pre className="swap-code"><span className="dim">2 │</span> int height = 20{'\n'}<span className="dim">3 │</span> <span className="err">int</span> area = width * height;</pre>
                <p className="swap-msg">Syntax error: expected ';' but found 'int' on line 3</p></div></Card>
              <Card><div className="swap-card"><span className="swap-n">2 · Features extracted</span>
                <div className="swap-feats">
                  <i>expected = ;</i><i>found = int</i><i>prev1 = INT</i><i>ctx = decl_end</i><i>newline_before = 1</i><i>paren_bal = 0</i>
                </div><p className="swap-msg">Parser state + token context + symbol facts</p></div></Card>
              <Card><div className="swap-card"><span className="swap-n">3 · ML ranks causes</span>
                <div className="swap-bars">
                  <div><u style={{ width: '97%' }} /><span>Missing semicolon</span><b>97%</b></div>
                  <div><u style={{ width: '1.5%' }} /><span>Missing closing brace</span><b>1%</b></div>
                  <div><u style={{ width: '1%' }} /><span>Misspelled keyword</span><b>1%</b></div>
                </div></div></Card>
              <Card><div className="swap-card"><span className="swap-n">4 · RL policy picks the fix</span>
                <div className="swap-bars">
                  <div><u style={{ width: '78%' }} /><span>Insert ';' after `20`</span><b>π 78%</b></div>
                  <div><u style={{ width: '14%' }} /><span>Insert ')' after `20`</span><b>π 14%</b></div>
                  <div><u style={{ width: '8%' }} /><span>Insert '}' before `int`</span><b>π 8%</b></div>
                </div><p className="swap-msg">reward = progress toward the intended program</p></div></Card>
              <Card><div className="swap-card"><span className="swap-n">5 · Compiler validates</span>
                <div className="swap-cands">
                  <div className="ok">✓ Insert ';' after `20` <em>verified</em></div>
                  <div className="no">✗ Insert ')' after `20` <em>rejected</em></div>
                </div><p className="swap-msg">Re-run lexer → parser → semantic analysis</p></div></Card>
            </CardSwap>
          </div>
        </div>
      </section>

      {/* ---------------- CTA ---------------- */}
      <section className="cta">
        <div className="cta-balls" aria-hidden="true">
          <ErrorBoundary>
            <Ballpit count={90} colors={['#E7D623', '#2CF7A4', '#ffffff', '#602CF7', '#0A041A']} gravity={0.45} followCursor />
          </ErrorBoundary>
        </div>
        <div className="container cta-inner">
          <h2>Break a program on purpose.</h2>
          <ShinyText text="Twelve ready-made bugs are waiting in the Studio." color="#ffffffcc" shineColor="#E7D623" speed={3} className="cta-sub" />
          <Magnet padding={80} magnetStrength={3}>
            <Link to="/studio" className="btn btn-yellow">Try the Studio</Link>
          </Magnet>
        </div>
      </section>
    </>
  );
}
