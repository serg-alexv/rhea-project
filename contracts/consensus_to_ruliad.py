"""
Contract: consensus → ruliad

consensus provides text to verify. ruliad returns per-domain verdicts.
"""

from dataclasses import dataclass


DOMAINS = frozenset({
    "proof_theory",
    "category_theory",
    "dynamical_systems",
    "game_theory",
    "information_geometry",
})

VERDICTS = frozenset({"verified", "failed", "skipped"})


@dataclass(frozen=True)
class VerificationRequest:
    """What gets sent to ruliad for mathematical verification."""
    prompt: str                     # original question
    consensus_text: str             # synthesized answer from consensus

    def __post_init__(self):
        if not self.prompt.strip():
            raise ValueError("prompt cannot be empty")
        if not self.consensus_text.strip():
            raise ValueError("consensus_text cannot be empty")


@dataclass(frozen=True)
class VerificationResult:
    """What ruliad returns. One verdict per domain."""
    verdicts: dict[str, str]        # domain → "verified"/"failed"/"skipped"

    def __post_init__(self):
        for domain, verdict in self.verdicts.items():
            if domain not in DOMAINS:
                raise ValueError(f"unknown domain: {domain}. Valid: {DOMAINS}")
            if verdict not in VERDICTS:
                raise ValueError(f"unknown verdict: {verdict}. Valid: {VERDICTS}")

    @property
    def passed_domains(self) -> list[str]:
        return [d for d, v in self.verdicts.items() if v == "verified"]

    @property
    def any_passed(self) -> bool:
        return any(v == "verified" for v in self.verdicts.values())
