# Rhea — User Guide

> Your AI-powered daily rhythm optimizer. ADHD-optimized, science-backed, passive profiling.

## What is Rhea?

Rhea is a Mind Blueprint Factory — it generates, evaluates, and iterates on your daily structure using scientific rhythms, multi-model AI consensus, and closed-loop planning.

Rhea does NOT tell you what to do. It discovers your natural patterns (sleep, movement, energy) and builds a schedule that works *with* your biology, not against it.

## Core Principles

**Body-first:** Morning starts with movement and light, not screens and decisions.

**Passive profiling:** Rhea learns from your behavior (sleep times, activity patterns, HRV) — no questionnaires, no onboarding surveys.

**ADHD-friendly:** Every interaction assumes executive dysfunction as default. Minimal choices, clear actions, no guilt.

**Hunter-gatherer baseline:** Your nervous system evolved for a pattern that modern life disrupts. Rhea reconstructs what foragers get naturally.

---

## Getting Started

### 1. Current: CLI Mode (Cowork/Claude Code)
```bash
# Check system health
./rhea check

# Take a memory snapshot
./rhea memory snapshot "my first snapshot"

# Run the memory benchmark
bash scripts/memory_benchmark.sh

# Commit with Entire.io checkpoint (always use this instead of raw git commit)
bash scripts/rhea_commit.sh -m "your commit message"
```

### 2. Future: iOS App
TestFlight → production pipeline. SwiftUI + HealthKit + Apple Watch.
See `docs/ROADMAP.md` for timeline.

### 3. Future: React PWA
Web dashboard for visualizing state, agents, and schedules.
See `docs/ui_pwa_vision.md`.

---

## How Rhea Thinks

Rhea uses 8 specialized AI agents that collaborate:

| Agent | Role | What it does for you |
|-------|------|---------------------|
| Chronos | Time keeper | Manages your schedule and rhythm detection |
| Gaia | Body state | Reads HRV, movement, interoception signals |
| Hypnos | Sleep | Tracks sleep debt and recovery |
| Athena | Strategist | Plans your day with deep reasoning |
| Hermes | Communicator | Handles user interaction |
| Hephaestus | Builder | Generates code and technical work |
| Hestia | Guardian | Safety checks and constraint enforcement |
| Apollo | Synthesizer | Detects patterns and generates insights |

---

## Memory Capabilities

Rhea has a 6-layer memory architecture that gives it continuity across sessions. Unlike a typical AI chat that forgets everything, Rhea *remembers*, *learns*, and *improves*.

### Layer 1: Compact State (`docs/state.md`)
A ≤2KB summary of the project's current status — mission, deliverables, what's done, what's next. This is loaded at the start of every session so Rhea knows where it left off. Think of it as Rhea's "working memory."

### Layer 2: Full State (`docs/state_full.md`)
The detailed version with architecture decisions, agent definitions, and technical context. Loaded on demand when deeper understanding is needed.

