# Ruliad References Index
## Mathematical Content Consolidated from rh.1 Repository

**Generated:** 2026-02-26
**Total files with math content found:** ~55 across all search patterns
**Files copied here:** 19 (8 STRONG + 11 MEDIUM)
**Files assessed as WEAK (not copied):** ~36

---

## COPIED FILES

### STRONG — Contains actual mathematical formulas, proofs, theorem statements, or rigorous definitions

---

#### `PERELMAN_RICCI_FLOW_RESEARCH.md`
**Original path:** `/Users/sa/rh.1/docs/experimental/PERELMAN_RICCI_FLOW_RESEARCH.md`
**Mathematical depth:** STRONG

**Key formulas and theorems:**
- Ricci flow equation: `∂g_ij/∂t = -2R_ij`
- Perelman F-functional: `F(g,f) = ∫_M (R + |∇f|²) e^{-f} dV`
- Perelman W-entropy: `W(g,f,τ) = ∫_M [τ(R + |∇f|²) + f - n] u dV` where `u = (4πτ)^{-n/2} e^{-f}`
- Monotonicity theorem: `d/dt W(g(t), f(t), τ(t)) ≥ 0`
- Finite-time extinction results on specific 3-manifolds
- No-local-collapsing theorem (bounds injectivity radius)
- Ollivier-Ricci Curvature (ORC) for discrete graphs
- Forman-Ricci Curvature (FRC) for hypergraphs
- Fisher Information Metric as Riemannian metric on statistical manifolds
- Pythagorean theorem of information geometry

**Key concepts:** Ricci flow, geometric surgery, W-entropy monotonicity, Self-Organizing Survival Manifold (SOSM), Ollivier-Ricci curvature on metabolic networks, deep learning as discrete Ricci flow, "cognitive exoskeleton" as geometric stabilizer, Lyapunov function interpretation of W-entropy

**Mathematical universes:** Differential geometry, topology (3-manifolds), information geometry, control theory, network geometry, mathematical oncology

**Theorems extractable:** Perelman's W-entropy monotonicity (stated and used), no-local-collapsing theorem (referenced), finite-time extinction (referenced), geodesic existence under bounded curvature

---

#### `RHEA_VS_RULIAD.md`
**Original path:** `/Users/sa/rh.1/docs/experimental/RHEA_VS_RULIAD.md`
**Mathematical depth:** STRONG

**Key formulas and theorems (stated or referenced):**
- Wolfram's Principle of Computational Equivalence (PCE) — ontological claim
- Computational irreducibility as structural feature of Ruliad
- Ricci flow `∂g/∂t = -2Ric` → state smoothing analog
- W-entropy monotonicity → stability guarantee analog
- Causal invariance → reference frame independence analog
- SHA-256 hash-chaining as cryptographic proof of history
- Gödel incompleteness as positional phenomenon in metamathematical space

**Key concepts:** Ruliad (entangled limit of all computations), multiway graph, observer theory, branchial space, emes, Gödel navigation via metamathematical position shifts, trans-Gödelian logic, computational irreducibility detection, causal invariance as test criterion

**Mathematical universes:** Computation theory, metamathematics, differential geometry (Ricci flow), cryptography, logic (Gödel), category theory (referenced)

**Theorems extractable:** 3 convergence principles (multi-perspective sampling, Gödel navigability, geometric evolution); structural isomorphism table between Ruliad and Rhea geometric frameworks

---

#### `proof_theory.py`
**Original path:** `/Users/sa/rh.1/friends/ruliad/explorer/plugins/proof_theory.py`
**Mathematical depth:** STRONG

**Key concepts implemented:**
- Curry-Howard correspondence (proofs as programs, propositions as types)
- Cut elimination and proof normalization
- Proof complexity lower bounds
- Realizability theory (computational content extraction)
- Ordinal analysis (measuring proof-theoretic strength)
- Sequent calculus and natural deduction
- Homotopy type theory and univalence axiom
- Intuitionistic type theory vs classical logic distinction
- Gödel-Friedman double negation translation
- ZFC and beyond (axiom system strength classification)

**Mathematical universes:** Proof theory, type theory, logic, computation theory, category theory (Curry-Howard)

**Theorems extractable:** Curry-Howard correspondence (stated as mapping principle), cut elimination (named as transformation), ordinal analysis framework

---

