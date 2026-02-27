"""
Agent Tree — budget allocation for daily self-evolve cycle.

Each agent has a role, a model tier, and a turn budget.
The tree enforces that strategic work stays on Opus,
implementation on Sonnet, mechanics on Haiku.
No agent can exceed its budget. No agent can call a higher tier.
"""

from dataclasses import dataclass, field
from enum import Enum


class Tier(Enum):
    OPUS = "opus"           # thinks
    SONNET = "sonnet"       # builds
    HAIKU = "haiku"         # moves


@dataclass
class AgentBudget:
    max_turns: int              # hard cap on agentic round-trips
    max_file_reads: int         # cap on Read tool calls
    max_file_writes: int        # cap on Write/Edit calls
    can_spawn: bool = False     # can this agent spawn sub-agents?
    allowed_tiers: tuple[Tier, ...] = (Tier.HAIKU,)  # tiers it can spawn


@dataclass
class AgentNode:
    name: str
    role: str
    tier: Tier
    budget: AgentBudget
    children: list["AgentNode"] = field(default_factory=list)
    product: str | None = None  # which contract boundary it operates within

    def total_tree_turns(self) -> int:
        return self.budget.max_turns + sum(c.total_tree_turns() for c in self.children)


# ── The Tree ────────────────────────────────────────────────────

DAILY_EVOLVE_TREE = AgentNode(
    name="rex",
    role="coordinator — reads probe results, decides what to improve, delegates",
    tier=Tier.OPUS,
    budget=AgentBudget(
        max_turns=15,
        max_file_reads=10,
        max_file_writes=3,      # only contracts and MEMORY
        can_spawn=True,
        allowed_tiers=(Tier.SONNET, Tier.HAIKU),
    ),
    children=[
        # ── Probe agent: finds weaknesses ───────────────
        AgentNode(
            name="probe",
            role="run tests, measure coverage, find lowest-scoring component",
            tier=Tier.SONNET,
            budget=AgentBudget(max_turns=20, max_file_reads=30, max_file_writes=0),
            product=None,  # cross-cutting — reads all products
        ),

        # ── Per-product implementors ────────────────────
        AgentNode(
            name="consensus-dev",
            role="improve consensus accuracy within contract",
            tier=Tier.SONNET,
            budget=AgentBudget(
                max_turns=25, max_file_reads=15, max_file_writes=10,
                can_spawn=True, allowed_tiers=(Tier.HAIKU,),
            ),
            product="consensus",
            children=[
                AgentNode(
                    name="consensus-fmt",
                    role="formatting, imports, file moves",
                    tier=Tier.HAIKU,
                    budget=AgentBudget(max_turns=10, max_file_reads=5, max_file_writes=10),
                    product="consensus",
                ),
            ],
        ),
        AgentNode(
            name="aletheia-dev",
            role="improve storage reliability, chain accuracy within contract",
            tier=Tier.SONNET,
            budget=AgentBudget(
                max_turns=25, max_file_reads=15, max_file_writes=10,
                can_spawn=True, allowed_tiers=(Tier.HAIKU,),
            ),
            product="aletheia",
            children=[
                AgentNode(
                    name="aletheia-fmt",
                    role="formatting, imports, file moves",
                    tier=Tier.HAIKU,
                    budget=AgentBudget(max_turns=10, max_file_reads=5, max_file_writes=10),
                    product="aletheia",
                ),
            ],
        ),
        AgentNode(
            name="ruliad-dev",
            role="improve verification depth within contract",
            tier=Tier.SONNET,
            budget=AgentBudget(
                max_turns=25, max_file_reads=15, max_file_writes=10,
                can_spawn=True, allowed_tiers=(Tier.HAIKU,),
            ),
            product="ruliad",
            children=[
                AgentNode(
                    name="ruliad-fmt",
                    role="formatting, imports, file moves",
                    tier=Tier.HAIKU,
                    budget=AgentBudget(max_turns=10, max_file_reads=5, max_file_writes=10),
                    product="ruliad",
                ),
            ],
        ),

        # ── Reviewer: checks contracts after changes ────
        AgentNode(
            name="reviewer",
            role="run contract tests, verify no boundary violations",
            tier=Tier.SONNET,
            budget=AgentBudget(max_turns=10, max_file_reads=20, max_file_writes=0),
            product=None,  # cross-cutting
        ),

        # ── Committer: mechanical git work ──────────────
        AgentNode(
            name="committer",
            role="stage, commit, push — nothing else",
            tier=Tier.HAIKU,
            budget=AgentBudget(max_turns=5, max_file_reads=0, max_file_writes=0),
        ),
    ],
)


def print_tree(node: AgentNode, indent: int = 0):
    prefix = "  " * indent
    tier_label = node.tier.value.upper()
    budget = f"{node.budget.max_turns}t/{node.budget.max_file_reads}r/{node.budget.max_file_writes}w"
    product = f" [{node.product}]" if node.product else ""
    print(f"{prefix}{node.name} ({tier_label}) — {budget}{product}")
    print(f"{prefix}  {node.role}")
    for child in node.children:
        print_tree(child, indent + 1)


if __name__ == "__main__":
    print("\nAgent Tree — Daily Evolve Cycle\n")
    print_tree(DAILY_EVOLVE_TREE)
    total = DAILY_EVOLVE_TREE.total_tree_turns()
    print(f"\nTotal budget: {total} turns across tree")
    print(f"Opus turns: {DAILY_EVOLVE_TREE.budget.max_turns} (coordinator only)")
    sonnet = sum(c.budget.max_turns for c in DAILY_EVOLVE_TREE.children if c.tier == Tier.SONNET)
    haiku = sum(c.budget.max_turns for c in DAILY_EVOLVE_TREE.children if c.tier == Tier.HAIKU)
    # include nested haiku
    for c in DAILY_EVOLVE_TREE.children:
        for gc in c.children:
            if gc.tier == Tier.HAIKU:
                haiku += gc.budget.max_turns
    print(f"Sonnet turns: {sonnet}")
    print(f"Haiku turns: {haiku}")
