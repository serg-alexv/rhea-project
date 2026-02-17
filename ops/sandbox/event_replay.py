#!/usr/bin/env /usr/bin/python3
"""
event_replay.py — Event Sourcing Replay + Projection Engine

Reads any JSONL event log, replays entries through user-defined projections,
and builds materialized views. Works with all Rhea JSONL files.

Core concepts:
  - Event: a JSONL line with at minimum {timestamp}
  - Projection: a pure function (state, event) -> state
  - Store: the engine that manages logs + projections + materialized state

Built-in projections:
  - relay_stats: message counts, latency, per-agent stats
  - chain_integrity: verify hash chain continuity
  - bridge_cost: per-provider cost tracking from bridge_calls.jsonl
  - dialogue_state: reconstruct dialogue convergence state
  - timeline: ordered event timeline across all logs

Usage:
  python3 event_replay.py replay ops/virtual-office/relay_mailbox.jsonl relay_stats
  python3 event_replay.py replay ops/virtual-office/relay_chain.jsonl chain_integrity
  python3 event_replay.py replay logs/bridge_calls.jsonl bridge_cost
  python3 event_replay.py replay-all                    # replay every known JSONL
  python3 event_replay.py timeline                      # global timeline
  python3 event_replay.py snapshot <log> <projection>   # save materialized view
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

OPS_DIR = Path(__file__).parent.parent / "virtual-office"
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
SNAPSHOTS_DIR = Path(__file__).parent / "replay_snapshots"


# ---------------------------------------------------------------------------
# Event loading
# ---------------------------------------------------------------------------

def load_events(path: Path) -> list[dict]:
    """Load a JSONL file, return list of dicts with _source metadata."""
    if not path.exists():
        return []
    events = []
    for i, line in enumerate(path.read_text().strip().split("\n")):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            e["_source"] = str(path)
            e["_line"] = i + 1
            events.append(e)
        except json.JSONDecodeError:
            events.append({"_source": str(path), "_line": i + 1, "_parse_error": True, "_raw": line[:200]})
    return events


def load_all_events() -> list[dict]:
    """Load events from all known JSONL files, sorted by timestamp."""
    sources = [
        OPS_DIR / "relay_mailbox.jsonl",
        OPS_DIR / "relay_acks.jsonl",
        OPS_DIR / "relay_chain.jsonl",
        OPS_DIR / "rex_pager_queue.jsonl",
        OPS_DIR / "knowledge_gaps.jsonl",
        LOGS_DIR / "bridge_calls.jsonl",
        LOGS_DIR / "firebase_calls.jsonl",
        LOGS_DIR / "tribunal_api_calls.jsonl",
    ]
    # Also glob for dialogue files
    if (OPS_DIR / "dialogues").exists():
        sources.extend(sorted((OPS_DIR / "dialogues").glob("*.jsonl")))

    all_events = []
    for src in sources:
        all_events.extend(load_events(src))

    # Sort by timestamp (best effort — not all events have one)
    def sort_key(e):
        ts = e.get("timestamp", "")
        if isinstance(ts, str) and ts:
            return ts
        return "9999"

    all_events.sort(key=sort_key)
    return all_events


# ---------------------------------------------------------------------------
# Projection registry
# ---------------------------------------------------------------------------

PROJECTIONS: dict[str, Callable] = {}


def projection(name: str):
    """Register a projection function."""
    def decorator(fn):
        PROJECTIONS[name] = fn
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Built-in projections
# ---------------------------------------------------------------------------

@projection("relay_stats")
def relay_stats(events: list[dict]) -> dict:
    """Build relay message statistics from mailbox/queue events."""
    state = {
        "total_messages": 0,
        "by_type": defaultdict(int),
        "by_source": defaultdict(int),
        "by_target": defaultdict(int),
        "by_priority": defaultdict(int),
        "by_status": defaultdict(int),
        "seq_range": [None, None],
    }
    for e in events:
        if e.get("_parse_error"):
            continue
        state["total_messages"] += 1
        state["by_type"][e.get("type", "unknown")] += 1
        state["by_source"][e.get("source", "unknown")] += 1
        state["by_target"][e.get("target", "unknown")] += 1
        state["by_priority"][e.get("priority", "none")] += 1
        state["by_status"][e.get("status", "unknown")] += 1

        seq = e.get("seq")
        if seq is not None:
            if state["seq_range"][0] is None or seq < state["seq_range"][0]:
                state["seq_range"][0] = seq
            if state["seq_range"][1] is None or seq > state["seq_range"][1]:
                state["seq_range"][1] = seq

    # Convert defaultdicts for JSON serialization
    for k in ["by_type", "by_source", "by_target", "by_priority", "by_status"]:
        state[k] = dict(state[k])
    return state


@projection("chain_integrity")
def chain_integrity(events: list[dict]) -> dict:
    """Verify hash chain continuity from relay_chain.jsonl."""
    state = {
        "entries": 0,
        "valid": True,
        "broken_at": None,
        "actors": set(),
        "event_types": defaultdict(int),
    }
    prev_hash = None
    for e in events:
        if e.get("_parse_error"):
            state["valid"] = False
            state["broken_at"] = e.get("_line", "?")
            break

        state["entries"] += 1
        state["actors"].add(e.get("actor", "?"))
        state["event_types"][e.get("event_type", "?")] += 1

        if prev_hash is not None:
            if e.get("prev_hash") != prev_hash:
                state["valid"] = False
                state["broken_at"] = e.get("_line", state["entries"])
                break

        # Verify self-hash (canonical JSON: sorted keys, compact separators)
        check = {k: v for k, v in e.items() if not k.startswith("_") and k != "event_hash"}
        content = json.dumps(check, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(content.encode()).hexdigest()
        if e.get("event_hash") != expected:
            state["valid"] = False
            state["broken_at"] = e.get("_line", state["entries"])
            break

        prev_hash = e.get("event_hash")

    state["actors"] = list(state["actors"])
    state["event_types"] = dict(state["event_types"])
    return state


@projection("bridge_cost")
def bridge_cost(events: list[dict]) -> dict:
    """Track API costs from bridge_calls.jsonl."""
    state = {
        "total_calls": 0,
        "total_tokens": 0,
        "by_provider": defaultdict(lambda: {"calls": 0, "tokens": 0, "errors": 0, "avg_latency": 0, "latencies": []}),
        "by_model": defaultdict(lambda: {"calls": 0, "tokens": 0}),
        "errors": 0,
        "time_range": [None, None],
    }
    for e in events:
        if e.get("_parse_error"):
            continue
        state["total_calls"] += 1
        provider = e.get("provider", "unknown")
        model = e.get("model", "unknown")
        tokens = e.get("tokens_used", 0) or 0
        latency = e.get("latency_s", 0) or 0
        error = e.get("error") or e.get("status") == "error"

        state["total_tokens"] += tokens
        prov = state["by_provider"][provider]
        prov["calls"] += 1
        prov["tokens"] += tokens
        prov["latencies"].append(latency)
        if error:
            prov["errors"] += 1
            state["errors"] += 1

        mod = state["by_model"][model]
        mod["calls"] += 1
        mod["tokens"] += tokens

        ts = e.get("timestamp", "")
        if ts:
            if state["time_range"][0] is None or ts < state["time_range"][0]:
                state["time_range"][0] = ts
            if state["time_range"][1] is None or ts > state["time_range"][1]:
                state["time_range"][1] = ts

    # Compute averages and clean up
    for prov_data in state["by_provider"].values():
        lats = prov_data.pop("latencies", [])
        prov_data["avg_latency"] = round(sum(lats) / len(lats), 3) if lats else 0

    state["by_provider"] = {k: dict(v) for k, v in state["by_provider"].items()}
    state["by_model"] = {k: dict(v) for k, v in state["by_model"].items()}
    return state


@projection("dialogue_state")
def dialogue_state(events: list[dict]) -> dict:
    """Reconstruct dialogue convergence state."""
    state = {
        "topic": None,
        "speakers": set(),
        "rounds": 0,
        "entries": 0,
        "by_type": defaultdict(int),
        "converged": False,
        "convergence_reason": "",
    }
    for e in events:
        if e.get("_parse_error"):
            continue
        state["entries"] += 1
        etype = e.get("type", "")
        state["by_type"][etype] += 1

        if etype == "meta" and state["topic"] is None:
            state["topic"] = e.get("content", "")
        elif etype != "meta":
            state["speakers"].add(e.get("speaker", "?"))

        r = e.get("round", 0)
        if r > state["rounds"]:
            state["rounds"] = r

    # Check convergence
    commits = [e for e in events if e.get("type") == "commit"]
    if commits:
        state["converged"] = True
        state["convergence_reason"] = f"commit by {commits[-1].get('speaker')}"
    else:
        agrees = [e for e in events if e.get("type") == "agree"]
        agreeing = set(e.get("speaker") for e in agrees)
        if len(agreeing) >= 2:
            state["converged"] = True
            state["convergence_reason"] = f"mutual agreement: {', '.join(agreeing)}"

    state["speakers"] = list(state["speakers"])
    state["by_type"] = dict(state["by_type"])
    return state


@projection("timeline")
def timeline(events: list[dict]) -> dict:
    """Build a unified timeline across all event sources."""
    entries = []
    for e in events:
        if e.get("_parse_error"):
            continue
        ts = e.get("timestamp", "")
        source = Path(e.get("_source", "?")).name
        actor = e.get("actor") or e.get("source") or e.get("speaker") or e.get("provider") or "?"
        etype = e.get("event_type") or e.get("type") or "?"
        summary = ""

        # Extract meaningful summary
        if "body" in e.get("payload", {}):
            summary = e["payload"]["body"][:80]
        elif "content" in e:
            summary = e["content"][:80] if isinstance(e["content"], str) else ""
        elif "model" in e:
            summary = f"{e.get('model', '?')} {e.get('tokens_used', 0)}tok"

        entries.append({
            "time": ts[:19] if ts else "?",
            "source_file": source,
            "actor": actor,
            "type": etype,
            "summary": summary,
        })

    return {"count": len(entries), "entries": entries}


# ---------------------------------------------------------------------------
# Replay engine
# ---------------------------------------------------------------------------

def replay(log_path: Path, projection_name: str) -> dict:
    """Load events from a JSONL and run a projection."""
    if projection_name not in PROJECTIONS:
        print(f"Unknown projection: {projection_name}")
        print(f"Available: {', '.join(PROJECTIONS.keys())}")
        sys.exit(1)

    events = load_events(log_path)
    if not events:
        print(f"No events in {log_path}")
        return {}

    result = PROJECTIONS[projection_name](events)
    return result


def replay_all() -> dict:
    """Replay all known JSONL files with appropriate projections."""
    results = {}

    # Relay mailbox → relay_stats
    mb = OPS_DIR / "relay_mailbox.jsonl"
    if mb.exists():
        results["relay_stats"] = replay(mb, "relay_stats")

    # Chain → integrity
    ch = OPS_DIR / "relay_chain.jsonl"
    if ch.exists():
        results["chain_integrity"] = replay(ch, "chain_integrity")

    # Bridge calls → cost
    bc = LOGS_DIR / "bridge_calls.jsonl"
    if bc.exists():
        results["bridge_cost"] = replay(bc, "bridge_cost")

    # Dialogues → state
    dlg_dir = OPS_DIR / "dialogues"
    if dlg_dir.exists():
        for f in sorted(dlg_dir.glob("*.jsonl")):
            results[f"dialogue_{f.stem}"] = replay(f, "dialogue_state")

    # Global timeline
    all_events = load_all_events()
    results["timeline_count"] = len(all_events)

    return results


def save_snapshot(result: dict, name: str):
    """Save materialized projection to disk."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = SNAPSHOTS_DIR / f"{name}_{ts}.json"
    path.write_text(json.dumps(result, indent=2, default=str))
    print(f"Snapshot saved: {path}")
    return path


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def display_result(name: str, result: dict):
    """Pretty-print a projection result."""
    print(f"\n{'=' * 60}")
    print(f"  PROJECTION: {name}")
    print(f"{'=' * 60}")

    if name == "timeline":
        entries = result.get("entries", [])
        print(f"  Total events: {result.get('count', 0)}\n")
        for e in entries:
            print(f"  {e['time']}  [{e['source_file']:<30}] {e['actor']:<8} {e['type']:<20} {e['summary']}")
    else:
        print(json.dumps(result, indent=2, default=str))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "replay":
        if len(sys.argv) < 4:
            print("Usage: event_replay.py replay <jsonl_path> <projection>")
            print(f"Projections: {', '.join(PROJECTIONS.keys())}")
            sys.exit(1)
        log_path = Path(sys.argv[2])
        proj_name = sys.argv[3]
        result = replay(log_path, proj_name)
        display_result(proj_name, result)

    elif cmd == "replay-all":
        results = replay_all()
        for name, result in results.items():
            if isinstance(result, dict):
                display_result(name, result)
            else:
                print(f"\n  {name}: {result}")
        save_snapshot(results, "replay_all")

    elif cmd == "timeline":
        all_events = load_all_events()
        result = PROJECTIONS["timeline"](all_events)
        display_result("timeline", result)

    elif cmd == "snapshot":
        if len(sys.argv) < 4:
            print("Usage: event_replay.py snapshot <jsonl_path> <projection>")
            sys.exit(1)
        log_path = Path(sys.argv[2])
        proj_name = sys.argv[3]
        result = replay(log_path, proj_name)
        display_result(proj_name, result)
        save_snapshot(result, proj_name)

    elif cmd == "projections":
        print("Available projections:")
        for name, fn in PROJECTIONS.items():
            doc = (fn.__doc__ or "").strip().split("\n")[0]
            print(f"  {name:<20} {doc}")

    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
