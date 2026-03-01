#if os(macOS)
import SwiftUI
import RheaKit

/// Menu bar status widget — compact agent health at a glance.
struct MenuBarView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var agents: [(name: String, alive: Bool, tokens: Int)] = []
    @State private var lastCheck: Date?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("RHEA AGENTS")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)

            if agents.isEmpty {
                Text("Checking...")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            } else {
                ForEach(agents, id: \.name) { agent in
                    HStack(spacing: 6) {
                        Circle()
                            .fill(agent.alive ? Color.green : Color.red)
                            .frame(width: 6, height: 6)
                        Text(agent.name)
                            .font(.system(size: 11, weight: .semibold, design: .monospaced))
                        Spacer()
                        if agent.tokens > 0 {
                            Text("\(agent.tokens > 1000 ? "\(agent.tokens / 1000)K" : "\(agent.tokens)")")
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }

            Divider()

            if let check = lastCheck {
                Text("Updated \(check, style: .relative) ago")
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            Button("Refresh") { poll() }
                .keyboardShortcut("r", modifiers: .command)

            Divider()

            Button("Quit Rhea") { NSApplication.shared.terminate(nil) }
                .keyboardShortcut("q", modifiers: .command)
        }
        .padding(8)
        .frame(width: 200)
        .task { poll() }
    }

    private func poll() {
        guard let url = URL(string: "\(apiBaseURL)/agents/status") else { return }
        var req = URLRequest(url: url)
        req.timeoutInterval = 5
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        URLSession.shared.dataTask(with: req) { data, _, _ in
            guard let data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let list = json["agents"] as? [[String: Any]] else { return }
            DispatchQueue.main.async {
                agents = list.map { a in
                    (
                        name: a["name"] as? String ?? a["agent"] as? String ?? "?",
                        alive: a["alive"] as? Bool ?? false,
                        tokens: a["T_day"] as? Int ?? 0
                    )
                }
                lastCheck = Date()
            }
        }.resume()
    }
}
#endif
