import SwiftUI

/// Compact tools hub — the "Rhea keyboard" tab.
/// Quick-action buttons in a horizontal strip, each expanding into its tool.
public struct ToolsHubView: View {
    @State private var activeTool: Tool = .clipboard
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    enum Tool: String, CaseIterable {
        case clipboard = "Clipboard"
        case office = "Office"
        case verify = "Verify"
        case scheduler = "Scheduler"

        var icon: String {
            switch self {
            case .clipboard: return "doc.on.clipboard"
            case .office: return "bubble.left.and.bubble.right"
            case .verify: return "checkmark.shield"
            case .scheduler: return "arrow.triangle.2.circlepath"
            }
        }

        var color: Color {
            switch self {
            case .clipboard: return RheaTheme.accent
            case .office: return RheaTheme.green
            case .verify: return RheaTheme.amber
            case .scheduler: return .purple
            }
        }
    }

    public init() {}

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Tool strip — the "keyboard" row
                toolStrip

                // Active tool content
                switch activeTool {
                case .clipboard:
                    ClipboardContentView()
                case .office:
                    OfficeToolView()
                case .verify:
                    QuickVerifyView()
                case .scheduler:
                    SchedulerToolView()
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("Tools")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
        }
    }

    private var toolStrip: some View {
        HStack(spacing: 0) {
            ForEach(Tool.allCases, id: \.rawValue) { tool in
                Button {
                    withAnimation(.spring(duration: 0.25)) { activeTool = tool }
                } label: {
                    VStack(spacing: 4) {
                        Image(systemName: tool.icon)
                            .font(.system(size: 16, weight: activeTool == tool ? .bold : .regular))
                            .foregroundStyle(activeTool == tool ? tool.color : .secondary)
                        Text(tool.rawValue)
                            .font(.system(size: 9, weight: .medium, design: .monospaced))
                            .foregroundStyle(activeTool == tool ? .white : .secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(
                        activeTool == tool
                            ? tool.color.opacity(0.12)
                            : Color.clear
                    )
                    .overlay(alignment: .bottom) {
                        if activeTool == tool {
                            Rectangle()
                                .fill(tool.color)
                                .frame(height: 2)
                        }
                    }
                }
                .buttonStyle(.plain)
            }
        }
        .background(RheaTheme.card)
    }
}

// MARK: - Clipboard content (reuses ClipboardView internals without NavigationStack)
private struct ClipboardContentView: View {
    var body: some View {
        ClipboardView()
            .navigationBarHidden(true)
    }
}

// MARK: - Office Tool
private struct OfficeToolView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var messages: [[String: String]] = []
    @State private var loading = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                sectionHeader("AGENT MESSAGES", icon: "bubble.left.and.bubble.right")

                if loading {
                    ProgressView().tint(RheaTheme.accent)
                        .frame(maxWidth: .infinity).padding(.vertical, 20)
                } else if messages.isEmpty {
                    VStack(spacing: 8) {
                        Image(systemName: "tray")
                            .font(.system(size: 28))
                            .foregroundStyle(.secondary)
                        Text("No office messages yet")
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Text("Agent messages from Rex, Orion, Gemini will appear here when synced.")
                            .font(.system(size: 11))
                            .foregroundStyle(.tertiary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 30)
                } else {
                    ForEach(Array(messages.enumerated()), id: \.offset) { _, msg in
                        officeRow(msg)
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.bottom, 20)
        }
        .background(RheaTheme.bg)
        .refreshable { await fetchMessages() }
        .task { await fetchMessages() }
    }

    private func sectionHeader(_ title: String, icon: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon).font(.system(size: 11)).foregroundStyle(RheaTheme.green)
            Text(title).font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.green.opacity(0.8))
            Spacer()
        }
        .padding(.top, 8)
    }

    private func officeRow(_ msg: [String: String]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                Text(msg["sender"] ?? "?")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(agentColor(msg["sender"] ?? ""))
                Image(systemName: "arrow.right")
                    .font(.system(size: 8))
                    .foregroundStyle(.secondary)
                Text(msg["receiver"] ?? "all")
                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                    .foregroundStyle(.secondary)
                Spacer()
                Text(msg["ts"] ?? "")
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.tertiary)
            }
            Text(msg["text"] ?? "(empty)")
                .font(.system(size: 12))
                .foregroundStyle(.white.opacity(0.85))
                .lineLimit(4)
        }
        .padding(10)
        .background(
            RoundedRectangle(cornerRadius: 10).fill(.white.opacity(0.04))
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(.white.opacity(0.06), lineWidth: 1))
        )
    }

    private func agentColor(_ agent: String) -> Color {
        switch agent.lowercased() {
        case "rex": return RheaTheme.accent
        case "orion": return RheaTheme.green
        case "gemini": return RheaTheme.amber
        case "hyperion": return .purple
        case "human": return .white
        default: return .secondary
        }
    }

    private func fetchMessages() async {
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBaseURL)/office/history?limit=30") else { return }
        do {
            var req = URLRequest(url: url)
            if let token = AuthManager.shared.token {
                req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            } else {
                req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
            }
            let (data, _) = try await URLSession.shared.data(for: req)
            if let resp = try? JSONDecoder().decode([String: [[String: String]]].self, from: data) {
                messages = resp["messages"] ?? []
            }
        } catch {}
    }
}

