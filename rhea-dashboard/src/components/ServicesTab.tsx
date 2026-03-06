import { useStore } from '../store'

export default function ServicesTab() {
  const procs = useStore(s => s.procs)
  
  return (
    <div className="space-y-3">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-3">Running Services</h3>
        <div className="space-y-2">
          {procs.map(p => (
            <div key={p.name} className="flex justify-between items-center text-xs">
              <span className="text-slate-300">{p.name}</span>
              <div className="flex items-center gap-2">
                <span className={`inline-block w-2 h-2 rounded-full ${p.status === 'running' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                <span className="text-slate-400 w-12 text-right">{p.port}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-2 text-xs">System Load</h3>
        <p className="text-xs text-slate-400">CPU: 8.2% • Memory: 340MB • Disk: 2.1GB</p>
      </div>
    </div>
  )
}
