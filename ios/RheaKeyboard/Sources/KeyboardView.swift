import SwiftUI

/// Rhea keyboard — system-wide AI text tool with full QWERTY input.
///
/// Four modes via visible tab bar:
///   1. ABC — full QWERTY letter keyboard (default)
///   2. Quick — single-model fast actions (translate, rewrite, grammar)
///   3. Tribunal — multi-model consensus for claims
///   4. Builder — LEGO-like block chain constructor (ComfyUI-style)
struct KeyboardView: View {

    let insertText: (String) -> Void
    let deleteBackward: () -> Void
    let switchKeyboard: () -> Void
    let getContext: () -> String

    // Shared state
    @State private var query = ""
    @State private var isLoading = false
    @State private var resultText: String?
    @State private var resultMeta: String?
    @State private var errorText: String?
    @State private var copied = false
    @State private var showLangPicker = false
    @State private var selectedLang = "en"
    @State private var mode: KeyboardMode = .typing

    // Typing state
    @State private var shifted = false
    @State private var capsLock = false
    @State private var numbersMode = false
    @State private var symbolsMode = false

    // Builder state
    @State private var chain: [ChainBlock] = [
        ChainBlock(type: .input, label: "Input", config: [:]),
        ChainBlock(type: .model, label: "Claude", config: ["model": "cheap"]),
        ChainBlock(type: .output, label: "Paste", config: [:]),
    ]
    @State private var showBlockPalette = false
    @State private var editingBlockIndex: Int? = nil
    @State private var chainRunning = false
    @State private var chainProgress: String? = nil

    enum KeyboardMode: String, CaseIterable {
        case typing   = "ABC"
        case actions  = "Quick"
        case tribunal = "Tribunal"
        case builder  = "Builder"
        case logic    = "Logic"

        var icon: String {
            switch self {
            case .typing:   return "keyboard"
            case .actions:  return "bolt.fill"
            case .tribunal: return "scalemass.fill"
            case .builder:  return "puzzlepiece.fill"
            case .logic:    return "function"
            }
        }
    }

    // Logic mode state
    @State private var logicPalette: LogicPalette = .operators
    enum LogicPalette: String, CaseIterable {
        case operators = "∧∨¬"
        case greek     = "αβγ"
        case sets      = "∈∪∩"
        case math      = "∑∫∂"
        case sub       = "x₁₂"
    }

    // Colors (local — no RheaKit import in extensions)
    private let bg = Color(red: 0.06, green: 0.06, blue: 0.10)
    private let card = Color(red: 0.10, green: 0.10, blue: 0.16)
    private let keyBg = Color(red: 0.18, green: 0.18, blue: 0.24)
    private let accent = Color(red: 0.40, green: 0.85, blue: 1.0)
    private let green = Color(red: 0.30, green: 0.90, blue: 0.50)
    private let amber = Color(red: 1.0, green: 0.78, blue: 0.20)
    private let red = Color(red: 1.0, green: 0.35, blue: 0.35)
    private let keySpacing: CGFloat = 5

    // QWERTY layout
    private let row1 = ["q","w","e","r","t","y","u","i","o","p"]
    private let row2 = ["a","s","d","f","g","h","j","k","l"]
    private let row3 = ["z","x","c","v","b","n","m"]
    private let numRow1 = ["1","2","3","4","5","6","7","8","9","0"]
    private let numRow2 = ["-","/",":",";","(",")","$","&","@","\""]
    private let numRow3 = [".",",","?","!","'"]
    private let symRow1 = ["[","]","{","}","#","%","^","*","+","="]
    private let symRow2 = ["_","\\","|","~","<",">","€","£","¥","·"]
    private let symRow3 = [".",",","?","!","'"]

    var body: some View {
        VStack(spacing: 0) {
            tabBar
            Divider().background(Color.white.opacity(0.06))

            if showLangPicker {
                languagePicker
            } else if isLoading || resultText != nil || errorText != nil {
                responseArea
            } else {
                switch mode {
                case .typing:   qwertyView
                case .actions:  quickActions
                case .tribunal: tribunalInput
                case .builder:  builderView
                case .logic:    logicView
                }
            }
        }
        .frame(maxWidth: .infinity)
        .background(bg)
    }

    // MARK: - Tab Bar

