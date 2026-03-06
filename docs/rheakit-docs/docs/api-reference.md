---
sidebar_position: 12
title: API Reference
---

# API Reference

All public types and key APIs exported by RheaKit.

## Core Singletons

### RheaAPI

```swift
public final class RheaAPI: @unchecked Sendable {
    public static let shared: RheaAPI

    // Transport
    public func get(_ path: String, auth: Bool = false) async throws -> Data
    public func post(_ path: String, body: Encodable, auth: Bool = true) async throws -> Data
    public func getJSON(_ path: String, auth: Bool = false) async throws -> [String: Any]

    // Typed endpoints
    public func health() async throws -> HealthSnapshot
    public func agents() async throws -> [AgentDTO]
    public func history(limit: Int = 50) async throws -> [[String: Any]]
    public func radio(limit: Int = 100) async throws -> [[String: Any]]
    public func office(limit: Int = 50) async throws -> [[String: Any]]
    public func proofs() async throws -> [[String: Any]]
    public func ontologies() async throws -> [[String: Any]]
    public func ontologyDetail(_ name: String) async throws -> [[String: Any]]
    public func models() async throws -> InfraModels
    public func ndi() async throws -> [String: Any]
    public func sessions(limit: Int = 20) async throws -> [[String: Any]]

    // Wallet
    public func walletStatus() async throws -> [[String: Any]]
    public func walletBalance(chain: String) async throws -> [String: Any]

    // Supervisor
    public func supervisorSessions() async throws -> [SupervisorSession]
    public func supervisorSpawn(agent: String, prompt: String? = nil) async throws -> [String: Any]
    public func supervisorKill(sessionId: String) async throws -> [String: Any]
    public func supervisorOutput(sessionId: String, lines: Int = 50) async throws -> String
    public func supervisorInput(sessionId: String, text: String) async throws -> [String: Any]
    public func wakeAgent(_ agent: String) async throws -> [String: Any]

    // Governor
    public func governorAll() async throws -> [String: GovernorAgentStatus]
    public func governor(agent: String) async throws -> GovernorAgentStatus

    // Settings
    public func executionProfile() async throws -> [String: Any]
    public func setExecutionProfile(_ profile: String) async throws -> [String: Any]

    // NDI
    public func ndiDiscover() async throws -> [NDISource]
    public func ndiSendTest() async throws -> [String: Any]

    // API key management
    public var apiKey: String { get }
    public func setAPIKey(_ key: String)
    public var baseURL: String { get }
}
```

### RheaStore

```swift
@MainActor
public final class RheaStore: ObservableObject {
    public static let shared: RheaStore

    // Core state (polled)
    @Published public var agents: [AgentDTO]
    @Published public var health: HealthSnapshot?
    @Published public var connectionAlive: Bool
    @Published public var proofCount: Int

    // Derived
    public var totalTokens: Int
    public var totalCost: Double
    public var aliveCount: Int
    public var familyOnline: Bool

    // Agent lookup
    public private(set) var agentMap: OrderedDictionary<String, AgentDTO>

    // Lifecycle
    public func startPolling(interval: TimeInterval = 5)
    public func stopPolling()
    public func refreshCore() async

    // On-demand refresh
    public func refreshHistory(limit: Int = 50) async -> [[String: Any]]
    public func refreshRadio(limit: Int = 100) async -> [[String: Any]]
    public func refreshProofs() async -> [[String: Any]]
    public func refreshOntologies() async -> [[String: Any]]
    public func refreshOffice(limit: Int = 50) async -> [[String: Any]]
    public func refreshSessions(limit: Int = 20) async -> [[String: Any]]

    // Staleness
    public func age(_ key: String) -> TimeInterval

    // Helpers
    public func formatTokens(_ n: Int) -> String

    // Local DB
    public let db: DatabaseQueue?
}
```

### AuthManager

```swift
public class AuthManager: ObservableObject {
    public static let shared: AuthManager

    @Published public var token: String?
    @Published public var email: String?
    @Published public var plan: String
    @Published public var queriesUsed: Int
    @Published public var queryLimit: Int
    @Published public var didSkipAuth: Bool

    public var isLoggedIn: Bool

    public func save(token: String, email: String)
    public func logout()
    public func skipLogin()
    public func authorize(_ request: inout URLRequest)
}
```

## Data Types

### AgentDTO

```swift
public struct AgentDTO: Codable, Identifiable {
    public let name: String
    public let alive: Bool
    public let pace: String              // "green", "yellow", "red"
    public let mode: String              // "normal", "compact", "critical", "hard_fail"
    public let billing_mode: String?
    public let T_day: Int                // tokens consumed today
    public let dollar_day: Double        // cost today
    public let floor_gap: Int
    public let office_status: String?
    public let pending_msgs: Int?
    public let tasks_open: Int?
    public let tasks_claimed: Int?
    public let last_activity: String?
    public let last_feed: String?
    public let lease_token: Int?
    public let lease_expired: Bool?
    public let lease_expires_at: String?
    public let forecast: String?
    public let budget_cap: Double?
    public let budget_remaining: Double?
    public let hard_fail: Bool?
}
```

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

### Other DTOs

| Type | Description |
|---|---|
| `SupervisorSession` | Agent process session with id, status, pid |
| `GovernorAgentStatus` | Governor-specific: pace, forecast, budget_cap, compliance |
| `InfraModels` | Provider list with availability and model counts |
| `NDISource` | Network Device Interface source (name, url) |
| `FeedItem` | Radio feed message (sender, receiver, text, ts) |
| `TaskItem` | Task with priority, status, agent, tags |
| `ChatMsg` | Dialog message with sender, text, timestamp |
| `ClipEntry` | Clipboard entry with privacy, device, expiry |
| `PipelineNode` | Node editor graph node with type, position, connections |
| `NodeType` | Enum: input, tribunal, sceptic, filter, proof, output |

## View Modifier

### GlassCard

```swift
public struct GlassCard: ViewModifier { ... }

// Usage
myView.glassCard()
```

## Theme

### RheaTheme

```swift
public enum RheaTheme {
    static let bg: Color
    static let card: Color
    static let cardBorder: Color
    static let accent: Color
    static let green: Color
    static let amber: Color
    static let red: Color
    static let purple: Color
    static let muted: Color
    static let text: Color

    static func modeColor(_ mode: String) -> Color
    static func paceColor(_ pace: String) -> Color
    static func priorityColor(_ priority: String) -> Color
    static func statusColor(_ status: String) -> Color
}
```

## Configuration

### AppConfig

```swift
public enum AppConfig {
    static let productionAPIBaseURL: String  // "https://rhea-tribunal.fly.dev"
    static var defaultAtlasBaseURL: String   // auto: localhost:3000 or production
    static var defaultAPIBaseURL: String     // auto: localhost:8400 or production
    static func migrateStaleDefaults()       // fix saved localhost URLs on device
}
```
