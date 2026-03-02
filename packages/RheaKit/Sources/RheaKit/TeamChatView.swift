import SwiftUI
import Starscream

// MARK: - Models

public struct FeedItem: Codable, Identifiable {
    public let id: String
    public let type: String
    public let sender: String
    public let receiver: String
    public let text: String
    public let ts: String

    public init(id: String, type: String, sender: String, receiver: String, text: String, ts: String) {
        self.id = id
        self.type = type
        self.sender = sender
        self.receiver = receiver
        self.text = text
        self.ts = ts
    }
}

public struct FeedResponse: Codable {
    public let items: [FeedItem]
    public let total: Int

    public init(items: [FeedItem], total: Int) {
        self.items = items
        self.total = total
    }
}

// MARK: - Live Radio View

public struct TeamChatView: View {
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
    @State private var knownAgents: [AgentDTO] = []
    @State private var wakingAgent: String? = nil
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @AppStorage("table_rex") private var tableRex = true
    @AppStorage("table_orion") private var tableOrion = true
    @AppStorage("table_gpt") private var tableGpt = false
    @AppStorage("table_hyperion") private var tableHyperion = true
    @AppStorage("table_gemini") private var tableGemini = false
    @AppStorage("table_shared") private var tableShared = false
    @AppStorage("family_visibility_only") private var familyVisibilityOnly = false
    @AppStorage("family_send_mode") private var familySendMode = true
    @AppStorage("table_experiment_mode") private var tableExperimentMode = true
    @AppStorage("table_session_id") private var tableSessionID = ""
    @AppStorage("table_turn_counter") private var tableTurn = 0
    @State private var activeTurnTag: String? = nil
    @State private var activeTurnTargets: [String] = []

    public init() {}

    /// All known senders (for filter chips)
    public var allSenders: [String] {
        Array(Set(items.map { $0.sender.lowercased() })).sorted()
    }

    /// Filtered items based on selected agent filter
    public var visibleItems: [FeedItem] {
        var base = items
        if familyVisibilityOnly {
            let allowed = Set(activeTableTargets().map { $0.lowercased() }).union(["human", "relay"])
            base = base.filter { item in
                let s = item.sender.lowercased()
                let r = item.receiver.lowercased()
                return allowed.contains(s) || allowed.contains(r)
            }
        }
        guard let agent = filterAgent else { return base }
        return base.filter { $0.sender.lowercased() == agent }
    }

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // ON AIR — who's active NOW
                onAirBanner

                if familySendMode {
                    tableExperimentBanner
                }

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
                .scrollDismissesKeyboard(.interactively)
                .onTapGesture {
                    #if os(iOS)
                    UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
                    #endif
                }

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
                ensureTableSession()
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

