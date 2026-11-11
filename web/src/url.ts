// Deep links: ?part=<id>&proc=<id>&step=<n>&dir=assemble&view=<name>&explode=<0..1>&seals=1&section=<name>
// Render flags: ui=0 (no panels), bg=transparent, anim=0 (no animations), quality=low (software rendering)
import { data } from './data';
import { useStore } from './state/store';

export function readUrl() {
  const q = new URLSearchParams(location.search);
  const s = useStore.getState();
  const patch: Partial<typeof s> = {};
  if (q.get('ui') === '0') patch.ui = false;
  if (q.get('anim') === '0') patch.animate = false;
  if (q.get('quality') === 'low') patch.lowQuality = true;
  if (window.matchMedia?.('(max-width: 760px)').matches) patch.treeOpen = false;
  const part = q.get('part');
  if (part) patch.selected = part;
  if (q.get('explode')) patch.explode = Math.max(0, Math.min(1, parseFloat(q.get('explode')!)));
  if (q.get('seals') === '1') patch.sealMap = true;
  const sec = q.get('section');
  if (sec && data.sections[sec]) patch.section = sec;
  s.set(patch);
  const proc = q.get('proc');
  if (proc && data.procedures.some((p) => p.id === proc)) {
    s.startProcedure(proc, Math.max(0, parseInt(q.get('step') ?? '1', 10) - 1), q.get('dir') === 'assemble' ? 'assemble' : 'disassemble');
  }
  const view = q.get('view');
  return { view: view && data.views[view] ? view : 'iso', transparent: q.get('bg') === 'transparent' };
}

export function syncUrl() {
  let prev = '';
  useStore.subscribe((s) => {
    const q = new URLSearchParams(location.search);
    const setOrDel = (k: string, v: string | null) => (v ? q.set(k, v) : q.delete(k));
    setOrDel('part', s.selected);
    setOrDel('proc', s.mode === 'procedure' ? s.procId : null);
    setOrDel('step', s.mode === 'procedure' ? String(s.stepIdx + 1) : null);
    setOrDel('dir', s.mode === 'procedure' && s.dir === 'assemble' ? 'assemble' : null);
    setOrDel('seals', s.sealMap ? '1' : null);
    setOrDel('section', s.section);
    const str = q.toString();
    if (str !== prev) {
      prev = str;
      history.replaceState(null, '', str ? `?${str}` : location.pathname);
    }
  });
}
