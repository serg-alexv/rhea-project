"""billing.py — Stripe + BTC billing for Rhea platform.

Plans:
  free       — 100 queries/month, single model, no API keys
  pro        — 10K queries/month, multi-model consensus, 3 API keys   ($29/mo)
  enterprise — unlimited, custom models, webhooks, white-label         ($99/mo)

Stripe: subscription billing via Checkout Sessions + webhooks.
BTC:    BTCPay Server webhook integration (invoice.settled → upgrade plan).

Storage: SQLite users.db (extends auth_api tables).
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

log = logging.getLogger("rhea.billing")

def _get_current_user():
    """Lazy import to avoid circular dependency with auth_api."""
    from auth_api import _current_user
    return _current_user

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "users.db"

# Critical security: detect missing secrets without taking the whole app down.
def _missing_config() -> list[str]:
    """Return the list of enabled billing secrets that are currently missing."""
    missing_secrets = []
    
    # Check Stripe configuration if enabled
    if os.environ.get("STRIPE_ENABLED", "true").lower() == "true":
        if not os.environ.get("STRIPE_SECRET_KEY"):
            missing_secrets.append("STRIPE_SECRET_KEY")
        if not os.environ.get("STRIPE_WEBHOOK_SECRET"):
            missing_secrets.append("STRIPE_WEBHOOK_SECRET")
    
    # Check BTCPay configuration if enabled
    if os.environ.get("BTCPAY_ENABLED", "false").lower() == "true":
        if not os.environ.get("BTCPAY_WEBHOOK_SECRET"):
            missing_secrets.append("BTCPAY_WEBHOOK_SECRET")
    
    # Check OAuth providers if enabled
    if os.environ.get("GOOGLE_OAUTH_ENABLED", "false").lower() == "true":
        if not os.environ.get("GOOGLE_CLIENT_ID"):
            missing_secrets.append("GOOGLE_CLIENT_ID")
        if not os.environ.get("GOOGLE_CLIENT_SECRET"):
            missing_secrets.append("GOOGLE_CLIENT_SECRET")
    
    if os.environ.get("MICROSOFT_OAUTH_ENABLED", "false").lower() == "true":
        if not os.environ.get("MICROSOFT_CLIENT_ID"):
            missing_secrets.append("MICROSOFT_CLIENT_ID")
        if not os.environ.get("MICROSOFT_CLIENT_SECRET"):
            missing_secrets.append("MICROSOFT_CLIENT_SECRET")
    
    return missing_secrets

_MISSING_CONFIG = _missing_config()
if _MISSING_CONFIG:
    log.warning(
        "Billing providers disabled until required secrets are configured: %s",
        ", ".join(_MISSING_CONFIG),
    )

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
BTCPAY_WEBHOOK_SECRET = os.environ.get("BTCPAY_WEBHOOK_SECRET", "")

PLANS = {
    "free":       {"queries_month": 100,   "models": 1, "api_keys": 0,  "price_usd": 0},
    "pro":        {"queries_month": 10000, "models": 5, "api_keys": 3,  "price_usd": 29},
    "enterprise": {"queries_month": -1,    "models": -1, "api_keys": 10, "price_usd": 99},
}

# ---------------------------------------------------------------------------
# DB extensions
# ---------------------------------------------------------------------------
def _get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    return db

def _ensure_billing_tables():
    with _get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key        TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL,
                label      TEXT DEFAULT '',
                created_at REAL NOT NULL,
                revoked    INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_apikeys_user ON api_keys(user_id);

            CREATE TABLE IF NOT EXISTS billing_events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                event_type TEXT NOT NULL,
                provider   TEXT NOT NULL,
                reference  TEXT,
                amount_usd REAL,
                plan       TEXT,
                ts         REAL NOT NULL,
                raw        TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_billing_user ON billing_events(user_id);

            CREATE TABLE IF NOT EXISTS usage_monthly (
                user_id    INTEGER NOT NULL,
                month      TEXT NOT NULL,
                queries    INTEGER DEFAULT 0,
                tokens_in  INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                cost_usd   REAL DEFAULT 0.0,
                PRIMARY KEY (user_id, month)
            );

            CREATE TABLE IF NOT EXISTS resellers (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL UNIQUE,
                company_name TEXT,
                domain       TEXT,
                markup_pct   REAL DEFAULT 20.0,
                active       INTEGER DEFAULT 1,
                created_at   REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_resellers_user ON resellers(user_id);

            CREATE TABLE IF NOT EXISTS reseller_users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                reseller_id INTEGER NOT NULL,
                email       TEXT UNIQUE,
                plan        TEXT DEFAULT 'free',
                api_key     TEXT,
                created_at  REAL,
                FOREIGN KEY (reseller_id) REFERENCES resellers(id)
            );
            CREATE INDEX IF NOT EXISTS idx_reseller_users_reseller ON reseller_users(reseller_id);
            CREATE INDEX IF NOT EXISTS idx_reseller_users_key ON reseller_users(api_key);
        """)
        db.executescript("""
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                delta INTEGER NOT NULL,
                balance INTEGER NOT NULL,
                reason TEXT NOT NULL,
                ref_id TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_ledger_user ON ledger(user_id);
            CREATE INDEX IF NOT EXISTS idx_ledger_created ON ledger(created_at);
        """)
        # Add plan_expires_at to users if missing
        try:
            db.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            db.execute("ALTER TABLE users ADD COLUMN plan_expires_at REAL")
        except sqlite3.OperationalError:
            pass
        # Credits column on users
        try:
            db.execute("ALTER TABLE users ADD COLUMN credits INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        # Patron keys for crypto auto-accounts
        db.executescript("""
            CREATE TABLE IF NOT EXISTS patron_keys (
                key        TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL,
                tx_hash    TEXT,
                amount_usd REAL DEFAULT 0,
                redeemed   INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_patron_user ON patron_keys(user_id);
        """)
        db.commit()

_ensure_billing_tables()

# ---------------------------------------------------------------------------
# Credit Operations
# ---------------------------------------------------------------------------

# Cost per operation type (in credits)
CREDIT_COSTS = {
    "tribunal": 3,      # 3-model consensus
    "ice": 10,           # iterative deep consensus
    "sceptic": 5,        # sceptic mode
    "dialog": 1,         # simple chat
    "workflow": 2,       # workflow execution step
}

SIGNUP_BONUS_CREDITS = 100  # free credits on signup


TIER_MULTIPLIERS = {"cheap": 1, "mid": 2, "premium": 4, "max": 8}


def compute_query_cost(operation: str, k: int = 3, tier: str = "cheap") -> int:
    """Dynamic credit cost: base * tier_multiplier + (k - 2) for multi-model ops."""
    base = CREDIT_COSTS.get(operation, 1)
    tier_mult = TIER_MULTIPLIERS.get(tier, 1)
    k_extra = max(0, k - 2) if operation in ("tribunal", "ice") else 0
    return max(1, base * tier_mult + k_extra)


def get_balance(user_id: int) -> int:
    """Get current credit balance for a user."""
    with _get_db() as db:
        row = db.execute("SELECT credits FROM users WHERE id = ?", (user_id,)).fetchone()
    return row["credits"] if row else 0


def grant_credits(user_id: int, amount: int, reason: str, ref_id: str = "") -> int:
    """Add credits to a user's balance. Returns new balance."""
    if amount <= 0:
        raise ValueError("Grant amount must be positive")
    with _get_db() as db:
        db.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amount, user_id))
        row = db.execute("SELECT credits FROM users WHERE id = ?", (user_id,)).fetchone()
        new_balance = row["credits"]
        db.execute(
            "INSERT INTO ledger (user_id, delta, balance, reason, ref_id, created_at) VALUES (?,?,?,?,?,?)",
            (user_id, amount, new_balance, reason, ref_id, time.time())
        )
        db.commit()
    return new_balance


