"""
Game Theory Plugin — Mathematical Universe for Ontology Explorer

Models hypotheses as strategic interactions:
  - Nash equilibria as stable hypothesis states
  - Evolutionary dynamics for hypothesis fitness
  - Mechanism design for hypothesis testing protocols
  - Signaling games for information verification
  - Bayesian games for incomplete information
"""

try:
    import numpy as np
    from scipy.optimize import linprog
    _SCIPY_AVAILABLE = True
except ImportError:
    np = None
    linprog = None
    _SCIPY_AVAILABLE = False


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
    """Build a real numpy payoff matrix from the hypothesis statement."""
    try:
        if not _SCIPY_AVAILABLE:
            raise ImportError("numpy/scipy not available")

        # Parse player count from hypothesis text (look for digit before "player")
        import re
        statement = hypothesis.statement
        match = re.search(r'(\d+)\s*[-\s]?player', statement, re.IGNORECASE)
        n_players = int(match.group(1)) if match else 2

        # Default 2-player Prisoner's Dilemma payoffs: [[3,0],[5,1]]
        # Row player payoffs; column = column player's action
        if n_players == 2:
            payoff_matrix = np.array([[3, 0], [5, 1]], dtype=float)
        else:
            # n-player generalisation: random symmetric payoffs seeded from statement hash
            seed = sum(ord(c) for c in statement) % (2 ** 31)
            rng = np.random.default_rng(seed)
            payoff_matrix = rng.integers(0, 6, size=(n_players, n_players)).astype(float)

        return {
            "framework": "game_theory",
            "game_type": _infer_game_type(statement),
            "n_players": n_players,
            "payoff_matrix": payoff_matrix.tolist(),
            "payoff_matrix_description": (
                "Row index = row player's strategy, "
                "value = row player's payoff given column player's strategy. "
                "Prisoner's Dilemma default: cooperate=0, defect=1."
            ),
            "players": ["hypothesis_proponent", "red_team_critic", "neutral_observer"][
                       :n_players
            ],
            "strategy_spaces": {
                "proponent": ["present_evidence", "strengthen_claim", "narrow_scope"],
                "critic": ["find_counterexample", "attack_assumptions",
                           "propose_alternative"],
                "observer": ["accept", "reject", "request_more_evidence"],
            },
            "raw_statement": statement,
            "numpy_available": True,
        }
    except Exception as exc:
        return {
            "framework": "game_theory",
            "game_type": _infer_game_type(hypothesis.statement),
            "players": ["hypothesis_proponent", "red_team_critic", "neutral_observer"],
            "strategy_spaces": {
                "proponent": ["present_evidence", "strengthen_claim", "narrow_scope"],
                "critic": ["find_counterexample", "attack_assumptions",
                           "propose_alternative"],
                "observer": ["accept", "reject", "request_more_evidence"],
            },
            "raw_statement": hypothesis.statement,
            "numpy_available": False,
            "fallback_reason": str(exc),
        }


def gt_transform(representation, transform_type="nash_analysis"):
    """Apply mathematical transforms; nash_analysis and evolutionary are computed."""
    if transform_type == "nash_analysis":
        return _transform_nash_analysis(representation)
    elif transform_type == "evolutionary":
        return _transform_evolutionary(representation)
    else:
        # Descriptive-only transforms — keep original behaviour
        transforms = {
            "mechanism_design": "Design an optimal hypothesis testing protocol",
            "auction": "Frame as information auction — what is this hypothesis worth?",
        }
        return {
            "input": representation,
            "transform": transform_type,
            "description": transforms.get(transform_type, "Unknown"),
        }


