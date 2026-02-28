#!/usr/bin/env python3
"""
rhea_queue_guard.py — queue/log overflow maintainer with compact archiving.

Functions:
  - monitor critical JSONL logs
  - compact overflow into gzip archives
  - keep hot logs short and fast
  - publish queue health pulse for UI/applets
"""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "queue_guard"
STATE_FILE = STATE_DIR / "state.json"
HEALTH_FILE = ROOT / "opera" / "metrics" / "queue_health.json"
TRACE_FILE = ROOT / "opera" / "metrics" / "queue_guard_trace.jsonl"
COMPACT_ROOT = ROOT / "opera" / "metrics" / "compact"

WATCH = [
    {"name": "task_queue", "path": ROOT / "opera" / "tasks" / "queue.jsonl", "max_lines": 4000, "keep_lines": 2000},
    {
        "name": "relay_mailbox",
        "path": ROOT / "opera" / "ops" / "virtual-office" / "relay_mailbox.jsonl",
        "max_lines": 8000,
        "keep_lines": 3000,
    },
    {
        "name": "relay_acks",
        "path": ROOT / "opera" / "ops" / "virtual-office" / "relay_acks.jsonl",
        "max_lines": 8000,
        "keep_lines": 3000,
    },
    {"name": "bridge_calls", "path": ROOT / "logs" / "bridge_calls.jsonl", "max_lines": 10000, "keep_lines": 4000},
    {"name": "radio_feed", "path": ROOT / "opera" / "metrics" / "radio_feed.jsonl", "max_lines": 15000, "keep_lines": 5000},
    {"name": "ndi_trace", "path": ROOT / "opera" / "metrics" / "ndi_trace.jsonl", "max_lines": 8000, "keep_lines": 2000},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    COMPACT_ROOT.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"runs": 0, "compactions": 0, "last_run": None, "last_compaction": None, "totals": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"runs": 0, "compactions": 0, "last_run": None, "last_compaction": None, "totals": {}}


def save_state(state: dict) -> None:
    state["last_run"] = now_iso()
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def _safe_read_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _archive_path(name: str) -> Path:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return COMPACT_ROOT / f"{name}.{day}.jsonl.gz"


def _append_gzip(path: Path, lines: List[str]) -> None:
    if not lines:
        return
    with gzip.open(path, "at", encoding="utf-8") as f:
        for line in lines:
            f.write(line)
            f.write("\n")


def _write_lines(path: Path, lines: List[str]) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = ("\n".join(lines) + "\n") if lines else ""
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def append_trace(event: dict) -> None:
    payload = {"ts": now_iso(), **event}
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def notify(text: str, sound: str = "Hero") -> None:
    msg = text.replace("\\", "\\\\").replace('"', "'")
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{msg}" with title "RHEA QUEUE" sound name "{sound}"'],
            check=False,
            timeout=5,
        )
    except Exception:
        pass


def compact_one(cfg: dict, force: bool = False) -> dict:
    path: Path = cfg["path"]
    name = str(cfg["name"])
    max_lines = int(cfg["max_lines"])
    keep_lines = int(cfg["keep_lines"])
    lines = _safe_read_lines(path)
    line_count = len(lines)
    size_bytes = int(path.stat().st_size) if path.exists() else 0

    overflow = max(0, line_count - keep_lines) if force else max(0, line_count - max_lines)
    changed = False
    archived = 0

    if overflow > 0:
        archived_lines = lines[:overflow]
        hot_lines = lines[overflow:]
        _append_gzip(_archive_path(name), archived_lines)
        _write_lines(path, hot_lines)
        changed = True
        archived = overflow
        lines = hot_lines
        line_count = len(lines)
        size_bytes = int(path.stat().st_size) if path.exists() else 0

    return {
        "name": name,
        "path": str(path),
        "line_count": line_count,
        "size_bytes": size_bytes,
        "max_lines": max_lines,
        "keep_lines": keep_lines,
        "overflow_archived": archived,
        "changed": changed,
    }


def build_health(rows: List[dict], state: dict) -> dict:
    warnings: List[str] = []
    total_lines = 0
    total_bytes = 0
    changed = 0
    archived = 0
    for r in rows:
        total_lines += int(r["line_count"])
        total_bytes += int(r["size_bytes"])
        if r["changed"]:
            changed += 1
        archived += int(r["overflow_archived"])
        if int(r["line_count"]) > int(r["max_lines"]):
            warnings.append(f"{r['name']}:line_count>{r['max_lines']}")

    risk = "ok"
    if warnings:
        risk = "warn"
    if len(warnings) >= 3:
        risk = "critical"

    summary = f"risk={risk} files={len(rows)} changed={changed} archived={archived} lines={total_lines} bytes={total_bytes}"
    return {
        "ts": now_iso(),
        "risk": risk,
        "summary": summary,
        "totals": {"files": len(rows), "lines": total_lines, "bytes": total_bytes, "changed": changed, "archived": archived},
        "warnings": warnings,
        "files": rows,
        "runs": int(state.get("runs", 0)),
        "compactions": int(state.get("compactions", 0)),
        "last_compaction": state.get("last_compaction"),
    }


