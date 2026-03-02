import SwiftUI
import RheaKit

@main
struct RheaPreviewApp: App {
    @AppStorage("hasEnteredIntent") private var hasEnteredIntent = false
    @AppStorage("intentRevealLevel") private var intentRevealLevel = 1
    @StateObject private var auth = AuthManager.shared
    @State private var selectedPane: PlayPane = .ops

    init() {
        AppConfig.migrateStaleDefaults()
    }

    var body: some Scene {
        WindowGroup {
            Group {
                if !auth.isLoggedIn && !auth.didSkipAuth {
                    AuthView()
                } else if hasEnteredIntent {
                    PlayShell(selectedPane: $selectedPane, revealLevel: intentRevealLevel)
                } else {
                    IntentEntryView(selectedPane: $selectedPane)
                }
            }
            .preferredColorScheme(.dark)
            .environmentObject(auth)
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - Play Pane — mirrors macOS Play app
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

enum PlayPane: String, CaseIterable, Identifiable {
    case ops, tribunal, bio, radio, tasks, governor, tools, settings
    var id: String { rawValue }

    var label: String {
        switch self {
        case .ops: return "OPS"
        case .tribunal: return "TRIBUNAL"
        case .bio: return "BIO"
        case .radio: return "RADIO"
        case .tasks: return "TASKS"
        case .governor: return "GOVERNOR"
        case .tools: return "TOOLS"
        case .settings: return "CONFIG"
        }
    }

    var icon: String {
        switch self {
        case .ops: return "square.grid.2x2"
        case .tribunal: return "text.bubble"
        case .bio: return "atom"
        case .radio: return "waveform"
        case .tasks: return "checklist"
        case .governor: return "gauge.with.dots.needle.33percent"
        case .tools: return "keyboard"
        case .settings: return "slider.horizontal.3"
        }
    }

    static func visiblePanes(for level: Int) -> [PlayPane] {
        var list: [PlayPane] = [.ops, .tools]
        if level >= 2 {
            list.append(contentsOf: [.tribunal, .bio, .tasks, .governor])
        }
        if level >= 3 {
            // Expert-only: raw radio feed (ops traffic)
            list.append(.radio)
        }
        list.append(.settings)
        return list
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - Play Shell — command centre layout for iOS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

private struct PlayShell: View {
    @Binding var selectedPane: PlayPane
    let revealLevel: Int
    @StateObject private var store = RheaStore.shared
    @State private var pulseFlash = false
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    private var panes: [PlayPane] {
        PlayPane.visiblePanes(for: revealLevel)
    }

    var body: some View {
        VStack(spacing: 0) {
            // ── Top bar: RHEA + agent pills + metrics (info only) ──
            topBar

            // ── Content ──
            contentPane
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            // ── Status bar ──
            statusBar

            // ── Pane selector: thumb zone at bottom ──
            paneSelector
        }
        .background(RheaTheme.bg)
        .task { store.startPolling() }
        .onDisappear { store.stopPolling() }
        .onChange(of: store.connectionAlive) { _ in pulseFlash.toggle() }
    }

    // ━━ TOP BAR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    var topBar: some View {
        HStack(spacing: 12) {
            // Logo
            HStack(spacing: 6) {
                Image(systemName: "antenna.radiowaves.left.and.right")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(RheaTheme.accent)

                Text("RHEA")
                    .font(.system(size: 14, weight: .black, design: .monospaced))
                    .foregroundStyle(.white)
            }

            // Agent pills
            HStack(spacing: 4) {
                ForEach(store.agents) { agent in
                    HStack(spacing: 3) {
                        Circle()
                            .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                            .frame(width: 5, height: 5)
                        Text(agent.name.prefix(3).lowercased())
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.7))
                    }
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(
                        Capsule()
                            .fill(RheaTheme.card)
                            .overlay(
                                Capsule()
                                    .stroke(agent.alive ? RheaTheme.green.opacity(0.2) : RheaTheme.red.opacity(0.2), lineWidth: 1)
                            )
                    )
                }
            }

            Spacer()

            // Metrics
            HStack(spacing: 10) {
                metricBadge("T", store.formatTokens(store.totalTokens), .white)
                metricBadge("$", String(format: "%.2f", store.totalCost), RheaTheme.amber)
                metricBadge("P", "\(store.aliveCount)/\(store.agents.count)", RheaTheme.green)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(RheaTheme.card.opacity(0.6))
    }

    func metricBadge(_ label: String, _ value: String, _ color: Color) -> some View {
        HStack(spacing: 2) {
            Text(label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
        }
    }

    // ━━ PANE SELECTOR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    var paneSelector: some View {
        ScrollViewReader { proxy in
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 0) {
                    ForEach(panes) { pane in
                        Button {
                            withAnimation(.spring(duration: 0.25)) {
                                selectedPane = pane
                            }
                        } label: {
                            VStack(spacing: 3) {
                                // Active indicator bar
                                Rectangle()
                                    .fill(selectedPane == pane ? RheaTheme.accent : .clear)
                                    .frame(height: 2)
                                    .cornerRadius(1)

                                Image(systemName: pane.icon)
                                    .font(.system(size: 18, weight: .semibold))

                                Text(pane.label)
                                    .font(.system(size: 8, weight: .bold, design: .monospaced))
                            }
                            .foregroundStyle(selectedPane == pane ? RheaTheme.accent : .white.opacity(0.4))
                            .frame(minWidth: 56)
                            .padding(.vertical, 6)
                            .padding(.horizontal, 4)
                        }
                        .buttonStyle(.plain)
                        .id(pane)
                    }
                }
                .padding(.horizontal, 4)
            }
            .onChange(of: selectedPane) { newPane in
                withAnimation { proxy.scrollTo(newPane, anchor: .center) }
            }
        }
        .padding(.bottom, 2)
        .background(RheaTheme.card.opacity(0.8))
    }

    // ━━ CONTENT PANE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    var contentPane: some View {
        Group {
            switch selectedPane {
            case .ops: OpsView()
            case .tribunal: DialogView()
            case .bio: BioRendererView()
            case .radio: TeamChatView()
            case .tasks: TasksView()
            case .governor: GovernorView()
            case .tools: ToolsHubView()
            case .settings: SettingsView()
            }
        }
        .background(RheaTheme.bg)
    }

    // ━━ STATUS BAR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    var statusBar: some View {
        HStack(spacing: 10) {
            // Connection indicator
            HStack(spacing: 4) {
                Circle()
                    .fill(store.connectionAlive ? RheaTheme.green : RheaTheme.red)
                    .frame(width: 5, height: 5)
                Text(store.connectionAlive ? "LIVE" : "OFFLINE")
                    .font(.system(size: 8, weight: .bold, design: .monospaced))
                    .foregroundStyle(store.connectionAlive ? RheaTheme.green : RheaTheme.red)
            }

            Rectangle()
                .fill(.white.opacity(0.1))
                .frame(width: 1, height: 10)

            // API url (truncated)
            Text(apiBaseURL
                .replacingOccurrences(of: "https://", with: "")
                .replacingOccurrences(of: "http://", with: ""))
                .font(.system(size: 8, design: .monospaced))
                .foregroundStyle(.white.opacity(0.2))
                .lineLimit(1)

            Spacer()

            // Current pane
            Text(selectedPane.label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            Rectangle()
                .fill(.white.opacity(0.1))
                .frame(width: 1, height: 10)

            // Live clock
            TimelineView(.periodic(from: .now, by: 1)) { context in
                Text(context.date.formatted(.dateTime.hour().minute().second()))
                    .font(.system(size: 8, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.3))
            }

            // Proof count
            if store.proofCount > 0 {
                HStack(spacing: 2) {
                    Image(systemName: "checkmark.seal")
                        .font(.system(size: 7))
                    Text("\(store.proofCount)")
                        .font(.system(size: 8, weight: .bold, design: .monospaced))
                }
                .foregroundStyle(RheaTheme.green.opacity(0.5))
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 5)
        .background(RheaTheme.card.opacity(0.4))
    }
}

private struct IntentRoute: Identifiable {
    let id: String
    let title: String
    let subtitle: String
    let seed: String
    let role: String
    let revealLevel: Int
    let icon: String
}

private struct IntentEntryView: View {
    @Binding var selectedPane: PlayPane
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @AppStorage("hasEnteredIntent") private var hasEnteredIntent = false
    @AppStorage("intentRevealLevel") private var intentRevealLevel = 1
    @AppStorage("intentRole") private var intentRole = "biochemist"
    @AppStorage("firstIntentText") private var firstIntentText = ""

    @State private var intentText = ""
    @State private var isSending = false
    @State private var errorText: String? = nil

    private let routes: [IntentRoute] = [
        .init(
            id: "quick",
            title: "Quick Ask",
            subtitle: "2 steps to first useful answer",
            seed: "Give me one practical next step for my current work block.",
            role: "biochemist",
            revealLevel: 1,
            icon: "bolt.fill"
        ),
        .init(
            id: "research",
            title: "Research",
            subtitle: "Hypothesis -> evidence -> next experiment",
            seed: "I need a hypothesis + evidence plan for this research question:",
            role: "biochemist",
            revealLevel: 2,
            icon: "flask.fill"
        ),
        .init(
            id: "operator",
            title: "Operator",
            subtitle: "Queue, radio, and control panel",
            seed: "Show current blockers, owner, and next action for each P0 item.",
            role: "operator",
            revealLevel: 2,
            icon: "slider.horizontal.3"
        ),
        .init(
            id: "investor",
            title: "Investor",
            subtitle: "Proof of progress with concrete signals",
            seed: "What changed in the last 90 minutes with verifiable evidence?",
            role: "investor",
            revealLevel: 2,
            icon: "chart.line.uptrend.xyaxis"
        )
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Text("Rhea")
                        .font(.system(size: 34, weight: .bold, design: .rounded))
                        .foregroundStyle(.white)
                    Text("Start with one base query. Advanced controls open only after intent.")
                        .font(.system(size: 13, weight: .medium, design: .default))
                        .foregroundStyle(.secondary)

                    routeGrid

                    VStack(alignment: .leading, spacing: 8) {
                        Text("BASE QUERY")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.accent)

                        TextField("What do you need right now?", text: $intentText, axis: .vertical)
                            .textFieldStyle(.plain)
                            .font(.system(size: 15))
                            .foregroundStyle(.white)
                            .lineLimit(2...5)
                            .padding(12)
                            .background(
                                RoundedRectangle(cornerRadius: 14)
                                    .fill(RheaTheme.card)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 14)
                                            .stroke(RheaTheme.cardBorder, lineWidth: 1)
                                    )
                            )
                    }
                    .glassCard()

