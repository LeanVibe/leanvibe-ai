//
//  OnboardingManagerProtocol.swift
//  LeanVibe
//
//  Created on 2025-07-01
//  Contract-First Integration Recovery Implementation
//

import Foundation

/// Protocol defining the exact interface for onboarding management
/// This contract MUST be implemented exactly to prevent integration failures
/// Based on project-schema.yaml definitions
protocol OnboardingManagerProtocol: ObservableObject {
    
    // MARK: - Properties
    /// Set of completed onboarding steps
    var completedSteps: Set<OnboardingStep> { get }
    
    /// Whether onboarding is fully complete
    var isOnboardingComplete: Bool { get }
    
    /// Current onboarding progress (0.0 to 1.0)
    var progress: Double { get }
    
    // MARK: - Core Methods
    /// Mark onboarding step as completed and persist state
    /// - Parameter step: OnboardingStep to mark as completed
    func markStepCompleted(_ step: OnboardingStep)
    
    /// Get next step to resume onboarding flow
    /// - Returns: Next incomplete OnboardingStep, or nil if all complete
    func getNextIncompleteStep() -> OnboardingStep?
    
    /// Reset onboarding state (for debugging or re-onboarding)
    func resetOnboarding()
    
    /// Check if specific step is completed
    /// - Parameter step: OnboardingStep to check
    /// - Returns: Boolean indicating completion status
    func isStepCompleted(_ step: OnboardingStep) -> Bool
    
    // MARK: - Persistence Methods
    /// Save current onboarding state to persistent storage
    func saveState()
    
    /// Load onboarding state from persistent storage
    func loadState()
}

// MARK: - Default Implementation Helpers
extension OnboardingManagerProtocol {
    /// Default implementation for completion check
    func isStepCompleted(_ step: OnboardingStep) -> Bool {
        return completedSteps.contains(step)
    }
    
    /// Default implementation for progress calculation
    var progress: Double {
        let totalSteps = OnboardingStep.allCases.count
        let completedCount = completedSteps.count
        return totalSteps > 0 ? Double(completedCount) / Double(totalSteps) : 0.0
    }
    
    /// Default implementation for completion status
    var isOnboardingComplete: Bool {
        return completedSteps.count == OnboardingStep.allCases.count
    }
}