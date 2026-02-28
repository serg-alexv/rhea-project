#!/usr/bin/env python3
"""Tk applet for queue guard pulse + maintenance controls."""

from __future__ import annotations

import json
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext


ROOT = Path(__file__).resolve().parents[1]
HEALTH_FILE = ROOT / "opera" / "metrics" / "queue_health.json"
QUEUE_SH = ROOT / "scripts" / "rhea" / "queue_guard.sh"
RADIO_SH = ROOT / "scripts" / "rhea" / "radio.sh"
NDI_SH = ROOT / "scripts" / "rhea" / "ndi.sh"
FLICKER_MARK = ROOT / "scripts" / "flicker_mark.py"
FLICKER_TRACE = ROOT / "scripts" / "flicker_trace.sh"


class QueueApplet:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Rhea Queue Maintainer")
        self.root.geometry("980x650")
        self.refresh_sec = 5

        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=8, pady=8)

        tk.Button(top, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(top, text="Start Guard", command=lambda: self.run_cmd([str(QUEUE_SH), "start", "--interval", "30"])).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(top, text="Stop Guard", command=lambda: self.run_cmd([str(QUEUE_SH), "stop"])).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(top, text="Compact Now", command=lambda: self.run_cmd([str(QUEUE_SH), "compact"])).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(top, text="Guard Status", command=lambda: self.run_cmd([str(QUEUE_SH), "status"])).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(top, text="Start Radio", command=lambda: self.run_cmd([str(RADIO_SH), "start", "--interval", "2"])).pack(side=tk.LEFT, padx=(16, 8))
        tk.Button(top, text="Radio Status", command=lambda: self.run_cmd([str(RADIO_SH), "status"])).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(top, text="Start NDI", command=lambda: self.run_cmd([str(NDI_SH), "start", "--interval", "8"])).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(top, text="Stop NDI", command=lambda: self.run_cmd([str(NDI_SH), "stop"])).pack(side=tk.LEFT, padx=(0, 8))

        flicker = tk.Frame(root)
        flicker.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Label(flicker, text="Flicker note:").pack(side=tk.LEFT)
        self.flicker_entry = tk.Entry(flicker)
        self.flicker_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        self.flicker_entry.insert(0, "screen flicker observed")
        tk.Button(flicker, text="Mark Flicker", command=self.mark_flicker).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(flicker, text="Trace 60s", command=lambda: self.trace_flicker(60)).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(flicker, text="Trace 300s", command=lambda: self.trace_flicker(300)).pack(side=tk.LEFT, padx=(0, 8))

        self.summary_var = tk.StringVar(value="pulse: no data")
        self.stats_var = tk.StringVar(value="stats: no data")
        tk.Label(root, textvariable=self.summary_var, font=("Menlo", 12, "bold"), anchor="w", justify=tk.LEFT).pack(fill=tk.X, padx=8, pady=(0, 4))
        tk.Label(root, textvariable=self.stats_var, font=("Menlo", 10), anchor="w", justify=tk.LEFT).pack(fill=tk.X, padx=8, pady=(0, 8))

        cols = tk.Frame(root)
        cols.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        left = tk.Frame(cols)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        right = tk.Frame(cols)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        tk.Label(left, text="File Health").pack(anchor="w")
        self.files_text = scrolledtext.ScrolledText(left, wrap=tk.NONE, height=18)
        self.files_text.pack(fill=tk.BOTH, expand=True)

        tk.Label(right, text="Activity Log").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(right, wrap=tk.WORD, height=18)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log("Queue applet ready.")
        self.refresh()
        self.auto_tick()

    def log(self, msg: str) -> None:
        stamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        self.log_text.insert(tk.END, f"[{stamp}] {msg}\n")
        self.log_text.see(tk.END)

    def run_cmd(self, cmd: list[str]) -> None:
        self.log("$ " + " ".join(cmd))

        def worker() -> None:
            try:
                proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=25, check=False)
                out = (proc.stdout or "") + (proc.stderr or "")
                text = out.strip() or "(no output)"
                self.root.after(0, lambda: self.log(text))
                self.root.after(0, self.refresh)
            except Exception as exc:
                self.root.after(0, lambda: self.log(f"ERROR: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def refresh(self) -> None:
        if not HEALTH_FILE.exists():
            self.summary_var.set("pulse: no queue_health.json yet")
            self.stats_var.set("stats: run `bash scripts/rhea/queue_guard.sh once`")
            self.files_text.delete("1.0", tk.END)
            return
        try:
            health = json.loads(HEALTH_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            self.summary_var.set(f"pulse: invalid health file ({exc})")
            return

        self.summary_var.set("pulse: " + str(health.get("summary", "n/a")))
        totals = health.get("totals", {})
        stats = (
            f"risk={health.get('risk')}  files={totals.get('files', 0)}  changed={totals.get('changed', 0)}  "
            f"archived={totals.get('archived', 0)}  lines={totals.get('lines', 0)}  bytes={totals.get('bytes', 0)}"
        )
        self.stats_var.set(stats)

        self.files_text.delete("1.0", tk.END)
        rows = health.get("files", [])
        if isinstance(rows, list):
            for r in rows:
                line = (
                    f"{r.get('name'):14} lines={int(r.get('line_count', 0)):6d} "
                    f"max={int(r.get('max_lines', 0)):6d} keep={int(r.get('keep_lines', 0)):6d} "
                    f"archived={int(r.get('overflow_archived', 0)):6d} size={int(r.get('size_bytes', 0)):9d}"
                )
                self.files_text.insert(tk.END, line + "\n")
        warns = health.get("warnings", [])
        if warns:
            self.files_text.insert(tk.END, "\nWARNINGS\n")
            for w in warns:
                self.files_text.insert(tk.END, f"- {w}\n")

    def mark_flicker(self) -> None:
        note = self.flicker_entry.get().strip() or "screen flicker observed"
        self.run_cmd(["python3", str(FLICKER_MARK), note])

    def trace_flicker(self, seconds: int) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = ROOT / "diagnostics" / f"screen-flicker-live-{stamp}"
        self.run_cmd(["bash", str(FLICKER_TRACE), str(seconds), str(out_dir)])

    def auto_tick(self) -> None:
        self.refresh()
        self.root.after(self.refresh_sec * 1000, self.auto_tick)


def main() -> None:
    root = tk.Tk()
    QueueApplet(root)
    root.mainloop()


if __name__ == "__main__":
    main()
