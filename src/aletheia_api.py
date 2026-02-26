"""
aletheia_api.py — FastAPI router for the Aletheia proof verification pipeline.

Endpoints:
  POST /submit           — submit a proof/theorem for verification
  GET  /proofs           — list all stored proofs
  GET  /proofs/{id}      — get a specific proof by ID
  POST /verify/{id}      — trigger re-verification of a proof

Storage: SQLite at data/aletheia.db, table `proofs`
         (id, title, statement, proof_text, status, submitted_at, verified_at, score)

Note: No LLM calls yet — pure CRUD + status tracking.
      The aletheia_pipeline.py handles deep tribunal-integrated capture.
      This router is the public-facing submission/retrieval API (Phase 6).
"""

import hashlib
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
ALETHEIA_DB = PROJECT_ROOT / "data" / "aletheia.db"

# Valid status values
STATUS_PENDING = "pending"
STATUS_VERIFIED = "verified"
STATUS_REJECTED = "rejected"
STATUS_INCONCLUSIVE = "inconclusive"

VALID_STATUSES = {STATUS_PENDING, STATUS_VERIFIED, STATUS_REJECTED, STATUS_INCONCLUSIVE}


# ─────────────────────────────────────────────────────────────────────────────
# Database bootstrap
# ─────────────────────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS proofs (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    statement    TEXT NOT NULL,
    proof_text   TEXT NOT NULL DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'pending',
    submitted_at TEXT NOT NULL,
    verified_at  TEXT,
    score        REAL
);

CREATE INDEX IF NOT EXISTS idx_aletheia_status       ON proofs(status);
CREATE INDEX IF NOT EXISTS idx_aletheia_submitted_at ON proofs(submitted_at);
CREATE INDEX IF NOT EXISTS idx_aletheia_score        ON proofs(score);
"""


def _get_conn() -> sqlite3.Connection:
    """Return an open SQLite connection with WAL mode and schema ensured."""
    ALETHEIA_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ALETHEIA_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────

class ProofSubmitRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Short title for the theorem/claim")
    statement: str = Field(..., min_length=1, description="Formal or informal statement of what is being proved")
    proof_text: str = Field(default="", description="The proof body (may be empty for theorems awaiting proof)")


class ProofResponse(BaseModel):
    id: str
    title: str
    statement: str
    proof_text: str
    status: str
    submitted_at: str
    verified_at: Optional[str]
    score: Optional[float]


class VerifyRequest(BaseModel):
    """Optional body for POST /verify/{id} — allows passing a scorer hint."""
    force: bool = Field(default=False, description="Re-verify even if already verified")
    score_override: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Manually set score (0.0–1.0); if provided, drives status update"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _generate_id(title: str, statement: str) -> str:
    """Deterministic-ish ID: SHA-256 of title+statement+current nanoseconds."""
    raw = f"{title}:{statement}:{time.time_ns()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_proof(row: sqlite3.Row) -> dict:
    return {
        "id":           row["id"],
        "title":        row["title"],
        "statement":    row["statement"],
        "proof_text":   row["proof_text"],
        "status":       row["status"],
        "submitted_at": row["submitted_at"],
        "verified_at":  row["verified_at"],
        "score":        row["score"],
    }


def _derive_status_from_score(score: float) -> str:
    """
    Rule-based status from score.
    >= 0.85  → verified
    >= 0.50  → inconclusive
    < 0.50   → rejected
    """
    if score >= 0.85:
        return STATUS_VERIFIED
    if score >= 0.50:
        return STATUS_INCONCLUSIVE
    return STATUS_REJECTED


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

aletheia_router = APIRouter(tags=["aletheia"])


@aletheia_router.post("/submit", response_model=ProofResponse, status_code=201)
def submit_proof(body: ProofSubmitRequest):
    """
    Submit a proof or theorem for verification.

    Returns the created proof record with status='pending'.
    Re-verification can be triggered later via POST /verify/{id}.
    """
    proof_id = _generate_id(body.title, body.statement)
    now = _now_iso()

    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO proofs (id, title, statement, proof_text, status, submitted_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (proof_id, body.title, body.statement, body.proof_text, STATUS_PENDING, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM proofs WHERE id = ?", (proof_id,)).fetchone()
    finally:
        conn.close()

    return _row_to_proof(row)


@aletheia_router.get("/proofs", response_model=List[ProofResponse])
def list_proofs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    List stored proofs, ordered by submitted_at descending.

    Query params:
      status  — filter by status (pending|verified|rejected|inconclusive)
      limit   — max results (default 50, max 200)
      offset  — pagination offset
    """
    if status and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{status}'. Valid: {sorted(VALID_STATUSES)}"
        )
    limit = min(limit, 200)

    conn = _get_conn()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM proofs WHERE status = ? "
                "ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                (status, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM proofs ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
    finally:
        conn.close()

    return [_row_to_proof(r) for r in rows]


@aletheia_router.get("/proofs/{proof_id}", response_model=ProofResponse)
def get_proof(proof_id: str):
    """
    Retrieve a single proof by its ID.

    Returns 404 if the proof does not exist.
    """
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM proofs WHERE id = ?", (proof_id,)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Proof '{proof_id}' not found")

    return _row_to_proof(row)


@aletheia_router.post("/verify/{proof_id}", response_model=ProofResponse)
def verify_proof(proof_id: str, body: VerifyRequest = VerifyRequest()):
    """
    Trigger (re-)verification of a stored proof.

    Current behaviour (no LLM integration yet):
      - If score_override is provided: apply it, derive status, set verified_at.
      - If no score_override and status is already verified: return as-is
        (unless force=True, which resets to pending for a fresh run).
      - If no score_override and status is pending/inconclusive: mark as
        inconclusive (placeholder — LLM verifier will fill this in Phase 7).

    When the LLM verifier is wired in (Phase 7), replace the placeholder block
    with a call to aletheia_pipeline.capture() or a dedicated verify() function.
    """
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM proofs WHERE id = ?", (proof_id,)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Proof '{proof_id}' not found")

        current_status = row["status"]
        now = _now_iso()

        if body.score_override is not None:
            # Caller supplied a score — apply immediately
            new_status = _derive_status_from_score(body.score_override)
            conn.execute(
                "UPDATE proofs SET status = ?, score = ?, verified_at = ? WHERE id = ?",
                (new_status, body.score_override, now, proof_id),
            )
            conn.commit()

        elif body.force:
            # Force re-verification: reset to pending (LLM hook goes here in Phase 7)
            conn.execute(
                "UPDATE proofs SET status = ?, score = NULL, verified_at = NULL WHERE id = ?",
                (STATUS_PENDING, proof_id),
            )
            conn.commit()

        elif current_status == STATUS_VERIFIED and not body.force:
            # Already verified — return without modification
            pass

        else:
            # Placeholder: no LLM yet — mark inconclusive so callers know it was attempted
            conn.execute(
                "UPDATE proofs SET status = ?, verified_at = ? WHERE id = ?",
                (STATUS_INCONCLUSIVE, now, proof_id),
            )
            conn.commit()

        updated = conn.execute(
            "SELECT * FROM proofs WHERE id = ?", (proof_id,)
        ).fetchone()
    finally:
        conn.close()

    return _row_to_proof(updated)
