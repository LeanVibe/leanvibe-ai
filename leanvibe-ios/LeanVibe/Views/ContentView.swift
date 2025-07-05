import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct ContentView: View {
    @StateObject private var webSocketService = WebSocketService.shared
    @StateObject private var featureFlagManager = FeatureFlagManager.shared
    @State private var inputText = ""
    @State private var showingSettings = false
    @State private var showingCodeCompletion = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Connection Status Header
                connectionStatusHeader
                
                // Messages List
                messagesScrollView
                
                // Input Area
                inputSection
            }
            .navigationTitle("LeanVibe Agent")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    connectionButton
                }
                
                ToolbarItem(placement: .primaryAction) {
                    HStack {
                        if featureFlagManager.isFeatureEnabled(.codeCompletion) {
                            Button("Code Test") {
                                showingCodeCompletion = true
                            }
                            .font(.caption)
                        }
                        
                        settingsButton
                    }
                }
            }
            .sheet(isPresented: $showingSettings) {
                ConnectionSettingsView(webSocketService: webSocketService)
            }
            .sheet(isPresented: $showingCodeCompletion) {
                if featureFlagManager.isFeatureEnabled(.codeCompletion) {
                    CodeCompletionTestView(webSocketService: webSocketService)
                }
            }
            .onTapGesture {
                // Dismiss keyboard when tapping outside text field
                hideKeyboard()
            }
        }
    }
    
    private var connectionStatusHeader: some View {
        HStack {
            Circle()
                .fill(webSocketService.isConnected ? .green : .red)
                .frame(width: 12, height: 12)
            
            Text(webSocketService.connectionStatus)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Spacer()
            
            if let error = webSocketService.lastError {
                Button("⚠️") {
                    // Show error details
                }
                .foregroundColor(.red)
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
    }
    
    private var messagesScrollView: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    if webSocketService.messages.isEmpty {
                        emptyStateView
                    } else {
                        ForEach(webSocketService.messages) { message in
                            MessageBubble(message: message)
                                .id(message.id)
                        }
                    }
                }
                .padding()
            }
            .onTapGesture {
                // Dismiss keyboard when tapping on messages area
                hideKeyboard()
            }
            .onChange(of: webSocketService.messages.count) { _ in
                // Auto-scroll to bottom when new message arrives
                if let lastMessage = webSocketService.messages.last {
                    withAnimation(.easeOut(duration: 0.3)) {
                        proxy.scrollTo(lastMessage.id, anchor: .bottom)
                    }
                }
            }
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text("Welcome to LeanVibe")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Connect to your Mac agent to start coding assistance")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Try these commands:")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
                
                CommandSuggestion(command: "/status", description: "Check agent status")
                CommandSuggestion(command: "/list-files", description: "List current directory")
                CommandSuggestion(command: "/help", description: "Show all commands")
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
        }
        .padding()
    }
    
    private var inputSection: some View {
        VStack(spacing: 8) {
            // Quick command buttons
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    QuickCommandButton(title: "/status", action: { sendQuickCommand("/status") })
                    QuickCommandButton(title: "/list-files", action: { sendQuickCommand("/list-files") })
                    QuickCommandButton(title: "/current-dir", action: { sendQuickCommand("/current-dir") })
                    QuickCommandButton(title: "/help", action: { sendQuickCommand("/help") })
                }
                .padding(.horizontal)
            }
            
            // Text input
            HStack {
                TextField("Enter command or message...", text: $inputText, axis: .vertical)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .lineLimit(1...4)
                    .onSubmit {
                        sendMessage()
                    }
                
                Button(action: sendMessage) {
                    Image(systemName: "paperplane.fill")
                        .foregroundColor(.white)
                        .padding(8)
                        .background(inputText.isEmpty || !webSocketService.isConnected ? Color.gray : Color.blue)
                        .clipShape(Circle())
                }
                .disabled(inputText.isEmpty || !webSocketService.isConnected)
            }
            .padding(.horizontal)
            .padding(.bottom)
        }
    }
    
    private var connectionButton: some View {
        Button(webSocketService.isConnected ? "Disconnect" : "Connect") {
            if webSocketService.isConnected {
                webSocketService.disconnect()
            } else {
                webSocketService.connect()
            }
        }
    }
    
    private var settingsButton: some View {
        Button("Settings") {
            showingSettings = true
        }
    }
    
    private func sendMessage() {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        let commandType = inputText.hasPrefix("/") ? "command" : "message"
        webSocketService.sendMessage(inputText.trimmingCharacters(in: .whitespacesAndNewlines), type: commandType)
        
        inputText = ""
        // Dismiss keyboard after sending message
        hideKeyboard()
    }
    
    private func sendQuickCommand(_ command: String) {
        webSocketService.sendCommand(command)
    }
    
    /// Hide the keyboard by ending text editing
    private func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct CommandSuggestion: View {
    let command: String
    let description: String
    
    var body: some View {
        HStack {
            Text(command)
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(.blue)
            
            Text("- \(description)")
                .font(.caption)
                .foregroundColor(.secondary)
            
            Spacer()
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct QuickCommandButton: View {
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.blue.opacity(0.1))
                .foregroundColor(.blue)
                .cornerRadius(16)
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct MessageBubble: View {
    let message: AgentMessage
    
    var body: some View {
        HStack {
            if message.isFromUser { Spacer(minLength: 50) }
            
            VStack(alignment: message.isFromUser ? .trailing : .leading, spacing: 4) {
                HStack {
                    if !message.isFromUser {
                        messageTypeIcon
                    }
                    
                    Text(message.content)
                        .padding()
                        .background(messageBackgroundColor)
                        .foregroundColor(messageTextColor)
                        .cornerRadius(16)
                        .textSelection(.enabled)
                    
                    if message.isFromUser {
                        messageTypeIcon
                    }
                }
                
                Text(DateFormatter.shortTime.string(from: message.timestamp))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            if !message.isFromUser { Spacer(minLength: 50) }
        }
    }
    
    private var messageTypeIcon: some View {
        Image(systemName: message.isFromUser ? "person.circle" : "brain.head.profile")
            .foregroundColor(.secondary)
    }
    
    private var messageBackgroundColor: Color {
        if message.isFromUser {
            return .blue
        } else {
            return Color(.systemGray5)
        }
    }
    
    private var messageTextColor: Color {
        if message.isFromUser {
            return .white
        } else {
            return .primary
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
struct ConnectionSettingsView: View {
    @ObservedObject var webSocketService: WebSocketService
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                Section("Connection") {
                    HStack {
                        Text("Status")
                        Spacer()
                        Text(webSocketService.connectionStatus)
                            .foregroundColor(.secondary)
                    }
                    
                    if let error = webSocketService.lastError {
                        HStack {
                            Text("Last Error")
                            Spacer()
                            Text(error)
                                .foregroundColor(.red)
                                .font(.caption)
                        }
                    }
                }
                
                Section("Actions") {
                    Button("Clear Messages") {
                        webSocketService.clearMessages()
                    }
                    
                    if webSocketService.isConnected {
                        Button("Disconnect") {
                            webSocketService.disconnect()
                        }
                        .foregroundColor(.red)
                    } else {
                        Button("Connect") {
                            webSocketService.connect()
                        }
                    }
                }
                
                Section("Information") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("0.1.0")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Messages")
                        Spacer()
                        Text("\(webSocketService.messages.count)")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

extension DateFormatter {
    static let shortTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .short
        return formatter
    }()
}

#if DEBUG
@available(iOS 18.0, macOS 14.0, *)
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
#endif