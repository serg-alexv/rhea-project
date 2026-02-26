#!/usr/bin/env python3
"""
D-Metric: Old vs Proposed — side-by-side comparison.
Uses real data from metrics/memory_metrics.json.

Run: python3 scripts/d_metric_comparison.py
"""
import json
import math

METRICS_FILE = "metrics/memory_metrics.json"
T1 = 150.0
T2 = 300.0

# ── Old formula (current, broken) ──────────────────────────────
# D = w1*docs_kb + w2*repo_mb + w3*todos + w4*(1/insights) + w5*tokens
# Implied from current data: w1≈0.3, w2≈0.1, w3≈?, w4≈?, w5≈?
OLD_WEIGHTS = {
    "docs_kb":    0.3,
    "repo_mb":    0.1,
    "todos":      1.0,
    "inv_insights": 10.0,
    "tokens":     0.001,
}

# ── Proposed formula (log-scale + rebalanced) ──────────────────
# D = w1*log10(1+docs_kb) + w2*log10(1+repo_mb) + w3*sqrt(todos)
#   + w4*(1/insights) + w5*(tokens/1000)
#
# Weights calibrated so a "healthy but growing" project → D ≈ 100-200
# Cap: no single component > 40% of total
# TODO(human): Tune these weights and thresholds based on your gut feel.
# Current state (2692 KB docs, 522 MB repo, 0 todos) → D ≈ 202 with these defaults.
# Questions to ask yourself:
#   - Is 202 the right "feel" for current state? (mid-warning)
#   - If 25 open TODOs appeared, should that alone push you to OVERLOAD?
#   - Which input bothers you most: bloated docs, big repo, stale todos, or token burn?
# The ratio between weights matters more than absolute values.
NEW_WEIGHTS = {
    "docs_kb":    30.0,   # 30 * log10(2693) ≈ 103
    "repo_mb":    20.0,   # 20 * log10(523)  ≈ 54
    "todos":      15.0,   # 15 * sqrt(N)
    "inv_insights": 50.0, # 50 * (1/insights)
    "tokens":     10.0,   # 10 * (tokens/1000)
}
COMPONENT_CAP = 0.40  # no single component > 40% of total


def compute_old(m):
    w = OLD_WEIGHTS
    components = {
        "docs":     w["docs_kb"]      * m["core_docs_kb"],
        "repo":     w["repo_mb"]      * m["repo_size_mb"],
        "todos":    w["todos"]        * m["open_todo_count"],
        "insights": w["inv_insights"] * (1.0 / max(m["insights_per_request"], 0.01)),
        "tokens":   w["tokens"]       * m["avg_context_tokens_estimate"],
    }
    total = sum(components.values())
    return total, components


def compute_new(m):
    w = NEW_WEIGHTS
    components = {
        "docs":     w["docs_kb"]      * math.log10(1 + m["core_docs_kb"]),
        "repo":     w["repo_mb"]      * math.log10(1 + m["repo_size_mb"]),
        "todos":    w["todos"]        * math.sqrt(m["open_todo_count"]),
        "insights": w["inv_insights"] * (1.0 / max(m["insights_per_request"], 0.01)),
        "tokens":   w["tokens"]       * (m["avg_context_tokens_estimate"] / 1000.0),
    }

    # Component cap: if any component > 40% of total, clamp it
    raw_total = sum(components.values())
    if raw_total > 0:
        capped = {}
        cap_limit = COMPONENT_CAP * raw_total
        for k, v in components.items():
            capped[k] = min(v, cap_limit)
        components = capped

    total = sum(components.values())
    return total, components


def severity(d):
    if d < T1:   return "COMFORT"
    if d < T2:   return "WARNING (T1)"
    return "OVERLOAD (T2) [SPRINT NEEDED]"


def print_comparison(label, metrics):
    d_old, c_old = compute_old(metrics)
    d_new, c_new = compute_new(metrics)

    print(f"\n{'=' * 62}")
    print(f"  {label}")
    print(f"{'=' * 62}")
    print(f"  {'Input':25s} = {metrics['core_docs_kb']} KB docs, "
          f"{metrics['repo_size_mb']} MB repo, "
          f"{metrics['open_todo_count']} todos, "
          f"{metrics['insights_per_request']} ins/req, "
          f"{metrics['avg_context_tokens_estimate']} ctx tokens")
    print()

    # Old
    total_old = sum(c_old.values())
    print(f"  OLD FORMULA (linear)        D = {d_old:.1f}  [{severity(d_old)}]")
    for k, v in c_old.items():
        pct = (v / total_old * 100) if total_old > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"    {k:12s} {v:8.1f}  ({pct:4.1f}%)  {bar}")
    print()

    # New
    total_new = sum(c_new.values())
    print(f"  NEW FORMULA (log-scale)     D = {d_new:.1f}  [{severity(d_new)}]")
    for k, v in c_new.items():
        pct = (v / total_new * 100) if total_new > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"    {k:12s} {v:8.1f}  ({pct:4.1f}%)  {bar}")

    print(f"\n  Delta: {d_old:.1f} → {d_new:.1f}  "
          f"({'↓' if d_new < d_old else '↑'} {abs(d_old - d_new):.1f})")
    print(f"{'─' * 62}")


def main():
    with open(METRICS_FILE) as f:
        real = json.load(f)

    print("\n" + "█" * 62)
    print("  D-METRIC COMPARISON: Old (linear) vs Proposed (log-scale)")
    print("  Thresholds: T1={:.0f} (warning), T2={:.0f} (overload)".format(T1, T2))
    print("█" * 62)

    # ── Scenario 1: Current real data ──
    print_comparison("SCENARIO 1: Current state (real data)", real)

    # ── Scenario 2: Docs cleaned to 500 KB ──
    clean = {**real, "core_docs_kb": 500}
    print_comparison("SCENARIO 2: After doc cleanup (500 KB)", clean)

    # ── Scenario 3: Todo explosion (25 open tasks) ──
    todo_spike = {**real, "open_todo_count": 25}
    print_comparison("SCENARIO 3: Todo explosion (25 open)", todo_spike)

    # ── Scenario 4: Healthy project baseline ──
    healthy = {
        "core_docs_kb": 300,
        "repo_size_mb": 80,
        "open_todo_count": 3,
        "insights_per_request": 5.0,
        "avg_context_tokens_estimate": 2000,
    }
    print_comparison("SCENARIO 4: Healthy small project", healthy)

    # ── Scenario 5: Massive but organized ──
    massive = {
        "core_docs_kb": 10000,
        "repo_size_mb": 2000,
        "open_todo_count": 5,
        "insights_per_request": 4.0,
        "avg_context_tokens_estimate": 8000,
    }
    print_comparison("SCENARIO 5: Large but organized project", massive)

    print()


if __name__ == "__main__":
    main()
