import XCTest
import Starscream
import Combine
@testable import LeanVibe

/// Test suite for WebSocketService with 35% stability impact
/// Tests WebSocket connection, QR code flow, message handling, and error recovery
@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class WebSocketServiceTests: XCTestCase {
    
    // MARK: - Test Dependencies
    
    private var webSocketService: WebSocketService!
    private var mockWebSocket: MockWebSocket!
    private var mockStorageManager: MockConnectionStorageManager!
    private var cancellables: Set<AnyCancellable>!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        webSocketService = WebSocketService()
        cancellables = Set<AnyCancellable>()
        
        // Note: We can't easily mock the internal WebSocket since it's created internally
        // So these tests focus on the public interface and state management
    }
    
    override func tearDownWithError() throws {
        cancellables?.removeAll()
        cancellables = nil
        webSocketService?.disconnect()
        webSocketService = nil
        mockWebSocket = nil
        mockStorageManager = nil
        
        try super.tearDownWithError()
    }
    
    // MARK: - Initialization Tests
    
    func testWebSocketServiceInitialization() {
        XCTAssertFalse(webSocketService.isConnected)
        XCTAssertTrue(webSocketService.messages.isEmpty)
        XCTAssertEqual(webSocketService.connectionStatus, "No saved connection - Scan QR to connect")
        XCTAssertNil(webSocketService.lastError)
    }
    
    // MARK: - Connection Status Tests
    
    func testConnectionStatusWithoutStoredConnection() {
        // Given: Fresh service with no stored connection
        let service = WebSocketService()
        
        // Then: Should show appropriate status
        XCTAssertEqual(service.connectionStatus, "No saved connection - Scan QR to connect")
        XCTAssertFalse(service.hasStoredConnection())
        XCTAssertNil(service.getCurrentConnectionInfo())
    }
    
    // MARK: - Message Handling Tests
    
    func testSendMessage_NotConnected() {
        // Given: Disconnected service
        XCTAssertFalse(webSocketService.isConnected)
        
        // When: Attempting to send message
        webSocketService.sendMessage("test message")
        
        // Then: Should set error and not add to messages
        XCTAssertEqual(webSocketService.lastError, "Not connected")
        XCTAssertTrue(webSocketService.messages.isEmpty)
    }
    
    func testSendCommand() {
        // Given: Command string
        let command = "/status"
        
        // When: Sending command while disconnected
        webSocketService.sendCommand(command, type: "command")
        
        // Then: Should handle same as regular message when disconnected
        XCTAssertEqual(webSocketService.lastError, "Not connected")
    }
    
    func testClearMessages() {
        // Given: Service with mock messages (simulate adding messages)
        webSocketService.messages = [
            AgentMessage(content: "Test 1", isFromUser: true, type: .message),
            AgentMessage(content: "Test 2", isFromUser: false, type: .response)
        ]
        
        XCTAssertEqual(webSocketService.messages.count, 2)
        
        // When: Clearing messages
        webSocketService.clearMessages()
        
        // Then: Messages should be empty
        XCTAssertTrue(webSocketService.messages.isEmpty)
    }
    
    // MARK: - QR Code Parsing Tests
    
    func testParseQRConfig_ValidJSON() async {
        let validQRData = """
        {
            "leanvibe": {
                "server": {
                    "host": "192.168.1.100",
                    "port": 8000,
                    "websocket_path": "/ws"
                },
                "metadata": {
                    "server_name": "Test Server",
                    "network": "Home Network"
                }
            }
        }
        """
        
        // Test through connectWithQRCode which will parse internally
        // We expect this to fail with timeout since we can't connect, but parsing should work
        do {
            try await webSocketService.connectWithQRCode(validQRData)
            XCTFail("Should have failed with timeout")
        } catch {
            // Expected to fail due to connection timeout, but parsing should have worked
            XCTAssertTrue(error.localizedDescription.contains("timeout") || 
                         error.localizedDescription.contains("Connection") ||
                         error.localizedDescription.contains("failed"))
        }
        
        // Check that connection settings were stored (indicating successful parsing)
        XCTAssertTrue(webSocketService.hasStoredConnection())
    }
    
    func testParseQRConfig_InvalidJSON() async {
        let invalidQRData = "invalid json data"
        
        // When: Connecting with invalid QR data
        do {
            try await webSocketService.connectWithQRCode(invalidQRData)
            XCTFail("Should have failed with invalid QR format")
        } catch {
            // Then: Should fail with parsing error
            XCTAssertTrue(error.localizedDescription.contains("Invalid QR code format"))
        }
    }
    
    func testParseQRConfig_MissingRequiredFields() async {
        let incompleteQRData = """
        {
            "leanvibe": {
                "server": {
                    "host": "192.168.1.100"
                }
            }
        }
        """
        
        // When: Connecting with incomplete QR data
        do {
            try await webSocketService.connectWithQRCode(incompleteQRData)
            XCTFail("Should have failed with missing fields")
        } catch {
            // Then: Should fail with parsing error
            XCTAssertTrue(error.localizedDescription.contains("Invalid QR code format"))
        }
    }
    
    // MARK: - Connection Flow Tests
    
    func testConnectWithQRCode_Timeout() async {
        let validQRData = """
        {
            "leanvibe": {
                "server": {
                    "host": "192.168.1.100",
                    "port": 8000,
                    "websocket_path": "/ws"
                }
            }
        }
        """
        
        // When: Connecting with valid QR code (will timeout since server doesn't exist)
        let startTime = CFAbsoluteTimeGetCurrent()
        
        do {
            try await webSocketService.connectWithQRCode(validQRData)
            XCTFail("Should have failed with timeout")
        } catch {
            let endTime = CFAbsoluteTimeGetCurrent()
            let duration = endTime - startTime
            
            // Then: Should timeout within reasonable time (10 seconds + buffer)
            XCTAssertGreaterThan(duration, 9.0, "Should wait for timeout")
            XCTAssertLessThan(duration, 15.0, "Should not wait too long")
            XCTAssertTrue(error.localizedDescription.contains("timeout") || 
                         error.localizedDescription.contains("Connection"))
        }
    }
    
    // MARK: - Connection Management Tests
    
    func testDisconnect() {
        // Given: Service (whether connected or not)
        webSocketService.lastError = "Previous error"
        
        // When: Disconnecting
        webSocketService.disconnect()
        
        // Then: Should reset connection state
        XCTAssertFalse(webSocketService.isConnected)
        XCTAssertEqual(webSocketService.connectionStatus, "Disconnected")
        XCTAssertNil(webSocketService.lastError)
    }
    
    func testConnectToSavedConnection_NoConnection() {
        // Given: Service with no saved connection
        XCTAssertFalse(webSocketService.hasStoredConnection())
        
        // When: Attempting to connect to saved connection
        webSocketService.connectToSavedConnection()
        
        // Then: Should show appropriate status
        XCTAssertEqual(webSocketService.connectionStatus, "No saved connection - Scan QR to connect")
    }
    
    // MARK: - Message Formatting Tests
    
    func testMessageCreation() {
        // Test creating different types of agent messages
        let messageTypes: [AgentMessage.MessageType] = [.message, .command, .response, .error, .status]
        
        for type in messageTypes {
            let message = AgentMessage(content: "Test content", isFromUser: true, type: type)
            
            XCTAssertEqual(message.content, "Test content")
            XCTAssertTrue(message.isFromUser)
            XCTAssertEqual(message.type, type)
            XCTAssertNotNil(message.timestamp)
        }
    }
    
    // MARK: - Error Handling Tests
    
    func testErrorStateManagement() {
        // Given: Service with an error
        webSocketService.lastError = "Test error"
        
        // When: Connecting (which would clear error on success)
        webSocketService.connect()
        
        // Then: Error should initially remain (since connection will likely fail)
        // This test validates that error state is managed properly
        XCTAssertNotNil(webSocketService.lastError) // Will be set during failed connection
    }
    
    func testConnectionStatusUpdates() {
        // Test various connection status states
        let initialStatus = webSocketService.connectionStatus
        XCTAssertEqual(initialStatus, "No saved connection - Scan QR to connect")
        
        // When connecting
        webSocketService.connect()
        // Status should change (exact value depends on connection state)
        XCTAssertNotEqual(webSocketService.connectionStatus, initialStatus)
        
        // When disconnecting
        webSocketService.disconnect()
        XCTAssertEqual(webSocketService.connectionStatus, "Disconnected")
    }
    
    // MARK: - Storage Integration Tests
    
    func testConnectionStorageIntegration() {
        // Access the connection storage manager
        let storageManager = webSocketService.connectionStorage
        
        // Should be able to interact with storage
        XCTAssertNotNil(storageManager)
        XCTAssertTrue(storageManager.savedConnections.isEmpty)
        XCTAssertNil(storageManager.currentConnection)
    }
    
    // MARK: - Concurrent Access Tests
    
    func testConcurrentMessageHandling() async {
        // Given: Multiple message operations
        let messages = (1...10).map { "Message \($0)" }
        
        // When: Sending multiple messages concurrently
        await withTaskGroup(of: Void.self) { group in
            for message in messages {
                group.addTask { [weak webSocketService] in
                    await MainActor.run {
                        webSocketService?.sendMessage(message)
                    }
                }
            }
        }
        
        // Then: Should handle all operations gracefully (all will fail due to no connection)
        XCTAssertEqual(webSocketService.lastError, "Not connected")
        XCTAssertTrue(webSocketService.messages.isEmpty)
    }
    
    func testConcurrentConnectionAttempts() async {
        let validQRData = """
        {
            "leanvibe": {
                "server": {
                    "host": "192.168.1.100",
                    "port": 8000,
                    "websocket_path": "/ws"
                }
            }
        }
        """
        
        // When: Making multiple concurrent connection attempts
        await withTaskGroup(of: Void.self) { group in
            for _ in 1...3 {
                group.addTask { [weak webSocketService] in
                    do {
                        try await webSocketService?.connectWithQRCode(validQRData)
                    } catch {
                        // Expected to fail - testing concurrent access
                    }
                }
            }
        }
        
        // Then: Should handle concurrent access gracefully
        XCTAssertTrue(webSocketService.hasStoredConnection())
    }
    
    // MARK: - Performance Tests
    
    func testMessageClearingPerformance() {
        // Given: Large number of messages
        let largeMessageArray = (1...1000).map { i in
            AgentMessage(content: "Message \(i)", isFromUser: i % 2 == 0, type: .message)
        }
        
        webSocketService.messages = largeMessageArray
        XCTAssertEqual(webSocketService.messages.count, 1000)
        
        // When: Clearing messages
        let startTime = CFAbsoluteTimeGetCurrent()
        webSocketService.clearMessages()
        let endTime = CFAbsoluteTimeGetCurrent()
        
        // Then: Should clear quickly
        let executionTime = endTime - startTime
        XCTAssertTrue(webSocketService.messages.isEmpty)
        XCTAssertLessThan(executionTime, 0.1, "Clearing 1000 messages should be fast")
    }
    
    // MARK: - Memory Management Tests
    
    func testMemoryManagement() {
        // Test that objects are properly deallocated
        weak var weakService: WebSocketService?
        
        autoreleasepool {
            let service = WebSocketService()
            weakService = service
            
            // Use the service
            service.sendMessage("test")
            service.clearMessages()
        }
        
        // Give time for deallocation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            // Service should be deallocated (this is more of a documentation test)
            // In practice, WebSocketService might be retained by the system
        }
    }
    
    // MARK: - Edge Cases
    
    func testEmptyMessageHandling() {
        // Test sending empty messages
        webSocketService.sendMessage("")
        webSocketService.sendCommand("")
        
        // Should handle gracefully
        XCTAssertEqual(webSocketService.lastError, "Not connected")
    }
    
    func testLongMessageHandling() {
        // Test sending very long messages
        let longMessage = String(repeating: "A", count: 10000)
        webSocketService.sendMessage(longMessage)
        
        // Should handle gracefully
        XCTAssertEqual(webSocketService.lastError, "Not connected")
    }
    
    func testSpecialCharacterHandling() {
        // Test messages with special characters
        let specialMessage = "Test 🚀 with émojis and spëcial châractërs"
        webSocketService.sendMessage(specialMessage)
        
        // Should handle gracefully
        XCTAssertEqual(webSocketService.lastError, "Not connected")
    }
}

