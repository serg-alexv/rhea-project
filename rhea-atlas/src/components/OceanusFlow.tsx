'use client';

import { useMemo, useRef } from 'react';
import { Float, MeshDistortMaterial } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { ContextDensity } from '@/store/useAtlasStore';
import DensityField from '@/components/DensityField';
import ErebusRing from '@/components/rings/ErebusRing';
import ChronosRing from '@/components/rings/ChronosRing';
import ErosRing from '@/components/rings/ErosRing';
import TethysRing from '@/components/rings/TethysRing';
import PhoebeRing from '@/components/rings/PhoebeRing';

function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace('#', '');
  const normalized = clean.length === 3
    ? clean.split('').map((c) => c + c).join('')
    : clean.padEnd(6, '0').slice(0, 6);
  const value = Number.parseInt(normalized, 16);
  return [
    ((value >> 16) & 255) / 255,
    ((value >> 8) & 255) / 255,
    (value & 255) / 255,
  ];
}

function shade(hex: string, factor: number, alpha = 1): string {
  const [r, g, b] = hexToRgb(hex);
  const fr = Math.max(0, Math.min(255, Math.round(r * 255 * factor)));
  const fg = Math.max(0, Math.min(255, Math.round(g * 255 * factor)));
  const fb = Math.max(0, Math.min(255, Math.round(b * 255 * factor)));
  return `rgba(${fr}, ${fg}, ${fb}, ${alpha})`;
}

function hashText(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function averageMagnitude(vectors: ContextDensity['vectorField']): number {
  if (!vectors.length) return 0.2;
  return vectors.reduce((sum, v) => sum + v.magnitude, 0) / vectors.length;
}

function buildTethysDots(density: ContextDensity): Array<{ ontology: string; count: number; color?: string }> {
  const dots: Array<{ ontology: string; count: number; color?: string }> = [
    {
      ontology: density.ontology || density.label || 'general',
      count: Math.max(1, density.sampleCount),
      color: density.color,
    },
  ];

  const motion = Math.round(Math.max(1, density.vectorField.length / 3));
  dots.push({
    ontology: density.consistency >= 0.75 ? 'aligned' : 'cross-check',
    count: motion,
    color: density.consistency >= 0.75 ? '#22d3ee' : '#fb7185',
  });

  if (density.sampleCount >= 4) {
    dots.push({
      ontology: 'archive',
      count: Math.max(1, Math.round(density.sampleCount / 2)),
      color: '#c4b5fd',
    });
  }

  if (density.consistency < 0.6) {
    dots.push({
      ontology: 'skeptic',
      count: Math.max(1, Math.round((1 - density.consistency) * 6)),
      color: '#f59e0b',
    });
  }

  return dots.slice(0, 5);
}

function DensityLabel({ density }: { density: ContextDensity }) {
  return (
    <group position={[0, 0.95, 0]}>
      <sprite scale={[0.9, 0.22, 1]}>
        <spriteMaterial color={density.color} opacity={0.18 + density.consistency * 0.15} transparent />
      </sprite>
    </group>
  );
}

function NebulaField({ density }: { density: ContextDensity }) {
  const pointsRef = useRef<THREE.Points>(null);
  const seed = useMemo(() => hashText(density.id), [density.id]);
  const spread = 1.2 + (1 - density.density) * 2.8;
  const count = Math.max(80, Math.min(320, Math.round(80 + density.density * 520)));

  const { positions, sizes } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const size = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2 + (seed % 37) * 0.01;
      const b = ((i * 17 + seed) % 360) * (Math.PI / 180);
      const radius = spread * (0.25 + ((i * 13 + seed) % 100) / 100);
      pos[i * 3 + 0] = Math.cos(a) * Math.sin(b) * radius;
      pos[i * 3 + 1] = Math.sin(a * 1.4) * 0.45 * radius;
      pos[i * 3 + 2] = Math.cos(b) * radius * 0.8;
      size[i] = 0.02 + (((i * 19 + seed) % 100) / 100) * 0.06;
    }
    return { positions: pos, sizes: size };
  }, [count, seed, spread]);

  useFrame((state) => {
    if (!pointsRef.current) return;
    pointsRef.current.rotation.y += 0.0008 + density.density * 0.0008;
    pointsRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.15 + seed) * 0.06;
  });

  return (
    <group>
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={positions.length / 3} array={positions} itemSize={3} />
          <bufferAttribute attach="attributes-size" count={sizes.length} array={sizes} itemSize={1} />
        </bufferGeometry>
        <pointsMaterial
          color={density.color}
          transparent
          opacity={0.12 + density.consistency * 0.18}
          size={0.055}
          sizeAttenuation
          depthWrite={false}
        />
      </points>
      <DensityField vectors={density.vectorField} color={shade(density.color, 1.05, 0.9)} maxArrows={12} />
      <DensityLabel density={density} />
    </group>
  );
}

