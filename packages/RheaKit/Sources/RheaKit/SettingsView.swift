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

                Section("API Base URL") {
                    TextField(AppConfig.productionAPIBaseURL, text: $draftAPI)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        #endif
                        .autocorrectionDisabled()

                    HStack {
                        Text("Used by Governor/Tasks/Radio tabs.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Spacer()
                        connectionBadge
                    }

                    Button("Use Cloud Run (production)") {
                        draftAPI = AppConfig.productionAPIBaseURL
                        apiBaseURL = AppConfig.productionAPIBaseURL
                        Task { await testConnection() }
                    }
                    .font(.caption)

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
}
