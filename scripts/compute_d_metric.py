#!/usr/bin/env python3
"""
compute_d_metric.py — D-metric (drift metric) for Rhea project.

Measures how far the project has drifted from ideal operating state.
D is a weighted sum of drift indicators. Lower = healthier.

Thresholds:
  T1 = 150  (caution)
  T2 = 300  (sprint needed)

Exit codes:
  0 — D <= T2 (healthy or caution)
  1 — D > T2  (sprint needed, also prints [SPRINT NEEDED])

Usage:
  python3 scripts/compute_d_metric.py
  python3 scripts/compute_d_metric.py --verbose
  python3 scripts/compute_d_metric.py --json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

T1 = 150   # caution
T2 = 300   # sprint needed

# ---------------------------------------------------------------------------
# Staleness probe
# ---------------------------------------------------------------------------

# Files that should be updated at least every N days or they count as stale.
# Format: (relative_path, max_age_days, weight_per_day_over)
STALENESS_TARGETS = [
    ("docs/state.md",                            1,  20),
    ("docs/state_full.md",                       2,  15),
    ("ops/virtual-office/TODAY_CAPSULE.md",      1,  10),
    ("ops/virtual-office/relay_chain.jsonl",     3,   8),
    ("ops/virtual-office/shared/LEARNING_FEED.md", 5, 5),
    ("ops/virtual-office/outbox/REX_INSIGHTS.md",  5, 5),
]


def file_age_days(path: Path) -> float | None:
    """Return file age in fractional days, or None if file doesn't exist."""
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    age_s = time.time() - mtime
    return age_s / 86400.0


def compute_staleness() -> tuple[float, list[dict]]:
    """
    Return (score, details).
    Score = sum over stale files of: days_over_limit * weight_per_day.
    If file is missing entirely, treat as 14 days stale.
    """
    score = 0.0
    details = []
    for rel, max_days, weight in STALENESS_TARGETS:
        path = ROOT / rel
        age = file_age_days(path)
        if age is None:
            # File absent — treat as severely stale
            days_over = 14.0
            note = "MISSING"
        else:
            days_over = max(0.0, age - max_days)
            note = f"{age:.1f}d old (limit {max_days}d)"

        contrib = days_over * weight
        score += contrib
        details.append({
            "file": rel,
            "age_days": round(age, 2) if age is not None else None,
            "max_age_days": max_days,
            "days_over": round(days_over, 2),
            "weight": weight,
            "contribution": round(contrib, 2),
            "note": note,
        })
    return score, details


# ---------------------------------------------------------------------------
# Unpushed commits
# ---------------------------------------------------------------------------

