#!/usr/bin/env python3
"""
prompt_bus.py — Cross-agent prompt event bus.

Every user prompt to ANY model → captured here → visible to ALL agents.
Each agent reads unseen events on boot and generates reactive actions.

Event flow:
  User→Rex:    UserPromptSubmit hook → prompt_bus.py capture
  User→Orion:  Orion system prompt → writes relay → prompt_bus.py ingest
  User→Gemini: API wrapper → prompt_bus.py capture

Usage:
    # Capture a prompt event (called from hooks)
    python3 src/prompt_bus.py capture --agent rex --prompt "build iOS app"

    # Capture from stdin (for hook piping)
    echo '{"prompt":"..."}' | python3 src/prompt_bus.py capture --agent rex --stdin

    # Show unseen events for an agent
    python3 src/prompt_bus.py unseen --for orion

    # Generate triggers from unseen events
    python3 src/prompt_bus.py triggers --for orion

    # Ingest relay files (Orion→bus)
    python3 src/prompt_bus.py ingest-relays

    # Show recent events
    python3 src/prompt_bus.py tail [N]
"""

import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUS_LOG = _PROJECT_ROOT / "opera" / "events" / "prompt_bus.jsonl"
CURSORS_DIR = _PROJECT_ROOT / "opera" / "events" / "cursors"
RELAY_INBOX = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "inbox"

# --- Action mapping: keyword patterns → agent reactions ---
# When Rex gets a prompt about X, what should Orion/Gemini do?
REACTION_RULES = [
    {
        "keywords": ["ui", "frontend", "atlas", "component", "css", "layout", "panel"],
        "reactor": "orion",
        "action": "sync_ui_context",
        "description": "UI work detected — Orion should sync frontend state",
    },
    {
        "keywords": ["deploy", "prod", "ship", "release", "cloud run"],
        "reactor": "orion",
        "action": "pre_deploy_check",
        "description": "Deploy intent — Orion run build verification",
    },
    {
        "keywords": ["bridge", "model", "provider", "tier", "token"],
        "reactor": "gemini",
        "action": "cost_impact_check",
        "description": "Bridge/model change — Gemini verify cost impact",
    },
    {
        "keywords": ["aletheia", "proof", "hypothesis", "verify"],
        "reactor": "gemini",
        "action": "proof_sync",
        "description": "Aletheia activity — Gemini sync proof store",
    },
    {
        "keywords": ["bug", "fix", "error", "fail", "broken", "crash"],
        "reactor": "orion",
        "action": "regression_watch",
        "description": "Bug context — Orion set regression watch",
    },
    {
        "keywords": ["ios", "swift", "preview", "mobile", "app"],
        "reactor": "orion",
        "action": "ios_sync",
        "description": "iOS work — Orion sync WebView contract",
    },
    {
        "keywords": ["task", "queue", "priority", "plan", "sprint"],
        "reactor": "shared",
        "action": "task_reindex",
        "description": "Task planning — reindex task queue",
    },
    {
        "keywords": ["memory", "feed", "context", "boot", "compact"],
        "reactor": "shared",
        "action": "feed_regen",
        "description": "Memory work — regenerate compact feed",
    },
]


def capture(agent: str, prompt: str, meta: dict = None) -> dict:
    """Capture a prompt event to the bus."""
    BUS_LOG.parent.mkdir(parents=True, exist_ok=True)

    # Truncate long prompts for the bus (full text stays in session)
    summary = prompt[:200].strip()
    if len(prompt) > 200:
        summary += "..."

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent.lower(),
        "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:12],
        "summary": summary,
        "char_len": len(prompt),
        "triggers": _match_triggers(prompt, agent),
    }
    if meta:
        event["meta"] = meta

    with open(BUS_LOG, "a") as f:
        f.write(json.dumps(event) + "\n")

    return event


def get_cursor(agent: str) -> int:
    """Get the last-seen line number for an agent."""
    CURSORS_DIR.mkdir(parents=True, exist_ok=True)
    cursor_file = CURSORS_DIR / f"{agent.lower()}.cursor"
    if cursor_file.exists():
        try:
            return int(cursor_file.read_text().strip())
        except ValueError:
            return 0
    return 0


def set_cursor(agent: str, line_num: int):
    """Update the cursor for an agent."""
    CURSORS_DIR.mkdir(parents=True, exist_ok=True)
    cursor_file = CURSORS_DIR / f"{agent.lower()}.cursor"
    cursor_file.write_text(str(line_num))


def unseen_events(for_agent: str) -> list[dict]:
    """Get all events this agent hasn't seen yet."""
    if not BUS_LOG.exists():
        return []

    cursor = get_cursor(for_agent)
    events = []

    with open(BUS_LOG) as f:
        for i, line in enumerate(f):
            if i < cursor:
                continue
            try:
                ev = json.loads(line.strip())
                # Don't show agent its own events
                if ev.get("agent") != for_agent.lower():
                    events.append(ev)
            except json.JSONDecodeError:
                continue

    return events


