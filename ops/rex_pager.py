#!/usr/bin/env /usr/bin/python3
"""
rex_pager.py — QWRR: Relay + Resurrection for quota-walled agents.

Implements: docs/qwrr-layer.md (Quota Walls, Relays, and Resurrection)
Phases 0+1: Envelope v1, monotonic seq, idempotency, leases, snapshots,
            staleness policy, effect intents, boot protocol.

Architecture:
  - Triple-write: local JSONL (git-auditable) + Firestore + inbox markdown
  - Envelope v1: id, runpoint_id, seq, type, timestamp, source, target, version,
                  idempotency_key, ttl_s, lease_token_required, payload
  - Delivery: ordered by seq, ack-based, at-least-once + idempotent
  - Leases: monotonic fencing tokens, zombie protection (I4, I5)
  - Snapshots: last_seq_applied + state_hash for crash-safe catch-up
  - Boot: acquire lease → load snapshot → catch-up → drain → heartbeat
  - Wake: polls API availability, fires notification + boot on reset

Usage:
  python3 ops/rex_pager.py send B2 LEAD "P0: fix secrets in logs"
  python3 ops/rex_pager.py send HUMAN LEAD "stop retry loops" --priority P0 --ttl 86400
  python3 ops/rex_pager.py status
  python3 ops/rex_pager.py drain LEAD         # deliver pending messages for LEAD
  python3 ops/rex_pager.py boot LEAD          # full boot protocol (section 8)
  python3 ops/rex_pager.py lease LEAD         # acquire/show lease
  python3 ops/rex_pager.py snapshot LEAD      # show/commit snapshot
  python3 ops/rex_pager.py watch              # daemon: poll API + auto-boot on wake
  python3 ops/rex_pager.py wake LEAD          # manual wake signal
  python3 ops/rex_pager.py inspect <msg_id>   # show full envelope
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
MAILBOX_FILE = PROJECT_ROOT / "ops" / "virtual-office" / "relay_mailbox.jsonl"
ACKS_FILE = PROJECT_ROOT / "ops" / "virtual-office" / "relay_acks.jsonl"
INBOX_DIR = PROJECT_ROOT / "ops" / "virtual-office" / "inbox"
POLL_INTERVAL = 300  # 5 min
ANTHROPIC_HEALTH_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_TTL = 86400  # 24h
DEFAULT_RUNPOINT = "rp_rhea_office_v1"

# Firestore (optional — graceful if unavailable)
FIRESTORE_PROJECT = "rhea-office-sync"
FIRESTORE_BASE = f"https://firestore.googleapis.com/v1/projects/{FIRESTORE_PROJECT}/databases/(default)/documents"

# Monotonic sequence counter (file-backed for crash safety)
SEQ_FILE = PROJECT_ROOT / "ops" / "virtual-office" / "relay_seq.txt"

# Leases + snapshots (Phase 1)
LEASES_DIR = PROJECT_ROOT / "ops" / "virtual-office" / "leases"
SNAPSHOTS_DIR = PROJECT_ROOT / "ops" / "virtual-office" / "snapshots"
INTENTS_FILE = PROJECT_ROOT / "ops" / "virtual-office" / "effect_intents.jsonl"
INCIDENTS_FILE = PROJECT_ROOT / "ops" / "virtual-office" / "relay_incidents.jsonl"
CHAIN_FILE = PROJECT_ROOT / "ops" / "virtual-office" / "relay_chain.jsonl"  # hash-chained audit

# Staleness policy (section 8) — max age in seconds before action changes
STALENESS_POLICY = {
    "msg.send": None,           # always deliverable
    "task.create": None,        # can execute after delay
    "decision.record": None,    # informational, always valid
    "effect.request": 3600,     # 1h — requires re-confirmation if older
    "push.now": 900,            # 15min — expires, needs fresh approve
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _next_seq() -> int:
    """Monotonic sequence number, crash-safe via file."""
    SEQ_FILE.parent.mkdir(parents=True, exist_ok=True)
    seq = 0
    if SEQ_FILE.exists():
        try:
            seq = int(SEQ_FILE.read_text().strip())
        except ValueError:
            seq = 0
    seq += 1
    SEQ_FILE.write_text(str(seq))
    return seq


def _idempotency_key(source: str, body: str, ts: str) -> str:
    """Deterministic key: same source+body+second = same key (dedup retries)."""
    raw = f"{source}:{body}:{ts[:19]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _uuidv7_ish() -> str:
    """UUID with timestamp prefix for natural ordering."""
    ts_hex = hex(int(time.time() * 1000))[2:]
    rand = uuid.uuid4().hex[:20]
    return f"{ts_hex}-{rand}"


# ---------------------------------------------------------------------------
# Hash-chained audit log (rhea-advanced lesson 12)
# Tamper-evident: each entry contains hash of previous entry.
# Threats mitigated: truncation, reordering, replay, silent edit.
# ---------------------------------------------------------------------------

def _canonical_json(obj: dict) -> str:
    """Stable JSON encoding: sorted keys, no whitespace, ensure reproducibility."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _last_chain_hash() -> str:
    """Read the hash of the last entry in the chain. Genesis = '0'*64."""
    if not CHAIN_FILE.exists():
        return "0" * 64
    last_line = ""
    for line in CHAIN_FILE.read_text().strip().split("\n"):
        if line.strip():
            last_line = line
    if not last_line:
        return "0" * 64
    return json.loads(last_line).get("event_hash", "0" * 64)


