export default function AITab() {
  return (
    <div className="space-y-3">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-3">AI Services</h3>
        <div className="space-y-2 text-xs text-slate-400">
          <div className="flex justify-between">
            <span>Auth Captcha</span>
            <span className="text-green-400">✓</span>
          </div>
          <div className="flex justify-between">
            <span>Angel Game Evaluator</span>
            <span className="text-green-400">✓</span>
          </div>
          <div className="flex justify-between">
            <span>RAG Embeddings</span>
            <span className="text-yellow-400">⚠</span>
          </div>
        </div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-2">Last Query</h3>
        <p className="text-xs text-slate-400">No active queries</p>
      </div>
    </div>
  )
}
