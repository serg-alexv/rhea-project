import SwiftUI

public enum AppConfig {
    /// Production Fly.io URL (always reachable from any network).
    public static let productionAPIBaseURL = "https://rhea-tribunal.fly.dev"

    /// Atlas web UI — same origin as API on production, localhost:3000 for local dev only
    public static var defaultAtlasBaseURL: String {
        #if targetEnvironment(simulator)
        return "http://localhost:3000"
        #else
        return productionAPIBaseURL
        #endif
    }

    /// On simulator, localhost works for local dev. On device, use Cloud Run.
    public static var defaultAPIBaseURL: String {
        #if targetEnvironment(simulator)
        return "http://localhost:8400"
        #else
        return productionAPIBaseURL
        #endif
    }

    /// Migrate stale localhost/LAN URLs saved by earlier builds to Cloud Run.
    /// Call once at app launch, before any @AppStorage reads take effect.
    public static func migrateStaleDefaults() {
        let ud = UserDefaults.standard
        if let saved = ud.string(forKey: "apiBaseURL") {
            // Detect localhost or private-network addresses that won't work on device
            let stalePatterns = [
                "localhost",
                "127.0.0.1",
                "192.168.",
                "10.0.",
                "10.1.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
            ]
            #if !targetEnvironment(simulator)
            let isStale = stalePatterns.contains { saved.contains($0) }
            if isStale {
                ud.set(productionAPIBaseURL, forKey: "apiBaseURL")
            }
            #endif
        }
    }
}

