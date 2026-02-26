'use client'
import { useState } from 'react'
import { API_BASE } from '@/lib/config'

type Agent = {
  id: string
  name: string
  domain: string
  color: string
  actions: [string, string, string]
}

const AGENTS: Agent[] = [
  { id: 'A1', name: 'Quantitative Scientist', domain: 'Fourier, Bayesian, MPC',    color: '#60a5fa', actions: ['Validate Model', 'Run Fourier',    'Bayesian Check'] },
  { id: 'A2', name: 'Life Sciences',          domain: 'HRV, chronobiology, sleep', color: '#34d399', actions: ['HRV Analysis',   'Chrono Query',   'Sleep Science']  },
  { id: 'A3', name: 'Psychologist',           domain: 'ADHD, behavioral signals',  color: '#a78bfa', actions: ['Profile Check',  'ADHD Optimize',  'Behavioral Scan'] },
  { id: 'A4', name: 'Linguist-Culturologist', domain: '42 calendars, symbolism',   color: '#fbbf24', actions: ['Calendar Systems','Symbolic Analysis','Cultural Map'] },
  { id: 'A5', name: 'Product Architect',      domain: 'UX, HealthKit, iOS',        color: '#f472b6', actions: ['UI Prototype',   'UX Review',      'HealthKit Query'] },
  { id: 'A6', name: 'Tech Lead',              domain: 'API, bridge, infra',         color: '#38bdf8', actions: ['Bridge Status',  'API Audit',      'Infra Check']    },
  { id: 'A7', name: 'Growth Strategist',      domain: 'market, monetization',       color: '#fb923c', actions: ['Market Scan',    'Monetize Check', 'Growth Plan']    },
  { id: 'A8', name: 'Critical Reviewer',      domain: 'tribunal, quality gate',     color: '#f87171', actions: ['Quality Gate',   'Gap Analysis',   'Challenge This'] },
]

export default function AgentRoster() {
  const [busy, setBusy] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<{ agentId: string; action: string; text: string } | null>(null)

  const runAction = async (agent: Agent, action: string) => {
    const key = `${agent.id}:${action}`
    if (busy) return
    setBusy(key)
    setLastResult(null)
    try {
      const res = await fetch(`${API_BASE}/api/tribunal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `[${agent.name}] ${action}`,
          context: agent.domain,
          mode: 'tribunal',
          ontology: 'general',
        }),
      })
      const data = await res.json()
      setLastResult({ agentId: agent.id, action, text: data.result ?? data.answer ?? data.message ?? 'done' })
    } catch {
      setLastResult({ agentId: agent.id, action, text: 'error — API unreachable' })
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="space-y-2">
      {AGENTS.map((agent) => (
        <div
          key={agent.id}
          className="rounded-xl border border-white/5 bg-black/25 px-2.5 py-2"
          style={{ borderLeftColor: agent.color, borderLeftWidth: 2 }}
        >
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[10px]" style={{ color: agent.color }}>◉</span>
            <span className="text-[10px] font-mono font-bold text-white/80">{agent.id}</span>
            <span className="text-[10px] font-mono text-white/70 truncate">{agent.name}</span>
          </div>
          <div className="text-[8px] font-mono text-white/35 mb-1.5 truncate">{agent.domain}</div>
          <div className="flex gap-1 flex-wrap">
            {agent.actions.map((action) => {
              const key = `${agent.id}:${action}`
              const isRunning = busy === key
              return (
                <button
                  key={action}
                  onClick={() => runAction(agent, action)}
                  disabled={!!busy}
                  className="rounded px-1.5 py-0.5 text-[8px] font-mono border transition-colors disabled:opacity-40"
                  style={{
                    borderColor: `${agent.color}55`,
                    color: isRunning ? agent.color : `${agent.color}bb`,
                    backgroundColor: isRunning ? `${agent.color}18` : 'transparent',
                  }}
                  onMouseEnter={(e) => { if (!busy) (e.currentTarget as HTMLButtonElement).style.backgroundColor = `${agent.color}18` }}
                  onMouseLeave={(e) => { if (!isRunning) (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent' }}
                >
                  {isRunning ? '…' : action}
                </button>
              )
            })}
          </div>
          {lastResult?.agentId === agent.id && (
            <div className="mt-1.5 text-[8px] font-mono text-white/40 leading-relaxed line-clamp-2">
              <span style={{ color: agent.color }}>↳</span> {lastResult.action}: {lastResult.text}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
