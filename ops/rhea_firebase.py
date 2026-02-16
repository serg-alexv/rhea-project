#!/usr/bin/env /usr/bin/python3
"""
Rhea Firebase Office — Inter-agent communication layer.
Uses Firestore as real-time shared memory between all agents.

Usage:
  python3 ops/rhea_firebase.py heartbeat <desk> <status>
  python3 ops/rhea_firebase.py send <from_desk> <to_desk> <message>
  python3 ops/rhea_firebase.py inbox <desk>
  python3 ops/rhea_firebase.py gem <id> <text> <source> <topic>
  python3 ops/rhea_firebase.py incident <id> <symptom> <status>
  python3 ops/rhea_firebase.py capsule <json_string>
  python3 ops/rhea_firebase.py status
"""

import sys
import json
import os
from datetime import datetime, timezone

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# Init with Application Default Credentials
PROJ = "rhea-office-sync"
if not firebase_admin._apps:
    firebase_admin.initialize_app(options={"projectId": PROJ})

db = firestore.client()

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def cmd_heartbeat(desk, status):
    db.collection("agents").document(desk).set({
        "desk": desk,
        "status": status,
        "last_seen": now_iso(),
    }, merge=True)
    print(f"[heartbeat] {desk} → {status}")

def cmd_send(from_desk, to_desk, message):
    # Support structured JSON messages: if message parses as JSON, store fields directly
    try:
        payload = json.loads(message)
        payload["_raw"] = message
    except (json.JSONDecodeError, TypeError):
        payload = {"text": message}

    ref = db.collection("inbox").add({
        "from": from_desk,
        "to": to_desk,
        "message": message,
        "payload": payload,
        "timestamp": now_iso(),
        "read": False,
    })
    print(f"[send] {from_desk}→{to_desk}: {message[:80]}...")

def cmd_inbox(desk):
    docs = db.collection("inbox").where("to", "==", desk).where("read", "==", False).stream()
    count = 0
    for doc in docs:
        d = doc.to_dict()
        print(f"  [{d.get('from','?')}] {d.get('message','')[:120]}")
        doc.reference.update({"read": True})
        count += 1
    if count == 0:
        print(f"[inbox] {desk}: empty")
    else:
        print(f"[inbox] {desk}: {count} messages (marked read)")

def cmd_gem(gem_id, text, source, topic):
    db.collection("gems").document(gem_id).set({
        "id": gem_id,
        "text": text,
        "source": source,
        "topic": topic,
        "timestamp": now_iso(),
        "used_by": [],
    })
    print(f"[gem] {gem_id} saved")

def cmd_incident(inc_id, symptom, status):
    db.collection("incidents").document(inc_id).set({
        "id": inc_id,
        "symptom": symptom,
        "status": status,
        "timestamp": now_iso(),
    }, merge=True)
    print(f"[incident] {inc_id} → {status}")

def cmd_capsule(json_string):
    data = json.loads(json_string)
    data["updated"] = now_iso()
    db.collection("capsule").document("today").set(data)
    print(f"[capsule] updated")

def cmd_status():
    print("RHEA FIREBASE OFFICE STATUS")
    print("=" * 50)
    # Agents
    print("\nDesks:")
    for doc in db.collection("agents").stream():
        d = doc.to_dict()
        print(f"  {d.get('desk','?'):10s} {d.get('status','?'):12s} last_seen: {d.get('last_seen','?')}")
    # Inbox unread
    unread = list(db.collection("inbox").where("read", "==", False).stream())
    print(f"\nInbox unread: {len(unread)}")
    # Gems
    gems = list(db.collection("gems").stream())
    print(f"Gems: {len(gems)}")
    # Incidents
    incs = list(db.collection("incidents").stream())
    print(f"Incidents: {len(incs)}")
    # Capsule
    cap = db.collection("capsule").document("today").get()
    if cap.exists:
        print(f"Capsule: updated {cap.to_dict().get('updated','?')}")
    else:
        print("Capsule: not set")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

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
    elif cmd == "capsule" and len(args) >= 1:
        cmd_capsule(" ".join(args))
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)
        sys.exit(1)
