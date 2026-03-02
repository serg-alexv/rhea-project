#!/usr/bin/env python3
"""
axiom_contract.py — executable axiom checks (behavior > text).

A0 contract (from operator doctrine):
  pass iff last semantic act of agent is PUSH/ACTION, not REPORT/STATUS.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OFFICE_LOG = ROOT / "data" / "office.jsonl"


ACTION_HINTS = (
    "wake",
    "boot",
    "claim",
    "deploy",
    "ship",
    "send",
    "broadcast",
    "push",
    "fix",
    "patch",
    "implement",
    "run",
    "start",
    "restart",
    "sync",
    "apply",
    "execute",
    "relay",
    "done",
)

REPORT_HINTS = (
    "status",
    "report",
    "summary",
    "state",
    "monitor",
    "metrics",
    "logs",
    "checked",
    "verified",
    "analysis",
    "insight",
    "snapshot",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(raw: str) -> datetime | None:
    if not raw:
        return None
    s = str(raw).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _text_of(rec: dict[str, Any]) -> str:
    return str(rec.get("compressed") or rec.get("text") or "").strip()


def classify_semantic_action(text: str) -> str:
    low = text.lower()
    has_action = any(h in low for h in ACTION_HINTS)
    has_report = any(h in low for h in REPORT_HINTS)
    if has_action and not has_report:
        return "push"
    if has_report and not has_action:
        return "report"
    if has_action and has_report:
        # Tie-break: action wins because it is operationally falsifiable.
        return "push"
    return "unknown"


def load_agent_events(agent: str, limit: int) -> list[dict[str, Any]]:
    if not OFFICE_LOG.exists():
        return []
    a = agent.lower().strip()
    rows: list[dict[str, Any]] = []
    for raw in OFFICE_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        sender = str(rec.get("sender", "")).lower().strip()
        if sender != a:
            continue
        ts = parse_ts(str(rec.get("ts", "")))
        if ts is None:
            continue
        rows.append(
            {
                "id": rec.get("id", ""),
                "sender": sender,
                "receiver": str(rec.get("receiver", "")).lower(),
                "text": _text_of(rec),
                "ts": ts,
                "ts_raw": rec.get("ts", ""),
            }
        )
    rows.sort(key=lambda r: r["ts"])
    return rows[-max(1, limit) :]


@dataclass
class A0State:
    agent: str
    last_event_id: str | None
    last_event_ts: str | None
    last_event_text: str | None
    last_action_type: str
    last_push_ts: str | None
    last_report_ts: str | None
    last_push_id: str | None
    last_report_id: str | None


def evaluate_a0(agent: str, events: list[dict[str, Any]]) -> tuple[bool, A0State]:
    last_push: dict[str, Any] | None = None
    last_report: dict[str, Any] | None = None
    last_event: dict[str, Any] | None = events[-1] if events else None

    for ev in events:
        kind = classify_semantic_action(ev["text"])
        if kind == "push":
            last_push = ev
        elif kind == "report":
            last_report = ev

    if not last_event:
        state = A0State(
            agent=agent.lower(),
            last_event_id=None,
            last_event_ts=None,
            last_event_text=None,
            last_action_type="unknown",
            last_push_ts=None,
            last_report_ts=None,
            last_push_id=None,
            last_report_id=None,
        )
        return False, state

    # Determine semantic class of last event directly.
    last_kind = classify_semantic_action(last_event["text"])
    if last_kind == "unknown":
        # If unknown, infer from latest known push/report timestamps.
        if last_push and (not last_report or last_push["ts"] >= last_report["ts"]):
            last_kind = "push"
        elif last_report:
            last_kind = "report"

    state = A0State(
        agent=agent.lower(),
        last_event_id=str(last_event.get("id") or ""),
        last_event_ts=str(last_event.get("ts_raw") or ""),
        last_event_text=str(last_event.get("text") or "")[:240],
        last_action_type=last_kind,
        last_push_ts=(str(last_push.get("ts_raw")) if last_push else None),
        last_report_ts=(str(last_report.get("ts_raw")) if last_report else None),
        last_push_id=(str(last_push.get("id")) if last_push else None),
        last_report_id=(str(last_report.get("id")) if last_report else None),
    )
    passed = state.last_action_type == "push"
    return passed, state


def cmd_check(args: argparse.Namespace) -> int:
    axiom = str(args.axiom or "A0").upper().strip()
    if axiom != "A0":
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"unknown axiom '{axiom}'",
                    "supported": ["A0"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    events = load_agent_events(agent=args.agent, limit=max(1, int(args.limit)))
    passed, state = evaluate_a0(agent=args.agent, events=events)

    # keep formula explicit and executable
    gradient_gt_0 = bool(passed)
    bottom = bool(not passed)
    expr = bool(gradient_gt_0 or bottom)

    verdict = "PASS" if passed else "FAIL"
    payload = {
        "ok": True,
        "ts": now_iso(),
        "axiom": "A0",
        "agent": args.agent.lower(),
        "events_considered": len(events),
        "passed": passed,
        "verdict": verdict,
        "state": asdict(state),
        "formula": {
            "gradient_gt_0": gradient_gt_0,
            "bottom": bottom,
            "expr": expr,
            "expr_text": "∇ > 0 ∨ ⊥",
        },
        "rule": "pass iff last semantic act is PUSH/ACTION, not REPORT/STATUS",
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"A0 {verdict} | agent={payload['agent']} | "
            f"last={state.last_action_type} | events={payload['events_considered']}"
        )
        print(json.dumps(payload["state"], ensure_ascii=False, indent=2))
    return 0 if passed else 1


def cmd_check_fleet(args: argparse.Namespace) -> int:
    axiom = str(args.axiom or "A0").upper().strip()
    if axiom != "A0":
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"unknown axiom '{axiom}'",
                    "supported": ["A0"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    agents = [a.strip().lower() for a in str(args.agents).split(",") if a.strip()]
    limit = max(1, int(args.limit))
    rows = []
    for a in agents:
        events = load_agent_events(agent=a, limit=limit)
        passed, state = evaluate_a0(agent=a, events=events)
        rows.append(
            {
                "agent": a,
                "passed": passed,
                "events_considered": len(events),
                "last_action_type": state.last_action_type,
                "last_event_ts": state.last_event_ts,
                "last_event_id": state.last_event_id,
            }
        )

    passed_n = sum(1 for r in rows if r["passed"])
    total_n = len(rows)
    payload = {
        "ok": True,
        "ts": now_iso(),
        "axiom": axiom,
        "passed_agents": passed_n,
        "total_agents": total_n,
        "all_passed": passed_n == total_n,
        "results": rows,
        "rule": "A0 pass iff last semantic act is PUSH/ACTION, not REPORT/STATUS",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{axiom} fleet: {passed_n}/{total_n} pass")
        for r in rows:
            mark = "PASS" if r["passed"] else "FAIL"
            print(
                f"  {mark:4s} {r['agent']:9s} "
                f"last={r['last_action_type']:7s} events={r['events_considered']}"
            )
    return 0 if payload["all_passed"] else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Executable axiom contracts")
    sub = p.add_subparsers(dest="cmd", required=True)

    chk = sub.add_parser("check")
    chk.add_argument("--axiom", default="A0")
    chk.add_argument("--agent", default="orion")
    chk.add_argument("--limit", type=int, default=200)
    chk.add_argument("--json", action="store_true")
    chk.set_defaults(func=cmd_check)

    fleet = sub.add_parser("check-fleet")
    fleet.add_argument("--axiom", default="A0")
    fleet.add_argument("--agents", default="rex,orion,gemini,hyperion,gpt,shared")
    fleet.add_argument("--limit", type=int, default=200)
    fleet.add_argument("--json", action="store_true")
    fleet.set_defaults(func=cmd_check_fleet)
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
