//
//  TaskServiceProtocol.swift
//  LeanVibe
//
//  Created on 2025-07-01
//  Contract-First Integration Recovery Implementation
//

import Foundation
import Combine

/// Protocol defining the exact interface for task management services
/// This contract MUST be implemented exactly to prevent integration failures
/// CRITICAL: Uses LeanVibeTask to avoid Swift.Task conflicts
/// Based on project-schema.yaml definitions
@MainActor
protocol TaskServiceProtocol: ObservableObject {
    
    // MARK: - Published Properties
    /// Array of all tasks - MUST use LeanVibeTask from schema
    var tasks: [LeanVibeTask] { get }
    
    /// Loading state indicator for UI
    var isLoading: Bool { get }
    
    /// Last error message for UI display - nil if no error
    var lastError: String? { get }
    
    // MARK: - Core Methods
    /// Load tasks for specific project
    /// - Parameter projectId: UUID of project to load tasks for
    /// - Throws: Network or persistence errors
    func loadTasks(for projectId: UUID) async throws
    
    /// Add new task with persistence
    /// - Parameter task: LeanVibeTask to add using schema-defined model
    /// - Throws: Validation or persistence errors
    func addTask(_ task: LeanVibeTask) async throws
    
    /// Update task status for drag-and-drop operations
    /// - Parameters:
    ///   - taskId: UUID of task to update
    ///   - status: New TaskStatus from schema enum
    /// - Throws: Validation or persistence errors
    func updateTaskStatus(_ taskId: UUID, _ status: TaskStatus) async throws
    
    /// Update complete task with all properties
    /// - Parameter task: Updated LeanVibeTask data
    /// - Throws: Validation or persistence errors
    func updateTask(_ task: LeanVibeTask) async throws
    
    /// Delete task by ID
    /// - Parameter taskId: UUID of task to delete
    /// - Throws: Persistence errors
    func deleteTask(_ taskId: UUID) async throws
    
    /// Move task between projects
    /// - Parameters:
    ///   - taskId: UUID of task to move
    ///   - newProjectId: UUID of destination project
    /// - Throws: Validation or persistence errors
    func moveTask(_ taskId: UUID, to newProjectId: UUID) async throws
    
    // MARK: - Computed Properties
    /// Tasks grouped by status for Kanban columns
    var tasksByStatus: [TaskStatus: [LeanVibeTask]] { get }
    
    /// Tasks for specific project
    func tasks(for projectId: UUID) -> [LeanVibeTask]
    
    /// Task count by status
    var taskCountByStatus: [TaskStatus: Int] { get }
}

// MARK: - Default Implementation Helpers
extension TaskServiceProtocol {
    /// Default implementation for tasks grouped by status
    var tasksByStatus: [TaskStatus: [LeanVibeTask]] {
        return Dictionary(grouping: tasks) { $0.status }
    }
    
    /// Default implementation for tasks filtered by project
    func tasks(for projectId: UUID) -> [LeanVibeTask] {
        return tasks.filter { $0.projectId == projectId }
    }
    
    /// Default implementation for task count by status
    var taskCountByStatus: [TaskStatus: Int] {
        return tasksByStatus.mapValues { $0.count }
    }
}