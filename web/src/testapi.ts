// window.__pavoni for tests and render scripts (PLAN 9).
import { data, model } from './data';
import { registry } from './scene/registry';
import { useStore } from './state/store';

export function installTestApi() {
  const api = {
    get ready() {
      return !!(window as unknown as { __pavoniReady?: boolean }).__pavoniReady;
    },
    select: (id: string | null) => useStore.getState().select(id),
    setExplode: (x: number) => useStore.getState().set({ explode: x, mode: 'explore' }),
    setView: (name: string) => useStore.getState().setView(name),
    setSealMap: (on: boolean) => useStore.getState().set({ sealMap: on }),
    setSection: (name: string | null, offset = 0) => useStore.getState().set({ section: name, sectionOffset: offset }),
    gotoStep: (proc: string, n: number, dir: 'disassemble' | 'assemble' = 'disassemble') => {
      const s = useStore.getState();
      if (s.procId !== proc || s.mode !== 'procedure' || s.dir !== dir) s.startProcedure(proc, n, dir);
      else s.gotoStep(n);
    },
    exitMode: () => useStore.getState().exitMode(),
    state: () => {
      const s = useStore.getState();
      return { selected: s.selected, explode: s.explode, mode: s.mode, procId: s.procId, stepIdx: s.stepIdx, sealMap: s.sealMap, section: s.section,
        view: s.viewRequest?.name ?? null };
    },
    /** world-space (GL, m) position of an instance mesh */
    instancePosition: (iid: string) => {
      const m = registry.get(iid);
      return m ? m.position.toArray() : null;
    },
    instanceVisible: (iid: string) => registry.get(iid)?.visible ?? null,
    instances: () => [...registry.keys()],
    capCount: () => registry.capCount,
    frames: () => registry.frames,
    data,
    model,
  };
  (window as unknown as { __pavoni: typeof api }).__pavoni = api;
}
