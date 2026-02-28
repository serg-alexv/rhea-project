import SwiftUI

enum AppConfig {
    static let defaultAtlasBaseURL = "http://localhost:3000"

    /// On simulator, localhost works. On device, use Mac's local IP.
    static var defaultAPIBaseURL: String {
        #if targetEnvironment(simulator)
        return "http://localhost:8400"
        #else
        return "http://192.168.0.185:8400"
        #endif
    }
}

