import SwiftUI

@main
public struct LeenVibeApp: App {
    public init() {}
    
    public var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.light) // Force light mode for MVP
        }
    }
}