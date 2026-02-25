"""
Category Theory Plugin — Mathematical Universe for Ontology Explorer

Provides category-theoretic tools for hypothesis exploration:
  - Objects, morphisms, functors, natural transformations
  - Topos-theoretic semantics for logical frameworks
  - Adjunction detection between mathematical structures
  - Yoneda-style representability checks
  - Cross-universe mapping via functorial semantics
"""


def register_plugin(engine):
    from core.engine import MathUniversePlugin

    plugin = MathUniversePlugin(
        name="category_theory",
        version="0.1.0",
        description=(
            "Category theory and topos theory. Structural foundations for "
            "comparing formal systems via functors, adjunctions, and natural "
            "transformations. Enables systematic cross-domain mapping."
        ),
        category="foundations",
        represent=ct_represent,
        transform=ct_transform,
        verify=ct_verify,
        generate_hypotheses=ct_generate,
        cross_map=ct_cross_map,
        meta={
            "key_concepts": [
                "category", "functor", "natural_transformation", "adjunction",
                "limit", "colimit", "topos", "sheaf", "yoneda_embedding",
                "monad", "kan_extension", "enriched_category",
            ],
            "cross_maps_to": [
                "type_theory", "topology", "logic", "information_geometry",
            ],
        },
    )
    engine.registry.register(plugin)


def ct_represent(hypothesis):
    """Convert hypothesis to category-theoretic representation."""
    return {
        "framework": "category_theory",
        "objects": _extract_objects(hypothesis.statement),
        "morphisms": _extract_morphisms(hypothesis.statement),
        "diagrams": [],
        "commutative_conditions": [],
        "raw_statement": hypothesis.statement,
        "suggested_category": _suggest_ambient_category(hypothesis.statement),
    }


def ct_transform(representation, transform_type="functor"):
    """Apply category-theoretic transformation."""
    transforms = {
        "functor": "Map objects and morphisms preserving composition",
        "duality": "Reverse all morphisms (apply op functor)",
        "yoneda": "Embed into presheaf category via Yoneda lemma",
        "limit": "Take limit of the diagram",
        "adjunction": "Seek left/right adjoint of the primary functor",
    }
    return {
        "input": representation,
        "transform": transform_type,
        "description": transforms.get(transform_type, "Unknown transform"),
        "result_sketch": f"Apply {transform_type} to the structure",
    }


def ct_verify(hypothesis, representation=None):
    """Category-theoretic verification checks."""
    checks = []

    statement = hypothesis.statement.lower()

    # Check for well-formedness
    if any(kw in statement for kw in ["functor", "morphism", "natural transformation"]):
        checks.append({
            "check": "functoriality",
            "question": "Does the proposed mapping preserve composition and identities?",
            "status": "requires_proof",
        })

    if "adjunction" in statement or "adjoint" in statement:
        checks.append({
            "check": "adjunction_conditions",
            "question": "Are the unit and counit natural transformations well-defined?",
            "status": "requires_proof",
        })

    if "limit" in statement or "colimit" in statement:
        checks.append({
            "check": "universal_property",
            "question": "Does the claimed (co)limit satisfy the universal property?",
            "status": "requires_proof",
        })

    # Default: always check category axioms
    checks.append({
        "check": "category_axioms",
        "question": "Is the ambient category well-defined (associativity, identity)?",
        "status": "assumed_standard" if "Set" in hypothesis.statement or "Top" in hypothesis.statement else "requires_verification",
    })

    return {
        "framework": "category_theory",
        "checks": checks,
        "overall": "requires_proof" if any(c["status"] == "requires_proof" for c in checks) else "plausible",
        "lean4_formalization_hint": _lean4_hint(hypothesis),
    }


