import SwiftUI
import WebKit

struct AtlasView: View {
    @AppStorage("atlasBaseURL") private var atlasBaseURL = AppConfig.defaultAtlasBaseURL

    var body: some View {
        AtlasWebView(path: "/", baseURL: atlasBaseURL)
    }
}

#if os(iOS)
struct AtlasWebView: UIViewRepresentable {
    let path: String
    let baseURL: String

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        let webView = WKWebView(frame: .zero, configuration: config)
        if let url = URL(string: baseURL + path) {
            webView.load(URLRequest(url: url))
        }
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {}
}
#else
struct AtlasWebView: NSViewRepresentable {
    let path: String
    let baseURL: String

    func makeNSView(context: Context) -> WKWebView {
        let webView = WKWebView(frame: .zero)
        if let url = URL(string: baseURL + path) {
            webView.load(URLRequest(url: url))
        }
        return webView
    }

    func updateNSView(_ webView: WKWebView, context: Context) {}
}
#endif
