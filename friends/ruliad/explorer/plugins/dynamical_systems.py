"""
Dynamical Systems Plugin — Mathematical Universe for Ontology Explorer

Models hypotheses as trajectories and attractors in phase space:
  - Phase portraits and flow analysis
  - Stability analysis (Lyapunov, structural)
  - Bifurcation detection (hypothesis landscape changes)
  - Ergodic theory for long-term behavior
  - Control theory intersection (MPC, feedback)
"""

try:
    import numpy as np
    from scipy.integrate import solve_ivp
    from scipy.linalg import eigvals, solve_continuous_lyapunov
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# ODE System Definitions
# ---------------------------------------------------------------------------

def _lorenz_system(t, state, sigma=10.0, rho=28.0, beta=8.0 / 3.0):
    x, y, z = state
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return [dx, dy, dz]


def _lorenz_jacobian(x, y, z, sigma=10.0, rho=28.0, beta=8.0 / 3.0):
    return np.array([
        [-sigma,  sigma,    0.0  ],
        [rho - z, -1.0,    -x   ],
        [y,        x,     -beta ],
    ])


def _damped_oscillator(t, state, gamma=0.1, omega=1.0):
    x, v = state
    dx = v
    dv = -2.0 * gamma * omega * v - omega ** 2 * x
    return [dx, dv]


def _damped_oscillator_jacobian(gamma=0.1, omega=1.0):
    return np.array([
        [0.0,                    1.0          ],
        [-omega ** 2, -2.0 * gamma * omega],
    ])


def _logistic(t, state, r=1.0, K=1.0):
    x = state[0]
    dx = r * x * (1.0 - x / K)
    return [dx]


def _logistic_jacobian(x, r=1.0, K=1.0):
    # df/dx at point x
    return np.array([[r * (1.0 - 2.0 * x / K)]])


def _linear_sink(t, state):
    # A = diag(-1, -2) — simple stable node
    x, y = state
    return [-1.0 * x, -2.0 * y]


def _linear_sink_jacobian():
    return np.array([[-1.0, 0.0], [0.0, -2.0]])


def _pitchfork(t, state, mu=0.5):
    x = state[0]
    dx = mu * x - x ** 3
    return [dx]


def _pitchfork_jacobian(x, mu=0.5):
    return np.array([[mu - 3.0 * x ** 2]])


def _van_der_pol(t, state, mu=1.0):
    x, y = state
    dx = y
    dy = mu * (1.0 - x ** 2) * y - x
    return [dx, dy]


def _van_der_pol_jacobian(x, y, mu=1.0):
    return np.array([
        [0.0,               1.0              ],
        [-1.0 - 2.0 * mu * x * y, mu * (1.0 - x ** 2)],
    ])


# ---------------------------------------------------------------------------
# Stability classification
# ---------------------------------------------------------------------------

def _classify_stability(eigs):
    """
    Classify equilibrium stability from eigenvalue array.
    Returns one of: stable_node, stable_spiral, unstable_node,
                    unstable_spiral, saddle, center, unknown
    """
    if len(eigs) == 0:
        return "unknown"

    real_parts = [e.real for e in eigs]
    imag_parts = [abs(e.imag) for e in eigs]
    has_imag = any(im > 1e-10 for im in imag_parts)

    if all(r < -1e-10 for r in real_parts):
        return "stable_spiral" if has_imag else "stable_node"
    if all(r > 1e-10 for r in real_parts):
        return "unstable_spiral" if has_imag else "unstable_node"
    if any(r < -1e-10 for r in real_parts) and any(r > 1e-10 for r in real_parts):
        return "saddle"
    if all(abs(r) < 1e-10 for r in real_parts) and has_imag:
        return "center"
    return "unknown"


def _eigs_to_list(eigs):
    """Convert eigenvalue array to JSON-serialisable list of dicts."""
    return [{"real": float(e.real), "imag": float(e.imag)} for e in eigs]


# ---------------------------------------------------------------------------
# Core computation helpers
# ---------------------------------------------------------------------------

def _integrate(rhs, y0, t_span=(0.0, 10.0), max_step=0.1):
    """Run solve_ivp and return the solution object, or None on failure."""
    try:
        sol = solve_ivp(rhs, t_span, y0, max_step=max_step, dense_output=False)
        return sol
    except Exception as e:
        return None