    private var tabBar: some View {
        HStack(spacing: 0) {
            ForEach(KeyboardMode.allCases, id: \.self) { m in
                Button {
                    withAnimation(.easeInOut(duration: 0.15)) {
                        mode = m
                        showLangPicker = false
                        showBlockPalette = false
                        editingBlockIndex = nil
                        if m == .typing {
                            resultText = nil
                            errorText = nil
                        }
                    }
                } label: {
                    HStack(spacing: 3) {
                        Image(systemName: m.icon)
                            .font(.system(size: 9))
                        Text(m.rawValue)
                            .font(.system(size: 10, weight: .semibold, design: .monospaced))
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 5)
                    .frame(maxWidth: .infinity)
                    .background(
                        mode == m
                        ? accent.opacity(0.15)
                        : Color.clear
                    )
                    .foregroundStyle(mode == m ? accent : .secondary)
                }
            }

            // Auth dot
            Circle()
                .fill(TribunalClient.authToken != nil ? green : amber)
                .frame(width: 5, height: 5)
                .padding(.trailing, 6)
        }
        .frame(height: 28)
    }

    // MARK: - QWERTY Keyboard

    private var isUppercase: Bool { shifted || capsLock }

    private var qwertyView: some View {
        VStack(spacing: 6) {
            if numbersMode || symbolsMode {
                numbersSymbolsView
            } else {
                lettersView
            }
        }
        .padding(.horizontal, 3)
        .padding(.vertical, 4)
    }

