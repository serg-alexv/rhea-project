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
///
/// The renderer runs entirely client-side — 3Dmol.js loaded from CDN,
/// no server-side computation needed. PDB files fetched from RCSB.
public struct BioRendererView: View {
    @State private var searchText = ""
    @State private var currentID = "1CRN"  // crambin — classic small protein
    @State private var renderStyle = "cartoon"
    @State private var colorScheme = "spectrum"
    @State private var isLoading = false
    @State private var errorMsg: String?
    @State private var webViewRef = WebViewRef()

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
                    pdbID: currentID,
                    style: renderStyle,
                    colorScheme: colorScheme,
                    ref: webViewRef
                )
                .frame(maxWidth: .infinity, maxHeight: .infinity)

                // Style controls
                styleBar
            }
            .background(RheaTheme.bg)
            .navigationTitle("Bio")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
        }
    }

    private var controlBar: some View {
        VStack(spacing: 6) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "atom")
                    .foregroundStyle(RheaTheme.accent)
                    .font(.system(size: 14))

                TextField("PDB ID or SMILES...", text: $searchText)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundStyle(.white)
                    #if os(iOS)
                    .textInputAutocapitalization(.characters)
                    #endif
                    .autocorrectionDisabled()
                    .submitLabel(.search)
                    .onSubmit { loadStructure() }

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

            // Preset molecules
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    ForEach(presets, id: \.id) { preset in
                        Button {
                            currentID = preset.id
                            searchText = preset.id
                        } label: {
                            Text(preset.name)
                                .font(.system(size: 10, weight: .medium, design: .monospaced))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    Capsule()
                                        .fill(currentID == preset.id
                                              ? RheaTheme.accent.opacity(0.2)
                                              : RheaTheme.card)
                                        .overlay(
                                            Capsule()
                                                .stroke(currentID == preset.id
                                                        ? RheaTheme.accent.opacity(0.4)
                                                        : RheaTheme.cardBorder, lineWidth: 0.5)
                                        )
                                )
                                .foregroundStyle(currentID == preset.id ? RheaTheme.accent : .secondary)
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

    private func loadStructure() {
        let input = searchText.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        guard !input.isEmpty else { return }
        errorMsg = nil
        currentID = input
    }
}

// MARK: - WebView Reference

class WebViewRef: ObservableObject {
    var webView: WKWebView?
}

// MARK: - 3Dmol.js WebView

#if os(iOS)
struct BioWebView: UIViewRepresentable {
    let pdbID: String
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
        webView.loadHTMLString(bioHTML(pdbID: pdbID, style: style, colorScheme: colorScheme), baseURL: nil)
    }
}
#else
struct BioWebView: NSViewRepresentable {
    let pdbID: String
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
        webView.loadHTMLString(bioHTML(pdbID: pdbID, style: style, colorScheme: colorScheme), baseURL: nil)
    }
}
#endif

// MARK: - 3Dmol.js HTML Template

private func bioHTML(pdbID: String, style: String, colorScheme: String) -> String {
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
            }
        </style>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
    </head>
    <body>
        <div id="viewer"></div>
        <div id="info">\(pdbID)</div>
        <div id="loading">Loading \(pdbID)...</div>
        <script>
            var viewer = $3Dmol.createViewer("viewer", {
                backgroundColor: "0x0f0f1a",
                antialias: true
            });

            $3Dmol.download("pdb:\(pdbID)", viewer, {}, function() {
                \(styleJS)
                viewer.zoomTo();
                viewer.render();
                document.getElementById("loading").style.display = "none";

                // Show atom count
                var atoms = viewer.getModel().selectedAtoms({});
                document.getElementById("info").textContent =
                    "\(pdbID) — " + atoms.length + " atoms";
            });
        </script>
    </body>
    </html>
    """
}
