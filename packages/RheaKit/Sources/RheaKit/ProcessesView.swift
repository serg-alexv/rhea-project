import SwiftUI

/// Supervisor session manager — spawn, kill, view output, send input.
/// Ported from Play macOS → iOS-compatible.
public struct ProcessesView: View {
    @ObservedObject private var store = RheaStore.shared
    @State private var sessions: [SupervisorSession] = []
    @State private var selectedSession: SupervisorSession? = nil
    @State private var sessionOutput = ""
    @State private var inputText = ""
    @State private var loading = true
    @State private var showSpawn = false
    @State private var spawnAgent = "rex"
    @State private var spawnPrompt = ""
    private let api = RheaAPI.shared

    private let knownAgents = ["rex", "orion", "gemini", "hyperion", "shared", "b2"]

    public init() {}

    public var body: some View {
        NavigationStack {
            Group {
                if loading && sessions.isEmpty {
                    ProgressView().controlSize(.regular)
                } else {
                    sessionContent
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("PROCESSES")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    let running = sessions.filter { $0.isAlive }.count
                    HStack(spacing: 8) {
                        badge("RUN", "\(running)", RheaTheme.green)
                        badge("ALL", "\(sessions.count)", .white)
                    }
                }
                ToolbarItem(placement: .automatic) {
                    HStack(spacing: 12) {
                        Button { showSpawn = true } label: {
                            Image(systemName: "plus.circle.fill")
                                .foregroundStyle(RheaTheme.green)
                        }
                        Button { Task { await fetchSessions() } } label: {
                            Image(systemName: "arrow.clockwise")
                                .font(.system(size: 13))
                        }
                    }
                }
            }
            .task { await fetchSessions() }
            .refreshable { await fetchSessions() }
            .sheet(isPresented: $showSpawn) { spawnSheet }
        }
    }

    // MARK: - Session List + Detail

