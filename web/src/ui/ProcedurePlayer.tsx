import { useEffect } from 'react';
import { data, partsById } from '../data';
import { procedureState, stepAt, stepUnits } from '../logic/procedure';
import { removalDisplay } from '../logic/explode';
import { model } from '../data';
import { refName } from './names';
import { useStore } from '../state/store';

const PRE: Record<string, string> = {
  unplugged: 'Netzstecker gezogen',
  cold: 'Maschine kalt',
  depressurized: 'drucklos (Dampfhahn offen)',
  boiler_empty: 'Kessel entleert',
};

export function ProcedureList() {
  const start = useStore((s) => s.startProcedure);
  return (
    <section className="panel procs">
      <h2>Anleitungen</h2>
      <ul className="proc-list">
        {data.procedures.map((p) => (
          <li key={p.id}>
            <button className="link" onClick={() => start(p.id)} data-proc={p.id}>{p.title.de}</button>
            <span className="muted small"> · {p.steps.length} Schritte · ca. {p.duration_min} min · Schwierigkeit {p.difficulty}/5</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function ProcedurePlayer() {
  const procId = useStore((s) => s.procId);
  const stepIdx = useStore((s) => s.stepIdx);
  const dir = useStore((s) => s.dir);
  const gotoStep = useStore((s) => s.gotoStep);
  const set = useStore((s) => s.set);
  const exit = useStore((s) => s.exitMode);
  const setView = useStore((s) => s.setView);
  const proc = data.procedures.find((p) => p.id === procId);
  const st = proc ? stepAt(proc, stepIdx, dir) : undefined;
  useEffect(() => {
    if (!proc || !st) return;
    // Aim at the middle of the way the parts of this step travel: follows parts whose assembly
    // sits on the bench (detached earlier) and keeps both the start and the end of the move in
    // frame (aiming at the start alone left a detached group half outside the view).
    const start = removalDisplay(data, model, procedureState(model, proc, stepIdx, 0, dir));
    const end = removalDisplay(data, model, procedureState(model, proc, stepIdx, 1, dir));
    const units = stepUnits(model, st.remove ?? st.highlight ?? []);
    const insts = units.flatMap((u) => (model.kind(u) === 'asm' ? model.expand(u) : model.instPart[u] ? [u] : []));
    const off: [number, number, number] = [0, 0, 0];
    for (const i of insts) for (let k = 0; k < 3; k++) off[k] += ((start[i]?.offset[k] ?? 0) + (end[i]?.offset[k] ?? 0)) / 2 / insts.length;
    if (st.camera) setView(st.camera, off);
    set({ section: st.section ?? null, sectionOffset: 0 });
  }, [st, setView, set, proc, stepIdx, dir]);
  if (!proc || !st) return null;
  const n = proc.steps.length;
  const tools = (st.tools ?? []).map((t) => data.tools.find((x) => x.id === t)?.name.de ?? t);
  const removed = (st.remove ?? []).map(refName);
  return (
    <section className="panel player" data-testid="procedure-player">
      <header>
        <h2>{proc.title.de}</h2>
        <button className="close" onClick={exit} aria-label="Anleitung schließen">×</button>
      </header>
      <div className="row">
        <button className={dir === 'disassemble' ? 'on' : ''} onClick={() => set({ dir: 'disassemble', stepIdx: 0, animStart: performance.now() })}>Zerlegen</button>
        <button className={dir === 'assemble' ? 'on' : ''} onClick={() => set({ dir: 'assemble', stepIdx: 0, animStart: performance.now() })}>Zusammenbauen</button>
      </div>
      {stepIdx === 0 && dir === 'disassemble' && (
        <div className="pre small">
          Vorher: {proc.preconditions.map((c) => PRE[c] ?? c).join(' · ')}
          {proc.danger && <div className="warn">{proc.danger.de}</div>}
          {proc.parts_needed && proc.parts_needed.length > 0 && (
            <div className="needed">
              Ersatzteile:{' '}
              {proc.parts_needed.map((pid) => (
                <span key={pid} className="needed-item">
                  {partsById[pid]?.name.de ?? pid}
                  {partsById[pid]?.order_terms?.[0] && <code> {partsById[pid].order_terms![0]}</code>}
                </span>
              ))}
              <div className="muted">Dichtungsmaße vor der Bestellung an den ausgebauten Teilen nachmessen.</div>
            </div>
          )}
        </div>
      )}
      <div className="step" data-step={st.id}>
        <div className="muted small">Schritt {stepIdx + 1} von {n}</div>
        <h3>{st.title.de}</h3>
        <p>{dir === 'assemble' && st.reassembly ? st.reassembly.de : st.text.de}</p>
        {dir === 'assemble' && st.reassembly && <p className="muted small">Ausbau war: {st.text.de}</p>}
        {st.warn && <div className="warn">{st.warn.de}</div>}
        {removed.length > 0 && <p className="small">{dir === 'disassemble' ? 'Raus' : 'Rein'}: {removed.join(', ')}</p>}
        {tools.length > 0 && <p className="small">Werkzeug: {tools.join(', ')}</p>}
      </div>
      <div className="row nav">
        <button disabled={stepIdx === 0} onClick={() => gotoStep(stepIdx - 1)}>‹ Zurück</button>
        <button onClick={() => gotoStep(stepIdx)}>↻</button>
        <button disabled={stepIdx >= n - 1} onClick={() => gotoStep(stepIdx + 1)} data-testid="next-step">Weiter ›</button>
      </div>
    </section>
  );
}

export function DisassemblyPlayer() {
  const plan = useStore((s) => s.disassembly);
  const set = useStore((s) => s.set);
  const exit = useStore((s) => s.exitMode);
  if (!plan) return null;
  const name = refName;
  return (
    <section className="panel player">
      <header>
        <h2>Ausbau: {name(plan.target)}</h2>
        <button className="close" onClick={exit} aria-label="Schließen">×</button>
      </header>
      <ol className="small order">
        {plan.order.map((r, k) => (
          <li key={r} className={k < plan.idx ? 'done' : k === plan.idx ? 'next' : ''}>{name(r)}</li>
        ))}
      </ol>
      <div className="row nav">
        <button disabled={plan.idx === 0} onClick={() => set({ disassembly: { ...plan, idx: plan.idx - 1 }, animStart: performance.now() })}>‹</button>
        <button disabled={plan.idx >= plan.order.length} onClick={() => set({ disassembly: { ...plan, idx: plan.idx + 1 }, animStart: performance.now() })}>Nächstes Teil ›</button>
        <button onClick={() => set({ disassembly: { ...plan, idx: plan.order.length }, animStart: performance.now() - 5000 })}>Alle</button>
      </div>
    </section>
  );
}
