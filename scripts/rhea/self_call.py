#!/usr/bin/env python3
"""
self_call.py — controlled long-task loop with explicit checkpoints.

Purpose:
  Keep execution continuous ("always do something") while preserving operator control.

Commands:
  start     Begin a new self-call session
  step      Append one concrete step (observe/plan/execute/verify/checkpoint)
  status    Show current session state
  autonext  Suggest next mode from current state
  guard     Enforce budget/inactivity gates
  stop      Close active session and persist summary
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


VALID_MODES = {"observe", "plan", "execute", "verify", "checkpoint"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_root() -> Path:
    override = os.getenv("RHEA_SELF_CALL_DIR")
    if override:
        return Path(override)
    return repo_root() / ".rhea" / "self_call"


def ensure_dirs(root: Path) -> None:
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "sessions").mkdir(parents=True, exist_ok=True)


def write_json_atomic(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def active_path(root: Path) -> Path:
    return root / "active.json"


def load_active(root: Path) -> Dict[str, Any] | None:
    p = active_path(root)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_active(root: Path, state: Dict[str, Any]) -> None:
    write_json_atomic(active_path(root), state)


def elapsed_minutes(started_at: str) -> int:
    delta = datetime.now(timezone.utc) - parse_iso(started_at)
    return max(0, int(delta.total_seconds() // 60))


def compute_budget(state: Dict[str, Any]) -> Dict[str, Any]:
    elapsed = elapsed_minutes(state["started_at"])
    budget_min = int(state["budget_minutes"])
    budget_tokens = int(state["budget_tokens"])
    tokens_used = int(state["tokens_used"])

    time_ratio = elapsed / budget_min if budget_min > 0 else 1.0
    token_ratio = tokens_used / budget_tokens if budget_tokens > 0 else 1.0
    return {
        "elapsed_minutes": elapsed,
        "time_ratio": round(time_ratio, 3),
        "token_ratio": round(token_ratio, 3),
        "minutes_left": max(0, budget_min - elapsed),
        "tokens_left": max(0, budget_tokens - tokens_used),
        "over_time": elapsed > budget_min,
        "over_tokens": tokens_used > budget_tokens,
    }


def cmd_start(args: argparse.Namespace) -> int:
    root = data_root()
    ensure_dirs(root)
    existing = load_active(root)
    if existing and not args.force:
        print(
            json.dumps(
                {
                    "status": "error",
                    "reason": "active_session_exists",
                    "active_id": existing["id"],
                    "hint": "use stop or start --force",
                },
                ensure_ascii=False,
            )
        )
        return 1

    session_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    event_path = root / "events" / f"{session_id}.jsonl"
    state = {
        "id": session_id,
        "status": "active",
        "goal": args.goal,
        "started_at": now_iso(),
        "last_step_at": None,
        "steps": 0,
        "tokens_used": 0,
        "budget_tokens": int(args.budget_tokens),
        "budget_minutes": int(args.budget_minutes),
        "interval_minutes": int(args.interval_minutes),
        "last_mode": None,
        "next_hint": "observe",
        "event_path": str(event_path),
    }
    save_active(root, state)
    append_jsonl(
        event_path,
        {
            "ts": now_iso(),
            "kind": "start",
            "session_id": session_id,
            "goal": args.goal,
            "budget_tokens": int(args.budget_tokens),
            "budget_minutes": int(args.budget_minutes),
            "interval_minutes": int(args.interval_minutes),
        },
    )
    print(json.dumps({"status": "started", "id": session_id, "goal": args.goal}, ensure_ascii=False))
    return 0


def cmd_step(args: argparse.Namespace) -> int:
    root = data_root()
    ensure_dirs(root)
    state = load_active(root)
    if not state:
        print(json.dumps({"status": "error", "reason": "no_active_session"}, ensure_ascii=False))
        return 1

    mode = args.mode
    if mode not in VALID_MODES:
        print(json.dumps({"status": "error", "reason": "invalid_mode", "mode": mode}, ensure_ascii=False))
        return 1

    step_no = int(state["steps"]) + 1
    token_delta = int(args.tokens)
    token_delta = max(token_delta, 0)
    state["steps"] = step_no
    state["tokens_used"] = int(state["tokens_used"]) + token_delta
    state["last_mode"] = mode
    state["last_step_at"] = now_iso()
    state["next_hint"] = args.next or suggest_next_mode(state)
    save_active(root, state)

    event = {
        "ts": now_iso(),
        "kind": "step",
        "session_id": state["id"],
        "step": step_no,
        "mode": mode,
        "what": args.what,
        "tokens": token_delta,
        "evidence": args.evidence,
        "next": state["next_hint"],
    }
    append_jsonl(Path(state["event_path"]), event)
    print(json.dumps({"status": "stepped", "step": step_no, "mode": mode, "next": state["next_hint"]}, ensure_ascii=False))
    return 0


def suggest_next_mode(state: Dict[str, Any]) -> str:
    last = state.get("last_mode")
    seq = {
        None: "observe",
        "observe": "plan",
        "plan": "execute",
        "execute": "verify",
        "verify": "checkpoint",
        "checkpoint": "observe",
    }
    suggested = seq.get(last, "observe")
    budget = compute_budget(state)
    if budget["token_ratio"] >= 0.8 or budget["time_ratio"] >= 0.8:
        return "verify"
    return suggested


def cmd_status(_args: argparse.Namespace) -> int:
    root = data_root()
    ensure_dirs(root)
    state = load_active(root)
    if not state:
        print(json.dumps({"status": "idle"}, ensure_ascii=False))
        return 0
    budget = compute_budget(state)
    out = {
        "status": state["status"],
        "id": state["id"],
        "goal": state["goal"],
        "started_at": state["started_at"],
        "steps": state["steps"],
        "last_mode": state["last_mode"],
        "next_hint": state["next_hint"],
        "tokens_used": state["tokens_used"],
        "budget_tokens": state["budget_tokens"],
        "budget_minutes": state["budget_minutes"],
        "interval_minutes": state["interval_minutes"],
        "budget": budget,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_autonext(_args: argparse.Namespace) -> int:
    root = data_root()
    ensure_dirs(root)
    state = load_active(root)
    if not state:
        print(json.dumps({"status": "error", "reason": "no_active_session"}, ensure_ascii=False))
        return 1
    next_mode = suggest_next_mode(state)
    print(
        json.dumps(
            {
                "status": "ok",
                "session_id": state["id"],
                "next_mode": next_mode,
                "template": f"python3 scripts/rhea/self_call.py step --mode {next_mode} --what \"...\" --tokens 0",
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_guard(_args: argparse.Namespace) -> int:
    root = data_root()
    ensure_dirs(root)
    state = load_active(root)
    if not state:
        print(json.dumps({"status": "error", "reason": "no_active_session"}, ensure_ascii=False))
        return 2

    budget = compute_budget(state)
    reasons = []
    if budget["over_time"]:
        reasons.append("time_budget_exceeded")
    if budget["over_tokens"]:
        reasons.append("token_budget_exceeded")

    last_step = state.get("last_step_at")
    if last_step:
        idle_min = max(0, int((datetime.now(timezone.utc) - parse_iso(last_step)).total_seconds() // 60))
        if idle_min > int(state["interval_minutes"]):
            reasons.append("inactivity_exceeded")
    else:
        idle_min = elapsed_minutes(state["started_at"])
        if idle_min > int(state["interval_minutes"]):
            reasons.append("no_step_since_start")

    if reasons:
        print(json.dumps({"status": "fail", "reasons": reasons, "budget": budget}, ensure_ascii=False))
        return 1

    print(json.dumps({"status": "ok", "budget": budget}, ensure_ascii=False))
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    root = data_root()
    ensure_dirs(root)
    state = load_active(root)
    if not state:
        print(json.dumps({"status": "error", "reason": "no_active_session"}, ensure_ascii=False))
        return 1

    finished_at = now_iso()
    budget = compute_budget(state)
    append_jsonl(
        Path(state["event_path"]),
        {
            "ts": finished_at,
            "kind": "stop",
            "session_id": state["id"],
            "result": args.result,
            "notes": args.notes,
        },
    )

    session_doc = {
        "id": state["id"],
        "goal": state["goal"],
        "started_at": state["started_at"],
        "finished_at": finished_at,
        "summary": {
            "result": args.result,
            "notes": args.notes,
            "steps": state["steps"],
            "tokens_used": state["tokens_used"],
            "budget_tokens": state["budget_tokens"],
            "budget_minutes": state["budget_minutes"],
            "last_mode": state["last_mode"],
            "budget": budget,
        },
        "event_path": state["event_path"],
    }
    session_path = root / "sessions" / f"{state['id']}.json"
    write_json_atomic(session_path, session_doc)
    active_path(root).unlink(missing_ok=True)
    print(
        json.dumps(
            {"status": "stopped", "id": state["id"], "session_path": str(session_path), "result": args.result},
            ensure_ascii=False,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Rhea self-call controller")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_start = sub.add_parser("start", help="start a new self-call session")
    s_start.add_argument("--goal", required=True, help="session goal")
    s_start.add_argument("--budget-tokens", type=int, default=120000)
    s_start.add_argument("--budget-minutes", type=int, default=360)
    s_start.add_argument("--interval-minutes", type=int, default=25)
    s_start.add_argument("--force", action="store_true", help="replace existing active session")
    s_start.set_defaults(func=cmd_start)

    s_step = sub.add_parser("step", help="append one concrete step")
    s_step.add_argument("--mode", required=True, choices=sorted(VALID_MODES))
    s_step.add_argument("--what", required=True, help="action executed")
    s_step.add_argument("--tokens", type=int, default=0, help="token delta for this step")
    s_step.add_argument("--evidence", default="", help="path or note proving this step")
    s_step.add_argument("--next", default="", help="explicit next hint")
    s_step.set_defaults(func=cmd_step)

    s_status = sub.add_parser("status", help="show active session")
    s_status.set_defaults(func=cmd_status)

    s_autonext = sub.add_parser("autonext", help="suggest next mode")
    s_autonext.set_defaults(func=cmd_autonext)

    s_guard = sub.add_parser("guard", help="enforce budget and inactivity gates")
    s_guard.set_defaults(func=cmd_guard)

    s_stop = sub.add_parser("stop", help="stop active session and persist summary")
    s_stop.add_argument("--result", required=True, choices=["ok", "handoff", "abort"])
    s_stop.add_argument("--notes", default="")
    s_stop.set_defaults(func=cmd_stop)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
