import React, { useEffect, useMemo, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Float, Html, RoundedBox } from '@react-three/drei';
import * as THREE from 'three';
import ErrorBoundary from './ErrorBoundary.jsx';

const STAGES = [
  { label: 'Lexer', sub: 'tokens', color: '#F4F1FE' },
  { label: 'Parser', sub: 'AST', color: '#E7D623' },
  { label: 'Semantic', sub: 'types', color: '#2CF7A4' },
  { label: 'IR', sub: '3-address', color: '#F4F1FE' },
  { label: 'Optimizer', sub: 'passes', color: '#E7D623' },
  { label: 'VM', sub: 'run', color: '#2CF7A4' },
];

const positions = STAGES.map((_, i) => {
  const t = i / (STAGES.length - 1);
  return new THREE.Vector3(-5.4 + t * 10.8, Math.sin(t * Math.PI * 1.6) * 0.9 - 0.9, (i % 2 ? -0.6 : 0.5));
});
const ML_POS = new THREE.Vector3(0.2, 2.5, -0.4);
const VAL_POS = new THREE.Vector3(3.6, 2.35, 0.2);

function Tile({ pos, stage, index }) {
  return (
    <Float speed={1.6} rotationIntensity={0.18} floatIntensity={0.7} floatingRange={[-0.12, 0.12]}>
      <group position={pos}>
        <RoundedBox args={[1.8, 1.15, 0.8]} radius={0.2} smoothness={4}>
          <meshStandardMaterial color={stage.color} roughness={0.45} metalness={0.05} />
        </RoundedBox>
        <RoundedBox args={[1.8, 0.16, 0.82]} radius={0.06} smoothness={2} position={[0, -0.66, 0]}>
          <meshStandardMaterial color="#0A041A" roughness={0.8} />
        </RoundedBox>
        <Html center position={[0, 0.02, 0.45]} distanceFactor={7.5} style={{ pointerEvents: 'none' }}>
          <div className="h3d-label">
            <span className="h3d-n">{String(index + 1).padStart(2, '0')}</span>
            <b>{stage.label}</b>
            <i>{stage.sub}</i>
          </div>
        </Html>
      </group>
    </Float>
  );
}

function MLCore() {
  const shell = useRef();
  const ringA = useRef();
  const ringB = useRef();
  useFrame((_, dt) => {
    shell.current.rotation.y += dt * 0.5;
    shell.current.rotation.x += dt * 0.2;
    ringA.current.rotation.z += dt * 0.9;
    ringB.current.rotation.x += dt * 0.7;
  });
  return (
    <Float speed={2} floatIntensity={0.9}>
      <group position={ML_POS}>
        <mesh>
          <icosahedronGeometry args={[0.62, 2]} />
          <meshStandardMaterial color="#602CF7" emissive="#5423E7" emissiveIntensity={0.9} roughness={0.25} />
        </mesh>
        <mesh ref={shell}>
          <icosahedronGeometry args={[0.95, 1]} />
          <meshBasicMaterial color="#2CF7A4" wireframe transparent opacity={0.85} />
        </mesh>
        <mesh ref={ringA} rotation={[Math.PI / 2.4, 0, 0]}>
          <torusGeometry args={[1.25, 0.035, 12, 80]} />
          <meshBasicMaterial color="#E7D623" />
        </mesh>
        <mesh ref={ringB} rotation={[0, Math.PI / 3, 0]}>
          <torusGeometry args={[1.45, 0.025, 12, 80]} />
          <meshBasicMaterial color="#ffffff" transparent opacity={0.8} />
        </mesh>
        <Html center position={[0, -1.75, 0]} distanceFactor={8} style={{ pointerEvents: 'none' }}>
          <div className="h3d-tag mint">ML classifier</div>
        </Html>
      </group>
    </Float>
  );
}

function Validator() {
  return (
    <Float speed={1.8} floatIntensity={0.8}>
      <group position={VAL_POS}>
        <RoundedBox args={[1.5, 0.8, 0.6]} radius={0.18} smoothness={4}>
          <meshStandardMaterial color="#E7D623" roughness={0.4} />
        </RoundedBox>
        <Html center position={[0, 0, 0.36]} distanceFactor={8} style={{ pointerEvents: 'none' }}>
          <div className="h3d-label small"><b>Validator</b><i>recompile</i></div>
        </Html>
      </group>
    </Float>
  );
}

