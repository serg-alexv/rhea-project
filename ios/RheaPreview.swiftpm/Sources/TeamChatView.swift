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
    @State private var expandedIDs: Set<String> = []
    @State private var filterAgent: String? = nil  // nil = show all
    @State private var composerText: String = ""
    @State private var isSending = false
    @State private var prevItemCount = 0
    @State private var showBubbles = false  // toggle: console vs bubble view
    @State private var showAgentSheet = false
    @State private var knownAgents: [RadioAgentInfo] = []
    @State private var wakingAgent: String? = nil
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    /// All known senders (for filter chips)
    var allSenders: [String] {
        Array(Set(items.map { $0.sender.lowercased() })).sorted()
    }

    /// Filtered items based on selected agent filter
    var visibleItems: [FeedItem] {
        guard let agent = filterAgent else { return items }
        return items.filter { $0.sender.lowercased() == agent }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // ON AIR — who's active NOW
                onAirBanner

                // Filter chips (scrollable, only when >1 sender)
                if allSenders.count > 1 {
                    filterBar
                }

                // Live stream — console or bubble mode
                ScrollView {
                    if showBubbles {
                        LazyVStack(spacing: 8) {
                            ForEach(visibleItems) { item in
                                BubbleLine(item: item, isExpanded: expandedIDs.contains(item.id))
                                    .contentShape(Rectangle())
                                    .onTapGesture {
                                        withAnimation(.easeInOut(duration: 0.2)) {
                                            if expandedIDs.contains(item.id) {
                                                expandedIDs.remove(item.id)
                                            } else {
                                                expandedIDs.insert(item.id)
                                            }
                                        }
                                    }
                            }
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                    } else {
                        LazyVStack(alignment: .leading, spacing: 2) {
                            ForEach(visibleItems) { item in
                                ConsoleLine(item: item, isExpanded: expandedIDs.contains(item.id))
                                    .contentShape(Rectangle())
                                    .onTapGesture {
                                        withAnimation(.easeInOut(duration: 0.2)) {
                                            if expandedIDs.contains(item.id) {
                                                expandedIDs.remove(item.id)
                                            } else {
                                                expandedIDs.insert(item.id)
                                            }
                                        }
                                    }
                            }
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                    }
                }
                .background(Color.black)

                // Composer bar
                composerBar
            }
            .background(Color.black)
            .navigationTitle("Radio")
            .toolbar {
                ToolbarItemGroup(placement: .primaryAction) {
                    // Console ↔ Bubble toggle
                    Button {
                        withAnimation(.easeInOut(duration: 0.25)) { showBubbles.toggle() }
                    } label: {
                        Image(systemName: showBubbles ? "terminal" : "bubble.left.and.bubble.right")
                            .font(.caption)
                            .foregroundStyle(.white.opacity(0.7))
                    }

                    // Agent roster sheet
                    Button {
                        Task { await fetchAgents() }
                        showAgentSheet = true
                    } label: {
                        Image(systemName: "person.3")
                            .font(.caption)
                            .foregroundStyle(.white.opacity(0.7))
                    }
                }
            }
            #if os(iOS)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .sheet(isPresented: $showAgentSheet) {
                agentSheet
            }
            .task {
                await fetchFull()
                startPolling()
            }
            .onDisappear { pollTimer?.invalidate() }
        }
    }

    // MARK: - Composer bar

    var composerBar: some View {
        HStack(spacing: 8) {
            TextField("broadcast...", text: $composerText)
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.white)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color.white.opacity(0.08))
                )
                .submitLabel(.send)
                .onSubmit { Task { await sendMessage() } }

            Button {
                Task { await sendMessage() }
            } label: {
                Image(systemName: isSending ? "arrow.up.circle.fill" : "arrow.up.circle")
                    .font(.title3)
                    .foregroundStyle(composerText.isEmpty ? .secondary : RheaTheme.green)
            }
            .disabled(composerText.isEmpty || isSending)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.black.opacity(0.95))
    }

    func sendMessage() async {
        let text = composerText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        isSending = true
        defer { isSending = false }

        guard let url = URL(string: "\(apiBaseURL)/feed/push") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "sender": "human",
            "text": text,
            "type": "radio"
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                withAnimation { composerText = "" }
                // Immediately poll for the new message
                await pollDelta()
            }
        } catch {}
    }

    // MARK: - Filter bar

    var filterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                // "All" chip
                RadioFilterChip(label: "ALL", isActive: filterAgent == nil, color: .white) {
                    withAnimation { filterAgent = nil }
                }

                ForEach(allSenders, id: \.self) { agent in
                    RadioFilterChip(label: agent.uppercased(), isActive: filterAgent == agent, color: agentColor(agent)) {
                        withAnimation { filterAgent = (filterAgent == agent) ? nil : agent }
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
        }
        .background(Color.black.opacity(0.95))
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

    // MARK: - Agent Sheet

    var agentSheet: some View {
        NavigationStack {
            List {
                if knownAgents.isEmpty {
                    HStack {
                        ProgressView()
                            .tint(.white)
                        Text("Loading agents…")
                            .foregroundStyle(.secondary)
                    }
                    .listRowBackground(Color.black.opacity(0.8))
                } else {
                    ForEach(knownAgents) { agent in
                        HStack(spacing: 12) {
                            // Color dot
                            Circle()
                                .fill(agentColor(agent.name))
                                .frame(width: 10, height: 10)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(agent.name.uppercased())
                                    .font(.system(.body, design: .monospaced, weight: .bold))
                                    .foregroundStyle(agentColor(agent.name))
                                Text(agent.expired ? "offline" : "lease #\(agent.leaseToken)")
                                    .font(.system(.caption2, design: .monospaced))
                                    .foregroundStyle(agent.expired ? .red.opacity(0.7) : .green.opacity(0.7))
                            }

                            Spacer()

                            // Wake button
                            Button {
                                Task { await wakeAgent(agent.name) }
                            } label: {
                                if wakingAgent == agent.name.uppercased() {
                                    ProgressView()
                                        .tint(agentColor(agent.name))
                                } else {
                                    Text("WAKE")
                                        .font(.system(.caption, design: .monospaced, weight: .bold))
                                        .foregroundStyle(.black)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 5)
                                        .background(Capsule().fill(agentColor(agent.name)))
                                }
                            }
                            .buttonStyle(.plain)
                        }
                        .padding(.vertical, 4)
                        .listRowBackground(Color.black.opacity(0.8))
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.black)
            .navigationTitle("Agents")
            .navigationBarTitleDisplayMode(.inline)
            #if os(iOS)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { showAgentSheet = false }
                        .foregroundStyle(RheaTheme.green)
                }
            }
        }
        .presentationDetents([.medium])
        .presentationDragIndicator(.visible)
    }

    // MARK: - Agent Networking

    func fetchAgents() async {
        guard let url = URL(string: "\(apiBaseURL)/agents") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let dict = try JSONSerialization.jsonObject(with: data) as? [String: [String: Any]] {
                knownAgents = dict.map { (key, val) in
                    RadioAgentInfo(
                        name: key,
                        leaseToken: val["lease_token"] as? Int ?? 0,
                        expired: val["expired"] as? Bool ?? true,
                        lastActive: val["last_active"] as? String ?? ""
                    )
                }.sorted { $0.name < $1.name }
            }
        } catch {}
    }

    func wakeAgent(_ name: String) async {
        let upper = name.uppercased()
        wakingAgent = upper
        defer { wakingAgent = nil }
        guard let url = URL(string: "\(apiBaseURL)/agents/wake/\(upper)") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                #if os(iOS)
                let generator = UINotificationFeedbackGenerator()
                generator.notificationOccurred(.success)
                #endif
                // Refresh agent list
                await fetchAgents()
                // Poll for the wake broadcast
                await pollDelta()
            }
        } catch {}
    }

    // MARK: - Feed Networking

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
            // Deduplicate: only insert items we don't already have
            let existingIDs = Set(items.map(\.id))
            let newItems = response.items.filter { !existingIDs.contains($0.id) }
            if !newItems.isEmpty {
                withAnimation(.spring(duration: 0.2)) {
                    items.insert(contentsOf: newItems, at: 0)
                    latestItem = newItems.first
                }
                updateActiveSenders()
                if let first = newItems.first {
                    lastTS = first.ts
                }
                // Haptic kick — new activity on the radio
                #if os(iOS)
                let generator = UIImpactFeedbackGenerator(style: .medium)
                generator.impactOccurred()
                #endif
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
    var isExpanded: Bool = false
    @State private var appeared = false

    var senderColor: Color {
        switch item.sender.lowercased() {
        case "rex": return RheaTheme.accent
        case "orion": return .purple
        case "gemini": return RheaTheme.amber
        case "human": return RheaTheme.green
        case "relay": return .orange
        case "tribunal": return .cyan
        default: return .gray
        }
    }

    var typeGlyph: String {
        switch item.type {
        case "office": return ">"
        case "outbox": return ">>"
        case "relay": return "~>"
        case "tribunal": return "⚖"
        case "broadcast": return "⦿"
        default: return "|"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Compact line (always visible)
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
                    .lineLimit(isExpanded ? nil : 2)
            }

            // Expanded detail (tap to reveal)
            if isExpanded {
                VStack(alignment: .leading, spacing: 4) {
                    if !item.receiver.isEmpty && item.receiver != "all" {
                        Text("→ \(item.receiver.uppercased())")
                            .foregroundStyle(senderColor.opacity(0.6))
                    }
                    Text(item.text)
                        .foregroundStyle(.white.opacity(0.65))
                        .textSelection(.enabled)
                }
                .font(.system(size: 11, weight: .regular, design: .monospaced))
                .padding(.leading, 42) // align under message text
                .padding(.top, 4)
                .padding(.bottom, 8)
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .font(.system(size: 11, weight: .regular, design: .monospaced))
        .padding(.vertical, 1)
        .background(isExpanded ? Color.white.opacity(0.04) : .clear)
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

// MARK: - Agent Status Model

struct RadioAgentInfo: Identifiable {
    var id: String { name }
    let name: String
    let leaseToken: Int
    let expired: Bool
    let lastActive: String
}

// MARK: - Bubble Line (chat-style, v1 restored)

struct BubbleLine: View {
    let item: FeedItem
    var isExpanded: Bool = false
    @State private var appeared = false

    var senderColor: Color {
        switch item.sender.lowercased() {
        case "rex": return RheaTheme.accent
        case "orion": return .purple
        case "gemini": return RheaTheme.amber
        case "human": return RheaTheme.green
        case "relay": return .orange
        case "tribunal": return .cyan
        default: return .gray
        }
    }

    var isHuman: Bool { item.sender.lowercased() == "human" }

    var senderIcon: String {
        switch item.sender.lowercased() {
        case "rex": return "crown"
        case "orion": return "star.circle"
        case "gemini": return "sparkles"
        case "human": return "person.fill"
        case "relay": return "antenna.radiowaves.left.and.right"
        case "tribunal": return "scalemass"
        default: return "circle.dotted"
        }
    }

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            if isHuman { Spacer(minLength: 40) }

            // Agent avatar (left side for non-human)
            if !isHuman {
                Image(systemName: senderIcon)
                    .font(.system(size: 14))
                    .foregroundStyle(senderColor)
                    .frame(width: 24, height: 24)
                    .background(Circle().fill(senderColor.opacity(0.15)))
            }

            VStack(alignment: isHuman ? .trailing : .leading, spacing: 4) {
                // Header: sender → receiver + time
                HStack(spacing: 6) {
                    Text(item.sender.uppercased())
                        .font(.system(.caption2, design: .monospaced, weight: .bold))
                        .foregroundStyle(senderColor)
                    if !item.receiver.isEmpty && item.receiver != "all" {
                        Text("→ \(item.receiver.uppercased())")
                            .font(.system(.caption2, design: .monospaced))
                            .foregroundStyle(senderColor.opacity(0.5))
                    }
                    Spacer()
                    Text(formatBubbleTime(item.ts))
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundStyle(.secondary)
                }

                // Message body
                Text(isExpanded ? item.text : truncatedText(item.text))
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.85))
                    .multilineTextAlignment(.leading)
                    .textSelection(.enabled)

                // Type badge
                Text(item.type.uppercased())
                    .font(.system(size: 9, weight: .medium, design: .monospaced))
                    .foregroundStyle(senderColor.opacity(0.5))
            }
            .padding(10)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(senderColor.opacity(0.12))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .strokeBorder(senderColor.opacity(0.2), lineWidth: 0.5)
                    )
            )

            // Human avatar (right side)
            if isHuman {
                Image(systemName: senderIcon)
                    .font(.system(size: 14))
                    .foregroundStyle(senderColor)
                    .frame(width: 24, height: 24)
                    .background(Circle().fill(senderColor.opacity(0.15)))
            }

            if !isHuman { Spacer(minLength: 40) }
        }
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 8)
        .onAppear {
            withAnimation(.easeOut(duration: 0.2)) {
                appeared = true
            }
        }
    }

    func formatBubbleTime(_ iso: String) -> String {
        if let tIdx = iso.firstIndex(of: "T") {
            let time = iso[iso.index(after: tIdx)...]
            if time.count >= 5 { return String(time.prefix(5)) }
        }
        return ""
    }

    func truncatedText(_ text: String) -> String {
        let clean = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if clean.count > 200 {
            return String(clean.prefix(200)) + "…"
        }
        return clean
    }
}

// MARK: - Filter Chip

struct RadioFilterChip: View {
    let label: String
    let isActive: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.system(.caption2, design: .monospaced, weight: .bold))
                .foregroundStyle(isActive ? .black : color)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(
                    Capsule().fill(isActive ? color : color.opacity(0.15))
                )
        }
        .buttonStyle(.plain)
    }
}
