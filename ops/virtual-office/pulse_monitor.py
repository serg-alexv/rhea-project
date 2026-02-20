#!/usr/bin/env python3
"""Minimal no-deps pulse monitor for Rhea virtual office."""

from __future__ import annotations

import curses
import json
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def safe_add(stdscr: "curses._CursesWindow", y: int, x: int, text: str) -> None:
    """Best-effort write that never crashes on small or resized terminals."""
    h, w = stdscr.getmaxyx()
    if y < 0 or x < 0 or y >= h or x >= w:
        return
    max_len = max(0, w - x - 1)
    if max_len <= 0:
        return
    try:
        stdscr.addnstr(y, x, text, max_len)
    except curses.error:
        pass


def _ts_to_age_minutes(ts: str) -> float:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return -1.0
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 60.0)


def gather() -> dict:
    mailbox = HERE / "relay_mailbox.jsonl"
    acks = HERE / "relay_acks.jsonl"
    chain = HERE / "relay_chain.jsonl"
    seq = (HERE / "relay_seq.txt").read_text().strip() if (HERE / "relay_seq.txt").exists() else "?"

    total, pending = 0, 0
    by_target: Counter[str] = Counter()
    if mailbox.exists():
        for line in mailbox.read_text().splitlines():
            if not line.strip():
                continue
            total += 1
            msg = json.loads(line)
            if msg.get("status") == "pending":
                pending += 1
                by_target[msg.get("target", "?")] += 1

    acked = 0
    if acks.exists():
        acked = sum(1 for ln in acks.read_text().splitlines() if ln.strip())

    last_chain = "n/a"
    if chain.exists():
        lines = [ln for ln in chain.read_text().splitlines() if ln.strip()]
        if lines:
            obj = json.loads(lines[-1])
            age = _ts_to_age_minutes(obj.get("timestamp", ""))
            last_chain = f"{age:.1f}m ago" if age >= 0 else "unknown"

    leases = []
    now = datetime.now(timezone.utc)
    for f in sorted((HERE / "leases").glob("*.json")):
        try:
            lease = json.loads(f.read_text())
            exp = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
            secs = int((exp - now).total_seconds())
            leases.append((lease.get("agent", f.stem), lease.get("lease_token", "?"), secs))
        except Exception:
            leases.append((f.stem, "?", -99999))

    failures = sorted((HERE / "inbox").glob("WATCHER_*_REX_FAILURE.md"))
    last_failure = failures[-1].name if failures else "none"

    return {
        "seq": seq,
        "total": total,
        "pending": pending,
        "acked": acked,
        "by_target": by_target,
        "last_chain": last_chain,
        "leases": leases,
        "last_failure": last_failure,
    }


def run_action(args: list[str]) -> str:
    try:
        out = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=12, check=False)
        text = (out.stdout or out.stderr or "").strip().splitlines()
        return text[0] if text else "ok"
    except Exception as exc:
        return f"error: {exc}"


def draw(stdscr: "curses._CursesWindow") -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    last_action = "ready"
    while True:
        data = gather()
        stdscr.erase()
        safe_add(stdscr, 0, 0, "Rhea Pulse Monitor (no restart mode)")
        safe_add(
            stdscr,
            1,
            0,
            f"UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}  seq={data['seq']}",
        )
        safe_add(stdscr, 2, 0, f"mailbox total={data['total']} pending={data['pending']} acked={data['acked']}")
        safe_add(stdscr, 3, 0, f"last chain event: {data['last_chain']}")
        safe_add(stdscr, 4, 0, f"last watcher REX failure: {data['last_failure']}")
        safe_add(stdscr, 6, 0, "Pending by target:")
        row = 7
        for target, cnt in data["by_target"].most_common(8):
            safe_add(stdscr, row, 2, f"- {target}: {cnt}")
            row += 1
        row += 1
        safe_add(stdscr, row, 0, "Leases:")
        row += 1
        for agent, token, secs in data["leases"][:8]:
            state = "OK" if secs > 0 else "EXPIRED"
            safe_add(stdscr, row, 2, f"- {agent:8} token={token:<4} expires_in={secs:>6}s {state}")
            row += 1
        row += 1
        safe_add(stdscr, row, 0, "Keys: [r] wake REX  [g] drain GPT  [s] status  [q] quit")
        safe_add(stdscr, row + 1, 0, f"last action: {last_action}")
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            return
        if key in (ord("r"), ord("R")):
            last_action = run_action(["python3", "ops/rex_pager.py", "wake", "REX"])
        elif key in (ord("g"), ord("G")):
            last_action = run_action(["python3", "ops/rex_pager.py", "drain", "GPT"])
        elif key in (ord("s"), ord("S")):
            last_action = run_action(["python3", "ops/rex_pager.py", "status"])
        time.sleep(0.75)


if __name__ == "__main__":
    curses.wrapper(draw)