def run_pass(state: dict, force: bool = False, do_notify: bool = False, sound: str = "Hero") -> dict:
    rows = [compact_one(cfg, force=force) for cfg in WATCH]
    changed = any(r["changed"] for r in rows)
    archived = sum(int(r["overflow_archived"]) for r in rows)
    old_risk = str(state.get("last_risk", "ok"))

    state["runs"] = int(state.get("runs", 0)) + 1
    if changed:
        state["compactions"] = int(state.get("compactions", 0)) + 1
        state["last_compaction"] = now_iso()
    totals = state.setdefault("totals", {})
    totals["archived_lines"] = int(totals.get("archived_lines", 0)) + archived
    totals["last_archived"] = archived

    health = build_health(rows, state)
    HEALTH_FILE.write_text(json.dumps(health, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state["last_risk"] = health["risk"]
    append_trace(
        {
            "event": "queue_health",
            "risk": health["risk"],
            "summary": health["summary"],
            "changed_files": health["totals"]["changed"],
            "archived": health["totals"]["archived"],
            "notify": bool(health["risk"] != "ok" or health["totals"]["archived"] > 0),
        }
    )
    if do_notify:
        risk_up = old_risk != health["risk"] and health["risk"] in {"warn", "critical"}
        compact_happened = health["totals"]["archived"] > 0
        if risk_up or compact_happened:
            notify(health["summary"], sound=sound)
    save_state(state)
    return health


def cmd_once(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    health = run_pass(state, force=args.force, do_notify=args.notify, sound=args.sound)
    print(json.dumps({"status": "ok", "summary": health["summary"], "ts": now_iso()}))
    return 0


def cmd_compact(_args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    health = run_pass(state, force=True)
    print(json.dumps({"status": "compacted", "summary": health["summary"], "ts": now_iso()}))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    interval = max(5, int(args.interval))
    while True:
        health = run_pass(state, force=False, do_notify=args.notify, sound=args.sound)
        if args.echo:
            print(health["summary"])
        time.sleep(interval)


def cmd_status(_args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    out = {
        "state_file": str(STATE_FILE),
        "health_file": str(HEALTH_FILE),
        "compact_dir": str(COMPACT_ROOT),
        "trace_file": str(TRACE_FILE),
        "last_run": state.get("last_run"),
        "runs": state.get("runs", 0),
        "compactions": state.get("compactions", 0),
        "last_compaction": state.get("last_compaction"),
        "totals": state.get("totals", {}),
    }
    if HEALTH_FILE.exists():
        try:
            out["health"] = json.loads(HEALTH_FILE.read_text(encoding="utf-8"))
        except Exception:
            out["health"] = "invalid"
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    ensure_dirs()
    n = max(1, int(args.n))
    if not HEALTH_FILE.exists():
        print(f"health missing: {HEALTH_FILE}")
        return 0
    print(HEALTH_FILE.read_text(encoding="utf-8", errors="replace").strip())
    compact_files = sorted(COMPACT_ROOT.glob("*.jsonl.gz"))
    print(json.dumps({"compact_files": [str(x) for x in compact_files[-n:]]}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Rhea queue/log overflow guard")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_once = sub.add_parser("once", help="single pass (compact only on overflow)")
    sp_once.add_argument("--force", action="store_true", help="force compaction to keep_lines")
    sp_once.add_argument("--notify", action="store_true", help="send macOS notification on risk/compaction")
    sp_once.add_argument("--sound", default="Hero", help="notification sound")
    sp_once.set_defaults(func=cmd_once)

    sp_compact = sub.add_parser("compact", help="force compact now")
    sp_compact.set_defaults(func=cmd_compact)

    sp_run = sub.add_parser("run", help="continuous guard loop")
    sp_run.add_argument("--interval", type=int, default=30, help="poll interval seconds")
    sp_run.add_argument("--echo", action="store_true", help="echo summary each loop")
    sp_run.add_argument("--notify", action="store_true", help="send macOS notifications on risk/compaction")
    sp_run.add_argument("--sound", default="Hero", help="notification sound")
    sp_run.set_defaults(func=cmd_run)

    sp_status = sub.add_parser("status", help="show state + last health pulse")
    sp_status.set_defaults(func=cmd_status)

    sp_tail = sub.add_parser("tail", help="show health + recent compact archives")
    sp_tail.add_argument("-n", type=int, default=10, help="recent compact file count")
    sp_tail.set_defaults(func=cmd_tail)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
