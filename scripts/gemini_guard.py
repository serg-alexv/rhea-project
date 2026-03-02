#!/usr/bin/env python3
"""
gemini_guard.py — dedicated watchdog for stable GEMINI presence in live flow.

Responsibilities:
- keep GEMINI lease/activity alive
- detect degraded state from bridge logs
- auto-recover via wake/boot/probe
- emit compact pulse + append-only trace
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "gemini_guard"
STATE_FILE = STATE_DIR / "state.json"
STDOUT_LOG = STATE_DIR / "gemini_guard.stdout.log"
PULSE_FILE = ROOT / "opera" / "metrics" / "gemini_presence.json"
TRACE_FILE = ROOT / "opera" / "metrics" / "gemini_presence_trace.jsonl"
BRIDGE_LOG = ROOT / "logs" / "bridge_calls.jsonl"
REX_PAGER = ROOT / "opera" / "ops" / "rex_pager.py"

API_BASE_DEFAULT = "http://localhost:8400"
DEFAULT_MODELS = [
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-flash-8b",
    "gemini/gemini-2.0-flash",
]
DEFAULT_FALLBACK_MODELS = [
    "openrouter/google/gemini-2.5-pro-preview",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(raw: str) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PULSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {
            "runs": 0,
            "last_state": "unknown",
            "last_ok_probe_at": None,
            "last_error": None,
            "last_run": None,
        }
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "runs": 0,
            "last_state": "unknown",
            "last_ok_probe_at": None,
            "last_error": None,
            "last_run": None,
        }


def save_state(state: dict[str, Any]) -> None:
    state["last_run"] = now_iso()
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def append_trace(event: dict[str, Any]) -> None:
    payload = {"ts": now_iso(), **event}
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def notify(text: str, sound: str = "Hero") -> None:
    msg = text.replace("\\", "\\\\").replace('"', "'")
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{msg}" with title "RHEA GEMINI" sound name "{sound}"'],
            check=False,
            timeout=5,
        )
    except Exception:
        pass


def _http(method: str, url: str, timeout: int = 8) -> dict[str, Any]:
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", errors="replace")
    if not raw.strip():
        return {}
    return json.loads(raw)


def get_json(path: str, api_base: str) -> dict[str, Any]:
    return _http("GET", f"{api_base}{path}")


def post_json(path: str, api_base: str) -> dict[str, Any]:
    return _http("POST", f"{api_base}{path}")


def wake_agent(api_base: str) -> tuple[bool, str]:
    try:
        out = post_json("/agents/wake/GEMINI", api_base=api_base)
        return True, str(out.get("status", "wake_sent"))
    except Exception as e:
        return False, f"wake_err:{e}"


def boot_agent() -> tuple[bool, str]:
    try:
        out = subprocess.run(
            ["python3", str(REX_PAGER), "boot", "GEMINI"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=45,
        )
        if out.returncode == 0:
            return True, "boot_ok"
        err = ((out.stderr or "") + (out.stdout or "")).strip().replace("\n", " ")
        return False, f"boot_rc={out.returncode}:{err[:160]}"
    except Exception as e:
        return False, f"boot_err:{e}"


def _extract_json(text: str) -> dict[str, Any] | None:
    data = (text or "").strip()
    if not data:
        return None
    try:
        obj = json.loads(data)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    start = data.find("{")
    end = data.rfind("}")
    if start >= 0 and end > start:
        block = data[start : end + 1]
        try:
            obj = json.loads(block)
            if isinstance(obj, dict):
                return obj
        except Exception:
            return None
    return None


def probe_model(model: str, prompt: str, mode: str, env: dict[str, str]) -> dict[str, Any]:
    cmd = [
        "python3",
        "src/rhea_bridge.py",
        "ask",
        model,
        prompt,
        "--mode",
        mode,
    ]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False, timeout=120, env=env)
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    payload = _extract_json(out) or {}
    err = str(payload.get("error", "")).strip()
    ok = p.returncode == 0 and not err
    return {
        "ok": ok,
        "returncode": p.returncode,
        "provider": str(payload.get("provider", "")).strip(),
        "model": str(payload.get("model", model)).strip() or model,
        "latency_s": float(payload.get("latency_s", 0.0) or 0.0),
        "tokens_used": int(payload.get("tokens_used", 0) or 0),
        "error": err or ("" if ok else out.strip()[-240:]),
    }


def run_probe(
    models: list[str],
    prompt: str,
    mode: str,
    use_t1_key: bool = False,
) -> tuple[bool, dict[str, Any]]:
    env = os.environ.copy()
    using_t1 = False
    if use_t1_key:
        t1 = str(env.get("GEMINI_T1_API_KEY", "")).strip()
        if t1:
            env["GEMINI_API_KEY"] = t1
            using_t1 = True

    attempts: list[dict[str, Any]] = []
    for model in models:
        res = probe_model(model=model, prompt=prompt, mode=mode, env=env)
        attempts.append(res)
        if res.get("ok"):
            return True, {"attempts": attempts, "winner": res, "using_t1": using_t1}
    return False, {"attempts": attempts, "winner": None, "using_t1": using_t1}


def probe_gemini_cli(prompt: str) -> dict[str, Any]:
    try:
        p = subprocess.run(
            ["gemini", "--model", "gemini-2.5-flash-lite", "-p", prompt],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    except Exception as e:
        return {
            "ok": False,
            "provider": "gemini-cli",
            "model": "gemini-2.5-flash-lite",
            "error": str(e),
            "returncode": 1,
            "text_preview": "",
        }

    out = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    low = out.lower()
    fail_markers = (
        "authentication",
        "unauthorized",
        "quota",
        "exhausted",
        "permission denied",
        "api key",
        "forbidden",
    )
    marker_hit = any(m in low for m in fail_markers)
    ok = p.returncode == 0 and (not marker_hit)
    tail = out.splitlines()[-1] if out else ""
    return {
        "ok": ok,
        "provider": "gemini-cli",
        "model": "gemini-2.5-flash-lite",
        "error": "" if ok else tail[:220],
        "returncode": p.returncode,
        "text_preview": tail[:220],
    }


def _agent_snapshot(api_base: str) -> dict[str, Any]:
    try:
        st = get_json("/agents/status", api_base=api_base)
        agents = st.get("agents", {}) if isinstance(st, dict) else {}
        row = agents.get("GEMINI", {}) if isinstance(agents, dict) else {}
        if row:
            return {
                "alive": bool(row.get("alive", False)),
                "lease_expired": bool(row.get("lease_expired", True)),
                "lease_token": int(row.get("lease_token", 0) or 0),
                "last_activity": str(row.get("last_activity") or ""),
                "office_status": str(row.get("office_status") or "unknown"),
                "floor_gap": int(row.get("floor_gap", 0) or 0),
                "pace": str(row.get("pace") or "red"),
                "pending_msgs": int(row.get("pending_msgs", 0) or 0),
                "raw": row,
            }
    except Exception:
        pass

    try:
        st = get_json("/agents", api_base=api_base)
        row = {}
        if isinstance(st, dict):
            row = st.get("GEMINI") or st.get("gemini") or {}
        return {
            "alive": bool(row) and not bool(row.get("expired", True)),
            "lease_expired": bool(row.get("expired", True)),
            "lease_token": int(row.get("lease_token", 0) or 0),
            "last_activity": str(row.get("last_active") or ""),
            "office_status": "unknown",
            "floor_gap": 0,
            "pace": "red",
            "pending_msgs": 0,
            "raw": row or {},
        }
    except Exception:
        return {
            "alive": False,
            "lease_expired": True,
            "lease_token": 0,
            "last_activity": "",
            "office_status": "unknown",
            "floor_gap": 0,
            "pace": "red",
            "pending_msgs": 0,
            "raw": {},
        }


def _read_recent_gemini_calls(max_lines: int = 3000) -> list[dict[str, Any]]:
    if not BRIDGE_LOG.exists():
        return []

    lines = BRIDGE_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    rows: list[dict[str, Any]] = []
    for raw in lines[-max_lines:]:
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        provider = str(obj.get("provider", "")).lower()
        model = str(obj.get("model", "")).lower()
        agent_id = str(obj.get("agent_id", "")).lower()
        agent_name = str(obj.get("agent_name", "")).lower()
        if (
            provider == "gemini"
            or "gemini" in model
            or "gemini" in agent_id
            or "gemini" in agent_name
            or provider == "deepseek"
        ):
            rows.append(obj)
    return rows


def summarize_calls(rows: list[dict[str, Any]], now_dt: datetime, recent_window_s: int) -> dict[str, Any]:
    last_any = None
    last_ok = None
    last_err = None
    recent_err = 0
    consec_err = 0

    for r in rows:
        dt = parse_iso(str(r.get("timestamp", "")))
        if not dt:
            continue
        if (last_any is None) or dt > last_any:
            last_any = dt
        status = str(r.get("status", "")).lower()
        if status == "ok":
            if (last_ok is None) or dt > last_ok:
                last_ok = dt
        else:
            if (last_err is None) or dt > last_err:
                last_err = dt
            if (now_dt - dt).total_seconds() <= recent_window_s:
                recent_err += 1

    for r in reversed(rows):
        status = str(r.get("status", "")).lower()
        if status == "ok":
            break
        consec_err += 1

    idle_ref = last_ok or last_any
    idle_sec = int((now_dt - idle_ref).total_seconds()) if idle_ref else 10**9

    return {
        "calls_total": len(rows),
        "last_any": last_any.isoformat().replace("+00:00", "Z") if last_any else None,
        "last_ok": last_ok.isoformat().replace("+00:00", "Z") if last_ok else None,
        "last_error": last_err.isoformat().replace("+00:00", "Z") if last_err else None,
        "recent_errors": recent_err,
        "consecutive_errors": consec_err,
        "idle_sec": idle_sec,
    }


def _split_models(raw: str) -> list[str]:
    out = [x.strip() for x in str(raw).split(",") if x.strip()]
    return out


def run_pass(
    state: dict[str, Any],
    api_base: str,
    idle_threshold_s: int,
    err_threshold: int,
    recent_window_s: int,
    notify_enabled: bool,
    echo: bool,
    models: list[str],
    fallback_models: list[str],
    mode: str,
    cli_fallback: bool,
) -> dict[str, Any]:
    now_dt = datetime.now(timezone.utc)
    actions: list[str] = []
    errors: list[str] = []

    snap = _agent_snapshot(api_base=api_base)
    calls = summarize_calls(
        rows=_read_recent_gemini_calls(),
        now_dt=now_dt,
        recent_window_s=recent_window_s,
    )

    degraded = False
    reason = []
    if not snap.get("alive", False):
        degraded = True
        reason.append("agent_not_alive")
    if int(calls.get("idle_sec", 10**9)) > idle_threshold_s:
        degraded = True
        reason.append("idle_too_long")
    if int(calls.get("consecutive_errors", 0)) >= err_threshold:
        degraded = True
        reason.append("consecutive_errors")
    if int(calls.get("recent_errors", 0)) >= err_threshold:
        degraded = True
        reason.append("recent_errors")

    probe = {"ok": False, "path": "skipped", "winner": None, "attempts": []}

    if degraded:
        ok_w, msg_w = wake_agent(api_base=api_base)
        actions.append(f"wake:{msg_w}")
        if not ok_w:
            errors.append(f"wake:{msg_w}")

        ok_b, msg_b = boot_agent()
        actions.append(f"boot:{msg_b}")
        if not ok_b:
            errors.append(f"boot:{msg_b}")

        ok_probe, detail = run_probe(models=models, prompt="heartbeat::gemini_guard", mode=mode, use_t1_key=False)
        probe = {
            "ok": ok_probe,
            "path": "direct",
            **detail,
        }
        if not ok_probe:
            ok_t1, detail_t1 = run_probe(models=models, prompt="heartbeat::gemini_guard_t1", mode=mode, use_t1_key=True)
            if ok_t1:
                probe = {"ok": True, "path": "direct_t1", **detail_t1}
            else:
                probe = {"ok": False, "path": "direct_t1_failed", **detail_t1}

        if (not probe.get("ok")) and fallback_models:
            ok_fb, detail_fb = run_probe(
                models=fallback_models,
                prompt="heartbeat::gemini_guard_openrouter",
                mode=mode,
                use_t1_key=False,
            )
            probe = {
                "ok": ok_fb,
                "path": "openrouter_fallback",
                **detail_fb,
            }

        if (not probe.get("ok")) and cli_fallback:
            cli_res = probe_gemini_cli("heartbeat::gemini_guard_cli")
            probe = {
                "ok": bool(cli_res.get("ok", False)),
                "path": "gemini_cli",
                "attempts": [cli_res],
                "winner": cli_res if cli_res.get("ok") else None,
                "using_t1": False,
            }
    else:
        # Lightweight keepalive when healthy but nearly idle.
        if int(calls.get("idle_sec", 10**9)) > max(90, idle_threshold_s // 2):
            ok_probe, detail = run_probe(models=models[:1], prompt="heartbeat::gemini_soft", mode=mode, use_t1_key=False)
            probe = {"ok": ok_probe, "path": "soft", **detail}
            actions.append("soft_probe")
            if not ok_probe:
                degraded = True
                reason.append("soft_probe_failed")

    # Refresh snapshot after recovery attempt
    snap2 = _agent_snapshot(api_base=api_base)

    healthy = bool(snap2.get("alive", False)) and bool(probe.get("ok") or not degraded)
    state_name = "healthy" if healthy else ("recovering" if probe.get("ok") else "degraded")
    if errors and not probe.get("ok"):
        state_name = "critical"

    score = 100
    if not snap2.get("alive", False):
        score -= 40
    score -= min(30, int(calls.get("consecutive_errors", 0)) * 10)
    score -= min(20, int(calls.get("recent_errors", 0)) * 5)
    score -= min(20, int(calls.get("idle_sec", 0)) // 120)
    if probe.get("ok"):
        score = min(100, score + 20)
    score = max(0, score)

    payload = {
        "ts": now_iso(),
        "state": state_name,
        "score": score,
        "reason": reason,
        "agent": {
            "alive": bool(snap2.get("alive", False)),
            "lease_expired": bool(snap2.get("lease_expired", True)),
            "lease_token": int(snap2.get("lease_token", 0) or 0),
            "last_activity": snap2.get("last_activity"),
            "office_status": snap2.get("office_status"),
            "pace": snap2.get("pace"),
            "floor_gap": int(snap2.get("floor_gap", 0) or 0),
            "pending_msgs": int(snap2.get("pending_msgs", 0) or 0),
        },
        "bridge": calls,
        "probe": probe,
        "actions": actions,
        "errors": errors,
    }

    PULSE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_trace({"event": "gemini_presence", **payload})

    state["runs"] = int(state.get("runs", 0) or 0) + 1
    state["last_state"] = state_name
    if probe.get("ok"):
        state["last_ok_probe_at"] = now_iso()
        state["last_error"] = None
    elif errors:
        state["last_error"] = "; ".join(errors[:4])

    if notify_enabled:
        if state_name in {"critical", "degraded"}:
            notify(f"GEMINI {state_name} score={score} idle={calls.get('idle_sec', 0)}s", sound="Basso")
        elif state_name == "recovering":
            notify(f"GEMINI recovering score={score}", sound="Hero")

    if echo:
        print(
            f"[{payload['ts']}] gemini={state_name} score={score} "
            f"alive={payload['agent']['alive']} idle={calls.get('idle_sec', 0)} "
            f"err_recent={calls.get('recent_errors', 0)} err_streak={calls.get('consecutive_errors', 0)} "
            f"probe={probe.get('ok')} path={probe.get('path')}",
            flush=True,
        )

    return payload


def cmd_once(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    models = _split_models(args.models) or list(DEFAULT_MODELS)
    fallback_models = _split_models(args.fallback_models)
    try:
        run_pass(
            state=state,
            api_base=args.api,
            idle_threshold_s=max(60, int(args.idle_threshold)),
            err_threshold=max(1, int(args.error_threshold)),
            recent_window_s=max(30, int(args.recent_window)),
            notify_enabled=args.notify,
            echo=args.echo,
            models=models,
            fallback_models=fallback_models,
            mode=args.mode,
            cli_fallback=not args.no_cli_fallback,
        )
        save_state(state)
        return 0
    except Exception as e:
        tb = traceback.format_exc(limit=8)
        state["runs"] = int(state.get("runs", 0) or 0) + 1
        state["last_state"] = "guard_error"
        state["last_error"] = str(e)
        save_state(state)
        append_trace({"event": "gemini_presence.guard_error", "error": str(e), "traceback": tb})
        if args.notify:
            notify(f"GEMINI guard_error: {str(e)[:120]}", sound="Basso")
        if args.echo:
            print(f"[{now_iso()}] gemini=guard_error error={e}", flush=True)
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    models = _split_models(args.models) or list(DEFAULT_MODELS)
    fallback_models = _split_models(args.fallback_models)
    interval = max(10, int(args.interval))
    while True:
        if (ROOT / "STOP").exists():
            print("gemini_guard stopped by STOP sentinel")
            break
        if (ROOT / "PAUSE").exists():
            time.sleep(interval)
            continue
        try:
            run_pass(
                state=state,
                api_base=args.api,
                idle_threshold_s=max(60, int(args.idle_threshold)),
                err_threshold=max(1, int(args.error_threshold)),
                recent_window_s=max(30, int(args.recent_window)),
                notify_enabled=args.notify,
                echo=args.echo,
                models=models,
                fallback_models=fallback_models,
                mode=args.mode,
                cli_fallback=not args.no_cli_fallback,
            )
            save_state(state)
        except Exception as e:
            tb = traceback.format_exc(limit=8)
            state["runs"] = int(state.get("runs", 0) or 0) + 1
            state["last_state"] = "guard_error"
            state["last_error"] = str(e)
            save_state(state)
            append_trace({"event": "gemini_presence.guard_error", "error": str(e), "traceback": tb})
            if args.notify:
                notify(f"GEMINI guard_error: {str(e)[:120]}", sound="Basso")
            if args.echo:
                print(f"[{now_iso()}] gemini=guard_error error={e}", flush=True)
        time.sleep(interval)
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    pulse: dict[str, Any] = {}
    if PULSE_FILE.exists():
        try:
            pulse = json.loads(PULSE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pulse = {}
    out = {
        "state_file": str(STATE_FILE),
        "pulse_file": str(PULSE_FILE),
        "trace_file": str(TRACE_FILE),
        "stdout_log": str(STDOUT_LOG),
        "runs": int(state.get("runs", 0) or 0),
        "last_run": state.get("last_run"),
        "last_state": state.get("last_state"),
        "last_ok_probe_at": state.get("last_ok_probe_at"),
        "last_error": state.get("last_error"),
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
    p = argparse.ArgumentParser(description="Gemini presence guard")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_once = sub.add_parser("once")
    p_once.add_argument("--api", default=API_BASE_DEFAULT)
    p_once.add_argument("--notify", action="store_true")
    p_once.add_argument("--echo", action="store_true")
    p_once.add_argument("--idle-threshold", type=int, default=300)
    p_once.add_argument("--error-threshold", type=int, default=3)
    p_once.add_argument("--recent-window", type=int, default=900)
    p_once.add_argument("--mode", default="control")
    p_once.add_argument("--models", default=",".join(DEFAULT_MODELS))
    p_once.add_argument("--fallback-models", default=",".join(DEFAULT_FALLBACK_MODELS))
    p_once.add_argument("--no-cli-fallback", action="store_true")
    p_once.set_defaults(func=cmd_once)

    p_run = sub.add_parser("run")
    p_run.add_argument("--api", default=API_BASE_DEFAULT)
    p_run.add_argument("--interval", type=int, default=45)
    p_run.add_argument("--notify", action="store_true")
    p_run.add_argument("--echo", action="store_true")
    p_run.add_argument("--idle-threshold", type=int, default=300)
    p_run.add_argument("--error-threshold", type=int, default=3)
    p_run.add_argument("--recent-window", type=int, default=900)
    p_run.add_argument("--mode", default="control")
    p_run.add_argument("--models", default=",".join(DEFAULT_MODELS))
    p_run.add_argument("--fallback-models", default=",".join(DEFAULT_FALLBACK_MODELS))
    p_run.add_argument("--no-cli-fallback", action="store_true")
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
