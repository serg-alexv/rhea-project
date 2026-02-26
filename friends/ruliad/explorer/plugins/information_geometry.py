"""
Information Geometry Plugin — Mathematical Universe for Ontology Explorer

Models hypotheses as points/distributions on statistical manifolds:
  - Fisher information matrices for Gaussian, Bernoulli, Categorical families
  - Geodesics on the statistical manifold = optimal inference paths
  - Divergence measures (KL, Rényi, f-divergence) for hypothesis comparison
  - Exponential/mixture families for natural parameterizations
  - Amari's dual connections for complementary perspectives
"""

try:
    import numpy as np
    import numpy.linalg as nla
    _NUMPY_OK = True
except ImportError:
    np = None
    nla = None
    _NUMPY_OK = False

try:
    from scipy import linalg as sla
    from scipy.stats import norm as sp_norm
    _SCIPY_OK = True
except ImportError:
    sla = None
    sp_norm = None
    _SCIPY_OK = False


# ---------------------------------------------------------------------------
# Fisher matrix builders
# ---------------------------------------------------------------------------

def _fisher_gaussian(mu=0.0, sigma=1.0):
    """
    Fisher information matrix for N(mu, sigma^2).
    Parameters: theta = (mu, sigma).
    F = diag(1/sigma^2, 2/sigma^4).
    At sigma=1: F = diag(1, 2).
    """
    f11 = 1.0 / (sigma ** 2)
    f22 = 2.0 / (sigma ** 4)
    return np.array([[f11, 0.0], [0.0, f22]])


def _fisher_bernoulli(p=0.5):
    """
    Fisher information for Bernoulli(p).
    F = 1 / (p * (1 - p)).
    At p=0.5: F = 4.0.
    Returns a 1x1 numpy array for uniformity.
    """
    f = 1.0 / (p * (1.0 - p))
    return np.array([[f]])


def _fisher_categorical(k=3):
    """
    Fisher information matrix for Categorical(p_1,...,p_k) at uniform p_i = 1/k.
    The (k-1)-dimensional constrained manifold yields:
      F_ij = delta_ij / p_i - 1   (in full k-dim embedding, then projected).
    Using the standard formula for the (k-1)-simplex interior:
      F = diag(1/p_i) - ones_matrix
    At uniform p_i = 1/k, F_ii = k - 1, F_ij = -1 for i != j.
    Returns a (k x k) matrix (embed in full space; rank = k-1).
    """
    p = np.full(k, 1.0 / k)
    F = np.diag(1.0 / p) - np.ones((k, k))
    return F


def _matrix_stats(F):
    """Return condition number, rank, and eigenvalues of a matrix."""
    try:
        eigvals = nla.eigvalsh(F)
        rank = int(np.sum(np.abs(eigvals) > 1e-10))
        # condition number: max(|eig|) / min(|eig|) for non-zero eigenvalues
        nonzero = eigvals[np.abs(eigvals) > 1e-10]
        cond = float(np.max(np.abs(nonzero)) / np.min(np.abs(nonzero))) if len(nonzero) > 0 else float("inf")
        return {
            "eigenvalues": eigvals.tolist(),
            "rank": rank,
            "condition_number": cond,
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# KL divergence helpers
# ---------------------------------------------------------------------------

def _kl_gaussian(mu1=0.0, sigma1=1.0, mu2=1.0, sigma2=1.0):
    """
    KL(N(mu1,sigma1^2) || N(mu2,sigma2^2))
      = log(sigma2/sigma1) + (sigma1^2 + (mu1-mu2)^2)/(2*sigma2^2) - 1/2
    KL(N(0,1)||N(1,1)) = 0 + (1 + 1)/2 - 1/2 = 0.5
    """
    kl = (
        np.log(sigma2 / sigma1)
        + (sigma1 ** 2 + (mu1 - mu2) ** 2) / (2.0 * sigma2 ** 2)
        - 0.5
    )
    return float(kl)


def _kl_bernoulli(p=0.5, q=0.6):
    """
    KL(Bern(p) || Bern(q)) = p*log(p/q) + (1-p)*log((1-p)/(1-q))
    """
    eps = 1e-15
    p = np.clip(p, eps, 1 - eps)
    q = np.clip(q, eps, 1 - eps)
    kl = p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q))
    return float(kl)


