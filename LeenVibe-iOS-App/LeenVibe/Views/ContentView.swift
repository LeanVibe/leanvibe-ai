import SwiftUI

struct ContentView: View {
    @StateObject private var webSocketService = WebSocketService()
    @State private var inputText = ""
    @State private var showingSettings = false
    @State private var showingQRScanner = false
    @Environment(\.scenePhase) private var scenePhase
    
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
            .navigationTitle("LeenVibe Agent")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                #if os(iOS)
                ToolbarItem(placement: .navigationBarLeading) {
                    connectionButton
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    settingsButton
                }
                #else
                ToolbarItem(placement: .primaryAction) {
                    connectionButton
                }
                ToolbarItem(placement: .secondaryAction) {
                    settingsButton
                }
                #endif
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView(webSocketService: webSocketService)
            }
            .sheet(isPresented: $showingQRScanner) {
                QRScannerView(isPresented: $showingQRScanner, webSocketService: webSocketService)
            }
            .onChange(of: scenePhase) { newPhase in
                switch newPhase {
                case .active:
                    // App became active - try to reconnect if we have stored settings and aren't connected
                    if !webSocketService.isConnected && webSocketService.hasStoredConnection() {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                            webSocketService.connectToSavedConnection()
                        }
                    }
                case .background:
                    // App went to background - optionally disconnect to save resources
                    // We'll keep connection alive for real-time notifications
                    break
                case .inactive:
                    // App became inactive (e.g., during transitions)
                    break
                @unknown default:
                    break
                }
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
        .background(Color.gray.opacity(0.1))
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
            
            Text("Welcome to LeenVibe")
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
                
                CommandSuggestion(command: "/status", description: "Check agent status and health")
                CommandSuggestion(command: "/list-files", description: "List current directory")
                CommandSuggestion(command: "/analyze-file <path>", description: "Analyze code with AI")
                CommandSuggestion(command: "/help", description: "Show all commands")
            }
            .padding()
            .background(Color.gray.opacity(0.1))
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
                    QuickCommandButton(title: "/analyze-file app/main.py", action: { sendQuickCommand("/analyze-file app/main.py") })
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
        Button(action: {
            if webSocketService.isConnected {
                webSocketService.disconnect()
            } else {
                // If we have a stored connection, try to reconnect
                if webSocketService.hasStoredConnection() {
                    webSocketService.connectToSavedConnection()
                } else {
                    // No stored connection, show QR scanner
                    showingQRScanner = true
                }
            }
        }) {
            HStack {
                if webSocketService.isConnected {
                    Image(systemName: "wifi")
                    Text("Disconnect")
                } else if webSocketService.hasStoredConnection() {
                    Image(systemName: "arrow.clockwise")
                    Text("Reconnect")
                } else {
                    Image(systemName: "qrcode.viewfinder")
                    Text("Scan QR")
                }
            }
        }
        .contextMenu {
            if webSocketService.hasStoredConnection() {
                Button(action: {
                    showingQRScanner = true
                }) {
                    Label("Scan New QR Code", systemImage: "qrcode.viewfinder")
                }
                
                if let connection = webSocketService.getCurrentConnectionInfo() {
                    Button(action: {}) {
                        Label("Current: \(connection.displayName)", systemImage: "info.circle")
                    }
                    .disabled(true)
                }
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
    }
    
    private func sendQuickCommand(_ command: String) {
        webSocketService.sendCommand(command)
    }
}

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

struct MessageBubble: View {
    let message: AgentMessage
    
