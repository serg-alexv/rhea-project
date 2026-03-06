#!/usr/bin/env python3
"""
Extracts a pragmatic "component inventory" from Next.js/Mintlify chunk JS files.
Output:
  artifacts/components_inventory.json
  artifacts/components_inventory.jsonl (evidence lines)

Heuristics:
- Next.js webpack exports: o.d(t,{Name:()=>X})
- function Name( or const Name=
- JSX factory usage around (0,r.jsx)("Component"... is NOT reliable; we mostly keep symbol exports.

Usage:
  python3 scripts/extract_component_inventory.py [root_dir]
Default root_dir = docs/restore
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import defaultdict

ROOT_DEFAULT = Path("docs/restore")
OUT_JSON = Path("artifacts/components_inventory.json")
OUT_JSONL = Path("artifacts/components_inventory.jsonl")

# Patterns
EXPORTS_RE = re.compile(r'\bo\.d\(t,\s*\{([^}]{1,5000})\}\)', re.DOTALL)
EXPORT_NAME_RE = re.compile(r'([A-Za-z_$][A-Za-z0-9_$]{1,80})\s*:\s*\(\)\s*=>')
FUNC_RE = re.compile(r'\bfunction\s+([A-Za-z_$][A-Za-z0-9_$]{1,80})\s*\(')
CONST_FN_RE = re.compile(r'\bconst\s+([A-Za-z_$][A-Za-z0-9_$]{1,80})\s*=\s*\(?[A-Za-z_$][A-Za-z0-9_$]*\)?\s*=>')

# noise filter
NOISE_PREFIX = ("_", "$", "webpack", "regeneratorRuntime")
NOISE_NAMES = set([
    "default","__esModule","n","t","o","r","e","i","a","s","d","c","u","l","p","m","g","h","x","y","b"
])

def is_noise(name: str) -> bool:
    if not name: return True
    if name in NOISE_NAMES: return True
    if name.startswith(NOISE_PREFIX): return True
    if len(name) <= 2: return True
    return False

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT_DEFAULT
    root = root.resolve()
    chunks = list(root.rglob("_next/static/chunks/**/*.js"))
    if not chunks:
        print(f"[extract_component_inventory] no chunks found under {root}", file=sys.stderr)
        return 2

    hits = defaultdict(list)

    for p in chunks:
        try:
            txt = p.read_text("utf-8", errors="ignore")
        except Exception:
            continue

        # exports
        for m in EXPORTS_RE.finditer(txt):
            block = m.group(1)
            for nm in EXPORT_NAME_RE.findall(block):
                if not is_noise(nm):
                    hits[nm].append({"source":"chunk_export","path":str(p)})

        # functions
        for nm in FUNC_RE.findall(txt):
            if not is_noise(nm):
                hits[nm].append({"source":"function","path":str(p)})

        # const arrow fns (limited signal)
        for nm in CONST_FN_RE.findall(txt):
            if not is_noise(nm):
                hits[nm].append({"source":"const_arrow","path":str(p)})

    # Build inventory
    inventory = []
    for name in sorted(hits.keys(), key=lambda x: x.lower()):
        evidence = hits[name]
        # cap evidence list
        ev = evidence[:20]
        inventory.append({
            "name": name,
            "count": len(evidence),
            "evidence": ev,
        })

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")

    # jsonl evidence (easier to grep later)
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for item in inventory:
            f.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(f"[extract_component_inventory] chunks={len(chunks)} components={len(inventory)} -> {OUT_JSON}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
