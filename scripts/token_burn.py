#!/usr/bin/env python3
"""
token_burn.py — Who burned how many tokens today.

Live mode:  python3 scripts/token_burn.py --live
Daily log:  python3 scripts/token_burn.py
Yesterday:  python3 scripts/token_burn.py --date 2026-02-26
JSON out:   python3 scripts/token_burn.py --json
"""

import json
import sys
import time
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

LOGS = Path(__file__).resolve().parent.parent / "logs" / "bridge_calls.jsonl"
OUT = Path(__file__).resolve().parent.parent / "opera" / "metrics" / "token_burn.json"

# Agent = provider mapping (who owns which models)
AGENT_MAP = {
    "openai": "ORION",
    "gemini": "GEMINI",
    "anthropic": "REX",
    "deepseek": "GEMINI",      # Gemini pyramid uses DeepSeek workers
    "openrouter": "SHARED",    # shared pool
    "huggingface": "SHARED",
    "azure": "ORION",          # Orion pyramid uses Azure
}


def load_calls(target_date: date = None) -> list[dict]:
    if not LOGS.exists():
        return []
    target = target_date or date.today()
    target_str = target.isoformat()
    calls = []
    with open(LOGS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("timestamp", "").startswith(target_str):
                    calls.append(rec)
            except json.JSONDecodeError:
                continue
    return calls


def aggregate(calls: list[dict]) -> dict:
    agents = defaultdict(lambda: {
        "calls": 0, "tokens": 0, "prompt_tokens": 0,
        "completion_tokens": 0, "cost_usd": 0.0,
        "errors": 0, "models": defaultdict(int),
    })
    for c in calls:
        provider = c.get("provider", "unknown")
        agent = AGENT_MAP.get(provider, provider.upper())
        a = agents[agent]
        a["calls"] += 1
        a["tokens"] += c.get("total_tokens", 0)
        a["prompt_tokens"] += c.get("prompt_tokens", 0)
        a["completion_tokens"] += c.get("completion_tokens", 0)
        a["cost_usd"] += c.get("cost_usd", 0.0)
        if c.get("status") != "ok":
            a["errors"] += 1
        a["models"][c.get("model", "?")] += 1
    # Convert defaultdicts
    return {k: {**v, "models": dict(v["models"])} for k, v in agents.items()}


def bar(value: int, max_val: int, width: int = 40) -> str:
    if max_val == 0:
        return ""
    filled = int(value / max_val * width)
    return "#" * filled + "." * (width - filled)


def render_terminal(agg: dict, target_date: date):
    total_tokens = sum(a["tokens"] for a in agg.values())
    total_cost = sum(a["cost_usd"] for a in agg.values())
    total_calls = sum(a["calls"] for a in agg.values())
    max_tokens = max((a["tokens"] for a in agg.values()), default=1)

    print(f"\n  TOKEN BURN — {target_date.isoformat()}")
    print(f"  {'='*58}")
    print(f"  Total: {total_tokens:,} tokens | ${total_cost:.4f} | {total_calls} calls\n")

    # Sort by tokens descending
    for agent, data in sorted(agg.items(), key=lambda x: x[1]["tokens"], reverse=True):
        pct = (data["tokens"] / total_tokens * 100) if total_tokens else 0
        err = f" ({data['errors']} err)" if data["errors"] else ""
        print(f"  {agent:8s} {bar(data['tokens'], max_tokens)} {data['tokens']:>8,} tok  ${data['cost_usd']:.4f}  {pct:4.1f}%{err}")
        for model, count in sorted(data["models"].items(), key=lambda x: -x[1]):
            print(f"           {model:30s} x{count}")
    print()


def save_json(agg: dict, target_date: date):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": target_date.isoformat(),
        "generated": datetime.now().isoformat(),
        "agents": {},
        "totals": {
            "tokens": sum(a["tokens"] for a in agg.values()),
            "cost_usd": round(sum(a["cost_usd"] for a in agg.values()), 6),
            "calls": sum(a["calls"] for a in agg.values()),
        },
    }
    for agent, data in agg.items():
        payload["agents"][agent] = {
            "tokens": data["tokens"],
            "cost_usd": round(data["cost_usd"], 6),
            "calls": data["calls"],
            "errors": data["errors"],
            "prompt_tokens": data["prompt_tokens"],
            "completion_tokens": data["completion_tokens"],
            "top_model": max(data["models"], key=data["models"].get) if data["models"] else None,
        }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    return OUT


def live_mode(target_date: date):
    """Reprint every 10 seconds."""
    try:
        while True:
            print("\033[2J\033[H", end="")  # clear screen
            calls = load_calls(target_date)
            agg = aggregate(calls)
            render_terminal(agg, target_date)
            save_json(agg, target_date)
            print(f"  [live — refreshing every 10s, Ctrl+C to stop]")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n  Stopped.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Token burn per agent")
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--live", action="store_true", help="Auto-refresh every 10s")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else date.today()

    if args.live:
        live_mode(target)
    else:
        calls = load_calls(target)
        agg = aggregate(calls)
        if args.json:
            path = save_json(agg, target)
            print(json.dumps(json.loads(path.read_text()), indent=2))
        else:
            render_terminal(agg, target)
            save_json(agg, target)
            print(f"  Saved: {OUT}")
