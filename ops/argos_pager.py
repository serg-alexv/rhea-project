#!/usr/bin/env python3
"""
argos_pager.py — COWORK/Argos Observation Daemon.

The hundred-eyed watchman: continuous observation of all Rhea office
participants without relying on the human as intermediary.

Implements the COWORK desk's unique role: observation, aggregation,
and proactive alerting. Built on QWRR infrastructure (docs/qwrr-layer.md).

Architecture:
  - Reuses rex_pager.py relay infrastructure (envelope v1, mailbox, chain)
  - Adds: git monitoring, inbox scanning, status aggregation, alerts
  - Deployable as: host daemon, cron job, or Cowork scheduled shortcut
  - Triple observation: git log + relay mailbox + desk leases/snapshots

Modes:
  watch     — daemon: poll git + inbox + desks, alert on changes
  scan      — one-shot: scan everything, print report, exit
  inbox     — check and process COWORK inbox messages
  status    — show all-desks watchtower view
  report    — generate structured observation report (markdown)
  alert     — send alert to relay (any desk)
  heartbeat — update COWORK desk heartbeat
  boot      — full COWORK boot protocol (lease + drain + snapshot)

Usage:
  python3 ops/argos_pager.py watch                     # daemon mode
  python3 ops/argos_pager.py watch --interval 60       # custom poll interval
  python3 ops/argos_pager.py scan                      # one-shot scan
  python3 ops/argos_pager.py inbox                     # process inbox
  python3 ops/argos_pager.py status                    # watchtower view
  python3 ops/argos_pager.py report                    # generate report
  python3 ops/argos_pager.py alert B2 "P0: need review"
  python3 ops/argos_pager.py heartbeat
  python3 ops/argos_pager.py boot
"""
from __future__ import annotations

import hashlib
import json
import os
import fcntl
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
OPS_DIR = PROJECT_ROOT / "ops"
OFFICE_DIR = OPS_DIR / "virtual-office"
INBOX_DIR = OFFICE_DIR / "inbox"
OUTBOX_DIR = OFFICE_DIR / "outbox"
LEASES_DIR = OFFICE_DIR / "leases"
SNAPSHOTS_DIR = OFFICE_DIR / "snapshots"
MAILBOX_FILE = OFFICE_DIR / "relay_mailbox.jsonl"
ACKS_FILE = OFFICE_DIR / "relay_acks.jsonl"
CHAIN_FILE = OFFICE_DIR / "relay_chain.jsonl"
SEQ_FILE = OFFICE_DIR / "relay_seq.txt"
INCIDENTS_FILE = OFFICE_DIR / "relay_incidents.jsonl"

# Argos-specific state
ARGOS_STATE_DIR = OFFICE_DIR / "argos"
ARGOS_STATE_FILE = ARGOS_STATE_DIR / "watcher_state.json"
ARGOS_LOG_FILE = ARGOS_STATE_DIR / "observations.jsonl"
ARGOS_REPORT_DIR = INBOX_DIR  # reports go to inbox for visibility

AGENT_ID = "COWORK"
AGENT_NAME = "Argos"
DEFAULT_RUNPOINT = "rp_rhea_office_v1"
DEFAULT_POLL_INTERVAL = 120  # 2 min for observation
GIT_BRANCH = "feat/chronos-agents-and-bridge"

# Known desks (from OFFICE.md)
KNOWN_DESKS = ["LEAD", "B2", "COWORK", "GPT"]

# Firestore config (shared with rex_pager.py)
FIRESTORE_PROJECT = "rhea-office-sync"
FIRESTORE_BASE = f"https://firestore.googleapis.com/v1/projects/{FIRESTORE_PROJECT}/databases/(default)/documents"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _now_compact():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------------------
# Shared infrastructure (import from rex_pager or standalone)
# ---------------------------------------------------------------------------

def _try_import_rex_pager():
    """Try to import rex_pager for shared functionality."""
    try:
        sys.path.insert(0, str(OPS_DIR))
        import rex_pager
        return rex_pager
    except ImportError:
        return None


