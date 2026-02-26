'use client'
import { useRef, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Sphere, MeshDistortMaterial } from '@react-three/drei'
import * as THREE from 'three'

interface RuliadicIslandProps {
  position: [number, number, number]
  color: string
  onClick?: () => void
}

export default function RuliadicIsland({ position, color, onClick }: RuliadicIslandProps) {
  const meshRef = useRef<THREE.Mesh>(null!)
  const [hovered, setHovered] = useState(false)

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.003
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1
    }
  })

  return (
    <group position={position}>
      <Sphere
        ref={meshRef}
        args={[1, 64, 64]}
        onClick={onClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        scale={hovered ? 1.15 : 1}
      >
        <MeshDistortMaterial
          color={color}
          roughness={0.2}
          metalness={0.8}
          distort={hovered ? 0.4 : 0.25}
          speed={2}
          transparent
          opacity={0.85}
        />
      </Sphere>
      {/* Glow ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.3, 1.35, 64]} />
        <meshBasicMaterial color={color} transparent opacity={hovered ? 0.4 : 0.15} side={THREE.DoubleSide} />
      </mesh>
    </group>
  )
}
