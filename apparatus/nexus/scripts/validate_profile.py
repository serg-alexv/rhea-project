#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    import tomllib  # py3.11+
except Exception:
    tomllib = None

REQUIRED = [
    ("profile", "enabled"),
    ("modes", "operator_first"),
    ("modes", "loop_killer"),
    ("modes", "patch_first"),
    ("stop", "path"),
    ("ledger", "file"),
]


def main(p: str) -> int:
    if tomllib is None:
        print("FAIL: tomllib unavailable (need Python 3.11+)")
        return 2
    data = tomllib.loads(Path(p).read_text(encoding="utf-8"))
    missing = []
    for sect, key in REQUIRED:
        if sect not in data or key not in data[sect]:
            missing.append(f"{sect}.{key}")
    if missing:
        print("FAIL: missing keys:")
        for m in missing:
            print(" -", m)
        return 1
    print("OK: profile looks structurally valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "operator_profile.toml"))
