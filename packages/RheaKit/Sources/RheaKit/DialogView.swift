import SwiftUI
import MarkdownUI

// MARK: - Models

public struct ChatMsg: Codable, Identifiable {
    public let id: String
    public let sender: String
    public let text: String
    public let ts: String

    public init(id: String, sender: String, text: String, ts: String) {
        self.id = id
        self.sender = sender
        self.text = text
        self.ts = ts
    }

    public var isHuman: Bool { sender.lowercased() == "human" }
    public var displayTime: String {
        // "2026-02-28T17:00:00Z" → "17:00"
        guard let tIdx = ts.firstIndex(of: "T"),
              ts.distance(from: tIdx, to: ts.endIndex) > 5 else { return "" }
        let start = ts.index(after: tIdx)
        let end = ts.index(start, offsetBy: 5)
        return String(ts[start..<end])
    }
}

public struct ChatHistoryResponse: Codable {
    public let messages: [ChatMsg]

    public init(messages: [ChatMsg]) {
        self.messages = messages
    }
}

public struct DialogRequest: Codable {
    public let text: String
    public let sender: String

    public init(text: String, sender: String) {
        self.text = text
        self.sender = sender
    }
}

public struct DialogResponse: Codable {
    public let reply: String?
    public let agreement_score: Double?
    public let models_responded: Int?
    public let elapsed_s: Double?
    public let ts: String?

    public init(reply: String?, agreement_score: Double?, models_responded: Int?, elapsed_s: Double?, ts: String?) {
        self.reply = reply
        self.agreement_score = agreement_score
        self.models_responded = models_responded
        self.elapsed_s = elapsed_s
        self.ts = ts
    }
}

// MARK: - Dialog View

public struct DialogView: View {
    @State private var messages: [ChatMsg] = []
    @State private var inputText = ""
    @State private var isSending = false
    @State private var targetAgent = "shared"
    @State private var pollTimer: Timer? = nil
    @State private var lastMsgID = ""
    @State private var agentResponse: String? = nil
    @State private var lastMeta: DialogResponse? = nil
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    private let agents = ["shared", "rex", "orion", "gemini", "hyperion"]

    public init() {}

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Agent picker
                agentPicker

                // Messages
                messageList

