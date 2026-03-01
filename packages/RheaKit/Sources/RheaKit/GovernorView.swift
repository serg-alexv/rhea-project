import SwiftUI
import Charts
import Pow

// MARK: - Token Burn Data Point
public struct BurnPoint: Identifiable {
    public let id = UUID()
    public let ts: Date
    public let tokens: Int

    public init(ts: Date, tokens: Int) {
        self.ts = ts
        self.tokens = tokens
    }
}

public struct GovernorView: View {
    @State private var agents: [AgentDTO] = []
    @State private var loading = true
    @State private var refreshCount = 0
    @State private var burnHistory: [BurnPoint] = []
    @State private var pollTimer: Timer? = nil
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    private let maxBurnPoints = 60 // 5 minutes at 5s intervals

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                if loading && agents.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity, minHeight: 300)
                } else if agents.isEmpty {
                    ContentUnavailableView("No Data", systemImage: "gauge.with.dots.needle.0percent",
                                           description: Text("Governor API not reachable"))
                } else {
                    LazyVStack(spacing: 14) {
                        // Token burn chart
                        tokenBurnChart

                        // Summary header
                        summaryHeader

                        ForEach(agents) { agent in
                            AgentCard(status: agent)
                                .transition(.movingParts.pop(.white))
                        }
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 20)
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("Governor")
            #if os(iOS)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .refreshable { await fetch() }
            .task {
                await fetch()
                startPolling()
            }
            .onDisappear { stopPolling() }
        }
    }

    // MARK: - Token Burn Chart
    var tokenBurnChart: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("TOKEN BURN (5 min)")
                .font(.system(.caption2, design: .monospaced, weight: .bold))
                .foregroundStyle(RheaTheme.accent.opacity(0.7))

            if burnHistory.count >= 2 {
                Chart(burnHistory) { point in
                    LineMark(
                        x: .value("Time", point.ts),
                        y: .value("Tokens", point.tokens)
                    )
                    .foregroundStyle(RheaTheme.accent)
                    .interpolationMethod(.catmullRom)

                    AreaMark(
                        x: .value("Time", point.ts),
                        y: .value("Tokens", point.tokens)
                    )
                    .foregroundStyle(
                        LinearGradient(
                            colors: [RheaTheme.accent.opacity(0.3), RheaTheme.accent.opacity(0.0)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .interpolationMethod(.catmullRom)
                }
                .chartXAxis {
                    AxisMarks(values: .automatic(desiredCount: 3)) { _ in
                        AxisGridLine().foregroundStyle(.white.opacity(0.05))
                        AxisValueLabel().foregroundStyle(.secondary)
                    }
                }
                .chartYAxis {
                    AxisMarks(position: .leading, values: .automatic(desiredCount: 3)) { _ in
                        AxisGridLine().foregroundStyle(.white.opacity(0.05))
                        AxisValueLabel().foregroundStyle(.secondary)
                    }
                }
                .chartYScale(domain: .automatic(includesZero: false))
                .frame(height: 80)
            } else {
                HStack {
                    Spacer()
                    Text("Collecting data...")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
                .frame(height: 80)
            }
        }
        .glassCard()
    }

    private func startPolling() {
        pollTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
            Task { await fetch() }
        }
    }

    private func stopPolling() {
        pollTimer?.invalidate()
        pollTimer = nil
    }

    var summaryHeader: some View {
        let totalTokens = agents.reduce(0) { $0 + $1.T_day }
        let totalCost = agents.reduce(0.0) { $0 + $1.dollar_day }
        let stableCount = agents.filter { $0.mode == "normal" && !$0.isHardFail }.count
        let onTrackCount = agents.filter { $0.floor_gap <= 0 }.count

        return VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 12) {
                MetricPill(label: "Agents", value: "\(agents.count)", color: RheaTheme.accent)
                MetricPill(label: "Stable", value: "\(stableCount)/\(agents.count)",
                           color: stableCount == agents.count ? RheaTheme.green : RheaTheme.amber)
                MetricPill(label: "Tokens", value: formatTokens(totalTokens), color: .white)
                MetricPill(label: "Cost", value: "$\(String(format: "%.2f", totalCost))", color: RheaTheme.amber)
            }

            Text("On track: \(onTrackCount)/\(agents.count) (floor trajectory)")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .glassCard()
    }

    struct GovernorUnifiedResponse: Codable {
        let _ts: String
        let agents: [String: AgentDTO]
    }

    func fetch() async {
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBaseURL)/agents/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let resp = try JSONDecoder().decode(GovernorUnifiedResponse.self, from: data)
            let sorted = resp.agents.values.sorted { $0.agent < $1.agent }
            withAnimation(.spring(duration: 0.4)) {
                agents = sorted
                refreshCount += 1
            }
            // Append to burn history for the chart
            let totalTokens = sorted.reduce(0) { $0 + $1.T_day }
            let point = BurnPoint(ts: Date(), tokens: totalTokens)
            withAnimation(.easeInOut(duration: 0.3)) {
                burnHistory.append(point)
                if burnHistory.count > maxBurnPoints {
                    burnHistory.removeFirst(burnHistory.count - maxBurnPoints)
                }
            }
        } catch {
            agents = []
        }
    }

    func formatTokens(_ n: Int) -> String {
        if n >= 1_000_000 { return "\(n / 1_000_000)M" }
        if n >= 1_000 { return "\(n / 1_000)K" }
        return "\(n)"
    }
}

