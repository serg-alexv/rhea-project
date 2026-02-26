'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { animate, motion, useMotionValue, AnimatePresence } from 'framer-motion';
import { useAtlasStore, AtlasState, SessionEntry } from '@/store/useAtlasStore';
import { useWhisperStore } from '@/store/useWhisperStore';
import { TRIBUNAL_API } from '@/lib/config';

function PaidToast({ message, visible }: { message: string; visible: boolean }) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="paid-toast"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.22 }}
          className="fixed bottom-5 right-5 z-[200] rounded-lg border border-amber-500/60 bg-black/80 backdrop-blur px-4 py-2 text-[11px] font-mono text-amber-400 pointer-events-none"
          style={{ boxShadow: '0 0 12px rgba(251,191,36,0.12)' }}
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

const ONTOLOGIES = [
  'General',
  'Pharmacology',
  'Biochemistry',
  'Logic',
  'Topology',
  'Systems Biology',
] as const;
const ONTOLOGY_API_VALUE: Record<typeof ONTOLOGIES[number], string> = {
  General: 'general',
  Pharmacology: 'pharmacology',
  Biochemistry: 'biochemistry',
  Logic: 'logic',
  Topology: 'topology',
  'Systems Biology': 'systems_biology',
};

type Ontology = typeof ONTOLOGIES[number];
type Mode = 'tribunal' | 'sceptic' | 'ice';

// ── Paid-action toast messages ────────────────────────────────────────────────
const PAID_MSGS: Record<Mode, string> = {
  tribunal: '⚡ Tribunal query uses AI credits (~$0.002)',
  sceptic:  '⚡ Sceptic analysis uses AI credits (~$0.004)',
  ice:      '⚡ Deep analysis uses AI credits (~$0.01)',
};

const MODE_LABELS: Record<Mode, string> = {
  tribunal: 'Tribunal',
  sceptic:  'Sceptic',
  ice:      'ICE',
};

const MODE_ENDPOINTS: Record<Mode, string> = {
  tribunal: `${TRIBUNAL_API}/tribunal`,
  sceptic:  `${TRIBUNAL_API}/tribunal/sceptic`,
  ice:      `${TRIBUNAL_API}/tribunal/ice`,
};

