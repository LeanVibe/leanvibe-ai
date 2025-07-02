import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct SettingsTabView: View {
    @ObservedObject var webSocketService: WebSocketService
    
    var body: some View {
        // Use the existing SettingsView which already has all the settings functionality
        SettingsView(webSocketService: webSocketService)
    }
}

#Preview {
    SettingsTabView(webSocketService: WebSocketService.shared)
}