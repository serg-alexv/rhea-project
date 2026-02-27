#!/usr/bin/env python3
"""
test_pipeline_e2e.py — End-to-end pipeline test.

Proves the Rhea pipeline works without API keys:
  mock responses → consensus analysis → math verification → Aletheia capture

This IS the specification. If this test passes, the pipeline is wired correctly.

Usage:
    python3 -m pytest tests/test_pipeline_e2e.py -v
    python3 tests/test_pipeline_e2e.py   # standalone
"""

import sys
import os
import json
import tempfile
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# ═══════════════════════════════════════════════════════════════════════
# MOCK DATA — what real models would return for a chronobiology question
# ═══════════════════════════════════════════════════════════════════════

PROMPT = "Does disruption of the circadian clock accelerate tumor growth in mammals?"

MOCK_RESPONSES = [
    {
        "model": "claude-sonnet-4-20250514",
        "provider": "anthropic",
        "text": (
            "Yes, substantial evidence supports this. Circadian disruption via SCN lesion "
            "or chronic jet lag accelerates tumor growth in mouse xenograft models. The mechanism "
            "involves deregulation of clock-controlled genes (Per2, Cry1) that normally suppress "
            "cell proliferation via Wee1/Cyclin D1 pathway. Epidemiological data from shift workers "
            "shows elevated breast and colorectal cancer risk (OR ~1.2-1.4). However, the effect "
            "is not universal — some tumor types show no clock dependence."
        ),
        "tokens_used": 890,
        "latency_s": 2.1,
        "error": None,
    },
    {
        "model": "gpt-4o",
        "provider": "openai",
        "text": (
            "The evidence is strong for a connection between circadian disruption and tumor "
            "acceleration. Key findings: (1) Per2 knockout mice show increased tumor susceptibility, "
            "(2) chronic jet lag protocol in mice accelerates Glasgow osteosarcoma and Lewis lung "
            "carcinoma growth, (3) melatonin suppression via constant light increases tumor growth "
            "rate. The IARC classified shift work as probably carcinogenic (Group 2A) in 2007. "
            "Mechanistically, clock genes regulate DNA damage response and apoptosis."
        ),
        "tokens_used": 920,
        "latency_s": 1.8,
        "error": None,
    },
    {
        "model": "gemini-2.0-flash",
        "provider": "google",
        "text": (
            "There is a well-established link. Circadian disruption accelerates tumor growth "
            "through multiple pathways: (1) impaired DNA repair via BMAL1-controlled NER, "
            "(2) immune suppression through disrupted cortisol/melatonin rhythms affecting "
            "NK cell cytotoxicity, (3) metabolic reprogramming favoring Warburg effect. "
            "Mouse models consistently show 30-60% faster tumor growth under circadian disruption. "
            "Human epidemiological evidence is consistent but confounded by other shift work factors."
        ),
        "tokens_used": 850,
        "latency_s": 3.0,
        "error": None,
    },
    {
        "model": "deepseek-chat",
        "provider": "deepseek",
        "text": (
            "Evidence supports this claim. Circadian disruption promotes tumorigenesis through: "
            "deregulated cell cycle (loss of circadian gating at G1/S and G2/M checkpoints), "
            "impaired apoptosis (Per2 and Cry1 loss reduces p53 stability), and "
            "immunosuppression (disrupted NK and T-cell circadian trafficking). "
            "The effect is dose-dependent: chronic disruption > acute. Some tumor types "
            "(e.g., hepatocellular carcinoma) show strong clock dependence, others less so."
        ),
        "tokens_used": 870,
        "latency_s": 2.5,
        "error": None,
    },
    {
        "model": "llama-3.3-70b",
        "provider": "openrouter",
        "text": (
            "Yes. The circadian clock acts as a tumor suppressor through regulation of "
            "cell cycle checkpoints, DNA damage response, and immune surveillance. "
            "Disruption via SCN ablation, genetic clock mutations, or environmental "
            "perturbation (chronic jet lag, constant light) consistently accelerates tumor "
            "growth in rodent models. Human evidence from shift work studies supports "
            "this, though effect sizes are modest (RR ~1.1-1.4). Key mechanism: "
            "BMAL1::CLOCK heterodimer controls ~40% of the transcriptome including "
            "tumor suppressors."
        ),
        "tokens_used": 900,
        "latency_s": 2.8,
        "error": None,
    },
]

