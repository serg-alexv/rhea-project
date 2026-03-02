import SwiftUI
import WebKit

/// Molecular visualization powered by 3Dmol.js in a WebView.
///
/// Features:
///   - PDB lookup by ID (e.g. "1CRN" for crambin)
///   - SMILES input for small molecules (drug candidates)
///   - Multiple render styles: cartoon, stick, sphere, surface
///   - Rotate, zoom, pan via touch/mouse gestures
///   - Color by chain, secondary structure, or element
///   - "Ask about this molecule" — tribunal-powered analysis panel
///
/// The renderer runs entirely client-side — 3Dmol.js bundled locally (no CDN),
/// no server-side computation needed. PDB files fetched from RCSB (public domain).
public struct BioRendererView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = "http://localhost:8400"

    @State private var searchText = ""
    @State private var currentID = "1CRN"  // crambin — classic small protein
    @State private var isSmilesMode = false
    @State private var renderStyle = "cartoon"
    @State private var colorScheme = "spectrum"
    @State private var isLoading = false
    @State private var errorMsg: String?
    @State private var webViewRef = WebViewRef()

    // Analysis panel
    @State private var analysisText: String? = nil
    @State private var isAnalysisLoading = false
    @State private var analysisExpanded = false
    @State private var analysisError: String? = nil

    // Copy/export
    @State private var snapshotCopied = false

    // Metadata panel
    @State private var metaTitle: String? = nil
    @State private var metaMethod: String? = nil
    @State private var metaResolution: String? = nil
    @State private var metaOrganism: String? = nil

    private let styles = ["cartoon", "stick", "sphere", "line", "cross"]
    private let colors = ["spectrum", "chain", "ss", "element", "residue"]
    private let presets: [(id: String, name: String)] = [
        ("1CRN", "Crambin"),
        ("1BNA", "DNA B-form"),
        ("4HHB", "Hemoglobin"),
        ("1ATP", "ATP synthase"),
        ("6LU7", "SARS-CoV-2 Mpro"),
        ("1GZM", "GFP"),
    ]

    public init() {}

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Search + presets
                controlBar

                // 3D viewer
                BioWebView(
                    moleculeID: currentID,
                    isSMILES: isSmilesMode,
                    style: renderStyle,
                    colorScheme: colorScheme,
                    ref: webViewRef
                )
                .frame(maxWidth: .infinity, maxHeight: .infinity)

                // Analysis panel (collapsible, shown after Ask)
                if analysisText != nil || isAnalysisLoading || analysisError != nil {
                    analysisPanel
                }

                // Style controls
                styleBar
            }
            .background(RheaTheme.bg)
            .navigationTitle("Bio")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .toolbar {
                ToolbarItemGroup(placement: .primaryAction) {
                    // Copy 3D snapshot to clipboard
                    Button {
                        captureSnapshot()
                    } label: {
                        Image(systemName: snapshotCopied ? "checkmark.circle.fill" : "camera.fill")
                            .font(.system(size: 14))
                            .foregroundStyle(snapshotCopied ? RheaTheme.green : RheaTheme.accent)
                    }
                    .help("Copy 3D view to clipboard")

                    // Copy analysis text
                    if let text = analysisText {
                        Button {
                            #if os(iOS)
                            UIPasteboard.general.string = "[\(currentID)] \(text)"
                            #else
                            NSPasteboard.general.clearContents()
                            NSPasteboard.general.setString("[\(currentID)] \(text)", forType: .string)
                            #endif
                        } label: {
                            Image(systemName: "doc.on.doc")
                                .font(.system(size: 13))
                                .foregroundStyle(RheaTheme.green)
                        }
                        .help("Copy analysis text")
                    }
                }
            }
        }
    }

    // MARK: - Control Bar

    private var controlBar: some View {
        VStack(spacing: 6) {
            // Search row
            HStack(spacing: 8) {
                Image(systemName: isSmilesMode ? "flask" : "atom")
                    .foregroundStyle(isSmilesMode ? RheaTheme.amber : RheaTheme.accent)
                    .font(.system(size: 14))

                TextField("PDB ID or SMILES...", text: $searchText)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundStyle(.white)
                    #if os(iOS)
                    .textInputAutocapitalization(.never)
                    #endif
                    .autocorrectionDisabled()
                    .submitLabel(.search)
                    .onSubmit { loadStructure() }

                // Ask button
                Button(action: askAboutMolecule) {
                    Image(systemName: "brain")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(isAnalysisLoading ? .secondary : RheaTheme.green)
                }
                .disabled(isAnalysisLoading)

                Button(action: loadStructure) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(searchText.isEmpty ? .secondary : RheaTheme.accent)
                }
                .disabled(searchText.isEmpty)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(RheaTheme.card)

            // Metadata row (shown when we have PDB metadata)
            if let title = metaTitle {
                HStack(spacing: 6) {
                    Text(title)
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                    Spacer()
                    if let method = metaMethod {
                        metaTag(method)
                    }
                    if let res = metaResolution {
                        metaTag(res + " Å")
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 2)
            }

            // Preset molecules
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    ForEach(presets, id: \.id) { preset in
                        Button {
                            currentID = preset.id
                            searchText = preset.id
                            isSmilesMode = false
                            clearAnalysis()
                            fetchMetadata(for: preset.id)
                        } label: {
                            Text(preset.name)
                                .font(.system(size: 10, weight: .medium, design: .monospaced))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    Capsule()
                                        .fill(currentID == preset.id && !isSmilesMode
                                              ? RheaTheme.accent.opacity(0.2)
                                              : RheaTheme.card)
                                        .overlay(
                                            Capsule()
                                                .stroke(currentID == preset.id && !isSmilesMode
                                                        ? RheaTheme.accent.opacity(0.4)
                                                        : RheaTheme.cardBorder, lineWidth: 0.5)
                                        )
                                )
                                .foregroundStyle(currentID == preset.id && !isSmilesMode
                                                 ? RheaTheme.accent : .secondary)
                        }
                    }

                    Divider()
                        .frame(height: 14)
                        .padding(.horizontal, 2)

                    // SMILES presets
                    ForEach(smilesPresets, id: \.name) { preset in
                        Button {
                            currentID = preset.smiles
                            searchText = preset.smiles
                            isSmilesMode = true
                            clearAnalysis()
                            clearMeta()
                        } label: {
                            Text(preset.name)
                                .font(.system(size: 10, weight: .medium, design: .monospaced))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    Capsule()
                                        .fill(currentID == preset.smiles && isSmilesMode
                                              ? RheaTheme.amber.opacity(0.2)
                                              : RheaTheme.card)
                                        .overlay(
                                            Capsule()
                                                .stroke(currentID == preset.smiles && isSmilesMode
                                                        ? RheaTheme.amber.opacity(0.4)
                                                        : RheaTheme.cardBorder, lineWidth: 0.5)
                                        )
                                )
                                .foregroundStyle(currentID == preset.smiles && isSmilesMode
                                                 ? RheaTheme.amber : .secondary)
                        }
                    }
                }
                .padding(.horizontal, 12)
            }

            if let err = errorMsg {
                Text(err)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(RheaTheme.red)
                    .padding(.horizontal, 12)
            }
        }
        .padding(.vertical, 4)
    }

    // MARK: - Analysis Panel

    private var analysisPanel: some View {
        VStack(spacing: 0) {
            // Header / toggle
            Button(action: { withAnimation(.easeInOut(duration: 0.2)) { analysisExpanded.toggle() } }) {
                HStack(spacing: 6) {
                    Image(systemName: "brain")
                        .font(.system(size: 11))
                        .foregroundStyle(RheaTheme.green)

                    Text("MOLECULE ANALYSIS")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(RheaTheme.green)

                    if isAnalysisLoading {
                        ProgressView()
                            .scaleEffect(0.6)
                            .tint(RheaTheme.green)
                    }

                    Spacer()

                    Image(systemName: analysisExpanded ? "chevron.down" : "chevron.right")
                        .font(.system(size: 10))
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
            }
            .background(RheaTheme.card)

            if analysisExpanded {
                Divider()
                    .background(RheaTheme.cardBorder)

                ScrollView {
                    if let err = analysisError {
                        Text(err)
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(RheaTheme.red)
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    } else if let text = analysisText {
                        Text(text)
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.85))
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    } else if isAnalysisLoading {
                        Text("Querying Rhea AI...")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .padding(12)
                    }
                }
                .frame(maxHeight: 160)
                .background(RheaTheme.bg)
            }
        }
    }

    // MARK: - Style Bar

    private var styleBar: some View {
        VStack(spacing: 6) {
            // Render style
            HStack(spacing: 4) {
                Text("STYLE")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                    .frame(width: 40)

                ForEach(styles, id: \.self) { style in
                    Button {
                        renderStyle = style
                    } label: {
                        Text(style.prefix(4).uppercased())
                            .font(.system(size: 9, weight: .semibold, design: .monospaced))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(
                                Capsule().fill(renderStyle == style
                                              ? RheaTheme.green.opacity(0.2)
                                              : Color.clear)
                            )
                            .foregroundStyle(renderStyle == style ? RheaTheme.green : .secondary)
                    }
                }
                Spacer()
            }

            // Color scheme
            HStack(spacing: 4) {
                Text("COLOR")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                    .frame(width: 40)

                ForEach(colors, id: \.self) { color in
                    Button {
                        colorScheme = color
                    } label: {
                        Text(color.prefix(4).uppercased())
                            .font(.system(size: 9, weight: .semibold, design: .monospaced))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(
                                Capsule().fill(colorScheme == color
                                              ? RheaTheme.amber.opacity(0.2)
                                              : Color.clear)
                            )
                            .foregroundStyle(colorScheme == color ? RheaTheme.amber : .secondary)
                    }
                }
                Spacer()
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(RheaTheme.card)
    }

    // MARK: - Helper views

    private func metaTag(_ label: String) -> some View {
        Text(label)
            .font(.system(size: 9, weight: .medium, design: .monospaced))
            .padding(.horizontal, 5)
            .padding(.vertical, 2)
            .background(Capsule().fill(RheaTheme.accent.opacity(0.12)))
            .foregroundStyle(RheaTheme.accent.opacity(0.7))
    }

    // MARK: - SMILES Presets

    private let smilesPresets: [(name: String, smiles: String)] = [
        ("Aspirin",   "CC(=O)Oc1ccccc1C(=O)O"),
        ("Caffeine",  "Cn1cnc2c1c(=O)n(C)c(=O)n2C"),
        ("Dopamine",  "NCCc1ccc(O)c(O)c1"),
        ("Glucose",   "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O"),
    ]

    // MARK: - Snapshot Copy (cross-device via clipboard sync)

    private func captureSnapshot() {
        guard let webView = webViewRef.webView else { return }

        #if os(iOS)
        let config = WKSnapshotConfiguration()
        webView.takeSnapshot(with: config) { image, error in
            guard let image = image, error == nil else { return }
            UIPasteboard.general.image = image
            withAnimation { snapshotCopied = true }
            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                withAnimation { snapshotCopied = false }
            }
            // Haptic feedback
            let generator = UINotificationFeedbackGenerator()
            generator.notificationOccurred(.success)
        }
        #else
        let config = WKSnapshotConfiguration()
        webView.takeSnapshot(with: config) { image, error in
            guard let image = image, error == nil else { return }
            let pb = NSPasteboard.general
            pb.clearContents()
            pb.writeObjects([image])
            withAnimation { snapshotCopied = true }
            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                withAnimation { snapshotCopied = false }
            }
        }
        #endif
    }

    // MARK: - Actions

    private func loadStructure() {
        let raw = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !raw.isEmpty else { return }
        errorMsg = nil

        if isSMILES(raw) {
            currentID = raw
            isSmilesMode = true
            clearMeta()
        } else {
            let upper = raw.uppercased()
            currentID = upper
            isSmilesMode = false
            fetchMetadata(for: upper)
        }
        clearAnalysis()
    }

    private func askAboutMolecule() {
        guard !isAnalysisLoading else { return }
        let molecule = currentID
        let isSMILESMolecule = isSmilesMode

        analysisText = nil
        analysisError = nil
        isAnalysisLoading = true
        analysisExpanded = true

        let prompt: String
        if isSMILESMolecule {
            prompt = "Describe the biological significance of this molecule (SMILES: \(molecule)). Include: chemical class, pharmacological activity, key functional groups, common research uses, and any known drug interactions."
        } else {
            prompt = "Describe the biological significance of \(molecule). Include: protein function, common uses in biochemistry research, key binding sites, structural highlights, and any known drug interactions or therapeutic relevance."
        }

        let body: [String: Any] = [
            "text": prompt,
            "action": "freeform"
        ]

        guard let url = URL(string: "\(apiBaseURL)/keyboard/quick"),
              let bodyData = try? JSONSerialization.data(withJSONObject: body) else {
            analysisError = "Invalid API URL"
            isAnalysisLoading = false
            return
        }

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = bodyData
        req.timeoutInterval = 30

        URLSession.shared.dataTask(with: req) { data, _, error in
            DispatchQueue.main.async {
                self.isAnalysisLoading = false
                if let error = error {
                    self.analysisError = "Network error: \(error.localizedDescription)"
                    return
                }
                guard let data = data,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let text = json["text"] as? String else {
                    self.analysisError = "Failed to parse response"
                    return
                }
                self.analysisText = text
            }
        }.resume()
    }

    private func fetchMetadata(for pdbID: String) {
        clearMeta()
        guard let url = URL(string: "\(apiBaseURL)/bio/lookup?q=\(pdbID)") else { return }

        URLSession.shared.dataTask(with: url) { data, _, _ in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }

            DispatchQueue.main.async {
                if let err = json["error"] as? String, !err.isEmpty { return }
                self.metaTitle = json["title"] as? String
                self.metaMethod = (json["experimental_method"] as? String).flatMap {
                    $0.isEmpty ? nil : String($0.prefix(4).uppercased())
                }
                if let res = json["resolution_angstrom"] {
                    if let d = res as? Double {
                        self.metaResolution = String(format: "%.2f", d)
                    } else if let s = res as? String {
                        self.metaResolution = s
                    }
                }
                self.metaOrganism = json["organism"] as? String
            }
        }.resume()
    }

    private func clearAnalysis() {
        analysisText = nil
        analysisError = nil
        isAnalysisLoading = false
        analysisExpanded = false
    }

    private func clearMeta() {
        metaTitle = nil
        metaMethod = nil
        metaResolution = nil
        metaOrganism = nil
    }
}