// MARK: - MetricPill
public struct MetricPill: View {
    public let label: String
    public let value: String
    public let color: Color

    public init(label: String, value: String, color: Color) {
        self.label = label
        self.value = value
        self.color = color
    }

    public var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(.title3, design: .rounded, weight: .bold))
                .foregroundStyle(color)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - AgentCard
public struct AgentCard: View {
    public let status: AgentDTO
    @State private var appeared = false
    @State private var actionInProgress: String? = nil
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    public init(status: AgentDTO) {
        self.status = status
    }

    /// Fraction of budget used: prefers (cap - remaining)/cap, falls back to dollar_day/cap
    public var budgetRemainingFraction: Double {
        guard let cap = status.budget_cap, cap > 0 else { return 0 }
        if let remaining = status.budget_remaining {
            return min(max((cap - remaining) / cap, 0), 1.0)
        }
        return min(status.dollar_day / cap, 1.0)
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header row: name + mode badge
            HStack {
                HStack(spacing: 8) {
                    Circle()
                        .fill(RheaTheme.paceColor(status.pace))
                        .frame(width: 10, height: 10)
                        .changeEffect(.pulse(shape: Circle(), count: 2), value: status.pace, isEnabled: status.pace == "red")

                    Text(status.agent.uppercased())
                        .font(.system(.headline, design: .monospaced, weight: .bold))
                        .foregroundStyle(.white)
                }

                Spacer()

                Text(status.mode.uppercased())
                    .font(.system(.caption2, design: .rounded, weight: .semibold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(
                        Capsule().fill(RheaTheme.modeColor(status.mode).opacity(0.25))
                    )
                    .foregroundStyle(RheaTheme.modeColor(status.mode))
                    .changeEffect(.shake(rate: .fast), value: status.mode, isEnabled: status.isHardFail)
            }

            // Budget gauge — shows budget_remaining/budget_cap when available, falls back to dollar_day/budget_cap
            if let cap = status.budget_cap, cap > 0 {
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Budget")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Spacer()
                        if let remaining = status.budget_remaining {
                            Text("$\(String(format: "%.2f", remaining)) left of $\(String(format: "%.0f", cap))")
                                .font(.system(.caption, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.7))
                        } else {
                            Text("$\(String(format: "%.2f", status.dollar_day)) / $\(String(format: "%.0f", cap))")
                                .font(.system(.caption, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.7))
                        }
                    }

                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 4)
                                .fill(.white.opacity(0.08))
                            RoundedRectangle(cornerRadius: 4)
                                .fill(budgetRemainingFraction < 0.6 ? RheaTheme.green :
                                      budgetRemainingFraction < 0.85 ? RheaTheme.amber :
                                      RheaTheme.red)
                                .frame(width: geo.size.width * budgetRemainingFraction)
                                .animation(.spring(duration: 0.6), value: budgetRemainingFraction)
                        }
                    }
                    .frame(height: 6)
                }
            }

            if status.billing_mode == "subscription" {
                Text("subscription mode")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            // Office status enrichment
            if let officeStatus = status.office_status {
                HStack(spacing: 8) {
                    Text(officeStatus)
                        .font(.system(.caption2, design: .monospaced, weight: .semibold))
                        .foregroundStyle(status.alive ? RheaTheme.green : RheaTheme.red)
                    if let pending = status.pending_msgs, pending > 0 {
                        Text("\(pending) pending")
                            .font(.system(.caption2, design: .monospaced))
                            .foregroundStyle(RheaTheme.amber)
                    }
                    if let open = status.tasks_open, open > 0 {
                        Text("\(open) tasks")
                            .font(.system(.caption2, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }
                }
            }

            // Stats row
            HStack(spacing: 16) {
                StatChip(icon: "number", text: formatTokens(status.T_day))
                StatChip(icon: "clock", text: "h\(status.hour ?? 0)")
                if let forecast = status.forecast, !forecast.isEmpty {
                    StatChip(icon: "chart.line.uptrend.xyaxis", text: forecast, color: RheaTheme.accent)
                }
                if status.floor_gap > 0 {
                    StatChip(icon: "arrow.down.to.line", text: "gap:\(status.floor_gap)", color: RheaTheme.amber)
                }
                Spacer()
            }

            // Floor trajectory row
            HStack(spacing: 8) {
                if let floorExp = status.floor_expected {
                    Text("floor: \(formatTokens(floorExp))")
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundStyle(.secondary)
                    if status.floor_gap > 0 {
                        Text("gap: \(status.floor_gap)")
                            .font(.system(.caption2, design: .monospaced))
                            .foregroundStyle(RheaTheme.amber)
                    }
                }
                if let rail = status.upper_rail_enabled, rail {
                    Text("RAIL")
                        .font(.system(.caption2, design: .monospaced, weight: .bold))
                        .foregroundStyle(RheaTheme.red.opacity(0.8))
                }
                Spacer()
                Text(status.floor_gap > 0 ? "behind floor" : "on track")
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundStyle(status.floor_gap > 0 ? RheaTheme.amber : RheaTheme.green)
            }

            // Action buttons
            HStack(spacing: 10) {
                AgentActionButton(label: "Wake", icon: "bolt.fill", color: RheaTheme.amber, isLoading: actionInProgress == "wake") {
                    await performAction("wake")
                }
                AgentActionButton(label: "Ping", icon: "antenna.radiowaves.left.and.right", color: RheaTheme.accent, isLoading: actionInProgress == "ping") {
                    await performAction("ping")
                }
                AgentActionButton(
                    label: status.mode == "paused" ? "Resume" : "Pause",
                    icon: status.mode == "paused" ? "play.fill" : "pause.fill",
                    color: status.mode == "paused" ? RheaTheme.green : .secondary,
                    isLoading: actionInProgress == "pause"
                ) {
                    await performAction("pause")
                }
                Spacer()
            }
        }
        .glassCard()
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 20)
        .onAppear {
            withAnimation(.spring(duration: 0.5, bounce: 0.3)) {
                appeared = true
            }
        }
    }

    func performAction(_ action: String) async {
        actionInProgress = action
        defer { actionInProgress = nil }
        let endpoint: String
        var body: [String: Any]? = nil
        switch action {
        case "wake":
            endpoint = "agents/wake/\(status.agent)"
        case "pause":
            endpoint = "governor/\(status.agent)"
            let newMode = status.mode == "paused" ? "normal" : "paused"
            body = ["mode": newMode]
        default:
            endpoint = "feed/push"
            body = ["sender": "human", "text": "PING \(status.agent)", "type": "radio"]
        }
        guard let url = URL(string: "\(apiBaseURL)/\(endpoint)") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        if let body = body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                #if os(iOS)
                UINotificationFeedbackGenerator().notificationOccurred(.success)
                #endif
            }
        } catch {}
    }

    func formatTokens(_ n: Int) -> String {
        if n >= 1_000_000 { return "\(n / 1_000_000)M" }
        if n >= 1_000 { return "\(n / 1_000)K" }
        return "\(n)"
    }
}

