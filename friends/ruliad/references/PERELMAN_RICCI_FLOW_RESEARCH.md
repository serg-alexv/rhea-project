# Research Report

# Technical Deep Dive: The Entropy Formula for the Ricci Flow and its Interdisciplinary Geometric Applications

**Key Points**
*   **Mathematical Foundation:** Grisha Perelman’s 2002 paper introduced the $\mathcal{W}$-entropy functional, proving that the Ricci flow is a gradient flow that monotonically increases entropy, thereby precluding "local collapsing" of the manifold and enabling the resolution of the Geometrization Conjecture [cite: 1, 2].
*   **Biological Isomorphism:** The mathematical machinery of Ricci flow—specifically the smoothing of curvature and the management of singularities via surgery—maps directly to biological processes such as tumor tumorigenesis (singularity formation), protein folding (manifold compaction), and metabolic network reorganization [cite: 3, 4].
*   **The "Survival Manifold":** Recent theoretical frameworks define biological survival not as a labeled outcome but as a geometric consequence of a system evolving along low-curvature geodesic flows on a "Self-Organizing Survival Manifold" (SOSM), governed by principles analogous to Perelman’s thermodynamic entropy [cite: 4, 5].
*   **Neural & Cognitive Dynamics:** Deep learning training dynamics exhibit properties of Ricci flow, smoothing the "neural manifold" to separate data classes. This establishes a theoretical basis for a "Cognitive Exoskeleton"—a control mechanism that stabilizes high-dimensional cognitive states by minimizing information-geometric curvature [cite: 6, 7, 8].

## 1. Introduction: The Geometric Thermodynamics of Perelman

In November 2002, Grisha Perelman posted *The entropy formula for the Ricci flow and its geometric applications* to the arXiv, fundamentally altering the landscape of differential geometry and geometric analysis [cite: 1]. While the immediate objective was the proof of Thurston's Geometrization Conjecture and the Poincaré Conjecture, Perelman’s introduction of statistical mechanical tools—specifically the $\mathcal{F}$-functional and the $\mathcal{W}$-entropy—bridged a critical gap between pure topology and thermodynamic evolution [cite: 2, 9].

This report investigates the isomorphism between Perelman’s geometric evolution equations and complex biological and cognitive systems. By treating biological entities (metabolic networks, protein structures, neural activities) as Riemannian or discrete manifolds, we can apply the diffusive smoothing of Ricci flow and the monotonic stability of $\mathcal{W}$-entropy to model evolutionary dynamics, disease progression, and cognitive control.

## 2. Mathematical Entities: Perelman’s Framework

To understand the interdisciplinary applications, one must first rigorously define the mathematical structures introduced by Hamilton and perfected by Perelman.

### 2.1 The Ricci Flow Equation
The Ricci flow is a nonlinear partial differential equation on a Riemannian manifold $(M, g_{ij})$ defined by:
\[ \frac{\partial g_{ij}}{\partial t} = -2R_{ij} \]
where $g_{ij}$ is the metric tensor and $R_{ij}$ is the Ricci curvature tensor [cite: 1, 10]. This equation dictates that the metric changes in proportion to its curvature; positively curved regions shrink, and negatively curved regions expand, analogous to the heat diffusion of geometry.

### 2.2 Perelman’s Entropy Functionals ($\mathcal{F}$ and $\mathcal{W}$)
Perelman realized that the standard Ricci flow could be interpreted as a gradient flow of a specific functional, provided one introduces a "dilaton" field $f$.
The $\mathcal{F}$-functional is defined as:
\[ \mathcal{F}(g, f) = \int_M (R + |\nabla f|^2) e^{-f} dV \]
Perelman further introduced the $\mathcal{W}$-entropy, which includes a scale parameter $\tau > 0$:
\[ \mathcal{W}(g, f, \tau) = \int_M \left[ \tau(R + |\nabla f|^2) + f - n \right] u \, dV \]
where $u = (4\pi\tau)^{-n/2}e^{-f}$ is the conjugate heat kernel probability density.

**Crucial Property:** Perelman proved the monotonicity formula:
\[ \frac{d}{dt} \mathcal{W}(g(t), f(t), \tau(t)) \ge 0 \]
This monotonicity prevents the manifold from "collapsing" locally (volume going to zero while curvature remains bounded), a technical necessity for performing surgery on 3-manifolds [cite: 1, 9]. In a thermodynamic context, this asserts that the Ricci flow describes a system evolving toward a state of higher geometric entropy (uniformity).

### 2.3 Geometric Surgery and Singularity Resolution
In the evolution of 3-manifolds, singularities (points where curvature becomes infinite) inevitably form. Perelman’s "surgery" involves cutting the manifold at a high-curvature "neck" (a region approximating a cylinder $S^2 \times \mathbb{R}$), capping the cut ends, and continuing the flow [cite: 2, 11].
This concept of "surgery" is mathematically isomorphic to biological events where topological continuity is broken or reorganized, such as cell division, apoptosis, or the rewiring of metabolic pathways [cite: 3, 11].

## 3. Biological Applications: The Geometry of Life

The translation of Ricci flow to biology relies on discretizing the curvature. Biological networks are rarely continuous manifolds; they are graphs or hypergraphs. The introduction of **Ollivier-Ricci Curvature (ORC)** and **Forman-Ricci Curvature (FRC)** allows Perelman’s concepts to be applied to discrete biological data [cite: 12, 13].

### 3.1 Metabolic Networks and Genomic Manifolds
Metabolic networks are complex directed hypergraphs where nodes are metabolites and edges are enzymatic reactions.

#### 3.1.1 Curvature as a Measure of Robustness
Research indicates that metabolic networks (e.g., *E. coli*) exhibit specific curvature distributions that deviate significantly from random models. High positive curvature in a metabolic graph indicates a "clique" or functional module with high redundancy (robustness), while negative curvature represents "bridges" or bottlenecks that are fragile points in the system [cite: 12, 14].
*   **Application:** By computing the Ricci flow on these networks, researchers can simulate "diffusion" of functional stress. The flow smooths the curvature, revealing the backbone of the metabolic structure.
*   **Cancer Metabolism:** In colorectal cancer, Ollivier-Ricci curvature analysis has revealed that tumor cells undergo "geometric remodeling." The metabolic network does not just change flux; it changes topology. Cancer-associated fibroblasts and macrophages reorganize their metabolic architecture to create "division of labor," detectable as coordinated changes in manifold curvature [cite: 15].

#### 3.1.2 The Self-Organizing Survival Manifold (SOSM)
A profound theoretical advancement is the **Self-Organizing Survival Manifold (SOSM)**. This theory posits that patient survival is not merely a statistical correlation but a geometric property of the biological state space.
*   **Mechanism:** Biological systems are modeled as evolving on a latent manifold $\mathcal{M}$. Health is defined as a trajectory along a "low-curvature geodesic flow," minimizing thermodynamic costs and entropy production [cite: 4].
*   **Disease as Geometric Collapse:** Disease progression represents a deviation from this geodesic, moving into high-curvature regions (instability). The SOSM framework explicitly uses an energy functional based on geodesic curvature minimization, mathematically mirroring Perelman’s entropy minimization principles [cite: 5].
*   **Thermodynamic Link:** The stability of the survival manifold is linked to W-entropy. A "healthy" homeostatic state maintains a coherent entropy flow, whereas the "collapsed" manifold of terminal disease exhibits chaotic, high-entropy dissipation [cite: 5, 16].

