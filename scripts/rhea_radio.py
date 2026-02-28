#!/usr/bin/env python3
"""
rhea_radio.py — unified "radio frequency" for agent work signals.

Streams key events from:
  - virtual office relay mailbox/acks
  - bridge call log (model calls)
  - task queue changes

Outputs:
  - append-only feed log: opera/metrics/radio_feed.jsonl
  - optional macOS notifications (deduplicated)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "radio"
STATE_FILE = STATE_DIR / "state.json"
FEED_FILE = ROOT / "opera" / "metrics" / "radio_feed.jsonl"

SOURCES = {
    "relay_mailbox": ROOT / "opera" / "ops" / "virtual-office" / "relay_mailbox.jsonl",
    "relay_acks": ROOT / "opera" / "ops" / "virtual-office" / "relay_acks.jsonl",
    "bridge_calls": ROOT / "logs" / "bridge_calls.jsonl",
    "task_queue": ROOT / "opera" / "tasks" / "queue.jsonl",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    FEED_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"cursors": {}, "notify_cache": {}, "last_run": None}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"cursors": {}, "notify_cache": {}, "last_run": None}


def save_state(state: dict) -> None:
    state["last_run"] = now_iso()
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def _cursor_for(state: dict, path: Path) -> dict:
    return state.setdefault("cursors", {}).get(str(path), {"inode": 0, "offset": 0})


def _set_cursor(state: dict, path: Path, inode: int, offset: int) -> None:
    state.setdefault("cursors", {})[str(path)] = {"inode": inode, "offset": offset}


def read_new_lines(path: Path, state: dict) -> List[str]:
    if not path.exists():
        return []
    cur = _cursor_for(state, path)
    st = path.stat()
    inode = int(getattr(st, "st_ino", 0))
    offset = int(cur.get("offset", 0))
    prev_inode = int(cur.get("inode", 0))
    if prev_inode != inode or offset > st.st_size:
        offset = 0

    lines: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        f.seek(offset)
        for line in f:
            lines.append(line.rstrip("\n"))
        new_offset = f.tell()
    _set_cursor(state, path, inode, new_offset)
    return lines


def _short(text: str, n: int = 120) -> str:
    x = " ".join((text or "").split())
    return x if len(x) <= n else (x[: n - 1] + "…")


def parse_relay_mailbox(obj: dict) -> Optional[dict]:
    seq = obj.get("seq")
    if seq is None:
        return None
    priority = str(obj.get("priority", "P1"))
    source = str(obj.get("source", "?"))
    target = str(obj.get("target", "?"))
    body = ""
    payload = obj.get("payload", {})
    if isinstance(payload, dict):
        body = str(payload.get("body", ""))
    text = f"[relay#{seq} {priority}] {source}->{target}: {_short(body)}"
    level = "critical" if priority == "P0" else ("normal" if priority == "P1" else "info")
    return {
        "event_id": f"relay:{seq}",
        "source": "relay_mailbox",
        "text": text,
        "level": level,
        "notify": priority in {"P0", "P1"},
    }


def parse_relay_ack(obj: dict) -> Optional[dict]:
    msg_id = str(obj.get("message_id", "")).strip()
    if not msg_id:
        return None
    target = str(obj.get("target", "?"))
    text = f"[ack] {target} <= {msg_id[:12]}"
    return {
        "event_id": f"ack:{msg_id}",
        "source": "relay_acks",
        "text": text,
        "level": "info",
        "notify": False,
    }


def parse_bridge_call(obj: dict) -> Optional[dict]:
    req_id = str(obj.get("request_id", "")).strip()
    if not req_id:
        return None
    status = str(obj.get("status", ""))
    provider = str(obj.get("provider", "?"))
    model = str(obj.get("model", "?"))
    agent = str(obj.get("agent_id", "unknown"))
    tokens = int(obj.get("total_tokens", 0) or 0)
    cost = float(obj.get("cost_usd", 0.0) or 0.0)

    if status.lower() == "ok":
        text = f"[call ok] {agent} {provider}/{model} tok={tokens} cost=${cost:.4f}"
        level = "info"
        notify = False
    else:
        err = _short(str(obj.get("error_short", "")), n=90)
        text = f"[call {status}] {agent} {provider}/{model}: {err}"
        level = "warn"
        notify = True
    return {
        "event_id": f"call:{req_id}",
        "source": "bridge_calls",
        "text": text,
        "level": level,
        "notify": notify,
    }


def parse_task_queue(obj: dict) -> Optional[dict]:
    action = str(obj.get("action", "")).strip()
    task_id = str(obj.get("id", "")).strip()
    if not action:
        return None
    title = _short(str(obj.get("title", "")), n=90)
    result = _short(str(obj.get("result", "")), n=90)
    content = title or result or _short(str(obj), n=90)
    text = f"[task {action}] {task_id} {content}".strip()
    notify = action in {"add", "complete", "claim", "blocked"}
    level = "normal" if notify else "info"
    ev_key = f"{obj.get('ts', '')}:{task_id}:{action}"
    return {
        "event_id": f"task:{ev_key}",
        "source": "task_queue",
        "text": text,
        "level": level,
        "notify": notify,
    }


PARSERS: Dict[str, Callable[[dict], Optional[dict]]] = {
    "relay_mailbox": parse_relay_mailbox,
    "relay_acks": parse_relay_ack,
    "bridge_calls": parse_bridge_call,
    "task_queue": parse_task_queue,
}


def append_feed(event: dict) -> None:
    payload = {
        "ts": now_iso(),
        "source": event["source"],
        "level": event["level"],
        "text": event["text"],
        "event_id": event["event_id"],
    }
    with FEED_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _osa_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace('"', "'")


def _should_notify(state: dict, event_id: str, cooldown_s: int) -> bool:
    cache = state.setdefault("notify_cache", {})
    now = int(time.time())
    last = int(cache.get(event_id, 0))
    if now - last < cooldown_s:
        return False
    cache[event_id] = now
    # prune old keys
    cutoff = now - 3600
    stale = [k for k, ts in cache.items() if int(ts) < cutoff]
    for k in stale:
        cache.pop(k, None)
    return True


def notify_event(event: dict, sound: str = "Hero") -> None:
    title = "RHEA RADIO"
    msg = _osa_escape(event.get("text", ""))
    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                f'display notification "{msg}" with title "{title}" sound name "{sound}"',
            ],
            timeout=5,
            check=False,
        )
    except Exception:
        pass


def process_once(
    state: dict,
    notify: bool,
    notify_all: bool,
    notify_cooldown_s: int,
    sound: str,
    echo: bool,
) -> int:
    emitted = 0
    for source_name, path in SOURCES.items():
        lines = read_new_lines(path, state)
        if not lines:
            continue
        parser = PARSERS[source_name]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            event = parser(obj)
            if not event:
                continue
            append_feed(event)
            emitted += 1
            if echo:
                print(event["text"])
            wants_notify = bool(event.get("notify", False))
            if notify and (notify_all or wants_notify):
                if _should_notify(state, str(event["event_id"]), notify_cooldown_s):
                    notify_event(event, sound=sound)
    return emitted


def cmd_once(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    emitted = process_once(
        state=state,
        notify=args.notify,
        notify_all=args.notify_all,
        notify_cooldown_s=args.notify_cooldown,
        sound=args.sound,
        echo=args.echo,
    )
    save_state(state)
    print(json.dumps({"status": "ok", "emitted": emitted, "ts": now_iso()}))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    interval = max(1, int(args.interval))
    while True:
        emitted = process_once(
            state=state,
            notify=args.notify,
            notify_all=args.notify_all,
            notify_cooldown_s=args.notify_cooldown,
            sound=args.sound,
            echo=args.echo,
        )
        save_state(state)
        if args.heartbeat and emitted == 0:
            print(f"[radio] idle heartbeat {now_iso()}")
        time.sleep(interval)


def cmd_status(_args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    cursors = state.get("cursors", {})
    notify_cache = state.get("notify_cache", {})
    out = {
        "state_file": str(STATE_FILE),
        "feed_file": str(FEED_FILE),
        "last_run": state.get("last_run"),
        "sources": {k: str(v) for k, v in SOURCES.items()},
        "cursor_count": len(cursors),
        "notify_cache_count": len(notify_cache),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    ensure_dirs()
    n = max(1, int(args.n))
    if not FEED_FILE.exists():
        print(f"feed missing: {FEED_FILE}")
        return 0
    lines = FEED_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-n:]:
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="RHEA radio stream daemon")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--notify", action="store_true", help="send macOS notifications")
        sp.add_argument("--notify-all", action="store_true", help="notify for every event (not only high-signal)")
        sp.add_argument("--notify-cooldown", type=int, default=45, help="dedup cooldown in seconds")
        sp.add_argument("--sound", default="Hero", help="macOS notification sound")
        sp.add_argument("--echo", action="store_true", help="echo events to stdout")

    sp_once = sub.add_parser("once", help="process updates once")
    add_common_flags(sp_once)
    sp_once.set_defaults(func=cmd_once)

    sp_run = sub.add_parser("run", help="run continuous stream loop")
    sp_run.add_argument("--interval", type=int, default=2, help="poll interval seconds")
    sp_run.add_argument("--heartbeat", action="store_true", help="print heartbeat while idle")
    add_common_flags(sp_run)
    sp_run.set_defaults(func=cmd_run)

    sp_status = sub.add_parser("status", help="show daemon state")
    sp_status.set_defaults(func=cmd_status)

    sp_tail = sub.add_parser("tail", help="print last feed entries")
    sp_tail.add_argument("-n", type=int, default=40, help="line count")
    sp_tail.set_defaults(func=cmd_tail)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
