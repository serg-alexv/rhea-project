import SwiftUI
import WebKit

// Change to your machine's local IP for on-device testing
private let atlasBase = "http://localhost:3000"

#if os(iOS)
struct AtlasWebView: UIViewRepresentable {
    let path: String

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        let webView = WKWebView(frame: .zero, configuration: config)
        if let url = URL(string: atlasBase + path) {
            webView.load(URLRequest(url: url))
        }
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {}
}
#else
struct AtlasWebView: NSViewRepresentable {
    let path: String

    func makeNSView(context: Context) -> WKWebView {
        let webView = WKWebView(frame: .zero)
        if let url = URL(string: atlasBase + path) {
            webView.load(URLRequest(url: url))
        }
        return webView
    }

    func updateNSView(_ webView: WKWebView, context: Context) {}
}
#endif
