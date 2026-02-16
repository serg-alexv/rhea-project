# Blueprint Literacy Ladder
> RHEA-COMM-002 | 10 micro-lessons | 2-4 min each | Ties to safety constraints and loop variables

## How to use this

Each lesson builds on the previous. Complete them in order. After lesson 5, you understand enough to use Rhea daily. After lesson 10, you understand enough to contribute.

---

## Lesson 1: Why Your Morning Is Not Yours (2 min)

**Core idea:** Your morning routine was not chosen by you. It was inherited from industrial-era defaults: alarm → screen → caffeine → sitting.

**The science:** The autonomic nervous system has three modes (Porges, polyvagal theory):
- Ventral vagal = safe, social, executive function online
- Sympathetic = fight/flight, reactive, no long-term planning
- Dorsal vagal = shutdown, freeze, dissociation

Modern mornings push you into sympathetic before you're regulated. Rhea's first job: don't do that.

**Safety constraint:** Morning rituals are body-first (sensory contact, light, movement) — never decisions, never screens.

**Loop variable:** `circadianPhase` — where you are in your 24h cycle determines what interventions work.

---

## Lesson 2: What Hunter-Gatherers Get for Free (3 min)

**Core idea:** Hadza, San, and Tsimane communities don't need wellness apps. Their environment provides circadian anchoring automatically: natural light at dawn, movement throughout the day, social bonding at dusk, temperature variation, darkness at night.

**The pattern:** Every elite ritual across 16+ civilizations (Japanese forest bathing, Nordic cold exposure, Mediterranean siesta, Ayurvedic dinacharya) independently reconstructs what foragers get for free.

**Safety constraint:** Every Rhea recommendation must trace to a biological mechanism AND a cultural precedent. No "productivity tips."

**Loop variable:** `baselineAlignment` — how close your current defaults are to the forager pattern. Closer = less intervention needed.

---

## Lesson 3: Your Body Knows Before You Do (2 min)

**Core idea:** Heart rate variability (HRV) is a proxy for vagal tone — your nervous system's readiness for cognitive work, social engagement, and emotional regulation.

**The ADHD connection:** Diminished interoception (Bruton et al. 2025) means ADHD brains often can't read their own body signals. By the time you "feel tired," you've been in sympathetic overdrive for hours.

**Safety constraint:** Rhea uses passive biometrics (HRV, sleep, steps) — never questionnaires. Self-report fails precisely for those who need help most.

**Loop variable:** `avgHRV` — rolling 7-day average. Higher = more regulated. Drop = intervention needed.

---

## Lesson 4: Minimum Effective Dose (3 min)

**Core idea:** From control theory — the smallest intervention that produces the largest shift in system state. Not "do more," but "do the right thing at the right time."

**Example:** 10 minutes of morning sunlight shifts circadian phase more than 2 hours of afternoon exercise. 5 minutes of cold water exposure raises HRV more than 30 minutes of meditation for most people.

**Safety constraint:** Rhea limits daily rituals to 6-8. More is not better. Overwhelm = sympathetic activation = the opposite of what we want.

**Loop variable:** `ritualCount` — capped per day. If the system suggests more than 8, something is wrong with the model, not with the user.

---

## Lesson 5: Reading Your Blueprint (2 min)

**Core idea:** Your daily blueprint is a timeline of 6-8 rituals, each tied to a time window, a source civilization, and a biological mechanism.

**How to read a ritual card:**
- **Title:** What to do (e.g., "Morning light exposure")
- **Time window:** When (e.g., "06:30–07:00")
- **Source:** Which civilization discovered this (e.g., "Hadza dawn wake pattern")
- **Mechanism:** Why it works (e.g., "Suppresses melatonin, advances circadian phase via SCN")

**Safety constraint:** 2 taps maximum from app launch to today's blueprint. If navigation is complex, the app has failed.

**Loop variable:** `chronotype` — owl vs lark shifts all time windows. The blueprint adapts, you don't.

---

## Lesson 6: Chronotype Is Not a Preference (3 min)

