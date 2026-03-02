import SwiftUI

public struct SettingsView: View {
    @AppStorage("atlasBaseURL") private var atlasBaseURL = AppConfig.defaultAtlasBaseURL
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @AppStorage("hasEnteredIntent") private var hasEnteredIntent = false
    @AppStorage("intentRevealLevel") private var intentRevealLevel = 1
    @AppStorage("intentRole") private var intentRole = "biochemist"
    @AppStorage("firstIntentText") private var firstIntentText = ""
    @AppStorage("table_rex") private var tableRex = true
    @AppStorage("table_orion") private var tableOrion = true
    @AppStorage("table_gpt") private var tableGpt = false
    @AppStorage("table_hyperion") private var tableHyperion = true
    @AppStorage("table_gemini") private var tableGemini = false
    @AppStorage("table_shared") private var tableShared = false
    @AppStorage("family_visibility_only") private var familyVisibilityOnly = false
    @AppStorage("family_send_mode") private var familySendMode = true
    @AppStorage("pane_ops") private var paneOps = true
    @AppStorage("pane_tribunal") private var paneTribunal = true
    @AppStorage("pane_secrets") private var paneSecrets = true
    @AppStorage("pane_bio") private var paneBio = true
    @AppStorage("pane_radio") private var paneRadio = false
    @AppStorage("pane_tasks") private var paneTasks = true
    @AppStorage("pane_governor") private var paneGovernor = true
    @AppStorage("pane_tools") private var paneTools = true
    @AppStorage("pane_dpi") private var paneDpi = false
    @AppStorage("pane_aletheia") private var paneAletheia = true
    @AppStorage("pane_history") private var paneHistory = false
    @AppStorage("pane_processes") private var paneProcesses = false
    @AppStorage("pane_models") private var paneModels = true
    @AppStorage("pane_ruliad") private var paneRuliad = false
    @AppStorage("pane_nodes") private var paneNodes = false
    @AppStorage("pane_settings") private var paneSettings = true
    @State private var draftAtlas = ""
    @State private var draftAPI = ""
    @State private var connectionStatus: ConnectionStatus = .unknown

    enum ConnectionStatus {
        case unknown, checking, ok, failed(String)
    }

    public init() {}

    public var body: some View {
        NavigationStack {
            Form {
                Section("Account") {
                    AccountBadge()
                    NavigationLink("Billing & Usage") {
                        BillingView()
                    }
                }

                Section("Atlas Web URL") {
                    TextField("http://localhost:3000", text: $draftAtlas)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        #endif
                        .autocorrectionDisabled()
                    Text("Used by Atlas tab (WKWebView).")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Server") {
                    // One-tap cloud/localhost toggle
                    HStack(spacing: 12) {
                        Button {
                            draftAPI = "http://localhost:8400"
                            apiBaseURL = "http://localhost:8400"
                            Task { await testConnection() }
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "desktopcomputer")
                                    .font(.system(size: 11))
                                Text("Local")
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(apiBaseURL.contains("localhost") ? RheaTheme.green.opacity(0.2) : .clear)
                                    .overlay(RoundedRectangle(cornerRadius: 8)
                                        .stroke(apiBaseURL.contains("localhost") ? RheaTheme.green : .secondary.opacity(0.3), lineWidth: 1))
                            )
                            .foregroundStyle(apiBaseURL.contains("localhost") ? RheaTheme.green : .secondary)
                        }
                        .buttonStyle(.plain)

                        Button {
                            draftAPI = AppConfig.productionAPIBaseURL
                            apiBaseURL = AppConfig.productionAPIBaseURL
                            Task { await testConnection() }
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "cloud.fill")
                                    .font(.system(size: 11))
                                Text("Cloud")
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(!apiBaseURL.contains("localhost") ? RheaTheme.accent.opacity(0.2) : .clear)
                                    .overlay(RoundedRectangle(cornerRadius: 8)
                                        .stroke(!apiBaseURL.contains("localhost") ? RheaTheme.accent : .secondary.opacity(0.3), lineWidth: 1))
                            )
                            .foregroundStyle(!apiBaseURL.contains("localhost") ? RheaTheme.accent : .secondary)
                        }
                        .buttonStyle(.plain)
                    }

