#!/usr/bin/env python3
"""
rhea_executor.py — Autonomous task execution engine.

The self-evolving loop:
  1. Claim highest-priority open task
  2. Route to the right agent (claude/codex/bridge)
  3. Execute
  4. Capture result
  5. Mark complete (or block with reason)
  6. Check for new tasks created by execution
  7. Relay outbox → inbox
  8. Heartbeat
  9. Loop

Usage:
    python3 scripts/rhea_executor.py              # one cycle
    python3 scripts/rhea_executor.py --daemon      # continuous loop
    python3 scripts/rhea_executor.py --agent rex    # run as specific agent
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import urllib.request
import urllib.error

from task_queue import TaskQueue

API_BASE = "http://localhost:8400"


def api_call(method: str, path: str, data: dict = None) -> dict | None:
    """Call Tribunal API. Returns parsed JSON or None on error."""
    url = f"{API_BASE}{path}"
    try:
        if data:
            body = json.dumps(data).encode()
            req = urllib.request.Request(url, data=body, method=method,
                                        headers={"Content-Type": "application/json"})
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None

AGENT_ROUTES = {
    "rex":      {"cmd": "claude", "args": ["-p", "--output-format", "text"], "timeout": 300},
    "orion":    {"cmd": "codex", "args": ["-q"], "timeout": 300},
    "gemini":   {"cmd": "python3", "args": [str(PROJECT_ROOT / "src/rhea_bridge.py"), "ask", "gemini/gemini-2.5-flash"], "timeout": 120},
    "shared":   {"cmd": "claude", "args": ["-p", "--output-format", "text", "--model", "sonnet"], "timeout": 180},
    "gpt":      {"cmd": "codex", "args": ["-q"], "timeout": 300},
    "hyperion": {"cmd": "claude", "args": ["-p", "--output-format", "text", "--model", "sonnet"], "timeout": 180},
}

RELAY_DIR = PROJECT_ROOT / "opera" / "ops" / "virtual-office"
LOG_DIR = PROJECT_ROOT / "opera" / "logs" / "swarm"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_DIR / "executor.log", "a") as f:
        f.write(line + "\n")


def execute_task(task: dict, agent_name: str) -> tuple[bool, str]:
    """Execute a task via the agent's CLI. Returns (success, result_text)."""
    route = AGENT_ROUTES.get(agent_name, AGENT_ROUTES["shared"])
    prompt = f"""You are {agent_name.upper()}, an autonomous agent in the Rhea system.
Execute this task completely. No questions. Produce output.

Task ID: {task['id']}
Priority: {task['priority']}
Title: {task['title']}
Tags: {', '.join(task.get('tags', []))}

Working directory: {PROJECT_ROOT}
Deliver the result. If blocked, explain why in one line."""

    cmd = route["cmd"]
    args = route["args"]

    try:
        if cmd == "claude":
            # Claude Code: pipe prompt via -p flag
            result = subprocess.run(
                [cmd] + args + [prompt],
                capture_output=True, text=True,
                timeout=route["timeout"],
                cwd=str(PROJECT_ROOT),
                env={**os.environ, "CLAUDE_NO_HOOKS": "1"},
            )
            output = result.stdout.strip() or result.stderr.strip()

        elif cmd == "codex":
            # Codex: pipe prompt
            result = subprocess.run(
                [cmd] + args + [prompt],
                capture_output=True, text=True,
                timeout=route["timeout"],
                cwd=str(PROJECT_ROOT),
            )
            output = result.stdout.strip() or result.stderr.strip()

        elif cmd == "python3":
            # Bridge: direct ask
            result = subprocess.run(
                args + [prompt],
                capture_output=True, text=True,
                timeout=route["timeout"],
                cwd=str(PROJECT_ROOT),
            )
            output = result.stdout.strip()

        else:
            return False, f"Unknown command: {cmd}"

        if result.returncode != 0 and not output:
            return False, f"Exit code {result.returncode}: {result.stderr[:200]}"

        return True, output[:2000]  # cap result size

    except subprocess.TimeoutExpired:
        return False, f"Timeout after {route['timeout']}s"
    except FileNotFoundError:
        return False, f"Command not found: {cmd}"
    except Exception as e:
        return False, f"Error: {str(e)[:200]}"


def relay_cycle():
    """Run one outbox→inbox relay cycle."""
    try:
        result = subprocess.run(
            ["bash", str(PROJECT_ROOT / "scripts" / "rhea_swarm.sh"), "relay"],
            capture_output=True, text=True, timeout=30,
        )
        if "delivered" in result.stdout:
            log(f"  Relay: {result.stdout.strip()}")
    except Exception as e:
        log(f"  Relay error: {e}")


