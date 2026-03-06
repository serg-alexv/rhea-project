import { useStore } from '../store'

export default function ProcsTab() {
  const procs = useStore(s => s.procs)
  
  return (
    <div className="space-y-3">
      {procs.map(p => (
        <div key={p.name} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="flex justify-between items-center mb-2">
            <div>
              <h3 className="font-medium text-sm">{p.name}</h3>
              <p className="text-xs text-slate-400 mt-1">Port {p.port}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className={`inline-block w-2 h-2 rounded-full ${p.status === 'running' ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="text-xs text-slate-300 capitalize">{p.status}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>Uptime: {(p.uptime / 60).toFixed(1)}m</span>
            <span>•</span>
            <span>CPU: 2.3% • MEM: 45MB</span>
          </div>
        </div>
      ))}
    </div>
  )
}
