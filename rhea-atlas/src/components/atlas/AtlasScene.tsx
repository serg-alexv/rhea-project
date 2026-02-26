'use client';

import React, { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Float, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { useAtlasStore, AtlasState, Island as AtlasIsland } from '@/store/useAtlasStore';
import MagneticNebula from '@/components/atlas/MagneticNebula';
import OceanusFlow from '@/components/OceanusFlow';
import { useDensityAnalysis } from '@/hooks/useDensityAnalysis';

function hashText(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function Island({ island, semanticSeed }: { island: AtlasIsland; semanticSeed: string }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const setActiveIsland = useAtlasStore((state: AtlasState) => state.setActiveIsland);
  const signature = useMemo(() => hashText(`${island.name}:${semanticSeed}:${island.complexity}`), [island.name, island.complexity, semanticSeed]);
  const radius = Math.max(0.75, Math.min(1.55, 0.75 + (island.complexity || 0) * 0.22));
  const distort = 0.15 + (signature % 18) / 100;
  const opacity = Math.max(0.35, Math.min(0.9, 0.35 + (island.complexity || 0) * 0.08));
  const speed = 1 + ((signature >> 5) % 20) / 10;

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.005 + ((signature % 7) * 0.0006);
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.22 + (signature % 13)) * 0.08;
    }
  });

  return (
    <Float speed={1.4 + ((signature >> 9) % 10) / 10} rotationIntensity={0.35} floatIntensity={0.8}>
      <mesh 
        ref={meshRef} 
        position={island.position} 
        onClick={() => setActiveIsland(island.id)}
      >
        <icosahedronGeometry args={[radius, 4]} />
        <MeshDistortMaterial
          color={island.color}
          speed={speed}
          distort={distort}
          radius={radius}
          wireframe
          transparent
          opacity={opacity}
        />
      </mesh>
    </Float>
  );
}

function ConnectionLine() {
  const islands = useAtlasStore((state: AtlasState) => state.islands);
  if (islands.length < 2) return null;

  const points = [
    new THREE.Vector3(...islands[0].position),
    new THREE.Vector3(...islands[1].position)
  ];

  const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
  const complexityDelta = Math.abs((islands[0].complexity ?? 0) - (islands[1].complexity ?? 0));
  const opacity = Math.max(0.2, Math.min(0.85, 0.3 + complexityDelta * 0.12));

  return (
    <primitive 
      object={new THREE.Line(
        lineGeometry, 
        new THREE.LineBasicMaterial({ color: 0x00ffff, transparent: true, opacity })
      )} 
    />
  );
}

export default function AtlasScene() {
  const islands = useAtlasStore((state: AtlasState) => state.islands);
  const sessionHistory = useAtlasStore((state: AtlasState) => state.sessionHistory);
  const dMetric = useAtlasStore((state: AtlasState) => state.dMetric);
  const consensusScore = useAtlasStore((state: AtlasState) => state.consensusScore);
  const contextDensities = useAtlasStore((state: AtlasState) => state.contextDensities);
  const showOceanusFlow = useAtlasStore((state: AtlasState) => state.showOceanusFlow);
  useDensityAnalysis();
  const semanticSeed = useMemo(
    () => `${sessionHistory[0]?.query ?? ''}|${sessionHistory[0]?.result ?? ''}|d:${dMetric}|c:${consensusScore}`,
    [sessionHistory, dMetric, consensusScore],
  );

  return (
    <div className="w-full h-screen bg-[#050505]">
      <Canvas camera={{ position: [0, 0, 10], fov: 75 }}>
        <color attach="background" args={['#050505']} />
        <MagneticNebula />
        {showOceanusFlow && <OceanusFlow densities={contextDensities} />}
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        
        {islands.map((island: AtlasIsland) => (
          <Island key={island.id} island={island} semanticSeed={semanticSeed} />
        ))}
        
        <ConnectionLine />
        <OrbitControls enablePan={false} enableZoom={true} minDistance={5} maxDistance={20} />
      </Canvas>
    </div>
  );
}
