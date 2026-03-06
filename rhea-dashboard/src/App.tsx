import { useState, useEffect } from 'react'
import { useStore } from './store'
import ChainsTab from './components/ChainsTab'
import ProcsTab from './components/ProcsTab'
import BottomNav from './components/BottomNav'

export default function App() {
  const [activeTab, setActiveTab] = useState<'chains' | 'procs'>('chains')
  const [activeNav, setActiveNav] = useState<string>('live')
  const sessions = useStore(s => s.sessions)
  const startPolling = useStore(s => s.startPolling)
  const stopPolling = useStore(s => s.stopPolling)
  
  useEffect(() => {
    startPolling()
    return () => stopPolling()
  }, [startPolling, stopPolling])

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-4 py-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="text-xs font-mono text-slate-500">7:51</div>
            <span className="text-lg font-bold">◆ RHEA</span>
          </div>
          <div className="text-xs text-slate-400">LTE • Battery</div>
        </div>
        
        {/* Tab navigation */}
        <div className="flex gap-2 mt-3">
          <button
            onClick={() => setActiveTab('chains')}
            className={`px-6 py-2 rounded-full text-sm font-medium transition ${
              activeTab === 'chains'
                ? 'bg-slate-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Chains
          </button>
          <button
            onClick={() => setActiveTab('procs')}
            className={`px-6 py-2 rounded-full text-sm font-medium transition ${
              activeTab === 'procs'
                ? 'bg-slate-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Procs
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-auto p-4 pb-24">
        {activeTab === 'chains' && <ChainsTab />}
        {activeTab === 'procs' && <ProcsTab />}
      </main>

      {/* Bottom Navigation */}
      <BottomNav active={activeNav} onChange={setActiveNav} />
    </div>
  )
}
