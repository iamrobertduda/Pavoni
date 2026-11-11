import { assembliesById, data, model, partsById } from '../data';
import type { DimEntry } from '../data/types';
import { useStore } from '../state/store';
import { ConfBadge, StatusBadge } from './Badge';
import { MATERIALS } from '../scene/materials';
import { refName } from './names';

const KIND: Record<string, string> = { seal: 'Dichtung', fastener: 'Befestigung', structural: 'Bauteil', electrical: 'Elektrik', accessory: 'Zubehör' };

function fmt(e: DimEntry) {
  const v = Math.round(e.resolved * 10) / 10;
  return `${v.toLocaleString('de-DE')} ${e.unit === 'mm' ? 'mm' : e.unit}`;
}

function Dim({ k }: { k: string }) {
  const e = data.dims[k];
  if (!e) return null;
  const weak = e.confidence === 'guess' || e.confidence === 'photo';
  return (
    <li className={weak ? 'dim weak' : 'dim'}>
      <span className="dim-key">{k}</span>
      <span className="dim-val">{weak ? `ca. ${fmt(e)}` : fmt(e)}</span>
      <ConfBadge c={e.confidence} />
      <div className="dim-src">
        Quelle: {e.source}
        {e.note && <div className="dim-note">{e.note}</div>}
        {e.alt?.map((a) => (
          <div className="dim-note" key={a.source}>
            Abweichende Angabe: {a.value} {e.unit} ({a.source})
          </div>
        ))}
      </div>
    </li>
  );
}

export function InfoPanel() {
  const sel = useStore((s) => s.selected);
  const set = useStore((s) => s.set);
  const isolate = useStore((s) => s.isolate);
  const ghost = useStore((s) => s.ghostOthers);
  if (!sel) return null;
  const asm = assembliesById[sel];
  if (asm) {
    const parts = data.parts.filter((p) => p.assembly === sel || p.assembly.startsWith(sel + '.'));
    return (
      <section className="panel info">
        <header>
          <h2>{asm.name.de}</h2>
          <button className="close" onClick={() => set({ selected: null })} aria-label="Schließen">×</button>
        </header>
        <p className="muted">Baugruppe · {parts.length} Positionen{asm.detachable ? ' · als Einheit abnehmbar' : ''}</p>
        {asm.notes && <p>{asm.notes.de}</p>}
      </section>
    );
  }
  const p = partsById[sel];
  if (!p) return null;
  const built = p.instances.filter((i) => model.instPart[i]).length;
  const dims = p.dims ?? [];
  const sealWarn = p.kind === 'seal' && dims.some((k) => data.dims[k] && data.dims[k].confidence !== 'measured');
  const tools = (p.tools ?? []).map((t) => data.tools.find((x) => x.id === t)?.name.de ?? t);
  const order = model.removalOrder(p.id).filter((r) => r !== p.id);
  const procs = data.procedures.filter((pr) => pr.steps.some((s) => (s.remove ?? []).some((r) => r === p.id || p.instances.includes(r) || p.assembly === r || p.assembly.startsWith(r + '.'))));
  return (
    <section className="panel info" data-testid="info-panel">
      <header>
        <h2>{p.name.de}</h2>
        <button className="close" onClick={() => set({ selected: null })} aria-label="Schließen">×</button>
      </header>
      <div className="meta">
        {p.pos !== null && <span className="pos">Pos. {p.pos}</span>}
        <span>{KIND[p.kind]}</span>
        <span>{p.instances.length}×</span>
        <span>{MATERIALS[p.material]?.label ?? p.material}</span>
        {p.wear_part && <span className="badge wear">Verschleißteil</span>}
        <StatusBadge s={p.status} />
      </div>
      {(p.name.en || p.name.it) && (
        <p className="muted small">
          {p.name.en && <>EN: {p.name.en}</>} {p.name.it && <>· IT: {p.name.it}</>}
        </p>
      )}
      <p className="muted small">
        Baugruppe: {assembliesById[p.assembly]?.name.de ?? p.assembly} · ID <code>{p.id}</code>
        {built < p.instances.length && <> · {p.instances.length - built} Instanz(en) noch nicht modelliert</>}
      </p>
      {sealWarn && <div className="warn">Maße nicht am Gerät gemessen. Vor der Bestellung die ausgebaute Dichtung nachmessen.</div>}
      {p.notes && <p>{p.notes.de}</p>}
      {dims.length > 0 && (
        <>
          <h3>Maße</h3>
          <ul className="dims">{dims.map((k) => <Dim key={k} k={k} />)}</ul>
        </>
      )}
      {p.thread && <p className="small">Gewinde: {p.thread}</p>}
      {tools.length > 0 && <p className="small">Werkzeug: {tools.join(', ')}</p>}
      {p.order_terms && p.order_terms.length > 0 && (
        <>
          <h3>Ersatzteil-Suchbegriffe</h3>
          <ul className="terms">{p.order_terms.map((t) => <li key={t}><code>{t}</code></li>)}</ul>
        </>
      )}
      {order.length > 0 && (
        <>
          <h3>Vorher ausbauen</h3>
          <ol className="small order">
            {order.map((r) => (
              <li key={r}>
                <button className="link" onClick={() => set({ selected: r.split('__')[0] })}>{refName(r)}</button>
              </li>
            ))}
          </ol>
        </>
      )}
      {p.open_questions && p.open_questions.length > 0 && (
        <>
          <h3>Offene Fragen</h3>
          <ul className="small">{p.open_questions.map((q) => <li key={q}>{q}</li>)}</ul>
        </>
      )}
      {p.sources && p.sources.length > 0 && <p className="small muted">Quellen: {p.sources.join(', ')}</p>}
      <div className="row">
        <button className={isolate ? 'on' : ''} onClick={() => set({ isolate: !isolate })}>Isolieren</button>
        <button className={ghost ? 'on' : ''} onClick={() => set({ ghostOthers: !ghost })}>Rest transparent</button>
        {order.length > 0 && <DisassembleButton id={p.id} />}
      </div>
      {procs.length > 0 && (
        <p className="small">
          Anleitung:{' '}
          {procs.map((pr) => (
            <button key={pr.id} className="link" onClick={() => useStore.getState().startProcedure(pr.id)}>{pr.title.de}</button>
          ))}
        </p>
      )}
    </section>
  );
}

function DisassembleButton({ id }: { id: string }) {
  const set = useStore((s) => s.set);
  return (
    <button
      onClick={() => {
        const order = model.removalOrder(id);
        set({ mode: 'disassembly', disassembly: { target: id, order, idx: 0 }, procId: null, explode: 0, animStart: performance.now() });
      }}
    >
      Ausbauen zeigen
    </button>
  );
}
