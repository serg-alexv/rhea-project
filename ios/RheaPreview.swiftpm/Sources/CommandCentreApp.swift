#if os(macOS)
import SwiftUI
import Pow

@main
struct CommandCentreApp: App {
    init() {
        AppConfig.migrateStaleDefaults()
    }

    var body: some Scene {
        WindowGroup("Rhea") {
            PlayShell()
                .preferredColorScheme(.dark)
                .frame(minWidth: 960, minHeight: 640)
        }
        .defaultSize(width: 1280, height: 800)
        .commands {
            CommandGroup(replacing: .newItem) { }
        }

        MenuBarExtra {
            MenuBarView()
        } label: {
            HStack(spacing: 4) {
                Image(systemName: "antenna.radiowaves.left.and.right")
                Text("RHEA")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
            }
        }
        .menuBarExtraStyle(.window)
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - Play Shell — the ops centre frame
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct PlayShell: View {
    @State private var selectedPane: Pane = .radio
    @State private var agents: [AgentDTO] = []
    @State private var pollTimer: Timer? = nil
    @State private var connectionAlive = false
    @State private var pulseFlash = false
    @State private var totalTokens = 0
    @State private var totalCost = 0.0
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    enum Pane: String, CaseIterable, Identifiable {
        case radio, dialog, governor, tasks, pulse, atlas, history, settings
        var id: String { rawValue }

        var label: String {
            switch self {
            case .radio: return "RADIO"
            case .dialog: return "DIALOG"
            case .governor: return "GOVERNOR"
            case .tasks: return "TASKS"
            case .pulse: return "PULSE"
            case .atlas: return "ATLAS"
            case .history: return "HISTORY"
            case .settings: return "CONFIG"
            }
        }

        var icon: String {
            switch self {
            case .radio: return "waveform"
            case .dialog: return "text.bubble"
            case .governor: return "gauge.with.dots.needle.33percent"
            case .tasks: return "checklist"
            case .pulse: return "heart.text.square"
            case .atlas: return "globe"
            case .history: return "clock.arrow.circlepath"
            case .settings: return "slider.horizontal.3"
            }
        }

        var shortcut: KeyEquivalent {
            switch self {
            case .radio: return "1"
            case .dialog: return "2"
            case .governor: return "3"
            case .tasks: return "4"
            case .pulse: return "5"
            case .atlas: return "6"
            case .history: return "7"
            case .settings: return "8"
            }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // ── Top bar: RHEA + live indicator + agent pills + token counter ──
            topBar

            Divider().overlay(RheaTheme.accent.opacity(0.15))

            // ── Main content: sidebar + detail ──
            HStack(spacing: 0) {
                // Sidebar: nav rail + agent roster
                sideRail
                    .frame(width: 200)

                // Thin accent divider
                Rectangle()
                    .fill(RheaTheme.accent.opacity(0.08))
                    .frame(width: 1)

                // Detail pane
                detailPane
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }

            // ── Status bar: connection + API url + clock ──
            statusBar
        }
        .background(RheaTheme.bg)
        .task {
            await fetchAgents()
            startPolling()
        }
        .onDisappear { stopPolling() }
    }

    // ━━ TOP BAR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    var topBar: some View {
        HStack(spacing: 16) {
            // Logo
            HStack(spacing: 8) {
                Image(systemName: "antenna.radiowaves.left.and.right")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundStyle(RheaTheme.accent)
                    .changeEffect(.pulse(shape: Circle(), count: 2), value: pulseFlash)

                Text("RHEA")
                    .font(.system(size: 16, weight: .black, design: .monospaced))
                    .foregroundStyle(.white)

                Text("PLAY")
                    .font(.system(size: 11, weight: .bold, design: .rounded))
                    .foregroundStyle(RheaTheme.accent)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(
                        Capsule().fill(RheaTheme.accent.opacity(0.15))
                    )
            }

            // Agent pills
            HStack(spacing: 6) {
                ForEach(agents) { agent in
                    agentPill(agent)
                }
            }

            Spacer()

            // Metrics
            HStack(spacing: 16) {
                metricLabel("T", formatTokens(totalTokens), .white)
                metricLabel("$", String(format: "%.2f", totalCost), RheaTheme.amber)
                metricLabel("P", "\(agents.filter { !$0.isHardFail }.count)/\(agents.count)", RheaTheme.green)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(
            RheaTheme.card.opacity(0.6)
        )
    }

    func agentPill(_ agent: AgentDTO) -> some View {
        HStack(spacing: 5) {
            Circle()
                .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                .frame(width: 6, height: 6)
            Text(agent.name.prefix(3).lowercased())
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.white.opacity(0.8))
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(RheaTheme.card)
                .overlay(
                    Capsule()
                        .stroke(agent.alive ? RheaTheme.green.opacity(0.2) : RheaTheme.red.opacity(0.2), lineWidth: 1)
                )
        )
    }

    func metricLabel(_ label: String, _ value: String, _ color: Color) -> some View {
        HStack(spacing: 4) {
            Text(label)
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 12, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
        }
    }

    // ━━ SIDE RAIL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    var sideRail: some View {
        VStack(spacing: 0) {
            // Nav items
            ScrollView {
                VStack(spacing: 2) {
                    ForEach(Pane.allCases) { pane in
                        Button {
                            withAnimation(.spring(duration: 0.25)) {
                                selectedPane = pane
                            }
                        } label: {
                            HStack(spacing: 10) {
                                Image(systemName: pane.icon)
                                    .font(.system(size: 12, weight: .semibold))
                                    .frame(width: 18)
                                    .foregroundStyle(selectedPane == pane ? RheaTheme.accent : .secondary)

                                Text(pane.label)
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                    .foregroundStyle(selectedPane == pane ? .white : .secondary)

                                Spacer()

                                // Keyboard shortcut hint
                                Text("\(pane.shortcut)")
                                    .font(.system(size: 9, weight: .medium, design: .monospaced))
                                    .foregroundStyle(.white.opacity(0.15))
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(selectedPane == pane ? RheaTheme.accent.opacity(0.12) : .clear)
                            )
                        }
                        .buttonStyle(.plain)
                        .keyboardShortcut(pane.shortcut, modifiers: .command)
                    }
                }
                .padding(.horizontal, 8)
                .padding(.top, 8)
            }

            Spacer()

            // Agent roster at bottom of sidebar
            agentRoster
                .padding(.bottom, 8)
        }
        .background(RheaTheme.bg.opacity(0.8))
    }

    var agentRoster: some View {
        VStack(alignment: .leading, spacing: 4) {
            Divider().overlay(RheaTheme.accent.opacity(0.08))

            Text("AGENTS ONLINE")
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))
                .padding(.horizontal, 12)
                .padding(.top, 6)

            ForEach(agents) { agent in
                HStack(spacing: 8) {
                    Circle()
                        .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                        .frame(width: 6, height: 6)

                    Text(agent.name.lowercased())
                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.7))

                    Spacer()

                    Text(agent.mode)
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(RheaTheme.modeColor(agent.mode).opacity(0.6))

                    if agent.T_day > 0 {
                        Text(formatTokens(agent.T_day))
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.3))
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 2)
            }
        }
    }

    // ━━ DETAIL PANE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    var detailPane: some View {
        Group {
            switch selectedPane {
            case .radio: TeamChatView()
            case .dialog: DialogView()
            case .governor: GovernorView()
            case .tasks: TasksView()
            case .pulse: PulseMonitorView()
            case .atlas: AtlasView()
            case .history: HistoryView()
            case .settings: SettingsView()
            }
        }
        .background(RheaTheme.bg)
    }

    // ━━ STATUS BAR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    var statusBar: some View {
        HStack(spacing: 12) {
            // Connection indicator
            HStack(spacing: 6) {
                Circle()
                    .fill(connectionAlive ? RheaTheme.green : RheaTheme.red)
                    .frame(width: 6, height: 6)
                Text(connectionAlive ? "LIVE" : "OFFLINE")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(connectionAlive ? RheaTheme.green : RheaTheme.red)
            }

            Rectangle()
                .fill(.white.opacity(0.1))
                .frame(width: 1, height: 12)

            // API URL
            Text(apiBaseURL.replacingOccurrences(of: "https://", with: ""))
                .font(.system(size: 9, design: .monospaced))
                .foregroundStyle(.white.opacity(0.3))
                .textSelection(.enabled)

            Spacer()

            // Selected pane label
            Text(selectedPane.label)
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            Rectangle()
                .fill(.white.opacity(0.1))
                .frame(width: 1, height: 12)

            // Live clock
            TimelineView(.periodic(from: .now, by: 1)) { context in
                Text(context.date.formatted(.dateTime.hour().minute().second()))
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.3))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .background(RheaTheme.card.opacity(0.4))
    }

    // ━━ POLLING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    func fetchAgents() async {
        guard let url = URL(string: "\(apiBaseURL)/agents/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            struct Resp: Codable { let agents: [String: AgentDTO] }
            let resp = try JSONDecoder().decode(Resp.self, from: data)
            withAnimation(.spring(duration: 0.3)) {
                agents = resp.agents.values.sorted { $0.name < $1.name }
                totalTokens = agents.reduce(0) { $0 + $1.T_day }
                totalCost = agents.reduce(0.0) { $0 + $1.dollar_day }
                connectionAlive = true
                pulseFlash.toggle()
            }
        } catch {
            connectionAlive = false
        }
    }

    func startPolling() {
        pollTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
            Task { await fetchAgents() }
        }
    }

    func stopPolling() {
        pollTimer?.invalidate()
        pollTimer = nil
    }

    func formatTokens(_ n: Int) -> String {
        if n >= 1_000_000 { return "\(n / 1_000_000)M" }
        if n >= 1_000 { return "\(n / 1_000)K" }
        return "\(n)"
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - History View (SQL-backed)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct HistoryView: View {
    @State private var entries: [[String: Any]] = []
    @State private var loading = true
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("TRIBUNAL HISTORY")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.7))

                Spacer()

                Text("\(entries.count) entries")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)

                Button { Task { await fetch() } } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11))
                        .foregroundStyle(RheaTheme.accent)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)

            Divider().overlay(RheaTheme.accent.opacity(0.08))

            if loading && entries.isEmpty {
                Spacer()
                ProgressView()
                    .controlSize(.small)
                Spacer()
            } else if entries.isEmpty {
                Spacer()
                VStack(spacing: 12) {
                    Image(systemName: "clock.arrow.circlepath")
                        .font(.system(size: 32))
                        .foregroundStyle(.white.opacity(0.15))
                    Text("No history yet")
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.3))
                    Text("Submit a tribunal query to start")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.15))
                }
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: 2) {
                        ForEach(Array(entries.enumerated()), id: \.offset) { _, entry in
                            historyRow(entry)
                        }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                }
            }
        }
        .background(RheaTheme.bg)
        .task { await fetch() }
    }

    func historyRow(_ entry: [String: Any]) -> some View {
        HStack(spacing: 12) {
            // Type badge
            Text((entry["type"] as? String ?? "?").uppercased())
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent)
                .frame(width: 60, alignment: .leading)

            // Prompt
            Text(entry["prompt"] as? String ?? "")
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.white.opacity(0.8))
                .lineLimit(1)
                .frame(maxWidth: .infinity, alignment: .leading)

            // Agreement score
            if let score = entry["agreement_score"] as? Double {
                Text("\(Int(score * 100))%")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(score > 0.7 ? RheaTheme.green : score > 0.4 ? RheaTheme.amber : RheaTheme.red)
                    .frame(width: 40, alignment: .trailing)
            }

            // Time
            if let ts = entry["created_at"] as? String, ts.count > 11 {
                let timeStr = String(ts.dropFirst(11).prefix(5))
                Text(timeStr)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.2))
                    .frame(width: 45, alignment: .trailing)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(RheaTheme.card.opacity(0.5))
        )
    }

    func fetch() async {
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBaseURL)/cc/history?limit=50") else { return }
        var request = URLRequest(url: url)
        request.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let history = json["history"] as? [[String: Any]] {
                entries = history
            }
        } catch {}
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - Menu Bar Widget
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct MenuBarView: View {
    @State private var agents: [AgentDTO] = []
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("RHEA PLAY")
                    .font(.system(size: 10, weight: .black, design: .monospaced))
                    .foregroundStyle(.white)
                Spacer()
                Circle()
                    .fill(agents.isEmpty ? Color.red : Color.green)
                    .frame(width: 6, height: 6)
            }

            Divider()

            if agents.isEmpty {
                Text("connecting...")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)
            } else {
                ForEach(agents) { agent in
                    HStack(spacing: 8) {
                        Circle()
                            .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                            .frame(width: 6, height: 6)

                        Text(agent.name.lowercased())
                            .font(.system(size: 11, weight: .semibold, design: .monospaced))
                            .foregroundStyle(.white)

                        Spacer()

                        Text(agent.mode)
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(RheaTheme.modeColor(agent.mode))
                    }
                }
            }

            Divider()

            HStack {
                let totalTokens = agents.reduce(0) { $0 + $1.T_day }
                let totalCost = agents.reduce(0.0) { $0 + $1.dollar_day }
                Text("T:\(formatTokens(totalTokens))")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.5))
                Spacer()
                Text("$\(String(format: "%.2f", totalCost))")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.amber)
            }
        }
        .padding(12)
        .frame(width: 220)
        .task { await fetch() }
    }

    func fetch() async {
        guard let url = URL(string: "\(apiBaseURL)/agents/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            struct Resp: Codable { let agents: [String: AgentDTO] }
            let resp = try JSONDecoder().decode(Resp.self, from: data)
            agents = resp.agents.values.sorted { $0.name < $1.name }
        } catch {}
    }

    func formatTokens(_ n: Int) -> String {
        if n >= 1_000_000 { return "\(n / 1_000_000)M" }
        if n >= 1_000 { return "\(n / 1_000)K" }
        return "\(n)"
    }
}
#endif