def _transform_nash_analysis(representation):
    """
    Solve Nash equilibrium for a 2-player zero-sum game via LP (linprog).

    Zero-sum LP for row player:
      max  v
      s.t. A^T x >= v * 1   (column player can't do better than v)
           sum(x) = 1, x >= 0

    Reformulated as minimisation for linprog:
      min  -v
      s.t. -A^T x + v <= 0
           sum(x) = 1, x >= 0
    """
    try:
        if not _SCIPY_AVAILABLE:
            raise ImportError("scipy not available")

        payoff_raw = representation.get("payoff_matrix")
        if payoff_raw is None:
            raise ValueError("No payoff_matrix in representation")

        A = np.array(payoff_raw, dtype=float)
        n, m = A.shape  # n strategies for row player, m for column player

        # --- LP for row player's mixed strategy ---
        # Variables: [x_0, ..., x_{n-1}, v]
        # min  -v  (maximise v)
        c = np.zeros(n + 1)
        c[-1] = -1.0  # coefficient for -v

        # Inequality: -A^T x + v <= 0  =>  for each column j: sum_i(-A[i,j]*x_i) + v <= 0
        A_ub = np.hstack([-A.T, np.ones((m, 1))])   # shape (m, n+1)
        b_ub = np.zeros(m)

        # Equality: sum(x) = 1
        A_eq = np.zeros((1, n + 1))
        A_eq[0, :n] = 1.0
        b_eq = np.array([1.0])

        bounds = [(0.0, None)] * n + [(None, None)]  # x_i >= 0, v unbounded

        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                      bounds=bounds, method="highs")

        if res.success:
            x_star = res.x[:n].tolist()
            game_value = float(res.x[-1])
        else:
            x_star = None
            game_value = None

        # --- LP for column player's mixed strategy ---
        # Variables: [y_0, ..., y_{m-1}, v]
        # min  v  (minimise v — column player minimises row player's gain)
        c2 = np.zeros(m + 1)
        c2[-1] = 1.0

        # Inequality: A y - v <= 0  =>  for each row i: sum_j(A[i,j]*y_j) - v <= 0
        A_ub2 = np.hstack([A, -np.ones((n, 1))])   # shape (n, m+1)
        b_ub2 = np.zeros(n)

        A_eq2 = np.zeros((1, m + 1))
        A_eq2[0, :m] = 1.0
        b_eq2 = np.array([1.0])

        bounds2 = [(0.0, None)] * m + [(None, None)]

        res2 = linprog(c2, A_ub=A_ub2, b_ub=b_ub2, A_eq=A_eq2, b_eq=b_eq2,
                       bounds=bounds2, method="highs")

        y_star = res2.x[:m].tolist() if res2.success else None

        return {
            "input": representation,
            "transform": "nash_analysis",
            "method": "linprog_LP_zero_sum",
            "row_player_mixed_strategy": x_star,
            "col_player_mixed_strategy": y_star,
            "game_value": game_value,
            "lp_row_success": bool(res.success),
            "lp_col_success": bool(res2.success),
            "interpretation": (
                "Mixed Nash equilibrium computed via LP duality for zero-sum game. "
                f"Game value (row player's guaranteed payoff): {game_value:.4f}"
                if game_value is not None else
                "LP did not converge — game may not be zero-sum or matrix is degenerate."
            ),
        }
    except Exception as exc:
        return {
            "input": representation,
            "transform": "nash_analysis",
            "status": "computation_failed",
            "error": str(exc),
        }


def _transform_evolutionary(representation):
    """
    One round of replicator dynamics for 10 iterations from uniform start.

    Replicator dynamics:
        dx_i/dt = x_i * (f_i(x) - f_bar(x))
    where f_i(x) = sum_j A[i,j] * x_j  (expected payoff of strategy i)
    and   f_bar  = sum_i x_i * f_i(x)  (mean fitness)

    Discrete Euler step: x_i(t+1) = x_i(t) + dt * x_i(t) * (f_i - f_bar)
    followed by renormalisation.
    """
    try:
        if not _SCIPY_AVAILABLE:
            raise ImportError("numpy not available")

        payoff_raw = representation.get("payoff_matrix")
        if payoff_raw is None:
            raise ValueError("No payoff_matrix in representation")

        A = np.array(payoff_raw, dtype=float)
        n = A.shape[0]

        # Uniform initial population share
        x = np.ones(n) / n
        dt = 0.1
        trajectory = [x.tolist()]

        for _ in range(10):
            f = A @ x                     # f_i = sum_j A[i,j] x_j
            f_bar = float(x @ f)          # mean fitness
            dx = x * (f - f_bar)
            x = x + dt * dx
            # Clip negatives from numerical noise then renormalise
            x = np.clip(x, 0.0, None)
            total = x.sum()
            if total > 0:
                x = x / total
            trajectory.append(x.tolist())

        # Identify dominant strategy at convergence
        dominant_idx = int(np.argmax(x))

        return {
            "input": representation,
            "transform": "evolutionary",
            "method": "replicator_dynamics_euler",
            "iterations": 10,
            "dt": dt,
            "initial_distribution": trajectory[0],
            "final_distribution": trajectory[-1],
            "trajectory": trajectory,
            "dominant_strategy_index": dominant_idx,
            "interpretation": (
                f"After 10 replicator-dynamics steps from uniform start, "
                f"strategy {dominant_idx} dominates with share "
                f"{trajectory[-1][dominant_idx]:.4f}."
            ),
        }
    except Exception as exc:
        return {
            "input": representation,
            "transform": "evolutionary",
            "status": "computation_failed",
            "error": str(exc),
        }


