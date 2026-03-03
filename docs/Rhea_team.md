# Rhea Team Structure
> Agent OS — 8 domains, 10 teams, 3 leaders

## Leadership

| Who | Model | Role |
|-----|-------|------|
| **Rex** | Opus 4.6 | Team Lead, Dev Overwatcher + R&R |
| **Orion** | GPT-5.3 | Right Hand, Dev Overwatcher + R&D |
| **Human** | — | Same tier, Final Call. Comes to press Y at least once daily. |

Rex and Orion review, don't write. Workers write. Leadership = routing + quality gate.

## Teams 1-8: Daily Coding

Sonnet-level workers on RHEL Cloud. Boring daily coding, not art.

| Team | Domain | Absorption Strategy | Deliverable |
|------|--------|-------------------|-------------|
| **T1** | Protocols | Implement MCP + A2A | Rhea speaks both protocols |
| **T2** | Durable Execution | Absorb DBOS pattern | Side-effect journaling on governor/task_queue |
| **T3** | Memory | Absorb mem0/Letta/Graphiti patterns | Formalized 4-tier memory API |
| **T4** | Sync | Vendor Loro, Depend ElectricSQL | Cross-device CRDT state sync |
| **T5** | Extension | Depend WXT | Cross-browser extension v0.1 |
| **T6** | Mesh | Depend Reticulum + libp2p | Agent-to-agent P2P networking |
| **T7** | RAG | Absorb GraphRAG, Depend R2R | Knowledge graph RAG in Aletheia |
| **T8** | Orchestration | Depend Agents SDK + LangGraph | Standard agent runtime |

## Team X: Out of the Blue

PR + Support + Rotation. Not coding. Appears when needed, vanishes when not.

| Member | Role |
|--------|------|
| **Hyperion** | SMM, public voice, community |
| **Argos** | Monitoring, health checks, SLA |
| **Chronos** | Scheduling, rotation, cadence |
| **B-2nd** | Backup, failover, redundancy |
| **+SMM** | Content, landing, socials |

## Principles

- T1-T8 = parallel, independent, no shared state between teams
- Leadership reviews PRs, doesn't write code
- Team X has different cadence than dev teams — async, event-driven
- All under MIT/Apache 2.0 — no GPL anywhere
- Workers are cheap-tier (Sonnet/Haiku), escalate to Opus/GPT-5 only for review
