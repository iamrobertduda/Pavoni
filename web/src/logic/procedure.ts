// Procedure playback: state before/after each step, disassembly and reassembly.
import type { Procedure } from '../data/types';
import type { ModelIndex } from './graph';
import type { RemovalState } from './explode';

export type Direction = 'disassemble' | 'assemble';

/** Expand a step's remove refs into units (declared instance ids or assembly ids). */
export function stepUnits(idx: ModelIndex, refs: string[] = []): string[] {
  const out: string[] = [];
  for (const r of refs) {
    const k = idx.kind(r);
    if (k === 'asm' || k === 'inst') out.push(r);
    else if (k === 'part') out.push(...idx.parts[r].instances);
  }
  return out;
}

/**
 * State for step index `i` (0-based) of a procedure in a direction, at animation
 * progress `p` (0..1). In assemble mode, step i is the reverse of disassembly step
 * (n-1-i): its parts move back in.
 */
export function procedureState(idx: ModelIndex, proc: Procedure, i: number, p: number, dir: Direction): RemovalState {
  const n = proc.steps.length;
  const removed = new Set<string>(idx.closure(proc.start_removed ?? []));
  const moving = new Map<string, number>();
  const di = dir === 'disassemble' ? i : n - 1 - i;
  for (let k = 0; k < di; k++) stepUnits(idx, proc.steps[k].remove).forEach((u) => removed.add(u));
  const units = stepUnits(idx, proc.steps[di]?.remove);
  for (const u of units) moving.set(u, dir === 'disassemble' ? p : 1 - p);
  return { removed, moving };
}

/** Step as seen in a direction (reassembly shows steps in reverse order). */
export function stepAt(proc: Procedure, i: number, dir: Direction) {
  return dir === 'disassemble' ? proc.steps[i] : proc.steps[proc.steps.length - 1 - i];
}

/** Validation mirror of the Python check: requirements satisfied before each removal. */
export function checkProcedure(idx: ModelIndex, proc: Procedure): string[] {
  const errs: string[] = [];
  const removed = idx.closure(proc.start_removed ?? []);
  for (const st of proc.steps) {
    for (const r of st.remove ?? []) {
      if (idx.kind(r) === 'unknown') {
        errs.push(`${proc.id}/${st.id}: ${r} unbekannt`);
        continue;
      }
      const need = idx.closure(idx.requires(r));
      for (const q of need) if (!removed.has(q) && q !== r) errs.push(`${proc.id}/${st.id}: ${r} braucht ${q}`);
      for (const u of stepUnits(idx, [r])) removed.add(u);
      if (idx.kind(r) === 'asm') removed.add(r);
    }
  }
  return errs;
}
