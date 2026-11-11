import { useMemo, useState } from 'react';
import { data } from '../data';
import type { Assembly, Part } from '../data/types';
import { useStore } from '../state/store';

interface Node {
  asm: Assembly;
  children: Node[];
  parts: Part[];
}

function buildTree(): Node[] {
  const nodes = new Map<string, Node>();
  for (const a of data.assemblies) nodes.set(a.id, { asm: a, children: [], parts: [] });
  const roots: Node[] = [];
  for (const a of data.assemblies) {
    const parent = a.id.includes('.') ? a.id.slice(0, a.id.lastIndexOf('.')) : null;
    if (parent && nodes.get(parent)) nodes.get(parent)!.children.push(nodes.get(a.id)!);
    else roots.push(nodes.get(a.id)!);
  }
  for (const p of data.parts) nodes.get(p.assembly)?.parts.push(p);
  for (const n of nodes.values()) n.parts.sort((a, b) => (a.pos ?? 999) - (b.pos ?? 999));
  return roots;
}

function matches(p: Part, q: string) {
  if (!q) return true;
  const s = `${p.name.de} ${p.name.en ?? ''} ${p.name.it ?? ''} ${p.id} ${p.pos ?? ''} ${(p.order_terms ?? []).join(' ')}`.toLowerCase();
  return q
    .toLowerCase()
    .split(/\s+/)
    .every((w) => s.includes(w));
}

function countMatches(n: Node, q: string): number {
  return n.parts.filter((p) => matches(p, q)).length + n.children.reduce((s, c) => s + countMatches(c, q), 0);
}

function TreeNode({ n, q, depth }: { n: Node; q: string; depth: number }) {
  const [open, setOpen] = useState(depth === 0 ? false : true);
  const selected = useStore((s) => s.selected);
  const hidden = useStore((s) => s.hidden);
  const select = useStore((s) => s.select);
  const toggleHidden = useStore((s) => s.toggleHidden);
  const c = countMatches(n, q);
  if (q && c === 0) return null;
  const isOpen = open || !!q;
  return (
    <li className="tree-asm">
      <div className={`tree-row asm ${selected === n.asm.id ? 'sel' : ''}`}>
        <button className="twist" onClick={() => setOpen(!open)} aria-label={isOpen ? 'zuklappen' : 'aufklappen'}>{isOpen ? '▾' : '▸'}</button>
        <button className="tree-label" onClick={() => select(n.asm.id)}>{n.asm.name.de}</button>
        <span className="muted small">{c}</span>
      </div>
      {isOpen && (
        <ul>
          {n.children.map((ch) => <TreeNode key={ch.asm.id} n={ch} q={q} depth={depth + 1} />)}
          {n.parts.filter((p) => matches(p, q)).map((p) => (
            <li key={p.id} className={`tree-row part ${selected === p.id ? 'sel' : ''} ${p.status === 'planned' ? 'planned' : ''}`}>
              <button className={`eye ${hidden.has(p.id) ? 'off' : ''}`} onClick={() => toggleHidden(p.id)} title="Ein-/Ausblenden" aria-label="Ein-/Ausblenden">
                {hidden.has(p.id) ? '○' : '●'}
              </button>
              <button className="tree-label" onClick={() => select(p.id)} data-part={p.id}>
                {p.pos !== null && <span className="pos">{p.pos}</span>} {p.name.de}
                {p.instances.length > 1 && <span className="muted"> ×{p.instances.length}</span>}
              </button>
              {p.kind === 'seal' && <span className="dot seal" title="Dichtung" />}
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

export function PartTree() {
  const [q, setQ] = useState('');
  const tree = useMemo(() => buildTree(), []);
  return (
    <section className="panel tree">
      <input className="search" placeholder="Teil suchen (Name, Pos., Bestellnr.)" value={q} onChange={(e) => setQ(e.target.value)} />
      <ul className="tree-root">{tree.map((n) => <TreeNode key={n.asm.id} n={n} q={q} depth={0} />)}</ul>
    </section>
  );
}
