#!/usr/bin/env python3
"""
flow_guard.py — Non-stop flow health checks from bridge call logs.

Goal:
- Treat errors as recoverable events, not stop conditions.
- Compute 10 continuity checks over a rolling window.
- Emit both terminal report and JSON artifact for dashboards.

Examples:
  python3 scripts/flow_guard.py
  python3 scripts/flow_guard.py --window-hours 48 --json
  python3 scripts/flow_guard.py --recovery-sec 600 --out opera/metrics/flow_guard_48h.json
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = REPO_ROOT / "logs" / "bridge_calls.jsonl"
DEFAULT_OUT = REPO_ROOT / "opera" / "metrics" / "flow_guard.json"


@dataclass
class CheckResult:
    id: str
    name: str
    passed: bool
    value: float | int | str
    threshold: str
    note: str


def parse_ts(raw: str) -> datetime | None:
    if not raw:
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        ts = datetime.fromisoformat(text)
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    k = (len(xs) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return float(xs[int(k)])
    return float(xs[lo] + (xs[hi] - xs[lo]) * (k - lo))


def read_records(path: Path, since: datetime) -> tuple[list[dict], int, int]:
    records: list[dict] = []
    total_lines = 0
    parse_errors = 0

    if not path.exists():
        return records, total_lines, parse_errors

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            total_lines += 1
            try:
                rec = json.loads(line)
            except Exception:
                parse_errors += 1
                continue

            ts = parse_ts(str(rec.get("timestamp", "")))
            if not ts:
                parse_errors += 1
                continue
            if ts < since:
                continue

            rec["_ts"] = ts
            rec["_status"] = str(rec.get("status") or "unknown").strip().lower()
            rec["_provider"] = str(rec.get("provider") or "unknown").strip().lower()
            rec["_model"] = str(rec.get("model") or "unknown").strip().lower()
            records.append(rec)

    records.sort(key=lambda r: r["_ts"])
    return records, total_lines, parse_errors


def compute_checks(records: list[dict], total_lines: int, parse_errors: int, recovery_sec: int) -> tuple[list[CheckResult], dict]:
    n = len(records)
    ok_idx = [i for i, r in enumerate(records) if r["_status"] == "ok"]
    err_idx = [i for i, r in enumerate(records) if r["_status"] != "ok"]

    ok_calls = len(ok_idx)
    err_calls = len(err_idx)
    ok_rate = (ok_calls / n) if n else 0.0
    err_rate = (err_calls / n) if n else 0.0
    parse_error_rate = (parse_errors / total_lines) if total_lines else 0.0

    # Recovery analysis after error events
    recovered = 0
    recovery_times: list[float] = []
    continued_after_error = 0
    fallback_switch = 0

    for i in err_idx:
        e = records[i]
        had_next = False
        for j in range(i + 1, n):
            nxt = records[j]
            dt = (nxt["_ts"] - e["_ts"]).total_seconds()
            if dt <= recovery_sec:
                had_next = True
            if nxt["_status"] == "ok":
                if dt <= recovery_sec:
                    recovered += 1
                    recovery_times.append(dt)
                # fallback switch proxy: provider or model changed after an error
                if nxt["_provider"] != e["_provider"] or nxt["_model"] != e["_model"]:
                    fallback_switch += 1
                break
        if had_next:
            continued_after_error += 1

    recovery_rate = (recovered / err_calls) if err_calls else 1.0
    continuation_rate = (continued_after_error / err_calls) if err_calls else 1.0
    fallback_switch_rate = (fallback_switch / err_calls) if err_calls else 1.0
    p95_recovery_sec = percentile(recovery_times, 0.95) if recovery_times else 0.0

    # Error streak
    max_err_streak = 0
    cur_err_streak = 0
    for r in records:
        if r["_status"] != "ok":
            cur_err_streak += 1
            max_err_streak = max(max_err_streak, cur_err_streak)
        else:
            cur_err_streak = 0

    # Success gaps (between OK calls)
    max_ok_gap_sec = 0.0
    if len(ok_idx) >= 2:
        for a, b in zip(ok_idx[:-1], ok_idx[1:]):
            dt = (records[b]["_ts"] - records[a]["_ts"]).total_seconds()
            max_ok_gap_sec = max(max_ok_gap_sec, dt)

    # Terminal health: last status is ok OR at least one ok in last 3 calls
    terminal_ok = False
    if records:
        tail = records[-3:]
        terminal_ok = (records[-1]["_status"] == "ok") or any(r["_status"] == "ok" for r in tail)

    # Observability coverage in-window
    required_fields = ("timestamp", "status", "total_tokens", "cost_usd", "latency_ms", "provider", "model")
    covered = 0
    for r in records:
        if all(k in r for k in required_fields):
            covered += 1
    observability_coverage = (covered / n) if n else 0.0

    checks: list[CheckResult] = [
        CheckResult("C1", "Log parse integrity", parse_error_rate <= 0.01, round(parse_error_rate, 4), "<= 0.01", "JSONL rows parse cleanly"),
        CheckResult("C2", "Activity present", n >= 10, n, ">= 10 calls", "Enough data for continuity signal"),
        CheckResult("C3", "Success ratio", ok_rate >= 0.60, round(ok_rate, 3), ">= 0.60", "Majority of calls complete"),
        CheckResult("C4", "Error recovery ratio", recovery_rate >= 0.70, round(recovery_rate, 3), ">= 0.70", "Errors recover to OK within recovery window"),
        CheckResult("C5", "Consecutive error cap", max_err_streak <= 3, max_err_streak, "<= 3", "No long failure cascades"),
        CheckResult("C6", "Recovery speed P95", p95_recovery_sec <= float(recovery_sec), round(p95_recovery_sec, 1), f"<= {recovery_sec}s", "Recover fast enough for live flow"),
        CheckResult("C7", "Post-error continuation", continuation_rate >= 0.90, round(continuation_rate, 3), ">= 0.90", "Errors do not halt activity stream"),
        CheckResult("C8", "Fallback agility", fallback_switch_rate >= 0.30, round(fallback_switch_rate, 3), ">= 0.30", "After error, route/model switch appears"),
        CheckResult("C9", "Terminal health", terminal_ok, str(terminal_ok).lower(), "true", "Tail is recoverable/alive"),
        CheckResult("C10", "Observability coverage", observability_coverage >= 0.95, round(observability_coverage, 3), ">= 0.95", "Rows contain fields needed for diagnosis"),
    ]

    summary = {
        "calls": n,
        "ok_calls": ok_calls,
        "error_calls": err_calls,
        "ok_rate": round(ok_rate, 4),
        "error_rate": round(err_rate, 4),
        "parse_error_rate": round(parse_error_rate, 4),
        "recovery_rate": round(recovery_rate, 4),
        "p95_recovery_sec": round(p95_recovery_sec, 2),
        "max_error_streak": max_err_streak,
        "max_ok_gap_sec": round(max_ok_gap_sec, 2),
        "continuation_rate": round(continuation_rate, 4),
        "fallback_switch_rate": round(fallback_switch_rate, 4),
        "observability_coverage": round(observability_coverage, 4),
        "checks_passed": sum(1 for c in checks if c.passed),
        "checks_total": len(checks),
    }
    return checks, summary


def render_terminal(payload: dict) -> None:
    print(f"FLOW GUARD ({payload['window_hours']}h)")
    print("=" * 72)
    s = payload["summary"]
    print(
        f"calls={s['calls']} ok={s['ok_calls']} err={s['error_calls']} "
        f"ok_rate={s['ok_rate']:.3f} recovery_rate={s['recovery_rate']:.3f} "
        f"checks={s['checks_passed']}/{s['checks_total']}"
    )
    print("-" * 72)
    for c in payload["checks"]:
        mark = "GREEN" if c["passed"] else "RED"
        print(f"{c['id']:>3} {mark:5s}  {c['name']:<24s} value={c['value']!s:<8s} threshold {c['threshold']}  | {c['note']}")
    print("=" * 72)


def main() -> int:
    p = argparse.ArgumentParser(description="Continuity checks for non-stop flow")
    p.add_argument("--log", type=Path, default=DEFAULT_LOG, help=f"JSONL log path (default: {DEFAULT_LOG})")
    p.add_argument("--window-hours", type=int, default=24, help="Rolling analysis window (1..168)")
    p.add_argument("--recovery-sec", type=int, default=300, help="Recovery SLO in seconds")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output JSON path (default: {DEFAULT_OUT})")
    p.add_argument("--json", action="store_true", help="Print JSON payload to stdout")
    args = p.parse_args()

    window_hours = max(1, min(args.window_hours, 168))
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=window_hours)

    records, total_lines, parse_errors = read_records(args.log, since)
    checks, summary = compute_checks(records, total_lines, parse_errors, args.recovery_sec)

    payload = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "window_hours": window_hours,
        "since": since.isoformat().replace("+00:00", "Z"),
        "until": now.isoformat().replace("+00:00", "Z"),
        "log": str(args.log),
        "summary": summary,
        "checks": [asdict(c) for c in checks],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        render_terminal(payload)
        print(f"Saved: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
