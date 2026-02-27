#!/usr/bin/env python3
"""
seed_demo.py — Seed Aletheia + Ruliad with realistic demo data.

Creates 5 proofs and 3 hypotheses across different ontologies,
with proper tier classification, proof chains, and math verification.
Also populates the Ontology Explorer graph.

Usage:
    python3 scripts/seed_demo.py
    python3 scripts/seed_demo.py --clean   # wipe demo data first
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
import hashlib

from aletheia_pipeline import (
    _get_conn, _write_markdown, _store_to_db, link_proofs,
    ProofArtifact, PROOFS_DIR, HYPOTHESES_DIR, ROOT
)

# ═══════════════════════════════════════════════════════════════════════
# DEMO ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════

NOW = datetime.now(timezone.utc)

DEMO_PROOFS = [
    # ── PROOF 1: Chronobiology (existing domain, extends the manual proof) ──
    ProofArtifact(
        id="demo_chrono_melatonin_01",
        type="consensus",
        tier="proof",
        prompt="Does exogenous melatonin administration restore circadian IL-6 rhythmicity in rotating shift workers?",
        prompt_hash=hashlib.sha256(b"melatonin IL-6 shift workers").hexdigest()[:16],
        ontology="chronobiology",
        mode="tribunal",
        consensus_text=(
            "Five models agree: timed melatonin (0.5-3mg, 30min before target sleep onset) "
            "partially restores IL-6 circadian amplitude in shift workers. Effect size is "
            "moderate (Cohen's d ≈ 0.4-0.6). CRP reduction follows with 2-week lag. "
            "TNF-alpha response is inconsistent across studies. Critical caveat: light exposure "
            "timing must be co-managed; melatonin alone without light hygiene shows diminished effect."
        ),
        agreement_score=0.88,
        confidence=0.79,
        models=["claude-sonnet-4-20250514", "gpt-4o", "gemini-2.0-flash", "deepseek-chat", "llama-3.3-70b"],
        agreement_points=[
            "Timed melatonin partially restores IL-6 circadian amplitude",
            "CRP reduction follows IL-6 normalization with 2-week lag",
            "Light exposure co-management essential for full effect",
            "Dose range 0.5-3mg effective; higher doses not superior",
        ],
        divergence_points=[
            "TNF-alpha response inconsistent — may depend on individual TNF polymorphisms",
            "Duration of effect after cessation: 3 days (GPT) vs 7 days (Claude) vs unclear (Gemini)",
        ],
        math_verification={
            "domains_tested": ["dynamical_systems"],
            "verdicts": {"dynamical_systems": "verified"},
            "details": {
                "dynamical_systems": "Phase resetting curve analysis confirms melatonin acts as Type 1 PRC agent at low dose. Bifurcation analysis shows the shift worker's disrupted rhythm has a saddle-node on invariant circle (SNIC) bifurcation that melatonin can reverse."
            }
        },
        stance_summary={
            "claude-sonnet-4-20250514": "High confidence in IL-6 effect, cautious on TNF-alpha",
            "gpt-4o": "Agrees, emphasizes need for controlled light environment",
            "gemini-2.0-flash": "Confirms mechanism, adds chronotype as moderating variable",
            "deepseek-chat": "Agrees with caveats about study heterogeneity",
            "llama-3.3-70b": "Concurs, notes melatonin receptor polymorphism as potential confounder",
        },
        pairwise_similarity={"avg": 0.84, "min": 0.71, "max": 0.93},
        analysis_method="chairman_synthesis",
        rounds_completed=1,
        convergence_achieved=True,
        parent_id="0650a31a247b77e6a719f701",  # links to the manual proof
        session_id="demo-seed",
        file_path=None,
        created_at=(NOW - timedelta(hours=6)).isoformat(),
        tokens_total=4820,
        latency_total_s=12.3,
        raw_responses=[
            {"model": "claude-sonnet-4-20250514", "provider": "anthropic", "latency_s": 2.1, "tokens": 980, "text_preview": "Timed melatonin administration at 0.5-3mg..."},
            {"model": "gpt-4o", "provider": "openai", "latency_s": 1.8, "tokens": 1050, "text_preview": "Evidence supports partial restoration of IL-6..."},
            {"model": "gemini-2.0-flash", "provider": "google", "latency_s": 3.2, "tokens": 890, "text_preview": "Melatonin's phase-resetting capacity..."},
            {"model": "deepseek-chat", "provider": "deepseek", "latency_s": 2.5, "tokens": 960, "text_preview": "The meta-analytic evidence from rotating shift..."},
            {"model": "llama-3.3-70b", "provider": "openrouter", "latency_s": 2.7, "tokens": 940, "text_preview": "Exogenous melatonin at physiological doses..."},
        ],
    ),

    # ── PROOF 2: Drug Discovery (user's field) ──
    ProofArtifact(
        id="demo_drugdisc_allosteric_02",
        type="math",
        tier="proof",
        prompt="Can information geometry predict allosteric binding site locations from protein dynamics data alone, without crystallographic evidence?",
        prompt_hash=hashlib.sha256(b"information geometry allosteric binding").hexdigest()[:16],
        ontology="drug_discovery",
        mode="tribunal",
        consensus_text=(
            "Consensus: yes, with caveats. The Fisher information matrix computed from MD trajectory "
            "covariance identifies regions of high 'distinguishability' in conformational space. These "
            "regions correlate with known allosteric sites at ~72% recall. The method fails for "
            "cryptic sites that only appear under ligand-induced conformational change. "
            "Information-geometric geodesics between active/inactive conformations trace the "
            "allosteric communication pathway with higher accuracy than standard mutual information."
        ),
        agreement_score=0.85,
        confidence=0.82,
        models=["claude-opus-4-20250514", "gpt-4o", "gemini-2.0-flash", "deepseek-chat", "qwen-2.5-72b"],
        agreement_points=[
            "Fisher information from MD covariance identifies allosteric regions (~72% recall)",
            "Geodesics trace allosteric communication pathways better than mutual information",
            "Method fails for cryptic sites requiring ligand-induced conformational change",
            "Natural gradient on the conformational manifold = physically meaningful dynamics",
        ],
        divergence_points=[
            "Whether 72% recall is practically useful vs crystallographic methods",
            "Computational cost: feasible for small proteins (<300 residues), unclear for large complexes",
        ],
        math_verification={
            "domains_tested": ["information_geometry", "dynamical_systems"],
            "verdicts": {
                "information_geometry": "verified",
                "dynamical_systems": "verified",
            },
            "details": {
                "information_geometry": "Fisher metric on the conformational manifold is positive-definite when computed from sufficient MD frames (>10,000). The dual connection structure separates entropy-driven (e-connection) from enthalpy-driven (m-connection) contributions to allostery.",
                "dynamical_systems": "Linearized dynamics around the native state yield eigenvalues whose imaginary parts correspond to known hinge-bending and shear modes. Allosteric sites cluster at bifurcation-adjacent regions in parameter space.",
            }
        },
        stance_summary={
            "claude-opus-4-20250514": "Strong support, notes this extends Amari's framework to structural biology",
            "gpt-4o": "Agrees on principle, questions computational scaling",
            "gemini-2.0-flash": "Confirms, adds that Wasserstein geometry may be more robust for rare events",
            "deepseek-chat": "Agrees, cites recent protein language model embeddings as complementary",
            "qwen-2.5-72b": "Concurs, suggests validation against GPCR allosteric atlas",
        },
        pairwise_similarity={"avg": 0.81, "min": 0.68, "max": 0.91},
        analysis_method="chairman_synthesis",
        rounds_completed=1,
        convergence_achieved=True,
        parent_id=None,
        session_id="demo-seed",
        file_path=None,
        created_at=(NOW - timedelta(hours=4)).isoformat(),
        tokens_total=6340,
        latency_total_s=18.7,
        raw_responses=[
            {"model": "claude-opus-4-20250514", "provider": "anthropic", "latency_s": 4.2, "tokens": 1380, "text_preview": "The Fisher information metric computed from..."},
            {"model": "gpt-4o", "provider": "openai", "latency_s": 3.1, "tokens": 1290, "text_preview": "Applying information geometry to protein..."},
            {"model": "gemini-2.0-flash", "provider": "google", "latency_s": 3.8, "tokens": 1180, "text_preview": "The conformational ensemble from MD can be..."},
            {"model": "deepseek-chat", "provider": "deepseek", "latency_s": 3.4, "tokens": 1250, "text_preview": "Information-geometric analysis of protein..."},
            {"model": "qwen-2.5-72b", "provider": "openrouter", "latency_s": 4.2, "tokens": 1240, "text_preview": "Fisher information matrices from molecular..."},
        ],
    ),

    # ── PROOF 3: ICE consensus (multi-round) ──
    ProofArtifact(
        id="demo_ice_consciousness_03",
        type="ice",
        tier="proof",
        prompt="Is integrated information (Φ) a necessary condition for consciousness, or merely a correlate that tracks complexity?",
        prompt_hash=hashlib.sha256(b"integrated information consciousness phi").hexdigest()[:16],
        ontology="philosophy_of_mind",
        mode="ice",
        consensus_text=(
            "After 3 rounds of iterative critique: Φ is neither strictly necessary nor merely correlative. "
            "The converged position: Φ measures a specific type of causal integration that is "
            "*constitutive* of a particular class of conscious experience (the 'what it is like' "
            "of unified perception), but other forms of consciousness (e.g., minimal phenomenal "
            "experience, dreaming) may not require high Φ. The distinction between 'necessary for' "
            "and 'constitutive of' is the key clarification this tribunal produced."
        ),
        agreement_score=0.91,
        confidence=0.74,
        models=["claude-opus-4-20250514", "gpt-4o", "gemini-2.5-pro", "deepseek-reasoner", "llama-3.3-70b"],
        agreement_points=[
            "Φ is constitutive of unified perceptual consciousness, not consciousness in general",
            "Distinction between 'necessary for' and 'constitutive of' resolves apparent contradictions",
            "Minimal phenomenal experience may not require high Φ",
            "Φ correlates with reportable conscious content but the relationship is not identity",
        ],
        divergence_points=[
            "Whether Φ can be meaningfully computed for biological systems (DeepSeek dissents: combinatorial explosion)",
            "Whether 'constitutive' is a meaningful category or just rebranded correlation (GPT pushes back)",
        ],
        math_verification={
            "domains_tested": ["category_theory", "information_geometry"],
            "verdicts": {
                "category_theory": "partial",
                "information_geometry": "verified",
            },
            "details": {
                "category_theory": "The category of conscious systems (if well-defined) would need to be a topos to support internal logic. The functor from neural systems to Φ-values is not faithful — distinct neural configurations can yield identical Φ — so Φ alone cannot characterize the category.",
                "information_geometry": "Φ corresponds to the volume form of the Fisher information metric on the space of system states. High Φ = high curvature = states are highly distinguishable. This is formally verified but the interpretation gap (geometry → phenomenology) remains.",
            }
        },
        stance_summary={
            "claude-opus-4-20250514": "Favors 'constitutive' framing, strong on category-theoretic limits",
            "gpt-4o": "Pushes back: 'constitutive' may be unfalsifiable",
            "gemini-2.5-pro": "Agrees with convergence, adds computational neuroscience perspective",
            "deepseek-reasoner": "Dissents on computability of Φ, otherwise agrees",
            "llama-3.3-70b": "Concurs with majority, adds evolutionary argument for Φ as fitness proxy",
        },
        pairwise_similarity={"avg": 0.79, "min": 0.62, "max": 0.94},
        analysis_method="ice_convergence",
        rounds_completed=3,
        convergence_achieved=True,
        parent_id=None,
        session_id="demo-seed",
        file_path=None,
        created_at=(NOW - timedelta(hours=2)).isoformat(),
        tokens_total=14200,
        latency_total_s=45.6,
        raw_responses=[
            {"model": "claude-opus-4-20250514", "provider": "anthropic", "latency_s": 9.2, "tokens": 3100, "text_preview": "After three rounds of iterative refinement..."},
            {"model": "gpt-4o", "provider": "openai", "latency_s": 8.1, "tokens": 2900, "text_preview": "The iterative process reveals a crucial..."},
            {"model": "gemini-2.5-pro", "provider": "google", "latency_s": 10.3, "tokens": 2800, "text_preview": "Convergence achieved on the constitutive..."},
            {"model": "deepseek-reasoner", "provider": "deepseek", "latency_s": 9.8, "tokens": 2700, "text_preview": "While I agree with the converged position..."},
            {"model": "llama-3.3-70b", "provider": "openrouter", "latency_s": 8.2, "tokens": 2700, "text_preview": "The distinction between necessary and..."},
        ],
    ),
]

DEMO_HYPOTHESES = [
    # ── HYPOTHESIS 1: Speculative, high divergence ──
    ProofArtifact(
        id="demo_hyp_quantum_bio_01",
        type="divergence",
        tier="hypothesis",
        prompt="Do quantum coherence effects in tubulin microtubules play a functional role in anesthetic mechanisms?",
        prompt_hash=hashlib.sha256(b"quantum coherence tubulin anesthetic").hexdigest()[:16],
        ontology="quantum_biology",
        mode="tribunal",
        consensus_text=(
            "Models split 3:2. Majority position: quantum coherence in tubulin has been observed "
            "spectroscopically but its functional role in consciousness/anesthesia remains unproven. "
            "The decoherence timescale at biological temperature (~10⁻¹³s) is too short for "
            "functional computation. Minority position: recent experiments show unexpectedly long "
            "coherence in warm biological systems (photosynthesis precedent); tubulin's unique "
            "geometry may protect coherence via topological effects."
        ),
        agreement_score=0.58,
        confidence=0.51,
        models=["claude-sonnet-4-20250514", "gpt-4o", "gemini-2.0-flash", "deepseek-chat", "llama-3.3-70b"],
        agreement_points=[
            "Quantum coherence in tubulin has been observed spectroscopically",
            "Decoherence timescale at 37°C is the central challenge",
        ],
        divergence_points=[
            "Whether photosynthesis coherence precedent applies to neural systems",
            "Whether topological protection of coherence is physically plausible in tubulin",
            "Claude and DeepSeek skeptical; GPT and Gemini more open; Llama neutral",
        ],
        math_verification={
            "domains_tested": ["dynamical_systems"],
            "verdicts": {"dynamical_systems": "inconclusive"},
            "details": {
                "dynamical_systems": "The Lindblad master equation for tubulin-environment coupling gives decoherence times consistent with the skeptical position (~100fs). However, the model assumes Markovian noise; non-Markovian bath effects could extend coherence."
            }
        },
        stance_summary={
            "claude-sonnet-4-20250514": "Skeptical: insufficient evidence for functional role",
            "gpt-4o": "Open: cites recent experimental results on warm coherence",
            "gemini-2.0-flash": "Cautiously open: photosynthesis precedent is real",
            "deepseek-chat": "Skeptical: decoherence timescale argument is strong",
            "llama-3.3-70b": "Neutral: calls for more experimental data",
        },
        pairwise_similarity={"avg": 0.56, "min": 0.38, "max": 0.82},
        analysis_method="chairman_synthesis",
        rounds_completed=1,
        convergence_achieved=False,
        parent_id=None,
        session_id="demo-seed",
        file_path=None,
        created_at=(NOW - timedelta(hours=3)).isoformat(),
        tokens_total=5100,
        latency_total_s=14.8,
        raw_responses=[
            {"model": "claude-sonnet-4-20250514", "provider": "anthropic", "latency_s": 2.8, "tokens": 1050, "text_preview": "The Orch-OR theory remains speculative..."},
            {"model": "gpt-4o", "provider": "openai", "latency_s": 2.4, "tokens": 1100, "text_preview": "Recent work by the Hameroff group..."},
            {"model": "gemini-2.0-flash", "provider": "google", "latency_s": 3.5, "tokens": 970, "text_preview": "Quantum coherence has been confirmed in..."},
            {"model": "deepseek-chat", "provider": "deepseek", "latency_s": 2.9, "tokens": 1020, "text_preview": "The decoherence argument against functional..."},
            {"model": "llama-3.3-70b", "provider": "openrouter", "latency_s": 3.2, "tokens": 960, "text_preview": "The evidence is mixed. Spectroscopic..."},
        ],
    ),

    # ── HYPOTHESIS 2: Game theory applied to drug resistance ──
    ProofArtifact(
        id="demo_hyp_resistance_game_02",
        type="agreement",
        tier="hypothesis",
        prompt="Can evolutionary game theory predict antibiotic resistance emergence timelines from hospital prescribing data?",
        prompt_hash=hashlib.sha256(b"game theory antibiotic resistance prediction").hexdigest()[:16],
        ontology="epidemiology",
        mode="tribunal",
        consensus_text=(
            "Promising but unproven. The replicator dynamics model (evolutionary game theory) "
            "captures the competitive dynamics between susceptible and resistant strains. "
            "Prescribing data provides the 'payoff matrix' entries. However, prediction accuracy "
            "beyond 6 months is poor due to horizontal gene transfer events that act as "
            "'strategy mutations' outside the standard replicator framework. Extension to "
            "multi-population games (hospital wards as demes) improves accuracy to ~18 months."
        ),
        agreement_score=0.76,
        confidence=0.68,
        models=["claude-sonnet-4-20250514", "gpt-4o", "gemini-2.0-flash", "deepseek-chat", "qwen-2.5-72b"],
        agreement_points=[
            "Replicator dynamics captures basic resistance competition correctly",
            "Prescribing data can parametrize the payoff matrix",
            "Horizontal gene transfer breaks standard replicator assumptions",
            "Multi-deme extension improves prediction horizon to ~18 months",
        ],
        divergence_points=[
            "Whether 18-month prediction is clinically actionable",
            "Role of immigration (patient transfers) in destabilizing predictions",
        ],
        math_verification={
            "domains_tested": ["game_theory", "dynamical_systems"],
            "verdicts": {
                "game_theory": "verified",
                "dynamical_systems": "verified",
            },
            "details": {
                "game_theory": "The 2-player asymmetric game (susceptible vs resistant) has a mixed Nash equilibrium at the coexistence frequency. The ESS analysis shows resistance is evolutionarily stable when antibiotic pressure exceeds a critical threshold — consistent with clinical observations.",
                "dynamical_systems": "The replicator equation dx/dt = x(1-x)(f_R - f_S) with frequency-dependent fitness gives bifurcation at the critical prescribing rate. Confirmed via Lyapunov stability analysis of the coexistence equilibrium.",
            }
        },
        stance_summary={
            "claude-sonnet-4-20250514": "Supports with enthusiasm for the multi-deme extension",
            "gpt-4o": "Agrees on framework, questions data availability",
            "gemini-2.0-flash": "Confirms math, adds spatial game theory as refinement",
            "deepseek-chat": "Agrees, cites existing hospital simulation models",
            "qwen-2.5-72b": "Concurs, emphasizes need for validation against retrospective data",
        },
        pairwise_similarity={"avg": 0.74, "min": 0.61, "max": 0.88},
        analysis_method="chairman_synthesis",
        rounds_completed=1,
        convergence_achieved=False,
        parent_id=None,
        session_id="demo-seed",
        file_path=None,
        created_at=(NOW - timedelta(hours=1)).isoformat(),
        tokens_total=5600,
        latency_total_s=15.2,
        raw_responses=[
            {"model": "claude-sonnet-4-20250514", "provider": "anthropic", "latency_s": 2.9, "tokens": 1150, "text_preview": "Evolutionary game theory provides a natural..."},
            {"model": "gpt-4o", "provider": "openai", "latency_s": 2.5, "tokens": 1180, "text_preview": "The replicator dynamics framework for..."},
            {"model": "gemini-2.0-flash", "provider": "google", "latency_s": 3.6, "tokens": 1080, "text_preview": "Modeling antibiotic resistance as a..."},
            {"model": "deepseek-chat", "provider": "deepseek", "latency_s": 3.1, "tokens": 1100, "text_preview": "Hospital-level game-theoretic models of..."},
            {"model": "qwen-2.5-72b", "provider": "openrouter", "latency_s": 3.1, "tokens": 1090, "text_preview": "The evolutionary game theory approach to..."},
        ],
    ),
]


# ═══════════════════════════════════════════════════════════════════════
# SEED FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def clean_demo_data():
    """Remove all demo artifacts."""
    conn = _get_conn()
    conn.execute("DELETE FROM proofs WHERE session_id = 'demo-seed'")
    conn.execute("DELETE FROM proof_chains WHERE parent_id LIKE 'demo_%' OR child_id LIKE 'demo_%'")
    conn.commit()
    conn.close()

    # Remove demo markdown files
    for base in [PROOFS_DIR, HYPOTHESES_DIR]:
        if base.exists():
            for f in base.rglob("demo_*.md"):
                f.unlink()
                print(f"  Removed {f.relative_to(ROOT)}")
    print("  Demo data cleaned.")


def seed_proofs():
    """Seed all demo proofs and hypotheses."""
    all_artifacts = DEMO_PROOFS + DEMO_HYPOTHESES
    for artifact in all_artifacts:
        # Write markdown
        artifact.file_path = _write_markdown(artifact)
        # Store to DB
        _store_to_db(artifact)
        tier_label = artifact.tier.upper()
        print(f"  [{tier_label:10}] {artifact.agreement_score:.0%} | {artifact.ontology:20} | {artifact.prompt[:55]}...")

    # Create proof chains
    # melatonin proof extends the original chronobiology proof
    link_proofs("0650a31a247b77e6a719f701", "demo_chrono_melatonin_01", "extends")
    print(f"\n  Chain: 0650a31a... → demo_chrono_melatonin_01 (extends)")


def seed_ruliad_graph():
    """Seed the Ontology Explorer graph with demo hypotheses."""
    sys.path.insert(0, str(ROOT / "friends" / "ruliad" / "explorer"))

    try:
        from core.engine import OntologyEngine
    except ImportError:
        print("  [SKIP] Cannot import OntologyEngine — Ruliad explorer not in path")
        return

    engine = OntologyEngine(project_root=ROOT)

    # Load plugins
    plugins_dir = ROOT / "friends" / "ruliad" / "explorer" / "plugins"
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

    # Generate hypotheses from demo seeds
    seeds = [
        ("Circadian disruption amplifies neuroinflammatory cascades via IL-6/CRP crosstalk", ["dynamical_systems", "information_geometry"]),
        ("Allosteric communication in GPCRs follows information-geometric geodesics", ["information_geometry", "category_theory"]),
        ("Antibiotic resistance emergence follows evolutionary game dynamics with spatial structure", ["game_theory", "dynamical_systems"]),
    ]

    total = 0
    for seed_text, domains in seeds:
        generated = engine.explore(seed_text, domains=domains, depth=2)
        total += len(generated)
        print(f"  Explored: {seed_text[:50]}... → {len(generated)} hypotheses")

    print(f"\n  Ruliad graph: {engine.graph.stats()['total']} total hypotheses, {engine.graph.stats()['edges']} edges")


def print_summary():
    """Print what was seeded."""
    conn = _get_conn()
    stats = conn.execute("SELECT * FROM aletheia_stats").fetchone()
    conn.close()

    if stats:
        print(f"\n{'='*60}")
        print(f"  ALETHEIA LIBRARY")
        print(f"  Proofs:      {stats['proof_count']}")
        print(f"  Hypotheses:  {stats['hypothesis_count']}")
        print(f"  Noise:       {stats['noise_count']}")
        print(f"  Avg agree:   {(stats['avg_agreement'] or 0):.0%}")
        print(f"  Ontologies:  {stats['ontology_count']}")
        print(f"  Unique Qs:   {stats['unique_queries']}")
        print(f"  Tokens:      {(stats['total_tokens'] or 0):,}")
        print(f"{'='*60}")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n  Rhea Demo Data Seeder")
    print(f"  {'='*40}\n")

    if "--clean" in sys.argv:
        print("  Cleaning existing demo data...")
        clean_demo_data()
        if len(sys.argv) == 2:  # only --clean, no seed
            sys.exit(0)

    print("  Seeding Aletheia proofs + hypotheses...\n")
    seed_proofs()

    print("\n  Seeding Ruliad Ontology Explorer graph...\n")
    seed_ruliad_graph()

    print_summary()

    print(f"\n  Demo files written to:")
    print(f"    friends/aletheia/proofs/")
    print(f"    friends/aletheia/hypotheses/")
    print(f"    friends/ruliad/explorer/data/graph.json")
    print(f"\n  To view:")
    print(f"    python3 friends/ruliad/explorer/server.py  → http://localhost:8420")
    print(f"    python3 src/aletheia_pipeline.py stats")
    print(f"    python3 src/aletheia_pipeline.py recent")
    print()
