// swift-tools-version: 5.9
import PackageDescription
import AppleProductTypes

let package = Package(
    name: "RheaPreview",
    platforms: [.iOS("17.0")],
    products: [
        .iOSApplication(
            name: "RheaPreview",
            targets: ["RheaPreview"],
            bundleIdentifier: "com.rhea.preview",
            displayVersion: "1.0",
            bundleVersion: "1",
            supportedDeviceFamilies: [.phone, .pad],
            supportedInterfaceOrientations: [
                .portrait,
                .landscapeRight,
                .landscapeLeft
            ]
        )
    ],
    dependencies: [
        // Rhea Plus UI stack — all forked to serg-alexv/* (MIT/Apache-2.0)
        .package(url: "https://github.com/serg-alexv/Pow", from: "1.0.0"),
        .package(url: "https://github.com/serg-alexv/SwiftUIX", from: "0.2.2"),
        .package(url: "https://github.com/serg-alexv/Chat", from: "2.0.0"),
        .package(url: "https://github.com/serg-alexv/PopupView", from: "3.0.0"),
        .package(url: "https://github.com/serg-alexv/AnimatedTabBar", from: "0.0.1"),
        .package(url: "https://github.com/serg-alexv/FloatingButton", from: "1.2.0"),
        .package(url: "https://github.com/serg-alexv/AlertKit", from: "5.1.0"),
        // Kingfisher comes transitively via Chat — no duplicate needed
    ],
    targets: [
        .executableTarget(
            name: "RheaPreview",
            dependencies: [
                "Pow",
                "SwiftUIX",
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
