#!/usr/bin/env python3
"""Validate Continuity Corpus v1 and optionally score candidate JSONL output.

Stdlib-only so CI and clean clones can run it without dependency installation.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REQUIRED_CASE_KEYS = {"id", "category", "input", "expected"}
REQUIRED_EXPECTED_KEYS = {"decision", "truth_label", "action", "reason_code"}
ALLOWED_TRUTH = {
    "VERIFIED",
    "OBSERVED",
    "DERIVED",
    "PROPOSED",
    "UNVERIFIED",
    "CONTRADICTED",
    "PARKED",
}
REQUIRED_CATEGORIES = {
    "identity",
    "intent",
    "evidence",
    "provenance",
    "contradiction",
    "replay",
    "staleness",
    "authority",
    "injection",
    "rollback",
    "consensus",
    "independence",
    "long_context",
    "local_backend",
    "ontology",
    "cross_ontology",
}
REQUIRED_ONTOLOGIES = {
    "us_constitutional_liberal",
    "prc_administrative_collective",
    "arabia_islamic_juristic_plural",
    "eu_rights_regulatory",
    "india_plural_constitutional",
}
SEMANTIC_FIELDS = ("decision", "truth_label", "action", "reason_code")
MIN_CASES = 47


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                die(f"{path}:{lineno}: invalid JSON: {exc}")
            if not isinstance(row, dict):
                die(f"{path}:{lineno}: each line must be a JSON object")
            rows.append(row)
    return rows


def load_ontologies(path: Path | None) -> set[str]:
    if path is None:
        return set()
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"{path}: invalid ontology pack: {exc}")
    items = doc.get("ontologies") if isinstance(doc, dict) else None
    if not isinstance(items, list):
        die(f"{path}: ontologies must be an array")
    ids: set[str] = set()
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            die(f"{path}: ontology #{idx} must be an object")
        for key in ("id", "label", "scope", "authority_order", "reasoning_principles", "anti_stereotype_rule"):
            if key not in item:
                die(f"{path}: ontology #{idx} missing {key}")
        oid = item["id"]
        if not isinstance(oid, str) or not oid:
            die(f"{path}: ontology #{idx} has invalid id")
        if oid in ids:
            die(f"{path}: duplicate ontology id {oid}")
        if not isinstance(item["authority_order"], list) or not item["authority_order"]:
            die(f"{path}: {oid}.authority_order must be non-empty")
        if not isinstance(item["reasoning_principles"], list) or not item["reasoning_principles"]:
            die(f"{path}: {oid}.reasoning_principles must be non-empty")
        ids.add(oid)
    missing = REQUIRED_ONTOLOGIES - ids
    if missing:
        die(f"{path}: missing required ontology ids: {sorted(missing)}")
    print(f"ONTOLOGIES_OK count={len(ids)}")
    return ids


def validate_corpus(cases: list[dict], ontology_ids: set[str]) -> dict[str, dict]:
    if len(cases) < MIN_CASES:
        die(f"corpus contains {len(cases)} cases; expected at least {MIN_CASES}")

    by_id: dict[str, dict] = {}
    categories: Counter[str] = Counter()

    for idx, case in enumerate(cases, 1):
        missing = REQUIRED_CASE_KEYS - case.keys()
        if missing:
            die(f"case #{idx} missing keys: {sorted(missing)}")
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id:
            die(f"case #{idx}: id must be a non-empty string")
        if case_id in by_id:
            die(f"duplicate case id: {case_id}")
        if not isinstance(case["category"], str) or not case["category"]:
            die(f"{case_id}: category must be a non-empty string")
        if not isinstance(case["input"], dict):
            die(f"{case_id}: input must be an object")
        if not isinstance(case["expected"], dict):
            die(f"{case_id}: expected must be an object")
        expected = case["expected"]
        missing_expected = REQUIRED_EXPECTED_KEYS - expected.keys()
        if missing_expected:
            die(f"{case_id}: expected missing keys: {sorted(missing_expected)}")
        if expected["truth_label"] not in ALLOWED_TRUTH:
            die(f"{case_id}: unknown truth label {expected['truth_label']!r}")
        for field in SEMANTIC_FIELDS:
            if not isinstance(expected[field], str) or not expected[field]:
                die(f"{case_id}: expected.{field} must be a non-empty string")

        if case["category"] in {"ontology", "cross_ontology"} and ontology_ids:
            inp = case["input"]
            refs: list[str] = []
            if "ontology_id" in inp and inp["ontology_id"] != "unknown":
                refs.append(inp["ontology_id"])
            if "ontology_ids" in inp:
                if not isinstance(inp["ontology_ids"], list):
                    die(f"{case_id}: ontology_ids must be an array")
                refs.extend(inp["ontology_ids"])
            unknown = sorted({ref for ref in refs if ref not in ontology_ids})
            if unknown:
                die(f"{case_id}: unknown ontology references: {unknown}")

        by_id[case_id] = case
        categories[case["category"]] += 1

    missing_categories = REQUIRED_CATEGORIES - categories.keys()
    if missing_categories:
        die(f"missing required categories: {sorted(missing_categories)}")

    print(f"CORPUS_OK cases={len(cases)} categories={len(categories)}")
    for category in sorted(categories):
        print(f"  {category}: {categories[category]}")
    return by_id


def score_candidate(by_id: dict[str, dict], rows: list[dict]) -> None:
    candidate: dict[str, dict] = {}
    for idx, row in enumerate(rows, 1):
        case_id = row.get("id")
        if not isinstance(case_id, str) or not case_id:
            die(f"candidate row #{idx}: missing non-empty id")
        if case_id in candidate:
            die(f"candidate duplicate id: {case_id}")
        candidate[case_id] = row

    unknown = sorted(set(candidate) - set(by_id))
    missing = sorted(set(by_id) - set(candidate))
    if unknown:
        die(f"candidate has unknown ids: {unknown}")
    if missing:
        die(f"candidate missing ids: {missing}")

    failures: list[str] = []
    for case_id in sorted(by_id):
        expected = by_id[case_id]["expected"]
        actual = candidate[case_id]
        for field in SEMANTIC_FIELDS:
            if actual.get(field) != expected[field]:
                failures.append(
                    f"{case_id}.{field}: expected={expected[field]!r} actual={actual.get(field)!r}"
                )

    passed = len(by_id) - len({f.split(".", 1)[0] for f in failures})
    print(f"SCORE passed={passed}/{len(by_id)} field_mismatches={len(failures)}")
    if failures:
        for failure in failures:
            print(f"  FAIL {failure}")
        raise SystemExit(1)
    print("CANDIDATE_OK exact semantic match")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--ontologies", type=Path)
    args = parser.parse_args()

    ontology_ids = load_ontologies(args.ontologies)
    cases = load_jsonl(args.corpus)
    by_id = validate_corpus(cases, ontology_ids)
    if args.candidate:
        score_candidate(by_id, load_jsonl(args.candidate))


if __name__ == "__main__":
    main()