                // Input bar
                inputBar
            }
            .background(RheaTheme.bg)
            .navigationTitle("Tribunal")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button { fetchHistory() } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(RheaTheme.accent)
                    }
                }
            }
            .onAppear {
                fetchHistory()
                startPolling()
            }
            .onDisappear { stopPolling() }
        }
    }

    // MARK: - Agent Picker

    private var agentPicker: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(agents, id: \.self) { agent in
                    Button {
                        targetAgent = agent
                    } label: {
                        Text(agent.uppercased())
                            .font(.system(size: 11, weight: .semibold, design: .monospaced))
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(
                                Capsule()
                                    .fill(targetAgent == agent
                                          ? RheaTheme.accent.opacity(0.25)
                                          : RheaTheme.card)
                            )
                            .overlay(
                                Capsule()
                                    .stroke(targetAgent == agent
                                            ? RheaTheme.accent : RheaTheme.cardBorder,
                                            lineWidth: 1)
                            )
                            .foregroundColor(targetAgent == agent
                                             ? RheaTheme.accent : .secondary)
                    }
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
        .background(RheaTheme.bg)
    }

    // MARK: - Message List

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 10) {
                    ForEach(messages) { msg in
                        messageBubble(msg)
                            .id(msg.id)
                    }

                    // Show agent response inline if present
                    if let resp = agentResponse {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(targetAgent.uppercased())
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .foregroundColor(RheaTheme.green)
                                Markdown(resp)
                                    .font(.system(size: 13, design: .monospaced))
                                    .foregroundColor(.white.opacity(0.9))
                            }
                            .padding(12)
                            .background(
                                RoundedRectangle(cornerRadius: 12)
                                    .fill(RheaTheme.green.opacity(0.08))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 12)
                                            .stroke(RheaTheme.green.opacity(0.2), lineWidth: 1)
                                    )
                            )
                            Spacer(minLength: 40)
                        }
                        .padding(.horizontal, 16)
                        .id("agent-response")
                    }

                    // Tribunal consensus metadata
                    if let meta = lastMeta, meta.reply != nil {
                        HStack(spacing: 12) {
                            if let score = meta.agreement_score {
                                HStack(spacing: 4) {
                                    Image(systemName: "checkmark.shield")
                                        .font(.system(size: 10))
                                    Text("\(Int(score * 100))%")
                                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                                }
                                .foregroundColor(score >= 0.7 ? RheaTheme.green : score >= 0.4 ? RheaTheme.amber : RheaTheme.red)
                            }
                            if let models = meta.models_responded {
                                HStack(spacing: 4) {
                                    Image(systemName: "cpu")
                                        .font(.system(size: 10))
                                    Text("\(models) models")
                                        .font(.system(size: 11, design: .monospaced))
                                }
                                .foregroundColor(.secondary)
                            }
                            if let elapsed = meta.elapsed_s {
                                HStack(spacing: 4) {
                                    Image(systemName: "clock")
                                        .font(.system(size: 10))
                                    Text(String(format: "%.1fs", elapsed))
                                        .font(.system(size: 11, design: .monospaced))
                                }
                                .foregroundColor(.secondary)
                            }
                            Spacer()
                        }
                        .padding(.horizontal, 20)
                        .padding(.vertical, 4)
                        .id("tribunal-meta")
                    }
                }
                .padding(.vertical, 12)
            }
            .onChange(of: messages.count) { _ in
                if let last = messages.last {
                    withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                }
            }
            .onChange(of: agentResponse) { _ in
                if agentResponse != nil {
                    withAnimation { proxy.scrollTo("agent-response", anchor: .bottom) }
                }
            }
        }
    }

    private func messageBubble(_ msg: ChatMsg) -> some View {
        HStack {
            if msg.isHuman { Spacer(minLength: 40) }

            VStack(alignment: msg.isHuman ? .trailing : .leading, spacing: 4) {
                if !msg.isHuman {
                    Text(msg.sender.uppercased())
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundColor(agentColor(msg.sender))
                }

                Text(msg.text)
                    .font(.system(size: 14, design: .default))
                    .foregroundColor(.white.opacity(0.9))
                    .multilineTextAlignment(msg.isHuman ? .trailing : .leading)

                Text(msg.displayTime)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(.secondary.opacity(0.5))
            }
            .padding(12)
            .background(
                RoundedRectangle(cornerRadius: 14)
                    .fill(msg.isHuman
                          ? RheaTheme.accent.opacity(0.12)
                          : RheaTheme.card)
                    .overlay(
                        RoundedRectangle(cornerRadius: 14)
                            .stroke(msg.isHuman
                                    ? RheaTheme.accent.opacity(0.2)
                                    : RheaTheme.cardBorder, lineWidth: 1)
                    )
            )

            if !msg.isHuman { Spacer(minLength: 40) }
        }
        .padding(.horizontal, 16)
    }

    private func agentColor(_ sender: String) -> Color {
        switch sender.lowercased() {
        case "rex": return RheaTheme.accent
        case "orion": return RheaTheme.green
        case "gemini": return .purple
        case "hyperion": return RheaTheme.amber
        default: return .secondary
        }
    }

    // MARK: - Input Bar

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField("Message \(targetAgent)…", text: $inputText, axis: .vertical)
                .textFieldStyle(.plain)
                .font(.system(size: 14))
                .padding(10)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(RheaTheme.card)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(RheaTheme.cardBorder, lineWidth: 1)
                        )
                )
                .lineLimit(1...5)
                .foregroundColor(.white)
                .submitLabel(.send)
                .onSubmit { send() }

            Button(action: send) {
                Group {
                    if isSending {
                        ProgressView()
                            .scaleEffect(0.7)
                    } else {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 28))
                    }
                }
                .foregroundColor(inputText.trimmingCharacters(in: .whitespaces).isEmpty
                                 ? .secondary : RheaTheme.accent)
            }
            .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty || isSending)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(RheaTheme.bg)
    }

    // MARK: - Networking

    private func send() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        inputText = ""
        isSending = true
        agentResponse = nil

        // Optimistic local message
        let localMsg = ChatMsg(
            id: UUID().uuidString,
            sender: "human",
            text: text,
            ts: ISO8601DateFormatter().string(from: Date())
        )
        messages.append(localMsg)

        // Send via /dialog for real LLM tribunal response
        let body = DialogRequest(text: text, sender: "human")
        guard let url = URL(string: "\(apiBaseURL)/dialog"),
              let payload = try? JSONEncoder().encode(body) else {
            isSending = false
            return
        }

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        req.httpBody = payload

        URLSession.shared.dataTask(with: req) { data, _, error in
            DispatchQueue.main.async {
                isSending = false
                if let data = data,
                   let resp = try? JSONDecoder().decode(DialogResponse.self, from: data) {
                    lastMeta = resp
                    if let reply = resp.reply, !reply.isEmpty {
                        agentResponse = reply
                        // Also add as a chat message so it persists in scroll
                        let replyMsg = ChatMsg(
                            id: UUID().uuidString,
                            sender: "rhea",
                            text: reply,
                            ts: resp.ts ?? ISO8601DateFormatter().string(from: Date())
                        )
                        messages.append(replyMsg)
                        agentResponse = nil
                    }
                }
            }
        }.resume()
    }

    private func fetchHistory() {
        guard let url = URL(string: "\(apiBaseURL)/chat?limit=50") else { return }
        var req = URLRequest(url: url)
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        URLSession.shared.dataTask(with: req) { data, _, _ in
            guard let data = data,
                  let resp = try? JSONDecoder().decode(ChatHistoryResponse.self, from: data) else { return }
            DispatchQueue.main.async {
                messages = resp.messages
                lastMsgID = resp.messages.last?.id ?? ""
            }
        }.resume()
    }

    private func startPolling() {
        pollTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
            fetchHistory()
        }
    }

    private func stopPolling() {
        pollTimer?.invalidate()
        pollTimer = nil
    }
}