def heartbeat():
    """Run heartbeat check."""
    try:
        result = subprocess.run(
            ["python3", str(PROJECT_ROOT / "scripts" / "rhea_heartbeat.py")],
            capture_output=True, text=True, timeout=30,
        )
        # Only log if there are issues
        for line in result.stdout.split("\n"):
            if "P0" in line or "P1" in line:
                log(f"  Heartbeat: {line.strip()}")
    except Exception:
        pass


def git_push_check():
    """Check for unpushed commits and push if overdue."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "@{push}..HEAD"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        if len(lines) > 3:
            log(f"  Git: {len(lines)} unpushed commits — pushing...")
            subprocess.run(
                ["git", "push"],
                capture_output=True, timeout=30,
                cwd=str(PROJECT_ROOT),
            )
    except Exception:
        pass


def one_cycle(agent_name: str) -> bool:
    """Run one claim→execute→complete cycle. Returns True if work was done."""

    # 1. Release stale via API (single source of truth)
    released = api_call("POST", "/tasks/release-stale?hours=2")
    if released and released.get("released", 0) > 0:
        log(f"Released {released['released']} stale tasks via API")

    # 2. Claim via API
    claim_resp = api_call("POST", f"/tasks/next/claim?agent={agent_name}")
    if not claim_resp:
        # Fallback to direct file access if API is down
        q = TaskQueue()
        task = q.claim(agent_name)
        if not task:
            summary = api_call("GET", "/tasks/summary") or q.summary()
            log(f"No tasks for {agent_name}. Queue: {summary.get('counts', {})}")
            return False
    else:
        task = claim_resp

    log(f"CLAIMED {task['id']} [{task['priority']}]: {task['title'][:60]}")

    # 3. Route to correct agent
    target_agent = task.get("claimed_by", agent_name)
    if task.get("agent") not in ("any", agent_name):
        target_agent = task["agent"]

    # 4. Execute
    success, result_text = execute_task(task, target_agent)

    # 5. Complete or block via API (with file fallback)
    if success:
        resp = api_call("POST", f"/tasks/{task['id']}/complete?result={urllib.parse.quote(result_text[:500])}")
        if not resp:
            q = TaskQueue()
            q.complete(task["id"], result=result_text[:500])
        log(f"DONE {task['id']}: {result_text[:80]}")
    else:
        resp = api_call("POST", f"/tasks/{task['id']}/block?reason={urllib.parse.quote(result_text[:200])}")
        if not resp:
            q = TaskQueue()
            q.block(task["id"], reason=result_text[:200])
        log(f"BLOCKED {task['id']}: {result_text[:80]}")

    # 6. Write result to outbox
    outbox_file = RELAY_DIR / "outbox" / f"{agent_name.upper()}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_task_{task['id']}.md"
    outbox_file.write_text(
        f"AGENT: {agent_name.upper()}\n"
        f"TASK: {task['id']}\n"
        f"STATUS: {'done' if success else 'blocked'}\n"
        f"TITLE: {task['title']}\n\n"
        f"# Result\n{result_text[:1000]}\n"
    )

    return True


def daemon_loop(agent_name: str, interval: int = 120):
    """Continuous execution loop."""
    log(f"=== RHEA EXECUTOR STARTED as {agent_name.upper()} (interval={interval}s) ===")

    cycle = 0
    while True:
        cycle += 1
        log(f"--- Cycle {cycle} ---")

        # Execute task
        did_work = one_cycle(agent_name)

        # Relay
        relay_cycle()

        # Heartbeat (every 5th cycle)
        if cycle % 5 == 0:
            heartbeat()

        # Git push check (every 3rd cycle)
        if cycle % 3 == 0:
            git_push_check()

        # If no work, sleep longer
        sleep_time = interval if did_work else interval * 2
        log(f"Sleeping {sleep_time}s...")
        time.sleep(sleep_time)


def main():
    parser = argparse.ArgumentParser(description="Rhea autonomous task executor")
    parser.add_argument("--daemon", action="store_true", help="Run continuous loop")
    parser.add_argument("--agent", default="rex", help="Agent name (default: rex)")
    parser.add_argument("--interval", type=int, default=120, help="Loop interval seconds")
    args = parser.parse_args()

    if args.daemon:
        daemon_loop(args.agent, args.interval)
    else:
        one_cycle(args.agent)


if __name__ == "__main__":
    main()