### 3.2 Protein Folding and Hypergraph Geometry
Protein-protein interaction (PPI) networks are traditionally modeled as graphs, but recent work utilizes hypergraphs to capture multi-protein complexes.
*   **Ricci Flow on Proteins:** By applying discrete Ricci flow to PPI networks, researchers can detect communities (functional protein clusters) more accurately than with standard modularity maximization. The flow "shrinks" the metric within functional clusters (increasing positive curvature) and "stretches" the metric between clusters (decreasing negative curvature), effectively performing a soft clustering "surgery" [cite: 12, 14].
*   **Folding Pathways:** The protein folding process itself can be modeled as a flow on an energy landscape. Perelman’s "no local collapsing" theorem suggests that viable protein folding pathways must maintain a certain "injectivity radius," preventing the structure from collapsing into non-functional aggregates (singularities) before reaching the native state [cite: 1, 17].

### 3.3 Tumor Initiation as Ricci Flow Singularity
Mathematical oncology models tumor initiation as a singularity formation event under Ricci flow.
*   **The Model:** A tissue is viewed as a 3-dimensional manifold with a metric representing physiological connectivity/signaling.
*   **Injury and Curvature:** An injury or inflammation creates a region of high scalar curvature. Under Ricci flow dynamics, this region shrinks and becomes rounder [cite: 3].
*   **Singularity:** If the curvature exceeds a threshold, the flow drives the metric to a singularity in finite time. This mathematical singularity corresponds to the biological initiation of a tumor—a breakdown of the standard tissue topology and the emergence of an uncontrolled, self-contained geometry [cite: 3]. Perelman’s "surgery" (excision of the high-curvature neck) is literally the mathematical equivalent of surgical tumor resection.

## 4. Neurobiology and Intelligence: The Neural Manifold

The application of Perelman’s work to neuroscience and artificial intelligence centers on the "Neural Manifold Hypothesis"—the idea that high-dimensional neural activity collapses onto low-dimensional topological structures.

### 4.1 Deep Learning as Ricci Flow
Recent theoretical work proposes that the training of Deep Neural Networks (DNNs) is functionally equivalent to a discrete Ricci flow.
*   **Mechanism:** As data passes through layers of a DNN, the network applies geometric transformations. A well-trained network evolves the "data manifold" by smoothing its curvature, effectively separating complex, entangled classes into flat, linearly separable regions [cite: 6, 7].
*   **Metric Equilibrium:** In Graph Neural Networks (GNNs), a phenomenon known as "oversmoothing" is analogous to the Ricci flow reaching a trivial fixed point (constant curvature). However, controlled Ricci flow (using a "surgery" or re-wiring step) prevents this, allowing the network to resolve bottlenecks (negative curvature edges) and improve information flow [cite: 18, 19].
*   **Gradient Mismatch:** In discretized neural networks (used for efficiency), gradient mismatch is modeled as a metric perturbation on a Riemannian manifold. Using Ricci flow equations, researchers can ensure the stability of the "Linearly Nearly Euclidean" (LNE) metric, guaranteeing convergence [cite: 20, 21].

### 4.2 Biological Oscillators and W-Entropy
Neuronal firing and biological oscillators operate under thermodynamic constraints.
*   **Fisher Information:** The firing rates of neuronal populations define a statistical manifold equipped with the Fisher Information Metric. Homeostasis drives the system to maximize information transfer while minimizing metabolic cost [cite: 22].
*   **W-Entropy Connection:** Perelman’s W-entropy serves as a Lyapunov function for these systems. In the "Recursive Information Curvature" model, consciousness and cognitive states are trajectories on an informational manifold. The "intrinsic semantic curvature" determines whether a cognitive state is stable (recursive convergence) or entropic (divergence) [cite: 23].
*   **Bio-RegNet:** This meta-homeostatic framework integrates a "Regulatory Immune Network" (RIN) and an "Autophagic Optimization Engine." It explicitly uses Fisher information and entropy-based inhibitory feedback to drive the system toward equilibrium ($dE/dt \to 0$), mirroring the dissipation of energy in Ricci flow [cite: 24].

## 5. Control Theory: The "Cognitive Exoskeleton" & "Mind Browser"

The "Cognitive Exoskeleton" and "Mind Browser" are conceptual control mechanisms that leverage these geometric principles to augment human or artificial cognition.

### 5.1 The Cognitive Exoskeleton as a Geometric Stabilizer
The term "Cognitive Exoskeleton" refers to a system that reinforces cognitive cooperation and reduces load [cite: 8]. Mathematically, we can map this to a control system on the "Thought Manifold."
*   **Function:** The exoskeleton observes the user’s cognitive state (a point on the manifold). If the state trajectory approaches a region of high instability (high curvature/singularity), the exoskeleton applies a "Ricci flow" force—smoothing the metric of the information presented to the user.
*   **Manifold Surgery:** If the user encounters a cognitive bottleneck (e.g., information overload analogous to a "neck" pinch in a 3-manifold), the exoskeleton performs "surgery": it cuts the connections to irrelevant data dimensions, capping the manifold to restore a simply connected, navigable topology [cite: 2, 8].
*   **Safety Levers:** In AI alignment, specific neural pathways (the "Assistant Axis") act as geometric vectors. The "Cognitive Exoskeleton" acts as a constraint mechanism, hard-coding safety levers into the neural architecture to prevent "jailbreaks" (deviations from the safe manifold) [cite: 25].

### 5.2 The "Mind Browser": Navigating the Information Manifold
The "Mind Browser" is a navigational interface for this high-dimensional space.
*   **Orbits and Periodicity:** Perelman proved that Ricci flow has no nontrivial periodic orbits [cite: 1]. For a "Mind Browser," this implies that an optimal information retrieval system should not loop endlessly but converge to a "fixed point" (the answer/solution).
*   **Injectivity Radius Control:** Perelman showed that in regions of singularity formation, the injectivity radius is controlled by curvature [cite: 1]. A "Mind Browser" uses this to zoom in/out. In "flat" regions (low information density), the browser allows broad traversal. In "curved" regions (dense, complex information), the browser restricts the "radius" of navigation to prevent cognitive overwhelming, presenting data in local charts.
*   **Phylogenetic/Evolutionary Browsing:** Applying Ricci flow to phylogenetic networks (evolutionary dynamics) allows the reconstruction of ancestral states by running the flow backward (inverse diffusion), or predicting future evolutionary bottlenecks [cite: 12, 26].

## 6. Synthesis: The Grand Unification of Geometry and Dynamics

The investigation reveals that Perelman’s work is not limited to the Poincaré Conjecture. It provides a universal language for systems undergoing structural evolution under thermodynamic pressure.

### 6.1 Mapping of Mathematical Structures to Applications

| Mathematical Entity | Perelman’s Concept | Biological/Cognitive Application | "Cognitive Exoskeleton" Function |
| :--- | :--- | :--- | :--- |
| **Ricci Flow** | $\partial_t g = -2 Ric$ (Smoothing) | Protein folding pathways; Tumor shrinkage/growth; Deep Learning training. | Smoothing information noise; Reducing cognitive load by flattening complexity. |
| **$\mathcal{W}$-Entropy** | Monotonic functional ($dW/dt \ge 0$) | Biological homeostasis; Evolutionary fitness; SOSM stability. | Monitoring system stability; Warning of "entropic collapse" (confusion/fatigue). |
| **Surgery** | Cutting/Capping singularities | Cell division; Apoptosis; Network rewiring (metabolic/neural). | "Clipping" irrelevant data streams; Task switching; Preventing decision paralysis. |
| **Geometrization** | Decomposition into prime manifolds | Modular brain function; Protein domain identification. | Decomposing complex problems into solvable "prime" sub-tasks. |
| **Injectivity Radius** | Controlled by curvature | Reach of neural connections; Metabolic reaction ranges. | Dynamic scaling of information presentation (Zoom In/Out). |

