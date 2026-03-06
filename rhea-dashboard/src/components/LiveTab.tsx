export default function LiveTab() {
  return (
    <div className="space-y-3">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-3">Live Dashboard</h3>
        <div className="space-y-3 text-xs">
          <div>
            <p className="text-slate-400 mb-1">Active Sessions</p>
            <p className="text-2xl font-bold text-green-400">0</p>
          </div>
          <div>
            <p className="text-slate-400 mb-1">Total Messages</p>
            <p className="text-2xl font-bold text-blue-400">0</p>
          </div>
          <div>
            <p className="text-slate-400 mb-1">Max Lamport Clock</p>
            <p className="text-2xl font-bold text-purple-400">0</p>
          </div>
        </div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-2">System Status</h3>
        <div className="space-y-1 text-xs text-slate-400">
          <div className="flex justify-between">
            <span>Uptime</span>
            <span>4h 32m</span>
          </div>
          <div className="flex justify-between">
            <span>Network</span>
            <span className="text-green-400">Connected</span>
          </div>
          <div className="flex justify-between">
            <span>Database</span>
            <span className="text-green-400">Synced</span>
          </div>
        </div>
      </div>
    </div>
  )
}