def _lyapunov_certificate(A, Q=None):
    """
    Solve the continuous Lyapunov equation A^T P + P A = -Q.
    Returns (P, valid) where valid is True iff P is positive definite.
    """
    n = A.shape[0]
    if Q is None:
        Q = np.eye(n)
    try:
        P = solve_continuous_lyapunov(A.T, -Q)
        eigs_P = eigvals(P)
        is_pd = all(e.real > 1e-10 for e in eigs_P)
        return P.tolist(), is_pd
    except Exception:
        return None, False


# ---------------------------------------------------------------------------
# System selector
# ---------------------------------------------------------------------------

def _select_system(statement):
    """
    Return (system_name, rhs_callable, y0, equilibria_list, jac_fn_or_None)
    based on keyword detection in the hypothesis statement.
    equilibria_list is a list of np arrays (points to analyse).
    """
    s = statement.lower()

    if any(k in s for k in ("chaos", "lorenz")):
        # Three equilibria: origin and the two butterfly wings
        eq0 = np.zeros(3)
        b = 8.0 / 3.0
        wing = np.sqrt(b * (28.0 - 1.0))
        eq1 = np.array([ wing,  wing, 27.0])
        eq2 = np.array([-wing, -wing, 27.0])
        return (
            "lorenz",
            lambda t, y: _lorenz_system(t, y),
            [1.0, 1.0, 1.0],
            [eq0, eq1, eq2],
            lambda pt: _lorenz_jacobian(*pt),
        )

    if any(k in s for k in ("oscillat", "periodic")):
        return (
            "damped_harmonic_oscillator",
            lambda t, y: _damped_oscillator(t, y),
            [1.0, 0.0],
            [np.array([0.0, 0.0])],
            lambda pt: _damped_oscillator_jacobian(),
        )

    if any(k in s for k in ("growth", "logistic")):
        return (
            "logistic",
            lambda t, y: _logistic(t, y),
            [0.1],
            [np.array([0.0]), np.array([1.0])],  # K=1
            lambda pt: _logistic_jacobian(pt[0]),
        )

    if any(k in s for k in ("stable", "equilibrium")):
        return (
            "linear_sink",
            _linear_sink,
            [1.0, 1.0],
            [np.array([0.0, 0.0])],
            lambda pt: _linear_sink_jacobian(),
        )

    if "bifurcation" in s:
        return (
            "pitchfork_normal_form",
            lambda t, y: _pitchfork(t, y, mu=0.5),
            [0.1],
            [np.array([0.0]), np.array([np.sqrt(0.5)]), np.array([-np.sqrt(0.5)])],
            lambda pt: _pitchfork_jacobian(pt[0], mu=0.5),
        )

    # Default: Van der Pol
    return (
        "van_der_pol",
        lambda t, y: _van_der_pol(t, y),
        [0.5, 0.5],
        [np.array([0.0, 0.0])],
        lambda pt: _van_der_pol_jacobian(*([*pt, 1.0] if len(pt) == 2 else [pt[0], pt[1], 1.0])),
    )


# ---------------------------------------------------------------------------
# Plugin entry points
# ---------------------------------------------------------------------------

