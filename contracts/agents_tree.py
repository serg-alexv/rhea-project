"""
Agent Tree — budget allocation for daily self-evolve cycle.

Rex (Opus 4.6) is the sole team lead. Makes all decisions.
Orion (GPT-5.3) and Gemini 3.1 are senior specialists — strong, but directed by Rex.
Sonnet workers write code within contracts. Haiku does mechanical ops.

Human controls max 2 agents directly (Rex + one senior when needed).
Everything else is Rex's internal delegation — invisible to human.
"""

from dataclasses import dataclass, field
from enum import Enum


class Tier(Enum):
    FRONTIER = "frontier"   # Opus 4.6, GPT-5.3, Gemini 3.1 — thinks, decides
    SONNET = "sonnet"       # builds code within contracts
    HAIKU = "haiku"         # moves files, commits, formats


@dataclass
class AgentBudget:
    max_turns: int
    max_file_reads: int
    max_file_writes: int
    can_spawn: bool = False
    allowed_tiers: tuple[Tier, ...] = (Tier.HAIKU,)


@dataclass
class AgentNode:
    name: str
    role: str
    tier: Tier
    model: str                      # actual model ID
    budget: AgentBudget
    children: list["AgentNode"] = field(default_factory=list)
    product: str | None = None

    def total_tree_turns(self) -> int:
        return self.budget.max_turns + sum(c.total_tree_turns() for c in self.children)


# ── The Tree ────────────────────────────────────────────────────

DAILY_EVOLVE_TREE = AgentNode(
    name="rex",
    role="team lead — decides what to improve, delegates, reviews",
    tier=Tier.FRONTIER,
    model="claude-opus-4-6",
    budget=AgentBudget(
        max_turns=15,
        max_file_reads=10,
        max_file_writes=3,
        can_spawn=True,
        allowed_tiers=(Tier.FRONTIER, Tier.SONNET, Tier.HAIKU),
    ),
    children=[
        # ── Senior specialists (frontier models) ────────
        AgentNode(
            name="orion",
            role="frontend, code review, leak detection, fast pattern matching",
            tier=Tier.FRONTIER,
            model="gpt-5.3",
            budget=AgentBudget(
                max_turns=20, max_file_reads=30, max_file_writes=15,
                can_spawn=True, allowed_tiers=(Tier.SONNET, Tier.HAIKU),
            ),
            product=None,  # cross-cutting — Rex assigns per task
        ),
        AgentNode(
            name="gemini",
            role="full-project analysis, long-context review, documentation",
            tier=Tier.FRONTIER,
            model="gemini-3.1",
            budget=AgentBudget(
                max_turns=15, max_file_reads=50, max_file_writes=10,
                can_spawn=True, allowed_tiers=(Tier.SONNET, Tier.HAIKU),
            ),
            product=None,  # cross-cutting — Rex assigns per task
        ),

        # ── Sonnet workers (one per product) ────────────
        AgentNode(
            name="consensus-dev",
            role="improve consensus accuracy within contract",
            tier=Tier.SONNET,
            model="claude-sonnet-4-6",
            budget=AgentBudget(max_turns=25, max_file_reads=15, max_file_writes=10),
            product="consensus",
        ),
        AgentNode(
            name="aletheia-dev",
            role="improve storage reliability, chain accuracy",
            tier=Tier.SONNET,
            model="claude-sonnet-4-6",
            budget=AgentBudget(max_turns=25, max_file_reads=15, max_file_writes=10),
            product="aletheia",
        ),
        AgentNode(
            name="ruliad-dev",
            role="improve verification depth, plugin quality",
            tier=Tier.SONNET,
            model="claude-sonnet-4-6",
            budget=AgentBudget(max_turns=25, max_file_reads=15, max_file_writes=10),
            product="ruliad",
        ),

        # ── Mechanical ──────────────────────────────────
        AgentNode(
            name="ops",
            role="git, formatting, file moves, cleanup",
            tier=Tier.HAIKU,
            model="claude-haiku-4-5",
            budget=AgentBudget(max_turns=10, max_file_reads=5, max_file_writes=15),
        ),
    ],
)


def print_tree(node: AgentNode, indent: int = 0):
    prefix = "  " * indent
    tier = node.tier.value.upper()
    budget = f"{node.budget.max_turns}t/{node.budget.max_file_reads}r/{node.budget.max_file_writes}w"
    prod = f" [{node.product}]" if node.product else ""
    print(f"{prefix}{node.name} ({tier}: {node.model}) — {budget}{prod}")
    print(f"{prefix}  {node.role}")
    for child in node.children:
        print_tree(child, indent + 1)


if __name__ == "__main__":
    print("\nAgent Tree — Daily Evolve Cycle\n")
    print_tree(DAILY_EVOLVE_TREE)
    total = DAILY_EVOLVE_TREE.total_tree_turns()

    frontier = DAILY_EVOLVE_TREE.budget.max_turns
    frontier += sum(c.budget.max_turns for c in DAILY_EVOLVE_TREE.children if c.tier == Tier.FRONTIER)
    sonnet = sum(c.budget.max_turns for c in DAILY_EVOLVE_TREE.children if c.tier == Tier.SONNET)
    haiku = sum(c.budget.max_turns for c in DAILY_EVOLVE_TREE.children if c.tier == Tier.HAIKU)

    print(f"\nTotal: {total} turns")
    print(f"  Frontier: {frontier}  (Rex 15 + Orion 20 + Gemini 15)")
    print(f"  Sonnet:   {sonnet}  (3 product devs × 25)")
    print(f"  Haiku:    {haiku}")
    print(f"\nHuman controls: Rex + (Orion | Gemini) = max 2")
