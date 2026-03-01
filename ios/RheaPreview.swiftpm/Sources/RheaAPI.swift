import Foundation
import KeychainAccess

/// Shared HTTP client for all Rhea API communication.
/// Single source of truth for base URL, auth headers, timeouts.
/// Every pane talks through this — no more independent URLSession calls.
final class RheaAPI: @unchecked Sendable {
    static let shared = RheaAPI()

    private let keychain = Keychain(service: "com.rhea.api")

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 30
        return URLSession(configuration: config)
    }()

    /// API key: reads from Keychain, falls back to dev-bypass for local dev.
    var apiKey: String {
        (try? keychain.get("api-key")) ?? "dev-bypass"
    }

    func setAPIKey(_ key: String) {
        try? keychain.set(key, key: "api-key")
    }

    var baseURL: String {
        UserDefaults.standard.string(forKey: "apiBaseURL")
            ?? AppConfig.defaultAPIBaseURL
    }

    // MARK: - Core Transport

    func get(_ path: String, auth: Bool = false) async throws -> Data {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw RheaAPIError.invalidURL(path)
        }
        var request = URLRequest(url: url)
        if auth {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw RheaAPIError.http(code, path)
        }
        return data
    }

    func post(_ path: String, body: Encodable, auth: Bool = true) async throws -> Data {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw RheaAPIError.invalidURL(path)
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if auth {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
        request.httpBody = try JSONEncoder().encode(body)
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw RheaAPIError.http(code, path)
        }
        return data
    }

    func getJSON(_ path: String, auth: Bool = false) async throws -> [String: Any] {
        let data = try await get(path, auth: auth)
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw RheaAPIError.decode(path)
        }
        return json
    }

    // MARK: - Typed Endpoints (SQL-backed, survives restarts)

    func health() async throws -> HealthSnapshot {
        let data = try await get("/health")
        return try JSONDecoder().decode(HealthSnapshot.self, from: data)
    }

    func agents() async throws -> [AgentDTO] {
        let data = try await get("/agents/status")
        struct Resp: Codable { let agents: [String: AgentDTO] }
        let resp = try JSONDecoder().decode(Resp.self, from: data)
        return resp.agents.values.sorted { $0.name < $1.name }
    }

    /// SQL-backed: survives cloud restarts
    func history(limit: Int = 50) async throws -> [[String: Any]] {
        let json = try await getJSON("/cc/history?limit=\(limit)", auth: true)
        return json["history"] as? [[String: Any]] ?? []
    }

    /// SQL-backed: survives cloud restarts
    func radio(limit: Int = 100) async throws -> [[String: Any]] {
        let json = try await getJSON("/cc/radio?limit=\(limit)", auth: true)
        return json["radio"] as? [[String: Any]] ?? []
    }

    /// SQL-backed: proof.db, immutable once written
    func proofs() async throws -> [[String: Any]] {
        let json = try await getJSON("/aletheia/proofs")
        return json["proofs"] as? [[String: Any]] ?? []
    }

    func ontologies() async throws -> [[String: Any]] {
        let json = try await getJSON("/ontology")
        return json["ontologies"] as? [[String: Any]] ?? []
    }

    func ontologyDetail(_ name: String) async throws -> [[String: Any]] {
        let json = try await getJSON("/ontology/\(name)")
        return json["hypotheses"] as? [[String: Any]] ?? []
    }

    func models() async throws -> InfraModels {
        let data = try await get("/models", auth: true)
        return try JSONDecoder().decode(InfraModels.self, from: data)
    }

    func ndi() async throws -> [String: Any] {
        return try await getJSON("/cc/ndi", auth: true)
    }

    func sessions(limit: Int = 20) async throws -> [[String: Any]] {
        let json = try await getJSON("/cc/sessions?limit=\(limit)", auth: true)
        return json["sessions"] as? [[String: Any]] ?? []
    }
}

// MARK: - Shared DTOs (response types that survive restarts)

struct HealthSnapshot: Codable {
    let status: String
    let providers_available: Int
    let providers_total: Int
    let total_models: Int
    let execution_profile: String
    let analyzer_version: String
    let profile_mode: String
}

struct InfraModels: Codable {
    let providers: [ProviderInfo]?
    let total_models: Int?

    struct ProviderInfo: Codable, Identifiable {
        var id: String { name }
        let name: String
        let available: Bool?
        let model_count: Int?
        let tier: String?
    }
}

// MARK: - Errors

enum RheaAPIError: Error, CustomStringConvertible {
    case invalidURL(String)
    case http(Int, String)
    case decode(String)

    var description: String {
        switch self {
        case .invalidURL(let path): return "Invalid URL: \(path)"
        case .http(let code, let path): return "HTTP \(code) on \(path)"
        case .decode(let path): return "Decode failed: \(path)"
        }
    }
}
