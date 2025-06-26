import Foundation
import Network

@MainActor
class WebSocketService: ObservableObject {
    @Published var isConnected = false
    @Published var messages: [AgentMessage] = []
    @Published var connectionStatus = "Disconnected"
    @Published var lastError: String?
    
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private let serverURL = "ws://localhost:8000/ws/ios-client"
    private let clientId = "ios-client-\(UUID().uuidString.prefix(8))"
    
    init() {
        setupURLSession()
    }
    
    private func setupURLSession() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        urlSession = URLSession(configuration: config)
    }
    
    func connect() {
        guard let url = URL(string: serverURL) else {
            connectionStatus = "Invalid URL"
            return
        }
        
        connectionStatus = "Connecting..."
        
        var request = URLRequest(url: url)
        request.timeoutInterval = 10
        
        webSocketTask = urlSession?.webSocketTask(with: request)
        webSocketTask?.resume()
        
        isConnected = true
        connectionStatus = "Connected"
        
        // Start listening for messages
        receiveMessage()
        
        // Send initial status request
        sendCommand("/status", type: "command")
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
        connectionStatus = "Disconnected"
        lastError = nil
    }
    
    func sendMessage(_ content: String, type: String = "message") {
        guard isConnected, let webSocketTask = webSocketTask else {
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
            
            webSocketTask.send(.string(string)) { [weak self] error in
                DispatchQueue.main.async {
                    if let error = error {
                        self?.lastError = "Send error: \(error.localizedDescription)"
                        self?.disconnect()
                    }
                }
            }
            
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
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    DispatchQueue.main.async {
                        self?.handleReceivedMessage(text)
                    }
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        DispatchQueue.main.async {
                            self?.handleReceivedMessage(text)
                        }
                    }
                @unknown default:
                    break
                }
                
                // Continue listening
                self?.receiveMessage()
                
            case .failure(let error):
                DispatchQueue.main.async {
                    self?.lastError = "Receive error: \(error.localizedDescription)"
                    self?.disconnect()
                }
            }
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
    
    func clearMessages() {
        messages.removeAll()
    }
}