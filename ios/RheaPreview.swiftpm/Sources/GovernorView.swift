import SwiftUI

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
    private let apiBase = "http://localhost:8400"

    var body: some View {
        NavigationStack {
            Group {
                if loading {
                    ProgressView("Loading governor...")
                } else if agents.isEmpty {
                    ContentUnavailableView("No Data", systemImage: "gauge.with.dots.needle.0percent",
                                           description: Text("Governor API not reachable"))
                } else {
                    List(agents) { agent in
                        AgentRow(status: agent)
                    }
                }
            }
            .navigationTitle("Governor")
            .refreshable { await fetch() }
            .task { await fetch() }
        }
    }

    func fetch() async {
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBase)/governor") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let raw = try JSONDecoder().decode([String: AgentStatus].self, from: data)
            agents = raw.values.sorted { $0.agent < $1.agent }
        } catch {
            agents = []
        }
    }
}

struct AgentRow: View {
    let status: AgentStatus

    var paceColor: Color {
        switch status.pace {
        case "green": return .green
        case "yellow": return .yellow
        case "red": return .red
        default: return .gray
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Circle().fill(paceColor).frame(width: 12, height: 12)
                Text(status.agent.uppercased()).font(.headline.monospaced())
                Spacer()
                Text(status.mode).font(.caption).padding(.horizontal, 8).padding(.vertical, 2)
                    .background(status.mode == "normal" ? Color.green.opacity(0.2) :
                                status.mode == "compact" ? Color.yellow.opacity(0.2) :
                                Color.red.opacity(0.2))
                    .clipShape(Capsule())
            }
            HStack(spacing: 16) {
                Label("\(status.T_day.formatted()) tok", systemImage: "number")
                    .font(.caption.monospaced())
                Label("$\(status.dollar_day, specifier: "%.2f")/\(status.budget_cap, specifier: "%.0f")",
                      systemImage: "dollarsign.circle")
                    .font(.caption.monospaced())
                if status.floor_gap > 0 {
                    Label("gap: \(status.floor_gap)", systemImage: "arrow.down.to.line")
                        .font(.caption).foregroundStyle(.orange)
                }
            }
        }
        .padding(.vertical, 4)
    }
}
