import Foundation
import Starscream

@MainActor
public class WebSocketService: ObservableObject, WebSocketDelegate {
    @Published public var isConnected = false
    @Published public var messages: [AgentMessage] = []
    @Published public var connectionStatus = "Disconnected"
    @Published public var lastError: String?
    
    private var socket: WebSocket?
    private let serverURL = "ws://localhost:8000/ws/ios-client"
    private let clientId = "ios-client-\(UUID().uuidString.prefix(8))"
    
    public init() {
        setupWebSocket()
    }
    
    private func setupWebSocket() {
        guard let url = URL(string: serverURL) else {
            connectionStatus = "Invalid URL"
            return
        }
        
        var request = URLRequest(url: url)
        request.timeoutInterval = 10
        
        socket = WebSocket(request: request)
        socket?.delegate = self
    }
    
    public func connect() {
        connectionStatus = "Connecting..."
        socket?.connect()
    }
    
    public func disconnect() {
        socket?.disconnect()
        isConnected = false
        connectionStatus = "Disconnected"
        lastError = nil
    }
    
    public func sendMessage(_ content: String, type: String = "message") {
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
    
    public func sendCommand(_ command: String, type: String = "command") {
        sendMessage(command, type: type)
    }
    
    public func clearMessages() {
        messages.removeAll()
    }
    
    // MARK: - WebSocketDelegate
    
    public func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        switch event {
        case .connected(let headers):
            isConnected = true
            connectionStatus = "Connected"
            
            // Send initial status request
            sendCommand("/status", type: "command")
            
        case .disconnected(let reason, let code):
            isConnected = false
            connectionStatus = "Disconnected"
            
        case .text(let string):
            handleReceivedMessage(string)
            
        case .binary(let data):
            if let text = String(data: data, encoding: .utf8) {
                handleReceivedMessage(text)
            }
            
        case .error(let error):
            lastError = error?.localizedDescription ?? "Unknown WebSocket error"
            isConnected = false
            connectionStatus = "Error"
            
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