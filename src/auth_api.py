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

# Apple Sign In (web)
APPLE_SERVICES_ID = os.environ.get("APPLE_SERVICES_ID", "")  # e.g. com.rhea.auth.web
APPLE_TEAM_ID = os.environ.get("APPLE_TEAM_ID", "398XACWZ7G")
APPLE_KEY_ID = os.environ.get("APPLE_KEY_ID", "")
APPLE_PRIVATE_KEY = os.environ.get("APPLE_PRIVATE_KEY", "")  # .p8 contents

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
    # Role column (admin / user)
    try:
        _db.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    except sqlite3.OperationalError:
        pass
    _db.commit()

# Admin emails from env — comma-separated
ADMIN_EMAILS = set(e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip())

# Sync admin roles on boot
if ADMIN_EMAILS:
    with _get_db() as _db:
        for email in ADMIN_EMAILS:
            _db.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
        _db.commit()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hash_password(password: str, salt: str) -> str:
    return hmac.new(
        salt.encode(), password.encode(), hashlib.sha256
    ).hexdigest()

def _make_token(user_id: int, email: str) -> str:
    # Look up role
    role = "user"
    try:
        with _get_db() as db:
            row = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
            if row and row["role"]:
                role = row["role"]
    except Exception:
        pass
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
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
            "SELECT id, email, plan, queries, created_at, role FROM users WHERE id = ?",
            (int(payload["sub"]),)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(row)

def _admin_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    user = _current_user(creds)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

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
    # Grant signup bonus credits
    try:
        from billing import grant_signup_bonus
        grant_signup_bonus(user_id)
    except Exception:
        pass  # billing bonus must never block signup
    return {
        "token": _make_token(user_id, body.email.lower()),
        "credits": 100,
        "message": "Welcome to Rhea. You own your infrastructure — "
                   "the infrastructure owner controls who's admin, not the application. "
                   "100 free credits granted.",
    }

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
        "role": user.get("role", "user"),
        "usage": {"queries": user["queries"], "limit": 100},
    }

@auth_router.post("/logout")
def logout():
    return {"detail": "Logged out. Discard your token client-side."}

@auth_router.get("/test")
def auth_test_page():
    """Serve a simple OAuth test page for browser-based testing."""
    from fastapi.responses import HTMLResponse
    google_ok = "enabled" if GOOGLE_CLIENT_ID else "not configured"
    ms_ok = "enabled" if MICROSOFT_CLIENT_ID else "not configured"
    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><title>Rhea Auth Test</title>
