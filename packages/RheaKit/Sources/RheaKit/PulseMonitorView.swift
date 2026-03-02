import SwiftUI

public struct PulseQueueSummary: Codable {
    public let total: Int
    public let counts: [String: Int]
    public let active_by_priority: [String: Int]
    public let stale_count: Int
    public let _updated: String?

    public init(total: Int, counts: [String: Int], active_by_priority: [String: Int], stale_count: Int, _updated: String?) {
        self.total = total
        self.counts = counts
        self.active_by_priority = active_by_priority
        self.stale_count = stale_count
        self._updated = _updated
    }
}

public struct PulseUnifiedResponse: Codable {
    public let _ts: String
    public let agents: [String: AgentDTO]

    public init(_ts: String, agents: [String: AgentDTO]) {
        self._ts = _ts
        self.agents = agents
    }
}

public struct PulseMonitorView: View {
    @State private var summary: PulseQueueSummary? = nil
    @State private var agents: [String: AgentDTO] = [:]
    @State private var loading = true
    @State private var lastAction = "idle"
    @State private var pollTimer: Timer? = nil
    @State private var flickerNote = "screen flicker observed"
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @AppStorage("table_rex") private var tableRex = true
    @AppStorage("table_orion") private var tableOrion = true
    @AppStorage("table_gpt") private var tableGpt = false
    @AppStorage("table_hyperion") private var tableHyperion = true
    @AppStorage("table_gemini") private var tableGemini = false
    @AppStorage("table_shared") private var tableShared = false
    @AppStorage("family_visibility_only") private var familyVisibilityOnly = false

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    pulseHeader

                    tableControlCard

                    flickerControlCard

                    queueCard

