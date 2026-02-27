#!/usr/bin/env python3
"""
autonudge_tmux.py — guarded tmux watchdog with optional Enter nudge.

Why this exists:
  Keep long-running operator loops from stalling without unsafe key-spam.

Safety model:
  - Only targets an explicit tmux pane.
  - Optional command allowlist gate.
  - STOP / PAUSE sentinels respected.
  - Cooldown + per-hour cap + optional max-total cap.
  - Every decision is appended to JSONL audit log.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Dict, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_log_path() -> Path:
    return repo_root() / ".entire" / "logs" / "autonudge.jsonl"


def append_jsonl(path: Path, event: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def run_tmux(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(["tmux", *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def get_pane_command(target: str) -> Optional[str]:
    rc, out, _err = run_tmux(["display-message", "-p", "-t", target, "#{pane_current_command}"])
    if rc != 0:
        return None
    return out


def capture_pane_hash(target: str, lines: int) -> Optional[str]:
    rc, out, _err = run_tmux(["capture-pane", "-p", "-t", target, "-S", f"-{lines}", "-E", "-1"])
    if rc != 0:
        return None
    return hashlib.sha256(out.encode("utf-8", errors="ignore")).hexdigest()


def pane_exists(target: str) -> bool:
    rc, _out, _err = run_tmux(["display-message", "-p", "-t", target, "#{pane_id}"])
    return rc == 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Guarded tmux watchdog / autonudge daemon")
    p.add_argument("--target-pane", required=True, help="tmux pane target, e.g. %1 or session:window.pane")
    p.add_argument("--mode", choices=["monitor", "nudge"], default="monitor")
    p.add_argument("--allow-command", default="codex|python|node|bash|zsh", help="regex gate for pane command")
    p.add_argument("--poll-sec", type=int, default=5)
    p.add_argument("--idle-sec", type=int, default=90, help="unchanged output threshold for stale detection")
    p.add_argument("--cooldown-sec", type=int, default=45, help="min seconds between nudges")
    p.add_argument("--max-nudges-per-hour", type=int, default=20)
    p.add_argument("--max-total-nudges", type=int, default=0, help="0 means unlimited")
    p.add_argument("--capture-lines", type=int, default=80)
    p.add_argument("--log-path", default=str(default_log_path()))
    p.add_argument("--name", default="autonudge", help="daemon name for audit logs")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if shutil.which("tmux") is None:
        print("tmux not found in PATH", file=sys.stderr)
        return 2

    root = repo_root()
    stop_file = root / "STOP"
    pause_file = root / "PAUSE"
    log_path = Path(args.log_path)

    allow_re = re.compile(args.allow_command)
    nudge_timestamps: Deque[float] = deque()
    total_nudges = 0
    start_ts = time.time()

    if not pane_exists(args.target_pane):
        append_jsonl(
            log_path,
            {
                "ts": now_iso(),
                "daemon": args.name,
                "event": "start_failed",
                "reason": "pane_not_found",
                "target": args.target_pane,
            },
        )
        print(f"target pane not found: {args.target_pane}", file=sys.stderr)
        return 3

    pane_hash = capture_pane_hash(args.target_pane, args.capture_lines)
    if pane_hash is None:
        print("failed to capture target pane", file=sys.stderr)
        return 4

    last_change = time.time()
    last_nudge = 0.0
    loop = 0

    append_jsonl(
        log_path,
        {
            "ts": now_iso(),
            "daemon": args.name,
            "event": "started",
            "target": args.target_pane,
            "mode": args.mode,
            "idle_sec": args.idle_sec,
            "cooldown_sec": args.cooldown_sec,
            "max_nudges_per_hour": args.max_nudges_per_hour,
            "max_total_nudges": args.max_total_nudges,
            "allow_command": args.allow_command,
        },
    )

    while True:
        loop += 1

        if stop_file.exists():
            append_jsonl(
                log_path,
                {
                    "ts": now_iso(),
                    "daemon": args.name,
                    "event": "stopped_by_sentinel",
                    "target": args.target_pane,
                    "uptime_sec": int(time.time() - start_ts),
                    "total_nudges": total_nudges,
                },
            )
            return 0

        if pause_file.exists():
            if loop % 12 == 0:
                append_jsonl(
                    log_path,
                    {
                        "ts": now_iso(),
                        "daemon": args.name,
                        "event": "paused",
                        "target": args.target_pane,
                    },
                )
            time.sleep(max(1, args.poll_sec))
            continue

        if not pane_exists(args.target_pane):
            append_jsonl(
                log_path,
                {
                    "ts": now_iso(),
                    "daemon": args.name,
                    "event": "stopped_pane_lost",
                    "target": args.target_pane,
                    "uptime_sec": int(time.time() - start_ts),
                    "total_nudges": total_nudges,
                },
            )
            return 0

        pane_cmd = get_pane_command(args.target_pane) or ""
        pane_hash_new = capture_pane_hash(args.target_pane, args.capture_lines)
        if pane_hash_new is None:
            time.sleep(max(1, args.poll_sec))
            continue

        if pane_hash_new != pane_hash:
            pane_hash = pane_hash_new
            last_change = time.time()

        stale_for = time.time() - last_change
        if loop % 12 == 0:
            append_jsonl(
                log_path,
                {
                    "ts": now_iso(),
                    "daemon": args.name,
                    "event": "heartbeat",
                    "target": args.target_pane,
                    "mode": args.mode,
                    "pane_command": pane_cmd,
                    "stale_sec": int(stale_for),
                    "nudges_total": total_nudges,
                },
            )

        if stale_for < args.idle_sec:
            time.sleep(max(1, args.poll_sec))
            continue

        if not allow_re.search(pane_cmd):
            append_jsonl(
                log_path,
                {
                    "ts": now_iso(),
                    "daemon": args.name,
                    "event": "skip_disallowed_command",
                    "target": args.target_pane,
                    "pane_command": pane_cmd,
                    "stale_sec": int(stale_for),
                },
            )
            time.sleep(max(1, args.poll_sec))
            continue

        now = time.time()
        while nudge_timestamps and now - nudge_timestamps[0] > 3600:
            nudge_timestamps.popleft()

        if now - last_nudge < args.cooldown_sec:
            time.sleep(max(1, args.poll_sec))
            continue

        if len(nudge_timestamps) >= args.max_nudges_per_hour:
            append_jsonl(
                log_path,
                {
                    "ts": now_iso(),
                    "daemon": args.name,
                    "event": "skip_rate_limited",
                    "target": args.target_pane,
                    "nudges_last_hour": len(nudge_timestamps),
                    "limit": args.max_nudges_per_hour,
                },
            )
            time.sleep(max(1, args.poll_sec))
            continue

        if args.max_total_nudges > 0 and total_nudges >= args.max_total_nudges:
            append_jsonl(
                log_path,
                {
                    "ts": now_iso(),
                    "daemon": args.name,
                    "event": "stopped_max_total_reached",
                    "target": args.target_pane,
                    "max_total_nudges": args.max_total_nudges,
                },
            )
            return 0

        if args.mode == "nudge":
            rc, _out, err = run_tmux(["send-keys", "-t", args.target_pane, "Enter"])
            if rc != 0:
                append_jsonl(
                    log_path,
                    {
                        "ts": now_iso(),
                        "daemon": args.name,
                        "event": "nudge_failed",
                        "target": args.target_pane,
                        "error": err,
                    },
                )
                time.sleep(max(1, args.poll_sec))
                continue
            nudge_kind = "nudged"
        else:
            nudge_kind = "would_nudge"

        total_nudges += 1
        nudge_timestamps.append(now)
        last_nudge = now
        last_change = now

        append_jsonl(
            log_path,
            {
                "ts": now_iso(),
                "daemon": args.name,
                "event": nudge_kind,
                "target": args.target_pane,
                "mode": args.mode,
                "pane_command": pane_cmd,
                "stale_sec": int(stale_for),
                "nudges_total": total_nudges,
                "nudges_last_hour": len(nudge_timestamps),
            },
        )

        time.sleep(max(1, args.poll_sec))


if __name__ == "__main__":
    sys.exit(main())