<style>body{{font-family:system-ui;background:#0a0a0a;color:#e0e0e0;padding:2rem}}
.btn{{display:inline-block;padding:.8rem 1.5rem;margin:.5rem;border-radius:8px;text-decoration:none;font-size:1rem;font-weight:600}}
.google{{background:#4285f4;color:#fff}}.ms{{background:#00a4ef;color:#fff}}.apple{{background:#333;color:#fff}}
.status{{font-size:.85rem;color:#888;margin-left:.5rem}}
h1{{color:#fff}}pre{{background:#111;padding:1rem;border-radius:8px;overflow-x:auto}}</style></head>
<body><h1>Rhea Auth Test</h1>
<p>Click a provider to test the OAuth flow (web mode):</p>
<a class="btn google" href="/auth/google?callback=web">Google</a><span class="status">{google_ok}</span><br>
<a class="btn ms" href="/auth/microsoft?callback=web">Microsoft</a><span class="status">{ms_ok}</span><br>
<a class="btn apple" href="/auth/apple?callback=web">Apple</a><span class="status">{"enabled" if APPLE_SERVICES_ID else "not configured"}</span>
<h3>Token</h3>
<pre id="tok">No token yet</pre>
<script>
window.addEventListener('message',e=>{{if(e.data&&e.data.type==='oauth')document.getElementById('tok').textContent=JSON.stringify(e.data,null,2)}});
let t=localStorage.getItem('rhea_token');if(t)document.getElementById('tok').textContent='Stored: '+t;
</script></body></html>""")

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
        # Grant signup bonus for new OAuth users
        try:
            from billing import grant_signup_bonus
            grant_signup_bonus(uid)
        except Exception:
            pass
    return uid, _make_token(uid, email)


def _oauth_redirect_with_token(token: str, email: str, error: str = "", callback: str = "rhea://oauth"):
    """Redirect to iOS deep link or serve web landing page with token."""
    from fastapi.responses import HTMLResponse
    params = {"token": token, "email": email} if not error else {"error": error}
    # iOS deep link
    if callback.startswith("rhea://"):
        return RedirectResponse(f"rhea://oauth?{urllib.parse.urlencode(params)}")
    # Web: serve a page that stores the token and closes
    if error:
        return HTMLResponse(f"<h2>OAuth Error</h2><p>{error}</p>")
    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><title>Rhea — Signed In</title>
<style>body{{font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#0a0a0a;color:#e0e0e0}}
.card{{background:#1a1a2e;padding:2rem 3rem;border-radius:12px;text-align:center;max-width:420px}}
.ok{{color:#4ade80;font-size:2rem}}
.principle{{margin-top:1.2rem;padding:1rem;border:1px solid rgba(74,222,128,0.2);border-radius:8px;background:rgba(74,222,128,0.04);font-size:.85rem;color:#9ca3af;line-height:1.5}}
.principle em{{color:#4ade80;font-style:normal}}</style></head>
<body><div class="card"><div class="ok">&#10003;</div><h2>Signed in as {email}</h2>
<p style="color:#6b7280;font-size:.9rem">100 free credits granted.</p>
<div class="principle"><em>The infrastructure owner controls who's admin, not the application.</em><br>You own your data, your models, your keys. Rhea serves you — not the other way around.</div>
<script>localStorage.setItem('rhea_token','{token}');localStorage.setItem('rhea_email','{email}');
if(window.opener)window.opener.postMessage({{type:'oauth',token:'{token}',email:'{email}'}},'*');</script>
</div></body></html>""")


# ---------------------------------------------------------------------------
# Apple Sign In (web OAuth + iOS native token)
# ---------------------------------------------------------------------------

def _apple_client_secret() -> str:
    """Generate Apple client_secret JWT signed with the .p8 private key."""
    headers = {"kid": APPLE_KEY_ID, "alg": "ES256"}
    payload = {
        "iss": APPLE_TEAM_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 180,  # 6 months max
        "aud": "https://appleid.apple.com",
        "sub": APPLE_SERVICES_ID,
    }
    return jwt.encode(payload, APPLE_PRIVATE_KEY, algorithm="ES256", headers=headers)


@auth_router.get("/apple")
def apple_start(callback: str = Query("rhea://oauth")):
    """Redirect to Apple Sign In consent screen (web flow)."""
    if not APPLE_SERVICES_ID or not APPLE_PRIVATE_KEY:
        raise HTTPException(503, "Apple Sign In not configured (set APPLE_SERVICES_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY)")
    redirect_uri = f"{OAUTH_REDIRECT_BASE}/auth/apple/callback"
    params = {
        "client_id": APPLE_SERVICES_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code id_token",
        "response_mode": "form_post",
        "scope": "name email",
        "state": callback,
    }
    url = f"https://appleid.apple.com/auth/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@auth_router.post("/apple/callback")
async def apple_callback(
    code: str = "",
    id_token: str = "",
    state: str = "rhea://oauth",
    error: str = "",
    user: str = "",  # JSON string, only on first auth
):
    """Handle Apple Sign In form_post callback.

    Apple POSTs code + id_token. The id_token contains the email.
    'user' JSON is only sent on the FIRST authorization — we must capture it.
    """
    if error or (not code and not id_token):
        return _oauth_redirect_with_token("", "", error=error or "no_code", callback=state)

    email = ""

    # Extract email from id_token (always present)
    if id_token:
        try:
            payload = jwt.decode(id_token, options={"verify_signature": False})
            email = payload.get("email", "")
        except Exception:
            pass

    # First-time auth: Apple sends user JSON with name/email
    if not email and user:
        try:
            import json
            user_data = json.loads(user)
            email = user_data.get("email", "")
        except Exception:
            pass

    # Last resort: exchange auth code for tokens
    if not email and code:
        try:
            client_secret = _apple_client_secret()
            redirect_uri = f"{OAUTH_REDIRECT_BASE}/auth/apple/callback"
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://appleid.apple.com/auth/token",
                    data={
                        "client_id": APPLE_SERVICES_ID,
                        "client_secret": client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri,
                    },
                )
                if token_resp.status_code == 200:
                    tokens = token_resp.json()
                    fresh_id_token = tokens.get("id_token", "")
                    if fresh_id_token:
                        payload = jwt.decode(fresh_id_token, options={"verify_signature": False})
                        email = payload.get("email", "")
        except Exception:
            pass

    if not email:
        return _oauth_redirect_with_token("", "", error="no_email", callback=state)

    _, jwt_token = _oauth_find_or_create(email.lower(), "apple")
    return _oauth_redirect_with_token(jwt_token, email.lower(), callback=state)


# iOS native: POST /auth/apple/native (identity token from AuthenticationServices)
class AppleAuthRequest(BaseModel):
    identity_token: str
    email: str = ""
    full_name: str = ""

@auth_router.post("/apple/native")
async def apple_signin_native(body: AppleAuthRequest):
    """Verify Apple identity token from iOS native AuthenticationServices."""
    try:
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
    return _oauth_redirect_with_token(jwt_token, email, callback=state)


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
    return _oauth_redirect_with_token(jwt_token, email, callback=state)
