import SwiftUI
import NetworkExtension

/// Privacy & relay configuration.
///
/// Layers:
///   1. DNS-over-HTTPS — encrypts DNS queries (system-level via NEDNSSettingsManager)
///   2. API Relay — routes tribunal queries through encrypted relay endpoint
///   3. VPN — full traffic tunneling via Rhea backend (PacketTunnelProvider + WireGuard)
///
/// No third-party VPN subscriptions. Own infrastructure only.
public struct RelayPrivacyView: View {
    @AppStorage("relayEnabled") private var relayEnabled = false
    @AppStorage("dohProvider") private var dohProvider = "cloudflare"
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    @StateObject private var tunnel = TunnelManager.shared

    @State private var connectionStatus = "Checking..."
    @State private var publicIP = "..."
    @State private var dnsProvider = "..."
    @State private var latencyMs: Int?
    @State private var isChecking = false
    @State private var vpnError: String?

    private let dohProviders: [(id: String, name: String, url: String)] = [
        ("cloudflare", "Cloudflare", "https://1.1.1.1/dns-query"),
        ("google", "Google", "https://dns.google/dns-query"),
        ("quad9", "Quad9", "https://dns.quad9.net:5053/dns-query"),
        ("mullvad", "Mullvad", "https://dns.mullvad.net/dns-query"),
    ]

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    // Status card
                    statusCard

                    // Relay toggle
                    relayCard

                    // DNS-over-HTTPS
                    dnsCard

                    // VPN tunnel
                    vpnCard

