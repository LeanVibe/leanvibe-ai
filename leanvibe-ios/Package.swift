// swift-tools-version:6.2
import PackageDescription

let package = Package(
  name: "LeenVibe",
  platforms: [
    .iOS(.v16)
  ],
  products: [
    .executable(
      name: "LeenVibe",
      targets: ["LeenVibe"])
  ],
  dependencies: [
    .package(url: "https://github.com/daltoniam/Starscream.git", from: "4.0.0")
  ],
  targets: [
    .executableTarget(
      name: "LeenVibe",
      dependencies: ["Starscream"],
      path: "LeenVibe",
      resources: [
        .process("Resources")
      ]
    )
  ]
)
