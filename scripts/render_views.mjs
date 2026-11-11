// Fixed views -> artifacts/renders/*.png (PLAN 11.3). Usage: node scripts/render_views.mjs [--hq] [name ...]
import { mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO, launch, openApp, serve } from './lib.mjs';

const args = process.argv.slice(2);
const hq = args.includes('--hq');
const only = args.filter((a) => !a.startsWith('--'));
const out = join(REPO, 'artifacts', 'renders');
mkdirSync(out, { recursive: true });
const data = JSON.parse(readFileSync(join(REPO, 'web', 'src', 'generated', 'data.json'), 'utf8'));

const jobs = [];
for (const [name, v] of Object.entries(data.views)) if (v.render) jobs.push({ name, q: `view=${name}` });
jobs.push({ name: 'exploded', q: 'view=exploded&explode=1' });
jobs.push({ name: 'exploded_left', q: 'view=left&explode=1' });
jobs.push({ name: 'sealmap', q: 'view=iso&seals=1' });
for (const [name, s] of Object.entries(data.sections)) jobs.push({ name: `section_${name}`, q: `view=${s.view ?? 'left'}&section=${name}` });
for (const [name, v] of Object.entries(data.views)) if (v.photo) jobs.push({ name: `photo_${name}`, q: `view=${name}` });
// one step per procedure, with the panels as the user sees them: the last step that highlights a seal
for (const p of data.procedures) {
  let i = p.steps.length - 1;
  for (let k = 0; k < p.steps.length; k++) if (p.steps[k].highlight?.length) i = k;
  jobs.push({ name: `proc_${p.id}`, q: `proc=${p.id}&step=${i + 1}`, ui: true }); // step is 1-based in URLs
}

const { server, url } = await serve();
const browser = await launch();
let failed = 0;
for (const j of jobs) {
  if (only.length && !only.includes(j.name)) continue;
  const t0 = Date.now();
  const { page, errors } = await openApp(browser, url, `${j.ui ? '' : 'ui=0&'}anim=0&${j.q}`, { scale: hq ? 2 : 1 });
  const file = join(out, `${j.name}.png`);
  await page.screenshot({ path: file });
  await page.close();
  if (errors.length) {
    failed++;
    console.log(`  ${j.name}: FEHLER ${errors.join(' | ')}`);
  } else console.log(`  ${j.name}.png (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
}
await browser.close();
server.close();
console.log(`render_views: ${jobs.length} Ansichten -> artifacts/renders/`);
process.exit(failed ? 1 : 0);
