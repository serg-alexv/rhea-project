# Mathematics of Rhea — Paper Outline
> Target: OpenAI Prism (scientific paper generation)

## Title
**"Mathematics of Rhea: A Formal Framework for Reconstructing Daily Defaults from Biological Rhythms and Cultural Universals"**

## Abstract (sketch)
We present a mathematical framework for generating personalized daily structure models ("Mind Blueprints") grounded in circadian/ultradian/infradian biology, polyvagal regulation theory, and cross-cultural analysis of 16+ civilizations. The system uses Bayesian inference, Fourier analysis of biorhythms, and optimal control theory to propose next-best-actions under uncertainty, with ADHD as the primary design constraint.

## 1. Introduction
- The problem of unchosen daily defaults (cultural automatisms)
- Hunter-gatherer calibration zero: Hadza/San/Tsimane baselines (Yetish et al. 2015)
- Elite rituals as independent convergence on forager biology (Wiessner 2014, PNAS)
- Why existing tools fail: habit trackers assume executive function

## 2. Biological Foundation
### 2.1 Polyvagal Hierarchy
- Ventral vagal ↔ sympathetic ↔ dorsal collapse (Porges)
- Environment as autonomic mode selector
- HRV as proxy for vagal tone and cognitive control (Längle et al. 2025; Takeda et al. 2025)

### 2.2 Interoception and ADHD
- Diminished body-signal reading in ADHD (Bruton et al. 2025)
- Feedback loop disruption: no interoception → poor decisions → worse interoception
- Passive profiling as a workaround

### 2.3 Multi-Scale Rhythms
- Circadian (~24h): sleep-wake, cortisol, melatonin
- Ultradian (~90-120min): BRAC cycles, attention windows
- Circabidian (~48h): alternating high/low days
- Infradian (>24h): weekly, menstrual, seasonal

## 3. Mathematical Framework
### 3.1 State Space
- x_t = (sleep_proxy, energy, time_budget, friction, vagal_state)
- Observation model: HealthKit/Watch signals → state estimate

### 3.2 Fourier Decomposition of Biorhythms
- Individual rhythm fingerprint: dominant frequencies, phase offsets
- Personalization via spectral analysis of HRV, activity, sleep time series

### 3.3 Bayesian Duration Model
- Prior: population-level task duration distributions
- Likelihood: individual completion data
- Posterior: personalized time estimates with uncertainty
- Online update after each action

### 3.4 Optimal Control (MPC)
- Objective: maximize agency score subject to safety constraints
- Minimum viable day constraint (anti-spiral floor)
- Hard bounds: context switches/hour, recovery floor
- Receding horizon: replan every action window

### 3.5 Multi-Armed Bandit for Micro-Interventions
- Exploration vs exploitation: Thompson sampling
- Action set: 2-5 min interventions (breathing, movement, hydration, light)
- Reward: completion + strain penalty + agency

## 4. Multi-Model Tribunal
- Rationale: no single LLM captures full knowledge
- Architecture: 5+ independent responses on same query
- Diversity scoring across providers/geographies
- Consensus extraction vs productive disagreement

## 5. Cross-Cultural Validation
- 16+ civilizations analyzed (hunter-gatherer → agricultural → industrial → digital)
- 40+ calendar systems as encoded wisdom about temporal structure
- Pattern: all elite rituals converge on biology the forager got free
- Formal mapping: cultural practice → biological mechanism

## 6. System Architecture
- 8-agent Chronos Protocol v3
- Agent competency matrix and delegation logic
- Closed-loop MVP: state → action → outcome → update
- Data pipeline: passive signals → Cosmos DB → bridge → agents → user

## 7. Evaluation Plan
- Simulated user cohort (before real participants)
- Metrics: action completion rate, agency score, HRV trajectory
- ADHD vs neurotypical comparison
- Ablation: with/without cultural grounding, with/without tribunal

## 8. Discussion
- Limitations: Apple ecosystem dependency, Western bias in initial data
- Ethics: passive profiling and consent, ADHD medicalization debate
- Future: Android, wearable-agnostic, multi-language

## References (key)
- Porges, S.W. — Polyvagal Theory
- Yetish, G. et al. (2015) — Natural sleep patterns in pre-industrial societies
- Wiessner, P. (2014, PNAS) — Embers of society: Firelight talk among the Ju/'hoansi
- Bruton, A. et al. (2025) — Interoception and ADHD
- Längle, G. et al. (2025) — HRV and cognitive control
- Takeda, R. et al. (2025) — HRV severity markers in ADHD
- Robe, A. et al. (2021) — Polyvagal and emotion regulation

## Prism Generation Notes
- Target: 15-20 page paper, formal academic style
- Use Prism's citation expansion to fill bibliography
- Generate figures: rhythm decomposition, state-space diagram, agent topology
- Include pseudocode for MPC controller and Bayesian update
