#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate Rhea component dependency graph")
    ap.add_argument("--registry", default="coordination/components.json")
    ap.add_argument("--receipt", default="")
    args = ap.parse_args()

    path = Path(args.registry)
    raw = path.read_bytes()
    reg = json.loads(raw)
    if reg.get("schema") != "rhea.component-registry/v1":
        fail("unsupported registry schema")

    comps = reg.get("components")
    if not isinstance(comps, list) or not comps:
        fail("components must be a non-empty list")
    by_id = {}
    for c in comps:
        cid = c.get("id")
        if not cid or cid in by_id:
            fail(f"invalid/duplicate component id: {cid!r}")
        by_id[cid] = c

    if "omnia-playbook" not in by_id or "rheknel" not in by_id:
        fail("omnia-playbook and rheknel are mandatory registry members")

    omnia = by_id["omnia-playbook"]
    rheknel = by_id["rheknel"]
    reqs = rheknel.get("requires", [])
    matches = [r for r in reqs if r.get("component") == "omnia-playbook" and r.get("mandatory") is True]
    if len(matches) != 1:
        fail("rheknel must have exactly one mandatory omnia-playbook dependency")
    contract = matches[0].get("contract")
    if not contract:
        fail("mandatory rheknel -> omnia-playbook edge must name a contract")
    if contract not in omnia.get("provides", []):
        fail(f"omnia-playbook does not provide required contract {contract!r}")
    consumers = omnia.get("consumers", [])
    if consumers.count("rheknel") != 1:
        fail("omnia-playbook must declare rheknel exactly once as consumer")

    for c in (omnia, rheknel):
        repo = c.get("repository", "")
        pin = c.get("pinned_main_sha", "")
        if not repo.startswith("timelabs-npo/"):
            fail(f"{c['id']}: repository boundary missing/invalid")
        if len(pin) != 40 or any(ch not in "0123456789abcdef" for ch in pin):
            fail(f"{c['id']}: pinned_main_sha must be a 40-char lowercase git SHA")

    receipt = {
        "schema": "rhea.component-check-receipt/v1",
        "result": "pass",
        "registry_sha256": sha256_bytes(raw),
        "checked_edges": [
            {
                "from": "rheknel",
                "to": "omnia-playbook",
                "mandatory": True,
                "contract": contract,
            }
        ],
        "components": {
            "omnia-playbook": {
                "repository": omnia["repository"],
                "pinned_main_sha": omnia["pinned_main_sha"],
            },
            "rheknel": {
                "repository": rheknel["repository"],
                "pinned_main_sha": rheknel["pinned_main_sha"],
            },
        },
    }
    rendered = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    if args.receipt:
        Path(args.receipt).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
