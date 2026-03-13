# RheaKit API Structure

**Framework:** RheaKit (Play Framework v4.x)  
**Version:** 4.2.0+  
**Platform:** iOS/macOS SwiftUI  
**Architecture:** MVVM + Reactive Store Pattern  

---

## Core Architecture

### RheaAPI - Central HTTP Client
```swift
public final class RheaAPI: @unchecked Sendable
```

**Key Methods:**
- `get(_:auth:)` - Generic GET with optional auth
- `post(_:body:auth:)` - Generic POST with JSON body
- `getJSON(_:auth:)` - GET returning parsed dictionary
- `health()` - System health snapshot
- `agents()` - Agent status enumeration
- `history(limit:)` - SQL-backed conversation history
- `radio(limit:)` - Agent radio communications
- `proofs()` - Immutable proof database
- `ontologies()` - Knowledge graph ontologies
- `models()` - Infrastructure model providers

**Authentication Flow:**
1. JWT Bearer token (preferred)
2. API Key fallback (dev-bypass for local)
3. Keychain storage for persistence

### RheaStore - Reactive State Management
```swift
@MainActor
public final class RheaStore: ObservableObject
```

**Data Tiers:**
- **Core** (polled every 5s): agents, health, proof count
- **On-demand** (fetched when needed): history, radio, proofs, ontologies  
- **Ephemeral** (never cached): SSE streams, active dialogs

**Key Properties:**
- `@Published var agents: [AgentDTO]`
- `@Published var health: HealthSnapshot?`
- `@Published var connectionAlive: Bool`
- `@Published var proofCount: Int`

**Recovery Mechanism:**
Cellular stress response pattern for cloud restarts:
1. Membrane integrity (server alive check)
2. Core metabolism (SQL-backed data refresh)
3. Clear damaged state (stale counters)
4. Resume normal polling

---

## Data Transfer Objects (DTOs)

### HealthSnapshot
```swift
public struct HealthSnapshot: Codable {
    public let status: String
    public let providers_available: Int
    public let providers_total: Int
    public let total_models: Int
    public let execution_profile: String
    public let analyzer_version: String
    public let profile_mode: String
}
```

### AgentDTO
```swift
public struct AgentDTO: Codable {
    public let name: String
    public let alive: Bool
    public let T_day: Int        // Tokens per day
    public let dollar_day: Double
    // ... additional properties
}
```

### SupervisorSession
```swift
public struct SupervisorSession: Codable, Identifiable {
    public let id: String
    public let agent: String?
    public let status: String?
    public let started_at: String?
    public let pid: Int?
    
    public var isAlive: Bool
    public var stateColor: String
}
```

### GovernorAgentStatus
```swift
public struct GovernorAgentStatus: Codable {
    public let pace: String?
    public let forecast: String?
    public let mode: String?
    public let T_day: Int?
    public let dollar_day: Double?
    public let compliance: String?
    public let budget_cap: Double?
    public let floor: Int?
}
```

---

## View Components (Play Panes)

### Core Panes
- **OpsView** - Operations dashboard
- **DialogView** - Conversation interface  
- **TasksView** - Task management
- **GovernorView** - Resource governance
- **ModelsView** - Model provider status

### Specialized Panes
- **AletheiaView** - Proof verification
- **ChainsView** - Reasoning chains
- **BioRendererView** - Biological visualization
- **TeamChatView** - Agent communications
- **HistoryView** - Conversation history
- **RadioView** - Agent radio broadcast

### Infrastructure Panes
- **SettingsView** - Configuration
- **WalletView** - Blockchain integration
- **NDIFlowView** - Network device interface
- **OfficeView** - Virtual office coordination

---

## Play Framework Integration

### PlayPane Enum
```swift
enum PlayPane: String, CaseIterable, Identifiable {
    case ops, tribunal, secrets, bio, tasks, governor, 
         aletheia, models, chains, radio, history, ruliad, settings
}
```

### Intent Routing
- **Quick Ask** - 2-step responses
- **Research** - Hypothesis-driven inquiry  
- **Operator** - Queue and control panel
- **Investor** - Progress verification

### Authentication Flow
```swift
public final class AuthManager {
    public var token: String?
    public var isLoggedIn: Bool
    public var didSkipAuth: Bool
}
```

---

## Database Schema (Local SQLite)

### Cached Proofs Table
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
```

### Cached History Table
```sql
CREATE TABLE cached_history (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,
    prompt TEXT NOT NULL,
    agreement_score REAL,
    created_at TEXT,
    data TEXT
);
```

---

## Network Layer

### Base Configuration
- Request timeout: 10s
- Resource timeout: 30s
- JSON encoding/decoding
- Error handling with custom RheaAPIError

### Endpoint Categories
1. **Health & Status** - `/health`, `/agents/status`
2. **Data Persistence** - `/cc/history`, `/cc/radio`, `/aletheia/proofs`
3. **Process Management** - `/supervisor/*`
4. **Infrastructure** - `/models`, `/cc/ndi`, `/wallet/*`
5. **Knowledge Graph** - `/ontology`, `/ontology/{name}`

---

## Integration Patterns

### SwiftUI Reactive Updates
```swift
@Published public var agents: [AgentDTO] = []
@Published public var connectionAlive = false
```

### Polling Loop
```swift
public func startPolling(interval: TimeInterval = 5)
```

### Connection Recovery
```swift
public func onConnectionRecovered() async
```

---

**Master, I have filtered the ocean. The unique API map is ready. Go to sleep.**