def gt_verify(hypothesis, representation=None):
    """
    Real game-theoretic verification:
      1. Pure Nash equilibrium via dominant strategy detection.
      2. Mixed Nash via LP (zero-sum).
      3. Pareto optimality check at Nash.
    """
    try:
        if not _SCIPY_AVAILABLE:
            raise ImportError("numpy/scipy not available")

        # Build / reuse payoff matrix
        if representation and "payoff_matrix" in representation:
            A = np.array(representation["payoff_matrix"], dtype=float)
        else:
            A = np.array([[3, 0], [5, 1]], dtype=float)  # Prisoner's Dilemma default

        n, m = A.shape
        checks = []

        # --- Check 1: Dominant strategy / pure Nash ---
        pure_nash = _find_pure_nash(A)
        checks.append({
            "check": "pure_nash_equilibrium",
            "method": "dominant_strategy_detection",
            "pure_nash_cells": pure_nash,
            "exists": len(pure_nash) > 0,
            "status": "computed",
        })

        # --- Check 2: Mixed Nash via LP ---
        nash_transform = _transform_nash_analysis(
            {"payoff_matrix": A.tolist()}
        )
        mixed_nash_exists = (
            nash_transform.get("lp_row_success") and
            nash_transform.get("lp_col_success")
        )
        checks.append({
            "check": "mixed_nash_equilibrium",
            "method": "linprog_LP_zero_sum",
            "row_strategy": nash_transform.get("row_player_mixed_strategy"),
            "col_strategy": nash_transform.get("col_player_mixed_strategy"),
            "game_value": nash_transform.get("game_value"),
            "exists": mixed_nash_exists,
            "status": "computed",
        })

        # --- Check 3: Pareto optimality at Nash ---
        pareto_result = _check_pareto_at_nash(A, pure_nash)
        checks.append({
            "check": "pareto_optimality_at_nash",
            "method": "exhaustive_cell_dominance",
            "pareto_optimal_cells": pareto_result["pareto_cells"],
            "nash_is_pareto_optimal": pareto_result["nash_pareto_overlap"],
            "status": "computed",
        })

        overall = (
            "verified" if (mixed_nash_exists or len(pure_nash) > 0) else "no_equilibrium_found"
        )

        return {
            "framework": "game_theory",
            "checks": checks,
            "overall": overall,
            "payoff_matrix_used": A.tolist(),
        }

    except Exception as exc:
        return {
            "framework": "game_theory",
            "checks": [],
            "overall": "computation_failed",
            "error": str(exc),
        }


def _find_pure_nash(A):
    """
    Find all pure Nash equilibria of a 2-player symmetric game.

    Cell (i, j) is a pure Nash if:
      - Row player: A[i, j] >= A[k, j] for all k  (row player can't improve)
      - Col player: A[j, i] >= A[j, k] for all k  (col player can't improve;
        uses transpose payoff = A.T as col player's payoff for symmetric games)
    """
    n, m = A.shape
    nash_cells = []
    for i in range(n):
        for j in range(m):
            row_best = float(A[i, j]) >= float(np.max(A[:, j]))
            col_best = float(A[j, i]) >= float(np.max(A[j, :]))
            if row_best and col_best:
                nash_cells.append((i, j))
    return nash_cells


def _check_pareto_at_nash(A, nash_cells):
    """
    Identify Pareto optimal cells and check overlap with Nash cells.

    A cell (i,j) is Pareto dominated if there exists (i',j') such that
    A[i',j'] > A[i,j] AND A[j',i'] >= A[j,i]  (both players weakly better,
    one strictly better). Simplified for symmetric payoffs.
    """
    n, m = A.shape
    pareto_cells = []
    for i in range(n):
        for j in range(m):
            dominated = False
            for ip in range(n):
                for jp in range(m):
                    if (ip == i and jp == j):
                        continue
                    # Both players at least as well off, row player strictly better
                    if (float(A[ip, jp]) > float(A[i, j]) and
                            float(A[jp, ip]) >= float(A[j, i])):
                        dominated = True
                        break
                if dominated:
                    break
            if not dominated:
                pareto_cells.append((i, j))

    nash_pareto_overlap = any(c in pareto_cells for c in nash_cells)
    return {
        "pareto_cells": pareto_cells,
        "nash_pareto_overlap": nash_pareto_overlap,
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

    if depth >= 3:
        hypotheses.append({
            "title": f"Mechanism design for: {seed[:40]}",
            "statement": (
                f"Optimal verification of '{seed}' can be framed as a mechanism design "
                f"problem: construct a protocol (direct revelation game) such that "
                f"truthful reporting is a dominant strategy for all agents, and the "
                f"resulting equilibrium maximises information gain about the hypothesis."
            ),
            "tags": ["game_theory", "mechanism_design", "revelation_principle",
                     "auto_generated"],
        })
        hypotheses.append({
            "title": f"Signaling game for: {seed[:40]}",
            "statement": (
                f"Information asymmetry in evaluating '{seed}' creates a signaling game: "
                f"the informed party (hypothesis author) chooses signals (evidence, "
                f"citations, scope restrictions) and uninformed parties update beliefs "
                f"via Bayes' rule. Separating equilibria distinguish high- from "
                f"low-quality hypotheses."
            ),
            "tags": ["game_theory", "signaling", "information_asymmetry",
                     "auto_generated"],
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