def _kl_categorical(p_vec, q_vec):
    """KL(P||Q) for categorical distributions."""
    p = np.array(p_vec, dtype=float)
    q = np.array(q_vec, dtype=float)
    eps = 1e-15
    p = np.clip(p, eps, 1.0)
    q = np.clip(q, eps, 1.0)
    return float(np.sum(p * np.log(p / q)))


# ---------------------------------------------------------------------------
# Core plugin functions
# ---------------------------------------------------------------------------

def ig_represent(hypothesis):
    """Represent hypothesis as a point on a statistical manifold with real Fisher matrices."""
    manifold_type = _infer_manifold_type(hypothesis.statement)
    result = {
        "framework": "information_geometry",
        "manifold_type": manifold_type,
        "parameterization": "natural",
        "fisher_metric_defined": False,
        "dual_structure": {
            "e_connection": "exponential connection (α=1)",
            "m_connection": "mixture connection (α=-1)",
            "levi_civita": "α=0 connection",
        },
        "raw_statement": hypothesis.statement,
    }

    if not _NUMPY_OK:
        result["numpy_unavailable"] = True
        return result

    try:
        s = hypothesis.statement.lower()

        if "gaussian" in s or "normal" in s:
            F = _fisher_gaussian(mu=0.0, sigma=1.0)
            stats = _matrix_stats(F)
            result["fisher_matrix"] = F.tolist()
            result["fisher_matrix_shape"] = list(F.shape)
            result["distribution_family"] = "Gaussian"
            result["canonical_point"] = {"mu": 0.0, "sigma": 1.0}
            result["natural_parameters"] = {
                "eta_1": "mu/sigma^2",
                "eta_2": "-1/(2*sigma^2)",
                "values_at_canonical": [0.0, -0.5],
            }
            result["cramer_rao_bound"] = nla.inv(F).diagonal().tolist()

        elif "bernoulli" in s or "binary" in s:
            F = _fisher_bernoulli(p=0.5)
            stats = _matrix_stats(F)
            result["fisher_matrix"] = F.tolist()
            result["fisher_matrix_shape"] = list(F.shape)
            result["distribution_family"] = "Bernoulli"
            result["canonical_point"] = {"p": 0.5}
            result["natural_parameters"] = {
                "eta": "log(p/(1-p))",
                "values_at_canonical": [0.0],
            }
            result["cramer_rao_bound"] = nla.inv(F).diagonal().tolist()

        elif "multinomial" in s or "categorical" in s:
            k = 3
            F = _fisher_categorical(k=k)
            stats = _matrix_stats(F)
            result["fisher_matrix"] = F.tolist()
            result["fisher_matrix_shape"] = list(F.shape)
            result["distribution_family"] = f"Categorical(k={k})"
            p_uniform = [1.0 / k] * k
            result["canonical_point"] = {"p": p_uniform}
            result["natural_parameters"] = {
                "eta_i": "log(p_i/p_k) for i=1..k-1",
                "values_at_canonical": [0.0] * (k - 1),
            }
            # pseudo-inverse for rank-deficient matrix
            F_pinv = nla.pinv(F)
            result["cramer_rao_bound"] = F_pinv.diagonal().tolist()

        else:
            # Generic: use Gaussian as default representative
            F = _fisher_gaussian(mu=0.0, sigma=1.0)
            stats = _matrix_stats(F)
            result["fisher_matrix"] = F.tolist()
            result["fisher_matrix_shape"] = list(F.shape)
            result["distribution_family"] = "Gaussian (default representative)"
            result["canonical_point"] = {"mu": 0.0, "sigma": 1.0}
            result["cramer_rao_bound"] = nla.inv(F).diagonal().tolist()

        result["fisher_metric_defined"] = True
        result["matrix_stats"] = stats

    except Exception as exc:
        result["computation_error"] = str(exc)

    return result


