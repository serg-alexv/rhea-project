'use client'
import { useEffect, useState } from 'react'
import { API_BASE } from '@/lib/config'
import { useAtlasStore, AtlasState, ViewId } from '@/store/useAtlasStore'

const FONT_MONO = '"SF Mono","Fira Code","JetBrains Mono",monospace'

// ── View tabs config ──────────────────────────────────────────────────────
interface ViewTab {
  id: ViewId
  label: string
  devLabel?: string
  tooltip: string
  external?: string // external URL instead of in-app view
}

const VIEW_TABS: ViewTab[] = [
  {
    id: 'system-pw',
    label: 'CONSOLE',
    devLabel: "THEMIS CONSOLE",
    tooltip: 'Rex Console — System Controls',
    external: `${API_BASE}/app/`,
  },
  {
    id: 'atlas-prime',
    label: 'ATLAS',
    devLabel: 'ATLAS PRIME',
    tooltip: '3D Knowledge Topology Explorer',
  },
  {
    id: 'theia-drift',
    label: 'THEIA DRIFT',
    tooltip: 'Ambient Research Observation',
    external: '/semantic-drift.html',
  },
]

// ── Code-Worm Profile ─────────────────────────────────────────────────────
const WORM_CHARS = ['{', '}', ';', '=>', '()', '[]', '::', '&&']

