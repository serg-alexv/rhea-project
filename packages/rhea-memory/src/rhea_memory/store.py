"""
MemoryStore — persistent key-value + timeline memory with SQL backing.

Stores facts, decisions, and session context across agent restarts.
Thread-safe, append-only timeline with key-value overlay.
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MemoryStore:
    """Persistent memory store backed by SQLite.

    Provides two access patterns:
      1. Key-value: store.remember("key", value) / store.recall("key")
      2. Timeline: store.log("event", data) / store.timeline(limit=50)
    """

    def __init__(self, data_dir: str | Path = "./data", db_name: str = "memory.db"):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._dir / db_name
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                data TEXT,
                ts TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_timeline_ts ON timeline(ts);
            CREATE INDEX IF NOT EXISTS idx_timeline_event ON timeline(event);
        """)
        self._conn.commit()

    def remember(self, key: str, value: Any) -> None:
        """Store a fact. Overwrites if key exists."""
        now = datetime.now(timezone.utc).isoformat()
        encoded = json.dumps(value) if not isinstance(value, str) else value
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO kv (key, value, updated_at) VALUES (?, ?, ?)",
                (key, encoded, now)
            )
            self._conn.commit()

    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored fact."""
        row = self._conn.execute(
            "SELECT value FROM kv WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return row[0]

    def forget(self, key: str) -> bool:
        """Remove a stored fact."""
        with self._lock:
            cursor = self._conn.execute("DELETE FROM kv WHERE key = ?", (key,))
            self._conn.commit()
            return cursor.rowcount > 0

    def facts(self) -> dict[str, Any]:
        """Return all stored facts as a dict."""
        rows = self._conn.execute("SELECT key, value FROM kv ORDER BY key").fetchall()
        result = {}
        for key, val in rows:
            try:
                result[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                result[key] = val
        return result

    def log(self, event: str, data: Any = None) -> int:
        """Append to the timeline. Returns the entry ID."""
        now = datetime.now(timezone.utc).isoformat()
        encoded = json.dumps(data) if data is not None else None
        with self._lock:
            cursor = self._conn.execute(
                "INSERT INTO timeline (event, data, ts) VALUES (?, ?, ?)",
                (event, encoded, now)
            )
            self._conn.commit()
            return cursor.lastrowid

    def timeline(self, limit: int = 50, event: str | None = None) -> list[dict]:
        """Query the timeline, newest first."""
        if event:
            rows = self._conn.execute(
                "SELECT id, event, data, ts FROM timeline WHERE event = ? ORDER BY id DESC LIMIT ?",
                (event, limit)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, event, data, ts FROM timeline ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        result = []
        for row_id, evt, data_str, ts in rows:
            entry = {"id": row_id, "event": evt, "ts": ts}
            if data_str:
                try:
                    entry["data"] = json.loads(data_str)
                except (json.JSONDecodeError, TypeError):
                    entry["data"] = data_str
            result.append(entry)
        return result

    def close(self):
        self._conn.close()
