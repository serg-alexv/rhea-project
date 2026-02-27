"""
Contract: backend → rhea-remote

HTTP endpoints. rhea-remote knows these shapes and nothing else.
If you change these, the phone app breaks.
"""

from dataclasses import dataclass


# GET /health
@dataclass(frozen=True)
class HealthResponse:
    status: str                     # "ok" | "degraded" | "down"
    components: dict[str, str]      # component_name → status


# GET /aletheia/stats
@dataclass(frozen=True)
class StatsResponse:
    total_proofs: int
    total_hypotheses: int
    ontologies: dict[str, int]      # ontology_name → count
    recent_activity: int            # proofs in last 24h


# GET /aletheia/proofs, GET /aletheia/search?q=
@dataclass(frozen=True)
class ProofEntry:
    id: str
    title: str
    ontology: str
    tier: str                       # "proof" | "hypothesis"
    agreement_score: float
    confidence: float
    created_at: str                 # ISO 8601
    model_count: int


# POST /tribunal → response
@dataclass(frozen=True)
class TribunalResponse:
    consensus: str
    agreement_score: float
    confidence: float
    models: list[str]
    tier: str
    math_verification: dict[str, str] | None    # domain → verdict, nullable
