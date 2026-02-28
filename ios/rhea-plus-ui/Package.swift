// swift-tools-version: 5.9
// RheaPlusUI — Rhea's curated SwiftUI component library
// Forked from MIT/Apache-2.0 sources, maintained independently.

import PackageDescription

let package = Package(
    name: "RheaPlusUI",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "RheaPlusUI", targets: ["RheaPlusUI"])
    ],
    dependencies: [
        // Foundation — missing SwiftUI APIs (MIT, 7989⭐)
        .package(url: "https://github.com/serg-alexv/SwiftUIX", from: "0.2.2"),
        // Animations & effects (MIT, 4236⭐)
        .package(url: "https://github.com/serg-alexv/Pow", from: "1.0.0"),
        // Chat UI framework (MIT, 1696⭐)
        .package(url: "https://github.com/serg-alexv/Chat", from: "2.0.0"),
        // Toasts & popups (MIT, 4010⭐)
        .package(url: "https://github.com/serg-alexv/PopupView", from: "3.0.0"),
        // Animated tab bar (MIT, 529⭐)
        .package(url: "https://github.com/serg-alexv/AnimatedTabBar", from: "0.0.1"),
        // FAB menu (MIT, 1256⭐)
        .package(url: "https://github.com/serg-alexv/FloatingButton", from: "1.2.0"),
        // Native alerts (MIT, 2620⭐)
        .package(url: "https://github.com/serg-alexv/AlertKit", from: "5.1.0"),
        // Image loading + caching (MIT, 24282⭐)
        .package(url: "https://github.com/serg-alexv/Kingfisher", from: "8.0.0"),
    ],
    targets: [
        .target(
            name: "RheaPlusUI",
            dependencies: [
                "SwiftUIX",
                "Pow",
                .product(name: "ExyteChat", package: "Chat"),
                "PopupView",
                "AnimatedTabBar",
                "FloatingButton",
                "AlertKit",
                "Kingfisher",
            ],
            path: "Sources"
        )
    ]
)
