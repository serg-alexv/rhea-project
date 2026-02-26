"""
Proof Theory Plugin — Mathematical Universe for Ontology Explorer

The meta-mathematical layer that reasons about proofs themselves:
  - Curry-Howard correspondence (proofs as programs)
  - Cut elimination and proof normalization
  - Proof complexity and lower bounds
  - Realizability and extraction of computational content
  - Ordinal analysis for measuring proof strength
"""

import re

try:
    import sympy
    from sympy import symbols, And, Or, Not, Implies, to_cnf
    from sympy.logic.inference import satisfiable
    _SYMPY_AVAILABLE = True
except ImportError:
    _SYMPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helpers: formula parsing
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset({
    "If", "Then", "And", "Or", "Not", "The", "A", "An",
    "That", "This", "Is", "Are", "In", "Of", "For", "To",
    "It", "We", "All", "Every", "No", "Some",
})


def _extract_atoms(statement):
    """
    Return a list of unique capitalised words as propositional atoms,
    excluding grammatical stop-words and connective keywords.
    """
    words = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', statement)
    seen = {}
    result = []
    for w in words:
        if w in _STOP_WORDS:
            continue
        if w not in seen:
            seen[w] = True
            result.append(w)
    return result


def _parse_formula(statement):
    """
    Parse a natural-language propositional statement into a sympy formula.

    Heuristic rule precedence (applied left-to-right on sentence fragments):
      1. "if <A> then <B>"  →  Implies(A, B)
      2. "not <A>"          →  Not(A)
      3. "<A> and <B>"      →  And(A, B)
      4. "<A> or <B>"       →  Or(A, B)
      5. Fallback           →  single Symbol for the whole statement
    """
    if not _SYMPY_AVAILABLE:
        return None, []

    atom_names = _extract_atoms(statement)
    if not atom_names:
        # No capitalised words — manufacture a single atom from the statement.
        safe = re.sub(r'\W+', '_', statement.strip())[:32] or "P"
        atom_names = [safe]

    sym_map = {name: symbols(name) for name in atom_names}
    s = statement.lower()

    try:
        # --- if…then ---
        m = re.search(r'\bif\b(.+?)\bthen\b(.+)', s)
        if m:
            ante_txt = m.group(1).strip()
            cons_txt = m.group(2).strip()
            ante = _text_to_expr(ante_txt, sym_map, atom_names)
            cons = _text_to_expr(cons_txt, sym_map, atom_names)
            formula = Implies(ante, cons)
            return formula, atom_names

        # --- and ---
        if ' and ' in s:
            parts = s.split(' and ', 1)
            lhs = _text_to_expr(parts[0].strip(), sym_map, atom_names)
            rhs = _text_to_expr(parts[1].strip(), sym_map, atom_names)
            formula = And(lhs, rhs)
            return formula, atom_names

        # --- or ---
        if ' or ' in s:
            parts = s.split(' or ', 1)
            lhs = _text_to_expr(parts[0].strip(), sym_map, atom_names)
            rhs = _text_to_expr(parts[1].strip(), sym_map, atom_names)
            formula = Or(lhs, rhs)
            return formula, atom_names

        # --- not ---
        if s.startswith('not '):
            inner = _text_to_expr(s[4:].strip(), sym_map, atom_names)
            formula = Not(inner)
            return formula, atom_names

        # --- fallback: conjunction of all atoms ---
        syms = [sym_map[n] for n in atom_names]
        formula = And(*syms) if len(syms) > 1 else syms[0]
        return formula, atom_names

    except Exception:
        syms = [sym_map[n] for n in atom_names]
        formula = And(*syms) if len(syms) > 1 else syms[0]
        return formula, atom_names


def _text_to_expr(text, sym_map, atom_names):
    """
    Map a small text fragment to a sympy expression using the pre-built symbol
    map.

    Handles:
      - Leading "not <fragment>"  →  Not(<fragment>)
      - "<A> and <B>"             →  And(A, B)   (recursive)
      - "<A> or <B>"              →  Or(A, B)    (recursive)
      - Known atom names (substring match, case-insensitive)
      - Fallback: fresh Symbol derived from text
    """
    text = text.strip()
    text_lower = text.lower()

    # Recursive not
    if text_lower.startswith("not "):
        inner = _text_to_expr(text[4:].strip(), sym_map, atom_names)
        return Not(inner)

    # Recursive and / or inside a fragment
    if " and " in text_lower:
        parts = text_lower.split(" and ", 1)
        # find actual-case splits at the same positions
        idx = text.lower().index(" and ")
        lhs = _text_to_expr(text[:idx].strip(), sym_map, atom_names)
        rhs = _text_to_expr(text[idx + 5:].strip(), sym_map, atom_names)
        return And(lhs, rhs)

    if " or " in text_lower:
        idx = text.lower().index(" or ")
        lhs = _text_to_expr(text[:idx].strip(), sym_map, atom_names)
        rhs = _text_to_expr(text[idx + 4:].strip(), sym_map, atom_names)
        return Or(lhs, rhs)

    # Known atom (substring match)
    for name in atom_names:
        if name.lower() in text_lower:
            return sym_map[name]

    # Fallback: fresh symbol from the text itself
    safe = re.sub(r'\W+', '_', text)[:32] or "P"
    if safe not in sym_map:
        sym_map[safe] = symbols(safe)
    return sym_map[safe]


