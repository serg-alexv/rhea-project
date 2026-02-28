#!/usr/bin/env python3
"""
red_pixel_canary.py - tiny topmost red pixel overlay for capture watermarking.

Purpose:
  - make captured frames visibly tagged when capture risk is active
  - controllable from automation (start/stop/status)
"""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".rhea" / "ndi"
PID_FILE = STATE_DIR / "red_pixel.pid"
LOG_FILE = STATE_DIR / "red_pixel.log"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return False
    try:
        subprocess.run(["kill", "-0", str(pid)], check=False, timeout=2)
        return True
    except Exception:
        return False


def cmd_start(args: argparse.Namespace) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if is_running():
        print(json.dumps({"status": "already_running", "pid": PID_FILE.read_text().strip()}))
        return 0

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run",
        "--x",
        str(args.x),
        "--y",
        str(args.y),
        "--size",
        str(args.size),
    ]
    with LOG_FILE.open("a", encoding="utf-8") as out:
        proc = subprocess.Popen(cmd, stdout=out, stderr=out, cwd=ROOT)
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    print(json.dumps({"status": "started", "pid": proc.pid, "ts": now_iso()}))
    return 0


def cmd_stop(_args: argparse.Namespace) -> int:
    if not PID_FILE.exists():
        print(json.dumps({"status": "not_running"}))
        return 0
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        PID_FILE.unlink(missing_ok=True)
        print(json.dumps({"status": "stale_pid"}))
        return 0

    try:
        subprocess.run(["kill", str(pid)], check=False, timeout=2)
        time.sleep(0.15)
        subprocess.run(["kill", "-9", str(pid)], check=False, timeout=2)
    except Exception:
        pass
    PID_FILE.unlink(missing_ok=True)
    print(json.dumps({"status": "stopped", "pid": pid, "ts": now_iso()}))
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    running = is_running()
    pid = None
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        except Exception:
            pid = None
    print(
        json.dumps(
            {
                "status": "running" if running else "stopped",
                "pid": pid,
                "pid_file": str(PID_FILE),
                "log_file": str(LOG_FILE),
                "ts": now_iso(),
            }
        )
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    import tkinter as tk

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    try:
        root.attributes("-alpha", 0.98)
    except Exception:
        pass
    root.configure(bg="#ff0000")
    root.geometry(f"{args.size}x{args.size}+{args.x}+{args.y}")

    colors = ["#ff0000", "#cc0000"]
    state = {"i": 0}

    def tick() -> None:
        state["i"] = 1 - state["i"]
        root.configure(bg=colors[state["i"]])
        root.after(350, tick)

    def shutdown(_sig=None, _frm=None) -> None:
        try:
            root.destroy()
        except Exception:
            pass

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    root.after(0, tick)
    root.mainloop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Topmost red pixel canary")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_start = sub.add_parser("start", help="start canary")
    sp_start.add_argument("--x", type=int, default=2, help="x position")
    sp_start.add_argument("--y", type=int, default=2, help="y position")
    sp_start.add_argument("--size", type=int, default=2, help="pixel size")
    sp_start.set_defaults(func=cmd_start)

    sp_stop = sub.add_parser("stop", help="stop canary")
    sp_stop.set_defaults(func=cmd_stop)

    sp_status = sub.add_parser("status", help="show status")
    sp_status.set_defaults(func=cmd_status)

    sp_run = sub.add_parser("run", help="foreground app loop")
    sp_run.add_argument("--x", type=int, default=2)
    sp_run.add_argument("--y", type=int, default=2)
    sp_run.add_argument("--size", type=int, default=2)
    sp_run.set_defaults(func=cmd_run)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

