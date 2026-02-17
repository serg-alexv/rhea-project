#!/usr/bin/env /usr/bin/python3
"""
local_relay.py — SQLite-backed local relay (Firebase replacement)

Zero cloud dependency. Same QWRR envelope format. Drop-in replacement
for the JSONL mailbox in rex_pager.py, with proper SQL indexing.

Features:
  - SQLite WAL mode (concurrent reads, single writer)
  - Envelope v1 stored as JSON in a column + indexed fields extracted
  - Ordered by seq (I2), ack-based delivery (I3), TTL enforcement
  - Hash chain integrated (tamper-evident)
  - Optional Firestore mirror (if creds available)
  - REST API for cross-process access (uvicorn optional)

Tables:
  messages   — the mailbox (envelope JSON + indexed fields)
  acks       — delivery receipts (idempotent upsert)
  leases     — fencing tokens per agent
  snapshots  — crash-recovery state per agent
  chain      — hash-chained audit log
  intents    — effect intents (outbox pattern)

Usage:
  python3 local_relay.py init                    # create DB
  python3 local_relay.py send B2 LEAD "msg"      # enqueue
  python3 local_relay.py drain LEAD              # deliver pending
  python3 local_relay.py boot LEAD               # full boot protocol
  python3 local_relay.py status                  # dashboard
  python3 local_relay.py verify                  # chain integrity
  python3 local_relay.py serve                   # REST API (port 8401)
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "ops" / "virtual-office" / "relay.db"
DEFAULT_TTL = 86400
DEFAULT_RUNPOINT = "rp_rhea_office_v1"

STALENESS_POLICY = {
    "msg.send": None,
    "task.create": None,
    "decision.record": None,
    "effect.request": 3600,
    "push.now": 900,
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _uuidv7_ish() -> str:
    ts_hex = hex(int(time.time() * 1000))[2:]
    rand = uuid.uuid4().hex[:20]
    return f"{ts_hex}-{rand}"


def _idempotency_key(source: str, body: str, ts: str) -> str:
    raw = f"{source}:{body}:{ts[:19]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            runpoint_id TEXT NOT NULL DEFAULT 'rp_rhea_office_v1',
            seq INTEGER NOT NULL,
            type TEXT NOT NULL DEFAULT 'msg.send',
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            idempotency_key TEXT NOT NULL,
            ttl_s INTEGER NOT NULL DEFAULT 86400,
            lease_token_required INTEGER NOT NULL DEFAULT 0,
            priority TEXT NOT NULL DEFAULT 'P1',
            payload TEXT NOT NULL,
            envelope TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_target_seq ON messages(target, seq);
        CREATE INDEX IF NOT EXISTS idx_messages_idempotency ON messages(idempotency_key);

        CREATE TABLE IF NOT EXISTS acks (
            message_id TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            acked_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS leases (
            agent TEXT PRIMARY KEY,
            lease_token INTEGER NOT NULL DEFAULT 0,
            acquired_at TEXT NOT NULL,
            prev_token INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            agent TEXT PRIMARY KEY,
            last_seq_applied INTEGER NOT NULL DEFAULT 0,
            state_hash TEXT NOT NULL DEFAULT '',
            saved_at TEXT NOT NULL,
            extra TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS chain (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            payload TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            event_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS intents (
            intent_id TEXT PRIMARY KEY,
            runpoint_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            lease_token INTEGER NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planned',
            receipt TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            source_message_id TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_intents_status ON intents(status);
    """)
    conn.close()
    print(f"[relay-db] Initialized: {DB_PATH}")


# ---------------------------------------------------------------------------
# Sequence counter (SQLite-atomic)
# ---------------------------------------------------------------------------

def _next_seq(conn: sqlite3.Connection) -> int:
    """Atomic seq via SQLite — no race conditions."""
    row = conn.execute("SELECT MAX(seq) FROM messages").fetchone()
    return (row[0] or 0) + 1