// MARK: - Quick Verify
private struct QuickVerifyView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var claim = ""
    @State private var result: String? = nil
    @State private var agreement: Double? = nil
    @State private var loading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                sectionHeader("QUICK VERIFY", icon: "checkmark.shield")

                VStack(spacing: 8) {
                    TextField("Type a claim to verify...", text: $claim, axis: .vertical)
                        .textFieldStyle(.plain)
                        .font(.system(size: 14))
                        .foregroundStyle(.white)
                        .lineLimit(2...4)
                        .padding(12)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(RheaTheme.card)
                                .overlay(RoundedRectangle(cornerRadius: 12).stroke(RheaTheme.cardBorder, lineWidth: 1))
                        )

                    Button {
                        Task { await verify() }
                    } label: {
                        HStack(spacing: 6) {
                            if loading {
                                ProgressView().tint(.white).controlSize(.small)
                            } else {
                                Image(systemName: "bolt.fill").font(.system(size: 11))
                            }
                            Text(loading ? "Verifying..." : "Verify")
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                        }
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Capsule().fill(RheaTheme.amber.opacity(0.3)))
                        .overlay(Capsule().stroke(RheaTheme.amber.opacity(0.5), lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                    .disabled(loading || claim.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
                .glassCard()

                if let score = agreement, let text = result {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("AGREEMENT")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(RheaTheme.amber)
                            Spacer()
                            Text(String(format: "%.0f%%", score * 100))
                                .font(.system(size: 18, weight: .bold, design: .rounded))
                                .foregroundStyle(score >= 0.7 ? RheaTheme.green : score >= 0.4 ? RheaTheme.amber : RheaTheme.red)
                        }
                        ProgressView(value: score)
                            .tint(score >= 0.7 ? RheaTheme.green : score >= 0.4 ? RheaTheme.amber : RheaTheme.red)

                        Text(text)
                            .font(.system(size: 12))
                            .foregroundStyle(.white.opacity(0.85))
                            .lineLimit(10)
                    }
                    .glassCard()
                }
            }
            .padding(.horizontal, 12)
            .padding(.bottom, 20)
        }
        .background(RheaTheme.bg)
    }

    private func sectionHeader(_ title: String, icon: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon).font(.system(size: 11)).foregroundStyle(RheaTheme.amber)
            Text(title).font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.amber.opacity(0.8))
            Spacer()
        }
        .padding(.top, 8)
    }

    private func verify() async {
        let text = claim.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBaseURL)/tribunal") else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = AuthManager.shared.token {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else {
            req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        }
        let body: [String: Any] = ["prompt": text, "k": 3, "tier": "cheap"]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                agreement = json["agreement_score"] as? Double
                result = json["consensus"] as? String
            }
        } catch {}
    }
}

