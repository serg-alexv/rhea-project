import SwiftUI
import MarkdownUI

/// Unified operations dashboard — combines verify, feed, budget, office, health
/// into a single scrollable pane. Replaces 5 separate tabs.
public struct OpsView: View {
    // MARK: - State

    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    // Connection
    @State private var apiReachable = false

    // Agents (budget + health)
    @State private var agents: [AgentDTO] = []

    // Queue (health)
    @State private var queueSummary: PulseQueueSummary? = nil

    // Feed
    @State private var feedItems: [FeedItem] = []

    // Office
    @State private var officeMessages: [[String: Any]] = []

    // Verify (tribunal)
    @State private var verifyInput = ""
    @State private var isSending = false
    @State private var lastReply: String? = nil
    @State private var lastMeta: DialogResponse? = nil

    // Polling
    @State private var pollTimer: Timer? = nil

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 12) {
                    statusBar
                    verifySection
                    feedSection
                    budgetSection
                    officeSection
                    queueSection
                }
                .padding(.horizontal, 12)
                .padding(.bottom, 20)
            }
            .background(RheaTheme.bg)
            .navigationTitle("Ops")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .refreshable { await refreshAll() }
            .task {
                await refreshAll()
                startPolling()
            }
            .onDisappear { stopPolling() }
        }
    }

    // MARK: - Status Bar

    private var statusBar: some View {
        let totalTokens = agents.reduce(0) { $0 + $1.T_day }
        let totalCost = agents.reduce(0.0) { $0 + $1.dollar_day }
        let aliveCount = agents.filter { $0.alive }.count
        let p0 = queueSummary?.active_by_priority["P0"] ?? 0
        let stale = queueSummary?.stale_count ?? 0
        let offline = agents.filter { !$0.alive }.count
        let riskLevel = pulseRisk(p0: p0, stale: stale, offline: offline)

        return VStack(spacing: 8) {
            HStack(spacing: 10) {
                // Connection dot
                Circle()
                    .fill(apiReachable ? RheaTheme.green : RheaTheme.red)
                    .frame(width: 8, height: 8)
                Text(apiReachable ? "ONLINE" : "OFFLINE")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(apiReachable ? RheaTheme.green : RheaTheme.red)
                Spacer()
                Text(riskLevel.label.uppercased())
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(riskLevel.color)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Capsule().fill(riskLevel.color.opacity(0.15)))
            }

            HStack(spacing: 12) {
                MetricPill(label: "Agents", value: "\(aliveCount)/\(agents.count)", color: RheaTheme.accent)
                MetricPill(label: "Tokens", value: formatTokens(totalTokens), color: .white)
                MetricPill(label: "Cost", value: "$\(String(format: "%.2f", totalCost))", color: RheaTheme.amber)
                MetricPill(label: "P0", value: "\(p0)", color: p0 > 0 ? RheaTheme.red : RheaTheme.green)
            }
        }
        .glassCard()
    }

    // MARK: - Verify (Tribunal)

    private var verifySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("VERIFY", icon: "checkmark.shield")

            HStack(spacing: 8) {
                TextField("Ask the tribunal...", text: $verifyInput)
                    .textFieldStyle(.plain)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundStyle(.white)
                    .padding(10)
                    .background(
                        RoundedRectangle(cornerRadius: 10)
                            .fill(.white.opacity(0.06))
                    )
                    .submitLabel(.send)
                    .onSubmit { Task { await sendVerify() } }

                Button {
                    Task { await sendVerify() }
                } label: {
                    if isSending {
                        ProgressView().tint(RheaTheme.accent)
                    } else {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.title3)
                            .foregroundStyle(verifyInput.isEmpty ? .secondary : RheaTheme.accent)
                    }
                }
                .disabled(verifyInput.trimmingCharacters(in: .whitespaces).isEmpty || isSending)
            }

            if let reply = lastReply {
                VStack(alignment: .leading, spacing: 4) {
                    Markdown(reply)
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.85))
                        .lineLimit(6)

                    if let meta = lastMeta {
                        HStack(spacing: 10) {
                            if let score = meta.agreement_score {
                                HStack(spacing: 3) {
                                    Image(systemName: "checkmark.shield")
                                        .font(.system(size: 9))
                                    Text("\(Int(score * 100))%")
                                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                                }
                                .foregroundStyle(score >= 0.7 ? RheaTheme.green : score >= 0.4 ? RheaTheme.amber : RheaTheme.red)
                            }
                            if let models = meta.models_responded {
                                Text("\(models) models")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundStyle(.secondary)
                            }
                            if let elapsed = meta.elapsed_s {
                                Text(String(format: "%.1fs", elapsed))
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
                .padding(10)
                .background(
                    RoundedRectangle(cornerRadius: 10)
                        .fill(RheaTheme.green.opacity(0.06))
                        .overlay(
                            RoundedRectangle(cornerRadius: 10)
                                .stroke(RheaTheme.green.opacity(0.15), lineWidth: 1)
                        )
                )
            }
        }
        .glassCard()
    }

    // MARK: - Feed (Radio)

    private var feedSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            sectionHeader("FEED", icon: "waveform")

            if feedItems.isEmpty {
                Text("No activity")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 8)
            } else {
                ForEach(feedItems.prefix(5)) { item in
                    HStack(alignment: .top, spacing: 0) {
                        Text(formatTime(item.ts))
                            .foregroundStyle(.green.opacity(0.5))
                        Text(" ")
                        Text(item.sender.prefix(6).uppercased())
                            .foregroundStyle(agentColor(item.sender))
                        Text(" ")
                        Text(item.text.replacingOccurrences(of: "\n", with: " ").prefix(80))
                            .foregroundStyle(.white.opacity(0.75))
                            .lineLimit(1)
                    }
                    .font(.system(size: 10, weight: .regular, design: .monospaced))
                }
            }
        }
        .glassCard()
    }

    // MARK: - Budget (Governor)

    private var budgetSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("BUDGET", icon: "dollarsign.circle")

            if agents.isEmpty {
                Text("No agent data")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            } else {
                ForEach(agents.prefix(4)) { agent in
                    HStack(spacing: 8) {
                        Circle()
                            .fill(RheaTheme.paceColor(agent.pace))
                            .frame(width: 8, height: 8)
                        Text(agent.agent.uppercased())
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(.white)
                            .frame(width: 60, alignment: .leading)
                        Text(formatTokens(agent.T_day))
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Spacer()
                        if let cap = agent.budget_cap, cap > 0 {
                            let frac = min(agent.dollar_day / cap, 1.0)
                            GeometryReader { geo in
                                ZStack(alignment: .leading) {
                                    RoundedRectangle(cornerRadius: 3)
                                        .fill(.white.opacity(0.08))
                                    RoundedRectangle(cornerRadius: 3)
                                        .fill(frac < 0.6 ? RheaTheme.green : frac < 0.85 ? RheaTheme.amber : RheaTheme.red)
                                        .frame(width: geo.size.width * frac)
                                }
                            }
                            .frame(width: 60, height: 4)
                        }
                        Text("$\(String(format: "%.2f", agent.dollar_day))")
                            .font(.system(size: 10, weight: .semibold, design: .monospaced))
                            .foregroundStyle(RheaTheme.amber)
                            .frame(width: 50, alignment: .trailing)
                    }
                }
                if agents.count > 4 {
                    Text("+\(agents.count - 4) more")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
            }
        }
        .glassCard()
    }

    // MARK: - Office

    private var officeSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            sectionHeader("OFFICE", icon: "bubble.left.and.bubble.right")

            if officeMessages.isEmpty {
                Text("No messages")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 4)
            } else {
                ForEach(Array(officeMessages.prefix(3).enumerated()), id: \.offset) { _, msg in
                    let sender = msg["sender"] as? String ?? "?"
                    let receiver = msg["receiver"] as? String ?? "?"
                    let text = msg["text"] as? String ?? ""
                    HStack(alignment: .top, spacing: 6) {
                        Text(sender.prefix(4).uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(agentColor(sender))
                        Image(systemName: "arrow.right")
                            .font(.system(size: 8))
                            .foregroundStyle(.secondary)
                        Text(receiver.prefix(4).uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.amber)
                        Text(text.replacingOccurrences(of: "\n", with: " ").prefix(60))
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.7))
                            .lineLimit(1)
                    }
                }
            }
        }
        .glassCard()
    }

    // MARK: - Queue

    private var queueSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            sectionHeader("QUEUE", icon: "checklist")

            if let s = queueSummary {
                HStack(spacing: 16) {
                    queuePill("Open", count: s.counts["open"] ?? 0, color: .white)
                    queuePill("Claimed", count: s.counts["claimed"] ?? 0, color: RheaTheme.accent)
                    queuePill("Done", count: s.counts["done"] ?? 0, color: RheaTheme.green)
                    queuePill("Blocked", count: s.counts["blocked"] ?? 0, color: RheaTheme.red)
                }
            } else {
                Text("No queue data")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
        }
        .glassCard()
    }

    // MARK: - Helpers

    private func sectionHeader(_ title: String, icon: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 11))
                .foregroundStyle(RheaTheme.accent)
            Text(title)
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.8))
            Spacer()
        }
    }

    private func queuePill(_ label: String, count: Int, color: Color) -> some View {
        VStack(spacing: 2) {
            Text("\(count)")
                .font(.system(size: 14, weight: .bold, design: .rounded))
                .foregroundStyle(count > 0 ? color : .secondary)
            Text(label)
                .font(.system(size: 9, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    private func formatTokens(_ n: Int) -> String {
        if n >= 1_000_000 { return "\(n / 1_000_000)M" }
        if n >= 1_000 { return "\(n / 1_000)K" }
        return "\(n)"
    }

    private func formatTime(_ iso: String) -> String {
        if let tIdx = iso.firstIndex(of: "T") {
            let time = iso[iso.index(after: tIdx)...]
            if time.count >= 5 { return String(time.prefix(5)) }
        }
        return "     "
    }

    private func agentColor(_ agent: String) -> Color {
        switch agent.lowercased() {
        case "rex": return RheaTheme.accent
        case "orion": return .purple
        case "gemini": return RheaTheme.amber
        case "human": return RheaTheme.green
        case "relay": return .orange
        default: return .gray
        }
    }

    private func pulseRisk(p0: Int, stale: Int, offline: Int) -> (label: String, color: Color) {
        if p0 > 0 || stale > 0 { return ("critical", RheaTheme.red) }
        if offline > 0 { return ("warn", RheaTheme.amber) }
        return ("ok", RheaTheme.green)
    }

    // MARK: - Networking

    private func refreshAll() async {
        await withTaskGroup(of: Void.self) { group in
            group.addTask { await fetchHealth() }
            group.addTask { await fetchAgents() }
            group.addTask { await fetchFeed() }
            group.addTask { await fetchOffice() }
            group.addTask { await fetchQueue() }
        }
    }

    private func fetchHealth() async {
        guard let url = URL(string: "\(apiBaseURL)/health") else { return }
        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                await MainActor.run { apiReachable = true }
            }
        } catch {
            await MainActor.run { apiReachable = false }
        }
    }

    private func fetchAgents() async {
        guard let url = URL(string: "\(apiBaseURL)/agents/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            struct Resp: Codable { let _ts: String; let agents: [String: AgentDTO] }
            let resp = try JSONDecoder().decode(Resp.self, from: data)
            let sorted = resp.agents.values.sorted { $0.agent < $1.agent }
            await MainActor.run {
                agents = sorted
                apiReachable = true
            }
        } catch {
            await MainActor.run { agents = [] }
        }
    }

    private func fetchFeed() async {
        guard let url = URL(string: "\(apiBaseURL)/feed?limit=10") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(FeedResponse.self, from: data)
            await MainActor.run { feedItems = response.items }
        } catch {
            await MainActor.run { feedItems = [] }
        }
    }

    private func fetchOffice() async {
        guard let url = URL(string: "\(apiBaseURL)/cc/office?limit=5") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let msgs = json["office"] as? [[String: Any]] {
                await MainActor.run { officeMessages = msgs }
            }
        } catch {
            await MainActor.run { officeMessages = [] }
        }
    }

    private func fetchQueue() async {
        guard let url = URL(string: "\(apiBaseURL)/tasks/summary") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let summary = try JSONDecoder().decode(PulseQueueSummary.self, from: data)
            await MainActor.run { queueSummary = summary }
        } catch {
            await MainActor.run { queueSummary = nil }
        }
    }

    private func sendVerify() async {
        let text = verifyInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isSending else { return }
        isSending = true
        verifyInput = ""

        let body = DialogRequest(text: text, sender: "human")
        guard let url = URL(string: "\(apiBaseURL)/dialog"),
              let payload = try? JSONEncoder().encode(body) else {
            isSending = false
            return
        }

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let jwt = AuthManager.shared.token {
            req.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        } else {
            req.setValue(RheaAPI.shared.apiKey, forHTTPHeaderField: "X-API-Key")
        }
        req.httpBody = payload

        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            let resp = try JSONDecoder().decode(DialogResponse.self, from: data)
            await MainActor.run {
                isSending = false
                lastMeta = resp
                lastReply = resp.reply
            }
        } catch {
            await MainActor.run {
                isSending = false
                lastReply = "Error: \(error.localizedDescription)"
            }
        }
    }

    private func startPolling() {
        pollTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
            Task { await refreshAll() }
        }
    }

    private func stopPolling() {
        pollTimer?.invalidate()
        pollTimer = nil
    }
}