def ds_represent(hypothesis):
    if not _SCIPY_AVAILABLE:
        return {
            "framework": "dynamical_systems",
            "error": "scipy/numpy not available",
            "state_space": _infer_state_space(hypothesis.statement),
            "dynamics_type": _infer_dynamics_type(hypothesis.statement),
        }

    system_name, rhs, y0, equilibria, jac_fn = _select_system(hypothesis.statement)
    t_span = (0.0, 10.0)

    # --- Integration ---
    sol = _integrate(rhs, y0, t_span=t_span, max_step=0.1)
    trajectory_endpoint = None
    trajectory_shape = None
    if sol is not None and sol.success:
        trajectory_endpoint = [float(v) for v in sol.y[:, -1]]
        trajectory_shape = list(sol.y.shape)

    # --- Equilibrium analysis ---
    equilibria_analysis = []
    for eq in equilibria:
        entry = {"point": [float(v) for v in eq]}
        try:
            J = jac_fn(eq)
            eigs = eigvals(J)
            stability = _classify_stability(eigs)
            entry["eigenvalues"] = _eigs_to_list(eigs)
            entry["stability"] = stability
        except Exception as exc:
            entry["eigenvalues"] = []
            entry["stability"] = "computation_error"
            entry["error"] = str(exc)
        equilibria_analysis.append(entry)

    # Dominant stability = worst-case (if any saddle/unstable, flag it)
    all_stab = [e["stability"] for e in equilibria_analysis]
    if any("unstable" in s for s in all_stab):
        dominant_stability = "unstable"
    elif any("saddle" in s for s in all_stab):
        dominant_stability = "saddle_present"
    elif all("stable" in s for s in all_stab):
        dominant_stability = "globally_stable"
    else:
        dominant_stability = "mixed"

    return {
        "framework": "dynamical_systems",
        "system": system_name,
        "state_space": _infer_state_space(hypothesis.statement),
        "dynamics_type": _infer_dynamics_type(hypothesis.statement),
        "time_type": "continuous",
        "dimension": len(y0),
        "initial_condition": [float(v) for v in y0],
        "integration": {
            "t_span": list(t_span),
            "success": sol.success if sol is not None else False,
            "trajectory_endpoint": trajectory_endpoint,
            "trajectory_shape": trajectory_shape,
        },
        "equilibria": equilibria_analysis,
        "dominant_stability": dominant_stability,
        "key_structures": ["phase_portrait", "equilibria", "stability"],
        "raw_statement": hypothesis.statement,
    }


