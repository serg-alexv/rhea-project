export default function SecurityTab() {
  return (
    <div className="space-y-3">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-3">Authentication</h3>
        <div className="space-y-2 text-xs text-slate-400">
          <div className="flex justify-between items-center">
            <span>Inverse Captcha</span>
            <span className="text-green-400 font-medium">Active</span>
          </div>
          <p className="text-slate-500 text-xs mt-2">AI-only challenge. No brute force possible.</p>
        </div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-3">TCC Permissions</h3>
        <div className="space-y-2 text-xs text-slate-400">
          <div className="flex justify-between">
            <span>Network Extension</span>
            <span className="text-yellow-400">Pending</span>
          </div>
          <div className="flex justify-between">
            <span>System Daemon</span>
            <span className="text-yellow-400">Pending</span>
          </div>
        </div>
      </div>
    </div>
  )
}
