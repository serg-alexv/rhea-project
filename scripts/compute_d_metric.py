#!/usr/bin/env python3
import json
import sys

METRICS_FILE = "metrics/memory_metrics.json"
T2_THRESHOLD = 300.0

def main():
    """
    Reads the D-metric from the metrics file, prints it,
    and returns a non-zero exit code if it exceeds the T2 threshold.
    """
    try:
        with open(METRICS_FILE, "r") as f:
            metrics = json.load(f)
    except FileNotFoundError:
        print(f"Error: Metrics file not found at {METRICS_FILE}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {METRICS_FILE}", file=sys.stderr)
        sys.exit(1)

    d_metric = metrics.get("discomfort_metric_d")

    if d_metric is None:
        print(f"Error: 'discomfort_metric_d' not found in {METRICS_FILE}", file=sys.stderr)
        sys.exit(1)

    print(f"D-Metric: {d_metric}")

    if d_metric > T2_THRESHOLD:
        print(f"Warning: D-metric ({d_metric}) exceeds T2 threshold ({T2_THRESHOLD}). [SPRINT NEEDED]", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
