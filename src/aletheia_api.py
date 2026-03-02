"""
aletheia_api.py — FastAPI router for the Aletheia proof library.

Thin wrapper around aletheia_pipeline.py. All storage goes to data/proof.db,
markdown artifacts land in friends/aletheia/{proofs,hypotheses}/.

Endpoints:
  POST /submit           — manual proof/hypothesis submission
  GET  /proofs           — list proofs (delegates to pipeline.get_recent)
  GET  /proofs/{id}      — get a specific proof (delegates to pipeline.get_proof)
  GET  /stats            — library statistics
  GET  /search           — keyword search
  GET  /chain/{id}       — proof chain (ancestors + descendants)
  POST /verify           — DB/filesystem consistency check
"""

import hashlib
import time
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import aletheia_pipeline as pipeline

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas (match pipeline's ProofArtifact fields)
# ─────────────────────────────────────────────────────────────────────────────

class ProofSubmitRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The claim or question being proved")
    consensus_text: str = Field(default="", description="Proof body / consensus text")
    ontology: str = Field(default="general", description="Ontology lens (e.g., 'chronobiology', 'math')")
    agreement_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Self-assessed agreement score")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence level")
    models: List[str] = Field(default_factory=lambda: ["manual"], description="Models used (or 'manual')")
    mode: str = Field(default="manual", description="Capture mode")


class ProofSummary(BaseModel):
    id: str
    type: Optional[str] = None
    tier: str
    prompt: str
    ontology: Optional[str] = None
    agreement_score: float
    confidence: float
    created_at: str


class ProofDetail(BaseModel):
    id: str
    type: Optional[str] = None
    tier: str
    prompt: str
    prompt_hash: Optional[str] = None
    ontology: Optional[str] = None
    mode: Optional[str] = None
    consensus_text: Optional[str] = None
    agreement_score: float
    confidence: float
    models: Optional[list] = None
    agreement_points: Optional[list] = None
    divergence_points: Optional[list] = None
    math_verification: Optional[dict] = None
    stance_summary: Optional[dict] = None
    analysis_method: Optional[str] = None
    rounds_completed: Optional[int] = None
    convergence_achieved: Optional[bool] = None
    parent_id: Optional[str] = None
    session_id: Optional[str] = None
    file_path: Optional[str] = None
    created_at: str
    tokens_total: Optional[int] = None
    latency_total_s: Optional[float] = None


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

aletheia_router = APIRouter(tags=["aletheia"])


@aletheia_router.post("/submit", response_model=ProofDetail, status_code=201)
def submit_proof(body: ProofSubmitRequest):
    """
    Manual proof/hypothesis submission.

    Classifies tier via pipeline.classify_tier(), writes markdown to
    friends/aletheia/{proofs,hypotheses}/, stores in data/proof.db.
    """
    now = datetime.now(timezone.utc).isoformat()
    proof_id = hashlib.sha256(f"{body.prompt}:{now}".encode()).hexdigest()[:24]
    prompt_hash = hashlib.sha256(body.prompt.encode()).hexdigest()[:16]

    tier = pipeline.classify_tier(body.agreement_score, body.confidence)

    proof_type = "consensus"
    if body.mode == "math":
        proof_type = "math"

    artifact = pipeline.ProofArtifact(
        id=proof_id,
        type=proof_type,
        tier=tier,
        prompt=body.prompt,
        prompt_hash=prompt_hash,
        ontology=body.ontology,
        mode=body.mode,
        consensus_text=body.consensus_text,
        agreement_score=body.agreement_score,
        confidence=body.confidence,
        models=body.models,
        agreement_points=[],
        divergence_points=[],
        math_verification={},
        stance_summary={},
        pairwise_similarity={},
        analysis_method="manual_submit",
        rounds_completed=0,
        convergence_achieved=False,
        parent_id=pipeline._find_parent(prompt_hash),
        session_id=None,
        file_path=None,
        created_at=now,
        tokens_total=0,
        latency_total_s=0.0,
        raw_responses=[],
    )

    # Write markdown (proofs/hypotheses only, noise gets logged without file)
    if tier != "noise":
        artifact.file_path = pipeline._write_markdown(artifact)

    # Store to DB
    pipeline._store_to_db(artifact)

    # Link to parent if found
    if artifact.parent_id:
        relation = "refines" if tier == "proof" else "extends"
        pipeline.link_proofs(artifact.parent_id, artifact.id, relation)

    return _artifact_to_detail(artifact)