#### `category_theory.py`
**Original path:** `/Users/sa/rh.1/friends/ruliad/explorer/plugins/category_theory.py`
**Mathematical depth:** STRONG

**Key concepts implemented:**
- Category axioms (associativity, identity)
- Functors (morphism-preserving maps between categories)
- Natural transformations
- Adjunctions (unit/counit conditions, free-forgetful)
- Limits and colimits with universal property
- Topos theory and Grothendieck topologies
- Sheaf theory on topological sites
- Yoneda lemma and representability
- Kan extensions
- Monoidal categories and enriched categories
- Cross-mappings: functors → continuous maps (topology), natural transformations → homotopies, adjunctions → Galois connections, monoidal categories → type systems, presheaves → statistical models

**Mathematical universes:** Category theory, topology, type theory, order theory, information geometry

**Theorems extractable:** Yoneda lemma (stated as principle), adjunction conditions (unit/counit requirements formalized as checks), universal property of limits (check formalized)

---

#### `information_geometry.py`
**Original path:** `/Users/sa/rh.1/friends/ruliad/explorer/plugins/information_geometry.py`
**Mathematical depth:** STRONG

**Key concepts implemented:**
- Fisher information matrix as Riemannian metric
- Statistical manifolds with natural parameterization
- Amari's dual connections: e-connection (α=1, exponential), m-connection (α=-1, mixture), Levi-Civita (α=0)
- KL divergence, Rényi divergence, f-divergence
- Exponential families and mixture families
- Natural gradient descent: `G(θ)^{-1} ∇L(θ)`
- e-projection (moment matching) and m-projection (information projection)
- Pythagorean theorem of information geometry for projections
- Information-geometric phase transitions (Fisher matrix rank drop = singularity)
- Cross-map to algebraic geometry: exponential families → algebraic varieties

**Mathematical universes:** Information geometry, Riemannian geometry, statistics, optimization, algebraic geometry

**Theorems extractable:** Pythagorean theorem of information geometry (stated), metric positivity check (formalized), divergence non-negativity conditions

---

#### `dynamical_systems.py`
**Original path:** `/Users/sa/rh.1/friends/ruliad/explorer/plugins/dynamical_systems.py`
**Mathematical depth:** STRONG

**Key concepts implemented:**
- Phase space and flow analysis (dx/dt = f(x))
- Lyapunov stability theory and Lyapunov functions
- Structural stability
- Bifurcation theory: non-degeneracy and transversality conditions
- Lyapunov exponents (chaos detection, λ > 0 condition)
- Center manifold reduction
- Normal form theory near bifurcation points
- Poincaré sections and return maps
- Ergodic theory (time average = space average condition)
- Ω-limit sets and attractor theory
- Picard-Lindelöf existence-uniqueness theorem
- Strange attractors with fractal dimension
- Cross-maps: phase space → statistical manifold, flows → functors between time categories, attractors → topological invariants

**Mathematical universes:** Dynamical systems, ergodic theory, topology, category theory, information geometry

**Theorems extractable:** Picard-Lindelöf theorem (named check), Lyapunov stability conditions (formalized), bifurcation non-degeneracy conditions (formalized), Lyapunov exponent chaos criterion

---

#### `game_theory.py`
**Original path:** `/Users/sa/rh.1/friends/ruliad/explorer/plugins/game_theory.py`
**Mathematical depth:** STRONG

**Key concepts implemented:**
- Nash equilibrium theory
- Dominant strategy identification
- Pareto optimality
- Evolutionarily Stable Strategy (ESS)
- Replicator dynamics: `dx_i/dt = x_i(f_i - f̄)`
- Bayesian games and Bayesian Nash equilibrium
- Mechanism design and revelation principle
- Signaling games
- Cooperative game theory and Shapley value
- Information completeness conditions
- Cross-map: Nash equilibria → fixed points (dynamical systems), strategy spaces → objects in a category

**Mathematical universes:** Game theory, dynamical systems (replicator), category theory, probability theory

**Theorems extractable:** Nash equilibrium existence (named), ESS stability (replicator dynamics formula given), Bayesian Nash equilibrium conditions

---

#### `engine.py`
**Original path:** `/Users/sa/rh.1/friends/ruliad/explorer/core/engine.py`
**Mathematical depth:** STRONG