def _formula_depth(formula):
    """Recursively compute the connective depth of a sympy Boolean formula."""
    if formula.is_Atom:
        return 0
    return 1 + max((_formula_depth(arg) for arg in formula.args), default=0)


def _count_connectives(formula):
    """Count And/Or/Not/Implies nodes in the formula tree."""
    if formula.is_Atom:
        return 0
    return 1 + sum(_count_connectives(arg) for arg in formula.args)


def _is_horn_cnf(cnf_formula):
    """
    Check whether every clause in the CNF has at most one positive (non-negated)
    literal, i.e. the formula is a set of Horn clauses.
    """
    # Normalise to a top-level And of clauses
    if isinstance(cnf_formula, And):
        clauses = list(cnf_formula.args)
    else:
        clauses = [cnf_formula]

    for clause in clauses:
        # Collect literals in the clause
        if isinstance(clause, Or):
            literals = list(clause.args)
        else:
            literals = [clause]

        positive_count = sum(1 for lit in literals if not isinstance(lit, Not))
        if positive_count > 1:
            return False
    return True


# ---------------------------------------------------------------------------
# Plugin hooks
# ---------------------------------------------------------------------------

def pt_represent(hypothesis):
    """
    Parse hypothesis.statement into a real sympy propositional formula.
    Returns the formula string, its atoms, and its CNF form.
    """
    base = {
        "framework": "proof_theory",
        "proof_system": "intuitionistic_type_theory",
        "curry_howard_type": "Proposition (to be inhabited by a proof term)",
        "raw_statement": hypothesis.statement,
    }

    if not _SYMPY_AVAILABLE:
        base["logical_form"] = _to_logical_form(hypothesis.statement)
        base["sympy_available"] = False
        return base

    formula, atoms = _parse_formula(hypothesis.statement)
    if formula is None:
        base["logical_form"] = _to_logical_form(hypothesis.statement)
        base["sympy_available"] = True
        base["parse_error"] = "Could not construct formula"
        return base

    cnf_str = "unavailable"
    try:
        cnf = to_cnf(formula)
        cnf_str = str(cnf)
    except Exception as exc:
        cnf_str = f"cnf_error: {exc}"

    base.update({
        "sympy_available": True,
        "logical_form": str(formula),
        "atoms": atoms,
        "cnf_form": cnf_str,
        "connective_depth": _formula_depth(formula),
        "connective_count": _count_connectives(formula),
    })
    return base


def pt_verify(hypothesis, representation=None):
    """
    Real sympy-based verification checks:
      1. Logical consistency  — satisfiable(formula)
      2. Tautology            — satisfiable(Not(formula)) == False
      3. Horn clause property — at most 1 positive literal per CNF clause
    """
    checks = []

    if not _SYMPY_AVAILABLE:
        checks = [
            {
                "check": "logical_consistency",
                "question": "Is the hypothesis consistent (no derivation of ⊥)?",
                "status": "requires_proof",
                "note": "sympy not available",
            },
            {
                "check": "constructive_content",
                "question": "Can a constructive (intuitionistic) proof be given?",
                "status": "requires_analysis",
                "note": "sympy not available",
            },
            {
                "check": "proof_strength",
                "question": "What axiom system is needed?",
                "status": "requires_analysis",
                "note": "sympy not available",
            },
        ]
        return {
            "framework": "proof_theory",
            "checks": checks,
            "overall": "requires_proof",
            "sympy_available": False,
        }

    # Build or reuse the formula
    formula, atoms = _parse_formula(hypothesis.statement)
    if formula is None:
        return {
            "framework": "proof_theory",
            "checks": [],
            "overall": "parse_failed",
            "sympy_available": True,
        }

    # --- Check 1: logical consistency ---
    consistency_status = "unknown"
    consistency_model = None
    consistency_note = ""
    try:
        model = satisfiable(formula)
        if model is False:
            consistency_status = "inconsistent"
            consistency_note = "No satisfying assignment exists — formula is a contradiction."
        else:
            consistency_status = "consistent"
            # model is a dict {Symbol: True/False}
            consistency_model = {str(k): v for k, v in model.items()}
            consistency_note = "At least one satisfying assignment found."
    except Exception as exc:
        consistency_status = "error"
        consistency_note = f"satisfiable() raised: {exc}"

    checks.append({
        "check": "logical_consistency",
        "question": "Is the hypothesis consistent (no derivation of ⊥)?",
        "status": consistency_status,
        "note": consistency_note,
        "satisfying_model": consistency_model,
    })

    # --- Check 2: tautology ---
    tautology_status = "unknown"
    tautology_note = ""
    try:
        neg_sat = satisfiable(Not(formula))
        if neg_sat is False:
            tautology_status = "tautology"
            tautology_note = "¬formula is unsatisfiable → formula is a classical tautology."
        else:
            tautology_status = "not_tautology"
            tautology_note = "¬formula is satisfiable → formula is not a tautology."
    except Exception as exc:
        tautology_status = "error"
        tautology_note = f"satisfiable(Not(formula)) raised: {exc}"

    checks.append({
        "check": "tautology",
        "question": "Is the formula a classical tautology (true under all valuations)?",
        "status": tautology_status,
        "note": tautology_note,
    })

    # --- Check 3: Horn clause / constructive provability ---
    horn_status = "unknown"
    horn_note = ""
    try:
        cnf = to_cnf(formula)
        if _is_horn_cnf(cnf):
            horn_status = "horn_clause"
            horn_note = (
                "Every CNF clause has at most one positive literal. "
                "Constructively provable via SLD-resolution (Prolog-style)."
            )
        else:
            horn_status = "not_horn"
            horn_note = (
                "At least one CNF clause has multiple positive literals. "
                "Not a Horn clause set; constructive proof path is less direct."
            )
    except Exception as exc:
        horn_status = "error"
        horn_note = f"Horn check raised: {exc}"

    checks.append({
        "check": "horn_clause",
        "question": "Does the CNF have at most 1 positive literal per clause (Horn / constructively provable)?",
        "status": horn_status,
        "note": horn_note,
    })

    # Derive overall verdict
    if consistency_status == "inconsistent":
        overall = "rejected_inconsistent"
    elif tautology_status == "tautology":
        overall = "tautology_verified"
    elif consistency_status == "consistent":
        overall = "consistent_requires_deeper_proof"
    else:
        overall = "requires_proof"

    return {
        "framework": "proof_theory",
        "checks": checks,
        "overall": overall,
        "sympy_available": True,
        "atoms": atoms,
    }


