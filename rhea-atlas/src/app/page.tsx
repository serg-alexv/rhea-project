'use client'
import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

const repositories = [
  {
    name: 'rhea-project (monorepo)',
    summary: 'Root of everything: backend, Atlas, mobile, docs, automation, CLI, extensions.',
    focus: 'ORION owns `rhea-atlas` (Next.js) while Rex owns `rhea/` (Tribunal API) and mobile surfaces.',
    tags: ['atlas', 'tribunal', 'mobile', 'cli'],
    detail: 'Contains Atlas UI, `packages/*` helpers, global docs, `rhea-memory` state, extensions, and tools for Build/Deploy. Changes flow through the stage4-release branch.'
  },
  {
    name: 'packages/RheaKit',
    summary: 'PlayUI-native rendering primitives (BioRenderer, NodeEditor, DPIView).',
    focus: 'Allowed inside PlayUI/RheaKit only—SwiftUI helpers for desktop/mobile phenotypes.',
    tags: ['playui', 'rheakit', 'swiftui'],
    detail: 'Provides themed components used by Play and desktop tooling. Keep these classes scoped to `packages/RheaKit`, no separate repo.'
  },
  {
    name: 'packages/rhea-cli',
    summary: 'Python CLI automations (rhea command wrapping tasks).',
    focus: 'Self-serve orchestration entrypoint for agents and devs.',
    tags: ['python', 'cli', 'automation'],
    detail: 'Duty: trigger builds, commit-checks, and hot reload flows from the shell. Owned by the automation team, coordinated with REX.'
  },
  {
    name: 'packages/rhea-memory',
    summary: 'Mission-memory package powering Nexus state sync.',
    focus: 'Stores `docs/state` snapshots and anchors cross-agent persistence.',
    tags: ['memory', 'nexus', 'python'],
    detail: 'Installable via pip. Feeds the Atlas HUD and CLI flows with the canonical story state (CHECK: `docs/state.md`).'
  },
  {
    name: 'extensions/rhea-pluggable',
    summary: 'Manifest + assets for Chrome/extension experiments.',
    focus: 'Pluggable experiences hooking into the Atlas surfaces.',
    tags: ['extension', 'chrome', 'pluggable'],
    detail: 'Add-on UI for live glyphs and CLI insights, waiting for Rex to confirm scope before more work.'
  },
]

const surfaces = [
  { title: 'Tribunal API', detail: 'Python backend, 50+ endpoints, Fly.io public URL (rhea-tribunal.fly.dev). Auth via JWT + OAuth.', metric: '::: Trib Flow' },
  { title: 'Atlas UI', detail: 'Next.js + Framer/Tailwind canvas (port 3000) with hero, cards, language switcher, explanation timeline, and animation pipelines.', metric: '::: UI Flow' },
  { title: 'Play UI / RheaKit', detail: 'Rust/Swift-run creative toolkit, BioRenderer, NodeEditor, DPIView macros for physical surfaces.', metric: '::: Play Flow' },
  { title: 'Mobile (RheaApp)', detail: 'iOS SwiftUI app build 1.0.26 in TestFlight with NE + Hotspot entitlements staged.', metric: '::: Mobile Flow' },
]

const stats = [
  { label: 'Assets hosted', value: '11 Atlas pages + 54 Tribunal endpoints' },
  { label: 'Deploy', value: 'Fly.io rhea-tribunal with JWT/OAuth' },
  { label: 'Graphics', value: 'Gemini-powered render cards + motion' },
]

const languages = ['English', 'Русский', 'Français', 'Deutsch']