                    HStack {
                        connectionBadge
                        Spacer()
                        Text(apiBaseURL
                            .replacingOccurrences(of: "https://", with: "")
                            .replacingOccurrences(of: "http://", with: ""))
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }
                }

                Section("API Base URL") {
                    TextField(AppConfig.productionAPIBaseURL, text: $draftAPI)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        #endif
                        .autocorrectionDisabled()

                    Button("Test Connection") {
                        Task { await testConnection() }
                    }
                    .font(.caption)
                }

                Section {
                    Button("Save") {
                        atlasBaseURL = normalize(draftAtlas, fallback: AppConfig.defaultAtlasBaseURL)
                        apiBaseURL = normalize(draftAPI, fallback: AppConfig.defaultAPIBaseURL)
                    }
                    .buttonStyle(.borderedProminent)

                    Button("Reset Defaults") {
                        atlasBaseURL = AppConfig.defaultAtlasBaseURL
                        apiBaseURL = AppConfig.defaultAPIBaseURL
                        draftAtlas = AppConfig.defaultAtlasBaseURL
                        draftAPI = AppConfig.defaultAPIBaseURL
                    }
                }

                Section("Current Effective Values") {
                    LabeledContent("Atlas", value: atlasBaseURL)
                    LabeledContent("API", value: apiBaseURL)
                }

                Section("Intent-First UX") {
                    Picker("Reveal Level", selection: $intentRevealLevel) {
                        Text("L1 · Ask + Dialog").tag(1)
                        Text("L2 · +Governor +Tasks").tag(2)
                        Text("L3 · Full cockpit").tag(3)
                    }
                    .pickerStyle(.segmented)

                    LabeledContent("Role", value: intentRole)
                    if !firstIntentText.isEmpty {
                        Text(firstIntentText)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }

                    Button("Reset Intent Gate") {
                        hasEnteredIntent = false
                        intentRevealLevel = 1
                        intentRole = "biochemist"
                        firstIntentText = ""
                    }
                    .buttonStyle(.bordered)
                }

                Section("Family Table Composition") {
                    Toggle("REX seat", isOn: $tableRex)
                    Toggle("ORION seat", isOn: $tableOrion)
                    Toggle("GPT seat", isOn: $tableGpt)
                    Toggle("HYPERION seat", isOn: $tableHyperion)
                    Toggle("GEMINI seat", isOn: $tableGemini)
                    Toggle("SHARED seat", isOn: $tableShared)
                }

                Section("Visible Tabs") {
                    paneAlwaysOn("square.grid.2x2", "ops")
                    paneToggle("text.bubble", "tribunal", $paneTribunal)
                    paneToggle("lock.shield", "secrets", $paneSecrets)
                    paneToggle("atom", "bio", $paneBio)
                    paneToggle("waveform", "radio", $paneRadio)
                    paneToggle("checklist", "tasks", $paneTasks)
                    paneToggle("gauge.with.dots.needle.33percent", "governor", $paneGovernor)
                    paneToggle("keyboard", "tools", $paneTools)
                    paneToggle("checkmark.seal", "aletheia", $paneAletheia)
                    paneToggle("cpu", "models", $paneModels)
                    paneToggle("clock.arrow.circlepath", "history", $paneHistory)
                    paneToggle("terminal", "processes", $paneProcesses)
                    paneToggle("function", "ruliad", $paneRuliad)
                    paneToggle("eye.trianglebadge.exclamationmark", "dpi", $paneDpi)
                    paneToggle("point.3.connected.trianglepath.dotted", "nodes", $paneNodes)
                    paneAlwaysOn("slider.horizontal.3", "settings")
                }

                Section("Family Visibility Scope") {
                    Toggle("Show only active table scope", isOn: $familyVisibilityOnly)
                    Toggle("Send composer to table seats (not broadcast)", isOn: $familySendMode)
                    Text("When enabled, Radio composer duplicates one message to all active table seats.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .scrollContentBackground(.hidden)
            .background(RheaTheme.bg)
            .navigationTitle("Settings")
            .onAppear {
                draftAtlas = atlasBaseURL
                draftAPI = apiBaseURL
            }
            .task {
                await testConnection()
            }
        }
    }

    @ViewBuilder
    private var connectionBadge: some View {
        switch connectionStatus {
        case .unknown:
            EmptyView()
        case .checking:
            ProgressView()
                .controlSize(.mini)
        case .ok:
            Label("Connected", systemImage: "checkmark.circle.fill")
                .font(.caption2)
                .foregroundStyle(.green)
        case .failed(let reason):
            Label(reason, systemImage: "xmark.circle.fill")
                .font(.caption2)
                .foregroundStyle(.red)
        }
    }

    private func testConnection() async {
        connectionStatus = .checking
        let base = apiBaseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: "\(base)/health") else {
            connectionStatus = .failed("Invalid URL")
            return
        }
        var req = URLRequest(url: url)
        req.timeoutInterval = 10
        do {
            let (_, response) = try await URLSession.shared.data(for: req)
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                connectionStatus = .ok
            } else {
                let code = (response as? HTTPURLResponse)?.statusCode ?? 0
                connectionStatus = .failed("HTTP \(code)")
            }
        } catch {
            connectionStatus = .failed(error.localizedDescription)
        }
    }

    private func normalize(_ raw: String, fallback: String) -> String {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return fallback }
        return trimmed.hasSuffix("/") ? String(trimmed.dropLast()) : trimmed
    }

    private func paneToggle(_ icon: String, _ name: String, _ binding: Binding<Bool>) -> some View {
        Toggle(isOn: binding) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12, design: .monospaced))
                Text(name)
                    .font(.system(size: 12, design: .monospaced))
            }
        }
    }

    private func paneAlwaysOn(_ icon: String, _ name: String) -> some View {
        HStack {
            Image(systemName: icon)
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.secondary)
            Text(name)
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.secondary)
            Spacer()
            Text("(always visible)")
                .font(.system(size: 10, design: .monospaced))
                .foregroundStyle(.tertiary)
        }
    }
}
