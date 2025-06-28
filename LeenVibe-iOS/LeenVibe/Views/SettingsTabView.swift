import SwiftUI

struct SettingsTabView: View {
    @ObservedObject var webSocketService: WebSocketService
    
    var body: some View {
        // Use the existing SettingsView which already has all the settings functionality
        SettingsView(webSocketService: webSocketService)
    }
}

#Preview {
    SettingsTabView(webSocketService: WebSocketService())
}