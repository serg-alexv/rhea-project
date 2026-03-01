'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useWhisperStore } from '@/store/useWhisperStore';
import { MoodCategory, WhisperGlyph } from '@/data/whispers';

const MOOD_COLOR: Record<MoodCategory, string> = {
  focused: '#06b6d4',
  exploring: '#a78bfa',
  frustrated: '#f97316',
  triumphant: '#facc15',
  idle: '#64748b',
  entering: '#34d399',
  departing: '#60a5fa',
};

const CORNERS = ['top-left', 'top-right', 'bottom-left'] as const;
type WhisperCorner = typeof CORNERS[number];

function cornerClass(corner: WhisperCorner): string {
  if (corner === 'top-left') return 'top-12 left-80';
  if (corner === 'top-right') return 'top-12 right-80';
  return 'bottom-24 left-80';
}

function glyphPath(glyph: WhisperGlyph): React.JSX.Element {
  const common = { stroke: 'currentColor', fill: 'none', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  switch (glyph) {
    case 'moon':
      return <path {...common} d="M20 5a10 10 0 1 0 7 17A11 11 0 0 1 20 5Z" />;
    case 'wave':
      return <path {...common} d="M3 16c3-6 6 6 9 0s6-6 9 0 6 6 9 0" />;
    case 'eye':
      return <><path {...common} d="M2 16s5-8 14-8 14 8 14 8-5 8-14 8S2 16 2 16Z" /><circle {...common} cx="16" cy="16" r="3.5" /></>;
    case 'flame':
      return <path {...common} d="M17 3c2 5-1 6 1 9 1 2 4 2 4 7a6 6 0 0 1-12 0c0-4 3-6 4-8 1-2 0-4 3-8Z" />;
    case 'seed':
      return <><path {...common} d="M16 6c5 0 8 4 8 8s-3 8-8 8-8-4-8-8 3-8 8-8Z" /><path {...common} d="M16 10v12" /></>;
    case 'spiral':
      return <path {...common} d="M16 16m-1 0a1 1 0 1 0 2 0 3 3 0 1 0-3 3 5 5 0 1 0 5-5 7 7 0 1 0-7 7" />;
    case 'compass':
      return <><circle {...common} cx="16" cy="16" r="11" /><path {...common} d="M20 12l-3 8-5 2 3-8 5-2Z" /></>;
    case 'prism':
      return <><path {...common} d="M8 8h12l4 8-4 8H8l-4-8 4-8Z" /><path {...common} d="M8 8l8 8-8 8" /></>;
    case 'feather':
      return <path {...common} d="M26 6c-9 0-16 7-16 16m0 0c2-3 5-4 8-4m-8 4 4 4" />;
    case 'anchor':
      return <><path {...common} d="M16 4v14" /><circle {...common} cx="16" cy="7" r="2" /><path {...common} d="M8 18a8 8 0 0 0 16 0" /><path {...common} d="M10 18H6m20 0h-4" /></>;
    case 'lotus':
      return <><path {...common} d="M16 8c2 3 2 7 0 10-2-3-2-7 0-10Z" /><path {...common} d="M10 11c3 1 5 4 6 7-4 0-7-2-9-5 1-1 2-2 3-2Z" /><path {...common} d="M22 11c-3 1-5 4-6 7 4 0 7-2 9-5-1-1-2-2-3-2Z" /></>;
    case 'star':
      return <path {...common} d="M16 3l3.5 9H29l-7.5 5.5L24 27l-8-5-8 5 2.5-9.5L3 12h9.5L16 3Z" />;
    default:
      return <circle {...common} cx="16" cy="16" r="10" />;
  }
}

function WhisperGlyphIcon({ glyph, mood }: { glyph: WhisperGlyph; mood: MoodCategory }) {
  return (
    <div className="w-8 h-8 rounded-lg border border-white/10 bg-black/30 flex items-center justify-center" style={{ color: MOOD_COLOR[mood] }}>
      <svg width="22" height="22" viewBox="0 0 32 32" aria-hidden="true">
        {glyphPath(glyph)}
      </svg>
    </div>
  );
}

export default function MnemosyneWhisper() {
  const current = useWhisperStore((s) => s.current);
  const visible = useWhisperStore((s) => s.visible);
  const dismissCurrent = useWhisperStore((s) => s.dismissCurrent);
  const currentMood = useWhisperStore((s) => s.currentMood);
  const [corner, setCorner] = useState<WhisperCorner>('top-right');

  useEffect(() => {
    if (!current) return;
    const sum = current.id.split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
    setCorner(CORNERS[sum % CORNERS.length]);
  }, [current]);

  const color = current ? MOOD_COLOR[current.mood] : MOOD_COLOR[currentMood];
  const edgeDirection = useMemo(() => {
    if (corner === 'top-left') return { x: -14, y: -10 };
    if (corner === 'top-right') return { x: 14, y: -10 };
    return { x: -14, y: 10 };
  }, [corner]);

  return (
    <AnimatePresence>
      {visible && current && (
        <motion.button
          key={current.id}
          type="button"
          onClick={dismissCurrent}
          initial={{ opacity: 0, x: edgeDirection.x, y: edgeDirection.y, scale: 0.985 }}
          animate={{ opacity: 1, x: 0, y: 0, scale: 1 }}
          exit={{ opacity: 0, x: edgeDirection.x * 0.6, y: edgeDirection.y * 0.6, scale: 0.985 }}
          transition={{ duration: 0.28, ease: 'easeOut' }}
          className={`fixed ${cornerClass(corner)} z-[260] w-[240px] text-left rounded-2xl border border-white/10 bg-black/70 backdrop-blur-2xl shadow-[0_8px_40px_rgba(0,0,0,0.5)] p-3 cursor-pointer`}
          style={{ boxShadow: `0 8px 40px rgba(0,0,0,0.5), 0 0 0 1px ${color}20` }}
          title="Dismiss whisper"
        >
          <div className="flex items-start gap-3">
            <WhisperGlyphIcon glyph={current.glyph} mood={current.mood} />
            <div className="min-w-0 flex-1">
              <div className="text-[10px] font-mono text-gray-200/85 leading-relaxed">
                {current.text}
              </div>
              <div className="mt-1 text-[9px] font-mono text-gray-500 text-right">- {current.attribution}</div>
            </div>
          </div>
          <div className="mt-2 h-1 rounded-full bg-white/5 overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: `linear-gradient(90deg, ${color}, transparent)` }}
              initial={{ width: '100%' }}
              animate={{ width: '0%' }}
              transition={{ duration: 8, ease: 'linear' }}
            />
          </div>
          <div className="mt-1 flex items-center justify-between text-[8px] font-mono uppercase tracking-widest text-gray-500">
            <span>mood: {current.mood}</span>
            <span className="text-gray-600">mnemosyne whisper</span>
          </div>
        </motion.button>
      )}
    </AnimatePresence>
  );
}
