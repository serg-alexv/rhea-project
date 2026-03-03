# Agent OS — Absorption Map
> Generated: 2026-03-03 | Research: 7 parallel agents, 8 technology domains
> License constraint: MIT/Apache 2.0 only. No GPL/AGPL/BSL/SSPL.

## Architecture Formula
```
Agent OS = Protocols (implement) + Runtime (durable) + Memory (4-tier)
         + Sync (CRDT) + Extension (cross-browser) + Mesh (p2p)
         + RAG (knowledge) + Orchestration (agent SDK)
```

## Decision: Absorb vs Implement vs Follow

| Strategy | Meaning | When |
|----------|---------|------|
| **Implement** | We speak the protocol, we don't own it | Standards (MCP, A2A) |
| **Absorb pattern** | Take the idea, write our own | mem0 triple-store, DBOS decorators |
| **Vendor** | Fork/embed source, maintain ourselves | Loro (Rust), Reticulum (Python) |
| **Depend** | npm/pip dependency, don't fork | libp2p, LlamaIndex, WXT |
| **Skip** | License/philosophy/dead | Inngest, CJDNS, ZeroTier, AutoGen |

---

## Layer 1: Protocols (IMPLEMENT)

| Protocol | Owner | License | Version | Strategy | Notes |
|----------|-------|---------|---------|----------|-------|
| MCP | Anthropic → AAIF/Linux Foundation | MIT | 2025-11-25 (v2.0 Q1'26) | Implement | 97M+/mo downloads. Universal tool/resource protocol. |
| A2A | Google → AAIF | Apache 2.0 | v0.3.0 (v1.0 Q1'26) | Implement | Agent↔agent coordination. Complements MCP. |
| OpenAI Responses API | OpenAI | Proprietary (SDKs: MIT) | v1 (Mar 2025) | Abstract behind bridge | API = service. SDK = absorbable. |

**Rhea status:** rhea_bridge.py already abstracts 6 providers. MCP/A2A = new protocol layers on top.

## Layer 2: Durable Execution (ABSORB PATTERN → DEPEND)

| Project | License | Architecture | Strategy | Notes |
|---------|---------|-------------|----------|-------|
| **DBOS** | MIT | Decorators + Postgres | Absorb pattern | Lightest. `@DBOS.workflow()` decorator model fits our Python. |
| **Hatchet** | MIT | DAG + durable event log | Depend (growth) | When we need distributed workers. |
| **Temporal** | MIT | Event sourcing + replay | Depend (scale) | 9.1T actions. Planet-scale growth path. |
| Inngest | SSPL | Event-driven steps | **Skip** | SSPL kills MIT product. |
| Restate | BSL server | Command log | **Skip** | BSL server. SDKs MIT but server is core. |
| CrewAI | MIT | Multi-agent | **Skip** | No real durability. |
| AutoGen | MIT | Multi-agent chat | **Skip** | Maintenance mode. Dying. |

**Rhea status:** governor + task_queue checkpoint but don't journal side effects. DBOS pattern = minimal upgrade.
**Key insight:** Checkpoints ≠ durable execution. True durable = journal BEFORE execute + deterministic replay.

## Layer 3: Memory (ABSORB PATTERN — already building)

| Project | License | Memory Model | Strategy | Notes |
|---------|---------|-------------|----------|-------|
| **mem0** | Apache 2.0 | Triple-store (vector+graph+KV) | Absorb architecture | 41k★. OpenMemory MCP = local-first. |
| **Letta** | Apache 2.0 | OS-like (RAM/disk/recall) | Absorb self-manage pattern | Agent decides what to remember. |
| **Graphiti/Zep** | Apache 2.0 | Temporal knowledge graph | Absorb temporal layer | Only system with belief evolution tracking. |
| **LangGraph** | MIT | Checkpoints + MemoryStore | Absorb checkpoint model | 25k★. Time-travel debugging. |
| Motorhead | Apache 2.0 | Sliding window | **Skip** | Dead. Pattern trivial. |

**Winning architecture (4-tier):**
1. Working memory (in-context, agent-managed) — Letta pattern
2. Episodic memory (checkpoints, time-travel) — LangGraph pattern
3. Semantic memory (vector search, facts) — mem0 pattern
4. Temporal memory (knowledge graph, belief evolution) — Graphiti pattern

**Rhea status:** proof.db (semantic) + tasks.db (episodic) + MongoDB (temporal candidate) + governor (working). ~60% there. Need: formalize tiers, add graph layer, add self-manage.

## Layer 4: Sync (VENDOR or DEPEND)

| Project | License | Type | Language | Strategy | Notes |
|---------|---------|------|----------|----------|-------|
| **Loro** | MIT | CRDT (Replayable Event Graph) | Rust+WASM+Swift | Vendor Rust core | Fastest. Movable tree. Shallow snapshots. |
| **Yjs** | MIT | CRDT (YATA) | JS | Depend | 900k+/wk npm. Battle-tested. JS-only. |
| **Automerge** | MIT | CRDT (OpSet) | Rust+WASM+Swift+Go+Python | Depend | v3 10x memory cut. Multi-lang. |
| **ElectricSQL** | Apache 2.0 | Postgres sync | Elixir+TS | Depend | Shape-based sync. 100x faster writes v1.1. |
| **TinyBase** | MIT | Reactive store+CRDT | TS | Depend | 5.5kB. Zero deps. Glue layer. |
| Liveblocks | AGPL server | WebSocket+Yjs | TS | **Skip** | AGPL kills self-hosting. |
| Replicache | Proprietary | Client sync | TS | **Skip** | Dead. Team pivoted to Zero. |

**Rhea status:** No CRDT layer yet. Priority: Loro for cross-device agent state sync.

## Layer 5: Cross-Browser Extension (DEPEND)

| Framework | License | Browsers | Strategy | Notes |
|-----------|---------|----------|----------|-------|
| **WXT** | MIT | Chrome+Firefox+Edge+Safari+all Chromium | **Depend** | Winner. Vite. 9.3k★. Framework-agnostic. |
| Plasmo | MIT | Same minus Safari ease | **Skip** | Maintenance mode. Parcel drag. |
| Extension.js | MIT | No Safari | **Skip** | Smaller ecosystem. |

**Pipeline:** WXT → Chrome/Firefox/Edge + Apple converter → Safari iOS/macOS. Firefox Android = free.
**Not possible:** Chrome Android (Google blocks extensions on mobile).

**Rhea status:** No extension yet. WXT = day-1 choice.

## Layer 6: Mesh Networks (DEPEND + VENDOR)

| Network | License | Language | Strategy | Notes |
|---------|---------|----------|----------|-------|
| **Reticulum** | MIT | Python | Vendor/depend | Zero infrastructure. LoRa/WiFi/radio/TCP. Crypto built-in. |
| **libp2p** | MIT+Apache 2.0 | Go/Rust/JS | Depend | IPFS/Ethereum battle-tested. Pubsub+DHT. Planetary scale. |
| Tailscale/Headscale | BSD | Go | Depend (already using) | Private mesh. Not true P2P (star topology). |
| Yggdrasil | LGPLv3 | Go | **Caution** | LGPLv3 requires linking care. |
| CJDNS | GPLv3 | C | **Skip** | GPL incompatible. Dormant. |
| ZeroTier | BSL | C++ | **Skip** | BSL restricts commercial. |
| I2P | Mixed | Java | **Skip** | Complex, Java overhead. |

**Rhea status:** Tailscale in Fly.io container. Reticulum = next layer for true mesh.

## Layer 7: RAG (DEPEND)

| Framework | License | Strategy | Notes |
|-----------|---------|----------|-------|
| **R2R** | MIT | Depend | Production RAG backend. Auth, multi-tenancy, Deep Research. |
| **GraphRAG** | MIT | Absorb pattern | Microsoft. Knowledge graph RAG. LazyGraphRAG = no upfront cost. |
| **LlamaIndex** | MIT | Depend (connectors) | 350+ data connectors. Workflow engine. |
| **RAGFlow** | Apache 2.0 | Depend (PDF) | Best PDF/table parsing. 30k★. |
| LangChain | MIT | Depend (selective) | Largest community. Use LangGraph, skip chains. |

**Rhea status:** Aletheia does proof chains + RAG. Needs: graph layer (GraphRAG pattern), better PDF parsing (RAGFlow).

## Layer 8: Orchestration (DEPEND)

| SDK | License | Strategy | Notes |
|-----|---------|----------|-------|
| **OpenAI Agents SDK** | MIT | Depend | Lightweight multi-agent + native MCP. 19k★. |
| **LangGraph** | MIT | Depend | Agent graphs + persistence. 25k★. 90M/mo downloads. |
| **Dapr Agents** | Apache 2.0 | Depend (K8s path) | CNCF. Actor model. |

**Rhea status:** office.py + task_queue.py = custom orchestration. Agents SDK / LangGraph = formalization path.

---

## What Rhea Already Has (vs This Map)

| Layer | Industry Standard | Rhea Equivalent | Gap |
|-------|------------------|-----------------|-----|
| Protocols | MCP + A2A | rhea_bridge (6 providers) | Need MCP/A2A protocol support |
| Durable | DBOS/Temporal | governor + task_queue | No side-effect journaling |
| Memory | mem0 4-tier | proof.db + tasks.db + Mongo | Need formalized tiers + graph |
| Sync | Loro/CRDT | Git + file-based | No real-time CRDT |
| Extension | WXT | Atlas (Next.js web) | No browser extension |
| Mesh | Reticulum + libp2p | Tailscale on Fly.io | No true P2P mesh |
| RAG | R2R + GraphRAG | Aletheia RAG | Needs graph + PDF parsing |
| Orchestration | Agents SDK + LangGraph | office.py custom | Works but not standard |

**Bottom line:** Rhea is ~40% there with custom implementations. Formalization path = adopt standards where they exist, keep custom where we're ahead (memory model, agent personality, proof chains).

---

## Next Steps (Priority Order)
1. WXT browser extension skeleton (cross-browser from day 1)
2. MCP server implementation (expose Rhea tools via MCP)
3. DBOS decorator layer on governor/task_queue
4. Loro CRDT for cross-device state sync
5. Reticulum mesh layer for agent-to-agent
6. GraphRAG pattern in Aletheia
7. A2A protocol for external agent interop

## Maintainers Philosophy Study (TODO)
> "чтобы понять: абсорбировать или следовать — требуется изучить maintainers team и их философию"
- [ ] WXT maintainers + community governance
- [ ] Loro team (Rust CRDT — who are they?)
- [ ] DBOS team (ex-MIT CSAIL?)
- [ ] Reticulum (Mark Qvist — solo or team?)
- [ ] mem0 team ($24M YC Series A — VC pressure?)
