"""
crdb_store.py — CockroachDB persistent store for workflows, tasks, and billing.

Replaces SQLite for cloud persistence (Fly.io). Uses psycopg2 (PostgreSQL wire).
Connection URL from GCloud Secret Manager or COCKROACHDB_URL env var.

Usage:
    from crdb_store import crdb
    crdb.init()
    crdb.upsert_task(task_id, title, agent="rex", priority="P0")
    tasks = crdb.list_tasks(status="pending")
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

log = logging.getLogger("rhea.crdb")

_pool = None


def _get_url() -> str | None:
    """Resolve CockroachDB URL from secrets or env."""
    # Try rhea secrets module (file-level import to avoid stdlib collision)
    try:
        import importlib.util
        _secrets_path = Path(__file__).parent / "secrets.py"
        if _secrets_path.exists():
            spec = importlib.util.spec_from_file_location("rhea_secrets", str(_secrets_path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            url = mod.get_cockroachdb_url()
            if url:
                return url
    except Exception as e:
        log.debug("secrets.py import failed: %s", e)
    return os.environ.get("COCKROACHDB_URL")


def _get_pool():
    global _pool
    if _pool is not None:
        return _pool
    url = _get_url()
    if not url:
        log.warning("No COCKROACHDB_URL — crdb_store disabled")
        return None
    try:
        import psycopg2.pool
        _pool = psycopg2.pool.ThreadedConnectionPool(1, 5, url)
        log.info("CockroachDB pool created (1-5 connections)")
        return _pool
    except Exception as e:
        log.error("CockroachDB pool failed: %s", e)
        return None


@contextmanager
def _conn():
    """Yield a connection from the pool, auto-return on exit."""
    pool = _get_pool()
    if pool is None:
        raise RuntimeError("CockroachDB not available")
    c = pool.getconn()
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        pool.putconn(c)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT NOT NULL DEFAULT 'P1',
    agent TEXT DEFAULT '',
    claimed_by TEXT DEFAULT '',
    claimed_at TIMESTAMPTZ,
    result TEXT DEFAULT '',
    error TEXT DEFAULT '',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);

CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    nodes JSONB NOT NULL DEFAULT '[]',
    edges JSONB NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    last_run_at TIMESTAMPTZ,
    run_count INT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'running',
    node_results JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    error TEXT DEFAULT '',
    duration_ms INT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_wf_runs_wf ON workflow_runs(workflow_id);

CREATE TABLE IF NOT EXISTS billing_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    amount_usd NUMERIC(10,6) DEFAULT 0,
    tokens_used INT DEFAULT 0,
    model TEXT DEFAULT '',
    provider TEXT DEFAULT '',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_billing_user ON billing_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_type ON billing_events(event_type);
"""


def init():
    """Create tables if they don't exist."""
    try:
        with _conn() as c:
            cur = c.cursor()
            cur.execute(_SCHEMA)
            log.info("CockroachDB schema initialized")
            return True
    except Exception as e:
        log.error("CockroachDB schema init failed: %s", e)
        return False


def available() -> bool:
    """Check if CockroachDB is reachable."""
    try:
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT 1")
            return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Tasks CRUD
# ---------------------------------------------------------------------------

def upsert_task(
    task_id: str | None = None,
    title: str = "",
    description: str = "",
    status: str = "pending",
    priority: str = "P1",
    agent: str = "",
    metadata: dict | None = None,
) -> dict:
    """Create or update a task. Returns the task dict."""
    tid = task_id or str(uuid4())
    meta = json.dumps(metadata or {})
    with _conn() as c:
        cur = c.cursor()
        cur.execute("""
            INSERT INTO tasks (id, title, description, status, priority, agent, metadata, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, now())
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                priority = EXCLUDED.priority,
                agent = EXCLUDED.agent,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id, title, status, priority, agent, created_at, updated_at
        """, (tid, title, description, status, priority, agent, meta))
        row = cur.fetchone()
        return {
            "id": str(row[0]), "title": row[1], "status": row[2],
            "priority": row[3], "agent": row[4],
            "created_at": row[5].isoformat() if row[5] else None,
            "updated_at": row[6].isoformat() if row[6] else None,
        }


def claim_task(task_id: str, agent: str) -> bool:
    """Claim a pending task for an agent. Returns True if claimed."""
    with _conn() as c:
        cur = c.cursor()
        cur.execute("""
            UPDATE tasks SET claimed_by = %s, claimed_at = now(), status = 'running', updated_at = now()
            WHERE id = %s AND status = 'pending'
        """, (agent, task_id))
        return cur.rowcount > 0