                    if let errorText {
                        Text(errorText)
                            .font(.system(size: 12, weight: .semibold, design: .monospaced))
                            .foregroundStyle(RheaTheme.red)
                    }

                    HStack(spacing: 10) {
                        Button(action: submitIntent) {
                            HStack(spacing: 8) {
                                if isSending {
                                    ProgressView()
                                        .scaleEffect(0.75)
                                } else {
                                    Image(systemName: "arrow.up.circle.fill")
                                }
                                Text(isSending ? "Sending..." : "Start")
                            }
                            .font(.system(size: 14, weight: .bold, design: .monospaced))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(RheaTheme.accent)
                        .disabled(isSending || intentText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

                        Button("Expert") {
                            intentRole = "operator"
                            intentRevealLevel = 3
                            hasEnteredIntent = true
                            selectedPane = .tribunal
                        }
                        .font(.system(size: 13, weight: .semibold, design: .monospaced))
                        .buttonStyle(.bordered)
                    }
                }
                .padding(16)
            }
            .background(RheaTheme.bg)
            .navigationTitle("Intent")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private var routeGrid: some View {
        VStack(spacing: 10) {
            ForEach(routes) { route in
                Button {
                    intentText = route.seed
                    intentRole = route.role
                    intentRevealLevel = route.revealLevel
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: route.icon)
                            .frame(width: 20)
                            .foregroundStyle(RheaTheme.accent)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(route.title)
                                .font(.system(size: 14, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white)
                            Text(route.subtitle)
                                .font(.system(size: 12))
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                    }
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(RheaTheme.card)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(RheaTheme.cardBorder, lineWidth: 1)
                            )
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func submitIntent() {
        let text = intentText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isSending else { return }
        isSending = true
        errorText = nil

        let body = DialogRequest(text: text, sender: "human")
        guard let url = URL(string: "\(apiBaseURL)/dialog"),
              let payload = try? JSONEncoder().encode(body) else {
            isSending = false
            errorText = "Invalid API configuration."
            return
        }

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        req.httpBody = payload

        URLSession.shared.dataTask(with: req) { _, response, error in
            DispatchQueue.main.async {
                isSending = false
                if let error {
                    errorText = "Send failed: \(error.localizedDescription)"
                    return
                }
                if let http = response as? HTTPURLResponse, http.statusCode >= 300 {
                    errorText = "Send failed: HTTP \(http.statusCode)"
                    return
                }
                firstIntentText = text
                hasEnteredIntent = true
                selectedPane = .ops
            }
        }.resume()
    }
}
