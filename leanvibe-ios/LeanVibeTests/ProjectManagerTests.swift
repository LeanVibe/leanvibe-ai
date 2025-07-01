import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class ProjectManagerTests: XCTestCase {
    
    private var projectManager: ProjectManager!
    private var mockWebSocketService: MockWebSocketService!
    
    override func setUp() async throws {
        mockWebSocketService = MockWebSocketService()
        projectManager = ProjectManager()
        projectManager.configure(with: mockWebSocketService)
    }
    
    override func tearDown() async throws {
        projectManager = nil
        mockWebSocketService = nil
    }
    
    // MARK: - Initialization Tests
    
    func testProjectManagerInitialization() throws {
        XCTAssertTrue(projectManager.projects.isEmpty)
        XCTAssertFalse(projectManager.isLoading)
        XCTAssertNil(projectManager.lastError)
    }
    
    // MARK: - Project Loading Tests
    
    func testRefreshProjectsSuccess() async throws {
        // Given
        mockWebSocketService.shouldSucceed = true
        XCTAssertTrue(projectManager.projects.isEmpty)
        
        // When
        try await projectManager.refreshProjects()
        
        // Then
        XCTAssertFalse(projectManager.projects.isEmpty)
        XCTAssertFalse(projectManager.isLoading)
        XCTAssertNil(projectManager.lastError)
    }
    
    func testRefreshProjectsWithRetry() async throws {
        // Given - First attempt fails, then succeeds
        mockWebSocketService.shouldSucceed = false
        
        // When - This should trigger the retry mechanism
        do {
            try await projectManager.refreshProjects()
            XCTFail("Expected error on first attempt")
        } catch {
            // Expected to fail due to mock configuration
            XCTAssertNotNil(projectManager.lastError)
        }
        
        // Change mock to succeed for retry
        mockWebSocketService.shouldSucceed = true
        
        // When - Retry
        try await projectManager.refreshProjects()
        
        // Then
        XCTAssertFalse(projectManager.projects.isEmpty)
        XCTAssertNil(projectManager.lastError)
    }
    
    func testLoadSampleProjects() throws {
        // Given
        XCTAssertTrue(projectManager.projects.isEmpty)
        
        // When
        projectManager.loadSampleProjects()
        
        // Then
        XCTAssertFalse(projectManager.projects.isEmpty)
        XCTAssertGreaterThanOrEqual(projectManager.projects.count, 3)
        
        // Verify sample projects have required properties
        for project in projectManager.projects {
            XCTAssertFalse(project.displayName.isEmpty)
            XCTAssertFalse(project.path.isEmpty)
            XCTAssertNotNil(project.language)
        }
    }
    
    // MARK: - Project CRUD Tests
    
    func testAddProjectSuccess() async throws {
        // Given
        let newProject = Project(
            displayName: "Test Project",
            path: "/test/path",
            language: .swift,
            status: .active
        )
        
        // When
        try await projectManager.addProject(newProject)
        
        // Then
        XCTAssertEqual(projectManager.projects.count, 1)
        XCTAssertEqual(projectManager.projects.first?.displayName, "Test Project")
        XCTAssertEqual(projectManager.projects.first?.path, "/test/path")
        XCTAssertEqual(projectManager.projects.first?.language, .swift)
        XCTAssertNil(projectManager.lastError)
    }
    
    func testAddProjectWithEmptyName() async throws {
        // Given
        let invalidProject = Project(
            displayName: "",
            path: "/test/path",
            language: .swift,
            status: .active
        )
        
        // When & Then
        do {
            try await projectManager.addProject(invalidProject)
            XCTFail("Expected error for empty project name")
        } catch ProjectManagerError.invalidProjectName {
            // Expected error
            XCTAssertNotNil(projectManager.lastError)
            XCTAssertTrue(projectManager.projects.isEmpty)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    func testAddDuplicateProject() async throws {
        // Given
        let project1 = Project(displayName: "Project 1", path: "/same/path", language: .swift, status: .active)
        let project2 = Project(displayName: "Project 2", path: "/same/path", language: .python, status: .active)
        
        try await projectManager.addProject(project1)
        XCTAssertEqual(projectManager.projects.count, 1)
        
        // When & Then
        do {
            try await projectManager.addProject(project2)
            XCTFail("Expected error for duplicate project path")
        } catch ProjectManagerError.duplicateProject {
            // Expected error
            XCTAssertEqual(projectManager.projects.count, 1)
            XCTAssertNotNil(projectManager.lastError)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    func testRemoveProject() async throws {
        // Given
        let project = Project(displayName: "Test Project", path: "/test/path", language: .swift, status: .active)
        try await projectManager.addProject(project)
        XCTAssertEqual(projectManager.projects.count, 1)
        
        // When
        try await projectManager.removeProject(project.id)
        
        // Then
        XCTAssertTrue(projectManager.projects.isEmpty)
        XCTAssertNil(projectManager.lastError)
    }
    
    func testRemoveNonexistentProject() async throws {
        // Given
        let nonexistentId = UUID()
        
        // When & Then
        do {
            try await projectManager.removeProject(nonexistentId)
            XCTFail("Expected error for nonexistent project")
        } catch ProjectManagerError.projectNotFound {
            // Expected error
            XCTAssertNotNil(projectManager.lastError)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    func testUpdateProject() async throws {
        // Given
        var project = Project(displayName: "Original Name", path: "/test/path", language: .swift, status: .active)
        try await projectManager.addProject(project)
        
        // When
        project.displayName = "Updated Name"
        project.status = .inactive
        try await projectManager.updateProject(project)
        
        // Then
        XCTAssertEqual(projectManager.projects.count, 1)
        XCTAssertEqual(projectManager.projects.first?.displayName, "Updated Name")
        XCTAssertEqual(projectManager.projects.first?.status, .inactive)
        XCTAssertNil(projectManager.lastError)
    }
    
    // MARK: - Project Filtering Tests
    
    func testActiveProjects() throws {
        // Given
        let activeProject = Project(displayName: "Active", path: "/active", language: .swift, status: .active)
        let inactiveProject = Project(displayName: "Inactive", path: "/inactive", language: .python, status: .inactive)
        
        projectManager.projects = [activeProject, inactiveProject]
        
        // When
        let activeProjects = projectManager.activeProjects
        
        // Then
        XCTAssertEqual(activeProjects.count, 1)
        XCTAssertEqual(activeProjects.first?.displayName, "Active")
        XCTAssertEqual(activeProjects.first?.status, .active)
    }
    
    func testProjectsByLanguage() throws {
        // Given
        let swiftProject1 = Project(displayName: "Swift 1", path: "/swift1", language: .swift, status: .active)
        let swiftProject2 = Project(displayName: "Swift 2", path: "/swift2", language: .swift, status: .active)
        let pythonProject = Project(displayName: "Python", path: "/python", language: .python, status: .active)
        
        projectManager.projects = [swiftProject1, swiftProject2, pythonProject]
        
        // When
        let swiftProjects = projectManager.projects.filter { $0.language == .swift }
        let pythonProjects = projectManager.projects.filter { $0.language == .python }
        
        // Then
        XCTAssertEqual(swiftProjects.count, 2)
        XCTAssertEqual(pythonProjects.count, 1)
    }
    
    // MARK: - Data Persistence Tests
    
    func testProjectPersistence() async throws {
        // Given
        let project = Project(displayName: "Persistent Project", path: "/persistent", language: .swift, status: .active)
        try await projectManager.addProject(project)
        
        // When - Create a new ProjectManager instance (simulating app restart)
        let newProjectManager = ProjectManager()
        newProjectManager.loadPersistedProjects()
        
        // Then
        XCTAssertEqual(newProjectManager.projects.count, 1)
        XCTAssertEqual(newProjectManager.projects.first?.displayName, "Persistent Project")
    }
    
    func testClearAllProjects() async throws {
        // Given
        projectManager.loadSampleProjects()
        XCTAssertFalse(projectManager.projects.isEmpty)
        
        // When
        try await projectManager.clearAllProjects()
        
        // Then
        XCTAssertTrue(projectManager.projects.isEmpty)
        XCTAssertNil(projectManager.lastError)
    }
    
    // MARK: - WebSocket Integration Tests
    
    func testWebSocketConfiguration() throws {
        // Given
        let webSocketService = MockWebSocketService()
        let projectManager = ProjectManager()
        
        // When
        projectManager.configure(with: webSocketService)
        
        // Then
        // Configuration should complete without errors
        XCTAssertNotNil(projectManager)
    }
    
    // MARK: - Error Handling Tests
    
    func testErrorStateManagement() async throws {
        // Given
        projectManager.lastError = "Previous error"
        
        // When
        let project = Project(displayName: "Test", path: "/test", language: .swift, status: .active)
        try await projectManager.addProject(project)
        
        // Then - Successful operation should clear error
        XCTAssertNil(projectManager.lastError)
    }
    
    // MARK: - Concurrent Access Tests
    
    func testConcurrentProjectOperations() async throws {
        // Given
        let projects = (1...10).map { i in
            Project(displayName: "Project \(i)", path: "/project\(i)", language: .swift, status: .active)
        }
        
        // When - Add projects concurrently
        await withTaskGroup(of: Void.self) { group in
            for project in projects {
                group.addTask { [weak projectManager] in
                    do {
                        try await projectManager?.addProject(project)
                    } catch {
                        // Some may fail due to concurrent access
                    }
                }
            }
        }
        
        // Then - Should handle gracefully without crashes
        XCTAssertLessThanOrEqual(projectManager.projects.count, 10)
        XCTAssertGreaterThan(projectManager.projects.count, 0)
    }
    
    // MARK: - Performance Tests
    
    func testProjectLoadingPerformance() throws {
        measure {
            projectManager.loadSampleProjects()
        }
    }
    
    func testLargeProjectListPerformance() async throws {
        // Given - Add many projects
        let startTime = Date()
        
        for i in 1...100 {
            let project = Project(
                displayName: "Performance Project \(i)",
                path: "/perf/project\(i)",
                language: .swift,
                status: .active
            )
            try await projectManager.addProject(project)
        }
        
        let endTime = Date()
        let executionTime = endTime.timeIntervalSince(startTime)
        
        // Then - Should complete in reasonable time
        XCTAssertLessThan(executionTime, 5.0, "Adding 100 projects should complete within 5 seconds")
        XCTAssertEqual(projectManager.projects.count, 100)
    }
}

// MARK: - Mock WebSocket Service

@available(iOS 18.0, macOS 14.0, *)
class MockWebSocketService: WebSocketService {
    var shouldSucceed = true
    var simulatedDelay: TimeInterval = 0.1
    
    override func connect() {
        // Simulate connection behavior
        DispatchQueue.main.asyncAfter(deadline: .now() + simulatedDelay) {
            if self.shouldSucceed {
                self.isConnected = true
                self.lastError = nil
            } else {
                self.isConnected = false
                self.lastError = "Mock connection failed"
            }
        }
    }
    
    override func sendMessage(_ message: String) {
        if shouldSucceed {
            // Simulate successful message sending
            let agentMessage = AgentMessage()
            agentMessage.content = message
            agentMessage.isFromUser = true
            agentMessage.timestamp = Date()
            messages.append(agentMessage)
        } else {
            lastError = "Mock send failed"
        }
    }
}

// MARK: - Test Helpers

extension ProjectManagerTests {
    
    /// Helper to create a test project with unique properties
    func createTestProject(name: String = "Test Project") -> Project {
        return Project(
            displayName: name,
            path: "/test/\(UUID().uuidString)",
            language: .swift,
            status: .active
        )
    }
    
    /// Helper to verify project equality
    func assertProjectsEqual(_ project1: Project, _ project2: Project) {
        XCTAssertEqual(project1.id, project2.id)
        XCTAssertEqual(project1.displayName, project2.displayName)
        XCTAssertEqual(project1.path, project2.path)
        XCTAssertEqual(project1.language, project2.language)
        XCTAssertEqual(project1.status, project2.status)
    }
}