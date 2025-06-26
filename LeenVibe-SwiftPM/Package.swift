// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "LeenVibe",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "LeenVibe",
            targets: ["LeenVibe"]
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/daltoniam/Starscream.git", from: "4.0.0"),
    ],
    targets: [
        .executableTarget(
            name: "LeenVibe",
            dependencies: [
                "Starscream",
            ],
            resources: [
                .process("Resources")
            ]
        ),
        .testTarget(
            name: "LeenVibeTests",
            dependencies: ["LeenVibe"]
        ),
    ]
)