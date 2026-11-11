import { data } from '../data';
import { useStore } from '../state/store';

export function Toolbar() {
  const explode = useStore((s) => s.explode);
  const sealMap = useStore((s) => s.sealMap);
  const section = useStore((s) => s.section);
  const offset = useStore((s) => s.sectionOffset);
  const mode = useStore((s) => s.mode);
  const set = useStore((s) => s.set);
  const setView = useStore((s) => s.setView);
  const treeOpen = useStore((s) => s.treeOpen);
  return (
    <div className="toolbar">
      <button className="menu" onClick={() => set({ treeOpen: !treeOpen })} aria-label="Teilebaum">☰</button>
      <label className="explode" title="Explosionsansicht">
        <span>Explosion</span>
        <input type="range" min={0} max={1} step={0.01} value={explode} disabled={mode !== 'explore'}
          onChange={(e) => set({ explode: parseFloat(e.target.value) })} data-testid="explode" />
      </label>
      <button className={sealMap ? 'on' : ''} onClick={() => set({ sealMap: !sealMap })} data-testid="sealmap">Dichtungen</button>
      <select value={section ?? ''} onChange={(e) => set({ section: e.target.value || null, sectionOffset: 0 })} data-testid="section">
        <option value="">Kein Schnitt</option>
        {Object.entries(data.sections).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
      </select>
      {section && (
        <input type="range" min={-60} max={60} step={0.5} value={offset} onChange={(e) => set({ sectionOffset: parseFloat(e.target.value) })} title="Schnittebene verschieben" />
      )}
      <select value="" onChange={(e) => e.target.value && setView(e.target.value)} aria-label="Ansicht">
        <option value="">Ansicht…</option>
        {Object.entries(data.views).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
      </select>
    </div>
  );
}
