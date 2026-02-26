'use client'
import dynamic from 'next/dynamic'
import { Suspense, useEffect, useMemo, useState } from 'react'
import { API_BASE } from '@/lib/config'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, Stars, Float } from '@react-three/drei'
import { animate, motion, AnimatePresence, useMotionValue } from 'framer-motion'
import * as THREE from 'three'
import { getLastHealth, useAtlasSync } from '@/hooks/useAtlasSync'
import { useAtlasStore, AtlasState } from '@/store/useAtlasStore'

const RuliadicIsland  = dynamic(() => import('@/components/RuliadicIsland'),  { ssr: false })
const IsomorphismBeam = dynamic(() => import('@/components/IsomorphismBeam'), { ssr: false })
const ResearchPanel   = dynamic(() => import('@/components/ResearchPanel'),   { ssr: false })
const SessionTimeline = dynamic(() => import('@/components/SessionTimeline'), { ssr: false })
const AtlasScene      = dynamic(() => import('@/components/atlas/AtlasScene'), { ssr: false })
const MagneticNebula  = dynamic(() => import('@/components/atlas/MagneticNebula'), { ssr: false })
const AgentRoster     = dynamic(() => import('@/components/AgentRoster'),     { ssr: false })
const MnemosyneWhisper = dynamic(() => import('@/components/MnemosyneWhisper'), { ssr: false })

const IS_DEV = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

type UiSchema = 'prime' | 'mesh'
let PANEL_Z = 30

type ColorProfile = 'tribunal' | 'ice' | 'ember' | 'mono'
type AgentHubView = 'coach' | 'ops' | 'compact'
type DockSlot = 'tl' | 'tc' | 'tr' | 'ml' | 'mc' | 'mr' | 'bl' | 'bc' | 'br'
type ManagedPanelId = 'hud' | 'intent' | 'council' | 'timeline' | 'research' | 'pw' | 'memory' | 'agents'

type PanelDockState = {
  slot: DockSlot
  minimized: boolean
}

type FloatingPanelManaged = {
  id: ManagedPanelId | string
  title: string
  slot: DockSlot
  focused: boolean
  uiIdle: boolean
  minimized: boolean
  panelIndex: number
  onFocus: () => void
  onToggleMin: () => void
  onCycleSlot: (dir: -1 | 1) => void
}

const DOCK_SLOT_ORDER: DockSlot[] = ['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br']
const DOCK_SLOT_CLASS: Record<DockSlot, string> = {
  tl: 'top-8 left-8',
  tc: 'top-8 left-1/2 -translate-x-1/2',
  tr: 'top-8 right-8',
  ml: 'top-[20rem] left-8',
  mc: 'top-[20rem] left-1/2 -translate-x-1/2',
  mr: 'top-[20rem] right-8',
  bl: 'bottom-8 left-8',
  bc: 'bottom-8 left-1/2 -translate-x-1/2',
  br: 'bottom-8 right-8',
}

const PANEL_ORDER: ManagedPanelId[] = ['hud', 'council', 'timeline', 'agents', 'research', 'memory', 'pw', 'intent']

const DEFAULT_DOCK_LAYOUT: Record<ManagedPanelId, PanelDockState> = {
  hud:      { slot: 'tl', minimized: false },
  council:  { slot: 'tr', minimized: false },
  timeline: { slot: 'tc', minimized: false },
  agents:   { slot: 'ml', minimized: false },
  research: { slot: 'mr', minimized: false },
  memory:   { slot: 'mc', minimized: false },
  pw:       { slot: 'bc', minimized: false },
  intent:   { slot: 'bl', minimized: false },
}

function nextSlot(slot: DockSlot, dir: -1 | 1): DockSlot {
  const idx = DOCK_SLOT_ORDER.indexOf(slot)
  const next = (idx + dir + DOCK_SLOT_ORDER.length) % DOCK_SLOT_ORDER.length
  return DOCK_SLOT_ORDER[next]
}

