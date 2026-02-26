"""auth_api.py — Minimal JWT auth router for Rhea FastAPI backend.

Endpoints:
  POST /auth/signup   — register email+password, return JWT
  POST /auth/login    — verify email+password, return JWT
  GET  /auth/profile  — bearer-protected, return profile
  POST /auth/logout   — stateless acknowledgement

Storage : SQLite at data/users.db (auto-created)
Hashing : hashlib SHA-256 + per-user salt (no bcrypt dep)
JWT     : PyJWT (HS256)
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from pathlib import Path

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "users.db"
JWT_SECRET = os.environ.get("JWT_SECRET", "rhea-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days

# ---------------------------------------------------------------------------
# DB bootstrap — runs on import
# ---------------------------------------------------------------------------
def _get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    return db

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
with _get_db() as _db:
    _db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT UNIQUE NOT NULL,
            salt       TEXT NOT NULL,
            pw_hash    TEXT NOT NULL,
            plan       TEXT NOT NULL DEFAULT 'free',
            queries    INTEGER NOT NULL DEFAULT 0,
            created_at REAL NOT NULL
        )
    """)
    _db.commit()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hash_password(password: str, salt: str) -> str:
    return hmac.new(
        salt.encode(), password.encode(), hashlib.sha256
    ).hexdigest()

def _make_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_TTL_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
_bearer = HTTPBearer()

def _current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    payload = _decode_token(creds.credentials)
    with _get_db() as db:
        row = db.execute(
            "SELECT id, email, plan, queries, created_at FROM users WHERE id = ?",
            (int(payload["sub"]),)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(row)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AuthRequest(BaseModel):
    email: str
    password: str

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
auth_router = APIRouter(tags=["auth"])

@auth_router.post("/signup", status_code=201)
def signup(body: AuthRequest):
    salt = secrets.token_hex(16)
    pw_hash = _hash_password(body.password, salt)
    try:
        with _get_db() as db:
            cur = db.execute(
                "INSERT INTO users (email, salt, pw_hash, created_at) VALUES (?,?,?,?)",
                (body.email.lower(), salt, pw_hash, time.time()),
            )
            db.commit()
            user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Email already registered")
    return {"token": _make_token(user_id, body.email.lower())}

@auth_router.post("/login")
def login(body: AuthRequest):
    with _get_db() as db:
        row = db.execute(
            "SELECT id, email, salt, pw_hash FROM users WHERE email = ?",
            (body.email.lower(),)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    expected = _hash_password(body.password, row["salt"])
    if not hmac.compare_digest(expected, row["pw_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": _make_token(row["id"], row["email"])}

@auth_router.get("/profile")
def profile(user: dict = Depends(_current_user)):
    return {
        "email": user["email"],
        "created_at": user["created_at"],
        "plan": user["plan"],
        "usage": {"queries": user["queries"], "limit": 100},
    }

@auth_router.post("/logout")
def logout():
    return {"detail": "Logged out. Discard your token client-side."}

# ---------------------------------------------------------------------------
# Usage increment helper (called from tribunal middleware)
# ---------------------------------------------------------------------------
def increment_query_count(user_id: int) -> None:
    with _get_db() as db:
        db.execute("UPDATE users SET queries = queries + 1 WHERE id = ?", (user_id,))
        db.commit()