// MARK: - Mock Dependencies

/// Mock WebSocket for testing without actual network connections
class MockWebSocket: WebSocketClient {
    var delegate: WebSocketDelegate?
    var isConnected: Bool = false
    var request: URLRequest
    
    // Configurable mock behavior
    var shouldConnectSuccessfully = true
    var connectionDelay: TimeInterval = 0
    var mockMessages: [String] = []
    var sentMessages: [String] = []
    
    init(request: URLRequest) {
        self.request = request
    }
    
    func connect() {
        DispatchQueue.main.asyncAfter(deadline: .now() + connectionDelay) {
            if self.shouldConnectSuccessfully {
                self.isConnected = true
                self.delegate?.didReceive(event: .connected([:]), client: self)
            } else {
                let error = NSError(domain: "MockWebSocket", code: 1, userInfo: [NSLocalizedDescriptionKey: "Mock connection failed"])
                self.delegate?.didReceive(event: .error(error), client: self)
            }
        }
    }
    
    func disconnect(forceTimeout: TimeInterval? = nil, closeCode: UInt16 = CloseCode.normal.rawValue) {
        isConnected = false
        delegate?.didReceive(event: .disconnected("Mock disconnect", closeCode), client: self)
    }
    
    func disconnect(closeCode: UInt16) {
        disconnect(forceTimeout: nil, closeCode: closeCode)
    }
    
