import { useStore } from '../store'

export default function SessionFlightViz() {
  const sessions = useStore(s => s.sessions)

  if (!sessions || sessions.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center">
        <p className="text-slate-400">No sessions to visualize</p>
      </div>
    )
  }

  const maxLC = Math.max(...sessions.map(s => s.lamport_clock || 0), 10)

  return (
    <div className="space-y-4">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-4">Session Flight Timeline</h3>
        <div className="space-y-3">
          {sessions.map(s => (
            <div key={s.id} className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400 font-mono">{s.id.slice(0, 8)}</span>
                <span className="text-slate-300">LC: {s.lamport_clock || 0}</span>
              </div>
              <div className="bg-slate-700 rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all"
                  style={{width: `${((s.lamport_clock || 0) / maxLC) * 100}%`}}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-500">
                <span>{s.message_count} msg</span>
                <span>{s.devices} dev</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-3">Timeline Stats</h3>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <p className="text-slate-400">Total Sessions</p>
            <p className="text-2xl font-bold text-blue-400">{sessions.length}</p>
          </div>
          <div>
            <p className="text-slate-400">Max LC</p>
            <p className="text-2xl font-bold text-purple-400">{maxLC}</p>
          </div>
          <div>
            <p className="text-slate-400">Total Messages</p>
            <p className="text-xl font-bold text-green-400">{sessions.reduce((sum, s) => sum + s.message_count, 0)}</p>
          </div>
          <div>
            <p className="text-slate-400">Total Devices</p>
            <p className="text-xl font-bold text-yellow-400">{sessions.reduce((sum, s) => sum + s.devices, 0)}</p>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-xs text-slate-400">
        <p className="mb-2 font-medium text-slate-300">How to Read:</p>
        <ul className="space-y-1 list-disc list-inside">
          <li>Bar width = Lamport Clock progress (LC / max)</li>
          <li>Longer bar = more messages processed</li>
          <li>Deterministic ordering guaranteed by LC logic</li>
          <li>See <code className="bg-slate-700 px-1 rounded">docs/decisions.md</code> (ADR-017)</li>
        </ul>
      </div>
    </div>
  )
}