// MARK: - SMILES Heuristic

/// Returns true when `input` looks like a SMILES string rather than a PDB ID.
///
/// Rules:
///   - A 4-char alphanumeric string like "1CRN" is always PDB.
///   - Presence of SMILES-specific characters (=, #, (, ), @, /, \\, [, ])
///     or lowercase organic-subset atoms signals SMILES.
///   - Strings longer than 6 chars with no spaces that are not purely
///     alphanumeric are treated as SMILES.
func isSMILES(_ input: String) -> Bool {
    let trimmed = input.trimmingCharacters(in: .whitespacesAndNewlines)

    // Classic PDB IDs: exactly 4 alphanumeric chars
    let isAlnum = trimmed.allSatisfy { $0.isLetter || $0.isNumber }
    if trimmed.count == 4 && isAlnum { return false }

    // Definitive SMILES tokens
    let smilesChars: Set<Character> = ["=", "#", "(", ")", "@", "/", "\\", "[", "]", "+", "-", "%"]
    if trimmed.contains(where: { smilesChars.contains($0) }) { return true }

    // Lowercase organic-subset atoms that appear in SMILES but not PDB IDs
    // (SMILES uses c, n, o, s for aromatic; PDB IDs are uppercase)
    let lowerOrganics: Set<Character> = ["c", "n", "o", "s", "p", "b", "f", "i"]
    if trimmed.contains(where: { lowerOrganics.contains($0) }) { return true }

    // Long alphanumeric strings beyond 6 chars with digits embedded = likely SMILES InChI fragment
    if trimmed.count > 6 && !isAlnum { return true }

    return false
}