def deduct_credits(user_id: int, operation: str, ref_id: str = "") -> int:
    """Deduct credits for an operation. Returns new balance. Raises HTTPException if insufficient."""
    cost = CREDIT_COSTS.get(operation, 1)
    return deduct_credits_dynamic(user_id, cost, operation, ref_id)


def deduct_credits_dynamic(user_id: int, cost: int, operation: str, ref_id: str = "") -> int:
    """Deduct a pre-computed credit amount. Use with compute_query_cost() for dynamic pricing.
    
    Uses atomic UPDATE to prevent race conditions and ensure consistency.
    """
    if cost <= 0:
        raise ValueError("Cost must be positive")
    
    with _get_db() as db:
        # Atomic operation: check and deduct in single statement
        cursor = db.execute(
            "UPDATE users SET credits = credits - ? WHERE id = ? AND credits >= ?",
            (cost, user_id, cost)
        )
        
        if cursor.rowcount == 0:
            # Either user doesn't exist or insufficient credits
            row = db.execute("SELECT credits FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise HTTPException(404, "User not found")
            current = row["credits"]
            raise HTTPException(
                402,
                f"Insufficient credits. Need {cost} for {operation}, have {current}. "
                f"Buy credits at /billing/credits/buy"
            )
        
        # Get the new balance
        row = db.execute("SELECT credits FROM users WHERE id = ?", (user_id,)).fetchone()
        new_balance = row["credits"]
        
        # Record the transaction
        db.execute(
            "INSERT INTO ledger (user_id, delta, balance, reason, ref_id, created_at) VALUES (?,?,?,?,?,?)",
            (user_id, -cost, new_balance, operation, ref_id, time.time())
        )
        db.commit()
        
    # Mirror to CockroachDB for persistent cloud billing
    try:
        import crdb_store
        crdb_store.log_billing(
            user_id=str(user_id),
            event_type=operation,
            amount_usd=cost * 0.001,  # 1 credit ≈ $0.001
            tokens_used=cost,
            metadata={"ref_id": ref_id, "balance_after": new_balance},
        )
    except Exception:
        pass  # CRDB logging must never block billing
    
    return new_balance


def grant_signup_bonus(user_id: int) -> int:
    """Grant signup bonus credits. Idempotent — skips if already granted."""
    with _get_db() as db:
        existing = db.execute(
            "SELECT id FROM ledger WHERE user_id = ? AND reason = 'signup_bonus'", (user_id,)
        ).fetchone()
    if existing:
        return get_balance(user_id)
    return grant_credits(user_id, SIGNUP_BONUS_CREDITS, "signup_bonus", f"signup_{user_id}")


def get_ledger(user_id: int, limit: int = 50) -> list[dict]:
    """Get recent ledger entries for a user."""
    with _get_db() as db:
        rows = db.execute(
            "SELECT delta, balance, reason, ref_id, created_at FROM ledger WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]

# ---------------------------------------------------------------------------
# API Key Management
# ---------------------------------------------------------------------------
def generate_api_key(user_id: int, label: str = "") -> str:
    """Generate a new API key for a user."""
    plan = _user_plan(user_id)
    max_keys = PLANS.get(plan, PLANS["free"])["api_keys"]
    if max_keys == 0:
        raise HTTPException(400, "Free plan does not include API keys. Upgrade to Pro.")

    with _get_db() as db:
        existing = db.execute(
            "SELECT COUNT(*) as c FROM api_keys WHERE user_id = ? AND revoked = 0",
            (user_id,)
        ).fetchone()["c"]
        if max_keys > 0 and existing >= max_keys:
            raise HTTPException(400, f"Key limit reached ({max_keys}). Revoke an existing key first.")

    key = f"rk_{secrets.token_hex(24)}"
    with _get_db() as db:
        db.execute(
            "INSERT INTO api_keys (key, user_id, label, created_at) VALUES (?, ?, ?, ?)",
            (key, user_id, label, time.time())
        )
        db.commit()
    return key

def validate_api_key(key: str) -> Optional[dict]:
    """Validate an API key and return user info.

    Handles two key prefixes:
      rk_  — regular customer key (api_keys table, joined to users)
      rr_  — reseller sub-user key (reseller_users table, joined to resellers)
    """
    if key.startswith("rr_"):
        with _get_db() as db:
            row = db.execute("""
                SELECT ru.id AS user_id, ru.email, ru.plan,
                       r.id AS reseller_id, r.user_id AS reseller_owner_id,
                       r.company_name, r.markup_pct
                FROM reseller_users ru
                JOIN resellers r ON ru.reseller_id = r.id
                WHERE ru.api_key = ? AND r.active = 1
            """, (key,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["is_reseller_user"] = True
        return result

    # Default path: rk_ or legacy keys stored in api_keys
    with _get_db() as db:
        row = db.execute("""
            SELECT ak.user_id, u.email, u.plan
            FROM api_keys ak JOIN users u ON ak.user_id = u.id
            WHERE ak.key = ? AND ak.revoked = 0
        """, (key,)).fetchone()
    return dict(row) if row else None

def _user_plan(user_id: int) -> str:
    with _get_db() as db:
        row = db.execute("SELECT plan FROM users WHERE id = ?", (user_id,)).fetchone()
    return row["plan"] if row else "free"

# ---------------------------------------------------------------------------
# Usage Metering
# ---------------------------------------------------------------------------
def record_usage(user_id: int, tokens_in: int = 0, tokens_out: int = 0, cost: float = 0.0):
    """Record API usage for billing."""
    month = time.strftime("%Y-%m")
    with _get_db() as db:
        db.execute("""
            INSERT INTO usage_monthly (user_id, month, queries, tokens_in, tokens_out, cost_usd)
            VALUES (?, ?, 1, ?, ?, ?)
            ON CONFLICT(user_id, month) DO UPDATE SET
                queries = queries + 1,
                tokens_in = tokens_in + excluded.tokens_in,
                tokens_out = tokens_out + excluded.tokens_out,
                cost_usd = cost_usd + excluded.cost_usd
        """, (user_id, month, tokens_in, tokens_out, cost))
        db.commit()

def check_quota(user_id: int) -> bool:
    """Check if user is within their plan quota."""
    plan = _user_plan(user_id)
    limit = PLANS.get(plan, PLANS["free"])["queries_month"]
    if limit == -1:
        return True
    month = time.strftime("%Y-%m")
    with _get_db() as db:
        row = db.execute(
            "SELECT queries FROM usage_monthly WHERE user_id = ? AND month = ?",
            (user_id, month)
        ).fetchone()
    used = row["queries"] if row else 0
    return used < limit

def get_usage(user_id: int) -> dict:
    """Get current month usage stats."""
    plan = _user_plan(user_id)
    plan_info = PLANS.get(plan, PLANS["free"])
    month = time.strftime("%Y-%m")
    with _get_db() as db:
        row = db.execute(
            "SELECT queries, tokens_in, tokens_out, cost_usd FROM usage_monthly WHERE user_id = ? AND month = ?",
            (user_id, month)
        ).fetchone()
    usage = dict(row) if row else {"queries": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}
    usage["limit"] = plan_info["queries_month"]
    usage["plan"] = plan
    usage["month"] = month
    return usage

# ---------------------------------------------------------------------------
# Plan upgrades
# ---------------------------------------------------------------------------
def upgrade_plan(user_id: int, plan: str, provider: str, reference: str, amount: float):
    """Upgrade a user's plan after payment confirmation."""
    if plan not in PLANS:
        return
    with _get_db() as db:
        db.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))
        db.execute("""
            INSERT INTO billing_events (user_id, event_type, provider, reference, amount_usd, plan, ts)
            VALUES (?, 'upgrade', ?, ?, ?, ?, ?)
        """, (user_id, provider, reference, amount, plan, time.time()))
        db.commit()

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
billing_router = APIRouter(prefix="/billing", tags=["billing"])

class CreateKeyRequest(BaseModel):
    label: str = ""

class CheckoutRequest(BaseModel):
    plan: str
    success_url: str = ""
    cancel_url: str = ""

class ResellerRegisterRequest(BaseModel):
    company_name: str
    domain: str = ""
    markup_pct: float = 20.0

class ResellerCreateUserRequest(BaseModel):
    email: str
    plan: str = "free"

@billing_router.get("/plans")
def list_plans():
    """List available plans and pricing."""
    return {"plans": PLANS}

@billing_router.get("/usage")
def usage(user: dict = Depends(_get_current_user())):
    return get_usage(user["id"])

@billing_router.post("/keys")
def create_key(body: CreateKeyRequest, user: dict = Depends(_get_current_user())):
    key = generate_api_key(user["id"], body.label)
    return {"key": key, "label": body.label}

@billing_router.get("/keys")
def list_keys(user: dict = Depends(_get_current_user())):
    with _get_db() as db:
        rows = db.execute(
            "SELECT key, label, created_at, revoked FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
            (user["id"],)
        ).fetchall()
    return {"keys": [
        {"key": r["key"][:8] + "..." + r["key"][-4:], "label": r["label"],
         "created_at": r["created_at"], "active": not r["revoked"]}
        for r in rows
    ]}

@billing_router.delete("/keys/{key_prefix}")
def revoke_key(key_prefix: str, user: dict = Depends(_get_current_user())):
    with _get_db() as db:
        db.execute(
            "UPDATE api_keys SET revoked = 1 WHERE user_id = ? AND key LIKE ?",
            (user["id"], key_prefix + "%")
        )
        db.commit()
    return {"revoked": True}

@billing_router.post("/checkout")
def create_checkout(body: CheckoutRequest):
    """Create a Stripe Checkout Session for plan upgrade."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Stripe not configured. Contact admin.")
    if body.plan not in PLANS or body.plan == "free":
        raise HTTPException(400, f"Invalid plan: {body.plan}")

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        price_map = {
            "pro": os.environ.get("STRIPE_PRO_PRICE_ID", ""),
            "enterprise": os.environ.get("STRIPE_ENTERPRISE_PRICE_ID", ""),
        }
        price_id = price_map.get(body.plan)
        if not price_id:
            raise HTTPException(503, f"Stripe price not configured for {body.plan}")

        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=body.success_url or "https://rhea-tribunal.fly.dev/billing/success",
            cancel_url=body.cancel_url or "https://rhea-tribunal.fly.dev/billing/cancel",
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except ImportError:
        raise HTTPException(503, "Stripe SDK not installed")
    except Exception as e:
        raise HTTPException(500, str(e))

@billing_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (subscription created/updated/cancelled)."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "Stripe webhooks not configured")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(400, f"Webhook verification failed: {e}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email", "")
        # Find user by email and upgrade
        with _get_db() as db:
            row = db.execute("SELECT id FROM users WHERE email = ?", (customer_email,)).fetchone()
            if row:
                # Determine plan from price
                plan = "pro"  # default; parse from line_items for accuracy
                upgrade_plan(row["id"], plan, "stripe", session.get("id", ""), 29.0)

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        customer_email = sub.get("customer_email", "")
        with _get_db() as db:
            db.execute("UPDATE users SET plan = 'free' WHERE email = ?", (customer_email,))
            db.commit()

    return {"received": True}

def _patron_key_from_tx(tx_hash: str) -> str:
    """Derive a deterministic patron key from a transaction hash."""
    digest = hashlib.sha256(f"rhea-patron:{tx_hash}".encode()).hexdigest()[:16]
    return f"rp_{digest}"


@billing_router.post("/webhook/btcpay")
async def btcpay_webhook(request: Request):
    """Handle BTCPay Server invoice.settled webhook.

    Flow:
    1. Verify HMAC signature
    2. If buyer email matches existing user → credit account
    3. If no email / unknown email → auto-create patron account, generate patron key
    4. 95% → user credits, 5% → impact fund (carbon, science, shelter)
    """
    payload = await request.body()

    # Verify HMAC signature
    if BTCPAY_WEBHOOK_SECRET:
        sig = request.headers.get("btcpay-sig", "")
        expected = "sha256=" + hmac.new(
            BTCPAY_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(400, "Invalid BTCPay signature")

    data = json.loads(payload)
    event_type = data.get("type", "")

    if event_type == "InvoiceSettled":
        invoice = data.get("invoiceId", "")
        metadata = data.get("metadata", {})
        user_email = metadata.get("buyerEmail", "").strip().lower()
        amount_usd = float(metadata.get("amount", 0))
        tx_hash = metadata.get("txHash", invoice)

        # 95% to user credits (1 USD ≈ 100 credits)
        credit_amount = int(amount_usd * 95)

        with _get_db() as db:
            user_id = None
            patron_key = None

            # Try to find existing user
            if user_email:
                row = db.execute("SELECT id FROM users WHERE email = ?", (user_email,)).fetchone()
                if row:
                    user_id = row["id"]

            # Auto-create patron account if no match
            if user_id is None:
                patron_key = _patron_key_from_tx(tx_hash)
                patron_email = f"patron_{patron_key}@rhea.local"
                from auth_api import _hash_password
                salt = secrets.token_hex(16)
                pw_hash = _hash_password(patron_key, salt)  # patron key IS the password
                try:
                    cur = db.execute(
                        "INSERT INTO users (email, salt, pw_hash, created_at) VALUES (?,?,?,?)",
                        (patron_email, salt, pw_hash, time.time()),
                    )
                    db.commit()
                    user_id = cur.lastrowid
                except sqlite3.IntegrityError:
                    # Patron already exists (duplicate webhook)
                    row = db.execute("SELECT id FROM users WHERE email = ?", (patron_email,)).fetchone()
                    if row:
                        user_id = row["id"]

            if user_id and credit_amount > 0:
                grant_credits(user_id, credit_amount, "btcpay_payment", invoice)

            # Record patron key for redemption
            if patron_key:
                db.execute("""
                    INSERT OR IGNORE INTO patron_keys (key, user_id, tx_hash, amount_usd, created_at)
                    VALUES (?,?,?,?,?)
                """, (patron_key, user_id, tx_hash, amount_usd, time.time()))
                db.commit()

    return {"received": True}


@billing_router.post("/redeem")
def redeem_patron_key(body: dict):
    """Redeem a patron key (rp_...) to link credits to your real account.

    Body: {"patron_key": "rp_...", "email": "you@example.com", "password": "..."}
    Transfers all credits from the patron account to the target account.
    """
    patron_key = body.get("patron_key", "").strip()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not patron_key.startswith("rp_") or not email or not password:
        raise HTTPException(400, "patron_key, email, and password required")

    patron_email = f"patron_{patron_key}@rhea.local"

    with _get_db() as db:
        # Find patron account
        patron = db.execute("SELECT id, credits FROM users WHERE email = ?", (patron_email,)).fetchone()
        if not patron:
            raise HTTPException(404, "Patron key not found or already redeemed")

        # Find or create target account
        target = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if target:
            target_id = target["id"]
        else:
            # Auto-signup
            from auth_api import _hash_password, _make_token
            salt = secrets.token_hex(16)
            pw_hash = _hash_password(password, salt)
            cur = db.execute(
                "INSERT INTO users (email, salt, pw_hash, created_at) VALUES (?,?,?,?)",
                (email, salt, pw_hash, time.time()),
            )
            db.commit()
            target_id = cur.lastrowid

        # Transfer credits
        patron_credits = patron["credits"] or 0
        if patron_credits > 0:
            grant_credits(target_id, patron_credits, "patron_redeem", patron_key)
            db.execute("UPDATE users SET credits = 0 WHERE id = ?", (patron["id"],))
            db.commit()

        from auth_api import _make_token
        return {
            "token": _make_token(target_id, email),
            "credits_transferred": patron_credits,
            "message": f"{patron_credits} credits transferred to {email}",
        }

# ---------------------------------------------------------------------------
# Reseller Endpoints
# ---------------------------------------------------------------------------

def _get_reseller(user_id: int) -> Optional[dict]:
    """Return the reseller row for user_id, or None if not a reseller."""
    with _get_db() as db:
        row = db.execute(
            "SELECT * FROM resellers WHERE user_id = ? AND active = 1",
            (user_id,)
        ).fetchone()
    return dict(row) if row else None


@billing_router.post("/reseller/register")
def reseller_register(
    body: ResellerRegisterRequest,
    user: dict = Depends(_get_current_user()),
):
    """Register the authenticated enterprise user as a reseller.

    Requires enterprise plan. Idempotent: calling twice updates the record.
    """
    plan = _user_plan(user["id"])
    if plan != "enterprise":
        raise HTTPException(403, "Reseller registration requires an enterprise plan.")

    if not body.company_name.strip():
        raise HTTPException(400, "company_name is required.")
    if not (0.0 <= body.markup_pct <= 500.0):
        raise HTTPException(400, "markup_pct must be between 0 and 500.")

    now = time.time()
    with _get_db() as db:
        existing = db.execute(
            "SELECT id FROM resellers WHERE user_id = ?", (user["id"],)
        ).fetchone()

        if existing:
            db.execute(
                """UPDATE resellers
                   SET company_name = ?, domain = ?, markup_pct = ?, active = 1
                   WHERE user_id = ?""",
                (body.company_name.strip(), body.domain.strip(), body.markup_pct, user["id"]),
            )
        else:
            db.execute(
                """INSERT INTO resellers (user_id, company_name, domain, markup_pct, active, created_at)
                   VALUES (?, ?, ?, ?, 1, ?)""",
                (user["id"], body.company_name.strip(), body.domain.strip(), body.markup_pct, now),
            )
        db.commit()

        reseller = db.execute(
            "SELECT * FROM resellers WHERE user_id = ?", (user["id"],)
        ).fetchone()

    return {
        "reseller_id": reseller["id"],
        "company_name": reseller["company_name"],
        "domain": reseller["domain"],
        "markup_pct": reseller["markup_pct"],
        "active": bool(reseller["active"]),
        "created_at": reseller["created_at"],
    }


@billing_router.get("/reseller/dashboard")
def reseller_dashboard(user: dict = Depends(_get_current_user())):
    """Return reseller overview: sub-user count, aggregated usage, revenue share."""
    reseller = _get_reseller(user["id"])
    if not reseller:
        raise HTTPException(404, "No active reseller account found for this user.")

    month = time.strftime("%Y-%m")
    with _get_db() as db:
        sub_users = db.execute(
            "SELECT id, email, plan, api_key, created_at FROM reseller_users WHERE reseller_id = ?",
            (reseller["id"],),
        ).fetchall()

        # Aggregate usage for all sub-users via their api_keys
        sub_user_ids = [row["id"] for row in sub_users]
        if sub_user_ids:
            placeholders = ",".join("?" * len(sub_user_ids))
            # usage_monthly is keyed by user_id; reseller_users have their own id
            # We stored usage under reseller_user.id in record_usage calls
            agg = db.execute(
                f"""SELECT
                        COALESCE(SUM(queries), 0)    AS total_queries,
                        COALESCE(SUM(tokens_in), 0)  AS total_tokens_in,
                        COALESCE(SUM(tokens_out), 0) AS total_tokens_out,
                        COALESCE(SUM(cost_usd), 0.0) AS total_cost_usd
                    FROM usage_monthly
                    WHERE user_id IN ({placeholders}) AND month = ?""",
                (*sub_user_ids, month),
            ).fetchone()
        else:
            agg = {"total_queries": 0, "total_tokens_in": 0, "total_tokens_out": 0, "total_cost_usd": 0.0}

    total_cost = float(agg["total_cost_usd"]) if agg["total_cost_usd"] else 0.0
    markup = reseller["markup_pct"] / 100.0
    revenue_share = round(total_cost * markup, 4)

    return {
        "reseller_id": reseller["id"],
        "company_name": reseller["company_name"],
        "domain": reseller["domain"],
        "markup_pct": reseller["markup_pct"],
        "month": month,
        "sub_user_count": len(sub_users),
        "sub_users": [
            {
                "id": u["id"],
                "email": u["email"],
                "plan": u["plan"],
                "api_key_hint": (u["api_key"][:8] + "..." + u["api_key"][-4:]) if u["api_key"] else None,
                "created_at": u["created_at"],
            }
            for u in sub_users
        ],
        "usage": {
            "queries": agg["total_queries"],
            "tokens_in": agg["total_tokens_in"],
            "tokens_out": agg["total_tokens_out"],
            "cost_usd": total_cost,
        },
        "revenue_share_usd": revenue_share,
    }


@billing_router.post("/reseller/create-user")
def reseller_create_user(
    body: ResellerCreateUserRequest,
    user: dict = Depends(_get_current_user()),
):
    """Create a sub-user account under this reseller.

    Generates an rr_ API key for the sub-user. The reseller must have an active
    enterprise plan; quota is checked against the reseller's own plan limits.
    """
    reseller = _get_reseller(user["id"])
    if not reseller:
        raise HTTPException(404, "No active reseller account found for this user.")

    if body.plan not in PLANS:
        raise HTTPException(400, f"Unknown plan '{body.plan}'. Valid: {list(PLANS.keys())}")

    email = body.email.strip().lower()
    if not email:
        raise HTTPException(400, "email is required.")

    # Check reseller hasn't exceeded their own enterprise quota (unlimited = -1)
    reseller_plan = _user_plan(user["id"])
    plan_info = PLANS.get(reseller_plan, PLANS["free"])
    if plan_info["queries_month"] != -1:
        # Non-enterprise reseller: shouldn't normally get here given register check,
        # but guard anyway so quota logic is consistent.
        month = time.strftime("%Y-%m")
        with _get_db() as db:
            row = db.execute(
                "SELECT COUNT(*) AS c FROM reseller_users WHERE reseller_id = ?",
                (reseller["id"],),
            ).fetchone()
        if row["c"] >= plan_info["api_keys"]:
            raise HTTPException(
                400,
                f"Sub-user limit reached for plan '{reseller_plan}'. Upgrade to enterprise."
            )

    sub_key = f"rr_{secrets.token_hex(24)}"
    now = time.time()

    with _get_db() as db:
        existing = db.execute(
            "SELECT id FROM reseller_users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            raise HTTPException(409, f"A sub-user with email '{email}' already exists.")

        db.execute(
            """INSERT INTO reseller_users (reseller_id, email, plan, api_key, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (reseller["id"], email, body.plan, sub_key, now),
        )
        db.commit()

    return {
        "email": email,
        "plan": body.plan,
        "api_key": sub_key,
        "reseller_id": reseller["id"],
        "created_at": now,
    }


@billing_router.get("/reseller/usage")
def reseller_usage(user: dict = Depends(_get_current_user())):
    """Aggregated usage breakdown across all sub-users for the current month."""
    reseller = _get_reseller(user["id"])
    if not reseller:
        raise HTTPException(404, "No active reseller account found for this user.")

    month = time.strftime("%Y-%m")
    with _get_db() as db:
        sub_users = db.execute(
            "SELECT id, email, plan FROM reseller_users WHERE reseller_id = ?",
            (reseller["id"],),
        ).fetchall()

        rows = []
        for su in sub_users:
            row = db.execute(
                """SELECT queries, tokens_in, tokens_out, cost_usd
                   FROM usage_monthly WHERE user_id = ? AND month = ?""",
                (su["id"], month),
            ).fetchone()
            usage = dict(row) if row else {"queries": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}
            rows.append({
                "user_id": su["id"],
                "email": su["email"],
                "plan": su["plan"],
                "queries": usage["queries"],
                "tokens_in": usage["tokens_in"],
                "tokens_out": usage["tokens_out"],
                "cost_usd": usage["cost_usd"],
            })

    total_cost = sum(r["cost_usd"] for r in rows)
    markup = reseller["markup_pct"] / 100.0

    return {
        "reseller_id": reseller["id"],
        "month": month,
        "markup_pct": reseller["markup_pct"],
        "sub_users": rows,
        "totals": {
            "queries": sum(r["queries"] for r in rows),
            "tokens_in": sum(r["tokens_in"] for r in rows),
            "tokens_out": sum(r["tokens_out"] for r in rows),
            "cost_usd": round(total_cost, 4),
            "revenue_share_usd": round(total_cost * markup, 4),
        },
    }


@billing_router.get("/success")
def billing_success():
    from fastapi.responses import HTMLResponse
    return HTMLResponse("<h1>Payment successful</h1><p>Your plan has been upgraded. Return to the app.</p>")

@billing_router.get("/cancel")
def billing_cancel():
    from fastapi.responses import HTMLResponse
    return HTMLResponse("<h1>Payment cancelled</h1><p>No changes were made to your account.</p>")

# ---------------------------------------------------------------------------
# Credit Endpoints
# ---------------------------------------------------------------------------

@billing_router.get("/credits")
def credits_balance(user: dict = Depends(_get_current_user())):
    """Get current credit balance and recent transactions."""
    return {
        "balance": get_balance(user["id"]),
        "costs": CREDIT_COSTS,
        "ledger": get_ledger(user["id"], 20),
    }


@billing_router.get("/credits/costs")
def credits_costs():
    """Public: credit costs per operation type."""
    return {
        "costs": CREDIT_COSTS,
        "signup_bonus": SIGNUP_BONUS_CREDITS,
        "principle": "The infrastructure owner controls who's admin, not the application. "
                     "Self-host free with your own keys, or use our cloud bridge with credits.",
        "byok": "Bring Your Own Key — plug your API keys, pay providers directly, platform fee: $0.",
    }


# ---------------------------------------------------------------------------
# Admin Endpoints (require admin role)
# ---------------------------------------------------------------------------

def _get_admin_user():
    """Lazy import to avoid circular dependency."""
    from auth_api import _admin_user
    return _admin_user


class AdminGrantCreditsRequest(BaseModel):
    email: str
    amount: int
    reason: str = "admin_grant"


class AdminSetRoleRequest(BaseModel):
    email: str
    role: str  # 'user' or 'admin'


@billing_router.post("/admin/grant-credits")
def admin_grant_credits(body: AdminGrantCreditsRequest, admin: dict = Depends(_get_admin_user())):
    """Admin: grant credits to any user."""
    if body.amount <= 0 or body.amount > 100000:
        raise HTTPException(400, "Amount must be 1-100000")
    with _get_db() as db:
        row = db.execute("SELECT id FROM users WHERE email = ?", (body.email.lower(),)).fetchone()
    if not row:
        raise HTTPException(404, f"User '{body.email}' not found")
    new_balance = grant_credits(row["id"], body.amount, body.reason, f"admin:{admin['email']}")
    return {"email": body.email, "granted": body.amount, "new_balance": new_balance}


@billing_router.get("/admin/users")
def admin_list_users(admin: dict = Depends(_get_admin_user())):
    """Admin: list all users with balances."""
    with _get_db() as db:
        rows = db.execute(
            "SELECT id, email, plan, credits, role, queries, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
    return {"users": [dict(r) for r in rows]}


@billing_router.get("/admin/ledger/{email}")
def admin_user_ledger(email: str, admin: dict = Depends(_get_admin_user())):
    """Admin: view any user's ledger."""
    with _get_db() as db:
        row = db.execute("SELECT id FROM users WHERE email = ?", (email.lower(),)).fetchone()
    if not row:
        raise HTTPException(404, f"User '{email}' not found")
    return {"email": email, "balance": get_balance(row["id"]), "ledger": get_ledger(row["id"], 100)}
