import SwiftUI

// MARK: - AuthorView
// PlayUI author tool — compose relay messages, radio broadcasts, tasks, and notes
// from a single focused writing surface. Wired into Play pane system (⌘A).

public struct AuthorView: View {

    // ── Compose mode ──────────────────────────────────────────────────────────
    public enum ComposeMode: String, CaseIterable, Identifiable {
        case relay, broadcast, task, note
        public var id: String { rawValue }

        public var label: String {
            switch self {
            case .relay:     return "RELAY"
            case .broadcast: return "BROADCAST"
            case .task:      return "TASK"
            case .note:      return "NOTE"
            }
        }

        public var icon: String {
            switch self {
            case .relay:     return "arrow.turn.up.right"
            case .broadcast: return "antenna.radiowaves.left.and.right"
            case .task:      return "checklist"
            case .note:      return "note.text"
            }
        }

        public var color: Color {
            switch self {
            case .relay:     return RheaTheme.accent
            case .broadcast: return RheaTheme.amber
            case .task:      return RheaTheme.green
            case .note:      return RheaTheme.purple
            }
        }

        public var placeholder: String {
            switch self {
            case .relay:     return "Write your relay message…"
            case .broadcast: return "Write your broadcast to all agents…"
            case .task:      return "Describe the task…"
            case .note:      return "Write a note…"
            }
        }
    }

    // ── State ─────────────────────────────────────────────────────────────────
    @State private var mode: ComposeMode = .relay
    @State private var messageText: String = ""
    @State private var sender: String = "human"
    @State private var receiver: String = "rex"
    @State private var priority: String = "P1"
    @State private var noteTag: String = ""

    @State private var isSending = false
    @State private var lastResult: SendResult? = nil
    @State private var showResult = false
    @State private var history: [DraftRecord] = []
    @State private var showHistory = false

    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    private let knownAgents = ["rex", "orion", "gemini", "hyperion", "human", "shared"]
    private let knownSenders = ["human", "rex", "orion", "gemini"]
    private let priorities = ["P0", "P1", "P2", "P3"]

    public init() {}

