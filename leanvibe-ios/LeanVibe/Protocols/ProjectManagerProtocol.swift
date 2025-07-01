//
//  ProjectManagerProtocol.swift
//  LeanVibe
//
//  Created on 2025-07-01
//  Contract-First Integration Recovery Implementation
//

import Foundation
import Combine

/// Protocol defining the exact interface for project management services
/// This contract MUST be implemented exactly to prevent integration failures
/// Based on project-schema.yaml definitions
@MainActor
protocol ProjectManagerProtocol: ObservableObject {
    
    // MARK: - Published Properties
    /// Array of all projects - MUST use Project model from schema
    var projects: [Project] { get }
    
    /// Loading state indicator for UI
    var isLoading: Bool { get }
    
    /// Last error message for UI display - nil if no error
    var lastError: String? { get }
    
    // MARK: - Core Methods
    /// Fetch projects from backend or storage
    /// - Throws: Network or persistence errors
    func refreshProjects() async throws
    
    /// Add new project with persistence
    /// - Parameter project: Project to add using schema-defined Project model
    /// - Throws: Validation or persistence errors
    func addProject(_ project: Project) async throws
    
    /// Update existing project
    /// - Parameter project: Updated project data
    /// - Throws: Validation or persistence errors  
    func updateProject(_ project: Project) async throws
    
    /// Delete project by ID
    /// - Parameter projectId: UUID of project to delete
    /// - Throws: Persistence errors
    func deleteProject(_ projectId: UUID) async throws
    
    // MARK: - Computed Properties
    /// Total number of projects
    var projectCount: Int { get }
    
    /// Projects grouped by status
    var projectsByStatus: [ProjectStatus: [Project]] { get }
}

// MARK: - Default Implementation Helpers
extension ProjectManagerProtocol {
    /// Default implementation for project count
    var projectCount: Int {
        return projects.count
    }
    
    /// Default implementation for projects grouped by status
    var projectsByStatus: [ProjectStatus: [Project]] {
        return Dictionary(grouping: projects) { $0.status }
    }
}