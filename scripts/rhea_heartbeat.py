#!/usr/bin/env python3
"""
rhea_heartbeat.py — Proactive health monitoring daemon (ADR-015)
Inspired by OpenClaw's heartbeat pattern with smart suppression.

Usage:
    python3 scripts/rhea_heartbeat.py           # run once
    python3 scripts/rhea_heartbeat.py --daemon   # run every 30 min
    python3 scripts/rhea_heartbeat.py --json     # machine-readable output
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_MD = ROOT / "docs" / "state.md"
INBOX = ROOT / "opera" / "ops" / "virtual-office" / "inbox"
OUTBOX = ROOT / "opera" / "ops" / "virtual-office" / "outbox"
HEARTBEAT_LOG = ROOT / "logs" / "heartbeat.log"


def check_state_md() -> dict:
    """Check state.md exists and is under 2KB."""
    if not STATE_MD.exists():
        return {"check": "state_md", "ok": False, "priority": "P0",
                "msg": "docs/state.md missing"}
    size = STATE_MD.stat().st_size
    if size > 2048:
        return {"check": "state_md", "ok": False, "priority": "P0",
                "msg": f"docs/state.md too large: {size}B > 2048B"}
    return {"check": "state_md", "ok": True, "size": size}


def check_git_push() -> dict:
    """Check last git push was within 30 minutes."""
    try:
        result = subprocess.run(
            ["git", "log", "--format=%ct", "-1", "origin/stage4-release"],
            capture_output=True, text=True, cwd=ROOT, timeout=5
        )
        if result.returncode != 0:
            # Try main branch
            result = subprocess.run(
                ["git", "log", "--format=%ct", "-1", "origin/main"],
                capture_output=True, text=True, cwd=ROOT, timeout=5
            )
        if result.returncode == 0 and result.stdout.strip():
            last_push = int(result.stdout.strip())
            age_min = (time.time() - last_push) / 60
            if age_min > 60:
                return {"check": "git_push", "ok": False, "priority": "P0",
                        "msg": f"Last push {age_min:.0f}min ago (>60min)"}
            if age_min > 30:
                return {"check": "git_push", "ok": False, "priority": "P1",
                        "msg": f"Last push {age_min:.0f}min ago (>30min)"}
            return {"check": "git_push", "ok": True, "age_min": round(age_min, 1)}
    except Exception as e:
        return {"check": "git_push", "ok": False, "priority": "P1",
                "msg": f"git check failed: {e}"}
    return {"check": "git_push", "ok": True, "msg": "no remote tracking"}


def check_invariants() -> dict:
    """Run scripts/rhea/check.sh."""
    try:
        result = subprocess.run(
            ["bash", "scripts/rhea/check.sh"],
            capture_output=True, text=True, cwd=ROOT, timeout=10
        )
        if result.returncode == 0:
            return {"check": "invariants", "ok": True}
        return {"check": "invariants", "ok": False, "priority": "P0",
                "msg": result.stderr.strip() or result.stdout.strip()}
    except Exception as e:
        return {"check": "invariants", "ok": False, "priority": "P1",
                "msg": str(e)}


def check_inbox() -> dict:
    """Check for unread relay messages."""
    if not INBOX.exists():
        return {"check": "inbox", "ok": True, "count": 0}
    msgs = list(INBOX.glob("RELAY_*.md"))
    if not msgs:
        return {"check": "inbox", "ok": True, "count": 0}
    # Check age of oldest unread
    oldest_age = 0
    for m in msgs:
        age = time.time() - m.stat().st_mtime
        oldest_age = max(oldest_age, age)
    age_hr = oldest_age / 3600
    priority = "P1" if age_hr > 1 else "P2"
    return {"check": "inbox", "ok": age_hr < 1, "count": len(msgs),
            "oldest_hr": round(age_hr, 1), "priority": priority}


def check_api() -> dict:
    """Check if tribunal API is responsive."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "3", "http://localhost:8400/health"],
            capture_output=True, text=True, timeout=5
        )
        code = result.stdout.strip()
        if code in ("200", "404"):  # 404 = no /health but server alive
            return {"check": "api", "ok": True, "status": code}
        return {"check": "api", "ok": False, "priority": "P1",
                "msg": f"API returned {code}"}
    except Exception:
        return {"check": "api", "ok": False, "priority": "P2",
                "msg": "API not reachable (server may be stopped)"}


def run_heartbeat() -> dict:
    """Execute all checks and return summary."""
    ts = datetime.now(timezone.utc).isoformat()
    checks = [
        check_state_md(),
        check_git_push(),
        check_invariants(),
        check_inbox(),
        check_api(),
    ]

    failures = [c for c in checks if not c.get("ok")]
    p0 = [c for c in failures if c.get("priority") == "P0"]
    p1 = [c for c in failures if c.get("priority") == "P1"]

    result = {
        "ts": ts,
        "status": "HEARTBEAT_OK" if not (p0 or p1) else "ALERT",
        "checks": checks,
        "p0_count": len(p0),
        "p1_count": len(p1),
        "total_failures": len(failures),
    }
    return result


def log_result(result: dict):
    """Append heartbeat result to log file."""
    HEARTBEAT_LOG.parent.mkdir(exist_ok=True)
    with open(HEARTBEAT_LOG, "a") as f:
        f.write(json.dumps(result) + "\n")
    # Keep only last 500 entries
    try:
        lines = HEARTBEAT_LOG.read_text().strip().split("\n")
        if len(lines) > 500:
            HEARTBEAT_LOG.write_text("\n".join(lines[-500:]) + "\n")
    except Exception:
        pass


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    daemon = "--daemon" in args

    while True:
        result = run_heartbeat()
        log_result(result)

        if as_json:
            print(json.dumps(result, indent=2))
        else:
            status = result["status"]
            symbol = "OK" if status == "HEARTBEAT_OK" else "!!"
            print(f"[{symbol}] {result['ts']} — {status}")
            for c in result["checks"]:
                mark = "+" if c.get("ok") else "-"
                msg = c.get("msg", "")
                extra = f" — {msg}" if msg else ""
                print(f"  [{mark}] {c['check']}{extra}")
            if result["p0_count"]:
                print(f"\n  P0 ALERTS: {result['p0_count']}")
            if result["p1_count"]:
                print(f"  P1 warnings: {result['p1_count']}")

        if not daemon:
            break
        time.sleep(1800)  # 30 minutes


if __name__ == "__main__":
    main()
