import { describe, expect, it } from 'vitest';
import { data } from '../data';
import { buildModelIndex } from './graph';
import { explodeOffsets, maxStage, removalDisplay, stageFactor } from './explode';
import { checkProcedure, procedureState } from './procedure';
import { cadDirToGl, cadToGl } from './coords';

const idx = buildModelIndex(data);

describe('coords', () => {
  it('maps CAD mm Z-up to GL m Y-up', () => {
    expect(cadToGl([100, -200, 300])).toEqual([0.1, 0.3, 0.2]);
    expect(cadDirToGl([0, -1, 0])).toEqual([0, 0, 1]); // front faces the default camera
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
        const key = idx.kind(r) === 'inst' ? r.split('__')[0] : r;
        expect(order.indexOf(key)).toBeLessThan(order.length - 1);
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
    const st = { removed: new Set<string>(), moving: new Map([['group.piston', 1]]) };
    const d = removalDisplay(data, idx, st);
    const inside = Object.keys(data.instances).filter((i) => data.instances[i].assembly.startsWith('group.piston'));
    for (const i of inside) expect(d[i].offset).toEqual(d[inside[0]].offset);
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
