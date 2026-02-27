"""
Contract: consensus → aletheia

consensus produces this. aletheia consumes this. Nothing else crosses the boundary.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConsensusVerdict:
    """What consensus hands to aletheia. Frozen — consensus cannot mutate after handoff."""
    agreement_score: float          # 0.0–1.0
    confidence: float               # 0.0–1.0
    consensus_text: str
    agreement_points: tuple[str, ...]       # immutable
    divergence_points: tuple[str, ...]      # immutable
    stance_summary: dict[str, str]          # model_id → "affirmative"/"negative"/"qualified"/"neutral"
    model_count: int
    successful_count: int
    analysis_method: str

    def __post_init__(self):
        if not 0.0 <= self.agreement_score <= 1.0:
            raise ValueError(f"agreement_score must be 0.0–1.0, got {self.agreement_score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0–1.0, got {self.confidence}")
        if self.successful_count > self.model_count:
            raise ValueError(f"successful_count ({self.successful_count}) > model_count ({self.model_count})")


@dataclass(frozen=True)
class AletheiaReceipt:
    """What aletheia returns after storing. The only acknowledgment consensus sees."""
    artifact_id: str                # hex hash
    tier: str                       # "proof" | "hypothesis" | "noise"
    file_path: str                  # where the markdown landed

    def __post_init__(self):
        if self.tier not in ("proof", "hypothesis", "noise"):
            raise ValueError(f"tier must be proof/hypothesis/noise, got {self.tier}")