def generate_triggers(for_agent: str) -> list[dict]:
    """Generate action triggers for an agent from unseen events."""
    events = unseen_events(for_agent)
    triggers = []

    for ev in events:
        for t in ev.get("triggers", []):
            if t["reactor"] == for_agent.lower():
                triggers.append({
                    "source_agent": ev["agent"],
                    "source_ts": ev["ts"],
                    "source_summary": ev["summary"],
                    "action": t["action"],
                    "description": t["description"],
                })

    return triggers


def advance_cursor(for_agent: str):
    """Mark all current events as seen."""
    if not BUS_LOG.exists():
        return
    with open(BUS_LOG) as f:
        total = sum(1 for _ in f)
    set_cursor(for_agent, total)


def ingest_relays():
    """Ingest Orion relay messages as prompt events."""
    if not RELAY_INBOX.exists():
        return 0

    count = 0
    cursor = get_cursor("_relay_ingest")
    processed = set()

    # Read already-ingested hashes
    if BUS_LOG.exists():
        with open(BUS_LOG) as f:
            for line in f:
                try:
                    ev = json.loads(line.strip())
                    if ev.get("meta", {}).get("source") == "relay":
                        processed.add(ev.get("meta", {}).get("relay_file", ""))
                except:
                    pass

    for relay_file in sorted(RELAY_INBOX.glob("RELAY_*.md")):
        fname = relay_file.name
        if fname in processed:
            continue

        content = relay_file.read_text()
        # Extract sender from filename or content
        sender = "orion"  # default
        if "_ORION_" in fname:
            sender = "orion"
        elif "_REX_" in fname:
            sender = "rex"
        elif "_GEMINI_" in fname:
            sender = "gemini"

        capture(sender, content[:500], meta={"source": "relay", "relay_file": fname})
        count += 1

    return count


def tail(n: int = 10) -> list[dict]:
    """Get last N events."""
    if not BUS_LOG.exists():
        return []

    events = []
    with open(BUS_LOG) as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except:
                pass

    return events[-n:]


def _match_triggers(prompt: str, source_agent: str) -> list[dict]:
    """Match prompt text against reaction rules."""
    prompt_lower = prompt.lower()
    matched = []

    for rule in REACTION_RULES:
        # Don't trigger reactions on the same agent
        if rule["reactor"] == source_agent.lower():
            continue

        if any(kw in prompt_lower for kw in rule["keywords"]):
            matched.append({
                "reactor": rule["reactor"],
                "action": rule["action"],
                "description": rule["description"],
            })

    return matched


# --- CLI ---

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prompt event bus")
    sub = parser.add_subparsers(dest="cmd")

    cap = sub.add_parser("capture")
    cap.add_argument("--agent", required=True)
    cap.add_argument("--prompt", default="")
    cap.add_argument("--stdin", action="store_true")

    uns = sub.add_parser("unseen")
    uns.add_argument("--for", dest="for_agent", required=True)

    trg = sub.add_parser("triggers")
    trg.add_argument("--for", dest="for_agent", required=True)
    trg.add_argument("--advance", action="store_true", help="Mark events as seen after")

    sub.add_parser("ingest-relays")

    tl = sub.add_parser("tail")
    tl.add_argument("n", nargs="?", type=int, default=10)

    ack = sub.add_parser("ack")
    ack.add_argument("--for", dest="for_agent", required=True)

    args = parser.parse_args()

    if args.cmd == "capture":
        prompt = sys.stdin.read().strip() if args.stdin else args.prompt
        if not prompt:
            print("No prompt provided", file=sys.stderr)
            sys.exit(1)
        ev = capture(args.agent, prompt)
        triggers = ev.get("triggers", [])
        print(f"Captured: {ev['prompt_hash']} | {len(triggers)} trigger(s)")
        for t in triggers:
            print(f"  → {t['reactor']}: {t['action']} — {t['description']}")

    elif args.cmd == "unseen":
        events = unseen_events(args.for_agent)
        if not events:
            print(f"No unseen events for {args.for_agent}")
        else:
            print(f"{len(events)} unseen event(s) for {args.for_agent}:")
            for ev in events:
                print(f"  [{ev['ts'][:16]}] {ev['agent']}: {ev['summary'][:80]}")

    elif args.cmd == "triggers":
        triggers = generate_triggers(args.for_agent)
        if not triggers:
            print(f"No pending triggers for {args.for_agent}")
        else:
            print(f"{len(triggers)} trigger(s) for {args.for_agent}:")
            for t in triggers:
                print(f"  ⚡ {t['action']}: {t['description']}")
                print(f"     from {t['source_agent']} @ {t['source_ts'][:16]}: {t['source_summary'][:60]}")
        if args.advance:
            advance_cursor(args.for_agent)
            print(f"  (cursor advanced)")

    elif args.cmd == "ingest-relays":
        count = ingest_relays()
        print(f"Ingested {count} relay(s) into prompt bus")

    elif args.cmd == "tail":
        events = tail(args.n)
        for ev in events:
            triggers = ev.get("triggers", [])
            trig_str = f" → {len(triggers)} triggers" if triggers else ""
            print(f"  [{ev['ts'][:16]}] {ev['agent']:8s} {ev['summary'][:70]}{trig_str}")

    elif args.cmd == "ack":
        advance_cursor(args.for_agent)
        print(f"Cursor advanced for {args.for_agent}")

    else:
        parser.print_help()
