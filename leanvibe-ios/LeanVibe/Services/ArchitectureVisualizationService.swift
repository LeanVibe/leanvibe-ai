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

    private let baseURL = URL(string: "http://localhost:8000")!
    private var webSocketService: WebSocketService
    private var cancellables = Set<AnyCancellable>()
    private var architectureChangeTimer: Timer?
    @Published var lastKnownDiagram: ArchitectureDiagram?

    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
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
        
        do {
            // First try to get client_id from settings or websocket
            let clientId = getClientId()
            
            // Make HTTP request to backend visualization endpoint
            let url = baseURL.appendingPathComponent("visualization/\(clientId)/generate")
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            let requestBody = [
                "project_id": projectId,
                "diagram_type": "architecture"
            ]
            
            request.httpBody = try JSONEncoder().encode(requestBody)
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                errorMessage = "Invalid response from server"
                isLoading = false
                return
            }
            
            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                let architectureDiagram = try decoder.decode(ArchitectureDiagram.self, from: data)
                self.diagram = architectureDiagram
            } else {
                errorMessage = "Server error: \(httpResponse.statusCode)"
            }
            
        } catch {
            errorMessage = "Network error: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    private func getClientId() -> String {
        // Use a consistent client ID for this session
        return "mobile_\(UUID().uuidString.prefix(8))"
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
        
        // Fetch latest diagram silently
        let currentProjectId = "default_project" // This should be dynamic based on current context
        
        do {
            let clientId = getClientId()
            let url = baseURL.appendingPathComponent("visualization/\(clientId)/generate")
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            let requestBody = [
                "project_id": currentProjectId,
                "diagram_type": "architecture"
            ]
            
            request.httpBody = try JSONEncoder().encode(requestBody)
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                return
            }
            
            let decoder = JSONDecoder()
            let latestDiagram = try decoder.decode(ArchitectureDiagram.self, from: data)
            
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