def compute_unpushed() -> tuple[float, int]:
    """
    Return (score, count).
    Each unpushed commit adds 10 points (mandate: push every 30 min).
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--oneline", "@{u}..HEAD"],
            capture_output=True, text=True, timeout=10
        )
        lines = [l for l in result.stdout.strip().split("\n") if l]
        count = len(lines)
    except Exception:
        # If no upstream configured or git error, report 0
        count = 0
    score = count * 10.0
    return score, count


# ---------------------------------------------------------------------------
# Check.sh invariant failures
# ---------------------------------------------------------------------------

def compute_invariant_failures() -> tuple[float, int]:
    """
    Return (score, failure_count).
    Run check.sh; each FAIL line = 50 points.
    If check.sh exits 0 cleanly, 0 failures.
    """
    check_sh = ROOT / "scripts" / "rhea" / "check.sh"
    if not check_sh.exists():
        # Script missing is itself a problem
        return 50.0, 1

    try:
        result = subprocess.run(
            ["bash", str(check_sh)],
            capture_output=True, text=True,
            cwd=str(ROOT), timeout=30
        )
        fails = result.stderr.count("FAIL:")
        warns = result.stderr.count("WARN:")
        # FAILs are hard (50 pts each), WARNs are soft (5 pts each)
        score = fails * 50.0 + warns * 5.0
        count = fails
    except Exception:
        score = 50.0
        count = 1
    return score, count


# ---------------------------------------------------------------------------
# Relay chain gaps
# ---------------------------------------------------------------------------

def compute_chain_gaps() -> tuple[float, dict]:
    """
    Return (score, info).
    If relay_chain.jsonl is absent or empty: 40 pts.
    If last chain entry is >3 days old: 20 pts per additional day.
    """
    chain_path = ROOT / "ops" / "virtual-office" / "relay_chain.jsonl"
    if not chain_path.exists() or chain_path.stat().st_size == 0:
        return 40.0, {"status": "missing_or_empty", "last_entry_age_days": None}

    age = file_age_days(chain_path)
    threshold = 3.0
    if age is None or age <= threshold:
        score = 0.0
    else:
        score = (age - threshold) * 20.0

    return score, {"status": "present", "last_entry_age_days": round(age, 2) if age else None}


# ---------------------------------------------------------------------------
# Memory layer staleness (from memory_metrics.json)
# ---------------------------------------------------------------------------

def compute_memory_layer() -> tuple[float, dict]:
    """
    Return (score, info).
    Reads metrics/memory_metrics.json if it exists.
    Falls back to 0 if absent (can't penalize for missing instrumentation yet).

    Uses the existing discomfort_metric_d as a secondary signal, scaled down:
    contribution = existing_d * 0.1 (capped at 100 to avoid domination).
    """
    metrics_path = ROOT / "metrics" / "memory_metrics.json"
    if not metrics_path.exists():
        return 0.0, {"status": "no_metrics_file", "contribution": 0.0}

    try:
        data = json.loads(metrics_path.read_text())
    except Exception as e:
        return 5.0, {"status": f"parse_error: {e}", "contribution": 5.0}

    existing_d = data.get("discomfort_metric_d", 0.0) or 0.0
    # Scale: cap at 100 pts contribution so it's a signal, not a dominator
    contribution = min(existing_d * 0.1, 100.0)

    # Also penalize open TODOs
    todo_count = data.get("open_todo_count", 0) or 0
    todo_contribution = todo_count * 5.0

    total = contribution + todo_contribution
    return total, {
        "status": "loaded",
        "existing_d": existing_d,
        "contribution_from_existing_d": round(contribution, 2),
        "open_todos": todo_count,
        "todo_contribution": round(todo_contribution, 2),
        "total": round(total, 2),
    }


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------

def compute_d(verbose: bool = False) -> tuple[float, dict]:
    stale_score, stale_details = compute_staleness()
    unpushed_score, unpushed_count = compute_unpushed()
    invariant_score, invariant_failures = compute_invariant_failures()
    chain_score, chain_info = compute_chain_gaps()
    memory_score, memory_info = compute_memory_layer()

    components = {
        "staleness":      round(stale_score, 2),
        "unpushed":       round(unpushed_score, 2),
        "invariants":     round(invariant_score, 2),
        "chain_gaps":     round(chain_score, 2),
        "memory_layer":   round(memory_score, 2),
    }

    d = sum(components.values())

    breakdown = {
        "D": round(d, 3),
        "T1": T1,
        "T2": T2,
        "status": "healthy" if d <= T1 else ("caution" if d <= T2 else "sprint_needed"),
        "components": components,
    }

    if verbose:
        breakdown["staleness_details"] = stale_details
        breakdown["unpushed_count"] = unpushed_count
        breakdown["invariant_failures"] = invariant_failures
        breakdown["chain_info"] = chain_info
        breakdown["memory_info"] = memory_info

    return d, breakdown


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    as_json = "--json" in sys.argv

    d, breakdown = compute_d(verbose=verbose or as_json)

    if as_json:
        print(json.dumps(breakdown, indent=2))
    else:
        print(f"D={d:.1f}")
        if verbose:
            print(f"  T1={T1} (caution)  T2={T2} (sprint needed)")
            print(f"  Status: {breakdown['status'].upper()}")
            print(f"  Components:")
            for k, v in breakdown["components"].items():
                print(f"    {k:<14} {v:>8.2f}")

    if d > T2:
        print("[SPRINT NEEDED]")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
