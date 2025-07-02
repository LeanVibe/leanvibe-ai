import Foundation
import Starscream

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class WebSocketService: ObservableObject, WebSocketDelegate {
    @Published var isConnected = false
    @Published var messages: [AgentMessage] = []
    @Published var connectionStatus = "Disconnected"
    @Published var lastError: String?
    
    // MARK: - Singleton Pattern
    static let shared = WebSocketService()
    
    private var socket: WebSocket?
    private let clientId = "ios-client-\(UUID().uuidString.prefix(8))"
    private let storageManager = ConnectionStorageManager()
    private var qrConnectionTask: Task<Void, Error>?
    
    init() {
        // Try to auto-connect with stored settings on init
        autoConnectIfAvailable()
    }
    
    // MARK: - Connection Management
    
    private func autoConnectIfAvailable() {
        // In simulator mode, always try to connect to localhost first
        if isRunningInSimulator() {
            if let defaultConnection = createDefaultConnection() {
                connectionStatus = "Auto-connecting to simulator backend..."
                print("🤖 Simulator mode: bypassing QR and connecting to \(defaultConnection.host):\(defaultConnection.port)")
                
                // Save this connection for future use
                storageManager.saveConnection(defaultConnection)
                
                connectWithSettings(defaultConnection)
                return
            }
        }
        
        guard let storedConnection = storageManager.currentConnection else {
            // Try default configuration for development
            if let defaultConnection = createDefaultConnection() {
                connectionStatus = "Connecting to \(defaultConnection.displayName)..."
                connectWithSettings(defaultConnection)
            } else {
                connectionStatus = "No saved connection - Scan QR to connect"
            }
            return
        }
        
        connectionStatus = "Connecting to \(storedConnection.displayName)..."
        connectWithSettings(storedConnection)
    }
    
    private func createDefaultConnection() -> ConnectionSettings? {
        let config = AppConfiguration.shared
        
        // Always auto-connect in debug builds or when explicitly configured
        guard config.isLoggingEnabled else { return nil }
        
        // Detect if running in simulator
        let isSimulator = isRunningInSimulator()
        
        do {
            try config.validateConfiguration()
            
            // Parse URL to extract host and port
            let url = URL(string: config.apiBaseURL)
            var host = url?.host ?? "localhost"
            var port = url?.port ?? 8001
            
            // For simulator, try multiple common development ports
            if isSimulator {
                host = "localhost"
                // Try port 8002 first (since 8001 might be used by OrbStack), then 8001
                port = 8002
                print("🤖 Simulator detected - auto-connecting to \(host):\(port)")
            }
            
            return ConnectionSettings(
                host: host,
                port: port,
                websocketPath: "/ws",
                serverName: isSimulator ? "Simulator Development" : "Local Development",
                network: isSimulator ? "simulator" : "development"
            )
        } catch {
            print("⚠️ Cannot create default connection: \(error)")
            return nil
        }
    }
    
    /// Detect if the app is running in iOS Simulator
    private func isRunningInSimulator() -> Bool {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }
    
    private func connectWithSettings(_ settings: ConnectionSettings) {
        let url = "\(settings.websocketURL)/\(clientId)"
        setupWebSocketWithURL(url)
        connect()
    }
    
    func connect() {
        connectionStatus = "Connecting..."
        socket?.connect()
    }
    
    func disconnect() {
        socket?.disconnect()
        isConnected = false
        connectionStatus = "Disconnected"
        lastError = nil
    }
    
    func sendMessage(_ content: String, type: String = "message") {
        guard isConnected, let socket = socket else {
            lastError = "Not connected"
            return
        }
        
        let message = WebSocketMessage(
            type: type,
            content: content,
            timestamp: ISO8601DateFormatter().string(from: Date()),
            clientId: clientId,
            priority: .normal
        )
        
        do {
            let data = try JSONEncoder().encode(message)
            let string = String(data: data, encoding: .utf8) ?? ""
            
            socket.write(string: string)
            
            // Add user message to UI
            let userMessage = AgentMessage(
                content: content,
                isFromUser: true,
                type: type == "command" ? .command : .message
            )
            messages.append(userMessage)
            
        } catch {
            lastError = "Encoding error: \(error.localizedDescription)"
        }
    }
    
    func sendCommand(_ command: String, type: String = "command") {
        sendMessage(command, type: type)
    }
    
    func clearMessages() {
        messages.removeAll()
    }
    
    // MARK: - Connection Management
    
    var connectionStorage: ConnectionStorageManager {
        return storageManager
    }
    
    func connectToSavedConnection() {
        autoConnectIfAvailable()
    }
    
    func hasStoredConnection() -> Bool {
        return storageManager.hasValidConnection()
    }
    
    func getCurrentConnectionInfo() -> ConnectionSettings? {
        return storageManager.currentConnection
    }
    
    // MARK: - QR Code Connection
    
    func connectWithQRCode(_ qrData: String) async throws {
        guard let config = parseQRConfig(qrData) else {
            throw NSError(domain: "WebSocketService", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid QR code format"])
        }
        
        // Create connection settings from QR config
        let connectionSettings = ConnectionSettings(from: config)
        
        // Save the connection settings for future use
        storageManager.saveConnection(connectionSettings)
        
        // Disconnect if already connected
        if isConnected {
            disconnect()
        }
        
        // Update status and connect
        connectionStatus = "Connecting to \(connectionSettings.displayName)..."
        
        // Connect using the new settings with proper timeout and cleanup
        // Cancel any existing connection task
        qrConnectionTask?.cancel()
        
        // Use TaskGroup to handle timeout and connection attempt safely
        return try await withThrowingTaskGroup(of: Void.self) { group in
            // Add connection attempt task
            group.addTask { [weak self] in
                try await self?.connectWithSettingsAsync(connectionSettings)
            }
            
            // Add timeout task
            group.addTask {
                try await Task.sleep(nanoseconds: 10_000_000_000) // 10 seconds
                throw NSError(
                    domain: "WebSocketService", 
                    code: 4, 
                    userInfo: [NSLocalizedDescriptionKey: "Connection timeout after 10 seconds"]
                )
            }
            
            // Wait for first task to complete, then cancel the rest
            try await group.next()
            group.cancelAll()
        }
    }
    
    // Convert the existing connectWithSettings to async for TaskGroup usage
    private func connectWithSettingsAsync(_ connectionSettings: ConnectionSettings) async throws {
        connectWithSettings(connectionSettings)
        
        // Wait for connection to be established or fail
        // This approach uses polling instead of continuation storage
        var attempts = 0
        let maxAttempts = 100 // 10 seconds with 100ms intervals
        
        while attempts < maxAttempts {
            try await Task.sleep(nanoseconds: 100_000_000) // 100ms
            
            if isConnected {
                return // Success
            }
            
            // Check if we got an error
            if let error = lastError {
                throw NSError(
                    domain: "WebSocketService",
                    code: 6,
                    userInfo: [NSLocalizedDescriptionKey: error]
                )
            }
            
            attempts += 1
        }
        
        // Timeout after polling
        throw NSError(
            domain: "WebSocketService",
            code: 7,
            userInfo: [NSLocalizedDescriptionKey: "Connection attempt timeout"]
        )
    }
    
    private func parseQRConfig(_ qrData: String) -> ServerConfig? {
        do {
            let data = qrData.data(using: .utf8) ?? Data()
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            
            guard let leanvibe = json?["leanvibe"] as? [String: Any],
                  let server = leanvibe["server"] as? [String: Any],
                  let host = server["host"] as? String,
                  let port = server["port"] as? Int,
                  let websocketPath = server["websocket_path"] as? String else {
                return nil
            }
            
            let metadata = leanvibe["metadata"] as? [String: Any]
            let serverName = metadata?["server_name"] as? String
            let network = metadata?["network"] as? String
            
            return ServerConfig(
                host: host,
                port: port,
                websocketPath: websocketPath,
                serverName: serverName,
                network: network
            )
        } catch {
            print("Error parsing QR config: \(error)")
            return nil
        }
    }
    
    private func setupWebSocketWithURL(_ url: String) {
        guard let wsURL = URL(string: url) else {
            connectionStatus = "Invalid URL"
            return
        }
        
        var request = URLRequest(url: wsURL)
        request.timeoutInterval = 10
        
        socket = WebSocket(request: request)
        socket?.delegate = self
    }
    
    // MARK: - WebSocketDelegate
    
    nonisolated func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        // Create a copy of the event data that we need
        switch event {
        case .connected:
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.isConnected = true
                self.connectionStatus = "Connected"
                self.lastError = nil
                
                // Connection successful - the TaskGroup will handle completion
                
                // Send initial status request
                self.sendCommand("/status", type: "command")
            }
            
        case .disconnected(let reason, _):
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.isConnected = false
                self.connectionStatus = "Disconnected"
                
                // Connection failed - error will be captured by TaskGroup polling
            }
            
        case .text(let string):
            Task { @MainActor [weak self] in
                self?.handleReceivedMessage(string)
            }
            
        case .binary(let data):
            if let text = String(data: data, encoding: .utf8) {
                Task { @MainActor [weak self] in
                    self?.handleReceivedMessage(text)
                }
            }
            
        case .error(let error):
            let errorMessage = error?.localizedDescription ?? "Unknown WebSocket error"
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                self.lastError = errorMessage
                self.connectionStatus = "Error: \(errorMessage)"
                
                // Error will be captured by TaskGroup polling
            }
            
        case .cancelled, .peerClosed:
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.isConnected = false
                self.connectionStatus = "Connection closed"
                
                // Connection cancelled - error will be captured by TaskGroup polling
            }
            
        default:
            break
        }
    }
    
    private func handleReceivedMessage(_ text: String) {
        guard let data = text.data(using: .utf8) else {
            handleFallbackMessage(text)
            return
        }
        
        // Check if this might be a code completion response by looking for key fields
        if text.contains("\"intent\"") && text.contains("\"confidence\"") && text.contains("\"suggestions\"") {
            // This looks like a code completion response, forward it to interested parties
            DispatchQueue.main.async {
                NotificationCenter.default.post(
                    name: Notification.Name("codeCompletionResponse"), 
                    object: text
                )
            }
            return
        }
        
        // Try AgentResponse (existing behavior)
        do {
            let response = try JSONDecoder().decode(AgentResponse.self, from: data)
            
            let messageType: AgentMessage.MessageType = {
                switch response.status {
                case "error":
                    return .error
                case "success":
                    return response.type == "agent_status" ? .status : .response
                default:
                    return .response
                }
            }()
            
            let agentMessage = AgentMessage(
                content: formatResponseMessage(response),
                isFromUser: false,
                type: messageType
            )
            
            messages.append(agentMessage)
            
        } catch {
            handleFallbackMessage(text)
        }
    }
    
    private func handleFallbackMessage(_ text: String) {
        // Fallback for non-JSON responses
        let agentMessage = AgentMessage(
            content: text,
            isFromUser: false,
            type: .response
        )
        messages.append(agentMessage)
    }
    
    private func formatResponseMessage(_ response: AgentResponse) -> String {
        var output = response.message
        
        // Add processing time if available
        if let processingTime = response.processingTime {
            output += "\n\n⏱️ Processed in \(String(format: "%.3f", processingTime))s"
        }
        
        // Add confidence score if available
        if let confidence = response.confidence {
            let confidencePercent = Int(confidence * 100)
            let confidenceEmoji = confidence >= 0.8 ? "🟢" : confidence >= 0.5 ? "🟡" : "🔴"
            output += "\n\n\(confidenceEmoji) Confidence: \(confidencePercent)%"
            
            // Add warning for low confidence
            if confidence < 0.5 {
                output += "\n⚠️ Low confidence - consider manual review"
            }
        }
        
        // Add model information if available
        if let model = response.model {
            output += "\n\n🤖 Model: \(model)"
        }
        
        // Format specific response types
        if let data = response.data {
            if let files = data.files, let directories = data.directories {
                output += "\n\n📁 Directories: \(directories.count)"
                output += "\n📄 Files: \(files.count)"
                
                if directories.count > 0 {
                    output += "\n\nDirectories:"
                    for dir in directories.prefix(5) {
                        output += "\n  📁 \(dir.name)"
                    }
                    if directories.count > 5 {
                        output += "\n  ... and \(directories.count - 5) more"
                    }
                }
                
                if files.count > 0 {
                    output += "\n\nFiles:"
                    for file in files.prefix(5) {
                        let sizeStr = file.size.map { formatFileSize($0) } ?? ""
                        output += "\n  📄 \(file.name) \(sizeStr)"
                    }
                    if files.count > 5 {
                        output += "\n  ... and \(files.count - 5) more"
                    }
                }
            }
            
            if let currentDir = data.currentDirectory {
                output += "\n\n📍 \(currentDir)"
            }
        }
        
        return output
    }
    
    private func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB]
        formatter.countStyle = .file
        return "(\(formatter.string(fromByteCount: Int64(bytes))))"
    }
}

