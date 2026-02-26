'use client';

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Float, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { useAtlasStore } from '@/store/useAtlasStore';

function Island({ island }: { island: any }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const setActiveIsland = useAtlasStore((state) => state.setActiveIsland);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01;
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
      <mesh 
        ref={meshRef} 
        position={island.position} 
        onClick={() => setActiveIsland(island.id)}
      >
        <icosahedronGeometry args={[1, 4]} />
        <MeshDistortMaterial
          color={island.color}
          speed={2}
          distort={0.3}
          radius={1}
          wireframe
          transparent
          opacity={0.6}
        />
      </mesh>
    </Float>
  );
}

function ConnectionLine() {
  const islands = useAtlasStore((state) => state.islands);
  if (islands.length < 2) return null;

  const points = [
    new THREE.Vector3(...islands[0].position),
    new THREE.Vector3(...islands[1].position)
  ];

  const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);

  return (
    <primitive 
      object={new THREE.Line(
        lineGeometry, 
        new THREE.LineBasicMaterial({ color: 0x00ffff, transparent: true, opacity: 0.4 })
      )} 
    />
  );
}

export default function AtlasScene() {
  const islands = useAtlasStore((state) => state.islands);

  return (
    <div className="w-full h-screen bg-[#050505]">
      <Canvas camera={{ position: [0, 0, 10], fov: 75 }}>
        <color attach="background" args={['#050505']} />
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        
        {islands.map((island) => (
          <Island key={island.id} island={island} />
        ))}
        
        <ConnectionLine />
        <OrbitControls enablePan={false} enableZoom={true} minDistance={5} maxDistance={20} />
      </Canvas>
    </div>
  );
}
