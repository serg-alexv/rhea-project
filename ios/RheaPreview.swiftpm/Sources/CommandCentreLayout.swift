#if os(macOS)
import SwiftUI
import RheaKit

/// Three-column command centre layout.
///
/// ```
/// ┌────────────┬────────────────────────┬───────────────────────┐
/// │ SIDEBAR    │  CONTENT               │  DETAIL               │
/// │            │                        │                       │
/// │ Agents     │  Radio / Office feed   │  Tribunal / Tasks /   │
/// │ Governor   │                        │  History / Bio        │
/// │ Relay      │                        │                       │
/// └────────────┴────────────────────────┴───────────────────────┘
/// ```
struct CommandCentreLayout: View {
    @State private var selectedPanel: Panel = .radio
    @State private var detailPanel: DetailPanel = .tribunal

    enum Panel: String, CaseIterable, Identifiable {
        case radio, office, atlas
        var id: String { rawValue }
        var label: String { rawValue.capitalized }
        var icon: String {
            switch self {
            case .radio: return "antenna.radiowaves.left.and.right"
            case .office: return "envelope"
            case .atlas: return "globe"
            }
        }
    }

    enum DetailPanel: String, CaseIterable, Identifiable {
        case tribunal, tasks, history, bio, relay, pulse
        var id: String { rawValue }
        var label: String { rawValue.capitalized }
        var icon: String {
            switch self {
            case .tribunal: return "scalemass"
            case .tasks: return "checklist"
            case .history: return "clock.arrow.circlepath"
            case .bio: return "atom"
            case .relay: return "shield.lefthalf.filled"
            case .pulse: return "waveform.path.ecg"
            }
        }
    }

    var body: some View {
        NavigationSplitView {
            sidebar
        } content: {
            contentPane
        } detail: {
            detailPane
        }
        .navigationSplitViewStyle(.balanced)
        .background(RheaTheme.bg)
        .onReceive(NotificationCenter.default.publisher(for: .ccNavigate)) { notif in
            if let name = notif.object as? String {
                if let p = Panel(rawValue: name) { selectedPanel = p }
                if let d = DetailPanel(rawValue: name) { detailPanel = d }
            }
        }
    }

    // MARK: - Sidebar

    private var sidebar: some View {
        List {
            Section("FEED") {
                ForEach(Panel.allCases) { panel in
                    Button {
                        selectedPanel = panel
                    } label: {
                        Label(panel.label, systemImage: panel.icon)
                    }
                    .buttonStyle(.plain)
                    .padding(.vertical, 2)
                    .foregroundStyle(selectedPanel == panel ? RheaTheme.accent : .secondary)
                }
            }

            Section("DETAIL") {
                ForEach(DetailPanel.allCases) { panel in
                    Button {
                        detailPanel = panel
                    } label: {
                        Label(panel.label, systemImage: panel.icon)
                    }
                    .buttonStyle(.plain)
                    .padding(.vertical, 2)
                    .foregroundStyle(detailPanel == panel ? RheaTheme.accent : .secondary)
                }
            }

            Section("STATUS") {
                SidebarGovernorWidget()
            }
        }
        .listStyle(.sidebar)
        .frame(minWidth: 160)
        .navigationTitle("Rhea")
    }

    // MARK: - Content (middle pane)

    private var contentPane: some View {
        Group {
            switch selectedPanel {
            case .radio:
                TeamChatView()
            case .office:
                OfficeView()
            case .atlas:
                AtlasView()
            }
        }
        .frame(minWidth: 300)
    }

    // MARK: - Detail (right pane)

    private var detailPane: some View {
        Group {
            switch detailPanel {
            case .tribunal:
                DialogView()
            case .tasks:
                TasksView()
            case .history:
                HistoryView()
            case .bio:
                BioRendererView()
            case .relay:
                RelayPrivacyView()
            case .pulse:
                PulseMonitorView()
            }
        }
        .frame(minWidth: 320)
    }
}