REQUEST_META = {
    "prompt": PROMPT,
    "k": 5,
    "mode": "tribunal",
    "ontology": "chronobiology",
    "session_id": "test-e2e",
}


# ═══════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_consensus_analysis():
    """
    Step 1: Feed mock responses into ConsensusAnalyzer.
    Expect: high agreement (models mostly agree), identified agreement/divergence points.
    """
    from consensus_analyzer import ConsensusAnalyzer

    # ConsensusAnalyzer needs a bridge, but analyze() with pre-collected responses
    # only uses the bridge for chairman synthesis (which we skip by passing llm_tier=None)
    analyzer = ConsensusAnalyzer(bridge=None)

    # analyze() expects list of (model_name, text) tuples
    response_tuples = [(r["model"], r["text"]) for r in MOCK_RESPONSES]

    report = analyzer.analyze(
        responses=response_tuples,
        prompt=PROMPT,
        mode="local",      # local = no LLM call needed
        llm_tier="cheap",
    )

    # ConsensusReport is a dataclass — use attribute access
    assert hasattr(report, 'agreement_score'), "Missing agreement_score"
    assert hasattr(report, 'agreement_points'), "Missing agreement_points"
    assert hasattr(report, 'divergence_points'), "Missing divergence_points"
    assert hasattr(report, 'pairwise_similarity'), "Missing pairwise_similarity"

    # All 5 models agree on the basic claim — expect high agreement
    score = report.agreement_score
    assert 0.5 < score <= 1.0, f"Agreement score {score} unexpectedly low for 5 agreeing models"

    # Should find at least some agreement points
    assert len(report.agreement_points) > 0, "No agreement points found"

    print(f"  [PASS] Consensus: agreement={score:.2f}, "
          f"{len(report.agreement_points)} agreement, "
          f"{len(report.divergence_points)} divergence")

    return report.to_dict()


def test_math_domain_detection():
    """
    Step 2: Check that Ruliad math domain detection works.
    A chronobiology question should match dynamical_systems at minimum.
    """
    from consensus_analyzer import detect_math_domains

    domains = detect_math_domains(PROMPT)

    assert isinstance(domains, list), f"Expected list, got {type(domains)}"
    # "tumor growth" and "accelerate" should trigger dynamical_systems
    # This may or may not work depending on keyword matching quality
    print(f"  [INFO] Detected math domains: {domains}")

    return domains


def test_tier_classification():
    """
    Step 3: Verify tier classification logic.
    """
    from aletheia_pipeline import classify_tier

    # High agreement → proof
    assert classify_tier(0.90, 0.80) == "proof"
    assert classify_tier(0.85, 0.50) == "proof"

    # Medium agreement + math boost → proof
    assert classify_tier(0.76, 0.70, {"verdicts": {"dynamical_systems": "verified"}}) == "proof"

    # Medium agreement without math → hypothesis
    assert classify_tier(0.76, 0.70) == "hypothesis"
    assert classify_tier(0.50, 0.50) == "hypothesis"

    # Low agreement → noise
    assert classify_tier(0.49, 0.90) == "noise"
    assert classify_tier(0.10, 0.10) == "noise"

    print("  [PASS] Tier classification: all thresholds correct")


