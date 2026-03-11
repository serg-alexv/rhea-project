'use client'
import { useRef } from 'react'
import { Mesh } from 'three'
import { useFrame } from '@react-three/fiber'
import { MeshDistortMaterial } from '@react-three/drei'

interface IslandProps {
  position: [number, number, number];
  color: string;
  onClick: () => void;
}

export default function RuliadicIsland({ position, color, onClick }: IslandProps) {
  const meshRef = useRef<Mesh>(null)
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01;
      const pulse = Math.sin(state.clock.elapsedTime * 2) * 0.05 + 1;
      meshRef.current.scale.setScalar(pulse);
    }
  })

  return (
    <mesh ref={meshRef} position={position} onClick={onClick}>
      <icosahedronGeometry args={[1, 2]} /> {/* Lower detail makes it look like a jagged island, not a marble */}
      <MeshDistortMaterial
        color={color}
        speed={2}
        distort={0.4}
        radius={1}
        wireframe
        transparent
        opacity={0.7}
      />
      <pointLight position={[0, 0, 0]} intensity={1} color={color} distance={3} />
    </mesh>
  )
}
