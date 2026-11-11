// Seal overview (PLAN 9.5): all seals with size, confidence and order terms.
import { data } from '../data';
import type { Part } from '../data/types';
import { useStore } from '../state/store';
import { ConfBadge } from './Badge';

function sizeText(p: Part) {
  const keys = p.dims ?? [];
  const v = keys.map((k) => data.dims[k]).filter(Boolean);
  if (!v.length) return 'Maß unbekannt';
  return v.map((e) => (Math.round(e.resolved * 100) / 100).toLocaleString('de-DE')).join(' × ') + ' mm';
}

function weakest(p: Part) {
  const order = ['measured', 'catalog', 'spec', 'photo', 'guess'] as const;
  let w = 0;
  for (const k of p.dims ?? []) {
    const c = data.dims[k]?.confidence;
    if (c) w = Math.max(w, order.indexOf(c));
  }
  return order[w];
}

export function SealList() {
  const select = useStore((s) => s.select);
  const selected = useStore((s) => s.selected);
  const seals = data.parts.filter((p) => p.kind === 'seal' && !(p as Part & { optional?: boolean }).optional);
  const byAsm = new Map<string, Part[]>();
  for (const p of seals) {
    const top = data.assemblies.find((a) => a.id === p.assembly)?.name.de ?? p.assembly;
    if (!byAsm.has(top)) byAsm.set(top, []);
    byAsm.get(top)!.push(p);
  }
  return (
    <section className="panel seals" data-testid="seal-list">
      <h2>Dichtungen ({seals.reduce((n, p) => n + p.instances.length, 0)} Stück)</h2>
      <p className="muted small">Alle Dichtungen in Signalfarbe, der Rest transparent. Maße sind Katalog- oder Schätzwerte: vor der Bestellung nachmessen.</p>
      {[...byAsm.entries()].map(([asm, list]) => (
        <div key={asm} className="seal-group">
          <h3>{asm}</h3>
          <ul>
            {list.map((p) => (
              <li key={p.id} className={selected === p.id ? 'sel' : ''}>
                <button className="link" onClick={() => select(p.id)} data-seal={p.id}>
                  {p.pos !== null && <span className="pos">{p.pos}</span>} {p.name.de}
                  {p.instances.length > 1 && <span className="muted"> ×{p.instances.length}</span>}
                </button>
                <div className="small">
                  {sizeText(p)} <ConfBadge c={weakest(p)} />
                  {p.order_terms?.[0] && <code> {p.order_terms[0]}</code>}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}
