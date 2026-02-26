"""
Information Geometry Plugin — Mathematical Universe for Ontology Explorer

Models hypotheses as points/distributions on statistical manifolds:
  - Fisher information metric for measuring distances between hypotheses
  - Geodesics on the statistical manifold = optimal inference paths
  - Divergence measures (KL, Rényi, f-divergence) for hypothesis comparison
  - Exponential/mixture families for natural parameterizations
  - Amari's dual connections for complementary perspectives
"""


def register_plugin(engine):
    from core.engine import MathUniversePlugin

    plugin = MathUniversePlugin(
        name="information_geometry",
        version="0.1.0",
        description=(
            "Information geometry: Fisher metrics, statistical manifolds, "
            "dual connections, divergence measures. Models how hypotheses "
            "relate as probability distributions on a manifold, with "
            "geodesics representing optimal inference paths."
        ),
        category="geometry",
        represent=ig_represent,
        transform=ig_transform,
        verify=ig_verify,
        generate_hypotheses=ig_generate,
        cross_map=ig_cross_map,
        meta={
            "key_concepts": [
                "fisher_information", "statistical_manifold", "geodesic",
                "kl_divergence", "exponential_family", "mixture_family",
                "dual_connection", "alpha_connection", "natural_gradient",
                "information_projection", "pythagorean_theorem",
            ],
            "cross_maps_to": [
                "category_theory", "dynamical_systems", "topology",
            ],
        },
    )
    engine.registry.register(plugin)


def ig_represent(hypothesis):
    """Represent hypothesis as a point on a statistical manifold."""
    return {
        "framework": "information_geometry",
        "manifold_type": _infer_manifold_type(hypothesis.statement),
        "parameterization": "natural",
        "fisher_metric_defined": False,
        "dual_structure": {
            "e_connection": "exponential connection (α=1)",
            "m_connection": "mixture connection (α=-1)",
            "levi_civita": "α=0 connection",
        },
        "raw_statement": hypothesis.statement,
    }


def ig_transform(representation, transform_type="natural_gradient"):
    """Apply information-geometric transformation."""
    transforms = {
        "natural_gradient": "Compute gradient in Fisher metric (steepest ascent on manifold)",
        "e_projection": "Project onto exponential subfamily (moment matching)",
        "m_projection": "Project onto mixture subfamily (information projection)",
        "geodesic": "Find geodesic between two hypothesis-distributions",
        "divergence": "Compute KL or α-divergence between hypothesis distributions",
    }
    return {
        "input": representation,
        "transform": transform_type,
        "description": transforms.get(transform_type, "Unknown transform"),
    }


def ig_verify(hypothesis, representation=None):
    """Information-geometric verification checks."""
    checks = []
    s = hypothesis.statement.lower()

    if "metric" in s or "distance" in s:
        checks.append({
            "check": "metric_positivity",
            "question": "Is the proposed metric positive-definite on the parameter space?",
            "status": "requires_proof",
        })

    if "divergence" in s:
        checks.append({
            "check": "divergence_properties",
            "question": "Does the divergence satisfy non-negativity and identity of indiscernibles?",
            "status": "requires_proof",
        })

    if "geodesic" in s:
        checks.append({
            "check": "geodesic_existence",
            "question": "Do geodesics exist and are they unique in the relevant connection?",
            "status": "requires_proof",
        })

    checks.append({
        "check": "manifold_regularity",
        "question": "Is the statistical model regular (full rank Fisher matrix)?",
        "status": "requires_verification",
    })

    return {
        "framework": "information_geometry",
        "checks": checks,
        "overall": "requires_proof" if any(c["status"] == "requires_proof" for c in checks) else "plausible",
    }


def ig_generate(seed, depth=3):
    """Generate information-geometric hypotheses from a seed."""
    hypotheses = []

    hypotheses.append({
        "title": f"Statistical manifold of: {seed[:45]}",
        "statement": (
            f"The space of models/explanations for '{seed}' forms a statistical manifold M "
            f"where each point θ represents a probability distribution P_θ over possible "
            f"observations. The Fisher information matrix G(θ) defines a Riemannian metric "
            f"that captures the intrinsic geometry of distinguishability."
        ),
        "tags": ["information_geometry", "manifold", "fisher", "auto_generated"],
    })

    if depth >= 2:
        hypotheses.append({
            "title": f"Natural gradient descent on: {seed[:40]}",
            "statement": (
                f"Optimization in the '{seed}' hypothesis space is more efficient when "
                f"following the natural gradient G(θ)⁻¹∇L(θ) rather than the Euclidean "
                f"gradient. This accounts for the curvature of the statistical manifold "
                f"and provides parameterization-invariant updates."
            ),
            "tags": ["information_geometry", "natural_gradient", "optimization", "auto_generated"],
        })

        hypotheses.append({
            "title": f"Dual structure in: {seed[:40]}",
            "statement": (
                f"The hypothesis space for '{seed}' admits Amari's dual connection structure: "
                f"the exponential connection (∇⁽ᵉ⁾) captures maximum entropy reasoning, "
                f"while the mixture connection (∇⁽ᵐ⁾) captures Bayesian updating. "
                f"The Pythagorean theorem of information geometry holds for projections."
            ),
            "tags": ["information_geometry", "duality", "amari", "auto_generated"],
        })

    if depth >= 3:
        hypotheses.append({
            "title": f"Information-geometric phase transition in: {seed[:30]}",
            "statement": (
                f"The statistical manifold for '{seed}' exhibits singular points where the "
                f"Fisher metric degenerates (rank drops). These singularities correspond to "
                f"phase transitions or critical phenomena in the underlying system, where "
                f"qualitatively different explanations become indistinguishable."
            ),
            "tags": ["information_geometry", "singularity", "phase_transition", "deep", "auto_generated"],
        })

    return hypotheses[:depth * 2]


def ig_cross_map(from_universe, hypothesis, target_universe):
    """Map to another mathematical universe."""
    return {
        "source": "information_geometry",
        "target": target_universe,
        "mapping_strategy": (
            f"Fisher metric → Riemannian metric (differential geometry), "
            f"exponential families → algebraic varieties (algebraic geometry), "
            f"statistical manifold → enriched category (category theory)"
        ),
    }


def _infer_manifold_type(statement):
    s = statement.lower()
    if "gaussian" in s or "normal" in s:
        return "Gaussian family (natural params: mean, precision)"
    if "exponential" in s:
        return "Exponential family"
    if "bernoulli" in s or "binary" in s:
        return "Bernoulli manifold (1-simplex)"
    if "multinomial" in s or "categorical" in s:
        return "Categorical manifold (k-simplex)"
    return "General parametric family"
