const BASE = import.meta.env.VITE_API_URL || '';

async function req(path, opts) {
  const res = await fetch(`${BASE}/api${path}`, opts);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = JSON.stringify((await res.json()).detail ?? detail); } catch { /* ignore */ }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json();
}

const post = (path, body) =>
  req(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export const api = {
  health: () => req('/health'),
  examples: () => req('/examples'),
  compile: (source, optimize = true, mode = 'ml') => post('/compile', { source, optimize, mode }),
  autofix: (source, mode = 'ml') => post('/autofix', { source, mode }),
  model: () => req('/model'),
  session: () => req('/session'),
  dataset: () => req('/dataset'),
  samples: (label, offset = 0, limit = 6) =>
    req(`/dataset/samples?label=${encodeURIComponent(label)}&offset=${offset}&limit=${limit}`),
};
