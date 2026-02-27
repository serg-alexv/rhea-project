'use client';

import { useEffect, useMemo, useState } from 'react';
import { TRIBUNAL_API, TRIBUNAL_API_KEY } from '@/lib/config';

type OfficeAgentPulse = {
  agent: string;
  status: 'stuck' | 'needs_attention' | 'alive' | 'idle' | string;
  lease_expired: boolean;
  pending_count: number;
  question_count: number;
  oldest_pending_min: number;
  last_activity_at: string | null;
};

type OfficePulsePayload = {
  generated_at: string;
  pending_total: number;
  stuck_total: number;
  question_total: number;
  agents: OfficeAgentPulse[];
};

type OfficeActionPayload = {
  status: string;
  ok_count: number;
  error_count: number;
};

const STATUS_DOT: Record<string, string> = {
  stuck: 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.65)]',
  needs_attention: 'bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.6)]',
  alive: 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.55)]',
  idle: 'bg-slate-500 shadow-[0_0_8px_rgba(100,116,139,0.4)]',
};

function prettyAge(min: number): string {
  if (!Number.isFinite(min) || min <= 0) return '0m';
  if (min < 60) return `${Math.round(min)}m`;
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return `${h}h ${m}m`;
}

export default function OfficePulsePanel({ maxRows = 5 }: { maxRows?: number }) {
  const [data, setData] = useState<OfficePulsePayload | null>(null);
  const [error, setError] = useState('');
  const [busyKey, setBusyKey] = useState('');
  const [actionNote, setActionNote] = useState('');

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const res = await fetch(`${TRIBUNAL_API}/office/pulse`, {
          headers: { 'X-API-Key': TRIBUNAL_API_KEY },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const payload = (await res.json()) as OfficePulsePayload;
        if (!mounted) return;
        setData(payload);
        setError('');
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
  }, []);

  const rows = useMemo(() => {
    const source = data?.agents ?? [];
    return source.slice(0, Math.max(1, maxRows));
  }, [data, maxRows]);

  const runAction = async (
    action: 'wake' | 'boot' | 'drain' | 'ping',
    target: string,
    message?: string,
  ) => {
    const key = `${action}:${target}`;
    setBusyKey(key);
    setActionNote('');
    try {
      const body: Record<string, unknown> = { action, target };
      if (message) body.message = message;
      if (action === 'ping') body.priority = 'P1';
      const res = await fetch(`${TRIBUNAL_API}/office/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': TRIBUNAL_API_KEY,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as OfficeActionPayload;
      setActionNote(`${action}:${target} · ok ${payload.ok_count} / err ${payload.error_count}`);
    } catch (e) {
      setActionNote(`${action}:${target} failed · ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBusyKey('');
    }
  };

  return (
    <div className="pt-1 border-t border-white/5">
      <div className="flex items-center justify-between text-[10px] font-mono">
        <span className="opacity-40">OFFICE LAMPS</span>
        <span className="text-cyan-300/75">
          pending {data?.pending_total ?? 0} · stuck {data?.stuck_total ?? 0}
        </span>
      </div>

      <div className="mt-1 flex gap-1">
        <button
          type="button"
          onClick={() => runAction('wake', 'ALL')}
          disabled={busyKey !== ''}
          className="rounded border border-cyan-500/25 bg-cyan-500/10 px-1.5 py-0.5 text-[8px] font-mono text-cyan-200 disabled:opacity-40"
        >
          WAKE ALL
        </button>
        <button
          type="button"
          onClick={() => runAction('boot', 'ALL')}
          disabled={busyKey !== ''}
          className="rounded border border-amber-500/25 bg-amber-500/10 px-1.5 py-0.5 text-[8px] font-mono text-amber-200 disabled:opacity-40"
        >
          RESTART ALL
        </button>
      </div>

      {error ? (
        <div className="mt-1 text-[8px] font-mono text-red-400/80">office pulse unavailable: {error}</div>
      ) : (
        <div className="mt-1 space-y-1">
          {rows.length === 0 ? (
            <div className="text-[8px] font-mono text-gray-600">no office agents detected</div>
          ) : (
            rows.map((row) => {
              const dot = STATUS_DOT[row.status] ?? STATUS_DOT.idle;
              const busyWake = busyKey === `wake:${row.agent}`;
              const busyBoot = busyKey === `boot:${row.agent}`;
              const busyPing = busyKey === `ping:${row.agent}`;
              return (
                <div
                  key={row.agent}
                  className="rounded-lg border border-white/10 bg-black/25 px-1.5 py-1"
                >
                  <div className="flex items-center justify-between gap-2 text-[8px] font-mono">
                    <div className="min-w-0 flex items-center gap-1.5">
                      <span className={`inline-block h-1.5 w-1.5 rounded-full ${dot}`} />
                      <span className="truncate text-gray-200">{row.agent}</span>
                      <span className="text-gray-500">{row.status}</span>
                    </div>
                    <span className="text-gray-400">
                      p:{row.pending_count} · q:{row.question_count} · wait:{prettyAge(row.oldest_pending_min)}
                    </span>
                  </div>
                  <div className="mt-1 flex gap-1">
                    <button
                      type="button"
                      onClick={() => runAction('wake', row.agent)}
                      disabled={busyWake || busyKey !== ''}
                      className="rounded border border-white/10 bg-black/25 px-1 py-0.5 text-[8px] font-mono text-gray-300 disabled:opacity-40"
                    >
                      {busyWake ? '...' : 'wake'}
                    </button>
                    <button
                      type="button"
                      onClick={() => runAction('boot', row.agent)}
                      disabled={busyBoot || busyKey !== ''}
                      className="rounded border border-white/10 bg-black/25 px-1 py-0.5 text-[8px] font-mono text-gray-300 disabled:opacity-40"
                    >
                      {busyBoot ? '...' : 'restart'}
                    </button>
                    <button
                      type="button"
                      onClick={() => runAction('ping', row.agent, 'UI ACK: please post status + blocker in virtual office')}
                      disabled={busyPing || busyKey !== ''}
                      className="rounded border border-white/10 bg-black/25 px-1 py-0.5 text-[8px] font-mono text-gray-300 disabled:opacity-40"
                    >
                      {busyPing ? '...' : 'ping'}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      <div className="mt-1 text-[8px] font-mono text-gray-500">
        {actionNote || `questions ${data?.question_total ?? 0} · update ${data?.generated_at ? new Date(data.generated_at).toLocaleTimeString() : '—'}`}
      </div>
    </div>
  );
}
