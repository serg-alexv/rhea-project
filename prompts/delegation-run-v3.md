# Delegation Run v3 — Test Cases
> Protocol: AI_COMPACT_LANG v0.1 ⟨docs/AI_COMPACT_LANG.md⟩

## Pre-Run
- [ ] 8 agent prompts loaded + tested
- [ ] RB → 6 providers connected
- [ ] `@A→@A` format validated
- [ ] TB models accessible (o3, DeepSeek-R1, Gemini 3 Pro, GPT-5, Kimi K2.5)

## Task A: Morning Routine

@human → @A8: Design morning sequence for MVP

**Flow:**
1. A8 decomposes → A4(rituals 15+ civilizations) ∥ A1(cortisol/melatonin model) ∥ A2(ADHD neuroendocrine)
2. A4: 7 civilizations + 2 hunter-gatherer. Convergence: light, cold, movement before food, social contact
3. A1: CAR peaks 30-45min post-wake. 10K lux within 30min. f(t)=baseline+CAR_amp·e^(-λt)
4. A2: ADHD cortisol blunted. Dopamine delayed ~60min. Compensate: sensory stim before cognitive. Polyvagal: dorsal→ventral = graded arousal ✗ alarm shock
5. A3: #decisions_first_15min=0. Max 2 choices/screen. ✗ text before cortisol peak. Haptic+audio ✗ visual
6. A5: UX spec: 0-5min haptic wake | 5-15min body first (single action, system selects) | 15-30min passive lux tracking | 30-45min optional cultural practice | 45-90min gradual cognitive load after HRV cortisol peak
7. A6: lux via AVCaptureDevice ✓ (±30%). HRV via HealthKit background ✓ (Apple Watch). Cortisol = inferred
8. Gate: 5/5 ✓ → ✓ Approved

## Task B: ADHD Passive Profiling

@human → @A8: Build passive ADHD profiling

**Flow:**
1. A3 ∥ A2, then A1
2. A3 signals: inattentive(app-switch freq, incomplete tasks, long dwell) | hyperactive(short sessions, high movement, device pickup) | combined(both, time-dependent: hyperactive AM, inattentive PM)
3. A2: lower RMSSD in ADHD (Koenig 2017). Hyperactive: higher LF/HF. Inattentive: lower HF power
4. A1: Bayesian classifier. Feature vector: [app_switch, session_dur_μ/σ, movement, notif_response, sleep_onset, RMSSD, LF_HF, HRV_react]. Prior: inatt 50%, combined 30%, hyper 20%. 14-day window. Confidence ≥0.75
5. A5: adaptive UI per subtype. Unclassified (day 1-14) = combined + max accommodation
6. Gate: 5/5 ✓

## Task C: HRV Calibration

@human → @A8: Calibrate HRV thresholds

**Flow:**
1. A2(population norms) ∥ A1(personalization model) ∥ A4(cultural HRV practices)
2. A2: RMSSD ranges per state (recovery/baseline/alert/stressed/overloaded)
3. A1: EMA + Bayesian priors, 14-day personalization
4. A4: pranayama, Wim Hof, shinrin-yoku → all improve vagal tone (convergent)
5. A5: HRV dashboard = color gradient ✗ numbers (ADHD). A6: HealthKit RMSSD frequency ✓
6. Gate: 5/5 ✓

## Task D: Content Strategy

@human → @A8: Plan content for launch

**Flow:**
1. A4(10 compelling stories) ∥ A3(3 personas), then A7
2. A4: ikigai, Hadza dawn, Roman otium, friluftsliv, dinacharya...
3. A3: "Overwhelmed Optimizer" | "Curious Skeptic" | "Culture Explorer"
4. A7: 4 pillars (science, culture, social proof, micro-stories). Channels: Medium, X, TikTok, Reddit. 8-week pre-launch runway. Key: "Every civilization discovered what your nervous system knows"
5. Anti-patterns: ✗ productivity porn, ✗ "10 habits", ✗ guilt-based motivation
6. Gate: 4/4 ✓

## Task E: Tribunal — Sleep in MVP?

FOR (A4): 16/16 civilizations regulate sleep. #1 convergence.
AGAINST (A5): scope creep, iPhone sleep data unreliable ✗ Apple Watch, +3 weeks delay.

**TB result:**
| Model | Position | Confidence |
|-------|----------|--------:|
| o3 | Include (passive) | 85% |
| DeepSeek-R1 | Defer | 70% |
| Gemini 3 Pro | Compromise | 90% |
| GPT-5 | Compromise | 80% |
| Kimi K2.5 | Include (passive) | 75% |

Consensus 4/5 (80%): COMPROMISE — passive sleep tracking in MVP (onset+duration via iPhone). Defer recommendations → Phase 2 (Apple Watch required). → ADR-008

## Post-Run Checklist
- [ ] 5 tasks completed within timeline
- [ ] ✗ out-of-domain assignments
- [ ] Parallel execution used (A,B,C,D all had ∥ phases)
- [ ] Sequential deps respected
- [ ] All 5 tasks passed 5-chk gate
- [ ] TB mode exercised (Task E): 5 models, 80% consensus, ADR documented
