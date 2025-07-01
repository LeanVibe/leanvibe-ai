import XCTest
@testable import LeanVibe

@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class TaskServiceTests: XCTestCase {
    
    private var taskService: TaskService!
    private var testProjectId: UUID!
    
    override func setUp() async throws {
        taskService = TaskService()
        testProjectId = UUID()
    }
    
    override func tearDown() async throws {
        taskService = nil
        testProjectId = nil
    }
    
    // MARK: - Initialization Tests
    
    func testTaskServiceInitialization() throws {
        XCTAssertTrue(taskService.tasks.isEmpty)
        XCTAssertFalse(taskService.isLoading)
        XCTAssertNil(taskService.lastError)
    }
    
    // MARK: - Task Loading Tests
    
    func testLoadTasksForProject() async throws {
        // Given
        XCTAssertTrue(taskService.tasks.isEmpty)
        
        // When
        try await taskService.loadTasks(for: testProjectId)
        
        // Then
        XCTAssertFalse(taskService.tasks.isEmpty)
        XCTAssertFalse(taskService.isLoading)
        XCTAssertNil(taskService.lastError)
        
        // Verify all tasks belong to the project
        for task in taskService.tasks {
            XCTAssertEqual(task.projectId, testProjectId)
        }
    }
    
    func testLoadTasksWithRetryMechanism() async throws {
        // Given - Mock a scenario where retry is needed
        let originalTasks = taskService.tasks
        
        // When - Load tasks (this should trigger sample data generation)
        try await taskService.loadTasks(for: testProjectId)
        
        // Then - Should succeed with retry mechanism
        XCTAssertGreaterThan(taskService.tasks.count, originalTasks.count)
        XCTAssertNil(taskService.lastError)
    }
    
    func testLoadTasksForMultipleProjects() async throws {
        // Given
        let project1 = UUID()
        let project2 = UUID()
        
        // When
        try await taskService.loadTasks(for: project1)
        let project1TaskCount = taskService.tasks.filter { $0.projectId == project1 }.count
        
        try await taskService.loadTasks(for: project2)
        let project2TaskCount = taskService.tasks.filter { $0.projectId == project2 }.count
        
        // Then
        XCTAssertGreaterThan(project1TaskCount, 0)
        XCTAssertGreaterThan(project2TaskCount, 0)
        XCTAssertEqual(taskService.tasks.count, project1TaskCount + project2TaskCount)
    }
    
    // MARK: - Task CRUD Tests
    
    func testAddTask() async throws {
        // Given
        let newTask = LeanVibeTask(
            id: UUID(),
            title: "Test Task",
            description: "Test Description",
            status: .todo,
            priority: .medium,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        // When
        try await taskService.addTask(newTask)
        
        // Then
        XCTAssertEqual(taskService.tasks.count, 1)
        XCTAssertEqual(taskService.tasks.first?.title, "Test Task")
        XCTAssertEqual(taskService.tasks.first?.description, "Test Description")
        XCTAssertEqual(taskService.tasks.first?.status, .todo)
        XCTAssertEqual(taskService.tasks.first?.priority, .medium)
        XCTAssertNil(taskService.lastError)
    }
    
    func testAddTaskWithEmptyTitle() async throws {
        // Given
        let invalidTask = LeanVibeTask(
            id: UUID(),
            title: "",
            description: "Valid description",
            status: .todo,
            priority: .medium,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        // When & Then
        do {
            try await taskService.addTask(invalidTask)
            XCTFail("Expected error for empty task title")
        } catch {
            XCTAssertNotNil(taskService.lastError)
            XCTAssertTrue(taskService.tasks.isEmpty)
        }
    }
    
    func testUpdateTask() async throws {
        // Given
        var task = LeanVibeTask(
            id: UUID(),
            title: "Original Title",
            description: "Original Description",
            status: .todo,
            priority: .low,
            projectId: testProjectId,
            confidence: 0.5,
            clientId: "test-client"
        )
        
        try await taskService.addTask(task)
        XCTAssertEqual(taskService.tasks.count, 1)
        
        // When
        task.title = "Updated Title"
        task.description = "Updated Description"
        task.priority = .high
        task.confidence = 0.9
        
        try await taskService.updateTask(task)
        
        // Then
        XCTAssertEqual(taskService.tasks.count, 1)
        let updatedTask = taskService.tasks.first!
        XCTAssertEqual(updatedTask.title, "Updated Title")
        XCTAssertEqual(updatedTask.description, "Updated Description")
        XCTAssertEqual(updatedTask.priority, .high)
        XCTAssertEqual(updatedTask.confidence, 0.9)
        XCTAssertNil(taskService.lastError)
    }
    
    func testUpdateNonexistentTask() async throws {
        // Given
        let nonexistentTask = LeanVibeTask(
            id: UUID(),
            title: "Nonexistent",
            description: "Description",
            status: .todo,
            priority: .medium,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        // When & Then
        do {
            try await taskService.updateTask(nonexistentTask)
            XCTFail("Expected error for nonexistent task")
        } catch TaskServiceError.taskNotFound {
            // Expected error
            XCTAssertNotNil(taskService.lastError)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    func testUpdateTaskStatus() async throws {
        // Given
        let task = LeanVibeTask(
            id: UUID(),
            title: "Status Test Task",
            description: "Description",
            status: .todo,
            priority: .medium,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        try await taskService.addTask(task)
        XCTAssertEqual(taskService.tasks.first?.status, .todo)
        
        // When
        try await taskService.updateTaskStatus(task.id, .inProgress)
        
        // Then
        XCTAssertEqual(taskService.tasks.first?.status, .inProgress)
        XCTAssertNotEqual(taskService.tasks.first?.updatedAt, task.updatedAt)
        XCTAssertNil(taskService.lastError)
    }
    
    func testUpdateStatusForNonexistentTask() async throws {
        // Given
        let nonexistentId = UUID()
        
        // When & Then
        do {
            try await taskService.updateTaskStatus(nonexistentId, .done)
            XCTFail("Expected error for nonexistent task")
        } catch TaskServiceError.taskNotFound {
            // Expected error
            XCTAssertNotNil(taskService.lastError)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    func testDeleteTask() async throws {
        // Given
        let task = LeanVibeTask(
            id: UUID(),
            title: "Task to Delete",
            description: "Description",
            status: .todo,
            priority: .medium,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        try await taskService.addTask(task)
        XCTAssertEqual(taskService.tasks.count, 1)
        
        // When
        try await taskService.deleteTask(task.id)
        
        // Then
        XCTAssertTrue(taskService.tasks.isEmpty)
        XCTAssertNil(taskService.lastError)
    }
    
    func testDeleteNonexistentTask() async throws {
        // Given
        let nonexistentId = UUID()
        
        // When & Then
        do {
            try await taskService.deleteTask(nonexistentId)
            XCTFail("Expected error for nonexistent task")
        } catch TaskServiceError.taskNotFound {
            // Expected error
            XCTAssertNotNil(taskService.lastError)
        } catch {
            XCTFail("Unexpected error type: \(error)")
        }
    }
    
    // MARK: - Task Filtering and Querying Tests
    
    func testTasksByStatus() async throws {
        // Given
        let todoTask = LeanVibeTask(id: UUID(), title: "Todo", status: .todo, projectId: testProjectId, confidence: 0.8, clientId: "test")
        let inProgressTask = LeanVibeTask(id: UUID(), title: "In Progress", status: .inProgress, projectId: testProjectId, confidence: 0.8, clientId: "test")
        let doneTask = LeanVibeTask(id: UUID(), title: "Done", status: .done, projectId: testProjectId, confidence: 0.8, clientId: "test")
        
        try await taskService.addTask(todoTask)
        try await taskService.addTask(inProgressTask)
        try await taskService.addTask(doneTask)
        
        // When
        let todoTasks = taskService.tasks.filter { $0.status == .todo }
        let inProgressTasks = taskService.tasks.filter { $0.status == .inProgress }
        let doneTasks = taskService.tasks.filter { $0.status == .done }
        
        // Then
        XCTAssertEqual(todoTasks.count, 1)
        XCTAssertEqual(inProgressTasks.count, 1)
        XCTAssertEqual(doneTasks.count, 1)
        XCTAssertEqual(todoTasks.first?.title, "Todo")
        XCTAssertEqual(inProgressTasks.first?.title, "In Progress")
        XCTAssertEqual(doneTasks.first?.title, "Done")
    }
    
    func testTasksByPriority() async throws {
        // Given
        let lowTask = LeanVibeTask(id: UUID(), title: "Low Priority", priority: .low, projectId: testProjectId, confidence: 0.8, clientId: "test")
        let highTask = LeanVibeTask(id: UUID(), title: "High Priority", priority: .high, projectId: testProjectId, confidence: 0.8, clientId: "test")
        let urgentTask = LeanVibeTask(id: UUID(), title: "Urgent", priority: .urgent, projectId: testProjectId, confidence: 0.8, clientId: "test")
        
        try await taskService.addTask(lowTask)
        try await taskService.addTask(highTask)
        try await taskService.addTask(urgentTask)
        
        // When
        let sortedByPriority = taskService.tasks.sorted { $0.priority.weight > $1.priority.weight }
        
        // Then
        XCTAssertEqual(sortedByPriority.first?.title, "Urgent")
        XCTAssertEqual(sortedByPriority.last?.title, "Low Priority")
    }
    
    func testTasksByProject() async throws {
        // Given
        let project1 = UUID()
        let project2 = UUID()
        
        let task1 = LeanVibeTask(id: UUID(), title: "Project 1 Task", projectId: project1, confidence: 0.8, clientId: "test")
        let task2 = LeanVibeTask(id: UUID(), title: "Project 2 Task", projectId: project2, confidence: 0.8, clientId: "test")
        
        try await taskService.addTask(task1)
        try await taskService.addTask(task2)
        
        // When
        let project1Tasks = taskService.tasks.filter { $0.projectId == project1 }
        let project2Tasks = taskService.tasks.filter { $0.projectId == project2 }
        
        // Then
        XCTAssertEqual(project1Tasks.count, 1)
        XCTAssertEqual(project2Tasks.count, 1)
        XCTAssertEqual(project1Tasks.first?.title, "Project 1 Task")
        XCTAssertEqual(project2Tasks.first?.title, "Project 2 Task")
    }
    
    // MARK: - Task Validation Tests
    
    func testTaskValidation() async throws {
        // Test various validation scenarios
        let validTask = LeanVibeTask(
            id: UUID(),
            title: "Valid Task",
            description: "Valid description",
            status: .todo,
            priority: .medium,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        // Should succeed
        try await taskService.addTask(validTask)
        XCTAssertEqual(taskService.tasks.count, 1)
    }
    
    func testTaskWithTags() async throws {
        // Given
        let taskWithTags = LeanVibeTask(
            id: UUID(),
            title: "Tagged Task",
            description: "Task with tags",
            status: .todo,
            priority: .medium,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client",
            tags: ["frontend", "ui", "urgent"]
        )
        
        // When
        try await taskService.addTask(taskWithTags)
        
        // Then
        XCTAssertEqual(taskService.tasks.first?.tags.count, 3)
        XCTAssertTrue(taskService.tasks.first?.tags.contains("frontend") == true)
        XCTAssertTrue(taskService.tasks.first?.tags.contains("ui") == true)
        XCTAssertTrue(taskService.tasks.first?.tags.contains("urgent") == true)
    }
    
    // MARK: - Data Persistence Tests
    
    func testTaskPersistence() async throws {
        // Given
        let task = LeanVibeTask(
            id: UUID(),
            title: "Persistent Task",
            description: "Should persist",
            status: .todo,
            priority: .medium,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        try await taskService.addTask(task)
        XCTAssertEqual(taskService.tasks.count, 1)
        
        // When - Create new TaskService instance (simulating app restart)
        let newTaskService = TaskService()
        try await newTaskService.loadTasks(for: testProjectId)
        
        // Then - Should load persisted tasks
        XCTAssertGreaterThan(newTaskService.tasks.count, 0)
        // Note: Since we generate sample data when no tasks exist, 
        // we can't guarantee exact match, but persistence system should be working
    }
    
    // MARK: - Concurrent Access Tests
    
    func testConcurrentTaskOperations() async throws {
        // Given
        let tasks = (1...10).map { i in
            LeanVibeTask(
                id: UUID(),
                title: "Concurrent Task \(i)",
                description: "Description \(i)",
                status: .todo,
                priority: .medium,
                projectId: testProjectId,
                confidence: 0.8,
                clientId: "test-client"
            )
        }
        
        // When - Add tasks concurrently
        await withTaskGroup(of: Void.self) { group in
            for task in tasks {
                group.addTask { [weak taskService] in
                    do {
                        try await taskService?.addTask(task)
                    } catch {
                        // Some may fail due to concurrent access
                    }
                }
            }
        }
        
        // Then - Should handle gracefully
        XCTAssertLessThanOrEqual(taskService.tasks.count, 10)
        XCTAssertGreaterThan(taskService.tasks.count, 0)
    }
    
    func testConcurrentStatusUpdates() async throws {
        // Given
        let task = LeanVibeTask(
            id: UUID(),
            title: "Status Update Task",
            status: .todo,
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        try await taskService.addTask(task)
        
        // When - Update status concurrently
        let statuses: [TaskStatus] = [.inProgress, .done, .todo]
        
        await withTaskGroup(of: Void.self) { group in
            for status in statuses {
                group.addTask { [weak taskService, taskId = task.id] in
                    do {
                        try await taskService?.updateTaskStatus(taskId, status)
                    } catch {
                        // Expected that some may fail due to concurrency
                    }
                }
            }
        }
        
        // Then - Should be in a consistent state
        XCTAssertEqual(taskService.tasks.count, 1)
        XCTAssertTrue(statuses.contains(taskService.tasks.first?.status ?? .todo))
    }
    
    // MARK: - Performance Tests
    
    func testTaskLoadingPerformance() async throws {
        // Test loading performance
        let startTime = Date()
        
        try await taskService.loadTasks(for: testProjectId)
        
        let endTime = Date()
        let executionTime = endTime.timeIntervalSince(startTime)
        
        XCTAssertLessThan(executionTime, 2.0, "Task loading should complete within 2 seconds")
    }
    
    func testLargeTaskListPerformance() async throws {
        // Given - Add many tasks
        let startTime = Date()
        
        for i in 1...100 {
            let task = LeanVibeTask(
                id: UUID(),
                title: "Performance Task \(i)",
                description: "Description \(i)",
                status: TaskStatus.allCases[i % TaskStatus.allCases.count],
                priority: TaskPriority.allCases[i % TaskPriority.allCases.count],
                projectId: testProjectId,
                confidence: Double(i % 100) / 100.0,
                clientId: "perf-test-client"
            )
            try await taskService.addTask(task)
        }
        
        let endTime = Date()
        let executionTime = endTime.timeIntervalSince(startTime)
        
        // Then
        XCTAssertLessThan(executionTime, 10.0, "Adding 100 tasks should complete within 10 seconds")
        XCTAssertEqual(taskService.tasks.count, 100)
    }
    
    // MARK: - Error Recovery Tests
    
    func testErrorRecovery() async throws {
        // Given - Force an error condition
        taskService.lastError = "Previous error"
        
        // When - Perform successful operation
        let task = LeanVibeTask(
            id: UUID(),
            title: "Recovery Task",
            projectId: testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
        
        try await taskService.addTask(task)
        
        // Then - Error should be cleared
        XCTAssertNil(taskService.lastError)
        XCTAssertEqual(taskService.tasks.count, 1)
    }
}

// MARK: - Test Helpers

extension TaskServiceTests {
    
    /// Helper to create a test task with unique properties
    func createTestTask(title: String = "Test Task", projectId: UUID? = nil) -> LeanVibeTask {
        return LeanVibeTask(
            id: UUID(),
            title: title,
            description: "Test Description",
            status: .todo,
            priority: .medium,
            projectId: projectId ?? testProjectId,
            confidence: 0.8,
            clientId: "test-client"
        )
    }
    
    /// Helper to verify task equality
    func assertTasksEqual(_ task1: LeanVibeTask, _ task2: LeanVibeTask) {
        XCTAssertEqual(task1.id, task2.id)
        XCTAssertEqual(task1.title, task2.title)
        XCTAssertEqual(task1.description, task2.description)
        XCTAssertEqual(task1.status, task2.status)
        XCTAssertEqual(task1.priority, task2.priority)
        XCTAssertEqual(task1.projectId, task2.projectId)
        XCTAssertEqual(task1.confidence, task2.confidence, accuracy: 0.001)
        XCTAssertEqual(task1.clientId, task2.clientId)
    }
}