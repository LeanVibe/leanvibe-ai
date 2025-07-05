import Foundation
import Starscream

@available(iOS 18.0, macOS 14.0, *)
@MainActor
class WebSocketService: ObservableObject, WebSocketDelegate {
    @Published var isConnected = false
    @Published var messages: [AgentMessage] = []
    @Published var connectionStatus = "Disconnected"
    @Published var lastError: String?
    @Published var conflictNotifications: [ConflictNotification] = []
    
    // MARK: - Singleton Pattern
    static let shared = WebSocketService()
    
    private var socket: WebSocket?
    private let clientId = "ios-client-\(UUID().uuidString.prefix(8))"
    private let storageManager = ConnectionStorageManager()
    private var qrConnectionTask: Task<Void, Error>?
    
    // MARK: - Conflict Resolution Properties
    private var pendingMessages: [String: WebSocketMessage] = [:]
    private var messageVersions: [String: Int] = [:]
    private var sessionId: String = UUID().uuidString
    private var conflictResolver = ConflictResolver()
    
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
        
        // Only auto-connect if backend is properly configured
        guard config.isBackendConfigured else { 
            print("⚠️ No backend configured - QR code setup required")
            return nil 
        }
        
        // Detect if running in simulator
        let isSimulator = isRunningInSimulator()
        