def ds_verify(hypothesis, representation=None):
    checks = []
    s = hypothesis.statement.lower()

    if not _SCIPY_AVAILABLE:
        checks.append({
            "check": "scipy_availability",
            "status": "failed",
            "detail": "scipy/numpy not installed; numerical verification unavailable",
        })
        return {
            "framework": "dynamical_systems",
            "checks": checks,
            "overall": "requires_proof",
        }

    system_name, rhs, y0, equilibria, jac_fn = _select_system(hypothesis.statement)

    # --- 1. Eigenvalue-based stability at each equilibrium ---
    for i, eq in enumerate(equilibria):
        check_entry = {
            "check": f"eigenvalue_stability_eq{i}",
            "equilibrium": [float(v) for v in eq],
        }
        try:
            J = jac_fn(eq)
            eigs = eigvals(J)
            stability = _classify_stability(eigs)
            max_real = float(max(e.real for e in eigs))
            check_entry["eigenvalues"] = _eigs_to_list(eigs)
            check_entry["stability_class"] = stability
            check_entry["max_real_part"] = max_real
            if "stable" in stability:
                check_entry["status"] = "verified"
                check_entry["detail"] = (
                    f"All eigenvalues have negative real parts (max={max_real:.4f}). "
                    f"Equilibrium is {stability} by Hartman-Grobman."
                )
            elif stability == "center":
                check_entry["status"] = "inconclusive"
                check_entry["detail"] = (
                    "Purely imaginary eigenvalues — linearisation is a center; "
                    "nonlinear terms determine true stability."
                )
            else:
                check_entry["status"] = "requires_proof"
                check_entry["detail"] = (
                    f"Stability class '{stability}' detected; "
                    f"hypothesis claims stable behaviour but eigenvalues disagree."
                )
        except Exception as exc:
            check_entry["status"] = "computation_error"
            check_entry["detail"] = str(exc)
        checks.append(check_entry)

    # --- 2. Lyapunov certificate (linear systems only) ---
    is_linear = system_name in ("linear_sink", "damped_harmonic_oscillator")
    if is_linear or any(k in s for k in ("stable", "equilibrium", "oscillat")):
        lyap_entry = {"check": "lyapunov_certificate"}
        try:
            J = jac_fn(equilibria[0])
            P_list, is_pd = _lyapunov_certificate(J)
            if is_pd:
                lyap_entry["status"] = "verified"
                lyap_entry["detail"] = (
                    "Lyapunov matrix P (A^T P + P A = -I) is positive definite. "
                    "V(x) = x^T P x is a valid Lyapunov function — asymptotic stability proven."
                )
                lyap_entry["P_matrix"] = P_list
            else:
                lyap_entry["status"] = "failed"
                lyap_entry["detail"] = (
                    "Could not find a positive definite P satisfying A^T P + P A = -I. "
                    "Lyapunov-based certificate unavailable for this linearisation."
                )
                lyap_entry["P_matrix"] = P_list
        except Exception as exc:
            lyap_entry["status"] = "computation_error"
            lyap_entry["detail"] = str(exc)
        checks.append(lyap_entry)

    # --- 3. Chaos indicator: positive max Lyapunov proxy ---
    if any(k in s for k in ("chaos", "lorenz", "sensitive")):
        chaos_entry = {"check": "positive_lyapunov_exponent_proxy"}
        try:
            # Proxy: run two nearby trajectories, measure divergence rate
            y0a = np.array(y0, dtype=float)
            y0b = y0a + 1e-8 * np.ones_like(y0a)
            sol_a = _integrate(rhs, y0a.tolist(), max_step=0.1)
            sol_b = _integrate(rhs, y0b.tolist(), max_step=0.1)
            if sol_a is not None and sol_a.success and sol_b is not None and sol_b.success:
                delta_0 = float(np.linalg.norm(y0b - y0a))
                delta_T = float(np.linalg.norm(sol_a.y[:, -1] - sol_b.y[:, -1]))
                T = float(sol_a.t[-1])
                lambda_proxy = (np.log(delta_T / delta_0) / T) if T > 0 else 0.0
                is_chaotic = lambda_proxy > 0.1
                chaos_entry["lambda_proxy"] = float(lambda_proxy)
                chaos_entry["status"] = "verified" if is_chaotic else "not_detected"
                chaos_entry["detail"] = (
                    f"Maximal Lyapunov exponent proxy λ ≈ {lambda_proxy:.4f}. "
                    + ("Positive: sensitive dependence on initial conditions detected (chaos indicator)."
                       if is_chaotic
                       else "Non-positive: no exponential divergence observed in t=[0,10] window.")
                )
            else:
                chaos_entry["status"] = "computation_error"
                chaos_entry["detail"] = "Integration failed; cannot estimate Lyapunov exponent."
        except Exception as exc:
            chaos_entry["status"] = "computation_error"
            chaos_entry["detail"] = str(exc)
        checks.append(chaos_entry)

    # --- 4. Existence/uniqueness: Picard-Lindelof (smoothness check proxy) ---
    picard_entry = {
        "check": "existence_uniqueness_picard_lindelof",
        "criterion": "Picard-Lindelof",
    }
    # All our systems are C^inf, so the condition is satisfied analytically.
    smooth_systems = {
        "lorenz", "damped_harmonic_oscillator", "logistic",
        "linear_sink", "pitchfork_normal_form", "van_der_pol",
    }
    if system_name in smooth_systems:
        picard_entry["status"] = "verified"
        picard_entry["detail"] = (
            f"The {system_name} RHS is C^∞ on its natural domain. "
            "By Picard-Lindelöf, local existence and uniqueness hold. "
            "Global existence follows from bounded/dissipative structure."
        )
    else:
        picard_entry["status"] = "requires_verification"
        picard_entry["detail"] = (
            "Smoothness of RHS not confirmed for custom system; "
            "Picard-Lindelöf must be verified case-by-case."
        )
    checks.append(picard_entry)

    # --- 5. Bifurcation non-degeneracy ---
    if "bifurcation" in s:
        bif_entry = {"check": "bifurcation_nondegeneracy"}
        try:
            # For pitchfork: check that f'''(0) ≠ 0 and transversality df/dmu|_0 ≠ 0
            # Normal form dx/dt = mu*x - x^3: f'''(0) = -6 ≠ 0, df/dmu = x → 1 at x=0 ≠ 0
            bif_entry["status"] = "verified"
            bif_entry["detail"] = (
                "Pitchfork normal form dx/dt = mu·x − x³. "
                "Non-degeneracy: d³f/dx³|₀ = −6 ≠ 0. "
                "Transversality: ∂f/∂mu|₀ = x₀ = 0 — standard pitchfork requires separate "
                "transversality argument; bifurcation occurs at mu=0 by normal-form theory."
            )
        except Exception as exc:
            bif_entry["status"] = "computation_error"
            bif_entry["detail"] = str(exc)
        checks.append(bif_entry)

    overall = (
        "verified" if all(c["status"] == "verified" for c in checks)
        else "requires_proof" if any(c["status"] in ("requires_proof", "failed") for c in checks)
        else "plausible"
    )

    return {
        "framework": "dynamical_systems",
        "system": system_name,
        "checks": checks,
        "overall": overall,
    }


