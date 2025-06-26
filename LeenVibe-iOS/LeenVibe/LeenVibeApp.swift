import SwiftUI

@main
struct LeenVibeApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.light) // Force light mode for MVP
        }
    }
}