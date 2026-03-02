'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

const CC_API = process.env.NEXT_PUBLIC_CC_API ?? 'http://localhost:8400'

// ─── Decision Cards Data ─────────────────────────────────────────────

interface Decision {
  id: string
  title: string
  question: string
  youDecide: string[]
  saasDecides: string
  impact: string
  configKey: string
  current?: string
  category: 'sovereignty' | 'models' | 'economics' | 'security'
}

const DECISIONS: Decision[] = [
  {
    id: 'admin',
    title: 'Admin Access',
    question: 'Who controls admin privileges?',
    youDecide: ['Set ADMIN_EMAILS env var', 'Revoke via infrastructure', 'No vendor backdoor'],
    saasDecides: 'Vendor dashboard. Vendor support can access your data. You can be locked out.',
    impact: 'Full sovereignty over who sees and controls your instance.',
    configKey: 'ADMIN_EMAILS',
    category: 'sovereignty',
  },
  {
    id: 'models',
    title: 'Model Selection',
    question: 'Which AI models run your queries?',
    youDecide: ['31 models across 9 providers', 'Mix cheap + premium per query', 'Add new providers anytime'],
    saasDecides: '"We use GPT-4." No choice. Their margin, your bill.',
    impact: 'Optimize cost/quality per query. Tribunal consensus across diverse models.',
    configKey: 'rhea_bridge tiers',
    category: 'models',
  },
  {
    id: 'data',
    title: 'Data Location',
    question: 'Where does your data live?',
    youDecide: ['Local SQLite on your machine', 'Your own server / VPS', 'No third-party data access'],
    saasDecides: '"Your data is in our cloud." Their jurisdiction, their breach risk.',
    impact: 'Zero egress fees. Full GDPR/HIPAA control. Survives vendor shutdown.',
    configKey: 'data/rhea.db',
    category: 'sovereignty',
  },
  {
    id: 'keys',
    title: 'API Keys',
    question: 'Who pays for model inference?',
    youDecide: ['BYOK — your keys, direct provider billing', 'Use cloud bridge with credits', 'Mix both per query'],
    saasDecides: '"$29/mo flat." Hidden markup on every API call.',
    impact: 'BYOK: $0 platform fee. Cloud bridge: transparent per-query credits.',
    configKey: '.env provider keys',
    category: 'economics',
  },
  {
    id: 'rate-limits',
    title: 'Rate Limits',
    question: 'How many queries can you run?',
    youDecide: ['Set TRIBUNAL_RATE_LIMIT yourself', 'Self-hosted: unlimited', 'Cloud: buy credits as needed'],
    saasDecides: '"Pro plan: 100/min. Enterprise: call sales."',
    impact: 'No artificial throttling. Your infra, your throughput.',
    configKey: 'TRIBUNAL_RATE_LIMIT',
    category: 'economics',
  },
  {
    id: 'auth',
    title: 'Authentication',
    question: 'How do users sign in?',
    youDecide: ['Email/password', 'Google OAuth', 'Microsoft OAuth', 'Apple Sign In', 'API keys'],
    saasDecides: '"Sign in with us." One option. Vendor lock-in.',
    impact: 'Your users, your auth. No vendor in the identity chain.',
    configKey: 'OAuth providers in .env',
    category: 'security',
  },
  {
    id: 'pricing',
    title: 'Pricing Model',
    question: 'How do you charge your users?',
    youDecide: ['Credits (pay-per-query)', 'Subscriptions via Stripe', 'BTC via BTCPay', 'Free for your team'],
    saasDecides: '"$29/mo or nothing." One-size-fits-all.',
    impact: 'You set the economics. Resell with markup. Or run free internally.',
    configKey: 'billing.py PLANS + CREDIT_COSTS',
    category: 'economics',
  },
  {
    id: 'ontology',
    title: 'Knowledge Domains',
    question: 'What expertise shapes the analysis?',
    youDecide: ['Pharmacology, Biochemistry, Logic, Topology, Systems Biology', 'Add custom ontologies', 'Switch per query'],
    saasDecides: '"General purpose AI." No domain specialization.',
    impact: 'Domain-specific consensus. Your ontologies reflect your expertise.',
    configKey: 'ONTOLOGY_PROMPTS',
    category: 'models',
  },
  {
    id: 'workflows',
    title: 'Automation',
    question: 'How do you orchestrate multi-step tasks?',
    youDecide: ['Visual DAG editor', '8 node types (tribunal, LLM, HTTP, transform...)', 'Custom pipelines'],
    saasDecides: '"Use our workflow." No customization. Their templates.',
    impact: 'Build exactly the automation your process needs. No template tax.',
    configKey: '/cc/automation',
    category: 'models',
  },
]

