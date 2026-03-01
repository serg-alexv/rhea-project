import SwiftUI
import AnimatedTabBar
import RheaKit

@main
struct RheaPreviewApp: App {
    @AppStorage("hasEnteredIntent") private var hasEnteredIntent = false
    @AppStorage("intentRevealLevel") private var intentRevealLevel = 1
    @AppStorage("skipAuth") private var skipAuth = false
    @StateObject private var auth = AuthManager.shared
    @State private var selectedTab = 0

    init() {
        AppConfig.migrateStaleDefaults()
    }

    var body: some Scene {
        WindowGroup {
            Group {
                if !auth.isLoggedIn && !skipAuth {
                    AuthView()
                        .onReceive(auth.objectWillChange) { _ in
                            // "Continue without account" sets token=nil, which triggers skipAuth
                            if !auth.isLoggedIn {
                                skipAuth = true
                            }
                        }
                } else if hasEnteredIntent {
                    MainTabShell(selectedTab: $selectedTab, revealLevel: intentRevealLevel)
                } else {
                    IntentEntryView(selectedTab: $selectedTab)
                }
            }
            .preferredColorScheme(.dark)
            .environmentObject(auth)
        }
    }
}

// MARK: - Tab descriptor for dynamic tab configuration
private struct TabDescriptor {
    let icon: String
    let label: String
    let view: AnyView
}

private struct MainTabShell: View {
    @Binding var selectedTab: Int
    let revealLevel: Int

    private var tabs: [TabDescriptor] {
        var list: [TabDescriptor] = [
            TabDescriptor(icon: "scalemass", label: "Tribunal", view: AnyView(DialogView())),
            TabDescriptor(icon: "antenna.radiowaves.left.and.right", label: "Radio", view: AnyView(TeamChatView())),
        ]
        if revealLevel >= 2 {
            list.append(TabDescriptor(icon: "gauge.with.dots.needle.33percent", label: "Governor", view: AnyView(GovernorView())))
            list.append(TabDescriptor(icon: "checklist", label: "Tasks", view: AnyView(TasksView())))
        }
        if revealLevel >= 3 {
            list.append(TabDescriptor(icon: "globe", label: "Atlas", view: AnyView(AtlasView())))
            list.append(TabDescriptor(icon: "dot.radiowaves.left.and.right", label: "Pulse", view: AnyView(PulseMonitorView())))
            list.append(TabDescriptor(icon: "atom", label: "Bio", view: AnyView(BioRendererView())))
            list.append(TabDescriptor(icon: "shield.lefthalf.filled", label: "Relay", view: AnyView(RelayPrivacyView())))
        }
        list.append(TabDescriptor(icon: "slider.horizontal.3", label: "Settings", view: AnyView(SettingsView())))
        return list
    }

    /// Clamp selectedTab to valid range when revealLevel changes
    private var safeIndex: Int {
        min(max(selectedTab, 0), tabs.count - 1)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Page content
            tabs[safeIndex].view
                .frame(maxWidth: .infinity, maxHeight: .infinity)

            // Animated tab bar
            AnimatedTabBar(selectedIndex: $selectedTab, views: tabs.map { tab in
                VStack(spacing: 2) {
                    Image(systemName: tab.icon)
                        .font(.system(size: 18))
                    Text(tab.label)
                        .font(.system(size: 9, weight: .medium, design: .monospaced))
                }
            })
            .barColor(RheaTheme.card)
            .selectedColor(RheaTheme.accent)
            .unselectedColor(.gray)
            .ballColor(RheaTheme.accent)
            .verticalPadding(12)
            .cornerRadius(0)
            .ballTrajectory(.parabolic)
            .ballAnimation(.spring(duration: 0.4, bounce: 0.2))
            .indentAnimation(.spring(duration: 0.4, bounce: 0.1))
        }
        .background(RheaTheme.bg)
        .onChange(of: tabs.count) {
            // Clamp if tab count changes
            if selectedTab >= tabs.count {
                selectedTab = tabs.count - 1
            }
        }
    }
}

private struct IntentRoute: Identifiable {
    let id: String
    let title: String
    let subtitle: String
    let seed: String
    let role: String
    let revealLevel: Int
    let icon: String
}

private struct IntentEntryView: View {
    @Binding var selectedTab: Int
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @AppStorage("hasEnteredIntent") private var hasEnteredIntent = false
    @AppStorage("intentRevealLevel") private var intentRevealLevel = 1
    @AppStorage("intentRole") private var intentRole = "biochemist"
    @AppStorage("firstIntentText") private var firstIntentText = ""

    @State private var intentText = ""
    @State private var isSending = false
    @State private var errorText: String? = nil