**Key concepts implemented:**
- Hypothesis lifecycle as formal state machine (7 states)
- Three-layer verification pipeline: consensus + formal proof + red-team adversarial
- SHA-256 content hashing for deduplication (content_hash method)
- Lean4 stub generation for formal verification
- 6 adversarial attack strategies (find_counterexample, attack_assumptions, boundary_stress_test, domain_mismatch_probe, logical_consistency_check, steelman_alternative)
- Hypothesis graph as directed graph with cross-domain edges
- Evidence confidence scoring (0-1 scale)
- Cross-universe linking infrastructure

**Mathematical universes:** Formal verification (Lean4), graph theory, computation theory, logic

**Extractable:** Lean4 stub generation pattern, formal verification pipeline architecture, red-team attack taxonomy

---

### MEDIUM — References mathematical concepts with some depth but no formal proofs

---

#### `CHAT_SYNTHESIS_REPORT.md`
**Original path:** `/Users/sa/rh.1/archive/chats/CHAT_SYNTHESIS_REPORT.md`
**Mathematical depth:** MEDIUM

**Key theorems referenced:**
- Takens' Embedding Theorem (1981): delay embedding from scalar time series with embedding dimension 2d+1 → topological diffeomorphism to attractor
- Universality of barrier-crossing: tunneling formula exp(-barrier/energy) across alpha decay, black hole splitting, enzyme catalysis
- Gamow (1928): Alpha decay probability `w ∝ exp(-2πZe²/ℏv)`
- Volovik (2025): Black hole splitting probability `w ∝ exp(-N₁N₂)`, entropy `S_BH = N(N-1)/2`
- Klinman (2025): Enzyme catalysis `k = A·exp(-E_a/RT)`
- ΔG = ΔH − TΔS as systemic (not molecular) property
- Genetic code as topological protection (wobble position = degeneracy)

**Key concepts:** Stream-gradient ontology vs. spacetime, Mode A (static) vs. Mode B (dynamic) vs. Mode T (topological), fertility test, 0-truth protocol, tunneling barriers as universal topological class, entropy as correlations (Volovik), Leuconostoc metabolic engineering

**Mathematical universes:** Topology, dynamical systems, thermodynamics, information theory, quantum mechanics, combinatorics

---

#### `CHAT_SYNTHESIS_QUICK_REF.md`
**Original path:** `/Users/sa/rh.1/archive/chats/CHAT_SYNTHESIS_QUICK_REF.md`
**Mathematical depth:** MEDIUM

**Key theorems/formulas stated:**
- Takens (1981): embedding dimension 2d+1 guarantees topological diffeomorphism
- Gamow: Three exponentials table (nuclear/cosmic/biochemical) with formulas
- Volovik: `S_BH = N(N-1)/2` (entropy as pairwise correlations)
- Lyapunov exponent: `λ > 0 = chaos`
- Bifurcation: qualitative change in attractor structure at parameter threshold
- Ricci flow: `∂g/∂t = -2 Ric`
- KIE (kinetic isotope effect) as quantum tunneling signature
- ΔG = ΔH − TΔS as system property

**Mathematical universes:** Dynamical systems, topology, thermodynamics, information theory, quantum mechanics

---

#### `CHAT_SYNTHESIS_INDEX.md`
**Original path:** `/Users/sa/rh.1/archive/chats/CHAT_SYNTHESIS_INDEX.md`
**Mathematical depth:** MEDIUM

**Key theorems indexed:**
- Takens' Embedding Theorem (navigation by topic and thinker)
- Gamow's three tunneling formulas
- Entropy as correlations (Volovik model)
- Topological protection (genetic code degeneracy)
- Fertility Test as methodological criterion

**Mathematical universes:** Dynamical systems, topology, thermodynamics, quantum mechanics, information theory

---

#### `prism_paper_outline.md`
**Original path:** `/Users/sa/rh.1/docs/prism_paper_outline.md`
**Mathematical depth:** MEDIUM

**Key frameworks outlined:**
- State space: `x_t = (sleep_proxy, energy, time_budget, friction, vagal_state)`
- Fourier decomposition of biorhythms (individual rhythm fingerprint via spectral analysis)
- Bayesian duration model: prior → likelihood → posterior → online update
- Optimal control (MPC): maximize agency score subject to safety constraints, receding horizon replanning
- Multi-armed bandit with Thompson sampling for micro-interventions
- Tribunal consensus extraction via ICE (Iterative Consensus Ensemble) and TF-IDF similarity

