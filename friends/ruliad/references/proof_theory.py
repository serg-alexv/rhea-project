"""
Proof Theory Plugin — Mathematical Universe for Ontology Explorer

The meta-mathematical layer that reasons about proofs themselves:
  - Curry-Howard correspondence (proofs as programs)
  - Cut elimination and proof normalization
  - Proof complexity and lower bounds
  - Realizability and extraction of computational content
  - Ordinal analysis for measuring proof strength
"""


def register_plugin(engine):
    from core.engine import MathUniversePlugin

    plugin = MathUniversePlugin(
        name="proof_theory",
        version="0.1.0",
        description=(
            "Proof theory and type theory. Meta-mathematical reasoning about "
            "proofs, computability, and logical strength. Curry-Howard "
            "correspondence, cut elimination, ordinal analysis."
        ),
        category="logic",
        represent=pt_represent,
        transform=pt_transform,
        verify=pt_verify,
        generate_hypotheses=pt_generate,
        cross_map=pt_cross_map,
        meta={
            "key_concepts": [
                "curry_howard", "cut_elimination", "normalization",
                "realizability", "ordinal_analysis", "proof_complexity",
                "sequent_calculus", "natural_deduction", "type_theory",
                "homotopy_type_theory", "univalence",
            ],
        },
    )
    engine.registry.register(plugin)


def pt_represent(hypothesis):
    return {
        "framework": "proof_theory",
        "logical_form": _to_logical_form(hypothesis.statement),
        "proof_system": "intuitionistic_type_theory",
        "curry_howard_type": "Proposition (to be inhabited by a proof term)",
        "raw_statement": hypothesis.statement,
    }


def pt_transform(representation, transform_type="curry_howard"):
    transforms = {
        "curry_howard": "Convert proposition to type, seek a program (proof term) inhabiting it",
        "cut_elimination": "Eliminate detours (cuts) from proof to get direct proof",
        "ordinal_analysis": "Measure the proof-theoretic strength required",
        "double_negation": "Apply Friedman/Gödel translation to extract constructive content",
    }
    return {
        "input": representation,
        "transform": transform_type,
        "description": transforms.get(transform_type, "Unknown"),
    }


def pt_verify(hypothesis, representation=None):
    checks = [{
        "check": "logical_consistency",
        "question": "Is the hypothesis consistent (no derivation of ⊥)?",
        "status": "requires_proof",
    }, {
        "check": "constructive_content",
        "question": "Can a constructive (intuitionistic) proof be given, or does it require classical logic?",
        "status": "requires_analysis",
    }, {
        "check": "proof_strength",
        "question": "What axiom system is needed? Does it go beyond ZFC?",
        "status": "requires_analysis",
    }]
    return {
        "framework": "proof_theory",
        "checks": checks,
        "overall": "requires_proof",
    }


def pt_generate(seed, depth=3):
    hypotheses = []
    hypotheses.append({
        "title": f"Curry-Howard type of: {seed[:45]}",
        "statement": (
            f"Under the Curry-Howard correspondence, the proposition '{seed}' "
            f"corresponds to a type T. A proof of this proposition is a program "
            f"of type T. The computational content of the proof reveals the "
            f"constructive information hidden in the claim."
        ),
        "tags": ["proof_theory", "curry_howard", "auto_generated"],
    })

    if depth >= 2:
        hypotheses.append({
            "title": f"Proof complexity of: {seed[:40]}",
            "statement": (
                f"The shortest proof of '{seed}' in a standard proof system "
                f"(resolution, Frege, bounded arithmetic) reveals the intrinsic "
                f"logical difficulty of the claim. A proof complexity lower bound "
                f"would show the claim is inherently hard to verify."
            ),
            "tags": ["proof_theory", "complexity", "auto_generated"],
        })

    return hypotheses[:depth * 2]


def pt_cross_map(from_universe, hypothesis, target_universe):
    return {
        "source": "proof_theory",
        "target": target_universe,
        "mapping_strategy": (
            "proofs → programs (computability theory), "
            "propositions → types → objects in a topos (category theory), "
            "proof normalization → rewriting dynamics (dynamical systems)"
        ),
    }


def _to_logical_form(statement):
    s = statement.lower()
    if "for all" in s or "every" in s: return "∀-statement (universal)"
    if "exists" in s or "there is" in s: return "∃-statement (existential)"
    if "implies" in s or "if" in s: return "→-statement (implication)"
    if "and" in s: return "∧-statement (conjunction)"
    if "or" in s: return "∨-statement (disjunction)"
    return "atomic proposition"
