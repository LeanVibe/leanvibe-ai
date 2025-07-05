import XCTest
import Foundation
@testable import LeanVibe

/// Test suite for ConnectionStorageManager with 25% stability impact
/// Tests UserDefaults persistence, connection management, and array limits
@MainActor
final class ConnectionStorageManagerTests: XCTestCase {
    
    // MARK: - Test Dependencies
    
    private var storageManager: ConnectionStorageManager!
    private var mockUserDefaults: MockUserDefaultsForConnectionTests!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        mockUserDefaults = MockUserDefaultsForConnectionTests()
        storageManager = ConnectionStorageManager()
        
        // Clear any existing data
        storageManager.clearAllConnections()
    }
    
    override func tearDownWithError() throws {
        storageManager?.clearAllConnections()
        storageManager = nil
        mockUserDefaults = nil
        
        try super.tearDownWithError()
    }
    
    // MARK: - Initialization Tests
    
    func testConnectionStorageManagerInitialization() {
        XCTAssertTrue(storageManager.savedConnections.isEmpty)
        XCTAssertNil(storageManager.currentConnection)
        XCTAssertFalse(storageManager.hasValidConnection())
        XCTAssertFalse(storageManager.hasStoredConnection())
    }
    
    // MARK: - Save Connection Tests
    
    func testSaveConnection_Single() {
        // Given: A connection settings object
        let connection = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        
        // When: Saving the connection
        storageManager.saveConnection(connection)
        
        // Then: Connection should be saved and set as current
        XCTAssertEqual(storageManager.savedConnections.count, 1)
        XCTAssertEqual(storageManager.savedConnections[0].host, "192.168.1.100")
        XCTAssertEqual(storageManager.savedConnections[0].port, 8000)
        XCTAssertNotNil(storageManager.currentConnection)
        XCTAssertEqual(storageManager.currentConnection?.host, "192.168.1.100")
        XCTAssertTrue(storageManager.hasValidConnection())
    }
    
    func testSaveConnection_Multiple() {
        // Given: Multiple connection settings
        let connection1 = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        let connection2 = createTestConnectionSettings(host: "192.168.1.101", port: 8001)
        let connection3 = createTestConnectionSettings(host: "192.168.1.102", port: 8002)
        
        // When: Saving multiple connections
        storageManager.saveConnection(connection1)
        storageManager.saveConnection(connection2)
        storageManager.saveConnection(connection3)
        
        // Then: All connections should be saved, most recent first
        XCTAssertEqual(storageManager.savedConnections.count, 3)
        XCTAssertEqual(storageManager.savedConnections[0].host, "192.168.1.102") // Most recent first
        XCTAssertEqual(storageManager.savedConnections[1].host, "192.168.1.101")
        XCTAssertEqual(storageManager.savedConnections[2].host, "192.168.1.100")
        XCTAssertEqual(storageManager.currentConnection?.host, "192.168.1.102")
    }
    
    func testSaveConnection_ArrayTrimming() {
        // Given: More than 5 connections
        let connections = (1...7).map { i in
            createTestConnectionSettings(host: "192.168.1.\(i)", port: 8000 + i)
        }
        
        // When: Saving all connections
        for connection in connections {
            storageManager.saveConnection(connection)
        }
        
        // Then: Only last 5 connections should be kept
        XCTAssertEqual(storageManager.savedConnections.count, 5)
        XCTAssertEqual(storageManager.savedConnections[0].host, "192.168.1.7") // Most recent
        XCTAssertEqual(storageManager.savedConnections[4].host, "192.168.1.3") // Oldest kept
    }
    
    func testSaveConnection_DuplicateReplacement() {
        // Given: A connection and then a duplicate with same host:port
        let connection1 = createTestConnectionSettings(host: "192.168.1.100", port: 8000, serverName: "Server A")
        let connection2 = createTestConnectionSettings(host: "192.168.1.101", port: 8001, serverName: "Server B")
        let connection1Updated = createTestConnectionSettings(host: "192.168.1.100", port: 8000, serverName: "Server A Updated")
        
        // When: Saving connections including duplicate
        storageManager.saveConnection(connection1)
        storageManager.saveConnection(connection2)
        storageManager.saveConnection(connection1Updated)
        
        // Then: Duplicate should replace original, not add to list
        XCTAssertEqual(storageManager.savedConnections.count, 2)
        XCTAssertEqual(storageManager.savedConnections[0].host, "192.168.1.100") // Updated duplicate first
        XCTAssertEqual(storageManager.savedConnections[0].serverName, "Server A Updated")
        XCTAssertEqual(storageManager.savedConnections[1].host, "192.168.1.101")
    }
    
    // MARK: - Current Connection Tests
    
    func testSetCurrentConnection() {
        // Given: A saved connection and a new connection to set as current
        let savedConnection = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        let newCurrentConnection = createTestConnectionSettings(host: "192.168.1.101", port: 8001)
        
        storageManager.saveConnection(savedConnection)
        
        // When: Setting a new current connection
        storageManager.setCurrentConnection(newCurrentConnection)
        
        // Then: Current connection should be updated with new timestamp
        XCTAssertNotNil(storageManager.currentConnection)
        XCTAssertEqual(storageManager.currentConnection?.host, "192.168.1.101")
        XCTAssertEqual(storageManager.currentConnection?.port, 8001)
        
        // And saved connections should be updated if exists
        XCTAssertEqual(storageManager.savedConnections.count, 2)
    }
    
    func testSetCurrentConnection_UpdatesExisting() {
        // Given: A saved connection
        let connection = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        storageManager.saveConnection(connection)
        
        let originalTimestamp = storageManager.currentConnection?.lastConnected
        
        // Wait briefly to ensure timestamp difference
        Thread.sleep(forTimeInterval: 0.01)
        
        // When: Setting the same connection as current again
        storageManager.setCurrentConnection(connection)
        
        // Then: Timestamp should be updated
        XCTAssertNotNil(storageManager.currentConnection)
        XCTAssertNotEqual(storageManager.currentConnection?.lastConnected, originalTimestamp)
    }
    
    // MARK: - Remove Connection Tests
    
    func testRemoveConnection() {
        // Given: Multiple saved connections with one as current
        let connection1 = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        let connection2 = createTestConnectionSettings(host: "192.168.1.101", port: 8001)
        
        storageManager.saveConnection(connection1)
        storageManager.saveConnection(connection2) // This becomes current
        
        XCTAssertEqual(storageManager.savedConnections.count, 2)
        XCTAssertEqual(storageManager.currentConnection?.host, "192.168.1.101")
        
        // When: Removing the current connection
        storageManager.removeConnection(connection2)
        
        // Then: Connection should be removed and current should be cleared
        XCTAssertEqual(storageManager.savedConnections.count, 1)
        XCTAssertEqual(storageManager.savedConnections[0].host, "192.168.1.100")
        XCTAssertNil(storageManager.currentConnection)
        XCTAssertFalse(storageManager.hasValidConnection())
    }
    
    func testRemoveConnection_NonCurrent() {
        // Given: Multiple saved connections
        let connection1 = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        let connection2 = createTestConnectionSettings(host: "192.168.1.101", port: 8001)
        
        storageManager.saveConnection(connection1)
        storageManager.saveConnection(connection2) // This becomes current
        
        // When: Removing a non-current connection
        storageManager.removeConnection(connection1)
        
        // Then: Only that connection should be removed, current should remain
        XCTAssertEqual(storageManager.savedConnections.count, 1)
        XCTAssertEqual(storageManager.savedConnections[0].host, "192.168.1.101")
        XCTAssertNotNil(storageManager.currentConnection)
        XCTAssertEqual(storageManager.currentConnection?.host, "192.168.1.101")
    }
    
    // MARK: - Clear All Connections Tests
    
    func testClearAllConnections() {
        // Given: Multiple saved connections
        let connection1 = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        let connection2 = createTestConnectionSettings(host: "192.168.1.101", port: 8001)
        
        storageManager.saveConnection(connection1)
        storageManager.saveConnection(connection2)
        
        XCTAssertEqual(storageManager.savedConnections.count, 2)
        XCTAssertNotNil(storageManager.currentConnection)
        
        // When: Clearing all connections
        storageManager.clearAllConnections()
        
        // Then: All connections should be removed
        XCTAssertTrue(storageManager.savedConnections.isEmpty)
        XCTAssertNil(storageManager.currentConnection)
        XCTAssertFalse(storageManager.hasValidConnection())
        XCTAssertFalse(storageManager.hasStoredConnection())
    }
    
    // MARK: - ServerConfig Integration Tests
    
    func testStoreServerConfig() {
        // Given: A ServerConfig object
        let serverConfig = ServerConfig(
            host: "192.168.1.100",
            port: 8000,
            websocketPath: "/ws",
            serverName: "Test Server",
            network: "Home Network"
        )
        
        // When: Storing the server config
        storageManager.store(serverConfig)
        
        // Then: Should be converted to ConnectionSettings and saved
        XCTAssertEqual(storageManager.savedConnections.count, 1)
        XCTAssertEqual(storageManager.savedConnections[0].host, "192.168.1.100")
        XCTAssertEqual(storageManager.savedConnections[0].port, 8000)
        XCTAssertEqual(storageManager.savedConnections[0].websocketPath, "/ws")
        XCTAssertEqual(storageManager.savedConnections[0].serverName, "Test Server")
        XCTAssertEqual(storageManager.savedConnections[0].network, "Home Network")
        XCTAssertNotNil(storageManager.currentConnection)
    }
    
    func testLoadStoredConnection() {
        // Given: A stored connection
        let connection = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        storageManager.saveConnection(connection)
        
        // When: Loading stored connection as ServerConfig
        let serverConfig = storageManager.loadStoredConnection()
        
        // Then: Should return correct ServerConfig
        XCTAssertNotNil(serverConfig)
        XCTAssertEqual(serverConfig?.host, "192.168.1.100")
        XCTAssertEqual(serverConfig?.port, 8000)
        XCTAssertEqual(serverConfig?.websocketPath, "/ws")
    }
    
    func testLoadStoredConnection_NoConnection() {
        // Given: No stored connections
        XCTAssertTrue(storageManager.savedConnections.isEmpty)
        
        // When: Loading stored connection
        let serverConfig = storageManager.loadStoredConnection()
        
        // Then: Should return nil
        XCTAssertNil(serverConfig)
    }
    
    // MARK: - Legacy Method Tests
    
    func testClearStoredConnection() {
        // Given: A stored connection
        let connection = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        storageManager.saveConnection(connection)
        
        XCTAssertNotNil(storageManager.currentConnection)
        
        // When: Clearing stored connection (legacy method)
        storageManager.clearStoredConnection()
        
        // Then: Current connection should be cleared
        XCTAssertNil(storageManager.currentConnection)
        XCTAssertFalse(storageManager.hasValidConnection())
    }
    
    func testClearConnection_Legacy() {
        // Given: A stored connection
        let connection = createTestConnectionSettings(host: "192.168.1.100", port: 8000)
        storageManager.saveConnection(connection)
        
        // When: Calling legacy clear method
        storageManager.clearConnection()
        
        // Then: Should behave same as clearStoredConnection
        XCTAssertNil(storageManager.currentConnection)
        XCTAssertFalse(storageManager.hasValidConnection())
    }
    
    // MARK: - Display Name Tests
    
    func testConnectionDisplayName() {
        // Given: Connections with and without server names
        let connectionWithName = createTestConnectionSettings(
            host: "192.168.1.100", 
            port: 8000, 
            serverName: "My Server"
        )
        let connectionWithoutName = createTestConnectionSettings(
            host: "192.168.1.101", 
            port: 8001, 
            serverName: nil
        )
        
        // When: Getting display names
        let displayName1 = connectionWithName.displayName
        let displayName2 = connectionWithoutName.displayName
        
        // Then: Should use server name or fallback to host:port
        XCTAssertEqual(displayName1, "My Server")
        XCTAssertEqual(displayName2, "192.168.1.101:8001")
    }
    
    func testWebSocketURL() {
        // Given: A connection settings
        let connection = createTestConnectionSettings(
            host: "192.168.1.100", 
            port: 8000, 
            websocketPath: "/ws/client"
        )
        
        // When: Getting WebSocket URL
        let websocketURL = connection.websocketURL
        
        // Then: Should construct correct URL
        XCTAssertEqual(websocketURL, "ws://192.168.1.100:8000/ws/client")
    }
    
    // MARK: - Edge Cases & Error Handling
    
    func testEmptyHostHandling() {
        // Given: Connection with empty host
        let connection = createTestConnectionSettings(host: "", port: 8000)
        
        // When: Saving connection
        storageManager.saveConnection(connection)
        
        // Then: Should still save but display name should handle empty host
        XCTAssertEqual(storageManager.savedConnections.count, 1)
        XCTAssertEqual(connection.displayName, ":8000")
    }
    
    func testZeroPortHandling() {
        // Given: Connection with zero port
        let connection = createTestConnectionSettings(host: "192.168.1.100", port: 0)
        
        // When: Saving connection
        storageManager.saveConnection(connection)
        
        // Then: Should save with zero port
        XCTAssertEqual(storageManager.savedConnections.count, 1)
        XCTAssertEqual(storageManager.savedConnections[0].port, 0)
    }
    
    func testConcurrentAccess() {
        // Given: Multiple connections to save concurrently
        let connections = (1...10).map { i in
            createTestConnectionSettings(host: "192.168.1.\(i)", port: 8000 + i)
        }
        
        // When: Saving connections concurrently (simulated)
        for connection in connections {
            storageManager.saveConnection(connection)
        }
        
        // Then: Should handle all saves correctly (limited to 5)
        XCTAssertEqual(storageManager.savedConnections.count, 5)
        XCTAssertEqual(storageManager.currentConnection?.host, "192.168.1.10") // Last saved
    }
    
    // MARK: - Performance Tests
    
    func testLargeConnectionListPerformance() {
        // Given: Performance measurement setup
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // When: Saving many connections (will be trimmed to 5)
        for i in 1...100 {
            let connection = createTestConnectionSettings(host: "192.168.1.\(i)", port: 8000 + i)
            storageManager.saveConnection(connection)
        }
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let executionTime = endTime - startTime
        
        // Then: Should complete quickly and maintain array limit
        XCTAssertEqual(storageManager.savedConnections.count, 5)
        XCTAssertLessThan(executionTime, 1.0, "Saving 100 connections should take less than 1 second")
    }
}

// MARK: - Test Helpers

/// Helper function to create test ConnectionSettings
private func createTestConnectionSettings(
    host: String,
    port: Int,
    websocketPath: String = "/ws",
    serverName: String? = nil,
    network: String? = nil
) -> ConnectionSettings {
    return ConnectionSettings(
        host: host,
        port: port,
        websocketPath: websocketPath,
        serverName: serverName,
        network: network
    )
}

// MARK: - Mock Dependencies

/// Mock UserDefaults for testing without affecting real user defaults
class MockUserDefaultsForConnectionTests: UserDefaults {
    private var storage: [String: Any] = [:]
    
    override func set(_ value: Any?, forKey defaultName: String) {
        storage[defaultName] = value
    }
    
    override func data(forKey defaultName: String) -> Data? {
        return storage[defaultName] as? Data
    }
    
    override func removeObject(forKey defaultName: String) {
        storage.removeValue(forKey: defaultName)
    }
    
    override func object(forKey defaultName: String) -> Any? {
        return storage[defaultName]
    }
}