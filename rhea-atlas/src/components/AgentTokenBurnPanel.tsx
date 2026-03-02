'use client';

import { useEffect, useMemo, useState } from 'react';
import { TRIBUNAL_API, TRIBUNAL_API_KEY } from '@/lib/config';

type AgentUsage = {
  agent_id: string;
  agent_name: string;
  calls: number;
  tokens: number;
  cost_usd: number;
};

type UsagePayload = {
  window_hours: number;
  total_calls: number;
  total_tokens: number;
  total_cost_usd: number;
  agents: AgentUsage[];
};

export default function AgentTokenBurnPanel({ windowHours = 24 }: { windowHours?: number }) {
  const [data, setData] = useState<UsagePayload | null>(null);
  const [error, setError] = useState('');
  const [updatedAt, setUpdatedAt] = useState<number>(0);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const res = await fetch(`${TRIBUNAL_API}/usage/agents?window_hours=${windowHours}`, {
          headers: {
            'X-API-Key': TRIBUNAL_API_KEY,
          },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const payload = await res.json();
        if (!mounted) return;
        setData(payload);
        setError('');
        setUpdatedAt(Date.now());
      } catch (e) {
        if (!mounted) return;
        setError(e instanceof Error ? e.message : String(e));
      }
    };

    load();
    const timer = setInterval(load, 8000);
    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, [windowHours]);

  const top = useMemo(() => {
    const rows = data?.agents ?? [];
    return rows
      .filter((r) => r.tokens > 0)
      .sort((a, b) => b.tokens - a.tokens)
      .slice(0, 6);
  }, [data]);

  const maxTokens = useMemo(() => Math.max(1, ...top.map((r) => r.tokens)), [top]);

  return (
    <div className="pt-1 border-t border-white/5">
      <div className="flex justify-between items-center text-[10px] font-mono">
        <span className="opacity-40">AGENT TOKEN BURN ({windowHours}h)</span>
        <span className="text-cyan-300/70">
          {(data?.total_tokens ?? 0).toLocaleString()}
        </span>
      </div>

      {error ? (
        <div className="mt-1 text-[8px] font-mono text-red-400/70">usage unavailable: {error}</div>
      ) : (
        <>
          <div className="mt-1 space-y-1">
            {top.length === 0 ? (
              <div className="text-[8px] font-mono text-gray-600">no attributed token usage yet</div>
            ) : (
              top.map((row) => {
                const width = Math.max(6, Math.round((row.tokens / maxTokens) * 100));
                const label = row.agent_name?.trim() || row.agent_id || 'unknown';
                return (
                  <div key={`${row.agent_id}-${label}`}>
                    <div className="flex justify-between text-[8px] font-mono text-gray-400">
                      <span className="truncate max-w-[58%]">{label}</span>
                      <span>{row.tokens.toLocaleString()} tok · ${row.cost_usd.toFixed(4)}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-500/65 to-emerald-500/40"
                        style={{ width: `${width}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
          <div className="mt-1 text-[8px] font-mono text-gray-500">
            calls {(data?.total_calls ?? 0).toLocaleString()} · cost ${((data?.total_cost_usd ?? 0)).toFixed(4)}
            {updatedAt ? ` · live ${new Date(updatedAt).toLocaleTimeString()}` : ''}
          </div>
        </>
      )}
    </div>
  );
}
