#!/usr/bin/env python3
"""
task_db.py — SQLite-backed task queue for autonomous multi-agent workflows.

Replaces file-based task_queue.py. SQLite WAL mode handles concurrent
readers/writers natively — no file locking, no race conditions.

Storage: data/tasks.db
Compatible with: tribunal_api.py, rhea_executor.py, any agent via SQL

Usage:
    from task_db import TaskDB
    db = TaskDB()
    db.add("Fix the bridge", priority="P0", agent="rex")
    task = db.claim("gemini")
    db.complete(task["id"], result="done")
    stale = db.release_stale(hours=2)
    summary = db.summary()
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = _PROJECT_ROOT / "data" / "tasks.db"

PRIORITIES = ["P0", "P1", "P2", "P3"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskDB:
    """SQLite task queue with WAL mode for concurrent agent access."""

    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(db_path), timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=5000")
        self._init_schema()

    def _init_schema(self):
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                priority    TEXT NOT NULL DEFAULT 'P1',
                status      TEXT NOT NULL DEFAULT 'open',
                agent       TEXT NOT NULL DEFAULT 'any',
                claimed_by  TEXT NOT NULL DEFAULT '',
                depends_on  TEXT NOT NULL DEFAULT '[]',
                result      TEXT NOT NULL DEFAULT '',
                tags        TEXT NOT NULL DEFAULT '[]',
                created     TEXT NOT NULL,
                updated     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent);
            CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);

            CREATE TABLE IF NOT EXISTS task_log (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                ts      TEXT NOT NULL,
                action  TEXT NOT NULL,
                task_id TEXT,
                agent   TEXT,
                detail  TEXT
            );
        """)
        self.db.commit()

    def _log(self, action: str, task_id: str = "", agent: str = "", detail: str = ""):
        self.db.execute(
            "INSERT INTO task_log (ts, action, task_id, agent, detail) VALUES (?,?,?,?,?)",
            (_now(), action, task_id, agent, detail)
        )

    def _row_to_dict(self, row) -> dict:
        d = dict(row)
        d["depends_on"] = json.loads(d.get("depends_on", "[]"))
        d["tags"] = json.loads(d.get("tags", "[]"))
        return d

    # ─── CRUD ───

    def add(self, title: str, priority: str = "P1", agent: str = "any",
            depends_on: list = None, tags: list = None) -> dict:
        now = _now()
        task_id = f"T-{uuid.uuid4().hex[:8]}"
        self.db.execute(
            """INSERT INTO tasks (id, title, priority, status, agent, claimed_by,
               depends_on, result, tags, created, updated)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (task_id, title, priority if priority in PRIORITIES else "P1",
             "open", agent, "", json.dumps(depends_on or []), "",
             json.dumps(tags or []), now, now)
        )
        self._log("add", task_id, agent, title)
        self.db.commit()
        return self.get(task_id)

    def get(self, task_id: str) -> Optional[dict]:
        row = self.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def claim(self, agent: str) -> Optional[dict]:
        """Claim highest-priority open task. Atomic via SQL transaction."""
        # Prefer tasks assigned to this agent, then "any"
        row = self.db.execute("""
            SELECT * FROM tasks
            WHERE status='open'
              AND (agent=? OR agent='any')
            ORDER BY
              CASE WHEN agent=? THEN 0 ELSE 1 END,
              CASE priority
                WHEN 'P0' THEN 0 WHEN 'P1' THEN 1
                WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 9 END,
              created ASC
            LIMIT 1
        """, (agent, agent)).fetchone()

        if not row:
            return None

        task_id = row["id"]
        now = _now()
        self.db.execute(
            "UPDATE tasks SET status='claimed', claimed_by=?, updated=? WHERE id=?",
            (agent, now, task_id)
        )
        self._log("claim", task_id, agent)
        self.db.commit()
        return self.get(task_id)

    def complete(self, task_id: str, result: str = "") -> Optional[dict]:
        now = _now()
        self.db.execute(
            "UPDATE tasks SET status='done', result=?, updated=? WHERE id=?",
            (result, now, task_id)
        )
        self._log("complete", task_id, detail=result[:200])
        self.db.commit()
        return self.get(task_id)

    def block(self, task_id: str, reason: str = "") -> Optional[dict]:
        now = _now()
        self.db.execute(
            "UPDATE tasks SET status='blocked', result=?, claimed_by='', updated=? WHERE id=?",
            (reason, now, task_id)
        )
        self._log("block", task_id, detail=reason)
        self.db.commit()
        return self.get(task_id)

    def reopen(self, task_id: str) -> Optional[dict]:
        now = _now()
        self.db.execute(
            "UPDATE tasks SET status='open', claimed_by='', result='', updated=? WHERE id=?",
            (now, task_id)
        )
        self._log("reopen", task_id)
        self.db.commit()
        return self.get(task_id)

    def cancel(self, task_id: str, reason: str = "") -> Optional[dict]:
        now = _now()
        self.db.execute(
            "UPDATE tasks SET status='cancelled', result=?, updated=? WHERE id=?",
            (reason, now, task_id)
        )
        self._log("cancel", task_id, detail=reason)
        self.db.commit()
        return self.get(task_id)

    # ─── Queries ───

    def list_tasks(self, status: str = None, agent: str = None,
                   priority: str = None) -> list[dict]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status=?"
            params.append(status)
        if agent:
            query += " AND (agent=? OR claimed_by=?)"
            params.extend([agent, agent])
        if priority:
            query += " AND priority=?"
            params.append(priority)
        query += """ ORDER BY
            CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1
            WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 9 END,
            created ASC"""
        return [self._row_to_dict(r) for r in self.db.execute(query, params).fetchall()]

    def release_stale(self, hours: int = 2) -> list[dict]:
        """Release claimed tasks with no progress for N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        rows = self.db.execute(
            "SELECT * FROM tasks WHERE status='claimed' AND updated<?",
            (cutoff,)
        ).fetchall()
        released = []
        now = _now()
        for row in rows:
            self.db.execute(
                "UPDATE tasks SET status='open', claimed_by='', updated=? WHERE id=?",
                (now, row["id"])
            )
            self._log("release", row["id"], detail=f"stale >{hours}h")
            released.append(self._row_to_dict(row))
        self.db.commit()
        return released

    def summary(self) -> dict:
        counts = {}
        for row in self.db.execute(
            "SELECT status, COUNT(*) as c FROM tasks GROUP BY status"
        ).fetchall():
            counts[row["status"]] = row["c"]

        by_priority = {}
        for row in self.db.execute(
            "SELECT priority, COUNT(*) as c FROM tasks WHERE status IN ('open','claimed') GROUP BY priority"
        ).fetchall():
            by_priority[row["priority"]] = row["c"]

        by_agent = {}
        for row in self.db.execute(
            "SELECT claimed_by, COUNT(*) as c FROM tasks WHERE claimed_by!='' GROUP BY claimed_by"
        ).fetchall():
            by_agent[row["claimed_by"]] = row["c"]

        stale_cutoff = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        stale = self.db.execute(
            "SELECT id, title, claimed_by FROM tasks WHERE status='claimed' AND updated<?",
            (stale_cutoff,)
        ).fetchall()

        total = self.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

        return {
            "total": total,
            "counts": {
                "open": counts.get("open", 0),
                "claimed": counts.get("claimed", 0),
                "done": counts.get("done", 0),
                "blocked": counts.get("blocked", 0),
                "cancelled": counts.get("cancelled", 0),
            },
            "active_by_priority": by_priority,
            "claimed_by_agent": by_agent,
            "stale_count": len(stale),
            "stale_tasks": [dict(r) for r in stale],
            "_updated": _now(),
        }

    # ─── Migration from JSON ───

    def migrate_from_json(self, json_path: Path = None):
        """Import tasks from the old file-based state.json."""
        path = json_path or (_PROJECT_ROOT / "opera" / "tasks" / "state.json")
        if not path.exists():
            return 0

        data = json.loads(path.read_text())
        tasks = data.get("tasks", {})
        imported = 0
        for tid, t in tasks.items():
            existing = self.get(tid)
            if existing:
                continue
            self.db.execute(
                """INSERT INTO tasks (id, title, priority, status, agent, claimed_by,
                   depends_on, result, tags, created, updated)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (tid, t["title"], t["priority"], t["status"], t["agent"],
                 t.get("claimed_by", ""), json.dumps(t.get("depends_on", [])),
                 t.get("result", ""), json.dumps(t.get("tags", [])),
                 t["created"], t["updated"])
            )
            imported += 1
        self.db.commit()
        return imported


# ─── CLI ───

if __name__ == "__main__":
    import sys
    db = TaskDB()

    if len(sys.argv) < 2:
        print(json.dumps(db.summary(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "migrate":
        n = db.migrate_from_json()
        print(f"Migrated {n} tasks from JSON to SQLite")
    elif cmd == "list":
        for t in db.list_tasks():
            print(f"{t['id']} | {t['status']:8s} | {t['priority']} | {t['agent']:10s} | {t['title'][:50]}")
    elif cmd == "summary":
        print(json.dumps(db.summary(), indent=2))
    elif cmd == "release":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        released = db.release_stale(hours)
        print(f"Released {len(released)} stale tasks")
    elif cmd == "claim":
        agent = sys.argv[2] if len(sys.argv) > 2 else "rex"
        task = db.claim(agent)
        print(json.dumps(task, indent=2) if task else "No available tasks")
    elif cmd == "add":
        title = " ".join(sys.argv[2:])
        task = db.add(title)
        print(f"Added: {task['id']}")
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: migrate, list, summary, release [hours], claim [agent], add <title>")
