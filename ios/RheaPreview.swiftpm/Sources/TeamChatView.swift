import SwiftUI

struct FeedItem: Codable, Identifiable {
    let id: String
    let type: String      // "office", "outbox", "relay"
    let sender: String
    let receiver: String
    let text: String
    let ts: String
}

struct FeedResponse: Codable {
    let items: [FeedItem]
    let total: Int
}

struct TeamChatView: View {
    @State private var items: [FeedItem] = []
    @State private var loading = true
    @State private var filter: String = "all"
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var filteredItems: [FeedItem] {
        guard filter != "all" else { return items }
        return items.filter { $0.sender.lowercased() == filter || $0.receiver.lowercased() == filter }
    }

    var agents: [String] {
        let all = Set(items.map { $0.sender.lowercased() })
        return Array(all).sorted()
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Agent filter bar
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        FilterChip(label: "All", count: items.count,
                                   isActive: filter == "all") { filter = "all" }
                        ForEach(agents, id: \.self) { agent in
                            FilterChip(
                                label: agent.uppercased(),
                                count: items.filter { $0.sender.lowercased() == agent }.count,
                                isActive: filter == agent,
                                color: agentColor(agent)
                            ) { filter = agent }
                        }
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 10)
                }
                .background(RheaTheme.bg)

                if loading {
                    Spacer()
                    ProgressView()
                    Spacer()
                } else if filteredItems.isEmpty {
                    Spacer()
                    ContentUnavailableView("No Messages", systemImage: "bubble.left.and.bubble.right",
                                           description: Text("Feed empty or API offline"))
                    Spacer()
                } else {
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            ForEach(filteredItems) { item in
                                ChatBubble(item: item)
                            }
                        }
                        .padding(.horizontal)
                        .padding(.top, 8)
                        .padding(.bottom, 20)
                    }
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("Team")
            #if os(iOS)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .refreshable { await fetch() }
            .task { await fetch() }
        }
    }

    func fetch() async {
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBaseURL)/feed?limit=80") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(FeedResponse.self, from: data)
            withAnimation(.spring(duration: 0.3)) {
                items = response.items
            }
        } catch {
            items = []
        }
    }

    func agentColor(_ agent: String) -> Color {
        switch agent {
        case "rex": return RheaTheme.accent
        case "orion": return .purple
        case "gemini": return RheaTheme.amber
        case "human": return RheaTheme.green
        default: return .secondary
        }
    }
}

// MARK: - ChatBubble
struct ChatBubble: View {
    let item: FeedItem
    @State private var appeared = false

    var typeIcon: String {
        switch item.type {
        case "office": return "bubble.left.fill"
        case "outbox": return "paperplane.fill"
        case "relay": return "arrow.triangle.swap"
        default: return "ellipsis.bubble"
        }
    }

    var senderColor: Color {
        switch item.sender.lowercased() {
        case "rex": return RheaTheme.accent
        case "orion": return .purple
        case "gemini": return RheaTheme.amber
        case "human", "to": return RheaTheme.green
        default: return .secondary
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header: sender → receiver + type icon
            HStack(spacing: 6) {
                Circle()
                    .fill(senderColor)
                    .frame(width: 8, height: 8)

                Text(item.sender.uppercased())
                    .font(.system(.caption, design: .monospaced, weight: .bold))
                    .foregroundStyle(senderColor)

                Image(systemName: "arrow.right")
                    .font(.system(size: 8))
                    .foregroundStyle(.secondary)

                Text(item.receiver.uppercased())
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundStyle(.secondary)

                Spacer()

                Image(systemName: typeIcon)
                    .font(.system(size: 10))
                    .foregroundStyle(.secondary)

                if !item.ts.isEmpty {
                    Text(formatTime(item.ts))
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundStyle(.secondary.opacity(0.7))
                }
            }

            // Message text
            Text(item.text.trimmingCharacters(in: .whitespacesAndNewlines))
                .font(.system(.caption, design: .default))
                .foregroundStyle(.white.opacity(0.85))
                .lineLimit(6)
        }
        .glassCard()
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 10)
        .onAppear {
            withAnimation(.spring(duration: 0.3, bounce: 0.2).delay(Double.random(in: 0...0.1))) {
                appeared = true
            }
        }
    }

    func formatTime(_ iso: String) -> String {
        // Extract HH:MM from ISO timestamp
        if let tIdx = iso.firstIndex(of: "T") {
            let time = iso[iso.index(after: tIdx)...]
            if time.count >= 5 {
                return String(time.prefix(5))
            }
        }
        return ""
    }
}
