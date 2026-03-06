---
sidebar_position: 1
slug: /
---

# Rhea System Overview

Rhea is a **multi-model advisory system** built on control theory, chronobiology, and distributed time. It queries multiple AI models simultaneously, compares their answers, and produces a **consensus with confidence scores** — the Tribunal.

## Architecture at a Glance

```
┌──────────────────────────────────────────────────────────────────┐
│                        Clients                                   │
│  iOS App · RheaKit Web · Chrome Extension · CLI                  │
└────────────┬─────────────────────────────────┬───────────────────┘
             │ HTTPS                           │ TCP/mDNS
             ▼                                 ▼
┌────────────────────────┐      ┌─────────────────────────────────┐
│  Tribunal API (FastAPI)│      │     frontier-gem (Rust daemon)  │
│  :8400                 │      │  HTTP :3456 · TCP :4444 · mDNS  │
│                        │      │                                  │
│  /tribunal    consensus│      │  0.log writer (hash-chain)       │
│  /clipboard   sync     │      │  clipboard proxy                 │
│  /salon       chat     │      │  AI discovery (focus tracking)   │
│  /office      agents   │      │  DTN outbox (offline-first)      │
│  /orchestration  flow  │      └──────────────┬──────────────────┘
│  /v1/chat/completions  │                     │ append
│  /mcp         bridge   │                     ▼
└───────────┬────────────┘      ┌──────────────────────────────────┐
            │                   │  0.log — Universal Event Bus      │
            ▼                   │  /tmp/0.log                       │
┌────────────────────────┐      │  Hash-chained JSONL frames        │
│  Rhea Bridge (Python)  │      └──────────────────────────────────┘
│  6+ providers           │
│  40+ models             │      ┌──────────────────────────────────┐
│  5 cost tiers           │      │  Session Server (Rust/Axum)      │
│  Backoff + retry        │      │  :3000                           │
│  Cost tracking          │      │  Lamport clocks · CRDT-ready     │
└────────────────────────┘      │  4 character archetypes           │
                                └──────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│                     Persistence                                   │
│  SQLite (WAL) — sessions, history, radio, clipboard, tasks        │
│  MongoDB — change stream → SSE push (optional)                    │
│  CockroachDB — distributed store (optional)                       │
└──────────────────────────────────────────────────────────────────┘
```

## Core Principles

| Principle | Implementation |
|-----------|---------------|
| **Multi-model consensus** | Tribunal queries 2–10 models, analyzes agreement/divergence |
| **Cost discipline** | 5 tiers (cheap→science), execution profiles, budget caps (ADR-008) |
| **Distributed time** | Lamport clocks in sessions, no wall-clock dependency |
| **Offline-first** | DTN outbox in frontier-gem, local SQLite, hash-chain event log |
| **Adversarial verification** | Devil's advocate layer, 15% skepticism discount on confidence |

## Key Technologies

- **Python 3.11** — Tribunal API, Bridge, Orchestration
- **Rust** — frontier-gem daemon, session server, rhea-dash
- **Swift** — iOS app (RheaApp, RheaKeyboard, RheaTunnel)
- **FastAPI** — HTTP API with OpenAPI/Swagger docs
- **Axum** — Rust HTTP framework for session server
- **LiteLLM** — Unified LLM provider interface
- **SQLite WAL** — Primary persistence layer

## What This Documentation Covers

This site documents the **backend system, protocols, and deployment**. For the RheaKit UI component library (SwiftUI/React), see its dedicated documentation site.
