import { data, partsById } from '../data';

/** Display name for a part, instance or assembly id. */
export function refName(r: string): string {
  if (partsById[r]) return partsById[r].name.de;
  const a = data.assemblies.find((x) => x.id === r);
  if (a) return a.name.de;
  if (r.includes('__')) {
    const [pid, n] = r.split('__');
    const p = partsById[pid];
    if (p) return p.instances.length > 1 ? `${p.name.de} (${n})` : p.name.de;
  }
  return r;
}
