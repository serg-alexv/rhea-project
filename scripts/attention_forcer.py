#!/usr/bin/env python3
"""
attention_forcer.py - force attention protocol for critical system events.

Behavior:
  - watch radio pulse risk
  - on trigger: unmute + set output volume, activate Music playback, emit sound/notification
  - write compact audit log
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "attention"
STATE_FILE = STATE_DIR / "state.json"
PULSE_FILE = ROOT / "opera" / "metrics" / "radio_pulse.json"
LOG_FILE = ROOT / "opera" / "metrics" / "attention_protocol.jsonl"

RISK_LEVEL = {"none": 0, "ok": 0, "info": 0, "warn": 1, "critical": 2}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {
            "last_trigger_epoch": 0,
            "last_trigger_ts": None,
            "last_reason": "",
            "last_risk": "none",
        }
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {
        "last_trigger_epoch": 0,
        "last_trigger_ts": None,
        "last_reason": "",
        "last_risk": "none",
    }


def save_state(state: dict) -> None:
    state["updated_at"] = now_iso()
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def append_log(event: dict) -> None:
    payload = {"ts": now_iso(), **event}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def sh(args: List[str], timeout: int = 6) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except Exception as exc:
        return 1, str(exc)


def osa(lines: List[str]) -> tuple[int, str]:
    args = ["osascript"]
    for line in lines:
        args.extend(["-e", line])
    return sh(args, timeout=8)


def parse_int(raw: str, default: int = 0) -> int:
    try:
        return int(str(raw).strip())
    except Exception:
        return default


def get_volume_state() -> dict:
    code1, out1 = osa(["output volume of (get volume settings)"])
    code2, out2 = osa(["output muted of (get volume settings)"])
    return {
        "output": parse_int(out1, 0) if code1 == 0 else 0,
        "muted": str(out2).strip().lower().startswith("true") if code2 == 0 else False,
        "ok": code1 == 0 and code2 == 0,
    }


def set_output_volume(level: int) -> bool:
    target = max(0, min(100, int(level)))
    code1, _ = osa(["set volume output muted false"])
    code2, _ = osa([f"set volume output volume {target}"])
    return code1 == 0 and code2 == 0


def notify(text: str) -> None:
    safe = text.replace("\\", "\\\\").replace('"', "'")
    osa([f'display notification "{safe}" with title "RHEA ATTENTION" sound name "Sosumi"'])


def speak(text: str) -> None:
    safe = text.replace('"', "'")
    sh(["say", safe], timeout=12)


def play_system_sound(name: str = "Sosumi", count: int = 2) -> None:
    sound = f"/System/Library/Sounds/{name}.aiff"
    p = Path(sound)
    if not p.exists():
        return
    for _ in range(max(1, count)):
        sh(["afplay", str(p)], timeout=4)


def music_attention(target_volume: int = 100) -> bool:
    lines = [
        'tell application "Music"',
        "if not running then launch",
        "activate",
        f"set sound volume to {max(0, min(100, int(target_volume)))}",
        "play",
        "end tell",
    ]
    code, _ = osa(lines)
    return code == 0


def load_pulse() -> dict:
    if not PULSE_FILE.exists():
        return {"risk": "none", "summary": "missing pulse"}
    try:
        obj = json.loads(PULSE_FILE.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return {"risk": "none", "summary": "invalid pulse"}


def should_trigger(pulse: dict, min_risk: str) -> bool:
    cur = str(pulse.get("risk", "none")).lower()
    need = str(min_risk).lower()
    return RISK_LEVEL.get(cur, 0) >= RISK_LEVEL.get(need, 2)


def run_attention(reason: str, pulse: dict, args: argparse.Namespace, state: dict, echo: bool) -> dict:
    before = get_volume_state()
    vol_changed = False
    if before["muted"] or int(before["output"]) < int(args.target_volume):
        vol_changed = set_output_volume(args.target_volume)
    after = get_volume_state()

    music_ok = False
    if args.music:
        music_ok = music_attention(target_volume=args.target_volume)
    if args.system_sound:
        play_system_sound(name=args.sound_name, count=args.sound_count)
    if args.notify:
        notify(f"{reason} | risk={pulse.get('risk', 'none')} | volume={after.get('output', 0)}")
    if args.speak:
        speak("Rhea alert. Attention required.")

    state["last_trigger_epoch"] = int(time.time())
    state["last_trigger_ts"] = now_iso()
    state["last_reason"] = reason
    state["last_risk"] = str(pulse.get("risk", "none"))

    event = {
        "event": "attention_trigger",
        "reason": reason,
        "pulse_risk": pulse.get("risk", "none"),
        "pulse_summary": str(pulse.get("summary", ""))[:200],
        "volume_before": before.get("output", 0),
        "muted_before": before.get("muted", False),
        "volume_after": after.get("output", 0),
        "muted_after": after.get("muted", False),
        "volume_changed": vol_changed,
        "music_ok": music_ok,
    }
    append_log(event)
    if echo:
        print(json.dumps(event, ensure_ascii=False))
    return event


def cmd_once(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    pulse = load_pulse()
    reason = args.reason.strip() or f"manual:{pulse.get('risk', 'none')}"
    run_attention(reason, pulse, args, state, echo=True)
    save_state(state)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    interval = max(2, int(args.interval))
    cooldown = max(5, int(args.cooldown))
    while True:
        pulse = load_pulse()
        risk = str(pulse.get("risk", "none")).lower()
        state["last_risk"] = risk
        should = should_trigger(pulse, args.min_risk)
        now_ep = int(time.time())
        last_ep = int(state.get("last_trigger_epoch", 0) or 0)
        elapsed = now_ep - last_ep
        if should and elapsed >= cooldown:
            reason = f"auto:pulse:{risk}"
            run_attention(reason, pulse, args, state, echo=args.echo)
        elif args.echo:
            print(
                json.dumps(
                    {
                        "event": "attention_idle",
                        "risk": risk,
                        "should_trigger": should,
                        "cooldown_left_s": max(0, cooldown - elapsed),
                        "ts": now_iso(),
                    },
                    ensure_ascii=False,
                )
            )
        save_state(state)
        time.sleep(interval)


def cmd_status(_args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    pulse = load_pulse()
    vol = get_volume_state()
    out = {
        "state_file": str(STATE_FILE),
        "log_file": str(LOG_FILE),
        "pulse_file": str(PULSE_FILE),
        "state": state,
        "pulse": {"risk": pulse.get("risk", "none"), "summary": str(pulse.get("summary", ""))[:200]},
        "volume": vol,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    ensure_dirs()
    n = max(1, int(args.n))
    if not LOG_FILE.exists():
        print(f"log missing: {LOG_FILE}")
        return 0
    lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-n:]:
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="RHEA forced attention protocol")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--target-volume", type=int, default=100, help="forced output volume (0..100)")
        sp.add_argument("--music", action="store_true", help="activate Apple Music and play")
        sp.add_argument("--system-sound", action="store_true", help="play system alarm sound")
        sp.add_argument("--sound-name", default="Sosumi", help="system sound name from /System/Library/Sounds")
        sp.add_argument("--sound-count", type=int, default=2, help="number of alarm repetitions")
        sp.add_argument("--notify", action="store_true", help="macOS notification")
        sp.add_argument("--speak", action="store_true", help="speech synthesis")

    sp_once = sub.add_parser("once", help="trigger attention immediately")
    common(sp_once)
    sp_once.add_argument("--reason", default="manual", help="reason text")
    sp_once.set_defaults(func=cmd_once)

    sp_run = sub.add_parser("run", help="daemon mode")
    common(sp_run)
    sp_run.add_argument("--interval", type=int, default=5, help="poll interval seconds")
    sp_run.add_argument("--cooldown", type=int, default=180, help="min seconds between forced triggers")
    sp_run.add_argument("--min-risk", default="critical", choices=["warn", "critical"], help="trigger threshold")
    sp_run.add_argument("--echo", action="store_true", help="echo loop events")
    sp_run.set_defaults(func=cmd_run)

    sp_status = sub.add_parser("status", help="show protocol status")
    sp_status.set_defaults(func=cmd_status)

    sp_tail = sub.add_parser("tail", help="print recent attention log rows")
    sp_tail.add_argument("-n", type=int, default=30, help="line count")
    sp_tail.set_defaults(func=cmd_tail)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

