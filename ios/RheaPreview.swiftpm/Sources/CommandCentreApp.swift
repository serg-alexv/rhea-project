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
    @StateObject private var store = RheaStore.shared
    @State private var selectedPane: Pane = .radio
    @State private var pulseFlash = false
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    enum Pane: String, CaseIterable, Identifiable {
        case radio, dialog, governor, tasks, pulse, atlas, history, aletheia, ruliad, infra, settings
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
            case .aletheia: return "ALETHEIA"
            case .ruliad: return "RULIAD"
            case .infra: return "INFRA"
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
            case .aletheia: return "checkmark.seal"
            case .ruliad: return "function"
            case .infra: return "server.rack"
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
            case .aletheia: return "8"
            case .ruliad: return "9"
            case .infra: return "0"
            case .settings: return ","
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
            store.startPolling()
        }
        .onDisappear { store.stopPolling() }
        .onChange(of: store.connectionAlive) { _ in
            pulseFlash.toggle()
        }
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
                ForEach(store.agents) { agent in
                    agentPill(agent)
                }
            }

            Spacer()

            // Metrics
            HStack(spacing: 16) {
                metricLabel("T", store.formatTokens(store.totalTokens), .white)
                metricLabel("$", String(format: "%.2f", store.totalCost), RheaTheme.amber)
                metricLabel("P", "\(store.aliveCount)/\(store.agents.count)", RheaTheme.green)
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

            ForEach(store.agents) { agent in
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
                        Text(store.formatTokens(agent.T_day))
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
            case .aletheia: AletheiaView()
            case .ruliad: RuliadView()
            case .infra: InfraView()
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
                    .fill(store.connectionAlive ? RheaTheme.green : RheaTheme.red)
                    .frame(width: 6, height: 6)
                Text(store.connectionAlive ? "LIVE" : "OFFLINE")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(store.connectionAlive ? RheaTheme.green : RheaTheme.red)
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
// MARK: - Aletheia View (Proof Store + Ontology)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct AletheiaView: View {
    @State private var proofs: [[String: Any]] = []
    @State private var ontologies: [[String: Any]] = []
    @State private var loading = true
    @State private var selectedProof: [String: Any]? = nil
    private let api = RheaAPI.shared

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("ALETHEIA · PROOF STORE")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.7))

                Spacer()

                // Summary badges
                HStack(spacing: 12) {
                    badge("PROOFS", "\(proofs.count)", RheaTheme.green)
                    badge("ONTOLOGIES", "\(ontologies.count)", RheaTheme.amber)
                }

                Button { Task { await fetchAll() } } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11))
                        .foregroundStyle(RheaTheme.accent)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)

            Divider().overlay(RheaTheme.accent.opacity(0.08))

            if loading && proofs.isEmpty {
                Spacer()
                ProgressView().controlSize(.small)
                Spacer()
            } else {
                HSplitView {
                    // Left: proof list
                    proofList
                        .frame(minWidth: 300)

                    // Right: detail + ontologies
                    VStack(spacing: 0) {
                        if let proof = selectedProof {
                            proofDetail(proof)
                        } else {
                            ontologyGrid
                        }
                    }
                    .frame(minWidth: 250)
                }
            }
        }
        .background(RheaTheme.bg)
        .task { await fetchAll() }
    }

    private func badge(_ label: String, _ value: String, _ color: Color) -> some View {
        HStack(spacing: 4) {
            Text(label)
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
        }
    }

    var proofList: some View {
        ScrollView {
            LazyVStack(spacing: 2) {
                ForEach(Array(proofs.enumerated()), id: \.offset) { _, proof in
                    Button {
                        selectedProof = proof
                    } label: {
                        HStack(spacing: 10) {
                            // Tier badge
                            let tier = proof["tier"] as? String ?? "?"
                            Text(tier)
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundStyle(tierColor(tier))
                                .frame(width: 30)

                            // Claim text
                            Text(proof["claim"] as? String ?? proof["prompt"] as? String ?? "—")
                                .font(.system(size: 12, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.8))
                                .lineLimit(2)
                                .frame(maxWidth: .infinity, alignment: .leading)

                            // Agreement
                            if let score = proof["agreement_score"] as? Double {
                                Text("\(Int(score * 100))%")
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                    .foregroundStyle(score > 0.7 ? RheaTheme.green : score > 0.4 ? RheaTheme.amber : RheaTheme.red)
                            }

                            // Seal icon
                            Image(systemName: "checkmark.seal.fill")
                                .font(.system(size: 10))
                                .foregroundStyle(RheaTheme.green.opacity(0.5))
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(selectedProof?["id"] as? String == proof["id"] as? String
                                      ? RheaTheme.accent.opacity(0.1)
                                      : RheaTheme.card.opacity(0.5))
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
    }

    func proofDetail(_ proof: [String: Any]) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                // Header
                HStack {
                    Text("PROOF DETAIL")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(RheaTheme.accent.opacity(0.5))
                    Spacer()
                    Button { selectedProof = nil } label: {
                        Text("CLOSE")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }

                // Claim
                VStack(alignment: .leading, spacing: 4) {
                    Text("CLAIM")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Text(proof["claim"] as? String ?? proof["prompt"] as? String ?? "—")
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundStyle(.white)
                        .textSelection(.enabled)
                }
                .glassCard()

                // Metrics row
                HStack(spacing: 12) {
                    if let score = proof["agreement_score"] as? Double {
                        metricBox("AGREEMENT", "\(Int(score * 100))%", score > 0.7 ? RheaTheme.green : RheaTheme.amber)
                    }
                    if let conf = proof["confidence"] as? Double {
                        metricBox("CONFIDENCE", "\(Int(conf * 100))%", conf > 0.7 ? RheaTheme.green : RheaTheme.amber)
                    }
                    metricBox("TIER", proof["tier"] as? String ?? "?", RheaTheme.accent)
                    if let models = proof["models_responded"] as? Int {
                        metricBox("MODELS", "\(models)", .white)
                    }
                }

                // Verdict
                if let verdict = proof["verdict"] as? String ?? proof["response"] as? String {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("VERDICT")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Text(verdict)
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.8))
                            .textSelection(.enabled)
                    }
                    .glassCard()
                }

                // Timestamp
                if let ts = proof["created_at"] as? String ?? proof["ts"] as? String {
                    HStack {
                        Text("CREATED")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Text(ts)
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.4))
                    }
                }
            }
            .padding(16)
        }
    }

    var ontologyGrid: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("ONTOLOGIES")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))
                .padding(.horizontal, 16)
                .padding(.top, 12)

            ScrollView {
                LazyVStack(spacing: 4) {
                    ForEach(Array(ontologies.enumerated()), id: \.offset) { _, ont in
                        HStack(spacing: 10) {
                            Image(systemName: "circle.hexagonpath")
                                .font(.system(size: 12))
                                .foregroundStyle(RheaTheme.accent)

                            Text(ont["name"] as? String ?? "—")
                                .font(.system(size: 12, weight: .semibold, design: .monospaced))
                                .foregroundStyle(.white)

                            Spacer()

                            if let count = ont["hypothesis_count"] as? Int {
                                Text("\(count) hyp")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundStyle(.secondary)
                            }

                            if let status = ont["status"] as? String {
                                Text(status.uppercased())
                                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                                    .foregroundStyle(status == "active" ? RheaTheme.green : .secondary)
                            }
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(RheaTheme.card.opacity(0.5))
                        )
                    }
                }
                .padding(.horizontal, 12)
            }

            if ontologies.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "function")
                        .font(.system(size: 24))
                        .foregroundStyle(.white.opacity(0.15))
                    Text("No ontologies loaded")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.3))
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    func metricBox(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 16, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
            Text(label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .glassCard()
    }

    func tierColor(_ tier: String) -> Color {
        switch tier.lowercased() {
        case "t0": return RheaTheme.green
        case "t1": return RheaTheme.accent
        case "t2": return RheaTheme.amber
        case "t3": return RheaTheme.red
        default: return .secondary
        }
    }

    func fetchAll() async {
        loading = true
        defer { loading = false }
        proofs = (try? await api.proofs()) ?? []
        ontologies = (try? await api.ontologies()) ?? []
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - Ruliad View (Ontology Engine + Verification)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct RuliadView: View {
    @State private var ontologies: [[String: Any]] = []
    @State private var selectedOntology: String? = nil
    @State private var hypotheses: [[String: Any]] = []
    @State private var loading = true
    private let api = RheaAPI.shared

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("RULIAD · ONTOLOGY ENGINE")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.7))

                Spacer()

                if let sel = selectedOntology {
                    Text(sel.uppercased())
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(RheaTheme.green)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Capsule().fill(RheaTheme.green.opacity(0.15)))
                }

                Button { Task { await fetchOntologies() } } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11))
                        .foregroundStyle(RheaTheme.accent)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)

            Divider().overlay(RheaTheme.accent.opacity(0.08))

            if loading && ontologies.isEmpty {
                Spacer()
                ProgressView().controlSize(.small)
                Spacer()
            } else {
                HSplitView {
                    // Ontology selector
                    ontologySelector
                        .frame(minWidth: 200, maxWidth: 250)

                    // Hypothesis space
                    hypothesisSpace
                }
            }
        }
        .background(RheaTheme.bg)
        .task { await fetchOntologies() }
    }

    var ontologySelector: some View {
        ScrollView {
            VStack(spacing: 2) {
                ForEach(Array(ontologies.enumerated()), id: \.offset) { _, ont in
                    let name = ont["name"] as? String ?? "—"
                    Button {
                        selectedOntology = name
                        Task { await fetchHypotheses(name) }
                    } label: {
                        HStack(spacing: 10) {
                            Image(systemName: "circle.hexagonpath")
                                .font(.system(size: 11))
                                .foregroundStyle(selectedOntology == name ? RheaTheme.accent : .secondary)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(name.uppercased())
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                    .foregroundStyle(selectedOntology == name ? .white : .secondary)

                                if let desc = ont["description"] as? String {
                                    Text(desc)
                                        .font(.system(size: 9, design: .monospaced))
                                        .foregroundStyle(.white.opacity(0.3))
                                        .lineLimit(1)
                                }
                            }

                            Spacer()

                            if let count = ont["hypothesis_count"] as? Int, count > 0 {
                                Text("\(count)")
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .foregroundStyle(RheaTheme.accent.opacity(0.6))
                            }
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(selectedOntology == name
                                      ? RheaTheme.accent.opacity(0.1) : .clear)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(8)
        }
    }

    var hypothesisSpace: some View {
        VStack(alignment: .leading, spacing: 0) {
            if selectedOntology == nil {
                Spacer()
                VStack(spacing: 12) {
                    Image(systemName: "function")
                        .font(.system(size: 36))
                        .foregroundStyle(.white.opacity(0.1))
                    Text("Select an ontology")
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.25))
                    Text("Explore hypothesis spaces and verification chains")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.12))
                }
                .frame(maxWidth: .infinity)
                Spacer()
            } else if hypotheses.isEmpty {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "leaf")
                        .font(.system(size: 24))
                        .foregroundStyle(.white.opacity(0.15))
                    Text("Empty ontology")
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.3))
                }
                .frame(maxWidth: .infinity)
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: 4) {
                        ForEach(Array(hypotheses.enumerated()), id: \.offset) { _, hyp in
                            hypothesisRow(hyp)
                        }
                    }
                    .padding(12)
                }
            }
        }
    }

    func hypothesisRow(_ hyp: [String: Any]) -> some View {
        HStack(spacing: 10) {
            // Status icon
            let status = hyp["status"] as? String ?? "proposed"
            Image(systemName: statusIcon(status))
                .font(.system(size: 11))
                .foregroundStyle(statusColor(status))

            // Claim
            Text(hyp["claim"] as? String ?? hyp["hypothesis"] as? String ?? "—")
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.white.opacity(0.8))
                .lineLimit(2)
                .frame(maxWidth: .infinity, alignment: .leading)

            // Status badge
            Text(status.uppercased())
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(statusColor(status))
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(
                    Capsule().fill(statusColor(status).opacity(0.15))
                )

            // Confidence
            if let conf = hyp["confidence"] as? Double {
                Text("\(Int(conf * 100))%")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(conf > 0.7 ? RheaTheme.green : RheaTheme.amber)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(RheaTheme.card.opacity(0.5))
        )
    }

    func statusIcon(_ status: String) -> String {
        switch status {
        case "accepted": return "checkmark.circle.fill"
        case "rejected": return "xmark.circle.fill"
        case "verified": return "checkmark.seal.fill"
        case "proposed": return "questionmark.circle"
        default: return "circle"
        }
    }

    func statusColor(_ status: String) -> Color {
        switch status {
        case "accepted", "verified": return RheaTheme.green
        case "rejected": return RheaTheme.red
        case "proposed": return RheaTheme.amber
        default: return .secondary
        }
    }

    func fetchOntologies() async {
        loading = true
        defer { loading = false }
        ontologies = (try? await api.ontologies()) ?? []
    }

    func fetchHypotheses(_ ontology: String) async {
        hypotheses = (try? await api.ontologyDetail(ontology)) ?? []
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - Infra View (Fly.io, GCloud, NDI, Models)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct InfraView: View {
    @ObservedObject private var store = RheaStore.shared
    @State private var providers: [InfraModels.ProviderInfo] = []
    @State private var ndiStatus: [String: Any]? = nil
    @State private var modelCount = 0
    @State private var providerCount = 0
    @State private var loading = true
    private let api = RheaAPI.shared

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("INFRA · DEPLOYMENT STATUS")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.7))

                Spacer()

                Button { Task { await fetchAll() } } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11))
                        .foregroundStyle(RheaTheme.accent)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)

            Divider().overlay(RheaTheme.accent.opacity(0.08))

            if loading && store.health == nil {
                Spacer()
                ProgressView().controlSize(.small)
                Spacer()
            } else {
                ScrollView {
                    VStack(spacing: 12) {
                        // Deployment cards row
                        HStack(spacing: 12) {
                            deploymentCard(
                                name: "FLY.IO",
                                icon: "airplane",
                                status: store.health != nil ? "LIVE" : "DOWN",
                                alive: store.health != nil,
                                details: [
                                    ("Region", "ams"),
                                    ("Profile", store.health?.execution_profile ?? "—"),
                                    ("Analyzer", store.health?.analyzer_version ?? "—"),
                                ]
                            )

                            deploymentCard(
                                name: "GCLOUD",
                                icon: "cloud",
                                status: "STANDBY",
                                alive: false,
                                details: [
                                    ("Project", "rhea-tribunal"),
                                    ("Region", "europe-west1"),
                                    ("Service", "Cloud Run"),
                                ]
                            )

                            deploymentCard(
                                name: "NDI",
                                icon: "video",
                                status: ndiStatus?["status"] as? String == "ok" ? "LIVE" : "N/A",
                                alive: ndiStatus?["status"] as? String == "ok",
                                details: [
                                    ("Module", ndiStatus?["module"] as? String ?? "not loaded"),
                                    ("Sources", "\(ndiStatus?["source_count"] as? Int ?? 0)"),
                                    ("Protocol", "NDI 6"),
                                ]
                            )
                        }

                        // Provider/Model summary
                        HStack(spacing: 12) {
                            infraMetric("PROVIDERS", "\(providerCount)", "server.rack", RheaTheme.green)
                            infraMetric("MODELS", "\(modelCount)", "cpu", RheaTheme.accent)
                            infraMetric("STATUS", store.health?.status ?? "—", "heart.fill", store.health != nil ? RheaTheme.green : RheaTheme.red)
                            infraMetric("MODE", store.health?.profile_mode ?? "—", "slider.horizontal.3", RheaTheme.amber)
                        }

                        // Provider list
                        VStack(alignment: .leading, spacing: 6) {
                            Text("MODEL PROVIDERS")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(RheaTheme.accent.opacity(0.5))
                                .padding(.horizontal, 4)

                            ForEach(providers) { prov in
                                providerRow(prov)
                            }
                        }
                        .padding(.horizontal, 12)

                        // API endpoint
                        HStack {
                            Text("ENDPOINT")
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundStyle(.secondary)
                            Text(api.baseURL)
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundStyle(RheaTheme.accent)
                                .textSelection(.enabled)
                            Spacer()
                            Circle()
                                .fill(store.connectionAlive ? RheaTheme.green : RheaTheme.red)
                                .frame(width: 8, height: 8)
                        }
                        .glassCard()
                        .padding(.horizontal, 12)
                    }
                    .padding(16)
                }
            }
        }
        .background(RheaTheme.bg)
        .task { await fetchAll() }
    }

    func deploymentCard(name: String, icon: String, status: String, alive: Bool, details: [(String, String)]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(alive ? RheaTheme.green : .secondary)

                Text(name)
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)

                Spacer()

                Text(status)
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(alive ? RheaTheme.green : .secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(
                        Capsule().fill((alive ? RheaTheme.green : Color.secondary).opacity(0.15))
                    )
            }

            ForEach(details, id: \.0) { label, value in
                HStack {
                    Text(label)
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text(value)
                        .font(.system(size: 10, weight: .semibold, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.7))
                }
            }
        }
        .glassCard()
    }

    func infraMetric(_ label: String, _ value: String, _ icon: String, _ color: Color) -> some View {
        VStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundStyle(color)
            Text(value)
                .font(.system(size: 16, weight: .bold, design: .monospaced))
                .foregroundStyle(.white)
            Text(label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .glassCard()
    }

    func providerRow(_ prov: InfraModels.ProviderInfo) -> some View {
        HStack(spacing: 10) {
            Circle()
                .fill((prov.available ?? false) ? RheaTheme.green : RheaTheme.red)
                .frame(width: 6, height: 6)

            Text(prov.name)
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundStyle(.white.opacity(0.8))

            Spacer()

            if let models = prov.model_count {
                Text("\(models) models")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            if let tier = prov.tier {
                Text(tier)
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.6))
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(RheaTheme.card.opacity(0.5))
        )
    }

    func fetchAll() async {
        loading = true
        defer { loading = false }

        // Models/providers (typed)
        if let resp = try? await api.models() {
            providers = resp.providers ?? []
            providerCount = providers.filter { $0.available ?? false }.count
            modelCount = resp.total_models ?? 0
        }

        // NDI status
        ndiStatus = try? await api.ndi()
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - Menu Bar Widget
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct MenuBarView: View {
    @ObservedObject private var store = RheaStore.shared

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("RHEA PLAY")
                    .font(.system(size: 10, weight: .black, design: .monospaced))
                    .foregroundStyle(.white)
                Spacer()
                Circle()
                    .fill(store.connectionAlive ? Color.green : Color.red)
                    .frame(width: 6, height: 6)
            }

            Divider()

            if store.agents.isEmpty {
                Text("connecting...")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)
            } else {
                ForEach(store.agents) { agent in
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
                Text("T:\(store.formatTokens(store.totalTokens))")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.5))
                Spacer()
                Text("$\(String(format: "%.2f", store.totalCost))")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.amber)
            }
        }
        .padding(12)
        .frame(width: 220)
    }
}
#endif
