import Foundation

/// Lightweight tribunal API client for the keyboard extension.
/// No RheaKit dependency — extensions must stay lean (<30MB).
/// Shares Keychain service with the main app for auth token access.
enum TribunalClient {

    static let apiBaseURL = "https://rhea-tribunal.fly.dev"

    /// Read JWT from shared Keychain (same service as main app).
    /// The main app writes here via KeychainAccess; we read with raw Security framework
    /// to avoid pulling in the full KeychainAccess dependency.
    static var authToken: String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: "com.rhea.preview",
            kSecAttrAccount as String: "jwt_token",
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            return nil
        }
        return token
    }

    // MARK: - Quick Action (single model, fast)

    struct QuickRequest: Encodable {
        let text: String
        let action: String     // translate, rewrite, grammar, summarize, explain, freeform
        let target_lang: String
        let style: String
    }

    struct QuickResponse: Decodable {
        let text: String?
        let model: String?
        let elapsed_s: Double?
        let action: String?
    }

    /// Fast single-model action — translation, rewriting, grammar fix, etc.
    static func quick(text: String, action: String, targetLang: String = "", style: String = "") async throws -> QuickResponse {
        guard let url = URL(string: "\(apiBaseURL)/keyboard/quick") else {
            throw URLError(.badURL)
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15

        if let jwt = authToken {
            request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        } else {
            request.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        }

        let body = QuickRequest(text: text, action: action, target_lang: targetLang, style: style)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw URLError(.init(rawValue: code))
        }

        return try JSONDecoder().decode(QuickResponse.self, from: data)
    }

    // MARK: - Tribunal (multi-model consensus, slower)

    struct TribunalRequest: Encodable {
        let text: String
        let sender: String
    }

    struct TribunalResponse: Decodable {
        let reply: String?
        let agreement_score: Double?
        let models_responded: Int?
        let elapsed_s: Double?
    }

    /// Full tribunal consensus — slower but higher confidence.
    static func tribunal(_ claim: String) async throws -> TribunalResponse {
        guard let url = URL(string: "\(apiBaseURL)/dialog") else {
            throw URLError(.badURL)
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30

        if let jwt = authToken {
            request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        } else {
            request.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        }

        let body = TribunalRequest(text: claim, sender: "keyboard")
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw URLError(.init(rawValue: code))
        }

        return try JSONDecoder().decode(TribunalResponse.self, from: data)
    }
}
