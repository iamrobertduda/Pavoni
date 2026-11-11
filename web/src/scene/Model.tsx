import { useGLTF } from '@react-three/drei';
import { type ThreeEvent, useFrame } from '@react-three/fiber';
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { data, model, partsById } from '../data';
import { explodeOffsets, removalDisplay, type InstanceDisplay } from '../logic/explode';
import { cadDirToGl } from '../logic/coords';
import { procedureState, stepAt } from '../logic/procedure';
import { useStore } from '../state/store';
import { makeMaterial, SEAL_COLOR, SELECT_COLOR } from './materials';
import { registry } from './registry';
import { useSectionPlanes } from './section';

const MODEL_URL = `${import.meta.env.BASE_URL}models/pavoni.glb`;
const STEP_SECONDS = 1.4;

export function Model() {
  const gltf = useGLTF(MODEL_URL);
  const root = useRef<THREE.Group>(null!);
  const planes = useSectionPlanes();

  // flatten instance meshes into one group (keeps world transforms)
  const meshes = useMemo(() => {
    const found: THREE.Mesh[] = [];
    gltf.scene.updateMatrixWorld(true);
    gltf.scene.traverse((o) => {
      if ((o as THREE.Mesh).isMesh && model.instPart[o.name]) found.push(o as THREE.Mesh);
    });
    return found;
  }, [gltf]);

  useEffect(() => {
    const g = root.current;
    registry.clear();
    for (const m of meshes) {
      g.attach(m);
      const pid = model.instPart[m.name];
      const part = partsById[pid];
      m.userData.instanceId = m.name;
      m.userData.partId = pid;
      m.userData.base = m.position.clone();
      m.material = makeMaterial(part.material, useStore.getState().lowQuality);
      m.castShadow = !useStore.getState().lowQuality;
      m.receiveShadow = !useStore.getState().lowQuality;
      registry.set(m.name, m);
    }
    registry.ready = true;
    useStore.getState().set({ modelReady: true });
    return () => {
      registry.ready = false;
      useStore.getState().set({ modelReady: false });
    };
  }, [meshes]);

  // apply section planes to all materials
  useEffect(() => {
    for (const m of registry.values()) {
      const mat = m.material as THREE.MeshPhysicalMaterial;
      mat.clippingPlanes = planes;
      mat.clipShadows = true;
      mat.needsUpdate = true;
    }
  }, [planes, meshes]);

  const last = useRef<{ key: string }>({ key: '' });

  useFrame(() => {
    const s = useStore.getState();
    let disp: Record<string, InstanceDisplay>;
    let highlight = new Set<string>();
    let animating = false;
    if (s.mode === 'procedure' && s.procId) {
      const proc = data.procedures.find((p) => p.id === s.procId)!;
      const p = s.animate ? Math.min(1, (performance.now() - s.animStart) / 1000 / STEP_SECONDS) : 1;
      animating = p < 1;
      disp = removalDisplay(data, model, procedureState(model, proc, s.stepIdx, p, s.dir));
      const st = stepAt(proc, s.stepIdx, s.dir);
      for (const r of st?.highlight ?? []) for (const i of model.expand(r)) highlight.add(i);
    } else if (s.mode === 'disassembly' && s.disassembly) {
      const plan = s.disassembly;
      const p = s.animate ? Math.min(1, (performance.now() - s.animStart) / 1000 / STEP_SECONDS) : 1;
      animating = p < 1;
      const removed = new Set<string>();
      const moving = new Map<string, number>();
      plan.order.forEach((ref, k) => {
        const units = model.kind(ref) === 'asm' ? [ref] : model.expand(ref);
        if (k < plan.idx - 1) units.forEach((u) => removed.add(u));
        else if (k === plan.idx - 1) units.forEach((u) => moving.set(u, p));
      });
      disp = removalDisplay(data, model, { removed, moving });
      highlight = new Set(model.expand(plan.target));
    } else {
      const off = explodeOffsets(data, s.explode);
      disp = Object.fromEntries(Object.entries(off).map(([k, v]) => [k, { offset: v, visible: true, active: false }]));
    }
    // positions
    for (const [iid, m] of registry) {
      const d = disp[iid];
      if (!d) continue;
      const o = cadDirToGl(d.offset);
      const b = m.userData.base as THREE.Vector3;
      m.position.set(b.x + o[0] / 1000, b.y + o[1] / 1000, b.z + o[2] / 1000);
    }
    // materials / visibility only when something relevant changed
    const key = [s.selected, s.isolate, s.ghostOthers, s.sealMap, [...s.hidden].join(','), s.mode, s.procId, s.stepIdx, s.dir,
      s.disassembly?.idx, animating ? 'a' : '', [...highlight].join(',')].join('|') + Object.values(disp).map((d) => (d.visible ? '1' : '0') + (d.active ? 'a' : '')).join('');
    if (key === last.current.key) return;
    last.current.key = key;
    const selInst = s.selected ? new Set(model.expand(s.selected)) : new Set<string>();
    for (const [iid, m] of registry) {
      const pid = model.instPart[iid];
      const part = partsById[pid];
      const d = disp[iid];
      const mat = m.material as THREE.MeshPhysicalMaterial;
      const base = mat.userData.base as { color: THREE.Color; transmission: number; transparent: boolean; opacity: number };
      let visible = (d?.visible ?? true) && !s.hidden.has(pid);
      if (s.isolate && s.selected && !selInst.has(iid)) visible = false;
      m.visible = visible;
      const isSel = selInst.has(iid);
      const ghost = (s.ghostOthers && s.selected && !isSel) || (s.sealMap && part.kind !== 'seal');
      mat.color.copy(base.color);
      mat.emissive.set(0, 0, 0);
      mat.emissiveIntensity = 1;
      if (s.sealMap && part.kind === 'seal') {
        mat.color.copy(SEAL_COLOR);
        mat.emissive.copy(SEAL_COLOR).multiplyScalar(0.45);
      }
      if (highlight.has(iid) || d?.active) mat.emissive.set('#ffb000').multiplyScalar(0.35);
      if (isSel) mat.emissive.copy(SELECT_COLOR).multiplyScalar(0.55);
      if (ghost) {
        mat.transparent = true;
        mat.opacity = 0.1;
        mat.depthWrite = false;
        mat.transmission = 0;
      } else {
        mat.transparent = base.transparent;
        mat.opacity = base.opacity;
        mat.depthWrite = !base.transparent;
        mat.transmission = base.transmission;
      }
      m.renderOrder = ghost || base.transparent ? 2 : 0;
      mat.needsUpdate = true;
    }
  });

  const onClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    let o: THREE.Object3D | null = e.object;
    while (o && !o.userData.partId) o = o.parent;
    if (!o) return;
    const s = useStore.getState();
    if (s.mode === 'explore' || s.mode === 'disassembly') s.select(o.userData.partId);
    else s.select(o.userData.partId);
  };

  return <group ref={root} onClick={onClick} />;
}

useGLTF.preload(MODEL_URL);