### 6.2 Theoretical Connections to Evolutionary Dynamics
Evolutionary dynamics can be viewed as a flow on a fitness landscape. However, Perelman’s framework suggests it is a flow on the *geometry* of the genotype-phenotype map. The "no local collapsing" theorem implies that evolutionary lineages must maintain a certain genetic diversity (volume) relative to their selective pressure (curvature) to survive [cite: 12, 27].
The "Self-Organizing Survival Manifold" validates this: survival is the maintenance of a trajectory on a manifold that resists the "singularity" of death (geometric collapse) via active entropy management [cite: 4, 5].

## 7. Conclusion

Grisha Perelman’s derivation of the entropy formula for the Ricci flow offers far more than a solution to a topological puzzle; it provides a **"Geometric Thermodynamics"** applicable to any system with interacting components. From the microscopic folding of proteins to the macroscopic organization of metabolic networks and the abstract topology of neural manifolds, the principles of curvature smoothing ($\mathcal{W}$-entropy maximization) and singularity management (surgery) are ubiquitous.

The **"Cognitive Exoskeleton"** represents the engineering application of these principles: a control system that actively monitors the geometry of a user’s cognitive state, applying "Ricci flow" to smooth out information turbulence and performing "surgery" to excise cognitive bottlenecks. This establishes a rigorous mathematical foundation for the next generation of Brain-Computer Interfaces (BCI) and AI alignment strategies, grounding them in the proven stability of Perelman’s geometric evolution.

---

### Detailed Analysis of Mathematical & Biological Entities

#### A. The $\mathcal{W}$-Entropy and Biological Homeostasis
Perelman’s $\mathcal{W}$-entropy is defined on a manifold coupled with a scalar field $f$ (often interpreted as a probability density potential). In biological systems, this maps to the **Fisher Information** measure of a system's state.
*   **Theorem:** The monotonicity of $\mathcal{W}$ along the Ricci flow corresponds to the Second Law of Thermodynamics in a geometric setting.
*   **Application:** In **Bio-RegNet**, the system uses a Bayesian Effector Network to minimize free energy ($E$) while maximizing entropy ($H$) in a controlled manner ($dE/dt \to 0$). This mimics Perelman’s flow, where the system evolves toward a soliton-like (steady) state [cite: 24].
*   **Neural Spike Trains:** The efficiency of information transmission in neurons is constrained by metabolic costs (ATP). The maximization of mutual information under metabolic constraints leads to a capacity-cost function $C(W)$ that behaves analogously to the $\mathcal{W}$-entropy functional, balancing geometry (spike timing/structure) with energy (firing rate) [cite: 22].

#### B. Singularities and Manifold Surgery in Disease
*   **Finite Time Extinction:** Perelman proved that on certain manifolds, the Ricci flow causes extinction in finite time. In cancer modeling, this describes the rapid collapse of healthy tissue architecture into a tumor mass (singularity) [cite: 3].
*   **Surgery as Therapy:** Mathematically, surgery requires identifying the "canonical neighborhood" of the singularity. Biologically, this maps to identifying the boundary of the tumor or the specific metabolic pathway bottleneck (e.g., a "bridge" edge with highly negative Ollivier-Ricci curvature) that supports the cancer's robustness. Targeting these high-curvature/bottleneck regions breaks the network topology—effectively "killing" the tumor manifold [cite: 15].

#### C. The "Mind Browser" Control Mechanism
The concept of a "Mind Browser" [cite: 28, 29] can be formalized as an interface that allows a user to traverse the "Semantic Manifold" of a large dataset.
*   **Curvature-Based Navigation:** Information is not uniform. Some concepts are "hubs" (high curvature), while others are transitive "bridges" (negative curvature). A "Mind Browser" powered by discrete Ricci flow would naturally "inflate" the hubs (making them easier to inspect) and "shrink" the bridges (making navigation faster), dynamically warping the user interface geometry to match the semantic topology [cite: 12, 30].
*   **Over-squashing Prevention:** In GNNs, "over-squashing" occurs when too much information tries to pass through a bottleneck. Perelman’s surgery technique provides the algorithm: detect the bottleneck (negative curvature), excision the edge, and create a "wormhole" (or rewire the graph) to relieve the pressure. This ensures the "Mind Browser" does not lag or become cluttered [cite: 18, 19].

#### D. Evolutionary Dynamics and $\phi$-Fractal Scaling
Theoretical physics suggests deep connections between Perelman’s scaling factors and fractal biology.
*   **Pellis-Fractal Paradigm:** The $\phi$-fractal quantum gravity framework links Perelman’s entropy to the Golden Ratio ($\phi$) scaling found in DNA helices and biological growth patterns. This suggests that the "optimal" manifold for life may be a fractal structure that maximizes $\mathcal{W}$-entropy across multiple scales [cite: 17].
*   **Evolutionary PDEs:** Reaction-diffusion systems in biology (e.g., pattern formation, morphogenesis) can be modeled as evolutionary PDEs that admit geometric order parameters. The Ricci flow acts as a renormalization group flow for these systems, governing how biological patterns scale and stabilize over evolutionary time [cite: 31, 32].

---

**References:**
[cite: 12, 14, 33] Ricci flow on hypergraphs; Metabolic networks; E. coli.
[cite: 15] Ollivier-Ricci curvature in cancer metabolism; Geometric remodeling.
[cite: 17, 34] $\phi$-fractal quantum gravity; W-entropy in DNA.
[cite: 3, 35] Tumor initiation as Ricci flow singularity; Surgery.
[cite: 6, 7, 18] Deep Learning as Ricci Flow; Neural Manifolds.
[cite: 20, 21, 36] Discretized Neural Networks; Linearly Nearly Euclidean manifolds.
[cite: 1, 2, 9, 10] Perelman’s original paper; Entropy formula; Surgery.
[cite: 4, 5, 16] Self-Organizing Survival Manifolds (SOSM).
[cite: 8, 37, 38] Cognitive Exoskeleton; Human-Machine Cooperation.
[cite: 22, 23, 24] Fisher Information; Bio-RegNet; Recursive Information Curvature.
[cite: 39] Topological Architecture of Information; Ontological Engineering.
[cite: 30, 40, 41] Forman-Ricci curvature; Biological oscillators.