function CloudField({ density }: { density: ContextDensity }) {
  const shellRef = useRef<THREE.Mesh>(null);
  const orbitRef = useRef<THREE.Points>(null);
  const seed = useMemo(() => hashText(`${density.id}:cloud`), [density.id]);
  const radius = 0.55 + density.density * 0.7;
  const particleCount = Math.max(60, Math.min(220, Math.round(80 + density.sampleCount * 14)));

  const orbitPositions = useMemo(() => {
    const arr = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const angle = ((i * 23 + seed) % 360) * (Math.PI / 180);
      const ring = radius * (1.15 + ((i * 7) % 11) * 0.035);
      arr[i * 3 + 0] = Math.cos(angle) * ring;
      arr[i * 3 + 1] = Math.sin(angle * 1.9) * 0.14;
      arr[i * 3 + 2] = Math.sin(angle) * ring;
    }
    return arr;
  }, [particleCount, radius, seed]);

  useFrame((state) => {
    if (shellRef.current) {
      shellRef.current.rotation.y += 0.0022;
      shellRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3 + seed) * 0.08;
    }
    if (orbitRef.current) {
      orbitRef.current.rotation.y -= 0.0015;
      orbitRef.current.rotation.z += 0.0008;
    }
  });

  return (
    <group>
      <mesh ref={shellRef}>
        <sphereGeometry args={[radius, 28, 28]} />
        <MeshDistortMaterial
          color={density.color}
          distort={0.35 + (1 - density.consistency) * 0.22}
          speed={1 + density.density}
          transparent
          opacity={0.2 + density.density * 0.35}
          roughness={0.25}
          metalness={0.35}
        />
      </mesh>
      <points ref={orbitRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={orbitPositions.length / 3} array={orbitPositions} itemSize={3} />
        </bufferGeometry>
        <pointsMaterial color={density.color} transparent opacity={0.22} size={0.035} sizeAttenuation depthWrite={false} />
      </points>
      <DensityField vectors={density.vectorField} color={shade(density.color, 1.1, 0.95)} maxArrows={16} />
      <DensityLabel density={density} />
    </group>
  );
}

function SphereField({ density }: { density: ContextDensity }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const seed = useMemo(() => hashText(`${density.id}:sphere`), [density.id]);
  const radius = 0.5 + density.density * 1.5;
  const meanFlow = useMemo(() => averageMagnitude(density.vectorField), [density.vectorField]);
  const tethysDots = useMemo(() => buildTethysDots(density), [density]);
  const showErebus = density.density > 0.7;
  const showMidRings = density.density > 0.8;
  const showFullRings = density.density > 0.9;

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.003 + density.consistency * 0.002;
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.22 + seed) * 0.05;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z += 0.004;
      ringRef.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 1.2 + seed) * 0.03);
    }
  });

  return (
    <group>
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[radius, 4]} />
        <MeshDistortMaterial
          color={density.color}
          distort={0.08 + (1 - density.consistency) * 0.12}
          speed={0.7 + density.density * 0.8}
          transparent
          opacity={0.5 + density.consistency * 0.35}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[radius * 1.03, radius * 1.07, 64]} />
        <meshBasicMaterial color={density.color} transparent opacity={0.12 + density.consistency * 0.35} side={THREE.DoubleSide} />
      </mesh>
      {showErebus && (
        <group>
          <ErebusRing radius={radius} auditCount={density.sampleCount + density.vectorField.length} />
          {showMidRings && (
            <>
              <ChronosRing radius={radius} count={density.sampleCount} recencyBias={1.05 + (1 - density.consistency) * 0.5} />
              <ErosRing radius={radius} agreement={density.consistency} />
            </>
          )}
          {showFullRings && (
            <>
              <TethysRing radius={radius} dots={tethysDots} />
              <PhoebeRing radius={radius} confidence={density.consistency} changeRate={meanFlow * 2} />
            </>
          )}
        </group>
      )}
      <DensityField vectors={density.vectorField} color={shade(density.color, 1.2, 1)} maxArrows={18} />
      <DensityLabel density={density} />
    </group>
  );
}

function DensityNode({ density }: { density: ContextDensity }) {
  const mode = density.density < 0.3 ? 'nebula' : density.density < 0.7 ? 'cloud' : 'sphere';

  return (
    <Float speed={0.9 + density.density * 0.8} floatIntensity={0.35} rotationIntensity={0.1}>
      <group position={density.position}>
        {mode === 'nebula' && <NebulaField density={density} />}
        {mode === 'cloud' && <CloudField density={density} />}
        {mode === 'sphere' && <SphereField density={density} />}
      </group>
    </Float>
  );
}

export default function OceanusFlow({ densities }: { densities: ContextDensity[] }) {
  const visible = useMemo(() => densities.slice(0, 6), [densities]);
  if (visible.length === 0) return null;

  return (
    <group position={[0, -0.45, 0]}>
      {visible.map((density) => (
        <DensityNode key={density.id} density={density} />
      ))}
    </group>
  );
}
