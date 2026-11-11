// Keyboard (Phase 7): ← / → step through a procedure or the disassembly order, Esc leaves the mode
// or clears the selection. Ignored while typing in a field.
import { useEffect } from 'react';
import { data } from '../data';
import { useStore } from '../state/store';

export function useKeyboard() {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      const s = useStore.getState();
      const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (d && s.mode === 'procedure') {
        const n = data.procedures.find((p) => p.id === s.procId)?.steps.length ?? 0;
        const i = s.stepIdx + d;
        if (i >= 0 && i < n) s.gotoStep(i);
        e.preventDefault();
      } else if (d && s.mode === 'disassembly' && s.disassembly) {
        const plan = s.disassembly;
        const idx = plan.idx + d;
        if (idx >= 0 && idx <= plan.order.length) s.set({ disassembly: { ...plan, idx }, animStart: performance.now() });
        e.preventDefault();
      } else if (e.key === 'Escape') {
        if (s.mode !== 'explore') s.exitMode();
        else s.select(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);
}
