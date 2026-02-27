import SwiftUI
import Charts
import Pow

struct AgentStatus: Codable, Identifiable {
    var id: String { agent }
    let agent: String
    let pace: String
    let forecast: String
    let mode: String
    let T_day: Int
    let dollar_day: Double
    let budget_cap: Double
    let budget_remaining: Double
    let floor_expected: Int
    let floor_gap: Int
    let hour: Int
    let hard_fail: Bool
}

struct GovernorView: View {
    @State private var agents: [AgentStatus] = []
    @State private var loading = true
    @State private var refreshCount = 0
    private let apiBase = "http://localhost:8400"

    var body: some View {
        NavigationStack {
            ScrollView {
                if loading {
                    ProgressView()
                        .frame(maxWidth: .infinity, minHeight: 300)
                } else if agents.isEmpty {
                    ContentUnavailableView("No Data", systemImage: "gauge.with.dots.needle.0percent",
                                           description: Text("Governor API not reachable"))
                } else {
                    LazyVStack(spacing: 14) {
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
            .task { await fetch() }
        }
    }

    var summaryHeader: some View {
        let totalTokens = agents.reduce(0) { $0 + $1.T_day }
        let totalCost = agents.reduce(0.0) { $0 + $1.dollar_day }
        let healthyCount = agents.filter { $0.mode == "normal" }.count

        return HStack(spacing: 12) {
            MetricPill(label: "Agents", value: "\(agents.count)", color: RheaTheme.accent)
            MetricPill(label: "Healthy", value: "\(healthyCount)/\(agents.count)",
                       color: healthyCount == agents.count ? RheaTheme.green : RheaTheme.amber)
            MetricPill(label: "Tokens", value: formatTokens(totalTokens), color: .white)
            MetricPill(label: "Cost", value: "$\(String(format: "%.2f", totalCost))", color: RheaTheme.amber)
        }
        .glassCard()
    }

    func fetch() async {
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBase)/governor") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let raw = try JSONDecoder().decode([String: AgentStatus].self, from: data)
            withAnimation(.spring(duration: 0.4)) {
                agents = raw.values.sorted { $0.agent < $1.agent }
                refreshCount += 1
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
struct MetricPill: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
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
struct AgentCard: View {
    let status: AgentStatus
    @State private var appeared = false

    var budgetFraction: Double {
        guard status.budget_cap > 0 else { return 0 }
        return min(status.dollar_day / status.budget_cap, 1.0)
    }

    var body: some View {
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
                    .changeEffect(.shake(rate: .fast), value: status.mode, isEnabled: status.mode == "hard_fail")
            }

            // Budget gauge (only for API-billed agents with budget_cap > 0)
            if status.budget_cap > 0 {
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Budget")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text("$\(String(format: "%.2f", status.dollar_day)) / $\(String(format: "%.0f", status.budget_cap))")
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.7))
                    }

                    // TODO(human): Implement the budget gauge visualization
                    // This gauge should show budget usage as a visual bar/ring.
                    // Available: budgetFraction (0.0–1.0), RheaTheme colors.
                    // Consider: ProgressView, Gauge, or custom Shape.
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 4)
                                .fill(.white.opacity(0.08))
                            RoundedRectangle(cornerRadius: 4)
                                .fill(budgetFraction < 0.6 ? RheaTheme.green :
                                      budgetFraction < 0.85 ? RheaTheme.amber :
                                      RheaTheme.red)
                                .frame(width: geo.size.width * budgetFraction)
                                .animation(.spring(duration: 0.6), value: budgetFraction)
                        }
                    }
                    .frame(height: 6)
                }
            }

            // Stats row
            HStack(spacing: 16) {
                StatChip(icon: "number", text: formatTokens(status.T_day))
                StatChip(icon: "clock", text: "h\(status.hour)")
                if status.floor_gap > 0 {
                    StatChip(icon: "arrow.down.to.line", text: "gap:\(status.floor_gap)", color: RheaTheme.amber)
                }
                Spacer()
                Text(status.forecast)
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundStyle(.secondary)
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

    func formatTokens(_ n: Int) -> String {
        if n >= 1_000_000 { return "\(n / 1_000_000)M" }
        if n >= 1_000 { return "\(n / 1_000)K" }
        return "\(n)"
    }
}

// MARK: - StatChip
struct StatChip: View {
    let icon: String
    let text: String
    var color: Color = .secondary

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 10))
            Text(text)
                .font(.system(.caption2, design: .monospaced))
        }
        .foregroundStyle(color)
    }
}