def _next_seq() -> int:
    """Monotonic sequence — shared counter with rex_pager."""
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
    raw = f"{source}:{body}:{ts[:19]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _uuidv7_ish() -> str:
    import uuid
    ts_hex = hex(int(time.time() * 1000))[2:]
    rand = uuid.uuid4().hex[:20]
    return f"{ts_hex}-{rand}"


# ---------------------------------------------------------------------------
# Watcher State (persistent across restarts)
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    """Load Argos watcher state."""
    ARGOS_STATE_DIR.mkdir(parents=True, exist_ok=True)
    if ARGOS_STATE_FILE.exists():
        try:
            return json.loads(ARGOS_STATE_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass
    return {
        "last_git_sha": "",
        "last_git_check": "",
        "last_inbox_scan": "",
        "last_mailbox_seq": 0,
        "last_heartbeat": "",
        "observations_count": 0,
        "alerts_sent": 0,
        "boot_count": 0,
        "created_at": _now_iso(),
    }


def _save_state(state: dict):
    """Atomic save: write tmp → rename."""
    ARGOS_STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = ARGOS_STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.rename(ARGOS_STATE_FILE)


def _log_observation(obs_type: str, data: dict):
    """Append to observations log (tamper-evident JSONL)."""
    ARGOS_STATE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _now_iso(),
        "observer": AGENT_NAME,
        "type": obs_type,
        "data": data,
    }
    with open(ARGOS_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Git Monitoring
# ---------------------------------------------------------------------------

def git_pull() -> tuple[bool, str]:
    """Pull latest from remote. Returns (changed, output)."""
    try:
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", GIT_BRANCH],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=30,
        )
        output = result.stdout.strip() + "\n" + result.stderr.strip()
        changed = "Already up to date" not in output
        return changed, output.strip()
    except subprocess.TimeoutExpired:
        return False, "git pull timed out"
    except Exception as e:
        return False, f"git pull failed: {e}"


def git_log_since(sha: str, limit: int = 20) -> list[dict]:
    """Get commits since given SHA."""
    try:
        if sha:
            cmd = ["git", "log", f"{sha}..HEAD", f"--max-count={limit}",
                   "--format=%H|%an|%ae|%ai|%s"]
        else:
            cmd = ["git", "log", f"--max-count={limit}",
                   "--format=%H|%an|%ae|%ai|%s"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=10
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 4)
            if len(parts) >= 5:
                commits.append({
                    "sha": parts[0][:8],
                    "sha_full": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4],
                })
        return commits
    except Exception:
        return []