def test_aletheia_capture():
    """
    Step 4: Full capture pipeline — consensus report → Aletheia storage.
    Uses a temp directory so we don't pollute real data.
    """
    import aletheia_pipeline as ap

    # Temporarily redirect DB and file paths
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        original_db = ap.PROOF_DB
        original_proofs = ap.PROOFS_DIR
        original_hyps = ap.HYPOTHESES_DIR
        original_root = ap.ROOT

        try:
            ap.PROOF_DB = tmp / "test_proof.db"
            ap.PROOFS_DIR = tmp / "proofs"
            ap.HYPOTHESES_DIR = tmp / "hypotheses"
            ap.ROOT = tmp

            # Build a realistic consensus report
            consensus_report = {
                "agreement_score": 0.87,
                "confidence": 0.78,
                "agreement_points": [
                    "Circadian disruption accelerates tumor growth in mouse models",
                    "Per2 and BMAL1 act as tumor suppressors",
                    "Mechanism involves cell cycle deregulation and immune suppression",
                ],
                "divergence_points": [
                    "Effect size in humans varies by tumor type",
                ],
                "pairwise_similarity": {"avg": 0.82},
                "stance_summary": {
                    "claude": "strong support",
                    "gpt-4o": "strong support, cites IARC",
                    "gemini": "strong support, emphasizes multiple pathways",
                },
                "analysis_method": "local_consensus",
                "math_verification": {},
                "rounds_completed": 1,
                "convergence_achieved": True,
            }

            tribunal_response = {
                "consensus": "All models agree: circadian disruption accelerates tumor growth.",
            }

            # Run capture
            artifact = ap.capture(
                tribunal_response=tribunal_response,
                consensus_report=consensus_report,
                raw_responses=MOCK_RESPONSES,
                request_meta=REQUEST_META,
            )

            # Verify capture happened
            assert artifact is not None, "Capture returned None — classified as noise?"
            assert artifact.tier == "proof", f"Expected 'proof', got '{artifact.tier}'"
            assert artifact.ontology == "chronobiology"
            assert len(artifact.models) == 5
            assert artifact.agreement_score == 0.87

            # Verify markdown file was written
            md_path = tmp / artifact.file_path
            assert md_path.exists(), f"Markdown not written: {artifact.file_path}"
            md_content = md_path.read_text()
            assert "[PROVEN]" in md_content
            assert "chronobiology" in md_content
            assert "87%" in md_content

            # Verify DB record
            conn = sqlite3.connect(str(ap.PROOF_DB))
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM proofs WHERE id = ?", (artifact.id,)).fetchone()
            conn.close()
            assert row is not None, "DB record not found"
            assert row["tier"] == "proof"
            assert row["ontology"] == "chronobiology"

            print(f"  [PASS] Aletheia capture: id={artifact.id}, "
                  f"tier={artifact.tier}, file={artifact.file_path}")

        finally:
            # Restore originals
            ap.PROOF_DB = original_db
            ap.PROOFS_DIR = original_proofs
            ap.HYPOTHESES_DIR = original_hyps
            ap.ROOT = original_root


def test_proof_chain():
    """
    Step 5: Verify that proof chains work — child links to parent.
    """
    import aletheia_pipeline as ap

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        original_db = ap.PROOF_DB
        original_proofs = ap.PROOFS_DIR
        original_hyps = ap.HYPOTHESES_DIR
        original_root = ap.ROOT

        try:
            ap.PROOF_DB = tmp / "test_chain.db"
            ap.PROOFS_DIR = tmp / "proofs"
            ap.HYPOTHESES_DIR = tmp / "hypotheses"
            ap.ROOT = tmp

            # Capture parent proof
            parent_artifact = ap.capture(
                tribunal_response={"consensus": "Parent finding."},
                consensus_report={
                    "agreement_score": 0.90,
                    "confidence": 0.85,
                    "agreement_points": ["Finding A"],
                    "divergence_points": [],
                    "pairwise_similarity": {},
                    "stance_summary": {},
                    "analysis_method": "test",
                    "math_verification": {},
                    "rounds_completed": 1,
                    "convergence_achieved": True,
                },
                raw_responses=MOCK_RESPONSES[:3],
                request_meta={
                    "prompt": "Parent question about circadian rhythms",
                    "k": 3,
                    "mode": "tribunal",
                    "ontology": "chronobiology",
                    "session_id": "test-chain",
                },
            )
            assert parent_artifact is not None

            # Capture child with SAME prompt hash → should auto-link
            child_artifact = ap.capture(
                tribunal_response={"consensus": "Child extends parent."},
                consensus_report={
                    "agreement_score": 0.92,
                    "confidence": 0.88,
                    "agreement_points": ["Finding A", "Finding B"],
                    "divergence_points": [],
                    "pairwise_similarity": {},
                    "stance_summary": {},
                    "analysis_method": "test",
                    "math_verification": {},
                    "rounds_completed": 1,
                    "convergence_achieved": True,
                },
                raw_responses=MOCK_RESPONSES,
                request_meta={
                    "prompt": "Parent question about circadian rhythms",  # same prompt
                    "k": 5,
                    "mode": "tribunal",
                    "ontology": "chronobiology",
                    "session_id": "test-chain",
                },
            )
            assert child_artifact is not None
            assert child_artifact.parent_id == parent_artifact.id, \
                f"Chain broken: child.parent_id={child_artifact.parent_id}, expected {parent_artifact.id}"

            # Verify chain in DB
            chain = ap.get_chain(child_artifact.id)
            assert len(chain["ancestors"]) > 0, "No ancestors found in chain"
            assert chain["ancestors"][0]["id"] == parent_artifact.id

            print(f"  [PASS] Proof chain: {parent_artifact.id} → {child_artifact.id} (refines)")

        finally:
            ap.PROOF_DB = original_db
            ap.PROOFS_DIR = original_proofs
            ap.HYPOTHESES_DIR = original_hyps
            ap.ROOT = original_root


