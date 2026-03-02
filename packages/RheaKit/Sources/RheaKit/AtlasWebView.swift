import SwiftUI
import WebKit

public struct AtlasView: View {
    @AppStorage("atlasBaseURL") private var atlasBaseURL = AppConfig.defaultAtlasBaseURL

    public init() {}

    public var body: some View {
        #if os(macOS)
        AtlasDashboardView()
        #else
        AtlasWebView(path: "/", baseURL: atlasBaseURL)
        #endif
    }
}

#if os(macOS)
/// Native macOS dashboard replacing the Three.js webview
public struct AtlasDashboardView: View {
    @State private var health: HealthData? = nil
    @State private var proofCount: Int = 0
    @State private var historyCount: Int = 0
    @State private var radioCount: Int = 0
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    public init() {}

    public struct HealthData: Codable {
        public let status: String
        public let providers_available: Int
        public let providers_total: Int
        public let total_models: Int
        public let execution_profile: String
        public let analyzer_version: String
        public let profile_mode: String
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    // System health
                    if let h = health {
                        systemHealthCard(h)
                    } else {
                        ProgressView("Connecting to tribunal...")
                            .frame(maxWidth: .infinity, minHeight: 100)
                    }

                    // Metrics grid
                    HStack(spacing: 12) {
                        metricCard(title: "PROVIDERS", value: "\(health?.providers_available ?? 0)/\(health?.providers_total ?? 0)", icon: "server.rack", color: RheaTheme.green)
                        metricCard(title: "MODELS", value: "\(health?.total_models ?? 0)", icon: "cpu", color: RheaTheme.accent)
                        metricCard(title: "PROOFS", value: "\(proofCount)", icon: "checkmark.seal", color: RheaTheme.amber)
                        metricCard(title: "HISTORY", value: "\(historyCount)", icon: "clock", color: .white)
                    }

                    // API endpoint
                    HStack {
                        Text("API")
                            .font(.system(.caption, design: .monospaced, weight: .bold))
                            .foregroundStyle(.secondary)
                        Text(apiBaseURL)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(RheaTheme.accent)
                            .textSelection(.enabled)
                        Spacer()
                        Circle()
                            .fill(health != nil ? RheaTheme.green : RheaTheme.red)
                            .frame(width: 8, height: 8)
                    }
                    .glassCard()

                    Spacer()
                }
                .padding()
            }
            .background(RheaTheme.bg)
            .navigationTitle("Atlas")
            .task { await fetchAll() }
        }
    }

    func systemHealthCard(_ h: HealthData) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("RHEA TRIBUNAL")
                    .font(.system(.title3, design: .monospaced, weight: .bold))
                    .foregroundStyle(.white)
                Spacer()
                Text(h.status.uppercased())
                    .font(.system(.caption, design: .monospaced, weight: .bold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Capsule().fill(RheaTheme.green.opacity(0.2)))
                    .foregroundStyle(RheaTheme.green)
            }

            HStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Profile").font(.caption2).foregroundStyle(.secondary)
                    Text(h.execution_profile).font(.system(.body, design: .monospaced)).foregroundStyle(.white)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("Analyzer").font(.caption2).foregroundStyle(.secondary)
                    Text(h.analyzer_version).font(.system(.body, design: .monospaced)).foregroundStyle(.white)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("Mode").font(.caption2).foregroundStyle(.secondary)
                    Text(h.profile_mode).font(.system(.body, design: .monospaced)).foregroundStyle(.white)
                }
            }
        }
        .glassCard()
    }

    func metricCard(title: String, value: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(color)
            Text(value)
                .font(.system(.title2, design: .rounded, weight: .bold))
                .foregroundStyle(.white)
            Text(title)
                .font(.system(.caption2, design: .monospaced, weight: .bold))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .glassCard()
    }

    func fetchAll() async {
        // Health
        if let url = URL(string: "\(apiBaseURL)/health") {
            if let (data, _) = try? await URLSession.shared.data(from: url),
               let h = try? JSONDecoder().decode(HealthData.self, from: data) {
                health = h
            }
        }
        // Proof count
        if let url = URL(string: "\(apiBaseURL)/aletheia/proofs") {
            if let (data, _) = try? await URLSession.shared.data(from: url),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let proofs = json["proofs"] as? [[String: Any]] {
                proofCount = proofs.count
            }
        }
        // History count
        var histReq = URLRequest(url: URL(string: "\(apiBaseURL)/cc/history?limit=1000")!)
        histReq.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        if let (data, _) = try? await URLSession.shared.data(for: histReq),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let history = json["history"] as? [[String: Any]] {
            historyCount = history.count
        }
        // Radio count
        var radioReq = URLRequest(url: URL(string: "\(apiBaseURL)/cc/radio?limit=1000")!)
        radioReq.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        if let (data, _) = try? await URLSession.shared.data(for: radioReq),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let radio = json["radio"] as? [[String: Any]] {
            radioCount = radio.count
        }
    }
}
#endif

#if os(iOS)
public struct AtlasWebView: UIViewRepresentable {
    public let path: String
    public let baseURL: String

    public init(path: String, baseURL: String) {
        self.path = path
        self.baseURL = baseURL
    }

    public func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        let webView = WKWebView(frame: .zero, configuration: config)
        if let url = URL(string: baseURL + path) {
            webView.load(URLRequest(url: url))
        }
        return webView
    }

    public func updateUIView(_ webView: WKWebView, context: Context) {}
}
#else
public struct AtlasWebView: NSViewRepresentable {
    public let path: String
    public let baseURL: String

    public init(path: String, baseURL: String) {
        self.path = path
        self.baseURL = baseURL
    }

    public func makeNSView(context: Context) -> WKWebView {
        let webView = WKWebView(frame: .zero)
        if let url = URL(string: baseURL + path) {
            webView.load(URLRequest(url: url))
        }
        return webView
    }

    public func updateNSView(_ webView: WKWebView, context: Context) {}
}
#endif
