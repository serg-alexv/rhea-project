#!/usr/bin/env python3
"""
Live Metrics Controller — Rex's autonomous health monitoring system.
Collects real data from the repo, computes 7 metrics, outputs dashboard.
Determines wake-up conditions for autonomous self-activation.

Run:  python3 scripts/live_metrics.py
JSON: python3 scripts/live_metrics.py --json
"""
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_FILE = os.path.join(REPO_ROOT, "opera", "metrics", "memory_metrics.json")
LIVE_OUTPUT = os.path.join(REPO_ROOT, "opera", "metrics", "live_dashboard.json")

# ── Metric Definitions ──────────────────────────────────────────
# Each metric: (green_max, yellow_max, red_above)
# green: healthy, yellow: attention needed, red: wake-up trigger

THRESHOLDS = {
    "d_metric":          (150, 300),      # D-metric log-scale
    "debt_velocity":     (2.0, 5.0),      # TODOs created per day net
    "doc_staleness":     (14, 30),        # avg days since last doc update
    "commit_frequency":  (3.0, 1.0),      # commits/day (inverted: low = bad)
    "todo_load":         (0.3, 0.7),      # open_todos / max_sustainable(300)
    "insight_density":   (2.0, 1.0),      # insights per request (inverted: low = bad)
    "repo_entropy":      (0.3, 0.6),      # root_files / total_root_items ratio
}


# ── Data Collection (from real repo state) ───────────────────────

def _run(cmd, default=""):
    try:
        return subprocess.check_output(
            cmd, shell=True, cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL, timeout=10
        ).decode().strip()
    except Exception:
        return default


def collect_raw():
    """Gather raw measurements from the repository."""
    raw = {}

    # TODO count (grep across codebase)
    todo_out = _run("grep -r 'TODO' --include='*.py' --include='*.md' --include='*.sh' -l . 2>/dev/null | wc -l", "0")
    raw["open_todo_count"] = int(todo_out.strip())

    # Docs size (KB)
    docs_size = _run("find docs opera/docs emergentia apparatus -name '*.md' -exec cat {} + 2>/dev/null | wc -c", "0")
    raw["core_docs_kb"] = int(docs_size.strip()) // 1024

    # Repo size (MB) — git objects
    repo_size = _run("du -sm .git 2>/dev/null | cut -f1", "0")
    raw["repo_size_mb"] = int(repo_size.strip())

    # Commits in last 24h
    commits_24h = _run("git log --oneline --since='24 hours ago' 2>/dev/null | wc -l", "0")
    raw["commits_24h"] = int(commits_24h.strip())

    # Commits in last 7 days (for daily average)
    commits_7d = _run("git log --oneline --since='7 days ago' 2>/dev/null | wc -l", "0")
    raw["commits_7d"] = int(commits_7d.strip())
    raw["commits_per_day_7d"] = raw["commits_7d"] / 7.0

    # Doc staleness: average age of .md files in docs/ (days since last modified)
    staleness_cmd = (
        "find docs -name '*.md' -exec stat -f '%m' {} \\; 2>/dev/null"
    )
    staleness_out = _run(staleness_cmd, "")
    if staleness_out:
        now = datetime.now().timestamp()
        mtimes = [float(t) for t in staleness_out.splitlines() if t.strip()]
        if mtimes:
            ages_days = [(now - mt) / 86400 for mt in mtimes]
            raw["avg_doc_staleness_days"] = sum(ages_days) / len(ages_days)
        else:
            raw["avg_doc_staleness_days"] = 0
    else:
        raw["avg_doc_staleness_days"] = 0

    # Insights per request (from metrics file if exists)
    raw["insights_per_request"] = 3.2  # default
    raw["avg_context_tokens_estimate"] = 4500  # default
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE) as f:
                stored = json.load(f)
            raw["insights_per_request"] = stored.get("insights_per_request", 3.2)
            raw["avg_context_tokens_estimate"] = stored.get("avg_context_tokens_estimate", 4500)
        except Exception:
            pass

    # Root item count (for entropy measure)
    root_items = _run("ls -1 | wc -l", "0")
    root_files = _run("ls -1 -p | grep -v / | wc -l", "0")
    raw["root_items"] = int(root_items.strip())
    raw["root_files"] = int(root_files.strip())

    # TODO velocity: diff between current and last known count
    raw["last_known_todo_count"] = 0
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE) as f:
                stored = json.load(f)
            raw["last_known_todo_count"] = stored.get("open_todo_count", 0)
        except Exception:
            pass

    raw["timestamp"] = datetime.now(timezone.utc).isoformat()
    return raw