def pt_transform(representation, transform_type="curry_howard"):
    """
    Apply a structural transform to the proof-theoretic representation.
    For curry_howard and cut_elimination, augments the result with
    formula-level structural analysis when sympy is available.
    """
    transforms = {
        "curry_howard": "Convert proposition to type, seek a program (proof term) inhabiting it",
        "cut_elimination": "Eliminate detours (cuts) from proof to get direct proof",
        "ordinal_analysis": "Measure the proof-theoretic strength required",
        "double_negation": "Apply Friedman/Gödel translation to extract constructive content",
    }

    result = {
        "input": representation,
        "transform": transform_type,
        "description": transforms.get(transform_type, "Unknown"),
    }

    if not _SYMPY_AVAILABLE:
        return result

    # Pull raw statement from representation dict if available
    raw = (representation or {}).get("raw_statement", "")
    if not raw:
        return result

    formula, atoms = _parse_formula(raw)
    if formula is None:
        return result

    structural = {
        "atom_count": len(atoms),
        "atoms": atoms,
        "connective_depth": _formula_depth(formula),
        "connective_count": _count_connectives(formula),
        "formula_str": str(formula),
    }

    try:
        cnf = to_cnf(formula)
        structural["cnf_str"] = str(cnf)
        structural["is_horn"] = _is_horn_cnf(cnf)
        clause_count = len(cnf.args) if isinstance(cnf, And) else 1
        structural["cnf_clause_count"] = clause_count
    except Exception as exc:
        structural["cnf_error"] = str(exc)

    if transform_type == "curry_howard":
        structural["ch_note"] = (
            f"Proposition has {structural['connective_depth']} nesting levels. "
            f"A proof term (program) must inhabit the corresponding type. "
            f"Depth {structural['connective_depth']} implies at least "
            f"{structural['connective_depth']} nested lambda/case abstractions."
        )
    elif transform_type == "cut_elimination":
        structural["cut_note"] = (
            f"Cut elimination operates on the {structural.get('cnf_clause_count', '?')}-clause "
            f"CNF. Each cut removal may expand proof size; complexity is at most "
            f"superexponential in the cut depth ({structural['connective_depth']})."
        )

    result["structural_analysis"] = structural
    return result


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

    if depth >= 3:
        hypotheses.append({
            "title": f"Ordinal rank of: {seed[:40]}",
            "statement": (
                f"The statement '{seed}' can be assigned an ordinal proof-theoretic "
                f"strength. If it is provable in Peano Arithmetic, its ordinal is "
                f"at most ε₀. Stronger statements require larger proof-theoretic "
                f"ordinals, measuring their distance from ZFC and beyond."
            ),
            "tags": ["proof_theory", "ordinal_analysis", "auto_generated"],
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


# ---------------------------------------------------------------------------
# Fallback helper (used when sympy unavailable)
# ---------------------------------------------------------------------------

def _to_logical_form(statement):
    s = statement.lower()
    if "for all" in s or "every" in s: return "∀-statement (universal)"
    if "exists" in s or "there is" in s: return "∃-statement (existential)"
    if "implies" in s or "if" in s: return "→-statement (implication)"
    if "and" in s: return "∧-statement (conjunction)"
    if "or" in s: return "∨-statement (disjunction)"
    return "atomic proposition"
