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
"""
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

PROJ = "rhea-office-sync"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJ}/databases/(default)/documents"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def sv(val):
    """Wrap string for Firestore."""
    return {"stringValue": str(val)}

def bv(val):
    """Wrap bool for Firestore."""
    return {"booleanValue": bool(val)}

def fs_get(collection):
    url = f"{BASE}/{collection}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def fs_patch(collection, doc_id, fields):
    url = f"{BASE}/{collection}/{doc_id}"
    data = json.dumps({"fields": fields}).encode()
    req = urllib.request.Request(url, data=data, method="PATCH",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def fs_post(collection, fields):
    url = f"{BASE}/{collection}"
    data = json.dumps({"fields": fields}).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def extract(field):
    if not field:
        return ""
    return field.get("stringValue", field.get("integerValue", field.get("booleanValue", "")))

# --- Commands ---

def cmd_heartbeat(desk, status):
    fs_patch("agents", desk, {
        "desk": sv(desk),
        "status": sv(status),
        "last_seen": sv(now_iso()),
    })
    print(f"[heartbeat] {desk} → {status}")

def cmd_send(from_desk, to_desk, message):
    # Support structured JSON payloads
    try:
        payload = json.loads(message)
    except (json.JSONDecodeError, TypeError):
        payload = None

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
            # Mark read via patch
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
    # Agents
    try:
        data = fs_get("agents")
        docs = data.get("documents", [])
        print(f"\nDesks: {len(docs)}")
        for doc in docs:
            f = doc.get("fields", {})
            print(f"  {extract(f.get('desk','')):10s} {extract(f.get('status','')):10s} {extract(f.get('last_seen',''))}")
    except Exception as e:
        print(f"  Error: {e}")
    # Inbox unread
    try:
        data = fs_get("inbox")
        docs = data.get("documents", [])
        unread = sum(1 for d in docs if not extract(d.get("fields", {}).get("read")))
        print(f"\nInbox: {len(docs)} total, {unread} unread")
    except Exception as e:
        print(f"  Inbox error: {e}")
    # Gems
    try:
        data = fs_get("gems")
        print(f"Gems: {len(data.get('documents', []))}")
    except:
        print("Gems: 0")
    # Incidents
    try:
        data = fs_get("incidents")
        print(f"Incidents: {len(data.get('documents', []))}")
    except:
        print("Incidents: 0")

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
        else:
            print(__doc__)
            sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"[error] HTTP {e.code}: {e.read().decode()[:200]}")
        sys.exit(1)
    except Exception as e:
        print(f"[error] {e}")
        sys.exit(1)
