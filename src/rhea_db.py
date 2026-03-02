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

        CREATE TABLE IF NOT EXISTS clipboard (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_id TEXT NOT NULL DEFAULT '',
            device_name TEXT DEFAULT '',
            content_type TEXT NOT NULL DEFAULT 'text',
            content TEXT NOT NULL,
            content_preview TEXT,
            content_hash TEXT,
            privacy TEXT DEFAULT 'normal',
            ttl_seconds INTEGER,
            pinned INTEGER DEFAULT 0,
            source_app TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            expires_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_clip_user ON clipboard(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_clip_hash ON clipboard(content_hash);
        CREATE INDEX IF NOT EXISTS idx_clip_expires ON clipboard(expires_at);

        CREATE TABLE IF NOT EXISTS shares (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL DEFAULT '',
            content_type TEXT NOT NULL DEFAULT 'text',
            title TEXT DEFAULT '',
            content TEXT NOT NULL,
            metadata TEXT,
            views INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            expires_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_shares_user ON shares(user_id, created_at DESC);
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


# ─── Clipboard Write-Through ─────────────────────────────────────────

import re as _re

_SENSITIVE_PATTERNS = [
    _re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),  # credit card
    _re.compile(r"\b(sk|pk|api|token|secret|password|bearer)[_-]?\w{16,}", _re.I),  # API keys/tokens
    _re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),  # PEM keys
    _re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"),  # long base64 (likely secrets)
]


def _classify_privacy(content: str) -> tuple[str, Optional[int]]:
    """Auto-classify clipboard content privacy level. Returns (privacy, ttl_seconds)."""
    for pat in _SENSITIVE_PATTERNS:
        if pat.search(content):
            return "secret", 30
    return "normal", None


def persist_clipboard(clip: dict) -> dict:
    """Insert a clipboard entry. Deduplicates by content_hash within 60s window."""
    import hashlib, uuid
    conn = _get_conn()
    content = clip.get("content", "")
    content_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]
    user_id = clip.get("user_id", "anon")

    # Dedup: skip if same hash from same user within last 60 seconds
    recent = conn.execute(
        "SELECT id FROM clipboard WHERE user_id=? AND content_hash=? AND created_at > datetime('now', '-60 seconds')",
        (user_id, content_hash),
    ).fetchone()
    if recent:
        return {"id": recent["id"], "deduplicated": True}

    # Auto-classify privacy if not provided
    privacy = clip.get("privacy")
    ttl = clip.get("ttl_seconds")
    if not privacy:
        privacy, auto_ttl = _classify_privacy(content)
        if ttl is None:
            ttl = auto_ttl

    now = datetime.now(timezone.utc).isoformat()
    expires_at = None
    if ttl:
        from datetime import timedelta
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()

    clip_id = clip.get("id") or uuid.uuid4().hex[:12]
    preview = content[:120] if privacy != "secret" else "[redacted]"

    conn.execute(
        """INSERT INTO clipboard (id, user_id, device_id, device_name, content_type,
           content, content_preview, content_hash, privacy, ttl_seconds, pinned,
           source_app, created_at, expires_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (clip_id, user_id, clip.get("device_id", ""), clip.get("device_name", ""),
         clip.get("content_type", "text"), content, preview, content_hash,
         privacy, ttl, clip.get("pinned", 0), clip.get("source_app", ""),
         now, expires_at),
    )
    conn.commit()
    return {"id": clip_id, "privacy": privacy, "ttl_seconds": ttl, "expires_at": expires_at, "deduplicated": False}


def query_clipboard(user_id: str, limit: int = 50, content_type: Optional[str] = None,
                    pinned_only: bool = False) -> list[dict]:
    """Query clipboard history for a user, excluding expired entries."""
    conn = _get_conn()
    # Clean expired entries first
    conn.execute("DELETE FROM clipboard WHERE expires_at IS NOT NULL AND expires_at < datetime('now')")
    conn.commit()

    sql = "SELECT * FROM clipboard WHERE user_id = ?"
    params: list = [user_id]
    if content_type:
        sql += " AND content_type = ?"
        params.append(content_type)
    if pinned_only:
        sql += " AND pinned = 1"
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_clipboard_latest(user_id: str) -> Optional[dict]:
    """Get the latest clipboard entry for a user."""
    results = query_clipboard(user_id, limit=1)
    return results[0] if results else None


def delete_clipboard(user_id: str, clip_id: str) -> bool:
    conn = _get_conn()
    cur = conn.execute("DELETE FROM clipboard WHERE id = ? AND user_id = ?", (clip_id, user_id))
    conn.commit()
    return cur.rowcount > 0


def clear_clipboard(user_id: str, before: Optional[str] = None) -> int:
    conn = _get_conn()
    if before:
        cur = conn.execute("DELETE FROM clipboard WHERE user_id = ? AND created_at < ? AND pinned = 0",
                           (user_id, before))
    else:
        cur = conn.execute("DELETE FROM clipboard WHERE user_id = ? AND pinned = 0", (user_id,))
    conn.commit()
    return cur.rowcount


def pin_clipboard(user_id: str, clip_id: str, pinned: bool = True) -> bool:
    conn = _get_conn()
    cur = conn.execute("UPDATE clipboard SET pinned = ?, expires_at = NULL WHERE id = ? AND user_id = ?",
                       (1 if pinned else 0, clip_id, user_id))
    conn.commit()
    return cur.rowcount > 0


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


# ─── Shares ──────────────────────────────────────────────────────────

import secrets as _secrets


def create_share(
    content: str,
    content_type: str = "text",
    title: str = "",
    user_id: str = "",
    metadata: Optional[dict] = None,
    ttl_hours: int = 720,  # 30 days default
) -> dict:
    """Create a shareable link. Returns the share record with token."""
    token = _secrets.token_urlsafe(12)  # 16-char URL-safe token
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    expires_at = (now + timedelta(hours=ttl_hours)).isoformat() if ttl_hours else None

    conn = _get_conn()
    conn.execute(
        "INSERT INTO shares (token, user_id, content_type, title, content, metadata, created_at, expires_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (token, user_id, content_type, title, content,
         json.dumps(metadata) if metadata else None,
         now.isoformat(), expires_at),
    )
    conn.commit()
    return {
        "token": token,
        "content_type": content_type,
        "title": title,
        "created_at": now.isoformat(),
        "expires_at": expires_at,
    }


def get_share(token: str) -> Optional[dict]:
    """Retrieve a shared item by token. Increments view count. Returns None if expired/missing."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM shares WHERE token = ?", (token,)).fetchone()
    if not row:
        return None
    rec = dict(row)
    # Check expiration
    if rec.get("expires_at"):
        exp = datetime.fromisoformat(rec["expires_at"])
        if datetime.now(timezone.utc) > exp:
            conn.execute("DELETE FROM shares WHERE token = ?", (token,))
            conn.commit()
            return None
    # Increment views
    conn.execute("UPDATE shares SET views = views + 1 WHERE token = ?", (token,))
    conn.commit()
    # Parse metadata
    if rec.get("metadata"):
        try:
            rec["metadata"] = json.loads(rec["metadata"])
        except (json.JSONDecodeError, TypeError):
            pass
    return rec


def list_shares(user_id: str, limit: int = 50) -> list:
    """List shares created by a user."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT token, content_type, title, views, created_at, expires_at "
        "FROM shares WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def delete_share(token: str, user_id: str = "") -> bool:
    """Delete a share. If user_id given, requires ownership."""
    conn = _get_conn()
    if user_id:
        cur = conn.execute("DELETE FROM shares WHERE token = ? AND user_id = ?", (token, user_id))
    else:
        cur = conn.execute("DELETE FROM shares WHERE token = ?", (token,))
    conn.commit()
    return cur.rowcount > 0
