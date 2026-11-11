// Camera pose for a named view (CAD mm in, GL metres out).
import type { Vec3, View } from '../data/types';
import { cadToGl } from './coords';

export interface Pose {
  position: Vec3;
  target: Vec3;
  fov: number;
}

const DEFAULT_FOV = 24;

/**
 * Views are composed for 4:3 landscape. On narrower screens the camera moves back so the same
 * width stays in frame, and in portrait the model is shown higher up because the panels cover
 * the lower part of the screen.
 *
 * Views fitted to a reference photo (`photo`) are exact camera poses for that photo's aspect:
 * they are never adapted, or the overlay (scripts/overlay.mjs) no longer lines up.
 *
 * `offset` (CAD mm) moves the whole pose, e.g. to follow parts lying "on the bench".
 */
export function viewPose(v: View, aspect: number, offset: Vec3 = [0, 0, 0]): Pose {
  const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const off = cadToGl(offset);
  const target = add(cadToGl(v.target), off);
  const eye = add(cadToGl(v.position), off);
  const fov = v.fov ?? DEFAULT_FOV;
  const fitted = Boolean(v.photo);
  const k = !fitted && aspect < 4 / 3 ? Math.min(3, 4 / 3 / aspect) : 1;
  const position: Vec3 = k === 1 ? eye : [target[0] + (eye[0] - target[0]) * k, target[1] + (eye[1] - target[1]) * k, target[2] + (eye[2] - target[2]) * k];
  if (!fitted && aspect < 1) {
    const dist = Math.hypot(position[0] - target[0], position[1] - target[1], position[2] - target[2]);
    const shift = dist * Math.tan(((fov / 2) * Math.PI) / 180) * 0.25;
    position[1] -= shift;
    target[1] -= shift;
  }
  return { position, target, fov };
}