    // ── Body ─────────────────────────────────────────────────────────────────

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                modePicker
                Divider().overlay(RheaTheme.accent.opacity(0.1))
                composeArea
                Divider().overlay(RheaTheme.accent.opacity(0.1))
                toolBar
            }
            .background(RheaTheme.bg)
            .navigationTitle("AUTHOR")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showHistory.toggle()
                    } label: {
                        Image(systemName: "clock.arrow.circlepath")
                            .foregroundStyle(RheaTheme.accent.opacity(0.8))
                    }
                    .help("Draft history")
                }
            }
            .sheet(isPresented: $showHistory) {
                historySheet
            }
            .overlay(alignment: .top) {
                if showResult, let r = lastResult {
                    resultBanner(r)
                        .transition(.move(edge: .top).combined(with: .opacity))
                        .padding(.top, 8)
                        .padding(.horizontal, 16)
                }
            }
        }
    }

    // ── Mode Picker ───────────────────────────────────────────────────────────

    private var modePicker: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(ComposeMode.allCases) { m in
                    Button {
                        withAnimation(.spring(duration: 0.2)) {
                            mode = m
                            clearResult()
                        }
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: m.icon)
                                .font(.system(size: 11, weight: .semibold))
                            Text(m.label)
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                        }
                        .foregroundStyle(mode == m ? .black : m.color)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 7)
                        .background(
                            Capsule()
                                .fill(mode == m ? m.color : m.color.opacity(0.12))
                        )
                        .overlay(
                            Capsule()
                                .stroke(mode == m ? .clear : m.color.opacity(0.3), lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .background(RheaTheme.bg)
    }

    // ── Compose Area ──────────────────────────────────────────────────────────

    @ViewBuilder
    private var composeArea: some View {
        VStack(spacing: 0) {
            // Header fields (mode-specific)
            headerFields
                .padding(.horizontal, 16)
                .padding(.top, 12)
                .padding(.bottom, 8)

            Divider().overlay(Color.white.opacity(0.05))

            // Main text editor
            ZStack(alignment: .topLeading) {
                if messageText.isEmpty {
                    Text(mode.placeholder)
                        .font(.system(size: 14, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.2))
                        .padding(.top, 14)
                        .padding(.leading, 17)
                        .allowsHitTesting(false)
                }
                TextEditor(text: $messageText)
                    .font(.system(size: 14, design: .monospaced))
                    .foregroundStyle(.white)
                    .scrollContentBackground(.hidden)
                    .background(.clear)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(RheaTheme.bg)
        }
    }

    // ── Header Fields ─────────────────────────────────────────────────────────

    @ViewBuilder
    private var headerFields: some View {
        switch mode {
        case .relay:
            VStack(spacing: 8) {
                fieldRow("FROM") {
                    agentPicker(selection: $sender, options: knownSenders, color: RheaTheme.green)
                }
                fieldRow("TO") {
                    agentPicker(selection: $receiver, options: knownAgents, color: RheaTheme.accent)
                }
            }
        case .broadcast:
            fieldRow("FROM") {
                agentPicker(selection: $sender, options: knownSenders, color: RheaTheme.amber)
            }
        case .task:
            VStack(spacing: 8) {
                fieldRow("ASSIGN TO") {
                    agentPicker(selection: $receiver, options: knownAgents, color: RheaTheme.green)
                }
                fieldRow("PRIORITY") {
                    priorityPicker
                }
            }
        case .note:
            fieldRow("TAG") {
                TextField("optional tag", text: $noteTag)
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundStyle(.white)
                    .textFieldStyle(.plain)
                    .frame(maxWidth: 160)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(RheaTheme.purple.opacity(0.12))
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(RheaTheme.purple.opacity(0.25), lineWidth: 1)
                            )
                    )
            }
        }
    }

    private func fieldRow<C: View>(_ label: String, @ViewBuilder content: () -> C) -> some View {
        HStack(spacing: 10) {
            Text(label)
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
                .frame(width: 64, alignment: .trailing)
            content()
            Spacer()
        }
    }

    private func agentPicker(selection: Binding<String>, options: [String], color: Color) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                ForEach(options, id: \.self) { opt in
                    Button {
                        withAnimation(.easeInOut(duration: 0.15)) {
                            selection.wrappedValue = opt
                        }
                    } label: {
                        Text(opt.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(selection.wrappedValue == opt ? .black : color)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(
                                Capsule()
                                    .fill(selection.wrappedValue == opt ? color : color.opacity(0.12))
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private var priorityPicker: some View {
        HStack(spacing: 6) {
            ForEach(priorities, id: \.self) { p in
                Button {
                    priority = p
                } label: {
                    Text(p)
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(priority == p ? .black : RheaTheme.priorityColor(p))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(
                            Capsule()
                                .fill(priority == p
                                      ? RheaTheme.priorityColor(p)
                                      : RheaTheme.priorityColor(p).opacity(0.12))
                        )
                }
                .buttonStyle(.plain)
            }
        }
    }

    // ── Toolbar ───────────────────────────────────────────────────────────────

    private var toolBar: some View {
        HStack(spacing: 12) {
            // Character count
            Text("\(messageText.count) chars")
                .font(.system(size: 10, design: .monospaced))
                .foregroundStyle(.secondary)

            Spacer()

            // Clear button
            Button {
                withAnimation { messageText = ""; clearResult() }
            } label: {
                Image(systemName: "xmark.circle")
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
            .disabled(messageText.isEmpty)
            .help("Clear")

            // Send / Create button
            Button {
                Task { await send() }
            } label: {
                HStack(spacing: 6) {
                    if isSending {
                        ProgressView()
                            .controlSize(.small)
                            .tint(.black)
                    } else {
                        Image(systemName: sendIcon)
                            .font(.system(size: 12, weight: .semibold))
                    }
                    Text(sendLabel)
                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                }
                .foregroundStyle(.black)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(
                    Capsule()
                        .fill(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                              ? mode.color.opacity(0.3)
                              : mode.color)
                )
            }
            .buttonStyle(.plain)
            .disabled(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending)
            .keyboardShortcut(.return, modifiers: .command)
            .help("Send ⌘↩")
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(RheaTheme.card.opacity(0.6))
    }

    private var sendLabel: String {
        switch mode {
        case .relay:     return "RELAY"
        case .broadcast: return "BROADCAST"
        case .task:      return "CREATE TASK"
        case .note:      return "SAVE NOTE"
        }
    }

    private var sendIcon: String {
        switch mode {
        case .relay:     return "arrow.turn.up.right"
        case .broadcast: return "antenna.radiowaves.left.and.right"
        case .task:      return "plus.circle.fill"
        case .note:      return "checkmark.circle.fill"
        }
    }

    // ── Result Banner ─────────────────────────────────────────────────────────

    private func resultBanner(_ result: SendResult) -> some View {
        HStack(spacing: 10) {
            Image(systemName: result.success ? "checkmark.circle.fill" : "xmark.circle.fill")
                .foregroundStyle(result.success ? RheaTheme.green : RheaTheme.red)
            Text(result.message)
                .font(.system(size: 12, weight: .semibold, design: .monospaced))
                .foregroundStyle(result.success ? RheaTheme.green : RheaTheme.red)
                .lineLimit(2)
            Spacer()
            Button {
                withAnimation { showResult = false }
            } label: {
                Image(systemName: "xmark")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(RheaTheme.card)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(
                            result.success ? RheaTheme.green.opacity(0.3) : RheaTheme.red.opacity(0.3),
                            lineWidth: 1
                        )
                )
        )
        .shadow(color: .black.opacity(0.4), radius: 8, y: 4)
        .zIndex(10)
    }

    // ── History Sheet ─────────────────────────────────────────────────────────

    private var historySheet: some View {
        NavigationStack {
            Group {
                if history.isEmpty {
                    ContentUnavailableView(
                        "No History",
                        systemImage: "clock.arrow.circlepath",
                        description: Text("Sent messages appear here")
                    )
                } else {
                    List {
                        ForEach(history) { record in
                            VStack(alignment: .leading, spacing: 6) {
                                HStack(spacing: 8) {
                                    Image(systemName: record.mode.icon)
                                        .font(.system(size: 11))
                                        .foregroundStyle(record.mode.color)
                                    Text(record.mode.label)
                                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                                        .foregroundStyle(record.mode.color)
                                    if let from = record.from, let to = record.to {
                                        Text("\(from.uppercased()) → \(to.uppercased())")
                                            .font(.system(size: 10, design: .monospaced))
                                            .foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                    Text(record.shortTimestamp)
                                        .font(.system(size: 9, design: .monospaced))
                                        .foregroundStyle(.secondary)
                                }
                                Text(record.text)
                                    .font(.system(size: 12, design: .monospaced))
                                    .foregroundStyle(.white.opacity(0.75))
                                    .lineLimit(3)

                                // Re-use button
                                Button {
                                    restoreFromHistory(record)
                                    showHistory = false
                                } label: {
                                    Text("RESTORE")
                                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                                        .foregroundStyle(.black)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 4)
                                        .background(Capsule().fill(record.mode.color))
                                }
                                .buttonStyle(.plain)
                            }
                            .padding(.vertical, 4)
                            .listRowBackground(RheaTheme.card)
                        }
                        .onDelete { indexSet in
                            history.remove(atOffsets: indexSet)
                        }
                    }
                    .scrollContentBackground(.hidden)
                    .background(RheaTheme.bg)
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("Draft History")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { showHistory = false }
                        .foregroundStyle(RheaTheme.accent)
                }
                if !history.isEmpty {
                    ToolbarItem(placement: .destructiveAction) {
                        Button("Clear All", role: .destructive) {
                            withAnimation { history.removeAll() }
                        }
                        .foregroundStyle(RheaTheme.red)
                    }
                }
            }
        }
        .preferredColorScheme(.dark)
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }

    // ── Send Logic ────────────────────────────────────────────────────────────

    private func send() async {
        let text = messageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        isSending = true
        clearResult()

        do {
            let result: SendResult
            switch mode {
            case .relay:
                result = try await sendRelay(text: text)
            case .broadcast:
                result = try await sendBroadcast(text: text)
            case .task:
                result = try await createTask(text: text)
            case .note:
                result = try await saveNote(text: text)
            }

            // Record in history
            let record = DraftRecord(
                id: UUID().uuidString,
                mode: mode,
                text: text,
                from: (mode == .relay || mode == .broadcast) ? sender : nil,
                to: (mode == .relay) ? receiver : (mode == .task) ? receiver : nil,
                timestamp: Date()
            )
            history.insert(record, at: 0)
            if history.count > 50 { history = Array(history.prefix(50)) }

            await MainActor.run {
                lastResult = result
                showResult = true
                isSending = false
                if result.success { messageText = "" }
                // Auto-dismiss success banner after 4 s
                if result.success {
                    Task {
                        try? await Task.sleep(nanoseconds: 4_000_000_000)
                        await MainActor.run {
                            withAnimation { showResult = false }
                        }
                    }
                }
            }
        } catch {
            await MainActor.run {
                lastResult = SendResult(success: false, message: error.localizedDescription)
                showResult = true
                isSending = false
            }
        }
    }

    // Relay: POST /office/send
    private func sendRelay(text: String) async throws -> SendResult {
        guard let url = URL(string: "\(apiBaseURL)/office/send") else {
            throw AuthorError.invalidURL
        }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        let payload: [String: Any] = [
            "sender": sender,
            "receiver": receiver,
            "text": text
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: payload)
        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            let errStr = String(data: data, encoding: .utf8) ?? ""
            throw AuthorError.http(code, errStr)
        }
        return SendResult(success: true, message: "Relay sent: \(sender.uppercased()) → \(receiver.uppercased())")
    }

    // Broadcast: POST /office/broadcast
    private func sendBroadcast(text: String) async throws -> SendResult {
        guard let url = URL(string: "\(apiBaseURL)/office/broadcast") else {
            throw AuthorError.invalidURL
        }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        let payload: [String: Any] = [
            "sender": sender,
            "text": text
        ]
        req.httpBody = try JSONSerialization.data(withJSONObject: payload)
        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            let errStr = String(data: data, encoding: .utf8) ?? ""
            throw AuthorError.http(code, errStr)
        }
        var sentCount = "all"
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let n = json["sent"] as? Int {
            sentCount = "\(n)"
        }
        return SendResult(success: true, message: "Broadcast sent to \(sentCount) agents")
    }

    // Task: POST /tasks?title=...&priority=...&agent=...
    private func createTask(text: String) async throws -> SendResult {
        var comps = URLComponents(string: "\(apiBaseURL)/tasks")
        comps?.queryItems = [
            URLQueryItem(name: "title", value: text),
            URLQueryItem(name: "priority", value: priority),
        ]
        if receiver != "shared" && !receiver.isEmpty {
            comps?.queryItems?.append(URLQueryItem(name: "agent", value: receiver))
        }
        guard let url = comps?.url else { throw AuthorError.invalidURL }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        let (_, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw AuthorError.http(code, "Task creation failed")
        }
        return SendResult(
            success: true,
            message: "Task created [\(priority)] → \(receiver.uppercased())"
        )
    }

    // Note: POST /feed/push with type=note
    private func saveNote(text: String) async throws -> SendResult {
        guard let url = URL(string: "\(apiBaseURL)/feed/push") else {
            throw AuthorError.invalidURL
        }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        var payload: [String: Any] = [
            "sender": "human",
            "text": text,
            "type": "note"
        ]
        if !noteTag.trimmingCharacters(in: .whitespaces).isEmpty {
            payload["tag"] = noteTag.trimmingCharacters(in: .whitespaces)
        }
        req.httpBody = try JSONSerialization.data(withJSONObject: payload)
        let (_, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse, http.statusCode < 300 else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw AuthorError.http(code, "Note push failed")
        }
        let tagStr = noteTag.isEmpty ? "" : " [\(noteTag)]"
        return SendResult(success: true, message: "Note saved to radio\(tagStr)")
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private func clearResult() {
        lastResult = nil
        showResult = false
    }

    private func restoreFromHistory(_ record: DraftRecord) {
        mode = record.mode
        messageText = record.text
        if let from = record.from { sender = from }
        if let to = record.to { receiver = to }
    }
}

// MARK: - Supporting Types

public struct SendResult {
    public let success: Bool
    public let message: String

    public init(success: Bool, message: String) {
        self.success = success
        self.message = message
    }
}

public struct DraftRecord: Identifiable {
    public let id: String
    public let mode: AuthorView.ComposeMode
    public let text: String
    public let from: String?
    public let to: String?
    public let timestamp: Date

    public var shortTimestamp: String {
        let cal = Calendar.current
        if cal.isDateInToday(timestamp) {
            let f = DateFormatter()
            f.dateFormat = "HH:mm"
            return f.string(from: timestamp)
        }
        let f = DateFormatter()
        f.dateFormat = "MM-dd HH:mm"
        return f.string(from: timestamp)
    }

    public init(id: String, mode: AuthorView.ComposeMode, text: String, from: String?, to: String?, timestamp: Date) {
        self.id = id
        self.mode = mode
        self.text = text
        self.from = from
        self.to = to
        self.timestamp = timestamp
    }
}

public enum AuthorError: LocalizedError {
    case invalidURL
    case http(Int, String)

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .http(let code, let desc):
            return "HTTP \(code): \(desc.prefix(120))"
        }
    }
}
