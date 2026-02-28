import SwiftUI

struct SettingsView: View {
    @AppStorage("atlasBaseURL") private var atlasBaseURL = AppConfig.defaultAtlasBaseURL
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var draftAtlas = ""
    @State private var draftAPI = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Atlas Web URL") {
                    TextField("http://localhost:3000", text: $draftAtlas)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                    Text("Used by Atlas tab (WKWebView).")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("API Base URL") {
                    TextField("http://localhost:8400", text: $draftAPI)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                    Text("Used by Governor/Tasks tabs.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
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
            }
            .scrollContentBackground(.hidden)
            .background(RheaTheme.bg)
            .navigationTitle("Settings")
            .onAppear {
                draftAtlas = atlasBaseURL
                draftAPI = apiBaseURL
            }
        }
    }

    private func normalize(_ raw: String, fallback: String) -> String {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return fallback }
        return trimmed.hasSuffix("/") ? String(trimmed.dropLast()) : trimmed
    }
}

