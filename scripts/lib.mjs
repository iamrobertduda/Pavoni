// Shared helpers for render/overlay scripts: static server for web/dist and a headless Chromium
// with software WebGL (PLAN 3.3). Uses the Playwright installed in web/node_modules.
import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(join(REPO, 'web', 'package.json'));
export const { chromium } = require('@playwright/test');

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg' };

export function serve(root = join(REPO, 'web', 'dist'), extra = {}) {
  if (!existsSync(join(root, 'index.html'))) throw new Error(`${root}/index.html fehlt - erst "make web"`);
  const server = createServer((req, res) => {
    const url = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    for (const [prefix, dir] of Object.entries(extra)) {
      if (url.startsWith(prefix)) return send(res, join(dir, url.slice(prefix.length)));
    }
    send(res, join(root, url === '/' ? 'index.html' : url));
  });
  return new Promise((ok) => server.listen(0, '127.0.0.1', () => ok({ server, url: `http://127.0.0.1:${server.address().port}/` })));
}

function send(res, file) {
  if (!existsSync(file) || !statSync(file).isFile()) {
    res.writeHead(404);
    return res.end('not found');
  }
  res.writeHead(200, { 'content-type': TYPES[extname(file)] ?? 'application/octet-stream' });
  createReadStream(file).pipe(res);
}

export async function launch() {
  return chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
}

export async function openApp(browser, base, query, { width = 1200, height = 900, scale = 1 } = {}) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: scale });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  page.setDefaultTimeout(180000);
  await page.goto(`${base}?quality=low&${query}`);
  await page.waitForFunction(() => window.__pavoni?.ready === true, null, { timeout: 120000 });
  await page.waitForTimeout(800);
  return { page, errors };
}