def chain_append(event_type: str, actor: str, payload: dict) -> dict:
    """Append a tamper-evident entry to the audit chain with exclusive locking."""
    import fcntl
    CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHAIN_FILE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
            prev_hash = "0" * 64
            if lines:
                try:
                    prev_hash = json.loads(lines[-1]).get("event_hash", "0" * 64)
                except Exception:
                    prev_hash = "0" * 64
            entry = {
                "timestamp": _now_iso(),
                "event_type": event_type,
                "actor": actor,
                "payload": payload,
                "prev_hash": prev_hash,
            }
            canonical = _canonical_json(entry)
            entry["event_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
            f.write(json.dumps(entry) + "
")
            f.flush()
            return entry
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def chain_verify() -> tuple[bool, int, str]:
    """Verify chain integrity. Returns (valid, entries_checked, error_or_ok)."""
    if not CHAIN_FILE.exists():
        return True, 0, "empty chain"
    prev_hash = "0" * 64
    count = 0
    for line in CHAIN_FILE.read_text().strip().split("\n"):
        if not line.strip():
            continue
        entry = json.loads(line)
        count += 1
        if entry.get("prev_hash") != prev_hash:
            return False, count, f"entry {count}: prev_hash mismatch (truncation/reorder)"
        check = dict(entry)
        stored_hash = check.pop("event_hash")
        canonical = _canonical_json(check)
        expected = hashlib.sha256(canonical.encode()).hexdigest()
        if stored_hash != expected:
            return False, count, f"entry {count}: event_hash mismatch (tampered)"
        prev_hash = stored_hash
    return True, count, "chain valid"


# ---------------------------------------------------------------------------
# Leases (QWRR section 8 step 1, invariants I4 + I5)
# ---------------------------------------------------------------------------

def _lease_file(agent: str) -> Path:
    return LEASES_DIR / f"{agent}.json"


LEASE_TTL_S = 600  # 10 minutes — lease expires if not renewed


def acquire_lease(agent: str, ttl_s: int = LEASE_TTL_S) -> int:
    """Acquire monotonic lease with TTL. Old lease holders are fenced out.

    Network partition safety:
    - Lease has expires_at timestamp
    - verify_lease() rejects expired leases
    - Holder must call renew_lease() before expiry (heartbeat)
    - If two agents both think they hold the lease, the one whose lease
      expired first is automatically fenced out on next verify_lease() call
    """
    LEASES_DIR.mkdir(parents=True, exist_ok=True)
    f = _lease_file(agent)
    prev_token = 0
    if f.exists():
        try:
            prev = json.loads(f.read_text())
            prev_token = prev.get("lease_token", 0)
        except (json.JSONDecodeError, ValueError):
            pass
    new_token = prev_token + 1
    now = _now_iso()
    lease = {
        "agent": agent,
        "lease_token": new_token,
        "acquired_at": now,
        "renewed_at": now,
        "expires_at": _future_iso(ttl_s),
        "ttl_s": ttl_s,
        "prev_token": prev_token,
    }
    f.write_text(json.dumps(lease, indent=2))

    # Also write to Firestore for cross-agent visibility
    _write_lease_firestore(agent, lease)

    chain_append("lease.acquire", agent, {"lease_token": new_token, "prev_token": prev_token, "ttl_s": ttl_s})
    print(f"[lease] {agent} acquired lease_token={new_token} (prev={prev_token}, TTL={ttl_s}s)")
    return new_token


def renew_lease(agent: str, token: int) -> bool:
    """Renew a lease (heartbeat). Returns False if lease is stale or expired."""
    f = _lease_file(agent)
    if not f.exists():
        return False
    lease = json.loads(f.read_text())
    if lease.get("lease_token") != token:
        return False
    # Check if already expired
    if _is_expired(lease.get("expires_at")):
        _write_incident({"id": f"lease-{agent}", "type": "lease.expired"}, f"Lease {token} expired before renewal")
        return False
    ttl = lease.get("ttl_s", LEASE_TTL_S)
    now = _now_iso()
    lease["renewed_at"] = now
    lease["expires_at"] = _future_iso(ttl)
    f.write_text(json.dumps(lease, indent=2))
    return True


def get_lease(agent: str) -> dict:
    f = _lease_file(agent)
    if not f.exists():
        return {"agent": agent, "lease_token": 0, "acquired_at": None, "expired": True}
    lease = json.loads(f.read_text())
    lease["expired"] = _is_expired(lease.get("expires_at"))
    return lease


def verify_lease(agent: str, token: int) -> bool:
    """I5: reject if token doesn't match current lease OR lease has expired.

    This is the critical split-brain protection:
    - If agent A's lease expired during a network partition, agent B can
      acquire a new lease. When A comes back, its old token is rejected.
    - Even if A still has the file, the expired flag prevents execution.
    """
    current = get_lease(agent)
    if current.get("lease_token", 0) != token:
        return False
    if current.get("expired", True):
        return False
    return True


def _future_iso(seconds: int) -> str:
    """Return ISO timestamp N seconds from now."""
    from datetime import timedelta
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def _is_expired(expires_at: str | None) -> bool:
    """Check if an ISO timestamp is in the past."""
    if not expires_at:
        return True
    try:
        exp = datetime.fromisoformat(expires_at)
        return datetime.now(timezone.utc) > exp
    except (ValueError, TypeError):
        return True


def _write_lease_firestore(agent: str, lease: dict):
    try:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if not creds_path:
            return
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=["https://www.googleapis.com/auth/datastore"]
        )
        creds.refresh(Request())
        url = f"{FIRESTORE_BASE}/runpoints/{DEFAULT_RUNPOINT}/leases/{agent}"
        fields = {k: {"stringValue": str(v)} if not isinstance(v, int) else {"integerValue": str(v)}
                  for k, v in lease.items()}
        data = json.dumps({"fields": fields}).encode()
        req = urllib.request.Request(url, data=data, method="PATCH",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {creds.token}"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  [firestore] lease write failed (non-fatal): {e}")


# ---------------------------------------------------------------------------
# Snapshots (QWRR section 8 step 2+6)
# ---------------------------------------------------------------------------

def _snapshot_file(agent: str) -> Path:
    return SNAPSHOTS_DIR / f"{agent}.json"


def load_snapshot(agent: str) -> dict:
    """Load last known state for agent."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    f = _snapshot_file(agent)
    if not f.exists():
        return {"agent": agent, "last_seq_applied": 0, "state_hash": "", "saved_at": None}
    return json.loads(f.read_text())


def commit_snapshot(agent: str, last_seq_applied: int, extra: dict = None):
    """Save snapshot after successful drain. Section 8 step 6."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    snap = {
        "agent": agent,
        "last_seq_applied": last_seq_applied,
        "state_hash": hashlib.sha256(f"{agent}:{last_seq_applied}:{_now_iso()}".encode()).hexdigest()[:16],
        "saved_at": _now_iso(),
    }
    if extra:
        snap.update(extra)
    _snapshot_file(agent).write_text(json.dumps(snap, indent=2))

    # Firestore mirror
    try:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if not creds_path:
            return
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=["https://www.googleapis.com/auth/datastore"]
        )
        creds.refresh(Request())
        url = f"{FIRESTORE_BASE}/runpoints/{DEFAULT_RUNPOINT}/snapshots/{agent}"
        fields = {k: {"stringValue": str(v)} if not isinstance(v, int) else {"integerValue": str(v)}
                  for k, v in snap.items()}
        data = json.dumps({"fields": fields}).encode()
        req = urllib.request.Request(url, data=data, method="PATCH",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {creds.token}"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

    print(f"[snapshot] {agent} seq={last_seq_applied} hash={snap['state_hash']}")


# ---------------------------------------------------------------------------
# Staleness policy (QWRR section 8)
# ---------------------------------------------------------------------------

def check_staleness(msg: dict) -> tuple[str, str]:
    """Returns (action, reason). action = 'deliver' | 'expire' | 'reconfirm'."""
    msg_type = msg.get("type", "msg.send")
    threshold = STALENESS_POLICY.get(msg_type)
    if threshold is None:
        return "deliver", "no staleness limit"
    age = time.time() - datetime.fromisoformat(msg["timestamp"]).timestamp()
    if age > msg.get("ttl_s", DEFAULT_TTL):
        return "expire", f"TTL exceeded ({age:.0f}s > {msg.get('ttl_s', DEFAULT_TTL)}s)"
    if age > threshold:
        if msg_type == "push.now":
            return "expire", f"push.now too stale ({age:.0f}s > {threshold}s)"
        return "reconfirm", f"{msg_type} needs re-confirmation ({age:.0f}s > {threshold}s)"
    return "deliver", "within staleness window"


def _write_incident(msg: dict, reason: str):
    """Log an incident for expired/stale messages."""
    INCIDENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    incident = {
        "incident_id": f"INC-RELAY-{_uuidv7_ish()[:13]}",
        "timestamp": _now_iso(),
        "message_id": msg.get("id"),
        "seq": msg.get("seq"),
        "source": msg.get("source"),
        "target": msg.get("target"),
        "type": msg.get("type"),
        "reason": reason,
    }
    with open(INCIDENTS_FILE, "a") as f:
        f.write(json.dumps(incident) + "\n")
    print(f"  [incident] {incident['incident_id']}: {reason}")


# ---------------------------------------------------------------------------
# Effect intents (QWRR section 9)
# ---------------------------------------------------------------------------

def create_effect_intent(msg: dict, lease_token: int, kind: str = None) -> dict:
    """Convert a message to an effect intent (outbox pattern). Section 9."""
    intent = {
        "intent_id": _uuidv7_ish(),
        "runpoint_id": msg.get("runpoint_id", DEFAULT_RUNPOINT),
        "kind": kind or msg.get("type", "unknown"),
        "idempotency_key": msg.get("idempotency_key", ""),
        "lease_token": lease_token,
        "payload": msg.get("payload", {}),
        "status": "planned",
        "receipt": {},
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "source_message_id": msg.get("id"),
    }
    INTENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INTENTS_FILE, "a") as f:
        f.write(json.dumps(intent) + "\n")
    return intent


