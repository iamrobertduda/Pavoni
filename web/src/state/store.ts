import { create } from 'zustand';
import type { Direction } from '../logic/procedure';

export type Mode = 'explore' | 'procedure' | 'disassembly';

export interface DisassemblyPlan {
  target: string; // part id or assembly id the user wants out
  order: string[]; // refs in removal order (dependencies first, target last)
  idx: number; // number of refs already played (0..order.length)
}

export interface PavoniState {
  selected: string | null; // part id or assembly id
  hidden: Set<string>; // part ids
  isolate: boolean;
  ghostOthers: boolean;
  explode: number;
  sealMap: boolean;
  section: string | null;
  sectionOffset: number; // mm along the section normal
  mode: Mode;
  procId: string | null;
  stepIdx: number;
  dir: Direction;
  animStart: number; // performance.now() when the current step started
  animate: boolean;
  disassembly: DisassemblyPlan | null;
  viewRequest: { name: string; nonce: number } | null;
  ui: boolean;
  treeOpen: boolean;
  lowQuality: boolean;
  modelReady: boolean;
  set: (p: Partial<PavoniState>) => void;
  select: (id: string | null) => void;
  toggleHidden: (pid: string) => void;
  setView: (name: string) => void;
  startProcedure: (id: string, step?: number, dir?: Direction) => void;
  gotoStep: (i: number) => void;
  exitMode: () => void;
}

export const useStore = create<PavoniState>((set, get) => ({
  selected: null,
  hidden: new Set(),
  isolate: false,
  ghostOthers: false,
  explode: 0,
  sealMap: false,
  section: null,
  sectionOffset: 0,
  mode: 'explore',
  procId: null,
  stepIdx: 0,
  dir: 'disassemble',
  animStart: 0,
  animate: true,
  disassembly: null,
  viewRequest: null,
  ui: true,
  treeOpen: true,
  lowQuality: false,
  modelReady: false,
  set: (p) => set(p),
  select: (id) => set({ selected: id }),
  toggleHidden: (pid) => {
    const h = new Set(get().hidden);
    if (h.has(pid)) h.delete(pid);
    else h.add(pid);
    set({ hidden: h });
  },
  setView: (name) => set({ viewRequest: { name, nonce: Math.random() } }),
  startProcedure: (id, step = 0, dir = 'disassemble') =>
    set({ mode: 'procedure', procId: id, stepIdx: step, dir, explode: 0, disassembly: null, animStart: performance.now() }),
  gotoStep: (i) => set({ stepIdx: i, animStart: performance.now() }),
  exitMode: () => set({ mode: 'explore', procId: null, disassembly: null, stepIdx: 0 }),
}));
