# Chronos Protocol v3 — Delegation Run
> Version: 3.0 | Date: 2026-02-13 | Status: Ready for execution

## Purpose

This document defines 5 sample delegation runs that exercise all 8 agents, testing parallel/sequential execution, conflict resolution, tribunal mode, and quality gates. Successful completion validates that Chronos Protocol v3 is operational.

---

## Pre-Run Checklist

- [ ] All 8 agent prompts loaded and tested individually
- [ ] rhea_bridge.py connected to all 6 providers
- [ ] Communication format (`[CHRONOS:A→A]`) validated
- [ ] Quality gate checklist available to A8
- [ ] Tribunal mode models accessible (o3, DeepSeek-R1, Gemini 3 Pro, GPT-5.2, Kimi K2.5)
- [ ] Azure Cosmos DB operational for data persistence

---

## Task A: Morning Routine Sequence Design

**Objective:** Design a science-backed, culturally grounded morning routine that works for ADHD users with executive dysfunction.

**Trigger:** `[CHRONOS:HUMAN→A8] Design optimal morning sequence for Rhea MVP`

### Delegation Chain

**Step 1 — A8 decomposes:**
```
[CHRONOS:A8→A4] Research morning rituals across 15+ civilizations. Focus: first 90 minutes after waking.
[CHRONOS:A8→A1] Model circadian cortisol/melatonin phase for wake-up window. Include light exposure timing.
[CHRONOS:A8→A2] Map neuroendocrine cascade: wake → cortisol peak → dopamine availability. ADHD-specific.
```
*Execution: A4, A1, A2 run in PARALLEL (no dependencies)*

**Step 2 — Research synthesis:**
```
[CHRONOS:A4→A8] Delivered: Morning rituals from Japanese (mizukori), Ayurvedic (dinacharya), Scandinavian (cold exposure), Roman (statio matutina), Islamic (fajr), Hadza (fire-side wake), San (dawn movement). Convergence: light exposure, cold/temperature shift, movement before food, social contact.

[CHRONOS:A1→A8] Delivered: Cortisol Awakening Response (CAR) peaks 30-45min post-wake. Optimal light exposure: 10,000 lux within 30min. Melatonin suppression requires 480nm+ wavelength. Model: f(t) = baseline + CAR_amplitude * e^(-λt).

[CHRONOS:A2→A8] Delivered: ADHD cortisol response is blunted (Imeraj et al. 2012). Dopamine availability delayed ~60min vs neurotypical. Compensatory strategy: sensory stimulation (cold, light, movement) before cognitive demand. Polyvagal: morning = transition from dorsal (sleep) to ventral vagal (social engagement) — needs graded arousal, not alarm shock.
```

**Step 3 — A8 routes to product:**
```
[CHRONOS:A8→A3] Given ADHD executive dysfunction: what morning UX constraints? Max decisions = ?
[CHRONOS:A8→A5] Design morning sequence UX. Inputs: A1 timing model, A2 ADHD constraints, A4 cultural practices, A3 profile constraints.
```
*Execution: A3 first (fast, ~2min), then A5 (needs A3 output)*

**Step 4 — A3 responds:**
```
[CHRONOS:A3→A5] ADHD morning constraints: zero decisions in first 15 minutes. Maximum 2 choices per screen. No text-heavy content before cortisol peak. Use haptic + audio cues, not visual notifications. Assume phone in hand but prefrontal cortex offline.
```

**Step 5 — A5 designs:**
```
[CHRONOS:A5→A8] Morning Sequence UX Spec v1:
  0-5min: Gentle haptic wake (no alarm sound). Screen shows only ambient light visualization.
  5-15min: "Body first" prompt — single action (cold face wash OR step outside OR stretch). No choice paralysis — system selects based on A3 profile.
  15-30min: Light exposure tracking (phone camera measures ambient lux). Passive — no user action needed.
  30-45min: First optional interaction — cultural morning practice (from A4 library, matched to user's cultural background via A4).
  45-90min: Gradual cognitive load increase. First task suggestion appears only after cortisol peak detected via HRV.
```