                    // Privacy info
                    infoCard
                }
                .padding(16)
            }
            .background(RheaTheme.bg)
            .navigationTitle("Relay")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button { checkStatus() } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(RheaTheme.accent)
                    }
                }
            }
            .task { checkStatus() }
        }
    }

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("CONNECTION")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent)
                Spacer()
                HStack(spacing: 4) {
                    Circle()
                        .fill(connectionStatus == "Connected" ? RheaTheme.green : RheaTheme.amber)
                        .frame(width: 6, height: 6)
                    Text(connectionStatus.uppercased())
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(connectionStatus == "Connected" ? RheaTheme.green : RheaTheme.amber)
                }
            }

            HStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("API")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Text(apiBaseURL.replacingOccurrences(of: "https://", with: ""))
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(.white)
                        .lineLimit(1)
                }
                if let ms = latencyMs {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("LATENCY")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Text("\(ms)ms")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(ms < 200 ? RheaTheme.green : ms < 500 ? RheaTheme.amber : RheaTheme.red)
                    }
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("RELAY")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Text(relayEnabled ? "ON" : "OFF")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(relayEnabled ? RheaTheme.green : .secondary)
                }
            }
        }
        .glassCard()
    }

    private var relayCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "shield.checkerboard")
                    .foregroundStyle(RheaTheme.accent)
                Text("API RELAY")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
                Spacer()
                Toggle("", isOn: $relayEnabled)
                    .labelsHidden()
                    .tint(RheaTheme.accent)
            }
            Text("Route all tribunal queries through encrypted relay. Prevents direct API fingerprinting.")
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
        }
        .glassCard()
    }

    private var dnsCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "network.badge.shield.half.filled")
                    .foregroundStyle(RheaTheme.green)
                Text("DNS PRIVACY")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
            }
            Text("DNS-over-HTTPS provider for encrypted name resolution:")
                .font(.system(size: 11))
                .foregroundStyle(.secondary)

            ForEach(dohProviders, id: \.id) { provider in
                Button {
                    dohProvider = provider.id
                } label: {
                    HStack {
                        Image(systemName: dohProvider == provider.id ? "checkmark.circle.fill" : "circle")
                            .foregroundStyle(dohProvider == provider.id ? RheaTheme.accent : .secondary)
                            .font(.system(size: 14))
                        VStack(alignment: .leading, spacing: 1) {
                            Text(provider.name)
                                .font(.system(size: 12, weight: .semibold, design: .monospaced))
                                .foregroundStyle(.white)
                            Text(provider.url)
                                .font(.system(size: 9, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .glassCard()
    }

    private var vpnCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "shield.lefthalf.filled")
                    .foregroundStyle(tunnel.isConnected ? RheaTheme.green : RheaTheme.accent)
                Text("RHEA VPN")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
                Spacer()
                if tunnel.status == .invalid {
                    Text("NOT CONFIGURED")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                } else {
                    Button {
                        do {
                            try tunnel.toggle()
                            vpnError = nil
                        } catch {
                            vpnError = error.localizedDescription
                        }
                    } label: {
                        Text(tunnel.isConnected ? "DISCONNECT" : "CONNECT")
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 4)
                            .background(
                                RoundedRectangle(cornerRadius: 6)
                                    .fill(tunnel.isConnected ? RheaTheme.red.opacity(0.3) : RheaTheme.green.opacity(0.3))
                            )
                            .foregroundStyle(tunnel.isConnected ? RheaTheme.red : RheaTheme.green)
                    }
                }
            }

            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("STATUS")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    HStack(spacing: 4) {
                        Circle()
                            .fill(tunnel.isConnected ? RheaTheme.green : .secondary)
                            .frame(width: 6, height: 6)
                        Text(tunnel.statusText.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(tunnel.isConnected ? RheaTheme.green : .secondary)
                    }
                }
                if let since = tunnel.connectedSince {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("UPTIME")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Text(since, style: .relative)
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.white)
                    }
                }
            }

            Text("Routes all device traffic through Rhea infrastructure. No third-party VPN. WireGuard protocol.")
                .font(.system(size: 11))
                .foregroundStyle(.secondary)

            if let vpnError {
                Text(vpnError)
                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                    .foregroundStyle(RheaTheme.red)
            }
        }
        .glassCard()
    }

    private var infoCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("PRIVACY LAYERS")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)

            privacyRow(icon: "lock.shield", label: "HTTPS", status: "Always on", color: RheaTheme.green)
            privacyRow(icon: "network", label: "DNS-over-HTTPS", status: dohProvider.capitalized, color: RheaTheme.green)
            privacyRow(icon: "arrow.triangle.branch", label: "API Relay", status: relayEnabled ? "Active" : "Off", color: relayEnabled ? RheaTheme.green : .secondary)
            privacyRow(
                icon: "shield.lefthalf.filled",
                label: "Full VPN",
                status: tunnel.isConnected ? "Active" : tunnel.status == .invalid ? "Setup needed" : "Off",
                color: tunnel.isConnected ? RheaTheme.green : .secondary
            )
        }
        .glassCard()
    }

    private func privacyRow(icon: String, label: String, status: String, color: Color) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 11))
                .foregroundStyle(color)
                .frame(width: 20)
            Text(label)
                .font(.system(size: 11, design: .monospaced))
                .foregroundStyle(.white)
            Spacer()
            Text(status)
                .font(.system(size: 10, weight: .semibold, design: .monospaced))
                .foregroundStyle(color)
        }
    }

    private func checkStatus() {
        isChecking = true
        connectionStatus = "Checking..."

        guard let url = URL(string: "\(apiBaseURL)/health") else {
            connectionStatus = "Invalid URL"
            isChecking = false
            return
        }

        let start = Date()
        var req = URLRequest(url: url)
        req.timeoutInterval = 10
        if let jwt = AuthManager.shared.token {
            req.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        }

        URLSession.shared.dataTask(with: req) { _, response, error in
            DispatchQueue.main.async {
                isChecking = false
                let elapsed = Date().timeIntervalSince(start)
                latencyMs = Int(elapsed * 1000)

                if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                    connectionStatus = "Connected"
                } else if let error = error {
                    connectionStatus = error.localizedDescription
                } else {
                    connectionStatus = "Error"
                }
            }
        }.resume()
    }
}