function uid(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

let PANEL_Z = 60

type ManagedResearchPanel = {
  slotClass: string;
  focused: boolean;
  uiIdle: boolean;
  minimized: boolean;
  slotIndex: number;
  onFocus: () => void;
  onToggleMin: () => void;
  onCycleSlot: (dir: -1 | 1) => void;
};

export default function ResearchPanel({ managed }: { managed?: ManagedResearchPanel } = {}) {
  const [query, setQuery] = useState('');
  const [ontology, setOntology] = useState<Ontology>('General');
  const [mode, setMode] = useState<Mode>('tribunal');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [isWaking, setIsWaking] = useState(false);
  const [error, setError] = useState('');
  const [toastVisible, setToastVisible] = useState(false);
  const [toastMsg, setToastMsg] = useState('');
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((msg: string) => {
    setToastMsg(msg);
    setToastVisible(true);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToastVisible(false), 4000);
  }, []);

  useEffect(() => () => { if (toastTimer.current) clearTimeout(toastTimer.current); }, []);

  const addSessionEntry = useAtlasStore((s: AtlasState) => s.addSessionEntry);
  const recordWhisperError = useWhisperStore((s) => s.recordError);
  const recordWhisperModeSwitch = useWhisperStore((s) => s.recordModeSwitch);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const [zIndex, setZIndex] = useState(++PANEL_Z);
  const [localMinimized, setLocalMinimized] = useState(false);
  const isMinimized = managed?.minimized ?? localMinimized;
  const toggleMinimized = () => {
    if (managed) managed.onToggleMin();
    else setLocalMinimized((v) => !v);
  };
  const panelTone = managed
    ? managed.focused
      ? 'border-cyan-500/20 bg-black/55 opacity-100'
      : managed.uiIdle
        ? 'border-white/5 bg-black/20 opacity-60'
        : 'border-white/5 bg-black/30 opacity-80'
    : 'border-white/5 bg-white/5 opacity-100';

  const handleSubmit = useCallback(async () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    // Paid-action notification
    showToast(PAID_MSGS[mode] ?? '⚡ This action uses AI credits');

    setLoading(true);
    const wakeTimer = setTimeout(() => setIsWaking(true), 1500);
    setError('');
    setResult('');

    try {
      // Keep backend ontology lens in sync with UI selector (best effort).
      try {
        await fetch(`${TRIBUNAL_API}/ontology/switch`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'dev-bypass',
          },
          body: JSON.stringify({ ontology: ONTOLOGY_API_VALUE[ontology] }),
        });
      } catch {
        // non-fatal
      }

      const payload =
        mode === 'ice'
          ? { prompt: trimmed, k: 5, rounds: 2, tier: 'cheap' }
          : mode === 'sceptic'
            ? { prompt: trimmed, k: 5, tier: 'cheap' }
            : { prompt: trimmed, k: 5, tier: 'cheap', mode: 'local' };

      const res = await fetch(MODE_ENDPOINTS[mode], {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'dev-bypass',
        },
        body: JSON.stringify(payload),
      });

      let text = '';
      if (res.ok) {
        const data = await res.json().catch(() => null);
        if (data) {
          // Try common response field names
          text =
            data.consensus ??
            data.result ??
            data.response ??
            data.answer ??
            data.text ??
            JSON.stringify(data, null, 2);
        } else {
          text = await res.text();
        }
      } else {
        text = `HTTP ${res.status}: ${res.statusText}`;
        setError(text);
        recordWhisperError();
      }

      clearTimeout(wakeTimer);
      setIsWaking(false);
      setResult(text);

      const entry: SessionEntry = {
        id: uid(),
        query: trimmed,
        result: text,
        mode,
        ontology,
        timestamp: Date.now(),
      };
      addSessionEntry(entry);
    } catch (err) {
      clearTimeout(wakeTimer);
      setIsWaking(false);
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Network error: ${msg}`);
      setResult('');
      recordWhisperError();
    } finally {
      setLoading(false);
    }
  }, [query, ontology, mode, loading, addSessionEntry, showToast, recordWhisperError]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit();
    }
  };

  return (
    <>
    <motion.div
      drag={managed ? false : true}
      dragMomentum={managed ? undefined : false}
      dragConstraints={managed ? undefined : { left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={managed ? undefined : 0.1}
      style={managed ? { zIndex: managed.focused ? 120 : 80 } : { x, y, zIndex }}
      onPointerDown={() => {
        if (managed) managed.onFocus();
        else setZIndex(++PANEL_Z);
      }}
      onFocusCapture={() => {
        if (managed) managed.onFocus();
        else setZIndex(++PANEL_Z);
      }}
      onDragStart={managed ? undefined : () => setZIndex(++PANEL_Z)}
      onDragEnd={managed ? undefined : () => {
        const step = 24;
        animate(x, Math.round(x.get() / step) * step, { type: 'spring', stiffness: 500, damping: 34 });
        animate(y, Math.round(y.get() / step) * step, { type: 'spring', stiffness: 500, damping: 34 });
      }}
      whileHover={managed ? { scale: 1 } : { scale: 1.01 }}
      whileDrag={managed ? undefined : { scale: 1.01 }}
      tabIndex={0}
      className={`${managed ? `absolute ${managed.slotClass}` : 'absolute bottom-8 right-8'} z-20 w-80 p-6 rounded-3xl border ${panelTone} backdrop-blur-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] ${managed ? 'outline-none transition-opacity duration-200' : 'cursor-grab active:cursor-grabbing'}`}
    >
      {/* Header */}
      <div className="mb-4 flex items-center justify-between gap-2">
        <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
          Research Query
        </h2>
        <div className="flex items-center gap-1">
          {managed && (
            <>
              <button
                type="button"
                onPointerDown={(e) => e.stopPropagation()}
                onClick={() => managed.onCycleSlot(-1)}
                className="h-5 w-5 rounded-md border border-white/10 bg-black/30 text-[10px] font-mono text-gray-300/70"
                title="Previous slot"
                aria-label="Previous slot"
              >
                ←
              </button>
              <span className="text-[8px] font-mono text-cyan-300/60">#{managed.slotIndex}</span>
            </>
          )}
          <button
            type="button"
            onPointerDown={(e) => e.stopPropagation()}
            onClick={toggleMinimized}
            className="rounded-md border border-white/10 bg-black/30 px-1.5 py-0.5 text-[8px] font-mono uppercase tracking-widest text-gray-300/70"
            aria-expanded={!isMinimized}
            title={isMinimized ? 'Restore' : 'Minimize'}
          >
            {isMinimized ? 'Restore' : 'Min'}
          </button>
          {managed && (
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={() => managed.onCycleSlot(1)}
              className="h-5 w-5 rounded-md border border-white/10 bg-black/30 text-[10px] font-mono text-gray-300/70"
              title="Next slot"
              aria-label="Next slot"
            >
              →
            </button>
          )}
        </div>
      </div>

      {isMinimized ? (
        <div className="text-[9px] font-mono text-gray-500">Minimized · Alt+0 restores focused panel</div>
      ) : (
        <>
          {/* Query textarea */}
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter query… (⌘↵ to submit)"
            rows={3}
            className="
              w-full resize-none rounded-xl border border-white/5 bg-black/30
              px-3 py-2 text-[10px] font-mono text-cyan-200/70 placeholder-gray-600
              focus:outline-none focus:border-cyan-500/30 focus:ring-0
              leading-relaxed
            "
          />

          {/* Ontology selector */}
          <div className="mt-3">
            <label className="text-[9px] uppercase tracking-widest text-gray-600 block mb-1">
              Ontology
            </label>
            <select
              value={ontology}
              onChange={(e) => {
                const next = e.target.value as Ontology;
                setOntology(next);
                recordWhisperModeSwitch();
              }}
              className="
                w-full rounded-xl border border-white/5 bg-black/30
                px-3 py-1.5 text-[10px] font-mono text-cyan-200/70
                focus:outline-none focus:border-cyan-500/30
                appearance-none cursor-pointer
              "
            >
              {ONTOLOGIES.map((o) => (
                <option key={o} value={o} className="bg-[#0a0a0a] text-cyan-200">
                  {o}
                </option>
              ))}
            </select>
          </div>

          {/* Mode toggle */}
          <div className="mt-3">
            <label className="text-[9px] uppercase tracking-widest text-gray-600 block mb-1">
              Mode
            </label>
            <div className="flex gap-1">
              {(Object.keys(MODE_LABELS) as Mode[]).map((m) => (
                <button
                  key={m}
                  onClick={() => {
                    if (m !== mode) {
                      setMode(m);
                      recordWhisperModeSwitch();
                      return;
                    }
                    setMode(m);
                  }}
                  className={`
                    flex-1 rounded-lg px-2 py-1 text-[9px] font-mono uppercase tracking-widest
                    border transition-all duration-150
                    ${mode === m
                      ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-400'
                      : 'border-white/5 bg-black/20 text-gray-600 hover:text-gray-400 hover:border-white/10'
                    }
                  `}
                >
                  {MODE_LABELS[m]}
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading || !query.trim()}
            className="
              mt-4 w-full rounded-xl border border-cyan-500/20 bg-cyan-500/5
              px-4 py-2 text-[10px] font-mono uppercase tracking-widest text-cyan-400
              hover:bg-cyan-500/10 hover:border-cyan-500/40
              disabled:opacity-30 disabled:cursor-not-allowed
              transition-all duration-150
            "
          >
            {loading ? (isWaking ? 'Waking backend (~3s)…' : 'Querying…') : 'submit'}
          </button>

          {/* Result / error area */}
          {(result || error) && (
            <div className="mt-4">
              <div className="text-[9px] uppercase tracking-widest text-gray-600 mb-1">
                {error ? 'Error' : 'Consensus'}
              </div>
              <div
                className={`
                  rounded-xl border border-white/5 bg-black/30 p-3
                  text-[10px] font-mono leading-relaxed max-h-40 overflow-y-auto
                  ${error ? 'text-red-400/70' : 'text-cyan-200/60'}
                `}
                style={{ scrollbarWidth: 'none' }}
              >
                {error || result}
              </div>
            </div>
          )}
        </>
      )}
    </motion.div>

    {/* Paid-action toast — rendered outside the draggable panel so it stays fixed */}
    <PaidToast message={toastMsg} visible={toastVisible} />
    </>
  );
}