// MARK: - Sidebar Governor Widget

private struct SidebarGovernorWidget: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var tokenCount: String = "..."
    @State private var costToday: String = "..."
    @State private var agentCount: Int = 0
    @State private var timer: Timer?

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                Text("T")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                Text(tokenCount)
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent)
            }
            HStack(spacing: 6) {
                Text("$")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                Text(costToday)
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.green)
            }
            HStack(spacing: 6) {
                Text("A")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                Text("\(agentCount) online")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.7))
            }
        }
        .task { poll() }
        .onAppear {
            timer = Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { _ in poll() }
        }
        .onDisappear { timer?.invalidate() }
    }

    private func poll() {
        guard let url = URL(string: "\(apiBaseURL)/governor") else { return }
        var req = URLRequest(url: url)
        req.timeoutInterval = 5
        URLSession.shared.dataTask(with: req) { data, _, _ in
            guard let data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
            DispatchQueue.main.async {
                if let agents = json["agents"] as? [[String: Any]] {
                    agentCount = agents.count
                    let totalTokens = agents.compactMap { $0["T_day"] as? Int }.reduce(0, +)
                    let totalCost = agents.compactMap { $0["cost_today_usd"] as? Double }.reduce(0, +)
                    tokenCount = totalTokens > 1000 ? "\(totalTokens / 1000)K" : "\(totalTokens)"
                    costToday = String(format: "%.2f", totalCost)
                }
            }
        }.resume()
    }
}

// MARK: - Office View (SQL-backed)

struct OfficeView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var messages: [[String: Any]] = []
    @State private var isLoading = false

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 6) {
                    if messages.isEmpty && !isLoading {
                        Text("No office messages yet")
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .padding()
                    }
                    ForEach(Array(messages.enumerated()), id: \.offset) { _, msg in
                        officeRow(msg)
                    }
                }
                .padding(12)
            }
            .background(RheaTheme.bg)
            .navigationTitle("Office")
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button { loadMessages() } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .task { loadMessages() }
        }
    }

    private func officeRow(_ msg: [String: Any]) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            HStack(spacing: 6) {
                Text((msg["sender"] as? String ?? "?").uppercased())
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent)
                Image(systemName: "arrow.right")
                    .font(.system(size: 8))
                    .foregroundStyle(.secondary)
                Text((msg["receiver"] as? String ?? "?").uppercased())
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.green)
                Spacer()
                Text(formatTS(msg["ts"] as? String ?? ""))
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
            Text(msg["compressed"] as? String ?? msg["text"] as? String ?? "")
                .font(.system(size: 11, design: .monospaced))
                .foregroundStyle(.white.opacity(0.85))
                .lineLimit(4)
        }
        .padding(8)
        .background(RheaTheme.card)
        .cornerRadius(6)
    }

    private func formatTS(_ ts: String) -> String {
        guard ts.count >= 16 else { return ts }
        return String(ts.dropFirst(11).prefix(5))
    }

    private func loadMessages() {
        isLoading = true
        guard let url = URL(string: "\(apiBaseURL)/cc/office?limit=50") else { return }
        URLSession.shared.dataTask(with: url) { data, _, _ in
            defer { DispatchQueue.main.async { isLoading = false } }
            guard let data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let msgs = json["messages"] as? [[String: Any]] else { return }
            DispatchQueue.main.async { messages = msgs }
        }.resume()
    }
}

// MARK: - History View (SQL-backed)

