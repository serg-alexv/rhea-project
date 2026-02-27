"""
Agent Tree — three autonomous pyramids under one team lead.

Rex (Opus 4.6) — team lead. Decides, delegates, reviews.
Orion (GPT-5.3) — second line. Owns a swarm (Codex workers, canvas agents).
Gemini 3.1 — second line. Owns a swarm (Jules workers, long-context analysts).

Rex does not see inside their swarms. Rex gives a task with a contract
and a budget. Gets back a result or "didn't fit". That's the interface.

Human controls max 2: Rex + (Orion | Gemini) when needed.
"""

from dataclasses import dataclass, field
from enum import Enum


class Tier(Enum):
    FRONTIER = "frontier"   # independent decision-maker with own swarm
    WORKER = "worker"       # executes within contract, no autonomy beyond it
    MECHANICAL = "mechanical"  # file ops, git, formatting


@dataclass(frozen=True)
class SwarmBudget:
    """What Rex allocates to a second-line pyramid per task."""
    max_hours: float            # wall clock — after this, result or nothing
    max_files_changed: int      # scope control — don't touch what's not yours
    product_scope: tuple[str, ...]  # which contracts this pyramid can operate in
    can_create_files: bool = True
    can_delete_files: bool = False  # destructive ops need Rex approval


@dataclass(frozen=True)
class TaskAssignment:
    """What crosses the boundary between Rex and a second-line leader."""
    target: str                 # "orion" | "gemini"
    contract: str               # which contract file governs this work
    objective: str              # what to achieve (not how)
    budget: SwarmBudget
    acceptance_test: str        # command that must pass for Rex to accept


@dataclass
class Pyramid:
    name: str
    model: str
    strengths: tuple[str, ...]
    default_budget: SwarmBudget
    internal_swarm: str         # description — Rex doesn't specify this

    def assign(self, objective: str, contract: str, test: str,
               budget: SwarmBudget | None = None) -> TaskAssignment:
        return TaskAssignment(
            target=self.name,
            contract=contract,
            objective=objective,
            budget=budget or self.default_budget,
            acceptance_test=test,
        )


# ── The Three Pyramids ──────────────────────────────────────────

REX = Pyramid(
    name="rex",
    model="claude-opus-4-6",
    strengths=("architecture", "contracts", "review", "long reasoning"),
    default_budget=SwarmBudget(
        max_hours=1.0, max_files_changed=5,
        product_scope=("consensus", "aletheia", "ruliad", "remote"),
    ),
    internal_swarm="Sonnet workers + Haiku ops via Claude Code Task tool",
)

ORION = Pyramid(
    name="orion",
    model="gpt-5.3",
    strengths=("frontend", "code review", "leak detection", "fast iteration"),
    default_budget=SwarmBudget(
        max_hours=2.0, max_files_changed=20,
        product_scope=("remote", "consensus"),  # frontend + consensus TypeScript port
    ),
    internal_swarm="Codex workers, canvas agents — Orion decides internally",
)

GEMINI = Pyramid(
    name="gemini",
    model="gemini-3.1",
    strengths=("long context", "full-project analysis", "documentation", "cross-reference"),
    default_budget=SwarmBudget(
        max_hours=2.0, max_files_changed=15,
        product_scope=("aletheia", "ruliad"),  # needs long context for proof chains + math plugins
    ),
    internal_swarm="Jules workers, long-context analysts — Gemini decides internally",
)

PYRAMIDS = {"rex": REX, "orion": ORION, "gemini": GEMINI}


# ── Daily Evolve Cycle ──────────────────────────────────────────

DAILY_CYCLE = [
    # Phase 1: Rex probes, decides what to improve
    {"agent": "rex", "action": "probe + decide", "turns": 15},

    # Phase 2: Rex assigns to pyramids (parallel)
    {"agent": "orion", "action": "assigned task within contract", "turns": "internal"},
    {"agent": "gemini", "action": "assigned task within contract", "turns": "internal"},

    # Phase 3: Rex reviews results against acceptance tests
    {"agent": "rex", "action": "review + accept/reject", "turns": 10},

    # Phase 4: Commit
    {"agent": "rex", "action": "commit accepted changes", "turns": 3},
]


if __name__ == "__main__":
    print("\nThree Pyramids\n")
    for name, p in PYRAMIDS.items():
        scope = ", ".join(p.default_budget.product_scope)
        print(f"  {p.name} ({p.model})")
        print(f"    strengths: {', '.join(p.strengths)}")
        print(f"    scope: {scope}")
        print(f"    swarm: {p.internal_swarm}")
        print()

    print("Daily cycle:")
    for phase in DAILY_CYCLE:
        print(f"  {phase['agent']:8s} → {phase['action']}")

    print(f"\nHuman controls: Rex + (Orion | Gemini) = max 2")
    print(f"Rex sees: task assignments + acceptance test results")
    print(f"Rex does NOT see: internal swarm decisions")
