# Rhea Redis Keyspace Schema (REDIS_SCHEMA.md)

**Version:** 1.0.0
**Role:** Authoritative keyspace mapping for multi-agent coordination and DTS (Deterministic Time System) synchronization.

---

## 1. Agent & System State

| Key | Type | Purpose | TTL |
|:----|:-----|:--------|:----|
| `rhea:agent:{id}:status` | HASH | Real-time health, task, and PID of background agents. | 300s (heartbeat) |
| `rhea:system:load` | STRING | Current system load average and memory pressure. | 60s |
| `rhea:state:snapshot` | STRING | Compressed JSON snapshot of the last active context (Compacted Continuity Capsule). | None |

## 2. DTS (Deterministic Time System)

| Key | Type | Purpose | TTL |
|:----|:-----|:--------|:----|
| `rhea:session:{id}:lc` | STRING | Authoritative Lamport Clock (LC) value for a given session. | None |
| `rhea:session:{id}:messages:count` | STRING | Current message count for validation against local database. | None |

## 3. Distributed Resource Management

| Key | Type | Purpose | TTL |
|:----|:-----|:--------|:----|
| `rhea:lock:{resource}` | STRING | Distributed mutex for safe concurrent file/asset modification (e.g., cloud migration). | 600s |
| `rhea:queue:jobs` | LIST | Prioritized background task queue for the `workflow_engine.py`. | None |

## 4. Knowledge & Memory

| Key | Type | Purpose | TTL |
|:----|:-----|:--------|:----|
| `rhea:memory:short_term` | LIST | Last 50 interaction summaries for fast local context retrieval. | 24h |
| `rhea:ontology:cache:{name}` | STRING | Cached fragments of the flow-gradient ontology for faster tribunal lookups. | 7d |

---

**Rules:**
1. All keys MUST be prefixed with `rhea:`.
2. HASH types are preferred for agent status to allow field-level updates (e.g., `last_seen`, `active_task`).
3. Binary data (e.g., compressed snapshots) should be stored as base64-encoded strings or raw bytes if supported by the client.
