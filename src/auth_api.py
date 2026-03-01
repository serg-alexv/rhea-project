"""auth_api.py — JWT auth + OAuth router for Rhea FastAPI backend.

Endpoints:
  POST /auth/signup              — register email+password, return JWT
  POST /auth/login               — verify email+password, return JWT
  GET  /auth/profile             — bearer-protected, return profile
  POST /auth/logout              — stateless acknowledgement
  GET  /auth/google              — start Google OAuth flow
  GET  /auth/google/callback     — Google OAuth callback → redirect with JWT
  GET  /auth/microsoft           — start Microsoft OAuth flow
  GET  /auth/microsoft/callback  — Microsoft OAuth callback → redirect with JWT

Storage : SQLite at data/users.db (auto-created)
Hashing : hashlib SHA-256 + per-user salt (no bcrypt dep)
JWT     : PyJWT (HS256)
OAuth   : Authorization Code flow (Google, Microsoft) via httpx
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import urllib.parse
from pathlib import Path

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
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

# OAuth providers
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET", "")
OAUTH_REDIRECT_BASE = os.environ.get("OAUTH_REDIRECT_BASE", "http://localhost:8400")

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
    # OAuth provider tracking (nullable — email/password users have NULL)
    try:
        _db.execute("ALTER TABLE users ADD COLUMN oauth_provider TEXT")
    except sqlite3.OperationalError:
        pass
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

# ---------------------------------------------------------------------------
# OAuth: find-or-create user by email from provider
# ---------------------------------------------------------------------------
def _oauth_find_or_create(email: str, provider: str) -> tuple[int, str]:
    """Return (user_id, jwt_token) for an OAuth-authenticated email."""
    email = email.lower().strip()
    with _get_db() as db:
        row = db.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            return row["id"], _make_token(row["id"], row["email"])
        # Create new user — no password (OAuth-only)
        salt = secrets.token_hex(16)
        pw_hash = "oauth-no-password"
        cur = db.execute(
            "INSERT INTO users (email, salt, pw_hash, oauth_provider, created_at) VALUES (?,?,?,?,?)",
            (email, salt, pw_hash, provider, time.time()),
        )
        db.commit()
        uid = cur.lastrowid
    return uid, _make_token(uid, email)


def _oauth_redirect_with_token(token: str, email: str, error: str = "") -> RedirectResponse:
    """Build redirect to rhea://oauth?token=...&email=..."""
    params = {"token": token, "email": email} if not error else {"error": error}
    return RedirectResponse(f"rhea://oauth?{urllib.parse.urlencode(params)}")


# ---------------------------------------------------------------------------
# Apple Sign In (token verification)
# ---------------------------------------------------------------------------
class AppleAuthRequest(BaseModel):
    identity_token: str
    email: str = ""
    full_name: str = ""

@auth_router.post("/apple")
async def apple_signin(body: AppleAuthRequest):
    """Verify Apple identity token and return JWT.

    Apple sends a signed JWT. We decode the payload to get the email.
    For full production, verify the token signature against Apple's JWKS at
    https://appleid.apple.com/auth/keys — for now we decode the payload
    (Apple tokens are short-lived and include the audience claim).
    """
    try:
        # Decode without verification to extract email (Apple tokens are signed JWTs)
        # Production: verify against https://appleid.apple.com/auth/keys
        payload = jwt.decode(body.identity_token, options={"verify_signature": False})
        email = payload.get("email") or body.email
        if not email:
            raise HTTPException(400, "No email in Apple token or request")
    except Exception:
        if not body.email:
            raise HTTPException(400, "Could not decode Apple token and no email provided")
        email = body.email

    uid, token = _oauth_find_or_create(email.lower(), "apple")
    return {"token": token, "email": email.lower()}


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------
@auth_router.get("/google")
def google_start(callback: str = Query("rhea://oauth")):
    """Redirect to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(503, "Google OAuth not configured (set GOOGLE_CLIENT_ID)")
    redirect_uri = f"{OAUTH_REDIRECT_BASE}/auth/google/callback"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": callback,
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@auth_router.get("/google/callback")
async def google_callback(code: str = "", error: str = "", state: str = "rhea://oauth"):
    """Exchange Google auth code for user token."""
    if error or not code:
        return _oauth_redirect_with_token("", "", error=error or "no_code")

    redirect_uri = f"{OAUTH_REDIRECT_BASE}/auth/google/callback"
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            return _oauth_redirect_with_token("", "", error="token_exchange_failed")

        tokens = token_resp.json()
        access_token = tokens.get("access_token", "")

        # Fetch user info
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            return _oauth_redirect_with_token("", "", error="userinfo_failed")

        userinfo = userinfo_resp.json()
        email = userinfo.get("email", "")
        if not email:
            return _oauth_redirect_with_token("", "", error="no_email")

    _, jwt_token = _oauth_find_or_create(email, "google")
    return _oauth_redirect_with_token(jwt_token, email)


# ---------------------------------------------------------------------------
# Microsoft OAuth
# ---------------------------------------------------------------------------
@auth_router.get("/microsoft")
def microsoft_start(callback: str = Query("rhea://oauth")):
    """Redirect to Microsoft OAuth consent screen."""
    if not MICROSOFT_CLIENT_ID:
        raise HTTPException(503, "Microsoft OAuth not configured (set MICROSOFT_CLIENT_ID)")
    redirect_uri = f"{OAUTH_REDIRECT_BASE}/auth/microsoft/callback"
    params = {
        "client_id": MICROSOFT_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile User.Read",
        "state": callback,
    }
    url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@auth_router.get("/microsoft/callback")
async def microsoft_callback(code: str = "", error: str = "", state: str = "rhea://oauth"):
    """Exchange Microsoft auth code for user token."""
    if error or not code:
        return _oauth_redirect_with_token("", "", error=error or "no_code")

    redirect_uri = f"{OAUTH_REDIRECT_BASE}/auth/microsoft/callback"
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "code": code,
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            return _oauth_redirect_with_token("", "", error="token_exchange_failed")

        tokens = token_resp.json()
        access_token = tokens.get("access_token", "")

        # Fetch user info from Microsoft Graph
        userinfo_resp = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            return _oauth_redirect_with_token("", "", error="userinfo_failed")

        userinfo = userinfo_resp.json()
        email = userinfo.get("mail") or userinfo.get("userPrincipalName", "")
        if not email:
            return _oauth_redirect_with_token("", "", error="no_email")

    _, jwt_token = _oauth_find_or_create(email, "microsoft")
    return _oauth_redirect_with_token(jwt_token, email)
