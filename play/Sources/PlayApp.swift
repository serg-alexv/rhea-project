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
// MARK: - Shared views: HistoryView, AletheiaView, RuliadView, ProcessesView, ModelsView
// Now imported from RheaKit shared package — local duplicates removed.
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    private let api = RheaAPI.shared
    @State private var sessionCount = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            // ── Header: RHEA + connection dot + show/hide ──
            HStack(spacing: 6) {
                Text("RHEA")
                    .font(.system(size: 10, weight: .black, design: .monospaced))
                    .foregroundStyle(.white)
                Circle()
                    .fill(store.connectionAlive ? Color.green : Color.red)
                    .frame(width: 6, height: 6)
                Spacer()
                Button {
                    NSApp.activate(ignoringOtherApps: true)
                    if let w = NSApp.windows.first(where: { $0.title.contains("Rhea") && $0.level == .normal }) {
                        w.makeKeyAndOrderFront(nil)
                    }
                } label: {
                    Text("CC")
                        .font(.system(size: 8, weight: .bold, design: .monospaced))
                        .padding(.horizontal, 5).padding(.vertical, 2)
                        .background(Capsule().fill(RheaTheme.accent.opacity(0.2)))
                }
                .buttonStyle(.plain)
                .foregroundStyle(RheaTheme.accent)

                Button { NSApp.hide(nil) } label: {
                    Image(systemName: "eye.slash").font(.system(size: 9))
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
            }

            // ── Metrics strip ──
            HStack(spacing: 0) {
                metricCell("T/day", store.formatTokens(store.totalTokens), .white)
                metricCell("$/day", String(format: "$%.2f", store.totalCost), RheaTheme.amber)
                metricCell("ALIVE", "\(store.aliveCount)/\(store.agents.count)", store.aliveCount > 0 ? RheaTheme.green : RheaTheme.red)
                metricCell("PROOFS", "\(store.proofCount)", RheaTheme.accent)
            }
            .padding(.vertical, 4)
            .background(RoundedRectangle(cornerRadius: 6).fill(RheaTheme.card.opacity(0.5)))

            // ── Health row ──
            if let h = store.health {
                HStack(spacing: 8) {
                    HStack(spacing: 3) {
                        Text("PROV").font(.system(size: 7, design: .monospaced)).foregroundStyle(.secondary)
                        Text("\(h.providers_available)/\(h.providers_total)")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(h.providers_available > 0 ? RheaTheme.green : RheaTheme.red)
                    }
                    HStack(spacing: 3) {
                        Text("MOD").font(.system(size: 7, design: .monospaced)).foregroundStyle(.secondary)
                        Text("\(h.total_models)")
                            .font(.system(size: 9, weight: .bold, design: .monospaced)).foregroundStyle(.white.opacity(0.6))
                    }
                    Spacer()
                    Text(h.execution_profile.replacingOccurrences(of: "_", with: " ").uppercased())
                        .font(.system(size: 7, weight: .bold, design: .monospaced))
                        .foregroundStyle(profileColor(h.execution_profile))
                        .padding(.horizontal, 4).padding(.vertical, 1)
                        .background(Capsule().fill(profileColor(h.execution_profile).opacity(0.15)))
                }
            }

            Divider().opacity(0.3)

            // ── Agent roster ──
            if store.agents.isEmpty {
                HStack {
                    ProgressView().controlSize(.mini)
                    Text("connecting...")
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
            } else {
                ForEach(store.agents) { agent in
                    HStack(spacing: 5) {
                        Circle()
                            .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                            .frame(width: 5, height: 5)

                        Text(agent.name.prefix(6).lowercased())
                            .font(.system(size: 9, weight: .semibold, design: .monospaced))
                            .foregroundStyle(agent.alive ? .white : .white.opacity(0.4))
                            .frame(width: 42, alignment: .leading)

                        // Per-agent T_day
                        if agent.T_day > 0 {
                            Text(store.formatTokens(agent.T_day))
                                .font(.system(size: 8, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.35))
                        }

                        Spacer()

                        // Office status
                        if let os = agent.office_status, os != "idle" && os != "unknown" {
                            Text(os.prefix(5).uppercased())
                                .font(.system(size: 7, weight: .bold, design: .monospaced))
                                .foregroundStyle(RheaTheme.amber.opacity(0.7))
                        }

                        // Pending messages badge
                        if agent.pendingMsgs > 0 {
                            Text("\(agent.pendingMsgs)")
                                .font(.system(size: 7, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white)
                                .padding(.horizontal, 3).padding(.vertical, 1)
                                .background(Circle().fill(RheaTheme.red))
                        }

                        // Mode chip
                        Text(agent.mode.prefix(4).uppercased())
                            .font(.system(size: 7, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.modeColor(agent.mode))

                        // Wake button for dead agents
                        if !agent.alive {
                            Button {
                                Task { _ = try? await api.wakeAgent(agent.name) }
                            } label: {
                                Image(systemName: "bolt.fill")
                                    .font(.system(size: 7))
                                    .foregroundStyle(RheaTheme.amber)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }

            Divider().opacity(0.3)

            // ── Controls ──
            HStack(spacing: 4) {
                // Wake All dead agents
                let deadAgents = store.agents.filter { !$0.alive }
                if !deadAgents.isEmpty {
                    Button {
                        Task {
                            for agent in deadAgents {
                                _ = try? await api.wakeAgent(agent.name)
                            }
                            await store.refreshCore()
                        }
                    } label: {
                        HStack(spacing: 2) {
                            Image(systemName: "bolt.fill").font(.system(size: 7))
                            Text("WAKE \(deadAgents.count)")
                                .font(.system(size: 7, weight: .bold, design: .monospaced))
                        }
                        .foregroundStyle(RheaTheme.amber)
                        .padding(.horizontal, 6).padding(.vertical, 3)
                        .background(Capsule().fill(RheaTheme.amber.opacity(0.12)))
                    }
                    .buttonStyle(.plain)
                }

                // Refresh
                Button {
                    Task { await store.refreshCore(); await fetchSessionCount() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 9))
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)

                Spacer()

                // Session count if > 0
                if sessionCount > 0 {
                    HStack(spacing: 2) {
                        Image(systemName: "terminal").font(.system(size: 7))
                        Text("\(sessionCount)")
                            .font(.system(size: 8, weight: .bold, design: .monospaced))
                    }
                    .foregroundStyle(RheaTheme.green.opacity(0.7))
                }
            }

            Divider().opacity(0.3)

            // ── Connection switcher + quit ──
            HStack(spacing: 4) {
                Button {
                    apiBaseURL = "http://localhost:8400"
                    Task { await store.refreshCore() }
                } label: {
                    Text("LOCAL")
                        .font(.system(size: 8, weight: .bold, design: .monospaced))
                        .foregroundStyle(apiBaseURL.contains("localhost") ? RheaTheme.green : .secondary)
                        .padding(.horizontal, 6).padding(.vertical, 3)
                        .background(
                            Capsule().fill(apiBaseURL.contains("localhost") ? RheaTheme.green.opacity(0.12) : .clear)
                        )
                }
                .buttonStyle(.plain)

                Button {
                    apiBaseURL = "https://rhea-tribunal.fly.dev"
                    Task { await store.refreshCore() }
                } label: {
                    Text("CLOUD")
                        .font(.system(size: 8, weight: .bold, design: .monospaced))
                        .foregroundStyle(apiBaseURL.contains("fly.dev") ? RheaTheme.accent : .secondary)
                        .padding(.horizontal, 6).padding(.vertical, 3)
                        .background(
                            Capsule().fill(apiBaseURL.contains("fly.dev") ? RheaTheme.accent.opacity(0.12) : .clear)
                        )
                }
                .buttonStyle(.plain)

                Spacer()

                Button { NSApp.terminate(nil) } label: {
                    Text("QUIT")
                        .font(.system(size: 8, weight: .bold, design: .monospaced))
                        .foregroundStyle(RheaTheme.red.opacity(0.6))
                }
                .buttonStyle(.plain)
            }
        }
        .padding(10)
        .frame(width: 260)
        .task {
            store.startPolling()
            await fetchSessionCount()
        }
    }

    // ── Helpers ──

    private func metricCell(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 1) {
            Text(value)
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            Text(label)
                .font(.system(size: 6, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    private func profileColor(_ p: String) -> Color {
        switch p {
        case "safe_cheap": return RheaTheme.green
        case "balanced": return RheaTheme.amber
        case "deep": return .purple
        default: return .secondary
        }
    }

    private func fetchSessionCount() async {
        sessionCount = ((try? await api.supervisorSessions()) ?? []).filter { $0.isAlive }.count
    }
}
