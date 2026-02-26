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


# ── Wake-Up Protocol ────────────────────────────────────────────

def check_wakeup(metrics, health):
    """
    Determine if Rex should self-activate.
    Returns list of triggered wake-up conditions.

    TODO(human): Define what Rex should DO for each wake-up trigger.
    Current triggers fire but actions are placeholders.
    For each trigger below, define the concrete response:
      - "d_metric_overload": D > 300 → what action? (e.g., "run TODO audit + compress docs")
      - "todo_crisis":       load > 0.7 → what action? (e.g., "auto-close stale TODOs older than 30d")
      - "dev_stalled":       < 1 commit/day → what action? (e.g., "alert human + run probe")
      - "knowledge_stagnant": insight < 1.0 → what action? (e.g., "trigger exploratory agent")
      - "health_critical":   composite < 0.3 → what action? (e.g., "emergency sprint protocol")
    """
    triggers = []

    if metrics["d_metric"]["value"] > 300:
        triggers.append({
            "condition": "d_metric_overload",
            "value": metrics["d_metric"]["value"],
            "action": "SPRINT_NEEDED",  # TODO(human): define concrete action
        })

    if metrics["todo_load"]["value"] > 0.7:
        triggers.append({
            "condition": "todo_crisis",
            "value": metrics["todo_load"]["value"],
            "action": "TRIAGE_TODOS",
        })

    if metrics["commit_frequency"]["value"] < 1.0:
        triggers.append({
            "condition": "dev_stalled",
            "value": metrics["commit_frequency"]["value"],
            "action": "ALERT_HUMAN",
        })

    if metrics["insight_density"]["value"] < 1.0:
        triggers.append({
            "condition": "knowledge_stagnant",
            "value": metrics["insight_density"]["value"],
            "action": "TRIGGER_EXPLORATION",
        })

    if health < 0.3:
        triggers.append({
            "condition": "health_critical",
            "value": health,
            "action": "EMERGENCY_SPRINT",
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
            print(f"    >> {t['condition']}: {t['value']} → {t['action']}")
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
