// Hierarchical explode and removal offsets in CAD mm (world frame).
import type { AppData, Vec3 } from '../data/types';
import { asmChain, type ModelIndex } from './graph';

export const smooth = (x: number) => x * x * (3 - 2 * x);
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

export function maxStage(d: Pick<AppData, 'instances' | 'assemblyGeo'>): number {
  let s = 1;
  for (const g of Object.values(d.instances)) s = Math.max(s, g.explode.stage);
  for (const a of Object.values(d.assemblyGeo)) s = Math.max(s, a.explode.stage);
  return s;
}

/** Fraction of a stage that is open at global explode t in [0, 1]. */
export function stageFactor(t: number, stage: number, nStages: number): number {
  return smooth(clamp01(t * nStages - (stage - 1)));
}

const add = (a: Vec3, b: Vec3, k: number): Vec3 => [a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k];

/**
 * Global explode view: assemblies move apart along their axes, then their parts
 * along their own axes, stage by stage (not radial from a centre).
 */
export function explodeOffsets(d: Pick<AppData, 'instances' | 'assemblyGeo'>, t: number): Record<string, Vec3> {
  const n = maxStage(d);
  const out: Record<string, Vec3> = {};
  for (const [iid, g] of Object.entries(d.instances)) {
    let o: Vec3 = [0, 0, 0];
    for (const a of asmChain(g.assembly)) {
      const ag = d.assemblyGeo[a];
      if (!ag) continue;
      o = add(o, ag.explode.axis, ag.explode.distance_mm * stageFactor(t, ag.explode.stage, n));
    }
    o = add(o, g.explode.axis, g.explode.distance_mm * stageFactor(t, g.explode.stage, n));
    out[iid] = o;
  }
  return out;
}

export interface RemovalState {
  /** fully removed refs (instances and detached assembly ids) */
  removed: Set<string>;
  /** refs currently moving, with progress 0..1 (1 = fully out) */
  moving: Map<string, number>;
}

export interface InstanceDisplay {
  offset: Vec3;
  visible: boolean;
  active: boolean;
}

/**
 * Display state for disassembly/procedure playback. Detached assemblies stay
 * visible at their offset ("on the bench"); removed parts are hidden once out,
 * parts moving in the current step stay visible.
 */
export function removalDisplay(d: Pick<AppData, 'instances' | 'assemblyGeo'>, idx: ModelIndex, st: RemovalState): Record<string, InstanceDisplay> {
  const out: Record<string, InstanceDisplay> = {};
  for (const [iid, g] of Object.entries(d.instances)) {
    let o: Vec3 = [0, 0, 0];
    let active = false;
    for (const a of asmChain(g.assembly)) {
      const ag = d.assemblyGeo[a];
      if (!ag) continue;
      const p = st.moving.get(a) ?? (st.removed.has(a) ? 1 : 0);
      if (st.moving.has(a)) active = true;
      if (p > 0) o = add(o, ag.explode.axis, ag.explode.distance_mm * smooth(p));
    }
    const pid = idx.instPart[iid];
    const own = st.moving.get(iid) ?? st.moving.get(pid);
    let visible = true;
    if (own !== undefined) {
      active = true;
      o = add(o, g.explode.axis, g.explode.distance_mm * smooth(own));
    } else if (st.removed.has(iid) || st.removed.has(pid)) {
      visible = false;
    }
    out[iid] = { offset: o, visible, active };
  }
  return out;
}