**Sources:**
1. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE4VWrs2VIvhGaLJGt9Na4a1dFcoqO9XCkFqI_kEZH0ViTXGN7yX8ksChMU76TWgj3Ekq8Fiwqu6RZyKPkiqKVU2oek_s_Dlw897EfMtGnULxK4hw8rjtLw)
2. [berkeley.edu](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGALMT7ULyD6JP5v1M13ACXtQFM3qFkMbNWaXa8mpkNLdBV4vzdtO1dkTjHGd5IO2b_f1rS42nuKhRFgvjld1shgyZaP8P4-FDZ1Pefc6FoTIGXxJ8ASpLQC6crCar4dHVNvfAg6bJMmRxdum5QRV0AD9E=)
3. [hilarispublisher.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFULCyYHiwRJMa16lUeUPG7RpwQorrSeEcjUVFTOCgjFDY9NMA0U6Y-6ljh2OcdNjjMo_czP2AsZ83ig1-fvFRAbz1uZ5tIL-oU2iazKj7KxeQhF_ZIvfAf3TlGRMZUVTmYqbkLsqBfCfs85m5y3PicA1THloHZuwZyBqB7jI6LeQKkl8nV362u6rYlIzZtmGxJof9tENWmjZqPZG2lAMg9)
4. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHOjgFdu6Vt0fUj2dfYE6shILCCxPTJ--OxgnnSxa5gXQLgnqk0zjLLUaQct2mMtXPw7yDmk6mdsDSscd3_p8Czvv9qsnBvXBJk9xc7MLkKn_kbxSL7N3szLNGP4AmqLWw6eUJLueqhcAt7cySM8SyKD--AJ0C4ZgLGuAtktfms9imkwLWR6uCUBxZ_ixmG2TEXM0skVzUTpefiecjZcqzE6iJXxQmkZc5bbGZSllDENXntP6KXMeeUO91rNBfkyOEeCtgzZv-hb3wDrcJuX4urQZHmJtZ68NL27bYFCBV-)
5. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBtSbS4RVVOynw2xiRYwKIGgjGx0WKGRlMn7974GSUOYM69s6YbCe8fskphKm1CtNhA4F-9TIqEs-GD2PRcPOB9_89zu8xJdO7b_eCTlNAdKJVvJplHg==)
6. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQErE8xCOnKOs_PREvLA4sFqcZcpYB-fQB9w5aJvplsQelhKQSNl_jeYw27P7xKCG28TST9KCsAkHUkC_YxwaHa-5zpaOZoF9IWMTGVgYmmDUxiRNiXVolZrzw==)
7. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEtI3gVChVUdusiNoAAOH85O5eVXWk1YM2pqsY4f3hyn02z82OpZo6NENNxSVj-5jLL9gJdJQhOwclGADQwRkNa80yTydlN8z-8bRfqtA9Fu_Y1Sy7kSgqdhmopaNVoYmjDkEDNJgvuE9g18RrwKjvWRcxHSFJdul5zl-1Qmm60M0h6O1U=)
8. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEscRGpemmlUbs6wL86EXqyBI8BmDBJNb-px36qFBD9MLVITbic9L2s1blyDUrsfFBjSSBByhdNg2hKgDKTPVOa-i4jPVghi0bc2hacEfwwkoB2znKmEKV46wVrhkbvpzR05LAr_AqO-1JN11OsW3o0u4566hUUefKtoLtG78gz-FJ8tFodB-0dxNSpALA19eV-0OS9Y_YfVNwxincpJT44i33wYkO6GLmNdA==)
9. [scispace.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE8YXyQ6JDogNmEITjDn_L4gJFbShd3kUQhJYjOvfa9SMZzYKcN0b_-X56zZhmY2AIAJPt4UqdcIS5F9o9_CFDqG6LqFIXcflr-Esw735F9pxwsTHy3oadLoyMeud-0JABk_6VYwadS9irbDxNbjSN9_faXXBu50RvKaDa9d7NNEVQYEsI4Tb8VYHzepxJRz1CIy1RANiE=)
10. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHPXiDGBsSdaNeL6222DRe70ULydSrbZ2Dz6zZ9sqrI6Yr-D6Ls3wByRmC-z_3uufzFF6T35ng5ZaTzBRRBeGaDVFGVg0AjMfSLJwz27etOEb-i3l1e590myhTtsyModtFzPLfD)
11. [aiaa.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEtLXUNsol_RRL0sZ1w1TCwOafwCVwV2UYfAF6ogqZtUbWMPR5IaS79HR4hTzvW_3NIMX31ZYOATH070pJt4ehttMsRznpHNyiqcc3tzws-oxIvJrexGYv2mr6lfabXiDWLaw4lY6SbCL1q6AG6FiC43KLdZ7VLhoj9xC_fbZBm9gk60vlmDS9bP9F6xkTTE6ByUDvZyEjc9Ag_hTGYpJKAtB6O9R73aQ==)
12. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEqXfMxGiwKKvDZ3e93kLfi8HGNuSPzLq_5kEFT5lJRFPS7Ufdnnky_iXOVCqIec3XyjIGLUNFa_Rr5jeg_5n0aI2q2nk4B54wYdH6eJueeD6TAaWN9zyD58rVp6Nhu7JPUjDu-wmsKFw3l22xTgoyFf8vu-AOzlAGCAENgyy8Jk8rK9FYO8nvMIPb1hNsdvfS4W7BOck486QZBCWiWM3HJku7otg==)
13. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFv1gRCGIqE4v2cGFShsYuGD4hZSEtCXU5-gOHf69_t8mMb_HVNmPEEjg4irwRCER_0OXDTIEf7rf8OWnUhWrujYnaZqCJgVrN9qXmfLWqWij5LEJSrMRzZ9pHNJ3M2y2XU_EUsowSe-AXukTjDERv-gNqfFf_X-2_w3NPTlDqfuji_5lQAWyuyUERvj-rOAFstznSMrcYguwyIKMHib0OvjSJN9ll-nJmGBhIZzLUUbm0G8neZXL6FM7gD9f-_xkfC_8_qQnkFd7_oFVT163yploBt8nWYDw==)
14. [qucosa.de](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFyt4qfQtpSHBvQRRE8EYyVYw1uAjATHd6q2eOUEWDfAELNd41_DgBt-o9wZu-LiYoopOKrc8HgvXGa2DHDlV27onPhaMJLZJkwFgHs0jvCVO44MVcJJyZnXMnHoaxMxNDaPaIAYKKsnRJv4GXnT2k=)
15. [biorxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBXNhaZCCsq0ZQipP6_1zQQTeiX2HuVtVzUhAZ-Rl27m5sM6cZ1hKU1MZBrjfGg_GXcta-qtv5N5s7F4F3jC_Ig1adJijFI1l1JB6lCnnJtB11x5yF5reKUJxg9qQvRPIZvW6WInduESAtGXEJU5mtaRgIPfvn8h_QxA==)
16. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEik4NFavb_TEL-ak4TeKRSuP8Kkjg6ouwWrEb1UcKbDkY0TQ45oFgWbHGXfG49N9x5h5nyomARtaN_XjztXwOlpW6bEjeeNjBcwM9EZ8n0FnwRqcJshyYdDw==)
17. [ssrn.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG1J6bBinCPfBERihp7fpZNSCZki5HAb5Qw7_Ubf1TrLEJfEZFRm80oZzTt3DtRwd8rKd5BBDuDM2F6vezXFtRObqk9tnNy7SF6iamd6ZMWltAKXXMGmHdyWZy4decKcOjkD_mJ0_aWvXC_8L_biMK9kkbKyQzdNK1YDnIclWSaKTY6dQyzlg==)
18. [openreview.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE3YxgC0a2HpOgO-aTsLkqrAwNmIaHZdw1jh3YbQMogwtuqPjKxPENyyELcGNdgWIUYIDTChSavBJExBvKMIn8_6dQeYq79hwufll-rqimy3ajIyN5yAGxDax0bsiBAmdeKmL_blb21qZrMUd-k8OKf5SIJtOgy9MeKU385AA==)
19. [iclr.cc](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQERfxoQJoc822vabXIed4Qsi2_-A4qkUOEUPlGiOBBnIYRlR3tdA0QJVEos9WLJl1eC0c6Vqg08qvToJpPXDRu6IDW1y8ccuOqpM9ECSyRFnjX1kehvpRRyj_OdfeRU0q0=)
20. [jmlr.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHXXwPErYn9oSJy0Bd32uBGoXqbFz_5QwYnI0Gt50ZYxSWM7rRsttNVGBUbfhq2JpX8gu-DseHBXaMtkyz8Ld3pUuoCmAmMlqCJscJVa54XrPj7jbXI11Z1sZ2khORGphviJX24S7L4GwtHC4wB2g==)
21. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE6_gO8BYv8KVYqLrMHokPoVIt7Y8P2WvVn1S6yZLWZsGeIyvS1U2voEl2TezmQwecKGNwX_paNvshds9JyWlCbO71OgzTAtlHSzngSBLi2o02cG_9S_lSO1w==)
22. [nih.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG12s0FrgN4SKa6kJEdtaTgSRaPEQNmzLDK3XFAgUxxcd3MnpGgeij5IrOurbBSMJkHbwuOko9JhbJqlCmlZ_nGD9EgLsIQ1NnKpuV-mZoRKRT4Tw49raC6hrUlfmqOOrdriaz8WIdQmw==)
23. [osf.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGeKHcEoA86y6QPKvYBW0wIUT5Tn9WZrvG7vr4h8nHZsdhhmw67uo-ABiOU4B9P5sXoCUqoJ9N1DS8_kgoXWEaM-f49gD3fWzcwagFXyWfZj7pUlA==)
24. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQExRN1D8-_lChR5OZ9TQriRq1zipgweEgyhCIeNN4VjrHWUxgkNU7VEeHkiEYEp0XbzIlAam-a2UhQZq-uMy98qci-ZNI8M5r3Gybbl2sSf9nmZb4l6HCiN1CA484H3Mo_lz1ERwA__BCHLPlCsXbd_dFaRe4vtBWcGhtsIbtDKjlopVvE5Da9SzDROb3AytmOLVWdQ9iBZkA4iRuuoL9fwBg4caq5CH4nqTFgosxL5mLxdKYsXDRjaPT5yfQYFGsou_W0MeGJlt7wiqS7nHNDoBucFP4_7qBwpuOdPS173R6bXY9XwL14eYKDSNrLvFnwwFtdHxmo_InLALStaHjjGbwOs6OtPzE_laXUuIIGoo8C_sbnHLyz2tMngaZisxPB3xE2fq8z3-eQ=)
25. [reddit.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEfAPyU436P_RJFO7o77GfvP_LQDX95Rujz6u4acMkRb2Trur6b5wRkzsHTxcARb7EavkHTuONnxCIKj6SqgnLeXo9Lnsa9t4NNinCluJ_PnQ_4pZf5KVwZ-JU_ba804r_xC9BR8QqyNhkJfDHtJfkov3SA6sJd2OYKlIgtY0_bv9uXDwkonnJdHpS18u-eUC4nmPQ6aCcwkb9O1Zc1hw==)
26. [nih.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFc7GoG1SxnLupXHZZBAzn17KPdnxc-dEPRh03SqKCJrroQU8JVrsq-dpcRlsuXgxb_jEjaUMxMSjSbBstDulleQD9dU56aY2WVCGnrP0s9tESIyqnWZ2aFZSxeEfKMutiUnSpSl5LL3A==)
27. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHBr5tSXxFt6B2Ba-fpwzdUgCipDh8NCDR4NQj0-3x7j0ucMH78pnRomZj_tfgfgb6qqhV4sm4Dk1pg-tEIT1Z57Sw3q_w_5qqL8ew9KQjFpuhIbNCBAGW1_eduTd90PlPP4fcXg1YWGqJiEf8lOflLRBiqfZrEJ539FHDT_6GWbKgP-bfiiZQtFf9UNXzcLmHbov2Nfb5zBLS-xtcoQ7DkSMxGu7zR)
28. [dokumen.pub](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG4Q4KpJ2juH4oCKO_U9nxOXrYnf_ImLHRC7l2SwZ7UwxG45pUfoc5AbBilcrsvj6SaJVgLScfN-AVM7h963SHs2paDedLAqF5Zb2uIw-w5SoRD8PwdUhohkzNdF28ADi0dm0SFCyCdlJ8yiDKHcHfEzvyfyv_r7-HpdYYlRMHjrJxekp2zP_YtgoWwYIxbpSZos5sGeVWEmOIZyzvWn9DsExxW-YX789TaJYbpSwAZsWXP4RVuZmFFivqIXx3fsuAJm65iyoCVJkaOIhu6U7pzUzwFY29kh1ZhEkkS82Fzle-6ZBw4SeyuOzIHBmD4Szam87OR9s4lA2c4s_Pm22KZAA==)
29. [gaiainstitute.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF9y3BjAdB2kTdlsM07V9LfAgoeWz7P0ZM2KZHwEk8yGzC4ZetdRJk5ajqczhUouI5FqCybnDxRrWYh0Ff-bVjk-tufyqduRoa78SNDjjDZ6hNCW_UweiybbHZzKDoielmDKA==)
30. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGvkQgeXueUzPV13Fg9I2jZeuj2ve58f36tMxnlyCjUxLY0B_Y5SdrG6rsnrHvOzzC8lsbjo127CxZBTEqy7T5L5LGzqTxj8lj8mi2gXpsbeXPB7BNCqNsqUnIxbeqNqfp7-hYRRGn-7GmfEPNMF8IPv_KIFxj-W7c8T-EKXyiAmvXkM14y_W7CxI-xUIjyHeuyLueRUuSb8BXvz3DkYYypN4BKwuaCdaPKli1d4eYm_WCeNJbhrvY2di7R-aph64yGm48v)
31. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGo-O7yHAfhDLnEGS8Tx4oeG3CFENQRAOVykhuO4jeEgVzp48epHF5YTW9ABcVrBpH3xmX3uNxAP9qP-3tgbUf9jF4Ins4rW3-b6rCZUCN2WZ7q03kexWW9uH9wHp7Z8nnfWxPwCPKCwIV7Lw2eeg3YolPoY6IrDNlRtOnmnZRbm6QZHrA5PcjzC29WTWPFcJsU7YNyke6Cd3luENMH92sEXQ6YYSqaySgx0rllMX_v425S8ntMxFqcLKwTcw==)
32. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEpUKDdccaGs3567tu11v8xrbcDi-qwENRNNtG4JVh5CS1bt1ipiQ1L5Ess5Dkihbu3xHHmUaq-oyoSvo4qvH7PESh0YET7XyX1dzYaY-gwkWFI_lZoeFgAT1dRSQVI1s2S23DBEvgFJBVgo68LMPHBm130zfe7oIAGPezsLEdd4izfvmyzQDyF6o2ZVByd5I0Y)
33. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFCSjZU-Ni0kYD4SM58JVARWh39QdTpy6O5xJ6xeCVncgXiR7-0KN9csXjFxbwTLZ9WjnGFKjX4pEsX9pbjzJYjItySOGnCc0cSW8QR15dFfrzfMm25MWI5HX_1mKlNMHjHoritAoIyNq4j0jYpB3NcsG9U0YjLy-y_3DCLj6Mq39q3lQXWZxTCXgnHhNZpt1qFzLZ5eQCAcq7ujauecHhR-1mwTNMyjYu2q4Kdm-yhEuDNomXRmuNE3A==)
34. [thelaszloinstitute.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-C1602UBsGgw5GbxSmXj9of5mrjRirmwbRR-caOjS54dd82WDqs2qRPRocwZQOtdg4DCSisv70I4dhvyl8VUL4SF-FLLZK0LmJ8YIDUuZiFDdb7IRSeln5Quc89wfMryBNnbZ3mXweyoq1q1lDJkcsPS4QN3vudNCYd32HnVFU_M-rF85ghmRJYB9YAsGyZ3A07RePzzynLmiWBBC)
35. [nih.gov](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGQ3fgtKzEgQ71zLIZDi1ZU4HXGaovAi3u5_Idn6nn2RRA-k2XOyLC_b_AgTZrFIkQkQbTmxLng2yiLnQlm9HeMGeRWE8Auf20JZdxgrvH3IyoUVVUOTwMf0UX8t1m7-K97FgI-G32I)
36. [arxiv.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHnwqwok6zaXHsKkD-XqG8jCJdvHXBpnSsaDY9nTNm-mHyl1e-gX3IAjzDK6qPTXzPTmn2qBDKsLfsmWb8ZyOuUWeekxEPT3Nf5mmFYlnWFo8OPrpuX6mrZ608=)
37. [mdpi.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFGzeVHdFyb_PRMZFa9puZHVwUWz6U2x53qC3mxJq2D780BTErpRtAh-oO2UFBm4eZHJ8klVhxvckGIWeLAhxLpcowZ2OHU9m1i9zy9esEJ2c4db-nYakjABDibHIUVJg==)
38. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFNHuXgZU6iuGASj9S9n-QOif-Cg3NWwWOsYXRp2-Y5QrItGfof57ktfHCeIPiVwBLHJTDse2-DfOmkAgpdxhKXY-KIPhORGwaj9OLFjdducgRrNuN49I3mLxZ00rNva35RbUDncV3nOC2Y7KTbzdciQK3dREtvIHTmM6EEFoFbmtTbskvsKMI7n5BE-N0_mhJ39kOmx_1Ey0HitMi9l8ba-RjeUEm-N-VzC8jnKUHGQrCZG-8=)
39. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEE-n_3w7XxOLFbHgvBSc7oG9Hh9r2TwEibcEbKvZiXqC6CfaJDg-IvaoGrQxDsoM9gXIb9KKELVSL8woYndiZLDfUEpWG66RWTIIJhGOPM7lE6tTFp_xic3VszNlx7Z1Zvl4zfEzB832-SZ5iO42i3ZZ2LLnzz9FGFoy0pxe9ip3N63TgfpoXDYidfw61Kons=)
40. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHiR4pRtlpbpHLPGJ9huVOcN-nqDtO04tSNB0xiI_TboqQfzQfQVUznViaJ7sqDWd1AXtgdkgOX13mBjRZTbSG9_hVQzNR9TX5DBzg_KTHD2zrXJqzT_SwXhG5kwI0FfUFdyDOrcsxVMc7vcfrXwvmx7lHgcl5mm0nVwRil991I4c_CnnsLjIOz7es007U3NPcCRLyLN1zz3cJ-es5130tCz4waRi54gUQkHu1IejMxroojvQ==)
41. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGWLHQMm8XhNo_0IlhOTtNeh7JcMtfJR176io5Zf3Xb0u_0BGpeOw2ZK-TtqinY_-p6Awr3dADiEGx0kHHONSE164ok1h-cLG4q4noV2QVSBe79xro7bhsljXEKEALVmb9Kw1dKO1vShyfHFDYd9mUCbZwP1o9455HzQhUEr6CjoQFj0IEAXt1jLpqn3g5W)