    init(message: AgentMessage) {
        self.message = message
    }
    
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
        Image(systemName: iconName)
            .font(.caption)
            .foregroundColor(iconColor)
    }
    
    private var iconName: String {
        switch message.type {
        case .command:
            return "terminal"
        case .error:
            return "exclamationmark.triangle"
        case .status:
            return "checkmark.circle"
        case .response:
            return "brain.head.profile"
        case .message:
            return message.isFromUser ? "person" : "brain.head.profile"
        }
    }
    
    private var iconColor: Color {
        switch message.type {
        case .error:
            return .red
        case .status:
            return .green
        case .command:
            return .blue
        default:
            return .secondary
        }
    }
    
    private var messageBackgroundColor: Color {
        if message.isFromUser {
            return .blue
        } else {
            switch message.type {
            case .error:
                return .red.opacity(0.1)
            case .status:
                return .green.opacity(0.1)
            default:
                return Color.gray.opacity(0.1)
            }
        }
    }
    
    private var messageTextColor: Color {
        if message.isFromUser {
            return .white
        } else {
            switch message.type {
            case .error:
                return .red
            default:
                return .primary
            }
        }
    }
}

struct SettingsView: View {
    @ObservedObject var webSocketService: WebSocketService
    @Environment(\.dismiss) private var dismiss
    
    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
    }
    
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
                    
                    if let connection = webSocketService.getCurrentConnectionInfo() {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text("Current Server")
                                Spacer()
                                Text(connection.displayName)
                                    .foregroundColor(.secondary)
                            }
                            
                            HStack {
                                Text("Address")
                                Spacer()
                                Text("\(connection.host):\(connection.port)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            
                            if let network = connection.network {
                                HStack {
                                    Text("Network")
                                    Spacer()
                                    Text(network)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                            
                            HStack {
                                Text("Last Connected")
                                Spacer()
                                Text(connection.lastConnected, style: .relative)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
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
                
                Section("Saved Connections") {
                    if webSocketService.connectionStorage.savedConnections.isEmpty {
                        Text("No saved connections")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    } else {
                        ForEach(webSocketService.connectionStorage.savedConnections.indices, id: \.self) { index in
                            let connection = webSocketService.connectionStorage.savedConnections[index]
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    VStack(alignment: .leading) {
                                        Text(connection.displayName)
                                            .font(.headline)
                                        Text("\(connection.host):\(connection.port)")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                    Spacer()
                                    if connection.host == webSocketService.getCurrentConnectionInfo()?.host &&
                                       connection.port == webSocketService.getCurrentConnectionInfo()?.port {
                                        Text("Current")
                                            .font(.caption)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 2)
                                            .background(Color.blue.opacity(0.2))
                                            .foregroundColor(.blue)
                                            .cornerRadius(4)
                                    }
                                }
                                
                                Text("Last used: \(connection.lastConnected, style: .relative)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .onTapGesture {
                                let settings = ConnectionSettings(
                                    host: connection.host,
                                    port: connection.port,
                                    websocketPath: connection.websocketPath,
                                    serverName: connection.serverName,
                                    network: connection.network
                                )
                                webSocketService.connectionStorage.setCurrentConnection(settings)
                                if !webSocketService.isConnected {
                                    webSocketService.connectToSavedConnection()
                                }
                            }
                            .swipeActions(edge: .trailing) {
                                Button("Delete", role: .destructive) {
                                    webSocketService.connectionStorage.removeConnection(connection)
                                }
                            }
                        }
                    }
                }
                
                Section("Actions") {
                    Button("Clear Messages") {
                        webSocketService.clearMessages()
                    }
                    
                    if webSocketService.hasStoredConnection() {
                        if webSocketService.isConnected {
                            Button("Disconnect") {
                                webSocketService.disconnect()
                            }
                            .foregroundColor(.red)
                        } else {
                            Button("Connect to Saved Server") {
                                webSocketService.connectToSavedConnection()
                            }
                        }
                    }
                    
                    if !webSocketService.connectionStorage.savedConnections.isEmpty {
                        Button("Clear All Saved Connections") {
                            webSocketService.connectionStorage.clearAllConnections()
                        }
                        .foregroundColor(.red)
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
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                #if os(iOS)
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
                #else
                ToolbarItem(placement: .primaryAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
                #endif
            }
        }
    }
}

extension DateFormatter {
    static let shortTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter
    }()
}

#Preview {
    ContentView()
}
