#!/usr/bin/env python3
"""
Contract enforcement tests.

These don't test logic. They test boundaries.
If consensus changes its output shape, this breaks.
If aletheia stops accepting the contract types, this breaks.
If ruliad returns unexpected domains, this breaks.

Run: python3 contracts/test_contracts.py
"""

from consensus_to_aletheia import ConsensusVerdict, AletheiaReceipt
from consensus_to_ruliad import VerificationRequest, VerificationResult, DOMAINS, VERDICTS
from backend_to_remote import HealthResponse, StatsResponse, ProofEntry, TribunalResponse
import sys

passed = 0
failed = 0


def check(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  [OK] {name}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        failed += 1


# ── consensus → aletheia ────────────────────────────────────────

def test_verdict_valid():
    v = ConsensusVerdict(
        agreement_score=0.87, confidence=0.78,
        consensus_text="Models agree on X.",
        agreement_points=("point A", "point B"),
        divergence_points=("point C",),
        stance_summary={"gpt-4o": "affirmative", "claude": "affirmative"},
        model_count=5, successful_count=5,
        analysis_method="tfidf_local",
    )
    assert v.agreement_score == 0.87
    assert isinstance(v.agreement_points, tuple), "agreement_points must be tuple (immutable)"

def test_verdict_rejects_bad_score():
    try:
        ConsensusVerdict(
            agreement_score=1.5, confidence=0.5,
            consensus_text="X", agreement_points=(), divergence_points=(),
            stance_summary={}, model_count=1, successful_count=1,
            analysis_method="test",
        )
        raise AssertionError("should have rejected score > 1.0")
    except ValueError:
        pass

def test_verdict_frozen():
    v = ConsensusVerdict(
        agreement_score=0.5, confidence=0.5,
        consensus_text="X", agreement_points=(), divergence_points=(),
        stance_summary={}, model_count=1, successful_count=1,
        analysis_method="test",
    )
    try:
        v.agreement_score = 0.9
        raise AssertionError("should be frozen")
    except AttributeError:
        pass

def test_receipt_valid():
    r = AletheiaReceipt(artifact_id="abc123", tier="proof", file_path="proofs/x/abc123.md")
    assert r.tier == "proof"

def test_receipt_rejects_bad_tier():
    try:
        AletheiaReceipt(artifact_id="abc", tier="maybe", file_path="x.md")
        raise AssertionError("should have rejected bad tier")
    except ValueError:
        pass

# ── consensus → ruliad ──────────────────────────────────────────

def test_verification_request_valid():
    r = VerificationRequest(prompt="Does X cause Y?", consensus_text="Yes, because Z.")
    assert r.prompt

def test_verification_request_rejects_empty():
    try:
        VerificationRequest(prompt="", consensus_text="X")
        raise AssertionError("should reject empty prompt")
    except ValueError:
        pass

def test_verification_result_valid():
    r = VerificationResult(verdicts={
        "proof_theory": "verified",
        "category_theory": "skipped",
        "dynamical_systems": "verified",
        "game_theory": "failed",
        "information_geometry": "skipped",
    })
    assert r.any_passed
    assert "proof_theory" in r.passed_domains

def test_verification_rejects_unknown_domain():
    try:
        VerificationResult(verdicts={"astrology": "verified"})
        raise AssertionError("should reject unknown domain")
    except ValueError:
        pass

def test_verification_rejects_unknown_verdict():
    try:
        VerificationResult(verdicts={"proof_theory": "maybe"})
        raise AssertionError("should reject unknown verdict")
    except ValueError:
        pass

def test_domains_complete():
    assert len(DOMAINS) == 5, f"expected 5 domains, got {len(DOMAINS)}"

# ── backend → remote ───────────────────────────────────────────

def test_health_response():
    h = HealthResponse(status="ok", components={"redis": "ok", "db": "ok"})
    assert h.status == "ok"

def test_stats_response():
    s = StatsResponse(total_proofs=10, total_hypotheses=5, ontologies={"bio": 8}, recent_activity=3)
    assert s.total_proofs == 10

def test_proof_entry():
    p = ProofEntry(
        id="abc", title="X causes Y", ontology="bio",
        tier="proof", agreement_score=0.9, confidence=0.85,
        created_at="2026-02-27T00:00:00Z", model_count=5,
    )
    assert p.tier == "proof"

def test_tribunal_response():
    t = TribunalResponse(
        consensus="X", agreement_score=0.8, confidence=0.7,
        models=["gpt-4o", "claude"], tier="hypothesis",
        math_verification={"proof_theory": "verified"},
    )
    assert t.math_verification is not None

def test_tribunal_response_null_math():
    t = TribunalResponse(
        consensus="X", agreement_score=0.5, confidence=0.4,
        models=["gpt-4o"], tier="noise", math_verification=None,
    )
    assert t.math_verification is None


# ── run ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Contract Enforcement Tests")
    print(f"  {'='*50}\n")

    tests = [fn for name, fn in list(globals().items()) if name.startswith("test_")]
    for fn in tests:
        check(fn.__name__, fn)

    print(f"\n  {'='*50}")
    print(f"  {passed}/{passed+failed} passed, {failed} failed")
    if failed:
        print(f"  CONTRACT VIOLATION — fix before merging\n")
        sys.exit(1)
    else:
        print(f"  All contracts hold.\n")