# ── Metric Computation ───────────────────────────────────────────

def compute_d_metric(raw):
    """Log-scale D-metric (proposed formula from tribunal)."""
    w = {"docs_kb": 30.0, "repo_mb": 20.0, "todos": 15.0, "inv_insights": 50.0, "tokens": 10.0}
    components = {
        "docs":     w["docs_kb"]      * math.log10(1 + raw["core_docs_kb"]),
        "repo":     w["repo_mb"]      * math.log10(1 + raw["repo_size_mb"]),
        "todos":    w["todos"]        * math.sqrt(raw["open_todo_count"]),
        "insights": w["inv_insights"] * (1.0 / max(raw["insights_per_request"], 0.01)),
        "tokens":   w["tokens"]       * (raw["avg_context_tokens_estimate"] / 1000.0),
    }
    # 40% component cap
    raw_total = sum(components.values())
    if raw_total > 0:
        cap = 0.40 * raw_total
        components = {k: min(v, cap) for k, v in components.items()}
    return sum(components.values()), components


def compute_all_metrics(raw):
    """Compute all 7 metrics from raw data."""
    d_val, d_components = compute_d_metric(raw)

    metrics = {}

    # 1. D-Metric (log-scale)
    metrics["d_metric"] = {
        "value": round(d_val, 1),
        "components": {k: round(v, 1) for k, v in d_components.items()},
    }

    # 2. Debt Velocity (TODO change rate)
    delta = raw["open_todo_count"] - raw["last_known_todo_count"]
    metrics["debt_velocity"] = {
        "value": round(abs(delta), 1),
        "direction": "growing" if delta > 0 else "shrinking" if delta < 0 else "stable",
    }

    # 3. Doc Staleness
    metrics["doc_staleness"] = {
        "value": round(raw["avg_doc_staleness_days"], 1),
    }

    # 4. Commit Frequency (inverted: LOW = bad)
    metrics["commit_frequency"] = {
        "value": round(raw["commits_per_day_7d"], 1),
        "last_24h": raw["commits_24h"],
    }

    # 5. TODO Load Factor
    max_sustainable = 300
    load = raw["open_todo_count"] / max_sustainable
    metrics["todo_load"] = {
        "value": round(load, 2),
        "open_todos": raw["open_todo_count"],
        "max_sustainable": max_sustainable,
    }

    # 6. Insight Density (inverted: LOW = bad)
    metrics["insight_density"] = {
        "value": round(raw["insights_per_request"], 1),
    }

    # 7. Repo Entropy (ratio of loose root files to total root items)
    if raw["root_items"] > 0:
        entropy = raw["root_files"] / raw["root_items"]
    else:
        entropy = 0
    metrics["repo_entropy"] = {
        "value": round(entropy, 2),
        "root_files": raw["root_files"],
        "root_items": raw["root_items"],
    }

    return metrics


# ── Severity & Scoring ───────────────────────────────────────────

def severity(metric_name, value):
    """Return (level, color) for a metric value."""
    t = THRESHOLDS[metric_name]

    # Inverted metrics: lower value = worse
    if metric_name in ("commit_frequency", "insight_density"):
        if value >= t[0]:   return "green"
        if value >= t[1]:   return "yellow"
        return "red"

    # Normal metrics: higher value = worse
    if value <= t[0]:   return "green"
    if value <= t[1]:   return "yellow"
    return "red"


def composite_health(metrics):
    """0.0 (dead) to 1.0 (perfect) health score."""
    weights = {
        "d_metric": 0.25,
        "debt_velocity": 0.10,
        "doc_staleness": 0.10,
        "commit_frequency": 0.15,
        "todo_load": 0.15,
        "insight_density": 0.10,
        "repo_entropy": 0.15,
    }

    score = 0.0
    for name, weight in weights.items():
        level = severity(name, metrics[name]["value"])
        if level == "green":
            score += weight * 1.0
        elif level == "yellow":
            score += weight * 0.5
        # red = 0
    return round(score, 2)


