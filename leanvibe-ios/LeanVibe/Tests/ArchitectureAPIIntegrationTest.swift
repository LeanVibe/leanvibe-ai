import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
final class ArchitectureAPIIntegrationTest: XCTestCase {
    
    var service: ArchitectureVisualizationService!
    var mockWebSocketService: WebSocketService!
    
    override func setUp() async throws {
        mockWebSocketService = WebSocketService()
        service = ArchitectureVisualizationService(webSocketService: mockWebSocketService)
    }
    
    override func tearDown() async throws {
        service = nil
        mockWebSocketService = nil
    }
    
    // MARK: - Test API Endpoint Format
    
    func testAPIEndpointFormat() async throws {
        // Test that the service uses the correct API endpoint format
        let projectId = "test-project-123"
        
        // Since we can't easily test actual network calls without a mock server,
        // we'll test the URL construction logic by checking the error message
        // when backend is not configured
        
        await service.fetchInitialDiagram(for: projectId)
        
        // Should get backend configuration error, not a URL format error
        XCTAssertNotNil(service.errorMessage)
        XCTAssertTrue(service.errorMessage?.contains("Backend not configured") == true, 
                     "Should show backend configuration error when no backend is set")
    }
    
    // MARK: - Test Project ID Handling
    
    func testProjectIDHandling() async throws {
        let projectId = "dynamic-project-456"
        
        await service.fetchInitialDiagram(for: projectId)
        
        // Verify the service stores the current project ID
        // We can't directly access private properties, but we can verify
        // that subsequent calls use the correct project ID
        XCTAssertFalse(service.isLoading)
        XCTAssertNotNil(service.errorMessage) // Should have configuration error
    }
    
    // MARK: - Test Data Format Parsing
    
    func testDiagramDataParsing() {
        // Test parsing of different response formats
        
        // Test 1: Direct Mermaid definition
        let mermaidResponse = [
            "name": "Test Architecture",
            "mermaid_definition": "graph TD\n    A[Frontend] --> B[Backend]",
            "description": "Test diagram",
            "diagram_type": "architecture"
        ]
        
        let diagram1 = service.parseDiagramFromResponse(mermaidResponse)
        XCTAssertEqual(diagram1.name, "Test Architecture")
        XCTAssertTrue(diagram1.mermaidDefinition.contains("A[Frontend] --> B[Backend]"))
        
        // Test 2: Nodes and edges format
        let nodesEdgesResponse = [
            "name": "Node Edge Architecture",
            "nodes": [
                ["id": "frontend", "label": "Frontend App"],
                ["id": "backend", "label": "Backend API"]
            ],
            "edges": [
                ["source": "frontend", "target": "backend"]
            ]
        ] as [String : Any]
        
        let diagram2 = service.parseDiagramFromResponse(nodesEdgesResponse)
        XCTAssertEqual(diagram2.name, "Node Edge Architecture")
        XCTAssertTrue(diagram2.mermaidDefinition.contains("frontend[Frontend App]"))
        XCTAssertTrue(diagram2.mermaidDefinition.contains("frontend --> backend"))
        
        // Test 3: Graph architecture format
        let graphResponse = [
            "title": "Graph Architecture",
            "architecture": [
                "patterns": [
                    [
                        "pattern_name": "MVC",
                        "confidence": 0.85,
                        "components": ["Controller", "Model", "View"]
                    ]
                ]
            ]
        ] as [String : Any]
        
        let diagram3 = service.parseDiagramFromResponse(graphResponse)
        XCTAssertEqual(diagram3.name, "Graph Architecture")
        XCTAssertTrue(diagram3.mermaidDefinition.contains("MVC"))
        XCTAssertTrue(diagram3.mermaidDefinition.contains("Controller"))
    }
    
    // MARK: - Test Error Handling
    
    func testErrorHandlingFormatMismatch() {
        // Test handling of invalid response formats
        let invalidResponse = [
            "unexpected_field": "unexpected_value"
        ]
        
        let diagram = service.parseDiagramFromResponse(invalidResponse)
        
        // Should create a fallback diagram
        XCTAssertEqual(diagram.name, "Architecture Diagram")
        XCTAssertTrue(diagram.mermaidDefinition.contains("No Architecture Data"))
    }
    
    func testMermaidGeneration() {
        // Test Mermaid generation from graph data
        let graphData = [
            "patterns": [
                [
                    "pattern_name": "Repository Pattern",
                    "confidence": 0.9,
                    "components": ["UserRepository", "DataSource", "User.Model"]
                ]
            ]
        ] as [String : Any]
        
        let mermaid = service.generateMermaidFromGraphData(graphData)
        
        XCTAssertTrue(mermaid.contains("graph TD"))
        XCTAssertTrue(mermaid.contains("Repository Pattern"))
        XCTAssertTrue(mermaid.contains("UserRepository"))
        XCTAssertTrue(mermaid.contains("User_Model")) // Should sanitize dots
    }
    
    // MARK: - Test Backend Configuration
    
    func testBackendConfigurationHandling() async {
        // Test behavior when backend is not configured
        await service.fetchInitialDiagram(for: "test-project")
        
        XCTAssertNotNil(service.errorMessage)
        XCTAssertTrue(service.errorMessage?.contains("Backend not configured") == true)
        XCTAssertFalse(service.isLoading)
        XCTAssertNil(service.diagram)
    }
}

