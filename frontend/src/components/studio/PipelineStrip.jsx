import React from 'react';

const ICONS = {
  lexer: <path d="M5 5h14v14H5zM9 10h6M9 14h4" />,
  parser: <path d="M12 4v4m0 0l-5 5m5-5l5 5M7 13v3m10-3v3" />,
  semantic: <path d="M5 12l4 4 10-10" />,
  ir: <path d="M5 7h14M5 12h9M5 17h12" />,
  optimizer: <path d="M12 3l2.4 5.2 5.6.7-4.1 3.9 1 5.6L12 15.6 7.1 18.4l1-5.6L4 8.9l5.6-.7z" />,
  vm: <path d="M7 5l12 7-12 7z" />,
};

const ML_STEPS = [
  ['Feature extractor', 'compiler state → 40 features'],
  ['ML classifier', 'rank 12 causes'],
  ['Repair generator', 'candidate edits'],
  ['Validator', 're-compile each fix'],
];

export default function PipelineStrip({ stages, diagnosis, onSelect }) {
  const failed = stages?.some((s) => s.status === 'error');
  const has = !!diagnosis?.entries?.length;
  const verified = diagnosis?.entries?.some((e) => e.candidates?.some((c) => c.status === 'verified'));
  return (
    <div className="pstrip">
      <div className="pstrip-track">
        {(stages || []).map((s, i) => (
          <React.Fragment key={s.key}>
            <button className={`pnode ${s.status}`} onClick={() => onSelect?.(s.key)} title={`${s.label}: ${s.status}${s.ms ? ` · ${s.ms} ms` : ''}`}>
              <span className="ring">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {s.status === 'error' ? <path d="M6 6l12 12M18 6L6 18" /> : ICONS[s.key]}
                </svg>
              </span>
              <span className="plabel">{s.label}</span>
              <span className="pms">{s.status === 'skipped' ? 'skipped' : `${s.ms} ms`}</span>
            </button>
            {i < stages.length - 1 && <span className={`ptrace ${stages[i + 1].status === 'skipped' ? 'dead' : stages[i].status === 'ok' ? 'live' : 'dead'}`}><i /></span>}
          </React.Fragment>
        ))}
      </div>
      {failed && (
        <div className={`pbranch ${has ? 'on' : ''}`}>
          <span className="pbranch-tag">compile failed → ML diagnosis</span>
          {ML_STEPS.map(([t, d], i) => (
            <React.Fragment key={t}>
              <span className={`bstep ${has ? (i === 3 && !verified ? 'warn' : 'on') : ''}`} style={{ '--d': `${i * 0.18}s` }}>
                <b>{t}</b><small>{d}</small>
              </span>
              {i < ML_STEPS.length - 1 && <span className="barrow">→</span>}
            </React.Fragment>
          ))}
          <span className="barrow loop" title="Rejected fixes go back to the repair generator">↺</span>
        </div>
      )}
    </div>
  );
}