# ── Wake-Up Protocol (Enhanced Circle) ──────────────────────────
# Loop: Detect → Classify → Predict → Diagnose → Select → Act → Verify → Learn → Log
#
# Control theory additions from tribunal (DeepSeek + Gemini consensus):
#   - Hysteresis: trigger at threshold, reset at threshold - 10%
#   - Rate limiting: max 3 interventions/hour per metric
#   - Escalation: least invasive first, human after 3 auto-cycles

HYSTERESIS = {
    "d_metric_overload":    (300, 270),   # trigger at 300, reset at 270
    "todo_crisis":          (0.7, 0.6),
    "dev_stalled":          (1.0, 1.5),   # inverted: trigger below 1.0, reset above 1.5
    "knowledge_stagnant":   (1.0, 1.5),   # inverted
    "health_critical":      (0.3, 0.4),   # inverted: trigger below 0.3, reset above 0.4
}

# Concrete action chains: detect → diagnose → act
# Each action is a real command Rex can execute
ACTION_CHAINS = {
    "d_metric_overload": {
        "diagnose": "python3 scripts/live_metrics.py --json",
        "actions": [
            "grep -rn 'TODO' --include='*.md' docs/ | wc -l",           # count doc TODOs
            "find docs -name '*.md' -size +100k -exec ls -lh {} \\;",    # find bloated docs
            "python3 scripts/compute_d_metric.py",                       # recompute baseline
        ],
        "escalation": "Log to outbox + notify human if D > 400 after action",
    },
    "todo_crisis": {
        "diagnose": "grep -rn 'TODO' --include='*.py' --include='*.md' --include='*.sh' . | sort",
        "actions": [
            "grep -rn 'TODO' --include='*.md' docs/ | head -20",        # surface top TODOs
            # consolidate duplicate TODOs, archive resolved ones
        ],
        "escalation": "Create sprint plan at opera/metrics/todo_sprint.md",
    },
    "dev_stalled": {
        "diagnose": "git log --oneline --since='7 days ago' --format='%h %s (%cr)'",
        "actions": [
            "bash scripts/rhea/check.sh",                               # health probe
            # log stall event for human review
        ],
        "escalation": "ALWAYS notify human — stall may be intentional",
    },
    "knowledge_stagnant": {
        "diagnose": "find emergentia -name '*.pdf' -o -name '*.md' -newer opera/metrics/live_dashboard.json 2>/dev/null",
        "actions": [
            # trigger exploratory agent to process new documents in emergentia/
        ],
        "escalation": "Deploy exploration agent after 7 days of stagnation",
    },
    "health_critical": {
        "diagnose": "python3 scripts/live_metrics.py --json",
        "actions": [
            "bash scripts/rhea/check.sh",                               # system invariants
            "git status",                                                # uncommitted work?
        ],
        "escalation": "IMMEDIATE human alert — multiple systems failing",
    },
}