**Mathematical universes:** Control theory (MPC), Bayesian inference, signal processing (Fourier), optimization (Thompson sampling), information theory (TF-IDF)

---

#### `METHODOLOGY.md`
**Original path:** `/Users/sa/rh.1/docs/METHODOLOGY.md`
**Mathematical depth:** MEDIUM

**Key formulas given:**
- State vector: `x_t = [E_t, M_t, C_t, S_t, O_t, R_t]`
- Objective function: `U = a*Progress + b*Evidence - g*Risk - d*Debt - e*MemoryLoad - z*BudgetCost`
- D-metric: `D = w1*core_docs_kb + w2*repo_size_mb + w3*open_todo_count + w4*(1/insights_per_request) + w5*avg_context_tokens`
- Tribunal: ICE (Iterative Consensus Ensemble) and TF-IDF consensus
- Ontology Explorer 3-layer verification architecture
- Formal proof hooks: Lean4/Z3 (stubbed)

**Mathematical universes:** Control theory, linear algebra (state vectors), optimization, information theory, formal verification (aspirational)

---

#### `EVOLUTION_PLAN_V1.md`
**Original path:** `/Users/sa/rh.1/docs/plans/EVOLUTION_PLAN_V1.md`
**Mathematical depth:** MEDIUM

**Key concepts referenced:**
- D-metric as curvature measure (Ruliad insight applied operationally)
- Tribunal mode as multi-perspective sampling (Ruliad → Rhea convergence)
- Ontology Explorer as metamathematical navigator
- Ricci flow / dynamical systems as research direction for A2 agent
- Category theory plugin as priority for trans-Gödelian translation program

**Mathematical universes:** Control theory, metamathematics, category theory, differential geometry (referenced)

---

#### `ADR-015_AXIOMATIC_0TRUST.md`
**Original path:** `/Users/sa/rh.1/docs/decisions/ADR-015_AXIOMATIC_0TRUST.md`
**Mathematical depth:** MEDIUM

**Key mathematical argument:**
- Uses Perelman's W-entropy (`d/dt W ≥ 0`) as operational metaphor for system trust
- "Singularity of Trust": unverified input introduces unbounded curvature (`Rc → ∞`)
- "Topological Surgery": excise contradictions and stitch manifold back to L8 ground truth
- Frames zero-trust as topological necessity, not security policy

**Mathematical universes:** Differential geometry (Ricci flow/W-entropy), topology, logic

---

#### `The_Einstein_Hallucination.yaml`
**Original path:** `/Users/sa/rh.1/apparatus/advanced/emc2/The_Einstein_Hallucination.yaml`
**Mathematical depth:** MEDIUM

**Key concepts:**
- Gödel incompleteness as epistemological exploit (undecidable structures mapped to physics)
- Duhem-Quine thesis: underdetermination of theory by data
- "Affirming the Consequent" fallacy: If T→E, E==True, therefore T==Reality
- Riemannian Geometry / Dirac's Equation as mathematical fittings vs. ontological truths
- Trans-Gödelian logic as next research direction

**Mathematical universes:** Logic (Gödel, formal systems), epistemology of mathematics, differential geometry

---

#### `sema_meta_export_2026-02-24.md`
**Original path:** `/Users/sa/rh.1/apparatus/advanced/emc2/sema_meta_export_2026-02-24.md`
**Mathematical depth:** MEDIUM

**Key mathematical content:**
- Cross-domain isomorphism validation: metabolic engineering ↔ nuclear energy access (structural mapping)
- Thermodynamic FBA (Flux Balance Analysis) as formalization of flow thinking
- ΔG as thermodynamic constraint: pathway exists iff ΔG favorable
- Tokenizability analysis as abstract resource theory framework
- Four tokenizability levers as topological accessibility metric

**Mathematical universes:** Thermodynamics, systems biology, resource theory (abstract)

---

#### `DECON-REL-BIO-2026-X.md`
**Original path:** `/Users/sa/rh.1/apparatus/advanced/emc2/DECON-REL-BIO-2026-X.md`
**Mathematical depth:** MEDIUM

