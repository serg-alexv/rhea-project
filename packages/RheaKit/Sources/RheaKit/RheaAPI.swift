import Foundation
import KeychainAccess

/// Shared HTTP client for all Rhea API communication.
/// Single source of truth for base URL, auth headers, timeouts.
/// Every pane talks through this — no more independent URLSession calls.
public final class RheaAPI: @unchecked Sendable {
    public static let shared = RheaAPI()

    private let keychain = Keychain(service: "com.rhea.api")

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 30
        return URLSession(configuration: config)
    }()

    public init() {}

    /// API key: reads from Keychain, falls back to dev-bypass for local dev.
    public var apiKey: String {
        (try? keychain.get("api-key")) ?? "dev-bypass"
    }

    public func setAPIKey(_ key: String) {
        try? keychain.set(key, key: "api-key")
    }

    /// Attach auth to a request: prefer JWT Bearer, fall back to API key.
    private func applyAuth(_ request: inout URLRequest) {
        if let jwt = AuthManager.shared.token {
            request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        } else {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
    }

    public var baseURL: String {
        UserDefaults.standard.string(forKey: "apiBaseURL")
            ?? AppConfig.defaultAPIBaseURL
    }

    // MARK: - Core Transport

    public func get(_ path: String, auth: Bool = false) async throws -> Data {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw RheaAPIError.invalidURL(path)
        }
        var request = URLRequest(url: url)
        if auth {
            applyAuth(&request)
        }
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw RheaAPIError.http(code, path)
        }
        return data
    }

    public func post(_ path: String, body: Encodable, auth: Bool = true) async throws -> Data {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw RheaAPIError.invalidURL(path)
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if auth {
            applyAuth(&request)
        }
        request.httpBody = try JSONEncoder().encode(body)
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw RheaAPIError.http(code, path)
        }
        return data
    }

    public func getJSON(_ path: String, auth: Bool = false) async throws -> [String: Any] {
        let data = try await get(path, auth: auth)
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw RheaAPIError.decode(path)
        }
        return json
    }

    // MARK: - Typed Endpoints (SQL-backed, survives restarts)

    public func health() async throws -> HealthSnapshot {
        let data = try await get("/health")
        return try JSONDecoder().decode(HealthSnapshot.self, from: data)
    }

    public func agents() async throws -> [AgentDTO] {
        let data = try await get("/agents/status")
        struct Resp: Codable { let agents: [String: AgentDTO] }
        let resp = try JSONDecoder().decode(Resp.self, from: data)
        return resp.agents.values.sorted { $0.name < $1.name }
    }

    /// SQL-backed: survives cloud restarts
    public func history(limit: Int = 50) async throws -> [[String: Any]] {
        let json = try await getJSON("/cc/history?limit=\(limit)")
        return json["history"] as? [[String: Any]] ?? []
    }

    /// SQL-backed: survives cloud restarts
    public func radio(limit: Int = 100) async throws -> [[String: Any]] {
        let json = try await getJSON("/cc/radio?limit=\(limit)")
        return json["radio"] as? [[String: Any]] ?? []
    }

    /// SQL-backed: office messages between agents
    public func office(limit: Int = 50) async throws -> [[String: Any]] {
        let json = try await getJSON("/cc/office?limit=\(limit)")
        return json["office"] as? [[String: Any]] ?? []
    }

    /// SQL-backed: proof.db, immutable once written
    public func proofs() async throws -> [[String: Any]] {
        let json = try await getJSON("/aletheia/proofs")
        return json["proofs"] as? [[String: Any]] ?? []
    }

    public func ontologies() async throws -> [[String: Any]] {
        let json = try await getJSON("/ontology")
        return json["ontologies"] as? [[String: Any]] ?? []
    }

    public func ontologyDetail(_ name: String) async throws -> [[String: Any]] {
        let json = try await getJSON("/ontology/\(name)")
        return json["hypotheses"] as? [[String: Any]] ?? []
    }

    public func models() async throws -> InfraModels {
        let data = try await get("/models", auth: true)
        return try JSONDecoder().decode(InfraModels.self, from: data)
    }

    public func ndi() async throws -> [String: Any] {
        return try await getJSON("/cc/ndi", auth: true)
    }

    public func sessions(limit: Int = 20) async throws -> [[String: Any]] {
        let json = try await getJSON("/cc/sessions?limit=\(limit)")
        return json["sessions"] as? [[String: Any]] ?? []
    }

    // MARK: - Wallet

    public func walletStatus() async throws -> [[String: Any]] {
        let json = try await getJSON("/wallet/status")
        return json["wallets"] as? [[String: Any]] ?? []
    }

    public func walletBalance(chain: String) async throws -> [String: Any] {
        return try await getJSON("/wallet/balance/\(chain)")
    }

    // MARK: - Supervisor (process management)

    public func supervisorSessions() async throws -> [SupervisorSession] {
        let data = try await get("/supervisor/sessions", auth: true)
        return (try? JSONDecoder().decode([SupervisorSession].self, from: data)) ?? []
    }

    public func supervisorSpawn(agent: String, prompt: String? = nil) async throws -> [String: Any] {
        struct Body: Encodable { let agent: String; let prompt: String? }
        let data = try await post("/supervisor/spawn", body: Body(agent: agent, prompt: prompt))
        return (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
    }

    public func supervisorKill(sessionId: String) async throws -> [String: Any] {
        struct Body: Encodable { let confirm: Bool }
        let data = try await post("/supervisor/kill/\(sessionId)", body: Body(confirm: true))
        return (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
    }

    public func supervisorOutput(sessionId: String, lines: Int = 50) async throws -> String {
        let json = try await getJSON("/supervisor/output/\(sessionId)?lines=\(lines)", auth: true)
        return json["output"] as? String ?? ""
    }

    public func supervisorInput(sessionId: String, text: String) async throws -> [String: Any] {
        struct Body: Encodable { let text: String }
        let data = try await post("/supervisor/input/\(sessionId)", body: Body(text: text))
        return (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
    }

    public func wakeAgent(_ agent: String) async throws -> [String: Any] {
        struct Body: Encodable { let wake: Bool }
        let data = try await post("/agents/wake/\(agent)", body: Body(wake: true))
        return (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
    }

    // MARK: - Models & Execution Profile

    public func executionProfile() async throws -> [String: Any] {
        return try await getJSON("/settings/execution-profile", auth: true)
    }

    public func setExecutionProfile(_ profile: String) async throws -> [String: Any] {
        struct Body: Encodable { let profile: String }
        let data = try await post("/settings/execution-profile", body: Body(profile: profile))
        return (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
    }

    public func governorAll() async throws -> [String: GovernorAgentStatus] {
        let data = try await get("/governor", auth: false)
        return (try? JSONDecoder().decode([String: GovernorAgentStatus].self, from: data)) ?? [:]
    }

    public func governor(agent: String) async throws -> GovernorAgentStatus {
        let data = try await get("/governor/\(agent)", auth: false)
        return try JSONDecoder().decode(GovernorAgentStatus.self, from: data)
    }

    // MARK: - NDI (Network Device Interface)

    public func ndiDiscover() async throws -> [NDISource] {
        let data = try await get("/cc/ndi/discover", auth: true)
        return (try? JSONDecoder().decode(NDIDiscoverResponse.self, from: data))?.sources ?? []
    }

    public func ndiSendTest() async throws -> [String: Any] {
        struct Body: Encodable { let pattern: String }
        let data = try await post("/cc/ndi/send-test", body: Body(pattern: "color_bars"))
        return (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
    }
}

// MARK: - Shared DTOs (response types that survive restarts)

public struct HealthSnapshot: Codable {
    public let status: String
    public let providers_available: Int
    public let providers_total: Int
    public let total_models: Int
    public let execution_profile: String
    public let analyzer_version: String
    public let profile_mode: String

    public init(status: String, providers_available: Int, providers_total: Int, total_models: Int, execution_profile: String, analyzer_version: String, profile_mode: String) {
        self.status = status
        self.providers_available = providers_available
        self.providers_total = providers_total
        self.total_models = total_models
        self.execution_profile = execution_profile
        self.analyzer_version = analyzer_version
        self.profile_mode = profile_mode
    }
}

public struct InfraModels: Codable {
    public let providers: [ProviderInfo]?
    public let total_models: Int?

    public init(providers: [ProviderInfo]?, total_models: Int?) {
        self.providers = providers
        self.total_models = total_models
    }

    public struct ProviderInfo: Codable, Identifiable {
        public var id: String { name }
        public let name: String
        public let available: Bool?
        public let model_count: Int?
        public let tier: String?

        public init(name: String, available: Bool?, model_count: Int?, tier: String?) {
            self.name = name
            self.available = available
            self.model_count = model_count
            self.tier = tier
        }
    }
}

// MARK: - Supervisor DTOs

public struct SupervisorSession: Codable, Identifiable {
    public let id: String
    public let agent: String?
    public let status: String?
    public let started_at: String?
    public let pid: Int?

    public var isAlive: Bool {
        status?.lowercased() == "running" || status?.lowercased() == "active"
    }

    public var stateColor: String {
        switch status?.lowercased() {
        case "running", "active": return "green"
        case "stopped", "killed": return "red"
        case "idle", "suspended": return "amber"
        default: return "secondary"
        }
    }

    public init(id: String, agent: String?, status: String?, started_at: String?, pid: Int?) {
        self.id = id
        self.agent = agent
        self.status = status
        self.started_at = started_at
        self.pid = pid
    }
}

// MARK: - Governor DTOs

public struct GovernorAgentStatus: Codable {
    public let pace: String?
    public let forecast: String?
    public let mode: String?
    public let T_day: Int?
    public let dollar_day: Double?
    public let compliance: String?
    public let budget_cap: Double?
    public let floor: Int?

    public init(pace: String?, forecast: String?, mode: String?, T_day: Int?, dollar_day: Double?, compliance: String?, budget_cap: Double?, floor: Int?) {
        self.pace = pace
        self.forecast = forecast
        self.mode = mode
        self.T_day = T_day
        self.dollar_day = dollar_day
        self.compliance = compliance
        self.budget_cap = budget_cap
        self.floor = floor
    }
}

// MARK: - NDI DTOs

public struct NDISource: Codable, Identifiable {
    public var id: String { name }
    public let name: String
    public let url: String?

    public init(name: String, url: String?) {
        self.name = name
        self.url = url
    }
}

public struct NDIDiscoverResponse: Codable {
    public let sources: [NDISource]?

    public init(sources: [NDISource]?) {
        self.sources = sources
    }
}

// MARK: - Errors

public enum RheaAPIError: Error, CustomStringConvertible {
    case invalidURL(String)
    case http(Int, String)
    case decode(String)

    public var description: String {
        switch self {
        case .invalidURL(let path): return "Invalid URL: \(path)"
        case .http(let code, let path): return "HTTP \(code) on \(path)"
        case .decode(let path): return "Decode failed: \(path)"
        }
    }
}
