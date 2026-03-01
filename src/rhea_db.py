"""
rhea_db.py — Unified SQL persistence for Rhea Command Centre.

Persists: session history, radio feed, office messages.
Write-through: callers append to in-memory structures AND call these functions.
Database: data/rhea.db (SQLite WAL mode for concurrent reads).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = _PROJECT_ROOT / "data" / "rhea.db"

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Thread-local SQLite connection with WAL mode."""
    if not hasattr(_local, "conn") or _local.conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        _local.conn = conn
    return _local.conn


def init_db() -> None:
    """Create tables if they don't exist. Safe to call multiple times."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            agent TEXT,
            mode TEXT
        );

        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            step INTEGER NOT NULL,
            type TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT,
            agreement_score REAL,
            confidence REAL,
            models TEXT,
            tier TEXT,
            created_at TEXT NOT NULL,
            metadata TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_history_session ON history(session_id);
        CREATE INDEX IF NOT EXISTS idx_history_type ON history(type);
        CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at);

        CREATE TABLE IF NOT EXISTS radio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            sender TEXT NOT NULL,
            receiver TEXT,
            text TEXT NOT NULL,
            ts TEXT NOT NULL,
            metadata TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_radio_ts ON radio(ts);
        CREATE INDEX IF NOT EXISTS idx_radio_sender ON radio(sender);

        CREATE TABLE IF NOT EXISTS office_messages (
            id TEXT PRIMARY KEY,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            text TEXT NOT NULL,
            compressed TEXT,
            ts TEXT NOT NULL,
            reply_to TEXT,
            response TEXT,
            response_ts TEXT,
            gate_tokens INTEGER DEFAULT 0,
            relay_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0
        );
        CREATE INDEX IF NOT EXISTS idx_office_ts ON office_messages(ts);
        CREATE INDEX IF NOT EXISTS idx_office_sender ON office_messages(sender);
    """)
    conn.commit()


# ─── Session Management ───────────────────────────────────────────────

_current_session_id: Optional[str] = None


def start_session(session_id: str, agent: str = "tribunal", mode: str = "normal") -> str:
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO sessions (id, started_at, agent, mode) VALUES (?, ?, ?, ?)",
        (session_id, datetime.now(timezone.utc).isoformat(), agent, mode),
    )
    conn.commit()
    global _current_session_id
    _current_session_id = session_id
    return session_id


def get_session_id() -> str:
    global _current_session_id
    if _current_session_id is None:
        import uuid
        _current_session_id = uuid.uuid4().hex[:12]
        start_session(_current_session_id)
    return _current_session_id


# ─── History Write-Through ─────────────────────────────────────────────

def persist_history(
    step: int,
    endpoint: str,
    prompt: str,
    response_dict: dict,
    ontology: str = "general",
) -> None:
    """Write-through: persist a tribunal/sceptic/ice step to SQL."""
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO history (session_id, step, type, prompt, response,
               agreement_score, confidence, models, tier, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                get_session_id(),
                step,
                endpoint.strip("/").replace("/", "_"),
                prompt,
                json.dumps(response_dict.get("consensus", response_dict.get("response", ""))),
                response_dict.get("agreement_score", 0.0),
                response_dict.get("confidence", 0.0),
                json.dumps(response_dict.get("models", [])) if isinstance(response_dict.get("models"), list)
                    else str(response_dict.get("models_responded", "")),
                response_dict.get("tier", ""),
                datetime.now(timezone.utc).isoformat(),
                json.dumps({"ontology": ontology, "endpoint": endpoint}),
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"[rhea_db] history persist error: {e}")


# ─── Radio Write-Through ──────────────────────────────────────────────

def persist_radio(event: dict) -> None:
    """Write-through: persist a radio/broadcast event to SQL."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO radio (type, sender, receiver, text, ts, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (
                event.get("type", "radio"),
                event.get("sender", "system"),
                event.get("receiver", ""),
                event.get("text", ""),
                event.get("ts", datetime.now(timezone.utc).isoformat()),
                json.dumps({k: v for k, v in event.items() if k not in ("type", "sender", "receiver", "text", "ts")}),
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"[rhea_db] radio persist error: {e}")


# ─── Office Write-Through ─────────────────────────────────────────────

def persist_office_message(msg_dict: dict) -> None:
    """Write-through: persist an office message to SQL."""
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO office_messages
               (id, sender, receiver, text, compressed, ts, reply_to, response, response_ts, gate_tokens, relay_tokens, cost_usd)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                msg_dict.get("id", ""),
                msg_dict.get("sender", ""),
                msg_dict.get("receiver", ""),
                msg_dict.get("text", msg_dict.get("compressed", "")),
                msg_dict.get("compressed", ""),
                msg_dict.get("ts", ""),
                msg_dict.get("reply_to"),
                msg_dict.get("response"),
                msg_dict.get("response_ts"),
                msg_dict.get("gate_tokens", 0),
                msg_dict.get("relay_tokens", 0),
                msg_dict.get("cost_usd", 0.0),
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"[rhea_db] office persist error: {e}")


# ─── Query Helpers (for Command Centre API) ───────────────────────────

def query_history(limit: int = 50, session_id: Optional[str] = None, type_filter: Optional[str] = None) -> list[dict]:
    conn = _get_conn()
    sql = "SELECT * FROM history WHERE 1=1"
    params = []
    if session_id:
        sql += " AND session_id = ?"
        params.append(session_id)
    if type_filter:
        sql += " AND type = ?"
        params.append(type_filter)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def query_radio(limit: int = 100, since: Optional[str] = None) -> list[dict]:
    conn = _get_conn()
    sql = "SELECT * FROM radio"
    params = []
    if since:
        sql += " WHERE ts > ?"
        params.append(since)
    sql += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def query_office(limit: int = 50, agent: Optional[str] = None) -> list[dict]:
    conn = _get_conn()
    sql = "SELECT * FROM office_messages"
    params = []
    if agent:
        sql += " WHERE sender = ? OR receiver = ?"
        params.extend([agent, agent])
    sql += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def query_sessions(limit: int = 20) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT s.*, COUNT(h.id) as step_count FROM sessions s LEFT JOIN history h ON s.id = h.session_id GROUP BY s.id ORDER BY s.started_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


# ─── JSONL Migration ──────────────────────────────────────────────────

def migrate_office_jsonl(jsonl_path: Optional[Path] = None) -> int:
    """One-time: import existing office.jsonl into SQL. Returns count imported."""
    path = jsonl_path or (_PROJECT_ROOT / "data" / "office.jsonl")
    if not path.exists():
        return 0
    conn = _get_conn()
    existing = conn.execute("SELECT COUNT(*) FROM office_messages").fetchone()[0]
    if existing > 0:
        return 0  # already migrated
    count = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                persist_office_message(rec)
                count += 1
            except Exception:
                continue
    return count
