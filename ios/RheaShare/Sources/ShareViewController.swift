import UIKit
import SwiftUI
import Security
import UniformTypeIdentifiers

/// Rhea Share Extension — "Rhea Selector"
/// Share text/URLs from any app → pick models → run tribunal → see consensus.
/// Zero external dependencies. Talks directly to the tribunal API.
@objc(ShareViewController)
class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        let hostingView = UIHostingController(rootView: RheaSelectorView(extensionContext: extensionContext))
        addChild(hostingView)
        view.addSubview(hostingView.view)
        hostingView.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            hostingView.view.topAnchor.constraint(equalTo: view.topAnchor),
            hostingView.view.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            hostingView.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            hostingView.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
        ])
        hostingView.didMove(toParent: self)
    }
}

// MARK: - Rhea Selector UI

struct RheaSelectorView: View {
    let extensionContext: NSExtensionContext?
    @State private var sharedText = ""
    @State private var selectedTier: Tier = .cheap
    @State private var selectedModels: Set<String> = ["gemini"]
    @State private var isVerifying = false
    @State private var result: TribunalResult? = nil
    @State private var errorText: String? = nil
    private let apiBaseURL = "https://rhea-tribunal.fly.dev"

    enum Tier: String, CaseIterable {
        case cheap = "Quick"
        case balanced = "Balanced"
        case deep = "Deep"

        var apiValue: String {
            switch self {
            case .cheap: return "cheap"
            case .balanced: return "balanced"
            case .deep: return "frontier"
            }
        }
        var color: Color {
            switch self {
            case .cheap: return .green
            case .balanced: return .orange
            case .deep: return .purple
            }
        }
        var k: Int {
            switch self {
            case .cheap: return 3
            case .balanced: return 5
            case .deep: return 7
            }
        }
    }

