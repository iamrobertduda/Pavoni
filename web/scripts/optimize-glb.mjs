// Raw build123d GLB (one primitive per B-rep face) -> optimized viewer GLB.
// One primitive per part instance, named nodes kept (PLAN 3.3, 13).
// Usage: node scripts/optimize-glb.mjs <in.glb> <out.glb>
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, joinPrimitives, meshopt, prune, weld } from '@gltf-transform/functions';
import { MeshoptEncoder } from 'meshoptimizer';
import { mkdirSync, statSync } from 'node:fs';
import { dirname } from 'node:path';

const [, , src, dst] = process.argv;
if (!src || !dst) {
  console.error('usage: optimize-glb.mjs <in.glb> <out.glb>');
  process.exit(2);
}
const INSTANCE = /^[px][0-9]{3}_[a-z0-9_]+__[0-9]+$/;

await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read(src);
const root = doc.getRoot();

// one shared neutral material; the viewer assigns real materials from parts.yaml
const mat = doc.createMaterial('default').setBaseColorFactor([0.8, 0.8, 0.8, 1]).setMetallicFactor(0).setRoughnessFactor(0.5);

let instances = 0;
for (const node of root.listNodes()) {
  const name = node.getName();
  if (!INSTANCE.test(name)) continue;
  instances++;
  const mesh = node.getMesh();
  if (!mesh) throw new Error(`instance node without mesh: ${name}`);
  const prims = mesh.listPrimitives();
  for (const p of prims) {
    for (const sem of p.listSemantics()) if (sem !== 'POSITION' && sem !== 'NORMAL') p.setAttribute(sem, null);
    p.setMaterial(mat);
  }
  if (prims.length > 1) {
    const joined = joinPrimitives(prims);
    for (const p of prims) {
      mesh.removePrimitive(p);
      p.dispose();
    }
    mesh.addPrimitive(joined);
  }
  mesh.setName(name);
  if (node.listChildren().length) throw new Error(`instance node has children: ${name}`);
}

for (const m of root.listMaterials()) if (m !== mat) m.dispose();

await doc.transform(
  weld(),
  dedup(),
  prune({ keepLeaves: true, keepAttributes: false }),
  meshopt({ encoder: MeshoptEncoder, level: 'medium', quantizePosition: 16, quantizeNormal: 12, quantizationVolume: 'scene' }),
);

// sanity: every instance node survived
const names = new Set(root.listNodes().map((n) => n.getName()));
let tris = 0;
let prims = 0;
for (const mesh of root.listMeshes())
  for (const p of mesh.listPrimitives()) {
    prims++;
    tris += (p.getIndices()?.getCount() ?? p.getAttribute('POSITION').getCount()) / 3;
  }
const kept = [...names].filter((n) => INSTANCE.test(n)).length;
if (kept !== instances) throw new Error(`named instance nodes lost: ${instances} -> ${kept}`);

mkdirSync(dirname(dst), { recursive: true });
await io.write(dst, doc);
const mb = statSync(dst).size / 1e6;
console.log(`optimize-glb: ${instances} Instanzen, ${prims} Primitives (Draw Calls), ${Math.round(tris)} Dreiecke, ${mb.toFixed(2)} MB -> ${dst}`);
