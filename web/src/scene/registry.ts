import type * as THREE from 'three';

/** instance id -> mesh, filled once the GLB is loaded */
class Registry extends Map<string, THREE.Mesh> {
  ready = false;
  /** number of section cap planes currently shown (test API) */
  capCount = 0;
  frames = 0; // rendered frames (test: no rendering while idle)
}
export const registry = new Registry();
