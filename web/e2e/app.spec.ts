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
  await load(page);
  const procs = await page.evaluate(() => window.__pavoni.data.procedures.map((p) => ({ id: p.id, n: p.steps.length })));
  for (const pr of procs) {
    await page.evaluate((id) => window.__pavoni.gotoStep(id, 0), pr.id);
    const player = page.getByTestId('procedure-player');
    await expect(player).toBeVisible();
    for (let i = 1; i < pr.n; i++) await page.getByTestId('next-step').click();
    expect(await page.evaluate(() => window.__pavoni.state().stepIdx)).toBe(pr.n - 1);
    await page.getByRole('button', { name: 'Zusammenbauen' }).click();
    for (let i = 1; i < pr.n; i++) await page.getByTestId('next-step').click();
    expect(await page.evaluate(() => window.__pavoni.state().stepIdx)).toBe(pr.n - 1);
  }
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
