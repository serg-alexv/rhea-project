// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "RheaPreview",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "RheaPreview", targets: ["RheaPreview"])
    ],
    targets: [
        .target(name: "RheaPreview", path: "Sources")
    ]
)
