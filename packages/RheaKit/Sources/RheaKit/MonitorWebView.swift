import SwiftUI
import WebKit

/// Live picture — shows the /monitor web dashboard in a WebView.
/// This is the real-time control panel: agents, tokens, history, radio.
/// Auto-refreshes every 5s server-side, no client polling needed.
public struct MonitorWebView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var isLoading = true

    public init() {}

    public var body: some View {
        NavigationStack {
            ZStack {
                MonitorWeb(url: "\(apiBaseURL)/monitor", isLoading: $isLoading)

                if isLoading {
                    ProgressView("Connecting to monitor...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(RheaTheme.bg.opacity(0.8))
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("Monitor")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
        }
    }
}

#if os(iOS)
private struct MonitorWeb: UIViewRepresentable {
    let url: String
    @Binding var isLoading: Bool

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = false
        webView.backgroundColor = UIColor(RheaTheme.bg)
        webView.navigationDelegate = context.coordinator
        if let u = URL(string: url) {
            webView.load(URLRequest(url: u))
        }
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(isLoading: $isLoading) }

    class Coordinator: NSObject, WKNavigationDelegate {
        @Binding var isLoading: Bool
        init(isLoading: Binding<Bool>) { _isLoading = isLoading }
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            isLoading = false
        }
        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            isLoading = false
        }
    }
}
#else
private struct MonitorWeb: NSViewRepresentable {
    let url: String
    @Binding var isLoading: Bool

    func makeNSView(context: Context) -> WKWebView {
        let webView = WKWebView(frame: .zero)
        webView.navigationDelegate = context.coordinator
        if let u = URL(string: url) {
            webView.load(URLRequest(url: u))
        }
        return webView
    }

    func updateNSView(_ webView: WKWebView, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(isLoading: $isLoading) }

    class Coordinator: NSObject, WKNavigationDelegate {
        @Binding var isLoading: Bool
        init(isLoading: Binding<Bool>) { _isLoading = isLoading }
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            isLoading = false
        }
    }
}
#endif
