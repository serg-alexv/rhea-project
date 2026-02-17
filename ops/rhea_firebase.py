#!/usr/bin/env /usr/bin/python3
"""
Rhea Firebase Office — Inter-agent communication layer.
Uses Firestore REST API (no gRPC dependency).

Usage:
  python3 ops/rhea_firebase.py heartbeat <desk> <status>
  python3 ops/rhea_firebase.py send <from_desk> <to_desk> <message>
  python3 ops/rhea_firebase.py inbox <desk>
  python3 ops/rhea_firebase.py gem <id> <text> <source> <topic>
  python3 ops/rhea_firebase.py incident <id> <symptom> <status>
  python3 ops/rhea_firebase.py status
  python3 ops/rhea_firebase.py health
"""
import sys
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import re

PROJ = "rhea-office-sync"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJ}/databases/(default)/documents"
LOG_PATH = Path(__file__).parent.parent / "logs" / "firebase_calls.jsonl"

_SECRET_RE = [
    (re.compile(r'AIzaSy[A-Za-z0-9_-]{33}'), '[REDACTED]'),
    (re.compile(r'sk-ant-[A-Za-z0-9_-]{20,}'), '[REDACTED]'),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), '[REDACTED]'),
    (re.compile(r'hf_[A-Za-z0-9]{20,}'), '[REDACTED]'),
    (re.compile(r'ya29\.[A-Za-z0-9_-]{50,}'), '[REDACTED]'),
]

def _redact(text):
    for pat, rep in _SECRET_RE:
        text = pat.sub(rep, text)
    return text

# --- Error mapping ---
ERROR_MAP = {
    400: "BAD_REQUEST — malformed payload or invalid field type",
    401: "UNAUTHENTICATED — Firestore rules block this or auth token expired",
    403: "PERMISSION_DENIED — Firestore security rules reject this operation",
    404: "NOT_FOUND — collection or document does not exist",
    409: "CONFLICT — document already exists (use PATCH not POST)",
    429: "RESOURCE_EXHAUSTED — Firestore rate limit hit, backoff needed",
    500: "INTERNAL — Firestore server error, retry with backoff",
    503: "UNAVAILABLE — Firestore temporarily down, retry with backoff",
    504: "DEADLINE_EXCEEDED — Firestore timeout, retry with backoff",
}

RETRYABLE = {429, 500, 503, 504}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def sv(val):
    return {"stringValue": str(val)}

def bv(val):
    return {"booleanValue": bool(val)}

def extract(field):
    if not field:
        return ""
    return field.get("stringValue", field.get("integerValue", field.get("booleanValue", "")))

def _log_call(method, url, status, latency_ms, error=None, root_cause=None):
    """Append every Firestore call to JSONL ledger."""
    LOG_PATH.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": now_iso(),
        "service": "firestore",
        "method": method,
        "url": url.replace(BASE, ""),
        "status": status,
        "latency_ms": latency_ms,
        "error": error,
        "root_cause": root_cause,
    }
    with open(LOG_PATH, "a") as f:
        f.write(_redact(json.dumps(entry)) + "\n")

def _classify_error(code, body):
    """Map HTTP code to human-readable root cause."""
    mapped = ERROR_MAP.get(code, f"UNKNOWN_{code}")
    detail = ""
    try:
        data = json.loads(body)
        detail = _redact(data.get("error", {}).get("message", "")[:150])
    except:
        detail = _redact(body[:150]) if body else ""
    return mapped, detail

def _request(method, url, data=None, retries=3, backoff=1.0):
    """HTTP request with retry, backoff, error mapping, and logging."""
    headers = {"Content-Type": "application/json"} if data else {}
    encoded = json.dumps(data).encode() if data else None
    last_err = None

    for attempt in range(retries):
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=encoded, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read()
                latency = int((time.time() - t0) * 1000)
                _log_call(method, url, r.status, latency)
                return json.loads(body)

        except urllib.error.HTTPError as e:
            latency = int((time.time() - t0) * 1000)
            err_body = e.read().decode()[:300]
            mapped, detail = _classify_error(e.code, err_body)
            _log_call(method, url, e.code, latency, error=mapped, root_cause=detail)

            if e.code in RETRYABLE and attempt < retries - 1:
                wait = backoff * (2 ** attempt)
                time.sleep(wait)
                last_err = f"HTTP {e.code}: {mapped}"
                continue
            raise RuntimeError(f"HTTP {e.code}: {mapped} | {detail}") from e

        except urllib.error.URLError as e:
            latency = int((time.time() - t0) * 1000)
            root = str(e.reason)
            if "timed out" in root.lower():
                _log_call(method, url, 504, latency, error="TIMEOUT", root_cause=root)
                if attempt < retries - 1:
                    time.sleep(backoff * (2 ** attempt))
                    last_err = f"TIMEOUT: {root}"
                    continue
            else:
                _log_call(method, url, 0, latency, error="NETWORK_ERROR", root_cause=root)
            raise RuntimeError(f"Network error: {root}") from e

    raise RuntimeError(f"All {retries} retries failed. Last: {last_err}")

def fs_get(collection):
    return _request("GET", f"{BASE}/{collection}")

def fs_patch(collection, doc_id, fields):
    return _request("PATCH", f"{BASE}/{collection}/{doc_id}", {"fields": fields})

def fs_post(collection, fields):
    return _request("POST", f"{BASE}/{collection}", {"fields": fields})

# --- Commands ---

