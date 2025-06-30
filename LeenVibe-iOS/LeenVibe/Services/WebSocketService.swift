import Foundation
import Starscream

@available(iOS 13.0, macOS 10.15, *)
@MainActor
class WebSocketService: ObservableObject, WebSocketDelegate {
    @Published var isConnected = false
    @Published var messages: [AgentMessage] = []
    @Published var connectionStatus = "Disconnected"
    @Published var lastError: String?
    
    private var socket: WebSocket?
    private let clientId = "ios-client-\(UUID().uuidString.prefix(8))"
    private let storageManager = ConnectionStorageManager()
    private var qrConnectionContinuation: CheckedContinuation<Void, Error>?
    private var qrConnectionTimeoutTask: Task<Void, Never>?
    
    init() {
        // Try to auto-connect with stored settings on init
        autoConnectIfAvailable()
    }
    
    // MARK: - Connection Management
    
    private func autoConnectIfAvailable() {
        guard let storedConnection = storageManager.currentConnection else {
            connectionStatus = "No saved connection - Scan QR to connect"
            return
        }
        
        connectionStatus = "Connecting to \(storedConnection.displayName)..."
        connectWithSettings(storedConnection)
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
        return try await withCheckedThrowingContinuation { continuation in
            // Clean up any existing continuation/timeout
            self.cleanupQRConnection(resumeWith: nil)
            
            // Store new continuation
            self.qrConnectionContinuation = continuation
            
            // Set up timeout task (10 seconds)
            self.qrConnectionTimeoutTask = Task { [weak self] in
                try? await Task.sleep(nanoseconds: 10_000_000_000) // 10 seconds
                await MainActor.run { [weak self] in
                    self?.cleanupQRConnection(resumeWith: .failure(NSError(
                        domain: "WebSocketService", 
                        code: 4, 
                        userInfo: [NSLocalizedDescriptionKey: "Connection timeout after 10 seconds"]
                    )))
                }
            }
            
            // Start connection attempt
            connectWithSettings(connectionSettings)
        }
    }
    
    private func cleanupQRConnection(resumeWith result: Result<Void, Error>?) {
        // Cancel timeout task
        qrConnectionTimeoutTask?.cancel()
        qrConnectionTimeoutTask = nil
        
        // Resume continuation if needed - ALWAYS resume to prevent leaks
        if let continuation = qrConnectionContinuation {
            qrConnectionContinuation = nil
            if let result = result {
                switch result {
                case .success:
                    continuation.resume()
                case .failure(let error):
                    continuation.resume(throwing: error)
                }
            } else {
                // If no result provided, resume with generic error to prevent leak
                continuation.resume(throwing: NSError(
                    domain: "WebSocketService", 
                    code: 5, 
                    userInfo: [NSLocalizedDescriptionKey: "Connection cleanup without result"]
                ))
            }
        }
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
                
                // Handle QR code connection completion
                self.cleanupQRConnection(resumeWith: .success(()))
                
                // Send initial status request
                self.sendCommand("/status", type: "command")
            }
            
        case .disconnected(let reason, _):
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.isConnected = false
                self.connectionStatus = "Disconnected"
                
                // Handle QR code connection failure
                self.cleanupQRConnection(resumeWith: .failure(NSError(
                    domain: "WebSocketService", 
                    code: 2, 
                    userInfo: [NSLocalizedDescriptionKey: "Connection failed: \(reason)"]
                )))
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
                
                // Handle QR code connection error
                self.cleanupQRConnection(resumeWith: .failure(
                    error ?? NSError(domain: "WebSocketService", code: 3, userInfo: [NSLocalizedDescriptionKey: "Unknown WebSocket error"])
                ))
            }
            
        case .cancelled, .peerClosed:
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.isConnected = false
                self.connectionStatus = "Connection closed"
                
                // Handle QR code connection cancellation
                self.cleanupQRConnection(resumeWith: .failure(NSError(
                    domain: "WebSocketService", 
                    code: 6, 
                    userInfo: [NSLocalizedDescriptionKey: "Connection was cancelled or closed by peer"]
                )))
            }
            
        default:
            break
        }
    }
    
    private func handleReceivedMessage(_ text: String) {
        do {
            let response = try JSONDecoder().decode(AgentResponse.self, from: text.data(using: .utf8) ?? Data())
            
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
            // Fallback for non-JSON responses
            let agentMessage = AgentMessage(
                content: text,
                isFromUser: false,
                type: .response
            )
            messages.append(agentMessage)
        }
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

