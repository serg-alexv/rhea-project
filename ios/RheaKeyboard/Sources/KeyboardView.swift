import SwiftUI

/// Rhea keyboard — system-wide AI text tool.
///
/// Two modes:
///   1. Quick Actions — single-model fast (translate, rewrite, grammar, summarize)
///   2. Tribunal — multi-model consensus for complex claims
///
/// Quick actions grab text from the host app's text field via `getContext()`,
/// process it through a single LLM, and let the user insert the result.
struct KeyboardView: View {

    // Callbacks from UIInputViewController
    let insertText: (String) -> Void
    let deleteBackward: () -> Void
    let switchKeyboard: () -> Void
    let getContext: () -> String

    @State private var query = ""
    @State private var isLoading = false
    @State private var resultText: String?
    @State private var resultMeta: String?
    @State private var errorText: String?
    @State private var copied = false
    @State private var showLangPicker = false
    @State private var selectedLang = "en"
    @State private var mode: KeyboardMode = .actions

    enum KeyboardMode {
        case actions    // quick action strip + result
        case tribunal   // full tribunal query
    }

    // Colors matching RheaTheme (local — no RheaKit import in extensions)
    private let bg = Color(red: 0.06, green: 0.06, blue: 0.10)
    private let card = Color(red: 0.10, green: 0.10, blue: 0.16)
    private let accent = Color(red: 0.40, green: 0.85, blue: 1.0)
    private let green = Color(red: 0.30, green: 0.90, blue: 0.50)
    private let amber = Color(red: 1.0, green: 0.78, blue: 0.20)
    private let red = Color(red: 1.0, green: 0.35, blue: 0.35)

    var body: some View {
        VStack(spacing: 0) {
            header
            if showLangPicker {
                languagePicker
            } else if mode == .actions {
                quickActions
            } else {
                tribunalInput
            }
            if isLoading || resultText != nil || errorText != nil {
                responseArea
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: resultText != nil ? 280 : (showLangPicker ? 240 : 170))
        .background(bg)
    }

    // MARK: - Header

    private var header: some View {
        HStack(spacing: 8) {
            Image(systemName: "scalemass.fill")
                .font(.system(size: 11))
                .foregroundStyle(accent)
            Text("RHEA")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(.white)

            Spacer()

            // Mode toggle
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    mode = mode == .actions ? .tribunal : .actions
                    showLangPicker = false
                    resultText = nil
                    errorText = nil
                }
            } label: {
                Text(mode == .actions ? "⚖ Tribunal" : "⚡ Quick")
                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Capsule().fill(card))
                    .foregroundStyle(accent)
            }

            // Auth dot
            Circle()
                .fill(TribunalClient.authToken != nil ? green : amber)
                .frame(width: 6, height: 6)