**Step 6 — A6 feasibility:**
```
[CHRONOS:A5→A6] Can we implement ambient lux measurement via iPhone camera? HealthKit HRV in background?
[CHRONOS:A6→A5] Lux measurement: YES, AVCaptureDevice.iso + exposureDuration approximation. Accuracy ±30%. HRV: YES via HealthKit background delivery (Apple Watch required). Cortisol peak: INFERRED from HRV trend, not measured directly.
```

**Step 7 — A8 quality gate:**
- [x] Scientific accuracy — A2 confirmed CAR model and ADHD compensatory strategy
- [x] Cultural provenance — A4 cited 7 civilizations + 2 hunter-gatherer societies
- [x] ADHD compatibility — A3 confirmed zero-decision first 15min
- [x] Technical feasibility — A6 confirmed lux + HRV implementation
- [x] Principle alignment — Body before mind ✓, Passive ✓, ADHD-optimized ✓, Cultural roots ✓

**Result:** ✅ Morning Routine Sequence approved for implementation

---

## Task B: ADHD Behavioral Profile Detection

**Objective:** Design passive behavioral profiling that detects ADHD subtypes without questionnaires.

**Trigger:** `[CHRONOS:HUMAN→A8] Build passive ADHD profiling system`

### Delegation Chain

**Step 1 — A8 decomposes:**
```
[CHRONOS:A8→A3] Define behavioral signals that distinguish ADHD subtypes (inattentive / hyperactive / combined). Passive only — no questionnaires.
[CHRONOS:A8→A2] What physiological markers correlate with ADHD subtypes? HRV signatures?
[CHRONOS:A8→A1] Statistical model needed: classify ADHD subtype from behavioral + physiological signal vector.
```
*Execution: A3 and A2 in PARALLEL, then A1 (needs their outputs)*

**Step 2 — Research delivers:**
```
[CHRONOS:A3→A8] Passive ADHD signals:
  Inattentive: High app-switching frequency, incomplete tasks (screen time data), long dwell on low-salience content, delayed response to notifications
  Hyperactive: Short session durations, high movement (accelerometer), frequent device pickup, typing speed variance
  Combined: Both patterns, time-of-day dependent (hyperactive AM, inattentive PM)
  Additional: Sleep onset latency (HealthKit), social media scroll depth, time-to-first-interaction after wake

[CHRONOS:A2→A8] HRV correlations:
  Lower resting RMSSD in ADHD vs neurotypical (meta: Koenig et al. 2017)
  Reduced HRV reactivity during cognitive tasks
  Hyperactive subtype: higher sympathetic tone (LF/HF ratio)
  Inattentive: reduced parasympathetic (lower HF power)
```

**Step 3 — A1 builds classifier:**
```
[CHRONOS:A1→A8] Bayesian classifier spec:
  Feature vector: [app_switch_freq, session_duration_mean, session_duration_var, movement_intensity, notification_response_time, sleep_onset_latency, RMSSD_rest, LF_HF_ratio, HRV_reactivity]
  Prior: Population prevalence (inattentive 50%, combined 30%, hyperactive 20%)
  Personalization: Bayesian update over 14-day observation window
  Confidence threshold: 0.75 before subtype assignment
  Output: P(inattentive), P(hyperactive), P(combined) + confidence interval
```

**Step 4 — A5 designs adaptive UI:**
```
[CHRONOS:A8→A5] Design UI that adapts to detected ADHD subtype.
[CHRONOS:A5→A8] Adaptive rules:
  Inattentive profile: Reduce information density, use single-focus screens, stronger haptic cues for transitions
  Hyperactive profile: Allow rapid navigation, shorter content blocks, movement-integrated interactions
  Combined profile: Time-of-day switching — hyperactive mode AM, inattentive mode PM
  Unclassified (Day 1-14): Conservative defaults — treat as combined with maximum accommodation
```