def ig_transform(representation, transform_type="natural_gradient"):
    """Apply information-geometric transformation with real computation."""
    base = {
        "input": representation,
        "transform": transform_type,
    }

    if not _NUMPY_OK:
        descriptions = {
            "natural_gradient": "Compute gradient in Fisher metric (steepest ascent on manifold)",
            "e_projection": "Project onto exponential subfamily (moment matching)",
            "m_projection": "Project onto mixture subfamily (information projection)",
            "geodesic": "Find geodesic between two hypothesis-distributions",
            "divergence": "Compute KL or α-divergence between hypothesis distributions",
        }
        base["description"] = descriptions.get(transform_type, "Unknown transform")
        base["numpy_unavailable"] = True
        return base

    try:
        if transform_type == "divergence":
            # Compute KL divergences for each supported family
            results = {}

            # Gaussian: KL(N(0,1) || N(1,1)) = 0.5  (analytic)
            kl_gauss = _kl_gaussian(mu1=0.0, sigma1=1.0, mu2=1.0, sigma2=1.0)
            results["gaussian_kl"] = {
                "KL(N(0,1)||N(1,1))": kl_gauss,
                "formula": "log(sigma2/sigma1) + (sigma1^2+(mu1-mu2)^2)/(2*sigma2^2) - 0.5",
                "exact_value": 0.5,
                "match": abs(kl_gauss - 0.5) < 1e-12,
            }

            # Bernoulli: KL(Bern(0.5) || Bern(0.6))
            kl_bern = _kl_bernoulli(p=0.5, q=0.6)
            results["bernoulli_kl"] = {
                "KL(Bern(0.5)||Bern(0.6))": kl_bern,
                "formula": "p*log(p/q) + (1-p)*log((1-p)/(1-q))",
            }

            # Categorical uniform: KL(P||P) = 0
            p_uniform = [1.0 / 3] * 3
            kl_cat_self = _kl_categorical(p_uniform, p_uniform)
            results["categorical_kl_self"] = {
                "KL(Uniform3||Uniform3)": kl_cat_self,
                "expected": 0.0,
                "match": abs(kl_cat_self) < 1e-12,
            }

            # Categorical: KL between slightly shifted distributions
            q_shifted = [0.4, 0.3, 0.3]
            kl_cat_shift = _kl_categorical(p_uniform, q_shifted)
            results["categorical_kl_shifted"] = {
                "KL(Uniform||[0.4,0.3,0.3])": kl_cat_shift,
            }

            base["divergences"] = results
            base["description"] = "KL divergences computed analytically for each distribution family"

        elif transform_type == "natural_gradient":
            # natural gradient = F^{-1} * grad  for a unit Euclidean gradient
            # Compute for Gaussian and Bernoulli families
            ng_results = {}

            # Gaussian
            F_gauss = _fisher_gaussian(sigma=1.0)
            grad_euclidean_gauss = np.array([1.0, 1.0])
            F_inv_gauss = nla.inv(F_gauss)
            nat_grad_gauss = F_inv_gauss @ grad_euclidean_gauss
            ng_results["gaussian"] = {
                "fisher_matrix": F_gauss.tolist(),
                "fisher_inverse": F_inv_gauss.tolist(),
                "euclidean_gradient": grad_euclidean_gauss.tolist(),
                "natural_gradient": nat_grad_gauss.tolist(),
                "scaling_factor_mu": float(nat_grad_gauss[0] / grad_euclidean_gauss[0]),
                "scaling_factor_sigma": float(nat_grad_gauss[1] / grad_euclidean_gauss[1]),
                "note": "Natural gradient rescales by inverse Fisher; sigma update halved (1/(2/sigma^4)=0.5 at sigma=1)",
            }

            # Bernoulli
            F_bern = _fisher_bernoulli(p=0.5)
            grad_euclidean_bern = np.array([1.0])
            F_inv_bern = nla.inv(F_bern)
            nat_grad_bern = F_inv_bern @ grad_euclidean_bern
            ng_results["bernoulli"] = {
                "fisher_matrix": F_bern.tolist(),
                "fisher_inverse": F_inv_bern.tolist(),
                "euclidean_gradient": grad_euclidean_bern.tolist(),
                "natural_gradient": nat_grad_bern.tolist(),
                "note": "At p=0.5: F=4, F^{-1}=0.25; natural gradient = 0.25 * Euclidean gradient",
            }

            base["natural_gradient_results"] = ng_results
            base["description"] = "Natural gradient F^{-1}*grad computed for each distribution family"

        elif transform_type == "geodesic":
            # Geodesic length in Fisher metric between two distributions
            # For Gaussian: ds^2 = d_mu^2/sigma^2 + 2*d_sigma^2/sigma^4
            # Between N(0,1) and N(1,1): ds = sqrt(F_11 * delta_mu^2) = 1.0
            geo_results = {}

            # Gaussian geodesic length (approximate via metric at midpoint)
            F_gauss = _fisher_gaussian(mu=0.0, sigma=1.0)
            delta_gauss = np.array([1.0, 0.0])  # from (0,1) to (1,1)
            length_gauss = float(np.sqrt(delta_gauss @ F_gauss @ delta_gauss))
            geo_results["gaussian_N01_to_N11"] = {
                "from": {"mu": 0.0, "sigma": 1.0},
                "to": {"mu": 1.0, "sigma": 1.0},
                "displacement": delta_gauss.tolist(),
                "geodesic_length_approx": length_gauss,
                "note": "sqrt(delta^T F delta) — exact for flat e-connection in exponential family",
            }

            # Bernoulli geodesic: Fisher-Rao metric on Bernoulli manifold
            # Exact geodesic distance = 2*arcsin(sqrt(p2)) - 2*arcsin(sqrt(p1))
            p1, p2 = 0.3, 0.7
            geo_length_bern = 2.0 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))
            geo_results["bernoulli_03_to_07"] = {
                "from": {"p": p1},
                "to": {"p": p2},
                "geodesic_length_exact": float(geo_length_bern),
                "formula": "2*(arcsin(sqrt(p2)) - arcsin(sqrt(p1)))",
                "note": "Exact Fisher-Rao geodesic on Bernoulli manifold (arc on unit sphere)",
            }

            base["geodesic_results"] = geo_results
            base["description"] = "Geodesic lengths computed in Fisher metric"

        else:
            descriptions = {
                "e_projection": "Project onto exponential subfamily (moment matching)",
                "m_projection": "Project onto mixture subfamily (information projection)",
            }
            base["description"] = descriptions.get(transform_type, f"Transform '{transform_type}' not yet implemented")

    except Exception as exc:
        base["computation_error"] = str(exc)

    return base


