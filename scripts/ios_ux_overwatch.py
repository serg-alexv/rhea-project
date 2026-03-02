#!/usr/bin/env python3
"""
ios_ux_overwatch.py - continuous iOS UI/UX guardrail monitor.

Purpose:
  - watch iOS app sources for high-signal UI/UX risks
  - emit compact trace + pulse snapshots for Radio and iOS Governor
  - provide always-on "external post-doc" style oversight loop
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "ios_ux"
STATE_FILE = STATE_DIR / "state.json"
TRACE_FILE = ROOT / "opera" / "metrics" / "ios_ux_trace.jsonl"
PULSE_FILE = ROOT / "opera" / "metrics" / "ios_ux_pulse.json"

TARGET_DIRS = [
    ROOT / "ios" / "RheaPreview.swiftpm" / "Sources",
    ROOT / "ios" / "RheaApp",
]
TARGET_FILES = [ROOT / "ios" / "RheaApp" / "project.yml"]

LOCALHOST_RE = re.compile(r"http://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?", re.IGNORECASE)
INSECURE_REMOTE_HTTP_RE = re.compile(r"http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)", re.IGNORECASE)
BUTTON_RE = re.compile(r"\bButton\s*\(")
TOGGLE_RE = re.compile(r"\bToggle\s*\(")
A11Y_RE = re.compile(r"\.accessibility(?:Label|Hint|Identifier)\s*\(")
TODO_RE = re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b")
DEV_LEAK_RE = re.compile(r"\b(?:REX|ORION|HYPERION|TRIBUNAL|COUNCIL|AGENT)\b")
IOS_SWIFT_EXT = ".swift"


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    path: str = ""
    count: int = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PULSE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {
            "last_run": None,
            "last_risk": "info",
            "last_signature": "",
            "last_notify_epoch": 0,
            "runs": 0,
        }
    try:
        obj = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return {
        "last_run": None,
        "last_risk": "info",
        "last_signature": "",
        "last_notify_epoch": 0,
        "runs": 0,
    }


def save_state(state: dict) -> None:
    state["last_run"] = now_iso()
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)


def append_trace(event: dict) -> None:
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), **event}, ensure_ascii=False) + "\n")


def notify(msg: str, sound: str = "Hero") -> None:
    safe = msg.replace('"', "'")
    subprocess.run(
        ["osascript", "-e", f'display notification "{safe}" with title "IOS UX OVERWATCH" sound name "{sound}"'],
        check=False,
        capture_output=True,
        text=True,
        timeout=6,
    )


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def iter_target_files() -> List[Path]:
    out: List[Path] = []
    for d in TARGET_DIRS:
        if not d.exists():
            continue
        out.extend(sorted([p for p in d.rglob("*") if p.is_file() and p.suffix == IOS_SWIFT_EXT]))
    for p in TARGET_FILES:
        if p.exists():
            out.append(p)
    return out


def file_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def calc_signature(files: List[Path]) -> str:
    h = hashlib.sha256()
    for p in files:
        try:
            st = p.stat()
            h.update(rel_path(p).encode("utf-8"))
            h.update(str(int(st.st_mtime)).encode("utf-8"))
            h.update(str(int(st.st_size)).encode("utf-8"))
        except Exception:
            continue
    return h.hexdigest()[:16]


def detect_issues(files: List[Path]) -> Tuple[List[Issue], Dict[str, int]]:
    issues: List[Issue] = []
    total_buttons = 0
    total_toggles = 0
    total_a11y = 0
    total_todos = 0
    total_dev_words = 0
    localhost_hits = 0
    insecure_remote_http_hits = 0

    for p in files:
        txt = file_text(p)
        if not txt:
            continue
        rp = rel_path(p)

        b = len(BUTTON_RE.findall(txt))
        t = len(TOGGLE_RE.findall(txt))
        a = len(A11Y_RE.findall(txt))
        total_buttons += b
        total_toggles += t
        total_a11y += a

        td = len(TODO_RE.findall(txt))
        if td:
            total_todos += td

        dev = len(DEV_LEAK_RE.findall(txt))
        if dev:
            total_dev_words += dev

        localhost = len(LOCALHOST_RE.findall(txt))
        if localhost:
            localhost_hits += localhost
            severity = "warn" if "AppConfig.swift" in rp else "critical"
            issues.append(
                Issue(
                    severity=severity,
                    code="LOCALHOST_URL",
                    message=f"hardcoded localhost URL in {rp}",
                    path=rp,
                    count=localhost,
                )
            )

        insecure = len(INSECURE_REMOTE_HTTP_RE.findall(txt))
        if insecure:
            insecure_remote_http_hits += insecure
            issues.append(
                Issue(
                    severity="critical",
                    code="INSECURE_HTTP",
                    message=f"insecure remote http:// URL in {rp}",
                    path=rp,
                    count=insecure,
                )
            )

    total_interactive = total_buttons + total_toggles
    if total_interactive >= 8:
        ratio = (total_a11y / total_interactive) if total_interactive else 1.0
        if ratio < 0.25:
            issues.append(
                Issue(
                    severity="warn",
                    code="LOW_A11Y_COVERAGE",
                    message=f"low accessibility coverage: a11y={total_a11y} interactive={total_interactive} ratio={ratio:.2f}",
                    count=total_interactive,
                )
            )

    if total_todos >= 10:
        issues.append(
            Issue(
                severity="warn",
                code="MANY_TODO",
                message=f"high TODO/FIXME count in iOS sources: {total_todos}",
                count=total_todos,
            )
        )
    elif total_todos > 0:
        issues.append(
            Issue(
                severity="info",
                code="TODO_PRESENT",
                message=f"TODO/FIXME present in iOS sources: {total_todos}",
                count=total_todos,
            )
        )

    if total_dev_words >= 20:
        issues.append(
            Issue(
                severity="warn",
                code="DEV_VOCAB_LEAK",
                message=f"dev/internal vocabulary appears in iOS copy too often: {total_dev_words}",
                count=total_dev_words,
            )
        )

    metrics = {
        "files": len(files),
        "buttons": total_buttons,
        "toggles": total_toggles,
        "a11y_annotations": total_a11y,
        "todos": total_todos,
        "dev_vocab_hits": total_dev_words,
        "localhost_hits": localhost_hits,
        "insecure_remote_http_hits": insecure_remote_http_hits,
    }
    return issues, metrics


def risk_from_issues(issues: List[Issue]) -> str:
    if any(i.severity == "critical" for i in issues):
        return "critical"
    if any(i.severity == "warn" for i in issues):
        return "warn"
    return "info"


def summarize(risk: str, metrics: Dict[str, int], issues: List[Issue]) -> str:
    top = issues[0].code if issues else "NONE"
    return (
        f"risk={risk} files={metrics['files']} buttons={metrics['buttons']} "
        f"a11y={metrics['a11y_annotations']} todos={metrics['todos']} "
        f"localhost={metrics['localhost_hits']} insecure_http={metrics['insecure_remote_http_hits']} top={top}"
    )


def issues_signature(issues: List[Issue], fsig: str) -> str:
    data = [{"severity": i.severity, "code": i.code, "path": i.path, "count": i.count} for i in issues]
    raw = json.dumps({"issues": data, "fsig": fsig}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def scan_once(state: dict, do_notify: bool, cooldown_s: int, echo: bool) -> dict:
    files = iter_target_files()
    fsig = calc_signature(files)
    issues, metrics = detect_issues(files)
    risk = risk_from_issues(issues)
    sig = issues_signature(issues, fsig)
    changed = sig != str(state.get("last_signature", ""))

    top_issues = [
        {"severity": i.severity, "code": i.code, "path": i.path, "count": i.count, "message": i.message}
        for i in issues[:12]
    ]
    pulse = {
        "ts": now_iso(),
        "risk": risk,
        "summary": summarize(risk, metrics, issues),
        "changed": changed,
        "metrics": metrics,
        "issues": top_issues,
        "signature": sig,
        "file_signature": fsig,
    }
    PULSE_FILE.write_text(json.dumps(pulse, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sev = {"info": 0, "warn": 1, "critical": 2}
    prev_risk = str(state.get("last_risk", "info"))
    now_ep = int(time.time())
    last_notify = int(state.get("last_notify_epoch", 0) or 0)
    allow_notify = do_notify and (now_ep - last_notify >= cooldown_s)
    should_notify = (changed and sev.get(risk, 0) >= 1) or (sev.get(risk, 0) > sev.get(prev_risk, 0))
    if should_notify and allow_notify:
        notify(pulse["summary"], sound="Basso" if risk == "critical" else "Hero")
        state["last_notify_epoch"] = now_ep

    if changed or sev.get(risk, 0) >= 1:
        append_trace(
            {
                "event": "ios_ux_overwatch",
                "risk": risk,
                "summary": pulse["summary"],
                "changed": changed,
                "issues": top_issues,
                "signature": sig,
            }
        )

    state["last_signature"] = sig
    state["last_risk"] = risk
    state["runs"] = int(state.get("runs", 0) or 0) + 1

    if echo:
        print(json.dumps(pulse, ensure_ascii=False))
    return pulse


def cmd_once(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    scan_once(state, do_notify=args.notify, cooldown_s=max(10, args.notify_cooldown), echo=args.echo)
    save_state(state)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    interval = max(5, int(args.interval))
    while True:
        scan_once(state, do_notify=args.notify, cooldown_s=max(10, args.notify_cooldown), echo=args.echo)
        save_state(state)
        time.sleep(interval)


def cmd_status(_args: argparse.Namespace) -> int:
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
        "trace_file": str(TRACE_FILE),
        "pulse_file": str(PULSE_FILE),
        "last_run": state.get("last_run"),
        "runs": state.get("runs", 0),
        "last_risk": state.get("last_risk", "info"),
        "pulse": pulse,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    ensure_dirs()
    n = max(1, int(args.n))
    if not TRACE_FILE.exists():
        print("[]")
        return 0
    lines = TRACE_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-n:]:
        print(line)
    return 0


def cmd_prime(_args: argparse.Namespace) -> int:
    ensure_dirs()
    state = load_state()
    files = iter_target_files()
    fsig = calc_signature(files)
    issues, _metrics = detect_issues(files)
    state["last_signature"] = issues_signature(issues, fsig)
    state["last_risk"] = risk_from_issues(issues)
    save_state(state)
    print("ios_ux_overwatch primed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Continuous iOS UI/UX guardrail monitor")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_once = sub.add_parser("once", help="single scan")
    s_once.add_argument("--notify", action="store_true")
    s_once.add_argument("--notify-cooldown", type=int, default=300)
    s_once.add_argument("--echo", action="store_true")

    s_run = sub.add_parser("run", help="continuous scan")
    s_run.add_argument("--interval", type=int, default=20)
    s_run.add_argument("--notify", action="store_true")
    s_run.add_argument("--notify-cooldown", type=int, default=300)
    s_run.add_argument("--echo", action="store_true")

    sub.add_parser("status", help="state + pulse")

    s_tail = sub.add_parser("tail", help="recent trace rows")
    s_tail.add_argument("-n", type=int, default=40)

    sub.add_parser("prime", help="baseline without notifications")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.cmd == "once":
        return cmd_once(args)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "tail":
        return cmd_tail(args)
    if args.cmd == "prime":
        return cmd_prime(args)
    parser.error(f"unknown cmd {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

