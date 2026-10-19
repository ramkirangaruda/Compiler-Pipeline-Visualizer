/** Convert the backend's AST JSON into a generic {label, sub, kind, children} tree. */
export function astToTree(n, role) {
  if (!n) return null;
  const kids = (...xs) => xs.filter(Boolean);
  const wrap = (r, node) => (node ? astToTree(node, r) : null);
  const ty = n.ty ? ` : ${n.ty}` : '';
  switch (n.node) {
    case 'Program':
      return { label: 'Program', sub: `${n.body.length} statements`, kind: 'root', children: n.body.map((b) => astToTree(b)) };
    case 'VarDecl':
      return { label: `${n.vtype} ${n.name}`, sub: 'declaration', kind: 'stmt', line: n.line, children: kids(n.init && astToTree(n.init)) };
    case 'Assign':
      return { label: `${n.name} =`, sub: 'assignment', kind: 'stmt', line: n.line, children: kids(astToTree(n.value)) };
    case 'Print':
      return { label: 'print', sub: 'statement', kind: 'stmt', line: n.line, children: kids(astToTree(n.value)) };
    case 'Block':
      return { label: '{ }', sub: role || 'block', kind: 'block', line: n.line, children: n.body.map((b) => astToTree(b)) };
    case 'If':
      return {
        label: 'if', sub: 'statement', kind: 'stmt', line: n.line,
        children: kids(wrap('cond', n.cond), wrap('then', n.then), n.alt && (n.alt.node === 'If' ? astToTree(n.alt) : wrap('else', n.alt))),
      };
    case 'While':
      return { label: 'while', sub: 'statement', kind: 'stmt', line: n.line, children: kids(wrap('cond', n.cond), wrap('body', n.body)) };
    case 'Binary':
      return { label: n.op, sub: `binary${ty}`, kind: 'op', line: n.line, children: kids(astToTree(n.left), astToTree(n.right)) };
    case 'Unary':
      return { label: n.op, sub: `unary${ty}`, kind: 'op', line: n.line, children: kids(astToTree(n.operand)) };
    case 'Literal':
      return { label: n.value, sub: `${n.kind.toLowerCase()}`, kind: 'lit', line: n.line, children: [] };
    case 'Ident':
      return { label: n.name, sub: `identifier${ty}`, kind: 'id', line: n.line, children: [] };
    default:
      return { label: n.node, sub: '', kind: 'op', children: [] };
  }
}

export const KIND_STYLE = {
  root: { bg: '#ffffff', fg: '#5423E7', hex: '#ffffff' },
  stmt: { bg: '#E7D623', fg: '#2b2600', hex: '#E7D623' },
  block: { bg: '#8E78F2', fg: '#ffffff', hex: '#8E78F2' },
  op: { bg: '#F4F1FE', fg: '#4A1FCC', hex: '#c9bcff' },
  lit: { bg: '#2CF7A4', fg: '#0A4029', hex: '#2CF7A4' },
  id: { bg: '#602CF7', fg: '#ffffff', hex: '#ff9ec1' },
};