**Key concepts:**
- Perelman's Ricci Flow with Surgery as "surgical recovery" from hallucinated ontologies
- Gödel-check: external verification via Condensed Matter Physics (Volovik) and Topology (Perelman) breaks self-referential Einstein-Dirac loop
- Ricci Flow math universality: applies to fluids, data, crystals, bio-networks
- Fertility Test metrics: (Narrative × Funding) / (Working Tools)
- 0-Truth Matrix methodology

**Mathematical universes:** Differential geometry, topology, logic (Gödel), computation theory

---

#### `ONTOLOGY_BRIDGE_VALIDATION.md`
**Original path:** `/Users/sa/rh.1/docs/ONTOLOGY_BRIDGE_VALIDATION.md`
**Mathematical depth:** MEDIUM

**Key mathematical content:**
- REST API verification of 3-layer mathematical verification pipeline
- Consensus scoring: agreement at 44% in live tribunal test
- Tribunal architecture: k parallel models, consensus analyzer, structured JSON
- Formal verification integration (Lean4/Z3 stubs documented)
- ICE (Iterative Consensus Ensemble) consensus mode vs. Chairman mode

**Mathematical universes:** Formal verification (Lean4/Z3), information theory (consensus scoring)

---

## SUMMARY STATISTICS

| Category | Count | Notes |
|----------|-------|-------|
| STRONG files | 8 | Contain actual formulas, theorem statements, rigorous definitions |
| MEDIUM files | 11 | Reference mathematical concepts with significant depth |
| WEAK files (not copied) | ~36 | Mention math terms in passing; operational docs, logs, chat transcripts |
| Total files found with math content | ~55 | Across all search patterns in 1694 files |

---

## MATHEMATICAL UNIVERSES REPRESENTED

| Universe | Coverage | Depth | Key Files |
|----------|----------|-------|-----------|
| **Differential Geometry / Ricci Flow** | HIGH | STRONG | PERELMAN_RICCI_FLOW_RESEARCH.md, RHEA_VS_RULIAD.md, ADR-015_AXIOMATIC_0TRUST.md |
| **Information Geometry** | HIGH | STRONG | information_geometry.py, PERELMAN_RICCI_FLOW_RESEARCH.md |
| **Category Theory** | HIGH | STRONG | category_theory.py, proof_theory.py |
| **Proof Theory / Type Theory** | HIGH | STRONG | proof_theory.py, engine.py |
| **Dynamical Systems** | HIGH | STRONG | dynamical_systems.py, CHAT_SYNTHESIS_QUICK_REF.md |
| **Game Theory** | MEDIUM | STRONG | game_theory.py |
| **Topology** | MEDIUM | STRONG | PERELMAN_RICCI_FLOW_RESEARCH.md, dynamical_systems.py, CHAT_SYNTHESIS_REPORT.md |
| **Control Theory (MPC/LQR)** | MEDIUM | MEDIUM | prism_paper_outline.md, METHODOLOGY.md |
| **Information Theory (Shannon/Kolmogorov)** | MEDIUM | MEDIUM | CHAT_SYNTHESIS_QUICK_REF.md, prism_paper_outline.md |
| **Computational Theory / Ruliad** | MEDIUM | STRONG | RHEA_VS_RULIAD.md, proof_theory.py |
| **Logic (Gödel/metamathematics)** | MEDIUM | STRONG | RHEA_VS_RULIAD.md, The_Einstein_Hallucination.yaml, proof_theory.py |
| **Thermodynamics** | MEDIUM | MEDIUM | CHAT_SYNTHESIS_REPORT.md, sema_meta_export_2026-02-24.md |
| **Bayesian Inference** | LOW | MEDIUM | prism_paper_outline.md |
| **Quantum Mechanics (tunneling)** | LOW | MEDIUM | CHAT_SYNTHESIS_REPORT.md |
| **Formal Verification (Lean4/Z3)** | ASPIRATIONAL | — | engine.py, proof_theory.py (stubs only) |
| **Algebraic Geometry** | MENTIONED | — | information_geometry.py (cross-map only) |

---

## THEOREMS / FORMAL RESULTS EXTRACTABLE

