# Rhea — User Guide

> Your AI-powered daily rhythm optimizer. ADHD-first, science-backed, zero-questionnaire.

## What is Rhea?

Rhea is a Mind Blueprint Factory — it generates, evaluates, and iterates on your daily structure using scientific rhythms, multi-model AI consensus, and closed-loop planning.

Rhea does NOT tell you what to do. It discovers your natural patterns (sleep, movement, energy) and builds a schedule that works *with* your biology, not against it.

## Core Principles

**Body-first:** Morning starts with movement and light, not screens and decisions.

**Passive profiling:** Rhea learns from your behavior (sleep times, activity patterns, HRV) — no questionnaires, no onboarding surveys.

**ADHD-friendly:** Every interaction assumes executive dysfunction as default. Minimal choices, clear actions, no guilt.

**Hunter-gatherer baseline:** Your nervous system evolved for a pattern that modern life disrupts. Rhea reconstructs what foragers get naturally.

## Getting Started

### 1. Current: CLI Mode (Cowork/Claude Code)
```bash
# Check system health
./rhea check

# Take a memory snapshot
./rhea memory snapshot "my first snapshot"

# Run the memory benchmark
bash scripts/memory_benchmark.sh
```

### 2. Future: iOS App
TestFlight → production pipeline. SwiftUI + HealthKit + Apple Watch.
See `docs/ROADMAP.md` for timeline.

### 3. Future: React PWA
Web dashboard for visualizing state, agents, and schedules.
See `docs/ui_pwa_vision.md`.

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

## Cost

Rhea is designed to run on ~$0.05/day in API costs. See `docs/cost_guide.md` for details.

## Data & Privacy

All your data stays in your repository. Rhea never sends personal information to third parties. AI model queries contain only anonymized task descriptions, never personal health data.
