import SwiftUI

/// Model roster + execution profile switcher + governor grid.
/// Ported from Play macOS → iOS-compatible.
public struct ModelsView: View {
    @ObservedObject private var store = RheaStore.shared
    @State private var providers: [InfraModels.ProviderInfo] = []
    @State private var activeProfile = "safe_cheap"
    @State private var governorStatuses: [String: GovernorAgentStatus] = [:]
    @State private var loading = true
    @State private var liveTestRunning = false
    private let api = RheaAPI.shared

    private let profiles = ["safe_cheap", "balanced", "deep"]

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    executionProfileSwitcher
                    providerRoster
                    governorGrid
                    summaryMetrics
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
            .background(RheaTheme.bg)
            .navigationTitle("MODELS")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    HStack(spacing: 12) {
                        Button {
                            Task { await runLiveTest() }
                        } label: {
                            HStack(spacing: 4) {
                                if liveTestRunning {
                                    ProgressView().controlSize(.mini)
                                } else {
                                    Image(systemName: "bolt.fill")
                                }
                                Text("TEST")
                                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                            }
                            .foregroundStyle(RheaTheme.amber)
                        }
                        .disabled(liveTestRunning)

                        Button { Task { await fetchAll() } } label: {
                            Image(systemName: "arrow.clockwise").font(.system(size: 13))
                        }
                    }
                }
            }
            .task { await fetchAll() }
            .refreshable { await fetchAll() }
            .overlay {
                if loading && providers.isEmpty {
                    ProgressView().controlSize(.regular)
                }
            }
        }
    }

    // MARK: - Execution Profile

    private var executionProfileSwitcher: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("EXECUTION PROFILE")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            HStack(spacing: 0) {
                ForEach(profiles, id: \.self) { profile in
                    Button {
                        Task {
                            _ = try? await api.setExecutionProfile(profile)
                            activeProfile = profile
                        }
                    } label: {
                        VStack(spacing: 4) {
                            Image(systemName: profileIcon(profile))
                                .font(.system(size: 18))
                            Text(profile.replacingOccurrences(of: "_", with: " ").uppercased())
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                            Text(profileDesc(profile))
                                .font(.system(size: 8, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.3))
                        }
                        .foregroundStyle(activeProfile == profile ? profileColor(profile) : .secondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                        .background(
                            RoundedRectangle(cornerRadius: 8)
                                .fill(activeProfile == profile ? profileColor(profile).opacity(0.12) : .clear)
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(activeProfile == profile ? profileColor(profile).opacity(0.3) : .clear, lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .background(RoundedRectangle(cornerRadius: 8).fill(RheaTheme.card.opacity(0.5)))
        }
    }

    // MARK: - Provider Roster

    private var providerRoster: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("PROVIDER ROSTER")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            ForEach(providers) { prov in
                HStack(spacing: 10) {
                    Circle()
                        .fill((prov.available ?? false) ? RheaTheme.green : RheaTheme.red)
                        .frame(width: 8, height: 8)

                    Text(prov.name.uppercased())
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(.white)

                    Spacer()

                    if let count = prov.model_count {
                        HStack(spacing: 2) {
                            Text("\(count)")
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.6))
                            Text("models")
                                .font(.system(size: 9, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                    }

                    if let tier = prov.tier {
                        Text(tier.uppercased())
                            .font(.system(size: 8, weight: .bold, design: .monospaced))
                            .foregroundStyle(tierColor(tier))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Capsule().fill(tierColor(tier).opacity(0.12)))
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(RheaTheme.card.opacity(0.5))
                )
            }
        }
    }

    // MARK: - Governor Grid

    private var governorGrid: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("GOVERNOR · BUDGET")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            ForEach(Array(governorStatuses.sorted(by: { $0.key < $1.key })), id: \.key) { agent, status in
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(agent.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(.white)
                        Spacer()
                        Text((status.mode ?? "?").uppercased())
                            .font(.system(size: 8, weight: .bold, design: .monospaced))
                            .foregroundStyle(modeColor(status.mode ?? ""))
                            .padding(.horizontal, 5)
                            .padding(.vertical, 2)
                            .background(Capsule().fill(modeColor(status.mode ?? "").opacity(0.12)))
                    }

                    HStack(spacing: 16) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("T/day").font(.system(size: 8, design: .monospaced)).foregroundStyle(.secondary)
                            Text(store.formatTokens(status.T_day ?? 0))
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text("$/day").font(.system(size: 8, design: .monospaced)).foregroundStyle(.secondary)
                            Text(String(format: "$%.3f", status.dollar_day ?? 0))
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                                .foregroundStyle(RheaTheme.amber)
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 2) {
                            Text("PACE").font(.system(size: 8, design: .monospaced)).foregroundStyle(.secondary)
                            Text((status.pace ?? "—").uppercased())
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(paceColor(status.pace ?? ""))
                        }
                    }

                    // Budget bar
                    if let cap = status.budget_cap, cap > 0, let spent = status.dollar_day {
                        GeometryReader { geo in
                            let pct = min(spent / cap, 1.0)
                            ZStack(alignment: .leading) {
                                RoundedRectangle(cornerRadius: 2).fill(.white.opacity(0.05))
                                RoundedRectangle(cornerRadius: 2)
                                    .fill(pct > 0.9 ? RheaTheme.red : pct > 0.7 ? RheaTheme.amber : RheaTheme.green)
                                    .frame(width: geo.size.width * pct)
                            }
                        }
                        .frame(height: 3)
                    }
                }
                .padding(12)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(RheaTheme.card.opacity(0.5))
                )
            }
        }
    }

    // MARK: - Summary

    private var summaryMetrics: some View {
        HStack(spacing: 8) {
            summaryBox("PROVIDERS", "\(providers.filter { $0.available ?? false }.count)/\(providers.count)", RheaTheme.green)
            summaryBox("MODELS", "\(store.health?.total_models ?? 0)", RheaTheme.accent)
            summaryBox("PROFILE", activeProfile.replacingOccurrences(of: "_", with: " ").uppercased(), profileColor(activeProfile))
        }
    }

    private func summaryBox(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 12, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            Text(label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
        .background(RoundedRectangle(cornerRadius: 8).fill(RheaTheme.card.opacity(0.5)))
    }

    // MARK: - Helpers

    private func profileIcon(_ p: String) -> String {
        switch p { case "safe_cheap": return "leaf.fill"; case "balanced": return "scale.3d"; case "deep": return "brain.head.profile"; default: return "questionmark" }
    }
    private func profileDesc(_ p: String) -> String {
        switch p { case "safe_cheap": return "DeepSeek + HF"; case "balanced": return "OpenRouter + Gemini"; case "deep": return "Anthropic Opus"; default: return "" }
    }
    private func profileColor(_ p: String) -> Color {
        switch p { case "safe_cheap": return RheaTheme.green; case "balanced": return RheaTheme.amber; case "deep": return .purple; default: return .secondary }
    }
    private func tierColor(_ t: String) -> Color {
        switch t.lowercased() { case "cheap": return RheaTheme.green; case "balanced": return RheaTheme.amber; case "expensive": return .orange; case "deep": return .purple; default: return .secondary }
    }
    private func modeColor(_ m: String) -> Color {
        switch m.lowercased() { case "normal": return RheaTheme.green; case "compact": return RheaTheme.amber; case "enforcement": return RheaTheme.red; case "shadow": return .purple; default: return .secondary }
    }
    private func paceColor(_ p: String) -> Color {
        switch p.lowercased() { case "on_track", "normal": return RheaTheme.green; case "over": return RheaTheme.amber; case "critical": return RheaTheme.red; default: return .secondary }
    }

    private func fetchAll() async {
        loading = true
        defer { loading = false }
        if let resp = try? await api.models() { providers = resp.providers ?? [] }
        if let profile = try? await api.executionProfile() {
            activeProfile = profile["active"] as? String ?? profile["profile"] as? String ?? "safe_cheap"
        }
        governorStatuses = (try? await api.governorAll()) ?? [:]
    }

    private func runLiveTest() async {
        liveTestRunning = true
        defer { liveTestRunning = false }
        _ = try? await api.getJSON("/health?live_test=true")
        if let resp = try? await api.models() { providers = resp.providers ?? [] }
    }
}
