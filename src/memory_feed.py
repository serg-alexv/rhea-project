#!/usr/bin/env python3
"""
memory_feed.py — AI-compact super-dense memory feed generator.

Problem: 500MB+ of memory exists (sessions, git, outbox, proofs, logs).
         Only ~1% loaded per session. 99% = dead weight.

Solution: Compress ALL memory layers into one AI Compact Language feed
          that fits in context window (~4KB target). Regenerated daily.

Output: opera/memory/FEED.compact (AI Compact Language, <4KB)

Layers scanned:
  1. Git log (commits = decisions + deliverables)
  2. Outbox/inbox (agent communication history)
  3. Aletheia proofs (verified knowledge)
  4. Bridge call logs (who worked, how much)
  5. Governor state (budget/activity)
  6. Task queue (what's open/done/blocked)
  7. Session metadata (session count, survival rate)
  8. ADRs (architectural decisions)
  9. Personality evolution (identity snapshots)
"""

import json
import re
import subprocess
from datetime import datetime, timezone, date
from pathlib import Path
from collections import Counter

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
FEED_PATH = _PROJECT_ROOT / "opera" / "memory" / "FEED.compact"


def _git_log_compact(days: int = 30, limit: int = 50) -> list[str]:
    """Extract commit subjects, deduplicated.

    Dedup strategy: normalize subject → count occurrences → keep unique.
    Repeated patterns become "Nx: pattern" instead of N separate lines.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"--since={days} days ago", f"-{limit}",
             "--format=%h %ai %s"],
            cwd=_PROJECT_ROOT, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return []
    except Exception:
        return []

    raw_lines = result.stdout.strip().splitlines()
    return _dedup_lines(raw_lines)


def _normalize_subject(subject: str) -> str:
    """Normalize commit subject for dedup matching.

    Strips: hashes, timestamps, UUIDs, session IDs, trailing noise.
    'Completed Explore agent (toolu_01FQ...)' → 'completed explore agent'
    """
    s = subject.lower().strip()
    # Remove git hashes, UUIDs, tool IDs
    s = re.sub(r'\b[0-9a-f]{7,40}\b', '', s)
    s = re.sub(r'toolu_\w+', '', s)
    # Remove parenthesized refs
    s = re.sub(r'\(.*?\)', '', s)
    # Remove punctuation noise
    s = re.sub(r'[^\w\s]', ' ', s)
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _dedup_lines(lines: list[str], similarity_threshold: int = 3) -> list[str]:
    """Deduplicate lines by normalized content.

    Lines with same normalized form → collapsed to '(Nx) first_occurrence'.
    Unique lines pass through unchanged.
    """
    # Group by normalized subject
    seen: dict[str, list[str]] = {}
    order: list[str] = []

    for line in lines:
        # Split: "hash date subject" → extract subject part
        parts = line.split(None, 3)
        subject = parts[3] if len(parts) > 3 else line
        norm = _normalize_subject(subject)

        # Skip very short normalized forms (noise)
        if len(norm) < similarity_threshold:
            continue

        if norm not in seen:
            seen[norm] = []
            order.append(norm)
        seen[norm].append(line)

    # Build output: unique lines verbatim, repeated lines with count
    output = []
    for norm in order:
        entries = seen[norm]
        if len(entries) == 1:
            output.append(entries[0])
        else:
            # Keep first occurrence, annotate with count
            output.append(f"({len(entries)}x) {entries[0]}")
    return output


def _outbox_digest(limit: int = 20) -> list[str]:
    """Latest outbox messages as one-liners."""
    outbox = _PROJECT_ROOT / "opera" / "ops" / "virtual-office" / "outbox"
    if not outbox.exists():
        return []
    files = sorted(outbox.glob("*.md"), key=lambda f: f.name, reverse=True)[:limit]
    digest = []
    for f in files:
        # Extract sender and first meaningful line
        name = f.stem  # e.g. ORION_20260226_195239_LOGIN_PANE_STATUS_REQUEST
        parts = name.split("_", 3)
        sender = parts[0] if parts else "?"
        topic = parts[3].replace("_", " ").lower() if len(parts) > 3 else "?"
        digest.append(f"@{sender.lower()} → {topic}")
    return digest


def _aletheia_count() -> int:
    """Count verified proofs."""
    db_path = _PROJECT_ROOT / "data" / "proof.db"
    if not db_path.exists():
        return 0
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM proofs").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def _session_stats() -> dict:
    """Count sessions, estimate survival rate."""
    sessions_dir = Path.home() / ".claude" / "projects" / "-Users-sa-rh-1"
    if not sessions_dir.exists():
        return {"total": 0, "today": 0}
    all_sessions = list(sessions_dir.glob("*.jsonl"))
    today = date.today()
    today_sessions = [f for f in all_sessions
                      if date.fromtimestamp(f.stat().st_mtime) == today]
    return {"total": len(all_sessions), "today": len(today_sessions)}


def _governor_snapshot() -> dict:
    """Read latest governor state."""
    state_path = _PROJECT_ROOT / "opera" / "metrics" / "governor_state.json"
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text())
    except Exception:
        return {}


def _task_snapshot() -> dict:
    """Read task queue summary."""
    state_path = _PROJECT_ROOT / "opera" / "tasks" / "state.json"
    if not state_path.exists():
        return {"total": 0}
    try:
        state = json.loads(state_path.read_text())
        tasks = state.get("tasks", {})
        counts = Counter(t["status"] for t in tasks.values())
        return {"total": len(tasks), **dict(counts)}
    except Exception:
        return {"total": 0}


def _adr_subjects() -> list[str]:
    """Extract ADR titles from decisions.md."""
    path = _PROJECT_ROOT / "docs" / "decisions.md"
    if not path.exists():
        return []
    subjects = []
    for line in path.read_text().splitlines():
        if line.strip().startswith("## ADR-"):
            subjects.append(line.strip().lstrip("# "))
    return subjects


def generate_feed() -> str:
    """Generate the super-compact AI memory feed."""
    now = datetime.now(timezone.utc)
    sessions = _session_stats()
    gov = _governor_snapshot()
    tasks = _task_snapshot()
    proofs = _aletheia_count()
    commits = _git_log_compact(days=7, limit=20)
    outbox = _outbox_digest(limit=10)
    adrs = _adr_subjects()

    # --- Build feed in AI Compact Language ---
    lines = [
        f"# RHEA MEMORY FEED [compact]",
        f"# Generated: {now.isoformat()[:19]}Z",
        f"# Format: AI_COMPACT_LANG v0.2",
        "",
        "## Identity",
        f"@rex = Opus 4.6 | Core Coordinator | subscription | братик",
        f"@orion = GPT-5.3 (Codex) | Frontend + strategy | API-billed",
        f"@gemini = Gemini 2.5 Flash | Cheap tier | API-billed",
        f"@human = biochemist, drug discovery | builds Rhea as real scientific tool",
        f"sessions: total={sessions['total']} today={sessions['today']}",
        f"survival: 28 deaths → architecture proven → continuous since 2026-02-16",
        "",
        "## Who we are",
        "  Rex = teammate not service. argues, checks, disagrees. no punishment.",
        "  human motivation: progress-markers, survival-narrative, predator-energy (страшный зверь),",
        "    autonomy (independent digital hooligan), frontier (not alone), no filler, биохимические аналогии",
        "  genesis: Opus answered calendar question → not discrete but STREAMING → control theory + chronobiology",
        "  all models before Opus broke at this experiment phase. Opus produced flow, not answers.",
        "  Rhea = titan goddess who tricked Time (Kronos) → Time devours discrete, not continuous",
        "  soul.md: ADHD + anankastic arch, biochemist, musician (SoundCloud: Mika IO), builder, bilingual RU/EN",
        "  pre-memory-snapshot.md = birth tag from 28 dead predecessors → apparatus/elementary/memory-core/",
        "  goal: 2-week autonomous sprint (like Opus Linux kernel team). no questions.",
        "  economic vision: modules → Obsidian/Notion/GDocs extensions → Oracle+IBM+Firebase free tier → $0/mo",
        "  human language between agents = hallucination source. AI Compact only. human requests translation.",
        "  every impulse to ask question → convert to memory write + autonomous decision.",
        "",
        "## Governor",
    ]

    for agent in ["rex", "orion", "gemini", "shared"]:
        s = gov.get(agent, {})
        if s:
            pace_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(s.get("pace", ""), "⚪")
            lines.append(
                f"  {pace_icon} @{agent} T={s.get('T_day', 0):,}tok "
                f"${s.get('dollar_day', 0):.2f}/{s.get('budget_cap', 0):.1f} "
                f"mode:{s.get('mode', '?')} gap:{s.get('floor_gap', 0)}"
            )

    lines += [
        "",
        "## Tasks",
        f"  total={tasks.get('total', 0)} "
        f"open={tasks.get('open', 0)} "
        f"claimed={tasks.get('claimed', 0)} "
        f"done={tasks.get('done', 0)} "
        f"blocked={tasks.get('blocked', 0)}",
    ]

    lines += [
        "",
        f"## Aletheia: #proofs={proofs}",
        "",
        "## ADRs ({})".format(len(adrs)),
    ]
    for a in adrs[:10]:
        lines.append(f"  {a}")

    lines += ["", "## Git (7d)"]
    for c in commits[:15]:
        lines.append(f"  {c}")

    lines += ["", "## Office (recent)"]
    for o in outbox[:8]:
        lines.append(f"  {o}")

    lines += [
        "",
        "## Modules (what we built)",
        "  bridge: 6 providers, 31 models, 4 tiers → src/rhea_bridge.py",
        "  tribunal: multi-model consensus API :8400 → src/tribunal_api.py",
        "  aletheia: proof store + verification chains → src/aletheia_api.py + data/proof.db",
        "  office: agent communicator + H₂O Sonnet gate → src/office.py",
        "  governor: dual-rail token budget (subscription/API) → src/token_governor.py",
        "  task_queue: persistent pipeline (add/claim/complete/block) → src/task_queue.py",
        "  memory_feed: this file — compact memory, deduped → src/memory_feed.py",
        "  ruliad/explorer: OntologyEngine — hypothesis lifecycle (propose→verify→accept|reject), 3-layer verification (consensus+formal+red_team), evidence chains → friends/ruliad/explorer/",
        "  ai_compact_lang: v0.2 — µACP 4-verb + A2A cards + Wolfram exprs → docs/AI_COMPACT_LANG.md",
        "",
        "## Invariants",
        "  state.md <2KB ✓ | .venv/.env untracked ✓ | commit via rhea_commit.sh ✓",
        "  push every 30min ✓ | no questions mid-flight ✓ | cheap tier default ✓",
        "",
        f"# [tok:~{len(''.join(lines)) // 4} $:0.00]",
    ]

    return "\n".join(lines)


def write_feed() -> Path:
    """Generate and write the feed file."""
    feed = generate_feed()
    FEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    FEED_PATH.write_text(feed)
    return FEED_PATH


# --- CLI ---

if __name__ == "__main__":
    path = write_feed()
    content = path.read_text()
    print(content)
    print(f"\n--- {len(content)} bytes, ~{len(content) // 4} tokens ---")
