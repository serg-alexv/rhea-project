#!/usr/bin/env python3
"""
rhea_flow.py — CLI for OpenClaw-style workflow flows.

Usage:
  python3 scripts/rhea_flow.py list
  python3 scripts/rhea_flow.py run openclaw.org.sync --message "..."
  python3 scripts/rhea_flow.py latest --limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flows.openclaw_flow_engine import list_flows, latest_runs, run_flow  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Rhea workflow-as-flow runner")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list available flow specs")

    sp_run = sub.add_parser("run", help="run a flow")
    sp_run.add_argument("flow_id", help="flow id")
    sp_run.add_argument("--message", default="", help="message text for org sync flows")
    sp_run.add_argument("--targets", default="REX", help="comma-separated targets for relay")
    sp_run.add_argument("--source", default="ORION", help="sender")
    sp_run.add_argument("--priority", default="P0", help="relay priority")
    sp_run.add_argument("--ttl", type=int, default=3600, help="relay ttl seconds")
    sp_run.add_argument("--ack-timeout", type=int, default=40, help="ack wait timeout seconds")
    sp_run.add_argument("--label", default="", help="label for continuity flow")

    sp_latest = sub.add_parser("latest", help="show latest flow runs")
    sp_latest.add_argument("--limit", type=int, default=10, help="limit")

    args = p.parse_args()

    if args.cmd == "list":
        print(json.dumps({"flows": list_flows()}, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "run":
        payload = {
            "message": args.message,
            "targets": args.targets,
            "source": args.source,
            "priority": args.priority,
            "ttl": args.ttl,
            "ack_timeout": args.ack_timeout,
        }
        if args.label:
            payload["label"] = args.label
        res = run_flow(args.flow_id, payload)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if bool(res.get("ok")) else 2

    if args.cmd == "latest":
        print(json.dumps({"runs": latest_runs(args.limit)}, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

