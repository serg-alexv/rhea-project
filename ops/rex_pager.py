#!/usr/bin/env /usr/bin/python3
"""
rex_pager.py — QWRR Phase 0: Relay + Resurrection for quota-walled agents.

Implements: docs/qwrr-layer.md (Quota Walls, Relays, and Resurrection)
Phase 0: Envelope v1, monotonic seq, idempotency, Firestore mailbox, drain, wake.

Architecture:
  - Dual-write: local JSONL (git-auditable) + Firestore (cross-agent readable)
  - Envelope v1: id, runpoint_id, seq, type, timestamp, source, target, version,
                  idempotency_key, ttl_s, lease_token_required, payload
  - Delivery: ordered by seq, ack-based, at-least-once + idempotent
  - Wake: polls API availability, fires macOS notification + drain on reset

Usage:
  python3 ops/rex_pager.py send B2 LEAD "P0: fix secrets in logs"
  python3 ops/rex_pager.py send HUMAN LEAD "stop retry loops" --priority P0 --ttl 86400
  python3 ops/rex_pager.py status
  python3 ops/rex_pager.py drain LEAD         # deliver pending messages for LEAD
  python3 ops/rex_pager.py watch              # daemon: poll API + auto-drain on wake
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


def drain(target: str):
    """Drain pending messages for target, in seq order. I2 + I3."""
    mailbox = _read_mailbox()
    acks = _read_acks()
    now = time.time()

    pending = []
    expired = []
    for m in mailbox:
        if m.get("target") != target:
            continue
        if m["id"] in acks:
            continue
        # TTL check
        msg_time = datetime.fromisoformat(m["timestamp"]).timestamp()
        if now - msg_time > m.get("ttl_s", DEFAULT_TTL):
            expired.append(m)
            continue
        pending.append(m)

    if expired:
        print(f"[relay] {len(expired)} expired messages (TTL exceeded):")
        for m in expired:
            print(f"  EXPIRED seq={m['seq']} from {m['source']}: {m['payload'].get('body', '')[:60]}")
            _write_ack(m["id"], target)  # ack as expired

    if not pending:
        print(f"[relay] No pending messages for {target}.")
        return []

    print(f"[relay] Draining {len(pending)} messages for {target} (ordered by seq):\n")
    print("=" * 60)
    for m in pending:
        body = m["payload"].get("body", json.dumps(m["payload"]))
        print(f"\n  seq={m['seq']} [{m['priority']}] {m['source']} @ {m['timestamp'][:19]}Z")
        print(f"  {body}")
        print(f"  id={m['id']} idem={m['idempotency_key']}")
        print("-" * 60)
        _write_ack(m["id"], target)

    print(f"\n[relay] {len(pending)} messages delivered + acked for {target}.")
    return pending


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
    """Fire wake: notification + drain + wake marker."""
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
    drain(target)

    # Wake marker
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    wake_file = INBOX_DIR / f"RELAY_WAKE_{ts}_{target}.md"
    wake_file.write_text(
        f"# RELAY WAKE — {target}\n"
        f"**Time:** {_now_iso()}\n"
        f"**Trigger:** API availability detected by rex_pager.py\n"
        f"**Action:** `python3 ops/rex_pager.py drain {target}`\n"
    )
    print(f"[relay] Wake marker: {wake_file.name}")


def watch_daemon(target: str = "LEAD"):
    """Poll API, auto-drain on wake. Section 7 of QWRR."""
    print(f"[relay] Watching for {target} wake (poll every {POLL_INTERVAL}s)")
    print(f"[relay] Ctrl+C to stop.\n")

    was_blocked = True

    while True:
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

    elif cmd == "wake":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        wake_signal(target)

    elif cmd == "watch":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        watch_daemon(target)

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

    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