    private var sessionContent: some View {
        ScrollView {
            VStack(spacing: 8) {
                // Agent quick-wake row
                agentQuickActions

                if sessions.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "terminal")
                            .font(.system(size: 28))
                            .foregroundStyle(.white.opacity(0.12))
                        Text("No supervisor sessions")
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.25))
                    }
                    .padding(.top, 40)
                } else {
                    ForEach(sessions) { sess in
                        sessionCard(sess)
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
    }

    private var agentQuickActions: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                ForEach(store.agents) { agent in
                    Button {
                        Task { _ = try? await api.wakeAgent(agent.name) }
                    } label: {
                        HStack(spacing: 4) {
                            Circle()
                                .fill(agent.alive ? RheaTheme.green : RheaTheme.red)
                                .frame(width: 5, height: 5)
                            Text(agent.name.prefix(3).uppercased())
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                            Image(systemName: "bolt.fill")
                                .font(.system(size: 7))
                        }
                        .foregroundStyle(agent.alive ? .secondary : RheaTheme.amber)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(
                            Capsule()
                                .fill(RheaTheme.card)
                                .overlay(Capsule().stroke(agent.alive ? RheaTheme.green.opacity(0.1) : RheaTheme.amber.opacity(0.2), lineWidth: 1))
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private func sessionCard(_ sess: SupervisorSession) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header row
            HStack(spacing: 10) {
                Circle()
                    .fill(sess.isAlive ? RheaTheme.green : RheaTheme.red)
                    .frame(width: 8, height: 8)

                Text(sess.agent?.uppercased() ?? "?")
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)

                Text(String(sess.id.prefix(8)))
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.3))

                Spacer()

                Text((sess.status ?? "?").uppercased())
                    .font(.system(size: 8, weight: .bold, design: .monospaced))
                    .foregroundStyle(sess.isAlive ? RheaTheme.green : .secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Capsule().fill((sess.isAlive ? RheaTheme.green : Color.secondary).opacity(0.12)))

                if sess.isAlive {
                    Button {
                        Task {
                            _ = try? await api.supervisorKill(sessionId: sess.id)
                            await fetchSessions()
                        }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(RheaTheme.red.opacity(0.6))
                    }
                }
            }

            // Expanded output (tap to toggle)
            if selectedSession?.id == sess.id {
                VStack(spacing: 6) {
                    ScrollView {
                        Text(sessionOutput.isEmpty ? "Waiting for output..." : sessionOutput)
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(RheaTheme.green.opacity(0.8))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                    .frame(maxHeight: 200)
                    .background(Color.black.opacity(0.3))
                    .cornerRadius(6)

                    if sess.isAlive {
                        HStack(spacing: 8) {
                            TextField("Input...", text: $inputText)
                                .textFieldStyle(.plain)
                                .font(.system(size: 12, design: .monospaced))
                                .padding(8)
                                .background(RoundedRectangle(cornerRadius: 6).fill(RheaTheme.card))
                                .onSubmit { sendInput(sess) }

                            Button { sendInput(sess) } label: {
                                Image(systemName: "arrow.right.circle.fill")
                                    .font(.system(size: 20))
                                    .foregroundStyle(RheaTheme.accent)
                            }
                            .disabled(inputText.isEmpty)
                        }
                    }
                }
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(selectedSession?.id == sess.id ? RheaTheme.accent.opacity(0.06) : RheaTheme.card.opacity(0.5))
        )
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) {
                if selectedSession?.id == sess.id {
                    selectedSession = nil
                } else {
                    selectedSession = sess
                    Task { await fetchOutput(sess.id) }
                }
            }
        }
    }

    // MARK: - Spawn Sheet

    private var spawnSheet: some View {
        NavigationStack {
            VStack(spacing: 20) {
                // Agent picker
                VStack(alignment: .leading, spacing: 8) {
                    Text("AGENT")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 6) {
                            ForEach(knownAgents, id: \.self) { agent in
                                Button {
                                    spawnAgent = agent
                                } label: {
                                    Text(agent.uppercased())
                                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 8)
                                        .background(
                                            Capsule().fill(spawnAgent == agent ? RheaTheme.accent.opacity(0.2) : RheaTheme.card)
                                        )
                                        .foregroundStyle(spawnAgent == agent ? RheaTheme.accent : .secondary)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                }

                // Prompt
                VStack(alignment: .leading, spacing: 8) {
                    Text("PROMPT (optional)")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)

                    TextEditor(text: $spawnPrompt)
                        .font(.system(size: 12, design: .monospaced))
                        .frame(minHeight: 60)
                        .scrollContentBackground(.hidden)
                        .background(RoundedRectangle(cornerRadius: 8).fill(RheaTheme.card))
                }

                Spacer()
            }
            .padding(20)
            .background(RheaTheme.bg)
            .navigationTitle("SPAWN SESSION")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showSpawn = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        Task {
                            _ = try? await api.supervisorSpawn(
                                agent: spawnAgent,
                                prompt: spawnPrompt.isEmpty ? nil : spawnPrompt
                            )
                            showSpawn = false
                            await fetchSessions()
                        }
                    } label: {
                        Text("SPAWN")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.green)
                    }
                }
            }
        }
    }

    // MARK: - Helpers

    private func badge(_ label: String, _ value: String, _ color: Color) -> some View {
        HStack(spacing: 4) {
            Text(label).font(.system(size: 9, weight: .bold, design: .monospaced)).foregroundStyle(.secondary)
            Text(value).font(.system(size: 11, weight: .bold, design: .monospaced)).foregroundStyle(color)
        }
    }

    private func fetchSessions() async {
        loading = true
        defer { loading = false }
        sessions = (try? await api.supervisorSessions()) ?? []
    }

    private func fetchOutput(_ sessionId: String) async {
        sessionOutput = (try? await api.supervisorOutput(sessionId: sessionId)) ?? ""
    }

    private func sendInput(_ sess: SupervisorSession) {
        guard !inputText.isEmpty else { return }
        let text = inputText
        inputText = ""
        Task {
            _ = try? await api.supervisorInput(sessionId: sess.id, text: text)
            await fetchOutput(sess.id)
        }
    }
}