struct HistoryView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var entries: [[String: Any]] = []
    @State private var sessions: [[String: Any]] = []
    @State private var selectedSession: String?
    @State private var isLoading = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Session selector
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        Button {
                            selectedSession = nil
                            loadHistory()
                        } label: {
                            Text("ALL")
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    Capsule().fill(selectedSession == nil
                                        ? RheaTheme.accent.opacity(0.2) : RheaTheme.card)
                                )
                                .foregroundStyle(selectedSession == nil ? RheaTheme.accent : .secondary)
                        }
                        .buttonStyle(.plain)

                        ForEach(Array(sessions.enumerated()), id: \.offset) { _, session in
                            let sid = session["id"] as? String ?? "?"
                            let count = session["step_count"] as? Int ?? 0
                            Button {
                                selectedSession = sid
                                loadHistory()
                            } label: {
                                Text("\(sid.prefix(8))… (\(count))")
                                    .font(.system(size: 9, weight: .medium, design: .monospaced))
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(
                                        Capsule().fill(selectedSession == sid
                                            ? RheaTheme.accent.opacity(0.2) : RheaTheme.card)
                                    )
                                    .foregroundStyle(selectedSession == sid ? RheaTheme.accent : .secondary)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                }

                Divider()

                // History entries
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 6) {
                        if entries.isEmpty && !isLoading {
                            VStack(spacing: 8) {
                                Image(systemName: "clock.arrow.circlepath")
                                    .font(.system(size: 32))
                                    .foregroundStyle(.secondary)
                                Text("No history yet")
                                    .font(.system(size: 13, design: .monospaced))
                                    .foregroundStyle(.secondary)
                                Text("Tribunal queries will appear here after they persist to SQL")
                                    .font(.system(size: 11))
                                    .foregroundStyle(.secondary.opacity(0.7))
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.top, 60)
                        }

                        ForEach(Array(entries.enumerated()), id: \.offset) { _, entry in
                            historyRow(entry)
                        }
                    }
                    .padding(12)
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("History")
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button { loadSessions(); loadHistory() } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .task { loadSessions(); loadHistory() }
        }
    }

    private func historyRow(_ entry: [String: Any]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 8) {
                let type = entry["type"] as? String ?? "?"
                Text(type.uppercased())
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Capsule().fill(typeColor(type).opacity(0.2)))
                    .foregroundStyle(typeColor(type))

                if let score = entry["agreement_score"] as? Double, score > 0 {
                    Text("\(Int(score * 100))%")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(score > 0.7 ? RheaTheme.green : score > 0.4 ? RheaTheme.amber : RheaTheme.red)
                }

                Spacer()

                Text(formatTS(entry["created_at"] as? String ?? ""))
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            Text(entry["prompt"] as? String ?? "")
                .font(.system(size: 11, design: .monospaced))
                .foregroundStyle(.white)
                .lineLimit(2)

            if let response = entry["response"] as? String, !response.isEmpty {
                Text(response)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.65))
                    .lineLimit(3)
            }
        }
        .padding(8)
        .background(RheaTheme.card)
        .cornerRadius(6)
    }

    private func typeColor(_ type: String) -> Color {
        switch type {
        case "tribunal": return RheaTheme.accent
        case "tribunal_sceptic": return RheaTheme.red
        case "tribunal_ice": return RheaTheme.amber
        default: return .secondary
        }
    }

    private func formatTS(_ ts: String) -> String {
        guard ts.count >= 16 else { return ts }
        return String(ts.dropFirst(11).prefix(5))
    }

    private func loadHistory() {
        isLoading = true
        var urlStr = "\(apiBaseURL)/cc/history?limit=50"
        if let sid = selectedSession { urlStr += "&session_id=\(sid)" }
        guard let url = URL(string: urlStr) else { return }
        URLSession.shared.dataTask(with: url) { data, _, _ in
            defer { DispatchQueue.main.async { isLoading = false } }
            guard let data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let rows = json["history"] as? [[String: Any]] else { return }
            DispatchQueue.main.async { entries = rows }
        }.resume()
    }

    private func loadSessions() {
        guard let url = URL(string: "\(apiBaseURL)/cc/sessions?limit=10") else { return }
        URLSession.shared.dataTask(with: url) { data, _, _ in
            guard let data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let rows = json["sessions"] as? [[String: Any]] else { return }
            DispatchQueue.main.async { sessions = rows }
        }.resume()
    }
}
#endif
