import Foundation
import Combine

@MainActor
class ArchitectureVisualizationService: ObservableObject {
    @Published var diagram: ArchitectureDiagram?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var selectedNode: DiagramNode?

    private let baseURL = URL(string: "http://localhost:8000")!
    private var webSocketService: WebSocketService
    private var cancellables = Set<AnyCancellable>()

    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        subscribeToMessages()
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
        let request = ["command": "/architecture", "projectId": projectId]
        await sendMessage(request)
    }

    func requestDiagramUpdate(for nodeId: String, in projectId: String) async {
        let request = ["command": "/architecture_node", "nodeId": nodeId, "projectId": projectId]
        await sendMessage(request)
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
