import React, { useEffect, useMemo, useRef, useState } from 'react';
import { hierarchy, tree as d3tree } from 'd3-hierarchy';
import { Canvas } from '@react-three/fiber';
import { Html, Line, OrbitControls } from '@react-three/drei';
import ErrorBoundary from '../ErrorBoundary.jsx';
import { astToTree, KIND_STYLE } from '../../lib/ast.js';

/* ------------------------------------------------------------------ AST 2D */
const trunc = (s, n = 15) => (s.length > n ? `${s.slice(0, n - 1)}…` : s);

function Tree2D({ root }) {
  const wrapRef = useRef(null);
  const layout = useMemo(() => {
    const h = hierarchy(root);
    d3tree().nodeSize([112, 84]).separation((a, b) => (a.parent === b.parent ? 1 : 1.15))(h);
    const nodes = h.descendants();
    const xs = nodes.map((d) => d.x);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const maxY = Math.max(...nodes.map((d) => d.y));
    return { nodes, links: h.links(), minX, width: maxX - minX + 140, height: maxY + 90 };
  }, [root]);

  const fit = useMemo(() => {
    const w = wrapRef.current?.clientWidth || 700;
    return Math.min(1, (w - 8) / layout.width);
  }, [layout]);
  const scale = fit;

  return (
    <div className="graph-wrap" ref={wrapRef}>
      <div className="graph-scroll">
        <svg width={layout.width * scale} height={layout.height * scale} viewBox={`0 0 ${layout.width} ${layout.height}`} role="img" aria-label="Abstract syntax tree">
          <g transform={`translate(${70 - layout.minX},34)`}>
            {layout.links.map((l, i) => (
              <path key={i} className="tlink" d={`M${l.source.x},${l.source.y + 14} C${l.source.x},${(l.source.y + l.target.y) / 2} ${l.target.x},${(l.source.y + l.target.y) / 2} ${l.target.x},${l.target.y - 14}`} />
            ))}
            {layout.nodes.map((d, i) => {
              const st = KIND_STYLE[d.data.kind] || KIND_STYLE.op;
              const label = trunc(d.data.label);
              const w = Math.max(44, label.length * 8.2 + 22);
              return (
                <g key={i} className="tnode" transform={`translate(${d.x},${d.y})`}>
                  <title>{`${d.data.label} · ${d.data.sub}${d.data.line ? ` · line ${d.data.line}` : ''}`}</title>
                  <rect x={-w / 2} y={-14} width={w} height={28} rx={9} fill={st.bg} />
                  <text textAnchor="middle" y={4} fill={st.fg} className="tlabel">{label}</text>
                  <text textAnchor="middle" y={27} className="tsub">{trunc(d.data.sub, 18)}</text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ AST 3D */
function Tree3D({ root }) {
  const { nodes, links, span } = useMemo(() => {
    const h = hierarchy(root);
    d3tree().nodeSize([1.15, 1.5])(h);
    const ns = h.descendants();
    const mean = (Math.min(...ns.map((d) => d.x)) + Math.max(...ns.map((d) => d.x))) / 2;
    const maxDepth = Math.max(...ns.map((d) => d.depth));
    const pos = new Map();
    ns.forEach((d, i) => {
      const z = d.depth === 0 ? 0 : ((i * 7) % 5 - 2) * 0.55;
      pos.set(d, [d.x - mean, -d.depth * 1.5 + (maxDepth * 1.5) / 2, z]);
    });
    const sp = Math.max(8, Math.max(...ns.map((d) => Math.abs(d.x - mean))) * 2, maxDepth * 1.5);
    return {
      nodes: ns.map((d) => ({ d, p: pos.get(d) })),
      links: h.links().map((l) => [pos.get(l.source), pos.get(l.target)]),
      span: sp,
    };
  }, [root]);
  const showAll = nodes.length <= 70;
  return (
    <div className="graph-3d">
      <ErrorBoundary fallback={<div className="empty">WebGL is unavailable - switch to the 2D view.</div>}>
        <Canvas camera={{ position: [0, 0, Math.min(40, span * 0.85 + 6)], fov: 50 }} dpr={[1, 2]}>
          <ambientLight intensity={1.2} />
          <directionalLight position={[6, 8, 8]} intensity={2} />
          {links.map((pts, i) => <Line key={i} points={pts} color="#b9a8ff" lineWidth={1.2} transparent opacity={0.6} />)}
          {nodes.map(({ d, p }, i) => {
            const st = KIND_STYLE[d.data.kind] || KIND_STYLE.op;
            return (
              <group key={i} position={p}>
                <mesh>
                  <sphereGeometry args={[d.data.kind === 'root' ? 0.36 : 0.26, 24, 24]} />
                  <meshStandardMaterial color={st.hex} roughness={0.35} />
                </mesh>
                {(showAll || d.children) && (
                  <Html center position={[0, 0.5, 0]} distanceFactor={11} style={{ pointerEvents: 'none' }}>
                    <span className="t3-label" style={{ background: st.bg, color: st.fg }}>{trunc(d.data.label, 12)}</span>
                  </Html>
                )}
              </group>
            );
          })}
          <OrbitControls autoRotate autoRotateSpeed={1.4} enableDamping makeDefault />
        </Canvas>
      </ErrorBoundary>
      <span className="g3-hint">drag to rotate · scroll to zoom</span>
    </div>
  );
}

export function TreeView({ ast }) {
  const [mode, setMode] = useState('2d');
  const root = useMemo(() => (ast ? astToTree(ast) : null), [ast]);
  if (!root) return <div className="empty">The parser stopped on a syntax error, so there is no complete syntax tree.</div>;
  return (
    <div>
      <div className="seg">
        <button className={`btn-flat ${mode === '2d' ? 'on' : ''}`} onClick={() => setMode('2d')}>2D tree</button>
        <button className={`btn-flat ${mode === '3d' ? 'on' : ''}`} onClick={() => setMode('3d')}>3D tree</button>
      </div>
      {mode === '2d' ? <Tree2D root={root} /> : <Tree3D root={root} />}
    </div>
  );
}

/* --------------------------------------------------------------------- CFG */
const BW = 270;
const LH = 17;

function layoutCfg(blocks) {
  const byId = Object.fromEntries(blocks.map((b) => [b.id, b]));
  const state = {};
  const back = new Set();
  const dfs = (u) => {
    state[u] = 1;
    for (const s of byId[u].succ) {
      if (state[s.to] === 1) back.add(`${u}>${s.to}`);
      else if (!state[s.to]) dfs(s.to);
    }
    state[u] = 2;
  };
  if (blocks.length) dfs(blocks[0].id);
  const rank = Object.fromEntries(blocks.map((b) => [b.id, 0]));
  for (let it = 0; it < blocks.length + 2; it++) {
    for (const b of blocks) {
      for (const s of b.succ) if (!back.has(`${b.id}>${s.to}`)) rank[s.to] = Math.max(rank[s.to], rank[b.id] + 1);
    }
  }
  const rows = [];
  blocks.forEach((b) => { (rows[rank[b.id]] ||= []).push(b); });
  const height = (b) => 30 + b.instrs.length * LH + 34;
  const pos = {};
  let y = 20;
  const maxCols = Math.max(...rows.map((r) => r.length), 1);
  const totalW = maxCols * (BW + 50) + 90;
  rows.forEach((row) => {
    const rowH = Math.max(...row.map(height));
    const rowW = row.length * (BW + 50) - 50;
    row.forEach((b, i) => {
      pos[b.id] = { x: (totalW - rowW) / 2 + i * (BW + 50) - 20, y, h: height(b) };
    });
    y += rowH + 64;
  });
  return { pos, back, width: totalW, height: y };
}

export function CfgView({ cfg }) {
  const data = cfg;
  const blocks = data?.blocks || [];
  const L = useMemo(() => layoutCfg(blocks), [blocks]);
  if (!cfg) return <div className="empty">Compile a valid program to see its control-flow graph.</div>;
  const edgePath = (a, b, isBack) => {
    const A = L.pos[a], B = L.pos[b];
    if (!A || !B) return '';
    if (isBack) {
      const x1 = A.x + BW, y1 = A.y + A.h / 2, x2 = B.x + BW, y2 = B.y + 22;
      const off = 34 + (Math.abs(A.y - B.y) % 3) * 6;
      return `M${x1},${y1} C${x1 + off},${y1} ${x2 + off},${y2} ${x2 + 3},${y2}`;
    }
    const x1 = A.x + BW / 2, y1 = A.y + A.h, x2 = B.x + BW / 2, y2 = B.y;
    const m = (y1 + y2) / 2;
    return `M${x1},${y1} C${x1},${m} ${x2},${m} ${x2},${y2 - 2}`;
  };
  return (
    <div>
      <p className="muted cfg-sum">{blocks.length} basic blocks · {data.edges} edges · <span className="mint">live-in</span> / <span className="pink">live-out</span> variables under each block</p>
      <div className="graph-scroll cfg">
        <svg width={L.width} height={L.height} role="img" aria-label="Control flow graph">
          <defs>
            <marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#c9bcff" /></marker>
            <marker id="ar-b" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#E7D623" /></marker>
          </defs>
          {blocks.map((b) => b.succ.map((s, i) => {
            const isBack = L.back.has(`${b.id}>${s.to}`);
            const A = L.pos[b.id], B = L.pos[s.to];
            if (!A || !B) return null;
            return (
              <g key={`${b.id}-${i}`}>
                <path d={edgePath(b.id, s.to, isBack)} className={`cfg-edge ${isBack ? 'back' : ''}`} markerEnd={`url(#${isBack ? 'ar-b' : 'ar'})`} />
                {s.kind !== 'fall' && !isBack && (
                  <text className="cfg-elabel" x={A.x + BW / 2 + (i ? 22 : -22)} y={A.y + A.h + 16}>{s.kind === 'jump' ? 'goto' : s.kind === 'true' ? 'T' : 'F'}</text>
                )}
              </g>
            );
          }))}
          {blocks.map((b) => {
            const p = L.pos[b.id];
            return (
              <g key={b.id} transform={`translate(${p.x},${p.y})`}>
                <rect width={BW} height={p.h} rx={14} className="cfg-box" />
                <rect width={BW} height={26} rx={14} className="cfg-head" />
                <rect y={14} width={BW} height={12} className="cfg-head" />
                <text x={14} y={18} className="cfg-id">{b.id}</text>
                <text x={BW - 14} y={18} textAnchor="end" className="cfg-range">instr {b.start}–{b.end - 1}</text>
                {b.instrs.map((t, i) => <text key={i} x={14} y={46 + i * LH} className="cfg-ins">{t}</text>)}
                <text x={14} y={p.h - 14} className="cfg-live">in {`{${b.live_in.join(', ')}}`}</text>
                <text x={BW - 14} y={p.h - 14} textAnchor="end" className="cfg-live out">out {`{${b.live_out.join(', ')}}`}</text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
