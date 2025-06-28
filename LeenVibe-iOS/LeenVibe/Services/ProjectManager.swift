import Foundation
import Combine

@MainActor
class ProjectManager: ObservableObject {
    @Published var projects: [Project] = []
    @Published var activeSessions: [ProjectSession] = []
    @Published var isLoading = false
    @Published var lastError: String?
    
    private var webSocketService: WebSocketService?
    private var cancellables = Set<AnyCancellable>()
    private let storageKey = "leenvibe_projects"
    private let userDefaults = UserDefaults.standard
    
    init() {
        loadProjects()
        startPeriodicUpdates()
    }
    
    // MARK: - Configuration
    
    func configure(with webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        
        // Subscribe to WebSocket connection changes
        webSocketService.$isConnected
            .sink { [weak self] isConnected in
                if isConnected {
                    self?.refreshProjectsFromBackend()
                }
            }
            .store(in: &cancellables)
        
        // Subscribe to WebSocket messages for real-time updates
        webSocketService.$messages
            .sink { [weak self] _ in
                // Process messages for project updates
                self?.processIncomingMessages()
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Public Methods
    
    func refreshProjects() async {
        isLoading = true
        lastError = nil
        
        do {
            // Fetch sessions from backend
            await fetchActiveSessions()
            
            // Fetch project analysis data
            await fetchProjectAnalysisData()
            
            // Update project statuses based on sessions
            updateProjectStatuses()
            
            // Save updated projects
            saveProjects()
            
        } catch {
            lastError = "Failed to refresh projects: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    func addProject(name: String, path: String, language: ProjectLanguage = .unknown) {
        let project = Project(
            name: name,
            path: path,
            language: language,
            status: .inactive,
            lastActivity: Date()
        )
        
        projects.append(project)
        saveProjects()
        
        // Trigger analysis if connected
        Task {
            await analyzeProject(project)
        }
    }
    
    func removeProject(_ project: Project) {
        projects.removeAll { $0.id == project.id }
        activeSessions.removeAll { $0.projectId == project.id }
        saveProjects()
    }
    
    func analyzeProject(_ project: Project) async {
        guard let webSocketService = webSocketService,
              webSocketService.isConnected else {
            lastError = "Not connected to backend"
            return
        }
        
        // Update project status to analyzing
        if let index = projects.firstIndex(where: { $0.id == project.id }) {
            projects[index] = Project(
                id: project.id,
                name: project.name,
                path: project.path,
                language: project.language,
                status: .analyzing,
                lastActivity: Date(),
                metrics: project.metrics,
                clientId: project.clientId
            )
        }
        
        // Send analysis command
        webSocketService.sendCommand("/analyze-project \(project.path)")
    }
    
    func getActiveProjects() -> [Project] {
        return projects.filter { $0.isActive }
    }
    
    func getProjectById(_ id: String) -> Project? {
        return projects.first { $0.id == id }
    }
    
    func getSessionsForProject(_ projectId: String) -> [ProjectSession] {
        return activeSessions.filter { $0.projectId == projectId }
    }
    
    // MARK: - Backend Integration
    
    private func fetchActiveSessions() async {
        guard let webSocketService = webSocketService,
              webSocketService.isConnected else { return }
        
        // Request sessions data
        webSocketService.sendCommand("/sessions")
        
        // Wait for response processing
        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
    }
    
    private func fetchProjectAnalysisData() async {
        guard let webSocketService = webSocketService,
              webSocketService.isConnected else { return }
        
        // For each active project/session, fetch analysis data
        for session in activeSessions {
            webSocketService.sendCommand("/ast/project/\(session.clientId)/analysis")
        }
        
        // Wait for response processing
        try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
    }
    
    private func processIncomingMessages() {
        guard let webSocketService = webSocketService else { return }
        
        // Process recent messages for project data
        let recentMessages = webSocketService.messages.suffix(5)
        
        for message in recentMessages {
            if message.type == .response {
                processProjectResponse(message.content)
            }
        }
    }
    
    private func processProjectResponse(_ content: String) {
        // Parse JSON responses for project/session data
        guard let data = content.data(using: .utf8) else { return }
        
        do {
            // Try to parse as session data
            if let sessionData = try? JSONDecoder().decode([String: Any].self, from: data),
               let sessions = sessionData["sessions"] as? [[String: Any]] {
                updateSessionsFromBackendData(sessions)
                return
            }
            
            // Try to parse as analysis data
            if let analysisData = try? JSONDecoder().decode([String: Any].self, from: data),
               let projectData = analysisData["project_analysis"] as? [String: Any] {
                updateProjectFromAnalysisData(projectData)
                return
            }
            
        } catch {
            // Ignore parsing errors for non-project messages
        }
    }
    
    private func updateSessionsFromBackendData(_ sessionData: [[String: Any]]) {
        let newSessions: [ProjectSession] = sessionData.compactMap { sessionDict in
            guard let clientId = sessionDict["client_id"] as? String,
                  let isActive = sessionDict["active"] as? Bool else {
                return nil
            }
            
            // Create or find associated project
            let projectPath = sessionDict["project_path"] as? String ?? "Unknown"
            let projectId = findOrCreateProjectForPath(projectPath)
            
            return ProjectSession(
                projectId: projectId,
                clientId: clientId,
                startTime: Date(), // Backend would provide this
                lastActivity: Date(),
                isActive: isActive
            )
        }
        
        activeSessions = newSessions
        updateProjectStatuses()
    }
    
    private func updateProjectFromAnalysisData(_ analysisData: [String: Any]) {
        guard let projectPath = analysisData["path"] as? String else { return }
        
        // Find project by path
        guard let projectIndex = projects.firstIndex(where: { $0.path == projectPath }) else {
            return
        }
        
        let currentProject = projects[projectIndex]
        
        // Extract metrics from analysis data
        let fileCount = analysisData["file_count"] as? Int ?? currentProject.metrics.fileCount
        let lineCount = analysisData["line_count"] as? Int ?? currentProject.metrics.lineCount
        let complexity = analysisData["complexity"] as? Double ?? currentProject.metrics.complexity
        let issueCount = analysisData["issue_count"] as? Int ?? currentProject.metrics.issueCount
        
        let updatedMetrics = ProjectMetrics(
            fileCount: fileCount,
            lineCount: lineCount,
            complexity: complexity,
            testCoverage: currentProject.metrics.testCoverage,
            buildTime: currentProject.metrics.buildTime,
            memoryUsage: currentProject.metrics.memoryUsage,
            cpuUsage: currentProject.metrics.cpuUsage,
            issueCount: issueCount,
            performanceScore: currentProject.metrics.performanceScore,
            lastAnalyzed: Date()
        )
        
        // Update project with new metrics
        projects[projectIndex] = Project(
            id: currentProject.id,
            name: currentProject.name,
            path: currentProject.path,
            language: detectLanguage(from: analysisData) ?? currentProject.language,
            status: .active,
            lastActivity: Date(),
            metrics: updatedMetrics,
            clientId: currentProject.clientId
        )
        
        saveProjects()
    }
    
    private func updateProjectStatuses() {
        for i in 0..<projects.count {
            let project = projects[i]
            let hasActiveSession = activeSessions.contains { 
                $0.projectId == project.id && $0.isActive 
            }
            
            let newStatus: ProjectStatus = hasActiveSession ? .active : .inactive
            let clientId = activeSessions.first { $0.projectId == project.id }?.clientId
            
            if project.status != newStatus || project.clientId != clientId {
                projects[i] = Project(
                    id: project.id,
                    name: project.name,
                    path: project.path,
                    language: project.language,
                    status: newStatus,
                    lastActivity: hasActiveSession ? Date() : project.lastActivity,
                    metrics: project.metrics,
                    clientId: clientId
                )
            }
        }
        
        saveProjects()
    }
    
    private func findOrCreateProjectForPath(_ path: String) -> String {
        // Check if project already exists for this path
        if let existingProject = projects.first(where: { $0.path == path }) {
            return existingProject.id
        }
        
        // Create new project
        let projectName = URL(fileURLWithPath: path).lastPathComponent
        let language = detectLanguageFromPath(path)
        
        let newProject = Project(
            name: projectName,
            path: path,
            language: language,
            status: .inactive
        )
        
        projects.append(newProject)
        saveProjects()
        
        return newProject.id
    }
    
    // MARK: - Utilities
    
    private func detectLanguageFromPath(_ path: String) -> ProjectLanguage {
        let url = URL(fileURLWithPath: path)
        let pathExtension = url.pathExtension.lowercased()
        
        switch pathExtension {
        case "swift": return .swift
        case "py": return .python
        case "js": return .javascript
        case "ts": return .typescript
        case "rs": return .rust
        case "go": return .go
        case "java": return .java
        case "cs": return .csharp
        case "cpp", "cc", "cxx": return .cpp
        default: return .unknown
        }
    }
    
    private func detectLanguage(from analysisData: [String: Any]) -> ProjectLanguage? {
        if let language = analysisData["primary_language"] as? String {
            return ProjectLanguage(rawValue: language.lowercased())
        }
        return nil
    }
    
    private func refreshProjectsFromBackend() {
        Task {
            await refreshProjects()
        }
    }
    
    private func startPeriodicUpdates() {
        Timer.publish(every: 30, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self = self,
                      let webSocketService = self.webSocketService,
                      webSocketService.isConnected else { return }
                
                Task {
                    await self.refreshProjects()
                }
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Persistence
    
    private func loadProjects() {
        guard let data = userDefaults.data(forKey: storageKey),
              let loadedProjects = try? JSONDecoder().decode([Project].self, from: data) else {
            projects = []
            return
        }
        projects = loadedProjects
    }
    
    private func saveProjects() {
        guard let data = try? JSONEncoder().encode(projects) else {
            print("Failed to encode projects")
            return
        }
        userDefaults.set(data, forKey: storageKey)
    }
}