export default function HomePage() {
  const [expandedRepo, setExpandedRepo] = useState<string | null>(repositories[0].name)
  const [selectedLang, setSelectedLang] = useState(languages[0])
  const heroToneClass = useMemo(() => {
    if (selectedLang === 'Русский') return 'text-amber-200'
    if (selectedLang === 'Français') return 'text-violet-200'
    if (selectedLang === 'Deutsch') return 'text-indigo-200'
    return 'text-cyan-200'
  }, [selectedLang])

  return (
    <div className="min-h-screen bg-[#07070f] text-white">
      <div className="relative isolate overflow-hidden" style={{ background: 'radial-gradient(circle at top, rgba(61, 255, 255, 0.2), transparent 55%), radial-gradient(circle at 20% 80%, rgba(255, 77, 166, 0.15), transparent 45%), #07070f' }}>
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="mx-auto max-w-6xl px-6 py-16"
        >
          <p className="text-sm uppercase tracking-[0.3em] text-cyan-300/80">RHEA TRIBUNAL · Fly.io Rebuild</p>
          <h1 className="mt-3 text-4xl font-semibold leading-tight text-white sm:text-5xl">Rebuild `rhea-tribunal.fly.dev` from the UI frontier.</h1>
          <p className="mt-4 max-w-3xl text-lg text-slate-200">
            Hero animation, explanation cards, languages switcher, and Gemini-generated graphics converge in a single Atlas surface.
            The mission: make every repo and surface readable, animated, and ready for the public fly deployment.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3 text-sm">
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="rounded-full bg-white/10 px-4 py-2 text-xs uppercase tracking-[0.4em] text-slate-200"
            >
              Language ↺
            </motion.div>
            <div className="flex flex-wrap gap-2">
              {languages.map((lang) => (
                <button
                  key={lang}
                  type="button"
                  onClick={() => setSelectedLang(lang)}
                  className={`rounded-full px-4 py-1 text-xs font-semibold tracking-[0.2em] transition ${selectedLang === lang ? 'bg-white text-black' : 'bg-white/10 text-slate-200 hover:bg-white/20'}`}
                >
                  {lang}
                </button>
              ))}
            </div>
            <span className="text-xs text-slate-400">Active: <span className={`font-semibold ${heroToneClass}`}>{selectedLang}</span></span>
          </div>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mt-12 grid gap-6 sm:grid-cols-3"
          >
            {stats.map((stat) => (
              <div key={stat.label} className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{stat.label}</p>
                <p className="mt-2 text-lg font-semibold text-white">{stat.value}</p>
              </div>
            ))}
          </motion.div>
        </motion.div>
        <div className="pointer-events-none absolute inset-0">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 48, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-16 rounded-[32px] border border-white/5"
          />
        </div>
      </div>

      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-500">Repository overview</p>
            <h2 className="text-3xl font-semibold text-white">Every Git surface, aligned.</h2>
          </div>
          <p className="max-w-lg text-sm text-slate-400">
            Clear purpose statements show what each repo owns. Visual cues keep the attention on outcomes, not busywork.
          </p>
        </div>
        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          {repositories.map((repo) => (
            <motion.article
              key={repo.name}
              layout
              whileHover={{ translateY: -6 }}
              className="group relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/5 to-black/40 p-6 shadow-lg shadow-cyan-500/5"
            >
              <div className="flex justify-between">
                <h3 className="text-xl font-semibold text-white">{repo.name}</h3>
                <span className="text-xs uppercase tracking-[0.4em] text-slate-400">{repo.tags.includes('atlas') ? 'Atlas' : 'Repo'}</span>
              </div>
              <p className="mt-2 text-sm text-slate-300">{repo.summary}</p>
              <p className="mt-1 text-xs uppercase tracking-[0.3em] text-slate-500">{repo.focus}</p>
              <button
                type="button"
                onClick={() => setExpandedRepo(expandedRepo === repo.name ? null : repo.name)}
                className="mt-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.4em] text-cyan-200 outline-none"
              >
                {expandedRepo === repo.name ? 'Hide details' : 'Reveal details'}
                <motion.span animate={{ rotate: expandedRepo === repo.name ? 180 : 0 }}>⌄</motion.span>
              </button>
              <AnimatePresence>
                {expandedRepo === repo.name && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="mt-4 rounded-2xl border border-white/5 bg-black/40 p-4 text-sm text-slate-300"
                  >
                    {repo.detail}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-500">Fly.io rebuild timeline</p>
            <h2 className="text-3xl font-semibold text-white">Animated surface, hiddable cards, Gemini art.</h2>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.3em] text-slate-200">
            Graphics by Gemini · Motion by Framer
          </div>
        </div>
        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          {surfaces.map((surface) => (
            <motion.div
              key={surface.title}
              whileHover={{ translateY: -4 }}
              className="rounded-3xl border border-white/10 bg-black/40 p-6 shadow-2xl shadow-indigo-900/20"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-semibold text-white">{surface.title}</h3>
                <span className="text-xs font-mono uppercase tracking-[0.4em] text-slate-400">{surface.metric}</span>
              </div>
              <p className="mt-3 text-sm text-slate-300">{surface.detail}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid gap-6 lg:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-600/20 to-indigo-900/30 p-8 shadow-2xl shadow-cyan-900/30"
          >
            <p className="text-xs uppercase tracking-[0.4em] text-cyan-200">Explain</p>
            <h3 className="mt-2 text-3xl font-semibold text-white">Gemini-powered explain cards</h3>
            <p className="mt-3 text-sm text-slate-100">
              Hidden cards drop down to tell the story for each repo and surface. They align with the Fly.io mission: authentication, multi-model consensus, visual narrative.
            </p>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Focus</p>
                <p className="text-sm text-white">Make the fly page explain the gits without distraction.</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Motion</p>
                <p className="text-sm text-white">Use Framer to echo the consensus pulses—cards breathe, gradients wave.</p>
              </div>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="rounded-3xl border border-white/10 bg-black/30 p-8"
          >
            <p className="text-xs uppercase tracking-[0.4em] text-slate-500">Language signal</p>
            <h3 className="mt-2 text-3xl font-semibold text-white">Switch at will</h3>
            <p className="mt-3 text-sm text-slate-200">
              The Atlas landing copy synchronizes with the `selectedLang` state. Each press triggers Gemini motion to refresh gradients and hero tone.
            </p>
            <div className="mt-5 grid grid-cols-2 gap-3 text-xs uppercase">
              {languages.map((lang) => (
                <span key={lang} className={`rounded-2xl border border-white/5 px-3 py-2 text-center ${selectedLang === lang ? 'bg-white text-black' : 'bg-white/5 text-slate-300'}`}>
                  {lang}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      <footer className="border-t border-white/10 bg-black/70 px-6 py-10">
        <div className="mx-auto max-w-6xl text-sm text-slate-400">
          <p>Rebuilding `rhea-tribunal.fly.dev` means the Atlas surface must narrate every repo, surface, and metric. This page does that with animated explanation cards, hidden details, and a languages switcher that mirrors the Fly mission.</p>
          <p className="mt-3">Ask Gemini for new graphics, call the `rhea-memory` pipeline to keep state fresh, and let Rex know when the next deploy is ready. All surfaces stay inside `rhea-project`, no scatter.</p>
        </div>
      </footer>
    </div>
  )
}