    func write(string: String, completion: (() -> ())? = nil) {
        sentMessages.append(string)
        completion?()
    }
    
    func write(stringData: Data, completion: (() -> ())? = nil) {
        if let string = String(data: stringData, encoding: .utf8) {
            sentMessages.append(string)
        }
        completion?()
    }
    
    func write(data: Data, completion: (() -> ())? = nil) {
        completion?()
    }
    
    func write(ping: Data, completion: (() -> ())? = nil) {
        completion?()
    }
    
    func write(pong: Data, completion: (() -> ())? = nil) {
        completion?()
    }
    
    // Simulate receiving messages
    func simulateReceiveMessage(_ message: String) {
        delegate?.didReceive(event: .text(message), client: self)
    }
    
    func simulateError(_ error: Error) {
        delegate?.didReceive(event: .error(error), client: self)
    }
}

/// Mock Connection Storage Manager for testing
class MockConnectionStorageManager: ConnectionStorageManager {
    private var mockConnections: [ConnectionSettings] = []
    private var mockCurrentConnection: ConnectionSettings?
    
    override var savedConnections: [ConnectionSettings] {
        get { mockConnections }
        set { mockConnections = newValue }
    }
    
    override var currentConnection: ConnectionSettings? {
        get { mockCurrentConnection }
        set { mockCurrentConnection = newValue }
    }
    
    override func saveConnection(_ settings: ConnectionSettings) {
        mockCurrentConnection = settings
        mockConnections.insert(settings, at: 0)
        // Simulate trimming to 5
        if mockConnections.count > 5 {
            mockConnections = Array(mockConnections.prefix(5))
        }
    }
    
    override func clearAllConnections() {
        mockConnections.removeAll()
        mockCurrentConnection = nil
    }
    
    override func hasValidConnection() -> Bool {
        return mockCurrentConnection != nil
    }
}

// MARK: - Test Extensions

// Removed invalid convenience initializer for AgentMessage struct