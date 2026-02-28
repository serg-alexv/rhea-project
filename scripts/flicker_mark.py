#!/usr/bin/env python3
"""Manual marker for screen-flicker events (for pulse correlation)."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACE_FILE = ROOT / "opera" / "metrics" / "ndi_trace.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    p = argparse.ArgumentParser(description="mark manual flicker event")
    p.add_argument("note", nargs="?", default="manual flicker observed")
    args = p.parse_args()

    note = " ".join(str(args.note).split()).strip() or "manual flicker observed"
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    eid = hashlib.sha1((note + now_iso()).encode("utf-8")).hexdigest()[:12]
    event = {
        "ts": now_iso(),
        "event": "manual_flicker",
        "event_id": eid,
        "risk": "warn",
        "notify": True,
        "summary": note,
    }
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "ok", "event_id": eid, "summary": note}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
