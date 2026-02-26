#!/usr/bin/env python3
"""
ontology_engine.py — Core engine for the Rhea Ontology Explorer

The engine manages:
  1. Hypothesis lifecycle (propose → verify → accept/reject)
  2. Mathematical universe plugin registry
  3. Three-layer verification pipeline
  4. Agent team orchestration for cross-disciplinary exploration
  5. Provenance tracking (every claim → evidence chain)

Design principles:
  - No claim accepted without multi-source verification
  - Every hypothesis has a formal "attack surface" for red-team agents
  - Mathematical universes are pluggable: each provides its own
    representation, transformation rules, and verification hooks
"""

import json
import uuid
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    CONSENSUS_PENDING = "consensus_pending"
    RED_TEAM_ATTACK = "red_team_attack"
    FORMAL_CHECK = "formal_check"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUSPENDED = "suspended"  # needs more evidence


class VerificationLayer(str, Enum):
    CONSENSUS = "multi_model_consensus"
    FORMAL = "formal_proof_check"
    RED_TEAM = "red_team_adversarial"


class Severity(str, Enum):
    CRITICAL = "critical"    # breaks the hypothesis entirely
    MAJOR = "major"          # significant weakness
    MINOR = "minor"          # edge case or nitpick
    INFO = "info"            # observation, not an attack


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Evidence:
    """A piece of evidence supporting or attacking a hypothesis."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    source: str = ""           # which model/agent/plugin produced this
    content: str = ""
    evidence_type: str = "support"  # support | attack | neutral
    severity: str = "info"
    confidence: float = 0.0    # 0-1 scale
    provenance: dict = field(default_factory=dict)  # full trace
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified_by: list = field(default_factory=list)  # which layers verified this


@dataclass
class Hypothesis:
    """A hypothesis in the ontology exploration graph."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    title: str = ""
    statement: str = ""
    domain: str = ""           # which mathematical universe
    status: str = HypothesisStatus.PROPOSED.value
    parent_id: Optional[str] = None  # derived from another hypothesis
    children: list = field(default_factory=list)
    evidence_for: list = field(default_factory=list)
    evidence_against: list = field(default_factory=list)
    verification_results: dict = field(default_factory=dict)
    consensus_score: float = 0.0
    red_team_score: float = 0.0  # 0 = no attacks survived, 1 = all attacks survived
    formal_proof_status: str = "unchecked"  # unchecked | verified | failed | partial
    tags: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    meta: dict = field(default_factory=dict)

    def content_hash(self) -> str:
        """Deterministic hash for deduplication."""
        return hashlib.sha256(f"{self.statement}|{self.domain}".encode()).hexdigest()[:16]


@dataclass
class MathUniversePlugin:
    """Registration record for a mathematical universe plugin."""
    name: str
    version: str = "0.1.0"
    description: str = ""
    category: str = "general"  # category_theory, topology, geometry, algebra, logic, etc.
    # Callable hooks — set at registration time
    represent: Optional[Callable] = None      # hypothesis → formal representation
    transform: Optional[Callable] = None      # apply universe-specific transforms
    verify: Optional[Callable] = None         # universe-specific verification
    generate_hypotheses: Optional[Callable] = None  # wild exploration
    cross_map: Optional[Callable] = None      # map to another universe
    meta: dict = field(default_factory=dict)


@dataclass
class AgentTeamConfig:
    """Configuration for an exploration agent team."""
    team_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    agents: list = field(default_factory=list)  # list of agent role dicts
    strategy: str = "parallel_then_synthesize"  # or "sequential_deepening", "adversarial_pairs"
    max_rounds: int = 5
    convergence_threshold: float = 0.75
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Plugin Registry
# ---------------------------------------------------------------------------

