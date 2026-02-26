'use client';

import { useState } from 'react';
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useReducedMotion,
  useTransform,
} from 'framer-motion';
import { useAtlasStore, AtlasState, SessionEntry } from '@/store/useAtlasStore';

function elapsed(ts: number): string {
  const delta = Math.floor((Date.now() - ts) / 1000);
  if (delta < 60) return `${delta}s`;
  if (delta < 3600) return `${Math.floor(delta / 60)}m`;
  return `${Math.floor(delta / 3600)}h`;
}

function truncate(s: string, n = 40): string {
  return s.length <= n ? s : s.slice(0, n - 1) + '…';
}

const MODE_COLOR: Record<string, string> = {
  tribunal: 'text-cyan-400',
  sceptic:  'text-amber-400',
  ice:      'text-violet-400',
};

let PANEL_Z = 70

type ManagedTimelinePanel = {
  slotClass: string;
  focused: boolean;
  uiIdle: boolean;
  minimized: boolean;
  slotIndex: number;
  onFocus: () => void;
  onToggleMin: () => void;
  onCycleSlot: (dir: -1 | 1) => void;
  onDropAtPoint?: (point: { x: number; y: number }) => void;
};

interface EntryRowProps {
  entry: SessionEntry;
  isActive: boolean;
  onSelect: (id: string) => void;
}

function EntryRow({ entry, isActive, onSelect }: EntryRowProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <motion.button
      onClick={() => onSelect(entry.id)}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      className={`
        w-full text-left rounded-xl px-3 py-2 border transition-all duration-150
        ${isActive
          ? 'border-cyan-500/30 bg-cyan-500/5'
          : 'border-white/5 bg-black/10 hover:border-white/10 hover:bg-white/5'
        }
      `}
      layout
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-[10px] font-mono text-gray-300/70 leading-snug flex-1 min-w-0">
          {truncate(entry.query)}
        </span>
        <span className="text-[9px] font-mono text-gray-600 shrink-0">
          {elapsed(entry.timestamp)}
        </span>
      </div>
      <div className="mt-0.5 flex items-center gap-2">
        <span className={`text-[9px] font-mono uppercase tracking-widest ${MODE_COLOR[entry.mode] ?? 'text-gray-500'}`}>
          {entry.mode}
        </span>
        <span className="text-[9px] font-mono text-gray-600">·</span>
        <span className="text-[9px] font-mono text-gray-600 truncate">
          {entry.ontology}
        </span>
      </div>

      {/* Inline result preview on hover */}
      <AnimatePresence>
        {hovered && entry.result && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-2 text-[9px] font-mono text-cyan-200/40 leading-relaxed line-clamp-3">
              {truncate(entry.result, 120)}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}

export default function SessionTimeline({ managed }: { managed?: ManagedTimelinePanel } = {}) {
  const sessionHistory  = useAtlasStore((s: AtlasState) => s.sessionHistory);
  const activeSessionId = useAtlasStore((s: AtlasState) => s.activeSessionId);
  const setActiveSession = useAtlasStore((s: AtlasState) => s.setActiveSession);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const dragTilt = useTransform(x, [-160, 0, 160], [-1.2, 0, 1.2]);
  const prefersReducedMotion = useReducedMotion();
  const [zIndex, setZIndex] = useState(++PANEL_Z);
  const [localMinimized, setLocalMinimized] = useState(false);

  const activeEntry = sessionHistory.find((e) => e.id === activeSessionId) ?? null;
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

  return (
    <motion.div
      drag={Boolean(managed)}
      dragMomentum={false}
      dragElastic={managed ? 0.18 : 0}
      dragSnapToOrigin={Boolean(managed)}
      dragTransition={managed ? { bounceStiffness: 260, bounceDamping: 26 } : undefined}
      style={managed ? { x, y, rotate: dragTilt, zIndex: managed.focused ? 120 : 80 } : { x, y, zIndex }}
      onPointerDown={() => {
        if (managed) managed.onFocus();
        else setZIndex(++PANEL_Z);
      }}
      onFocusCapture={() => {
        if (managed) managed.onFocus();
        else setZIndex(++PANEL_Z);
      }}
      onDragStart={managed ? () => managed.onFocus() : undefined}
      onDragEnd={
        managed
          ? (_event, info) => managed.onDropAtPoint?.({ x: info.point.x, y: info.point.y })
          : undefined
      }
      whileHover={managed ? { scale: 1 } : { scale: 1.01 }}
      whileDrag={managed ? { scale: 1.012 } : undefined}
      tabIndex={0}
      className={`${managed ? `absolute ${managed.slotClass}` : 'absolute top-8 left-1/2 -translate-x-1/2'} z-20 w-72 p-6 rounded-3xl border ${panelTone} backdrop-blur-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] ${managed ? 'outline-none transition-opacity duration-200' : ''}`}
    >
      <motion.div
        animate={prefersReducedMotion ? undefined : { y: [0, -1.5, 0, 1, 0] }}
        transition={prefersReducedMotion ? undefined : { duration: 14, ease: 'easeInOut', repeat: Infinity }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
            Session Timeline
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
            <span className="text-[9px] font-mono text-gray-600">
              {sessionHistory.length} entries
            </span>
          </div>
        </div>

        {isMinimized ? (
          <div className="text-[9px] font-mono text-gray-500">Minimized · Alt+0 restores focused panel</div>
        ) : (
          <>
            {/* Timeline list */}
            {sessionHistory.length === 0 ? (
              <div className="text-[10px] font-mono text-gray-700 text-center py-4">
                no queries yet
              </div>
            ) : (
              <motion.div
                className="pretty-scroll space-y-1.5 max-h-52 overflow-y-auto pr-1"
                layout
              >
                <AnimatePresence initial={false}>
                  {sessionHistory.map((entry) => (
                    <motion.div
                      key={entry.id}
                      initial={{ opacity: 0, y: -8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, height: 0 }}
                      layout
                    >
                      <EntryRow
                        entry={entry}
                        isActive={entry.id === activeSessionId}
                        onSelect={setActiveSession}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.div>
            )}

            {/* Rewound result display */}
            {activeEntry && (
              <motion.div
                key={activeEntry.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-4 border-t border-white/5 pt-4"
              >
                <div className="text-[9px] uppercase tracking-widest text-gray-600 mb-1">
                  Rewound · {activeEntry.mode} / {activeEntry.ontology}
                </div>
                <div
                  className="pretty-scroll rounded-xl border border-white/5 bg-black/30 p-3 text-[10px] font-mono text-cyan-200/50 leading-relaxed max-h-28 overflow-y-auto"
                >
                  {activeEntry.result || '(no result)'}
                </div>
              </motion.div>
            )}
          </>
        )}
      </motion.div>
    </motion.div>
  );
}
