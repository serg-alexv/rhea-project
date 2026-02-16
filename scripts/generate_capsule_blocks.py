#!/usr/bin/env python3
"""
generate_capsule_blocks.py — Deterministic route generator from TODAY_CAPSULE.

Reads TODAY_CAPSULE.md and produces three paste-blocks:
  LEADERS — what LEAD + COWORK need to know
  WORKERS — what B2 + GPT + on-demand agents need to know
  OPS     — what ops-focused agents need (bridge, infra, incidents)

Usage:
    python3 scripts/generate_capsule_blocks.py
    python3 scripts/generate_capsule_blocks.py --capsule path/to/capsule.md
    python3 scripts/generate_capsule_blocks.py --output-dir ops/outbox

Output: Three files in ops/outbox/:
    BLOCK_LEADERS.md
    BLOCK_WORKERS.md
    BLOCK_OPS.md
"""
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CAPSULE = PROJECT_ROOT / "ops" / "virtual-office" / "TODAY_CAPSULE.md"
DEFAULT_OUTPUT = PROJECT_ROOT / "ops" / "outbox"


def parse_capsule(text: str) -> dict[str, list[str]]:
    """Parse capsule markdown into sections."""
    sections: dict[str, list[str]] = {}
    current_section = "header"
    sections[current_section] = []

    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            current_section = heading.group(1).strip().lower()
            sections[current_section] = []
        else:
            if current_section in sections:
                sections[current_section].append(line)

    # Clean up: strip empty leading/trailing lines per section
    for key in sections:
        while sections[key] and not sections[key][0].strip():
            sections[key].pop(0)
        while sections[key] and not sections[key][-1].strip():
            sections[key].pop()

    return sections


def extract_backlog_refs(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Classify RHEA-* references into done, partial, todo."""
    done, partial, todo = [], [], []
    for line in lines:
        refs = re.findall(r"RHEA-\w+-\d+", line)
        for ref in refs:
            if "DONE" in line or "✅" in line:
                done.append(ref)
            elif "PARTIAL" in line or "⚠" in line:
                partial.append(ref)
            elif "TODO" in line or "🔲" in line:
                todo.append(ref)
    return done, partial, todo


def extract_incidents(lines: list[str]) -> list[str]:
    """Pull INC-* references."""
    incidents = []
    for line in lines:
        refs = re.findall(r"INC-\d{4}-\d{2}-\d{2}-\d+", line)
        incidents.extend(refs)
    return incidents


def extract_gems(lines: list[str]) -> list[str]:
    """Pull GEM-* references."""
    gems = []
    for line in lines:
        refs = re.findall(r"GEM-\w+", line)
        gems.extend(refs)
    return gems


def generate_leaders_block(sections: dict[str, list[str]], timestamp: str) -> str:
    """LEADERS block: strategic overview for LEAD + COWORK."""
    lines = [
        f"# LEADERS BLOCK — {timestamp}",
        "> Auto-generated from TODAY_CAPSULE. Do not edit manually.",
        "",
    ]

    # Done today
    done_section = sections.get("done today", sections.get("done", []))
    if done_section:
        done_refs, _, _ = extract_backlog_refs(done_section)
        lines.append(f"## Completed: {len(done_refs)} items")
        for ref in done_refs:
            lines.append(f"- {ref}")
        lines.append("")

    # Next priorities
    next_section = sections.get("next (p1--p2)", sections.get("next", sections.get("next (p1-p2)", [])))
    if next_section:
        lines.append("## Next Priorities")
        for line in next_section:
            if line.strip():
                lines.append(line)
        lines.append("")

    # Blockers (leaders need to know about all blockers)
    blockers = sections.get("blockers", [])
    if blockers:
        lines.append("## Blockers (action required)")
        for line in blockers:
            if line.strip():
                lines.append(line)
        lines.append("")

    # Human state (leaders coordinate around human availability)
    human = sections.get("human state", [])
    if human:
        lines.append("## Human State")
        for line in human:
            if line.strip():
                lines.append(line)
        lines.append("")

    return "\n".join(lines)


def generate_workers_block(sections: dict[str, list[str]], timestamp: str) -> str:
    """WORKERS block: actionable tasks for B2, GPT, on-demand agents."""
    lines = [
        f"# WORKERS BLOCK — {timestamp}",
        "> Auto-generated from TODAY_CAPSULE. Do not edit manually.",
        "",
    ]

    # What's TODO — this is what workers care about
    next_section = sections.get("next (p1--p2)", sections.get("next", sections.get("next (p1-p2)", [])))
    if next_section:
        lines.append("## Available Work")
        for line in next_section:
            if line.strip() and "🔲" in line:
                lines.append(line)
        lines.append("")

    # Active refs (gems and incidents workers might need)
    active = sections.get("active refs", sections.get("active", []))
    if active:
        gems = extract_gems(active)
        if gems:
            lines.append(f"## Reference GEMs: {', '.join(gems)}")
            lines.append("")

    # Blockers that affect work
    blockers = sections.get("blockers", [])
    if blockers:
        lines.append("## Known Blockers (work around these)")
        for line in blockers:
            if line.strip():
                lines.append(line)
        lines.append("")

    return "\n".join(lines)


def generate_ops_block(sections: dict[str, list[str]], timestamp: str) -> str:
    """OPS block: infrastructure, bridge, incidents for ops-focused agents."""
    lines = [
        f"# OPS BLOCK — {timestamp}",
        "> Auto-generated from TODAY_CAPSULE. Do not edit manually.",
        "",
    ]

    # State section (infra status)
    state = sections.get("state", [])
    if state:
        lines.append("## Infrastructure State")
        for line in state:
            if line.strip():
                lines.append(line)
        lines.append("")

    # Incidents
    all_lines = []
    for section_lines in sections.values():
        all_lines.extend(section_lines)
    incidents = extract_incidents(all_lines)
    if incidents:
        lines.append(f"## Open Incidents: {len(incidents)}")
        for inc in sorted(set(incidents)):
            lines.append(f"- {inc}")
        lines.append("")

    # Blockers (ops needs full detail)
    blockers = sections.get("blockers", [])
    if blockers:
        lines.append("## Blockers (ops action items)")
        for line in blockers:
            if line.strip():
                lines.append(line)
        lines.append("")

    # Bridge-specific (look for bridge/provider mentions)
    for line in all_lines:
        if "bridge" in line.lower() or "provider" in line.lower():
            if "## Bridge Status" not in "\n".join(lines):
                lines.append("## Bridge Status")
            lines.append(line)
    if lines[-1] != "":
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate paste-blocks from TODAY_CAPSULE")
    parser.add_argument("--capsule", type=Path, default=DEFAULT_CAPSULE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.capsule.exists():
        print(f"Capsule not found: {args.capsule}")
        return

    text = args.capsule.read_text()
    sections = parse_capsule(text)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    leaders = generate_leaders_block(sections, timestamp)
    workers = generate_workers_block(sections, timestamp)
    ops = generate_ops_block(sections, timestamp)

    (args.output_dir / "BLOCK_LEADERS.md").write_text(leaders)
    (args.output_dir / "BLOCK_WORKERS.md").write_text(workers)
    (args.output_dir / "BLOCK_OPS.md").write_text(ops)

    print(f"Generated 3 blocks in {args.output_dir}/")
    print(f"  BLOCK_LEADERS.md  ({len(leaders)} bytes)")
    print(f"  BLOCK_WORKERS.md  ({len(workers)} bytes)")
    print(f"  BLOCK_OPS.md      ({len(ops)} bytes)")


if __name__ == "__main__":
    main()
