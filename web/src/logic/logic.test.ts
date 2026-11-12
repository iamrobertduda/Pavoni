import { describe, expect, it } from 'vitest';
import { data } from '../data';
import { buildModelIndex } from './graph';
import { explodeOffsets, maxStage, removalDisplay, stageFactor } from './explode';
import { checkProcedure, procedureState } from './procedure';
import { cadDirToGl, cadToGl } from './coords';
import { viewPose } from './camera';

const idx = buildModelIndex(data);

describe('coords', () => {
  it('maps CAD mm Z-up to GL m Y-up', () => {
    expect(cadToGl([100, -200, 300])).toEqual([0.1, 0.3, 0.2]);
    expect(cadDirToGl([0, -1, 0])).toEqual([0, 0, 1]); // front faces the default camera
  });
});

describe('camera', () => {
  const dist = (p: { position: number[]; target: number[] }) => Math.hypot(...p.position.map((c, i) => c - p.target[i]));
  it('moves back on narrow screens so the same width stays in frame', () => {
    const v = data.views.iso;
    expect(dist(viewPose(v, 0.75))).toBeGreaterThan(dist(viewPose(v, 4 / 3)) * 1.5);
    expect(viewPose(v, 16 / 9)).toEqual(viewPose(v, 4 / 3));
  });
  it('never adapts views fitted to a reference photo (overlay must line up)', () => {
    const fitted = Object.values(data.views).filter((v) => v.photo);
    expect(fitted.length).toBeGreaterThan(0);
    for (const v of fitted) {
      const p = viewPose(v, 0.75); // the photos are 3:4 portrait
      expect(p.position).toEqual(cadToGl(v.position));
      expect(p.target).toEqual(cadToGl(v.target));
    }
  });
  it('follows an offset in CAD mm', () => {
    const v = data.views.iso;
    const a = viewPose(v, 4 / 3);
    const b = viewPose(v, 4 / 3, [0, -100, 0]); // 100 mm to the front = +0.1 m in GL z
    expect(b.target[2] - a.target[2]).toBeCloseTo(0.1);
    expect(b.position[2] - a.position[2]).toBeCloseTo(0.1);
  });
});

describe('graph', () => {
  it('knows every built instance', () => {
    for (const iid of Object.keys(data.instances)) expect(idx.kind(iid)).toBe('inst');
  });
  it('closure includes transitive requirements', () => {
    for (const p of data.parts) {
      const c = idx.closure([p.id]);
      for (const r of p.requires_removed) {
        const k = idx.kind(r);
        const units = k === 'asm' || k === 'inst' ? [r] : idx.parts[r].instances;
        for (const u of units) expect(c.has(u)).toBe(true);
      }
    }
  });
  it('removal order puts dependencies first and the target last', () => {
    for (const p of data.parts) {
      const order = idx.removalOrder(p.id);
      expect(order[order.length - 1]).toBe(p.id);
      for (const r of p.requires_removed) {
        expect(order.indexOf(r)).toBeGreaterThanOrEqual(0);
        expect(order.indexOf(r)).toBeLessThan(order.length - 1);
      }
    }
  });
});

describe('explode', () => {
  it('is zero at t=0 and full at t=1', () => {
    const z = explodeOffsets(data, 0);
    for (const v of Object.values(z)) expect(v).toEqual([0, 0, 0]);
    const f = explodeOffsets(data, 1);
    for (const [iid, g] of Object.entries(data.instances)) {
      const own = g.explode.distance_mm;
      const len = Math.hypot(...f[iid]);
      if (own > 0) expect(len).toBeGreaterThan(0);
    }
  });
  it('stages open one after another', () => {
    const n = maxStage(data);
    expect(stageFactor(0.5 / n, 1, n)).toBeGreaterThan(0);
    expect(stageFactor(0.5 / n, 2, n)).toBe(0);
  });
  it('detached assemblies move their parts as a unit', () => {
    const asm = 'boiler.group.piston';
    expect(idx.kind(asm)).toBe('asm');
    const st = { removed: new Set<string>(), moving: new Map([[asm, 1]]) };
    const d = removalDisplay(data, idx, st);
    const inside = Object.keys(data.instances).filter((i) => data.instances[i].assembly.startsWith(asm));
    expect(inside.length).toBeGreaterThan(2); // rod, piston and two seals at least
    const moved = d[inside[0]].offset;
    // only the piston assembly is moving here, its parent group is not detached: the way on the machine
    const e = data.assemblyGeo[asm].explode;
    expect(Math.hypot(...moved)).toBeCloseTo(e.removal_mm ?? e.distance_mm);
    for (const i of inside) expect(d[i].offset).toEqual(moved);
    // parts outside the assembly stay where they are
    const outside = Object.keys(data.instances).find((i) => data.instances[i].assembly === 'base')!;
    expect(d[outside].offset).toEqual([0, 0, 0]);
  });
  it('removal: short way on the machine, full explode distance once the assembly lies on the bench', () => {
    // the shower screen leaves the mounted group by a short way (the drip tray is below it) ...
    const screen = 'p081_shower_screen__1';
    const e = data.instances[screen].explode;
    expect(e.removal_mm).toBeDefined();
    expect(e.removal_mm!).toBeLessThan(e.distance_mm);
    const mounted = removalDisplay(data, idx, { removed: new Set<string>(), moving: new Map([[screen, 1]]) });
    expect(Math.hypot(...mounted[screen].offset)).toBeCloseTo(e.removal_mm!);
    // ... but with the group on the bench it ends up where the exploded view puts it, below the piston
    const bench = removalDisplay(data, idx, { removed: new Set(['boiler.group']), moving: new Map([[screen, 1], ['boiler.group.piston', 1]]) });
    const rel = (i: string) => bench[i].offset.map((c, k) => c - bench['p072_group_body__1'].offset[k]);
    expect(Math.hypot(...rel(screen))).toBeCloseTo(e.distance_mm);
    const f = explodeOffsets(data, 1);
    const body = f['p072_group_body__1'];
    for (const i of [screen, 'p079_piston__1', 'p078_piston_rod__1'])
      expect(rel(i).map((c) => Math.round(c * 100))).toEqual(f[i].map((c, k) => Math.round((c - body[k]) * 100)));
  });
});

describe('procedures', () => {
  it('satisfy requires_removed in order', () => {
    for (const p of data.procedures) expect(checkProcedure(idx, p)).toEqual([]);
  });
  it('play forward and backward to the same states', () => {
    for (const p of data.procedures) {
      const n = p.steps.length;
      for (let i = 0; i < n; i++) {
        const fwdEnd = procedureState(idx, p, i, 1, 'disassemble');
        const bwdStart = procedureState(idx, p, n - 1 - i, 0, 'assemble');
        expect([...fwdEnd.removed].sort()).toEqual([...bwdStart.removed].sort());
        expect([...fwdEnd.moving.keys()].sort()).toEqual([...bwdStart.moving.keys()].sort());
      }
    }
  });
});
