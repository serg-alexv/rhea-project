#if os(macOS)
import SwiftUI

@main
struct CommandCentreApp: App {
    init() {
        AppConfig.migrateStaleDefaults()
    }

    var body: some Scene {
        WindowGroup("Rhea Command Centre") {
            CommandCentreLayout()
                .preferredColorScheme(.dark)
                .frame(minWidth: 900, minHeight: 600)
        }
        .defaultSize(width: 1200, height: 800)
        .commands {
            CommandGroup(replacing: .newItem) { }
        }

        MenuBarExtra("Rhea", systemImage: "dot.radiowaves.left.and.right") {
            MenuBarView()
        }
        .menuBarExtraStyle(.window)
    }
}

// MARK: - 3-Column Layout

struct CommandCentreLayout: View {
    @State private var selectedPane: SidebarPane = .radio
    @State private var agents: [AgentDTO] = []
    @State private var pollTimer: Timer? = nil
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    enum SidebarPane: String, CaseIterable, Identifiable {
        case radio = "Radio"
        case dialog = "Dialog"
        case governor = "Governor"
        case tasks = "Tasks"
        case pulse = "Pulse"
        case atlas = "Atlas"
        case history = "History"

        var id: String { rawValue }

        var icon: String {
            switch self {
            case .radio: return "bubble.left.and.bubble.right"
            case .dialog: return "text.bubble"
            case .governor: return "gauge.with.dots.needle.33percent"
            case .tasks: return "checklist"
            case .pulse: return "dot.radiowaves.left.and.right"
            case .atlas: return "globe"
            case .history: return "clock.arrow.circlepath"
            }
        }
    }

    var body: some View {
        NavigationSplitView {
            // Sidebar: agent roster + nav
            VStack(spacing: 0) {
                // Agent roster (compact)
                agentRoster
                    .padding(.bottom, 8)

                Divider()

                // Navigation
                List(SidebarPane.allCases, selection: $selectedPane) { pane in
                    Label(pane.rawValue, systemImage: pane.icon)
                        .tag(pane)
                }
                .listStyle(.sidebar)
            }
            .frame(minWidth: 180)
            .background(RheaTheme.bg)
        } detail: {
            // Main content
            Group {
                switch selectedPane {
                case .radio:
                    TeamChatView()
                case .dialog:
                    DialogView()
                case .governor:
                    GovernorView()
                case .tasks:
                    TasksView()
                case .pulse:
                    PulseMonitorView()
                case .atlas:
                    AtlasView()
                case .history:
                    HistoryView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(RheaTheme.bg)
        }
        .navigationSplitViewStyle(.balanced)
        .task {
            await fetchAgents()
            startPolling()
        }
        .onDisappear { stopPolling() }
    }

    // MARK: - Agent Roster (sidebar)

    var agentRoster: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("AGENTS")
                .font(.system(.caption2, design: .monospaced, weight: .bold))
                .foregroundStyle(RheaTheme.accent.opacity(0.7))
                .padding(.horizontal, 12)
                .padding(.top, 8)

            ForEach(agents) { agent in
                HStack(spacing: 8) {
                    Circle()
                        .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                        .frame(width: 8, height: 8)

                    Text(agent.name.lowercased())
                        .font(.system(.caption, design: .monospaced, weight: .semibold))
                        .foregroundStyle(.white)

                    Spacer()

                    Text(agent.mode)
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(RheaTheme.modeColor(agent.mode))
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 2)
            }
        }
    }

    // MARK: - Polling

    func fetchAgents() async {
        guard let url = URL(string: "\(apiBaseURL)/agents/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            struct Resp: Codable { let agents: [String: AgentDTO] }
            let resp = try JSONDecoder().decode(Resp.self, from: data)
            withAnimation(.spring(duration: 0.3)) {
                agents = resp.agents.values.sorted { $0.name < $1.name }
            }
        } catch {}
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
}

// MARK: - History View (SQL-backed)

struct HistoryView: View {
    @State private var entries: [[String: Any]] = []
    @State private var loading = true
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var body: some View {
        NavigationStack {
            if loading && entries.isEmpty {
                ProgressView("Loading history...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if entries.isEmpty {
                ContentUnavailableView("No History", systemImage: "clock.arrow.circlepath",
                                       description: Text("Submit a tribunal query to start building history"))
            } else {
                List {
                    ForEach(Array(entries.enumerated()), id: \.offset) { _, entry in
                        historyRow(entry)
                    }
                }
                .listStyle(.inset)
            }
        }
        .navigationTitle("History")
        .background(RheaTheme.bg)
        .task { await fetch() }
    }

    func historyRow(_ entry: [String: Any]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(entry["type"] as? String ?? "?")
                    .font(.system(.caption, design: .monospaced, weight: .bold))
                    .foregroundStyle(RheaTheme.accent)

                Spacer()

                if let score = entry["agreement_score"] as? Double {
                    Text("\(Int(score * 100))%")
                        .font(.system(.caption, design: .monospaced))
                        .foregroundStyle(score > 0.7 ? RheaTheme.green : score > 0.4 ? RheaTheme.amber : RheaTheme.red)
                }

                Text(entry["created_at"] as? String ?? "")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            Text(entry["prompt"] as? String ?? "")
                .font(.system(.body))
                .foregroundStyle(.white)
                .lineLimit(2)
        }
        .padding(.vertical, 4)
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

// MARK: - Menu Bar Widget

struct MenuBarView: View {
    @State private var agents: [AgentDTO] = []
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("RHEA AGENTS")
                .font(.system(.caption2, design: .monospaced, weight: .bold))
                .foregroundStyle(.secondary)

            if agents.isEmpty {
                Text("Loading...")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(agents) { agent in
                    HStack(spacing: 8) {
                        Circle()
                            .fill(agent.alive ? Color.green : Color.red)
                            .frame(width: 8, height: 8)

                        Text(agent.name.lowercased())
                            .font(.system(.body, design: .monospaced))

                        Spacer()

                        Text(agent.mode)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Divider()

            HStack {
                let totalTokens = agents.reduce(0) { $0 + $1.T_day }
                let totalCost = agents.reduce(0.0) { $0 + $1.dollar_day }
                Text("T: \(formatTokens(totalTokens))")
                    .font(.system(.caption, design: .monospaced))
                Spacer()
                Text("$\(String(format: "%.2f", totalCost))")
                    .font(.system(.caption, design: .monospaced))
            }
        }
        .padding(12)
        .frame(width: 240)
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
