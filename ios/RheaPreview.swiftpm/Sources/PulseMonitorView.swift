import SwiftUI

struct PulseQueueSummary: Codable {
    let total: Int
    let counts: [String: Int]
    let active_by_priority: [String: Int]
    let stale_count: Int
    let _updated: String?
}

struct PulseAgentLeaseDTO: Codable {
    let agent: String?
    let lease_token: Int?
    let expired: Bool?
    let last_active: String?
}

struct PulseMonitorView: View {
    @State private var summary: PulseQueueSummary? = nil
    @State private var agents: [String: PulseAgentLeaseDTO] = [:]
    @State private var loading = true
    @State private var lastAction = "idle"
    @State private var pollTimer: Timer? = nil
    @State private var flickerNote = "screen flicker observed"
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    pulseHeader

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
        let offline = agents.values.filter { $0.expired ?? true }.count
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
                .textInputAutocapitalization(.never)
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
        VStack(alignment: .leading, spacing: 8) {
            Text("Agents")
                .font(.system(.headline, design: .rounded, weight: .bold))
                .foregroundStyle(.white)
            if agents.isEmpty {
                Text(loading ? "Loading..." : "No agent data")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(agents.keys.sorted(), id: \.self) { key in
                    let a = agents[key]
                    HStack {
                        Circle()
                            .fill((a?.expired ?? true) ? RheaTheme.red : RheaTheme.green)
                            .frame(width: 8, height: 8)
                        Text(key.uppercased())
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(.white)
                        Spacer()
                        Text("lease \(a?.lease_token ?? 0)")
                            .font(.system(.caption2, design: .monospaced))
                            .foregroundStyle(.secondary)
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
        guard let url = URL(string: "\(apiBaseURL)/agents") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            agents = try JSONDecoder().decode([String: PulseAgentLeaseDTO].self, from: data)
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
