import type { Vec3 } from '../data/types';

/** CAD (mm, Z up, -Y front) -> three/GLB (m, Y up): gl = (x, z, -y) / 1000 */
export function cadToGl(v: Vec3): Vec3 {
  return [v[0] / 1000, v[2] / 1000, -v[1] / 1000];
}

export function cadDirToGl(v: Vec3): Vec3 {
  return [v[0], v[2], -v[1]];
}