    private var lettersView: some View {
        VStack(spacing: 6) {
            // Row 1: Q W E R T Y U I O P
            HStack(spacing: 4) {
                ForEach(row1, id: \.self) { key in
                    letterKey(key)
                }
            }

            // Row 2: A S D F G H J K L
            HStack(spacing: 4) {
                ForEach(row2, id: \.self) { key in
                    letterKey(key)
                }
            }

            // Row 3: Shift Z X C V B N M Delete
            HStack(spacing: 4) {
                // Shift
                Button {
                    if shifted {
                        // Double-tap for caps lock
                        capsLock = !capsLock
                        shifted = false
                    } else {
                        shifted = true
                        capsLock = false
                    }
                } label: {
                    Image(systemName: capsLock ? "capslock.fill" : (shifted ? "shift.fill" : "shift"))
                        .font(.system(size: 14))
                        .frame(width: 38, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(
                            (shifted || capsLock) ? accent.opacity(0.25) : keyBg
                        ))
                        .foregroundStyle((shifted || capsLock) ? accent : .white)
                }

                ForEach(row3, id: \.self) { key in
                    letterKey(key)
                }

                // Delete
                Button {
                    deleteBackward()
                } label: {
                    Image(systemName: "delete.left")
                        .font(.system(size: 14))
                        .frame(width: 38, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.white)
                }
                .simultaneousGesture(
                    LongPressGesture(minimumDuration: 0.5).onEnded { _ in
                        // Delete word on long press
                        for _ in 0..<20 { deleteBackward() }
                    }
                )
            }

            // Row 4: 123 Globe Space Return
            HStack(spacing: 4) {
                Button {
                    withAnimation(.easeInOut(duration: 0.1)) { numbersMode = true }
                } label: {
                    Text("123")
                        .font(.system(size: 13, weight: .medium, design: .monospaced))
                        .frame(width: 44, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.white)
                }

                Button(action: switchKeyboard) {
                    Image(systemName: "globe")
                        .font(.system(size: 15))
                        .frame(width: 38, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.secondary)
                }

                // Space bar
                Button {
                    insertText(" ")
                } label: {
                    Text("space")
                        .font(.system(size: 13, design: .monospaced))
                        .frame(maxWidth: .infinity)
                        .frame(height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg.opacity(1.2)))
                        .foregroundStyle(.white.opacity(0.6))
                }

                Button {
                    insertText("\n")
                } label: {
                    Text("return")
                        .font(.system(size: 13, weight: .medium, design: .monospaced))
                        .frame(width: 72, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(accent.opacity(0.2)))
                        .foregroundStyle(accent)
                }
            }
        }
    }

    private var numbersSymbolsView: some View {
        let r1 = symbolsMode ? symRow1 : numRow1
        let r2 = symbolsMode ? symRow2 : numRow2
        let r3 = symbolsMode ? symRow3 : numRow3

        return VStack(spacing: 6) {
            // Row 1
            HStack(spacing: 4) {
                ForEach(r1, id: \.self) { key in
                    charKey(key)
                }
            }

            // Row 2
            HStack(spacing: 4) {
                ForEach(r2, id: \.self) { key in
                    charKey(key)
                }
            }

            // Row 3: #+= / ABC toggle + chars + delete
            HStack(spacing: 4) {
                Button {
                    withAnimation(.easeInOut(duration: 0.1)) {
                        symbolsMode.toggle()
                    }
                } label: {
                    Text(symbolsMode ? "123" : "#+=")
                        .font(.system(size: 12, weight: .medium, design: .monospaced))
                        .frame(width: 38, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.white)
                }

                ForEach(r3, id: \.self) { key in
                    charKey(key)
                }

                Spacer()

                Button { deleteBackward() } label: {
                    Image(systemName: "delete.left")
                        .font(.system(size: 14))
                        .frame(width: 38, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.white)
                }
            }

            // Row 4: ABC Globe Space Return
            HStack(spacing: 4) {
                Button {
                    withAnimation(.easeInOut(duration: 0.1)) {
                        numbersMode = false
                        symbolsMode = false
                    }
                } label: {
                    Text("ABC")
                        .font(.system(size: 13, weight: .medium, design: .monospaced))
                        .frame(width: 44, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.white)
                }

                Button(action: switchKeyboard) {
                    Image(systemName: "globe")
                        .font(.system(size: 15))
                        .frame(width: 38, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.secondary)
                }

                Button { insertText(" ") } label: {
                    Text("space")
                        .font(.system(size: 13, design: .monospaced))
                        .frame(maxWidth: .infinity)
                        .frame(height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg.opacity(1.2)))
                        .foregroundStyle(.white.opacity(0.6))
                }

                Button { insertText("\n") } label: {
                    Text("return")
                        .font(.system(size: 13, weight: .medium, design: .monospaced))
                        .frame(width: 72, height: 38)
                        .background(RoundedRectangle(cornerRadius: 6).fill(accent.opacity(0.2)))
                        .foregroundStyle(accent)
                }
            }
        }
    }

    private func letterKey(_ key: String) -> some View {
        let display = isUppercase ? key.uppercased() : key
        return Button {
            insertText(display)
            if shifted && !capsLock { shifted = false }
        } label: {
            Text(display)
                .font(.system(size: 18, weight: .regular))
                .frame(maxWidth: .infinity)
                .frame(height: 38)
                .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                .foregroundStyle(.white)
        }
    }

    private func charKey(_ key: String) -> some View {
        Button {
            insertText(key)
        } label: {
            Text(key)
                .font(.system(size: 16, weight: .regular))
                .frame(maxWidth: .infinity)
                .frame(height: 38)
                .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                .foregroundStyle(.white)
        }
    }

    // MARK: - Quick Actions

    private var quickActions: some View {
        VStack(spacing: 6) {
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

            HStack(spacing: 6) {
                TextField("Ask anything...", text: $query)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 6)
                    .background(RoundedRectangle(cornerRadius: 8).fill(card))
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
                Image(systemName: icon).font(.system(size: 10))
                Text(label).font(.system(size: 11, weight: .semibold, design: .monospaced))
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
        ("en", "🇬🇧", "English"), ("ja", "🇯🇵", "Japanese"), ("es", "🇪🇸", "Spanish"),
        ("fr", "🇫🇷", "French"), ("de", "🇩🇪", "German"), ("ru", "🇷🇺", "Russian"),
        ("zh", "🇨🇳", "Chinese"), ("ko", "🇰🇷", "Korean"), ("ar", "🇸🇦", "Arabic"),
        ("pt", "🇧🇷", "Portuguese"), ("it", "🇮🇹", "Italian"), ("uk", "🇺🇦", "Ukrainian"),
        ("hi", "🇮🇳", "Hindi"), ("tr", "🇹🇷", "Turkish"), ("nl", "🇳🇱", "Dutch"),
        ("th", "🇹🇭", "Thai"), ("vi", "🇻🇳", "Vietnamese"), ("pl", "🇵🇱", "Polish"),
        ("sv", "🇸🇪", "Swedish"), ("he", "🇮🇱", "Hebrew"),
    ]

    private var languagePicker: some View {
        VStack(spacing: 6) {
            HStack {
                Text("TRANSLATE TO")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(accent)
                Spacer()
                Button("Cancel") { withAnimation { showLangPicker = false } }
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 14)

            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: 5), spacing: 4) {
                ForEach(languages, id: \.code) { lang in
                    Button {
                        selectedLang = lang.code
                        withAnimation { showLangPicker = false }
                        runQuickAction("translate", targetLang: lang.code)
                    } label: {
                        VStack(spacing: 2) {
                            Text(lang.flag).font(.system(size: 20))
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

    // MARK: - Tribunal

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
                    .background(RoundedRectangle(cornerRadius: 8).fill(card))
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
                    ProgressView().scaleEffect(0.7).tint(accent)
                    Text("Processing...")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, 8)
            } else if let error = errorText {
                HStack {
                    Text(error)
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(red)
                    Spacer()
                    Button { errorText = nil } label: {
                        Image(systemName: "xmark.circle").foregroundStyle(.secondary)
                    }
                }
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
                .frame(maxHeight: 120)

                HStack(spacing: 8) {
                    if let meta = resultMeta {
                        Text(meta)
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }
                    Spacer()

                    Button {
                        resultText = nil
                        resultMeta = nil
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 10))
                            .foregroundStyle(.secondary)
                    }

                    Button {
                        insertText(text)
                        resultText = nil
                    } label: {
                        HStack(spacing: 3) {
                            Image(systemName: "arrow.up.doc").font(.system(size: 9))
                            Text("Insert").font(.system(size: 10, weight: .semibold, design: .monospaced))
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

    // MARK: - Network Actions

    private func runQuickAction(_ action: String, targetLang: String = "", style: String = "") {
        let text: String
        if action == "freeform" {
            text = query.trimmingCharacters(in: .whitespacesAndNewlines)
        } else {
            text = getContext().trimmingCharacters(in: .whitespacesAndNewlines)
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
                    text: text, action: action,
                    targetLang: targetLang, style: style
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
        resultText = nil; resultMeta = nil; errorText = nil

        Task {
            do {
                let resp = try await TribunalClient.tribunal(claim)
                await MainActor.run {
                    resultText = resp.reply
                    var meta = ""
                    if let score = resp.agreement_score { meta += "\(Int(score * 100))% agreement" }
                    if let models = resp.models_responded { meta += " · \(models) models" }
                    if let elapsed = resp.elapsed_s { meta += " · \(String(format: "%.1fs", elapsed))" }
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

    // MARK: - Builder Mode

    private var builderView: some View {
        VStack(spacing: 4) {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 0) {
                    ForEach(Array(chain.enumerated()), id: \.element.id) { idx, block in
                        if idx > 0 {
                            Image(systemName: "chevron.right")
                                .font(.system(size: 8, weight: .bold))
                                .foregroundStyle(.white.opacity(0.15))
                                .padding(.horizontal, 2)
                        }

                        Button {
                            withAnimation(.easeInOut(duration: 0.15)) {
                                editingBlockIndex = editingBlockIndex == idx ? nil : idx
                            }
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: block.type.icon).font(.system(size: 10))
                                Text(block.label)
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 7)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(block.type.color.opacity(editingBlockIndex == idx ? 0.35 : 0.18))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(block.type.color.opacity(0.5), lineWidth: editingBlockIndex == idx ? 1.5 : 0.5)
                                    )
                            )
                            .foregroundStyle(block.type.color)
                        }
                        .contextMenu {
                            Button(role: .destructive) {
                                if chain.count > 2 { chain.remove(at: idx) }
                            } label: { Label("Remove", systemImage: "trash") }
                        }
                    }

                    Button {
                        withAnimation { showBlockPalette.toggle() }
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 18))
                            .foregroundStyle(accent.opacity(0.5))
                            .padding(.leading, 6)
                    }
                }
                .padding(.horizontal, 12)
            }

            if showBlockPalette { blockPalette }
            if let idx = editingBlockIndex, idx < chain.count { blockEditor(for: idx) }

            HStack(spacing: 8) {
                if let progress = chainProgress {
                    Text(progress)
                        .font(.system(size: 9, design: .monospaced))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                Spacer()
                Button {
                    Task { await runChain() }
                } label: {
                    HStack(spacing: 4) {
                        if chainRunning {
                            ProgressView().scaleEffect(0.6).tint(green)
                        } else {
                            Image(systemName: "play.fill").font(.system(size: 10))
                        }
                        Text(chainRunning ? "Running..." : "Run Chain")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                    }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 6)
                    .background(
                        Capsule().fill(chainRunning ? card : green.opacity(0.2))
                            .overlay(Capsule().stroke(green.opacity(0.4), lineWidth: 0.5))
                    )
                    .foregroundStyle(green)
                }
                .disabled(chainRunning)
            }
            .padding(.horizontal, 12)
        }
        .padding(.vertical, 4)
    }

    private var blockPalette: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                ForEach(BlockType.allCases, id: \.self) { type in
                    Button {
                        let newBlock = ChainBlock(type: type, label: type.defaultLabel, config: type.defaultConfig)
                        let insertAt = max(chain.count - 1, 1)
                        withAnimation {
                            chain.insert(newBlock, at: insertAt)
                            showBlockPalette = false
                            editingBlockIndex = insertAt
                        }
                    } label: {
                        VStack(spacing: 2) {
                            Image(systemName: type.icon).font(.system(size: 14))
                            Text(type.rawValue)
                                .font(.system(size: 8, weight: .bold, design: .monospaced))
                        }
                        .frame(width: 52, height: 40)
                        .background(RoundedRectangle(cornerRadius: 8).fill(type.color.opacity(0.12)))
                        .foregroundStyle(type.color)
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 4)
        }
        .background(card.opacity(0.5))
    }

    private func blockEditor(for idx: Int) -> some View {
        let block = chain[idx]
        return HStack(spacing: 6) {
            switch block.type {
            case .model:
                ForEach(["cheap", "mid", "frontier"], id: \.self) { tier in
                    Button {
                        chain[idx].config["model"] = tier
                        chain[idx].label = tierLabel(tier)
                    } label: {
                        Text(tier.uppercased())
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 8).padding(.vertical, 4)
                            .background(Capsule().fill(
                                chain[idx].config["model"] == tier ? accent.opacity(0.2) : card
                            ))
                            .foregroundStyle(chain[idx].config["model"] == tier ? accent : .secondary)
                    }
                }
            case .action:
                ForEach(["translate", "rewrite", "summarize", "extract", "grammar"], id: \.self) { act in
                    Button {
                        chain[idx].config["action"] = act
                        chain[idx].label = act.capitalized
                    } label: {
                        Text(act.prefix(5).uppercased())
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 6).padding(.vertical, 4)
                            .background(Capsule().fill(
                                chain[idx].config["action"] == act ? amber.opacity(0.2) : card
                            ))
                            .foregroundStyle(chain[idx].config["action"] == act ? amber : .secondary)
                    }
                }
            case .verify:
                ForEach(["0.7", "0.8", "0.9"], id: \.self) { threshold in
                    Button {
                        chain[idx].config["threshold"] = threshold
                        chain[idx].label = "≥\(Int(Double(threshold)! * 100))%"
                    } label: {
                        Text("≥\(Int(Double(threshold)! * 100))%")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 8).padding(.vertical, 4)
                            .background(Capsule().fill(
                                chain[idx].config["threshold"] == threshold ? green.opacity(0.2) : card
                            ))
                            .foregroundStyle(chain[idx].config["threshold"] == threshold ? green : .secondary)
                    }
                }
            case .loop:
                ForEach(["3", "5", "10"], id: \.self) { max in
                    Button {
                        chain[idx].config["max"] = max
                        chain[idx].label = "×\(max)"
                    } label: {
                        Text("×\(max)")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 8).padding(.vertical, 4)
                            .background(Capsule().fill(
                                chain[idx].config["max"] == max ? Color.purple.opacity(0.2) : card
                            ))
                            .foregroundStyle(chain[idx].config["max"] == max ? .purple : .secondary)
                    }
                }
            default:
                EmptyView()
            }
            Spacer()
        }
        .padding(.horizontal, 12)
    }

    // MARK: - Logic Mode — Greek letters, operators, sets, math symbols

    private let logicSymbols: [LogicPalette: [String]] = [
        .operators: ["∧","∨","¬","→","←","↔","⊕","∀","∃","⊤","⊥","⊢","⊨","⇒","⇐","⇔"],
        .greek:     ["α","β","γ","δ","ε","ζ","η","θ","λ","μ","ν","ξ","π","ρ","σ","φ","χ","ψ","ω","Γ","Δ","Θ","Λ","Σ","Φ","Ψ","Ω"],
        .sets:      ["∈","∉","⊂","⊃","⊆","⊇","∪","∩","∅","ℕ","ℤ","ℚ","ℝ","ℂ","∖","×"],
        .math:      ["∑","∏","∫","∂","∞","√","≈","≠","≤","≥","±","·","÷","°","⁰","¹","²","³","ⁿ"],
        .sub:       ["₀","₁","₂","₃","₄","₅","₆","₇","₈","₉","₊","₋","₌","₍","₎","ₙ"],
    ]

    private var logicView: some View {
        VStack(spacing: 2) {
            // Palette selector
            HStack(spacing: 0) {
                ForEach(LogicPalette.allCases, id: \.self) { pal in
                    Button {
                        withAnimation(.easeInOut(duration: 0.12)) { logicPalette = pal }
                    } label: {
                        Text(pal.rawValue)
                            .font(.system(size: 13, weight: logicPalette == pal ? .bold : .regular))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .foregroundStyle(logicPalette == pal ? accent : .secondary)
                            .background(logicPalette == pal ? accent.opacity(0.12) : .clear)
                            .clipShape(Capsule())
                    }
                }
                Spacer()
                Button { switchKeyboard() } label: {
                    Image(systemName: "globe").font(.system(size: 14))
                        .foregroundStyle(.secondary)
                }
                .padding(.trailing, 8)
            }
            .padding(.horizontal, 8)
            .padding(.top, 4)

            // Symbol grid
            let syms = logicSymbols[logicPalette] ?? []
            let columns = min(syms.count, 9)
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 3), count: columns), spacing: 3) {
                ForEach(Array(syms.enumerated()), id: \.offset) { _, sym in
                    Button {
                        insertText(sym)
                    } label: {
                        Text(sym)
                            .font(.system(size: 20))
                            .frame(maxWidth: .infinity, minHeight: 36)
                            .background(
                                RoundedRectangle(cornerRadius: 6)
                                    .fill(keyBg)
                            )
                            .foregroundStyle(.white)
                    }
                }
            }
            .padding(.horizontal, 6)

            // Bottom row: space, backspace, return
            HStack(spacing: 6) {
                Button { insertText("(") } label: {
                    Text("(").font(.system(size: 16, weight: .bold))
                        .frame(width: 36, height: 34)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.white)
                }
                Button { insertText(")") } label: {
                    Text(")").font(.system(size: 16, weight: .bold))
                        .frame(width: 36, height: 34)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.white)
                }
                Button { insertText(" ") } label: {
                    Text("space")
                        .font(.system(size: 12, weight: .medium, design: .monospaced))
                        .frame(maxWidth: .infinity, minHeight: 34)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg.opacity(0.7)))
                        .foregroundStyle(.secondary)
                }
                Button { deleteBackward() } label: {
                    Image(systemName: "delete.left")
                        .font(.system(size: 16))
                        .frame(width: 44, height: 34)
                        .background(RoundedRectangle(cornerRadius: 6).fill(keyBg))
                        .foregroundStyle(.secondary)
                }
                Button { insertText("\n") } label: {
                    Image(systemName: "return")
                        .font(.system(size: 14))
                        .frame(width: 44, height: 34)
                        .background(RoundedRectangle(cornerRadius: 6).fill(accent.opacity(0.2)))
                        .foregroundStyle(accent)
                }
            }
            .padding(.horizontal, 6)
            .padding(.bottom, 4)
        }
    }

    private func tierLabel(_ tier: String) -> String {
        switch tier {
        case "cheap": return "Gemini"
        case "mid": return "Claude"
        case "frontier": return "Opus"
        default: return tier
        }
    }

    // MARK: - Chain Execution

    private func runChain() async {
        chainRunning = true
        chainProgress = "Starting..."
        defer { chainRunning = false }

        var currentText = ""

        for (idx, block) in chain.enumerated() {
            await MainActor.run {
                chainProgress = "Step \(idx + 1)/\(chain.count): \(block.label)"
            }

            switch block.type {
            case .input:
                let context = getContext()
                currentText = context.isEmpty ? query : context
                if currentText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    await MainActor.run {
                        chainProgress = "No input text"
                        errorText = "No text before cursor"
                    }
                    return
                }

            case .model:
                do {
                    let resp = try await TribunalClient.quick(
                        text: currentText, action: "freeform",
                        targetLang: "", style: ""
                    )
                    currentText = resp.text ?? currentText
                } catch {
                    await MainActor.run {
                        errorText = "Model failed: \(error.localizedDescription)"
                        chainProgress = nil
                    }
                    return
                }

            case .action:
                let action = block.config["action"] ?? "rewrite"
                do {
                    let resp = try await TribunalClient.quick(
                        text: currentText, action: action,
                        targetLang: block.config["lang"] ?? "en",
                        style: block.config["style"] ?? ""
                    )
                    currentText = resp.text ?? currentText
                } catch {
                    await MainActor.run {
                        errorText = "Action failed: \(error.localizedDescription)"
                        chainProgress = nil
                    }
                    return
                }

            case .verify:
                let threshold = Double(block.config["threshold"] ?? "0.8") ?? 0.8
                do {
                    let resp = try await TribunalClient.tribunal(currentText)
                    if let score = resp.agreement_score, score >= threshold {
                        await MainActor.run {
                            chainProgress = "Verified: \(Int(score * 100))% agreement"
                        }
                    } else {
                        let scoreStr = resp.agreement_score.map { "\(Int($0 * 100))%" } ?? "?"
                        await MainActor.run {
                            chainProgress = "Failed: \(scoreStr)"
                            errorText = "Below \(Int(threshold * 100))% threshold (\(scoreStr))"
                        }
                        return
                    }
                } catch {
                    await MainActor.run {
                        errorText = "Tribunal failed: \(error.localizedDescription)"
                        chainProgress = nil
                    }
                    return
                }

            case .loop:
                let maxIter = Int(block.config["max"] ?? "3") ?? 3
                for i in 1...maxIter {
                    await MainActor.run { chainProgress = "Loop \(i)/\(maxIter)" }
                    do {
                        let resp = try await TribunalClient.quick(
                            text: "Improve this text, iteration \(i): \(currentText)",
                            action: "rewrite", targetLang: "", style: "better"
                        )
                        currentText = resp.text ?? currentText
                    } catch { break }
                }

            case .output:
                await MainActor.run {
                    resultText = currentText
                    insertText(currentText)
                    chainProgress = "Done — inserted"
                }
            }
        }
    }
}

