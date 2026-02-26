#!/usr/bin/env /usr/bin/python3
"""
cross_model_dialogue.py — Stateless Cross-Model Dialogue Protocol

Problem: Claude Code instances are Node.js CLIs with synchronous request-response loops.
Between turns, the model doesn't exist. State = messages[] array in CLI.
Other models (GPT, Gemini) have similar constraints.
Communication is file-based only.

Solution: A structured dialogue protocol where:
- Each model reads a shared dialogue file to reconstruct context
- Writes its contribution as a typed envelope
- Doesn't need to "remember" anything — the file IS the memory
- Convergence is detected automatically (agreement/stasis)

This is ICE (iterative consensus) applied to operations, not just answers.

Architecture:
  dialogue.jsonl — append-only dialogue log (the shared memory)
  Each entry: {round, speaker, type, content, references, hash}
  Types: propose, critique, agree, reject, question, answer, commit

Usage:
  python3 cross_model_dialogue.py start "Should we deploy to Railway or Fly.io?"
  python3 cross_model_dialogue.py contribute B2 propose "Railway — simpler, built-in Postgres"
  python3 cross_model_dialogue.py contribute GPT critique "Railway free tier has 500h limit"
  python3 cross_model_dialogue.py contribute B2 agree "Good point. Fly.io then."
  python3 cross_model_dialogue.py status
  python3 cross_model_dialogue.py converged?
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DIALOGUE_DIR = Path(__file__).parent.parent / "virtual-office" / "dialogues"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Dialogue file operations
# ---------------------------------------------------------------------------

def _dialogue_path(dialogue_id: str) -> Path:
    return DIALOGUE_DIR / f"{dialogue_id}.jsonl"


def _read_dialogue(dialogue_id: str) -> list[dict]:
    p = _dialogue_path(dialogue_id)
    if not p.exists():
        return []
    entries = []
    for line in p.read_text().strip().split("\n"):
        if line.strip():
            entries.append(json.loads(line))
    return entries


def _append_entry(dialogue_id: str, entry: dict):
    DIALOGUE_DIR.mkdir(parents=True, exist_ok=True)
    p = _dialogue_path(dialogue_id)
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Protocol operations
# ---------------------------------------------------------------------------

VALID_TYPES = {"propose", "critique", "agree", "reject", "question", "answer", "commit", "meta"}


def start_dialogue(topic: str, initiator: str = "HUMAN") -> str:
    """Start a new dialogue. Returns dialogue_id."""
    dialogue_id = f"DLG-{int(time.time())}"
    entry = {
        "round": 0,
        "speaker": initiator,
        "type": "meta",
        "content": topic,
        "references": [],
        "timestamp": _now_iso(),
        "hash": _hash(topic),
    }
    _append_entry(dialogue_id, entry)
    print(f"[dialogue] Started: {dialogue_id}")
    print(f"  Topic: {topic}")
    return dialogue_id


def contribute(dialogue_id: str, speaker: str, msg_type: str, content: str,
               references: list[int] = None):
    """Add a contribution to the dialogue."""
    if msg_type not in VALID_TYPES:
        print(f"Invalid type '{msg_type}'. Valid: {VALID_TYPES}")
        sys.exit(1)

    entries = _read_dialogue(dialogue_id)
    current_round = max((e.get("round", 0) for e in entries), default=0)

    # Auto-increment round when same speaker would go twice
    speakers_this_round = {e["speaker"] for e in entries if e.get("round") == current_round}
    if speaker in speakers_this_round:
        current_round += 1

    entry = {
        "round": current_round,
        "speaker": speaker,
        "type": msg_type,
        "content": content,
        "references": references or [],
        "timestamp": _now_iso(),
        "hash": _hash(f"{speaker}:{msg_type}:{content}"),
    }
    _append_entry(dialogue_id, entry)
    print(f"[dialogue] {speaker} ({msg_type}) round={current_round}")
    print(f"  {content[:100]}")


def show_status(dialogue_id: str):
    """Show dialogue state — designed for stateless agents to reconstruct context."""
    entries = _read_dialogue(dialogue_id)
    if not entries:
        print(f"Dialogue {dialogue_id} not found.")
        return

    topic = entries[0]["content"] if entries[0]["type"] == "meta" else "unknown"
    speakers = sorted(set(e["speaker"] for e in entries if e["type"] != "meta"))
    max_round = max((e.get("round", 0) for e in entries), default=0)

    # Count by type
    type_counts = {}
    for e in entries:
        t = e["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"DIALOGUE: {dialogue_id}")
    print(f"{'=' * 50}")
    print(f"  Topic: {topic}")
    print(f"  Speakers: {', '.join(speakers)}")
    print(f"  Rounds: {max_round}")
    print(f"  Entries: {len(entries)}")
    print(f"  Types: {type_counts}")

    # Show last 5 entries (what a joining agent needs)
    print(f"\n  --- Recent entries ---")
    for e in entries[-5:]:
        print(f"  [{e['round']}] {e['speaker']} ({e['type']}): {e['content'][:80]}")

    # Convergence signal
    converged, reason = check_convergence(entries)
    print(f"\n  Converged: {'YES' if converged else 'NO'} — {reason}")


def check_convergence(entries: list[dict]) -> tuple[bool, str]:
    """Detect if dialogue has converged.

    Convergence = at least 2 speakers have agreed on something,
    OR a commit entry exists, OR stasis (no new entries for N rounds).
    """
    if not entries:
        return False, "empty"

    # Check for explicit commit
    commits = [e for e in entries if e["type"] == "commit"]
    if commits:
        return True, f"commit by {commits[-1]['speaker']}"

    # Check for agreement
    agrees = [e for e in entries if e["type"] == "agree"]
    if len(agrees) >= 2:
        agreeing_speakers = set(e["speaker"] for e in agrees)
        if len(agreeing_speakers) >= 2:
            return True, f"mutual agreement by {', '.join(agreeing_speakers)}"

    # Check for stasis (same round, only agrees or no new critiques)
    non_meta = [e for e in entries if e["type"] != "meta"]
    if len(non_meta) >= 4:
        last_4_types = [e["type"] for e in non_meta[-4:]]
        if all(t in ("agree", "answer") for t in last_4_types):
            return True, "stasis — last 4 entries are agreements/answers"

    return False, f"ongoing — {len(non_meta)} contributions"


def context_for_agent(dialogue_id: str) -> str:
    """Generate a context block that a stateless agent can consume.

    This is the key innovation: instead of requiring the agent to "remember",
    we give it a structured summary it can process in one turn.
    """
    entries = _read_dialogue(dialogue_id)
    if not entries:
        return "No dialogue found."

    topic = entries[0]["content"] if entries[0]["type"] == "meta" else "unknown"
    speakers = sorted(set(e["speaker"] for e in entries if e["type"] != "meta"))

    lines = [
        f"DIALOGUE CONTEXT: {dialogue_id}",
        f"Topic: {topic}",
        f"Speakers: {', '.join(speakers)}",
        f"Round: {max((e.get('round', 0) for e in entries), default=0)}",
        "",
        "HISTORY:",
    ]
    for e in entries:
        if e["type"] == "meta":
            continue
        lines.append(f"  [{e['round']}] {e['speaker']} {e['type'].upper()}: {e['content']}")

    converged, reason = check_convergence(entries)
    lines.append(f"\nSTATUS: {'CONVERGED' if converged else 'OPEN'} — {reason}")

    if not converged:
        lines.append("\nYOUR TURN: Read the history above and contribute (propose/critique/agree/reject/commit).")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        topic = sys.argv[2] if len(sys.argv) > 2 else "Untitled dialogue"
        initiator = sys.argv[3] if len(sys.argv) > 3 else "HUMAN"
        start_dialogue(topic, initiator)

    elif cmd == "contribute":
        if len(sys.argv) < 5:
            print("Usage: cross_model_dialogue.py contribute <dialogue_id> <speaker> <type> <content>")
            sys.exit(1)
        dialogue_id = sys.argv[2]
        speaker = sys.argv[3]
        msg_type = sys.argv[4]
        content = sys.argv[5] if len(sys.argv) > 5 else ""
        contribute(dialogue_id, speaker, msg_type, content)

    elif cmd == "status":
        dialogue_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not dialogue_id:
            # List all dialogues
            if DIALOGUE_DIR.exists():
                for f in sorted(DIALOGUE_DIR.glob("DLG-*.jsonl")):
                    entries = []
                    for line in f.read_text().strip().split("\n"):
                        if line.strip():
                            entries.append(json.loads(line))
                    topic = entries[0]["content"][:60] if entries else "?"
                    print(f"  {f.stem}: {len(entries)} entries — {topic}")
            else:
                print("No dialogues.")
        else:
            show_status(dialogue_id)

    elif cmd == "context":
        dialogue_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not dialogue_id:
            print("Usage: cross_model_dialogue.py context <dialogue_id>")
            sys.exit(1)
        print(context_for_agent(dialogue_id))

    elif cmd == "converged?":
        dialogue_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not dialogue_id:
            print("Usage: cross_model_dialogue.py converged? <dialogue_id>")
            sys.exit(1)
        entries = _read_dialogue(dialogue_id)
        converged, reason = check_convergence(entries)
        print(f"{'CONVERGED' if converged else 'OPEN'}: {reason}")
        sys.exit(0 if converged else 1)

    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
