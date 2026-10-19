import React from 'react';

/** Renders the hunks produced by the engine (difflib opcodes). */
export default function Diff({ hunks }) {
  if (!hunks?.length) return <div className="diff-empty">No textual change.</div>;
  return (
    <div className="diff">
      {hunks.map((h, i) => (
        <div className="diff-hunk" key={i}>
          {h.old.map((l, j) => (
            <div className="diff-row del" key={`o${j}`}><span className="ln">{h.old_start + j}</span><span className="sg">−</span><code>{l || ' '}</code></div>
          ))}
          {h.new.map((l, j) => (
            <div className="diff-row add" key={`n${j}`}><span className="ln">{h.new_start + j}</span><span className="sg">+</span><code>{l || ' '}</code></div>
          ))}
        </div>
      ))}
    </div>
  );
}
