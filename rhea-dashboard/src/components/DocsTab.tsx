export default function DocsTab() {
  const docs = [
    { title: 'Play Product Guide', path: '/docs/PLAY_PRODUCT_GUIDE.md' },
    { title: 'Play Maintenance Guide', path: '/docs/PLAY_MAINTENANCE_GUIDE.md' },
    { title: 'Dashboard Guide', path: '/docs/STAGE5_DASHBOARD_GUIDE.md' },
    { title: 'Architecture Overview', path: '/docs/TEAM_STATUS.md' },
    { title: 'Final Delivery', path: '/docs/FINAL_DELIVERY.md' },
  ]
  
  return (
    <div className="space-y-3">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-3">Documentation</h3>
        <div className="space-y-2">
          {docs.map((doc, i) => (
            <div key={i} className="flex items-center justify-between text-xs hover:bg-slate-700 p-2 rounded cursor-pointer transition">
              <span className="text-slate-300">{doc.title}</span>
              <span className="text-slate-500">→</span>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-2 text-xs">Quick Links</h3>
        <div className="space-y-1 text-xs text-slate-400">
          <p>• API Reference: <code className="bg-slate-700 px-1 rounded">GET /sessions</code></p>
          <p>• Token Mapper: <code className="bg-slate-700 px-1 rounded">POST /allocate</code></p>
        </div>
      </div>
    </div>
  )
}
