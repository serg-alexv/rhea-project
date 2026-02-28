import SwiftUI

// MARK: - Models

struct FeedItem: Codable, Identifiable {
    let id: String
    let type: String
    let sender: String
    let receiver: String
    let text: String
    let ts: String
}

struct FeedResponse: Codable {
    let items: [FeedItem]
    let total: Int
}

// MARK: - Live Radio View

struct TeamChatView: View {
    @State private var items: [FeedItem] = []
    @State private var activeSenders: Set<String> = []
    @State private var latestItem: FeedItem? = nil
    @State private var pulse = false
    @State private var pollTimer: Timer? = nil
    @State private var lastTS: String = ""
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // ON AIR — who's active NOW
                onAirBanner

                // Live stream console
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 2) {
                        ForEach(items) { item in
                            ConsoleLine(item: item)
                        }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                }
                .background(Color.black)
            }
            .background(Color.black)
            .navigationTitle("Radio")
            #if os(iOS)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .task {
                await fetchFull()
                startPolling()
            }
            .onDisappear { pollTimer?.invalidate() }
        }
    }

    // MARK: - ON AIR banner

    var onAirBanner: some View {
        HStack(spacing: 12) {
            // Pulsing red dot
            Circle()
                .fill(Color.red)
                .frame(width: 12, height: 12)
                .scaleEffect(pulse ? 1.3 : 0.8)
                .opacity(pulse ? 1.0 : 0.5)
                .animation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true), value: pulse)
                .onAppear { pulse = true }

            Text("ON AIR")
                .font(.system(.caption, design: .monospaced, weight: .black))
                .foregroundStyle(.red)

            // Active agents as bright pills
            ForEach(Array(activeSenders).sorted(), id: \.self) { agent in
                Text(agent.uppercased())
                    .font(.system(.caption2, design: .monospaced, weight: .bold))
                    .foregroundStyle(.black)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(
                        Capsule().fill(agentColor(agent))
                    )
            }

            Spacer()

            Text("\(items.count)")
                .font(.system(.caption2, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(Color.black)
        .overlay(
            Rectangle()
                .fill(latestItem != nil ? agentColor(latestItem?.sender ?? "").opacity(0.15) : .clear)
                .animation(.easeOut(duration: 1.5), value: latestItem?.id)
        )
    }

    // MARK: - Networking

    func fetchFull() async {
        guard let url = URL(string: "\(apiBaseURL)/feed?limit=100") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(FeedResponse.self, from: data)
            items = response.items
            updateActiveSenders()
            if let first = items.first {
                lastTS = first.ts
            }
        } catch {}
    }

    func pollDelta() async {
        let encoded = lastTS.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        guard let url = URL(string: "\(apiBaseURL)/feed?limit=20&since=\(encoded)") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(FeedResponse.self, from: data)
            if !response.items.isEmpty {
                withAnimation(.spring(duration: 0.2)) {
                    items.insert(contentsOf: response.items, at: 0)
                    latestItem = response.items.first
                }
                updateActiveSenders()
                if let first = response.items.first {
                    lastTS = first.ts
                }
            }
        } catch {}
    }

    func startPolling() {
        pollTimer = Timer.scheduledTimer(withTimeInterval: 3.0, repeats: true) { _ in
            Task { await pollDelta() }
        }
    }

    func updateActiveSenders() {
        // "Active" = sent something in the last 5 minutes
        let cutoff = ISO8601DateFormatter().string(from: Date().addingTimeInterval(-300))
        let recent = items.filter { $0.ts > cutoff }
        activeSenders = Set(recent.map { $0.sender.lowercased() })
    }

    func agentColor(_ agent: String) -> Color {
        switch agent.lowercased() {
        case "rex": return RheaTheme.accent
        case "orion": return .purple
        case "gemini": return RheaTheme.amber
        case "human": return RheaTheme.green
        case "relay": return .orange
        default: return .gray
        }
    }
}

// MARK: - Console Line (terminal-style)

struct ConsoleLine: View {
    let item: FeedItem
    @State private var appeared = false

    var senderColor: Color {
        switch item.sender.lowercased() {
        case "rex": return RheaTheme.accent
        case "orion": return .purple
        case "gemini": return RheaTheme.amber
        case "human": return RheaTheme.green
        case "relay": return .orange
        default: return .gray
        }
    }

    var typeGlyph: String {
        switch item.type {
        case "office": return ">"
        case "outbox": return ">>"
        case "relay": return "~>"
        default: return "|"
        }
    }

    var body: some View {
        HStack(alignment: .top, spacing: 0) {
            // Timestamp
            Text(formatTime(item.ts))
                .foregroundStyle(.green.opacity(0.5))

            Text(" ")

            // Sender
            Text(item.sender.prefix(6).uppercased().padding(toLength: 6, withPad: " ", startingAt: 0))
                .foregroundStyle(senderColor)

            Text(typeGlyph)
                .foregroundStyle(.secondary)

            Text(" ")

            // Message (first line, truncated)
            Text(firstLine(item.text))
                .foregroundStyle(.white.opacity(0.8))
                .lineLimit(2)
        }
        .font(.system(size: 11, weight: .regular, design: .monospaced))
        .padding(.vertical, 1)
        .opacity(appeared ? 1 : 0)
        .onAppear {
            withAnimation(.easeIn(duration: 0.15)) {
                appeared = true
            }
        }
    }

    func formatTime(_ iso: String) -> String {
        if let tIdx = iso.firstIndex(of: "T") {
            let time = iso[iso.index(after: tIdx)...]
            if time.count >= 5 { return String(time.prefix(5)) }
        }
        return "     "
    }

    func firstLine(_ text: String) -> String {
        let stripped = text.replacingOccurrences(of: "\n", with: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if stripped.count > 120 {
            return String(stripped.prefix(120)) + "…"
        }
        return stripped
    }
}
