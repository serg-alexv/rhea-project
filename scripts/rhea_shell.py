#!/usr/bin/env python3
"""
rhea_shell.py — Rhea Commander shell for next-stage Rhea operations.

Examples:
  python3 scripts/rhea_shell.py
  python3 scripts/rhea_shell.py -c "workflows list"
  python3 scripts/rhea_shell.py -c "workflows run openclaw.p0.recovery"
"""

from __future__ import annotations

import argparse
import cmd
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cmd(argv: list[str]) -> int:
    p = subprocess.run(argv, cwd=ROOT, check=False)
    return p.returncode


class RheaShell(cmd.Cmd):
    intro = "Rhea Commander (shell mode) — workflows as flows. Type 'help' or 'exit'."
    prompt = "commander> "

    def _run(self, line: str) -> int:
        parts = shlex.split(line)
        if not parts:
            return 0

        head = parts[0].lower()
        tail = parts[1:]

        if head in {"exit", "quit", "q"}:
            raise SystemExit(0)
        if head == "status":
            return run_cmd(["python3", "scripts/rhea_orchestrate.py", "status"])
        if head == "radio":
            return run_cmd(["bash", "scripts/rhea.sh", "radio"] + tail)
        if head == "ndi":
            return run_cmd(["bash", "scripts/rhea.sh", "ndi"] + tail)
        if head == "continuity":
            return run_cmd(["python3", "scripts/continuity_capsule.py"] + tail)
        if head == "continuity-smoke":
            return run_cmd(["python3", "scripts/continuity_cloud_smoke.py"] + tail)
        if head == "family":
            return run_cmd(["python3", "scripts/rhea_family.py"] + tail)
        if head == "workflows":
            return run_cmd(["python3", "scripts/rhea_flow.py"] + tail)
        if head == "axiom":
            return run_cmd(["python3", "scripts/axiom_contract.py"] + tail)
        if head == "rex-reqs":
            msg = (
                "Reqs needed for next-stage CLI: provide explicit requirements for "
                "rhea_shell/workflows (must-have commands, status panels, safety rails, "
                "ack policy, output format). Reply compact bullet list."
            )
            return run_cmd(
                [
                    "python3",
                    "scripts/rhea_flow.py",
                    "run",
                    "openclaw.org.sync",
                    "--targets",
                    "REX",
                    "--source",
                    "ORION",
                    "--priority",
                    "P0",
                    "--ack-timeout",
                    "45",
                    "--message",
                    msg,
                ]
            )
        if head == "help":
            print(
                "Commands:\n"
                "  status\n"
                "  workflows list\n"
                "  workflows run <flow_id> [--message ...]\n"
                "  axiom check --agent <name> [--json]\n"
                "  axiom check-fleet [--json]\n"
                "  family <send|status|wait|tail> ...\n"
                "  continuity <pack|verify|report> ...\n"
                "  continuity-smoke\n"
                "  radio <status|listen|tail>\n"
                "  ndi <status|once|tail>\n"
                "  rex-reqs\n"
                "  exit"
            )
            return 0

        print(f"Unknown command: {head}. Type 'help'.")
        return 2

    def default(self, line: str):
        try:
            self._run(line)
        except SystemExit:
            return True

    def do_exit(self, _arg):
        return True

    def do_quit(self, _arg):
        return True

    def do_EOF(self, _arg):
        print()
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Rhea interactive shell")
    parser.add_argument("-c", "--command", default="", help="Run one command and exit")
    args = parser.parse_args()

    shell = RheaShell()
    if args.command.strip():
        try:
            return shell._run(args.command.strip())
        except SystemExit:
            return 0
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
