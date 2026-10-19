import React, { useCallback, useEffect, useMemo, useRef } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { EditorView, Decoration, keymap } from '@codemirror/view';
import { StateEffect, StateField, Prec } from '@codemirror/state';
import { StreamLanguage, HighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { linter, lintGutter, setDiagnostics } from '@codemirror/lint';
import { tags as t } from '@lezer/highlight';

const miniC = StreamLanguage.define({
  token(stream) {
    if (stream.eatSpace()) return null;
    if (stream.match('//')) { stream.skipToEnd(); return 'comment'; }
    if (stream.match(/^"(?:[^"\\]|\\.)*"?/)) return 'string';
    if (stream.match(/^\d+(\.\d+)?/)) return 'number';
    if (stream.match(/^(if|else|while|print)\b/)) return 'keyword';
    if (stream.match(/^(int|float|bool|string)\b/)) return 'typeName';
    if (stream.match(/^(true|false)\b/)) return 'bool';
    if (stream.match(/^[A-Za-z_]\w*/)) return 'variableName';
    if (stream.match(/^(==|!=|<=|>=|&&|\|\|)/)) return 'operator';
    stream.next();
    return 'punctuation';
  },
  tokenTable: {
    keyword: t.keyword, typeName: t.typeName, bool: t.bool, number: t.number, string: t.string,
    comment: t.comment, operator: t.operator, variableName: t.variableName, punctuation: t.punctuation,
  },
});

const highlight = HighlightStyle.define([
  { tag: t.keyword, color: '#E7D623', fontWeight: '700' },
  { tag: t.typeName, color: '#2CF7A4', fontWeight: '700' },
  { tag: t.bool, color: '#ff9ec1' },
  { tag: t.number, color: '#ff9ec1' },
  { tag: t.string, color: '#9be7ff' },
  { tag: t.comment, color: '#8d7bd8', fontStyle: 'italic' },
  { tag: t.operator, color: '#c7b8ff' },
  { tag: t.variableName, color: '#ffffff' },
  { tag: t.punctuation, color: '#b9a8ff' },
]);

const theme = EditorView.theme(
  {
    '&': { backgroundColor: '#0A041A', color: '#fff', fontSize: '14px', height: '100%' },
    '.cm-scroller': { fontFamily: 'var(--mono)', lineHeight: '1.7', fontVariantLigatures: 'none' },
    '.cm-content': { caretColor: '#2CF7A4', padding: '12px 0' },
    '.cm-gutters': { backgroundColor: '#12082e', color: '#7e6bd0', border: 'none', borderRight: '1px solid rgba(255,255,255,0.08)' },
    '.cm-activeLine': { backgroundColor: 'rgba(255,255,255,0.045)' },
    '.cm-activeLineGutter': { backgroundColor: 'rgba(255,255,255,0.08)', color: '#fff' },
    '.cm-cursor': { borderLeftColor: '#2CF7A4' },
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground': { backgroundColor: 'rgba(96,44,247,0.55) !important' },
    '.cm-ml-line': { backgroundColor: 'rgba(44,247,164,0.13)', boxShadow: 'inset 3px 0 0 #2CF7A4' },
    '.cm-err-line': { backgroundColor: 'rgba(255,107,139,0.12)' },
    '.cm-exec-line': { backgroundColor: 'rgba(231,214,35,0.18)', boxShadow: 'inset 3px 0 0 #E7D623' },
    '.cm-lintRange-error': { backgroundImage: 'none', borderBottom: '2px wavy #FF6B8B', paddingBottom: '1px' },
    '.cm-lintRange-warning': { backgroundImage: 'none', borderBottom: '2px dotted #E7D623' },
    '.cm-tooltip': { backgroundColor: '#1d0d57', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', borderRadius: '10px' },
    '.cm-diagnostic': { padding: '6px 10px', fontFamily: 'var(--sans)' },
  },
  { dark: true },
);

const setLines = StateEffect.define();
const lineField = StateField.define({
  create: () => Decoration.none,
  update(deco, tr) {
    deco = deco.map(tr.changes);
    for (const e of tr.effects) {
      if (e.is(setLines)) {
        const { doc } = tr.state;
        const ranges = [];
        for (const [line, cls] of e.value) {
          if (line >= 1 && line <= doc.lines) ranges.push(Decoration.line({ class: cls }).range(doc.line(line).from));
        }
        ranges.sort((a, b) => a.from - b.from);
        deco = Decoration.set(ranges, true);
      }
    }
    return deco;
  },
  provide: (f) => EditorView.decorations.from(f),
});

/**
 * props.diagnostics: [{from,to,severity,message}] compiler errors (red squiggles)
 * props.mlLines: line numbers the ML localised the fault to (mint highlight)
 * props.errLines: line numbers where the compiler detected the error (red tint)
 */
export default function Editor({ value, onChange, diagnostics = [], mlLines = [], errLines = [], execLine = 0, onRun }) {
  const view = useRef(null);
  const onRunRef = useRef(onRun);
  onRunRef.current = onRun;

  const extensions = useMemo(
    () => [
      miniC,
      syntaxHighlighting(highlight),
      lintGutter(),
      linter(null),
      lineField,
      EditorView.lineWrapping,
      Prec.highest(keymap.of([{ key: 'Mod-Enter', run: () => { onRunRef.current?.(); return true; } }])),
    ],
    [],
  );

  const apply = useCallback(() => {
    const v = view.current;
    if (!v) return;
    const len = v.state.doc.length;
    const diags = diagnostics
      .filter((d) => d.from <= len)
      .map((d) => ({ ...d, to: Math.min(Math.max(d.to, d.from + 1), len) }));
    const lines = [...errLines.map((l) => [l, 'cm-err-line']), ...mlLines.map((l) => [l, 'cm-ml-line'])];
    if (execLine > 0) lines.push([execLine, 'cm-exec-line']);
    v.dispatch({ effects: setLines.of(lines) });
    v.dispatch(setDiagnostics(v.state, diags));
  }, [diagnostics, mlLines, errLines, execLine]);

  useEffect(apply, [apply, value]);

  return (
    <CodeMirror
      value={value}
      height="100%"
      theme={theme}
      extensions={extensions}
      basicSetup={{ foldGutter: false, highlightActiveLine: true, autocompletion: false }}
      onChange={onChange}
      onCreateEditor={(v) => { view.current = v; apply(); }}
      aria-label="MiniC source editor"
    />
  );
}