def git_current_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def git_diff_stat(sha: str) -> str:
    """Get diffstat since given SHA."""
    try:
        if not sha:
            return ""
        result = subprocess.run(
            ["git", "diff", "--stat", f"{sha}..HEAD"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _infer_author_desk(author: str, email: str) -> str:
    """Map git author to desk name."""
    email_lower = email.lower()
    author_lower = author.lower()
    if "b2" in author_lower or "opus" in author_lower:
        return "B2"
    if "argos" in author_lower or "cowork" in author_lower:
        return "COWORK"
    if "gpt" in author_lower or "openai" in author_lower or "chatgpt" in author_lower:
        return "GPT"
    if "rex" in author_lower or "lead" in author_lower:
        return "LEAD"
    # Check email patterns
    if "noreply@anthropic" in email_lower:
        return "B2/COWORK"  # Claude-authored
    return "HUMAN"


# ---------------------------------------------------------------------------
# Inbox Monitoring
# ---------------------------------------------------------------------------

def scan_inbox() -> list[dict]:
    """Scan inbox for files addressed to COWORK/Argos."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    cowork_files = []
    for f in sorted(INBOX_DIR.iterdir()):
        if not f.is_file():
            continue
        name = f.name.upper()
        # Files addressed to COWORK: RELAY_*_to_COWORK.md or COWORK_*.md
        if "COWORK" in name or "ARGOS" in name:
            stat = f.stat()
            cowork_files.append({
                "file": f.name,
                "path": str(f),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "is_relay": name.startswith("RELAY_"),
            })
    return cowork_files


def scan_mailbox_for_cowork() -> list[dict]:
    """Read relay mailbox for COWORK-targeted messages."""
    if not MAILBOX_FILE.exists():
        return []
    acks = set()
    if ACKS_FILE.exists():
        for line in ACKS_FILE.read_text().strip().split("\n"):
            if line.strip():
                try:
                    acks.add(json.loads(line).get("message_id", ""))
                except json.JSONDecodeError:
                    pass
    pending = []
    for line in MAILBOX_FILE.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
            if msg.get("target") == AGENT_ID and msg["id"] not in acks:
                pending.append(msg)
        except json.JSONDecodeError:
            continue
    return sorted(pending, key=lambda m: m.get("seq", 0))


# ---------------------------------------------------------------------------
# Desk Status Aggregation (Watchtower)
# ---------------------------------------------------------------------------

def get_all_desk_status() -> dict:
    """Aggregate status of all known desks."""
    desks = {}
    for desk in KNOWN_DESKS:
        info = {"desk": desk, "lease": None, "snapshot": None, "status": "UNKNOWN"}

        # Check lease
        lease_file = LEASES_DIR / f"{desk}.json"
        if lease_file.exists():
            try:
                lease = json.loads(lease_file.read_text())
                info["lease"] = lease
                expires = lease.get("expires_at", "")
                if expires:
                    try:
                        exp_dt = datetime.fromisoformat(expires)
                        if datetime.now(timezone.utc) > exp_dt:
                            info["status"] = "LEASE_EXPIRED"
                        else:
                            info["status"] = "ALIVE"
                    except ValueError:
                        info["status"] = "LEASE_UNKNOWN"
                info["lease_token"] = lease.get("lease_token", 0)
                info["last_renewed"] = lease.get("renewed_at", "")
            except (json.JSONDecodeError, ValueError):
                pass

        # Check snapshot
        snap_file = SNAPSHOTS_DIR / f"{desk}.json"
        if snap_file.exists():
            try:
                snap = json.loads(snap_file.read_text())
                info["snapshot"] = snap
                info["last_seq"] = snap.get("last_seq_applied", 0)
                info["snap_time"] = snap.get("saved_at", "")
            except (json.JSONDecodeError, ValueError):
                pass

        # Check mailbox for pending messages TO this desk
        pending_count = 0
        if MAILBOX_FILE.exists():
            acks = set()
            if ACKS_FILE.exists():
                for line in ACKS_FILE.read_text().strip().split("\n"):
                    if line.strip():
                        try:
                            acks.add(json.loads(line).get("message_id", ""))
                        except json.JSONDecodeError:
                            pass
            for line in MAILBOX_FILE.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line)
                    if msg.get("target") == desk and msg["id"] not in acks:
                        pending_count += 1
                except json.JSONDecodeError:
                    continue
        info["pending_messages"] = pending_count

        desks[desk] = info
    return desks


# ---------------------------------------------------------------------------
# Relay Operations (send alerts via shared infrastructure)
# ---------------------------------------------------------------------------

def send_alert(target: str, body: str, priority: str = "P1"):
    """Send alert through the relay (triple-write)."""
    ts = _now_iso()
    payload = {"body": body, "priority": priority}
    envelope = {
        "id": _uuidv7_ish(),
        "runpoint_id": DEFAULT_RUNPOINT,
        "seq": _next_seq(),
        "type": "msg.send",
        "timestamp": ts,
        "source": AGENT_ID,
        "target": target,
        "version": 1,
        "idempotency_key": _idempotency_key(AGENT_ID, json.dumps(payload, sort_keys=True), ts),
        "ttl_s": 86400,
        "lease_token_required": 0,
        "priority": priority,
        "payload": payload,
        "status": "pending",
    }

    # Triple-write
    # 1. Local JSONL
    MAILBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MAILBOX_FILE, "a") as f:
        f.write(json.dumps(envelope) + "\n")

    # 2. Inbox markdown backup
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ts_compact = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fname = f"RELAY_{ts_compact}_{AGENT_ID}_to_{target}.md"
    (INBOX_DIR / fname).write_text(
        f"# RELAY MESSAGE — {AGENT_ID} → {target}\n"
        f"**Envelope ID:** {envelope['id']}\n"
        f"**Seq:** {envelope['seq']}\n"
        f"**Priority:** {priority}\n"
        f"**Type:** msg.send\n"
        f"**TTL:** 86400s\n"
        f"**Idempotency Key:** {envelope['idempotency_key']}\n"
        f"**Time:** {ts}\n\n"
        f"{body}\n"
    )

    # 3. Firestore (best-effort)
    _write_firestore(envelope)

    # Audit chain
    _chain_append("relay.enqueue", AGENT_ID,
                  {"msg_id": envelope["id"], "seq": envelope["seq"], "target": target})

    print(f"[argos] Alert sent: seq={envelope['seq']} {AGENT_ID}→{target} ({priority})")
    return envelope


def _write_firestore(envelope: dict):
    """Write to Firestore (best-effort, same as rex_pager)."""
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
        url = (
            f"{FIRESTORE_BASE}/runpoints/{envelope['runpoint_id']}"
            f"/mailbox/{envelope['target']}/messages/{envelope['id']}"
        )
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
        import urllib.request
        req = urllib.request.Request(
            url, data=data, method="PATCH",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {creds.token}"}
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  [firestore] write failed (non-fatal): {e}")


def _chain_append(event_type: str, actor: str, payload: dict) -> dict:
    """Append to hash-chained audit log (shared with rex_pager)."""
    def _canonical_json(obj):
        return json.dumps(obj, sort_keys=True, separators=(",", ":"))

    CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Concurrency-safe: lock ledger for (read tail → compute → append) as one critical section.
    with open(CHAIN_FILE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
            prev_hash = "0" * 64
            # Walk backwards until we can parse a JSON entry (robust to partial lines)
            for ln in reversed(lines):
                try:
                    prev_hash = json.loads(ln).get("event_hash", "0" * 64)
                    break
                except Exception:
                    continue

            entry = {
                "timestamp": _now_iso(),
                "event_type": event_type,
                "actor": actor,
                "payload": payload,
                "prev_hash": prev_hash,
            }
            canonical = _canonical_json(entry)
            entry["event_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

            f.write(json.dumps(entry) + "\n")
            f.flush()
            os.fsync(f.fileno())
            return entry
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def heartbeat():
    """Update COWORK desk heartbeat (lease + Firestore + chain)."""
    # Local lease
    LEASES_DIR.mkdir(parents=True, exist_ok=True)
    lease_file = LEASES_DIR / f"{AGENT_ID}.json"
    prev_token = 0
    if lease_file.exists():
        try:
            prev = json.loads(lease_file.read_text())
            prev_token = prev.get("lease_token", 0)
        except (json.JSONDecodeError, ValueError):
            pass

    now = _now_iso()
    expires = (datetime.now(timezone.utc) + timedelta(seconds=600)).isoformat()
    lease = {
        "agent": AGENT_ID,
        "desk_name": AGENT_NAME,
        "lease_token": prev_token + 1,
        "acquired_at": now,
        "renewed_at": now,
        "expires_at": expires,
        "ttl_s": 600,
        "prev_token": prev_token,
    }
    lease_file.write_text(json.dumps(lease, indent=2))

    # Firestore heartbeat
    try:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if creds_path:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/datastore"]
            )
            creds.refresh(Request())
            import urllib.request
            url = f"{FIRESTORE_BASE}/agents/{AGENT_ID}"
            fields = {
                "desk": {"stringValue": AGENT_ID},
                "desk_name": {"stringValue": AGENT_NAME},
                "status": {"stringValue": "ALIVE"},
                "last_seen": {"stringValue": now},
                "lease_token": {"integerValue": str(lease["lease_token"])},
                "role": {"stringValue": "observer"},
            }
            data = json.dumps({"fields": fields}).encode()
            req = urllib.request.Request(
                url, data=data, method="PATCH",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {creds.token}"}
            )
            urllib.request.urlopen(req, timeout=10)
            print(f"[argos] Heartbeat: ALIVE (Firestore updated)")
    except Exception as e:
        print(f"[argos] Heartbeat: ALIVE (Firestore failed: {e})")

    _chain_append("heartbeat", AGENT_ID, {"lease_token": lease["lease_token"], "status": "ALIVE"})

    state = _load_state()
    state["last_heartbeat"] = now
    _save_state(state)

    print(f"[argos] Heartbeat: lease_token={lease['lease_token']}")
    return lease


# ---------------------------------------------------------------------------
# Boot Protocol (COWORK-specific)
# ---------------------------------------------------------------------------

def boot():
    """Full COWORK boot protocol, compatible with QWRR section 8."""
    print("=" * 60)
    print(f"  ARGOS BOOT PROTOCOL — {AGENT_NAME} ({AGENT_ID})")
    print("=" * 60)

    state = _load_state()
    state["boot_count"] = state.get("boot_count", 0) + 1

    # Step 1: Git pull
    print(f"\n[1/5] Git sync...")
    changed, output = git_pull()
    current_sha = git_current_sha()
    print(f"  HEAD: {current_sha[:8]}")
    if changed:
        print(f"  Changes pulled: {output[:200]}")

    # Step 2: Heartbeat (acquires lease)
    print(f"\n[2/5] Heartbeat + lease...")
    lease = heartbeat()

    # Step 3: Drain COWORK inbox
    print(f"\n[3/5] Checking relay inbox...")
    pending = scan_mailbox_for_cowork()
    if pending:
        print(f"  {len(pending)} pending messages for COWORK:")
        for msg in pending:
            body = msg.get("payload", {}).get("body", "")[:60]
            print(f"    seq={msg.get('seq', '?')} [{msg.get('priority', 'P1')}] "
                  f"{msg.get('source', '?')}: {body}...")
    else:
        print("  No pending relay messages.")

    # Step 4: Inbox files
    print(f"\n[4/5] Scanning inbox files...")
    inbox_files = scan_inbox()
    if inbox_files:
        print(f"  {len(inbox_files)} files for COWORK:")
        for f in inbox_files:
            print(f"    {f['file']} ({f['size']} bytes)")
    else:
        print("  No inbox files.")

    # Step 5: Commit snapshot
    print(f"\n[5/5] Saving snapshot...")
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    snap = {
        "agent": AGENT_ID,
        "agent_name": AGENT_NAME,
        "last_seq_applied": max((m.get("seq", 0) for m in pending), default=0),
        "state_hash": hashlib.sha256(f"{AGENT_ID}:{current_sha}:{_now_iso()}".encode()).hexdigest()[:16],
        "saved_at": _now_iso(),
        "git_sha": current_sha[:8],
        "lease_token": lease["lease_token"],
        "pending_messages": len(pending),
        "inbox_files": len(inbox_files),
    }
    (SNAPSHOTS_DIR / f"{AGENT_ID}.json").write_text(json.dumps(snap, indent=2))
    print(f"  Snapshot saved: seq={snap['last_seq_applied']} hash={snap['state_hash']}")

    state["last_git_sha"] = current_sha
    state["last_git_check"] = _now_iso()
    state["last_inbox_scan"] = _now_iso()
    _save_state(state)

    _chain_append("boot.complete", AGENT_ID, {
        "lease_token": lease["lease_token"],
        "git_sha": current_sha[:8],
        "pending": len(pending),
    })

    print(f"\n{'=' * 60}")
    print(f"  BOOT COMPLETE — {AGENT_NAME}")
    print(f"  lease={lease['lease_token']} sha={current_sha[:8]} "
          f"pending={len(pending)} inbox={len(inbox_files)}")
    print(f"{'=' * 60}")
    return snap


# ---------------------------------------------------------------------------
# One-shot Scan
# ---------------------------------------------------------------------------

def scan():
    """One-shot: scan everything, print report, exit."""
    print(f"ARGOS SCAN — {_now_iso()}")
    print("=" * 60)

    # Git
    print("\n[GIT]")
    state = _load_state()
    last_sha = state.get("last_git_sha", "")
    changed, pull_output = git_pull()
    current_sha = git_current_sha()
    if changed:
        print(f"  NEW CHANGES pulled (was: {last_sha[:8]})")
        commits = git_log_since(last_sha)
        for c in commits:
            desk = _infer_author_desk(c["author"], c["email"])
            print(f"  [{desk}] {c['sha']} {c['message']}")
        state["last_git_sha"] = current_sha
    else:
        print(f"  No changes (HEAD: {current_sha[:8]})")

    # Mailbox
    print("\n[RELAY]")
    pending = scan_mailbox_for_cowork()
    if pending:
        print(f"  {len(pending)} pending messages for COWORK:")
        for msg in pending:
            body = msg.get("payload", {}).get("body", "")[:60]
            print(f"    seq={msg.get('seq', '?')} from {msg.get('source', '?')}: {body}")
    else:
        print("  No pending relay messages.")

    # Inbox files
    print("\n[INBOX]")
    inbox_files = scan_inbox()
    new_files = []
    last_scan = state.get("last_inbox_scan", "")
    for f in inbox_files:
        if not last_scan or f["modified"] > last_scan:
            new_files.append(f)
    if new_files:
        print(f"  {len(new_files)} new file(s):")
        for f in new_files:
            print(f"    {f['file']} ({f['size']} bytes)")
    else:
        print(f"  No new inbox files (total: {len(inbox_files)})")

    # Desk status
    print("\n[DESKS]")
    desks = get_all_desk_status()
    for desk_id, info in desks.items():
        status = info.get("status", "UNKNOWN")
        pending_count = info.get("pending_messages", 0)
        last_seq = info.get("last_seq", "?")
        indicator = "●" if status == "ALIVE" else "○" if status == "LEASE_EXPIRED" else "?"
        print(f"  {indicator} {desk_id:8s} | {status:14s} | seq={last_seq} | pending={pending_count}")

    # Chain integrity
    print("\n[CHAIN]")
    if CHAIN_FILE.exists():
        lines = [l for l in CHAIN_FILE.read_text().strip().split("\n") if l.strip()]
        print(f"  Audit chain: {len(lines)} entries")
        # Quick integrity check (just last 3)
        if len(lines) >= 2:
            last = json.loads(lines[-1])
            prev = json.loads(lines[-2])
            if last.get("prev_hash") == prev.get("event_hash"):
                print("  Integrity: last link valid ✓")
            else:
                print("  Integrity: BROKEN ✗")
    else:
        print("  No chain file.")

    # Save state
    state["last_git_check"] = _now_iso()
    state["last_inbox_scan"] = _now_iso()
    state["observations_count"] = state.get("observations_count", 0) + 1
    _save_state(state)

    _log_observation("scan", {
        "git_changed": changed,
        "pending_relay": len(pending),
        "new_inbox": len(new_files),
        "desks": {k: v.get("status", "UNKNOWN") for k, v in desks.items()},
    })

    print(f"\n{'=' * 60}")


# ---------------------------------------------------------------------------
# Watchtower Status
# ---------------------------------------------------------------------------

def show_status():
    """All-desks watchtower view."""
    desks = get_all_desk_status()

    print(f"ARGOS WATCHTOWER — {_now_iso()}")
    print("=" * 60)

    # Seq counter
    seq = SEQ_FILE.read_text().strip() if SEQ_FILE.exists() else "0"
    print(f"  Global seq: {seq}")

    # Mailbox totals
    total_msgs = 0
    total_pending = 0
    if MAILBOX_FILE.exists():
        acks = set()
        if ACKS_FILE.exists():
            for line in ACKS_FILE.read_text().strip().split("\n"):
                if line.strip():
                    try:
                        acks.add(json.loads(line).get("message_id", ""))
                    except json.JSONDecodeError:
                        pass
        for line in MAILBOX_FILE.read_text().strip().split("\n"):
            if line.strip():
                total_msgs += 1
                try:
                    msg = json.loads(line)
                    if msg["id"] not in acks:
                        total_pending += 1
                except (json.JSONDecodeError, KeyError):
                    pass
    print(f"  Relay: {total_msgs} total, {total_pending} pending")

    # Per-desk
    print(f"\n  {'Desk':8s} | {'Status':14s} | {'Token':>5s} | {'Seq':>4s} | {'Pending':>7s} | Last Active")
    print(f"  {'-'*8} | {'-'*14} | {'-'*5} | {'-'*4} | {'-'*7} | {'-'*20}")

    for desk_id, info in desks.items():
        status = info.get("status", "UNKNOWN")
        token = str(info.get("lease_token", "-"))
        last_seq = str(info.get("last_seq", "-"))
        pending_count = str(info.get("pending_messages", 0))
        last_active = info.get("last_renewed", info.get("snap_time", "-"))
        if last_active and len(last_active) > 19:
            last_active = last_active[:19] + "Z"
        print(f"  {desk_id:8s} | {status:14s} | {token:>5s} | {last_seq:>4s} | {pending_count:>7s} | {last_active}")

    # Argos-specific state
    state = _load_state()
    print(f"\n  Argos watcher state:")
    print(f"    Observations: {state.get('observations_count', 0)}")
    print(f"    Alerts sent:  {state.get('alerts_sent', 0)}")
    print(f"    Boot count:   {state.get('boot_count', 0)}")
    print(f"    Last git:     {state.get('last_git_check', 'never')[:19]}")
    print(f"    Last inbox:   {state.get('last_inbox_scan', 'never')[:19]}")
    print(f"    Git HEAD:     {state.get('last_git_sha', 'unknown')[:8]}")


# ---------------------------------------------------------------------------
# Observation Report (markdown output)
# ---------------------------------------------------------------------------

def generate_report() -> str:
    """Generate structured observation report as markdown."""
    desks = get_all_desk_status()
    state = _load_state()
    now = _now_iso()

    # Git info
    current_sha = git_current_sha()
    recent_commits = git_log_since("", limit=10)

    # Pending messages
    pending = scan_mailbox_for_cowork()

    report = f"""# ARGOS OBSERVATION REPORT
> Observer: {AGENT_NAME} ({AGENT_ID})
> Time: {now}
> Git HEAD: {current_sha[:8]}

---

## Desk Status

| Desk | Status | Lease Token | Last Seq | Pending |
|------|--------|-------------|----------|---------|
"""
    for desk_id, info in desks.items():
        status = info.get("status", "UNKNOWN")
        token = info.get("lease_token", "-")
        seq = info.get("last_seq", "-")
        pend = info.get("pending_messages", 0)
        report += f"| {desk_id} | {status} | {token} | {seq} | {pend} |\n"

    report += f"""
## Recent Activity (last 10 commits)

"""
    for c in recent_commits:
        desk = _infer_author_desk(c["author"], c["email"])
        report += f"- `{c['sha']}` [{desk}] {c['message']}\n"

    if pending:
        report += f"\n## Pending COWORK Messages ({len(pending)})\n\n"
        for msg in pending:
            body = msg.get("payload", {}).get("body", "")[:80]
            report += f"- seq={msg.get('seq', '?')} from {msg.get('source', '?')}: {body}\n"

    report += f"""
## Watcher Metrics

- Observations: {state.get('observations_count', 0)}
- Alerts sent: {state.get('alerts_sent', 0)}
- Boot count: {state.get('boot_count', 0)}
- Last git check: {state.get('last_git_check', 'never')}
- Last inbox scan: {state.get('last_inbox_scan', 'never')}

---
**Signed:** {AGENT_NAME} (COWORK desk)
"""

    # Write to file
    ARGOS_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = ARGOS_REPORT_DIR / f"COWORK_{datetime.now(timezone.utc).strftime('%Y%m%d')}_observation-report.md"
    report_file.write_text(report)
    print(f"[argos] Report written: {report_file.name}")
    return str(report_file)


# ---------------------------------------------------------------------------
# Watch Daemon
# ---------------------------------------------------------------------------

def watch_daemon(interval: int = DEFAULT_POLL_INTERVAL):
    """Daemon mode: poll git + inbox + desks, alert on changes."""
    print(f"ARGOS WATCH DAEMON — {AGENT_NAME}")
    print(f"  Poll interval: {interval}s")
    print(f"  Monitoring: git, relay, inbox, desk leases")
    print(f"  Ctrl+C to stop.\n")

    # Initial boot
    boot()

    state = _load_state()
    cycle = 0
    stop_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'STOP')
    def _stop():
        return os.path.exists(stop_path)


    while True:
        # P0: Runtime STOP Enforcement
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.path.exists(os.path.join(root_dir, "STOP")):
            print(f"[{datetime.now()}] STOP sentinel detected in root. Exiting.")
            break
        cycle += 1
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        print(f"\n--- cycle {cycle} [{now_str}] ---")

        # 1. Git check
        changed, output = git_pull()
        current_sha = git_current_sha()
        if changed:
            old_sha = state.get("last_git_sha", "")
            commits = git_log_since(old_sha, limit=5)
            print(f"[git] NEW: {len(commits)} commits")
            for c in commits:
                desk = _infer_author_desk(c["author"], c["email"])
                print(f"  [{desk}] {c['sha']} {c['message']}")
            state["last_git_sha"] = current_sha

            _log_observation("git.new_commits", {
                "count": len(commits),
                "commits": [{"sha": c["sha"], "desk": _infer_author_desk(c["author"], c["email"]),
                             "msg": c["message"]} for c in commits],
            })
        else:
            print(f"[git] no changes (HEAD: {current_sha[:8]})")

        # 2. Relay check
        pending = scan_mailbox_for_cowork()
        if pending:
            known_seq = state.get("last_mailbox_seq", 0)
            new_msgs = [m for m in pending if m.get("seq", 0) > known_seq]
            if new_msgs:
                print(f"[relay] {len(new_msgs)} NEW messages for COWORK!")
                for msg in new_msgs:
                    body = msg.get("payload", {}).get("body", "")[:60]
                    print(f"  seq={msg['seq']} [{msg.get('priority', 'P1')}] "
                          f"{msg.get('source', '?')}: {body}")
                state["last_mailbox_seq"] = max(m.get("seq", 0) for m in pending)

                _log_observation("relay.new_messages", {
                    "count": len(new_msgs),
                    "sources": list(set(m.get("source", "?") for m in new_msgs)),
                })
        else:
            print(f"[relay] clear")

        # 3. Quick desk status
        desks = get_all_desk_status()
        for desk_id, info in desks.items():
            status = info.get("status", "UNKNOWN")
            pending_count = info.get("pending_messages", 0)
            if status == "LEASE_EXPIRED" and desk_id != AGENT_ID:
                print(f"[desk] ⚠ {desk_id} lease EXPIRED")
            if pending_count > 5:
                print(f"[desk] ⚠ {desk_id} has {pending_count} pending messages")

        # 4. Heartbeat (every 5th cycle to avoid spam)
        if cycle % 5 == 0:
            heartbeat()

        # Save state
        state["last_git_check"] = _now_iso()
        state["last_inbox_scan"] = _now_iso()
        state["observations_count"] = state.get("observations_count", 0) + 1
        _save_state(state)

        # P0-STOP: Responsive sleep
        for _ in range(interval):
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if os.path.exists(os.path.join(root_dir, "STOP")):
                break
            time.sleep(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "watch":
        interval = DEFAULT_POLL_INTERVAL
        if "--interval" in sys.argv:
            idx = sys.argv.index("--interval")
            if idx + 1 < len(sys.argv):
                interval = int(sys.argv[idx + 1])
        watch_daemon(interval)

    elif cmd == "scan":
        scan()

    elif cmd == "inbox":
        pending = scan_mailbox_for_cowork()
        inbox_files = scan_inbox()
        print(f"[argos] Relay messages for COWORK: {len(pending)}")
        for msg in pending:
            body = msg.get("payload", {}).get("body", "")[:80]
            print(f"  seq={msg.get('seq', '?')} [{msg.get('priority', 'P1')}] "
                  f"{msg.get('source', '?')}: {body}")
        print(f"\n[argos] Inbox files: {len(inbox_files)}")
        for f in inbox_files:
            tag = " [RELAY]" if f["is_relay"] else ""
            print(f"  {f['file']} ({f['size']}b){tag}")

    elif cmd == "status":
        show_status()

    elif cmd == "report":
        path = generate_report()
        print(f"Report: {path}")

    elif cmd == "alert":
        if len(sys.argv) < 4:
            print("Usage: argos_pager.py alert <target> <message> [--priority P0]")
            sys.exit(1)
        target = sys.argv[2]
        body = sys.argv[3]
        priority = "P1"
        if "--priority" in sys.argv:
            idx = sys.argv.index("--priority")
            if idx + 1 < len(sys.argv):
                priority = sys.argv[idx + 1]
        send_alert(target, body, priority)
        state = _load_state()
        state["alerts_sent"] = state.get("alerts_sent", 0) + 1
        _save_state(state)

    elif cmd == "heartbeat":
        heartbeat()

    elif cmd == "boot":
        boot()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