def cmd_heartbeat(desk, status):
    fs_patch("agents", desk, {
        "desk": sv(desk),
        "status": sv(status),
        "last_seen": sv(now_iso()),
    })
    print(f"[heartbeat] {desk} → {status}")

def cmd_send(from_desk, to_desk, message):
    fields = {
        "from": sv(from_desk),
        "to": sv(to_desk),
        "message": sv(message),
        "timestamp": sv(now_iso()),
        "read": bv(False),
    }
    fs_post("inbox", fields)
    print(f"[send] {from_desk}→{to_desk}: {message[:80]}")

def cmd_inbox(desk):
    data = fs_get("inbox")
    docs = data.get("documents", [])
    count = 0
    for doc in docs:
        f = doc.get("fields", {})
        if extract(f.get("to")) == desk and not extract(f.get("read")):
            print(f"  [{extract(f.get('from',''))}] {extract(f.get('message',''))[:120]}")
            doc_path = doc["name"].split("/documents/")[1]
            col, doc_id = doc_path.rsplit("/", 1)
            f["read"] = bv(True)
            fs_patch(col, doc_id, f)
            count += 1
    if count == 0:
        print(f"[inbox] {desk}: empty")
    else:
        print(f"[inbox] {desk}: {count} message(s) (marked read)")

def cmd_gem(gem_id, text, source, topic):
    fs_patch("gems", gem_id, {
        "id": sv(gem_id),
        "text": sv(text),
        "source": sv(source),
        "topic": sv(topic),
        "timestamp": sv(now_iso()),
    })
    print(f"[gem] {gem_id} saved")

def cmd_incident(inc_id, symptom, status):
    fs_patch("incidents", inc_id, {
        "id": sv(inc_id),
        "symptom": sv(symptom),
        "status": sv(status),
        "timestamp": sv(now_iso()),
    })
    print(f"[incident] {inc_id} → {status}")

def cmd_status():
    print("RHEA FIREBASE OFFICE STATUS")
    print("=" * 50)
    try:
        data = fs_get("agents")
        docs = data.get("documents", [])
        print(f"\nDesks: {len(docs)}")
        for doc in docs:
            f = doc.get("fields", {})
            print(f"  {extract(f.get('desk','')):10s} {extract(f.get('status','')):10s} {extract(f.get('last_seen',''))}")
    except Exception as e:
        print(f"  Error: {e}")
    try:
        data = fs_get("inbox")
        docs = data.get("documents", [])
        unread = sum(1 for d in docs if not extract(d.get("fields", {}).get("read")))
        print(f"\nInbox: {len(docs)} total, {unread} unread")
    except Exception as e:
        print(f"  Inbox error: {e}")
    try:
        data = fs_get("gems")
        print(f"Gems: {len(data.get('documents', []))}")
    except:
        print("Gems: 0")
    try:
        data = fs_get("incidents")
        print(f"Incidents: {len(data.get('documents', []))}")
    except:
        print("Incidents: 0")

def cmd_health():
    """Firestore health probe — tests read + write + latency."""
    print("FIRESTORE HEALTH PROBE")
    print("=" * 50)
    # Read probe
    try:
        t0 = time.time()
        fs_get("agents")
        ms = int((time.time() - t0) * 1000)
        print(f"  READ   ✅  {ms}ms")
    except Exception as e:
        print(f"  READ   ❌  {e}")

    # Write probe
    try:
        t0 = time.time()
        fs_patch("_health", "probe", {
            "ts": sv(now_iso()),
            "source": sv("health-check"),
        })
        ms = int((time.time() - t0) * 1000)
        print(f"  WRITE  ✅  {ms}ms")
    except Exception as e:
        print(f"  WRITE  ❌  {e}")

    # Auth check (no secrets in env — we use open rules)
    has_creds = bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    print(f"  AUTH   {'⚠️  ADC set (unused — open rules)' if has_creds else '✅  No secrets needed (open rules)'}")

    # Log file check
    if LOG_PATH.exists():
        lines = sum(1 for _ in open(LOG_PATH))
        print(f"  LOG    ✅  {lines} entries in {LOG_PATH}")
    else:
        print(f"  LOG    ⚠️  No log file yet (created on first call)")

    # Secrets hygiene
    env_keys = [k for k in os.environ if "KEY" in k.upper() or "SECRET" in k.upper() or "TOKEN" in k.upper() or "PASSWORD" in k.upper()]
    if env_keys:
        print(f"  SECRETS ⚠️  {len(env_keys)} sensitive env vars detected: {', '.join(env_keys[:5])}")
        print(f"          Ensure none are logged or sent to Firestore.")
    else:
        print(f"  SECRETS ✅  No sensitive env vars in scope")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "heartbeat" and len(args) >= 2:
            cmd_heartbeat(args[0], args[1])
        elif cmd == "send" and len(args) >= 3:
            cmd_send(args[0], args[1], " ".join(args[2:]))
        elif cmd == "inbox" and len(args) >= 1:
            cmd_inbox(args[0])
        elif cmd == "gem" and len(args) >= 4:
            cmd_gem(args[0], args[1], args[2], args[3])
        elif cmd == "incident" and len(args) >= 3:
            cmd_incident(args[0], args[1], args[2])
        elif cmd == "status":
            cmd_status()
        elif cmd == "health":
            cmd_health()
        else:
            print(__doc__)
            sys.exit(1)
    except Exception as e:
        print(f"[error] {e}")
        sys.exit(1)