// MARK: - WebView Reference

class WebViewRef: ObservableObject {
    var webView: WKWebView?
}

// MARK: - 3Dmol.js WebView

#if os(iOS)
struct BioWebView: UIViewRepresentable {
    let moleculeID: String
    let isSMILES: Bool
    let style: String
    let colorScheme: String
    let ref: WebViewRef

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = false
        webView.backgroundColor = .clear
        webView.scrollView.isScrollEnabled = false
        ref.webView = webView
        loadMolecule(webView)
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        loadMolecule(webView)
    }

    private func loadMolecule(_ webView: WKWebView) {
        webView.loadHTMLString(
            bioHTML(moleculeID: moleculeID, isSMILES: isSMILES, style: style, colorScheme: colorScheme),
            baseURL: nil
        )
    }
}
#else
struct BioWebView: NSViewRepresentable {
    let moleculeID: String
    let isSMILES: Bool
    let style: String
    let colorScheme: String
    let ref: WebViewRef

    func makeNSView(context: Context) -> WKWebView {
        let webView = WKWebView(frame: .zero)
        webView.wantsLayer = true
        webView.layer?.backgroundColor = .clear
        ref.webView = webView
        loadMolecule(webView)
        return webView
    }

    func updateNSView(_ webView: WKWebView, context: Context) {
        loadMolecule(webView)
    }

