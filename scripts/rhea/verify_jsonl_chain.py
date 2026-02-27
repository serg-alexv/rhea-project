#!/usr/bin/env python3
"""
verify_jsonl_chain.py — verify hash-chained JSONL integrity.

Default mode allows a legacy unchained prefix and starts verification from the
first chained entry that has seq/prev_hash/entry_hash fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict


def stable_json(obj: Dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verify(path: Path, strict: bool) -> Dict:
    if not path.exists():
        return {"status": "error", "reason": "log_not_found", "path": str(path)}

    prev_hash = "GENESIS"
    expected_seq = 1
    verified = 0
    legacy_prefix = 0
    started = False
    last_hash = "GENESIS"

    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception as e:
                return {
                    "status": "fail",
                    "reason": "invalid_json",
                    "line": lineno,
                    "error": str(e),
                }

            has_chain = all(k in entry for k in ("seq", "prev_hash", "entry_hash"))
            if not has_chain:
                if not started and not strict:
                    legacy_prefix += 1
                    continue
                return {
                    "status": "fail",
                    "reason": "missing_chain_fields",
                    "line": lineno,
                }

            seq = int(entry["seq"])
            if not started:
                started = True
                expected_seq = seq
                prev_hash = str(entry["prev_hash"])
            if seq != expected_seq:
                return {
                    "status": "fail",
                    "reason": "seq_mismatch",
                    "line": lineno,
                    "expected_seq": expected_seq,
                    "actual_seq": seq,
                }

            if str(entry["prev_hash"]) != prev_hash:
                return {
                    "status": "fail",
                    "reason": "prev_hash_mismatch",
                    "line": lineno,
                    "expected_prev_hash": prev_hash,
                    "actual_prev_hash": entry["prev_hash"],
                }

            claimed_hash = str(entry["entry_hash"])
            no_hash = dict(entry)
            no_hash.pop("entry_hash", None)
            computed = hashlib.sha256(stable_json(no_hash).encode("utf-8")).hexdigest()
            if claimed_hash != computed:
                return {
                    "status": "fail",
                    "reason": "entry_hash_mismatch",
                    "line": lineno,
                    "expected_entry_hash": computed,
                    "actual_entry_hash": claimed_hash,
                }

            verified += 1
            expected_seq += 1
            prev_hash = claimed_hash
            last_hash = claimed_hash

    if not started:
        return {"status": "error", "reason": "no_chain_entries_found", "legacy_prefix": legacy_prefix}

    return {
        "status": "ok",
        "entries_verified": verified,
        "legacy_prefix": legacy_prefix,
        "last_hash": last_hash,
        "path": str(path),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Verify hash chain in JSONL log")
    p.add_argument(
        "--path",
        default=".entire/logs/autonudge.jsonl",
        help="JSONL log path (default: .entire/logs/autonudge.jsonl)",
    )
    p.add_argument("--strict", action="store_true", help="fail on any unchained prefix entries")
    return p


def main() -> int:
    args = build_parser().parse_args()
    result = verify(Path(args.path), strict=args.strict)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
