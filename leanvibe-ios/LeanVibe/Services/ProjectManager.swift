import Foundation
import SwiftUI

// MARK: - ProjectManager Errors
enum ProjectManagerError: LocalizedError {
    case invalidProjectName
    case duplicateProject
    case projectNotFound
    case persistenceError(String)
    
    var errorDescription: String? {
        switch self {
        case .invalidProjectName:
            return "Project name cannot be empty"
        case .duplicateProject:
            return "A project with this path already exists"
        case .projectNotFound:
            return "Project not found"
        case .persistenceError(let message):
            return message
        }
    }
}


@available(macOS 10.15, iOS 13.0, *)
@MainActor
class ProjectManager: ObservableObject {
    @Published var projects: [Project] = []
    @Published var activeSessions: [ProjectSession] = []
    @Published var isLoading = false
    @Published var lastError: String?
    
    private var webSocketService: WebSocketService?
    private let userDefaultsKey = "leanvibe_projects"
    private let jsonEncoder = JSONEncoder()
    private let jsonDecoder = JSONDecoder()
    
    init() {
        setupDateFormatting()
        loadPersistedProjects()
    }
    
    private func setupDateFormatting() {
        jsonEncoder.dateEncodingStrategy = .iso8601
        jsonDecoder.dateDecodingStrategy = .iso8601
    }
    
    func configure(with webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        // Note: WebSocketService doesn't have onMessageReceived, 
        // message handling should be done via the @Published messages property
    }
    
    func refreshProjects() async throws {
        isLoading = true
        lastError = nil
        defer { isLoading = false }
        
        do {
            // Try to fetch from backend API
            if let backendProjects = try await fetchProjectsFromBackend() {
                projects = backendProjects
                try await saveProjects() // Persist fetched data
            } else {
                // Fallback to persistent storage if backend unavailable
                loadPersistedProjects()
                
                // If no projects exist locally, load sample data
                if projects.isEmpty {
                    loadSampleProjects()
                    try await saveProjects()
                }
            }
        } catch {
            lastError = "Failed to refresh projects: \(error.localizedDescription)"
            
            // On error, still try to load from persistence as fallback
            loadPersistedProjects()
            
            // If completely empty, show sample data so UI isn't broken
            if projects.isEmpty {
                loadSampleProjects()
            }
            
            throw error
        }
    }
    
