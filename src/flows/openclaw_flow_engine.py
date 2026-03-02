#!/usr/bin/env python3
"""
openclaw_flow_engine.py — workflow-as-flow runtime for Rhea organization.

Implements OpenClaw-inspired pattern:
- explicit stateful flows
- deterministic step execution
- append-only run ledger
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
LOG_FILE = ROOT / "opera" / "metrics" / "workflow_runs.jsonl"

sys.path.insert(0, str(ROOT / "src"))
from task_db import TaskDB  # noqa: E402


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append_log(obj: dict[str, Any]) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def run_cmd(cmd: list[str], timeout: int = 60) -> tuple[bool, str, str, int]:
    p = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return (p.returncode == 0, p.stdout or "", p.stderr or "", p.returncode)


@dataclass
class FlowStep:
    id: str
    action: str
    on_fail: str = "abort"  # abort|continue
    timeout_s: int = 60


@dataclass
class FlowSpec:
    id: str
    title: str
    steps: list[FlowStep]


FLOWS: dict[str, FlowSpec] = {
    "openclaw.org.sync": FlowSpec(
        id="openclaw.org.sync",
        title="P0 org sync to family ring with ack guarantees",
        steps=[
            FlowStep("health", "taskdb_health", "continue", 20),
            FlowStep("relay_send", "relay_send", "abort", 20),
            FlowStep("wait_ack", "relay_wait_ack", "continue", 45),
            FlowStep("wake", "wake_rex", "continue", 15),
            FlowStep("boot", "boot_rex", "continue", 45),
            FlowStep("wait_ack_retry", "relay_wait_ack", "abort", 45),
        ],
    ),
    "openclaw.continuity.smoke": FlowSpec(
        id="openclaw.continuity.smoke",
        title="Portability capsule pack + verify smoke",
        steps=[
            FlowStep("pack", "continuity_pack", "abort", 180),
            FlowStep("verify", "continuity_verify_latest", "abort", 120),
        ],
    ),
    "openclaw.p0.recovery": FlowSpec(
        id="openclaw.p0.recovery",
        title="Fast recovery lane: health + wake + boot",
        steps=[
            FlowStep("health", "taskdb_health", "continue", 20),
            FlowStep("wake", "wake_rex", "continue", 15),
            FlowStep("boot", "boot_rex", "continue", 45),
        ],
    ),
}


def action_taskdb_health(ctx: dict[str, Any], payload: dict[str, Any], _step: FlowStep) -> tuple[bool, dict[str, Any]]:
    db = TaskDB()
    summary = db.summary(stale_hours=int(payload.get("stale_hours", 2)))
    # Non-fatal health for org flows; caller decides escalation policy.
    return True, {"summary": summary}


def action_relay_send(ctx: dict[str, Any], payload: dict[str, Any], step: FlowStep) -> tuple[bool, dict[str, Any]]:
    msg = str(payload.get("message", "")).strip()
    if not msg:
        return False, {"error": "missing payload.message"}
    source = str(payload.get("source", "ORION")).upper()
    targets = str(payload.get("targets", "REX")).upper()
    priority = str(payload.get("priority", "P0")).upper()
    ttl = int(payload.get("ttl", 3600))

    ok, out, err, rc = run_cmd(
        [
            "python3",
            "scripts/rhea_family.py",
            "send",
            "--source",
            source,
            "--targets",
            targets,
            "--priority",
            priority,
            "--ttl",
            str(ttl),
            msg,
        ],
        timeout=step.timeout_s,
    )
    details: dict[str, Any] = {"rc": rc, "stdout": out.strip()[-1500:], "stderr": err.strip()[-1500:]}
    if ok:
        try:
            j = json.loads(out.strip().splitlines()[-1])
            family_id = str(j.get("family_id", "")).strip()
            if family_id:
                ctx["family_id"] = family_id
                details["family_id"] = family_id
        except Exception:
            pass
    return ok, details


def action_relay_wait_ack(ctx: dict[str, Any], payload: dict[str, Any], step: FlowStep) -> tuple[bool, dict[str, Any]]:
    family_id = str(payload.get("family_id") or ctx.get("family_id") or "").strip()
    if not family_id:
        return False, {"error": "missing family_id in context/payload"}
    timeout = int(payload.get("ack_timeout", step.timeout_s))

    ok, out, err, rc = run_cmd(
        ["python3", "scripts/rhea_family.py", "wait", "--timeout", str(timeout), family_id],
        timeout=timeout + 10,
    )
    details: dict[str, Any] = {"rc": rc, "stdout": out.strip()[-2000:], "stderr": err.strip()[-1500:]}
    try:
        j = json.loads(out.strip() or "{}")
        details["all_acked"] = bool(j.get("all_acked"))
        details["status_json"] = j
        return bool(j.get("all_acked")), details
    except Exception:
        return ok, details


def action_wake_rex(_ctx: dict[str, Any], _payload: dict[str, Any], step: FlowStep) -> tuple[bool, dict[str, Any]]:
    ok, out, err, rc = run_cmd(["curl", "-sS", "-m", "8", "-X", "POST", "http://localhost:8400/agents/wake/REX"], timeout=step.timeout_s)
    return ok, {"rc": rc, "stdout": out.strip()[-1000:], "stderr": err.strip()[-1000:]}


def action_boot_rex(_ctx: dict[str, Any], _payload: dict[str, Any], step: FlowStep) -> tuple[bool, dict[str, Any]]:
    ok, out, err, rc = run_cmd(["python3", "opera/ops/rex_pager.py", "boot", "REX"], timeout=step.timeout_s)
    return ok, {"rc": rc, "stdout": out.strip()[-2000:], "stderr": err.strip()[-1500:]}


def action_continuity_pack(ctx: dict[str, Any], payload: dict[str, Any], step: FlowStep) -> tuple[bool, dict[str, Any]]:
    label = str(payload.get("label") or f"flow-{datetime.now(timezone.utc).strftime('%Y%m%dt%H%M%Sz').lower()}")
    ok, out, err, rc = run_cmd(["python3", "scripts/continuity_capsule.py", "pack", "--label", label], timeout=step.timeout_s)
    details: dict[str, Any] = {"rc": rc, "stdout": out.strip()[-2000:], "stderr": err.strip()[-1500:]}
    if ok:
        latest_path = ROOT / "archive" / "continuity_capsules" / "LATEST.json"
        if latest_path.exists():
            try:
                latest = json.loads(latest_path.read_text(encoding="utf-8"))
                ctx["latest_bundle"] = latest.get("bundle")
                details["latest"] = latest
            except Exception:
                pass
    return ok, details


def action_continuity_verify_latest(ctx: dict[str, Any], _payload: dict[str, Any], step: FlowStep) -> tuple[bool, dict[str, Any]]:
    bundle_rel = str(ctx.get("latest_bundle", "")).strip()
    if not bundle_rel:
        latest = ROOT / "archive" / "continuity_capsules" / "LATEST.json"
        if not latest.exists():
            return False, {"error": "LATEST.json missing"}
        try:
            bundle_rel = str(json.loads(latest.read_text(encoding="utf-8")).get("bundle", "")).strip()
        except Exception:
            return False, {"error": "LATEST.json invalid"}
    if not bundle_rel:
        return False, {"error": "bundle path empty"}
    ok, out, err, rc = run_cmd(["python3", "scripts/continuity_capsule.py", "verify", bundle_rel], timeout=step.timeout_s)
    details: dict[str, Any] = {"rc": rc, "stdout": out.strip()[-2000:], "stderr": err.strip()[-1500:], "bundle": bundle_rel}
    try:
        details["verify"] = json.loads(out.strip() or "{}")
    except Exception:
        pass
    return ok, details


ACTIONS: dict[str, Callable[[dict[str, Any], dict[str, Any], FlowStep], tuple[bool, dict[str, Any]]]] = {
    "taskdb_health": action_taskdb_health,
    "relay_send": action_relay_send,
    "relay_wait_ack": action_relay_wait_ack,
    "wake_rex": action_wake_rex,
    "boot_rex": action_boot_rex,
    "continuity_pack": action_continuity_pack,
    "continuity_verify_latest": action_continuity_verify_latest,
}


def list_flows() -> list[dict[str, Any]]:
    return [{"id": f.id, "title": f.title, "steps": [s.id for s in f.steps]} for f in FLOWS.values()]


def run_flow(flow_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if flow_id not in FLOWS:
        return {"ok": False, "error": f"unknown flow: {flow_id}", "available": sorted(FLOWS.keys())}

    flow = FLOWS[flow_id]
    run_id = f"WF-{uuid.uuid4().hex[:8]}"
    started = now_iso()
    ctx: dict[str, Any] = {"run_id": run_id, "flow_id": flow_id, "started_at": started}
    steps_out: list[dict[str, Any]] = []

    append_log({"event": "workflow.start", "ts": started, "run_id": run_id, "flow_id": flow_id, "payload": payload})

    ok_all = True
    for step in flow.steps:
        fn = ACTIONS.get(step.action)
        if not fn:
            ok = False
            details = {"error": f"unknown action: {step.action}"}
        else:
            try:
                ok, details = fn(ctx, payload, step)
            except subprocess.TimeoutExpired:
                ok, details = False, {"error": f"timeout>{step.timeout_s}s"}
            except Exception as e:
                ok, details = False, {"error": str(e)[:500]}

        step_rec = {
            "ts": now_iso(),
            "run_id": run_id,
            "flow_id": flow_id,
            "step": step.id,
            "action": step.action,
            "ok": bool(ok),
            "on_fail": step.on_fail,
            "details": details,
        }
        steps_out.append(step_rec)
        append_log({"event": "workflow.step", **step_rec})

        if not ok:
            ok_all = False
            if step.on_fail == "abort":
                break

    ended = now_iso()
    result = {
        "ok": ok_all,
        "run_id": run_id,
        "flow_id": flow_id,
        "started_at": started,
        "ended_at": ended,
        "steps": steps_out,
        "context": {"family_id": ctx.get("family_id"), "latest_bundle": ctx.get("latest_bundle")},
    }
    append_log({"event": "workflow.end", "ts": ended, "run_id": run_id, "flow_id": flow_id, "ok": ok_all})
    return result


def latest_runs(limit: int = 10) -> list[dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    with LOG_FILE.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("event") == "workflow.end":
                rows.append(obj)
    return rows[-max(1, int(limit)) :]