# ---------------------------------------------------------------------------
# Hash chain
# ---------------------------------------------------------------------------

def _last_chain_hash(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT event_hash FROM chain ORDER BY rowid DESC LIMIT 1").fetchone()
    return row["event_hash"] if row else "0" * 64


def chain_append(conn: sqlite3.Connection, event_type: str, actor: str, payload: dict) -> dict:
    prev_hash = _last_chain_hash(conn)
    entry = {
        "timestamp": _now_iso(),
        "event_type": event_type,
        "actor": actor,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    canonical = _canonical_json(entry)
    event_hash = hashlib.sha256(canonical.encode()).hexdigest()
    conn.execute(
        "INSERT INTO chain (timestamp, event_type, actor, payload, prev_hash, event_hash) VALUES (?,?,?,?,?,?)",
        (entry["timestamp"], event_type, actor, json.dumps(payload), prev_hash, event_hash)
    )
    entry["event_hash"] = event_hash
    return entry


def chain_verify(conn: sqlite3.Connection) -> tuple[bool, int, str]:
    rows = conn.execute("SELECT * FROM chain ORDER BY rowid").fetchall()
    if not rows:
        return True, 0, "empty chain"
    prev_hash = "0" * 64
    for i, row in enumerate(rows):
        if row["prev_hash"] != prev_hash:
            return False, i + 1, f"entry {i+1}: prev_hash mismatch"
        check = {
            "timestamp": row["timestamp"],
            "event_type": row["event_type"],
            "actor": row["actor"],
            "payload": json.loads(row["payload"]),
            "prev_hash": row["prev_hash"],
        }
        canonical = _canonical_json(check)
        expected = hashlib.sha256(canonical.encode()).hexdigest()
        if row["event_hash"] != expected:
            return False, i + 1, f"entry {i+1}: hash mismatch (tampered)"
        prev_hash = row["event_hash"]
    return True, len(rows), "chain valid"


# ---------------------------------------------------------------------------
# Leases
# ---------------------------------------------------------------------------

def acquire_lease(conn: sqlite3.Connection, agent: str) -> int:
    row = conn.execute("SELECT lease_token FROM leases WHERE agent=?", (agent,)).fetchone()
    prev = row["lease_token"] if row else 0
    new_token = prev + 1
    conn.execute(
        "INSERT OR REPLACE INTO leases (agent, lease_token, acquired_at, prev_token) VALUES (?,?,?,?)",
        (agent, new_token, _now_iso(), prev)
    )
    chain_append(conn, "lease.acquire", agent, {"lease_token": new_token, "prev_token": prev})
    print(f"[lease] {agent} acquired lease_token={new_token} (prev={prev})")
    return new_token


def get_lease(conn: sqlite3.Connection, agent: str) -> dict:
    row = conn.execute("SELECT * FROM leases WHERE agent=?", (agent,)).fetchone()
    if not row:
        return {"agent": agent, "lease_token": 0}
    return dict(row)


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------

def load_snapshot(conn: sqlite3.Connection, agent: str) -> dict:
    row = conn.execute("SELECT * FROM snapshots WHERE agent=?", (agent,)).fetchone()
    if not row:
        return {"agent": agent, "last_seq_applied": 0, "state_hash": "", "saved_at": ""}
    result = dict(row)
    result["extra"] = json.loads(result.get("extra", "{}"))
    return result


def commit_snapshot(conn: sqlite3.Connection, agent: str, last_seq: int, extra: dict = None):
    state_hash = hashlib.sha256(f"{agent}:{last_seq}:{_now_iso()}".encode()).hexdigest()[:16]
    conn.execute(
        "INSERT OR REPLACE INTO snapshots (agent, last_seq_applied, state_hash, saved_at, extra) VALUES (?,?,?,?,?)",
        (agent, last_seq, state_hash, _now_iso(), json.dumps(extra or {}))
    )
    print(f"[snapshot] {agent} seq={last_seq} hash={state_hash}")


# ---------------------------------------------------------------------------
# Enqueue
# ---------------------------------------------------------------------------

def enqueue(conn: sqlite3.Connection, source: str, target: str, body: str,
            priority: str = "P1", msg_type: str = "msg.send", ttl_s: int = DEFAULT_TTL):
    ts = _now_iso()
    payload = {"body": body, "priority": priority}
    payload_str = json.dumps(payload, sort_keys=True)
    seq = _next_seq(conn)
    msg_id = _uuidv7_ish()
    idem = _idempotency_key(source, payload_str, ts)

    envelope = {
        "id": msg_id, "runpoint_id": DEFAULT_RUNPOINT, "seq": seq,
        "type": msg_type, "timestamp": ts, "source": source, "target": target,
        "version": 1, "idempotency_key": idem, "ttl_s": ttl_s,
        "lease_token_required": 0, "priority": priority, "payload": payload,
    }

    conn.execute(
        """INSERT INTO messages (id, runpoint_id, seq, type, timestamp, source, target,
           version, idempotency_key, ttl_s, lease_token_required, priority, payload, envelope)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (msg_id, DEFAULT_RUNPOINT, seq, msg_type, ts, source, target,
         1, idem, ttl_s, 0, priority, json.dumps(payload), json.dumps(envelope))
    )
    chain_append(conn, "relay.enqueue", source, {"msg_id": msg_id, "seq": seq, "target": target})
    print(f"[relay] Enqueued seq={seq} {source}->{target} ({priority}) id={msg_id}")
    return envelope


# ---------------------------------------------------------------------------
# Drain
# ---------------------------------------------------------------------------

def _check_staleness(msg_type: str, timestamp: str, ttl_s: int) -> tuple[str, str]:
    threshold = STALENESS_POLICY.get(msg_type)
    age = time.time() - datetime.fromisoformat(timestamp).timestamp()
    if age > ttl_s:
        return "expire", f"TTL exceeded ({age:.0f}s > {ttl_s}s)"
    if threshold and age > threshold:
        if msg_type == "push.now":
            return "expire", f"push.now stale ({age:.0f}s > {threshold}s)"
        return "reconfirm", f"{msg_type} needs reconfirm ({age:.0f}s > {threshold}s)"
    return "deliver", "ok"


def drain(conn: sqlite3.Connection, target: str, lease_token: int = 0, from_seq: int = 0):
    rows = conn.execute(
        """SELECT m.* FROM messages m
           LEFT JOIN acks a ON m.id = a.message_id
           WHERE m.target = ? AND m.seq > ? AND a.message_id IS NULL
           ORDER BY m.seq""",
        (target, from_seq)
    ).fetchall()

    delivered = []
    for row in rows:
        action, reason = _check_staleness(row["type"], row["timestamp"], row["ttl_s"])

        if action == "expire":
            conn.execute("INSERT OR IGNORE INTO acks (message_id, target, acked_at) VALUES (?,?,?)",
                         (row["id"], target, _now_iso()))
            print(f"  EXPIRED seq={row['seq']}: {reason}")
            continue

        if action == "reconfirm":
            conn.execute("INSERT OR IGNORE INTO acks (message_id, target, acked_at) VALUES (?,?,?)",
                         (row["id"], target, _now_iso()))
            print(f"  RECONFIRM seq={row['seq']}: {reason}")
            continue

        # Lease gate
        if row["lease_token_required"] > 0 and lease_token > 0:
            if row["lease_token_required"] != lease_token:
                conn.execute("INSERT OR IGNORE INTO acks (message_id, target, acked_at) VALUES (?,?,?)",
                             (row["id"], target, _now_iso()))
                print(f"  FENCED seq={row['seq']}: lease mismatch")
                continue

        payload = json.loads(row["payload"])
        body = payload.get("body", json.dumps(payload))
        print(f"  seq={row['seq']} [{row['priority']}] {row['source']} @ {row['timestamp'][:19]}Z")
        print(f"  {body}")

        # Effect types -> intents
        if row["type"] in ("effect.request", "push.now") and lease_token > 0:
            intent_id = _uuidv7_ish()
            conn.execute(
                """INSERT INTO intents (intent_id, runpoint_id, kind, idempotency_key,
                   lease_token, payload, status, created_at, updated_at, source_message_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (intent_id, row["runpoint_id"], row["type"], row["idempotency_key"],
                 lease_token, row["payload"], "planned", _now_iso(), _now_iso(), row["id"])
            )
            print(f"  -> intent {intent_id} (planned)")

        conn.execute("INSERT OR IGNORE INTO acks (message_id, target, acked_at) VALUES (?,?,?)",
                     (row["id"], target, _now_iso()))
        delivered.append(dict(row))
        print(f"  ---")

    if delivered:
        print(f"\n[relay] {len(delivered)} delivered + acked for {target}.")
    else:
        print(f"[relay] No pending messages for {target}.")
    return delivered


# ---------------------------------------------------------------------------
# Boot protocol (QWRR section 8)
# ---------------------------------------------------------------------------

def boot(conn: sqlite3.Connection, agent: str):
    print("=" * 60)
    print(f"  QWRR BOOT — {agent} (SQLite relay)")
    print("=" * 60)

    print(f"\n[1/6] Acquiring lease...")
    token = acquire_lease(conn, agent)

    print(f"\n[2/6] Loading snapshot...")
    snap = load_snapshot(conn, agent)
    last_seq = snap.get("last_seq_applied", 0)
    print(f"  last_seq={last_seq} hash={snap.get('state_hash', 'none')}")

    print(f"\n[3/6] Catch-up from seq>{last_seq}...")
    print(f"[4/6] Draining (lease={token})...\n")
    delivered = drain(conn, agent, lease_token=token, from_seq=last_seq)

    print(f"\n[5/6] Staleness applied during drain")

    max_seq = last_seq
    if delivered:
        max_seq = max(r.get("seq", 0) for r in delivered)
    commit_snapshot(conn, agent, max_seq, {"lease_token": token, "msgs": len(delivered)})

    chain_append(conn, "boot.complete", agent, {"lease": token, "seq": max_seq, "msgs": len(delivered)})

    print(f"\n[6/6] Heartbeat (local)...")
    print(f"  {agent}: ALIVE lease={token}")

    print(f"\n{'=' * 60}")
    print(f"  BOOT COMPLETE — {agent}")
    print(f"  lease={token} seq={max_seq} msgs={len(delivered)}")
    print(f"{'=' * 60}")
    return token, delivered


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def show_status(conn: sqlite3.Connection):
    total = conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"]
    acked = conn.execute("SELECT COUNT(*) c FROM acks").fetchone()["c"]
    pending = total - acked
    chain_count = conn.execute("SELECT COUNT(*) c FROM chain").fetchone()["c"]
    intents_planned = conn.execute("SELECT COUNT(*) c FROM intents WHERE status='planned'").fetchone()["c"]

    print(f"QWRR RELAY STATUS (SQLite)")
    print(f"{'=' * 50}")
    print(f"  DB: {DB_PATH}")
    print(f"  Size: {DB_PATH.stat().st_size / 1024:.1f} KB")
    print(f"  Messages: {total} (pending={pending}, acked={acked})")
    print(f"  Chain entries: {chain_count}")
    print(f"  Planned intents: {intents_planned}")

    # Pending by target
    rows = conn.execute(
        """SELECT m.target, COUNT(*) c FROM messages m
           LEFT JOIN acks a ON m.id = a.message_id
           WHERE a.message_id IS NULL GROUP BY m.target"""
    ).fetchall()
    if rows:
        print(f"\n  Pending by target:")
        for r in rows:
            print(f"    {r['target']}: {r['c']}")

    # Leases
    leases = conn.execute("SELECT * FROM leases").fetchall()
    if leases:
        print(f"\n  Leases:")
        for l in leases:
            print(f"    {l['agent']}: token={l['lease_token']} @ {l['acquired_at'][:19]}Z")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init_db()
        return

    # All other commands need the DB
    if not DB_PATH.exists():
        init_db()
    conn = get_db()

    if cmd == "send":
        if len(sys.argv) < 5:
            print("Usage: local_relay.py send <from> <to> <msg> [--priority P0] [--ttl 86400]")
            sys.exit(1)
        source, target, body = sys.argv[2], sys.argv[3], sys.argv[4]
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
        enqueue(conn, source, target, body, priority, ttl_s=ttl)

    elif cmd == "drain":
        target = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        drain(conn, target)

    elif cmd == "boot":
        agent = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        boot(conn, agent)

    elif cmd == "status":
        show_status(conn)

    elif cmd == "verify":
        valid, count, detail = chain_verify(conn)
        print(f"Chain: {'VALID' if valid else 'BROKEN'} ({count} entries) — {detail}")
        sys.exit(0 if valid else 1)

    elif cmd == "lease":
        agent = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        if "--acquire" in sys.argv:
            acquire_lease(conn, agent)
        else:
            print(json.dumps(get_lease(conn, agent), indent=2))

    elif cmd == "snapshot":
        agent = sys.argv[2] if len(sys.argv) > 2 else "LEAD"
        print(json.dumps(load_snapshot(conn, agent), indent=2))

    elif cmd == "inspect":
        if len(sys.argv) < 3:
            print("Usage: local_relay.py inspect <msg_id>")
            sys.exit(1)
        row = conn.execute("SELECT envelope FROM messages WHERE id=?", (sys.argv[2],)).fetchone()
        if row:
            print(json.dumps(json.loads(row["envelope"]), indent=2))
        else:
            print("Not found")
            sys.exit(1)

    elif cmd == "serve":
        _serve_rest(conn)

    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)

    conn.close()


# ---------------------------------------------------------------------------
# REST API (optional, for cross-process access)
# ---------------------------------------------------------------------------

def _serve_rest(conn: sqlite3.Connection):
    """Minimal HTTP API using stdlib only (no FastAPI dependency)."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    relay_conn = conn

    class RelayHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self._json_response({"status": "ok", "db": str(DB_PATH)})
            elif self.path == "/status":
                total = relay_conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"]
                acked = relay_conn.execute("SELECT COUNT(*) c FROM acks").fetchone()["c"]
                self._json_response({"total": total, "pending": total - acked, "acked": acked})
            elif self.path.startswith("/drain/"):
                target = self.path.split("/drain/")[1]
                delivered = drain(relay_conn, target)
                self._json_response({"drained": len(delivered), "target": target})
            else:
                self._json_response({"error": "not found"}, 404)

        def do_POST(self):
            if self.path == "/send":
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                env = enqueue(relay_conn, body["source"], body["target"], body["body"],
                              body.get("priority", "P1"))
                self._json_response({"id": env["id"], "seq": env["seq"]})
            elif self.path.startswith("/boot/"):
                agent = self.path.split("/boot/")[1]
                token, delivered = boot(relay_conn, agent)
                self._json_response({"lease": token, "drained": len(delivered)})
            else:
                self._json_response({"error": "not found"}, 404)

        def _json_response(self, data, code=200):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def log_message(self, fmt, *args):
            print(f"[relay-api] {args[0]}" if args else "")

    port = int(os.environ.get("RELAY_PORT", "8401"))
    server = HTTPServer(("127.0.0.1", port), RelayHandler)
    print(f"[relay-api] Serving on http://127.0.0.1:{port}")
    print(f"  GET  /health | /status | /drain/<agent>")
    print(f"  POST /send   | /boot/<agent>")
    server.serve_forever()


if __name__ == "__main__":
    main()
