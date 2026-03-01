// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "RheaKit",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
    ],
    products: [
        .library(name: "RheaKit", targets: ["RheaKit"]),
    ],
    dependencies: [
        .package(url: "https://github.com/groue/GRDB.swift", from: "7.0.0"),
        .package(url: "https://github.com/apple/swift-collections", from: "1.1.0"),
        .package(url: "https://github.com/kishikawakatsumi/KeychainAccess", from: "4.2.2"),
        .package(url: "https://github.com/gonzalezreal/swift-markdown-ui", from: "2.4.0"),
        .package(url: "https://github.com/daltoniam/Starscream", from: "4.0.8"),
        .package(url: "https://github.com/serg-alexv/Pow", from: "1.0.0"),
    ],
    targets: [
        .target(
            name: "RheaKit",
            dependencies: [
                .product(name: "GRDB", package: "GRDB.swift"),
                .product(name: "Collections", package: "swift-collections"),
                .product(name: "KeychainAccess", package: "KeychainAccess"),
                .product(name: "MarkdownUI", package: "swift-markdown-ui"),
                .product(name: "Starscream", package: "Starscream"),
                .product(name: "Pow", package: "Pow"),
            ],
            resources: [
                .copy("Resources/3Dmol-min.js"),
            ]
        ),
    ]
)