class PluginRegistry:
    """Registry for mathematical universe plugins."""

    def __init__(self):
        self._plugins: Dict[str, MathUniversePlugin] = {}
        self._cross_maps: Dict[str, Dict[str, Callable]] = {}  # from → {to → fn}

    def register(self, plugin: MathUniversePlugin):
        self._plugins[plugin.name] = plugin
        return self

    def get(self, name: str) -> Optional[MathUniversePlugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> List[str]:
        return list(self._plugins.keys())

    def register_cross_map(self, from_universe: str, to_universe: str, fn: Callable):
        if from_universe not in self._cross_maps:
            self._cross_maps[from_universe] = {}
        self._cross_maps[from_universe][to_universe] = fn

    def get_cross_map(self, from_u: str, to_u: str) -> Optional[Callable]:
        return self._cross_maps.get(from_u, {}).get(to_u)

    def info(self) -> dict:
        return {
            name: {
                "version": p.version,
                "description": p.description,
                "category": p.category,
                "hooks": [h for h in ["represent", "transform", "verify",
                                       "generate_hypotheses", "cross_map"]
                          if getattr(p, h) is not None]
            }
            for name, p in self._plugins.items()
        }


# ---------------------------------------------------------------------------
# Verification Pipeline
# ---------------------------------------------------------------------------

class VerificationPipeline:
    """Three-layer verification: consensus + formal + red-team."""

    def __init__(self, bridge_path: Optional[str] = None):
        self.bridge_path = bridge_path
        self.results_log: List[dict] = []

    def run_consensus(self, hypothesis: Hypothesis, models: int = 5,
                      tier: str = "balanced") -> dict:
        """Layer 1: Multi-model consensus via Rhea bridge tribunal."""
        prompt = self._build_consensus_prompt(hypothesis)
        result = {
            "layer": VerificationLayer.CONSENSUS.value,
            "hypothesis_id": hypothesis.id,
            "prompt": prompt,
            "models_requested": models,
            "tier": tier,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # Bridge call result will be populated by the orchestrator
            "status": "ready_to_execute",
            "command": f'python3 {self.bridge_path or "src/rhea_bridge.py"} '
                       f'tribunal "{prompt}" --k {models}'
        }
        self.results_log.append(result)
        return result

    def run_formal_check(self, hypothesis: Hypothesis,
                         plugin: Optional[MathUniversePlugin] = None) -> dict:
        """Layer 2: Formal proof checking (Lean4/Z3/plugin-specific)."""
        result = {
            "layer": VerificationLayer.FORMAL.value,
            "hypothesis_id": hypothesis.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ready_to_execute",
        }

        if plugin and plugin.verify:
            # Plugin provides its own verification
            result["method"] = f"plugin:{plugin.name}"
            result["formal_repr"] = (
                plugin.represent(hypothesis) if plugin.represent else hypothesis.statement
            )
        else:
            # Default: generate Lean4 proof sketch for manual verification
            result["method"] = "lean4_sketch"
            result["lean4_stub"] = self._generate_lean4_stub(hypothesis)

        self.results_log.append(result)
        return result

    def run_red_team(self, hypothesis: Hypothesis, num_attackers: int = 3,
                     attack_strategies: Optional[List[str]] = None) -> dict:
        """Layer 3: Red-team adversarial agents."""
        strategies = attack_strategies or [
            "find_counterexample",
            "attack_assumptions",
            "boundary_stress_test",
            "domain_mismatch_probe",
            "logical_consistency_check",
            "steelman_alternative",
        ]
        result = {
            "layer": VerificationLayer.RED_TEAM.value,
            "hypothesis_id": hypothesis.id,
            "num_attackers": num_attackers,
            "strategies": strategies[:num_attackers * 2],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ready_to_execute",
            "attack_prompts": [
                self._build_red_team_prompt(hypothesis, s)
                for s in strategies[:num_attackers * 2]
            ]
        }
        self.results_log.append(result)
        return result

    def full_verification(self, hypothesis: Hypothesis,
                          plugin: Optional[MathUniversePlugin] = None) -> dict:
        """Run all three layers and produce a verification report."""
        consensus = self.run_consensus(hypothesis)
        formal = self.run_formal_check(hypothesis, plugin)
        red_team = self.run_red_team(hypothesis)
        return {
            "hypothesis_id": hypothesis.id,
            "layers": {
                "consensus": consensus,
                "formal": formal,
                "red_team": red_team,
            },
            "overall_status": "pending_execution",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # --- Prompt builders ---

    def _build_consensus_prompt(self, h: Hypothesis) -> str:
        return (
            f"ONTOLOGY VERIFICATION REQUEST\n"
            f"Domain: {h.domain}\n"
            f"Hypothesis: {h.statement}\n\n"
            f"Evaluate this hypothesis. Consider:\n"
            f"1. Is the statement well-formed within its mathematical domain?\n"
            f"2. What evidence supports it? What evidence contradicts it?\n"
            f"3. Are there implicit assumptions that should be made explicit?\n"
            f"4. Rate your confidence (0-1) and explain.\n"
            f"5. If you disagree with the hypothesis, state your strongest counterargument."
        )

    def _build_red_team_prompt(self, h: Hypothesis, strategy: str) -> str:
        strategy_instructions = {
            "find_counterexample": (
                "Find a concrete counterexample that disproves this hypothesis. "
                "Be creative — look in unusual corners of the domain."
            ),
            "attack_assumptions": (
                "Identify every implicit assumption. For each, construct a scenario "
                "where that assumption fails and show the consequence."
            ),
            "boundary_stress_test": (
                "Push this hypothesis to its limits. What happens at extreme values, "
                "degenerate cases, infinite limits, or dimension boundaries?"
            ),
            "domain_mismatch_probe": (
                "Does this hypothesis accidentally assume properties specific to one "
                "mathematical universe that don't hold in others? Find the mismatch."
            ),
            "logical_consistency_check": (
                "Check for circular reasoning, undeclared axioms, scope creep, "
                "or category errors. Be ruthless."
            ),
            "steelman_alternative": (
                "Construct the strongest possible ALTERNATIVE hypothesis that explains "
                "the same phenomena but contradicts this one. Which is more parsimonious?"
            ),
        }
        instruction = strategy_instructions.get(strategy, f"Apply strategy: {strategy}")

        return (
            f"RED TEAM ATTACK — Strategy: {strategy}\n"
            f"Target hypothesis: {h.statement}\n"
            f"Domain: {h.domain}\n\n"
            f"YOUR MISSION: {instruction}\n\n"
            f"Rules:\n"
            f"- You MUST find a weakness. 'No issues found' is not acceptable.\n"
            f"- Rate severity: critical / major / minor / info\n"
            f"- Provide concrete evidence, not vague concerns.\n"
            f"- If the hypothesis survives your best attack, explain exactly why "
            f"it's robust and rate your attack strength (1-10)."
        )

    def _generate_lean4_stub(self, h: Hypothesis) -> str:
        safe_name = "".join(c if c.isalnum() else '_' for c in h.title[:40])
        return (
            f"-- Auto-generated Lean4 proof stub for: {h.title}\n"
            f"-- Hypothesis: {h.statement}\n"
            f"-- Domain: {h.domain}\n\n"
            f"theorem {safe_name} : sorry := by\n"
            f"  -- TODO: formalize and prove\n"
            f"  sorry\n"
        )


# ---------------------------------------------------------------------------
# Hypothesis Graph
# ---------------------------------------------------------------------------

class HypothesisGraph:
    """
    The central graph of all hypotheses being explored.
    Supports parent-child derivation chains and cross-universe links.
    """

    def __init__(self, persist_path: Optional[Path] = None):
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._edges: List[dict] = []  # {from, to, type, meta}
        self.persist_path = persist_path

    def add(self, hypothesis: Hypothesis) -> Hypothesis:
        # Dedup check
        content_hash = hypothesis.content_hash()
        for existing in self._hypotheses.values():
            if existing.content_hash() == content_hash:
                return existing  # already exists
        self._hypotheses[hypothesis.id] = hypothesis
        if hypothesis.parent_id and hypothesis.parent_id in self._hypotheses:
            parent = self._hypotheses[hypothesis.parent_id]
            if hypothesis.id not in parent.children:
                parent.children.append(hypothesis.id)
            self._edges.append({
                "from": hypothesis.parent_id,
                "to": hypothesis.id,
                "type": "derivation",
            })
        self._auto_persist()
        return hypothesis

    def get(self, hypothesis_id: str) -> Optional[Hypothesis]:
        return self._hypotheses.get(hypothesis_id)

    def update_status(self, hypothesis_id: str, status: HypothesisStatus):
        h = self._hypotheses.get(hypothesis_id)
        if h:
            h.status = status.value
            h.updated_at = datetime.now(timezone.utc).isoformat()
            self._auto_persist()

    def add_evidence(self, hypothesis_id: str, evidence: Evidence):
        h = self._hypotheses.get(hypothesis_id)
        if not h:
            return
        if evidence.evidence_type == "support":
            h.evidence_for.append(asdict(evidence))
        elif evidence.evidence_type == "attack":
            h.evidence_against.append(asdict(evidence))
        h.updated_at = datetime.now(timezone.utc).isoformat()
        self._auto_persist()

    def link(self, from_id: str, to_id: str, link_type: str = "related", meta: dict = None):
        self._edges.append({
            "from": from_id, "to": to_id,
            "type": link_type, "meta": meta or {}
        })
        self._auto_persist()

    def all_hypotheses(self) -> List[Hypothesis]:
        return list(self._hypotheses.values())

    def stats(self) -> dict:
        statuses = {}
        for h in self._hypotheses.values():
            statuses[h.status] = statuses.get(h.status, 0) + 1
        return {
            "total": len(self._hypotheses),
            "edges": len(self._edges),
            "by_status": statuses,
            "domains": list(set(h.domain for h in self._hypotheses.values())),
        }

    def to_json(self) -> str:
        return json.dumps({
            "hypotheses": {k: asdict(v) for k, v in self._hypotheses.items()},
            "edges": self._edges,
            "stats": self.stats(),
        }, indent=2, default=str)

    def export_for_viz(self) -> dict:
        """Export in a format ready for D3/vis.js visualization."""
        nodes = []
        for h in self._hypotheses.values():
            nodes.append({
                "id": h.id,
                "label": h.title or h.statement[:50],
                "status": h.status,
                "domain": h.domain,
                "consensus": h.consensus_score,
                "red_team": h.red_team_score,
                "evidence_for": len(h.evidence_for),
                "evidence_against": len(h.evidence_against),
            })
        edges = [
            {"from": e["from"], "to": e["to"], "type": e["type"]}
            for e in self._edges
        ]
        return {"nodes": nodes, "edges": edges}

    def _auto_persist(self):
        if self.persist_path:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            self.persist_path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "HypothesisGraph":
        graph = cls(persist_path=path)
        if path.exists():
            data = json.loads(path.read_text())
            for hid, hdata in data.get("hypotheses", {}).items():
                h = Hypothesis(**{k: v for k, v in hdata.items()
                                  if k in Hypothesis.__dataclass_fields__})
                graph._hypotheses[hid] = h
            graph._edges = data.get("edges", [])
        return graph


# ---------------------------------------------------------------------------
# Ontology Explorer Engine (main coordinator)
# ---------------------------------------------------------------------------

class OntologyEngine:
    """
    Top-level coordinator for ontology exploration.
    Manages plugins, hypothesis graph, verification pipeline, and agent teams.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(".")
        self.registry = PluginRegistry()
        self.graph = HypothesisGraph(
            persist_path=self.project_root / "rhea-ontology-explorer" / "data" / "graph.json"
        )
        bridge_path = self.project_root / "src" / "rhea_bridge.py"
        self.verifier = VerificationPipeline(
            bridge_path=str(bridge_path) if bridge_path.exists() else None
        )
        self.agent_teams: Dict[str, AgentTeamConfig] = {}
        self._exploration_log: List[dict] = []

    def propose(self, title: str, statement: str, domain: str,
                parent_id: Optional[str] = None, tags: list = None) -> Hypothesis:
        """Propose a new hypothesis for exploration."""
        h = Hypothesis(
            title=title,
            statement=statement,
            domain=domain,
            parent_id=parent_id,
            tags=tags or [],
        )
        h = self.graph.add(h)
        self._log("propose", h.id, {"title": title, "domain": domain})
        return h

    def verify(self, hypothesis_id: str) -> dict:
        """Run full 3-layer verification on a hypothesis."""
        h = self.graph.get(hypothesis_id)
        if not h:
            return {"error": f"Hypothesis {hypothesis_id} not found"}

        self.graph.update_status(hypothesis_id, HypothesisStatus.UNDER_REVIEW)
        plugin = self.registry.get(h.domain)
        report = self.verifier.full_verification(h, plugin)

        h.verification_results = report
        h.updated_at = datetime.now(timezone.utc).isoformat()
        self._log("verify", h.id, {"layers": list(report["layers"].keys())})
        return report

    def explore(self, seed: str, domains: Optional[List[str]] = None,
                depth: int = 3) -> List[Hypothesis]:
        """
        Cross-disciplinary wild exploration from a seed idea.
        Each registered plugin generates hypotheses, then they're cross-linked.
        """
        domains = domains or self.registry.list_plugins()
        generated = []

        for domain_name in domains:
            plugin = self.registry.get(domain_name)
            if plugin and plugin.generate_hypotheses:
                new_hypotheses = plugin.generate_hypotheses(seed, depth)
                for h_data in (new_hypotheses or []):
                    h = self.propose(
                        title=h_data.get("title", f"{domain_name} exploration"),
                        statement=h_data.get("statement", seed),
                        domain=domain_name,
                        tags=h_data.get("tags", ["auto_generated", "exploration"]),
                    )
                    generated.append(h)

        # Cross-link hypotheses from different domains
        for i, h1 in enumerate(generated):
            for h2 in generated[i+1:]:
                if h1.domain != h2.domain:
                    self.graph.link(h1.id, h2.id, "cross_domain")

        self._log("explore", None, {
            "seed": seed, "domains": domains,
            "generated": len(generated)
        })
        return generated

    def register_agent_team(self, config: AgentTeamConfig):
        self.agent_teams[config.team_id] = config

    def status(self) -> dict:
        return {
            "graph": self.graph.stats(),
            "plugins": self.registry.info(),
            "agent_teams": len(self.agent_teams),
            "verification_log": len(self.verifier.results_log),
            "exploration_log": len(self._exploration_log),
        }

    def _log(self, action: str, hypothesis_id: Optional[str], meta: dict):
        self._exploration_log.append({
            "action": action,
            "hypothesis_id": hypothesis_id,
            "meta": meta,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