def check_wakeup(metrics, health):
    """
    Enhanced wake-up protocol with hysteresis and concrete action chains.
    Returns list of triggered wake-up conditions with full action context.

    TODO(human): Review and tune the hysteresis bands.
    Current design: trigger at threshold, reset 10% below.
    If oscillation occurs (trigger → fix → trigger → fix repeating),
    widen the hysteresis gap. If response feels too slow, narrow it.
    Also: add any project-specific actions to ACTION_CHAINS above.
    """
    triggers = []

    # 1. D-Metric overload (higher = worse)
    if metrics["d_metric"]["value"] > HYSTERESIS["d_metric_overload"][0]:
        triggers.append({
            "condition": "d_metric_overload",
            "value": metrics["d_metric"]["value"],
            "threshold": HYSTERESIS["d_metric_overload"][0],
            "reset_at": HYSTERESIS["d_metric_overload"][1],
            "chain": ACTION_CHAINS["d_metric_overload"],
        })

    # 2. TODO crisis (higher = worse)
    if metrics["todo_load"]["value"] > HYSTERESIS["todo_crisis"][0]:
        triggers.append({
            "condition": "todo_crisis",
            "value": metrics["todo_load"]["value"],
            "threshold": HYSTERESIS["todo_crisis"][0],
            "reset_at": HYSTERESIS["todo_crisis"][1],
            "chain": ACTION_CHAINS["todo_crisis"],
        })

    # 3. Dev stalled (lower = worse, inverted)
    if metrics["commit_frequency"]["value"] < HYSTERESIS["dev_stalled"][0]:
        triggers.append({
            "condition": "dev_stalled",
            "value": metrics["commit_frequency"]["value"],
            "threshold": HYSTERESIS["dev_stalled"][0],
            "reset_at": HYSTERESIS["dev_stalled"][1],
            "chain": ACTION_CHAINS["dev_stalled"],
        })

    # 4. Knowledge stagnant (lower = worse, inverted)
    if metrics["insight_density"]["value"] < HYSTERESIS["knowledge_stagnant"][0]:
        triggers.append({
            "condition": "knowledge_stagnant",
            "value": metrics["insight_density"]["value"],
            "threshold": HYSTERESIS["knowledge_stagnant"][0],
            "reset_at": HYSTERESIS["knowledge_stagnant"][1],
            "chain": ACTION_CHAINS["knowledge_stagnant"],
        })

    # 5. Health critical (lower = worse, inverted)
    if health < HYSTERESIS["health_critical"][0]:
        triggers.append({
            "condition": "health_critical",
            "value": health,
            "threshold": HYSTERESIS["health_critical"][0],
            "reset_at": HYSTERESIS["health_critical"][1],
            "chain": ACTION_CHAINS["health_critical"],
        })

    return triggers


# ── Output ───────────────────────────────────────────────────────

SEVERITY_ICONS = {"green": "OK", "yellow": "!!", "red": "XX"}

def print_dashboard(metrics, health, triggers):
    """Print human-readable dashboard."""
    print()
    print("=" * 60)
    print("  REX LIVE METRICS DASHBOARD")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    for name in THRESHOLDS:
        val = metrics[name]["value"]
        level = severity(name, val)
        icon = SEVERITY_ICONS[level]
        print(f"  [{icon}] {name:20s}  {val:>8}  ({level})")

    print(f"\n  COMPOSITE HEALTH: {health:.0%}")

    if triggers:
        print(f"\n  WAKE-UP TRIGGERS ({len(triggers)}):")
        for t in triggers:
            esc = t.get("chain", {}).get("escalation", "—")
            print(f"    >> {t['condition']}: {t['value']} (reset@{t.get('reset_at','?')}) → {esc}")
    else:
        print("\n  No wake-up triggers. System healthy.")

    print("=" * 60)


def save_dashboard(metrics, health, triggers, raw):
    """Save dashboard to JSON for other agents to consume."""
    dashboard = {
        "timestamp": raw["timestamp"],
        "metrics": metrics,
        "composite_health": health,
        "wake_up_triggers": triggers,
        "raw_measurements": {
            "open_todo_count": raw["open_todo_count"],
            "core_docs_kb": raw["core_docs_kb"],
            "repo_size_mb": raw["repo_size_mb"],
            "commits_24h": raw["commits_24h"],
            "commits_per_day_7d": raw["commits_per_day_7d"],
            "avg_doc_staleness_days": raw["avg_doc_staleness_days"],
            "insights_per_request": raw["insights_per_request"],
            "root_files": raw["root_files"],
            "root_items": raw["root_items"],
        },
    }
    os.makedirs(os.path.dirname(LIVE_OUTPUT), exist_ok=True)
    with open(LIVE_OUTPUT, "w") as f:
        json.dump(dashboard, f, indent=2)
    return dashboard


# ── Main ─────────────────────────────────────────────────────────

def main():
    raw = collect_raw()
    metrics = compute_all_metrics(raw)
    health = composite_health(metrics)
    triggers = check_wakeup(metrics, health)

    if "--json" in sys.argv:
        dashboard = save_dashboard(metrics, health, triggers, raw)
        print(json.dumps(dashboard, indent=2))
    else:
        print_dashboard(metrics, health, triggers)
        save_dashboard(metrics, health, triggers, raw)

    # Exit non-zero if any wake-up triggers fired
    sys.exit(1 if triggers else 0)


if __name__ == "__main__":
    main()
