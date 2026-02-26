'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAtlasStore, SessionEntry } from '@/store/useAtlasStore';

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

export default function SessionTimeline() {
  const sessionHistory = useAtlasStore((s) => s.sessionHistory);
  const activeSessionId = useAtlasStore((s) => s.activeSessionId);
  const setActiveSession = useAtlasStore((s) => s.setActiveSession);

  const activeEntry = sessionHistory.find((e) => e.id === activeSessionId) ?? null;

  return (
    <motion.div
      drag
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={0.1}
      whileHover={{ scale: 1.01 }}
      className="absolute top-8 left-1/2 -translate-x-1/2 z-20 w-72 p-6 rounded-3xl border border-white/5 bg-white/5 backdrop-blur-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] cursor-grab active:cursor-grabbing"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
          Session Timeline
        </h2>
        <span className="text-[9px] font-mono text-gray-600">
          {sessionHistory.length} entries
        </span>
      </div>

      {/* Timeline list */}
      {sessionHistory.length === 0 ? (
        <div className="text-[10px] font-mono text-gray-700 text-center py-4">
          no queries yet
        </div>
      ) : (
        <motion.div
          className="space-y-1.5 max-h-52 overflow-y-auto pr-1"
          style={{ scrollbarWidth: 'none' }}
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
            className="rounded-xl border border-white/5 bg-black/30 p-3 text-[10px] font-mono text-cyan-200/50 leading-relaxed max-h-28 overflow-y-auto"
            style={{ scrollbarWidth: 'none' }}
          >
            {activeEntry.result || '(no result)'}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
