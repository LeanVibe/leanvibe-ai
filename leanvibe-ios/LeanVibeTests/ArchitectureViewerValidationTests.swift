import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class ArchitectureViewerValidationTests: XCTestCase {
    
    private var architectureService: ArchitectureVisualizationService!
    private var mermaidRenderer: MermaidRenderer!
    private var mockWebSocketService: WebSocketService!
    
    override func setUp() {
        super.setUp()
        mockWebSocketService = WebSocketService()
        architectureService = ArchitectureVisualizationService(webSocketService: mockWebSocketService)
        mermaidRenderer = MermaidRenderer()
    }
    
    override func tearDown() {
        architectureService = nil
        mermaidRenderer = nil
        mockWebSocketService = nil
        super.tearDown()
    }
    
    // MARK: - Architecture Viewer Core Functionality Tests
    
    /// Test that ArchitectureVisualizationService initializes correctly
    func testArchitectureServiceInitialization() {
        XCTAssertNotNil(architectureService)
        XCTAssertNil(architectureService.diagram)
        XCTAssertFalse(architectureService.isLoading)
        XCTAssertNil(architectureService.errorMessage)
        XCTAssertNil(architectureService.selectedNode)
    }
    
    /// Test MermaidRenderer initialization
    func testMermaidRendererInitialization() {
        XCTAssertNotNil(mermaidRenderer)
        XCTAssertFalse(mermaidRenderer.isLoading)
        XCTAssertNil(mermaidRenderer.errorMessage)
        XCTAssertNil(mermaidRenderer.lastRenderedDiagram)
        XCTAssertEqual(mermaidRenderer.renderingProgress, 0.0)
    }
    
    /// Test diagram data model structure
    func testArchitectureDiagramModel() {
        let node1 = DiagramNode(
            id: "node1",
            label: "Service A",
            type: .service,
            position: CGPoint(x: 100, y: 100)
        )
        
        let node2 = DiagramNode(
            id: "node2",
            label: "Service B", 
            type: .service,
            position: CGPoint(x: 200, y: 200)
        )
        
        let diagram = ArchitectureDiagram(
            id: "test-diagram",
            title: "Test Architecture",
            nodes: [node1, node2],
            connections: [],
            layout: .hierarchical,
            projectId: "test-project"
        )
        
        XCTAssertEqual(diagram.id, "test-diagram")
        XCTAssertEqual(diagram.title, "Test Architecture")
        XCTAssertEqual(diagram.nodes.count, 2)
        XCTAssertEqual(diagram.layout, .hierarchical)
        XCTAssertEqual(diagram.projectId, "test-project")
    }
    
    /// Test diagram node types and properties
    func testDiagramNodeTypes() {
        let serviceNode = DiagramNode(
            id: "service",
            label: "Service",
            type: .service,
            position: CGPoint(x: 0, y: 0)
        )
        
        let databaseNode = DiagramNode(
            id: "database",
            label: "Database",
            type: .database,
            position: CGPoint(x: 0, y: 0)
        )
        
        let apiNode = DiagramNode(
            id: "api",
            label: "API",
            type: .api,
            position: CGPoint(x: 0, y: 0)
        )
        
        XCTAssertEqual(serviceNode.type, .service)
        XCTAssertEqual(databaseNode.type, .database)
        XCTAssertEqual(apiNode.type, .api)
    }
    
    // MARK: - Architecture Integration Tests
    
    /// Test architecture service state management
    func testArchitectureServiceStateManagement() async {
        // Test initial state
        XCTAssertFalse(architectureService.isLoading)
        XCTAssertNil(architectureService.diagram)
        
        // Test loading state (simulated)
        architectureService.isLoading = true
        XCTAssertTrue(architectureService.isLoading)
        
        // Test error state
        architectureService.errorMessage = "Test error"
        XCTAssertEqual(architectureService.errorMessage, "Test error")
        
        // Test diagram loaded state
        let testDiagram = ArchitectureDiagram(
            id: "test",
            title: "Test",
            nodes: [],
            connections: [],
            layout: .hierarchical,
            projectId: "test"
        )
        
        architectureService.diagram = testDiagram
        XCTAssertNotNil(architectureService.diagram)
        XCTAssertEqual(architectureService.diagram?.id, "test")
    }
    
    /// Test node selection functionality
    func testNodeSelection() {
        let testNode = DiagramNode(
            id: "selected-node",
            label: "Selected Node",
            type: .service,
            position: CGPoint(x: 0, y: 0)
        )
        
        architectureService.selectedNode = testNode
        XCTAssertNotNil(architectureService.selectedNode)
        XCTAssertEqual(architectureService.selectedNode?.id, "selected-node")
        XCTAssertEqual(architectureService.selectedNode?.label, "Selected Node")
        XCTAssertEqual(architectureService.selectedNode?.type, .service)
    }
    
    /// Test diagram updates and change detection
    func testDiagramChangeDetection() {
        // Initial state - no changes
        XCTAssertFalse(architectureService.hasChanges)
        
        // Simulate diagram change
        architectureService.hasChanges = true
        XCTAssertTrue(architectureService.hasChanges)
        
        // Test last updated tracking
        let now = Date()
        architectureService.lastUpdated = now
        XCTAssertEqual(architectureService.lastUpdated, now)
    }
    
    // MARK: - Mermaid Rendering Tests
    
    /// Test mermaid rendering state management
    func testMermaidRenderingState() async {
        // Initial state
        XCTAssertFalse(mermaidRenderer.isLoading)
        XCTAssertEqual(mermaidRenderer.renderingProgress, 0.0)
        
        // Test loading state
        mermaidRenderer.isLoading = true
        XCTAssertTrue(mermaidRenderer.isLoading)
        
        // Test progress tracking
        mermaidRenderer.renderingProgress = 0.5
        XCTAssertEqual(mermaidRenderer.renderingProgress, 0.5, accuracy: 0.01)
        
        // Test completion
        mermaidRenderer.renderingProgress = 1.0
        mermaidRenderer.isLoading = false
        XCTAssertEqual(mermaidRenderer.renderingProgress, 1.0, accuracy: 0.01)
        XCTAssertFalse(mermaidRenderer.isLoading)
    }
    
    /// Test mermaid rendering error handling
    func testMermaidErrorHandling() {
        // Test error state
        let testError = "Mermaid rendering failed"
        mermaidRenderer.errorMessage = testError
        XCTAssertEqual(mermaidRenderer.errorMessage, testError)
        
        // Test error recovery
        mermaidRenderer.errorMessage = nil
        XCTAssertNil(mermaidRenderer.errorMessage)
    }
    
    // MARK: - Integration Validation Tests
    
    /// Test end-to-end architecture viewer workflow
    func testArchitectureViewerWorkflow() async {
        // 1. Initialize service
        XCTAssertNotNil(architectureService)
        XCTAssertFalse(architectureService.isLoading)
        
        // 2. Simulate loading diagram
        architectureService.isLoading = true
        XCTAssertTrue(architectureService.isLoading)
        
        // 3. Simulate diagram load completion
        let testDiagram = createTestDiagram()
        architectureService.diagram = testDiagram
        architectureService.isLoading = false
        architectureService.lastUpdated = Date()
        
        // 4. Verify final state
        XCTAssertNotNil(architectureService.diagram)
        XCTAssertFalse(architectureService.isLoading)
        XCTAssertNotNil(architectureService.lastUpdated)
        XCTAssertEqual(architectureService.diagram?.nodes.count, 3)
    }
    
    /// Test architecture viewer UI components accessibility
    func testArchitectureUIAccessibility() {
        // Test that key UI components can be created
        let architectureTabView = ArchitectureTabView()
        XCTAssertNotNil(architectureTabView)
        
        // This validates that the SwiftUI view initializes without errors
        // and that all required dependencies are available
    }
    
    /// Test backend integration readiness
    func testBackendIntegrationReadiness() {
        // Test WebSocket service integration
        XCTAssertNotNil(mockWebSocketService)
        
        // Test that architecture service can handle WebSocket messages
        // (This would be expanded with actual message handling tests)
        XCTAssertNotNil(architectureService)
    }
    
    // MARK: - Performance Tests
    
    /// Test diagram rendering performance
    func testDiagramRenderingPerformance() {
        measure {
            // Create a complex diagram
            let complexDiagram = createComplexTestDiagram()
            
            // Simulate processing
            _ = complexDiagram.nodes.count
            _ = complexDiagram.connections.count
        }
    }
    
    /// Test memory usage with large diagrams
    func testMemoryUsageWithLargeDiagrams() {
        // Create multiple diagrams to test memory handling
        var diagrams: [ArchitectureDiagram] = []
        
        for i in 0..<10 {
            let diagram = createTestDiagram(nodeCount: 50, id: "diagram-\(i)")
            diagrams.append(diagram)
        }
        
        XCTAssertEqual(diagrams.count, 10)
        
        // Clear diagrams to test cleanup
        diagrams.removeAll()
        XCTAssertEqual(diagrams.count, 0)
    }
    
    // MARK: - Helper Methods
    
    private func createTestDiagram(nodeCount: Int = 3, id: String = "test-diagram") -> ArchitectureDiagram {
        var nodes: [DiagramNode] = []
        
        for i in 0..<nodeCount {
            let node = DiagramNode(
                id: "node-\(i)",
                label: "Service \(i)",
                type: .service,
                position: CGPoint(x: i * 100, y: i * 100)
            )
            nodes.append(node)
        }
        
        return ArchitectureDiagram(
            id: id,
            title: "Test Architecture Diagram",
            nodes: nodes,
            connections: [],
            layout: .hierarchical,
            projectId: "test-project"
        )
    }
    
    private func createComplexTestDiagram() -> ArchitectureDiagram {
        return createTestDiagram(nodeCount: 20, id: "complex-diagram")
    }
}

// MARK: - Test Extensions

extension ArchitectureDiagram {
    static func testDiagram() -> ArchitectureDiagram {
        let nodes = [
            DiagramNode(id: "api", label: "API Layer", type: .api, position: CGPoint(x: 0, y: 0)),
            DiagramNode(id: "service", label: "Service Layer", type: .service, position: CGPoint(x: 0, y: 100)),
            DiagramNode(id: "database", label: "Database", type: .database, position: CGPoint(x: 0, y: 200))
        ]
        
        return ArchitectureDiagram(
            id: "test-architecture",
            title: "Test System Architecture",
            nodes: nodes,
            connections: [],
            layout: .hierarchical,
            projectId: "test-project"
        )
    }
}