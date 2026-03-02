'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion'; // Assuming framer-motion is available
import useWhisperStore from '@/store/useWhisperStore';
import { Whisper, MoodCategory, Glyph } from '@/data/whispers'; // Assuming whispers.ts is at this path

// --- SVG Glyphs ---
// Basic SVG definitions for each glyph. In a real app, these might be in a separate file or imported.

// Placeholder SVG component for a generic glyph
const GenericGlyph = ({ glyphName }: { glyphName: Glyph }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    className="w-8 h-8"
  >
    <title>{glyphName}</title>
    {/* Placeholder SVG path - Replace with actual glyphs */}
    {glyphName === 'eye' && <path d="M2 12s7-8 12-8 12 8 12 8-7 8-12 8-12-8-12-8z"></path>}
    {glyphName === 'eye' && <circle cx="12" cy="12" r="3"></circle>}
    {glyphName === 'moon' && <path d="M12 3a6 6 0 0 1 6 6 6 6 0 0 1-12 0 6 6 0 0 1 6-6z"></path>}
    {glyphName === 'wave' && <path d="M1.5 15.75l7.5-7.5 7.5 7.5 7.5-7.5"></path>}
    {glyphName === 'flame' && <path d="M8.25 21 12 15 15.75 21"></path>}
    {glyphName === 'flame' && <path d="M12 15V3M12 3l3 7-3 11"></path>}
    {glyphName === 'seed' && <path d="M12 1.5v2.25m0 13.5v2.25M4.5 4.5l1.5 1.5m12 12l1.5-1.5M3 12h2.25m13.5 0H21M12 4.5l-7.5 7.5 7.5 7.5 7.5-7.5-7.5-7.5z"></path>}
    {glyphName === 'spiral' && <path d="M12 1.5a10.5 10.5 0 10 0 21 10.5 10.5 0 000-21zM12 4.5a7.5 7.5 0 10 0 15 7.5 7.5 0 000-15z"></path>}
    {glyphName === 'compass' && <path d="M12 1.5a10.5 10.5 0 10 0 21 10.5 10.5 0 000-21z"></path>}
    {glyphName === 'compass' && <path d="M12 6v13.5"></path>}
    {glyphName === 'compass' && <path d="M6.75 12h10.5"></path>}
    {glyphName === 'prism' && <path d="M2.25 10.5h19.5m-19.5 0L12 3m-10.5 7.5h21"></path>}
    {glyphName === 'prism' && <path d="M12 3l10.5 7.5-10.5 7.5-10.5-7.5L12 3z"></path>}
    {glyphName === 'feather' && <path d="M12 1.5l-7.5 7.5 7.5 7.5 7.5-7.5-7.5-7.5z"></path>}
    {glyphName === 'feather' && <path d="M12 9.75l3 3"></path>}
    {glyphName === 'anchor' && <path d="M12 1.5l-3 7.5h6L12 1.5z"></path>}
    {glyphName === 'anchor' && <path d="M12 9v13.5"></path>}
    {glyphName === 'lotus' && <path d="M12 2.25a9.75 9.75 0 100 19.5 9.75 9.75 0 000-19.5z"></path>}
    {glyphName === 'lotus' && <path d="M12 5.25l3.75 3.75-3.75 3.75-3.75-3.75 3.75-3.75z"></path>}
    {glyphName === 'star' && <path d="M12 1.5l-2.687 5.438L2.25 7.5l4.938 4.812L8.125 21 12 16.5l3.875 4.5-0.75-8.688L21.75 7.5l-7.063-.563L12 1.5z"></path>}

    {/* Default fallback if glyph not found */}
    {!['eye', 'moon', 'wave', 'flame', 'seed', 'spiral', 'compass', 'prism', 'feather', 'anchor', 'lotus', 'star'].includes(glyphName) && (
      <circle cx="12" cy="12" r="5"></circle>
    )}
  </svg>
);

// Mapping moods to colors and preferred glyphs
const moodConfig: Record<MoodCategory, { color: string; glyph: Glyph }> = {
  focused: { color: '#06b6d4', glyph: 'eye' }, // cyan-500
  exploring: { color: '#a78bfa', glyph: 'compass' }, // violet-400
  frustrated: { color: '#f97316', glyph: 'anchor' }, // orange-500
  triumphant: { color: '#facc15', glyph: 'flame' }, // yellow-400
  idle: { color: '#64748b', glyph: 'moon' }, // slate-500
  entering: { color: '#34d399', glyph: 'seed' }, // emerald-400
  departing: { color: '#60a5fa', glyph: 'wave' }, // blue-400 (adding a default departing color)
};

// --- MnemosyneWhisper Component ---
const MnemosyneWhisper: React.FC = () => {
  const { currentWhisper, dismissWhisper, isShowingWhisper, autoDismissTimer } = useWhisperStore(
    (state) => ({
      currentWhisper: state.currentWhisper,
      dismissWhisper: state.dismissWhisper,
      isShowingWhisper: state.isShowingWhisper,
      autoDismissTimer: state.autoDismissTimer,
    })
  );

  // If no whisper is active, don't render anything
  if (!currentWhisper || !isShowingWhisper) {
    return null;
  }

  const { color, glyph } = moodConfig[currentWhisper.mood] || moodConfig.entering; // Fallback mood config

  // Animation variants for framer-motion
  const variants = {
    hidden: { opacity: 0, y: 50, x: -50, scale: 0.8 }, // Start off-screen, slightly scaled down
    visible: { opacity: 1, y: 0, x: 0, scale: 1, transition: { type: 'spring', stiffness: 200, damping: 20 } },
    exit: { opacity: 0, y: 50, x: -50, scale: 0.8, transition: { duration: 0.3 } },
  };

  // Positioning logic - random corner placement
  // This needs to be dynamic to avoid overlapping other UI elements,
  // but for simplicity, we'll use fixed corner classes.
  const positionClasses = ['bottom-4 left-4', 'bottom-4 right-4', 'top-4 left-4'];
  // A more robust solution would check z-indexes of other elements.
  // For now, we'll just pick one based on a simple heuristic or random.
  const posClass = positionClasses[Math.floor(Math.random() * positionClasses.length)];

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      exit="exit"
      variants={variants}
      className={`fixed z-[1000] w-64 p-4 rounded-lg shadow-xl backdrop-blur-sm bg-black/30 border border-white/10 ${posClass}`}
      style={{ '--whisper-color': color } as React.CSSProperties} // Use CSS variable for color
      onClick={dismissWhisper} // Dismiss on click
    >
      <div className="flex items-center mb-2">
        {/* Glyph */}
        <div className="mr-3" style={{ color: color }}>
          <GenericGlyph glyphName={glyph} />
        </div>
        {/* Attribution */}
        <span className="text-xs text-white/60 font-medium">— {currentWhisper.attribution}</span>
      </div>

      {/* Text */}
      <p className="text-sm text-white/80 mb-3 leading-tight">
        {currentWhisper.text}
      </p>

      {/* Mood Indicator Bar */}
      <div className="w-full h-1 rounded-full" style={{ backgroundColor: color }}></div>
      <div className="text-xs text-white/50 mt-1 capitalize">{currentWhisper.mood}</div>
    </motion.div>
  );
};

export default MnemosyneWhisper;
