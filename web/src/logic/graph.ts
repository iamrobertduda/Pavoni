// Parts, instances, assemblies and the requires_removed DAG.
import type { AppData, Assembly, Part } from '../data/types';

export type RefKind = 'part' | 'inst' | 'asm' | 'unknown';

export interface ModelIndex {
  parts: Record<string, Part>;
  assemblies: Record<string, Assembly>;
  /** built instance id -> part id */
  instPart: Record<string, string>;
  /** built instance id -> assembly id */
  instAsm: Record<string, string>;
  builtInstances: string[];
  kind(ref: string): RefKind;
  /** instances a ref stands for (built only) */
  expand(ref: string): string[];
  requires(ref: string): string[];
  /** transitive closure of refs plus their requirements (instances and assembly ids) */
  closure(refs: string[]): Set<string>;
  /** removal order for refs (dependencies first) */
  removalOrder(target: string): string[];
  chain(asm: string): string[];
}

export function asmChain(asm: string): string[] {
  const p = asm.split('.');
  return p.map((_, i) => p.slice(0, i + 1).join('.'));
}

export function buildModelIndex(d: Pick<AppData, 'parts' | 'assemblies' | 'instances'>): ModelIndex {
  const parts: Record<string, Part> = Object.fromEntries(d.parts.map((p) => [p.id, p]));
  const assemblies: Record<string, Assembly> = Object.fromEntries(d.assemblies.map((a) => [a.id, a]));
  const instPart: Record<string, string> = {};
  const instAsm: Record<string, string> = {};
  for (const [iid, g] of Object.entries(d.instances)) {
    instPart[iid] = g.part;
    instAsm[iid] = g.assembly;
  }
  const builtInstances = Object.keys(d.instances);

  const kind = (ref: string): RefKind => {
    if (assemblies[ref]) return 'asm';
    if (parts[ref]) return 'part';
    const pid = ref.split('__')[0];
    if (ref.includes('__') && parts[pid]?.instances.includes(ref)) return 'inst';
    return 'unknown';
  };
  const expand = (ref: string): string[] => {
    switch (kind(ref)) {
      case 'part':
        return parts[ref].instances.filter((i) => instPart[i]);
      case 'inst':
        return instPart[ref] ? [ref] : [];
      case 'asm':
        return builtInstances.filter((i) => instAsm[i] === ref || instAsm[i].startsWith(ref + '.'));
      default:
        return [];
    }
  };
  const requires = (ref: string): string[] => {
    switch (kind(ref)) {
      case 'asm':
        return assemblies[ref].requires_removed ?? [];
      case 'part':
        return parts[ref].requires_removed;
      case 'inst':
        return parts[ref.split('__')[0]].requires_removed;
      default:
        return [];
    }
  };
  const closure = (refs: string[]): Set<string> => {
    const out = new Set<string>();
    const stack = [...refs];
    while (stack.length) {
      const r = stack.pop()!;
      const k = kind(r);
      if (k === 'part') {
        const inst = expand(r);
        const fresh = inst.filter((i) => !out.has(i));
        fresh.forEach((i) => out.add(i));
        if (fresh.length || !inst.length) stack.push(...requires(r));
      } else if (k === 'inst' || k === 'asm') {
        if (!out.has(r)) {
          out.add(r);
          stack.push(...requires(r));
        }
      }
    }
    return out;
  };
  const removalOrder = (target: string): string[] => {
    // depth-first post order over requires: dependencies first, target last
    const order: string[] = [];
    const seen = new Set<string>();
    const visit = (r: string) => {
      const key = kind(r) === 'inst' ? r.split('__')[0] : r;
      if (seen.has(key)) return;
      seen.add(key);
      for (const q of requires(r)) visit(q);
      order.push(key);
    };
    visit(target);
    return order;
  };
  return { parts, assemblies, instPart, instAsm, builtInstances, kind, expand, requires, closure, removalOrder, chain: asmChain };
}