| Theorem/Result | Source File | Status |
|----------------|-------------|--------|
| Perelman W-entropy monotonicity: `d/dt W ≥ 0` | PERELMAN_RICCI_FLOW_RESEARCH.md | Stated with formula |
| Perelman no-local-collapsing | PERELMAN_RICCI_FLOW_RESEARCH.md | Referenced |
| Ricci flow equation: `∂g_ij/∂t = -2R_ij` | PERELMAN_RICCI_FLOW_RESEARCH.md | Stated |
| Ricci flow finite-time extinction | PERELMAN_RICCI_FLOW_RESEARCH.md | Referenced |
| Takens' Embedding Theorem (2d+1 embedding) | CHAT_SYNTHESIS_REPORT.md, CHAT_SYNTHESIS_QUICK_REF.md | Stated |
| Curry-Howard correspondence | proof_theory.py | Stated as principle |
| Cut elimination | proof_theory.py | Named as transformation |
| Yoneda lemma | category_theory.py | Stated as principle |
| Adjunction unit/counit conditions | category_theory.py | Formalized as check |
| Universal property of limits | category_theory.py | Formalized as check |
| Pythagorean theorem (information geometry) | information_geometry.py | Stated |
| Fisher metric positive-definiteness | information_geometry.py | Formalized as check |
| Picard-Lindelöf existence-uniqueness | dynamical_systems.py | Named as check |
| Lyapunov stability conditions | dynamical_systems.py | Formalized |
| Bifurcation non-degeneracy/transversality | dynamical_systems.py | Formalized as check |
| ESS (replicator dynamics): `dx_i/dt = x_i(f_i - f̄)` | game_theory.py | Formula given |
| Gamow alpha decay: `w ∝ exp(-2πZe²/ℏv)` | CHAT_SYNTHESIS_REPORT.md | Formula given |
| Volovik entropy: `S_BH = N(N-1)/2` | CHAT_SYNTHESIS_REPORT.md | Formula given |
| Gödel incompleteness as positional (Ruliad) | RHEA_VS_RULIAD.md | Structural argument |
| PCE (Wolfram Principle of Computational Equivalence) | RHEA_VS_RULIAD.md | Referenced |

**Total extractable theorems/results: ~20**

---

## GAPS IN THE MATHEMATICAL FOUNDATION

The following mathematical universes are either absent or underdeveloped relative to the project's stated ambitions:

1. **Formal proofs (Lean4/Z3):** Zero actual `.lean` or `.z3` files exist. The proof infrastructure is entirely aspirational. engine.py generates Lean4 stubs with `sorry`, never real proofs.

2. **Algebraic topology (homology, cohomology, homotopy groups):** Referenced in passing (category theory plugin cross-maps to "homotopy theory") but no actual content.

3. **Quantum mechanics formalism:** Tunneling referenced in chat synthesis; no Schrödinger equation, no Hamiltonian framework, no path integral formulation.

4. **Ergodic theory:** dynamical_systems.py lists it as a key concept but no actual ergodic theorems are stated or applied.

5. **Spectral theory:** Fourier decomposition is mentioned in prism_paper_outline.md but no actual spectral analysis formalism exists.

6. **Algebraic geometry:** information_geometry.py mentions "exponential families → algebraic varieties" as a cross-map but no content.

7. **Number theory / arithmetic:** Completely absent. The cryptographic hash-chaining (SHA-256) is operational but mathematically unanalyzed.

8. **Stochastic processes (SDEs, Markov chains):** prism_paper_outline.md mentions Thompson sampling but no SDE or Markov framework is developed.

9. **Measure theory / functional analysis:** The W-entropy is defined as an integral but no rigorous measure-theoretic treatment exists.

10. **Compressed sensing / sparse representation:** Referenced in nexus documents as "Sparse Priming Representation (SPR)" but never formalized mathematically.

---

## NOTES ON RATING METHODOLOGY

**STRONG criteria applied:**
- Contains LaTeX or ASCII-art mathematical formulas
- Names specific theorems with conditions/statements
- Implements formal mathematical structures in code (functors, morphisms, verification checks)
- States mathematical claims that could be formalized in a proof assistant

**MEDIUM criteria applied:**
- References specific theorems by name with correct attribution
- Uses mathematical vocabulary precisely within the correct domain
- Contains cross-domain mappings that could be formalized
- Lacks explicit formulas but demonstrates genuine mathematical understanding

**WEAK (not copied) criteria:**
- Uses terms like "curvature," "entropy," "topology" in metaphorical or casual sense
- Operational logs, session records, agent communications
- References math only as motivation or analogy
- No specific theorems, formulas, or rigorous definitions
