import Foundation
4import Starscream

struct ServerConfig {
    let host: String
    let port: Int
    let websocketPath: String
    let serverName: String?
    let network: String?
}

@MainActor
class WebSocketService: ObservableObject, WebSocketDelegate {
    @Published var isConnected = false
    @Published var messages: [AgentMessage] = []
    @Published var connectionStatus = "Disconnected"
    @Published var lastError: String?
    
    private var socket: WebSocket?
    private let clientId = "ios-client-\(UUID().uuidString.prefix(8))"
    private let storageManager = ConnectionStorageManager()
    private var qrConnectionCompletion: ((Bool, String?) -> Void)?
    
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
    
    private func setupWebSocket() {
        // This method is deprecated - use setupWebSocketWithURL instead
        connectionStatus = "No connection configured"
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
            clientId: clientId
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
    
    func connectWithQRCode(_ qrData: String, completion: @escaping (Bool, String?) -> Void) {
        guard let config = parseQRConfig(qrData) else {
            completion(false, "Invalid QR code format")
            return
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
        
        // Store completion for later
        qrConnectionCompletion = completion
        
        // Connect using the new settings
        connectWithSettings(connectionSettings)
    }
    
    private func parseQRConfig(_ qrData: String) -> ServerConfig? {
        do {
            let data = qrData.data(using: .utf8) ?? Data()
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            
            guard let leenvibe = json?["leenvibe"] as? [String: Any],
                  let server = leenvibe["server"] as? [String: Any],
                  let host = server["host"] as? String,
                  let port = server["port"] as? Int,
                  let websocketPath = server["websocket_path"] as? String else {
                return nil
            }
            
            let metadata = leenvibe["metadata"] as? [String: Any]
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
    
    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        switch event {
        case .connected(let headers):
            isConnected = true
            connectionStatus = "Connected"
            lastError = nil
            
            // Handle QR code connection completion
            if let completion = qrConnectionCompletion {
                completion(true, nil)
                qrConnectionCompletion = nil
            }
            
            // Send initial status request
            sendCommand("/status", type: "command")
            
        case .disconnected(let reason, let code):
            isConnected = false
            connectionStatus = "Disconnected"
            
            // Handle QR code connection failure
            if let completion = qrConnectionCompletion {
                completion(false, "Connection failed: \(reason)")
                qrConnectionCompletion = nil
            }
            
        case .text(let string):
            handleReceivedMessage(string)
            
        case .binary(let data):
            if let text = String(data: data, encoding: .utf8) {
                handleReceivedMessage(text)
            }
            
        case .error(let error):
            let errorMessage = error?.localizedDescription ?? "Unknown WebSocket error"
            lastError = errorMessage
            isConnected = false
            connectionStatus = "Error"
            
            // Handle QR code connection error
            if let completion = qrConnectionCompletion {
                completion(false, errorMessage)
                qrConnectionCompletion = nil
            }
            
        case .ping(_), .pong(_):
            // Handle ping/pong for connection keep-alive
            break
            
        case .viabilityChanged(let isViable):
            if !isViable {
                connectionStatus = "Connection not viable"
            }
            
        case .reconnectSuggested(let shouldReconnect):
            if shouldReconnect && !isConnected {
                connectionStatus = "Reconnecting..."
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    self.connect()
                }
            }
            
        case .cancelled:
            isConnected = false
            connectionStatus = "Cancelled"
            
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

