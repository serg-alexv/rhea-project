import SwiftUI

public struct MenuBarView: View {
    @StateObject private var store = RheaStore.shared

    public init() {}

    public var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header
            HStack {
                Circle()
                    .fill(store.connectionAlive ? RheaTheme.green : RheaTheme.red)
                    .frame(width: 8, height: 8)
                Text(store.connectionAlive ? "ONLINE" : "OFFLINE")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
                Spacer()
                Text(Date(), style: .time)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            Divider()

            // Agent summary
            ForEach(store.agents) { agent in
                HStack(spacing: 6) {
                    Circle()
                        .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                        .frame(width: 6, height: 6)
                    Text(agent.name.lowercased())
                        .font(.system(size: 11, weight: .medium, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.8))
                    Spacer()
                    Text(agent.mode)
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(RheaTheme.modeColor(agent.mode))
                }
            }

            Divider()

            // Metrics
            HStack {
                Text("T: \(store.formatTokens(store.totalTokens))")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)
                Spacer()
                Text("$\(String(format: "%.2f", store.totalCost))")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(RheaTheme.amber)
            }

            Divider()

            Button("Quit Rhea") {
                NSApplication.shared.terminate(nil)
            }
            .font(.system(size: 11))
        }
        .padding(12)
        .frame(width: 220)
    }
}
