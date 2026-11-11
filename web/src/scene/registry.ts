import type * as THREE from 'three';

/** instance id -> mesh, filled once the GLB is loaded */
class Registry extends Map<string, THREE.Mesh> {
  ready = false;
}
export const registry = new Registry();
