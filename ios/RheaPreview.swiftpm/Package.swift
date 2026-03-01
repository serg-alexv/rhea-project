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
        .package(path: "../../packages/RheaKit"),
        .package(url: "https://github.com/serg-alexv/AnimatedTabBar", from: "0.0.1"),
    ],
    targets: [
        .executableTarget(
            name: "RheaPreview",
            dependencies: [
                "RheaKit",
                "AnimatedTabBar",
            ],
            path: "Sources"
        )
    ]
)