def ct_generate(seed, depth=3):
    """Generate category-theoretic hypotheses from a seed idea."""
    hypotheses = []

    # Level 1: Direct categorical framing
    hypotheses.append({
        "title": f"Categorical structure of: {seed[:50]}",
        "statement": (
            f"The phenomenon '{seed}' can be modeled as a category C where objects "
            f"represent states/configurations and morphisms represent valid transitions. "
            f"Composition captures sequential transitions."
        ),
        "tags": ["category_theory", "structural", "auto_generated"],
    })

    if depth >= 2:
        # Level 2: Functorial relationships
        hypotheses.append({
            "title": f"Functorial bridge: {seed[:40]} → observable",
            "statement": (
                f"There exists a functor F: C → Meas from the category modeling '{seed}' "
                f"to the category of measurable spaces, such that F preserves the "
                f"compositional structure and maps transitions to measurable functions."
            ),
            "tags": ["category_theory", "functor", "measurement", "auto_generated"],
        })

        hypotheses.append({
            "title": f"Adjunction in: {seed[:40]}",
            "statement": (
                f"The free-forgetful adjunction F ⊣ U between the structured category of "
                f"'{seed}' and its underlying set-theoretic representation reveals a canonical "
                f"way to add/remove structure while preserving essential information."
            ),
            "tags": ["category_theory", "adjunction", "auto_generated"],
        })

    if depth >= 3:
        # Level 3: Topos-theoretic and sheaf-theoretic
        hypotheses.append({
            "title": f"Topos of local models for: {seed[:35]}",
            "statement": (
                f"Local observations of '{seed}' form a sheaf on a suitable Grothendieck "
                f"topology, and the category of all such sheaves forms a topos that serves "
                f"as the 'universe of discourse' for reasoning about {seed}."
            ),
            "tags": ["category_theory", "topos", "sheaf", "deep", "auto_generated"],
        })

        hypotheses.append({
            "title": f"Yoneda principle for: {seed[:35]}",
            "statement": (
                f"By the Yoneda lemma, the identity of any state in the '{seed}' category "
                f"is fully determined by its relationships (morphisms) to all other states. "
                f"This implies that relational structure alone suffices for complete characterization."
            ),
            "tags": ["category_theory", "yoneda", "representability", "auto_generated"],
        })

    return hypotheses[:depth * 2]  # cap output


def ct_cross_map(from_universe, hypothesis, target_universe):
    """Map from category theory to another mathematical universe."""
    return {
        "source": "category_theory",
        "target": target_universe,
        "mapping_strategy": (
            "functors → continuous maps (topology), "
            "natural transformations → homotopies (homotopy theory), "
            "adjunctions → Galois connections (order theory), "
            "monoidal categories → type systems (proof theory), "
            "presheaves → statistical models (information geometry)"
        ),
    }


# --- Internal helpers ---

def _extract_objects(statement):
    """Heuristic extraction of potential categorical objects from a statement."""
    # Simple keyword extraction — real implementation would use NLP
    keywords = []
    for word in statement.split():
        cleaned = word.strip(".,;:()[]{}\"'")
        if cleaned and cleaned[0].isupper() and len(cleaned) > 2:
            keywords.append(cleaned)
    return keywords[:10]


def _extract_morphisms(statement):
    """Heuristic extraction of potential morphisms."""
    arrow_words = ["maps", "transforms", "relates", "connects", "induces",
                   "implies", "determines", "preserves", "extends"]
    found = [w for w in arrow_words if w in statement.lower()]
    return found


def _suggest_ambient_category(statement):
    s = statement.lower()
    if any(w in s for w in ["topology", "continuous", "open set"]):
        return "Top (topological spaces)"
    if any(w in s for w in ["group", "symmetry", "action"]):
        return "Grp (groups)"
    if any(w in s for w in ["vector", "linear", "dimension"]):
        return "Vect (vector spaces)"
    if any(w in s for w in ["measure", "probability", "distribution"]):
        return "Meas (measurable spaces)"
    if any(w in s for w in ["graph", "network", "node"]):
        return "Gph (graphs)"
    return "Set (sets and functions)"


def _lean4_hint(hypothesis):
    return (
        f"-- Lean4 formalization direction:\n"
        f"-- Model as a Category instance with appropriate Hom types\n"
        f"-- Use Mathlib.CategoryTheory for standard constructions\n"
        f"-- Key import: import Mathlib.CategoryTheory.Functor.Basic\n"
    )
