import fs from 'node:fs';
import postcss from 'postcss';

const samples = JSON.parse(fs.readFileSync(new URL('../work/css-samples-for-validation.json', import.meta.url), 'utf8'));
let checked = 0;

for (const { path, language, sample } of samples) {
  const css = language === 'html' ? sample.match(/<style>([\s\S]*?)<\/style>/)?.[1] : sample;
  if (!css) throw new Error(`${path}: missing CSS inside HTML sample`);
  try {
    const ast = postcss.parse(css, { from: path });
    if (!ast.nodes.length) throw new Error('empty stylesheet');
  } catch (error) {
    throw new Error(`${path}: ${error.message}`);
  }
  checked += 1;
}

console.log(JSON.stringify({ passed: true, parsedSamples: checked }));
