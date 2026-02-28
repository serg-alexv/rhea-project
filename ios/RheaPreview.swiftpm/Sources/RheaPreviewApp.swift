import SwiftUI

@main
struct RheaPreviewApp: App {
    var body: some Scene {
        WindowGroup {
            TabView {
                TeamChatView()
                    .tabItem { Label("Team", systemImage: "bubble.left.and.bubble.right") }

                AtlasView()
                    .tabItem { Label("Atlas", systemImage: "globe") }

                GovernorView()
                    .tabItem { Label("Governor", systemImage: "gauge.with.dots.needle.33percent") }

                TasksView()
                    .tabItem { Label("Tasks", systemImage: "checklist") }

                SettingsView()
                    .tabItem { Label("Settings", systemImage: "slider.horizontal.3") }
            }
            .preferredColorScheme(.dark)
        }
    }
}
