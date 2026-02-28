#!/usr/bin/env python3
"""
rhea_family.py — shared-context fanout for MIKA↔REX↔ORION↔HYPERION.

Purpose:
  - send one message and duplicate it to all core agents
  - track delivery/ack in one place
  - make "Rex saw it, Orion saw it" explicit
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
MAILBOX = ROOT / "opera" / "ops" / "virtual-office" / "relay_mailbox.jsonl"
ACKS = ROOT / "opera" / "ops" / "virtual-office" / "relay_acks.jsonl"
LEDGER = ROOT / ".rhea" / "family" / "ledger.jsonl"
REX_PAGER = ROOT / "opera" / "ops" / "rex_pager.py"

DEFAULT_TARGETS = ["REX", "ORION", "HYPERION"]
DEFAULT_SOURCE = "MIKA"
DEFAULT_TTL = 86400
DEFAULT_PRIORITY = "P1"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def gen_family_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"fam-{ts}-{secrets.token_hex(2)}"


def ensure_dirs() -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def append_ledger(entry: dict) -> None:
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def parse_send_output(stdout: str) -> Dict[str, Optional[str]]:
    msg_id = None
    seq = None
    m = re.search(r"id:\s*([A-Za-z0-9\-]+)", stdout or "")
    if m:
        msg_id = m.group(1).strip()
    s = re.search(r"seq=(\d+)", stdout or "")
    if s:
        seq = s.group(1).strip()
    return {"message_id": msg_id, "seq": seq}


def run_send(source: str, target: str, body: str, priority: str, ttl: int) -> Dict[str, Optional[str]]:
    cmd = [
        "python3",
        str(REX_PAGER),
        "send",
        source,
        target,
        body,
        "--priority",
        priority,
        "--ttl",
        str(ttl),
    ]
    out = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    payload = parse_send_output((out.stdout or "") + (out.stderr or ""))
    payload["target"] = target
    payload["ok"] = out.returncode == 0
    payload["stdout"] = (out.stdout or "").strip()
    payload["stderr"] = (out.stderr or "").strip()
    return payload


def find_in_mailbox(family_id: str) -> List[dict]:
    out = []
    tag = f"[FAMILY:{family_id}]"
    for r in read_jsonl(MAILBOX):
        body = str((r.get("payload") or {}).get("body", ""))
        if tag in body:
            out.append(r)
    return out


def ack_map() -> Dict[str, dict]:
    mp: Dict[str, dict] = {}
    for a in read_jsonl(ACKS):
        mid = str(a.get("message_id", "")).strip()
        if not mid:
            continue
        mp[mid] = a
    return mp


def ledger_rows() -> List[dict]:
    rows = read_jsonl(LEDGER)
    rows.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return rows


def cmd_send(args: argparse.Namespace) -> int:
    ensure_dirs()
    family_id = args.family_id or gen_family_id()
    targets = [t.strip().upper() for t in (args.targets or ",".join(DEFAULT_TARGETS)).split(",") if t.strip()]
    source = (args.source or DEFAULT_SOURCE).strip().upper()
    body_raw = " ".join((args.message or "").split()).strip()
    if not body_raw:
        raise SystemExit("message is empty")
    body = f"[FAMILY:{family_id}] {body_raw}"

    sent: List[dict] = []
    for target in targets:
        sent.append(run_send(source, target, body, args.priority, args.ttl))
        time.sleep(0.05)

    # Fallback mailbox resolution in case parser missed IDs
    mail = find_in_mailbox(family_id)
    by_target = {str(m.get("target", "")).upper(): m for m in mail}
    for s in sent:
        if not s.get("message_id"):
            m = by_target.get(str(s["target"]).upper())
            if m:
                s["message_id"] = m.get("id")
                s["seq"] = m.get("seq")

    entry = {
        "ts": now_iso(),
        "family_id": family_id,
        "source": source,
        "targets": targets,
        "body": body_raw,
        "priority": args.priority,
        "ttl_s": args.ttl,
        "messages": [{"target": s["target"], "message_id": s.get("message_id"), "seq": s.get("seq")} for s in sent],
    }
    append_ledger(entry)

    print(json.dumps({"status": "ok", "family_id": family_id, "source": source, "targets": targets, "messages": entry["messages"]}, ensure_ascii=False))
    return 0


def _status_for_family(family_id: str) -> dict:
    rows = [r for r in ledger_rows() if str(r.get("family_id")) == family_id]
    if not rows:
        return {"status": "not_found", "family_id": family_id}
    row = rows[0]
    acks = ack_map()
    result = []
    for m in row.get("messages", []):
        mid = str(m.get("message_id") or "")
        ack = acks.get(mid) if mid else None
        result.append(
            {
                "target": m.get("target"),
                "seq": m.get("seq"),
                "message_id": mid or None,
                "acked": bool(ack),
                "acked_at": (ack or {}).get("acked_at"),
            }
        )
    all_acked = all(x.get("acked") for x in result) if result else False
    return {
        "status": "ok",
        "family_id": family_id,
        "source": row.get("source"),
        "body": row.get("body"),
        "sent_at": row.get("ts"),
        "messages": result,
        "all_acked": all_acked,
    }


def cmd_status(args: argparse.Namespace) -> int:
    rows = ledger_rows()
    if args.family_id:
        print(json.dumps(_status_for_family(args.family_id), ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print(json.dumps({"status": "empty"}))
        return 0
    latest = rows[0]
    fid = str(latest.get("family_id"))
    print(json.dumps(_status_for_family(fid), ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    rows = ledger_rows()
    n = max(1, int(args.n))
    out = []
    for r in rows[:n]:
        out.append(
            {
                "ts": r.get("ts"),
                "family_id": r.get("family_id"),
                "source": r.get("source"),
                "targets": r.get("targets"),
                "body": r.get("body"),
            }
        )
    print(json.dumps({"items": out, "count": len(out)}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Family context fanout control")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_send = sub.add_parser("send", help="send one message to family ring")
    sp_send.add_argument("message", help="message text")
    sp_send.add_argument("--source", default=DEFAULT_SOURCE, help="sender label")
    sp_send.add_argument("--targets", default=",".join(DEFAULT_TARGETS), help="comma-separated recipients")
    sp_send.add_argument("--family-id", default="", help="custom family correlation id")
    sp_send.add_argument("--priority", default=DEFAULT_PRIORITY, help="relay priority")
    sp_send.add_argument("--ttl", type=int, default=DEFAULT_TTL, help="ttl seconds")
    sp_send.set_defaults(func=cmd_send)

    sp_status = sub.add_parser("status", help="delivery status by family id (default: latest)")
    sp_status.add_argument("family_id", nargs="?", default="", help="family id")
    sp_status.set_defaults(func=cmd_status)

    sp_tail = sub.add_parser("tail", help="recent family fanout messages")
    sp_tail.add_argument("-n", type=int, default=20, help="line count")
    sp_tail.set_defaults(func=cmd_tail)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
