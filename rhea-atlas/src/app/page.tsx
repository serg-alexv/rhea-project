'use client'
import dynamic from 'next/dynamic'
import { Suspense, useState, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Environment, Stars, Float } from '@react-three/drei'
import { motion, AnimatePresence } from 'framer-motion'
import * as THREE from 'three'

const RuliadicIsland = dynamic(() => import('@/components/RuliadicIsland'), { ssr: false })
const IsomorphismBeam = dynamic(() => import('@/components/IsomorphismBeam'), { ssr: false })

function FloatingPanel({ children, position }: { children: React.ReactNode, position: string }) {
  return (
    <motion.div 
      drag
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={0.1}
      whileHover={{ scale: 1.02 }}
      className={`absolute ${position} z-20 p-6 rounded-3xl border border-white/5 bg-white/5 backdrop-blur-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] cursor-grab active:cursor-grabbing`}
    >
      {children}
    </motion.div>
  )
}

export default function Home() {
  const [selectedNode, setSelectedNode] = useState('Ruliadic Core')
  const [dMetric] = useState(282.4)

  return (
    <main className="h-screen w-full bg-[#030303] overflow-hidden relative">
      {/* 1. FLOATING HUD: The Meditative Panels */}
      <AnimatePresence>
        <FloatingPanel position="top-8 left-8 w-72">
          <h1 className="text-lg font-bold tracking-tighter text-cyan-400/80 mb-1">RHEA ATLAS</h1>
          <p className="text-[9px] uppercase tracking-[0.4em] opacity-30 mb-6 font-mono font-bold">Zen Garden Mode</p>
          <div className="space-y-4">
            <div className="flex justify-between text-[10px] font-mono"><span className="opacity-40">DRIFT</span><span className="text-cyan-400">{dMetric}</span></div>
            <div className="w-full bg-white/5 h-[1px] rounded-full overflow-hidden">
              <motion.div initial={{ width: 0 }} animate={{ width: '70%' }} className="bg-cyan-500/30 h-full" />
            </div>
          </div>
        </FloatingPanel>

        <FloatingPanel position="bottom-8 left-8 w-80">
          <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-2 font-bold italic">Active Intent</div>
          <div className="text-xs font-mono text-cyan-200/60 leading-relaxed capitalize">
            {selectedNode} :: Isomorphic Search Active
          </div>
        </FloatingPanel>

        <FloatingPanel position="top-8 right-8 w-64">
          <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-4">Council Pulse</h2>
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-ping" />
            <span className="text-[10px] font-mono text-gray-400">GEMINI 3.1 :: SYNC</span>
          </div>
        </FloatingPanel>
      </AnimatePresence>

      {/* 2. CENTER: The Ruliadic Space */}
      <div className="absolute inset-0 z-0 cursor-crosshair">
        <Canvas camera={{ position: [0, 0, 10], fov: 40 }}>
          <Suspense fallback={null}>
            <Stars radius={100} depth={50} count={7000} factor={4} saturation={0} fade speed={0.5} />
            <ambientLight intensity={0.2} />
            <pointLight position={[10, 10, 10]} intensity={1} color="#00ffff" />
            
            <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
              <RuliadicIsland position={[-3, 1, 0]} color="#4f46e5" onClick={() => setSelectedNode('Topological Logic')} />
              <RuliadicIsland position={[3, -1, 0]} color="#10b981" onClick={() => setSelectedNode('Metabolic Flow')} />
              <RuliadicIsland position={[0, -3, -2]} color="#f59e0b" onClick={() => setSelectedNode('Quantum Consensus')} />
            </Float>

            <IsomorphismBeam start={new THREE.Vector3(-3, 1, 0)} end={new THREE.Vector3(3, -1, 0)} color="#00ffff" speed={0.5} />
            
            <OrbitControls enablePan={false} rotateSpeed={0.3} zoomSpeed={0.5} />
            <Environment preset="night" />
          </Suspense>
        </Canvas>
      </div>
    </main>
  )
}
