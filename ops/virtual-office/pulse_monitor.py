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
OFFICE_CANDIDATES = (
    HERE / "OFFICE.md",
    REPO / "team" / "OFFICE.md",
    REPO / "teams" / "OFFICE.md",
)
DEFAULT_SENDER = "MIKA"
DEFAULT_TARGETS = ("REX", "GPT", "LEAD", "ORION", "B2", "COWORK", "TEAMLEAD")


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


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def _read_model_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    lines = path.read_text().splitlines()
    start = -1
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("| desk |") and "| model |" in line.lower():
            start = i + 2
            break
    if start < 0:
        return {}
    models: dict[str, str] = {}
    for line in lines[start:]:
        row = line.strip()
        if not row.startswith("|"):
            break
        cols = [c.strip() for c in row.strip("|").split("|")]
        if len(cols) < 3:
            continue
        desk = cols[0].upper()
        model = cols[2]
        if not desk or desk in {"DESK", "—", "-"}:
            continue
        if model:
            models[desk] = model
    return models


def _read_model_map_sources(paths: tuple[Path, ...]) -> dict[str, str]:
    # Merge model maps from all existing office files; later files override earlier.
    merged: dict[str, str] = {}
    for path in paths:
        if path.exists():
            merged.update(_read_model_map(path))
    return merged


def gather() -> dict:
    mailbox = HERE / "relay_mailbox.jsonl"
    acks = HERE / "relay_acks.jsonl"
    chain = HERE / "relay_chain.jsonl"
    seq = (HERE / "relay_seq.txt").read_text().strip() if (HERE / "relay_seq.txt").exists() else "?"

    total, pending = 0, 0
    by_target: Counter[str] = Counter()
    mailbox_rows = _read_jsonl(mailbox)
    ack_rows = _read_jsonl(acks)
    acked_ids = {str(row.get("message_id")) for row in ack_rows if row.get("message_id")}

    total = len(mailbox_rows)
    for msg in mailbox_rows:
        msg_id = str(msg.get("id", ""))
        if msg_id and msg_id in acked_ids:
            continue
        pending += 1
        by_target[msg.get("target", "?")] += 1
    acked = max(0, total - pending)

    last_chain = "n/a"
    if chain.exists():
        for line in reversed(chain.read_text().splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            age = _ts_to_age_minutes(obj.get("timestamp", ""))
            last_chain = f"{age:.1f}m ago" if age >= 0 else "unknown"
            break

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
    model_map = _read_model_map_sources(OFFICE_CANDIDATES)

    return {
        "seq": seq,
        "total": total,
        "pending": pending,
        "acked": acked,
        "by_target": by_target,
        "last_chain": last_chain,
        "leases": leases,
        "last_failure": last_failure,
        "model_map": model_map,
    }


def run_action_detail(args: list[str]) -> tuple[int, str]:
    try:
        out = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=12, check=False)
        text = (out.stdout or out.stderr or "").strip().splitlines()
        return out.returncode, (text[0] if text else "ok")
    except Exception as exc:
        return 1, f"error: {exc}"


def run_action(args: list[str]) -> str:
    _code, line = run_action_detail(args)
    return line


def build_send_cmd(sender: str, target: str, body: str, with_params: bool) -> list[str]:
    cmd = ["python3", "ops/rex_pager.py", "send", sender, target, body]
    if with_params:
        cmd.extend(["--priority", "P1", "--ttl", "86400"])
    return cmd


def discover_targets(data: dict, sender: str) -> list[str]:
    targets = {t for t in DEFAULT_TARGETS}
    for agent, _token, _secs in data.get("leases", []):
        targets.add(str(agent).upper())
    for target in data.get("by_target", {}):
        targets.add(str(target).upper())
    sender_norm = sender.upper()
    return sorted(t for t in targets if t and t != sender_norm)


def prompt_line(stdscr: "curses._CursesWindow", prompt: str) -> str:
    h, w = stdscr.getmaxyx()
    y = max(0, h - 2)
    safe_add(stdscr, y, 0, " " * max(0, w - 1))
    safe_add(stdscr, y, 0, prompt)
    stdscr.refresh()
    x = min(max(0, len(prompt)), max(0, w - 2))
    max_len = max(1, w - x - 2)
    try:
        stdscr.nodelay(False)
        curses.echo()
        try:
            curses.curs_set(1)
        except curses.error:
            pass
        raw = stdscr.getstr(y, x, max_len)
        text = raw.decode("utf-8", "ignore").strip() if raw else ""
    except Exception:
        text = ""
    finally:
        curses.noecho()
        stdscr.nodelay(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        safe_add(stdscr, y, 0, " " * max(0, w - 1))
    return text


def draw(stdscr: "curses._CursesWindow") -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    last_action = "ready"
    sender = DEFAULT_SENDER
    send_with_params = True
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
        model_map = data.get("model_map", {})
        for target, cnt in data["by_target"].most_common(8):
            model = model_map.get(str(target).upper(), "?")
            safe_add(stdscr, row, 2, f"- {target:8} ({model}): {cnt}")
            row += 1
        row += 1
        safe_add(stdscr, row, 0, "Leases:")
        row += 1
        for agent, token, secs in data["leases"][:8]:
            state = "OK" if secs > 0 else "EXPIRED"
            model = model_map.get(str(agent).upper(), "?")
            safe_add(stdscr, row, 2, f"- {agent:8} ({model}) token={token:<4} expires_in={secs:>6}s {state}")
            row += 1
        row += 1
        safe_add(
            stdscr,
            row,
            0,
            "Keys: [r] wake REX  [g] drain GPT  [s] status  [m] send  [b] broadcast  [u] sender  [p] params  [q] quit",
        )
        params_checkbox = "[x]" if send_with_params else "[ ]"
        safe_add(stdscr, row + 1, 0, f"sender={sender}  params={params_checkbox}  last action: {last_action}")
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
        elif key in (ord("u"), ord("U")):
            new_sender = prompt_line(stdscr, f"Sender [{sender}]: ")
            if new_sender:
                sender = new_sender.upper()
                last_action = f"sender updated to {sender}"
            else:
                last_action = "sender unchanged"
        elif key in (ord("p"), ord("P")):
            send_with_params = not send_with_params
            mode = "on" if send_with_params else "off"
            last_action = f"send params {mode}"
        elif key in (ord("m"), ord("M")):
            hint = ",".join(discover_targets(data, sender)[:6])
            target = prompt_line(stdscr, f"Target [{hint}]: ").upper()
            if target:
                body = prompt_line(stdscr, f"Message to {target}: ")
                if body:
                    last_action = run_action(build_send_cmd(sender, target, body, send_with_params))
                else:
                    last_action = "send canceled: empty message"
            else:
                last_action = "send canceled: no target"
        elif key in (ord("b"), ord("B")):
            body = prompt_line(stdscr, "Broadcast message: ")
            if not body:
                last_action = "broadcast canceled: empty message"
            else:
                targets = discover_targets(data, sender)
                sent, failed = 0, 0
                for target in targets:
                    if (REPO / "STOP").exists():
                        last_action = f"broadcast stopped by STOP ({sent}/{len(targets)})"
                        break
                    code, _line = run_action_detail(
                        build_send_cmd(sender, target, body, send_with_params)
                    )
                    if code == 0:
                        sent += 1
                    else:
                        failed += 1
                else:
                    last_action = f"broadcast complete: sent={sent} failed={failed}"
        time.sleep(0.75)


if __name__ == "__main__":
    curses.wrapper(draw)
