import { expect, type Page, test } from '@playwright/test';

declare global {
  interface Window {
    __pavoni: {
      ready: boolean;
      select: (id: string | null) => void;
      setExplode: (x: number) => void;
      setView: (n: string) => void;
      gotoStep: (proc: string, n: number, dir?: string) => void;
      state: () => { selected: string | null; explode: number; mode: string; procId: string | null; stepIdx: number; section: string | null };
      instancePosition: (iid: string) => number[] | null;
      instanceVisible: (iid: string) => boolean | null;
      instances: () => string[];
      capCount: () => number;
      frames: () => number;
      data: { parts: { id: string; instances: string[]; status: string }[]; procedures: { id: string; steps: { id: string }[] }[]; sections: Record<string, unknown> };
    };
  }
}

async function load(page: Page, query = '') {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`./?anim=0${query}`);
  await page.waitForFunction(() => window.__pavoni?.ready === true, null, { timeout: 120_000 });
  return errors;
}

test('loads the model with every built instance', async ({ page }) => {
  const errors = await load(page);
  const { inst, expected } = await page.evaluate(() => ({
    inst: window.__pavoni.instances(),
    expected: window.__pavoni.data.parts.filter((p) => p.status !== 'planned').flatMap((p) => p.instances),
  }));
  expect(inst.sort()).toEqual(expected.sort());
  expect(errors).toEqual([]);
  await expect(page.getByTestId('loader')).toHaveCount(0);
});

test('select a part from the tree shows the info panel', async ({ page }) => {
  await load(page);
  const first = await page.evaluate(() => window.__pavoni.data.parts.find((p) => p.status !== 'planned')!.id);
  await page.locator('.tree-row.asm .twist').first().click();
  await page.getByPlaceholder('Teil suchen').fill(first);
  await page.locator(`[data-part="${first}"]`).click();
  await expect(page.getByTestId('info-panel')).toBeVisible();
  expect(await page.evaluate(() => window.__pavoni.state().selected)).toBe(first);
  expect(page.url()).toContain(`part=${first}`);
});

test('clicking the model picks a part', async ({ page }) => {
  await load(page, '&view=front');
  await page.mouse.click(640, 520);
  await expect(page.getByTestId('info-panel')).toBeVisible();
});

test('explode slider moves parts', async ({ page }) => {
  await load(page);
  const iid = await page.evaluate(() => window.__pavoni.instances().find((i) => i.startsWith('p080'))!);
  const p0 = await page.evaluate((i) => window.__pavoni.instancePosition(i), iid);
  await page.getByTestId('explode').fill('1');
  await page.waitForTimeout(200);
  const p1 = await page.evaluate((i) => window.__pavoni.instancePosition(i), iid);
  expect(p1).not.toEqual(p0);
});

test('section preset can be chosen', async ({ page }) => {
  await load(page);
  const name = await page.evaluate(() => Object.keys(window.__pavoni.data.sections)[0]);
  await page.getByTestId('section').selectOption(name);
  expect(await page.evaluate(() => window.__pavoni.state().section)).toBe(name);
});

test('every procedure can be clicked through forward and backward', async ({ page }) => {
  test.setTimeout(600_000);
  const errors = await load(page);
  const procs = await page.evaluate(() => window.__pavoni.data.procedures.map((p) => ({ id: p.id, n: p.steps.length })));
  for (const pr of procs) {
    await page.evaluate((id) => window.__pavoni.gotoStep(id, 0), pr.id);
    const player = page.getByTestId('procedure-player');
    await expect(player).toBeVisible();
    // first step by button, the rest by keyboard (a click waits for stable frames, slow under SwiftShader)
    const forward = async () => {
      if (pr.n > 1) await page.getByTestId('next-step').click();
      for (let i = 2; i < pr.n; i++) await page.keyboard.press('ArrowRight');
      await page.keyboard.press('ArrowRight'); // past the end: stays on the last step
      expect(await page.evaluate(() => window.__pavoni.state().stepIdx)).toBe(pr.n - 1);
    };
    await forward();
    await page.getByRole('button', { name: 'Zusammenbauen' }).click();
    await forward();
    if (pr.n > 1) {
      await page.keyboard.press('ArrowLeft');
      expect(await page.evaluate(() => window.__pavoni.state().stepIdx)).toBe(pr.n - 2);
    }
  }
  expect(errors).toEqual([]);
  await page.keyboard.press('Escape');
  expect(await page.evaluate(() => window.__pavoni.state().mode)).toBe('explore');
});

test('seal map shows the seal list and colours seals', async ({ page }) => {
  await load(page);
  await page.getByTestId('sealmap').click();
  const list = page.getByTestId('seal-list');
  await expect(list).toBeVisible();
  await expect(list.locator('[data-seal="p080_piston_seal"]')).toBeVisible();
  await list.locator('[data-seal="p080_piston_seal"]').click();
  await expect(page.getByTestId('info-panel')).toContainText('Kolbendichtung');
  await expect(page.getByTestId('info-panel')).toContainText('Vor der Bestellung');
});

test('section view draws filled caps', async ({ page }) => {
  await load(page, '&section=group&view=sec_group');
  await page.waitForFunction(() => window.__pavoni.capCount() > 0, null, { timeout: 60_000 });
  expect(await page.evaluate(() => window.__pavoni.capCount())).toBeGreaterThan(2);
});

test('disassembly mode removes prerequisites in order', async ({ page }) => {
  await load(page, '&part=p080_piston_seal');
  await page.getByRole('button', { name: 'Ausbauen zeigen' }).click();
  const next = page.getByRole('button', { name: 'Nächstes Teil ›' });
  await expect(next).toBeVisible();
  // the cap nut comes off before the piston assembly
  const order = await page.locator('.order li').allTextContents();
  expect(order.findIndex((t) => t.includes('Hutmutter'))).toBeLessThan(order.findIndex((t) => t.includes('Kolben mit Stange')));
  await page.getByRole('button', { name: 'Alle' }).click();
  await page.waitForTimeout(300);
  expect(await page.evaluate(() => window.__pavoni.instanceVisible('p093_cap_nut__1'))).toBe(false);
});

test('phone layout keeps the model visible', async ({ browser }) => {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await load(page);
  const canvas = page.locator('canvas');
  await expect(canvas).toBeVisible();
  const box = await canvas.boundingBox();
  expect(box!.width).toBeGreaterThan(380);
  // tree closed by default on phones
  expect(await page.locator('.tree').count()).toBe(0);
  await page.close();
});

test('deep link opens a procedure step', async ({ page }) => {
  const proc = 'piston_seals';
  await load(page, `&proc=${proc}&step=2`);
  const st = await page.evaluate(() => window.__pavoni.state());
  expect(st.mode).toBe('procedure');
  expect(st.procId).toBe(proc);
  expect(st.stepIdx).toBe(1);
  await expect(page.getByTestId('procedure-player')).toBeVisible();
});

test('renders on demand: no frames while idle, new frames after a change', async ({ page }) => {
  await load(page);
  await page.waitForTimeout(1500);
  const f0 = await page.evaluate(() => window.__pavoni.frames());
  await page.waitForTimeout(1500);
  expect(await page.evaluate(() => window.__pavoni.frames())).toBe(f0);
  await page.evaluate(() => window.__pavoni.setExplode(0.5));
  await page.waitForTimeout(500);
  expect(await page.evaluate(() => window.__pavoni.frames())).toBeGreaterThan(f0);
});

