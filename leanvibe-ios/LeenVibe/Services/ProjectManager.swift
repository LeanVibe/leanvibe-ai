import Foundation
import SwiftUI


@available(macOS 10.15, iOS 13.0, *)
@MainActor
class ProjectManager: ObservableObject {
    @Published var projects: [Project] = []
    @Published var activeSessions: [ProjectSession] = []
    @Published var isLoading = false
    @Published var lastError: String?
    
    private var webSocketService: WebSocketService?
    
    init() {
        loadSampleProjects()
    }
    
    func configure(with webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        // Note: WebSocketService doesn't have onMessageReceived, 
        // message handling should be done via the @Published messages property
    }
    
    func refreshProjects() async {
        isLoading = true
        defer { isLoading = false }
        
        // In production, this would fetch from backend
        // For now, simulate network delay
        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Simulate refreshed data
        loadSampleProjects()
    }
    
    func addProject(name: String, path: String, language: ProjectLanguage) {
        let newProject = Project(
            name: name,
            path: path,
            language: language,
            status: .active,
            metrics: ProjectMetrics(
                filesCount: Int.random(in: 10...100),
                linesOfCode: Int.random(in: 1000...50000),
                healthScore: Double.random(in: 0.7...0.95),
                issuesCount: Int.random(in: 0...5)
            )
        )
        projects.append(newProject)
        saveProjects()
    }
    
    func removeProject(_ project: Project) {
        projects.removeAll { $0.id == project.id }
        saveProjects()
    }
    
    func updateProject(_ project: Project) {
        if let index = projects.firstIndex(where: { $0.id == project.id }) {
            projects[index] = project
            saveProjects()
        }
    }
    
    func analyzeProject(_ project: Project) async {
        guard let webSocketService = webSocketService else {
            lastError = "WebSocket service not configured"
            return
        }
        
        isLoading = true
        defer { isLoading = false }
        
        do {
            let analysisRequest = AnalysisRequest(
                projectId: project.id,
                analysisType: "comprehensive"
            )
            
            let jsonData = try JSONEncoder().encode(analysisRequest)
            if let jsonString = String(data: jsonData, encoding: .utf8) {
                webSocketService.sendCommand(jsonString)
            }
        } catch {
            lastError = "Failed to send analysis request: \(error.localizedDescription)"
        }
    }
    
    private func loadSampleProjects() {
        projects = [
            Project(
                id: "sample-1",
                name: "LeanVibe Backend",
                path: "/Users/bogdan/work/leanvibe-backend",
                language: .python,
                status: .active,
                lastActivity: Date(),
                metrics: ProjectMetrics(filesCount: 42, linesOfCode: 12345, healthScore: 0.9, issuesCount: 1),
                clientId: nil
            ),
            Project(
                id: "sample-2",
                name: "iOS Client",
                path: "/Users/bogdan/work/leanvibe-ios",
                language: .swift,
                status: .active,
                lastActivity: Date(),
                metrics: ProjectMetrics(filesCount: 30, linesOfCode: 6789, healthScore: 0.85, issuesCount: 0),
                clientId: nil
            )
        ]
    }
    
    private func processProjectResponse(_ content: String) {
        // Process project analysis response
        // This would parse the backend response and update projects
    }
    
    private func saveProjects() {
        // In a real app, this would save to Core Data or UserDefaults
        // For now, we'll keep them in memory
    }
}

// Supporting types
struct AnalysisRequest: Codable {
    let projectId: String
    let analysisType: String
}