**Step 5 — Quality gate:** All 5 checks pass. ✅ Approved.

---

## Task C: HRV Threshold Calibration

**Objective:** Define personalized HRV thresholds for cognitive readiness states.

**Trigger:** `[CHRONOS:HUMAN→A8] Calibrate HRV thresholds for Rhea users`

### Delegation Chain

**Step 1 — Parallel research:**
```
[CHRONOS:A8→A2] Population HRV norms for ADHD cohort. Define state thresholds: recovery / baseline / alert / stressed / overloaded.
[CHRONOS:A8→A1] Mathematical model for personalizing population thresholds to individual baseline over 14-day window.
[CHRONOS:A8→A4] Any cultural practices that correlate with improved HRV? (Breathing techniques, meditation, cold exposure across civilizations)
```

**Step 2 — Synthesis:**
A2 provides population baselines (RMSSD ranges per state), A1 builds personalization algorithm (exponential moving average with Bayesian priors), A4 identifies converging practices (pranayama, Wim Hof, Japanese forest bathing — all improve vagal tone).

**Step 3 — A5/A6 implementation:**
A5 designs HRV dashboard (minimal, shows autonomic state as color gradient — no numbers for ADHD users). A6 confirms HealthKit API delivers RMSSD at required frequency.

**Step 4 — Quality gate:** ✅ Approved.

---

## Task D: Content Strategy for Launch

**Objective:** Create launch content strategy leveraging Rhea's unique cultural + science narrative.

**Trigger:** `[CHRONOS:HUMAN→A8] Plan content strategy for Rhea launch`

### Delegation Chain

**Step 1 — A8 routes:**
```
[CHRONOS:A8→A7] Lead content strategy. Budget: organic first, paid later.
[CHRONOS:A8→A4] Provide 10 most compelling cultural stories for content (civilizations discovering same pattern independently).
[CHRONOS:A8→A3] Define 3 user personas from ADHD community for content targeting.
```
*Execution: A4 and A3 in PARALLEL, A7 waits for inputs*