const CATEGORY_COLORS: Record<string, { border: string; bg: string; text: string; label: string }> = {
  sovereignty: { border: 'border-emerald-500/30', bg: 'bg-emerald-500/5', text: 'text-emerald-400', label: 'Sovereignty' },
  models:      { border: 'border-cyan-500/30',    bg: 'bg-cyan-500/5',    text: 'text-cyan-400',    label: 'Models & Intelligence' },
  economics:   { border: 'border-amber-500/30',   bg: 'bg-amber-500/5',   text: 'text-amber-400',   label: 'Economics' },
  security:    { border: 'border-violet-500/30',   bg: 'bg-violet-500/5',  text: 'text-violet-400',  label: 'Security & Identity' },
}

// ─── Components ──────────────────────────────────────────────────────

function DecisionCard({ d, index }: { d: Decision; index: number }) {
  const [expanded, setExpanded] = useState(false)
  const cat = CATEGORY_COLORS[d.category]

  return (
    <div
      className={`group rounded-xl border ${cat.border} ${cat.bg} p-4 cursor-pointer transition-all duration-200 hover:border-opacity-60`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[9px] font-bold uppercase tracking-widest ${cat.text}`}>
              {cat.label}
            </span>
          </div>
          <h3 className="text-sm font-semibold text-white/90">{d.title}</h3>
          <p className="text-xs text-white/50 mt-1">{d.question}</p>
        </div>
        <div className={`text-xs shrink-0 transition-transform duration-200 text-white/30 ${expanded ? 'rotate-180' : ''}`}>
          &#9662;
        </div>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3 text-xs">
          {/* You Decide */}
          <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
            <div className="text-[9px] font-bold uppercase tracking-widest text-emerald-400 mb-2">
              You Decide
            </div>
            <ul className="space-y-1">
              {d.youDecide.map((item, i) => (
                <li key={i} className="text-white/70 flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5 shrink-0">&#10003;</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* SaaS Would Decide */}
          <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
            <div className="text-[9px] font-bold uppercase tracking-widest text-red-400 mb-2">
              SaaS Decides For You
            </div>
            <p className="text-white/50">{d.saasDecides}</p>
          </div>

          {/* Impact */}
          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
            <div className="text-[9px] font-bold uppercase tracking-widest text-white/40 mb-1">
              Impact
            </div>
            <p className="text-white/60">{d.impact}</p>
            <div className="mt-2 font-mono text-[10px] text-white/30">
              config: {d.configKey}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function CreditCalculator() {
  const [k, setK] = useState(3)
  const [tier, setTier] = useState<'cheap' | 'mid' | 'premium' | 'max'>('cheap')
  const [operation, setOperation] = useState<'tribunal' | 'ice' | 'sceptic' | 'dialog'>('tribunal')

  const COSTS: Record<string, number> = { tribunal: 3, ice: 10, sceptic: 5, dialog: 1 }
  const TIER_MULT: Record<string, number> = { cheap: 1, mid: 2, premium: 4, max: 8 }
  const kExtra = ['tribunal', 'ice'].includes(operation) ? Math.max(0, k - 2) : 0
  const cost = Math.max(1, COSTS[operation] * TIER_MULT[tier] + kExtra)
  const queriesFor100 = Math.floor(100 / cost)

  return (
    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
      <h3 className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-3">
        Credit Calculator
      </h3>
      <div className="grid grid-cols-3 gap-3 text-xs mb-4">
        <div>
          <label className="text-white/40 text-[10px] block mb-1">Operation</label>
          <select
            value={operation}
            onChange={e => setOperation(e.target.value as typeof operation)}
            className="w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-white/80 text-xs"
          >
            <option value="tribunal">Tribunal (consensus)</option>
            <option value="ice">ICE (deep)</option>
            <option value="sceptic">Sceptic</option>
            <option value="dialog">Dialog (chat)</option>
          </select>
        </div>
        <div>
          <label className="text-white/40 text-[10px] block mb-1">Tier</label>
          <select
            value={tier}
            onChange={e => setTier(e.target.value as typeof tier)}
            className="w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-white/80 text-xs"
          >
            <option value="cheap">Cheap (Groq, Cerebras)</option>
            <option value="mid">Mid (GPT-4o-mini)</option>
            <option value="premium">Premium (Claude, GPT-4o)</option>
            <option value="max">Max (GPT-4, Opus)</option>
          </select>
        </div>
        <div>
          <label className="text-white/40 text-[10px] block mb-1">Models (k={k})</label>
          <input
            type="range"
            min={2}
            max={10}
            value={k}
            onChange={e => setK(Number(e.target.value))}
            className="w-full accent-cyan-400"
          />
        </div>
      </div>
      <div className="flex items-end justify-between border-t border-white/5 pt-3">
        <div>
          <span className="text-2xl font-bold text-white">{cost}</span>
          <span className="text-white/40 text-xs ml-1">credits / query</span>
        </div>
        <div className="text-right text-xs text-white/40">
          100 signup credits = <span className="text-emerald-400 font-medium">{queriesFor100} queries</span>
        </div>
      </div>
    </div>
  )
}

// ─── Page ────────────────────────────────────────────────────────────

export default function DecisionsPage() {
  const [profile, setProfile] = useState<{ email: string; plan: string; role: string } | null>(null)
  const [filter, setFilter] = useState<string | null>(null)

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('rhea_token') : null
    if (!token) return
    fetch(`${CC_API}/auth/profile`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => d && setProfile(d))
      .catch(() => {})
  }, [])

  const filtered = filter ? DECISIONS.filter(d => d.category === filter) : DECISIONS
  const categories = Object.entries(CATEGORY_COLORS)

  return (
    <div className="h-screen flex flex-col bg-[#0a0b0f] text-white overflow-hidden">
      {/* Header */}
      <div className="border-b border-white/[0.06] px-4 py-3 flex items-center gap-3 shrink-0">
        <Link href="/cc" className="text-white/40 hover:text-white/60 text-xs transition-colors">
          &larr; Command Centre
        </Link>
        <div className="h-3 w-px bg-white/10" />
        <h1 className="text-xs font-bold uppercase tracking-widest text-white/80">
          Decisions Map
        </h1>
        {profile && (
          <span className="ml-auto text-[10px] text-white/30 font-mono">
            {profile.email} &middot; {profile.role} &middot; {profile.plan}
          </span>
        )}
      </div>

      {/* Principle banner */}
      <div className="border-b border-emerald-500/10 bg-emerald-500/[0.03] px-6 py-4 shrink-0">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-sm text-emerald-300/90 font-medium leading-relaxed">
            The infrastructure owner controls who&apos;s admin, not the application.
          </p>
          <p className="text-xs text-white/40 mt-1">
            Every decision below is yours. SaaS takes them from you. Here&apos;s what you keep.
          </p>
        </div>
      </div>

      {/* Category filters */}
      <div className="border-b border-white/[0.06] px-4 py-2 flex items-center gap-2 shrink-0">
        <button
          onClick={() => setFilter(null)}
          className={`px-3 py-1 rounded-full text-[10px] font-medium transition-colors ${
            !filter ? 'bg-white/10 text-white/80' : 'text-white/40 hover:text-white/60'
          }`}
        >
          All ({DECISIONS.length})
        </button>
        {categories.map(([key, val]) => (
          <button
            key={key}
            onClick={() => setFilter(filter === key ? null : key)}
            className={`px-3 py-1 rounded-full text-[10px] font-medium transition-colors ${
              filter === key ? `${val.bg} ${val.text} border ${val.border}` : 'text-white/40 hover:text-white/60'
            }`}
          >
            {val.label} ({DECISIONS.filter(d => d.category === key).length})
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Score banner */}
          <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-white/40 mb-1">
                Your Sovereignty Score
              </div>
              <div className="text-3xl font-bold text-emerald-400">
                {DECISIONS.length}/{DECISIONS.length}
              </div>
              <div className="text-xs text-white/40 mt-1">
                decisions you control
              </div>
            </div>
            <div className="text-right text-xs text-white/30 space-y-1">
              <div className="flex items-center gap-2 justify-end">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Self-hosted: all {DECISIONS.length} decisions yours
              </div>
              <div className="flex items-center gap-2 justify-end">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                Cloud bridge: {DECISIONS.length - 1} yours (we host infra)
              </div>
              <div className="flex items-center gap-2 justify-end">
                <span className="w-2 h-2 rounded-full bg-red-400" />
                Typical SaaS: 0-2 yours
              </div>
            </div>
          </div>

          {/* Credit calculator */}
          <CreditCalculator />

          {/* Decision cards */}
          <div className="space-y-3">
            {filtered.map((d, i) => (
              <DecisionCard key={d.id} d={d} index={i} />
            ))}
          </div>

          {/* BYOK callout */}
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5 text-center">
            <h3 className="text-sm font-semibold text-amber-300 mb-2">
              Bring Your Own Key = $0 Platform Fee
            </h3>
            <p className="text-xs text-white/50 max-w-md mx-auto leading-relaxed">
              Plug your API keys from OpenAI, Anthropic, Google, Groq, Cerebras, Mistral,
              Together, or Fireworks. Rhea routes to your keys — you pay providers directly.
              No markup. No middleman. The infrastructure serves you.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
