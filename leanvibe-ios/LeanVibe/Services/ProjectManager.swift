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


@available(iOS 18.0, macOS 14.0, *)
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
        // TODO: Fix RetryManager resolution issue
        // try await RetryManager.shared.executeWithRetry(
        //     operation: { [weak self] in
        //         try await self?.refreshProjectsInternal()
        //     },
        //     maxAttempts: 3,
        //     backoffStrategy: BackoffStrategy.exponential(base: 2.0, multiplier: 1.5),
        //     retryCondition: { error in
        //         // Only retry network errors, not validation errors
        //         if error is ProjectManagerError {
        //             return false
        //         }
        //         return RetryManager.shouldRetry(error)
        //     },
        //     context: "Refreshing projects from backend"
        // )
        try await refreshProjectsInternal()
    }
    
    private func refreshProjectsInternal() async throws {
        isLoading = true
        lastError = nil
        defer { isLoading = false }
        
        // Try to fetch from backend API
        if let backendProjects = try await fetchProjectsFromBackend() {
            projects = backendProjects
            try await saveProjects() // Persist fetched data
        } else {
            // Fallback to persistent storage if backend unavailable
            loadPersistedProjects()
            
            // If no projects exist locally, try auto-discovery from file system
            if projects.isEmpty {
                await discoverProjectsFromFileSystem()
                if projects.isEmpty {
                    loadSampleProjects() // Final fallback to sample data
                }
                try await saveProjects()
            }
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
        // Create project with initial metrics - will be updated by backend API
        let newProject = Project(
            displayName: name,
            status: .active,
            path: path,
            language: language,
            metrics: ProjectMetrics(
                filesCount: 0, // Will be calculated by backend
                linesOfCode: 0, // Will be calculated by backend
                healthScore: 0.50, // Initial placeholder, will be updated by backend
                issuesCount: 0 // Will be calculated by backend
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
    func removeProject(_ projectId: UUID) async throws {
        try await deleteProject(projectId)
    }
    
    // Legacy method for backwards compatibility
    func removeProject(_ project: Project) async throws {
        try await deleteProject(project.id)
    }
    
    func clearAllProjects() async throws {
        lastError = nil
        do {
            projects.removeAll()
            try await saveProjects()
        } catch {
            lastError = "Failed to clear projects: \(error.localizedDescription)"
            throw error
        }
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
    
    // MARK: - Project Auto-Discovery
    
    func discoverProjectsFromFileSystem() async {
        lastError = nil
        
        do {
            let fileManager = FileManager.default
            
            // Get the user's home directory (iOS-compatible approach)
            #if os(iOS)
            // For iOS, we'll use the app's documents directory as a fallback
            // since we can't access the actual ~/work folder on iOS due to sandboxing
            guard let documentsDirectory = fileManager.urls(for: .documentDirectory, in: .userDomainMask).first else {
                print("Could not access documents directory")
                return
            }
            let workDirectory = documentsDirectory.appendingPathComponent("work")
            #else
            // For macOS, use the actual home directory
            let homeDirectory = fileManager.homeDirectoryForCurrentUser
            let workDirectory = homeDirectory.appendingPathComponent("work")
            #endif
            
            // Check if ~/work directory exists
            guard fileManager.fileExists(atPath: workDirectory.path) else {
                print("~/work directory not found, skipping auto-discovery")
                return
            }
            
            let contents = try fileManager.contentsOfDirectory(at: workDirectory, includingPropertiesForKeys: [.isDirectoryKey], options: [.skipsHiddenFiles])
            
            for item in contents {
                let resourceValues = try item.resourceValues(forKeys: [.isDirectoryKey])
                
                // Only scan directories
                if resourceValues.isDirectory == true {
                    await checkDirectoryForProject(item)
                }
            }
            
            print("Auto-discovery completed. Found \(projects.count) projects.")
            
        } catch {
            lastError = "Project auto-discovery failed: \(error.localizedDescription)"
            print("Error during project discovery: \(error)")
        }
    }
    
    private func checkDirectoryForProject(_ directory: URL) async {
        let fileManager = FileManager.default
        
        do {
            let contents = try fileManager.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil, options: [.skipsHiddenFiles])
            
            // Check for agent.md, claude.md, CLAUDE.md, or PLAN.md files
            let projectIndicatorFiles = ["agent.md", "claude.md", "CLAUDE.md", "PLAN.md"]
            let hasProjectIndicator = contents.contains { url in
                projectIndicatorFiles.contains(url.lastPathComponent)
            }
            
            if hasProjectIndicator {
                // Determine project language from directory contents
                let language = detectProjectLanguage(from: contents)
                
                // Parse project documentation for additional info
                let projectInfo = await parseProjectDocumentation(directory: directory)
                
                let project = Project(
                    displayName: projectInfo.name ?? directory.lastPathComponent,
                    status: .active,
                    path: directory.path,
                    language: language,
                    lastActivity: getLastModificationDate(for: directory),
                    metrics: ProjectMetrics(
                        filesCount: countProjectFiles(in: directory),
                        linesOfCode: 0, // Will be calculated by backend
                        healthScore: 0.50, // Initial placeholder
                        issuesCount: 0 // Will be calculated by backend
                    )
                )
                
                projects.append(project)
                print("Discovered project: \(project.displayName) at \(project.path)")
            }
            
        } catch {
            print("Error scanning directory \(directory.path): \(error)")
        }
    }
    
    private func detectProjectLanguage(from contents: [URL]) -> ProjectLanguage {
        let fileExtensions = contents.map { $0.pathExtension.lowercased() }
        
        // Priority-based language detection
        if fileExtensions.contains("swift") || contents.contains(where: { $0.lastPathComponent == "Package.swift" }) {
            return .swift
        } else if fileExtensions.contains("py") || contents.contains(where: { $0.lastPathComponent == "requirements.txt" }) {
            return .python
        } else if fileExtensions.contains("js") || contents.contains(where: { $0.lastPathComponent == "package.json" }) {
            return .javascript
        } else if fileExtensions.contains("ts") || contents.contains(where: { $0.lastPathComponent == "tsconfig.json" }) {
            return .typescript
        } else if fileExtensions.contains("java") || contents.contains(where: { $0.lastPathComponent == "pom.xml" }) {
            return .java
        } else if fileExtensions.contains("go") || contents.contains(where: { $0.lastPathComponent == "go.mod" }) {
            return .go
        } else {
            return .unknown // Default fallback
        }
    }
    
    private func parseProjectDocumentation(directory: URL) async -> (name: String?, description: String?, mvpSpecs: [String]) {
        var projectName: String?
        let description: String? = nil // Not currently used but kept for future implementation
        var mvpSpecs: [String] = []
        
        let documentFiles = ["PLAN.md", "README.md", "claude.md", "CLAUDE.md", "agent.md"]
        
        for fileName in documentFiles {
            let fileURL = directory.appendingPathComponent(fileName)
            
            if FileManager.default.fileExists(atPath: fileURL.path) {
                do {
                    let content = try String(contentsOf: fileURL, encoding: .utf8)
                    
                    // Extract project name from first heading
                    if projectName == nil {
                        let lines = content.components(separatedBy: .newlines)
                        for line in lines {
                            if line.hasPrefix("# ") {
                                projectName = String(line.dropFirst(2)).trimmingCharacters(in: .whitespacesAndNewlines)
                                break
                            }
                        }
                    }
                    
                    // Look for MVP specifications or features
                    if fileName.contains("PLAN") || content.localizedCaseInsensitiveContains("mvp") {
                        let mvpFeatures = extractMVPFeatures(from: content)
                        mvpSpecs.append(contentsOf: mvpFeatures)
                    }
                    
                } catch {
                    print("Error reading \(fileName): \(error)")
                }
            }
        }
        
        return (projectName, description, mvpSpecs)
    }
    
    private func extractMVPFeatures(from content: String) -> [String] {
        var features: [String] = []
        let lines = content.components(separatedBy: .newlines)
        
        for line in lines {
            let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
            
            // Look for bullet points, numbered lists, or TODO items
            if trimmedLine.hasPrefix("- ") || trimmedLine.hasPrefix("* ") || 
               trimmedLine.hasPrefix("+ ") || trimmedLine.contains("TODO") ||
               trimmedLine.hasPrefix("✅") || trimmedLine.hasPrefix("❌") ||
               trimmedLine.hasPrefix("⚠️") {
                features.append(trimmedLine)
            }
        }
        
        return features
    }
    
    private func getLastModificationDate(for directory: URL) -> Date {
        do {
            let attributes = try FileManager.default.attributesOfItem(atPath: directory.path)
            return attributes[.modificationDate] as? Date ?? Date()
        } catch {
            return Date()
        }
    }
    
    private func countProjectFiles(in directory: URL) -> Int {
        do {
            let enumerator = FileManager.default.enumerator(at: directory, includingPropertiesForKeys: [.isRegularFileKey], options: [.skipsHiddenFiles, .skipsPackageDescendants])
            
            var count = 0
            while let url = enumerator?.nextObject() as? URL {
                let resourceValues = try url.resourceValues(forKeys: [.isRegularFileKey])
                if resourceValues.isRegularFile == true {
                    // Only count relevant project files (not .git, node_modules, etc.)
                    let pathExtensions = ["swift", "py", "js", "ts", "java", "go", "md", "txt", "json", "yml", "yaml"]
                    if pathExtensions.contains(url.pathExtension.lowercased()) {
                        count += 1
                    }
                }
            }
            return count
        } catch {
            return 0
        }
    }
    
    func loadSampleProjects() {
        // Note: These are fallback samples only used when backend is unavailable
        // Real data comes from backend APIs with dynamic health score calculation
        projects = [
            Project(
                displayName: "LeanVibe Backend",
                status: .active,
                path: "/Users/bogdan/work/leanvibe-backend",
                language: .python,
                lastActivity: Date(),
                metrics: ProjectMetrics(filesCount: 42, linesOfCode: 12345, healthScore: 0.75, issuesCount: 1) // Fallback value, real: 0.92
            ),
            Project(
                displayName: "iOS Client",
                status: .active,
                path: "/Users/bogdan/work/leanvibe-ios",
                language: .swift,
                lastActivity: Date(),
                metrics: ProjectMetrics(filesCount: 30, linesOfCode: 6789, healthScore: 0.70, issuesCount: 0) // Fallback value, real: 0.87
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
                // Success - decode projects and fetch detailed metrics
                let projectsResponse = try jsonDecoder.decode(ProjectsAPIResponse.self, from: data)
                var projectsWithMetrics: [Project] = []
                
                // Fetch detailed metrics for each project
                for project in projectsResponse.projects {
                    if let projectWithMetrics = try await fetchProjectMetrics(project: project, baseURL: baseURL) {
                        projectsWithMetrics.append(projectWithMetrics)
                    } else {
                        // Fallback to project data as-is if metrics fetch fails
                        projectsWithMetrics.append(project)
                    }
                }
                
                return projectsWithMetrics
                
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
    
    private func fetchProjectMetrics(project: Project, baseURL: String) async throws -> Project? {
        guard let url = URL(string: "\(baseURL)/api/projects/\(project.id.uuidString)/metrics") else {
            return nil
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 5.0 // Shorter timeout for individual metrics
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                return nil // Return nil to use original project data
            }
            
            let metricsResponse = try jsonDecoder.decode(ProjectMetricsAPIResponse.self, from: data)
            
            // Create updated project with fresh metrics
            var updatedProject = project
            updatedProject.metrics = ProjectMetrics(
                filesCount: metricsResponse.metrics.files_count,
                linesOfCode: metricsResponse.metrics.lines_of_code,
                lastBuildTime: metricsResponse.metrics.last_build_time,
                testCoverage: metricsResponse.metrics.test_coverage,
                healthScore: metricsResponse.metrics.health_score,
                issuesCount: metricsResponse.metrics.issues_count,
                performanceScore: metricsResponse.metrics.performance_score
            )
            
            return updatedProject
            
        } catch {
            // If metrics fetch fails, return nil to use original project data
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
    
    var activeProjects: [Project] {
        return projects.filter { $0.status == .active }
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

struct ProjectMetricsAPIResponse: Codable {
    let metrics: BackendProjectMetrics
    let project_id: String
    let updated_at: String
    
    enum CodingKeys: String, CodingKey {
        case metrics
        case project_id
        case updated_at
    }
}

struct BackendProjectMetrics: Codable {
    let files_count: Int
    let lines_of_code: Int
    let last_build_time: TimeInterval?
    let test_coverage: Double?
    let health_score: Double
    let issues_count: Int
    let performance_score: Double?
    
    enum CodingKeys: String, CodingKey {
        case files_count
        case lines_of_code
        case last_build_time
        case test_coverage
        case health_score
        case issues_count
        case performance_score
    }
}