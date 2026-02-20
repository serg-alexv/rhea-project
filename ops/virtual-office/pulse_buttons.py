#!/usr/bin/env python3
"""Primitive button UI for Rhea relay controls (no external deps)."""

from __future__ import annotations

import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


class PulseButtonsApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Rhea Pulse Buttons (primitive)")
        self.root.geometry("980x620")

        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=8, pady=8)

        self._add_btn(top, "Status", ["python3", "ops/rex_pager.py", "status"])
        self._add_btn(top, "Wake REX", ["python3", "ops/rex_pager.py", "wake", "REX"])
        self._add_btn(top, "Drain GPT", ["python3", "ops/rex_pager.py", "drain", "GPT"])
        self._add_btn(top, "Drain LEAD", ["python3", "ops/rex_pager.py", "drain", "LEAD"])
        self._add_btn(top, "Drain REX", ["python3", "ops/rex_pager.py", "drain", "REX"])

        msg = tk.Frame(root)
        msg.pack(fill=tk.X, padx=8, pady=(0, 8))

        tk.Label(msg, text="Message to REX:").pack(side=tk.LEFT)
        self.entry = tk.Entry(msg)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        self.entry.insert(0, "P1 ping from UI")
        tk.Button(msg, text="Send", command=self.send_to_rex).pack(side=tk.LEFT)

        self.log = scrolledtext.ScrolledText(root, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.append("Ready. Buttons call ops/rex_pager.py in this repo.")

    def _add_btn(self, parent: tk.Widget, label: str, cmd: list[str]) -> None:
        tk.Button(parent, text=label, command=lambda c=cmd: self.run_cmd(c)).pack(side=tk.LEFT, padx=(0, 8))

    def append(self, text: str) -> None:
        stamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        self.log.insert(tk.END, f"[{stamp}] {text}\n")
        self.log.see(tk.END)

    def run_cmd(self, cmd: list[str]) -> None:
        self.append("$ " + " ".join(cmd))

        def worker() -> None:
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=REPO,
                    capture_output=True,
                    text=True,
                    timeout=25,
                    check=False,
                )
                out = (proc.stdout or "") + (proc.stderr or "")
                result = out.strip() or "(no output)"
                self.root.after(0, lambda: self.append(result))
            except Exception as exc:
                self.root.after(0, lambda: self.append(f"ERROR: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def send_to_rex(self) -> None:
        text = self.entry.get().strip()
        if not text:
            self.append("Message is empty.")
            return
        cmd = [
            "python3",
            "ops/rex_pager.py",
            "send",
            "GPT",
            "REX",
            text,
            "--priority",
            "P1",
            "--ttl",
            "86400",
        ]
        self.run_cmd(cmd)


def main() -> None:
    root = tk.Tk()
    PulseButtonsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
