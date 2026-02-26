'use client';

import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { useAtlasStore } from '@/store/useAtlasStore';
import { useAtlasSync } from '@/hooks/useAtlasSync';

// Dynamic import for Three.js scene to avoid SSR issues
const AtlasScene = dynamic(() => import('@/components/atlas/AtlasScene'), { ssr: false });

export default function Home() {
  useAtlasSync(); // Start real-time sync
  const { dMetric, consensusScore, activeIslandId } = useAtlasStore();

  return (
    <main className="relative w-full h-screen overflow-hidden font-sans">
      {/* 3D Visual Surface */}
      <AtlasScene />

      {/* Top HUD */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute top-8 left-8 z-10 p-6 rounded-xl border border-white/10 bg-black/40 backdrop-blur-md w-80 shadow-2xl"
      >
        <h1 className="text-cyan-400 font-bold text-xl tracking-tight mb-1">RULIADIC ATLAS v5.0</h1>
        <p className="text-[10px] text-gray-500 uppercase tracking-[0.2em] mb-6">Scientific High-Density Cockpit</p>
        
        <div className="space-y-4">
          <div className="flex justify-between items-end">
            <span className="text-xs text-gray-400 uppercase">D-Metric Drift</span>
            <span className="text-sm font-mono text-cyan-400 font-bold">{dMetric}</span>
          </div>
          <div className="w-full bg-white/5 h-[2px] overflow-hidden rounded-full">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: '70%' }}
              className="bg-cyan-500/50 h-full"
            />
          </div>
          
          <div className="flex justify-between items-end">
            <span className="text-xs text-gray-400 uppercase">Council Confidence</span>
            <span className="text-sm font-mono text-green-400 font-bold">{consensusScore}%</span>
          </div>
        </div>

        <div className="mt-8 pt-4 border-t border-white/5 text-[10px] text-cyan-300/60 font-mono animate-pulse">
          📡 PULSE: MONITORING RELAY CHAIN...
        </div>
      </motion.div>

      {/* Bottom HUD: Tokenmeter */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="absolute bottom-8 right-8 z-10 w-24 h-24 rounded-full border border-cyan-500/20 bg-black/40 backdrop-blur-md flex items-center justify-center flex-col shadow-[0_0_30px_rgba(6,182,212,0.1)]"
      >
        <span className="text-[10px] font-bold text-cyan-400/80">FREE TIER</span>
        <span className="text-[8px] text-gray-500 mt-1 uppercase tracking-tighter">9router</span>
      </motion.div>

      {/* Interaction Indicator */}
      {activeIslandId && (
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="absolute top-8 right-8 z-10 p-6 rounded-xl border border-white/10 bg-black/40 backdrop-blur-md w-96"
        >
          <h2 className="text-white font-medium mb-4 text-sm uppercase tracking-widest border-b border-white/5 pb-2">Island Interrogation</h2>
          <div className="text-[11px] font-mono text-gray-400 space-y-2">
            <p>NAME: {activeIslandId === '1' ? 'BIOLOGY' : 'MATHEMATICS'}</p>
            <p>COORD: [0.24, -1.98, 0.05]</p>
            <p>SEEDER: GEMINI-2.0-PRO-EXP</p>
            <p>STATUS: UNTAMPERED (SHA-256 MATCH)</p>
          </div>
          <button className="mt-6 w-full py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-[10px] uppercase tracking-[0.2em] transition-colors">
            Trigger Isomorphic Audit
          </button>
        </motion.div>
      )}
    </main>
  );
}
