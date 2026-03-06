#!/usr/bin/env python3
"""
Disk-safe extractor for Next.js __NEXT_DATA__ blobs.

Writes ONE jsonl file: artifacts/next_data.jsonl
- No per-page huge JSON files
- Filters to high-signal keys (pageProps/props-like)
- Hard caps on blob size and output size
- Stores only compact JSON (no indent)

Usage:
  python3 scripts/extract_next_data.py [root_dir]

Defaults:
  root_dir = docs/restore
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DEFAULT = Path("docs/restore")
OUT_PATH = Path("artifacts/next_data.jsonl")

# Safety knobs
MAX_HTML_BYTES = 2_000_000          # skip giant html files
MAX_NEXTDATA_BYTES = 900_000        # skip giant __NEXT_DATA__ JSON
MAX_OUT_BYTES = 180_000_000         # stop after ~180MB output
MAX_RECORD_BYTES = 1_200_000        # cap per-record output line size
STOP_AFTER_PAGES = 0               # 0 = no limit

# high-signal keys we keep from page data
KEEP_TOP_LEVEL = {"props", "pageProps", "query", "page", "buildId", "locale", "locales", "defaultLocale"}
KEEP_DEEP_KEYS = {
    "navigation", "sidebar", "toc", "tableOfContents", "breadcrumbs", "routes", "pages",
    "title", "description", "meta", "metadata",
    "openapi", "api", "schema", "schemas",
    "mdx", "markdown", "content", "sections", "headings",
    "recommendedPages", "recommendPages",
}

NEXTDATA_RE = re.compile(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)

def _deep_prune(obj: Any, depth: int = 0, max_depth: int = 10) -> Any:
    """Prune big structures while keeping keys that look like docs/navigation metadata."""
    if depth > max_depth:
        return None
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if k in KEEP_DEEP_KEYS or depth < 2:
                pv = _deep_prune(v, depth + 1, max_depth)
                if pv is not None:
                    out[k] = pv
            else:
                # keep small scalars that might still be useful
                if isinstance(v, (str, int, float, bool)) and len(str(v)) <= 300:
                    out[k] = v
        return out
    if isinstance(obj, list):
        # cap list lengths hard
        out_list = []
        for i, v in enumerate(obj[:200]):
            pv = _deep_prune(v, depth + 1, max_depth)
            if pv is not None:
                out_list.append(pv)
        return out_list
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        # cap long strings
        if isinstance(obj, str) and len(obj) > 2000:
            return obj[:2000] + "…"
        return obj
    return None

def _extract_next_data(html: str) -> Optional[dict]:
    m = NEXTDATA_RE.search(html)
    if not m:
        return None
    raw = m.group(1)
    if len(raw.encode("utf-8", errors="ignore")) > MAX_NEXTDATA_BYTES:
        return None
    try:
        data = json.loads(raw)
        return data
    except Exception:
        return None

def _select_payload(data: dict) -> dict:
    picked: Dict[str, Any] = {}
    for k in KEEP_TOP_LEVEL:
        if k in data:
            picked[k] = data[k]
    # Next.js typically stores props under data["props"]["pageProps"]
    # We keep props but prune heavily.
    pruned = _deep_prune(picked)
    return pruned if isinstance(pruned, dict) else {}

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT_DEFAULT
    root = root.resolve()
    if not root.exists():
        print(f"[extract_next_data] root not found: {root}", file=sys.stderr)
        return 2

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    out_bytes = 0
    pages = 0
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for p in root.rglob("*.html"):
            try:
                if p.stat().st_size > MAX_HTML_BYTES:
                    continue
                html = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            data = _extract_next_data(html)
            if not data:
                continue

            payload = _select_payload(data)
            if not payload:
                continue

            rec = {
                "path": str(p),
                "buildId": data.get("buildId"),
                "page": data.get("page"),
                "query": data.get("query"),
                "payload": payload,
            }
            line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))

            if len(line.encode("utf-8", errors="ignore")) > MAX_RECORD_BYTES:
                # last-resort: drop payload entirely, keep just metadata
                rec2 = {"path": rec["path"], "buildId": rec["buildId"], "page": rec["page"], "query": rec["query"]}
                line = json.dumps(rec2, ensure_ascii=False, separators=(",", ":"))

            out.write(line + "\n")
            out_bytes += len(line) + 1
            pages += 1

            if out_bytes >= MAX_OUT_BYTES:
                print(f"[extract_next_data] stop: reached MAX_OUT_BYTES={MAX_OUT_BYTES} at pages={pages}", file=sys.stderr)
                break
            if STOP_AFTER_PAGES and pages >= STOP_AFTER_PAGES:
                break

    print(f"[extract_next_data] wrote {OUT_PATH} | pages={pages} | bytes={out_bytes}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