@aletheia_router.get("/proofs", response_model=List[ProofSummary])
def list_proofs(
    tier: Optional[str] = Query(None, description="Filter by tier: proof|hypothesis"),
    limit: int = Query(50, ge=1, le=200),
):
    """List proofs from the library, ordered by recency."""
    results = pipeline.get_recent(limit=limit, tier_filter=tier)
    return results


@aletheia_router.get("/proofs/{proof_id}", response_model=ProofDetail)
def get_proof(proof_id: str):
    """Get a single proof by ID with full detail."""
    result = pipeline.get_proof(proof_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Proof '{proof_id}' not found")
    return result


@aletheia_router.get("/stats")
def get_stats():
    """Proof library aggregate statistics."""
    return pipeline.get_stats()


@aletheia_router.get("/search", response_model=List[ProofSummary])
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    tier: Optional[str] = Query(None),
):
    """Keyword search across proofs."""
    return pipeline.search_proofs(query=q, k=limit, tier_filter=tier)


@aletheia_router.get("/chain/{proof_id}")
def get_chain(proof_id: str):
    """Get proof chain (ancestors + descendants)."""
    return pipeline.get_chain(proof_id)


@aletheia_router.get("/dedup")
def dedup_check(
    q: str = Query(..., min_length=1, description="Query to check for existing proof"),
    threshold: float = Query(0.85, ge=0.0, le=1.0),
):
    """Pre-query: check if this question has already been answered."""
    return pipeline.check_existing(q, threshold=threshold)


@aletheia_router.get("/ontology/{ontology}", response_model=List[ProofSummary])
def get_by_ontology(
    ontology: str,
    limit: int = Query(50, ge=1, le=200),
):
    """Get all proofs for a specific ontology."""
    return pipeline.get_by_ontology(ontology, limit=limit)


@aletheia_router.get("/gems")
def list_gems(
    min_agreement: float = Query(0.6, ge=0.0, le=1.0, description="Minimum agreement score"),
    ontology: Optional[str] = Query(None, description="Filter by ontology domain"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Curated knowledge gems — verified proofs and hypotheses with high agreement.

    Gems are the exportable, sellable, distributable artifacts.
    Only proofs/hypotheses above the agreement threshold qualify.
    Noise is always excluded.
    """
    all_items = pipeline.get_recent(limit=500, tier_filter=None)
    gems = []
    for item in all_items:
        tier = item.get("tier", "")
        if tier == "noise":
            continue
        score = item.get("agreement_score", 0)
        if score < min_agreement:
            continue
        if ontology and item.get("ontology", "") != ontology:
            continue
        gems.append({
            **item,
            "gem_grade": "A" if score >= 0.85 else "B" if score >= 0.7 else "C",
        })
        if len(gems) >= limit:
            break
    return {
        "gems": gems,
        "count": len(gems),
        "min_agreement": min_agreement,
        "ontology_filter": ontology,
        "grade_scale": {"A": ">=85% agreement", "B": ">=70%", "C": ">=60%"},
    }


@aletheia_router.post("/verify")
def verify_consistency():
    """Verify DB <-> filesystem consistency (friends/aletheia/)."""
    return pipeline.verify()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _artifact_to_detail(a: pipeline.ProofArtifact) -> dict:
    """Convert ProofArtifact dataclass to ProofDetail-compatible dict."""
    return {
        "id": a.id,
        "type": a.type,
        "tier": a.tier,
        "prompt": a.prompt,
        "prompt_hash": a.prompt_hash,
        "ontology": a.ontology,
        "mode": a.mode,
        "consensus_text": a.consensus_text,
        "agreement_score": a.agreement_score,
        "confidence": a.confidence,
        "models": a.models,
        "agreement_points": a.agreement_points,
        "divergence_points": a.divergence_points,
        "math_verification": a.math_verification,
        "stance_summary": a.stance_summary,
        "analysis_method": a.analysis_method,
        "rounds_completed": a.rounds_completed,
        "convergence_achieved": a.convergence_achieved,
        "parent_id": a.parent_id,
        "session_id": a.session_id,
        "file_path": a.file_path,
        "created_at": a.created_at,
        "tokens_total": a.tokens_total,
        "latency_total_s": a.latency_total_s,
    }
