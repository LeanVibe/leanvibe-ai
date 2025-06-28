import SwiftUI

struct ChatView: View {
    @ObservedObject var webSocketService: WebSocketService
    
    var body: some View {
        // Use the existing ContentView which already has all the chat functionality
        ContentView()
            .environmentObject(webSocketService)
    }
}

#Preview {
    ChatView(webSocketService: WebSocketService())
}