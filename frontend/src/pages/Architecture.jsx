import React from 'react';
import './architecture.css';

function Diagram() {
  const box = (x, y, w, h, t, s, cls = '') => (
    <g className={`ab ${cls}`} transform={`translate(${x},${y})`}>
      <rect width={w} height={h} rx="16" />
      <text x={w / 2} y={h / 2 - (s ? 3 : -4)} textAnchor="middle" className="ab-t">{t}</text>
      {s && <text x={w / 2} y={h / 2 + 14} textAnchor="middle" className="ab-s">{s}</text>}
    </g>
  );
  const arrow = (d, cls = '') => <path d={d} className={`aa ${cls}`} markerEnd="url(#arr)" />;
  return (
    <svg viewBox="0 0 1000 530" className="arch-svg" role="img" aria-label="Architecture diagram">
      <defs>
        <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#ffffff" /></marker>
      </defs>
      <text x="10" y="22" className="lane">COMPILER (the backbone)</text>
      {box(10, 40, 120, 64, 'Source', 'C program', 'src')}
      {box(170, 40, 120, 64, 'Lexer', 'tokens')}
      {box(330, 40, 120, 64, 'Parser', 'AST + context')}
      {box(490, 40, 130, 64, 'Semantic', 'symbols, types', 'mint')}
      {box(660, 40, 120, 64, 'gcc', 'the judge', 'yellow')}
      {box(820, 40, 170, 64, 'Run', 'interpreter · trace', 'mint')}
      {arrow('M130,72 L168,72')}{arrow('M290,72 L328,72')}{arrow('M450,72 L488,72')}{arrow('M620,72 L658,72')}{arrow('M780,72 L818,72')}
      <text x="240" y="208" className="lane err">ON FAILURE: ML classifier + RL policy sit inside this loop</text>
      {arrow('M390,104 C390,165 125,150 125,220', 'err')}{arrow('M555,104 C555,175 175,168 175,220', 'err')}
      <text x="250" y="150" className="lbl err">error + compiler facts</text>
      {box(30, 222, 170, 76, 'Feature extractor', 'parse state · tokens · symbols', 'err')}
      {box(235, 222, 170, 76, 'ML classifier', '14 causes + confidence', 'ml')}
      {box(440, 222, 190, 76, 'Repair generator', 'own + gcc fix-its + search', 'mint')}
      {box(665, 222, 190, 76, 'RL policy', 'REINFORCE · picks the fix', 'rl')}
      {arrow('M200,260 L233,260', 'err')}{arrow('M405,260 L438,260', 'err')}{arrow('M630,260 L663,260', 'err')}
      {box(665, 380, 190, 76, 'gcc validator', 'rebuild every candidate', 'yellow')}
      {arrow('M760,298 L760,378', 'err')}
      {arrow('M855,418 C955,418 955,262 857,262', 'loop')}
      <text x="868" y="338" className="lbl loop">rejected →</text>
      <text x="868" y="353" className="lbl loop">next candidate</text>
      {box(440, 380, 170, 76, 'Verified fix', 'shown to the user', 'ok')}
      {arrow('M663,418 L612,418', 'err')}
      {box(205, 380, 190, 76, 'Auto-fix loop', 'apply best, re-compile', 'src')}
      {arrow('M438,418 L397,418', 'err')}
      {arrow('M205,418 C-12,430 -12,150 195,106', 'loop')}
      <text x="8" y="352" className="lbl loop">re-enter</text>
      <text x="8" y="367" className="lbl loop">at the Lexer</text>
      {arrow('M760,456 C760,500 960,500 960,470', 'loop')}
      <text x="990" y="522" textAnchor="end" className="lbl loop">user accepts (+1) or undoes (−1) a fix → the policy keeps learning</text>
    </svg>
  );
}

export default function Architecture() {
  return (
    <div>
      <div className="container page-head">
        <h1>Architecture</h1>
        <p>The compiler is the backbone. When it fails, ML finds the cause, reinforcement learning picks the fix, and the compiler checks it.</p>
      </div>
      <div className="container arch-wrap">
        <div className="panel arch-panel"><Diagram /></div>
      </div>
    </div>
  );
}
