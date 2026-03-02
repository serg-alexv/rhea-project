#!/usr/bin/env python3
"""
continuity_capsule.py — verifiable "brain portability" bundle for Rhea.

Goal:
- Pack the minimum viable state needed to restore continuity on another machine.
- Keep bundle integrity verifiable (sha256 per file + bundle hash).
- Keep process cheap and local-first (no mandatory cloud dependency).

Usage:
  python3 scripts/continuity_capsule.py pack --label daily
  python3 scripts/continuity_capsule.py verify archive/continuity_capsules/brain-capsule-*.tar.gz
  python3 scripts/continuity_capsule.py report
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "archive" / "continuity_capsules"

CORE_PATTERNS = [
    "docs/state.md",
    "opera/memory/FEED.compact",
    "apparatus/nexus/memories/*.md",
    "data/tasks.db",
    "data/proof.db",
    "logs/bridge_calls.jsonl",
    "opera/ops/virtual-office/relay_mailbox.jsonl",
    "opera/ops/virtual-office/relay_chain.jsonl",
    "opera/ops/virtual-office/relay_acks.jsonl",
    "opera/ops/virtual-office/snapshots/*.json",
    "opera/metrics/*.json",
]

SNAPSHOT_PATTERN = ".entire/snapshots/*.json"
SNAPSHOT_LIMIT = 120


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_jsonl_last(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    last: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                last = obj
    return last


def extract_seq(obj: Any) -> int | None:
    if isinstance(obj, dict):
        if isinstance(obj.get("seq"), int):
            return obj["seq"]
        for value in obj.values():
            seq = extract_seq(value)
            if isinstance(seq, int):
                return seq
    if isinstance(obj, list):
        for value in obj:
            seq = extract_seq(value)
            if isinstance(seq, int):
                return seq
    return None


def git_meta() -> dict[str, Any]:
    def _run(*args: str) -> str:
        proc = subprocess.run(
            list(args),
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
        return (proc.stdout or "").strip()

    rev = _run("git", "rev-parse", "HEAD")
    branch = _run("git", "branch", "--show-current")
    dirty = bool(_run("git", "status", "--porcelain"))
    return {"rev": rev or "unknown", "branch": branch or "unknown", "dirty": dirty}


def task_summary() -> dict[str, Any]:
    db_path = ROOT / "data" / "tasks.db"
    if not db_path.exists():
        return {"exists": False}
    out: dict[str, Any] = {"exists": True, "path": str(db_path.relative_to(ROOT))}
    conn = sqlite3.connect(str(db_path))
    try:
        out["total"] = int(conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0])
        status_rows = conn.execute(
            "SELECT status, COUNT(*) FROM tasks GROUP BY status ORDER BY status"
        ).fetchall()
        out["status"] = {str(k): int(v) for k, v in status_rows}
        last_log = conn.execute("SELECT MAX(ts) FROM task_log").fetchone()[0]
        out["last_log_ts"] = last_log
    finally:
        conn.close()
    return out


def continuity_cursor() -> dict[str, Any]:
    relay_chain = ROOT / "opera" / "ops" / "virtual-office" / "relay_chain.jsonl"
    relay_mailbox = ROOT / "opera" / "ops" / "virtual-office" / "relay_mailbox.jsonl"

    chain_last = parse_jsonl_last(relay_chain) or {}
    mailbox_last = parse_jsonl_last(relay_mailbox) or {}

    return {
        "relay_chain_seq": extract_seq(chain_last),
        "relay_mailbox_seq": extract_seq(mailbox_last),
        "relay_chain_ts": chain_last.get("ts") if isinstance(chain_last, dict) else None,
        "relay_mailbox_ts": mailbox_last.get("ts") if isinstance(mailbox_last, dict) else None,
        "tasks": task_summary(),
    }


def collect_files() -> list[Path]:
    files: list[Path] = []
    for pattern in CORE_PATTERNS:
        for p in ROOT.glob(pattern):
            if p.is_file():
                files.append(p)

    snapshots = [p for p in ROOT.glob(SNAPSHOT_PATTERN) if p.is_file()]
    snapshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    files.extend(snapshots[:SNAPSHOT_LIMIT])

    uniq = sorted(set(files), key=lambda p: str(p))
    return uniq


def build_manifest(label: str, files: list[Path], payload_dir: Path | None = None) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    total_bytes = 0
    for p in files:
        rel = str(p.relative_to(ROOT))
        st = p.stat()
        hash_target = p
        if payload_dir is not None:
            staged = payload_dir / rel
            if staged.exists():
                hash_target = staged
        size = int(st.st_size)
        total_bytes += size
        entries.append(
            {
                "path": rel,
                "size": size,
                "mtime": int(st.st_mtime),
                "sha256": sha256_file(hash_target),
            }
        )

    return {
        "schema": "rhea.continuity_capsule.v1",
        "created_at": now_iso(),
        "label": label,
        "root": str(ROOT),
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "git": git_meta(),
        "continuity_cursor": continuity_cursor(),
        "files_count": len(entries),
        "total_bytes": total_bytes,
        "files": entries,
    }


def refresh_feed() -> None:
    proc = subprocess.run(
        ["python3", "src/memory_feed.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"memory_feed refresh failed: {proc.stderr.strip()[:300]}")


def normalize_label(raw: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in "-._" else "-" for ch in raw.strip().lower())
    clean = clean.strip("-._")
    return clean or "manual"


def pack(label: str, out_dir: Path, refresh: bool) -> Path:
    if refresh:
        refresh_feed()

    files = collect_files()
    if not files:
        raise RuntimeError("no files collected for capsule")

    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_name = f"brain-capsule-{stamp}-{label}.tar.gz"
    bundle_path = out_dir / bundle_name

    with tempfile.TemporaryDirectory(prefix="rhea_capsule_") as tmp:
        staging = Path(tmp)
        payload = staging / "payload"
        payload.mkdir(parents=True, exist_ok=True)

        for p in files:
            rel = p.relative_to(ROOT)
            dst = payload / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)

        manifest = build_manifest(label, files, payload_dir=payload)

        manifest_path = staging / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with tarfile.open(bundle_path, "w:gz", compresslevel=6) as tf:
            tf.add(manifest_path, arcname="manifest.json")
            tf.add(payload, arcname="payload")

    bundle_hash = sha256_file(bundle_path)
    sha_path = Path(str(bundle_path) + ".sha256")
    sha_path.write_text(f"{bundle_hash}  {bundle_path.name}\n", encoding="utf-8")

    latest = {
        "created_at": now_iso(),
        "bundle": str(bundle_path.relative_to(ROOT)),
        "sha256": bundle_hash,
        "files_count": manifest["files_count"],
        "total_bytes": manifest["total_bytes"],
        "relay_chain_seq": manifest["continuity_cursor"].get("relay_chain_seq"),
    }
    (out_dir / "LATEST.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, **latest}, ensure_ascii=False, indent=2))
    return bundle_path


def verify(bundle: Path) -> int:
    if not bundle.exists():
        print(json.dumps({"ok": False, "error": f"bundle not found: {bundle}"}, ensure_ascii=False))
        return 2

    errors: list[str] = []
    checked = 0

    with tarfile.open(bundle, "r:gz") as tf:
        try:
            manifest_member = tf.getmember("manifest.json")
        except KeyError:
            print(json.dumps({"ok": False, "error": "manifest.json missing"}, ensure_ascii=False))
            return 3
        manifest_raw = tf.extractfile(manifest_member)
        if manifest_raw is None:
            print(json.dumps({"ok": False, "error": "manifest unreadable"}, ensure_ascii=False))
            return 3
        manifest = json.loads(manifest_raw.read().decode("utf-8", errors="replace"))

        for item in manifest.get("files", []):
            rel = item.get("path")
            expected = item.get("sha256")
            if not rel or not expected:
                errors.append(f"bad_manifest_item:{rel}")
                continue
            tar_path = f"payload/{rel}"
            try:
                m = tf.getmember(tar_path)
            except KeyError:
                errors.append(f"missing:{rel}")
                continue

            fobj = tf.extractfile(m)
            if fobj is None:
                errors.append(f"unreadable:{rel}")
                continue
            h = hashlib.sha256()
            for chunk in iter(lambda: fobj.read(1024 * 1024), b""):
                h.update(chunk)
            actual = h.hexdigest()
            checked += 1
            if actual != expected:
                errors.append(f"hash_mismatch:{rel}")

    result = {
        "ok": len(errors) == 0,
        "bundle": str(bundle),
        "checked": checked,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


def report() -> int:
    out = {
        "created_at": now_iso(),
        "git": git_meta(),
        "continuity_cursor": continuity_cursor(),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/verify portability capsules for continuity.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pack = sub.add_parser("pack", help="Create new continuity capsule")
    p_pack.add_argument("--label", default="manual", help="Bundle label (default: manual)")
    p_pack.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUT_DIR})",
    )
    p_pack.add_argument(
        "--no-refresh-feed",
        action="store_true",
        help="Skip FEED.compact regeneration before pack",
    )

    p_verify = sub.add_parser("verify", help="Verify capsule integrity")
    p_verify.add_argument("bundle", help="Path to bundle .tar.gz")

    sub.add_parser("report", help="Print live continuity cursor summary")

    args = parser.parse_args()

    if args.cmd == "pack":
        label = normalize_label(args.label)
        out_dir = Path(args.out_dir)
        pack(label=label, out_dir=out_dir, refresh=not args.no_refresh_feed)
        return 0
    if args.cmd == "verify":
        return verify(Path(args.bundle))
    if args.cmd == "report":
        return report()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
