---
sidebar_position: 11
title: Architecture
---

# Architecture

RheaKit follows a layered architecture: views observe shared state, shared state is populated by a single API client, and the API client handles auth and transport.

## Layer Diagram

```
┌──────────────────────────────────────────────────────┐
│                    SwiftUI Views                     │
│  TeamChat · Governor · Tasks · Bio · Dialog · ...    │
├──────────────────────────────────────────────────────┤
│                    RheaStore                          │
│  @MainActor · @Published · GRDB local cache          │
│  Polling: agents, health, proofCount (every 5s)      │
│  On-demand: history, radio, proofs, ontologies       │
├──────────────────────────────────────────────────────┤
│                    RheaAPI                            │
│  Singleton HTTP client · URLSession                  │
│  JWT Bearer + API-key fallback · Typed DTOs          │
├──────────────────────────────────────────────────────┤
│                   AuthManager                        │
│  Keychain-backed JWT · Sign in with Apple            │
│  Skip-login mode for dev · Profile fetch             │
├──────────────────────────────────────────────────────┤
│                  Rhea Backend                        │
│  Fly.io (prod) · localhost:8400 (dev)                │
│  SQL-backed endpoints · In-memory governor state     │
└──────────────────────────────────────────────────────┘
```

## RheaStore — The Shared Brain

`RheaStore` is a `@MainActor` singleton `ObservableObject` that serves as the single source of truth for the entire UI.

### Data Tiers

| Tier | What | Refresh |
|---|---|---|
| **Core** (polled every 5s) | Agents, health, proof count | Automatic timer |
| **On-demand** | History, radio, proofs, ontologies, sessions, office | Fetched when pane opens |
| **Ephemeral** | SSE streams, active dialog | Never cached |

### Derived Metrics

```swift
var totalTokens: Int    // sum of all agents' T_day
var totalCost: Double   // sum of all agents' dollar_day
var aliveCount: Int     // count of agents where alive == true
var familyOnline: Bool  // true if all agents are alive
```

### Staleness Tracking

Every data type records its last fetch time. Views can check `store.age("proofs")` to decide whether to trigger a refresh.

### Connection Recovery

When connection is restored after an outage, RheaStore performs a recovery triage modeled on cellular stress response:

1. **Membrane** — Server alive (confirmed by successful agent fetch)
2. **Core metabolism** — Refresh SQL-backed data: proofs, history, radio, office
3. **Clear damaged** — Governor counters reset to 0 on restart (the zero IS truth)
4. **Resume** — Normal polling takes over

## RheaAPI — HTTP Transport

`RheaAPI` provides typed methods for every backend endpoint:

| Method | Endpoint | Returns |
|---|---|---|
| `health()` | `GET /health` | `HealthSnapshot` |
| `agents()` | `GET /agents/status` | `[AgentDTO]` |
| `history()` | `GET /cc/history` | `[[String: Any]]` |
| `radio()` | `GET /cc/radio` | `[[String: Any]]` |
| `proofs()` | `GET /aletheia/proofs` | `[[String: Any]]` |
| `ontologies()` | `GET /ontology` | `[[String: Any]]` |
| `models()` | `GET /models` | `InfraModels` |
| `sessions()` | `GET /cc/sessions` | `[[String: Any]]` |
| `walletStatus()` | `GET /wallet/status` | `[[String: Any]]` |
| `governorAll()` | `GET /governor` | `[String: GovernorAgentStatus]` |
| `supervisorSessions()` | `GET /supervisor/sessions` | `[SupervisorSession]` |

### Error Handling

```swift
public enum RheaAPIError: Error {
    case invalidURL(String)      // malformed path
    case http(Int, String)       // non-2xx response
    case decode(String)          // JSON decode failure
}
```

## AppConfig — Environment Routing

`AppConfig` auto-selects the correct backend:

| Environment | API URL | Atlas URL |
|---|---|---|
| Simulator | `http://localhost:8400` | `http://localhost:3000` |
| Device | `https://rhea-tribunal.fly.dev` | Same as API |

`migrateStaleDefaults()` detects and replaces localhost/LAN URLs saved by older builds when running on a physical device.

## Local Cache (GRDB)

`RheaStore` maintains a local SQLite database via GRDB for offline access:

```sql
CREATE TABLE cached_proofs (
    id TEXT PRIMARY KEY,
    claim TEXT NOT NULL,
    tier TEXT,
    agreement_score REAL,
    confidence REAL,
    created_at TEXT,
    data TEXT
);

CREATE TABLE cached_history (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,
    prompt TEXT NOT NULL,
    agreement_score REAL,
    created_at TEXT,
    data TEXT
);
```

This mirrors the server's `rhea.db`, allowing the app to display data even when offline.
