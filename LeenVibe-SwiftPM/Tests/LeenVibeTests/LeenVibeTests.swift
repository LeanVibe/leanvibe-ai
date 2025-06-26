import XCTest
@testable import LeenVibe

final class LeenVibeTests: XCTestCase {
    func testAgentMessageCreation() throws {
        let message = AgentMessage(content: "Test message", isFromUser: true, type: .message)
        XCTAssertEqual(message.content, "Test message")
        XCTAssertTrue(message.isFromUser)
        XCTAssertEqual(message.type, .message)
    }
    
    func testWebSocketMessageEncoding() throws {
        let message = WebSocketMessage(
            type: "command",
            content: "/status",
            timestamp: "2025-06-26T12:00:00Z",
            clientId: "test-client"
        )
        
        let encoder = JSONEncoder()
        let data = try encoder.encode(message)
        
        let decoder = JSONDecoder()
        let decoded = try decoder.decode(WebSocketMessage.self, from: data)
        
        XCTAssertEqual(decoded.type, "command")
        XCTAssertEqual(decoded.content, "/status")
        XCTAssertEqual(decoded.clientId, "test-client")
    }
    
    func testAgentResponseDecoding() throws {
        let jsonString = """
        {
            "status": "success",
            "type": "agent_status",
            "message": "Agent is ready",
            "processing_time": 0.123
        }
        """
        
        let data = jsonString.data(using: .utf8)!
        let decoder = JSONDecoder()
        let response = try decoder.decode(AgentResponse.self, from: data)
        
        XCTAssertEqual(response.status, "success")
        XCTAssertEqual(response.type, "agent_status")
        XCTAssertEqual(response.message, "Agent is ready")
        XCTAssertEqual(response.processingTime, 0.123, accuracy: 0.001)
    }
    
    @MainActor
    func testWebSocketServiceInitialization() throws {
        let service = WebSocketService()
        XCTAssertFalse(service.isConnected)
        XCTAssertEqual(service.connectionStatus, "Disconnected")
        XCTAssertTrue(service.messages.isEmpty)
    }
}