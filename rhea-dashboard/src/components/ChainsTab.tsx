import { useStore } from '../store'
import SessionFlightViz from './SessionFlightViz'

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

  return <SessionFlightViz />
}