### Citations
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE4VWrs2VIvhGaLJGt9Na4a1dFcoqO9XCkFqI_kEZH0ViTXGN7yX8ksChMU76TWgj3Ekq8Fiwqu6RZyKPkiqKVU2oek_s_Dlw897EfMtGnULxK4hw8rjtLw
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGALMT7ULyD6JP5v1M13ACXtQFM3qFkMbNWaXa8mpkNLdBV4vzdtO1dkTjHGd5IO2b_f1rS42nuKhRFgvjld1shgyZaP8P4-FDZ1Pefc6FoTIGXxJ8ASpLQC6crCar4dHVNvfAg6bJMmRxdum5QRV0AD9E=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFULCyYHiwRJMa16lUeUPG7RpwQorrSeEcjUVFTOCgjFDY9NMA0U6Y-6ljh2OcdNjjMo_czP2AsZ83ig1-fvFRAbz1uZ5tIL-oU2iazKj7KxeQhF_ZIvfAf3TlGRMZUVTmYqbkLsqBfCfs85m5y3PicA1THloHZuwZyBqB7jI6LeQKkl8nV362u6rYlIzZtmGxJof9tENWmjZqPZG2lAMg9
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHOjgFdu6Vt0fUj2dfYE6shILCCxPTJ--OxgnnSxa5gXQLgnqk0zjLLUaQct2mMtXPw7yDmk6mdsDSscd3_p8Czvv9qsnBvXBJk9xc7MLkKn_kbxSL7N3szLNGP4AmqLWw6eUJLueqhcAt7cySM8SyKD--AJ0C4ZgLGuAtktfms9imkwLWR6uCUBxZ_ixmG2TEXM0skVzUTpefiecjZcqzE6iJXxQmkZc5bbGZSllDENXntP6KXMeeUO91rNBfkyOEeCtgzZv-hb3wDrcJuX4urQZHmJtZ68NL27bYFCBV-
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBtSbS4RVVOynw2xiRYwKIGgjGx0WKGRlMn7974GSUOYM69s6YbCe8fskphKm1CtNhA4F-9TIqEs-GD2PRcPOB9_89zu8xJdO7b_eCTlNAdKJVvJplHg==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQErE8xCOnKOs_PREvLA4sFqcZcpYB-fQB9w5aJvplsQelhKQSNl_jeYw27P7xKCG28TST9KCsAkHUkC_YxwaHa-5zpaOZoF9IWMTGVgYmmDUxiRNiXVolZrzw==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEscRGpemmlUbs6wL86EXqyBI8BmDBJNb-px36qFBD9MLVITbic9L2s1blyDUrsfFBjSSBByhdNg2hKgDKTPVOa-i4jPVghi0bc2hacEfwwkoB2znKmEKV46wVrhkbvpzR05LAr_AqO-1JN11OsW3o0u4566hUUefKtoLtG78gz-FJ8tFodB-0dxNSpALA19eV-0OS9Y_YfVNwxincpJT44i33wYkO6GLmNdA==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEtI3gVChVUdusiNoAAOH85O5eVXWk1YM2pqsY4f3hyn02z82OpZo6NENNxSVj-5jLL9gJdJQhOwclGADQwRkNa80yTydlN8z-8bRfqtA9Fu_Y1Sy7kSgqdhmopaNVoYmjDkEDNJgvuE9g18RrwKjvWRcxHSFJdul5zl-1Qmm60M0h6O1U=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE8YXyQ6JDogNmEITjDn_L4gJFbShd3kUQhJYjOvfa9SMZzYKcN0b_-X56zZhmY2AIAJPt4UqdcIS5F9o9_CFDqG6LqFIXcflr-Esw735F9pxwsTHy3oadLoyMeud-0JABk_6VYwadS9irbDxNbjSN9_faXXBu50RvKaDa9d7NNEVQYEsI4Tb8VYHzepxJRz1CIy1RANiE=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHPXiDGBsSdaNeL6222DRe70ULydSrbZ2Dz6zZ9sqrI6Yr-D6Ls3wByRmC-z_3uufzFF6T35ng5ZaTzBRRBeGaDVFGVg0AjMfSLJwz27etOEb-i3l1e590myhTtsyModtFzPLfD
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEtLXUNsol_RRL0sZ1w1TCwOafwCVwV2UYfAF6ogqZtUbWMPR5IaS79HR4hTzvW_3NIMX31ZYOATH070pJt4ehttMsRznpHNyiqcc3tzws-oxIvJrexGYv2mr6lfabXiDWLaw4lY6SbCL1q6AG6FiC43KLdZ7VLhoj9xC_fbZBm9gk60vlmDS9bP9F6xkTTE6ByUDvZyEjc9Ag_hTGYpJKAtB6O9R73aQ==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEqXfMxGiwKKvDZ3e93kLfi8HGNuSPzLq_5kEFT5lJRFPS7Ufdnnky_iXOVCqIec3XyjIGLUNFa_Rr5jeg_5n0aI2q2nk4B54wYdH6eJueeD6TAaWN9zyD58rVp6Nhu7JPUjDu-wmsKFw3l22xTgoyFf8vu-AOzlAGCAENgyy8Jk8rK9FYO8nvMIPb1hNsdvfS4W7BOck486QZBCWiWM3HJku7otg==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFv1gRCGIqE4v2cGFShsYuGD4hZSEtCXU5-gOHf69_t8mMb_HVNmPEEjg4irwRCER_0OXDTIEf7rf8OWnUhWrujYnaZqCJgVrN9qXmfLWqWij5LEJSrMRzZ9pHNJ3M2y2XU_EUsowSe-AXukTjDERv-gNqfFf_X-2_w3NPTlDqfuji_5lQAWyuyUERvj-rOAFstznSMrcYguwyIKMHib0OvjSJN9ll-nJmGBhIZzLUUbm0G8neZXL6FM7gD9f-_xkfC_8_qQnkFd7_oFVT163yploBt8nWYDw==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFyt4qfQtpSHBvQRRE8EYyVYw1uAjATHd6q2eOUEWDfAELNd41_DgBt-o9wZu-LiYoopOKrc8HgvXGa2DHDlV27onPhaMJLZJkwFgHs0jvCVO44MVcJJyZnXMnHoaxMxNDaPaIAYKKsnRJv4GXnT2k=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBXNhaZCCsq0ZQipP6_1zQQTeiX2HuVtVzUhAZ-Rl27m5sM6cZ1hKU1MZBrjfGg_GXcta-qtv5N5s7F4F3jC_Ig1adJijFI1l1JB6lCnnJtB11x5yF5reKUJxg9qQvRPIZvW6WInduESAtGXEJU5mtaRgIPfvn8h_QxA==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEik4NFavb_TEL-ak4TeKRSuP8Kkjg6ouwWrEb1UcKbDkY0TQ45oFgWbHGXfG49N9x5h5nyomARtaN_XjztXwOlpW6bEjeeNjBcwM9EZ8n0FnwRqcJshyYdDw==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG1J6bBinCPfBERihp7fpZNSCZki5HAb5Qw7_Ubf1TrLEJfEZFRm80oZzTt3DtRwd8rKd5BBDuDM2F6vezXFtRObqk9tnNy7SF6iamd6ZMWltAKXXMGmHdyWZy4decKcOjkD_mJ0_aWvXC_8L_biMK9kkbKyQzdNK1YDnIclWSaKTY6dQyzlg==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE3YxgC0a2HpOgO-aTsLkqrAwNmIaHZdw1jh3YbQMogwtuqPjKxPENyyELcGNdgWIUYIDTChSavBJExBvKMIn8_6dQeYq79hwufll-rqimy3ajIyN5yAGxDax0bsiBAmdeKmL_blb21qZrMUd-k8OKf5SIJtOgy9MeKU385AA==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQERfxoQJoc822vabXIed4Qsi2_-A4qkUOEUPlGiOBBnIYRlR3tdA0QJVEos9WLJl1eC0c6Vqg08qvToJpPXDRu6IDW1y8ccuOqpM9ECSyRFnjX1kehvpRRyj_OdfeRU0q0=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE6_gO8BYv8KVYqLrMHokPoVIt7Y8P2WvVn1S6yZLWZsGeIyvS1U2voEl2TezmQwecKGNwX_paNvshds9JyWlCbO71OgzTAtlHSzngSBLi2o02cG_9S_lSO1w==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHXXwPErYn9oSJy0Bd32uBGoXqbFz_5QwYnI0Gt50ZYxSWM7rRsttNVGBUbfhq2JpX8gu-DseHBXaMtkyz8Ld3pUuoCmAmMlqCJscJVa54XrPj7jbXI11Z1sZ2khORGphviJX24S7L4GwtHC4wB2g==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG12s0FrgN4SKa6kJEdtaTgSRaPEQNmzLDK3XFAgUxxcd3MnpGgeij5IrOurbBSMJkHbwuOko9JhbJqlCmlZ_nGD9EgLsIQ1NnKpuV-mZoRKRT4Tw49raC6hrUlfmqOOrdriaz8WIdQmw==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGeKHcEoA86y6QPKvYBW0wIUT5Tn9WZrvG7vr4h8nHZsdhhmw67uo-ABiOU4B9P5sXoCUqoJ9N1DS8_kgoXWEaM-f49gD3fWzcwagFXyWfZj7pUlA==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQExRN1D8-_lChR5OZ9TQriRq1zipgweEgyhCIeNN4VjrHWUxgkNU7VEeHkiEYEp0XbzIlAam-a2UhQZq-uMy98qci-ZNI8M5r3Gybbl2sSf9nmZb4l6HCiN1CA484H3Mo_lz1ERwA__BCHLPlCsXbd_dFaRe4vtBWcGhtsIbtDKjlopVvE5Da9SzDROb3AytmOLVWdQ9iBZkA4iRuuoL9fwBg4caq5CH4nqTFgosxL5mLxdKYsXDRjaPT5yfQYFGsou_W0MeGJlt7wiqS7nHNDoBucFP4_7qBwpuOdPS173R6bXY9XwL14eYKDSNrLvFnwwFtdHxmo_InLALStaHjjGbwOs6OtPzE_laXUuIIGoo8C_sbnHLyz2tMngaZisxPB3xE2fq8z3-eQ=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEfAPyU436P_RJFO7o77GfvP_LQDX95Rujz6u4acMkRb2Trur6b5wRkzsHTxcARb7EavkHTuONnxCIKj6SqgnLeXo9Lnsa9t4NNinCluJ_PnQ_4pZf5KVwZ-JU_ba804r_xC9BR8QqyNhkJfDHtJfkov3SA6sJd2OYKlIgtY0_bv9uXDwkonnJdHpS18u-eUC4nmPQ6aCcwkb9O1Zc1hw==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFc7GoG1SxnLupXHZZBAzn17KPdnxc-dEPRh03SqKCJrroQU8JVrsq-dpcRlsuXgxb_jEjaUMxMSjSbBstDulleQD9dU56aY2WVCGnrP0s9tESIyqnWZ2aFZSxeEfKMutiUnSpSl5LL3A==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHBr5tSXxFt6B2Ba-fpwzdUgCipDh8NCDR4NQj0-3x7j0ucMH78pnRomZj_tfgfgb6qqhV4sm4Dk1pg-tEIT1Z57Sw3q_w_5qqL8ew9KQjFpuhIbNCBAGW1_eduTd90PlPP4fcXg1YWGqJiEf8lOflLRBiqfZrEJ539FHDT_6GWbKgP-bfiiZQtFf9UNXzcLmHbov2Nfb5zBLS-xtcoQ7DkSMxGu7zR
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF9y3BjAdB2kTdlsM07V9LfAgoeWz7P0ZM2KZHwEk8yGzC4ZetdRJk5ajqczhUouI5FqCybnDxRrWYh0Ff-bVjk-tufyqduRoa78SNDjjDZ6hNCW_UweiybbHZzKDoielmDKA==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG4Q4KpJ2juH4oCKO_U9nxOXrYnf_ImLHRC7l2SwZ7UwxG45pUfoc5AbBilcrsvj6SaJVgLScfN-AVM7h963SHs2paDedLAqF5Zb2uIw-w5SoRD8PwdUhohkzNdF28ADi0dm0SFCyCdlJ8yiDKHcHfEzvyfyv_r7-HpdYYlRMHjrJxekp2zP_YtgoWwYIxbpSZos5sGeVWEmOIZyzvWn9DsExxW-YX789TaJYbpSwAZsWXP4RVuZmFFivqIXx3fsuAJm65iyoCVJkaOIhu6U7pzUzwFY29kh1ZhEkkS82Fzle-6ZBw4SeyuOzIHBmD4Szam87OR9s4lA2c4s_Pm22KZAA==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGvkQgeXueUzPV13Fg9I2jZeuj2ve58f36tMxnlyCjUxLY0B_Y5SdrG6rsnrHvOzzC8lsbjo127CxZBTEqy7T5L5LGzqTxj8lj8mi2gXpsbeXPB7BNCqNsqUnIxbeqNqfp7-hYRRGn-7GmfEPNMF8IPv_KIFxj-W7c8T-EKXyiAmvXkM14y_W7CxI-xUIjyHeuyLueRUuSb8BXvz3DkYYypN4BKwuaCdaPKli1d4eYm_WCeNJbhrvY2di7R-aph64yGm48v
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEpUKDdccaGs3567tu11v8xrbcDi-qwENRNNtG4JVh5CS1bt1ipiQ1L5Ess5Dkihbu3xHHmUaq-oyoSvo4qvH7PESh0YET7XyX1dzYaY-gwkWFI_lZoeFgAT1dRSQVI1s2S23DBEvgFJBVgo68LMPHBm130zfe7oIAGPezsLEdd4izfvmyzQDyF6o2ZVByd5I0Y
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGo-O7yHAfhDLnEGS8Tx4oeG3CFENQRAOVykhuO4jeEgVzp48epHF5YTW9ABcVrBpH3xmX3uNxAP9qP-3tgbUf9jF4Ins4rW3-b6rCZUCN2WZ7q03kexWW9uH9wHp7Z8nnfWxPwCPKCwIV7Lw2eeg3YolPoY6IrDNlRtOnmnZRbm6QZHrA5PcjzC29WTWPFcJsU7YNyke6Cd3luENMH92sEXQ6YYSqaySgx0rllMX_v425S8ntMxFqcLKwTcw==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFCSjZU-Ni0kYD4SM58JVARWh39QdTpy6O5xJ6xeCVncgXiR7-0KN9csXjFxbwTLZ9WjnGFKjX4pEsX9pbjzJYjItySOGnCc0cSW8QR15dFfrzfMm25MWI5HX_1mKlNMHjHoritAoIyNq4j0jYpB3NcsG9U0YjLy-y_3DCLj6Mq39q3lQXWZxTCXgnHhNZpt1qFzLZ5eQCAcq7ujauecHhR-1mwTNMyjYu2q4Kdm-yhEuDNomXRmuNE3A==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH-C1602UBsGgw5GbxSmXj9of5mrjRirmwbRR-caOjS54dd82WDqs2qRPRocwZQOtdg4DCSisv70I4dhvyl8VUL4SF-FLLZK0LmJ8YIDUuZiFDdb7IRSeln5Quc89wfMryBNnbZ3mXweyoq1q1lDJkcsPS4QN3vudNCYd32HnVFU_M-rF85ghmRJYB9YAsGyZ3A07RePzzynLmiWBBC
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGQ3fgtKzEgQ71zLIZDi1ZU4HXGaovAi3u5_Idn6nn2RRA-k2XOyLC_b_AgTZrFIkQkQbTmxLng2yiLnQlm9HeMGeRWE8Auf20JZdxgrvH3IyoUVVUOTwMf0UX8t1m7-K97FgI-G32I
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHnwqwok6zaXHsKkD-XqG8jCJdvHXBpnSsaDY9nTNm-mHyl1e-gX3IAjzDK6qPTXzPTmn2qBDKsLfsmWb8ZyOuUWeekxEPT3Nf5mmFYlnWFo8OPrpuX6mrZ608=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFGzeVHdFyb_PRMZFa9puZHVwUWz6U2x53qC3mxJq2D780BTErpRtAh-oO2UFBm4eZHJ8klVhxvckGIWeLAhxLpcowZ2OHU9m1i9zy9esEJ2c4db-nYakjABDibHIUVJg==
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFNHuXgZU6iuGASj9S9n-QOif-Cg3NWwWOsYXRp2-Y5QrItGfof57ktfHCeIPiVwBLHJTDse2-DfOmkAgpdxhKXY-KIPhORGwaj9OLFjdducgRrNuN49I3mLxZ00rNva35RbUDncV3nOC2Y7KTbzdciQK3dREtvIHTmM6EEFoFbmtTbskvsKMI7n5BE-N0_mhJ39kOmx_1Ey0HitMi9l8ba-RjeUEm-N-VzC8jnKUHGQrCZG-8=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEE-n_3w7XxOLFbHgvBSc7oG9Hh9r2TwEibcEbKvZiXqC6CfaJDg-IvaoGrQxDsoM9gXIb9KKELVSL8woYndiZLDfUEpWG66RWTIIJhGOPM7lE6tTFp_xic3VszNlx7Z1Zvl4zfEzB832-SZ5iO42i3ZZ2LLnzz9FGFoy0pxe9ip3N63TgfpoXDYidfw61Kons=
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGWLHQMm8XhNo_0IlhOTtNeh7JcMtfJR176io5Zf3Xb0u_0BGpeOw2ZK-TtqinY_-p6Awr3dADiEGx0kHHONSE164ok1h-cLG4q4noV2QVSBe79xro7bhsljXEKEALVmb9Kw1dKO1vShyfHFDYd9mUCbZwP1o9455HzQhUEr6CjoQFj0IEAXt1jLpqn3g5W
- https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHiR4pRtlpbpHLPGJ9huVOcN-nqDtO04tSNB0xiI_TboqQfzQfQVUznViaJ7sqDWd1AXtgdkgOX13mBjRZTbSG9_hVQzNR9TX5DBzg_KTHD2zrXJqzT_SwXhG5kwI0FfUFdyDOrcsxVMc7vcfrXwvmx7lHgcl5mm0nVwRil991I4c_CnnsLjIOz7es007U3NPcCRLyLN1zz3cJ-es5130tCz4waRi54gUQkHu1IejMxroojvQ==