    private let routes: [IntentRoute] = [
        .init(
            id: "quick",
            title: "Quick Ask",
            subtitle: "2 steps to first useful answer",
            seed: "Give me one practical next step for my current work block.",
            role: "biochemist",
            revealLevel: 1,
            icon: "bolt.fill"
        ),
        .init(
            id: "research",
            title: "Research",
            subtitle: "Hypothesis -> evidence -> next experiment",
            seed: "I need a hypothesis + evidence plan for this research question:",
            role: "biochemist",
            revealLevel: 2,
            icon: "flask.fill"
        ),
        .init(
            id: "operator",
            title: "Operator",
            subtitle: "Queue, radio, and control panel",
            seed: "Show current blockers, owner, and next action for each P0 item.",
            role: "operator",
            revealLevel: 2,
            icon: "slider.horizontal.3"
        ),
        .init(
            id: "investor",
            title: "Investor",
            subtitle: "Proof of progress with concrete signals",
            seed: "What changed in the last 90 minutes with verifiable evidence?",
            role: "investor",
            revealLevel: 2,
            icon: "chart.line.uptrend.xyaxis"
        )
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Text("Rhea")
                        .font(.system(size: 34, weight: .bold, design: .rounded))
                        .foregroundStyle(.white)
                    Text("Start with one base query. Advanced controls open only after intent.")
                        .font(.system(size: 13, weight: .medium, design: .default))
                        .foregroundStyle(.secondary)

                    routeGrid

                    VStack(alignment: .leading, spacing: 8) {
                        Text("BASE QUERY")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.accent)

                        TextField("What do you need right now?", text: $intentText, axis: .vertical)
                            .textFieldStyle(.plain)
                            .font(.system(size: 15))
                            .foregroundStyle(.white)
                            .lineLimit(2...5)
                            .padding(12)
                            .background(
                                RoundedRectangle(cornerRadius: 14)
                                    .fill(RheaTheme.card)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 14)
                                            .stroke(RheaTheme.cardBorder, lineWidth: 1)
                                    )
                            )
                    }
                    .glassCard()

                    if let errorText {
                        Text(errorText)
                            .font(.system(size: 12, weight: .semibold, design: .monospaced))
                            .foregroundStyle(RheaTheme.red)
                    }

                    HStack(spacing: 10) {
                        Button(action: submitIntent) {
                            HStack(spacing: 8) {
                                if isSending {
                                    ProgressView()
                                        .scaleEffect(0.75)
                                } else {
                                    Image(systemName: "arrow.up.circle.fill")
                                }
                                Text(isSending ? "Sending..." : "Start")
                            }
                            .font(.system(size: 14, weight: .bold, design: .monospaced))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(RheaTheme.accent)
                        .disabled(isSending || intentText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

                        Button("Expert") {
                            intentRole = "operator"
                            intentRevealLevel = 3
                            hasEnteredIntent = true
                            selectedTab = 2
                        }
                        .font(.system(size: 13, weight: .semibold, design: .monospaced))
                        .buttonStyle(.bordered)
                    }
                }
                .padding(16)
            }
            .background(RheaTheme.bg)
            .navigationTitle("Intent")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private var routeGrid: some View {
        VStack(spacing: 10) {
            ForEach(routes) { route in
                Button {
                    intentText = route.seed
                    intentRole = route.role
                    intentRevealLevel = route.revealLevel
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: route.icon)
                            .frame(width: 20)
                            .foregroundStyle(RheaTheme.accent)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(route.title)
                                .font(.system(size: 14, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white)
                            Text(route.subtitle)
                                .font(.system(size: 12))
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                    }
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(RheaTheme.card)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(RheaTheme.cardBorder, lineWidth: 1)
                            )
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func submitIntent() {
        let text = intentText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isSending else { return }
        isSending = true
        errorText = nil

        let body = DialogRequest(text: text, sender: "human")
        guard let url = URL(string: "\(apiBaseURL)/dialog"),
              let payload = try? JSONEncoder().encode(body) else {
            isSending = false
            errorText = "Invalid API configuration."
            return
        }

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        req.httpBody = payload

        URLSession.shared.dataTask(with: req) { _, response, error in
            DispatchQueue.main.async {
                isSending = false
                if let error {
                    errorText = "Send failed: \(error.localizedDescription)"
                    return
                }
                if let http = response as? HTTPURLResponse, http.statusCode >= 300 {
                    errorText = "Send failed: HTTP \(http.statusCode)"
                    return
                }
                firstIntentText = text
                hasEnteredIntent = true
                selectedTab = 0
            }
        }.resume()
    }
}
