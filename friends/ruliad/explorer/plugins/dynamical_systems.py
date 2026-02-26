"""
Dynamical Systems Plugin — Mathematical Universe for Ontology Explorer

Models hypotheses as trajectories and attractors in phase space:
  - Phase portraits and flow analysis
  - Stability analysis (Lyapunov, structural)
  - Bifurcation detection (hypothesis landscape changes)
  - Ergodic theory for long-term behavior
  - Control theory intersection (MPC, feedback)
"""


def register_plugin(engine):
    from core.engine import MathUniversePlugin

    plugin = MathUniversePlugin(
        name="dynamical_systems",
        version="0.1.0",
        description=(
            "Dynamical systems: phase spaces, attractors, bifurcations, "
            "Lyapunov stability, ergodic theory. Models how hypotheses "
            "evolve over time, what states they converge to, and where "
            "qualitative behavior changes (bifurcation points)."
        ),
        category="analysis",
        represent=ds_represent,
        transform=ds_transform,
        verify=ds_verify,
        generate_hypotheses=ds_generate,
        cross_map=ds_cross_map,
        meta={
            "key_concepts": [
                "phase_space", "attractor", "repeller", "saddle_point",
                "bifurcation", "lyapunov_exponent", "ergodic", "chaotic",
                "invariant_manifold", "center_manifold", "normal_form",
                "structural_stability", "omega_limit_set",
            ],
            "cross_maps_to": [
                "category_theory", "information_geometry", "topology",
                "game_theory", "control_theory",
            ],
        },
    )
    engine.registry.register(plugin)


def ds_represent(hypothesis):
    return {
        "framework": "dynamical_systems",
        "state_space": _infer_state_space(hypothesis.statement),
        "dynamics_type": _infer_dynamics_type(hypothesis.statement),
        "time_type": "continuous",
        "key_structures": ["phase_portrait", "equilibria", "stability"],
        "raw_statement": hypothesis.statement,
    }


def ds_transform(representation, transform_type="stability_analysis"):
    transforms = {
        "stability_analysis": "Linearize around equilibria, compute eigenvalues, classify stability",
        "bifurcation_diagram": "Vary parameters, detect qualitative changes in phase portrait",
        "lyapunov_spectrum": "Compute Lyapunov exponents to detect chaos vs. regularity",
        "center_manifold_reduction": "Reduce dynamics near bifurcation to essential dimensions",
        "normal_form": "Transform to canonical form near a bifurcation point",
        "poincare_section": "Reduce continuous flow to discrete map via cross-section",
    }
    return {
        "input": representation,
        "transform": transform_type,
        "description": transforms.get(transform_type, "Unknown"),
    }


def ds_verify(hypothesis, representation=None):
    checks = []
    s = hypothesis.statement.lower()

    if "stable" in s or "stability" in s:
        checks.append({
            "check": "lyapunov_stability",
            "question": "Does a Lyapunov function exist for the claimed stable equilibrium?",
            "status": "requires_proof",
        })

    if "chaos" in s or "chaotic" in s:
        checks.append({
            "check": "positive_lyapunov_exponent",
            "question": "Is there a proven positive Lyapunov exponent, or is the claim based on numerical evidence alone?",
            "status": "requires_proof",
        })

    if "bifurcation" in s:
        checks.append({
            "check": "bifurcation_nondegeneracy",
            "question": "Are the non-degeneracy and transversality conditions for the claimed bifurcation satisfied?",
            "status": "requires_proof",
        })

    checks.append({
        "check": "existence_uniqueness",
        "question": "Do solutions exist and are they unique (Picard-Lindelöf)?",
        "status": "requires_verification",
    })

    return {
        "framework": "dynamical_systems",
        "checks": checks,
        "overall": "requires_proof" if any(c["status"] == "requires_proof" for c in checks) else "plausible",
    }


def ds_generate(seed, depth=3):
    hypotheses = []

    hypotheses.append({
        "title": f"Phase space model of: {seed[:45]}",
        "statement": (
            f"The phenomenon '{seed}' can be modeled as a dynamical system dx/dt = f(x) "
            f"on a phase space X. Key observables correspond to coordinates, and the "
            f"long-term behavior is governed by attractors of the flow."
        ),
        "tags": ["dynamical_systems", "phase_space", "auto_generated"],
    })

    if depth >= 2:
        hypotheses.append({
            "title": f"Bifurcation landscape of: {seed[:40]}",
            "statement": (
                f"The parameter space controlling '{seed}' contains bifurcation curves "
                f"where qualitative behavior changes. Identifying these bifurcations "
                f"reveals the 'tipping points' where the system transitions between "
                f"qualitatively different regimes."
            ),
            "tags": ["dynamical_systems", "bifurcation", "auto_generated"],
        })

        hypotheses.append({
            "title": f"Ergodic hypothesis for: {seed[:40]}",
            "statement": (
                f"Long-time averages of observables in the '{seed}' system equal "
                f"ensemble (phase-space) averages, implying ergodicity. This would "
                f"justify statistical approaches to predicting system behavior."
            ),
            "tags": ["dynamical_systems", "ergodic", "statistics", "auto_generated"],
        })

    if depth >= 3:
        hypotheses.append({
            "title": f"Strange attractor in: {seed[:35]}",
            "statement": (
                f"The dynamics of '{seed}' admit a strange attractor with fractal "
                f"dimension, exhibiting sensitive dependence on initial conditions "
                f"while remaining globally bounded. This explains apparent unpredictability "
                f"within deterministic dynamics."
            ),
            "tags": ["dynamical_systems", "chaos", "attractor", "deep", "auto_generated"],
        })

    return hypotheses[:depth * 2]


def ds_cross_map(from_universe, hypothesis, target_universe):
    return {
        "source": "dynamical_systems",
        "target": target_universe,
        "mapping_strategy": (
            "phase space → statistical manifold (info geometry), "
            "flows → functors between time categories (category theory), "
            "attractors → topological invariants (topology)"
        ),
    }


def _infer_state_space(statement):
    s = statement.lower()
    if any(w in s for w in ["oscillat", "periodic", "cycle"]):
        return "Likely: compact manifold (torus, sphere)"
    if any(w in s for w in ["growth", "decay", "population"]):
        return "Likely: positive orthant of R^n"
    return "R^n (Euclidean state space)"


def _infer_dynamics_type(statement):
    s = statement.lower()
    if "discrete" in s or "map" in s or "iteration" in s:
        return "discrete_map"
    if "stochastic" in s or "noise" in s or "random" in s:
        return "stochastic_ode"
    if "partial" in s or "pde" in s or "field" in s:
        return "pde"
    return "ode"