/** Tokens flowing along a curve. */
function Flow({ points, color, count = 26, speed = 0.07, size = 0.075 }) {
  const curve = useMemo(() => new THREE.CatmullRomCurve3(points, false, 'catmullrom', 0.5), [points]);
  const ref = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const tmp = useMemo(() => new THREE.Vector3(), []);
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    for (let i = 0; i < count; i++) {
      const u = (t * speed + i / count) % 1;
      curve.getPointAt(u, tmp);
      dummy.position.copy(tmp);
      const s = size * (0.75 + 0.5 * Math.sin(t * 3 + i));
      dummy.scale.setScalar(s / size);
      dummy.updateMatrix();
      ref.current.setMatrixAt(i, dummy.matrix);
    }
    ref.current.instanceMatrix.needsUpdate = true;
  });
  const geo = useMemo(() => new THREE.TubeGeometry(curve, 120, 0.018, 6, false), [curve]);
  return (
    <group>
      <mesh geometry={geo}>
        <meshBasicMaterial color={color} transparent opacity={0.35} />
      </mesh>
      <instancedMesh ref={ref} args={[null, null, count]}>
        <sphereGeometry args={[size, 12, 12]} />
        <meshBasicMaterial color={color} />
      </instancedMesh>
    </group>
  );
}

/** Pull the camera back on narrow containers so the whole pipeline stays in frame. */
function CameraRig() {
  const { camera, size } = useThree();
  useEffect(() => {
    camera.position.z = Math.max(11.5, 17.5 / (size.width / size.height));
    camera.updateProjectionMatrix();
  }, [camera, size]);
  return null;
}

function Scene() {
  const group = useRef();
  useFrame(({ pointer }, dt) => {
    group.current.rotation.y = THREE.MathUtils.damp(group.current.rotation.y, pointer.x * 0.32, 3, dt);
    group.current.rotation.x = THREE.MathUtils.damp(group.current.rotation.x, -pointer.y * 0.14, 3, dt);
  });
  const mainPath = useMemo(() => positions.map((p) => p.clone()), []);
  const toML = useMemo(() => [positions[1].clone(), new THREE.Vector3(-1.4, 1.2, 0), ML_POS.clone()], []);
  const mlToVal = useMemo(() => [ML_POS.clone(), new THREE.Vector3(1.9, 3.1, 0), VAL_POS.clone()], []);
  const valBack = useMemo(() => [VAL_POS.clone(), new THREE.Vector3(2.4, 0.9, 0.2), positions[3].clone()], []);
  return (
    <group ref={group}>
      {STAGES.map((s, i) => <Tile key={s.label} pos={positions[i]} stage={s} index={i} />)}
      <MLCore />
      <Validator />
      <Flow points={mainPath} color="#ffffff" count={30} />
      <Flow points={toML} color="#FF6B8B" count={8} speed={0.1} size={0.07} />
      <Flow points={mlToVal} color="#2CF7A4" count={8} speed={0.1} size={0.07} />
      <Flow points={valBack} color="#E7D623" count={8} speed={0.1} size={0.07} />
    </group>
  );
}

export default function Hero3D() {
  return (
    <div className="hero3d" role="img" aria-label="Animated 3D diagram of the compiler pipeline with the ML repair loop">
      <ErrorBoundary fallback={<div className="hero3d-fallback">3D preview unavailable in this browser.</div>}>
        <Canvas camera={{ position: [0, 0.6, 11.5], fov: 42 }} dpr={[1, 2]} gl={{ antialias: true, alpha: true }}>
          <ambientLight intensity={1.1} />
          <directionalLight position={[5, 8, 6]} intensity={2.2} />
          <pointLight position={[0, 3, 3]} intensity={25} color="#2CF7A4" distance={12} />
          <CameraRig />
          <Scene />
        </Canvas>
      </ErrorBoundary>
    </div>
  );
}