function hashText(input: string): number {
  let h = 2166136261
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function colorFromHash(seedText: string, profile: ColorProfile = 'tribunal', salt = 0): string {
  const h = hashText(`${seedText}:${salt}`)
  const profiles: Record<ColorProfile, [number, number, number]> = {
    tribunal: [192, 70, 56],
    ice: [210, 45, 66],
    ember: [24, 84, 56],
    mono: [0, 0, 62],
  }
  const [baseH, baseS, baseL] = profiles[profile]
  const hue = (baseH + (h % 180) - 90 + 360) % 360
  const sat = Math.max(12, Math.min(96, baseS + ((h >> 8) % 20) - 10))
  const lig = Math.max(28, Math.min(78, baseL + ((h >> 16) % 18) - 9))
  return `hsl(${hue} ${sat}% ${lig}%)`
}

// ── CrossNav + CodeWormProfile extracted to components/HyperionBar.tsx ────

function FloatingPanel({
  children,
  position,
  panelId,
  managed,
}: {
  children: React.ReactNode
  position: string
  panelId?: string
  managed?: FloatingPanelManaged
}) {
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const [zIndex, setZIndex] = useState(++PANEL_Z)
  const snap = () => {
    const step = 24
    animate(x, Math.round(x.get() / step) * step, { type: 'spring', stiffness: 500, damping: 34 })
    animate(y, Math.round(y.get() / step) * step, { type: 'spring', stiffness: 500, damping: 34 })
  }
  const shellTone = managed
    ? managed.focused
      ? 'border-cyan-500/20 bg-black/55 opacity-100 shadow-[0_0_55px_rgba(34,211,238,0.08)]'
      : managed.uiIdle
        ? 'border-white/5 bg-black/20 opacity-60 shadow-[0_0_30px_rgba(0,0,0,0.35)]'
        : 'border-white/5 bg-black/30 opacity-80 shadow-[0_0_36px_rgba(0,0,0,0.42)]'
    : 'border-white/5 bg-white/5 opacity-100 shadow-[0_0_50px_rgba(0,0,0,0.5)]'
  const panelClass = managed
    ? `absolute ${DOCK_SLOT_CLASS[managed.slot]} ${position} z-20 rounded-3xl border backdrop-blur-2xl transition-opacity duration-200`
    : `absolute ${position} z-20 p-6 rounded-3xl border backdrop-blur-2xl cursor-grab active:cursor-grabbing`
  return (
    <motion.div
      data-panel={panelId ?? managed?.id}
      drag={managed ? false : true}
      dragMomentum={managed ? undefined : false}
      dragConstraints={managed ? undefined : { left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={managed ? undefined : 0.1}
      style={managed ? { zIndex: managed.focused ? 120 : 80 } : { x, y, zIndex }}
      onPointerDown={() => {
        if (managed) managed.onFocus()
        else setZIndex(++PANEL_Z)
      }}
      onFocusCapture={() => {
        if (managed) managed.onFocus()
        else setZIndex(++PANEL_Z)
      }}
      onDragStart={managed ? undefined : () => setZIndex(++PANEL_Z)}
      onDragEnd={managed ? undefined : snap}
      whileHover={managed ? { scale: 1 } : { scale: 1.02 }}
      whileDrag={managed ? undefined : { scale: 1.015 }}
      tabIndex={0}
      className={`${panelClass} ${shellTone} ${managed ? 'outline-none' : ''}`}
    >
      <div className={managed ? 'p-3' : 'p-6'}>
        {managed && (
          <div className={`mb-2 flex items-center gap-2 ${managed.focused ? 'opacity-100' : 'opacity-70'} transition-opacity`}>
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={() => managed.onCycleSlot(-1)}
              className="h-5 w-5 rounded-md border border-white/10 bg-black/30 text-[10px] font-mono text-gray-300/70 hover:text-cyan-300/80"
              aria-label={`Move ${managed.title} to previous slot`}
              title="Previous slot"
            >
              ←
            </button>
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={managed.onToggleMin}
              className={`h-5 rounded-md border px-1.5 text-[9px] font-mono uppercase tracking-widest ${
                managed.minimized
                  ? 'border-amber-500/25 bg-amber-500/5 text-amber-300/80'
                  : 'border-white/10 bg-black/30 text-gray-300/70 hover:text-cyan-300/80'
              }`}
              aria-expanded={!managed.minimized}
              title={managed.minimized ? 'Restore panel' : 'Minimize panel'}
            >
              {managed.minimized ? 'Restore' : 'Min'}
            </button>
            <div className="min-w-0 flex-1 truncate text-[9px] font-mono uppercase tracking-widest text-gray-500">
              {managed.title} · slot {managed.panelIndex}
            </div>
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={() => managed.onCycleSlot(1)}
              className="h-5 w-5 rounded-md border border-white/10 bg-black/30 text-[10px] font-mono text-gray-300/70 hover:text-cyan-300/80"
              aria-label={`Move ${managed.title} to next slot`}
              title="Next slot"
            >
              →
            </button>
          </div>
        )}
        {!managed?.minimized ? children : (
          <div className="text-[9px] font-mono text-gray-500">minimized · use Alt+Tab / Alt+1..9 / Alt+0</div>
        )}
      </div>
    </motion.div>
  )
}

// Redis indicator dot colour
const REDIS_COLOR: Record<string, string> = {
  up:      'bg-green-500',
  down:    'bg-red-500',
  unknown: 'bg-yellow-500',
}

function HudLeft({ managed }: { managed?: FloatingPanelManaged }) {
  const dMetric      = useAtlasStore((s: AtlasState) => s.dMetric)
  const apiHealthy   = useAtlasStore((s: AtlasState) => s.apiHealthy)
  const providerCount = useAtlasStore((s: AtlasState) => s.providerCount)
  const redisStatus  = useAtlasStore((s: AtlasState) => s.redisStatus)
  const showOceanusFlow = useAtlasStore((s: AtlasState) => s.showOceanusFlow)
  const toggleOceanusFlow = useAtlasStore((s: AtlasState) => s.toggleOceanusFlow)

  return (
    <FloatingPanel position={managed ? 'w-72' : 'top-8 left-8 w-72'} managed={managed}>
      <h1 className="text-lg font-bold tracking-tighter text-cyan-400/80 mb-1">RHEA ATLAS</h1>
      <p className="text-[9px] uppercase tracking-[0.4em] opacity-30 mb-6 font-mono font-bold">
        Zen Garden Mode
      </p>
      <div className="space-y-4">
        {/* D-Metric */}
        <div className="flex justify-between text-[10px] font-mono">
          <span className="opacity-40">DRIFT</span>
          <span className="text-cyan-400">{dMetric > 0 ? dMetric.toFixed(2) : '—'}</span>
        </div>
        <div className="w-full bg-white/5 h-[1px] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, (dMetric / 400) * 100)}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="bg-cyan-500/30 h-full"
          />
        </div>

        {/* API health */}
        <div className="flex justify-between text-[10px] font-mono">
          <span className="opacity-40">API</span>
          <span className={apiHealthy ? 'text-green-400' : 'text-red-400/60'}>
            {apiHealthy ? 'online' : 'offline'}
          </span>
        </div>

        {/* Provider count */}
        {providerCount > 0 && (
          <div className="flex justify-between text-[10px] font-mono">
            <span className="opacity-40">PROVIDERS</span>
            <span className="text-cyan-400">{providerCount}</span>
          </div>
        )}

        {/* Redis status */}
        <div className="flex justify-between items-center text-[10px] font-mono">
          <span className="opacity-40">REDIS</span>
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${REDIS_COLOR[redisStatus]} ${redisStatus === 'up' ? 'animate-pulse' : ''}`} />
            <span className="text-gray-400">{redisStatus}</span>
          </div>
        </div>

        {/* Oceanus Flow toggle */}
        <div className="pt-1 border-t border-white/5">
          <div className="flex justify-between items-center text-[10px] font-mono">
            <span className="opacity-40">OCEANUS</span>
            <button
              type="button"
              onClick={toggleOceanusFlow}
              className={`rounded-md border px-2 py-0.5 text-[9px] uppercase tracking-widest transition-colors ${
                showOceanusFlow
                  ? 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300'
                  : 'border-white/10 bg-black/20 text-gray-500 hover:text-gray-300'
              }`}
              aria-pressed={showOceanusFlow}
              title={showOceanusFlow ? 'Hide Oceanus Flow' : 'Show Oceanus Flow'}
            >
              {showOceanusFlow ? 'On' : 'Off'}
            </button>
          </div>
          <div className="mt-1 text-[8px] font-mono text-gray-600">
            Density field + vectors {showOceanusFlow ? 'active' : 'hidden'}
          </div>
        </div>
      </div>
    </FloatingPanel>
  )
}

function HelperAvatar({
  label,
  role,
  online,
  emphasis = 0.5,
}: {
  label: string
  role: 'navigator' | 'builder' | 'skeptic' | 'archivist'
  online: boolean
  emphasis?: number
}) {
  const roleStyle: Record<'navigator' | 'builder' | 'skeptic' | 'archivist', { ring: string; glow: string; bg: string }> = {
    navigator: { ring: 'border-cyan-400/40', glow: 'shadow-[0_0_14px_rgba(34,211,238,0.35)]', bg: 'from-cyan-500/25 to-blue-500/10' },
    builder: { ring: 'border-emerald-400/40', glow: 'shadow-[0_0_14px_rgba(52,211,153,0.35)]', bg: 'from-emerald-500/25 to-lime-500/10' },
    skeptic: { ring: 'border-amber-400/40', glow: 'shadow-[0_0_14px_rgba(251,191,36,0.28)]', bg: 'from-amber-500/20 to-orange-500/10' },
    archivist: { ring: 'border-fuchsia-400/40', glow: 'shadow-[0_0_14px_rgba(232,121,249,0.28)]', bg: 'from-fuchsia-500/20 to-violet-500/10' },
  }
  const style = roleStyle[role]
  const initials = label
    .split(/\s+/)
    .slice(0, 2)
    .map((s) => s[0] ?? '')
    .join('')
    .toUpperCase()
  const scanlineOpacity = Math.max(0.08, Math.min(0.28, emphasis * 0.22))

  return (
    <div className="relative w-10 h-10 flex-shrink-0">
      <div className={`absolute inset-0 rounded-full border ${style.ring} ${style.glow} ${online ? 'animate-pulse' : ''}`} />
      <div className={`absolute inset-[2px] rounded-full bg-gradient-to-br ${style.bg} border border-white/10 overflow-hidden`}>
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `linear-gradient(to bottom, rgba(255,255,255,${scanlineOpacity}) 1px, transparent 1px)`,
            backgroundSize: '100% 4px',
          }}
        />
        <div className="absolute inset-0 flex items-center justify-center text-[9px] font-mono font-bold text-white/85 tracking-widest">
          {initials}
        </div>
      </div>
      <div className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border border-black/60 ${online ? 'bg-green-500' : 'bg-yellow-500'}`} />
    </div>
  )
}

function AgentsProvidersZone({
  selectedNode,
  uiSchema,
  managed,
}: {
  selectedNode: string
  uiSchema: UiSchema
  managed?: FloatingPanelManaged
}) {
  const providerCount = useAtlasStore((s: AtlasState) => s.providerCount)
  const redisStatus = useAtlasStore((s: AtlasState) => s.redisStatus)
  const apiHealthy = useAtlasStore((s: AtlasState) => s.apiHealthy)
  const dMetric = useAtlasStore((s: AtlasState) => s.dMetric)
  const consensusScore = useAtlasStore((s: AtlasState) => s.consensusScore)
  const sessionHistory = useAtlasStore((s: AtlasState) => s.sessionHistory)
  const activeSessionId = useAtlasStore((s: AtlasState) => s.activeSessionId)
  const [view, setView] = useState<AgentHubView>('coach')
  const { auditRecords } = getLastHealth()
  const last = sessionHistory[0]
  const galaxyName = selectedNode
  const starSeed = (last?.query ?? selectedNode)
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 3)
    .join(' ')
  const planetCount = Math.max(1, Math.min(12, Math.ceil((auditRecords || sessionHistory.length || 1) / 2)))
  const moonCount = Math.max(1, Math.min(12, Math.ceil((sessionHistory.length || 1) / 2)))
  const unresolved = Math.max(0, Math.min(1, 1 - consensusScore / 100))

  const helpers = useMemo(() => ([
    {
      id: 'rex',
      label: 'Rex Navigator',
      role: 'navigator' as const,
      online: apiHealthy,
      note: apiHealthy ? 'Routes work across System\'s P&W and Atlas.' : 'API degraded. Route via local relay/file evidence.',
    },
    {
      id: 'sonnet',
      label: 'Sonnet Swarm',
      role: 'builder' as const,
      online: providerCount > 0,
      note: providerCount > 0 ? 'Use for coding/test loops to save Orion context.' : 'Waiting for provider capacity or model routing.',
    },
    {
      id: 'skeptic',
      label: 'Sceptic Analyst',
      role: 'skeptic' as const,
      online: sessionHistory.length > 0,
      note: last ? `Challenge path after ${last.mode}/${last.ontology}.` : 'Seed with a Tribunal/Sceptic query for contradiction checks.',
    },
    {
      id: 'archive',
      label: 'Memory Archivist',
      role: 'archivist' as const,
      online: redisStatus !== 'down',
      note: `Tracks context snapshots and drift (${dMetric.toFixed(1)}).`,
    },
  ]), [apiHealthy, providerCount, sessionHistory.length, last, redisStatus, dMetric])

  const tips = useMemo(() => {
    const base = [
      apiHealthy
        ? 'One-window routing is active: move between Atlas, System\'s P&W, and Semantic Drift without losing session flow.'
        : 'API offline: use Semantic Drift for visual sketching, then return when Atlas reconnects.',
      providerCount > 0
        ? `Providers detected (${providerCount}). Prefer Sonnet Swarm for implementation loops.`
        : 'No providers visible. Keep requests short and validate using local relay evidence.',
      `Cosmic Scientific v1: "${galaxyName}" is the galaxy; "${starSeed || 'seed term'}" is the current star.`,
    ]
    if (redisStatus !== 'up') base.push('Redis/STM degraded: relay geometry may be stale, so rely on timestamps and source labels.')
    if (!activeSessionId) base.push('Run one Tribunal/Sceptic/ICE query to seed stars, planets, and memory-map colors deterministically.')
    return view === 'compact' ? base.slice(0, 2) : base
  }, [apiHealthy, providerCount, galaxyName, starSeed, redisStatus, activeSessionId, view])

  const universeName = uiSchema === 'mesh' ? 'Mesh Universe' : 'Prime Universe'

  return (
    <FloatingPanel panelId="agents-providers" position={managed ? 'w-[26rem]' : 'top-32 left-[21rem] w-[26rem]'} managed={managed}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Agents &amp; Providers</h2>
        <span className="text-[9px] font-mono text-cyan-300/60">vector helpers · v1</span>
      </div>

      <div className="flex gap-1 mb-3">
        {(['coach', 'ops', 'compact'] as AgentHubView[]).map((preset) => (
          <button
            key={preset}
            onClick={() => setView(preset)}
            className={`rounded-md px-2 py-1 text-[9px] font-mono uppercase tracking-widest border ${
              view === preset ? 'border-cyan-500/35 text-cyan-300 bg-cyan-500/10' : 'border-white/5 text-gray-500 bg-black/20'
            }`}
          >
            {preset}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2 mb-3 text-[9px] font-mono">
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Providers · {providerCount || '—'}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Redis · {redisStatus}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">API · {apiHealthy ? 'online' : 'offline'}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Audit · {auditRecords || 0}</div>
      </div>

      <div className="space-y-2 mb-3">
        {helpers.slice(0, view === 'compact' ? 2 : helpers.length).map((helper) => (
          <div key={helper.id} className="rounded-xl border border-white/5 bg-black/25 p-2.5 flex items-start gap-2">
            <HelperAvatar
              label={helper.label}
              role={helper.role}
              online={helper.online}
              emphasis={Math.min(1, Math.max(0.2, dMetric / 400))}
            />
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <div className="text-[10px] font-mono text-white/75 truncate">{helper.label}</div>
                <span className={`text-[8px] font-mono uppercase tracking-widest ${helper.online ? 'text-emerald-300/80' : 'text-amber-300/70'}`}>
                  {helper.online ? 'ready' : 'standby'}
                </span>
              </div>
              <div className="text-[9px] font-mono text-gray-400 leading-relaxed">{helper.note}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-white/5 bg-black/30 p-3 mb-3">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Cosmic Scientific v1</div>
          <div className="text-[8px] font-mono text-cyan-300/60">legended schema</div>
        </div>
        <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-[9px] font-mono">
          <span className="text-cyan-300/70">Universe</span><span className="text-gray-400">{universeName} (corpus space)</span>
          <span className="text-cyan-300/70">Galaxy</span><span className="text-gray-400">{galaxyName} (domain cluster)</span>
          <span className="text-cyan-300/70">Core</span><span className="text-gray-400">semantic centroid (selected focus)</span>
          <span className="text-cyan-300/70">Star</span><span className="text-gray-400">{starSeed || 'seed term'} (canonical concept)</span>
          <span className="text-cyan-300/70">Planets</span><span className="text-gray-400">{planetCount} concrete instances/examples</span>
          <span className="text-cyan-300/70">Moons</span><span className="text-gray-400">{moonCount} evidence chunks/quotes</span>
          <span className="text-cyan-300/70">Nebula</span><span className="text-gray-400">uncertain/emergent semantics · {Math.round(unresolved * 100)}% unresolved</span>
        </div>
      </div>

      {view !== 'ops' && (
        <div className="space-y-1.5">
          {tips.map((tip, i) => (
            <div key={`${i}:${tip}`} className="rounded-lg border border-white/5 bg-black/20 px-2 py-1.5 text-[9px] font-mono text-gray-300/70 leading-relaxed">
              <span className="text-cyan-300/60 mr-1">tip{i + 1}:</span>{tip}
            </div>
          ))}
        </div>
      )}
    </FloatingPanel>
  )
}

function SystemPWZone({
  selectedNode,
  uiSchema,
  visibleZones,
  managed,
}: {
  selectedNode: string
  uiSchema: UiSchema
  visibleZones: number
  managed?: FloatingPanelManaged
}) {
  const dMetric = useAtlasStore((s: AtlasState) => s.dMetric)
  const apiHealthy = useAtlasStore((s: AtlasState) => s.apiHealthy)
  const providerCount = useAtlasStore((s: AtlasState) => s.providerCount)
  const redisStatus = useAtlasStore((s: AtlasState) => s.redisStatus)
  const consensusScore = useAtlasStore((s: AtlasState) => s.consensusScore)
  const islands = useAtlasStore((s: AtlasState) => s.islands)
  const activeIslandId = useAtlasStore((s: AtlasState) => s.activeIslandId)
  const activeSessionId = useAtlasStore((s: AtlasState) => s.activeSessionId)
  const sessionHistory = useAtlasStore((s: AtlasState) => s.sessionHistory)
  const last = sessionHistory[0]
  const weights = [
    ['drift', Math.min(1, dMetric / 400)],
    ['consensus', Math.min(1, consensusScore / 100)],
    ['sessions', Math.min(1, sessionHistory.length / 50)],
    ['providers', Math.min(1, providerCount / 8)],
  ] as const

  return (
    <FloatingPanel panelId="system-pw" position={managed ? 'w-[32rem]' : 'bottom-8 left-1/2 -translate-x-1/2 w-[32rem]'} managed={managed}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500">{IS_DEV ? <>System&apos;s P&amp;W</> : 'Console'}</h2>
        <span className="text-[9px] font-mono text-cyan-300/60">extended zone</span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-[9px] font-mono mb-2">
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">API · {apiHealthy ? 'online' : 'offline'}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Redis · {redisStatus}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Providers · {providerCount || '—'}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Drift · {dMetric.toFixed(1)}</div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-[9px] font-mono mb-3">
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Consensus · {consensusScore}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Schema · {uiSchema}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Islands · {islands.length}</div>
        <div className="rounded-lg border border-white/5 bg-black/20 p-2 text-gray-400">Zones · {visibleZones}</div>
      </div>
      <div className="mb-3 flex flex-wrap gap-1">
        {weights.map(([k, v]) => (
          <span key={k} className="rounded-md border border-cyan-500/15 bg-cyan-500/5 px-2 py-1 text-[9px] font-mono text-cyan-200/70">
            w_{k}:{v.toFixed(2)}
          </span>
        ))}
      </div>
      <div className="rounded-xl border border-white/5 bg-black/30 p-3 text-[10px] font-mono text-cyan-100/60 leading-relaxed">
        <div className="text-gray-500 mb-1">{IS_DEV ? <>p&amp;w&gt; orbit status --zone atlas</> : 'console> status --zone atlas'}</div>
        <div className="mb-1">focus={selectedNode.toLowerCase().replace(/\s+/g, '-')} :: atlas synced :: schema={uiSchema}</div>
        <div className="mb-2">active_island={activeIslandId ?? 'none'} :: active_session={activeSessionId ?? 'none'}</div>
        <div className="text-gray-500 mb-1">{IS_DEV ? <>p&amp;w&gt; tail tribunal --last</> : 'console> tail --last'}</div>
        <div className="line-clamp-2">{last?.query ? `${last.mode}/${last.ontology} :: ${last.query}` : 'No tribunal sessions yet.'}</div>
        <div className="mt-2 text-[9px] text-gray-500">tip: use the Atlas `Agents &amp; Providers` panel (`coach/ops/compact`) for fast routing and operator hints.</div>
      </div>
    </FloatingPanel>
  )
}

function MemoryMapZone({
  selectedNode,
  profile,
  onProfileChange,
  managed,
}: {
  selectedNode: string
  profile: ColorProfile
  onProfileChange: (p: ColorProfile) => void
  managed?: FloatingPanelManaged
}) {
  const sessionHistory = useAtlasStore((s: AtlasState) => s.sessionHistory)
  const consensusScore = useAtlasStore((s: AtlasState) => s.consensusScore)
  const dMetric = useAtlasStore((s: AtlasState) => s.dMetric)
  const [randomSalt, setRandomSalt] = useState(0)

  const sourceText = useMemo(() => {
    const joined = sessionHistory
      .slice(0, 8)
      .map((s: AtlasState['sessionHistory'][number]) => `${s.query}\n${s.result}`)
      .join('\n')
      .trim()
    return joined || `${selectedNode}\nconsensus:${consensusScore}\ndrift:${dMetric}`
  }, [sessionHistory, selectedNode, consensusScore, dMetric])

  const tiles = useMemo(() => {
    const rows = 6
    const cols = 8
    const chunk = Math.max(12, Math.ceil(sourceText.length / (rows * cols)))
    return Array.from({ length: rows * cols }, (_, i) => {
      const segment = sourceText.slice(i * chunk, (i + 1) * chunk) || `${selectedNode}:${i}`
      const hex = new THREE.Color(colorFromHash(segment, profile, randomSalt + i)).getHexString()
      return `#${hex}`
    })
  }, [sourceText, selectedNode, profile, randomSalt])

  return (
    <FloatingPanel panelId="memory-map" position={managed ? 'w-80' : 'top-32 right-80 w-80'} managed={managed}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Memory Map</h2>
        <span className="text-[9px] font-mono text-cyan-300/60">text → colorfield</span>
      </div>

      <div className="flex flex-wrap gap-1 mb-2">
        {(['tribunal', 'ice', 'ember', 'mono'] as ColorProfile[]).map((p) => (
          <button
            key={p}
            onClick={() => onProfileChange(p)}
            className={`rounded-md px-2 py-1 text-[9px] font-mono border ${
              profile === p ? 'border-cyan-500/30 text-cyan-300' : 'border-white/5 text-gray-600'
            }`}
          >
            {p}
          </button>
        ))}
        <button
          onClick={() => setRandomSalt((v) => v + 17)}
          className="rounded-md px-2 py-1 text-[9px] font-mono border border-amber-500/20 text-amber-300/80"
        >
          randomize
        </button>
      </div>

      <div className="grid grid-cols-8 gap-1 rounded-xl border border-white/5 bg-black/25 p-2">
        {tiles.map((hex, i) => (
          <div
            key={`${hex}-${i}`}
            title={`cell:${i} ${hex}`}
            className="h-6 rounded-sm border border-black/20"
            style={{ background: hex }}
          />
        ))}
      </div>

      <div className="mt-2 rounded-xl border border-white/5 bg-black/20 p-2 text-[9px] font-mono text-gray-400">
        source_bytes={sourceText.length} :: deterministic_hashmap={randomSalt === 0 ? 'on' : 'offset'}
      </div>

      <div className="mt-2 flex flex-wrap gap-1">
        {tiles.slice(0, 6).map((hex) => (
          <span key={`${hex}-legend`} className="rounded-md border border-white/5 bg-black/30 px-2 py-1 text-[9px] font-mono text-gray-300/70">
            {hex}
          </span>
        ))}
      </div>
    </FloatingPanel>
  )
}

function RheaFooter() {
  const [chatOpen, setChatOpen] = useState(false)
  const [chatSent, setChatSent] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [popup, setPopup] = useState<'cookies' | 'personal' | null>(null)

  const handleSend = () => {
    if (!chatInput.trim()) return
    setChatSent(true)
    setChatInput('')
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setPopup(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const links = [
    { label: 'Terms',     href: 'https://github.com/serg-alexv/rhea-project/blob/main/docs/TERMS.md' },
    { label: 'Privacy',   href: 'https://github.com/serg-alexv/rhea-project/blob/main/docs/PRIVACY.md' },
    { label: 'Security',  href: 'https://github.com/serg-alexv/rhea-project/blob/main/docs/SECURITY.md' },
    { label: 'Community', href: 'https://github.com/serg-alexv/rhea-project' },
    { label: 'Docs',      href: 'https://github.com/serg-alexv/rhea-project/tree/main/docs' },
  ]

  const popupContent = {
    cookies: {
      title: 'Manage cookies',
      body: (
        <>
          <p className="mb-2.5">We use essential cookies to make Rhea work.</p>
          <p className="mb-2.5">We do <strong className="text-white/80">not</strong> use tracking, analytics, or advertising cookies.</p>
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-md px-3 py-2 my-2">
            <label className="flex items-center gap-2 text-[11px] cursor-pointer"><input type="checkbox" checked disabled className="accent-cyan-400" /> Essential cookies <em className="text-white/25 text-[10px]">(always on)</em></label>
          </div>
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-md px-3 py-2 my-2">
            <label className="flex items-center gap-2 text-[11px] cursor-pointer"><input type="checkbox" className="accent-cyan-400" /> Analytics cookies <em className="text-white/25 text-[10px]">(off)</em></label>
          </div>
          <p className="text-[10px] text-white/25 mt-3">For details, see our <a href="https://github.com/serg-alexv/rhea-project/blob/main/docs/COOKIES.md" target="_blank" rel="noopener noreferrer" className="text-cyan-400/70 hover:underline">Cookie Policy</a>.</p>
        </>
      ),
    },
    personal: {
      title: 'My personal information',
      body: (
        <>
          <p className="mb-2.5">Under CCPA / GDPR, you have the right to:</p>
          <ul className="list-disc ml-5 mb-2.5 space-y-1">
            <li>Know what personal data we collect</li>
            <li>Request deletion of your data</li>
            <li>Opt out of data sharing</li>
          </ul>
          <p className="mb-2.5">Rhea collects: <strong className="text-white/80">email</strong> (if you sign up) and <strong className="text-white/80">query history</strong> (stored locally).</p>
          <p className="mb-2.5">We do <strong className="text-white/80">not</strong> sell or share personal information with third parties.</p>
          <p className="mb-2.5">To request data deletion, email <a href="mailto:celestica201@gmail.com" className="text-cyan-400/70 hover:underline">celestica201@gmail.com</a>.</p>
          <p className="text-[10px] text-white/25 mt-3">Full policy: <a href="https://github.com/serg-alexv/rhea-project/blob/main/docs/PERSONAL_INFO.md" target="_blank" rel="noopener noreferrer" className="text-cyan-400/70 hover:underline">Personal Information Policy</a>.</p>
        </>
      ),
    },
  }

  return (
    <>
      {/* GitHub-style footer popup */}
      {popup && (
        <div className="fixed inset-0 z-[500]">
          <div className="absolute inset-0 bg-black/55 backdrop-blur-sm" onClick={() => setPopup(null)} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[440px] max-w-[92vw] bg-[#161b22] border border-white/10 rounded-xl shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center px-[18px] py-3.5 border-b border-white/[0.08]">
              <span className="text-[13px] font-semibold text-white/90 font-mono">{popupContent[popup].title}</span>
              <button onClick={() => setPopup(null)} className="text-white/35 hover:text-white text-xl leading-none px-1 transition-colors">×</button>
            </div>
            <div className="px-[18px] py-[18px] text-[12px] leading-relaxed text-white/50 font-mono">
              {popupContent[popup].body}
            </div>
            <div className="px-[18px] py-3 border-t border-white/[0.08] flex justify-end">
              <button onClick={() => setPopup(null)} className="bg-cyan-500 text-black px-[18px] py-1.5 rounded-md text-[11px] font-semibold font-mono hover:opacity-85 transition-opacity">Done</button>
            </div>
          </div>
        </div>
      )}

      {chatOpen && (
        <div className="fixed bottom-16 right-4 z-50 w-[280px] h-[350px] bg-black/90 backdrop-blur-xl border border-white/10 rounded-2xl flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
            <span className="text-[11px] font-mono text-white/60 tracking-wide">Contact Us</span>
            <button onClick={() => { setChatOpen(false); setChatSent(false); setChatInput('') }} className="text-white/30 hover:text-white/60 text-base leading-none">×</button>
          </div>
          <div className="flex-1 flex flex-col gap-2 px-3 py-3 overflow-y-auto">
            <div className="self-start bg-white/[0.08] rounded-xl rounded-tl-sm px-3 py-2 text-[10px] text-white/[0.55] max-w-[90%]">Hey! How can we help?</div>
            <div className="self-start bg-white/[0.08] rounded-xl rounded-tl-sm px-3 py-2 text-[10px] text-white/[0.55] max-w-[90%]">Drop us a message below or email <span className="text-cyan-400/70">celestica201@gmail.com</span></div>
            {chatSent && (
              <div className="self-start bg-white/[0.08] rounded-xl rounded-tl-sm px-3 py-2 text-[10px] text-white/[0.55] max-w-[90%]">Thanks! We&apos;ll get back to you.</div>
            )}
          </div>
          <div className="flex gap-2 px-3 pb-3">
            <input
              className="flex-1 bg-white/[0.06] border border-white/10 rounded-xl px-3 py-1.5 text-[10px] text-white/60 placeholder:text-white/20 outline-none focus:border-white/20 disabled:opacity-40"
              placeholder="Type a message…"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={chatSent}
            />
            <button onClick={handleSend} disabled={chatSent} className="bg-white/10 hover:bg-white/[0.16] disabled:opacity-30 rounded-xl px-3 py-1.5 text-[10px] text-white/50 font-mono transition-colors">Send</button>
          </div>
        </div>
      )}

      <footer className="fixed bottom-0 left-0 right-0 z-40 bg-black/[0.82] backdrop-blur-xl border-t border-white/[0.06] py-3 px-5 text-center">
        <div className="flex flex-wrap justify-center items-center gap-0">
          {links.map((link, i) => (
            <span key={link.label}>
              {i > 0 && <span className="mx-2 text-white/15">·</span>}
              <a href={link.href} target="_blank" rel="noopener noreferrer" className="text-[9px] font-mono text-white/35 hover:text-white/60 transition-colors">{link.label}</a>
            </span>
          ))}
          <span><span className="mx-2 text-white/15">·</span><button onClick={() => setChatOpen((o) => !o)} className="text-[9px] font-mono text-white/35 hover:text-white/60 transition-colors">Contact</button></span>
          <span><span className="mx-2 text-white/15">·</span><button onClick={() => setPopup('cookies')} className="text-[9px] font-mono text-white/35 hover:text-white/60 transition-colors">Manage cookies</button></span>
          <span><span className="mx-2 text-white/15">·</span><button onClick={() => setPopup('personal')} className="text-[9px] font-mono text-white/35 hover:text-white/60 transition-colors">My personal information</button></span>
          <span className="mx-2 text-white/15">·</span>
          <span className="group relative inline-block cursor-default text-[9px] font-mono text-white/[0.22] tracking-wide">
            © 2026 TimeLabs NPO
            <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 bg-black/90 border border-white/10 text-white/60 text-[9px] px-2.5 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-[300]">
              Non-Profit Samurai&apos;s Squad
            </span>
          </span>
        </div>
      </footer>
    </>
  )
}

export default function Home() {
  const [selectedNode, setSelectedNode] = useState('Ruliadic Core')
  const [uiSchema, setUiSchema] = useState<UiSchema>('prime')
  const [showTimeline, setShowTimeline] = useState(true)
  const [showResearch, setShowResearch] = useState(true)
  const [showRex, setShowRex] = useState(true)
  const [showMemory, setShowMemory] = useState(true)
  const [showAgents, setShowAgents] = useState(true)
  const [memoryProfile, setMemoryProfile] = useState<ColorProfile>('tribunal')
  const [dockLayout, setDockLayout] = useState<Record<ManagedPanelId, PanelDockState>>(DEFAULT_DOCK_LAYOUT)
  const [focusedPanel, setFocusedPanel] = useState<ManagedPanelId | null>('council')
  const [uiIdle, setUiIdle] = useState(false)
  const sessionHistory = useAtlasStore((s: AtlasState) => s.sessionHistory)
  const dMetric = useAtlasStore((s: AtlasState) => s.dMetric)
  const consensusScore = useAtlasStore((s: AtlasState) => s.consensusScore)

  const visibleZones =
    (showTimeline ? 1 : 0) +
    (showResearch ? 1 : 0) +
    (showRex ? 1 : 0) +
    (showMemory ? 1 : 0) +
    (showAgents ? 1 : 0)

  const visibleManagedPanels = useMemo<ManagedPanelId[]>(() => ([
    'hud',
    'intent',
    'council',
    ...(showTimeline ? (['timeline'] as ManagedPanelId[]) : []),
    ...(showResearch ? (['research'] as ManagedPanelId[]) : []),
    ...(showRex ? (['pw'] as ManagedPanelId[]) : []),
    ...(showMemory ? (['memory'] as ManagedPanelId[]) : []),
    ...(showAgents ? (['agents'] as ManagedPanelId[]) : []),
  ]), [showTimeline, showResearch, showRex, showMemory, showAgents])

  const movePanelToSlot = (panelId: ManagedPanelId, targetSlot: DockSlot) => {
    setDockLayout((prev) => {
      if (prev[panelId].slot === targetSlot) return prev
      const next = { ...prev }
      const sourceSlot = next[panelId].slot
      const occupant = (Object.keys(next) as ManagedPanelId[]).find((id) => id !== panelId && next[id].slot === targetSlot)
      next[panelId] = { ...next[panelId], slot: targetSlot }
      if (occupant) next[occupant] = { ...next[occupant], slot: sourceSlot }
      return next
    })
  }

  const cyclePanelSlot = (panelId: ManagedPanelId, dir: -1 | 1) => {
    movePanelToSlot(panelId, nextSlot(dockLayout[panelId].slot, dir))
  }

  const togglePanelMin = (panelId: ManagedPanelId) => {
    setDockLayout((prev) => ({
      ...prev,
      [panelId]: { ...prev[panelId], minimized: !prev[panelId].minimized },
    }))
  }

  const markUiActive = () => setUiIdle(false)

  const managedPanelProps = (panelId: ManagedPanelId, title: string): FloatingPanelManaged => ({
    id: panelId,
    title,
    slot: dockLayout[panelId].slot,
    focused: focusedPanel === panelId,
    uiIdle,
    minimized: dockLayout[panelId].minimized,
    panelIndex: DOCK_SLOT_ORDER.indexOf(dockLayout[panelId].slot) + 1,
    onFocus: () => {
      markUiActive()
      setFocusedPanel(panelId)
    },
    onToggleMin: () => {
      markUiActive()
      togglePanelMin(panelId)
    },
    onCycleSlot: (dir) => {
      markUiActive()
      setFocusedPanel(panelId)
      cyclePanelSlot(panelId, dir)
    },
  })

  const primeNodes = useMemo(() => {
    const basis = sessionHistory.slice(0, 3).map((s: AtlasState['sessionHistory'][number]) => `${s.query} ${s.result}`).join(' | ') || selectedNode
    const names = ['Topological Logic', 'Metabolic Flow', 'Quantum Consensus'] as const
    const positions: [number, number, number][] = [
      [-3, 1, 0],
      [3, -1, 0],
      [0, -3, -2],
    ]
    return names.map((name, i) => {
      const text = `${name} :: ${basis}`
      const jitter = ((hashText(text) % 31) - 15) / 100
      const scale = 0.9 + ((hashText(`${text}:scale`) % 45) / 100) + (i === 2 ? consensusScore / 500 : dMetric / 1200)
      return {
        name,
        position: [positions[i][0] + jitter, positions[i][1] - jitter, positions[i][2]] as [number, number, number],
        color: colorFromHash(text, memoryProfile, i),
        semanticText: text,
        semanticValue: scale,
      }
    })
  }, [sessionHistory, selectedNode, dMetric, consensusScore, memoryProfile])

  // Wire real-data sync — runs on mount, polls every 5 s
  useAtlasSync()
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const schema = params.get('schema')
    if (schema === 'mesh' || schema === 'prime') setUiSchema(schema)
  }, [])
  useEffect(() => {
    const url = new URL(window.location.href)
    url.searchParams.set('schema', uiSchema)
    window.history.replaceState({}, '', `${url.pathname}?${url.searchParams.toString()}`)
  }, [uiSchema])
  useEffect(() => {
    let idleTimer: number | undefined
    const ping = () => {
      setUiIdle(false)
      if (idleTimer) window.clearTimeout(idleTimer)
      idleTimer = window.setTimeout(() => setUiIdle(true), 2800)
    }
    const handleKey = (e: KeyboardEvent) => {
      ping()
      const key = e.key.toLowerCase()
      if (e.altKey && /^[1-9]$/.test(key) && focusedPanel) {
        e.preventDefault()
        movePanelToSlot(focusedPanel, DOCK_SLOT_ORDER[Number(key) - 1])
        return
      }
      if (e.altKey && key === '0' && focusedPanel) {
        e.preventDefault()
        togglePanelMin(focusedPanel)
        return
      }
      if (e.altKey && e.key === 'Tab') {
        e.preventDefault()
        const cycleBase: ManagedPanelId[] = visibleManagedPanels.length ? visibleManagedPanels : PANEL_ORDER
        const currentIdx = focusedPanel ? cycleBase.indexOf(focusedPanel) : -1
        const nextIdx = (currentIdx + 1 + cycleBase.length) % cycleBase.length
        setFocusedPanel(cycleBase[nextIdx] ?? null)
        return
      }
      if (key === 'escape') {
        setFocusedPanel(null)
      }
    }
    ping()
    const events: Array<keyof WindowEventMap> = ['pointerdown', 'pointermove', 'wheel', 'touchstart']
    events.forEach((evt) => window.addEventListener(evt, ping, { passive: true }))
    window.addEventListener('keydown', handleKey)
    return () => {
      if (idleTimer) window.clearTimeout(idleTimer)
      events.forEach((evt) => window.removeEventListener(evt, ping))
      window.removeEventListener('keydown', handleKey)
    }
  }, [focusedPanel, visibleManagedPanels, dockLayout])

  const activeView = useAtlasStore((s: AtlasState) => s.activeView)

  return (
    <>
    <main className="h-screen w-full bg-[#030303] overflow-hidden relative pb-10" style={{ paddingTop: '30px' }}>
      {/* ─── HyperionBar is in layout.tsx (layout-level singleton) ─── */}

      {/* ─── Floating HUD panels ─── */}
      <AnimatePresence>
        {/* Top-left: RHEA ATLAS master stats — offset below crossnav */}
        <HudLeft key="hud-left" managed={managedPanelProps('hud', 'Atlas Status')} />

        {/* Bottom-left: Active intent */}
        <FloatingPanel key="intent" position="w-80" managed={managedPanelProps('intent', 'Active Intent')}>
          <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-2 font-bold italic">
            Active Intent
          </div>
          <div className="text-xs font-mono text-cyan-200/60 leading-relaxed capitalize">
            {selectedNode} :: Isomorphic Search Active
          </div>
        </FloatingPanel>

        {/* Top-right: Council Pulse */}
        <FloatingPanel key="council" position="w-64" managed={managedPanelProps('council', IS_DEV ? 'Council Pulse' : 'System Status')}>
          <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3">{IS_DEV ? 'Council Pulse' : 'System Status'}</h2>
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-[10px] font-mono text-gray-400">{IS_DEV ? 'GEMINI 3.1 :: SYNC' : 'SYNC'}</span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-1">
            {(['prime', 'mesh'] as UiSchema[]).map((schema) => (
              <span key={schema} className="group relative">
                <button
                  onClick={() => setUiSchema(schema)}
                  className={`w-full rounded-lg px-2 py-1 text-[9px] font-mono uppercase tracking-widest border ${
                    uiSchema === schema ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-400' : 'border-white/5 bg-black/20 text-gray-600'
                  }`}
                >
                  {schema === 'prime' ? 'Atlas Prime' : 'Atlas Mesh'}
                </button>
                <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 bg-black/90 border border-white/10 text-white/60 text-[9px] px-2.5 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-[300]">
                  Prime: Node clusters · Mesh: Connected graph
                </span>
              </span>
            ))}
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {([
              ['Timeline', showTimeline, setShowTimeline, 'View and rewind your research session history'],
              ['Research', showResearch, setShowResearch, 'Open the research panel to query the Tribunal'],
              [IS_DEV ? 'P&W' : 'Console', showRex, setShowRex, undefined],
              ['Memory', showMemory, setShowMemory, undefined],
              ['Agents', showAgents, setShowAgents, undefined],
            ] as [string, boolean, React.Dispatch<React.SetStateAction<boolean>>, string | undefined][]).map(([label, on, setOn, tip]) => (
              <span key={label} className="group relative">
                <button
                  onClick={() => setOn((v) => !v)}
                  className={`rounded-md px-2 py-1 text-[9px] font-mono border ${on ? 'border-emerald-500/30 text-emerald-300/80' : 'border-white/5 text-gray-600'}`}
                >
                  {label}
                </button>
                {tip && (
                  <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 bg-black/90 border border-white/10 text-white/60 text-[9px] px-2.5 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-[300]">
                    {tip}
                  </span>
                )}
              </span>
            ))}
          </div>
          <div className="mt-2 grid grid-cols-2 gap-1">
            <a
              href={`${API_BASE}/app`}
              className="rounded-lg px-2 py-1 text-[9px] font-mono uppercase tracking-widest border border-white/5 bg-black/20 text-gray-400 hover:text-white/70"
            >
              {IS_DEV ? <>System&apos;s P&amp;W</> : 'Console'}
            </a>
            <a
              href="/semantic-drift.html"
              className="rounded-lg px-2 py-1 text-[9px] font-mono uppercase tracking-widest border border-fuchsia-500/20 bg-fuchsia-500/5 text-fuchsia-300/80 hover:text-fuchsia-200"
              title="Fun-only third UI (no live data linkage yet)"
            >
              Semantic Drift
            </a>
          </div>
          <a href={`/?schema=${uiSchema}`} className="mt-2 block text-[9px] font-mono text-cyan-300/60 hover:text-cyan-300">
            link: /?schema={uiSchema}
          </a>
          <div className="mt-1 text-[8px] font-mono text-gray-500">
            third-ui: /semantic-drift.html (fun-only, no live sync yet)
          </div>
          <div className="mt-1 text-[8px] font-mono text-gray-500">
            dock: Alt+Tab focus · Alt+1..9 snap · Alt+0 min
          </div>
        </FloatingPanel>
      </AnimatePresence>

      {/* ─── Session Timeline — top-centre ─── */}
      {showTimeline && (
        <SessionTimeline
          managed={{
            slotClass: `${DOCK_SLOT_CLASS[dockLayout.timeline.slot]} w-72`,
            focused: focusedPanel === 'timeline',
            uiIdle,
            minimized: dockLayout.timeline.minimized,
            slotIndex: DOCK_SLOT_ORDER.indexOf(dockLayout.timeline.slot) + 1,
            onFocus: () => { markUiActive(); setFocusedPanel('timeline') },
            onToggleMin: () => { markUiActive(); togglePanelMin('timeline') },
            onCycleSlot: (dir) => { markUiActive(); setFocusedPanel('timeline'); cyclePanelSlot('timeline', dir) },
          }}
        />
      )}

      {/* ─── Research Query Panel — bottom-right ─── */}
      {showResearch && (
        <ResearchPanel
          managed={{
            slotClass: `${DOCK_SLOT_CLASS[dockLayout.research.slot]} w-80`,
            focused: focusedPanel === 'research',
            uiIdle,
            minimized: dockLayout.research.minimized,
            slotIndex: DOCK_SLOT_ORDER.indexOf(dockLayout.research.slot) + 1,
            onFocus: () => { markUiActive(); setFocusedPanel('research') },
            onToggleMin: () => { markUiActive(); togglePanelMin('research') },
            onCycleSlot: (dir) => { markUiActive(); setFocusedPanel('research'); cyclePanelSlot('research', dir) },
          }}
        />
      )}
      {showRex && (
        <SystemPWZone selectedNode={selectedNode} uiSchema={uiSchema} visibleZones={visibleZones} managed={managedPanelProps('pw', IS_DEV ? "System's P&W" : 'Console')} />
      )}
      {showMemory && (
        <MemoryMapZone
          selectedNode={selectedNode}
          profile={memoryProfile}
          onProfileChange={setMemoryProfile}
          managed={managedPanelProps('memory', 'Memory Map')}
        />
      )}
      {showAgents && (
        <FloatingPanel position="w-72" managed={managedPanelProps('agents', 'Chronos Agents')}>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Chronos Agents</h2>
            <span className="text-[9px] font-mono text-cyan-300/60">8 specialists</span>
          </div>
          <div className="overflow-y-auto max-h-[60vh]">
            <AgentRoster />
          </div>
        </FloatingPanel>
      )}

      {/* ─── 3-D canvas — full-screen background ─── */}
      {uiSchema === 'mesh' ? (
        <div className="absolute inset-0 z-0 cursor-crosshair"><AtlasScene /></div>
      ) : (
        <div className="absolute inset-0 z-0 cursor-crosshair">
          <Canvas camera={{ position: [0, 0, 10], fov: 40 }}>
            <Suspense fallback={null}>
              <MagneticNebula />
              <Stars radius={100} depth={50} count={7000} factor={4} saturation={0} fade speed={0.5} />
              <ambientLight intensity={0.2} />
              <pointLight position={[10, 10, 10]} intensity={1} color="#00ffff" />
              <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
                {primeNodes.map((node) => (
                  <RuliadicIsland
                    key={node.name}
                    position={node.position}
                    color={node.color}
                    semanticText={node.semanticText}
                    semanticValue={node.semanticValue}
                    radius={Math.max(0.75, Math.min(1.45, node.semanticValue))}
                    onClick={() => setSelectedNode(node.name)}
                  />
                ))}
              </Float>
              <IsomorphismBeam start={new THREE.Vector3(-3, 1, 0)} end={new THREE.Vector3(3, -1, 0)} color="#00ffff" speed={0.5} />
              <OrbitControls enablePan={false} rotateSpeed={0.3} zoomSpeed={0.5} />
              <Environment preset="night" />
            </Suspense>
          </Canvas>
        </div>
      )}
    </main>
    <MnemosyneWhisper />
    <RheaFooter />
    </>
  )
}