// MARK: - Scheduler Tool
private struct SchedulerToolView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var prompt = ""
    @State private var target: Double = 0.9
    @State private var maxIter = 10
    @State private var loopId: String? = nil
    @State private var status: String = ""
    @State private var bestAgreement: Double = 0
    @State private var loading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                sectionHeader("CONSENSUS LOOP", icon: "arrow.triangle.2.circlepath")

                VStack(spacing: 10) {
                    TextField("Claim to reach consensus on...", text: $prompt, axis: .vertical)
                        .textFieldStyle(.plain)
                        .font(.system(size: 14))
                        .foregroundStyle(.white)
                        .lineLimit(2...4)
                        .padding(12)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(RheaTheme.card)
                                .overlay(RoundedRectangle(cornerRadius: 12).stroke(RheaTheme.cardBorder, lineWidth: 1))
                        )

                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("TARGET").font(.system(size: 9, weight: .bold, design: .monospaced)).foregroundStyle(.secondary)
                            Text(String(format: "%.0f%%", target * 100))
                                .font(.system(size: 20, weight: .bold, design: .rounded))
                                .foregroundStyle(.purple)
                        }
                        Slider(value: $target, in: 0.7...0.99, step: 0.05)
                            .tint(.purple)
                        VStack(alignment: .trailing, spacing: 2) {
                            Text("ROUNDS").font(.system(size: 9, weight: .bold, design: .monospaced)).foregroundStyle(.secondary)
                            Stepper("\(maxIter)", value: $maxIter, in: 3...50)
                                .font(.system(size: 12, design: .monospaced))
                        }
                    }

                    Button {
                        Task { await startLoop() }
                    } label: {
                        HStack(spacing: 6) {
                            if loading {
                                ProgressView().tint(.white).controlSize(.small)
                            } else {
                                Image(systemName: "play.fill").font(.system(size: 11))
                            }
                            Text(loading ? "Running..." : "Start Loop")
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                        }
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Capsule().fill(Color.purple.opacity(0.3)))
                        .overlay(Capsule().stroke(Color.purple.opacity(0.5), lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                    .disabled(loading || prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
                .glassCard()

                if let id = loopId {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("LOOP \(id.prefix(8))")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(.purple)
                            Spacer()
                            Text(status.uppercased())
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(status == "converged" ? RheaTheme.green : status == "running" ? RheaTheme.amber : .secondary)
                        }
                        if bestAgreement > 0 {
                            HStack {
                                Text("Best agreement:")
                                    .font(.system(size: 11, design: .monospaced)).foregroundStyle(.secondary)
                                Text(String(format: "%.1f%%", bestAgreement * 100))
                                    .font(.system(size: 14, weight: .bold, design: .rounded))
                                    .foregroundStyle(bestAgreement >= target ? RheaTheme.green : RheaTheme.amber)
                            }
                            ProgressView(value: bestAgreement)
                                .tint(bestAgreement >= target ? RheaTheme.green : .purple)
                        }
                    }
                    .glassCard()
                }
            }
            .padding(.horizontal, 12)
            .padding(.bottom, 20)
        }
        .background(RheaTheme.bg)
    }

    private func sectionHeader(_ title: String, icon: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon).font(.system(size: 11)).foregroundStyle(.purple)
            Text(title).font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(Color.purple.opacity(0.8))
            Spacer()
        }
        .padding(.top, 8)
    }

    private func startLoop() async {
        let text = prompt.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        loading = true
        defer { loading = false }
        guard let url = URL(string: "\(apiBaseURL)/workflows/scheduler/loop") else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = AuthManager.shared.token {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else {
            req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        }
        let body: [String: Any] = [
            "prompt": text,
            "target_agreement": target,
            "max_iterations": maxIter,
            "k": 5,
            "tier": "cheap"
        ]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                loopId = json["loop_id"] as? String
                status = json["status"] as? String ?? "pending"
            }
        } catch {}
    }
}
