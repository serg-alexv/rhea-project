import { useStore } from '../store'

export default function ChainsTab() {
  const sessions = useStore(s => s.sessions)
  
  if (!sessions || sessions.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <p className="text-lg">No sessions yet</p>
        <p className="text-sm mt-2">Create one with <code className="bg-slate-800 px-2 py-1 rounded">rhea session create</code></p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {sessions.map(s => (
        <div key={s.id} className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition cursor-pointer">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="font-mono text-sm text-slate-300">{s.id.slice(0, 8)}</h3>
              <p className="text-xs text-slate-400 mt-1">
                {s.message_count} messages • LC: {s.lamport_clock} • {s.devices} device{s.devices !== 1 ? 's' : ''}
              </p>
            </div>
            <div className="flex gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500"></span>
              <span className="text-xs text-slate-400">synced</span>
            </div>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1">
            <div className="bg-green-500 h-1 rounded-full" style={{width: `${(s.lamport_clock / 100) * 100}%`}}></div>
          </div>
        </div>
      ))}
    </div>
  )
}