// MARK: - AgentActionButton
public struct AgentActionButton: View {
    public let label: String
    public let icon: String
    public let color: Color
    public let isLoading: Bool
    public let action: () async -> Void

    public init(label: String, icon: String, color: Color, isLoading: Bool, action: @escaping () async -> Void) {
        self.label = label
        self.icon = icon
        self.color = color
        self.isLoading = isLoading
        self.action = action
    }

    public var body: some View {
        Button {
            Task { await action() }
        } label: {
            HStack(spacing: 4) {
                if isLoading {
                    ProgressView()
                        .tint(color)
                        .controlSize(.mini)
                } else {
                    Image(systemName: icon)
                        .font(.system(size: 10, weight: .bold))
                }
                Text(label)
                    .font(.system(.caption2, design: .monospaced, weight: .bold))
            }
            .foregroundStyle(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(
                Capsule().strokeBorder(color.opacity(0.4), lineWidth: 1)
                    .background(Capsule().fill(color.opacity(0.1)))
            )
        }
        .buttonStyle(.plain)
        .disabled(isLoading)
    }
}

// MARK: - StatChip
public struct StatChip: View {
    public let icon: String
    public let text: String
    public var color: Color = .secondary

    public init(icon: String, text: String, color: Color = .secondary) {
        self.icon = icon
        self.text = text
        self.color = color
    }

    public var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 10))
            Text(text)
                .font(.system(.caption2, design: .monospaced))
        }
        .foregroundStyle(color)
    }
}
