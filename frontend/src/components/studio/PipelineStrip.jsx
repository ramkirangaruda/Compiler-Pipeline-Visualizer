import React from 'react';

const TAB_OF = { lexer: 'tokens', parser: 'tree', semantic: 'symbols', ir: 'code', optimizer: 'code', vm: 'run' };

/** A slim status bar: one pill per compiler phase. */
export default function PhaseBar({ stages, onSelect }) {
  return (
    <div className="phases" role="list" aria-label="Compiler phases">
      {(stages || []).map((s, i) => (
        <React.Fragment key={s.key}>
          <button role="listitem" className={`phase ${s.status}`} onClick={() => onSelect?.(TAB_OF[s.key])}
            title={s.status === 'skipped' ? `${s.label}: not reached` : `${s.label}: ${s.status} · ${s.ms} ms`}>
            <i />{s.label}
          </button>
          {i < stages.length - 1 && <span className="phase-arrow">›</span>}
        </React.Fragment>
      ))}
    </div>
  );
}
