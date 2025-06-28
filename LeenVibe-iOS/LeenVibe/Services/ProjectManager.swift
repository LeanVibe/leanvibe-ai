import Foundation
import SwiftUI

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
        webSocketService.onMessageReceived = { [weak self] content in
            self?.processProjectResponse(content)
        }
    }
    
    func refreshProjects() async {
        isLoading = true
        defer { isLoading = false }
        
        // In production, this would fetch from backend
        // For now, simulate network delay
        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        // Update projects with fresh data
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
    
    private func loadSampleProjects() {
        projects = [
            Project(
                name: "LeenVibe iOS",
                path: "/Users/developer/Projects/LeenVibe-iOS",
                language: .swift,
                status: .active,
                metrics: ProjectMetrics(
                    filesCount: 45,
                    linesOfCode: 12500,
                    lastBuildTime: 2.3,
                    testCoverage: 0.85,
                    healthScore: 0.92,
                    issuesCount: 2,
                    performanceScore: 0.89
                )
            ),
            Project(
                name: "Backend API",
                path: "/Users/developer/Projects/leenvibe-backend",
                language: .python,
                status: .active,
                metrics: ProjectMetrics(
                    filesCount: 78,
                    linesOfCode: 25000,
                    lastBuildTime: 15.2,
                    testCoverage: 0.91,
                    healthScore: 0.88,
                    issuesCount: 1,
                    performanceScore: 0.94
                )
            ),
            Project(
                name: "CLI Tools",
                path: "/Users/developer/Projects/leenvibe-cli",
                language: .python,
                status: .maintenance,
                metrics: ProjectMetrics(
                    filesCount: 23,
                    linesOfCode: 5600,
                    lastBuildTime: 3.1,
                    testCoverage: 0.73,
                    healthScore: 0.76,
                    issuesCount: 3,
                    performanceScore: 0.82
                )
            )
        ]
    }
    
    private func processProjectResponse(_ content: String) {
        // Parse JSON responses for project/session data
        guard let data = content.data(using: .utf8) else { return }
        
        // Try to parse as session data using JSONSerialization
        if let sessionData = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
           let sessions = sessionData["sessions"] as? [[String: Any]] {
            updateSessionsFromBackendData(sessions)
            return
        }
        
        // Try to parse as analysis data using JSONSerialization
        if let jsonObject = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
           let projectData = jsonObject["project_analysis"] as? [String: Any] {
            updateProjectFromAnalysisData(projectData)
            return
        }
    }
    
    private func updateSessionsFromBackendData(_ sessionData: [[String: Any]]) {
        let newSessions: [ProjectSession] = sessionData.compactMap { sessionDict in
            guard let id = sessionDict["id"] as? String,
                  let projectId = sessionDict["project_id"] as? String,
                  let clientId = sessionDict["client_id"] as? String,
                  let startTimeString = sessionDict["start_time"] as? String else {
                return nil
            }
            
            let formatter = ISO8601DateFormatter()
            let startTime = formatter.date(from: startTimeString) ?? Date()
            let endTime = (sessionDict["end_time"] as? String).flatMap { formatter.date(from: $0) }
            let duration = sessionDict["duration"] as? TimeInterval ?? 0
            
            return ProjectSession(
                id: id,
                projectId: projectId,
                startTime: startTime,
                endTime: endTime,
                duration: duration,
                clientId: clientId
            )
        }
        
        activeSessions = newSessions
    }
    
    private func updateProjectFromAnalysisData(_ projectData: [String: Any]) {
        guard let projectPath = projectData["path"] as? String else { return }
        
        // Update existing project or create new one
        let language = ProjectLanguage(rawValue: projectData["language"] as? String ?? "Unknown") ?? .unknown
        let metrics = ProjectMetrics(
            filesCount: projectData["files_count"] as? Int ?? 0,
            linesOfCode: projectData["lines_of_code"] as? Int ?? 0,
            healthScore: projectData["health_score"] as? Double ?? 0.5,
            issuesCount: projectData["issues_count"] as? Int ?? 0
        )
        
        if let existingIndex = projects.firstIndex(where: { $0.path == projectPath }) {
            let existing = projects[existingIndex]
            projects[existingIndex] = Project(
                id: existing.id,
                name: existing.name,
                path: existing.path,
                language: language,
                status: existing.status,
                lastActivity: Date(),
                metrics: metrics,
                clientId: existing.clientId
            )
        }
    }
    
    private func saveProjects() {
        // In a real app, this would save to Core Data or UserDefaults
        // For now, we'll keep them in memory
    }
}