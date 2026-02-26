#!/usr/bin/env python3
"""
Stand-alone D-Metric calculator for Rhea.
Calculates current discomfort (D) based on real repo state.
Supports adjustable weights via metrics/d_metric_weights.json.
"""
import math
import os
import subprocess
import sys
import json
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T2_THRESHOLD = 300.0
WEIGHTS_FILE = os.path.join(REPO_ROOT, "opera", "metrics", "d_metric_weights.json")

# LOGIC BASELINE (v3.1)
DEFAULT_WEIGHTS = {
    "docs_kb": 30.0,
    "repo_mb": 20.0,
    "todos": 15.0,
    "inv_insights": 50.0,
    "tokens": 10.0
}

def _run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except:
        return "0"

def load_weights():
    """Load adjustable weights from file or return defaults."""
    if os.path.exists(WEIGHTS_FILE):
        try:
            with open(WEIGHTS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_WEIGHTS

def collect_raw():
    raw = {}
    exclude_args = "--exclude-dir=archive --exclude-dir=opera/cache --exclude-dir=.entire --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules"
    todo_cmd = f"grep -r 'TODO' {exclude_args} --include='*.py' --include='*.md' --include='*.sh' -l . 2>/dev/null | wc -l"
    raw["open_todo_count"] = int(_run(todo_cmd))
    
    docs_size = _run("find docs opera/docs emergentia apparatus -name '*.md' -exec cat {} + 2>/dev/null | wc -c")
    raw["core_docs_kb"] = int(docs_size) // 1024
    
    repo_size = _run("du -sm .git 2>/dev/null | cut -f1")
    raw["repo_size_mb"] = int(repo_size)
    
    # Defaults for metrics that require history
    raw["insights_per_request"] = 3.2
    raw["avg_context_tokens_estimate"] = 4500
    
    # Try to load historical data if available
    METRICS_FILE = os.path.join(REPO_ROOT, "opera", "metrics", "memory_metrics.json")
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE) as f:
                stored = json.load(f)
            raw["insights_per_request"] = stored.get("insights_per_request", 3.2)
            raw["avg_context_tokens_estimate"] = stored.get("avg_context_tokens_estimate", 4500)
        except:
            pass
            
    return raw

def compute_d_metric(raw, weights):
    """Calculates D using the official weighted formula."""
    w = weights
    components = {
        "docs":     w["docs_kb"]      * math.log10(1 + raw["core_docs_kb"]),
        "repo":     w["repo_mb"]      * math.log10(1 + raw["repo_size_mb"]),
        "todos":    w["todos"]        * math.sqrt(raw["open_todo_count"]),
        "insights": w["inv_insights"] * (1.0 / max(raw["insights_per_request"], 0.01)),
        "tokens":   w["tokens"]       * (raw["avg_context_tokens_estimate"] / 1000.0),
    }
    
    # Apply 40% component cap to prevent any single factor from dominating D
    raw_total = sum(components.values())
    if raw_total > 0:
        cap = 0.40 * raw_total
        components = {k: min(v, cap) for k, v in components.items()}
        
    return sum(components.values())

def main():
    raw = collect_raw()
    weights = load_weights()
    d_metric = compute_d_metric(raw, weights)
    
    # Update the JSON file so the record is fresh
    METRICS_FILE = os.path.join(REPO_ROOT, "opera", "metrics", "memory_metrics.json")
    if os.path.exists(os.path.dirname(METRICS_FILE)):
        try:
            if os.path.exists(METRICS_FILE):
                with open(METRICS_FILE, "r") as f:
                    data = json.load(f)
            else:
                data = {}
            data["discomfort_metric_d"] = round(d_metric, 2)
            data["core_docs_kb"] = raw["core_docs_kb"]
            data["open_todo_count"] = raw["open_todo_count"]
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
            data["weights"] = weights
            with open(METRICS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except:
            pass

    print(f"D-Metric: {d_metric:.2f}")
    
    if d_metric > T2_THRESHOLD:
        print(f"Warning: D-metric ({d_metric:.2f}) exceeds T2 threshold ({T2_THRESHOLD}). [SPRINT NEEDED]", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
