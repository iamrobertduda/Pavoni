import { ContactShadows, Environment, Lightformer, OrbitControls } from '@react-three/drei';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Suspense, useEffect, useRef } from 'react';
import * as THREE from 'three';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { data } from '../data';
import { cadToGl } from '../logic/coords';
import { useStore } from '../state/store';
import { Model } from './Model';
import { registry } from './registry';
import { SectionCaps } from './SectionCaps';

/** Studio environment built from light formers: no HDRI download, no foreign image in the repo. */
function Studio() {
  return (
    <Environment resolution={256} frames={1} background={false}>
      <color attach="background" args={['#6f757d']} />
      <Lightformer form="rect" intensity={2.6} position={[0, 4, 0]} rotation-x={Math.PI / 2} scale={[6, 6, 1]} />
      <Lightformer form="rect" intensity={3.0} position={[-4, 1.6, 1.5]} rotation-y={Math.PI / 2.4} scale={[1.6, 5, 1]} />
      <Lightformer form="rect" intensity={2.0} position={[4, 1.2, 1.2]} rotation-y={-Math.PI / 2.3} scale={[1.4, 4, 1]} />
      <Lightformer form="rect" intensity={1.4} position={[0, 1.4, -4]} scale={[4, 1.2, 1]} />
      <Lightformer form="rect" intensity={2.2} position={[0.8, 1.0, 4]} scale={[1.2, 3, 1]} />
      <Lightformer form="ring" intensity={2.4} position={[1.6, 2.6, 2.8]} scale={1.0} />
      <Lightformer form="rect" color="#e6e6e4" intensity={0.9} position={[0, -2, 0]} rotation-x={-Math.PI / 2} scale={[8, 8, 1]} />
      <Lightformer form="rect" color="#1d2024" intensity={1} position={[-2.5, 0.2, -2.5]} rotation-y={Math.PI / 4} scale={[3, 1.6, 1]} />
    </Environment>
  );
}

function CameraRig() {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  const controls = useThree((s) => s.controls) as unknown as OrbitControlsImpl | null;
  const req = useStore((s) => s.viewRequest);
  const size = useThree((s) => s.size);
  const invalidate = useThree((s) => s.invalidate);
  const anim = useRef<{ p0: THREE.Vector3; t0: THREE.Vector3; p1: THREE.Vector3; t1: THREE.Vector3; fov0: number; fov1: number; start: number } | null>(null);
  useEffect(() => {
    if (!req || !controls) return;
    const v = data.views[req.name];
    if (!v) return;
    // offset (CAD mm) follows parts that were moved to the "bench" in a procedure
    const off = req.offset ? new THREE.Vector3(...cadToGl(req.offset)) : new THREE.Vector3();
    const t1 = new THREE.Vector3(...cadToGl(v.target)).add(off);
    // views are composed for 4:3 landscape; on narrow (portrait) screens move back so the
    // same width stays in frame
    const aspect = size.width / Math.max(1, size.height);
    const k = aspect < 4 / 3 ? Math.min(3, 4 / 3 / aspect) : 1;
    const p1 = t1.clone().add(new THREE.Vector3(...cadToGl(v.position)).add(off).sub(t1).multiplyScalar(k));
    if (aspect < 1) {
      // portrait: panels cover the lower part of the screen, so show the model higher up
      const dist = p1.distanceTo(t1);
      const shift = dist * Math.tan(THREE.MathUtils.degToRad((v.fov ?? 24) / 2)) * 0.25;
      p1.y -= shift;
      t1.y -= shift;
    }
    const fov1 = v.fov ?? 24;
    if (!useStore.getState().animate) {
      camera.position.copy(p1);
      controls.target.copy(t1);
      camera.fov = fov1;
      camera.updateProjectionMatrix();
      controls.update();
      anim.current = null;
      invalidate();
      return;
    }
    anim.current = { p0: camera.position.clone(), t0: controls.target.clone(), p1, t1, fov0: camera.fov, fov1, start: performance.now() };
    invalidate();
  }, [req, controls, camera, size.width, size.height, invalidate]);
  useFrame(() => {
    const a = anim.current;
    if (!a || !controls) return;
    const k = Math.min(1, (performance.now() - a.start) / 900);
    const e = k * k * (3 - 2 * k);
    camera.position.lerpVectors(a.p0, a.p1, e);
    controls.target.lerpVectors(a.t0, a.t1, e);
    camera.fov = a.fov0 + (a.fov1 - a.fov0) * e;
    camera.updateProjectionMatrix();
    controls.update();
    if (k >= 1) anim.current = null;
    else invalidate();
  });
  return null;
}

/** Render on demand (Phase 7: no GPU load and battery drain while nothing moves): every store change
 * requests a frame; animations request the next one themselves. */
function DemandInvalidate() {
  const invalidate = useThree((s) => s.invalidate);
  useEffect(() => useStore.subscribe(() => invalidate()), [invalidate]);
  return null;
}

function ReadySignal() {
  const frames = useRef(0);
  useFrame((state) => {
    registry.frames++;
    if (!registry.ready) return;
    frames.current++;
    if (frames.current < 3) state.invalidate();
    if (frames.current === 3) (window as unknown as { __pavoniReady: boolean }).__pavoniReady = true;
  });
  return null;
}

export function Viewer({ transparent = false }: { transparent?: boolean }) {
  const select = useStore((s) => s.select);
  const low = useStore((s) => s.lowQuality);
  const init = data.views.iso;
  return (
    <Canvas
      className="viewer"
      gl={{ preserveDrawingBuffer: true, antialias: true, alpha: true, localClippingEnabled: true, stencil: true }}
      frameloop="demand"
      dpr={low ? 1 : [1, 2]}
      shadows={!low}
      camera={{ position: cadToGl(init.position), fov: init.fov ?? 24, near: 0.005, far: 30 }}
      onCreated={({ gl }) => {
        gl.localClippingEnabled = true; // renderer property, not a constructor option
        gl.toneMapping = THREE.ACESFilmicToneMapping;
        gl.toneMappingExposure = 1.0;
        gl.setClearColor(0x000000, transparent ? 0 : 0);
      }}
      onPointerMissed={(e) => {
        if (e.type === 'click') select(null);
      }}
    >
      <Studio />
      <ambientLight intensity={0.15} />
      <directionalLight position={[-0.6, 1.2, 0.8]} intensity={0.8} castShadow={!low} shadow-mapSize={[1024, 1024]} />
      <Suspense fallback={null}>
        <Model />
        <SectionCaps />
        {!transparent && <ContactShadows frames={1} position={[0, 0.0005, 0]} opacity={0.45} scale={0.9} blur={2.4} far={0.4} resolution={512} />}
      </Suspense>
      <OrbitControls makeDefault target={cadToGl(init.target)} minDistance={0.05} maxDistance={3} enableDamping dampingFactor={0.12} />
      <CameraRig />
      <DemandInvalidate />
      <ReadySignal />
    </Canvas>
  );
}
