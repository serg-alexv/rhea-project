#!/usr/bin/env python3
"""
rex_burn.py — Track Rex's own token burn from Claude Code session logs.

No API needed. Reads the session JSONL directly.

Usage:
    python3 scripts/rex_burn.py                  # current/latest session
    python3 scripts/rex_burn.py --live            # auto-refresh every 15s
    python3 scripts/rex_burn.py --all             # all sessions today
    python3 scripts/rex_burn.py --session <uuid>  # specific session
"""

import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

SESSIONS_DIR = Path.home() / ".claude" / "projects" / "-Users-sa-rh-1"
OUT = Path(__file__).resolve().parent.parent / "opera" / "metrics" / "rex_burn.json"

# Pricing: Opus 4.6
# Input: $15/M tokens, Output: $75/M tokens
PRICE_IN = 15.0 / 1_000_000
PRICE_OUT = 75.0 / 1_000_000
CHARS_PER_TOKEN = 4  # rough estimate, conservative


def find_sessions(target_date: date = None) -> list[Path]:
    """Find session JSONL files, optionally filtered by date."""
    target = target_date or date.today()
    files = sorted(SESSIONS_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    if target_date:
        return [f for f in files if date.fromtimestamp(f.stat().st_mtime) == target]
    return files


def analyze_session(path: Path) -> dict:
    """Parse a session JSONL and compute token estimates."""
    stats = {
        "session_id": path.stem,
        "file": str(path),
        "file_size_mb": round(path.stat().st_size / 1024 / 1024, 2),
        "started": None,
        "last_activity": None,
        "records": 0,
        "user_chars": 0,
        "assistant_chars": 0,
        "tool_result_chars": 0,
        "system_chars": 0,
        "user_messages": 0,
        "assistant_messages": 0,
        "tool_calls": 0,
    }

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            stats["records"] += 1
            ts = rec.get("timestamp")
            if ts:
                if stats["started"] is None:
                    stats["started"] = ts
                stats["last_activity"] = ts

            msg = rec.get("message", {})
            role = msg.get("role", "")
            rec_type = rec.get("type", "")

            # Count content chars by role
            content = msg.get("content", "")
            if isinstance(content, list):
                char_count = sum(len(json.dumps(c)) for c in content)
            elif isinstance(content, str):
                char_count = len(content)
            else:
                char_count = len(str(content)) if content else 0

            if role == "user":
                stats["user_chars"] += char_count
                stats["user_messages"] += 1
            elif role == "assistant":
                stats["assistant_chars"] += char_count
                stats["assistant_messages"] += 1

            # Tool results (these are input tokens — Rex reads them)
            tool_result = rec.get("toolUseResult")
            if tool_result:
                if isinstance(tool_result, dict):
                    tr_content = tool_result.get("content", "")
                else:
                    tr_content = str(tool_result)
                if isinstance(tr_content, list):
                    stats["tool_result_chars"] += sum(len(json.dumps(c)) for c in tr_content)
                elif isinstance(tr_content, str):
                    stats["tool_result_chars"] += len(tr_content)
                stats["tool_calls"] += 1

            if rec_type == "system":
                stats["system_chars"] += char_count

    # Compute token estimates
    # Input = user messages + tool results + system prompts
    input_chars = stats["user_chars"] + stats["tool_result_chars"] + stats["system_chars"]
    output_chars = stats["assistant_chars"]

    stats["est_input_tokens"] = input_chars // CHARS_PER_TOKEN
    stats["est_output_tokens"] = output_chars // CHARS_PER_TOKEN
    stats["est_total_tokens"] = stats["est_input_tokens"] + stats["est_output_tokens"]
    stats["est_cost_usd"] = round(
        stats["est_input_tokens"] * PRICE_IN + stats["est_output_tokens"] * PRICE_OUT, 4
    )

    # Duration
    if stats["started"] and stats["last_activity"]:
        try:
            t0 = datetime.fromisoformat(stats["started"].replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(stats["last_activity"].replace("Z", "+00:00"))
            stats["duration_min"] = round((t1 - t0).total_seconds() / 60, 1)
            hours = (t1 - t0).total_seconds() / 3600
            if hours > 0:
                stats["burn_rate_tok_per_hour"] = round(stats["est_total_tokens"] / hours)
                stats["burn_rate_usd_per_hour"] = round(stats["est_cost_usd"] / hours, 4)
        except (ValueError, TypeError):
            pass

    return stats


def bar(value: float, max_val: float, width: int = 30) -> str:
    if max_val == 0:
        return ""
    filled = int(min(value / max_val, 1.0) * width)
    return "#" * filled + "." * (width - filled)


def render_terminal(sessions: list[dict]):
    total_tokens = sum(s["est_total_tokens"] for s in sessions)
    total_cost = sum(s["est_cost_usd"] for s in sessions)
    total_out = sum(s["est_output_tokens"] for s in sessions)

    print(f"\n  REX TOKEN BURN (Opus 4.6)")
    print(f"  {'='*58}")
    print(f"  Total: ~{total_tokens:,} tokens | ~${total_cost:.2f} | {len(sessions)} session(s)\n")

    for s in sessions:
        sid = s["session_id"][:8]
        dur = s.get("duration_min", 0)
        rate = s.get("burn_rate_usd_per_hour", 0)
        print(f"  [{sid}] {dur:>6.0f} min | {bar(s['est_cost_usd'], max(total_cost, 0.01))} ${s['est_cost_usd']:.2f}")
        print(f"           in={s['est_input_tokens']:>10,}  out={s['est_output_tokens']:>10,}  tools={s['tool_calls']}")
        if rate > 0:
            print(f"           burn: ${rate:.2f}/hr  |  {s.get('burn_rate_tok_per_hour', 0):,} tok/hr")
        print()

    if total_out > 0:
        print(f"  Output token share: {total_out/total_tokens*100:.1f}% (these cost 5x more)")
    print()


def save_json(sessions: list[dict]):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated": datetime.now().isoformat(),
        "pricing": {"input_per_M": 15.0, "output_per_M": 75.0, "model": "claude-opus-4-6"},
        "sessions": sessions,
        "totals": {
            "est_tokens": sum(s["est_total_tokens"] for s in sessions),
            "est_cost_usd": round(sum(s["est_cost_usd"] for s in sessions), 4),
            "sessions": len(sessions),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str) + "\n")


def live_mode(session_path: Path):
    try:
        while True:
            print("\033[2J\033[H", end="")
            stats = analyze_session(session_path)
            render_terminal([stats])
            save_json([stats])
            print(f"  [live — {session_path.stem[:8]} — Ctrl+C to stop]")
            time.sleep(15)
    except KeyboardInterrupt:
        print("\n  Stopped.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rex token burn tracker")
    parser.add_argument("--live", action="store_true", help="Auto-refresh")
    parser.add_argument("--all", action="store_true", help="All sessions today")
    parser.add_argument("--session", type=str, help="Specific session UUID")
    parser.add_argument("--date", type=str, help="YYYY-MM-DD")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else None

    if args.session:
        path = SESSIONS_DIR / f"{args.session}.jsonl"
        if not path.exists():
            print(f"  Session not found: {path}")
            sys.exit(1)
        if args.live:
            live_mode(path)
        else:
            stats = analyze_session(path)
            render_terminal([stats])
            save_json([stats])
    elif args.all:
        files = find_sessions(target or date.today())
        sessions = [analyze_session(f) for f in files]
        render_terminal(sessions)
        save_json(sessions)
    else:
        # Latest session
        files = find_sessions()
        if not files:
            print("  No sessions found.")
            sys.exit(1)
        path = files[0]
        if args.live:
            live_mode(path)
        else:
            stats = analyze_session(path)
            render_terminal([stats])
            save_json([stats])
            print(f"  Saved: {OUT}")