            // Globe (switch keyboard — required by Apple)
            Button(action: switchKeyboard) {
                Image(systemName: "globe")
                    .font(.system(size: 15))
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 5)
    }

    // MARK: - Quick Actions

    private var quickActions: some View {
        VStack(spacing: 6) {
            // Row 1: Primary actions
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    actionPill("Translate", icon: "globe", color: accent) {
                        withAnimation { showLangPicker = true }
                    }
                    actionPill("Grammar", icon: "textformat.abc", color: green) {
                        runQuickAction("grammar")
                    }
                    actionPill("Rewrite", icon: "arrow.triangle.2.circlepath", color: amber) {
                        runQuickAction("rewrite", style: "clearer")
                    }
                    actionPill("Summarize", icon: "text.justify.leading", color: .purple) {
                        runQuickAction("summarize")
                    }
                    actionPill("Explain", icon: "lightbulb", color: .orange) {
                        runQuickAction("explain")
                    }
                }
                .padding(.horizontal, 12)
            }

            // Row 2: Rewrite styles
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    stylePill("Formal") { runQuickAction("rewrite", style: "formal") }
                    stylePill("Casual") { runQuickAction("rewrite", style: "casual") }
                    stylePill("Shorter") { runQuickAction("rewrite", style: "shorter") }
                    stylePill("Longer") { runQuickAction("rewrite", style: "longer") }
                    stylePill("Friendly") { runQuickAction("rewrite", style: "friendly") }
                    stylePill("Professional") { runQuickAction("rewrite", style: "professional") }
                }
                .padding(.horizontal, 12)
            }

            // Freeform input
            HStack(spacing: 6) {
                TextField("Ask anything...", text: $query)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 6)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(card)
                    )
                    .submitLabel(.send)
                    .onSubmit { runQuickAction("freeform") }

                Button { runQuickAction("freeform") } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 22))
                        .foregroundStyle(query.isEmpty ? .secondary : accent)
                }
                .disabled(query.isEmpty || isLoading)
            }
            .padding(.horizontal, 12)
        }
        .padding(.vertical, 4)
    }

    private func actionPill(_ label: String, icon: String, color: Color, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 10))
                Text(label)
                    .font(.system(size: 11, weight: .semibold, design: .monospaced))
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(
                Capsule().fill(color.opacity(0.15))
                    .overlay(Capsule().stroke(color.opacity(0.4), lineWidth: 0.5))
            )
            .foregroundStyle(color)
        }
        .disabled(isLoading)
    }

    private func stylePill(_ label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: 10, weight: .medium, design: .monospaced))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(
                    Capsule().fill(card)
                        .overlay(Capsule().stroke(Color.white.opacity(0.06), lineWidth: 0.5))
                )
                .foregroundStyle(.secondary)
        }
        .disabled(isLoading)
    }

    // MARK: - Language Picker

    private let languages: [(code: String, flag: String, name: String)] = [
        ("en", "🇬🇧", "English"),
        ("ja", "🇯🇵", "Japanese"),
        ("es", "🇪🇸", "Spanish"),
        ("fr", "🇫🇷", "French"),
        ("de", "🇩🇪", "German"),
        ("ru", "🇷🇺", "Russian"),
        ("zh", "🇨🇳", "Chinese"),
        ("ko", "🇰🇷", "Korean"),
        ("ar", "🇸🇦", "Arabic"),
        ("pt", "🇧🇷", "Portuguese"),
        ("it", "🇮🇹", "Italian"),
        ("uk", "🇺🇦", "Ukrainian"),
        ("hi", "🇮🇳", "Hindi"),
        ("tr", "🇹🇷", "Turkish"),
        ("nl", "🇳🇱", "Dutch"),
        ("th", "🇹🇭", "Thai"),
        ("vi", "🇻🇳", "Vietnamese"),
        ("pl", "🇵🇱", "Polish"),
        ("sv", "🇸🇪", "Swedish"),
        ("he", "🇮🇱", "Hebrew"),
    ]

    private var languagePicker: some View {
        VStack(spacing: 6) {
            HStack {
                Text("TRANSLATE TO")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(accent)
                Spacer()
                Button("Cancel") {
                    withAnimation { showLangPicker = false }
                }
                .font(.system(size: 11, design: .monospaced))
                .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 14)

            // Language grid (5 columns)
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: 5), spacing: 4) {
                ForEach(languages, id: \.code) { lang in
                    Button {
                        selectedLang = lang.code
                        withAnimation { showLangPicker = false }
                        runQuickAction("translate", targetLang: lang.code)
                    } label: {
                        VStack(spacing: 2) {
                            Text(lang.flag)
                                .font(.system(size: 20))
                            Text(lang.code.uppercased())
                                .font(.system(size: 8, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.7))
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
                        .background(
                            RoundedRectangle(cornerRadius: 8)
                                .fill(selectedLang == lang.code ? accent.opacity(0.2) : card)
                        )
                    }
                }
            }
            .padding(.horizontal, 12)
        }
        .padding(.vertical, 6)
    }

    // MARK: - Tribunal Mode

    private var tribunalInput: some View {
        VStack(spacing: 6) {
            Text("MULTI-MODEL CONSENSUS")
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(accent.opacity(0.6))

            HStack(spacing: 6) {
                TextField("Enter claim for tribunal...", text: $query)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 6)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(card)
                    )
                    .submitLabel(.send)
                    .onSubmit { runTribunal() }

                Button(action: runTribunal) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 22))
                        .foregroundStyle(query.isEmpty ? .secondary : accent)
                }
                .disabled(query.isEmpty || isLoading)
            }
            .padding(.horizontal, 12)
        }
        .padding(.vertical, 8)
    }

    // MARK: - Response

    private var responseArea: some View {
        VStack(alignment: .leading, spacing: 4) {
            if isLoading {
                HStack(spacing: 6) {
                    ProgressView()
                        .scaleEffect(0.7)
                        .tint(accent)
                    Text("Processing...")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, 8)
            } else if let error = errorText {
                Text(error)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(red)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 4)
            } else if let text = resultText {
                ScrollView {
                    Text(text)
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.9))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 14)
                }
                .frame(maxHeight: 90)

                // Meta + actions
                HStack(spacing: 8) {
                    if let meta = resultMeta {
                        Text(meta)
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    Button {
                        insertText(text)
                    } label: {
                        HStack(spacing: 3) {
                            Image(systemName: "arrow.up.doc")
                                .font(.system(size: 9))
                            Text("Insert")
                                .font(.system(size: 10, weight: .semibold, design: .monospaced))
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Capsule().fill(accent.opacity(0.2)))
                        .foregroundStyle(accent)
                    }

                    Button {
                        UIPasteboard.general.string = text
                        copied = true
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { copied = false }
                    } label: {
                        Image(systemName: copied ? "checkmark" : "doc.on.doc")
                            .font(.system(size: 11))
                            .foregroundStyle(copied ? green : .secondary)
                    }
                }
                .padding(.horizontal, 14)
                .padding(.bottom, 6)
            }
        }
    }

    // MARK: - Actions

    private func runQuickAction(_ action: String, targetLang: String = "", style: String = "") {
        // For freeform, use the typed query; for others, grab from host app's text field
        let text: String
        if action == "freeform" {
            text = query.trimmingCharacters(in: .whitespacesAndNewlines)
        } else {
            let context = getContext()
            text = context.trimmingCharacters(in: .whitespacesAndNewlines)
        }

        guard !text.isEmpty else {
            errorText = action == "freeform" ? "Type a question" : "No text before cursor"
            return
        }

        isLoading = true
        resultText = nil
        resultMeta = nil
        errorText = nil

        Task {
            do {
                let resp = try await TribunalClient.quick(
                    text: text,
                    action: action,
                    targetLang: targetLang,
                    style: style
                )
                await MainActor.run {
                    resultText = resp.text
                    if let elapsed = resp.elapsed_s, let model = resp.model {
                        resultMeta = "\(model) · \(String(format: "%.1fs", elapsed))"
                    }
                    isLoading = false
                    if action == "freeform" { query = "" }
                }
            } catch {
                await MainActor.run {
                    errorText = "Failed: \(error.localizedDescription)"
                    isLoading = false
                }
            }
        }
    }

    private func runTribunal() {
        let claim = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !claim.isEmpty else { return }

        isLoading = true
        resultText = nil
        resultMeta = nil
        errorText = nil

        Task {
            do {
                let resp = try await TribunalClient.tribunal(claim)
                await MainActor.run {
                    resultText = resp.reply
                    var meta = ""
                    if let score = resp.agreement_score {
                        meta += "\(Int(score * 100))% agreement"
                    }
                    if let models = resp.models_responded {
                        meta += " · \(models) models"
                    }
                    if let elapsed = resp.elapsed_s {
                        meta += " · \(String(format: "%.1fs", elapsed))"
                    }
                    resultMeta = meta
                    isLoading = false
                    query = ""
                }
            } catch {
                await MainActor.run {
                    errorText = "Failed: \(error.localizedDescription)"
                    isLoading = false
                }
            }
        }
    }
}
