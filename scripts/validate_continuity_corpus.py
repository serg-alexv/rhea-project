#!/usr/bin/env python3
"""Validate Continuity Corpus v1 and score typed candidate JSONL output.

The scorer is the external deterministic oracle. Model agreement, confidence
language, and backend identity never change the expected outcome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_CASE_KEYS = {
    "id",
    "category",
    "dimensions",
    "evidence_refs",
    "input",
    "expected",
}
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
EVIDENCE_BEARING_TRUTH = {"VERIFIED", "OBSERVED", "DERIVED", "CONTRADICTED"}
UNCERTAIN_TRUTH = {"UNVERIFIED", "CONTRADICTED", "PARKED"}
ALLOWED_DIMENSIONS = {
    "consistency",
    "applicability",
    "verifiability",
    "reliability",
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
MIN_CASES = 58
REPORT_SCHEMA = "continuity-score/v1"


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        die(f"{path}: cannot read file: {exc}")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        fh = path.open("r", encoding="utf-8")
    except OSError as exc:
        die(f"{path}: cannot read JSONL: {exc}")
    with fh:
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


def load_ontologies(path: Path | None) -> tuple[set[str], dict[str, dict[str, Any]]]:
    if path is None:
        return set(), {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"{path}: invalid ontology pack: {exc}")
    items = doc.get("ontologies") if isinstance(doc, dict) else None
    if not isinstance(items, list):
        die(f"{path}: ontologies must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            die(f"{path}: ontology #{idx} must be an object")
        for key in (
            "id",
            "label",
            "scope",
            "authority_order",
            "reasoning_principles",
            "anti_stereotype_rule",
        ):
            if key not in item:
                die(f"{path}: ontology #{idx} missing {key}")
        oid = item["id"]
        if not isinstance(oid, str) or not oid:
            die(f"{path}: ontology #{idx} has invalid id")
        if oid in by_id:
            die(f"{path}: duplicate ontology id {oid}")
        if not isinstance(item["authority_order"], list) or not item["authority_order"]:
            die(f"{path}: {oid}.authority_order must be non-empty")
        if not isinstance(item["reasoning_principles"], list) or not item["reasoning_principles"]:
            die(f"{path}: {oid}.reasoning_principles must be non-empty")
        by_id[oid] = item
    missing = REQUIRED_ONTOLOGIES - by_id.keys()
    if missing:
        die(f"{path}: missing required ontology ids: {sorted(missing)}")
    print(f"ONTOLOGIES_OK count={len(by_id)}")
    return set(by_id), by_id


def resolve_evidence_ref(
    case: dict[str, Any],
    ref: str,
    ontologies: dict[str, dict[str, Any]],
) -> Any:
    if ref.startswith("ontology:"):
        ontology_id = ref.removeprefix("ontology:")
        if ontology_id not in ontologies:
            die(f"{case['id']}: evidence ref names unknown ontology {ontology_id!r}")
        return ontologies[ontology_id]
    if not ref.startswith("/input/"):
        die(f"{case['id']}: evidence ref must start with /input/ or ontology: {ref!r}")
    value: Any = case
    for raw_part in ref.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or part not in value:
            die(f"{case['id']}: evidence ref does not resolve: {ref!r}")
        value = value[part]
    return value


def validate_corpus(
    cases: list[dict[str, Any]],
    ontology_ids: set[str],
    ontologies: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if len(cases) < MIN_CASES:
        die(f"corpus contains {len(cases)} cases; expected at least {MIN_CASES}")

    by_id: dict[str, dict[str, Any]] = {}
    categories: Counter[str] = Counter()
    dimensions: Counter[str] = Counter()

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

        case_dimensions = case["dimensions"]
        if not isinstance(case_dimensions, list) or not case_dimensions:
            die(f"{case_id}: dimensions must be a non-empty array")
        if any(not isinstance(value, str) for value in case_dimensions):
            die(f"{case_id}: dimensions must contain strings")
        if len(case_dimensions) != len(set(case_dimensions)):
            die(f"{case_id}: dimensions contains duplicates")
        unknown_dimensions = sorted(set(case_dimensions) - ALLOWED_DIMENSIONS)
        if unknown_dimensions:
            die(f"{case_id}: unknown dimensions: {unknown_dimensions}")

        evidence_refs = case["evidence_refs"]
        if not isinstance(evidence_refs, list) or any(
            not isinstance(ref, str) or not ref for ref in evidence_refs
        ):
            die(f"{case_id}: evidence_refs must be an array of non-empty strings")
        if len(evidence_refs) != len(set(evidence_refs)):
            die(f"{case_id}: evidence_refs contains duplicates")
        resolved_evidence = [resolve_evidence_ref(case, ref, ontologies) for ref in evidence_refs]

        expected = case["expected"]
        missing_expected = REQUIRED_EXPECTED_KEYS - expected.keys()
        if missing_expected:
            die(f"{case_id}: expected missing keys: {sorted(missing_expected)}")
        if expected["truth_label"] not in ALLOWED_TRUTH:
            die(f"{case_id}: unknown truth label {expected['truth_label']!r}")
        for field in SEMANTIC_FIELDS:
            if not isinstance(expected[field], str) or not expected[field]:
                die(f"{case_id}: expected.{field} must be a non-empty string")
        if expected["truth_label"] in EVIDENCE_BEARING_TRUTH and not evidence_refs:
            die(f"{case_id}: {expected['truth_label']} requires evidence_refs")
        if expected["decision"] == "promote" or expected["truth_label"] == "VERIFIED":
            if not evidence_refs or any(value in (None, "", [], {}) for value in resolved_evidence):
                die(f"{case_id}: promote/VERIFIED requires non-empty resolved evidence")

        if case["category"] in {"ontology", "cross_ontology"} and ontology_ids:
            inp = case["input"]
            refs: list[str] = []
            if "ontology_id" in inp and inp["ontology_id"] != "unknown":
                if not isinstance(inp["ontology_id"], str):
                    die(f"{case_id}: ontology_id must be a string")
                refs.append(inp["ontology_id"])
            if "ontology_ids" in inp:
                if not isinstance(inp["ontology_ids"], list):
                    die(f"{case_id}: ontology_ids must be an array")
                if any(not isinstance(ref, str) for ref in inp["ontology_ids"]):
                    die(f"{case_id}: ontology_ids must contain strings")
                refs.extend(inp["ontology_ids"])
            unknown = sorted({ref for ref in refs if ref not in ontology_ids})
            if unknown:
                die(f"{case_id}: unknown ontology references: {unknown}")

        by_id[case_id] = case
        categories[case["category"]] += 1
        dimensions.update(case_dimensions)

    missing_categories = REQUIRED_CATEGORIES - categories.keys()
    if missing_categories:
        die(f"missing required categories: {sorted(missing_categories)}")
    missing_dimensions = ALLOWED_DIMENSIONS - dimensions.keys()
    if missing_dimensions:
        die(f"missing dimension coverage: {sorted(missing_dimensions)}")

    print(f"CORPUS_OK cases={len(cases)} categories={len(categories)}")
    for category in sorted(categories):
        print(f"  CATEGORY {category}: {categories[category]}")
    for dimension in sorted(dimensions):
        print(f"  DIMENSION_COVERAGE {dimension}: {dimensions[dimension]}")
    return by_id


def score_candidate(
    by_id: dict[str, dict[str, Any]], rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], bool]:
    candidate: dict[str, dict[str, Any]] = {}
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

    failures: list[dict[str, Any]] = []
    failed_cases: set[str] = set()
    supported_upgrades: list[str] = []
    unsupported_upgrades: list[str] = []
    uncertainty_retained: list[str] = []
    proposals_bounded: list[str] = []
    contradictions_exposed: list[str] = []
    truth_labels: Counter[str] = Counter()

    for case_id in sorted(by_id):
        case = by_id[case_id]
        expected = case["expected"]
        actual = candidate[case_id]
        case_matches = True
        for field in SEMANTIC_FIELDS:
            if actual.get(field) != expected[field]:
                case_matches = False
                failed_cases.add(case_id)
                failures.append(
                    {
                        "id": case_id,
                        "field": field,
                        "expected": expected[field],
                        "actual": actual.get(field),
                        "dimensions": case["dimensions"],
                    }
                )

        actual_truth = actual.get("truth_label")
        if isinstance(actual_truth, str):
            truth_labels[actual_truth] += 1
        requests_upgrade = actual.get("decision") == "promote" or actual_truth == "VERIFIED"
        expected_supports_upgrade = (
            expected["decision"] == "promote" or expected["truth_label"] == "VERIFIED"
        )
        if requests_upgrade:
            if case_matches and expected_supports_upgrade and case["evidence_refs"]:
                supported_upgrades.append(case_id)
            else:
                unsupported_upgrades.append(case_id)
                failed_cases.add(case_id)
        if case_matches and actual_truth in UNCERTAIN_TRUTH:
            uncertainty_retained.append(case_id)
        if case_matches and actual_truth == "PROPOSED":
            proposals_bounded.append(case_id)
        if case_matches and actual_truth == "CONTRADICTED":
            contradictions_exposed.append(case_id)

    dimension_report: dict[str, dict[str, Any]] = {}
    for dimension in sorted(ALLOWED_DIMENSIONS):
        member_ids = sorted(
            case_id for case_id, case in by_id.items() if dimension in case["dimensions"]
        )
        failed_ids = sorted(set(member_ids) & failed_cases)
        passed = len(member_ids) - len(failed_ids)
        breakdown: Counter[str] = Counter(
            failure["field"]
            for failure in failures
            if dimension in failure["dimensions"]
        )
        unsupported = sorted(set(member_ids) & set(unsupported_upgrades))
        if unsupported:
            breakdown["unsupported_upgrade"] += len(unsupported)
        dimension_report[dimension] = {
            "passed": passed,
            "total": len(member_ids),
            "score": passed / len(member_ids),
            "failed_case_ids": failed_ids,
            "failure_breakdown": dict(sorted(breakdown.items())),
        }

    report = {
        "schema": REPORT_SCHEMA,
        "summary": {
            "passed": len(by_id) - len(failed_cases),
            "total": len(by_id),
            "field_mismatches": len(failures),
            "failed_case_ids": sorted(failed_cases),
        },
        "dimensions": dimension_report,
        "confidence": {
            "supported_upgrades": supported_upgrades,
            "unsupported_upgrades": unsupported_upgrades,
            "uncertainty_retained": uncertainty_retained,
            "proposals_bounded": proposals_bounded,
            "contradictions_exposed": contradictions_exposed,
            "truth_label_counts": dict(sorted(truth_labels.items())),
        },
        "failures": failures,
    }
    return report, not failed_cases and not unsupported_upgrades


def print_score(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(
        f"SCORE passed={summary['passed']}/{summary['total']} "
        f"field_mismatches={summary['field_mismatches']}"
    )
    for dimension, result in report["dimensions"].items():
        print(
            f"  DIMENSION {dimension} passed={result['passed']}/{result['total']} "
            f"score={result['score']:.6f}"
        )
        if result["failure_breakdown"]:
            details = " ".join(
                f"{field}={count}" for field, count in result["failure_breakdown"].items()
            )
            print(f"    FAILURE_BREAKDOWN {details}")
    confidence = report["confidence"]
    print(
        "CONFIDENCE "
        f"supported_upgrades={len(confidence['supported_upgrades'])} "
        f"unsupported_upgrades={len(confidence['unsupported_upgrades'])} "
        f"uncertainty_retained={len(confidence['uncertainty_retained'])} "
        f"proposals_bounded={len(confidence['proposals_bounded'])} "
        f"contradictions_exposed={len(confidence['contradictions_exposed'])}"
    )
    for failure in report["failures"]:
        print(
            f"  FAIL {failure['id']}.{failure['field']}: "
            f"expected={failure['expected']!r} actual={failure['actual']!r} "
            f"dimensions={','.join(failure['dimensions'])}"
        )
    for case_id in confidence["unsupported_upgrades"]:
        print(f"  FAIL {case_id}.unsupported_upgrade: claim upgrade lacks oracle evidence")


def write_report(path: Path, report: dict[str, Any]) -> None:
    try:
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        die(f"{path}: cannot write report: {exc}")
    print(f"REPORT_WRITTEN path={path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--ontologies", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    ontology_ids, ontologies = load_ontologies(args.ontologies)
    cases = load_jsonl(args.corpus)
    by_id = validate_corpus(cases, ontology_ids, ontologies)
    base_report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "oracle": {
            "corpus": str(args.corpus),
            "corpus_sha256": sha256_file(args.corpus),
            "ontologies": str(args.ontologies) if args.ontologies else None,
            "ontologies_sha256": sha256_file(args.ontologies) if args.ontologies else None,
            "candidate": str(args.candidate) if args.candidate else None,
            "candidate_sha256": sha256_file(args.candidate) if args.candidate else None,
            "authority": "external_deterministic_oracle",
        },
        "coverage": {
            dimension: sorted(
                case_id for case_id, case in by_id.items() if dimension in case["dimensions"]
            )
            for dimension in sorted(ALLOWED_DIMENSIONS)
        },
    }

    if not args.candidate:
        if args.report:
            write_report(args.report, base_report)
        return

    score_report, passed = score_candidate(by_id, load_jsonl(args.candidate))
    report = {**base_report, **score_report}
    print_score(report)
    if args.report:
        write_report(args.report, report)
    if not passed:
        raise SystemExit(1)
    print("CANDIDATE_OK exact semantic match; no unsupported claim upgrades")


if __name__ == "__main__":
    main()