        do {
            try config.validateConfiguration()
            
            // Parse URL to extract host and port
            guard let url = URL(string: config.apiBaseURL) else {
                print("⚠️ Invalid backend URL: \(config.apiBaseURL)")
                return nil
            }
            
            let host = url.host ?? ""
            let port = url.port ?? (url.scheme == "https" ? 443 : 80)
            
            if isSimulator {
                print("🤖 Simulator detected - connecting to configured backend: \(host):\(port)")
            }
            
            return ConnectionSettings(
                host: host,
                port: port,
                websocketPath: "/ws",
                serverName: isSimulator ? "Simulator (\(host))" : "Backend (\(host))",
                network: isSimulator ? "simulator" : "production"
            )
        } catch {
            print("⚠️ Cannot create connection from configuration: \(error)")
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
        
        let messageId = UUID().uuidString
        let currentVersion = (messageVersions[content] ?? 0) + 1
        messageVersions[content] = currentVersion
        
        let message = WebSocketMessage(
            type: type,
            content: content,
            timestamp: ISO8601DateFormatter().string(from: Date()),
            clientId: clientId,
            priority: .normal,
            messageId: messageId,
            sessionId: sessionId,
            version: currentVersion
        )
        
        // Store message for conflict resolution
        pendingMessages[messageId] = message
        
        do {
            let data = try JSONEncoder().encode(message)
            let string = String(data: data, encoding: .utf8) ?? ""
            
            socket.write(string: string)
            
            // Add user message to UI (optimistic update)
            let userMessage = AgentMessage(
                content: content,
                isFromUser: true,
                type: type == "command" ? .command : .message
            )
            messages.append(userMessage)
            
            // Schedule optimistic UI timeout (rollback if no confirmation)
            scheduleOptimisticTimeout(for: messageId, userMessage: userMessage)
            
        } catch {
            lastError = "Encoding error: \(error.localizedDescription)"
            // Remove from pending on error
            pendingMessages.removeValue(forKey: messageId)
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
                
                // Enhanced error handling with centralized error manager
                await self.handleWebSocketError(error, context: "websocket_connection")
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
        
        // Check for conflict resolution messages first
        if text.contains("\"type\":\"conflict_resolution\"") {
            handleConflictResolutionMessage(data)
            return
        }
        
        if text.contains("\"type\":\"conflict_detected\"") {
            handleConflictNotificationMessage(data)
            return
        }
        
        // Check if this is a WebSocket message that might conflict
        if text.contains("\"message_id\"") && text.contains("\"version\"") {
            handlePotentialConflictMessage(data)
            return
        }
        
        // Check if this might be a task update message
        if text.contains("\"type\":\"task_update\"") {
            handleTaskUpdateMessage(data)
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
    
    private func handleTaskUpdateMessage(_ data: Data) {
        do {
            let taskUpdate = try JSONDecoder().decode(TaskUpdateWebSocketMessage.self, from: data)
            
            // Forward to TaskService via notification
            DispatchQueue.main.async {
                NotificationCenter.default.post(
                    name: Notification.Name("taskUpdated"),
                    object: taskUpdate
                )
            }
            
            // Also add to messages for visibility
            let content = "Task \(taskUpdate.action): \(taskUpdate.task?.title ?? "Unknown")"
            let agentMessage = AgentMessage(
                content: content,
                isFromUser: false,
                type: .status
            )
            messages.append(agentMessage)
            
        } catch {
            print("Failed to decode task update message: \(error)")
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
    
    // MARK: - Conflict Resolution Methods
    
    private func scheduleOptimisticTimeout(for messageId: String, userMessage: AgentMessage) {
        Task { [weak self] in
            // Wait 5 seconds for server confirmation
            try await Task.sleep(nanoseconds: 5_000_000_000)
            
            await MainActor.run { [weak self] in
                guard let self = self else { return }
                
                // If message is still pending, consider it failed and remove from UI
                if self.pendingMessages[messageId] != nil {
                    self.pendingMessages.removeValue(forKey: messageId)
                    
                    // Remove optimistic message from UI
                    if let index = self.messages.firstIndex(where: { 
                        $0.id == userMessage.id 
                    }) {
                        self.messages.remove(at: index)
                        
                        // Add error message
                        let errorMessage = AgentMessage(
                            content: "⚠️ Message failed to send: \(userMessage.content)",
                            isFromUser: false,
                            type: .error
                        )
                        self.messages.append(errorMessage)
                    }
                }
            }
        }
    }
    
    private func handleConflictResolutionMessage(_ data: Data) {
        do {
            let conflictResolution = try JSONDecoder().decode(ConflictResolutionMessage.self, from: data)
            
            // Remove original conflicting messages from pending
            if let originalId = conflictResolution.originalMessage.messageId {
                pendingMessages.removeValue(forKey: originalId)
            }
            if let conflictingId = conflictResolution.conflictingMessage.messageId {
                pendingMessages.removeValue(forKey: conflictingId)
            }
            
            // Apply resolved message
            let resolvedContent = conflictResolution.resolvedMessage.content
            let agentMessage = AgentMessage(
                content: "🔄 Conflict resolved (\(conflictResolution.strategy.rawValue)): \(resolvedContent)",
                isFromUser: false,
                type: .status
            )
            
            messages.append(agentMessage)
            
            print("✅ Conflict resolved using \(conflictResolution.strategy.rawValue) strategy")
            
        } catch {
            print("❌ Failed to decode conflict resolution message: \(error)")
        }
    }
    
    private func handleConflictNotificationMessage(_ data: Data) {
        do {
            let notification = try JSONDecoder().decode(ConflictNotification.self, from: data)
            
            // Add to notifications list
            conflictNotifications.append(notification)
            
            // Add visual indicator to message list
            let conflictMessage = AgentMessage(
                content: "⚠️ Conflict detected: \(notification.description)",
                isFromUser: false,
                type: .error
            )
            
            messages.append(conflictMessage)
            
            print("⚠️ Conflict detected: \(notification.description)")
            
        } catch {
            print("❌ Failed to decode conflict notification: \(error)")
        }
    }
    
    private func handlePotentialConflictMessage(_ data: Data) {
        do {
            let incomingMessage = try JSONDecoder().decode(WebSocketMessage.self, from: data)
            
            // Check for conflicts with pending messages
            if let messageId = incomingMessage.messageId,
               let version = incomingMessage.version {
                
                let conflicts = conflictResolver.detectConflicts(
                    incomingMessage: incomingMessage,
                    pendingMessages: Array(pendingMessages.values)
                )
                
                if !conflicts.isEmpty {
                    handleDetectedConflicts(conflicts, incomingMessage: incomingMessage)
                } else {
                    // No conflict, confirm message receipt
                    if let pendingMessage = pendingMessages[messageId] {
                        pendingMessages.removeValue(forKey: messageId)
                        print("✅ Message confirmed: \(pendingMessage.content)")
                    }
                }
            }
            
        } catch {
            print("❌ Failed to decode potential conflict message: \(error)")
            handleFallbackMessage(String(data: data, encoding: .utf8) ?? "")
        }
    }
    
    private func handleDetectedConflicts(_ conflicts: [ConflictInfo], incomingMessage: WebSocketMessage) {
        for conflict in conflicts {
            // Apply last-write-wins strategy
            let resolution = conflictResolver.resolveConflict(
                conflict: conflict,
                strategy: .lastWriteWins
            )
            
            // Update local state based on resolution
            applyConflictResolution(resolution)
            
            // Send resolution back to server
            sendConflictResolution(resolution)
        }
    }
    
    private func applyConflictResolution(_ resolution: ConflictResolution) {
        // Remove conflicting messages from UI
        messages.removeAll { message in
            resolution.conflictingMessageIds.contains(message.id.uuidString)
        }
        
        // Add resolved message
        let resolvedMessage = AgentMessage(
            content: resolution.resolvedContent,
            isFromUser: resolution.isFromUser,
            type: .message
        )
        
        messages.append(resolvedMessage)
        
        // Clean up pending messages
        for messageId in resolution.conflictingMessageIds {
            pendingMessages.removeValue(forKey: messageId)
        }
    }
    
    private func sendConflictResolution(_ resolution: ConflictResolution) {
        // Implementation would send resolution back to server
        // For now, just log the resolution
        print("📤 Sending conflict resolution: \(resolution.strategy.rawValue)")
    }
    
    // MARK: - Conflict Resolution Public Methods
    
    func dismissConflictNotification(_ notificationId: String) {
        conflictNotifications.removeAll { $0.conflictId == notificationId }
    }
    
    func retryFailedMessage(_ content: String) {
        sendMessage(content)
    }
    
    // MARK: - Centralized Error Handling
    
    private func handleWebSocketError(_ error: Error?, context: String) async {
        let actualError = error ?? URLError(.unknown)
        
        // Categorize the error
        let category: ErrorCategory = {
            if actualError is URLError {
                return .network
            } else {
                return .service
            }
        }()
        
        // Create comprehensive error with recovery actions
        let appError = AppError(
            title: "Connection Error",
            message: actualError.localizedDescription,
            severity: .error,
            category: category,
            context: "websocket_\(context)",
            userFacingMessage: "We're having trouble connecting to the server. Please check your connection and try again.",
            technicalDetails: "WebSocketService Error in \(context): \(type(of: actualError)) - \(actualError.localizedDescription)",
            suggestedActions: createWebSocketRecoveryActions(for: actualError)
        )
        
        // Show error to user using centralized error manager
        if let globalErrorManager = try? GlobalErrorManager.shared {
            globalErrorManager.showError(appError)
            
            // Automatically attempt recovery for network errors
            if category == .network {
                await ErrorRecoveryManager.shared.attemptRecovery(for: appError)
            }
        } else {
            // Fallback if GlobalErrorManager is not available
            print("🚨 WebSocketService Error: \(actualError.localizedDescription)")
        }
    }
    
    private func createWebSocketRecoveryActions(for error: Error) -> [ErrorAction] {
        var actions: [ErrorAction] = []
        
        // Reconnect action
        actions.append(ErrorAction(title: "Reconnect", systemImage: "arrow.clockwise", isPrimary: true) {
            Task { @MainActor in
                self.connect()
            }
        })
        
        // Work offline action
        actions.append(ErrorAction(title: "Work Offline", systemImage: "wifi.slash") {
            // Enable offline mode
            print("User chose to work offline")
        })
        
        // Check network action
        actions.append(ErrorAction(title: "Check Network", systemImage: "network") {
            Task {
                await NetworkErrorHandler.shared.checkNetworkStatus()
            }
        })
        
        // Clear connection data for configuration issues
        if error is URLError {
            actions.append(ErrorAction(title: "Reconfigure Connection", systemImage: "qrcode.viewfinder") {
                // Reset connection settings
                self.storageManager.clearStoredConnection()
            })
        }
        
        return actions
    }
}

// MARK: - Conflict Resolution Support Classes

class ConflictResolver {
    func detectConflicts(incomingMessage: WebSocketMessage, pendingMessages: [WebSocketMessage]) -> [ConflictInfo] {
        var conflicts: [ConflictInfo] = []
        
        for pendingMessage in pendingMessages {
            // Check for content conflicts (same content, different versions)
            if pendingMessage.content == incomingMessage.content &&
               pendingMessage.version != incomingMessage.version {
                
                let conflict = ConflictInfo(
                    id: UUID().uuidString,
                    originalMessage: pendingMessage,
                    conflictingMessage: incomingMessage,
                    conflictType: .versionMismatch,
                    detectedAt: Date()
                )
                
                conflicts.append(conflict)
            }
            
            // Check for timing conflicts (similar timestamps)
            if let pendingTime = ISO8601DateFormatter().date(from: pendingMessage.timestamp),
               let incomingTime = ISO8601DateFormatter().date(from: incomingMessage.timestamp) {
                
                let timeDifference = abs(pendingTime.timeIntervalSince(incomingTime))
                
                if timeDifference < 2.0 { // Within 2 seconds
                    let conflict = ConflictInfo(
                        id: UUID().uuidString,
                        originalMessage: pendingMessage,
                        conflictingMessage: incomingMessage,
                        conflictType: .timingConflict,
                        detectedAt: Date()
                    )
                    
                    conflicts.append(conflict)
                }
            }
        }
        
        return conflicts
    }
    
    func resolveConflict(conflict: ConflictInfo, strategy: ConflictStrategy) -> ConflictResolution {
        switch strategy {
        case .lastWriteWins:
            return resolveLastWriteWins(conflict: conflict)
        case .firstWriteWins:
            return resolveFirstWriteWins(conflict: conflict)
        case .merge:
            return resolveMerge(conflict: conflict)
        case .userChoice:
            return resolveUserChoice(conflict: conflict)
        }
    }
    
    private func resolveLastWriteWins(conflict: ConflictInfo) -> ConflictResolution {
        let originalTime = ISO8601DateFormatter().date(from: conflict.originalMessage.timestamp) ?? Date.distantPast
        let conflictingTime = ISO8601DateFormatter().date(from: conflict.conflictingMessage.timestamp) ?? Date.distantPast
        
        let winningMessage = conflictingTime > originalTime ? conflict.conflictingMessage : conflict.originalMessage
        
        return ConflictResolution(
            conflictId: conflict.id,
            strategy: .lastWriteWins,
            resolvedContent: winningMessage.content,
            isFromUser: winningMessage.clientId.hasPrefix("ios-client"),
            conflictingMessageIds: [
                conflict.originalMessage.messageId ?? "",
                conflict.conflictingMessage.messageId ?? ""
            ]
        )
    }
    
    private func resolveFirstWriteWins(conflict: ConflictInfo) -> ConflictResolution {
        let originalTime = ISO8601DateFormatter().date(from: conflict.originalMessage.timestamp) ?? Date.distantFuture
        let conflictingTime = ISO8601DateFormatter().date(from: conflict.conflictingMessage.timestamp) ?? Date.distantFuture
        
        let winningMessage = originalTime < conflictingTime ? conflict.originalMessage : conflict.conflictingMessage
        
        return ConflictResolution(
            conflictId: conflict.id,
            strategy: .firstWriteWins,
            resolvedContent: winningMessage.content,
            isFromUser: winningMessage.clientId.hasPrefix("ios-client"),
            conflictingMessageIds: [
                conflict.originalMessage.messageId ?? "",
                conflict.conflictingMessage.messageId ?? ""
            ]
        )
    }
    
    private func resolveMerge(conflict: ConflictInfo) -> ConflictResolution {
        // Simple merge strategy: combine both messages
        let mergedContent = "\(conflict.originalMessage.content) | \(conflict.conflictingMessage.content)"
        
        return ConflictResolution(
            conflictId: conflict.id,
            strategy: .merge,
            resolvedContent: mergedContent,
            isFromUser: true, // Mark as user since it's a merge
            conflictingMessageIds: [
                conflict.originalMessage.messageId ?? "",
                conflict.conflictingMessage.messageId ?? ""
            ]
        )
    }
    
    private func resolveUserChoice(conflict: ConflictInfo) -> ConflictResolution {
        // For now, default to last write wins, but this would show UI for user choice
        return resolveLastWriteWins(conflict: conflict)
    }
}

struct ConflictInfo {
    let id: String
    let originalMessage: WebSocketMessage
    let conflictingMessage: WebSocketMessage
    let conflictType: ConflictType
    let detectedAt: Date
}

enum ConflictType {
    case versionMismatch
    case timingConflict
    case contentDivergence
}

struct ConflictResolution {
    let conflictId: String
    let strategy: ConflictStrategy
    let resolvedContent: String
    let isFromUser: Bool
    let conflictingMessageIds: [String]
}

// MARK: - Task WebSocket Message Models

struct TaskUpdateWebSocketMessage: Codable {
    let type: String
    let action: String // "created", "updated", "deleted", "moved"
    let task: LeanVibeTask?
    let timestamp: String?
}