    private func loadMolecule(_ webView: WKWebView) {
        webView.loadHTMLString(
            bioHTML(moleculeID: moleculeID, isSMILES: isSMILES, style: style, colorScheme: colorScheme),
            baseURL: nil
        )
    }
}
#endif

// MARK: - Bundled 3Dmol.js (no CDN dependency)

private let _bundled3DmolJS: String = {
    guard let url = Bundle.module.url(forResource: "3Dmol-min", withExtension: "js"),
          let js = try? String(contentsOf: url) else {
        return "/* 3Dmol.js bundle missing */"
    }
    return js
}()

// MARK: - 3Dmol.js HTML Template

private func bioHTML(moleculeID: String, isSMILES: Bool, style: String, colorScheme: String) -> String {
    let colorJS: String
    switch colorScheme {
    case "chain": colorJS = "{colorfunc: $3Dmol.chainHetatmColorFunc}"
    case "ss": colorJS = "{colorscheme: 'ssJmol'}"
    case "element": colorJS = "{colorscheme: 'default'}"
    case "residue": colorJS = "{colorscheme: 'amino'}"
    default: colorJS = "{color: 'spectrum'}"
    }

    let styleJS: String
    switch style {
    case "stick": styleJS = "viewer.setStyle({}, {stick: \(colorJS)});"
    case "sphere": styleJS = "viewer.setStyle({}, {sphere: {scale: 0.3, \(colorJS.dropFirst().dropLast())}});"
    case "line": styleJS = "viewer.setStyle({}, {line: \(colorJS)});"
    case "cross": styleJS = "viewer.setStyle({}, {cross: {linewidth: 2, \(colorJS.dropFirst().dropLast())}});"
    default: styleJS = "viewer.setStyle({}, {cartoon: \(colorJS)});"
    }

    // Escape the molecule ID for safe embedding in JS string literals.
    // SMILES strings can contain characters like (, ), =, # which are
    // safe inside a single-quoted JS string but we must escape backslashes
    // and single quotes.
    let escapedID = moleculeID
        .replacingOccurrences(of: "\\", with: "\\\\")
        .replacingOccurrences(of: "'", with: "\\'")

    // Build the JS snippet that loads the molecule.
    // For SMILES: addModel(smilesString, "smi") then render inline.
    // For PDB IDs: $3Dmol.download("pdb:ID", ...) as before.
    let loadJS: String
    let displayLabel: String

    if isSMILES {
        displayLabel = "SMILES"
        loadJS = """
            try {
                viewer.addModel('\(escapedID)', 'smi');
                \(styleJS)
                viewer.zoomTo();
                viewer.render();
                document.getElementById('loading').style.display = 'none';
                var atoms = viewer.getModel().selectedAtoms({});
                document.getElementById('info').textContent =
                    'SMILES — ' + atoms.length + ' atoms';
            } catch(e) {
                document.getElementById('loading').textContent = 'Error: ' + e.message;
                document.getElementById('loading').style.color = '#ff6b6b';
            }
        """
    } else {
        displayLabel = moleculeID
        loadJS = """
            $3Dmol.download('pdb:\(escapedID)', viewer, {}, function() {
                \(styleJS)
                viewer.zoomTo();
                viewer.render();
                document.getElementById('loading').style.display = 'none';
                var atoms = viewer.getModel().selectedAtoms({});
                document.getElementById('info').textContent =
                    '\(escapedID) — ' + atoms.length + ' atoms';
            });
        """
    }

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * { margin: 0; padding: 0; }
            body { background: #0f0f1a; overflow: hidden; }
            #viewer { width: 100vw; height: 100vh; position: relative; }
            #info {
                position: absolute; bottom: 8px; left: 8px;
                color: rgba(255,255,255,0.5);
                font: 10px/1.2 monospace;
                pointer-events: none;
            }
            #loading {
                position: absolute; top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                color: rgba(102, 217, 255, 0.8);
                font: 14px monospace;
                text-align: center;
                max-width: 80vw;
            }
        </style>
        <script>\(_bundled3DmolJS)</script>
    </head>
    <body>
        <div id="viewer"></div>
        <div id="info">\(displayLabel)</div>
        <div id="loading">Loading \(displayLabel)...</div>
        <script>
            var viewer = $3Dmol.createViewer("viewer", {
                backgroundColor: "0x0f0f1a",
                antialias: true
            });
            \(loadJS)
        </script>
    </body>
    </html>
    """
}
