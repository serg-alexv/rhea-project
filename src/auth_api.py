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
import logging
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
from validation import (
    ValidatedAuthRequest, validate_email, validate_password,
    validate_oauth_params, handle_validation_error
)

log = logging.getLogger("rhea.auth")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "users.db"

# Critical security: JWT_SECRET must be set in production
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable must be set. This is required for security.")

# Additional security: validate JWT secret complexity
if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET must be at least 32 characters long for security.")

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
@handle_validation_error
def signup(body: AuthRequest):
    # Validate inputs
    email = validate_email(body.email)
    password = validate_password(body.password)
    
    salt = secrets.token_hex(16)
    pw_hash = _hash_password(password, salt)
    try:
        with _get_db() as db:
            cur = db.execute(
                "INSERT INTO users (email, salt, pw_hash, created_at) VALUES (?,?,?,?)",
                (email, salt, pw_hash, time.time()),
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
        "token": _make_token(user_id, email),
        "credits": 100,
        "message": "Welcome to Rhea. You own your infrastructure — "
                   "the infrastructure owner controls who's admin, not the application. "
                   "100 free credits granted.",
    }

@auth_router.post("/login")
@handle_validation_error
def login(body: AuthRequest):
    # Validate inputs
    email = validate_email(body.email)
    password = validate_password(body.password)
    
    with _get_db() as db:
        row = db.execute(
            "SELECT id, email, salt, pw_hash FROM users WHERE email = ?",
            (email,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    expected = _hash_password(password, row["salt"])
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

@auth_router.get("/login-page")
def login_page():
    """Serve the full web login/signup page."""
    from fastapi.responses import HTMLResponse
    google_ok = bool(GOOGLE_CLIENT_ID)
    ms_ok = bool(MICROSOFT_CLIENT_ID)
    apple_ok = bool(APPLE_SERVICES_ID)
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign In &mdash; Rhea</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#000;--card:#111118;--border:rgba(255,255,255,.08);--text:#f5f5f7;--muted:#86868b;
  --accent:#0071e3;--green:#30d158;--radius:20px}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);
  display:flex;align-items:center;justify-content:center;min-height:100vh;padding:2rem;
  -webkit-font-smoothing:antialiased}}
a{{color:var(--accent);text-decoration:none}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:2.5rem;max-width:400px;width:100%}}
.card h1{{font-size:1.6rem;font-weight:700;text-align:center;margin-bottom:.3rem}}
.card .sub{{text-align:center;color:var(--muted);font-size:.82rem;margin-bottom:1.5rem}}
.oauth-btn{{display:flex;align-items:center;gap:.7rem;padding:.65rem 1rem;border-radius:12px;
  border:1px solid var(--border);background:rgba(255,255,255,.03);color:var(--text);
  font-size:.82rem;font-weight:500;text-decoration:none;transition:.2s;width:100%;margin-bottom:.5rem}}
.oauth-btn:hover{{background:rgba(255,255,255,.07);text-decoration:none}}
.oauth-btn.disabled{{opacity:.35;pointer-events:none}}
.sep{{display:flex;align-items:center;gap:.8rem;margin:1.2rem 0;color:var(--muted);font-size:.7rem}}
.sep div{{flex:1;height:1px;background:var(--border)}}
.form-row{{display:flex;gap:.4rem;margin-bottom:.5rem}}
.form-row input{{flex:1;padding:.55rem .8rem;border-radius:10px;border:1px solid var(--border);
  background:rgba(255,255,255,.04);color:var(--text);font-size:.82rem;font-family:inherit}}
