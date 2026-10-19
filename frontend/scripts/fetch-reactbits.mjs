// Vendors the React Bits (https://reactbits.dev) components used by the UI into src/reactbits/.
// Usage: npm run fetch:reactbits
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = join(dirname(fileURLToPath(import.meta.url)), '..', 'src', 'reactbits');
const COMPONENTS = [
  'SplitText', 'BlurText', 'GradientText', 'ShinyText', 'CountUp', 'DecryptedText', 'TextType',
  'SpotlightCard', 'Magnet', 'ClickSpark', 'StarBorder', 'AnimatedList', 'CardSwap',
  'Ballpit', 'ShapeGrid', 'FadeContent', 'AnimatedContent', 'TiltedCard',
];

await mkdir(OUT, { recursive: true });
const deps = new Set();
for (const name of COMPONENTS) {
  const res = await fetch(`https://reactbits.dev/r/${name}-JS-CSS.json`);
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  const item = await res.json();
  (item.dependencies || []).forEach((d) => deps.add(d));
  for (const f of item.files) {
    const file = f.path.split('/').pop();
    await writeFile(join(OUT, file), f.content, 'utf8');
  }
  console.log('fetched', name, (item.dependencies || []).join(' '));
}
console.log('\nnpm dependencies required:', [...deps].join(' ') || '(none)');
