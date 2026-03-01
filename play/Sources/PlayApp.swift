import SwiftUI
import Pow
import RheaKit

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
        case radio, dialog, governor, tasks, pulse, atlas, history, aletheia, ruliad, processes, models, ndi, settings
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
            case .processes: return "PROCS"
            case .models: return "MODELS"
            case .ndi: return "NDI"
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
            case .processes: return "terminal"
            case .models: return "cpu"
            case .ndi: return "video.badge.waveform"
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
            case .processes: return "0"
            case .models: return "-"
            case .ndi: return "="
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
            case .processes: ProcessesView()
            case .models: ModelsView()
            case .ndi: NDIFlowView()
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
// MARK: - Processes View (Supervisor sessions — spawn/kill/output)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct ProcessesView: View {
    @ObservedObject private var store = RheaStore.shared
    @State private var sessions: [SupervisorSession] = []
    @State private var selectedSession: SupervisorSession? = nil
    @State private var sessionOutput = ""
    @State private var inputText = ""
    @State private var loading = true
    @State private var spawnAgent = "rex"
    @State private var spawnPrompt = ""
    @State private var showSpawnSheet = false
    @State private var outputAutoRefresh: Timer? = nil
    private let api = RheaAPI.shared

    private let knownAgents = ["rex", "orion", "gemini", "hyperion", "shared", "b2"]

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("PROCESSES · SUPERVISOR")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.7))

                Spacer()

                // Counts
                let running = sessions.filter { $0.isAlive }.count
                HStack(spacing: 10) {
                    badge("RUNNING", "\(running)", RheaTheme.green)
                    badge("TOTAL", "\(sessions.count)", .white)
                }

                Button {
                    showSpawnSheet.toggle()
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "plus.circle.fill")
                        Text("SPAWN")
                    }
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.green)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Capsule().fill(RheaTheme.green.opacity(0.15)))
                }
                .buttonStyle(.plain)

                Button { Task { await fetchSessions() } } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11))
                        .foregroundStyle(RheaTheme.accent)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)

            Divider().overlay(RheaTheme.accent.opacity(0.08))

            if loading && sessions.isEmpty {
                Spacer()
                ProgressView().controlSize(.small)
                Spacer()
            } else {
                HSplitView {
                    // Left: session list + agent quick-actions
                    VStack(spacing: 0) {
                        // Agent quick-action row
                        agentQuickActions
                        Divider().overlay(RheaTheme.accent.opacity(0.05))
                        sessionList
                    }
                    .frame(minWidth: 300)

                    // Right: selected session output
                    sessionDetail
                        .frame(minWidth: 350)
                }
            }
        }
        .background(RheaTheme.bg)
        .task { await fetchSessions() }
        .sheet(isPresented: $showSpawnSheet) { spawnSheet }
        .onDisappear { outputAutoRefresh?.invalidate() }
    }

    // Quick action row: wake buttons for known agents
    var agentQuickActions: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                ForEach(store.agents) { agent in
                    Button {
                        Task { _ = try? await api.wakeAgent(agent.name) }
                    } label: {
                        HStack(spacing: 4) {
                            Circle()
                                .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                                .frame(width: 5, height: 5)
                            Text(agent.name.prefix(3).uppercased())
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                            Image(systemName: "bolt.fill")
                                .font(.system(size: 7))
                        }
                        .foregroundStyle(agent.alive ? .secondary : RheaTheme.amber)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 5)
                        .background(
                            Capsule()
                                .fill(RheaTheme.card)
                                .overlay(Capsule().stroke(agent.alive ? RheaTheme.green.opacity(0.1) : RheaTheme.amber.opacity(0.2), lineWidth: 1))
                        )
                    }
                    .buttonStyle(.plain)
                    .help("Wake \(agent.name)")
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
    }

    var sessionList: some View {
        ScrollView {
            LazyVStack(spacing: 2) {
                if sessions.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "terminal")
                            .font(.system(size: 28))
                            .foregroundStyle(.white.opacity(0.12))
                        Text("No supervisor sessions")
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.25))
                        Text("Spawn a new agent to start")
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.12))
                    }
                    .padding(.top, 60)
                } else {
                    ForEach(sessions) { sess in
                        sessionRow(sess)
                    }
                }
            }
            .padding(8)
        }
    }

    func sessionRow(_ sess: SupervisorSession) -> some View {
        Button {
            selectedSession = sess
            Task { await fetchOutput(sess.id) }
            startOutputPolling(sess.id)
        } label: {
            HStack(spacing: 10) {
                // State indicator
                Circle()
                    .fill(sess.isAlive ? RheaTheme.green : RheaTheme.red)
                    .frame(width: 7, height: 7)

                // Agent + session ID
                VStack(alignment: .leading, spacing: 2) {
                    Text(sess.agent?.uppercased() ?? "UNKNOWN")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(.white)

                    Text(String(sess.id.prefix(8)))
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.3))
                }

                Spacer()

                // Status badge
                Text((sess.status ?? "?").uppercased())
                    .font(.system(size: 8, weight: .bold, design: .monospaced))
                    .foregroundStyle(sess.isAlive ? RheaTheme.green : .secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Capsule().fill((sess.isAlive ? RheaTheme.green : Color.secondary).opacity(0.12)))

                // PID
                if let pid = sess.pid {
                    Text("PID \(pid)")
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.2))
                }

                // Kill button (only for alive sessions)
                if sess.isAlive {
                    Button {
                        Task {
                            _ = try? await api.supervisorKill(sessionId: sess.id)
                            await fetchSessions()
                        }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 12))
                            .foregroundStyle(RheaTheme.red.opacity(0.6))
                    }
                    .buttonStyle(.plain)
                    .help("Kill session")
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .fill(selectedSession?.id == sess.id ? RheaTheme.accent.opacity(0.1) : RheaTheme.card.opacity(0.4))
            )
        }
        .buttonStyle(.plain)
    }

    // Right panel: session output + input
    var sessionDetail: some View {
        VStack(spacing: 0) {
            if let sess = selectedSession {
                // Header
                HStack {
                    Text("\(sess.agent?.uppercased() ?? "?") · \(String(sess.id.prefix(8)))")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(RheaTheme.accent)

                    Spacer()

                    if let ts = sess.started_at {
                        Text(ts)
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.3))
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)

                Divider().overlay(RheaTheme.accent.opacity(0.05))

                // Output (terminal-like)
                ScrollView {
                    Text(sessionOutput.isEmpty ? "⏳ Waiting for output..." : sessionOutput)
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(RheaTheme.green.opacity(0.8))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .textSelection(.enabled)
                        .padding(12)
                }
                .background(Color.black.opacity(0.3))

                // Input bar (for alive sessions)
                if sess.isAlive {
                    HStack(spacing: 8) {
                        Text(">")
                            .font(.system(size: 12, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.green)

                        TextField("Send input to session...", text: $inputText)
                            .textFieldStyle(.plain)
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundColor(.white)
                            .onSubmit { sendInput() }

                        Button(action: sendInput) {
                            Image(systemName: "arrow.right.circle.fill")
                                .font(.system(size: 16))
                                .foregroundStyle(RheaTheme.accent)
                        }
                        .buttonStyle(.plain)
                        .disabled(inputText.isEmpty)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(RheaTheme.card.opacity(0.6))
                }
            } else {
                Spacer()
                VStack(spacing: 12) {
                    Image(systemName: "terminal")
                        .font(.system(size: 36))
                        .foregroundStyle(.white.opacity(0.1))
                    Text("Select a session to view output")
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.25))
                }
                Spacer()
            }
        }
    }

    var spawnSheet: some View {
        VStack(spacing: 16) {
            Text("SPAWN AGENT SESSION")
                .font(.system(size: 12, weight: .bold, design: .monospaced))
                .foregroundStyle(.white)

            // Agent picker
            HStack(spacing: 6) {
                ForEach(knownAgents, id: \.self) { agent in
                    Button {
                        spawnAgent = agent
                    } label: {
                        Text(agent.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(
                                Capsule().fill(spawnAgent == agent ? RheaTheme.accent.opacity(0.2) : RheaTheme.card)
                            )
                            .foregroundStyle(spawnAgent == agent ? RheaTheme.accent : .secondary)
                    }
                    .buttonStyle(.plain)
                }
            }

            // Prompt
            TextField("Optional prompt...", text: $spawnPrompt, axis: .vertical)
                .textFieldStyle(.plain)
                .font(.system(size: 12, design: .monospaced))
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 8).fill(RheaTheme.card))
                .lineLimit(3...6)

            // Actions
            HStack {
                Button("Cancel") { showSpawnSheet = false }
                    .buttonStyle(.plain)
                    .foregroundStyle(.secondary)

                Spacer()

                Button {
                    Task {
                        _ = try? await api.supervisorSpawn(
                            agent: spawnAgent,
                            prompt: spawnPrompt.isEmpty ? nil : spawnPrompt
                        )
                        showSpawnSheet = false
                        await fetchSessions()
                    }
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "play.fill")
                        Text("SPAWN")
                    }
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Capsule().fill(RheaTheme.green))
                }
                .buttonStyle(.plain)
            }
        }
        .padding(24)
        .frame(width: 420)
        .background(RheaTheme.bg)
    }

    func badge(_ label: String, _ value: String, _ color: Color) -> some View {
        HStack(spacing: 4) {
            Text(label)
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
        }
    }

    func fetchSessions() async {
        loading = true
        defer { loading = false }
        sessions = (try? await api.supervisorSessions()) ?? []
    }

    func fetchOutput(_ sessionId: String) async {
        sessionOutput = (try? await api.supervisorOutput(sessionId: sessionId)) ?? ""
    }

    func sendInput() {
        guard let sess = selectedSession, !inputText.isEmpty else { return }
        let text = inputText
        inputText = ""
        Task {
            _ = try? await api.supervisorInput(sessionId: sess.id, text: text)
            await fetchOutput(sess.id)
        }
    }

    func startOutputPolling(_ sessionId: String) {
        outputAutoRefresh?.invalidate()
        outputAutoRefresh = Timer.scheduledTimer(withTimeInterval: 3, repeats: true) { _ in
            Task { @MainActor in await fetchOutput(sessionId) }
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - Models View (Providers + Execution Profile + Governor)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct ModelsView: View {
    @ObservedObject private var store = RheaStore.shared
    @State private var providers: [InfraModels.ProviderInfo] = []
    @State private var activeProfile = "safe_cheap"
    @State private var governorStatuses: [String: GovernorAgentStatus] = [:]
    @State private var loading = true
    @State private var liveTestRunning = false
    private let api = RheaAPI.shared

    private let profiles = ["safe_cheap", "balanced", "deep"]

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("MODELS · EXECUTION CONTROL")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.7))

                Spacer()

                // Live test button
                Button {
                    Task { await runLiveTest() }
                } label: {
                    HStack(spacing: 4) {
                        if liveTestRunning {
                            ProgressView().controlSize(.mini)
                        } else {
                            Image(systemName: "bolt.fill")
                        }
                        Text("LIVE TEST")
                    }
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(liveTestRunning ? .secondary : RheaTheme.amber)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Capsule().fill(RheaTheme.amber.opacity(0.12)))
                }
                .buttonStyle(.plain)
                .disabled(liveTestRunning)

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

            if loading && providers.isEmpty {
                Spacer()
                ProgressView().controlSize(.small)
                Spacer()
            } else {
                ScrollView {
                    VStack(spacing: 16) {
                        // Execution profile switcher
                        executionProfileSwitcher

                        // Provider roster
                        providerRoster

                        // Governor status per agent
                        governorGrid

                        // Summary metrics
                        summaryMetrics
                    }
                    .padding(16)
                }
            }
        }
        .background(RheaTheme.bg)
        .task { await fetchAll() }
    }

    // Execution profile switcher: safe_cheap | balanced | deep
    var executionProfileSwitcher: some View {
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
                                .font(.system(size: 16))
                            Text(profile.replacingOccurrences(of: "_", with: " ").uppercased())
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                            Text(profileDescription(profile))
                                .font(.system(size: 8, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.3))
                        }
                        .foregroundStyle(activeProfile == profile ? profileColor(profile) : .secondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(
                            RoundedRectangle(cornerRadius: activeProfile == profile ? 8 : 0)
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

    var providerRoster: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("PROVIDER ROSTER")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            ForEach(providers) { prov in
                HStack(spacing: 10) {
                    // Health dot
                    Circle()
                        .fill((prov.available ?? false) ? RheaTheme.green : RheaTheme.red)
                        .frame(width: 8, height: 8)

                    // Name
                    Text(prov.name.uppercased())
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(.white)

                    Spacer()

                    // Model count
                    if let count = prov.model_count {
                        Text("\(count)")
                            .font(.system(size: 12, weight: .bold, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.6))
                        Text("models")
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }

                    // Tier
                    if let tier = prov.tier {
                        Text(tier.uppercased())
                            .font(.system(size: 8, weight: .bold, design: .monospaced))
                            .foregroundStyle(tierColor(tier))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Capsule().fill(tierColor(tier).opacity(0.12)))
                    }

                    // Status
                    Text((prov.available ?? false) ? "UP" : "DOWN")
                        .font(.system(size: 8, weight: .bold, design: .monospaced))
                        .foregroundStyle((prov.available ?? false) ? RheaTheme.green : RheaTheme.red)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 6)
                        .fill(RheaTheme.card.opacity(0.5))
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke((prov.available ?? false) ? RheaTheme.green.opacity(0.08) : RheaTheme.red.opacity(0.08), lineWidth: 1)
                        )
                )
            }
        }
    }

    var governorGrid: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("GOVERNOR · BUDGET ENFORCEMENT")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
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

                        HStack(spacing: 12) {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("T/day")
                                    .font(.system(size: 8, design: .monospaced))
                                    .foregroundStyle(.secondary)
                                Text(store.formatTokens(status.T_day ?? 0))
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                                    .foregroundStyle(.white)
                            }

                            VStack(alignment: .leading, spacing: 2) {
                                Text("$/day")
                                    .font(.system(size: 8, design: .monospaced))
                                    .foregroundStyle(.secondary)
                                Text(String(format: "$%.3f", status.dollar_day ?? 0))
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                                    .foregroundStyle(RheaTheme.amber)
                            }

                            Spacer()

                            VStack(alignment: .trailing, spacing: 2) {
                                Text("PACE")
                                    .font(.system(size: 8, design: .monospaced))
                                    .foregroundStyle(.secondary)
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
                                    RoundedRectangle(cornerRadius: 2)
                                        .fill(.white.opacity(0.05))
                                    RoundedRectangle(cornerRadius: 2)
                                        .fill(pct > 0.9 ? RheaTheme.red : pct > 0.7 ? RheaTheme.amber : RheaTheme.green)
                                        .frame(width: geo.size.width * pct)
                                }
                            }
                            .frame(height: 3)
                        }
                    }
                    .padding(10)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(RheaTheme.card.opacity(0.5))
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(RheaTheme.cardBorder, lineWidth: 1))
                    )
                }
            }
        }
    }

    var summaryMetrics: some View {
        HStack(spacing: 12) {
            summaryBox("PROVIDERS", "\(providers.filter { $0.available ?? false }.count)/\(providers.count)", "server.rack", RheaTheme.green)
            summaryBox("MODELS", "\(store.health?.total_models ?? 0)", "cpu", RheaTheme.accent)
            summaryBox("PROFILE", activeProfile.replacingOccurrences(of: "_", with: " ").uppercased(), "slider.horizontal.3", profileColor(activeProfile))
            summaryBox("STATUS", store.health?.status ?? "—", "heart.fill", store.connectionAlive ? RheaTheme.green : RheaTheme.red)
        }
    }

    func summaryBox(_ label: String, _ value: String, _ icon: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 14))
                .foregroundStyle(color)
            Text(value)
                .font(.system(size: 12, weight: .bold, design: .monospaced))
                .foregroundStyle(.white)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            Text(label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .glassCard()
    }

    func profileIcon(_ p: String) -> String {
        switch p {
        case "safe_cheap": return "leaf.fill"
        case "balanced": return "scale.3d"
        case "deep": return "brain.head.profile"
        default: return "questionmark"
        }
    }

    func profileDescription(_ p: String) -> String {
        switch p {
        case "safe_cheap": return "DeepSeek + HF"
        case "balanced": return "OpenRouter + Gemini"
        case "deep": return "Anthropic Opus"
        default: return ""
        }
    }

    func profileColor(_ p: String) -> Color {
        switch p {
        case "safe_cheap": return RheaTheme.green
        case "balanced": return RheaTheme.amber
        case "deep": return .purple
        default: return .secondary
        }
    }

    func tierColor(_ tier: String) -> Color {
        switch tier.lowercased() {
        case "cheap": return RheaTheme.green
        case "balanced": return RheaTheme.amber
        case "expensive": return .orange
        case "deep": return .purple
        default: return .secondary
        }
    }

    func modeColor(_ mode: String) -> Color {
        switch mode.lowercased() {
        case "normal": return RheaTheme.green
        case "compact": return RheaTheme.amber
        case "enforcement": return RheaTheme.red
        case "shadow": return .purple
        default: return .secondary
        }
    }

    func paceColor(_ pace: String) -> Color {
        switch pace.lowercased() {
        case "on_track", "normal": return RheaTheme.green
        case "over": return RheaTheme.amber
        case "critical": return RheaTheme.red
        default: return .secondary
        }
    }

    func fetchAll() async {
        loading = true
        defer { loading = false }

        // Providers
        if let resp = try? await api.models() {
            providers = resp.providers ?? []
        }

        // Active profile
        if let profile = try? await api.executionProfile() {
            activeProfile = profile["active"] as? String ?? profile["profile"] as? String ?? "safe_cheap"
        }

        // Governor statuses
        governorStatuses = (try? await api.governorAll()) ?? [:]
    }

    func runLiveTest() async {
        liveTestRunning = true
        defer { liveTestRunning = false }
        // Trigger health with live_test=true to ping all providers
        _ = try? await api.getJSON("/health?live_test=true")
        // Refresh providers after test
        if let resp = try? await api.models() {
            providers = resp.providers ?? []
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARK: - NDI Flow View (Source Discovery + Test Patterns + Flow Monitor)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

struct NDIFlowView: View {
    @State private var ndiAvailable = false
    @State private var ndiVersion = "—"
    @State private var sources: [NDISource] = []
    @State private var sourceCount = 0
    @State private var loading = true
    @State private var discovering = false
    @State private var testSending = false
    @State private var testResult: String? = nil
    @State private var lastDiscovery = Date.distantPast
    private let api = RheaAPI.shared

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("NDI · FLOW MONITOR")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.7))

                Spacer()

                // NDI status dot
                HStack(spacing: 4) {
                    Circle()
                        .fill(ndiAvailable ? RheaTheme.green : RheaTheme.red)
                        .frame(width: 6, height: 6)
                    Text(ndiAvailable ? "NDI READY" : "NDI UNAVAILABLE")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(ndiAvailable ? RheaTheme.green : RheaTheme.red)
                }

                Button { Task { await fetchStatus() } } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11))
                        .foregroundStyle(RheaTheme.accent)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)

            Divider().overlay(RheaTheme.accent.opacity(0.08))

            if loading {
                Spacer()
                ProgressView().controlSize(.small)
                Spacer()
            } else {
                ScrollView {
                    VStack(spacing: 16) {
                        // Status overview
                        ndiStatusPanel

                        // Action buttons
                        ndiActions

                        // Source list
                        ndiSourceList

                        // NDI flow visualization
                        ndiFlowDiagram
                    }
                    .padding(16)
                }
            }
        }
        .background(RheaTheme.bg)
        .task { await fetchStatus() }
    }

    var ndiStatusPanel: some View {
        HStack(spacing: 12) {
            ndiMetric("STATUS", ndiAvailable ? "ONLINE" : "OFFLINE", "antenna.radiowaves.left.and.right", ndiAvailable ? RheaTheme.green : RheaTheme.red)
            ndiMetric("VERSION", ndiVersion, "info.circle", RheaTheme.accent)
            ndiMetric("SOURCES", "\(sourceCount)", "video.badge.waveform", sourceCount > 0 ? RheaTheme.green : .secondary)
            ndiMetric("PROTOCOL", "NDI 6", "network", RheaTheme.accent)
        }
    }

    var ndiActions: some View {
        HStack(spacing: 12) {
            // Discover sources
            Button {
                Task { await discoverSources() }
            } label: {
                HStack(spacing: 6) {
                    if discovering {
                        ProgressView().controlSize(.mini)
                    } else {
                        Image(systemName: "magnifyingglass")
                    }
                    Text("DISCOVER SOURCES")
                }
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(RheaTheme.accent.opacity(0.1))
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(RheaTheme.accent.opacity(0.2), lineWidth: 1))
                )
            }
            .buttonStyle(.plain)
            .disabled(discovering || !ndiAvailable)

            // Send test pattern
            Button {
                Task { await sendTestPattern() }
            } label: {
                HStack(spacing: 6) {
                    if testSending {
                        ProgressView().controlSize(.mini)
                    } else {
                        Image(systemName: "rectangle.inset.filled.and.person.filled")
                    }
                    Text("SEND TEST PATTERN")
                }
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.amber)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(RheaTheme.amber.opacity(0.1))
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(RheaTheme.amber.opacity(0.2), lineWidth: 1))
                )
            }
            .buttonStyle(.plain)
            .disabled(testSending || !ndiAvailable)
        }
    }

    var ndiSourceList: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("DISCOVERED SOURCES")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent.opacity(0.5))

                Spacer()

                if lastDiscovery != Date.distantPast {
                    Text("Last scan: \(lastDiscovery.formatted(.dateTime.hour().minute().second()))")
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.2))
                }
            }

            if sources.isEmpty {
                HStack {
                    Spacer()
                    VStack(spacing: 8) {
                        Image(systemName: "video.slash")
                            .font(.system(size: 24))
                            .foregroundStyle(.white.opacity(0.12))
                        Text(ndiAvailable ? "No sources found — run discovery" : "NDI runtime not available on server")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.25))
                    }
                    .padding(.vertical, 24)
                    Spacer()
                }
            } else {
                ForEach(sources) { source in
                    HStack(spacing: 10) {
                        Image(systemName: "video.fill")
                            .font(.system(size: 12))
                            .foregroundStyle(RheaTheme.green)

                        VStack(alignment: .leading, spacing: 2) {
                            Text(source.name)
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white)

                            if let url = source.url {
                                Text(url)
                                    .font(.system(size: 9, design: .monospaced))
                                    .foregroundStyle(.white.opacity(0.3))
                            }
                        }

                        Spacer()

                        Circle()
                            .fill(RheaTheme.green)
                            .frame(width: 6, height: 6)

                        Text("ACTIVE")
                            .font(.system(size: 8, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.green)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(RheaTheme.card.opacity(0.5))
                            .overlay(RoundedRectangle(cornerRadius: 6).stroke(RheaTheme.green.opacity(0.1), lineWidth: 1))
                    )
                }
            }

            // Test result
            if let result = testResult {
                HStack(spacing: 8) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(RheaTheme.green)
                    Text(result)
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.7))
                }
                .padding(10)
                .background(
                    RoundedRectangle(cornerRadius: 6)
                        .fill(RheaTheme.green.opacity(0.08))
                )
            }
        }
    }

    var ndiFlowDiagram: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("FLOW TOPOLOGY")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            if sources.isEmpty {
                // No sources — show network scan prompt
                HStack {
                    Spacer()
                    VStack(spacing: 8) {
                        Image(systemName: "point.3.connected.trianglepath.dotted")
                            .font(.system(size: 28))
                            .foregroundStyle(.white.opacity(0.1))
                        Text("Run discovery to map flows")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.2))
                    }
                    .padding(.vertical, 24)
                    Spacer()
                }
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(RheaTheme.card.opacity(0.3))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(style: StrokeStyle(lineWidth: 1, dash: [4, 4]))
                                .foregroundStyle(.white.opacity(0.06))
                        )
                )
            } else {
                // Flow diagram: source nodes on left → hub → receivers on right
                Canvas { context, size in
                    let hubX = size.width * 0.5
                    let hubY = size.height * 0.5
                    let hubRadius: CGFloat = 18
                    let sourceSpacing = max(40, size.height / CGFloat(max(sources.count, 1) + 1))

                    // Draw hub (Rhea NDI router)
                    let hubRect = CGRect(x: hubX - hubRadius, y: hubY - hubRadius, width: hubRadius * 2, height: hubRadius * 2)
                    context.fill(Circle().path(in: hubRect), with: .color(RheaTheme.accent.opacity(0.15)))
                    context.stroke(Circle().path(in: hubRect), with: .color(RheaTheme.accent.opacity(0.4)), lineWidth: 1.5)

                    // Hub label
                    context.draw(
                        Text("NDI")
                            .font(.system(size: 8, weight: .black, design: .monospaced))
                            .foregroundStyle(RheaTheme.accent),
                        at: CGPoint(x: hubX, y: hubY)
                    )

                    // Draw source nodes on left
                    for (i, source) in sources.enumerated() {
                        let nodeY = sourceSpacing * CGFloat(i + 1)
                        let nodeX: CGFloat = 80
                        let nodeSize: CGFloat = 10

                        // Connection line: source → hub
                        var path = Path()
                        path.move(to: CGPoint(x: nodeX + nodeSize, y: nodeY))
                        // Bezier curve for smooth flow line
                        let cp1 = CGPoint(x: nodeX + (hubX - nodeX) * 0.4, y: nodeY)
                        let cp2 = CGPoint(x: hubX - (hubX - nodeX) * 0.3, y: hubY)
                        path.addCurve(to: CGPoint(x: hubX - hubRadius, y: hubY), control1: cp1, control2: cp2)
                        context.stroke(path, with: .color(RheaTheme.green.opacity(0.3)), lineWidth: 1)

                        // Animated pulse dot on line (uses source index for offset)
                        let pulseT = 0.3 + Double(i) * 0.15
                        let pulsePoint = path.trimmedPath(from: 0, to: pulseT).currentPoint ?? CGPoint(x: nodeX, y: nodeY)
                        let pulseDot = CGRect(x: pulsePoint.x - 2, y: pulsePoint.y - 2, width: 4, height: 4)
                        context.fill(Circle().path(in: pulseDot), with: .color(RheaTheme.green.opacity(0.6)))

                        // Source node
                        let nodeRect = CGRect(x: nodeX - nodeSize/2, y: nodeY - nodeSize/2, width: nodeSize, height: nodeSize)
                        context.fill(Circle().path(in: nodeRect), with: .color(RheaTheme.green))

                        // Source label
                        let shortName = source.name.components(separatedBy: " (").first ?? source.name
                        context.draw(
                            Text(shortName)
                                .font(.system(size: 9, weight: .semibold, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.6)),
                            at: CGPoint(x: nodeX - 30, y: nodeY),
                            anchor: .trailing
                        )

                        // IP label below
                        if let url = source.url {
                            let ip = url.components(separatedBy: ":").first ?? url
                            context.draw(
                                Text(ip)
                                    .font(.system(size: 7, design: .monospaced))
                                    .foregroundStyle(.white.opacity(0.2)),
                                at: CGPoint(x: nodeX - 30, y: nodeY + 11),
                                anchor: .trailing
                            )
                        }
                    }

                    // Draw output side (Rhea → broadcast)
                    let outX = size.width - 80
                    let outY = hubY

                    // Hub → output line
                    var outPath = Path()
                    outPath.move(to: CGPoint(x: hubX + hubRadius, y: hubY))
                    outPath.addLine(to: CGPoint(x: outX - 6, y: outY))
                    context.stroke(outPath, with: .color(RheaTheme.amber.opacity(0.3)), lineWidth: 1)

                    // Output node (broadcast)
                    let outRect = CGRect(x: outX - 5, y: outY - 5, width: 10, height: 10)
                    context.fill(Circle().path(in: outRect), with: .color(RheaTheme.amber))
                    context.draw(
                        Text("OUT")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.amber.opacity(0.7)),
                        at: CGPoint(x: outX + 25, y: outY)
                    )
                }
                .frame(height: max(150, CGFloat(sources.count + 1) * 50))
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color.black.opacity(0.2))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(RheaTheme.accent.opacity(0.08), lineWidth: 1)
                        )
                )

                // Legend
                HStack(spacing: 16) {
                    legendItem("Source", RheaTheme.green)
                    legendItem("Router", RheaTheme.accent)
                    legendItem("Output", RheaTheme.amber)
                    Spacer()
                    Text("\(sources.count) source\(sources.count == 1 ? "" : "s") mapped")
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.2))
                }
            }
        }
    }

    func legendItem(_ label: String, _ color: Color) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 6, height: 6)
            Text(label)
                .font(.system(size: 9, design: .monospaced))
                .foregroundStyle(.white.opacity(0.3))
        }
    }

    func ndiMetric(_ label: String, _ value: String, _ icon: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 14))
                .foregroundStyle(color)
            Text(value)
                .font(.system(size: 12, weight: .bold, design: .monospaced))
                .foregroundStyle(.white)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            Text(label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .glassCard()
    }

    func fetchStatus() async {
        loading = true
        defer { loading = false }
        if let status = try? await api.ndi() {
            ndiAvailable = status["status"] as? String == "ok"
            ndiVersion = status["version"] as? String ?? "—"
            sourceCount = status["source_count"] as? Int ?? 0
        }
    }

    func discoverSources() async {
        discovering = true
        defer { discovering = false }
        sources = (try? await api.ndiDiscover()) ?? []
        sourceCount = sources.count
        lastDiscovery = Date()
    }

    func sendTestPattern() async {
        testSending = true
        defer { testSending = false }
        let result = try? await api.ndiSendTest()
        testResult = result?["message"] as? String ?? "Test pattern sent"
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
