// Filled cut faces for the section view (PLAN 9.6), stencil technique as in the three.js
// "clipping stencil" example: per cap colour group, back faces increment and front faces
// decrement the stencil, then a plane in the cut draws where the stencil is non-zero.
import { useFrame } from '@react-three/fiber';
import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { model, partsById } from '../data';
import { useStore } from '../state/store';
import { MATERIALS, SEAL_COLOR } from './materials';
import { registry } from './registry';
import { useSectionPlanes } from './section';

const CAP_COLORS: Record<string, string> = {
  chrome: '#9aa1a9',
  stainless: '#a7adb3',
  steel: '#8d939a',
  brass: '#c79a3c',
  copper: '#b46a3c',
};

function capColor(material: string, kind: string, sealMap: boolean) {
  if (kind === 'seal') return sealMap ? SEAL_COLOR.getStyle() : MATERIALS[material]?.color ?? '#cc4422';
  return CAP_COLORS[material] ?? MATERIALS[material]?.color ?? '#888888';
}

export function SectionCaps() {
  const planes = useSectionPlanes();
  const sealMap = useStore((s) => s.sealMap);
  const ready = useStore((s) => s.modelReady);
  const group = useRef<THREE.Group>(null!);
  const added = useRef<THREE.Object3D[]>([]);
  const caps = useRef<THREE.Mesh[]>([]);

  useEffect(() => {
    // remove previous helpers
    for (const o of added.current) o.parent?.remove(o);
    added.current = [];
    for (const c of caps.current) {
      c.parent?.remove(c);
      (c.material as THREE.Material).dispose();
    }
    caps.current = [];
    if (!planes.length || !registry.ready) return;
    // group meshes by cap colour
    const groups = new Map<string, THREE.Mesh[]>();
    for (const [iid, m] of registry) {
      const p = partsById[model.instPart[iid]];
      const key = capColor(p.material, p.kind, sealMap);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(m);
    }
    let gi = 0;
    const base = new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: false, depthTest: false, stencilWrite: true, stencilFunc: THREE.AlwaysStencilFunc });
    for (const [color, meshes] of groups) {
      gi++;
      const back = base.clone();
      back.side = THREE.BackSide;
      back.clippingPlanes = planes;
      back.stencilFail = back.stencilZFail = back.stencilZPass = THREE.IncrementWrapStencilOp;
      const front = base.clone();
      front.side = THREE.FrontSide;
      front.clippingPlanes = planes;
      front.stencilFail = front.stencilZFail = front.stencilZPass = THREE.DecrementWrapStencilOp;
      for (const m of meshes) {
        for (const mat of [back, front]) {
          const s = new THREE.Mesh(m.geometry, mat);
          s.renderOrder = 10 + gi * 3;
          s.raycast = () => null;
          m.add(s);
          added.current.push(s);
        }
      }
      const capMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        metalness: 0.1,
        roughness: 0.7,
        stencilWrite: true,
        stencilRef: 0,
        stencilFunc: THREE.NotEqualStencilFunc,
        stencilFail: THREE.ReplaceStencilOp,
        stencilZFail: THREE.ReplaceStencilOp,
        stencilZPass: THREE.ReplaceStencilOp,
        side: THREE.DoubleSide,
      });
      const cap = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), capMat);
      cap.renderOrder = 10 + gi * 3 + 1;
      cap.raycast = () => null;
      cap.onAfterRender = (renderer) => renderer.clearStencil();
      group.current.add(cap);
      caps.current.push(cap);
    }
    return () => {
      base.dispose();
    };
  }, [planes, sealMap, ready]);

  // keep the cap planes in the cut plane
  useFrame(() => {
    if (!planes.length) return;
    const pl = planes[0];
    const p = pl.coplanarPoint(new THREE.Vector3());
    for (const c of caps.current) {
      c.position.copy(p);
      c.lookAt(p.clone().sub(pl.normal));
    }
  });

  return <group ref={group} />;
}