**Core idea:** Whether you're a morning person or evening person is ~50% genetic (PER3 gene polymorphism). It's not laziness or discipline — it's clock gene expression.

**Why it matters:** A "wake at 5am" recommendation for a late chronotype triggers sympathetic activation. The intervention becomes the stressor. Rhea never fights your chronotype.

**Safety constraint:** All time windows in the blueprint adjust to chronotype. A late chronotype's "morning ritual" might start at 09:00. That's correct, not a bug.

**Loop variable:** `chronotype` — enum: early/intermediate/late. Inferred from sleep patterns, not questionnaires.

---

## Lesson 7: The Feedback Loop (3 min)

**Core idea:** Rhea runs a daily loop: Observe → Profile → Generate → Execute → Observe.

```
HealthKit readings (HRV, sleep, steps)
        ↓
UpdateProfile (rolling averages, phase estimation)
        ↓
GenerateBlueprint (select rituals, set time windows)
        ↓
User follows blueprint (or doesn't)
        ↓
Next day's readings reflect the result
        ↓
Loop repeats
```

**Safety constraint:** The loop never punishes. If you skip rituals, the next day's blueprint adjusts — it doesn't add more. Guilt is sympathetic activation.

**Loop variable:** `sleepDebtHours` — accumulated sleep deficit. High debt = simpler blueprint (fewer rituals, later start time).

---

## Lesson 8: When the System Is Wrong (2 min)

**Core idea:** The model will be wrong sometimes. A ritual that's perfect for population averages may not work for you. That's expected.

**How Rhea handles it:** Bayesian updating. If your HRV drops after a recommended ritual (measured next morning), that ritual's weight decreases for your profile. No explicit feedback needed — the biometrics speak.

**Safety constraint:** No ritual is mandatory. The blueprint is a suggestion with a biological rationale, not a prescription. The user has full override at all times.

**Loop variable:** `ritualWeight` — per-user, per-ritual confidence score. Starts at population prior, converges to individual response.

---

## Lesson 9: Multi-Model Tribunal (4 min)

**Core idea:** For important decisions (profile model changes, new ritual introduction, chronotype reclassification), Rhea queries 5 different AI models and compares their answers.

**Why:** Single-model advice has blind spots. Each model (GPT, Gemini, DeepSeek, Claude, Mistral) has different training data and reasoning patterns. Agreement = higher confidence. Disagreement = flag for human review.

**Safety constraint:** Tribunal required for: changing the user's chronotype classification, adding a new ritual category, modifying the circadian phase model. No single model can make these changes alone.

**Loop variable:** `consensusThreshold` — minimum agreement ratio (e.g., 4/5 models) before a profile change is applied.

---

## Lesson 10: Contributing to Rhea (3 min)

**Core idea:** Rhea is built in the open. The four contribution areas (science validation, cultural research, iOS development, bridge engineering) each have specific entry points.

**What makes a good contribution:**
- Science: Point to a specific claim → link a paper → state whether it's wrong, incomplete, or could be stronger
- Culture: Documented daily rhythm pattern → primary source → biological mechanism connection
- iOS: Follow ARCHITECTURE_FREEZE.md → domain layer has zero framework imports → all biometrics through HealthKit adapter
- Bridge: Follow ProviderConfig pattern → test with `bash ops/bridge-probe.sh`

**Safety constraint:** No overclaims. If the evidence is preliminary, say "preliminary." If the mechanism is hypothesized, say "hypothesized." Confidence without evidence is worse than uncertainty.

**Loop variable:** You. The system improves because people contribute better science, better cultural data, and better code. The loop is human + machine, not machine alone.

---

## Unlock Map

```
Lesson 1-2:  Understand the problem        → Can explain Rhea to someone else
Lesson 3-4:  Understand the science         → Can evaluate if a ritual makes sense
Lesson 5-6:  Understand the app             → Can use Rhea daily
Lesson 7-8:  Understand the loop            → Can interpret why the blueprint changes
Lesson 9-10: Understand the system          → Can contribute to Rhea
```
