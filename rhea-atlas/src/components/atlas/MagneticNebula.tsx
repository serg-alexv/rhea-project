'use client';

import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// WATCHMAKER COMPONENT: The Magnetic Starfield
// Provokes reaction to every cursor movement via a custom shader
export default function MagneticNebula() {
  const meshRef = useRef<THREE.Points>(null);
  const count = 2000;

  const [particles, mouse] = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      p[i * 3] = (Math.random() - 0.5) * 10;
      p[i * 3 + 1] = (Math.random() - 0.5) * 10;
      p[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    return [p, new THREE.Vector2()];
  }, []);

  useFrame((state) => {
    if (!meshRef.current) return;
    
    // Smooth Cursor Tracking
    mouse.x = state.mouse.x * 5;
    mouse.y = state.mouse.y * 5;

    const positions = meshRef.current.geometry.attributes.position.array as Float32Array;
    
    for (let i = 0; i < count; i++) {
      const x = positions[i * 3];
      const y = positions[i * 3 + 1];
      
      // The "Relaxative" Physics: Particles gently shy away from the cursor
      const dx = x - mouse.x;
      const dy = y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      
      if (dist < 2) {
        positions[i * 3] += dx * 0.01;
        positions[i * 3 + 1] += dy * 0.01;
      }
    }
    meshRef.current.geometry.attributes.position.needsUpdate = true;
    meshRef.current.rotation.y += 0.001;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        color="#00ffff"
        transparent
        opacity={0.4}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
}
