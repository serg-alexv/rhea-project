#!/usr/bin/env python3
"""
flow_up_guard.py — keep system in "flowing-up" mode continuously.

What it does on each pass:
- wakes/boots expired core agents
- auto-claims open tasks across alive agents
- re-wakes stale task owners
- emits compact pulse for UI: opera/metrics/flow_up.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "flow_up"
STATE_FILE = STATE_DIR / "state.json"
PULSE_FILE = ROOT / "opera" / "metrics" / "flow_up.json"
TRACE_FILE = ROOT / "opera" / "metrics" / "flow_up_trace.jsonl"
REX_PAGER = ROOT / "opera" / "ops" / "rex_pager.py"

API_BASE = "http://localhost:8400"
CORE = ["REX", "ORION", "HYPERION", "GEMINI", "GPT", "SHARED"]
QUEUE_AGENT = {
    "REX": "rex",
    "ORION": "orion",
    "HYPERION": "hyperion",
    "GEMINI": "gemini",
    "GPT": "gpt",
    "SHARED": "shared",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_utc(raw: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return None


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PULSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"runs": 0, "rr_idx": 0, "last_score": 0, "last_state": "unknown", "last_run": None}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"runs": 0, "rr_idx": 0, "last_score": 0, "last_state": "unknown", "last_run": None}


def save_state(state: dict) -> None:
    state["last_run"] = now_iso()
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def append_trace(event: dict) -> None:
    payload = {"ts": now_iso(), **event}
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def notify(text: str, sound: str = "Hero") -> None:
    msg = text.replace("\\", "\\\\").replace('"', "'")
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{msg}" with title "RHEA FLOW" sound name "{sound}"'],
            check=False,
            timeout=5,
        )
    except Exception:
        pass


def osa(lines: List[str], timeout: int = 6) -> Tuple[int, str]:
    args = ["osascript"]
    for line in lines:
        args.extend(["-e", line])
    try:
        proc = subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout)
        out = ((proc.stdout or "") + (proc.stderr or "")).strip()
        return proc.returncode, out
    except Exception as e:
        return 1, str(e)


def parse_int(raw: str, default: int = 0) -> int:
    try:
        return int(str(raw).strip())
    except Exception:
        return default


def get_audio_state() -> dict:
    code_v, out_v = osa(["output volume of (get volume settings)"])
    code_m, out_m = osa(["output muted of (get volume settings)"])
    code_s, out_s = osa(
        [
            'tell application "Music"',
            "if running then",
            "return (player state as string)",
            "else",
            'return "stopped"',
            "end if",
            "end tell",
        ]
    )
    return {
        "ok": (code_v == 0 and code_m == 0),
        "volume": parse_int(out_v, 0) if code_v == 0 else 0,
        "muted": str(out_m).strip().lower().startswith("true") if code_m == 0 else False,
        "music_state": str(out_s).strip().lower() if code_s == 0 else "unknown",
    }


def mute_audio_channel() -> bool:
    code1, _ = osa(["set volume output muted true"])
    # if Music is active, pause it to avoid hidden playback resuming later
    code2, _ = osa(
        [
            'tell application "Music"',
            "if running then pause",
            "end tell",
        ]
    )
    return code1 == 0 and code2 == 0


def play_alarm_ping() -> None:
    # short system ping without forcing full media playback
    try:
        subprocess.run(["afplay", "/System/Library/Sounds/Sosumi.aiff"], check=False, timeout=4)
    except Exception:
        pass


def _http(method: str, url: str, timeout: int = 6) -> dict:
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", errors="replace")
    if not raw.strip():
        return {}
    return json.loads(raw)


def get_json(path: str) -> dict:
    return _http("GET", f"{API_BASE}{path}")


def post_json(path: str) -> dict:
    return _http("POST", f"{API_BASE}{path}")


def wake_agent(agent: str) -> Tuple[bool, str]:
    try:
        out = post_json(f"/agents/wake/{agent.upper()}")
        return True, str(out.get("status", "ok"))
    except Exception as e:
        return False, f"wake_err:{e}"


def boot_agent(agent: str) -> Tuple[bool, str]:
    # Best-effort local boot to refresh lease + drain pending messages.
    try:
        out = subprocess.run(
            ["python3", str(REX_PAGER), "boot", agent.upper()],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=45,
        )
        ok = out.returncode == 0
        msg = "boot_ok" if ok else f"boot_rc={out.returncode}"
        return ok, msg
    except Exception as e:
        return False, f"boot_err:{e}"


def claim_task(task_id: str, agent_queue_name: str) -> Tuple[bool, str]:
    q = urllib.parse.quote(agent_queue_name)
    try:
        out = post_json(f"/tasks/{task_id}/claim?agent={q}")
        return True, str(out.get("id", task_id))
    except urllib.error.HTTPError as e:
        return False, f"http_{e.code}"
    except Exception as e:
        return False, f"claim_err:{e}"


def choose_agent_for_task(task: dict, alive: List[str], rr_idx: int) -> Tuple[str, int]:
    preferred = str(task.get("agent", "")).strip()
    preferred_u = preferred.upper()
    if preferred and preferred_u in QUEUE_AGENT and preferred_u in alive:
        return QUEUE_AGENT[preferred_u], rr_idx

    ring = alive if alive else CORE
    if not ring:
        return "shared", rr_idx
    pick = ring[rr_idx % len(ring)]
    rr_idx = (rr_idx + 1) % max(1, len(ring))
    return QUEUE_AGENT.get(pick, "shared"), rr_idx


def score_state(open_count: int, stale_count: int, expired_core: int, claimed_count: int) -> Tuple[int, str]:
    score = 100
    score -= min(45, 15 * open_count)
    score -= min(24, 8 * stale_count)
    score -= min(30, 5 * expired_core)
    if claimed_count == 0:
        score -= 15
    score = max(0, score)
    if score >= 80:
        return score, "flowing-up"
    if score >= 50:
        return score, "recovering"
    return score, "stalled"


def stale_evidence(summary: dict, tasks: List[dict]) -> Tuple[List[dict], Dict[str, int]]:
    stale_rows = summary.get("stale_tasks", []) or []
    task_by_id = {str(t.get("id", "")): t for t in tasks}
    now = datetime.now(timezone.utc)

    out: List[dict] = []
    by_priority: Dict[str, int] = {}
    for row in stale_rows:
        tid = str(row.get("id", "")).strip()
        if not tid:
            continue
        full = task_by_id.get(tid, {})
        prio = str(full.get("priority") or row.get("priority") or "P?").upper()
        updated_raw = str(full.get("updated") or row.get("updated") or "")
        updated_dt = parse_iso_utc(updated_raw)
        age_min = None
        if updated_dt is not None:
            age_min = int(max(0, (now - updated_dt).total_seconds()) // 60)
        by_priority[prio] = int(by_priority.get(prio, 0) or 0) + 1
        out.append(
            {
                "id": tid,
                "priority": prio,
                "claimed_by": str(full.get("claimed_by") or row.get("claimed_by") or "").lower(),
                "age_min": age_min,
                "updated": updated_raw,
                "title": str(full.get("title") or row.get("title") or "")[:140],
            }
        )
    out.sort(key=lambda r: int(r.get("age_min") or -1), reverse=True)
    return out, by_priority


def bank_level_assurance(
    open_count: int,
    stale_count: int,
    stale_p0_count: int,
    expired_core: int,
    errors: List[str],
    claimed_count: int,
) -> dict:
    violations: List[str] = []
    if expired_core > 0:
        violations.append(f"expired_core={expired_core}")
    if open_count > 0:
        violations.append(f"open_tasks={open_count}")
    if stale_count > 0:
        violations.append(f"stale_tasks={stale_count}")
    if stale_p0_count > 0:
        violations.append(f"stale_p0={stale_p0_count}")
    if errors:
        violations.append(f"errors={len(errors)}")
    if claimed_count == 0:
        violations.append("no_active_claims")

    return {
        "bank_level": len(violations) == 0,
        "violations": violations,
    }


def maybe_empty_flow_alarm(active_tasks: int, mode: str, loud_threshold: int, do_notify: bool) -> Optional[dict]:
    if active_tasks > 0:
        return None
    audio = get_audio_state()
    event = {
        "event": "empty_flow_alarm",
        "active_tasks": active_tasks,
        "mode": mode,
        "audio_before": audio,
        "action": "none",
        "muted": False,
    }

    chosen = mode
    if mode == "adaptive":
        loud_without_music = (int(audio.get("volume", 0)) >= int(loud_threshold)) and (audio.get("music_state") != "playing")
        chosen = "mute" if loud_without_music else "ping"

    if chosen == "mute":
        event["muted"] = mute_audio_channel()
        event["action"] = "mute_audio_channel"
        if do_notify:
            notify("empty flow: audio channel muted (already loud)", sound="Basso")
    else:
        play_alarm_ping()
        event["action"] = "alarm_ping"
        if do_notify:
            notify("empty flow: no active tasks", sound="Sosumi")

    append_trace(event)
    return event


def run_pass(
    state: dict,
    do_notify: bool = False,
    quiet: bool = False,
    alarm_on_empty: bool = True,
    alarm_mode: str = "adaptive",
    loud_threshold: int = 70,
) -> dict:
    actions: List[str] = []
    errors: List[str] = []

    try:
        agents = get_json("/agents")
        summary = get_json("/tasks/summary")
        tasks_payload = get_json("/tasks")
    except Exception as e:
        payload = {
            "ts": now_iso(),
            "state": "stalled",
            "score": 0,
            "trend": "down",
            "reason": f"api_unavailable:{e}",
            "actions": [],
            "errors": [str(e)],
        }
        PULSE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        append_trace({"event": "flow_up", **payload})
        if do_notify:
            notify("flow-up stalled: API unavailable", sound="Basso")
        return payload

    tasks = list(tasks_payload.get("tasks", []))
    counts = summary.get("counts", {})
    open_count = int(counts.get("open", 0) or 0)
    claimed_count = int(counts.get("claimed", 0) or 0)
    stale_count = int(summary.get("stale_count", 0) or 0)

    # 1) revive expired core agents
    expired = []
    alive = []
    for a in CORE:
        rec = agents.get(a) or agents.get(a.lower()) or {}
        if rec and not bool(rec.get("expired", True)):
            alive.append(a)
        else:
            expired.append(a)

    for a in expired:
        ok_w, msg_w = wake_agent(a)
        actions.append(f"wake:{a}:{msg_w}")
        if not ok_w:
            errors.append(f"wake:{a}:{msg_w}")
        ok_b, msg_b = boot_agent(a)
        actions.append(f"boot:{a}:{msg_b}")
        if not ok_b:
            errors.append(f"boot:{a}:{msg_b}")

    # refresh alive set after revive attempt
    try:
        agents2 = get_json("/agents")
    except Exception:
        agents2 = agents
    alive2 = []
    for a in CORE:
        rec = agents2.get(a) or agents2.get(a.lower()) or {}
        if rec and not bool(rec.get("expired", True)):
            alive2.append(a)

    # 2) auto-claim open tasks
    rr_idx = int(state.get("rr_idx", 0))
    open_tasks = [t for t in tasks if str(t.get("status")) == "open"]
    for t in open_tasks:
        tid = str(t.get("id", "")).strip()
        if not tid:
            continue
        target_agent, rr_idx = choose_agent_for_task(t, alive2, rr_idx)
        ok, msg = claim_task(tid, target_agent)
        actions.append(f"claim:{tid}:{target_agent}:{msg}")
        if not ok:
            errors.append(f"claim:{tid}:{target_agent}:{msg}")

    state["rr_idx"] = rr_idx

    # 3) nudge stale owners
    stale_tasks = summary.get("stale_tasks", []) or []
    for t in stale_tasks[:4]:
        owner = str(t.get("claimed_by", "")).strip().upper()
        if not owner:
            continue
        if owner in QUEUE_AGENT:
            ok_w, msg_w = wake_agent(owner)
            actions.append(f"stale_wake:{owner}:{msg_w}")
            if not ok_w:
                errors.append(f"stale_wake:{owner}:{msg_w}")

    expired_core = 0
    for a in CORE:
        rec = agents2.get(a) or agents2.get(a.lower()) or {}
        if not rec or bool(rec.get("expired", True)):
            expired_core += 1

    # refresh counts after action
    try:
        summary2 = get_json("/tasks/summary")
    except Exception:
        summary2 = summary
    counts2 = summary2.get("counts", {})
    open2 = int(counts2.get("open", 0) or 0)
    claimed2 = int(counts2.get("claimed", 0) or 0)
    stale2 = int(summary2.get("stale_count", 0) or 0)
    stale_rows, stale_by_priority = stale_evidence(summary2, tasks)
    stale_p0 = int(stale_by_priority.get("P0", 0) or 0)

    score, state_name = score_state(open2, stale2, expired_core, claimed2)
    # P0 staleness is a hard integrity breach: never label this as healthy flow.
    if stale_p0 > 0:
        score = min(score, 35)
        state_name = "stalled"
    prev_score = int(state.get("last_score", 0) or 0)
    trend = "up" if score > prev_score else ("down" if score < prev_score else "flat")
    assurance = bank_level_assurance(open2, stale2, stale_p0, expired_core, errors, claimed2)

    empty_alarm = None
    if alarm_on_empty:
        empty_alarm = maybe_empty_flow_alarm(open2 + claimed2, alarm_mode, loud_threshold, do_notify)

    payload = {
        "ts": now_iso(),
        "state": state_name,
        "score": score,
        "trend": trend,
        "tasks": {
            "open": open2,
            "claimed": claimed2,
            "done": int(counts2.get("done", 0) or 0),
            "stale": stale2,
            "stale_by_priority": stale_by_priority,
            "stale_sample": stale_rows[:6],
        },
        "agents": {
            "core": CORE,
            "alive": alive2,
            "expired_core": expired_core,
        },
        "assurance": assurance,
        "actions": actions,
        "errors": errors,
        "empty_flow_alarm": empty_alarm,
    }

    PULSE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_trace({"event": "flow_up", **payload})

    state["runs"] = int(state.get("runs", 0)) + 1
    state["last_score"] = score
    state["last_state"] = state_name

    if do_notify:
        if state_name != "flowing-up":
            notify(f"{state_name} score={score} open={open2} stale={stale2}", sound="Basso")
        elif trend == "up":
            notify(f"flow-up score={score} trend=up", sound="Hero")

    if not quiet:
        print(
            f"[{payload['ts']}] state={state_name} score={score} trend={trend} "
            f"open={open2} stale={stale2} expired={expired_core} actions={len(actions)} errors={len(errors)}",
            flush=True,
        )

    return payload


def cmd_once(args: argparse.Namespace) -> int:
    ensure_dirs()
    global API_BASE
    API_BASE = args.api
    state = load_state()
    run_pass(
        state,
        do_notify=args.notify,
        quiet=not args.echo,
        alarm_on_empty=not args.no_alarm_on_empty,
        alarm_mode=args.alarm_mode,
        loud_threshold=args.loud_threshold,
    )
    save_state(state)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ensure_dirs()
    global API_BASE
    API_BASE = args.api
    state = load_state()
    interval = max(5, int(args.interval))
    while True:
        if (ROOT / "STOP").exists():
            print("flow-up guard stopped by STOP sentinel")
            break
        if (ROOT / "PAUSE").exists():
            time.sleep(interval)
            continue
        run_pass(
            state,
            do_notify=args.notify,
            quiet=not args.echo,
            alarm_on_empty=not args.no_alarm_on_empty,
            alarm_mode=args.alarm_mode,
            loud_threshold=args.loud_threshold,
        )
        save_state(state)
        time.sleep(interval)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    pulse = {}
    if PULSE_FILE.exists():
        try:
            pulse = json.loads(PULSE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pulse = {}
    out = {
        "state_file": str(STATE_FILE),
        "pulse_file": str(PULSE_FILE),
        "trace_file": str(TRACE_FILE),
        "runs": int(state.get("runs", 0)),
        "last_run": state.get("last_run"),
        "last_state": state.get("last_state"),
        "last_score": state.get("last_score"),
        "pulse": pulse,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    if not TRACE_FILE.exists():
        print("[]")
        return 0
    n = max(1, int(args.n))
    rows = TRACE_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in rows[-n:]:
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Flow-up guard for always-moving system state")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_once = sub.add_parser("once")
    p_once.add_argument("--api", default="http://localhost:8400")
    p_once.add_argument("--notify", action="store_true")
    p_once.add_argument("--echo", action="store_true")
    p_once.add_argument("--no-alarm-on-empty", action="store_true")
    p_once.add_argument("--alarm-mode", choices=["adaptive", "ping", "mute"], default="adaptive")
    p_once.add_argument("--loud-threshold", type=int, default=70)
    p_once.set_defaults(func=cmd_once)

    p_run = sub.add_parser("run")
    p_run.add_argument("--api", default="http://localhost:8400")
    p_run.add_argument("--interval", type=int, default=20)
    p_run.add_argument("--notify", action="store_true")
    p_run.add_argument("--echo", action="store_true")
    p_run.add_argument("--no-alarm-on-empty", action="store_true")
    p_run.add_argument("--alarm-mode", choices=["adaptive", "ping", "mute"], default="adaptive")
    p_run.add_argument("--loud-threshold", type=int, default=70)
    p_run.set_defaults(func=cmd_run)

    p_status = sub.add_parser("status")
    p_status.set_defaults(func=cmd_status)

    p_tail = sub.add_parser("tail")
    p_tail.add_argument("-n", type=int, default=20)
    p_tail.set_defaults(func=cmd_tail)
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
