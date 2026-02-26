'use client';

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useAtlasStore, SessionEntry } from '@/store/useAtlasStore';

const ONTOLOGIES = [
  'General',
  'Pharmacology',
  'Biochemistry',
  'Logic',
  'Topology',
  'Systems Biology',
] as const;

type Ontology = typeof ONTOLOGIES[number];
type Mode = 'tribunal' | 'sceptic' | 'ice';

const MODE_LABELS: Record<Mode, string> = {
  tribunal: 'Tribunal',
  sceptic:  'Sceptic',
  ice:      'ICE',
};

const MODE_ENDPOINTS: Record<Mode, string> = {
  tribunal: 'http://localhost:8000/api/tribunal',
  sceptic:  'http://localhost:8000/tribunal/sceptic',
  ice:      'http://localhost:8000/tribunal/ice',
};

function uid(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

export default function ResearchPanel() {
  const [query, setQuery] = useState('');
  const [ontology, setOntology] = useState<Ontology>('General');
  const [mode, setMode] = useState<Mode>('tribunal');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addSessionEntry = useAtlasStore((s) => s.addSessionEntry);

  const handleSubmit = useCallback(async () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError('');
    setResult('');

    try {
      const res = await fetch(MODE_ENDPOINTS[mode], {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'dev-bypass',
        },
        body: JSON.stringify({ query: trimmed, ontology }),
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
      }

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
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Network error: ${msg}`);
      setResult('');
    } finally {
      setLoading(false);
    }
  }, [query, ontology, mode, loading, addSessionEntry]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit();
    }
  };

  return (
    <motion.div
      drag
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={0.1}
      whileHover={{ scale: 1.01 }}
      className="absolute bottom-8 right-8 z-20 w-80 p-6 rounded-3xl border border-white/5 bg-white/5 backdrop-blur-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] cursor-grab active:cursor-grabbing"
    >
      {/* Header */}
      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-4">
        Research Query
      </h2>

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
          onChange={(e) => setOntology(e.target.value as Ontology)}
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
              onClick={() => setMode(m)}
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
        {loading ? 'querying…' : 'submit'}
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
    </motion.div>
  );
}
