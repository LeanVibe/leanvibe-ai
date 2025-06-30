import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
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