"""
Game Theory Plugin — Mathematical Universe for Ontology Explorer

Models hypotheses as strategic interactions:
  - Nash equilibria as stable hypothesis states
  - Evolutionary dynamics for hypothesis fitness
  - Mechanism design for hypothesis testing protocols
  - Signaling games for information verification
  - Bayesian games for incomplete information
"""


def register_plugin(engine):
    from core.engine import MathUniversePlugin

    plugin = MathUniversePlugin(
        name="game_theory",
        version="0.1.0",
        description=(
            "Game theory: strategic interactions, equilibria, evolutionary "
            "dynamics, mechanism design. Models hypotheses as players in "
            "epistemic games, where Nash equilibria represent stable "
            "knowledge states and deviations reveal weaknesses."
        ),
        category="strategic",
        represent=gt_represent,
        transform=gt_transform,
        verify=gt_verify,
        generate_hypotheses=gt_generate,
        cross_map=gt_cross_map,
        meta={
            "key_concepts": [
                "nash_equilibrium", "dominant_strategy", "pareto_optimal",
                "evolutionary_stable_strategy", "mechanism_design",
                "signaling_game", "bayesian_game", "auction",
                "cooperative_game", "shapley_value",
            ],
        },
    )
    engine.registry.register(plugin)


def gt_represent(hypothesis):
    return {
        "framework": "game_theory",
        "game_type": _infer_game_type(hypothesis.statement),
        "players": ["hypothesis_proponent", "red_team_critic", "neutral_observer"],
        "strategy_spaces": {
            "proponent": ["present_evidence", "strengthen_claim", "narrow_scope"],
            "critic": ["find_counterexample", "attack_assumptions", "propose_alternative"],
            "observer": ["accept", "reject", "request_more_evidence"],
        },
        "raw_statement": hypothesis.statement,
    }


def gt_transform(representation, transform_type="nash_analysis"):
    transforms = {
        "nash_analysis": "Find Nash equilibria of the hypothesis evaluation game",
        "evolutionary": "Apply replicator dynamics to hypothesis population",
        "mechanism_design": "Design an optimal hypothesis testing protocol",
        "auction": "Frame as information auction — what is this hypothesis worth?",
    }
    return {
        "input": representation,
        "transform": transform_type,
        "description": transforms.get(transform_type, "Unknown"),
    }


def gt_verify(hypothesis, representation=None):
    checks = [{
        "check": "strategic_stability",
        "question": "Is the hypothesis a Nash equilibrium? Could any agent improve by deviating?",
        "status": "requires_analysis",
    }, {
        "check": "information_completeness",
        "question": "Do all agents have the information needed to evaluate? Or is this a game of incomplete information?",
        "status": "requires_analysis",
    }]
    return {
        "framework": "game_theory",
        "checks": checks,
        "overall": "requires_analysis",
    }


def gt_generate(seed, depth=3):
    hypotheses = []
    hypotheses.append({
        "title": f"Epistemic game for: {seed[:45]}",
        "statement": (
            f"The evaluation of '{seed}' can be modeled as a Bayesian game where "
            f"each evaluator has private information (priors, expertise domain) "
            f"and must choose a strategy (accept, reject, investigate). A Bayesian "
            f"Nash equilibrium reveals the collectively rational assessment."
        ),
        "tags": ["game_theory", "bayesian", "epistemic", "auto_generated"],
    })

    if depth >= 2:
        hypotheses.append({
            "title": f"Evolutionary fitness of: {seed[:40]}",
            "statement": (
                f"In a population of competing hypotheses about '{seed}', the "
                f"evolutionarily stable strategy (ESS) corresponds to the hypothesis "
                f"that cannot be invaded by any mutant alternative. The replicator "
                f"dynamics dx_i/dt = x_i(f_i - f̄) governs hypothesis selection."
            ),
            "tags": ["game_theory", "evolutionary", "ESS", "auto_generated"],
        })

    return hypotheses[:depth * 2]


def gt_cross_map(from_universe, hypothesis, target_universe):
    return {
        "source": "game_theory",
        "target": target_universe,
        "mapping_strategy": "Nash equilibria → fixed points (dynamical systems), "
                            "strategy spaces → objects in a category (category theory)",
    }


def _infer_game_type(statement):
    s = statement.lower()
    if "cooperat" in s: return "cooperative"
    if "signal" in s: return "signaling"
    if "auction" in s: return "auction"
    if "evolution" in s: return "evolutionary"
    return "strategic_form"