    var tableExperimentBanner: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Text("TABLE \(tableSessionID) #\(tableTurn)")
                    .font(.system(.caption2, design: .monospaced, weight: .bold))
                    .foregroundStyle(.white.opacity(0.9))
                Spacer()
                Toggle("tag", isOn: $tableExperimentMode)
                    .labelsHidden()
                    .scaleEffect(0.85)
                Button("new") {
                    tableSessionID = Self.newTableSessionID()
                    tableTurn = 0
                    activeTurnTag = nil
                    activeTurnTargets = []
                }
                .font(.system(.caption2, design: .monospaced, weight: .bold))
                .foregroundStyle(RheaTheme.green)
            }

            if let tag = activeTurnTag {
                let statuses = turnStatuses(tag: tag)
                let pending = statuses.filter { !$0.seen }.count
                HStack(spacing: 8) {
                    Text(tag)
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Text("pending \(pending)")
                        .font(.system(.caption2, design: .monospaced, weight: .bold))
                        .foregroundStyle(pending == 0 ? RheaTheme.green : RheaTheme.amber)
                    Spacer()
                }
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(statuses, id: \.seat) { row in
                            Text("\(row.seat.uppercased()) \(row.seen ? "ok" : "wait")")
                                .font(.system(.caption2, design: .monospaced, weight: .bold))
                                .foregroundStyle(row.seen ? .black : .white.opacity(0.8))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    Capsule().fill(row.seen ? RheaTheme.green : Color.white.opacity(0.12))
                                )
                        }
                    }
                }
            }
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

        if familySendMode {
            let targets = activeTableTargets()
            if !targets.isEmpty {
                var outbound = text
                var turnTag: String? = nil
                if tableExperimentMode {
                    ensureTableSession()
                    tableTurn += 1
                    let tag = "[TABLE:\(tableSessionID)#\(tableTurn)]"
                    outbound = "\(tag) \(text)"
                    turnTag = tag
                }
                var okCount = 0
                for target in targets {
                    if await sendOfficeMessage(to: target, text: outbound) {
                        okCount += 1
                    }
                }
                if okCount > 0 {
                    activeTurnTag = turnTag
                    activeTurnTargets = targets
                    withAnimation { composerText = "" }
                    await pollDelta()
                }
                return
            }
        }

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

    func activeTableTargets() -> [String] {
        var out: [String] = []
        if tableRex { out.append("rex") }
        if tableOrion { out.append("orion") }
        if tableGpt { out.append("gpt") }
        if tableHyperion { out.append("hyperion") }
        if tableGemini { out.append("gemini") }
        if tableShared { out.append("shared") }
        return out
    }

    static func newTableSessionID() -> String {
        let stamp = String(Int(Date().timeIntervalSince1970), radix: 36).uppercased()
        let tail = UUID().uuidString.replacingOccurrences(of: "-", with: "").prefix(4).uppercased()
        return "\(stamp)-\(tail)"
    }

    func ensureTableSession() {
        if tableSessionID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            tableSessionID = Self.newTableSessionID()
            tableTurn = 0
        }
    }

    func turnStatuses(tag: String) -> [(seat: String, seen: Bool)] {
        activeTurnTargets.map { seat in
            (seat: seat, seen: hasTaggedReply(seat: seat, tag: tag))
        }
    }

    func hasTaggedReply(seat: String, tag: String) -> Bool {
        items.contains { item in
            seatMatchesSender(seat: seat, sender: item.sender) && item.text.contains(tag)
        }
    }

    func seatMatchesSender(seat: String, sender: String) -> Bool {
        let s = sender.lowercased()
        let seatL = seat.lowercased()
        return s == seatL || s.hasPrefix("\(seatL)-") || s.hasPrefix("\(seatL)_")
    }

    func sendOfficeMessage(to receiver: String, text: String) async -> Bool {
        guard let url = URL(string: "\(apiBaseURL)/office/send") else { return false }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "sender": "human",
            "receiver": receiver,
            "text": text
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let http = response as? HTTPURLResponse {
                return http.statusCode < 300
            }
        } catch {}
        return false
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
                            // Pace dot
                            Circle()
                                .fill(agent.alive ? RheaTheme.paceColor(agent.pace) : .red)
                                .frame(width: 10, height: 10)

                            VStack(alignment: .leading, spacing: 2) {
                                HStack(spacing: 6) {
                                    Text(agent.name.uppercased())
                                        .font(.system(.body, design: .monospaced, weight: .bold))
                                        .foregroundStyle(agentColor(agent.name))
                                    Text(agent.mode.uppercased())
                                        .font(.system(.caption2, design: .rounded, weight: .semibold))
                                        .foregroundStyle(RheaTheme.modeColor(agent.mode))
                                }
                                HStack(spacing: 8) {
                                    Text(agent.officeStatus)
                                        .foregroundStyle(agent.alive ? .green.opacity(0.7) : .red.opacity(0.7))
                                    if agent.pendingMsgs > 0 {
                                        Text("\(agent.pendingMsgs) pending")
                                            .foregroundStyle(RheaTheme.amber)
                                    }
                                    if agent.tasksOpen > 0 || agent.tasksClaimed > 0 {
                                        Text("T:\(agent.tasksOpen)/\(agent.tasksClaimed)")
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                .font(.system(.caption2, design: .monospaced))
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
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { showAgentSheet = false }
                        .foregroundStyle(RheaTheme.green)
                }
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        knownAgents = []
                        Task { await fetchAgents() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundStyle(.white.opacity(0.7))
                    }
                }
            }
            .task { await fetchAgents() }
        }
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }

    // MARK: - Agent Networking

    struct TeamUnifiedStatusResponse: Codable {
        let _ts: String
        let agents: [String: AgentDTO]
    }

    func fetchAgents() async {
        guard let url = URL(string: "\(apiBaseURL)/agents/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let resp = try JSONDecoder().decode(TeamUnifiedStatusResponse.self, from: data)
            withAnimation {
                knownAgents = resp.agents.values.sorted { $0.name < $1.name }
            }
        } catch {
            print("[RadioAgents] fetch error: \(error)")
        }
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

public struct ConsoleLine: View {
    public let item: FeedItem
    public var isExpanded: Bool = false
    @State private var appeared = false

    public init(item: FeedItem, isExpanded: Bool = false) {
        self.item = item
        self.isExpanded = isExpanded
    }

    public var senderColor: Color {
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

    public var typeGlyph: String {
        switch item.type {
        case "office": return ">"
        case "outbox": return ">>"
        case "relay": return "~>"
        case "tribunal": return "⚖"
        case "broadcast": return "⦿"
        default: return "|"
        }
    }

    public var body: some View {
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

// MARK: - Bubble Line (chat-style, v1 restored)

public struct BubbleLine: View {
    public let item: FeedItem
    public var isExpanded: Bool = false
    @State private var appeared = false

    public init(item: FeedItem, isExpanded: Bool = false) {
        self.item = item
        self.isExpanded = isExpanded
    }

    public var senderColor: Color {
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

    public var isHuman: Bool { item.sender.lowercased() == "human" }

    public var senderIcon: String {
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

    public var body: some View {
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

public struct RadioFilterChip: View {
    public let label: String
    public let isActive: Bool
    public let color: Color
    public let action: () -> Void

    public init(label: String, isActive: Bool, color: Color, action: @escaping () -> Void) {
        self.label = label
        self.isActive = isActive
        self.color = color
        self.action = action
    }

    public var body: some View {
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