def _read_intents() -> list[dict]:
    """Read all effect intents."""
    if not INTENTS_FILE.exists():
        return []
    intents = []
    for line in INTENTS_FILE.read_text().strip().split("\n"):
        if line.strip():
            intents.append(json.loads(line))
    return intents


def _update_intent(intent_id: str, status: str, receipt: dict = None):
    """Update an intent's status and receipt in-place."""
    intents = _read_intents()
    updated = []
    for intent in intents:
        if intent["intent_id"] == intent_id:
            intent["status"] = status
            intent["updated_at"] = _now_iso()
            if receipt:
                intent["receipt"] = receipt
        updated.append(intent)
    INTENTS_FILE.write_text("\n".join(json.dumps(i) for i in updated) + "\n")


# Effect handlers: kind → callable(payload) → receipt_dict
# Registered handlers return a receipt dict or raise on failure
EFFECT_HANDLERS: dict[str, callable] = {}


def register_effect_handler(kind: str, handler: callable):
    """Register a handler for an effect kind (git_push, firestore_write, etc.)."""
    EFFECT_HANDLERS[kind] = handler


def execute_intents(agent: str, lease_token: int = 0, dry_run: bool = False) -> dict:
    """Execute pending effect intents for an agent. QWRR Section 9 executor.

    Rules:
    - Reject intents with stale lease_token (if agent has active lease)
    - Deduplicate on idempotency_key
    - Write receipts on success
    - Log failures as incidents
    """
    intents = _read_intents()
    pending = [i for i in intents if i["status"] == "planned"]

    if not pending:
        print("[executor] No pending intents.")
        return {"executed": 0, "skipped": 0, "failed": 0}

    # Get current lease for validation
    current_token = 0
    if lease_token:
        current_token = lease_token
    else:
        lease = get_lease(agent)
        if lease:
            current_token = lease.get("lease_token", 0)

    executed = 0
    skipped = 0
    failed = 0
    seen_idem = set()

    for intent in pending:
        iid = intent["intent_id"]
        kind = intent["kind"]
        idem = intent.get("idempotency_key", "")

        # Deduplicate
        if idem and idem in seen_idem:
            _update_intent(iid, "skipped", {"reason": "duplicate idempotency_key"})
            skipped += 1
            print(f"  [skip] {iid}: duplicate idem={idem[:16]}")
            continue
        if idem:
            seen_idem.add(idem)

        # Lease validation
        if current_token > 0 and intent.get("lease_token", 0) > 0:
            if intent["lease_token"] != current_token:
                _update_intent(iid, "rejected", {"reason": f"stale lease: intent={intent['lease_token']}, current={current_token}"})
                skipped += 1
                _write_incident(intent, f"effect intent rejected: stale lease token {intent['lease_token']} != {current_token}")
                print(f"  [reject] {iid}: stale lease token")
                continue

        # Dry run
        if dry_run:
            print(f"  [dry-run] {iid}: {kind} — would execute")
            continue

        # Execute handler
        handler = EFFECT_HANDLERS.get(kind)
        if handler:
            try:
                receipt = handler(intent["payload"])
                _update_intent(iid, "committed", receipt or {})
                chain_append("effect.committed", agent, {"intent_id": iid, "kind": kind})
                executed += 1
                print(f"  [ok] {iid}: {kind} → committed")
            except Exception as e:
                _update_intent(iid, "failed", {"error": str(e)})
                _write_incident(intent, f"effect execution failed: {e}")
                failed += 1
                print(f"  [fail] {iid}: {kind} → {e}")
        else:
            # No handler registered — mark as pending until handler exists
            print(f"  [no-handler] {iid}: {kind} — no handler registered, stays planned")

    result = {"executed": executed, "skipped": skipped, "failed": failed, "total": len(pending)}
    print(f"\n[executor] {executed} committed, {skipped} skipped, {failed} failed (of {len(pending)})")
    return result