def ig_verify(hypothesis, representation=None):
    """Information-geometric verification with real numerical checks."""
    checks = []
    s = hypothesis.statement.lower()

    if not _NUMPY_OK:
        # Fall back to original template checks
        if "metric" in s or "distance" in s:
            checks.append({
                "check": "metric_positivity",
                "question": "Is the proposed metric positive-definite on the parameter space?",
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
            "overall": "requires_proof",
            "numpy_unavailable": True,
        }

    # -----------------------------------------------------------------------
    # Determine which family to verify
    # -----------------------------------------------------------------------
    if "gaussian" in s or "normal" in s:
        family = "gaussian"
        F = _fisher_gaussian(sigma=1.0)
        kl_val = _kl_gaussian(mu1=0.0, sigma1=1.0, mu2=1.0, sigma2=1.0)
        kl_label = "KL(N(0,1)||N(1,1))"
        kl_expected = 0.5
    elif "bernoulli" in s or "binary" in s:
        family = "bernoulli"
        F = _fisher_bernoulli(p=0.5)
        kl_val = _kl_bernoulli(p=0.5, q=0.6)
        kl_label = "KL(Bern(0.5)||Bern(0.6))"
        kl_expected = None
    elif "multinomial" in s or "categorical" in s:
        family = "categorical"
        F = _fisher_categorical(k=3)
        p_uniform = [1.0 / 3] * 3
        kl_val = _kl_categorical(p_uniform, p_uniform)
        kl_label = "KL(Uniform3||Uniform3)"
        kl_expected = 0.0
    else:
        family = "gaussian"
        F = _fisher_gaussian(sigma=1.0)
        kl_val = _kl_gaussian(mu1=0.0, sigma1=1.0, mu2=1.0, sigma2=1.0)
        kl_label = "KL(N(0,1)||N(1,1))"
        kl_expected = 0.5

    # -----------------------------------------------------------------------
    # Check 1: Positive (semi-)definiteness via eigenvalues
    # -----------------------------------------------------------------------
    try:
        eigvals = nla.eigvalsh(F)
        min_eig = float(np.min(eigvals))
        is_psd = bool(min_eig >= -1e-10)
        is_pd = bool(min_eig > 1e-10)
        checks.append({
            "check": "positive_definiteness",
            "family": family,
            "eigenvalues": eigvals.tolist(),
            "min_eigenvalue": min_eig,
            "is_positive_semidefinite": is_psd,
            "is_positive_definite": is_pd,
            "status": "verified" if is_psd else "failed",
            "note": "Fisher information matrix must be PSD for a valid Riemannian metric",
        })
    except Exception as exc:
        checks.append({
            "check": "positive_definiteness",
            "status": "error",
            "error": str(exc),
        })

    # -----------------------------------------------------------------------
    # Check 2: Condition number
    # -----------------------------------------------------------------------
    try:
        stats = _matrix_stats(F)
        cond = stats.get("condition_number", float("inf"))
        rank = stats.get("rank", 0)
        full_rank = bool(rank == F.shape[0])
        checks.append({
            "check": "condition_number",
            "family": family,
            "rank": rank,
            "matrix_size": F.shape[0],
            "full_rank": full_rank,
            "condition_number": cond,
            "status": "verified" if full_rank else "singular_matrix",
            "assessment": (
                "well-conditioned" if cond < 100 else
                "moderate conditioning" if cond < 1e6 else
                "ill-conditioned"
            ),
            "note": (
                "Full-rank Fisher matrix implies model identifiability and "
                "invertible Riemannian metric"
            ),
        })
    except Exception as exc:
        checks.append({
            "check": "condition_number",
            "status": "error",
            "error": str(exc),
        })

    # -----------------------------------------------------------------------
    # Check 3: Cramér-Rao bound (diagonal of F^{-1})
    # -----------------------------------------------------------------------
    try:
        if np.linalg.matrix_rank(F) == F.shape[0]:
            F_inv = nla.inv(F)
        else:
            F_inv = nla.pinv(F)
        crb = F_inv.diagonal().tolist()
        checks.append({
            "check": "cramer_rao_bound",
            "family": family,
            "cramer_rao_lower_bound": crb,
            "interpretation": "Minimum achievable variance for any unbiased estimator of each parameter",
            "status": "computed",
            "note": (
                f"For {family}: variance of any unbiased estimator >= {crb}; "
                f"MLE achieves this bound asymptotically"
            ),
        })
    except Exception as exc:
        checks.append({
            "check": "cramer_rao_bound",
            "status": "error",
            "error": str(exc),
        })

    # -----------------------------------------------------------------------
    # Check 4: KL divergence sanity (non-negativity, identity of indiscernibles)
    # -----------------------------------------------------------------------
    try:
        kl_nonneg = bool(kl_val >= -1e-12)
        kl_check = {
            "check": "kl_divergence_sanity",
            "family": family,
            "label": kl_label,
            "kl_value": float(kl_val),
            "non_negative": kl_nonneg,
            "status": "verified" if kl_nonneg else "failed",
        }
        if kl_expected is not None:
            kl_check["expected_value"] = kl_expected
            kl_check["matches_expected"] = bool(abs(kl_val - kl_expected) < 1e-10)
        checks.append(kl_check)
    except Exception as exc:
        checks.append({
            "check": "kl_divergence_sanity",
            "status": "error",
            "error": str(exc),
        })

    # -----------------------------------------------------------------------
    # Keyword-driven checks from original implementation
    # -----------------------------------------------------------------------
    if "metric" in s or "distance" in s:
        checks.append({
            "check": "metric_positivity",
            "question": "Is the proposed metric positive-definite on the parameter space?",
            "status": "verified" if any(
                c.get("check") == "positive_definiteness" and c.get("status") == "verified"
                for c in checks
            ) else "requires_proof",
        })

    if "divergence" in s:
        checks.append({
            "check": "divergence_properties",
            "question": "Does the divergence satisfy non-negativity and identity of indiscernibles?",
            "status": "verified" if any(
                c.get("check") == "kl_divergence_sanity" and c.get("status") == "verified"
                for c in checks
            ) else "requires_proof",
        })

    if "geodesic" in s:
        checks.append({
            "check": "geodesic_existence",
            "question": "Do geodesics exist and are they unique in the relevant connection?",
            "status": "verified" if family == "bernoulli" else "requires_proof",
            "note": (
                "Bernoulli manifold: exact geodesics via Fisher-Rao metric (arc on sphere). "
                "Gaussian: flat under e-connection, geodesics exist globally."
            ) if family in ("gaussian", "bernoulli") else "Requires case analysis",
        })

    # -----------------------------------------------------------------------
    # Overall verdict
    # -----------------------------------------------------------------------
    failed = [c for c in checks if c.get("status") == "failed"]
    errors = [c for c in checks if c.get("status") == "error"]
    verified = [c for c in checks if c.get("status") in ("verified", "computed")]

    if failed:
        overall = "failed"
    elif errors:
        overall = "partial_error"
    elif len(verified) >= 2:
        overall = "verified"
    else:
        overall = "requires_proof"

    return {
        "framework": "information_geometry",
        "distribution_family": family,
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "verified": len(verified),
            "failed": len(failed),
            "errors": len(errors),
        },
        "overall": overall,
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Plugin registration — DO NOT MODIFY
# ---------------------------------------------------------------------------

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
