
import Foundation
import Combine

@MainActor
class ArchitectureVisualizationService: ObservableObject {
    @Published var currentDiagram: ArchitectureDiagram?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var availableDiagramTypes: [DiagramType] = []
    @Published var selectedDiagramType: DiagramType = .architectureOverview
    @Published var zoomScale: CGFloat = 1.0

    private let baseURL = URL(string: "http://localhost:8000")!
    private let webSocketService: WebSocketService
    private var cancellables = Set<AnyCancellable>()

    init(webSocketService: WebSocketService = WebSocketService()) {
        self.webSocketService = webSocketService
        setupWebSocketListener()
        loadAvailableDiagramTypes()
    }

    private func setupWebSocketListener() {
        webSocketService.messagesPublisher
            .sink { [weak self] message in
                Task { @MainActor in
                    if message.type == "architecture_response" {
                        await self?.handleArchitectureResponse(message)
                    }
                }
            }
            .store(in: &cancellables)
    }

    private func loadAvailableDiagramTypes() {
        availableDiagramTypes = [
            .architectureOverview,
            .componentDiagram,
            .sequenceDiagram,
            .flowChart,
            .classDiagram
        ]
    }

    func fetchProjectArchitecture(clientId: String, diagramType: DiagramType? = nil) async {
        isLoading = true
        errorMessage = nil
        
        let typeToUse = diagramType ?? selectedDiagramType
        
        do {
            // Try WebSocket first for real-time updates
            let request = [
                "type": "get_architecture",
                "project_id": clientId,
                "diagram_type": typeToUse.rawValue,
                "format": "mermaid"
            ]
            
            try await webSocketService.sendMessage(request)
            
            // Fallback to HTTP if WebSocket not available
            if !webSocketService.isConnected {
                await fetchArchitectureViaHTTP(clientId: clientId, diagramType: typeToUse)
            }
            
        } catch {
            await fetchArchitectureViaHTTP(clientId: clientId, diagramType: typeToUse)
        }
    }
    
    private func fetchArchitectureViaHTTP(clientId: String, diagramType: DiagramType) async {
        let url = baseURL
            .appendingPathComponent("visualization")
            .appendingPathComponent(clientId)
            .appendingPathComponent("diagram")
            .appendingPathComponent(diagramType.rawValue)
        
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(VisualizationResponse.self, from: data)
            
            if let diagramData = response.diagram {
                self.currentDiagram = ArchitectureDiagram(
                    id: UUID(),
                    name: diagramData.name ?? "Architecture Diagram",
                    mermaidDefinition: diagramData.mermaidDefinition ?? generateFallbackDiagram()
                )
            } else {
                self.currentDiagram = createFallbackDiagram()
            }
        } catch {
            self.errorMessage = "Failed to fetch architecture diagram: \(error.localizedDescription)"
            self.currentDiagram = createFallbackDiagram()
        }
        
        isLoading = false
    }
    
    private func handleArchitectureResponse(_ message: AgentMessage) async {
        // Handle WebSocket architecture response
        if let data = message.data,
           let mermaidDef = data["mermaid_definition"] as? String {
            
            self.currentDiagram = ArchitectureDiagram(
                id: UUID(),
                name: data["name"] as? String ?? "Architecture Diagram",
                mermaidDefinition: mermaidDef
            )
        } else {
            self.currentDiagram = createFallbackDiagram()
        }
        
        isLoading = false
    }
    
    func refreshDiagram(clientId: String) async {
        await fetchProjectArchitecture(clientId: clientId)
    }
    
    func switchDiagramType(_ type: DiagramType, clientId: String) async {
        selectedDiagramType = type
        await fetchProjectArchitecture(clientId: clientId, diagramType: type)
    }
    
    func exportDiagram() -> String? {
        return currentDiagram?.mermaidDefinition
    }
    
    // Comparison functionality
    func fetchDiagramComparison(clientId: String, beforeCommit: String, afterCommit: String) async {
        isLoading = true
        errorMessage = nil
        
        // Implementation for diagram comparison
        // This would fetch two diagrams and show them side by side
        
        isLoading = false
    }
    
    private func createFallbackDiagram() -> ArchitectureDiagram {
        return ArchitectureDiagram(
            id: UUID(),
            name: "Demo Architecture",
            mermaidDefinition: generateFallbackDiagram()
        )
    }
    
    private func generateFallbackDiagram() -> String {
        return """
        graph TD
            A[LeenVibe iOS App] --> B[WebSocket Service]
            B --> C[Backend APIs]
            C --> D[Task Management]
            C --> E[Architecture Analysis]
            C --> F[AI Services]
            
            D --> G[Kanban Board]
            E --> H[Code Analysis]
            F --> I[MLX Models]
            
            style A fill:#e1f5fe
            style C fill:#f3e5f5
            style G fill:#e8f5e8
            style H fill:#fff3e0
            style I fill:#fce4ec
        """
    }
}

// Supporting types
enum DiagramType: String, CaseIterable, Identifiable {
    case architectureOverview = "architecture_overview"
    case componentDiagram = "component_diagram"
    case sequenceDiagram = "sequence_diagram" 
    case flowChart = "flow_chart"
    case classDiagram = "class_diagram"
    
    var id: String { rawValue }
    
    var displayName: String {
        switch self {
        case .architectureOverview: return "Architecture Overview"
        case .componentDiagram: return "Component Diagram"
        case .sequenceDiagram: return "Sequence Diagram"
        case .flowChart: return "Flow Chart"
        case .classDiagram: return "Class Diagram"
        }
    }
}

struct VisualizationResponse: Decodable {
    let diagram: DiagramData?
    let clientId: String?
    
    struct DiagramData: Decodable {
        let name: String?
        let mermaidDefinition: String?
        
        enum CodingKeys: String, CodingKey {
            case name
            case mermaidDefinition = "mermaid_definition"
        }
    }
}
