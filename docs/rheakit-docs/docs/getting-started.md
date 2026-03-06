---
sidebar_position: 2
title: Getting Started
---

# Getting Started

This guide walks you through adding RheaKit to your SwiftUI app and rendering your first component.

## 1. Add the Package

In your app's `Package.swift`, add RheaKit as a local or remote dependency:

```swift
// Package.swift
let package = Package(
    name: "MyApp",
    platforms: [.iOS(.v17), .macOS(.v14)],
    dependencies: [
        .package(path: "../packages/RheaKit"),
    ],
    targets: [
        .executableTarget(
            name: "MyApp",
            dependencies: ["RheaKit"]
        ),
    ]
)
```

## 2. Configure the API Endpoint

RheaKit connects to a Rhea backend server. By default it uses `localhost:8400` in the simulator and the production Fly.io URL on device. You can override this with `AppConfig`:

```swift
import RheaKit

// The default is automatic:
//   Simulator → http://localhost:8400
//   Device    → https://rhea-tribunal.fly.dev

// To force a custom endpoint, set UserDefaults:
UserDefaults.standard.set("https://your-server.example.com", forKey: "apiBaseURL")
```

Call `AppConfig.migrateStaleDefaults()` at app launch to auto-migrate old localhost URLs when running on a physical device.

## 3. Set Up Authentication

RheaKit uses `AuthManager.shared` for JWT-based auth. Users can sign in or skip:

```swift
import RheaKit

struct ContentView: View {
    @ObservedObject var auth = AuthManager.shared

    var body: some View {
        if auth.isLoggedIn || auth.didSkipAuth {
            MainTabView()
        } else {
            AuthView()
        }
    }
}
```

`AuthView` provides a complete sign-in/sign-up flow with "Sign in with Apple" support and a "Skip for now" option.

## 4. Display Your First View

Every RheaKit view is a self-contained `NavigationStack`. Drop any view into a `TabView`:

```swift
import RheaKit

struct MainTabView: View {
    var body: some View {
        TabView {
            TeamChatView()
                .tabItem { Label("Radio", systemImage: "antenna.radiowaves.left.and.right") }

            GovernorView()
                .tabItem { Label("Governor", systemImage: "gauge.with.dots.needle.67percent") }

            TasksView()
                .tabItem { Label("Tasks", systemImage: "checklist") }

            BioRendererView()
                .tabItem { Label("Bio", systemImage: "atom") }

            SettingsView()
                .tabItem { Label("Settings", systemImage: "gear") }
        }
        .preferredColorScheme(.dark)
    }
}
```

## 5. Apply the Theme

Use `RheaTheme` colors and the `.glassCard()` modifier in your own views:

```swift
import RheaKit

struct MyDashboard: View {
    var body: some View {
        VStack(spacing: 12) {
            Text("Status: Online")
                .foregroundStyle(RheaTheme.green)

            Text("Tokens today: 42K")
                .foregroundStyle(RheaTheme.accent)
        }
        .glassCard()
        .background(RheaTheme.bg)
    }
}
```

## 6. Start the Store

For views that depend on shared state (agent list, health, proof count), start the polling loop:

```swift
@main
struct MyApp: App {
    init() {
        AppConfig.migrateStaleDefaults()
        RheaStore.shared.startPolling()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

`RheaStore` polls `/agents/status` and `/health` every 5 seconds. On connection recovery it automatically refreshes SQL-backed data (proofs, history, radio, office messages).

## Next Steps

- [Design System →](./design-system) — Colors, typography, GlassCard
- [Components →](./category/components) — Full reference for every view
- [Architecture →](./architecture) — How the data flows
