#!/usr/bin/env python3
"""
ndi_watchdog.py — local NDI/screen-capture trace and pulse monitor.

Goal:
  - detect suspicious or unexpected screen capture activity
  - emit compact trace events + pulse snapshot for UI/alerts

Artifacts:
  - opera/metrics/ndi_trace.jsonl
  - opera/metrics/ndi_pulse.json
  - .rhea/ndi/state.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "ndi"
STATE_FILE = STATE_DIR / "state.json"
TRACE_FILE = ROOT / "opera" / "metrics" / "ndi_trace.jsonl"
PULSE_FILE = ROOT / "opera" / "metrics" / "ndi_pulse.json"

PROC_PATTERN = re.compile(
    r"(\bndi\b|\bnewtek\b|\bobs\b|\bwirecast\b|\bvmix\b|\bscreenflick\b|\bcapto\b|\bcamtasia\b|\breplayd\b|zoom\.us|\bteams\b|\bwebex\b|\bdiscord\b|\bffmpeg\b)",
    re.IGNORECASE,
)
NDI_PATTERN = re.compile(r"(\bndi\b|\bnewtek\b)", re.IGNORECASE)
PORT_PATTERN = re.compile(r":(5353|5960|5961|5962|5963|5964|5965|5966|5967|5968|5969|5970)\b")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {
            "active_proc_ids": [],
            "active_ndi_ids": [],
            "active_ports": [],
            "last_tcc_hash": "",
            "last_risk": "none",
            "last_run": None,
        }
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "active_proc_ids": [],
            "active_ndi_ids": [],
            "active_ports": [],
            "last_tcc_hash": "",
            "last_risk": "none",
            "last_run": None,
        }


def save_state(state: dict) -> None:
    state["last_run"] = now_iso()
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def sh(args: List[str], timeout: int = 8) -> Tuple[int, str]:
    try:
        out = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        text = (out.stdout or "") + (out.stderr or "")
        return out.returncode, text
    except Exception as exc:
        return 1, str(exc)


def sample_processes() -> List[dict]:
    code, text = sh(["ps", "-axo", "pid,ppid,command"], timeout=6)
    if code != 0:
        return []
    out: List[dict] = []
    for raw in text.splitlines()[1:]:
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        pid, ppid, cmd = parts[0], parts[1], parts[2]
        self_noise = (
            "scripts/ndi_watchdog.py" in cmd
            or "scripts/rhea/ndi.sh" in cmd
            or "bash scripts/rhea.sh ndi" in cmd
            or "scripts/rhea.sh ndi " in cmd
        )
        if self_noise:
            continue
        if not PROC_PATTERN.search(cmd):
            continue
        out.append(
            {
                "pid": int(pid),
                "ppid": int(ppid),
                "cmd": cmd,
                "is_ndi": bool(NDI_PATTERN.search(cmd)),
            }
        )
    return out


def sample_ports() -> List[dict]:
    code, text = sh(["lsof", "-nP", "-iUDP", "-iTCP"], timeout=10)
    if code != 0:
        return []
    rows: List[dict] = []
    for raw in text.splitlines()[1:]:
        line = raw.strip()
        if not line or "->" in line:
            continue
        cols = line.split()
        if len(cols) < 9:
            continue
        cmd = cols[0]
        pid = cols[1]
        name = cols[-1]
        if not PORT_PATTERN.search(name):
            continue
        port_ndi = any(f":{p}" in name for p in ("5960", "5961", "5962", "5963", "5964", "5965", "5966", "5967", "5968", "5969", "5970"))
        port_discovery = ":5353" in name and bool(PROC_PATTERN.search(cmd))
        rows.append({"cmd": cmd, "pid": int(pid) if str(pid).isdigit() else -1, "name": name, "is_ndi_port": port_ndi or port_discovery})
    return rows


def sample_tcc_screen_capture() -> List[dict]:
    db = Path.home() / "Library" / "Application Support" / "com.apple.TCC" / "TCC.db"
    if not db.exists():
        return []
    query = (
        "SELECT client,auth_value,last_modified "
        "FROM access WHERE service='kTCCServiceScreenCapture' "
        "ORDER BY last_modified DESC LIMIT 64;"
    )
    code, text = sh(["sqlite3", str(db), query], timeout=6)
    if code != 0:
        return []
    rows: List[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 3:
            continue
        client, auth, last = parts
        rows.append({"client": client, "auth": int(auth or 0), "last_modified": int(last or 0)})
    return rows


def append_trace(event: dict) -> None:
    payload = {"ts": now_iso(), **event}
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def notify(text: str, sound: str = "Hero") -> None:
    msg = text.replace("\\", "\\\\").replace('"', "'")
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{msg}" with title "RHEA NDI" sound name "{sound}"'],
            check=False,
            timeout=5,
        )
    except Exception:
        pass


def pulse_from_samples(processes: List[dict], ports: List[dict], tcc: List[dict]) -> dict:
    ndi_proc = [p for p in processes if p.get("is_ndi")]
    ndi_ports = [p for p in ports if p.get("is_ndi_port")]
    auth_clients = [x for x in tcc if int(x.get("auth", 0)) > 0]

    risk = "ok"
    reasons: List[str] = []
    if ndi_proc:
        risk = "warn"
        reasons.append(f"ndi_proc={len(ndi_proc)}")
    if len(ndi_ports) >= 3:
        risk = "warn" if risk == "ok" else risk
        reasons.append(f"ndi_ports={len(ndi_ports)}")
    if len(ndi_proc) >= 2 and len(ndi_ports) >= 5:
        risk = "critical"
        reasons.append("multi_ndi_streams")

    top = [
        {"pid": p["pid"], "cmd": p["cmd"][:120], "is_ndi": p["is_ndi"]}
        for p in sorted(processes, key=lambda x: (not x["is_ndi"], x["pid"]))[:8]
    ]
    port_top = [{"pid": p["pid"], "cmd": p["cmd"], "name": p["name"]} for p in ports[:12]]

    summary = (
        f"risk={risk} | proc={len(processes)} ndi_proc={len(ndi_proc)} "
        f"| ndi_ports={len(ndi_ports)} | tcc_grants={len(auth_clients)}"
    )

    return {
        "ts": now_iso(),
        "risk": risk,
        "reasons": reasons,
        "summary": summary,
        "active_processes": len(processes),
        "active_ndi_processes": len(ndi_proc),
        "active_ports": len(ports),
        "active_ndi_ports": len(ndi_ports),
        "screen_capture_grants": len(auth_clients),
        "processes": top,
        "ports": port_top,
        "tcc_clients": [x["client"] for x in auth_clients[:20]],
    }


def _fingerprint_rows(rows: List[dict], keys: List[str]) -> str:
    sl = []
    for r in rows:
        item = []
        for k in keys:
            item.append(str(r.get(k)))
        sl.append("|".join(item))
    sl.sort()
    joined = "\n".join(sl).encode("utf-8")
    return hashlib.sha1(joined).hexdigest()[:16]


def process_once(state: dict, do_notify: bool, sound: str, echo: bool) -> int:
    processes = sample_processes()
    ports = sample_ports()
    tcc = sample_tcc_screen_capture()
    pulse = pulse_from_samples(processes, ports, tcc)
    PULSE_FILE.write_text(json.dumps(pulse, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    active_proc_ids = sorted([f"{p['pid']}:{p['cmd'][:64]}" for p in processes])
    active_ndi_ids = sorted([f"{p['pid']}:{p['cmd'][:64]}" for p in processes if p.get("is_ndi")])
    active_ports = sorted([f"{p['pid']}:{p['name']}" for p in ports if p.get("is_ndi_port")])
    tcc_hash = _fingerprint_rows(tcc, ["client", "auth", "last_modified"])

    prev_proc = set(state.get("active_proc_ids", []))
    prev_ndi = set(state.get("active_ndi_ids", []))
    prev_ports = set(state.get("active_ports", []))
    prev_tcc = str(state.get("last_tcc_hash", ""))
    prev_risk = str(state.get("last_risk", "none"))

    cur_proc = set(active_proc_ids)
    cur_ndi = set(active_ndi_ids)
    cur_ports = set(active_ports)

    emitted = 0

    new_ndi = sorted(cur_ndi - prev_ndi)
    if new_ndi:
        text = f"NDI process started: {new_ndi[0]}"
        event = {
            "event": "ndi_process_start",
            "event_id": hashlib.sha1(text.encode("utf-8")).hexdigest()[:12],
            "risk": "warn",
            "summary": text,
            "notify": True,
            "count_new": len(new_ndi),
        }
        append_trace(event)
        emitted += 1
        if echo:
            print(text)
        if do_notify:
            notify(text, sound=sound)

    gone_ndi = sorted(prev_ndi - cur_ndi)
    if gone_ndi:
        text = f"NDI process stopped: {gone_ndi[0]}"
        event = {
            "event": "ndi_process_stop",
            "event_id": hashlib.sha1(text.encode("utf-8")).hexdigest()[:12],
            "risk": "info",
            "summary": text,
            "notify": False,
            "count_gone": len(gone_ndi),
        }
        append_trace(event)
        emitted += 1
        if echo:
            print(text)

    new_ports = sorted(cur_ports - prev_ports)
    if new_ports:
        text = f"NDI/discovery port activity: {new_ports[0]}"
        event = {
            "event": "ndi_port_activity",
            "event_id": hashlib.sha1(text.encode("utf-8")).hexdigest()[:12],
            "risk": "warn",
            "summary": text,
            "notify": True,
            "count_new": len(new_ports),
        }
        append_trace(event)
        emitted += 1
        if echo:
            print(text)
        if do_notify:
            notify(text, sound=sound)

    if tcc_hash != prev_tcc:
        text = "ScreenCapture TCC grants changed"
        event = {
            "event": "tcc_screen_capture_change",
            "event_id": hashlib.sha1((text + tcc_hash).encode("utf-8")).hexdigest()[:12],
            "risk": "warn",
            "summary": text,
            "notify": True,
            "grants": pulse.get("screen_capture_grants", 0),
        }
        append_trace(event)
        emitted += 1
        if echo:
            print(text)
        if do_notify:
            notify(text, sound=sound)

    if pulse["risk"] != prev_risk:
        text = f"NDI pulse risk changed: {prev_risk} -> {pulse['risk']}"
        event = {
            "event": "ndi_pulse_risk",
            "event_id": hashlib.sha1((text + pulse["summary"]).encode("utf-8")).hexdigest()[:12],
            "risk": pulse["risk"],
            "summary": pulse["summary"],
            "notify": pulse["risk"] in {"warn", "critical"},
        }
        append_trace(event)
        emitted += 1
        if echo:
            print(text)
        if do_notify and pulse["risk"] in {"warn", "critical"}:
            notify(text, sound=sound)

    # periodic heartbeat pulse (lossy compressed status)
    pulse_text = pulse["summary"]
    event = {
        "event": "ndi_pulse",
        "event_id": hashlib.sha1(("pulse:" + pulse_text).encode("utf-8")).hexdigest()[:12],
        "risk": pulse["risk"],
        "summary": pulse_text,
        "notify": False,
    }
    append_trace(event)
    emitted += 1
    if echo:
        print(pulse_text)

    state["active_proc_ids"] = active_proc_ids
    state["active_ndi_ids"] = active_ndi_ids
    state["active_ports"] = active_ports
    state["last_tcc_hash"] = tcc_hash
    state["last_risk"] = pulse["risk"]
    return emitted


def cmd_once(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    emitted = process_once(state, do_notify=args.notify, sound=args.sound, echo=args.echo)
    save_state(state)
    print(json.dumps({"status": "ok", "emitted": emitted, "ts": now_iso()}))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    interval = max(2, int(args.interval))
    while True:
        emitted = process_once(state, do_notify=args.notify, sound=args.sound, echo=args.echo)
        save_state(state)
        if args.heartbeat and emitted == 0:
            print(f"[ndi] idle heartbeat {now_iso()}")
        time.sleep(interval)


def cmd_status(_args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    out = {
        "state_file": str(STATE_FILE),
        "trace_file": str(TRACE_FILE),
        "pulse_file": str(PULSE_FILE),
        "last_run": state.get("last_run"),
        "active_proc": len(state.get("active_proc_ids", [])),
        "active_ndi": len(state.get("active_ndi_ids", [])),
        "active_ports": len(state.get("active_ports", [])),
        "last_risk": state.get("last_risk", "none"),
    }
    if PULSE_FILE.exists():
        try:
            out["pulse"] = json.loads(PULSE_FILE.read_text(encoding="utf-8"))
        except Exception:
            out["pulse"] = "invalid"
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_prime(_args: argparse.Namespace) -> int:
    ensure_dirs()
    processes = sample_processes()
    ports = sample_ports()
    tcc = sample_tcc_screen_capture()
    state = load_state()
    state["active_proc_ids"] = sorted([f"{p['pid']}:{p['cmd'][:64]}" for p in processes])
    state["active_ndi_ids"] = sorted([f"{p['pid']}:{p['cmd'][:64]}" for p in processes if p.get("is_ndi")])
    state["active_ports"] = sorted([f"{p['pid']}:{p['name']}" for p in ports if p.get("is_ndi_port")])
    state["last_tcc_hash"] = _fingerprint_rows(tcc, ["client", "auth", "last_modified"])
    pulse = pulse_from_samples(processes, ports, tcc)
    state["last_risk"] = pulse["risk"]
    PULSE_FILE.write_text(json.dumps(pulse, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save_state(state)
    print(json.dumps({"status": "primed", "ts": now_iso()}))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    ensure_dirs()
    n = max(1, int(args.n))
    if not TRACE_FILE.exists():
        print(f"trace missing: {TRACE_FILE}")
        return 0
    lines = TRACE_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-n:]:
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="NDI/screen capture watchdog")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--notify", action="store_true", help="send macOS notifications")
        sp.add_argument("--sound", default="Hero", help="notification sound")
        sp.add_argument("--echo", action="store_true", help="echo samples to stdout")

    sp_once = sub.add_parser("once", help="run one watchdog sample")
    common(sp_once)
    sp_once.set_defaults(func=cmd_once)

    sp_run = sub.add_parser("run", help="continuous watchdog")
    sp_run.add_argument("--interval", type=int, default=6, help="poll interval seconds")
    sp_run.add_argument("--heartbeat", action="store_true", help="print heartbeat while idle")
    common(sp_run)
    sp_run.set_defaults(func=cmd_run)

    sp_status = sub.add_parser("status", help="show watchdog state")
    sp_status.set_defaults(func=cmd_status)

    sp_prime = sub.add_parser("prime", help="capture baseline and suppress startup noise")
    sp_prime.set_defaults(func=cmd_prime)

    sp_tail = sub.add_parser("tail", help="print last trace rows")
    sp_tail.add_argument("-n", type=int, default=40, help="line count")
    sp_tail.set_defaults(func=cmd_tail)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