def intent_status() -> dict:
    """Show intent counts by status."""
    intents = _read_intents()
    by_status: dict[str, int] = {}
    for i in intents:
        s = i.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
    return {"total": len(intents), "by_status": by_status}


# ---------------------------------------------------------------------------
# Built-in effect handlers
# ---------------------------------------------------------------------------

def _handle_git_push(payload: dict) -> dict:
    """Execute a git push. Returns receipt with push result."""
    import subprocess
    remote = payload.get("remote", "origin")
    branch = payload.get("branch", "")
    if not branch:
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        branch = result.stdout.strip()
    result = subprocess.run(["git", "push", remote, branch],
                            capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        raise RuntimeError(f"git push failed: {result.stderr.strip()}")
    return {"remote": remote, "branch": branch, "output": result.stdout.strip() or result.stderr.strip()}


def _handle_git_commit(payload: dict) -> dict:
    """Execute a git commit. Returns receipt with commit SHA."""
    import subprocess
    msg = payload.get("message", "auto-commit")
    files = payload.get("files", [])
    if files:
        subprocess.run(["git", "add"] + files, cwd=str(PROJECT_ROOT), check=True)
    result = subprocess.run(["git", "commit", "-m", msg],
                            capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        raise RuntimeError(f"git commit failed: {result.stderr.strip()}")
    sha_result = subprocess.run(["git", "rev-parse", "HEAD"],
                                capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    return {"commit_sha": sha_result.stdout.strip(), "message": msg}


# Register built-in handlers
register_effect_handler("git_push", _handle_git_push)
register_effect_handler("git_commit", _handle_git_commit)


# ---------------------------------------------------------------------------
# Envelope v1 (per QWRR spec section 4)
# ---------------------------------------------------------------------------

def make_envelope(
    source: str,
    target: str,
    msg_type: str,
    payload: dict,
    priority: str = "P1",
    ttl_s: int = DEFAULT_TTL,
    runpoint_id: str = DEFAULT_RUNPOINT,
) -> dict:
    ts = _now_iso()
    body_str = json.dumps(payload, sort_keys=True)
    return {
        "id": _uuidv7_ish(),
        "runpoint_id": runpoint_id,
        "seq": _next_seq(),
        "type": msg_type,
        "timestamp": ts,
        "source": source,
        "target": target,
        "version": 1,
        "idempotency_key": _idempotency_key(source, body_str, ts),
        "ttl_s": ttl_s,
        "lease_token_required": 0,  # Phase 1: fencing
        "priority": priority,
        "payload": payload,
        "status": "pending",  # pending → delivered → acked
    }


# ---------------------------------------------------------------------------
# Mailbox: dual-write (local JSONL + Firestore)
# ---------------------------------------------------------------------------

def _write_local(envelope: dict):
    """Append to local JSONL (git-auditable)."""
    MAILBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MAILBOX_FILE, "a") as f:
        f.write(json.dumps(envelope) + "\n")


def _write_firestore(envelope: dict):
    """Write to Firestore mailbox collection (best-effort)."""
    try:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if not creds_path:
            return  # no creds, skip silently

        # Get auth token
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=["https://www.googleapis.com/auth/datastore"]
        )
        creds.refresh(Request())

        url = (
            f"{FIRESTORE_BASE}/runpoints/{envelope['runpoint_id']}"
            f"/mailbox/{envelope['target']}/messages/{envelope['id']}"
        )
        # Convert to Firestore field format
        fields = {}
        for k, v in envelope.items():
            if k == "payload":
                fields[k] = {"stringValue": json.dumps(v)}
            elif isinstance(v, int):
                fields[k] = {"integerValue": str(v)}
            elif isinstance(v, bool):
                fields[k] = {"booleanValue": v}
            else:
                fields[k] = {"stringValue": str(v)}

        data = json.dumps({"fields": fields}).encode()
        req = urllib.request.Request(
            url, data=data, method="PATCH",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds.token}",
            }
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  [firestore] write failed (non-fatal): {e}")


