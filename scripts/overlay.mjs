// Render a photo view with transparent background and lay it semi-transparently over the
// owner's reference photo -> artifacts/overlays/<view>.png (PLAN 11.3).
// Views with a `photo` field in data/views.yaml are used. Usage: node scripts/overlay.mjs [view ...] [--alpha=0.5]
import { mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO, launch, openApp, serve } from './lib.mjs';

const args = process.argv.slice(2);
const alpha = parseFloat((args.find((a) => a.startsWith('--alpha=')) ?? '--alpha=0.5').split('=')[1]);
const only = args.filter((a) => !a.startsWith('--'));
const out = join(REPO, 'artifacts', 'overlays');
mkdirSync(out, { recursive: true });
const data = JSON.parse(readFileSync(join(REPO, 'web', 'src', 'generated', 'data.json'), 'utf8'));
const views = Object.entries(data.views).filter(([n, v]) => v.photo && (!only.length || only.includes(n)));

const { server, url } = await serve(undefined, { '/ref/': join(REPO, 'reference', 'photos') });
const browser = await launch();
for (const [name, v] of views) {
  // photos are 3:4 portrait; render at the same aspect
  const w = 600;
  const h = 800;
  // 2x so that small deviations between model and photo are visible
  const { page } = await openApp(browser, url, `ui=0&anim=0&bg=transparent&view=${name}`, { width: w, height: h, scale: 2 });
  const png = await page.screenshot({ omitBackground: true });
  await page.close();
  const comp = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  await comp.setContent(`<html><body style="margin:0;position:relative;width:${w}px;height:${h}px;overflow:hidden">
    <img src="${url}ref/${v.photo}" style="position:absolute;inset:0;width:${w}px;height:${h}px;object-fit:cover">
    <img src="data:image/png;base64,${png.toString('base64')}" style="position:absolute;inset:0;width:${w}px;height:${h}px;opacity:${alpha}">
    <div style="position:absolute;left:6px;top:6px;font:12px sans-serif;background:#fff9;padding:2px 5px">${name} über ${v.photo} (Deckkraft ${alpha})</div>
  </body></html>`, { waitUntil: 'domcontentloaded' });
  await comp.waitForFunction(() => [...document.images].every((i) => i.complete && i.naturalWidth > 0), null, { timeout: 60000 });
  await comp.waitForTimeout(200);
  await comp.screenshot({ path: join(out, `${name}.png`) });
  await comp.close();
  console.log(`  ${name}.png`);
}
await browser.close();
server.close();
console.log(`overlay: ${views.length} Overlays -> artifacts/overlays/`);
