#!/usr/bin/env python3
"""
continuity_cloud_smoke.py — zero-cost portability smoke test via cloud-synced folder.

Flow:
1) Build fresh continuity capsule.
2) Mirror capsule + sha256 + LATEST.json into cloud-synced directory.
3) Simulate "another machine restore" by copying from cloud mirror to temp dir.
4) Run integrity verify on restored bundle.

Default cloud mirror (auto-detected):
  ~/Library/CloudStorage/GoogleDrive-*/My Drive/rhea/continuity_capsules

Override via env:
  RHEA_CLOUD_MIRROR=/absolute/path python3 scripts/continuity_cloud_smoke.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAP_DIR = ROOT / "archive" / "continuity_capsules"


def now_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def detect_cloud_dir() -> Path:
    env_raw = (__import__("os").environ.get("RHEA_CLOUD_MIRROR") or "").strip()
    if env_raw:
        return Path(env_raw)

    cloud_root = Path.home() / "Library" / "CloudStorage"
    candidates = sorted(cloud_root.glob("GoogleDrive-*"))
    for c in candidates:
        p = c / "My Drive" / "rhea" / "continuity_capsules"
        if p.parent.exists():
            return p
    # fallback first candidate path even if parent not present
    if candidates:
        return candidates[0] / "My Drive" / "rhea" / "continuity_capsules"
    raise RuntimeError("No Google Drive CloudStorage directory detected")


def latest_bundle_from_latest_json() -> Path:
    latest_path = CAP_DIR / "LATEST.json"
    if not latest_path.exists():
        raise RuntimeError("LATEST.json missing after pack")
    data = json.loads(latest_path.read_text(encoding="utf-8"))
    rel = data.get("bundle")
    if not rel:
        raise RuntimeError("LATEST.json has no bundle path")
    bundle = ROOT / rel
    if not bundle.exists():
        raise RuntimeError(f"Bundle missing: {bundle}")
    return bundle


def main() -> int:
    label = f"smoke-{now_tag().lower()}"
    pack = run(["python3", "scripts/continuity_capsule.py", "pack", "--label", label], timeout=300)
    if pack.returncode != 0:
        print(pack.stdout)
        print(pack.stderr)
        raise SystemExit(2)

    bundle = latest_bundle_from_latest_json()
    sha = Path(str(bundle) + ".sha256")
    latest = CAP_DIR / "LATEST.json"

    cloud_dir = detect_cloud_dir()
    cloud_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(bundle, cloud_dir / bundle.name)
    if sha.exists():
        shutil.copy2(sha, cloud_dir / sha.name)
    shutil.copy2(latest, cloud_dir / "LATEST.json")

    # Restore simulation: pull from cloud mirror to temp, verify there.
    with tempfile.TemporaryDirectory(prefix="rhea_cloud_restore_") as td:
        temp = Path(td)
        restored_bundle = temp / bundle.name
        shutil.copy2(cloud_dir / bundle.name, restored_bundle)
        verify = run(
            ["python3", "scripts/continuity_capsule.py", "verify", str(restored_bundle)],
            timeout=300,
        )
        if verify.returncode != 0:
            print(verify.stdout)
            print(verify.stderr)
            raise SystemExit(3)

        result = {
            "ok": True,
            "cloud_dir": str(cloud_dir),
            "bundle": str(bundle.relative_to(ROOT)),
            "bundle_size_bytes": bundle.stat().st_size,
            "verify": json.loads((verify.stdout or "{}").strip() or "{}"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
