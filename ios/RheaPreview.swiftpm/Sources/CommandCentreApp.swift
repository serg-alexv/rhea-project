#if os(macOS)
import SwiftUI
import RheaKit

@main
struct CommandCentreApp: App {
    @StateObject private var auth = AuthManager.shared

    init() {
        AppConfig.migrateStaleDefaults()
    }

    var body: some Scene {
        WindowGroup("Rhea Command Centre") {
            CommandCentreLayout()
                .frame(minWidth: 900, minHeight: 600)
                .preferredColorScheme(.dark)
                .environmentObject(auth)
        }
        .defaultSize(width: 1200, height: 800)
        .commands {
            CommandGroup(replacing: .newItem) {}
            CommandMenu("Panels") {
                Button("Radio") { NotificationCenter.default.post(name: .ccNavigate, object: "radio") }
                    .keyboardShortcut("1", modifiers: .command)
                Button("Tribunal") { NotificationCenter.default.post(name: .ccNavigate, object: "tribunal") }
                    .keyboardShortcut("2", modifiers: .command)
                Button("Governor") { NotificationCenter.default.post(name: .ccNavigate, object: "governor") }
                    .keyboardShortcut("3", modifiers: .command)
                Button("Tasks") { NotificationCenter.default.post(name: .ccNavigate, object: "tasks") }
                    .keyboardShortcut("4", modifiers: .command)
                Button("History") { NotificationCenter.default.post(name: .ccNavigate, object: "history") }
                    .keyboardShortcut("5", modifiers: .command)
                Button("Office") { NotificationCenter.default.post(name: .ccNavigate, object: "office") }
                    .keyboardShortcut("6", modifiers: .command)
            }
        }

        MenuBarExtra("Rhea", systemImage: "antenna.radiowaves.left.and.right") {
            MenuBarView()
        }
    }
}

extension Notification.Name {
    static let ccNavigate = Notification.Name("ccNavigate")
}
#endif
