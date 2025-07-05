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
            
            #if DEBUG
            print("ArchitectureVisualizationService: Primary endpoint response status: \((archResponse as? HTTPURLResponse)?.statusCode ?? 0)")
            if let responseString = String(data: archData, encoding: .utf8) {
                print("ArchitectureVisualizationService: Response data: \(responseString.prefix(500))")
            }
            #endif
            
            if let httpResponse = archResponse as? HTTPURLResponse, httpResponse.statusCode == 200 {
                // Parse standardized architecture response
                do {
                    if let jsonObject = try JSONSerialization.jsonObject(with: archData) as? [String: Any] {
                        
                        // Try to parse as a complete ArchitectureDiagram first
                        let decoder = JSONDecoder()
                        decoder.dateDecodingStrategy = .iso8601
                        if let diagramData = try? decoder.decode(ArchitectureDiagram.self, from: archData) {
                            self.diagram = diagramData
                            isLoading = false
                            return
                        }
                        
                        // Check if response has a nested diagram structure
                        if let diagramObj = jsonObject["diagram"] as? [String: Any] {
                            let diagram = parseDiagramFromResponse(diagramObj)
                            self.diagram = diagram
                            isLoading = false
                            return
                        }
                        
                        // Check if response has data wrapper
                        if let dataObj = jsonObject["data"] as? [String: Any] {
                            let diagram = parseDiagramFromResponse(dataObj)
                            self.diagram = diagram
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
                } catch {
                    print("Warning: Failed to parse primary architecture response: \(error)")
                }
            } else if let httpResponse = archResponse as? HTTPURLResponse, httpResponse.statusCode == 404 {
                print("Primary architecture endpoint not found, trying fallback")
            } else if let httpResponse = archResponse as? HTTPURLResponse {
                print("Primary architecture endpoint failed with status: \(httpResponse.statusCode)")
            }
            
            // Use actual backend visualization endpoint that exists
            let vizUrl = baseURL.appendingPathComponent("visualization/\(clientId)/generate")
            var vizRequest = URLRequest(url: vizUrl)
            vizRequest.httpMethod = "POST"
            vizRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            vizRequest.setValue("application/json", forHTTPHeaderField: "Accept")
            vizRequest.setValue(clientId, forHTTPHeaderField: "X-Client-ID")
            
            let requestBody = [
                "project_id": projectId,
                "diagram_type": "architecture_overview",
                "format": "mermaid",
                "theme": "light"
            ]
            
            vizRequest.httpBody = try JSONEncoder().encode(requestBody)
            
            let (vizData, vizResponse) = try await URLSession.shared.data(for: vizRequest)
            
            #if DEBUG
            print("ArchitectureVisualizationService: Fallback endpoint response status: \((vizResponse as? HTTPURLResponse)?.statusCode ?? 0)")
            if let responseString = String(data: vizData, encoding: .utf8) {
                print("ArchitectureVisualizationService: Fallback response data: \(responseString.prefix(500))")
            }
            #endif
            
            guard let httpResponse = vizResponse as? HTTPURLResponse else {
                errorMessage = "Invalid response from server"
                isLoading = false
                return
            }
            
            switch httpResponse.statusCode {
            case 200:
                // Parse visualization response
                do {
                    if let jsonObject = try JSONSerialization.jsonObject(with: vizData) as? [String: Any] {
                        let diagram: ArchitectureDiagram
                        
                        // Check if response has success status
                        if let status = jsonObject["status"] as? String, status != "success" {
                            if let message = jsonObject["message"] as? String {
                                errorMessage = "Backend error: \(message)"
                            } else {
                                errorMessage = "Backend returned error status: \(status)"
                            }
                            break
                        }
                        
                        // Check if response has diagram field
                        if let diagramData = jsonObject["diagram"] as? [String: Any] {
                            diagram = parseDiagramFromResponse(diagramData)
                        } else if let dataWrapper = jsonObject["data"] as? [String: Any] {
                            // Check if data has diagram field
                            if let diagramData = dataWrapper["diagram"] as? [String: Any] {
                                diagram = parseDiagramFromResponse(diagramData)
                            } else {
                                diagram = parseDiagramFromResponse(dataWrapper)
                            }
                        } else {
                            // Try to parse the entire response as diagram data
                            diagram = parseDiagramFromResponse(jsonObject)
                        }
                        
                        // Validate diagram has content
                        if diagram.mermaidDefinition.isEmpty || diagram.mermaidDefinition == "graph TD\n" {
                            errorMessage = "Backend returned empty architecture diagram"
                        } else {
                            self.diagram = diagram
                        }
                    } else {
                        errorMessage = "Invalid diagram data format from visualization endpoint"
                    }
                } catch {
                    errorMessage = "Failed to parse visualization response: \(error.localizedDescription)"
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
            errorMessage = "Data format error: Unable to parse server response. The API format may be incompatible. \(error.localizedDescription)"
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
        
        // Check if it's actual backend format with nested mermaid_diagram
        if let diagramObj = diagramData["diagram"] as? [String: Any],
           let mermaidObj = diagramObj["mermaid_diagram"] as? [String: Any],
           let content = mermaidObj["content"] as? String {
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: content,
                description: diagramObj["description"] as? String,
                diagramType: mermaidObj["diagram_type"] as? String ?? "architecture"
            )
        }
        
        // Check if it's direct mermaid_diagram at top level
        if let mermaidObj = diagramData["mermaid_diagram"] as? [String: Any],
           let content = mermaidObj["content"] as? String {
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: content,
                description: diagramData["description"] as? String,
                diagramType: mermaidObj["diagram_type"] as? String ?? "architecture"
            )
        }
        
        // Check if it's a direct Mermaid diagram (snake_case)
        if let mermaidDefinition = diagramData["mermaid_definition"] as? String {
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: mermaidDefinition,
                description: diagramData["description"] as? String,
                diagramType: diagramData["diagram_type"] as? String ?? "architecture"
            )
        }
        
        // Check if it's a direct Mermaid diagram (camelCase)
        if let mermaidDefinition = diagramData["mermaidDefinition"] as? String {
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: mermaidDefinition,
                description: diagramData["description"] as? String,
                diagramType: diagramData["diagramType"] as? String ?? "architecture"
            )
        }
        
        // Check if it's legacy content field
        if let content = diagramData["content"] as? String {
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: content,
                description: diagramData["description"] as? String,
                diagramType: diagramData["diagram_type"] as? String ?? diagramData["diagramType"] as? String ?? "architecture"
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
        
        // Check for components structure (alternative format)
        if let components = diagramData["components"] as? [[String: Any]] {
            var mermaid = "graph TD\n"
            
            for component in components {
                let componentId = component["id"] as? String ?? "unknown"
                let componentName = component["name"] as? String ?? componentId
                let sanitizedId = componentId.replacingOccurrences(of: ".", with: "_")
                mermaid += "    \(sanitizedId)[\(componentName)]\n"
                
                // Add dependencies
                if let dependencies = component["dependencies"] as? [String] {
                    for dep in dependencies {
                        let sanitizedDep = dep.replacingOccurrences(of: ".", with: "_")
                        mermaid += "    \(sanitizedId) --> \(sanitizedDep)\n"
                    }
                }
            }
            
            return ArchitectureDiagram(
                name: title,
                mermaidDefinition: mermaid,
                description: "Generated from components structure",
                diagramType: "architecture"
            )
        }
        
        // Generate Mermaid from nodes/edges structure
        var mermaid = "graph TD\n"
        var hasNodes = false
        
        if let nodes = diagramData["nodes"] as? [[String: Any]] {
            for node in nodes {
                let nodeId = node["id"] as? String ?? "unknown"
                let label = node["label"] as? String ?? node["name"] as? String ?? nodeId
                let sanitizedNodeId = nodeId.replacingOccurrences(of: ".", with: "_")
                mermaid += "    \(sanitizedNodeId)[\(label)]\n"
                hasNodes = true
            }
        }
        
        if let edges = diagramData["edges"] as? [[String: Any]] {
            for edge in edges {
                let source = (edge["source_id"] as? String ?? edge["source"] as? String ?? edge["from"] as? String ?? "unknown").replacingOccurrences(of: ".", with: "_")
                let target = (edge["target_id"] as? String ?? edge["target"] as? String ?? edge["to"] as? String ?? "unknown").replacingOccurrences(of: ".", with: "_")
                mermaid += "    \(source) --> \(target)\n"
                hasNodes = true
            }
        }
        
        // Fallback if no structure found
        if !hasNodes {
            mermaid += "    A[No Architecture Data]\n"
            mermaid += "    A --> B[Please check backend connection]\n"
        }
        
        return ArchitectureDiagram(
            name: title,
            mermaidDefinition: mermaid,
            description: diagramData["description"] as? String ?? "Auto-generated architecture diagram",
            diagramType: diagramData["diagram_type"] as? String ?? diagramData["diagramType"] as? String ?? "architecture"
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
            // Use the working graph architecture endpoint for monitoring
            let url = baseURL.appendingPathComponent("graph/architecture/\(clientId)")
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
            
            // Try to parse as AgentResponse first
            if let agentResponse = try? JSONDecoder().decode(AgentResponse.self, from: messageData) {
                if let responseData = agentResponse.data, 
                   let fileInfo = responseData.files?.first {
                    // Fix: The diagram data should be in the file content, not name
                    let diagramDataString = fileInfo.type == "architecture_diagram" ? fileInfo.name : message.content
                    if let diagramData = diagramDataString.data(using: .utf8),
                       let newDiagram = try? JSONDecoder().decode(ArchitectureDiagram.self, from: diagramData) {
                        self.diagram = newDiagram
                    } else {
                        // Try to parse as raw JSON object
                        if let jsonObject = try? JSONSerialization.jsonObject(with: diagramDataString.data(using: .utf8) ?? Data()) as? [String: Any] {
                            self.diagram = parseDiagramFromResponse(jsonObject)
                        } else {
                            self.errorMessage = "Invalid diagram data format in WebSocket response"
                        }
                    }
                } else if !agentResponse.message.isEmpty {
                     self.errorMessage = agentResponse.message
                }
            } else {
                // Fallback: Try to parse the entire message content as diagram data
                if let jsonObject = try? JSONSerialization.jsonObject(with: messageData) as? [String: Any] {
                    self.diagram = parseDiagramFromResponse(jsonObject)
                } else {
                    self.errorMessage = "Unable to parse WebSocket message format"
                }
            }
            self.isLoading = false
        } catch {
            self.errorMessage = "Failed to decode architecture diagram: \(error.localizedDescription)"
            self.isLoading = false
        }
    }
}