function CodeWormProfile() {
  const [isOpen, setIsOpen]   = useState(false)
  const [user, setUser]       = useState<{ email: string; plan: string; usage: number; limit: number } | null>(null)
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr]         = useState('')
  const [tick, setTick]       = useState(0)

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 900)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    const token = localStorage.getItem('rhea_token')
    if (!token) return
    fetch(`${API_BASE}/auth/profile`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => setUser({ email: data.email, plan: data.plan ?? 'FREE', usage: data.usage ?? 0, limit: data.limit ?? 100 }))
      .catch(() => localStorage.removeItem('rhea_token'))
  }, [])

  const doAuth = async () => {
    setErr('')
    const endpoint = isLogin ? '/auth/login' : '/auth/signup'
    try {
      const r = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await r.json()
      if (!r.ok) { setErr(data.detail ?? data.error ?? 'error'); return }
      localStorage.setItem('rhea_token', data.token ?? data.access_token ?? '')
      setUser({ email: data.email ?? email, plan: data.plan ?? 'FREE', usage: data.usage ?? 0, limit: data.limit ?? 100 })
      setIsOpen(false)
    } catch {
      setErr('network error')
    }
  }

  const doLogout = () => {
    localStorage.removeItem('rhea_token')
    setUser(null)
    setIsOpen(false)
  }

  const activeChars = WORM_CHARS.slice(tick % WORM_CHARS.length, (tick % WORM_CHARS.length) + 4)
  const isLoggedIn  = user !== null
  const usagePct    = user ? Math.min(100, Math.round((user.usage / user.limit) * 100)) : 0

  return (
    <>
      <style>{`
        @keyframes worm-orbit {
          0%   { transform: rotate(0deg) translateX(3px) rotate(0deg); opacity: 0.3; }
          50%  { opacity: 0.8; }
          100% { transform: rotate(360deg) translateX(3px) rotate(-360deg); opacity: 0.3; }
        }
        .worm-char { position: absolute; font-size: 5px; animation: worm-orbit 2s linear infinite; }
      `}</style>

      <div className="relative flex-shrink-0 ml-2">
        <span className="group relative">
        <button
          onClick={() => setIsOpen((v) => !v)}
          title={isLoggedIn ? user!.email : 'Login / Signup'}
          className={`
            relative w-5 h-5 rounded-full flex items-center justify-center
            font-mono text-[6px] font-bold uppercase tracking-tight
            transition-all duration-200 border
            ${isLoggedIn
              ? 'border-green-500/50 text-green-300 shadow-[0_0_6px_#22c55e] bg-black/60'
              : 'border-white/10 text-white/30 bg-black/40 hover:border-green-500/40 hover:text-green-300/70 hover:shadow-[0_0_6px_rgba(34,197,94,0.4)]'
            }
          `}
        >
          {isLoggedIn
            ? user!.email.slice(0, 2).toUpperCase()
            : (
              <>
                {activeChars.map((ch, i) => (
                  <span
                    key={i}
                    className="worm-char"
                    style={{ animationDelay: `${i * 0.45}s`, animationDuration: `${1.6 + i * 0.3}s` }}
                  >{ch}</span>
                ))}
              </>
            )
          }
        </button>
        <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 bg-black/90 border border-white/10 text-white/60 text-[9px] px-2.5 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-[300]">
          Login to track your research sessions
        </span>
        </span>

        {isOpen && (
          <div
            className="absolute top-7 right-0 z-[200] w-48 rounded-xl border border-white/10 bg-black/80 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.7)] p-3 flex flex-col gap-2"
            style={{ fontFamily: FONT_MONO }}
          >
            {isLoggedIn ? (
              <>
                <div className="text-[9px] font-mono text-white/60 truncate">{user!.email.slice(0, 20)}</div>
                <span className="self-start rounded-md bg-green-500/15 border border-green-500/30 text-green-400 text-[8px] font-mono px-1.5 py-0.5 uppercase tracking-widest">
                  {user!.plan}
                </span>
                <div className="text-[9px] font-mono text-white/40">{user!.usage}/{user!.limit} queries</div>
                <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full transition-all duration-500" style={{ width: `${usagePct}%` }} />
                </div>
                <button
                  onClick={doLogout}
                  className="mt-1 rounded-md border border-white/10 bg-white/5 hover:bg-red-500/10 hover:border-red-500/30 text-white/50 hover:text-red-300 text-[9px] font-mono uppercase tracking-widest px-2 py-1 transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <div className="flex gap-1 mb-1">
                  {['Login', 'Signup'].map((label) => (
                    <button
                      key={label}
                      onClick={() => { setIsLogin(label === 'Login'); setErr('') }}
                      className={`flex-1 rounded-md text-[9px] font-mono uppercase tracking-widest px-1 py-0.5 border transition-colors ${
                        (label === 'Login') === isLogin
                          ? 'border-cyan-500/40 text-cyan-400 bg-cyan-500/10'
                          : 'border-white/5 text-white/30'
                      }`}
                    >{label}</button>
                  ))}
                </div>
                <input
                  type="email"
                  placeholder="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-md bg-white/5 border border-white/10 text-white/80 text-[9px] font-mono px-2 py-1 outline-none focus:border-cyan-500/40 placeholder:text-white/20"
                />
                <input
                  type="password"
                  placeholder="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && doAuth()}
                  className="w-full rounded-md bg-white/5 border border-white/10 text-white/80 text-[9px] font-mono px-2 py-1 outline-none focus:border-cyan-500/40 placeholder:text-white/20"
                />
                {err && <div className="text-[8px] font-mono text-red-400/80">{err}</div>}
                <button
                  onClick={doAuth}
                  className="rounded-md border border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-[9px] font-mono uppercase tracking-widest px-2 py-1 transition-colors"
                >
                  {isLogin ? 'Login' : 'Create account'}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </>
  )
}

// ── Hyperion Bar ──────────────────────────────────────────────────────────
export default function HyperionBar() {
  const providerCount = useAtlasStore((s: AtlasState) => s.providerCount)
  const redisStatus   = useAtlasStore((s: AtlasState) => s.redisStatus)
  const activeView    = useAtlasStore((s: AtlasState) => s.activeView)
  const setActiveView = useAtlasStore((s: AtlasState) => s.setActiveView)
  const [isDevHost, setIsDevHost] = useState(false)

  useEffect(() => {
    const host = window.location.hostname
    setIsDevHost(host === 'localhost' || host === '127.0.0.1')
  }, [])

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[100] flex items-center px-3.5 gap-0"
      style={{
        height: '30px',
        background: 'rgba(0,0,0,0.82)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        fontFamily: FONT_MONO,
      }}
    >
      {/* Logo */}
      <span className="group relative text-cyan-400 font-bold text-[10px] tracking-[0.18em] uppercase mr-3.5 flex items-center gap-1 cursor-default">
        RHEA
        {isDevHost && (
          <span className="text-red-500 text-[7px] uppercase font-bold tracking-widest">DEV</span>
        )}
        <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 bg-black/90 border border-white/10 text-white/60 text-[9px] px-2.5 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-[300]">
          Rhythmic Homeostasis Engine for Adaptation
        </span>
      </span>

      {/* Separator */}
      <div className="w-px h-3.5 bg-white/10 mx-3" />

      {/* View tabs */}
      {VIEW_TABS.map((tab) => {
        const isActive = tab.id === activeView && !tab.external
        const label = isDevHost ? (tab.devLabel ?? tab.label) : tab.label

        if (tab.external) {
          return (
            <a
              key={tab.id}
              href={tab.external}
              className="group relative flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-widest text-white/38 transition-colors duration-150 hover:text-white/72 hover:bg-white/5"
            >
              {label} &rarr;
              <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 bg-black/90 border border-white/10 text-white/60 text-[9px] px-2.5 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-[300]">
                {tab.tooltip}
              </span>
            </a>
          )
        }

        return (
          <button
            key={tab.id}
            onClick={() => setActiveView(tab.id)}
            className={`group relative flex items-center gap-1.5 px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-widest transition-colors duration-150 ${
              isActive
                ? 'text-cyan-400 cursor-default'
                : 'text-white/38 hover:text-white/72 hover:bg-white/5'
            }`}
          >
            {isActive && (
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_5px_#22c55e] flex-shrink-0" />
            )}
            {label}
            {isActive && (
              <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-cyan-400 rounded-t" />
            )}
            <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 bg-black/90 border border-white/10 text-white/60 text-[9px] px-2.5 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-[300]">
              {tab.tooltip}
            </span>
          </button>
        )
      })}

      {/* Right-side meta */}
      <div className="ml-auto flex items-center gap-3 text-[9px] font-mono uppercase tracking-widest text-white/22">
        <span className="normal-case tracking-normal text-white/20" style={{ fontSize: '9px', letterSpacing: '0.03em', textTransform: 'none' }}>
          All features unlocked &bull; Some actions use AI credits
        </span>
        {providerCount > 0 && (
          <span>{providerCount} providers</span>
        )}
        <span className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
              redisStatus === 'up'   ? 'bg-green-500' :
              redisStatus === 'down' ? 'bg-red-500'   : 'bg-yellow-500'
            }`}
          />
          redis&nbsp;{redisStatus}
        </span>
      </div>

      {/* Code-worm profile button */}
      <CodeWormProfile />
    </div>
  )
}
