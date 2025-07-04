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
    private var currentProjectId: String?

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
        currentProjectId = projectId
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
            // Try standardized architecture endpoint with project ID
            let archUrl = baseURL.appendingPathComponent("api/projects/\(projectId)/architecture")
            var archRequest = URLRequest(url: archUrl)
            archRequest.httpMethod = "GET"
            archRequest.setValue("application/json", forHTTPHeaderField: "Accept")
            archRequest.setValue(clientId, forHTTPHeaderField: "X-Client-ID")
            
            let (archData, archResponse) = try await URLSession.shared.data(for: archRequest)
            
            if let httpResponse = archResponse as? HTTPURLResponse, httpResponse.statusCode == 200 {
                // Parse standardized architecture response
                if let jsonObject = try JSONSerialization.jsonObject(with: archData) as? [String: Any] {
                    
                    // Try to parse as a complete ArchitectureDiagram first
                    if let diagramData = try? JSONDecoder().decode(ArchitectureDiagram.self, from: archData) {
                        self.diagram = diagramData
                        isLoading = false
                        return
                    }
                    
                    // Fallback: Parse architecture data and convert to Mermaid
                    let diagram = parseDiagramFromResponse(jsonObject)
                    self.diagram = diagram
                    isLoading = false
                    return
                } else {
                    print("Warning: Primary architecture endpoint returned success but invalid JSON format")
                }
            } else if let httpResponse = archResponse as? HTTPURLResponse, httpResponse.statusCode == 404 {
                print("Primary architecture endpoint not found, trying fallback")
            } else if let httpResponse = archResponse as? HTTPURLResponse {
                print("Primary architecture endpoint failed with status: \(httpResponse.statusCode)")
            }
            
            // Fallback to alternative endpoint format
            let vizUrl = baseURL.appendingPathComponent("api/visualization/architecture")
            var vizRequest = URLRequest(url: vizUrl)
            vizRequest.httpMethod = "POST"
            vizRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            vizRequest.setValue("application/json", forHTTPHeaderField: "Accept")
            vizRequest.setValue(clientId, forHTTPHeaderField: "X-Client-ID")
            
            let requestBody = [
                "project_id": projectId,
                "diagram_type": "architecture_overview",
                "format": "mermaid"
            ]
            
            vizRequest.httpBody = try JSONEncoder().encode(requestBody)
            
            let (vizData, vizResponse) = try await URLSession.shared.data(for: vizRequest)
            
            guard let httpResponse = vizResponse as? HTTPURLResponse else {
                errorMessage = "Invalid response from server"
                isLoading = false
                return
            }
            
            switch httpResponse.statusCode {
            case 200:
                // Parse visualization response
                if let jsonObject = try JSONSerialization.jsonObject(with: vizData) as? [String: Any] {
                    let diagram: ArchitectureDiagram
                    
                    // Check if response has diagram field
                    if let diagramData = jsonObject["diagram"] as? [String: Any] {
                        diagram = parseDiagramFromResponse(diagramData)
                    } else {
                        // Try to parse the entire response as diagram data
                        diagram = parseDiagramFromResponse(jsonObject)
                    }
                    
                    self.diagram = diagram
                } else {
                    errorMessage = "Invalid diagram data format from visualization endpoint"
                }
            case 404:
                errorMessage = "Project not found or architecture endpoint not available"
            case 400:
                if let jsonObject = try JSONSerialization.jsonObject(with: vizData) as? [String: Any],
                   let error = jsonObject["error"] as? String {
                    errorMessage = "Invalid request: \(error)"
                } else {
                    errorMessage = "Invalid request parameters"
                }
            case 500...599:
                errorMessage = "Server error: The backend is experiencing issues. Please try again later."
            default:
                // Try to get error message from response
                if let jsonObject = try JSONSerialization.jsonObject(with: vizData) as? [String: Any],
                   let error = jsonObject["error"] as? String {
                    errorMessage = "Server error (\(httpResponse.statusCode)): \(error)"
                } else {
                    errorMessage = "Server error: HTTP \(httpResponse.statusCode)"
                }
            }
            
        } catch let error as URLError {
            switch error.code {
            case .notConnectedToInternet:
                errorMessage = "No internet connection. Please check your network settings."
            case .cannotConnectToHost:
                errorMessage = "Cannot connect to backend server. Please check if the server is running."
            case .timedOut:
                errorMessage = "Request timed out. The backend server may be overloaded."
            case .cannotParseResponse:
                errorMessage = "Invalid response format from server. The API format may have changed."
            default:
                errorMessage = "Network error: \(error.localizedDescription)"
            }
        } catch let error as DecodingError {
            errorMessage = "Data format error: Unable to parse server response. The API format may be incompatible."
        } catch {
            errorMessage = "Unexpected error: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    internal func generateMermaidFromGraphData(_ graphData: [String: Any]) -> String {
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
    
    internal func parseDiagramFromResponse(_ diagramData: [String: Any]) -> ArchitectureDiagram {
        // Parse backend diagram response into iOS model
        let title = diagramData["name"] as? String ?? diagramData["title"] as? String ?? "Architecture Diagram"
        
        // Check if it's a direct Mermaid diagram
        if let mermaidDefinition = diagramData["mermaid_definition"] as? String {
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: mermaidDefinition,
                description: diagramData["description"] as? String,
                diagramType: diagramData["diagram_type"] as? String ?? "architecture"
            )
        }
        
        // Check if it's legacy content field
        if let content = diagramData["content"] as? String {
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: content,
                description: diagramData["description"] as? String,
                diagramType: diagramData["diagram_type"] as? String ?? "architecture"
            )
        }
        
        // Check for graph architecture data
        if let architecture = diagramData["architecture"] as? [String: Any] {
            let mermaidDefinition = generateMermaidFromGraphData(architecture)
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: mermaidDefinition,
                description: "Generated from graph analysis",
                diagramType: "architecture"
            )
        }
        
        // Generate Mermaid from nodes/edges structure
        var mermaid = "graph TD\n"
        
        if let nodes = diagramData["nodes"] as? [[String: Any]] {
            for node in nodes {
                let nodeId = node["id"] as? String ?? "unknown"
                let label = node["label"] as? String ?? nodeId
                let sanitizedNodeId = nodeId.replacingOccurrences(of: ".", with: "_")
                mermaid += "    \(sanitizedNodeId)[\(label)]\n"
            }
        }
        
        if let edges = diagramData["edges"] as? [[String: Any]] {
            for edge in edges {
                let source = (edge["source_id"] as? String ?? edge["source"] as? String ?? "unknown").replacingOccurrences(of: ".", with: "_")
                let target = (edge["target_id"] as? String ?? edge["target"] as? String ?? "unknown").replacingOccurrences(of: ".", with: "_")
                mermaid += "    \(source) --> \(target)\n"
            }
        }
        
        // Fallback if no structure found
        if mermaid == "graph TD\n" {
            mermaid += "    A[No Architecture Data]\n"
            mermaid += "    A --> B[Please check backend connection]\n"
        }
        
        return ArchitectureDiagram(
            name: title,
            mermaidDefinition: mermaid,
            description: diagramData["description"] as? String ?? "Auto-generated architecture diagram",
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
        guard let currentDiagram = diagram,
              let projectId = currentProjectId else { return }
        
        // Check if backend is configured
        guard let baseURL = baseURL else { return }
        
        do {
            let url = baseURL.appendingPathComponent("api/projects/\(projectId)/architecture")
            var request = URLRequest(url: url)
            request.httpMethod = "GET"
            request.setValue("application/json", forHTTPHeaderField: "Accept")
            request.setValue(clientId, forHTTPHeaderField: "X-Client-ID")
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                return
            }
            
            // Parse standardized architecture response
            if let jsonObject = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                
                let latestDiagram: ArchitectureDiagram
                
                // Try to parse as a complete ArchitectureDiagram first
                if let diagramData = try? JSONDecoder().decode(ArchitectureDiagram.self, from: data) {
                    latestDiagram = diagramData
                } else {
                    // Fallback: Parse architecture data and convert to Mermaid
                    latestDiagram = parseDiagramFromResponse(jsonObject)
                }
            
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