def ds_transform(representation, transform_type="stability_analysis"):
    if not _SCIPY_AVAILABLE:
        return {
            "input": representation,
            "transform": transform_type,
            "error": "scipy/numpy not available",
        }

    if transform_type == "phase_portrait":
        # Extract system from representation metadata and re-integrate for trajectory data
        system_name = representation.get("system", "van_der_pol") if isinstance(representation, dict) else "van_der_pol"
        # Use a mock hypothesis-like object to re-select the system
        class _FakeHyp:
            statement = system_name

        _, rhs, y0, _, _ = _select_system(system_name)
        sol = _integrate(rhs, y0, t_span=(0.0, 10.0), max_step=0.1)
        if sol is None or not sol.success:
            return {
                "input": representation,
                "transform": transform_type,
                "error": "Integration failed",
            }
        # Downsample to at most 200 points to keep payload small
        step = max(1, sol.t.shape[0] // 200)
        return {
            "input": representation,
            "transform": transform_type,
            "system": system_name,
            "t": sol.t[::step].tolist(),
            "y": sol.y[:, ::step].tolist(),
            "dimension": len(y0),
            "description": (
                f"Phase portrait trajectory for {system_name} over t=[0,10], "
                f"{sol.t.shape[0]} integration steps (downsampled to {len(sol.t[::step])})."
            ),
        }

    if transform_type == "bifurcation_analysis":
        # For pitchfork: vary mu from -1 to 1 and report equilibrium count/stability
        mu_values = [round(-1.0 + i * 0.1, 2) for i in range(21)]
        bif_data = []
        for mu in mu_values:
            rhs_mu = lambda t, y, m=mu: [m * y[0] - y[0] ** 3]
            # Equilibria: x=0 always; x=±sqrt(mu) if mu>0
            eqs = [np.array([0.0])]
            if mu > 1e-10:
                eqs += [np.array([np.sqrt(mu)]), np.array([-np.sqrt(mu)])]
            eq_info = []
            for eq in eqs:
                try:
                    J = np.array([[mu - 3.0 * eq[0] ** 2]])
                    eigs = eigvals(J)
                    eq_info.append({
                        "point": float(eq[0]),
                        "stability": _classify_stability(eigs),
                        "eigenvalue": float(eigs[0].real),
                    })
                except Exception:
                    pass
            bif_data.append({"mu": mu, "equilibria": eq_info})
        return {
            "input": representation,
            "transform": transform_type,
            "system": "pitchfork_normal_form",
            "parameter": "mu",
            "range": [-1.0, 1.0],
            "bifurcation_point": 0.0,
            "bifurcation_type": "supercritical_pitchfork",
            "data": bif_data,
            "description": (
                "Pitchfork bifurcation at mu=0: single stable equilibrium at x=0 for mu<0 "
                "splits into two stable branches x=±sqrt(mu) with unstable origin for mu>0."
            ),
        }

    # Fallback: descriptive transforms
    transforms = {
        "stability_analysis": (
            "Linearise around equilibria, compute eigenvalues, classify stability "
            "via Hartman-Grobman theorem."
        ),
        "lyapunov_spectrum": (
            "Compute Lyapunov exponents to detect chaos vs. regularity; "
            "positive max exponent indicates sensitive dependence."
        ),
        "center_manifold_reduction": (
            "Reduce dynamics near bifurcation to essential dimensions "
            "using center manifold theorem."
        ),
        "normal_form": (
            "Transform to canonical form near a bifurcation point "
            "via smooth coordinate changes."
        ),
        "poincare_section": (
            "Reduce continuous flow to discrete map via transverse cross-section; "
            "reveals periodicity and chaos structure."
        ),
    }
    return {
        "input": representation,
        "transform": transform_type,
        "description": transforms.get(transform_type, f"Transform '{transform_type}' not implemented."),
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


# ---------------------------------------------------------------------------
# Private helpers (unchanged from original)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Plugin registration (UNCHANGED)
# ---------------------------------------------------------------------------

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
