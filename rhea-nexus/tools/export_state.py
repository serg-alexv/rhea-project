#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc)}

def parse_invariants(office_md: Path) -> list[str]:
    if not office_md.exists():
        return [f"MISSING: {office_md.as_posix()}"]
    lines = office_md.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    in_rules = False
    for line in lines:
        if line.strip() == "## Rules":
            in_rules = True
            continue
        if in_rules and line.startswith("## "):
            break
        if in_rules:
            m = re.match(r"^\d+\.\s+(.*)$", line.strip())
            if m:
                out.append(m.group(1))
    return out or [f"MISSING: {office_md.as_posix()}#Rules"]

def load_records(paths: list[Path], missing_label: str) -> list[dict[str, Any] | str]:
    if not paths:
        return [f"MISSING: {missing_label}"]
    records: list[dict[str, Any] | str] = []
    for path in sorted(paths, key=lambda p: p.as_posix()):
        records.append({"path": path.as_posix(), "data": read_json(path)})
    return records

def extract_agent_ids(*record_groups: list[dict[str, Any] | str]) -> list[str]:
    ids: set[str] = set()
    for records in record_groups:
        for item in records:
            if isinstance(item, str):
                continue
            data = item.get("data")
            if isinstance(data, dict) and "agent" in data:
                ids.add(str(data["agent"]))
    return sorted(ids)

def tail_relay(relay_path: Path, limit: int = 200) -> list[str]:
    if not relay_path.exists():
        return [f"MISSING: {relay_path.as_posix()}"]
    raw_lines = relay_path.read_text(encoding="utf-8").splitlines()[-limit:]
    out: list[str] = []
    for line in raw_lines:
        text = line.strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
            out.append(json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        except Exception:
            out.append(text)
    return out

def render_records(lines: list[str], title: str, records: list[dict[str, Any] | str]) -> None:
    lines.append(f"### {title}")
    for item in records:
        if isinstance(item, str):
            lines.append(f"- {item}")
            continue
        lines.append(f"- path: `{item['path']}`")
        lines.append("```json")
        lines.append(json.dumps(item["data"], sort_keys=True, indent=2, ensure_ascii=False))
        lines.append("```")

def build_payload(base: Path) -> str:
    invariants = parse_invariants(base / "OFFICE.md")
    watcher = load_records(list(base.rglob("watcher_state.json")), (base / "**" / "watcher_state.json").as_posix())
    snapshots = load_records(list((base / "snapshots").glob("*.json")), (base / "snapshots" / "*.json").as_posix())
    leases = load_records(list((base / "leases").glob("*.json")), (base / "leases" / "*.json").as_posix())
    routes = {
        "inbox_path": (base / "inbox").as_posix(),
        "outbox_path": (base / "outbox").as_posix(),
        "stop_path": (base / "STOP").as_posix(),
        "agent_ids": extract_agent_ids(watcher, snapshots, leases),
    }
    recent_signals = tail_relay(base / "relay_chain.jsonl", limit=200)
    checklist = [
        "Verify stop sentinel path exists and is monitored.",
        "Verify lease expirations and snapshot timestamps are fresh.",
        "Verify relay chain tail parses as JSON and remains append-only.",
        "Re-run exporter; confirm STATE_HASH only changes when payload changes.",
    ]
    lines: list[str] = []
    lines.append("=== PAYLOAD ===")
    lines.append("## 1) INVARIANTS")
    for bullet in invariants:
        lines.append(f"- {bullet}")
    lines.append("")
    lines.append("## 2) ROUTES")
    lines.append(f"- inbox: `{routes['inbox_path']}`")
    lines.append(f"- outbox: `{routes['outbox_path']}`")
    lines.append(f"- STOP: `{routes['stop_path']}`")
    if routes["agent_ids"]:
        for agent_id in routes["agent_ids"]:
            lines.append(f"- agent_id: `{agent_id}`")
    else:
        lines.append("- MISSING: agent ids")
    lines.append("")
    lines.append("## 3) LAST KNOWN STATE")
    render_records(lines, "watcher_state.json", watcher)
    render_records(lines, "snapshots", snapshots)
    render_records(lines, "leases", leases)
    lines.append("")
    lines.append("## 4) RECENT SIGNALS")
    for signal in recent_signals:
        lines.append(f"- `{signal}`")
    lines.append("")
    lines.append("## 5) CHECKLIST")
    for item in checklist:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"

def export_state(from_dir: Path, to_file: Path) -> str:
    payload = build_payload(from_dir)
    state_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    header = ["# Nexus State Export", f"Generated UTC: {now_utc_iso()}", f"STATE_HASH = {state_hash}", ""]
    to_file.parent.mkdir(parents=True, exist_ok=True)
    to_file.write_text("\n".join(header) + payload, encoding="utf-8")
    return to_file.as_posix()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="from_dir", required=True)
    parser.add_argument("--to", dest="to_file", required=True)
    args = parser.parse_args()
    output_path = export_state(Path(args.from_dir), Path(args.to_file))
    lines = Path(output_path).read_text(encoding="utf-8").splitlines()
    print("\n".join(lines[:40]))

if __name__ == "__main__":
    main()
