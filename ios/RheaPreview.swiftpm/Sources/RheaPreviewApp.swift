import SwiftUI

@main
struct RheaPreviewApp: App {
    var body: some Scene {
        WindowGroup {
            TabView {
                DialogView()
                    .tabItem { Label("Dialog", systemImage: "text.bubble") }

                TeamChatView()
                    .tabItem { Label("Team", systemImage: "bubble.left.and.bubble.right") }

                AtlasView()
                    .tabItem { Label("Atlas", systemImage: "globe") }

                GovernorView()
                    .tabItem { Label("Governor", systemImage: "gauge.with.dots.needle.33percent") }

                PulseMonitorView()
                    .tabItem { Label("Pulse", systemImage: "dot.radiowaves.left.and.right") }

                TasksView()
                    .tabItem { Label("Tasks", systemImage: "checklist") }

                NavigationStack {
                    ScreenPilotView()
                }
                    .tabItem { Label("Pilot", systemImage: "antenna.radiowaves.left.and.right.circle") }

                SettingsView()
                    .tabItem { Label("Settings", systemImage: "slider.horizontal.3") }
            }
            .preferredColorScheme(.dark)
        }
    }
}
