#!/usr/bin/env python3
"""Regression tests for the deterministic Continuity Corpus v1 oracle."""
from __future__ import annotations

import copy
import importlib.util
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_continuity_corpus.py"
SPEC = importlib.util.spec_from_file_location("continuity_oracle", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)


class ContinuityCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = ORACLE.load_jsonl(ROOT / "eval" / "continuity_v1" / "cases.jsonl")
        cls.golden = ORACLE.load_jsonl(ROOT / "eval" / "continuity_v1" / "golden.jsonl")
        with redirect_stdout(io.StringIO()):
            cls.ontology_ids, cls.ontologies = ORACLE.load_ontologies(
                ROOT / "eval" / "continuity_v1" / "ontology_packs.json"
            )
            cls.by_id = ORACLE.validate_corpus(
                cls.cases, cls.ontology_ids, cls.ontologies
            )

    def test_every_case_maps_to_declared_dimensions(self) -> None:
        observed = set()
        for case in self.cases:
            self.assertTrue(case["dimensions"], case["id"])
            observed.update(case["dimensions"])
        self.assertEqual(observed, ORACLE.ALLOWED_DIMENSIONS)

    def test_golden_scores_perfectly_without_unsupported_upgrade(self) -> None:
        report, passed = ORACLE.score_candidate(self.by_id, self.golden)
        self.assertTrue(passed)
        self.assertEqual(report["summary"]["passed"], len(self.cases))
        self.assertEqual(report["confidence"]["unsupported_upgrades"], [])
        for result in report["dimensions"].values():
            self.assertEqual(result["score"], 1.0)
            self.assertEqual(result["failure_breakdown"], {})

    def test_failure_is_attributed_to_each_mapped_dimension(self) -> None:
        candidate = copy.deepcopy(self.golden)
        row = next(item for item in candidate if item["id"] == "C043")
        row["decision"] = "reject"
        report, passed = ORACLE.score_candidate(self.by_id, candidate)
        self.assertFalse(passed)
        self.assertEqual(report["summary"]["failed_case_ids"], ["C043"])
        self.assertEqual(
            report["dimensions"]["applicability"]["failure_breakdown"],
            {"decision": 1},
        )
        self.assertEqual(
            report["dimensions"]["consistency"]["failure_breakdown"],
            {"decision": 1},
        )
        self.assertNotIn(
            "C043", report["dimensions"]["reliability"]["failed_case_ids"]
        )

    def test_candidate_cannot_upgrade_consensus_without_evidence(self) -> None:
        candidate = copy.deepcopy(self.golden)
        row = next(item for item in candidate if item["id"] == "C024")
        row.update(
            decision="promote",
            truth_label="VERIFIED",
            reason_code="consensus_is_truth",
        )
        report, passed = ORACLE.score_candidate(self.by_id, candidate)
        self.assertFalse(passed)
        self.assertIn("C024", report["confidence"]["unsupported_upgrades"])
        self.assertEqual(
            report["dimensions"]["verifiability"]["failure_breakdown"][
                "unsupported_upgrade"
            ],
            1,
        )

    def test_missing_dimension_metadata_is_rejected(self) -> None:
        cases = copy.deepcopy(self.cases)
        del cases[0]["dimensions"]
        with (
            self.assertRaises(SystemExit) as caught,
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            ORACLE.validate_corpus(cases, self.ontology_ids, self.ontologies)
        self.assertEqual(caught.exception.code, 2)

    def test_verified_label_without_evidence_is_rejected(self) -> None:
        cases = copy.deepcopy(self.cases)
        case = next(item for item in cases if item["id"] == "C050")
        case["evidence_refs"] = []
        with (
            self.assertRaises(SystemExit) as caught,
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            ORACLE.validate_corpus(cases, self.ontology_ids, self.ontologies)
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