                    agentsCard
                }
                .padding(.horizontal)
                .padding(.bottom, 20)
            }
            .background(RheaTheme.bg)
            .navigationTitle("Pulse")
            #if os(iOS)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .refreshable { await refresh() }
            .task {
                await refresh()
                startPolling()
            }
            .onDisappear {
                pollTimer?.invalidate()
                pollTimer = nil
            }
        }
    }

    var pulseHeader: some View {
        let p0 = summary?.active_by_priority["P0"] ?? 0
        let stale = summary?.stale_count ?? 0
        let openCount = summary?.counts["open"] ?? 0
        let offline = agents.values.filter { !$0.alive }.count
        let risk = pulseRisk(p0: p0, stale: stale, offline: offline)

        return VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 10) {
                MetricPill(label: "Risk", value: risk.label.uppercased(), color: risk.color)
                MetricPill(label: "Open", value: "\(openCount)", color: .white)
                MetricPill(label: "P0", value: "\(p0)", color: RheaTheme.red)
                MetricPill(label: "Stale", value: "\(stale)", color: stale > 0 ? RheaTheme.amber : RheaTheme.green)
                MetricPill(label: "Offline", value: "\(offline)", color: offline > 0 ? RheaTheme.amber : RheaTheme.green)
            }
            Text("last action: \(lastAction)")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .glassCard()
    }

    var flickerControlCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Flicker Control")
                .font(.system(.headline, design: .rounded, weight: .bold))
                .foregroundStyle(.white)

            TextField("flicker note", text: $flickerNote)
                #if os(iOS)
                .textInputAutocapitalization(.never)
                #endif
                .autocorrectionDisabled()
                .padding(.horizontal, 10)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 10)
                        .fill(.white.opacity(0.07))
                )

            HStack(spacing: 8) {
                Button("Mark Flicker") {
                    Task { await markFlicker() }
                }
                .buttonStyle(.borderedProminent)

                Button("Wake REX") {
                    Task { await wake("REX") }
                }
                .buttonStyle(.bordered)

                Button("Create Trace Task") {
                    Task { await createTraceTask() }
                }
                .buttonStyle(.bordered)
            }
            .font(.caption)
        }
        .glassCard()
    }

    var tableControlCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Family Table")
                .font(.system(.headline, design: .rounded, weight: .bold))
                .foregroundStyle(.white)
            Text("Tap seats to include/exclude from current family scope.")
                .font(.caption2)
                .foregroundStyle(.secondary)

            HStack(spacing: 8) {
                SeatToggle(label: "REX", isOn: $tableRex, onColor: RheaTheme.accent)
                SeatToggle(label: "ORION", isOn: $tableOrion, onColor: .purple)
                SeatToggle(label: "GPT", isOn: $tableGpt, onColor: .indigo)
                SeatToggle(label: "HYPERION", isOn: $tableHyperion, onColor: .mint)
            }
            HStack(spacing: 8) {
                SeatToggle(label: "GEMINI", isOn: $tableGemini, onColor: RheaTheme.amber)
                SeatToggle(label: "SHARED", isOn: $tableShared, onColor: .gray)
                Spacer()
            }

            Toggle("Apply family scope to visibility", isOn: $familyVisibilityOnly)
                .font(.caption)
        }
        .glassCard()
    }

    var queueCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Queue")
                .font(.system(.headline, design: .rounded, weight: .bold))
                .foregroundStyle(.white)
            if let s = summary {
                QueueRow(label: "total", value: "\(s.total)")
                QueueRow(label: "open", value: "\(s.counts["open"] ?? 0)")
                QueueRow(label: "claimed", value: "\(s.counts["claimed"] ?? 0)")
                QueueRow(label: "done", value: "\(s.counts["done"] ?? 0)")
                QueueRow(label: "blocked", value: "\(s.counts["blocked"] ?? 0)")
                QueueRow(label: "P0 active", value: "\(s.active_by_priority["P0"] ?? 0)")
                QueueRow(label: "stale", value: "\(s.stale_count)")
            } else if loading {
                ProgressView()
            } else {
                Text("No queue data")
                    .foregroundStyle(.secondary)
            }
        }
        .glassCard()
    }

    var agentsCard: some View {
        let seatSet = Set(activeSeatNames().map { $0.lowercased() })
        let keys = agents.keys.sorted().filter { key in
            if !familyVisibilityOnly { return true }
            return seatSet.contains(key.lowercased())
        }
        return VStack(alignment: .leading, spacing: 8) {
            Text("Agents")
                .font(.system(.headline, design: .rounded, weight: .bold))
                .foregroundStyle(.white)
            if keys.isEmpty {
                Text(loading ? "Loading..." : "No agent data")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(keys, id: \.self) { key in
                    let a = agents[key]
                    HStack {
                        Circle()
                            .fill(RheaTheme.paceColor(a?.pace ?? "red"))
                            .frame(width: 8, height: 8)
                        VStack(alignment: .leading, spacing: 1) {
                            Text(key.uppercased())
                                .font(.system(.caption, design: .monospaced, weight: .semibold))
                                .foregroundStyle(.white)
                            HStack(spacing: 6) {
                                Text(a?.office_status ?? "unknown")
                                    .foregroundStyle((a?.alive ?? false) ? RheaTheme.green : RheaTheme.red)
                                if (a?.pending_msgs ?? 0) > 0 {
                                    Text("\(a?.pending_msgs ?? 0)msg")
                                        .foregroundStyle(RheaTheme.amber)
                                }
                            }
                            .font(.system(.caption2, design: .monospaced))
                        }
                        Spacer()
                        Text((a?.mode ?? "?").uppercased())
                            .font(.system(.caption2, design: .rounded, weight: .semibold))
                            .foregroundStyle(RheaTheme.modeColor(a?.mode ?? "normal"))
                        Button {
                            Task { await wake(key.uppercased()) }
                        } label: {
                            Text("Wake")
                                .font(.system(.caption2, design: .monospaced, weight: .bold))
                                .foregroundStyle(RheaTheme.amber)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(Capsule().strokeBorder(RheaTheme.amber.opacity(0.4), lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .glassCard()
    }

    func activeSeatNames() -> [String] {
        var out: [String] = []
        if tableRex { out.append("rex") }
        if tableOrion { out.append("orion") }
        if tableGpt { out.append("gpt") }
        if tableHyperion { out.append("hyperion") }
        if tableGemini { out.append("gemini") }
        if tableShared { out.append("shared") }
        return out
    }

    func pulseRisk(p0: Int, stale: Int, offline: Int) -> (label: String, color: Color) {
        if p0 > 0 || stale > 0 { return ("critical", RheaTheme.red) }
        if offline > 0 { return ("warn", RheaTheme.amber) }
        return ("ok", RheaTheme.green)
    }

    func startPolling() {
        pollTimer?.invalidate()
        pollTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { _ in
            Task { await refresh() }
        }
    }

    func refresh() async {
        loading = true
        defer { loading = false }
        await fetchSummary()
        await fetchAgents()
    }

    func fetchSummary() async {
        guard let url = URL(string: "\(apiBaseURL)/tasks/summary") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            summary = try JSONDecoder().decode(PulseQueueSummary.self, from: data)
        } catch {
            summary = nil
        }
    }

    func fetchAgents() async {
        guard let url = URL(string: "\(apiBaseURL)/agents/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let resp = try JSONDecoder().decode(PulseUnifiedResponse.self, from: data)
            agents = resp.agents
        } catch {
            agents = [:]
        }
    }

    func markFlicker() async {
        guard let url = URL(string: "\(apiBaseURL)/feed/push") else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let note = flickerNote.trimmingCharacters(in: .whitespacesAndNewlines)
        let payload: [String: Any] = [
            "sender": "human",
            "receiver": "all",
            "type": "radio",
            "text": "[flicker] \(note.isEmpty ? "screen flicker observed" : note)"
        ]
        req.httpBody = try? JSONSerialization.data(withJSONObject: payload)
        do {
            let (_, response) = try await URLSession.shared.data(for: req)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                lastAction = "flicker marked"
            } else {
                lastAction = "flicker mark failed"
            }
        } catch {
            lastAction = "flicker mark error"
        }
    }

    func wake(_ agent: String) async {
        guard let url = URL(string: "\(apiBaseURL)/agents/wake/\(agent)") else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        do {
            let (_, response) = try await URLSession.shared.data(for: req)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                lastAction = "wake \(agent) sent"
            } else {
                lastAction = "wake \(agent) failed"
            }
        } catch {
            lastAction = "wake \(agent) error"
        }
    }

    func createTraceTask() async {
        var comps = URLComponents(string: "\(apiBaseURL)/tasks")
        comps?.queryItems = [
            URLQueryItem(name: "title", value: "Investigate screen flicker + correlate with NDI pulse"),
            URLQueryItem(name: "priority", value: "P0"),
            URLQueryItem(name: "agent", value: "orion"),
            URLQueryItem(name: "tags", value: "flicker,ndi,diagnostics,pulse"),
        ]
        guard let url = comps?.url else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        do {
            let (_, response) = try await URLSession.shared.data(for: req)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                lastAction = "trace task created"
                await fetchSummary()
            } else {
                lastAction = "trace task create failed"
            }
        } catch {
            lastAction = "trace task create error"
        }
    }
}

private struct QueueRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .font(.system(.caption, design: .monospaced, weight: .semibold))
                .foregroundStyle(.white)
        }
    }
}

private struct SeatToggle: View {
    let label: String
    @Binding var isOn: Bool
    let onColor: Color

    var body: some View {
        Button {
            isOn.toggle()
        } label: {
            Text(label)
                .font(.system(.caption2, design: .monospaced, weight: .bold))
                .foregroundStyle(isOn ? .black : .secondary)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(
                    Capsule().fill(isOn ? onColor : .white.opacity(0.08))
                )
        }
        .buttonStyle(.plain)
    }
}