    func addProject(_ project: Project) async throws {
        lastError = nil
        
        do {
            // Validate project data
            guard !project.displayName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw ProjectManagerError.invalidProjectName
            }
            
            // Check for duplicate projects by path
            if projects.contains(where: { $0.path == project.path }) {
                throw ProjectManagerError.duplicateProject
            }
            
            projects.append(project)
            try await saveProjects()
        } catch {
            lastError = "Failed to add project: \(error.localizedDescription)"
            throw error
        }
    }
    
    // Legacy method for backwards compatibility
    func addProject(name: String, path: String, language: ProjectLanguage) async throws {
        let newProject = Project(
            displayName: name,
            status: .active,
            path: path,
            language: language,
            metrics: ProjectMetrics(
                filesCount: Int.random(in: 10...100),
                linesOfCode: Int.random(in: 1000...50000),
                healthScore: Double.random(in: 0.7...0.95),
                issuesCount: Int.random(in: 0...5)
            )
        )
        try await addProject(newProject)
    }
    
    func deleteProject(_ projectId: UUID) async throws {
        lastError = nil
        
        do {
            guard let index = projects.firstIndex(where: { $0.id == projectId }) else {
                throw ProjectManagerError.projectNotFound
            }
            
            projects.remove(at: index)
            try await saveProjects()
        } catch {
            lastError = "Failed to delete project: \(error.localizedDescription)"
            throw error
        }
    }
    
    // Legacy method for backwards compatibility
    func removeProject(_ project: Project) async throws {
        try await deleteProject(project.id)
    }
    
    func updateProject(_ project: Project) async throws {
        lastError = nil
        
        do {
            guard let index = projects.firstIndex(where: { $0.id == project.id }) else {
                throw ProjectManagerError.projectNotFound
            }
            
            // Validate updated project data
            guard !project.displayName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw ProjectManagerError.invalidProjectName
            }
            
            var updatedProject = project
            updatedProject.updatedAt = Date()
            
            projects[index] = updatedProject
            try await saveProjects()
        } catch {
            lastError = "Failed to update project: \(error.localizedDescription)"
            throw error
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
                projectId: project.id.uuidString,
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
                displayName: "LeanVibe Backend",
                status: .active,
                path: "/Users/bogdan/work/leanvibe-backend",
                language: .python,
                lastActivity: Date(),
                metrics: ProjectMetrics(filesCount: 42, linesOfCode: 12345, healthScore: 0.9, issuesCount: 1)
            ),
            Project(
                displayName: "iOS Client",
                status: .active,
                path: "/Users/bogdan/work/leanvibe-ios",
                language: .swift,
                lastActivity: Date(),
                metrics: ProjectMetrics(filesCount: 30, linesOfCode: 6789, healthScore: 0.85, issuesCount: 0)
            )
        ]
    }
    
    private func fetchProjectsFromBackend() async throws -> [Project]? {
        // Get backend URL from WebSocket service connection settings
        guard let webSocketService = webSocketService,
              let connectionInfo = webSocketService.getCurrentConnectionInfo() else {
            // No backend connection available, return nil to use fallback
            return nil
        }
        
        // Convert WebSocket URL to HTTP API URL
        let baseURL = connectionInfo.websocketURL
            .replacingOccurrences(of: "ws://", with: "http://")
            .replacingOccurrences(of: "wss://", with: "https://")
        
        guard let url = URL(string: "\(baseURL)/api/projects") else {
            throw ProjectManagerError.persistenceError("Invalid backend URL")
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 10.0
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw ProjectManagerError.persistenceError("Invalid response from server")
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                // Success - decode projects
                let projectsResponse = try jsonDecoder.decode(ProjectsAPIResponse.self, from: data)
                return projectsResponse.projects
                
            case 404:
                // No projects endpoint available, use fallback
                return nil
                
            case 500...599:
                // Server error, use fallback
                return nil
                
            default:
                throw ProjectManagerError.persistenceError("Server returned error: \(httpResponse.statusCode)")
            }
            
        } catch is DecodingError {
            // JSON decoding failed, but don't crash - use fallback
            return nil
        } catch {
            // Network error, use fallback
            return nil
        }
    }
    
    private func processProjectResponse(_ content: String) {
        // Process project analysis response
        // This would parse the backend response and update projects
    }
    
    private func saveProjects() async throws {
        do {
            let data = try jsonEncoder.encode(projects)
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
            UserDefaults.standard.synchronize()
        } catch {
            throw ProjectManagerError.persistenceError("Failed to save projects: \(error.localizedDescription)")
        }
    }
    
    private func loadPersistedProjects() {
        guard let data = UserDefaults.standard.data(forKey: userDefaultsKey) else {
            // No persisted projects found, load samples
            loadSampleProjects()
            return
        }
        
        do {
            projects = try jsonDecoder.decode([Project].self, from: data)
        } catch {
            // If decoding fails, log error but don't crash
            lastError = "Failed to load saved projects: \(error.localizedDescription)"
            // Fall back to sample projects
            loadSampleProjects()
        }
    }
    
    // MARK: - Computed Properties
    
    var projectCount: Int {
        return projects.count
    }
    
    var projectsByStatus: [ProjectStatus: [Project]] {
        return Dictionary(grouping: projects) { $0.status }
    }
}

// Supporting types
struct AnalysisRequest: Codable {
    let projectId: String
    let analysisType: String
}

struct ProjectsAPIResponse: Codable {
    let projects: [Project]
    let total: Int?
    let status: String?
    
    enum CodingKeys: String, CodingKey {
        case projects
        case total
        case status
    }
}