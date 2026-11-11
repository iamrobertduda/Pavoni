import * as THREE from 'three';

export interface MatDef {
  color: string;
  metalness: number;
  roughness: number;
  transmission?: number;
  opacity?: number;
  label: string;
}

// PLAN 9: materials come from the parts.yaml key, not from exported colours.
export const MATERIALS: Record<string, MatDef> = {
  chrome: { color: '#f4f5f7', metalness: 1, roughness: 0.07, label: 'Messing verchromt' },
  brass: { color: '#d4a64a', metalness: 1, roughness: 0.28, label: 'Messing' },
  stainless: { color: '#d9dcdf', metalness: 1, roughness: 0.22, label: 'Edelstahl' },
  steel: { color: '#a9adb2', metalness: 0.9, roughness: 0.35, label: 'Stahl' },
  copper: { color: '#c87a4a', metalness: 1, roughness: 0.3, label: 'Kupfer' },
  aluminium: { color: '#c9ccd0', metalness: 0.9, roughness: 0.3, label: 'Aluminium' },
  rubber_black: { color: '#1b1b1b', metalness: 0, roughness: 0.85, label: 'Gummi schwarz' },
  silicone: { color: '#e9e3d6', metalness: 0, roughness: 0.55, label: 'Silikon' },
  silicone_red: { color: '#b2352b', metalness: 0, roughness: 0.55, label: 'Silikon rot' },
  ptfe: { color: '#f3f1ec', metalness: 0, roughness: 0.45, label: 'PTFE / Kunststoff weiß' },
  glass: { color: '#e8f2f4', metalness: 0, roughness: 0.04, transmission: 0.92, label: 'Glas' },
  bakelite: { color: '#141414', metalness: 0, roughness: 0.32, label: 'Bakelit / Duroplast' },
  plastic_black: { color: '#1a1a1a', metalness: 0, roughness: 0.5, label: 'Kunststoff schwarz' },
  plastic_clear: { color: '#f0f6f8', metalness: 0, roughness: 0.08, transmission: 0.85, label: 'Kunststoff transparent' },
  plastic_white: { color: '#efefea', metalness: 0, roughness: 0.5, label: 'Kunststoff weiß' },
  plastic_green: { color: '#12947a', metalness: 0, roughness: 0.3, label: 'Kunststoff grün (Schalterwippe)' },
  fiber: { color: '#8a7656', metalness: 0, roughness: 0.8, label: 'Faserdichtung' },
  gauge_face: { color: '#f7f7f2', metalness: 0, roughness: 0.4, label: 'Zifferblatt' },
  cable: { color: '#151515', metalness: 0, roughness: 0.6, label: 'Kabel' },
  emblem: { color: '#c8a85a', metalness: 0.8, roughness: 0.3, label: 'Emblem' },
};

export const SEAL_COLOR = new THREE.Color('#ff5a1f');
export const SELECT_COLOR = new THREE.Color('#2f7cff');

export function makeMaterial(key: string, lowQuality = false): THREE.MeshPhysicalMaterial {
  const d = MATERIALS[key] ?? MATERIALS.steel;
  const m = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(d.color),
    metalness: d.metalness,
    roughness: d.roughness,
    envMapIntensity: 1.0,
  });
  if (d.transmission && lowQuality) {
    // no transmission pass under software rendering: plain transparency
    m.transparent = true;
    m.opacity = 0.28;
    m.depthWrite = false;
  } else if (d.transmission) {
    m.transmission = d.transmission;
    m.thickness = 1.5;
    m.ior = 1.5;
    m.transparent = true;
  }
  m.userData.base = { color: m.color.clone(), transmission: m.transmission, transparent: m.transparent, opacity: m.opacity };
  return m;
}