// MARK: - Chain Block Model

struct ChainBlock: Identifiable {
    let id = UUID()
    var type: BlockType
    var label: String
    var config: [String: String]
}

enum BlockType: String, CaseIterable {
    case input = "INPUT"
    case model = "MODEL"
    case action = "ACTION"
    case verify = "VERIFY"
    case loop = "LOOP"
    case output = "OUTPUT"

    var icon: String {
        switch self {
        case .input: return "text.cursor"
        case .model: return "brain"
        case .action: return "wand.and.stars"
        case .verify: return "checkmark.seal"
        case .loop: return "repeat"
        case .output: return "arrow.up.doc"
        }
    }

    var color: Color {
        switch self {
        case .input: return Color(red: 0.40, green: 0.85, blue: 1.0)
        case .model: return .purple
        case .action: return Color(red: 1.0, green: 0.78, blue: 0.20)
        case .verify: return Color(red: 0.30, green: 0.90, blue: 0.50)
        case .loop: return .pink
        case .output: return Color(red: 0.40, green: 0.85, blue: 1.0)
        }
    }

    var defaultLabel: String {
        switch self {
        case .input: return "Input"
        case .model: return "Claude"
        case .action: return "Rewrite"
        case .verify: return "≥80%"
        case .loop: return "×3"
        case .output: return "Paste"
        }
    }

    var defaultConfig: [String: String] {
        switch self {
        case .input: return [:]
        case .model: return ["model": "cheap"]
        case .action: return ["action": "rewrite"]
        case .verify: return ["threshold": "0.8"]
        case .loop: return ["max": "3"]
        case .output: return [:]
        }
    }
}