    private let availableModels: [(id: String, label: String, color: Color)] = [
        ("gemini", "Gemini", .blue),
        ("claude", "Claude", .orange),
        ("gpt", "GPT", .green),
        ("deepseek", "DeepSeek", .cyan),
        ("qwen", "Qwen", .purple),
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    // Shared content preview
                    contentPreview

                    // Tier selector
                    tierSelector

                    // Model chips
                    modelSelector

                    // Verify button
                    verifyButton

                    // Result
                    if let result = result {
                        resultView(result)
                    }
                    if let err = errorText {
                        Text(err)
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(.red)
                            .padding(10)
                    }
                }
                .padding(16)
            }
            .background(Color(uiColor: .systemBackground))
            .navigationTitle("Rhea Selector")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        extensionContext?.completeRequest(returningItems: nil)
                    }
                }
            }
        }
        .task { await extractSharedContent() }
    }

    // MARK: - Content Preview

    private var contentPreview: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Image(systemName: "doc.text")
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
                Text("SHARED CONTENT")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            if sharedText.isEmpty {
                ProgressView()
                    .frame(maxWidth: .infinity, minHeight: 40)
            } else {
                Text(sharedText)
                    .font(.system(size: 13))
                    .lineLimit(6)
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(
                        RoundedRectangle(cornerRadius: 10)
                            .fill(Color(uiColor: .secondarySystemBackground))
                    )
            }
        }
    }

    // MARK: - Tier Selector

    private var tierSelector: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("VERIFICATION DEPTH")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)

            HStack(spacing: 8) {
                ForEach(Tier.allCases, id: \.rawValue) { tier in
                    Button {
                        withAnimation(.easeInOut(duration: 0.2)) { selectedTier = tier }
                    } label: {
                        VStack(spacing: 3) {
                            Text(tier.rawValue)
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                            Text("\(tier.k) models")
                                .font(.system(size: 9, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(
                            RoundedRectangle(cornerRadius: 10)
                                .fill(selectedTier == tier ? tier.color.opacity(0.15) : Color.clear)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 10)
                                        .stroke(selectedTier == tier ? tier.color.opacity(0.5) : Color.secondary.opacity(0.2), lineWidth: 1)
                                )
                        )
                        .foregroundStyle(selectedTier == tier ? tier.color : .secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - Model Selector

    private var modelSelector: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("MODELS")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    ForEach(availableModels, id: \.id) { model in
                        let isOn = selectedModels.contains(model.id)
                        Button {
                            if isOn { selectedModels.remove(model.id) }
                            else { selectedModels.insert(model.id) }
                        } label: {
                            Text(model.label)
                                .font(.system(size: 11, weight: isOn ? .bold : .medium, design: .monospaced))
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(
                                    Capsule()
                                        .fill(isOn ? model.color.opacity(0.15) : Color.clear)
                                        .overlay(
                                            Capsule()
                                                .stroke(isOn ? model.color.opacity(0.5) : Color.secondary.opacity(0.2), lineWidth: 1)
                                        )
                                )
                                .foregroundStyle(isOn ? model.color : .secondary)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }

    // MARK: - Verify Button

    private var verifyButton: some View {
        Button {
            Task { await verify() }
        } label: {
            HStack(spacing: 8) {
                if isVerifying {
                    ProgressView().tint(.white)
                } else {
                    Image(systemName: "checkmark.shield.fill")
                }
                Text(isVerifying ? "Verifying..." : "Verify with Tribunal")
                    .font(.system(size: 14, weight: .bold, design: .monospaced))
            }
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(sharedText.isEmpty || isVerifying
                          ? Color.gray.opacity(0.3)
                          : selectedTier.color.opacity(0.8))
            )
        }
        .buttonStyle(.plain)
        .disabled(sharedText.isEmpty || isVerifying)
    }

    // MARK: - Result View

    private func resultView(_ r: TribunalResult) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("CONSENSUS")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                Spacer()
                let scoreColor: Color = r.agreement >= 0.7 ? .green : r.agreement >= 0.4 ? .orange : .red
                Text(String(format: "%.0f%%", r.agreement * 100))
                    .font(.system(size: 22, weight: .bold, design: .rounded))
                    .foregroundStyle(scoreColor)
            }

            ProgressView(value: r.agreement)
                .tint(r.agreement >= 0.7 ? .green : r.agreement >= 0.4 ? .orange : .red)

            Text(r.consensus)
                .font(.system(size: 12))
                .lineLimit(8)

            HStack(spacing: 12) {
                if r.models > 0 {
                    Label("\(r.models) models", systemImage: "cpu")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
                if r.elapsed > 0 {
                    Label(String(format: "%.1fs", r.elapsed), systemImage: "clock")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
            }

            // Copy + Done buttons
            HStack(spacing: 10) {
                Button {
                    UIPasteboard.general.string = "[\(String(format: "%.0f%%", r.agreement * 100))] \(r.consensus)"
                } label: {
                    Label("Copy", systemImage: "doc.on.doc")
                        .font(.system(size: 12, weight: .medium))
                }
                .buttonStyle(.bordered)

                Spacer()

                Button("Done") {
                    extensionContext?.completeRequest(returningItems: nil)
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(uiColor: .secondarySystemBackground))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(r.agreement >= 0.7 ? Color.green.opacity(0.3) : Color.orange.opacity(0.3), lineWidth: 1)
                )
        )
    }

    // MARK: - Networking

    private func extractSharedContent() async {
        guard let items = extensionContext?.inputItems as? [NSExtensionItem] else { return }
        for item in items {
            guard let attachments = item.attachments else { continue }
            for provider in attachments {
                // Text
                if provider.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
                    if let text = try? await provider.loadItem(forTypeIdentifier: UTType.plainText.identifier) as? String {
                        await MainActor.run { sharedText = text }
                        return
                    }
                }
                // URL
                if provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                    if let url = try? await provider.loadItem(forTypeIdentifier: UTType.url.identifier) as? URL {
                        await MainActor.run { sharedText = url.absoluteString }
                        return
                    }
                }
            }
        }
        await MainActor.run { sharedText = "(no text content shared)" }
    }

    private func verify() async {
        let text = sharedText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        isVerifying = true
        errorText = nil
        result = nil

        let payload: [String: Any] = [
            "prompt": text,
            "k": selectedTier.k,
            "tier": selectedTier.apiValue,
        ]

        guard let url = URL(string: "\(apiBaseURL)/tribunal"),
              let body = try? JSONSerialization.data(withJSONObject: payload) else {
            isVerifying = false
            errorText = "Invalid API URL"
            return
        }

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.timeoutInterval = 120

        // Try JWT from shared Keychain
        if let jwt = readJWT() {
            req.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        }
        req.httpBody = body

        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                let agreement = json["agreement_score"] as? Double ?? 0
                let consensus = json["consensus"] as? String
                    ?? json["consensus_text"] as? String
                    ?? json["reply"] as? String ?? "No consensus text"
                let models = json["models_responded"] as? Int
                    ?? (json["models_used"] as? [String])?.count ?? 0
                let elapsed = json["elapsed_s"] as? Double ?? 0
                await MainActor.run {
                    isVerifying = false
                    result = TribunalResult(agreement: agreement, consensus: consensus, models: models, elapsed: elapsed)
                }
            } else {
                await MainActor.run {
                    isVerifying = false
                    errorText = "Failed to parse response"
                }
            }
        } catch {
            await MainActor.run {
                isVerifying = false
                errorText = "Network: \(error.localizedDescription)"
            }
        }
    }

    private func readJWT() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: "com.rhea.auth",
            kSecAttrAccount as String: "jwt",
            kSecReturnData as String: true,
            kSecAttrAccessGroup as String: "398XACWZ7G.com.rhea.preview",
        ]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
}

// MARK: - Result Model

struct TribunalResult {
    let agreement: Double
    let consensus: String
    let models: Int
    let elapsed: Double
}