**Step 2 — Inputs arrive:**
A4 delivers: Top stories include Japanese ikigai + Okinawan daily structure, Hadza dawn movement, Roman otium/negotium rhythm, Scandinavian friluftsliv, Ayurvedic dinacharya. A3 delivers: Personas — "Overwhelmed Optimizer" (knows what to do, can't execute), "Curious Skeptic" (needs science proof), "Culture Explorer" (drawn by civilizational wisdom).

**Step 3 — A7 builds strategy:**
```
[CHRONOS:A7→A8] Content Strategy v1:
  4 pillars: Educational blog (A2 science), Cultural wisdom series (A4 stories), Social proof (user transformation), In-app micro-stories
  Channels: Medium/Substack (long-form), Twitter/X (science threads), TikTok (cultural stories, 60sec), Reddit (r/ADHD, r/productivity)
  Launch sequence: 8-week pre-launch content runway → beta invite → public launch
  Key narrative: "Every civilization independently discovered what your nervous system already knows"
  Anti-patterns: No productivity porn, no "10 habits" lists, no guilt-based motivation
```

**Step 4 — A8 reviews:**
- [x] Aligns with ADHD-optimized (no guilt-based motivation) ✓
- [x] Cultural provenance in every content piece ✓
- [x] Science backing for every claim ✓
- [x] Accessible to all 3 personas ✓

**Result:** ✅ Content Strategy approved.

---

## Task E: Feature Release Decision — Tribunal Mode

**Objective:** Resolve disagreement about whether to include sleep timing recommendations in MVP.

**Trigger:** A4 argues sleep timing should be in MVP (every civilization regulates sleep). A5 argues defer to Phase 2 (scope creep, HealthKit sleep data unreliable without Apple Watch).

### Tribunal Activation

**Step 1 — A8 frames the question:**
```
[CHRONOS:A8→TRIBUNAL]
Question: Should Rhea MVP include active sleep timing recommendations?
Context:
  FOR (A4): 16/16 civilizations studied regulate sleep timing. Hunter-gatherer data shows sleep onset 3.5h after sunset. This is the #1 cultural convergence.
  AGAINST (A5): MVP scope risk. iPhone-only sleep data is inaccurate. Apple Watch required for reliable sleep stages. Adding sleep timing delays launch by 3 weeks.
Evaluate: Include in MVP, defer to Phase 2, or compromise?
```

**Step 2 — 5 models respond:**

| Model | Position | Confidence | Key Reasoning |
|-------|----------|--------:|---------------|
| o3 | Include (passive only) | 85% | Sleep is foundational. But only passive tracking — no recommendations until data quality confirmed. |
| DeepSeek-R1 | Defer | 70% | Technical risk. Inaccurate data → bad recommendations → user trust loss. Ship what works perfectly. |
| Gemini 3 Pro | Compromise | 90% | Include sleep *tracking* (passive). Defer *recommendations* to Phase 2 when Apple Watch data available. |
| GPT-5.2 | Compromise | 80% | Track sleep onset time (simple), show correlation with next-day energy. No prescriptive recommendations. |
| Kimi K2.5 | Include (passive only) | 75% | Cultural data too strong to exclude. But passive mode avoids accuracy problem. |

**Step 3 — A8 synthesizes:**
```
Consensus: 4/5 models support including sleep in some form (80%).
Position: COMPROMISE — Include passive sleep tracking in MVP (onset time + duration via iPhone). Defer active sleep timing recommendations to Phase 2 (requires Apple Watch for sleep stage accuracy).
Confidence: 82% weighted average.
```

**Step 4 — Decision documented:**
New ADR created: `ADR-008: Sleep tracking passive in MVP, recommendations in Phase 2`

**Result:** ✅ Tribunal decision accepted. A5 updates roadmap, A6 implements passive sleep tracking.

---

## Post-Run Checklist

### Execution Quality
- [ ] All 5 tasks completed within expected timelines
- [ ] No agent received a task outside its domain
- [ ] Parallel execution used where possible (Tasks A, B, C, D all had parallel phases)
- [ ] Sequential dependencies respected (no agent started before receiving required inputs)

### Communication Quality
- [ ] All inter-agent messages used `[CHRONOS:A→A]` format
- [ ] Payloads were specific and actionable (no vague requests)
- [ ] Dependencies explicitly tracked
- [ ] Deadlines set for all non-trivial tasks

### Quality Gates
- [ ] All 5 tasks passed the 5-check validation
- [ ] A2 validated all scientific claims
- [ ] A4 provided cultural provenance for all recommendations
- [ ] A3 confirmed ADHD compatibility for all UX decisions
- [ ] A6 confirmed technical feasibility for all implementation items

### Conflict Resolution
- [ ] Task E exercised Tribunal mode successfully
- [ ] 5 independent models provided independent evaluations
- [ ] Consensus reached (80% agreement on compromise)
- [ ] Decision documented as ADR

### Metrics
- [ ] Average response quality: ___ / 5 (agent output usefulness)
- [ ] Cross-agent coherence: ___ revision cycles needed
- [ ] Cost per task: $___  (via model routing)
- [ ] Time to completion per task: ___

---

## Next Steps After Successful Run

1. **Freeze Protocol v3** — Mark as stable in state.md
2. **Create agent prompt templates** — Individual system prompts for each agent derived from protocol
3. **Integrate with rhea_bridge.py** — Wire `[CHRONOS:A→A]` messages to actual API calls
4. **Begin iOS MVP scaffold** — A6 starts SwiftUI + HealthKit implementation
5. **Launch content runway** — A7 begins 8-week pre-launch content sequence
