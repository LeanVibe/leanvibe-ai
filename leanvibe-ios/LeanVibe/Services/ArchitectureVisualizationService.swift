import Foundation
import Combine

@MainActor
class ArchitectureVisualizationService: ObservableObject {
    @Published var diagram: ArchitectureDiagram?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var selectedNode: DiagramNode?
    @Published var lastUpdated: Date?
    @Published var hasChanges = false

    private var baseURL: URL? {
        // Use the same configuration as the rest of the app - NO HARDCODED FALLBACKS
        let config = AppConfiguration.shared
        guard config.isBackendConfigured else {
            return nil
        }
        return URL(string: config.apiBaseURL)
    }
    private var webSocketService: WebSocketService
    private var cancellables = Set<AnyCancellable>()
    private var architectureChangeTimer: Timer?
    @Published var lastKnownDiagram: ArchitectureDiagram?
    private var clientId: String = ""

    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        self.clientId = "ios_\(UUID().uuidString.prefix(8))"
        subscribeToMessages()
        startArchitectureMonitoring()
    }

    private func subscribeToMessages() {
        webSocketService.$messages
            .receive(on: DispatchQueue.main)
            .sink { [weak self] messages in
                guard let self = self else { return }
                if let latestMessage = messages.last, !latestMessage.isFromUser {
                    self.handleIncomingMessage(latestMessage)
                }
            }
            .store(in: &cancellables)
    }

    func fetchInitialDiagram(for projectId: String) async {
        await fetchDiagramFromBackend(projectId: projectId)
    }

    func requestDiagramUpdate(for nodeId: String, in projectId: String) async {
        let request = ["command": "/architecture_node", "nodeId": nodeId, "projectId": projectId]
        await sendMessage(request)
    }
    
    private func fetchDiagramFromBackend(projectId: String) async {
        isLoading = true
        errorMessage = nil
        
        // Check if backend is configured
        guard let baseURL = baseURL else {
            errorMessage = "Backend not configured. Please scan QR code or configure backend URL in Settings."
            isLoading = false
            return
        }
        
        do {
            // First try graph/architecture endpoint (Neo4j-based)
            let archUrl = baseURL.appendingPathComponent("graph/architecture/\(clientId)")
            var archRequest = URLRequest(url: archUrl)
            archRequest.httpMethod = "GET"
            
            let (archData, archResponse) = try await URLSession.shared.data(for: archRequest)
            
            if let httpResponse = archResponse as? HTTPURLResponse, httpResponse.statusCode == 200 {
                // Parse graph architecture response
                if let jsonObject = try JSONSerialization.jsonObject(with: archData) as? [String: Any],
                   let architecture = jsonObject["architecture"] as? [String: Any] {
                    
                    // Convert graph data to mermaid diagram
                    let mermaidDefinition = generateMermaidFromGraphData(architecture)
                    
                    let diagram = ArchitectureDiagram(
                        name: "Project Architecture",
                        mermaidDefinition: mermaidDefinition,
                        description: "Generated from graph analysis",
                        diagramType: "architecture"
                    )
                    
                    self.diagram = diagram
                    isLoading = false
                    return
                }
            }
            
            // Fallback to visualization endpoint
            let vizUrl = baseURL.appendingPathComponent("visualization/\(clientId)/generate")
            var vizRequest = URLRequest(url: vizUrl)
            vizRequest.httpMethod = "POST"
            vizRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            let requestBody = [
                "project_id": projectId,
                "diagram_type": "architecture_overview"
            ]
            
            vizRequest.httpBody = try JSONEncoder().encode(requestBody)
            
            let (vizData, vizResponse) = try await URLSession.shared.data(for: vizRequest)
            
            guard let httpResponse = vizResponse as? HTTPURLResponse else {
                errorMessage = "Invalid response from server"
                isLoading = false
                return
            }
            
            if httpResponse.statusCode == 200 {
                // Parse visualization response
                if let jsonObject = try JSONSerialization.jsonObject(with: vizData) as? [String: Any],
                   let diagramData = jsonObject["diagram"] as? [String: Any] {
                    
                    let diagram = parseDiagramFromResponse(diagramData)
                    self.diagram = diagram
                } else {
                    errorMessage = "Invalid diagram data format"
                }
            } else {
                // Try to get error message from response
                if let jsonObject = try JSONSerialization.jsonObject(with: vizData) as? [String: Any],
                   let error = jsonObject["error"] as? String {
                    errorMessage = "Server error: \(error)"
                } else {
                    errorMessage = "Server error: \(httpResponse.statusCode)"
                }
            }
            
        } catch {
            errorMessage = "Network error: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    private func generateMermaidFromGraphData(_ graphData: [String: Any]) -> String {
        // Convert graph architecture data to Mermaid syntax
        var mermaid = "graph TD\n"
        
        if let patterns = graphData["patterns"] as? [[String: Any]] {
            for (index, pattern) in patterns.enumerated() {
                let patternName = pattern["pattern_name"] as? String ?? "Pattern\(index)"
                let confidence = pattern["confidence"] as? Double ?? 0.0
                let components = pattern["components"] as? [String] ?? []
                
                mermaid += "    subgraph \"\(patternName) (\(Int(confidence * 100))%)\"\n"
                
                for component in components {
                    let nodeId = component.replacingOccurrences(of: ".", with: "_")
                    mermaid += "        \(nodeId)[\(component)]\n"
                }
                
                mermaid += "    end\n"
            }
        } else {
            // Fallback: simple architecture view
            mermaid += "    A[Frontend] --> B[Backend]\n"
            mermaid += "    B --> C[Database]\n"
            mermaid += "    B --> D[Cache]\n"
        }
        
        return mermaid
    }
    
    private func parseDiagramFromResponse(_ diagramData: [String: Any]) -> ArchitectureDiagram {
        // Parse backend diagram response into iOS model
        let title = diagramData["title"] as? String ?? "Architecture Diagram"
        
        // Check if it's a MermaidDiagram
        if let content = diagramData["content"] as? String {
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: content,
                description: diagramData["description"] as? String,
                diagramType: diagramData["diagram_type"] as? String ?? "architecture"
            )
        }
        
        // Generate Mermaid from nodes/edges structure
        var mermaid = "graph TD\n"
        
        if let nodes = diagramData["nodes"] as? [[String: Any]] {
            for node in nodes {
                let nodeId = node["id"] as? String ?? "unknown"
                let label = node["label"] as? String ?? nodeId
                mermaid += "    \(nodeId)[\(label)]\n"
            }
        }
        
        if let edges = diagramData["edges"] as? [[String: Any]] {
            for edge in edges {
                let source = edge["source_id"] as? String ?? "unknown"
                let target = edge["target_id"] as? String ?? "unknown"
                mermaid += "    \(source) --> \(target)\n"
            }
        }
        
        return ArchitectureDiagram(
            name: title,
            mermaidDefinition: mermaid,
            description: diagramData["description"] as? String,
            diagramType: diagramData["diagram_type"] as? String ?? "architecture"
        )
    }
    
    // MARK: - Real-time Architecture Monitoring
    
    private func startArchitectureMonitoring() {
        // Poll for architecture changes every 30 seconds
        architectureChangeTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                await self?.checkForArchitectureChanges()
            }
        }
    }
    
    private func stopArchitectureMonitoring() {
        architectureChangeTimer?.invalidate()
        architectureChangeTimer = nil
    }
    
    private func checkForArchitectureChanges() async {
        guard let currentDiagram = diagram else { return }
        
        // Check if backend is configured
        guard let baseURL = baseURL else { return }
        
        // Fetch latest diagram silently
        let currentProjectId = "default_project" // This should be dynamic based on current context
        
        do {
            let url = baseURL.appendingPathComponent("graph/architecture/\(clientId)")
            var request = URLRequest(url: url)
            request.httpMethod = "GET"
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                return
            }
            
            // Parse graph architecture response
            if let jsonObject = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let architecture = jsonObject["architecture"] as? [String: Any] {
                
                // Convert graph data to mermaid diagram
                let mermaidDefinition = generateMermaidFromGraphData(architecture)
                
                let latestDiagram = ArchitectureDiagram(
                    name: "Project Architecture",
                    mermaidDefinition: mermaidDefinition,
                    description: "Generated from graph analysis",
                    diagramType: "architecture"
                )
            
                // Compare diagrams
                if latestDiagram != currentDiagram {
                    self.hasChanges = true
                    self.lastKnownDiagram = latestDiagram
                    self.lastUpdated = Date()
                    
                    // Send notification about changes
                    NotificationCenter.default.post(
                        name: NSNotification.Name("ArchitectureChangesDetected"),
                        object: self,
                        userInfo: ["newDiagram": latestDiagram, "oldDiagram": currentDiagram]
                    )
                }
            }
            
        } catch {
            print("Error checking for architecture changes: \(error)")
        }
    }
    
    func acceptChanges() {
        if let latestDiagram = lastKnownDiagram {
            self.diagram = latestDiagram
            self.hasChanges = false
            self.lastKnownDiagram = nil
        }
    }
    
    func rejectChanges() {
        self.hasChanges = false
        self.lastKnownDiagram = nil
    }
    
    func stopMonitoring() {
        stopArchitectureMonitoring()
    }

    private func sendMessage(_ request: [String: String]) async {
        isLoading = true
        errorMessage = nil
        do {
            let data = try JSONEncoder().encode(request)
            guard let jsonString = String(data: data, encoding: .utf8) else {
                errorMessage = "Failed to encode request"
                isLoading = false
                return
            }
            webSocketService.sendCommand(jsonString)
        } catch {
            errorMessage = "Error sending message: \(error.localizedDescription)"
            isLoading = false
        }
    }

    private func handleIncomingMessage(_ message: AgentMessage) {
        guard message.type == .response else { return }

        isLoading = true
        errorMessage = nil
        
        do {
            guard let messageData = message.content.data(using: .utf8) else {
                errorMessage = "Could not get data from message content"
                isLoading = false
                return
            }
            
            let agentResponse = try JSONDecoder().decode(AgentResponse.self, from: messageData)

            if let responseData = agentResponse.data, 
               let fileInfo = responseData.files?.first {
                let diagramDataString = fileInfo.name
                if let diagramData = diagramDataString.data(using: .utf8),
                   let newDiagram = try? JSONDecoder().decode(ArchitectureDiagram.self, from: diagramData) {
                    self.diagram = newDiagram
                }
            } else if !agentResponse.message.isEmpty {
                 self.errorMessage = agentResponse.message
            }
            self.isLoading = false
        } catch {
            self.errorMessage = "Failed to decode architecture diagram: \(error.localizedDescription)"
            self.isLoading = false
        }
    }
}