def complete_task(task_id: str, result: str = "", error: str = "") -> bool:
    """Mark a task as completed or failed."""
    status = "failed" if error else "completed"
    with _conn() as c:
        cur = c.cursor()
        cur.execute("""
            UPDATE tasks SET status = %s, result = %s, error = %s, updated_at = now()
            WHERE id = %s
        """, (status, result, error, task_id))
        return cur.rowcount > 0


def list_tasks(
    status: str | None = None,
    agent: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List tasks with optional filters."""
    with _conn() as c:
        cur = c.cursor()
        where, params = [], []
        if status:
            where.append("status = %s")
            params.append(status)
        if agent:
            where.append("(agent = %s OR claimed_by = %s)")
            params.extend([agent, agent])
        clause = "WHERE " + " AND ".join(where) if where else ""
        cur.execute(f"""
            SELECT id, title, description, status, priority, agent, claimed_by,
                   result, error, metadata, created_at, updated_at
            FROM tasks {clause}
            ORDER BY
                CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END,
                created_at DESC
            LIMIT %s
        """, params + [limit])
        return [_task_row(r) for r in cur.fetchall()]


def _task_row(r) -> dict:
    return {
        "id": str(r[0]), "title": r[1], "description": r[2],
        "status": r[3], "priority": r[4], "agent": r[5],
        "claimed_by": r[6], "result": r[7], "error": r[8],
        "metadata": r[9] if isinstance(r[9], dict) else json.loads(r[9] or "{}"),
        "created_at": r[10].isoformat() if r[10] else None,
        "updated_at": r[11].isoformat() if r[11] else None,
    }


# ---------------------------------------------------------------------------
# Workflows CRUD
# ---------------------------------------------------------------------------

def save_workflow(
    workflow_id: str | None = None,
    name: str = "",
    description: str = "",
    nodes: list | None = None,
    edges: list | None = None,
    status: str = "draft",
    metadata: dict | None = None,
) -> dict:
    wid = workflow_id or str(uuid4())
    with _conn() as c:
        cur = c.cursor()
        cur.execute("""
            INSERT INTO workflows (id, name, description, nodes, edges, status, metadata, updated_at)
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb, now())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name, description = EXCLUDED.description,
                nodes = EXCLUDED.nodes, edges = EXCLUDED.edges,
                status = EXCLUDED.status, metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id, name, status, created_at
        """, (wid, name, description,
              json.dumps(nodes or []), json.dumps(edges or []),
              status, json.dumps(metadata or {})))
        row = cur.fetchone()
        return {"id": str(row[0]), "name": row[1], "status": row[2],
                "created_at": row[3].isoformat() if row[3] else None}


def list_workflows(limit: int = 50) -> list[dict]:
    with _conn() as c:
        cur = c.cursor()
        cur.execute("""
            SELECT id, name, description, status, run_count, created_at, updated_at
            FROM workflows ORDER BY updated_at DESC LIMIT %s
        """, (limit,))
        return [{
            "id": str(r[0]), "name": r[1], "description": r[2],
            "status": r[3], "run_count": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
            "updated_at": r[6].isoformat() if r[6] else None,
        } for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------

def log_billing(
    user_id: str,
    event_type: str,
    amount_usd: float = 0.0,
    tokens_used: int = 0,
    model: str = "",
    provider: str = "",
    metadata: dict | None = None,
) -> str:
    """Log a billing event. Returns event ID."""
    with _conn() as c:
        cur = c.cursor()
        cur.execute("""
            INSERT INTO billing_events (user_id, event_type, amount_usd, tokens_used,
                                        model, provider, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            RETURNING id
        """, (user_id, event_type, amount_usd, tokens_used,
              model, provider, json.dumps(metadata or {})))
        return str(cur.fetchone()[0])


def billing_summary(user_id: str) -> dict:
    """Get billing summary for a user."""
    with _conn() as c:
        cur = c.cursor()
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount_usd), 0), COALESCE(SUM(tokens_used), 0)
            FROM billing_events WHERE user_id = %s
        """, (user_id,))
        row = cur.fetchone()
        return {
            "total_events": row[0],
            "total_usd": float(row[1]),
            "total_tokens": int(row[2]),
        }
