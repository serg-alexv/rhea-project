import { useRef } from 'react'
import { Mesh } from 'three'
import { useFrame } from '@react-three/fiber'
import { MeshWobbleMaterial } from '@react-three/drei'

export default function RuliadicIsland() {
  const meshRef = useRef<Mesh>(null)
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.1
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.15
      const pulse = Math.sin(state.clock.elapsedTime * 2) * 0.05 + 1
      meshRef.current.scale.setScalar(pulse)
    }
  })
  return (
    <mesh ref={meshRef} position={[0, 0, 0]}>
      <icosahedronGeometry args={[1, 4]} />
      <MeshWobbleMaterial
        factor={0.2}
        speed={1}
        emissive="#4f46e5"
        emissiveIntensity={0.5}
        color="#6366f1"
        roughness={0.1}
        metalness={0.9}
      />
      <pointLight position={[0, 0, 0]} intensity={2} color="#8b5cf6" distance={5} />
    </mesh>
  )
}