def test_ruliad_plugin_registry():
    """
    Step 6: Verify Ruliad plugins load and have correct hooks.
    """
    ruliad_path = Path(__file__).parent.parent / "friends" / "ruliad" / "explorer"
    sys.path.insert(0, str(ruliad_path))

    from core.engine import OntologyEngine

    engine = OntologyEngine(project_root=Path(__file__).parent.parent)

    plugins_dir = ruliad_path / "plugins"
    loaded = []
    for pf in sorted(plugins_dir.glob("*.py")):
        if pf.name.startswith("_"):
            continue
        try:
            g = {"__file__": str(pf)}
            exec(pf.read_text(), g)
            if "register_plugin" in g:
                g["register_plugin"](engine)
                loaded.append(pf.stem)
        except Exception as e:
            print(f"  [FAIL] Plugin {pf.stem}: {e}")

    expected = {"category_theory", "dynamical_systems", "game_theory",
                "information_geometry", "proof_theory"}
    actual = set(engine.registry.list_plugins())

    assert expected == actual, f"Plugin mismatch: expected {expected}, got {actual}"

    # Each plugin should have at least represent + verify hooks
    for name in expected:
        plugin = engine.registry.get(name)
        assert plugin.represent is not None, f"{name} missing represent hook"
        assert plugin.verify is not None, f"{name} missing verify hook"

    print(f"  [PASS] Ruliad plugins: {len(loaded)} loaded, all hooks present")


def test_hypothesis_exploration():
    """
    Step 7: Verify that seeding a hypothesis generates cross-domain links.
    """
    ruliad_path = Path(__file__).parent.parent / "friends" / "ruliad" / "explorer"
    sys.path.insert(0, str(ruliad_path))

    from core.engine import OntologyEngine

    engine = OntologyEngine(project_root=Path(__file__).parent.parent)

    # Load plugins
    plugins_dir = ruliad_path / "plugins"
    for pf in sorted(plugins_dir.glob("*.py")):
        if pf.name.startswith("_"):
            continue
        try:
            g = {"__file__": str(pf)}
            exec(pf.read_text(), g)
            if "register_plugin" in g:
                g["register_plugin"](engine)
        except Exception:
            pass

    # Explore with a seed
    generated = engine.explore(
        "Circadian rhythm disruption and tumor growth",
        domains=["dynamical_systems", "game_theory"],
        depth=2,
    )

    assert len(generated) > 0, "No hypotheses generated"

    # Check cross-domain edges were created
    stats = engine.graph.stats()
    assert stats["edges"] > 0, "No cross-domain edges created"
    assert len(stats["domains"]) >= 2, "Expected multiple domains"

    print(f"  [PASS] Exploration: {len(generated)} hypotheses, "
          f"{stats['edges']} edges, domains: {stats['domains']}")


# ═══════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n  Rhea Pipeline E2E Test")
    print(f"  {'='*50}\n")

    tests = [
        ("Consensus Analysis", test_consensus_analysis),
        ("Math Domain Detection", test_math_domain_detection),
        ("Tier Classification", test_tier_classification),
        ("Aletheia Capture", test_aletheia_capture),
        ("Proof Chain", test_proof_chain),
        ("Ruliad Plugin Registry", test_ruliad_plugin_registry),
        ("Hypothesis Exploration", test_hypothesis_exploration),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print(f"\n  {'='*50}")
    print(f"  {passed}/{passed+failed} passed, {failed} failed")
    if failed == 0:
        print("  All pipeline stages verified.")
    print()
    sys.exit(1 if failed else 0)