### Layer 3: Episodic Memory (Entire.io)
Every commit creates an `Entire-Checkpoint` trailer that links to a searchable snapshot on [entire.io](https://entire.io). This is Rhea's "episodic memory" — it can recall what it was thinking at any past commit.

**How to use:**
```bash
# Commit with checkpoints (ALWAYS use wrapper, not raw git commit)
bash scripts/rhea_commit.sh -m "description of what changed"

# View checkpoints
# → https://entire.io/serg-alexv/rhea-project/checkpoints/main
```

### Layer 4: Local Snapshots (`.entire/snapshots/`)
JSON snapshots captured on every commit. Each snapshot contains: compact state, git status, document sizes, and metadata. These are the "offline backup" of episodic memory — available even without internet.

**How to use:**
```bash
# List all snapshots
ls .entire/snapshots/

# Create a named snapshot
./rhea memory snapshot "before_refactor"
```

### Layer 5: Decision Log (`docs/decisions.md`)
Every architectural choice is recorded as an ADR (Architecture Decision Record). Currently 13 ADRs. This prevents re-debating settled questions and lets Rhea explain *why* things are the way they are.

### Layer 6: Failure Memory (`docs/reflection_log.md`)
Every failure is logged with root cause and fix. Rhea consults this before repeating similar tasks. Currently 5 entries. This is how Rhea avoids making the same mistake twice.

### Memory Health

The Discomfort function **D** measures memory bloat. Current D=91.96 (comfort zone). Thresholds: T1=150 (warning), T2=300 (overload triggers cleanup).

```bash
# Run the memory benchmark
bash scripts/memory_benchmark.sh
```

---

## Bridge Capabilities

The Rhea Bridge (`src/rhea_bridge.py`) connects to 6 AI providers and 31+ models, enabling multi-perspective reasoning at minimal cost.

### Providers
| Provider | Models | Free tier? |
|----------|--------|-----------|
| OpenAI | GPT-4o, GPT-4o-mini, o4-mini, GPT-4.5-preview | ✅ (rate limited) |
| Google Gemini | 2.0-flash, 2.0-flash-lite, 2.5-flash, 2.5-pro | ✅ generous |
| DeepSeek | deepseek-chat, deepseek-reasoner | ✅ (with credits) |
| OpenRouter | Claude, Llama, Mistral, and 100+ models | Varies |
| HuggingFace | Open models via Inference API | ✅ |
| Azure | GPT-4o, GPT-4.1 | ✅ (with credits) |

### How to use

```bash
# Check which providers are available
python3 src/rhea_bridge.py status

# Ask a single model (cheapest available)
python3 src/rhea_bridge.py ask "What is the optimal morning routine for ADHD?"

# Run a tribunal — 3 models debate a question
python3 src/rhea_bridge.py tribunal "Should Rhea use auto-commit or manual-commit?" --k 3

# See all available models
python3 src/rhea_bridge.py models
```

### Tiered Model Routing (ADR-008)

Not all questions need expensive models. Rhea routes by tier:

| Tier | When to use | Cost |
|------|-------------|------|
| **cheap** | 80% of tasks: summarization, formatting, simple Q&A | ~$0.00 |
| **balanced** | Strategy, planning, moderate reasoning | ~$0.01 |
| **expensive** | Deep research, novel synthesis, critique | ~$0.05 |
| **reasoning** | Mathematical proofs, code architecture, complex logic | ~$0.10 |

Default = cheap. Expensive/reasoning require explicit justification.

### Tribunal Mode

The tribunal is Rhea's most powerful reasoning tool. Instead of trusting one model, it asks 3+ models the same question and synthesizes their responses into a weighted consensus.

**When to use tribunals:**
- Architectural decisions (which framework? which strategy?)
- Debugging when the cause is unclear
- Any question where multiple perspectives matter
- Evaluating trade-offs between approaches

**Tribunal output includes:** each model's position, agreement score (0.0–1.0), and an ADR if the question warrants a formal decision.

---

## Evolution Capabilities

Rhea is designed to *improve itself* over time. These are the self-upgrade mechanisms (ADR-011):

### 1. Reflexion Loop
Generate → self-evaluate → revise. Up to 3 cycles. Cheap models draft, then self-critique before presenting the result. This means first drafts are never final.

### 2. Tribunal/Debate
Multiple models argue different positions on a question. The synthesis captures insights no single model would reach alone. Used for all ADR decisions.

### 3. Tool-Verification Loops
After generating code, Rhea immediately runs and tests it. If tests fail, it iterates until they pass. Code is never committed without verification.

### 4. Eval Sets
Maintained in `eval/tasks/*.yaml` — known-answer tasks that Rhea runs periodically to detect regression. If the memory benchmark score drops, something broke.

```bash
# Run eval suite
bash scripts/memory_benchmark.sh
```

### 5. Failure Memory
Every failure is logged in `docs/reflection_log.md` with root cause and fix. Before attempting similar tasks, Rhea checks this log to avoid repeating mistakes.

### 6. Teacher-Student
For genuinely hard problems, expensive models (Opus, GPT-4.5) act as "teachers." Their reasoning patterns are distilled and applied by cheaper models in future sessions.

### How evolution works in practice

Each session, Rhea:
1. Loads compact state → knows where it left off
2. Checks reflection_log → avoids known pitfalls
3. Runs requested work → uses cheapest adequate model
4. Self-evaluates output → reflexion loop if quality is low
5. Commits with checkpoint → episodic memory updated
6. Updates metrics → D function tracks memory health

Over weeks, the accumulated decisions (ADRs), failure patterns (reflection_log), and episodic snapshots (Entire.io) make Rhea progressively smarter about *this specific project*.

---

## Cost

Rhea is designed to run on ~$0.05/day in API costs. See `docs/cost_guide.md` for details.

## Data & Privacy

All your data stays in your repository. Rhea never sends personal information to third parties. AI model queries contain only anonymized task descriptions, never personal health data.
