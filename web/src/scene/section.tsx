import { useMemo } from 'react';
import * as THREE from 'three';
import { data } from '../data';
import { cadDirToGl, cadToGl } from '../logic/coords';
import { useStore } from '../state/store';

/** Clipping plane for the active section preset (empty array = no section). */
export function useSectionPlanes(): THREE.Plane[] {
  const section = useStore((s) => s.section);
  const offset = useStore((s) => s.sectionOffset);
  return useMemo(() => {
    if (!section || !data.sections[section]) return [];
    const sec = data.sections[section];
    const n = new THREE.Vector3(...cadDirToGl(sec.normal)).normalize();
    const p = new THREE.Vector3(...cadToGl(sec.point)).addScaledVector(n, offset / 1000);
    // keep the half-space opposite to the normal (normal points at the viewer side that is cut away)
    return [new THREE.Plane().setFromNormalAndCoplanarPoint(n.clone().negate(), p)];
  }, [section, offset]);
}
