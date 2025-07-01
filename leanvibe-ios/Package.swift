// swift-tools-version:6.2
import PackageDescription

let package = Package(
  name: "LeanVibe",
  platforms: [
    .iOS(.v17)
  ],
  products: [
    .executable(
      name: "LeanVibe",
      targets: ["LeanVibe"])
  ],
  dependencies: [
    .package(url: "https://github.com/daltoniam/Starscream.git", from: "4.0.0")
  ],
  targets: [
    .executableTarget(
      name: "LeanVibe",
      dependencies: ["Starscream"],
      path: "LeanVibe",
      resources: [
        .process("Resources")
      ]
    ),
    .testTarget(
      name: "LeanVibeTests",
      dependencies: ["LeanVibe"],
      path: "LeanVibeTests"
    )
  ]
)
