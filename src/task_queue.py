#!/usr/bin/env python3
"""
task_queue.py — Persistent task pipeline for autonomous multi-agent sprints.

Missing piece for 2-week continuous operation:
  Governor → IF agent can work (budget/floor)
  Office   → HOW agents communicate
  Queue    → WHAT to work on next

Storage: opera/tasks/queue.jsonl (append-only log)
State:   opera/tasks/state.json  (latest snapshot, rebuilt from log)

Usage:
    from task_queue import TaskQueue
    q = TaskQueue()
    q.add("Deploy tribunal to Fly.io", priority="P0", agent="rex")
    task = q.claim("orion")          # claim highest-priority unclaimed task
    q.complete(task["id"], result="deployed at https://...")
    q.block(task["id"], reason="API key expired")
    stale = q.stale_check(hours=4)   # tasks claimed but no progress
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUEUE_LOG = _PROJECT_ROOT / "opera" / "tasks" / "queue.jsonl"
QUEUE_STATE = _PROJECT_ROOT / "opera" / "tasks" / "state.json"

PRIORITIES = ["P0", "P1", "P2", "P3"]
STATUSES = ["open", "claimed", "done", "blocked", "cancelled"]


@dataclass
class Task:
    id: str
    title: str
    priority: str       # P0 (critical) → P3 (nice-to-have)
    status: str         # open | claimed | done | blocked | cancelled
    agent: str          # who should/did work on it ("any" = unclaimed)
    depends_on: list    # task IDs that must be done first
    result: str         # completion result or block reason
    created: str
    updated: str
    claimed_by: str     # agent who claimed it
    tags: list          # for filtering: ["deploy", "frontend", "api", etc.]


class TaskQueue:
    """Persistent task pipeline — append-only log + state snapshot."""

    def __init__(self):
        QUEUE_LOG.parent.mkdir(parents=True, exist_ok=True)
        self.tasks: dict[str, dict] = {}
        self._load_state()

    def add(self, title: str, priority: str = "P1", agent: str = "any",
            depends_on: list | None = None, tags: list | None = None) -> dict:
        """Add a new task to the queue."""
        now = datetime.now(timezone.utc).isoformat()
        task = Task(
            id=f"T-{uuid.uuid4().hex[:8]}",
            title=title,
            priority=priority if priority in PRIORITIES else "P1",
            status="open",
            agent=agent,
            depends_on=depends_on or [],
            result="",
            created=now,
            updated=now,
            claimed_by="",
            tags=tags or [],
        )
        td = asdict(task)
        self.tasks[task.id] = td
        self._append_log("add", td)
        self._save_state()
        return td

    def claim(self, agent: str) -> Optional[dict]:
        """Claim the highest-priority available task for an agent.

        Selection: P0 first, then P1, etc. Within same priority: oldest first.
        Skips tasks with unmet dependencies or already claimed.
        Prefers tasks assigned to this agent over "any".
        """
        candidates = []
        for t in self.tasks.values():
            if t["status"] != "open":
                continue
            # Check dependencies
            if any(self.tasks.get(dep, {}).get("status") != "done"
                   for dep in t["depends_on"]):
                continue
            # Check agent assignment
            if t["agent"] not in ("any", agent):
                continue
            candidates.append(t)

        if not candidates:
            return None

        # Sort: agent-specific first, then by priority, then by creation time
        def sort_key(t):
            agent_match = 0 if t["agent"] == agent else 1
            pri = PRIORITIES.index(t["priority"]) if t["priority"] in PRIORITIES else 9
            return (agent_match, pri, t["created"])

        candidates.sort(key=sort_key)
        task = candidates[0]

        task["status"] = "claimed"
        task["claimed_by"] = agent
        task["updated"] = datetime.now(timezone.utc).isoformat()
        self._append_log("claim", {"id": task["id"], "agent": agent})
        self._save_state()
        return task

    def complete(self, task_id: str, result: str = "") -> Optional[dict]:
        """Mark task as done with optional result."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        task["status"] = "done"
        task["result"] = result
        task["updated"] = datetime.now(timezone.utc).isoformat()
        self._append_log("complete", {"id": task_id, "result": result})
        self._save_state()
        return task

    def block(self, task_id: str, reason: str = "") -> Optional[dict]:
        """Mark task as blocked with reason."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        task["status"] = "blocked"
        task["result"] = reason
        task["claimed_by"] = ""
        task["updated"] = datetime.now(timezone.utc).isoformat()
        self._append_log("block", {"id": task_id, "reason": reason})
        self._save_state()
        return task

    def unblock(self, task_id: str) -> Optional[dict]:
        """Return blocked task to open status."""
        task = self.tasks.get(task_id)
        if not task or task["status"] != "blocked":
            return None
        task["status"] = "open"
        task["result"] = ""
        task["updated"] = datetime.now(timezone.utc).isoformat()
        self._append_log("unblock", {"id": task_id})
        self._save_state()
        return task

    def cancel(self, task_id: str, reason: str = "") -> Optional[dict]:
        """Cancel a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        task["status"] = "cancelled"
        task["result"] = reason
        task["updated"] = datetime.now(timezone.utc).isoformat()
        self._append_log("cancel", {"id": task_id, "reason": reason})
        self._save_state()
        return task

    def list_tasks(self, status: str | None = None, agent: str | None = None,
                   priority: str | None = None) -> list[dict]:
        """List tasks with optional filters."""
        result = []
        for t in self.tasks.values():
            if status and t["status"] != status:
                continue
            if agent and t["agent"] != agent and t["claimed_by"] != agent:
                continue
            if priority and t["priority"] != priority:
                continue
            result.append(t)
        # Sort by priority then created
        result.sort(key=lambda t: (
            PRIORITIES.index(t["priority"]) if t["priority"] in PRIORITIES else 9,
            t["created"]
        ))
        return result

    def stale_check(self, hours: int = 4) -> list[dict]:
        """Find claimed tasks with no progress for N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        stale = []
        for t in self.tasks.values():
            if t["status"] == "claimed" and t["updated"] < cutoff:
                stale.append(t)
        return stale

    def summary(self) -> dict:
        """Queue health summary for governor/dashboard."""
        counts = {"open": 0, "claimed": 0, "done": 0, "blocked": 0, "cancelled": 0}
        by_priority = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        by_agent = {}
        for t in self.tasks.values():
            counts[t["status"]] = counts.get(t["status"], 0) + 1
            if t["status"] in ("open", "claimed"):
                by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1
            if t["claimed_by"]:
                by_agent[t["claimed_by"]] = by_agent.get(t["claimed_by"], 0) + 1

        stale = self.stale_check()
        return {
            "total": len(self.tasks),
            "counts": counts,
            "active_by_priority": by_priority,
            "claimed_by_agent": by_agent,
            "stale_count": len(stale),
            "stale_tasks": [{"id": t["id"], "title": t["title"], "claimed_by": t["claimed_by"]}
                           for t in stale],
            "_updated": datetime.now(timezone.utc).isoformat(),
        }

    # --- Persistence ---

    def _append_log(self, action: str, data: dict) -> None:
        """Append event to queue log (append-only, git-trackable)."""
        entry = {
            "action": action,
            "ts": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        with open(QUEUE_LOG, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def _save_state(self) -> None:
        """Write current state snapshot."""
        state = {
            "tasks": self.tasks,
            "_updated": datetime.now(timezone.utc).isoformat(),
        }
        QUEUE_STATE.write_text(json.dumps(state, indent=2, default=str))

    def _load_state(self) -> None:
        """Load from state snapshot (faster than replaying full log)."""
        if QUEUE_STATE.exists():
            try:
                state = json.loads(QUEUE_STATE.read_text())
                self.tasks = state.get("tasks", {})
                return
            except (json.JSONDecodeError, KeyError):
                pass
        self.tasks = {}


# --- Seed from TODO.md ---

def seed_from_todo(todo_path: Path | None = None) -> list[dict]:
    """Import tasks from TODO.md into the queue (idempotent)."""
    path = todo_path or (_PROJECT_ROOT / "TODO.md")
    if not path.exists():
        return []
    q = TaskQueue()
    existing_titles = {t["title"] for t in q.tasks.values()}

    added = []
    content = path.read_text()
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("- [ ]"):
            continue
        title = line[5:].strip().lstrip("  ")
        if title in existing_titles:
            continue
        # Infer priority from section context
        task = q.add(title, priority="P1", tags=["from-todo"])
        added.append(task)
    return added


# --- CLI ---

if __name__ == "__main__":
    import sys

    q = TaskQueue()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "summary":
        s = q.summary()
        print(f"  Tasks: {s['total']} | Open: {s['counts']['open']} | Claimed: {s['counts']['claimed']} | Done: {s['counts']['done']} | Blocked: {s['counts']['blocked']}")
        if s["stale_count"]:
            print(f"  ⚠ Stale: {s['stale_count']} tasks claimed but no progress >4h")
        for p in ["P0", "P1", "P2", "P3"]:
            if s["active_by_priority"][p]:
                print(f"  {p}: {s['active_by_priority'][p]} active")

    elif cmd == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        tasks = q.list_tasks(status=status)
        for t in tasks:
            icon = {"open": "○", "claimed": "◉", "done": "✓", "blocked": "✗", "cancelled": "–"}.get(t["status"], "?")
            agent = f" @{t['claimed_by']}" if t["claimed_by"] else ""
            print(f"  {icon} [{t['priority']}] {t['id']}  {t['title']}{agent}")

    elif cmd == "seed":
        added = seed_from_todo()
        print(f"  Seeded {len(added)} tasks from TODO.md")
        for t in added:
            print(f"    + [{t['priority']}] {t['id']}  {t['title']}")

    elif cmd == "add":
        title = " ".join(sys.argv[2:])
        if title:
            task = q.add(title)
            print(f"  + {task['id']}  {task['title']}")

    elif cmd == "claim":
        agent = sys.argv[2] if len(sys.argv) > 2 else "rex"
        task = q.claim(agent)
        if task:
            print(f"  ◉ @{agent} claimed [{task['priority']}] {task['id']}  {task['title']}")
        else:
            print(f"  No available tasks for @{agent}")

    elif cmd == "done":
        tid = sys.argv[2] if len(sys.argv) > 2 else ""
        result = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        task = q.complete(tid, result)
        if task:
            print(f"  ✓ {task['id']}  {task['title']}")
        else:
            print(f"  Task not found: {tid}")

    else:
        print("Usage: task_queue.py [summary|list|seed|add|claim|done] [args...]")