.form-row input:focus{{outline:none;border-color:var(--accent)}}
.btn{{display:inline-flex;align-items:center;justify-content:center;padding:.55rem 1.2rem;
  border-radius:10px;font-size:.82rem;font-weight:500;cursor:pointer;border:none;
  background:var(--accent);color:#fff;transition:.2s}}
.btn:hover{{filter:brightness(1.1)}}
.msg{{margin-top:1rem;padding:.8rem;border-radius:10px;font-size:.78rem;text-align:center;display:none}}
.msg.ok{{display:block;background:rgba(48,209,88,.08);border:1px solid rgba(48,209,88,.2);color:var(--green)}}
.msg.err{{display:block;background:rgba(255,69,58,.08);border:1px solid rgba(255,69,58,.2);color:#ff453a}}
.footer{{text-align:center;margin-top:1.5rem;font-size:.7rem;color:#444}}
</style></head>
<body>
<div class="card">
  <h1>Sign in to Rhea</h1>
  <div class="sub">100 free credits on signup. All platforms.</div>
  <a class="oauth-btn{'' if google_ok else ' disabled'}" href="/auth/google?callback=web">
    <svg viewBox="0 0 24 24" width="18" height="18"><path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.96 10.96 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
    Continue with Google</a>
  <a class="oauth-btn{'' if ms_ok else ' disabled'}" href="/auth/microsoft?callback=web">
    <svg viewBox="0 0 24 24" width="16" height="16"><rect fill="#f25022" x="1" y="1" width="10" height="10"/><rect fill="#00a4ef" x="1" y="13" width="10" height="10"/><rect fill="#7fba00" x="13" y="1" width="10" height="10"/><rect fill="#ffb900" x="13" y="13" width="10" height="10"/></svg>
    Continue with Microsoft</a>
  <a class="oauth-btn{'' if apple_ok else ' disabled'}" href="/auth/apple?callback=web">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="#fff"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
    Continue with Apple</a>
  <div class="sep"><div></div>or<div></div></div>
  <div id="mode-switch" style="display:flex;gap:.5rem;margin-bottom:.8rem">
    <button class="btn" style="flex:1;font-size:.75rem" onclick="setMode('login')">Sign In</button>
    <button class="btn" style="flex:1;font-size:.75rem;background:transparent;border:1px solid var(--border);color:var(--text)"
      onclick="setMode('signup')">Sign Up</button>
  </div>
  <form onsubmit="return doAuth(event)">
    <div class="form-row"><input id="em" type="email" placeholder="you@example.com" required></div>
    <div class="form-row"><input id="pw" type="password" placeholder="Password" required minlength="6"></div>
    <button class="btn" style="width:100%" type="submit" id="submit-btn">Sign In</button>
  </form>
  <div id="msg" class="msg"></div>
  <div class="footer">&copy; 2026 timelabs npo &mdash; <a href="/">Back to Rhea</a></div>
</div>
<script>
let mode='login';
function setMode(m){{
  mode=m;
  document.getElementById('submit-btn').textContent=m==='login'?'Sign In':'Create Account';
  const btns=document.querySelectorAll('#mode-switch .btn');
  btns[0].style.background=m==='login'?'var(--accent)':'transparent';
  btns[0].style.border=m==='login'?'none':'1px solid var(--border)';
  btns[0].style.color=m==='login'?'#fff':'var(--text)';
  btns[1].style.background=m==='signup'?'var(--accent)':'transparent';
  btns[1].style.border=m==='signup'?'none':'1px solid var(--border)';
  btns[1].style.color=m==='signup'?'#fff':'var(--text)';
}}
async function doAuth(e){{
  e.preventDefault();
  const em=document.getElementById('em').value,pw=document.getElementById('pw').value;
  const msg=document.getElementById('msg');
  msg.className='msg';msg.style.display='none';
  try{{
    const ep=mode==='signup'?'/auth/signup':'/auth/login';
    const r=await fetch(ep,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:em,password:pw}})}});
    const d=await r.json();
    if(!r.ok)throw new Error(d.detail||'Request failed');
    const token=d.token||d.access_token;
    if(token){{
      localStorage.setItem('rhea_token',token);localStorage.setItem('rhea_email',em);
      msg.className='msg ok';msg.textContent=mode==='signup'?'Account created! 100 free credits.':'Signed in!';
      msg.style.display='block';
      if(window.opener)window.opener.postMessage({{type:'oauth',token,email:em}},'*');
      setTimeout(()=>window.location='/',1500);
    }}else{{
      msg.className='msg ok';msg.textContent=d.detail||'Success';msg.style.display='block';
    }}
  }}catch(err){{
    msg.className='msg err';msg.textContent=err.message;msg.style.display='block';
  }}
}}
</script>
</body></html>""")

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
<p id="countdown" style="margin-top:1rem;color:#6b7280;font-size:.8rem">Redirecting in <span id="sec">3</span>s...</p>
<a href="/" style="display:inline-block;margin-top:.8rem;padding:.6rem 1.5rem;background:#0071e3;color:#fff;border-radius:8px;font-size:.85rem;font-weight:500;text-decoration:none">Continue to Rhea</a>
<script>localStorage.setItem('rhea_token','{token}');localStorage.setItem('rhea_email','{email}');
if(window.opener)window.opener.postMessage({{type:'oauth',token:'{token}',email:'{email}'}},'*');
let s=3;const el=document.getElementById('sec');
const iv=setInterval(()=>{{s--;el.textContent=s;if(s<=0){{clearInterval(iv);window.location='/'}}}},1000);
</script>
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
@handle_validation_error
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
    # Validate OAuth parameters
    oauth_params = validate_oauth_params(code, state, error)
    
    if "error" in oauth_params:
        return _oauth_redirect_with_token("", "", error=oauth_params["error"], callback=state)

    email = ""

    # Extract email from id_token with proper signature verification
    if id_token:
        try:
            # Get Apple's public keys for verification
            import httpx
            async with httpx.AsyncClient() as client:
                keys_response = await client.get("https://appleid.apple.com/auth/keys")
                if keys_response.status_code != 200:
                    raise Exception("Failed to fetch Apple public keys")
                apple_keys = keys_response.json()
            
            # Verify the token signature
            try:
                from jose import jwk
                from jose.utils import base64url_decode
                import json
                
                # Decode token header to get key ID
                header = json.loads(base64url_decode(id_token.split('.')[0]))
                kid = header.get('kid')
                
                # Find matching key
                key = next((k for k in apple_keys['keys'] if k['kid'] == kid), None)
                if not key:
                    raise Exception("Key not found")
                
                # Convert to JWK and verify
                public_key = jwk.construct(key)
                payload = jwt.decode(
                    id_token, 
                    key=public_key, 
                    algorithms=["RS256"],
                    audience=APPLE_SERVICES_ID,
                    issuer="https://appleid.apple.com"
                )
                email = payload.get("email", "")
            except Exception as e:
                log.warning(f"Apple token verification failed: {e}")
                # Fallback to unsigned verification only for development
                if os.environ.get("ENVIRONMENT") == "development":
                    payload = jwt.decode(id_token, options={"verify_signature": False})
                    email = payload.get("email", "")
                else:
                    raise Exception("Invalid Apple token signature")
        except Exception as e:
            log.warning(f"Apple id_token processing failed: {e}")
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
        # For native tokens, we need to verify with Apple's public keys
        import httpx
        async with httpx.AsyncClient() as client:
            keys_response = await client.get("https://appleid.apple.com/auth/keys")
            if keys_response.status_code != 200:
                raise HTTPException(503, "Failed to fetch Apple public keys")
            apple_keys = keys_response.json()
        
        # Verify the token signature
        try:
            from jose import jwk
            from jose.utils import base64url_decode
            import json
            
            # Decode token header to get key ID
            header = json.loads(base64url_decode(body.identity_token.split('.')[0]))
            kid = header.get('kid')
            
            # Find matching key
            key = next((k for k in apple_keys['keys'] if k['kid'] == kid), None)
            if not key:
                raise HTTPException(400, "Invalid Apple token - key not found")
            
            # Convert to JWK and verify
            public_key = jwk.construct(key)
            payload = jwt.decode(
                body.identity_token, 
                key=public_key, 
                algorithms=["RS256"],
                audience=APPLE_SERVICES_ID,
                issuer="https://appleid.apple.com"
            )
            email = payload.get("email") or body.email
            if not email:
                raise HTTPException(400, "No email in Apple token or request")
        except Exception as e:
            log.warning(f"Apple native token verification failed: {e}")
            # Fallback to unsigned verification only for development
            if os.environ.get("ENVIRONMENT") == "development":
                payload = jwt.decode(body.identity_token, options={"verify_signature": False})
                email = payload.get("email") or body.email
                if not email:
                    raise HTTPException(400, "No email in Apple token or request")
            else:
                raise HTTPException(400, f"Invalid Apple token signature: {e}")
    except HTTPException:
        raise
    except Exception as e:
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
        id_token = tokens.get("id_token", "")

        # Verify the ID token signature and claims
        if id_token:
            try:
                # Get Google's certificates for verification
                certs_response = await client.get("https://www.googleapis.com/oauth2/v3/certs")
                if certs_response.status_code != 200:
                    raise Exception("Failed to fetch Google certificates")
                
                certs = certs_response.json()
                
                # Verify the token
                try:
                    from jose import jwk
                    from jose.utils import base64url_decode
                    import json
                    
                    # Decode token header to get key ID
                    header = json.loads(base64url_decode(id_token.split('.')[0]))
                    kid = header.get('kid')
                    
                    # Find matching certificate
                    cert = next((c for c in certs['keys'] if c['kid'] == kid), None)
                    if not cert:
                        raise Exception("Certificate not found")
                    
                    # Convert to JWK and verify
                    public_key = jwk.construct(cert)
                    payload = jwt.decode(
                        id_token,
                        key=public_key,
                        algorithms=["RS256"],
                        audience=GOOGLE_CLIENT_ID,
                        issuer="accounts.google.com"
                    )
                    
                    # Use verified email from ID token
                    verified_email = payload.get("email")
                    if verified_email:
                        _, jwt_token = _oauth_find_or_create(verified_email, "google")
                        return _oauth_redirect_with_token(jwt_token, verified_email, callback=state)
                    
                except Exception as e:
                    log.warning(f"Google ID token verification failed: {e}")
                    # Fallback to userinfo API if verification fails
                    pass
                    
            except ImportError:
                # If python-jose is not available, fall back to userinfo
                log.warning("python-jose not available, using userinfo API fallback")
                pass

        # Fetch user info as fallback
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