def _write_inbox_backup(envelope: dict):
    """Also write to git-tracked inbox as human-readable backup."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fname = f"RELAY_{ts}_{envelope['source']}_to_{envelope['target']}.md"
    body = envelope["payload"].get("body", json.dumps(envelope["payload"]))

    (INBOX_DIR / fname).write_text(
        f"# RELAY MESSAGE — {envelope['source']} → {envelope['target']}\n"
        f"**Envelope ID:** {envelope['id']}\n"
        f"**Seq:** {envelope['seq']}\n"
        f"**Priority:** {envelope['priority']}\n"
        f"**Type:** {envelope['type']}\n"
        f"**TTL:** {envelope['ttl_s']}s\n"
        f"**Idempotency Key:** {envelope['idempotency_key']}\n"
        f"**Time:** {envelope['timestamp']}\n\n"
        f"{body}\n"
    )


def enqueue(source: str, target: str, body: str, priority: str = "P1",
            msg_type: str = "msg.send", ttl_s: int = DEFAULT_TTL):
    """Enqueue a message: I1 (no loss) guaranteed by triple-write."""
    payload = {"body": body, "priority": priority}
    envelope = make_envelope(source, target, msg_type, payload, priority, ttl_s)

    # Triple-write: local JSONL + Firestore + inbox file
    _write_local(envelope)
    _write_firestore(envelope)
    _write_inbox_backup(envelope)

    # Audit chain entry
    chain_append("relay.enqueue", source, {"msg_id": envelope["id"], "seq": envelope["seq"], "target": target})

    print(f"[relay] Enqueued seq={envelope['seq']} {source}→{target} ({priority})")
    print(f"  id: {envelope['id']}")
    print(f"  idem: {envelope['idempotency_key']}")
    return envelope


# ---------------------------------------------------------------------------
# Read + drain (I2: ordered by seq)
# ---------------------------------------------------------------------------

def _read_mailbox() -> list[dict]:
    if not MAILBOX_FILE.exists():
        return []
    msgs = []
    for line in MAILBOX_FILE.read_text().strip().split("\n"):
        if line.strip():
            msgs.append(json.loads(line))
    return sorted(msgs, key=lambda m: m.get("seq", 0))


def _read_acks() -> set[str]:
    if not ACKS_FILE.exists():
        return set()
    acks = set()
    for line in ACKS_FILE.read_text().strip().split("\n"):
        if line.strip():
            acks.add(json.loads(line).get("message_id", ""))
    return acks


def _write_ack(message_id: str, target: str):
    """I3: idempotent ack — safe to repeat."""
    acks = _read_acks()
    if message_id in acks:
        return  # already acked, no-op
    ACKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ACKS_FILE, "a") as f:
        f.write(json.dumps({
            "message_id": message_id,
            "target": target,
            "acked_at": _now_iso(),
        }) + "\n")


def drain(target: str, lease_token: int = 0, from_seq: int = 0):
    """Drain pending messages for target, in seq order.
    I2 (ordered) + I3 (idempotent) + staleness policy + effect intents."""
    mailbox = _read_mailbox()
    acks = _read_acks()

    delivered = []
    expired_list = []
    reconfirm_list = []
    seen_idem_keys = set()  # I3: idempotency dedup within single drain

    for m in mailbox:
        if m.get("target") != target:
            continue
        if m["id"] in acks:
            continue
        if m.get("seq", 0) <= from_seq:
            continue
        # I3: deduplicate by idempotency key (blocks replay attacks)
        idem = m.get("idempotency_key", "")
        if idem and idem in seen_idem_keys:
            _write_ack(m["id"], target)  # ack the duplicate
            continue
        if idem:
            seen_idem_keys.add(idem)

        # Staleness check (section 8)
        action, reason = check_staleness(m)

        if action == "expire":
            expired_list.append((m, reason))
            _write_ack(m["id"], target)
            _write_incident(m, reason)
            continue

        if action == "reconfirm":
            reconfirm_list.append((m, reason))
            _write_incident(m, f"NEEDS RECONFIRM: {reason}")
            _write_ack(m["id"], target)  # ack to prevent re-processing, log incident
            continue

        # Lease gate for dangerous types (I4, I5)
        if m.get("lease_token_required", 0) > 0 and lease_token > 0:
            if m["lease_token_required"] != lease_token:
                _write_incident(m, f"lease mismatch: msg requires {m['lease_token_required']}, current {lease_token}")
                _write_ack(m["id"], target)
                continue

        # Deliver
        body = m["payload"].get("body", json.dumps(m["payload"]))
        print(f"  seq={m['seq']} [{m.get('priority','P1')}] {m['source']} @ {m['timestamp'][:19]}Z")
        print(f"  {body}")
        print(f"  id={m['id']} idem={m['idempotency_key']}")

        # Effect types get converted to intents, not executed directly (section 9)
        if m.get("type") in ("effect.request", "push.now") and lease_token > 0:
            intent = create_effect_intent(m, lease_token)
            print(f"  -> effect intent: {intent['intent_id']} (status: planned)")

        _write_ack(m["id"], target)
        delivered.append(m)
        print("-" * 60)

    if expired_list:
        print(f"\n[relay] {len(expired_list)} expired:")
        for m, reason in expired_list:
            print(f"  seq={m['seq']} {m['source']}: {reason}")

    if reconfirm_list:
        print(f"\n[relay] {len(reconfirm_list)} need re-confirmation:")
        for m, reason in reconfirm_list:
            print(f"  seq={m['seq']} {m['source']}: {reason}")

    if delivered:
        print(f"\n[relay] {len(delivered)} messages delivered + acked for {target}.")
    else:
        print(f"[relay] No pending messages for {target}.")

    return delivered


# ---------------------------------------------------------------------------
# Boot protocol (QWRR section 8 — the full sequence)
# ---------------------------------------------------------------------------

def boot(agent: str):
    """Full boot protocol per QWRR section 8.
    1. Acquire lease
    2. Load snapshot
    3. Catch-up (seq > last_seq_applied)
    4. Drain mailbox in-order
    5. Staleness + lease gating (inside drain)
    6. Commit snapshot + heartbeat
    """
    print("=" * 60)
    print(f"  QWRR BOOT PROTOCOL — {agent}")
    print("=" * 60)

    # Step 1: Acquire lease
    print(f"\n[1/6] Acquiring lease...")
    token = acquire_lease(agent)

    # Step 2: Load snapshot
    print(f"\n[2/6] Loading snapshot...")
    snap = load_snapshot(agent)
    last_seq = snap.get("last_seq_applied", 0)
    print(f"  last_seq_applied={last_seq} hash={snap.get('state_hash', 'none')}")
    if snap.get("saved_at"):
        print(f"  saved_at={snap['saved_at']}")

    # Step 3+4: Catch-up + drain (from last_seq_applied)
    print(f"\n[3/6] Catching up from seq>{last_seq}...")
    print(f"[4/6] Draining mailbox (lease_token={token})...\n")
    delivered = drain(agent, lease_token=token, from_seq=last_seq)

    # Step 5: Staleness + lease gating handled inside drain()
    print(f"\n[5/6] Staleness + lease verification (applied during drain)")

    # Step 6: Commit snapshot + heartbeat
    max_seq = last_seq
    if delivered:
        max_seq = max(m.get("seq", 0) for m in delivered)
    commit_snapshot(agent, max_seq, extra={"lease_token": token, "messages_drained": len(delivered)})

    # Heartbeat
    print(f"\n[6/6] Heartbeat...")
    try:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if creds_path:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account
            cred = service_account.Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/datastore"])
            cred.refresh(Request())
            url = f"{FIRESTORE_BASE}/agents/{agent}"
            fields = {
                "desk": {"stringValue": agent},
                "status": {"stringValue": "ALIVE"},
                "last_seen": {"stringValue": _now_iso()},
                "lease_token": {"integerValue": str(token)},
            }
            data = json.dumps({"fields": fields}).encode()
            req = urllib.request.Request(url, data=data, method="PATCH",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {cred.token}"})
            urllib.request.urlopen(req, timeout=10)
            print(f"  {agent} heartbeat: ALIVE (lease={token})")
    except Exception as e:
        print(f"  heartbeat failed (non-fatal): {e}")

    chain_append("boot.complete", agent, {"lease_token": token, "last_seq": max_seq, "msgs": len(delivered)})

    print(f"\n{'=' * 60}")
    print(f"  BOOT COMPLETE — {agent}")
    print(f"  lease={token} last_seq={max_seq} msgs={len(delivered)}")
    print(f"{'=' * 60}")
    return token, delivered


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def show_status():
    mailbox = _read_mailbox()
    acks = _read_acks()
    now = time.time()

    pending = [m for m in mailbox if m["id"] not in acks]
    acked = [m for m in mailbox if m["id"] in acks]

    # Group by target
    by_target = {}
    for m in pending:
        t = m.get("target", "?")
        by_target.setdefault(t, []).append(m)

    print(f"QWRR RELAY STATUS")
    print(f"{'=' * 50}")
    print(f"  Total messages: {len(mailbox)}")
    print(f"  Pending:        {len(pending)}")
    print(f"  Acked:          {len(acked)}")
    print(f"  Seq counter:    {SEQ_FILE.read_text().strip() if SEQ_FILE.exists() else '0'}")

    for target, msgs in by_target.items():
        print(f"\n  --- {target} ({len(msgs)} pending) ---")
        for m in msgs:
            age = now - datetime.fromisoformat(m["timestamp"]).timestamp()
            ttl = m.get("ttl_s", DEFAULT_TTL)
            remaining = ttl - age
            status = "OK" if remaining > 0 else "EXPIRED"
            body = m["payload"].get("body", "")[:50]
            print(f"  seq={m['seq']:3d} [{m['priority']}] {m['source']:6s} | {status:7s} | {body}...")


# ---------------------------------------------------------------------------
# API check + wake
# ---------------------------------------------------------------------------

def check_anthropic_api() -> tuple[bool, str]:
    """Probe Anthropic API. Detects quota walls vs real availability."""
    try:
        req = urllib.request.Request(
            ANTHROPIC_HEALTH_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": "probe-key-not-real",
                "anthropic-version": "2023-06-01",
            },
            method="POST",
            data=json.dumps({
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "1"}],
            }).encode(),
        )
        urllib.request.urlopen(req, timeout=10)
        return True, "ok"
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        if "exceeded daily token limit" in body.lower() or "token limit" in body.lower():
            return False, "daily token limit exceeded"
        if e.code == 401:
            return True, "API reachable (auth rejected = not quota-blocked)"
        return True, f"API reachable (HTTP {e.code})"
    except Exception as e:
        return False, f"unreachable: {e}"


def wake_signal(target: str):
    """Fire wake: notification + full boot protocol + wake marker."""
    print(f"[relay] WAKE SIGNAL for {target}")

    # macOS notification
    try:
        mailbox = _read_mailbox()
        acks = _read_acks()
        n_pending = len([m for m in mailbox if m["id"] not in acks and m.get("target") == target])
        subprocess.run([
            "osascript", "-e",
            f'display notification "{target} can wake. {n_pending} pending messages." '
            f'with title "RHEA RELAY" sound name "Hero"'
        ], timeout=5)
    except Exception:
        pass

    print("\a")  # terminal bell

    # Full boot protocol instead of raw drain
    token, delivered = boot(target)

    # Wake marker
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    wake_file = INBOX_DIR / f"RELAY_WAKE_{ts}_{target}.md"
    wake_file.write_text(
        f"# RELAY WAKE — {target}\n"
        f"**Time:** {_now_iso()}\n"
        f"**Trigger:** API availability detected by rex_pager.py\n"
        f"**Lease:** {token}\n"
        f"**Messages drained:** {len(delivered)}\n"
        f"**Boot:** `python3 ops/rex_pager.py boot {target}`\n"
    )
    print(f"[relay] Wake marker: {wake_file.name}")


def watch_daemon(target: str = "LEAD"):
    """Poll API, auto-drain on wake. Section 7 of QWRR."""
    print(f"[relay] Watching for {target} wake (poll every {POLL_INTERVAL}s)")
    print(f"[relay] Ctrl+C to stop.\n")

    was_blocked = True

    while True:
        # P0: Runtime STOP Enforcement
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.path.exists(os.path.join(root_dir, \"STOP\")):
            print(f\"[{datetime.now()}] STOP sentinel detected in root. Exiting.\")
            break
        available, detail = check_anthropic_api()
        now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        if available and was_blocked:
            print(f"[{now}] QUOTA RESET DETECTED — waking {target}!")
            wake_signal(target)
            was_blocked = False
        elif available:
            print(f"[{now}] API available ✓")
        else:
            print(f"[{now}] blocked: {detail}")
            was_blocked = True

        time.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "send":
        if len(sys.argv) < 5:
            print("Usage: rex_pager.py send <from> <to> <message> [--priority P0] [--ttl 86400]")
            sys.exit(1)
        source = sys.argv[2]
        target = sys.argv[3]
        body = sys.argv[4]
        priority = "P1"
        ttl = DEFAULT_TTL
        if "--priority" in sys.argv:
            idx = sys.argv.index("--priority")
            if idx + 1 < len(sys.argv):
                priority = sys.argv[idx + 1]
        if "--ttl" in sys.argv:
            idx = sys.argv.index("--ttl")
            if idx + 1 < len(sys.argv):
                ttl = int(sys.argv[idx + 1])
        enqueue(source, target, body, priority, ttl_s=ttl)

    elif cmd == "status":
        show_status()

    elif cmd == "drain":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        drain(target)

    elif cmd == "boot":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        boot(target)

    elif cmd == "lease":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        if "--acquire" in sys.argv:
            acquire_lease(target)
        elif "--renew" in sys.argv:
            lease = get_lease(target)
            token = lease.get("lease_token", 0)
            ok = renew_lease(target, token)
            print(f"[lease] {target} renew: {'OK' if ok else 'FAILED (expired or stale)'}")
        else:
            lease = get_lease(target)
            print(json.dumps(lease, indent=2))
            if lease.get("expired"):
                print("  ⚠ LEASE EXPIRED — needs re-acquisition")

    elif cmd == "snapshot":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        snap = load_snapshot(target)
        print(json.dumps(snap, indent=2))

    elif cmd == "wake":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        wake_signal(target)

    elif cmd == "watch":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        watch_daemon(target)

    elif cmd == "verify":
        valid, count, detail = chain_verify()
        print(f"Chain integrity: {'VALID' if valid else 'BROKEN'}")
        print(f"  Entries: {count}")
        print(f"  Detail: {detail}")
        sys.exit(0 if valid else 1)

    elif cmd == "inspect":
        if len(sys.argv) < 3:
            print("Usage: rex_pager.py inspect <message_id>")
            sys.exit(1)
        msg_id = sys.argv[2]
        for m in _read_mailbox():
            if m["id"] == msg_id or m.get("idempotency_key") == msg_id:
                print(json.dumps(m, indent=2))
                sys.exit(0)
        print(f"Not found: {msg_id}")
        sys.exit(1)

    elif cmd == "execute":
        agent = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        dry = "--dry-run" in sys.argv
        execute_intents(agent, dry_run=dry)

    elif cmd == "intents":
        status = intent_status()
        print(f"Effect intents: {status['total']} total")
        for s, c in sorted(status["by_status"].items()):
            print(f"  {s}: {c}")

    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
