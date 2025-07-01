import XCTest
import Foundation
import SwiftUI
@testable import LeanVibe

/// Test suite for OnboardingManager and OnboardingCoordinator
/// Tests state persistence, resume functionality, and coordinator state restoration
@available(iOS 18.0, macOS 14.0, *)
@MainActor
final class OnboardingTests: XCTestCase {
    
    // MARK: - Test Dependencies
    
    private var onboardingManager: OnboardingManager!
    private var mockUserDefaults: MockUserDefaults!
    private let testUserDefaultsKey = "test_onboardingProgress"
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        mockUserDefaults = MockUserDefaults()
        onboardingManager = OnboardingManager()
        
        // Clear any existing data
        UserDefaults.standard.removeObject(forKey: "onboardingProgress")
    }
    
    override func tearDownWithError() throws {
        UserDefaults.standard.removeObject(forKey: "onboardingProgress")
        onboardingManager = nil
        mockUserDefaults = nil
        
        try super.tearDownWithError()
    }
    
    // MARK: - OnboardingManager Initialization Tests
    
    func testOnboardingManagerInitialization() {
        // Given: A fresh OnboardingManager
        let manager = OnboardingManager()
        
        // Then: Should start with empty state
        XCTAssertTrue(manager.completedSteps.isEmpty)
        XCTAssertFalse(manager.isOnboardingComplete)
        XCTAssertEqual(manager.progress, 0.0)
        XCTAssertEqual(manager.getNextIncompleteStep(), .welcome)
    }
    
    // MARK: - Step Completion Tests
    
    func testMarkStepCompleted_SingleStep() {
        // Given: A fresh onboarding manager
        XCTAssertTrue(onboardingManager.completedSteps.isEmpty)
        
        // When: Marking welcome step as completed
        onboardingManager.markStepCompleted(.welcome)
        
        // Then: Step should be marked complete
        XCTAssertTrue(onboardingManager.completedSteps.contains(.welcome))
        XCTAssertTrue(onboardingManager.isStepCompleted(.welcome))
        XCTAssertEqual(onboardingManager.completedSteps.count, 1)
        XCTAssertFalse(onboardingManager.isOnboardingComplete)
    }
    
    func testMarkStepCompleted_MultipleSteps() {
        // Given: A fresh onboarding manager
        let stepsToComplete: [OnboardingStep] = [.welcome, .voicePermissions, .projectSetup]
        
        // When: Marking multiple steps as completed
        for step in stepsToComplete {
            onboardingManager.markStepCompleted(step)
        }
        
        // Then: All steps should be marked complete
        XCTAssertEqual(onboardingManager.completedSteps.count, 3)
        for step in stepsToComplete {
            XCTAssertTrue(onboardingManager.isStepCompleted(step))
        }
        XCTAssertFalse(onboardingManager.isOnboardingComplete)
    }
    
    func testMarkStepCompleted_DuplicateSteps() {
        // Given: A fresh onboarding manager
        
        // When: Marking the same step multiple times
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.welcome)
        
        // Then: Step should only be counted once
        XCTAssertEqual(onboardingManager.completedSteps.count, 1)
        XCTAssertTrue(onboardingManager.isStepCompleted(.welcome))
    }
    
    func testMarkStepCompleted_AllSteps() {
        // Given: A fresh onboarding manager
        let allSteps = OnboardingStep.allCases
        
        // When: Completing all onboarding steps
        for step in allSteps {
            onboardingManager.markStepCompleted(step)
        }
        
        // Then: Onboarding should be complete
        XCTAssertEqual(onboardingManager.completedSteps.count, allSteps.count)
        XCTAssertTrue(onboardingManager.isOnboardingComplete)
        XCTAssertEqual(onboardingManager.progress, 1.0)
        XCTAssertNil(onboardingManager.getNextIncompleteStep())
    }
    
    // MARK: - Progress Calculation Tests
    
    func testProgressCalculation() {
        // Given: Total number of onboarding steps
        let totalSteps = OnboardingStep.allCases.count
        
        // Test 0% progress
        XCTAssertEqual(onboardingManager.progress, 0.0)
        
        // Test 25% progress (approximately)
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.voicePermissions)
        let expectedProgress25 = 2.0 / Double(totalSteps)
        XCTAssertEqual(onboardingManager.progress, expectedProgress25, accuracy: 0.01)
        
        // Test 50% progress (approximately) 
        let midPoint = totalSteps / 2
        let additionalSteps = Array(OnboardingStep.allCases.dropFirst(2).prefix(midPoint - 2))
        for step in additionalSteps {
            onboardingManager.markStepCompleted(step)
        }
        let expectedProgress50 = Double(midPoint) / Double(totalSteps)
        XCTAssertEqual(onboardingManager.progress, expectedProgress50, accuracy: 0.1)
        
        // Test 100% progress
        for step in OnboardingStep.allCases {
            onboardingManager.markStepCompleted(step)
        }
        XCTAssertEqual(onboardingManager.progress, 1.0)
    }
    
    // MARK: - Next Incomplete Step Tests
    
    func testGetNextIncompleteStep_EmptyState() {
        // Given: No completed steps
        
        // When: Getting next incomplete step
        let nextStep = onboardingManager.getNextIncompleteStep()
        
        // Then: Should return the first step
        XCTAssertEqual(nextStep, .welcome)
    }
    
    func testGetNextIncompleteStep_PartialProgress() {
        // Given: Some completed steps
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.voicePermissions)
        
        // When: Getting next incomplete step
        let nextStep = onboardingManager.getNextIncompleteStep()
        
        // Then: Should return the next step in sequence
        XCTAssertEqual(nextStep, .projectSetup)
    }
    
    func testGetNextIncompleteStep_NonSequentialCompletion() {
        // Given: Steps completed out of order
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.dashboardTour) // Skip ahead
        onboardingManager.markStepCompleted(.completion) // Skip to end
        
        // When: Getting next incomplete step
        let nextStep = onboardingManager.getNextIncompleteStep()
        
        // Then: Should return the first incomplete step in sequence
        XCTAssertEqual(nextStep, .voicePermissions)
    }
    
    func testGetNextIncompleteStep_AllComplete() {
        // Given: All steps completed
        for step in OnboardingStep.allCases {
            onboardingManager.markStepCompleted(step)
        }
        
        // When: Getting next incomplete step
        let nextStep = onboardingManager.getNextIncompleteStep()
        
        // Then: Should return nil
        XCTAssertNil(nextStep)
    }
    
    // MARK: - Reset Onboarding Tests
    
    func testResetOnboarding() {
        // Given: Partially completed onboarding
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.voicePermissions)
        onboardingManager.markStepCompleted(.projectSetup)
        
        XCTAssertEqual(onboardingManager.completedSteps.count, 3)
        XCTAssertGreaterThan(onboardingManager.progress, 0.0)
        
        // When: Resetting onboarding
        onboardingManager.resetOnboarding()
        
        // Then: Should clear all progress
        XCTAssertTrue(onboardingManager.completedSteps.isEmpty)
        XCTAssertFalse(onboardingManager.isOnboardingComplete)
        XCTAssertEqual(onboardingManager.progress, 0.0)
        XCTAssertEqual(onboardingManager.getNextIncompleteStep(), .welcome)
    }
    
    // MARK: - State Persistence Tests
    
    func testStatePersistence_SaveAndLoad() throws {
        // Given: A fresh manager with some completed steps
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.voicePermissions)
        onboardingManager.markStepCompleted(.projectSetup)
        
        let originalCompletedSteps = onboardingManager.completedSteps
        let originalProgress = onboardingManager.progress
        
        // When: Creating a new manager (simulates app restart)
        let newManager = OnboardingManager()
        
        // Then: State should be restored from persistence
        XCTAssertEqual(newManager.completedSteps, originalCompletedSteps)
        XCTAssertEqual(newManager.progress, originalProgress, accuracy: 0.01)
        XCTAssertEqual(newManager.getNextIncompleteStep(), .dashboardTour)
    }
    
    func testStatePersistence_EmptyState() {
        // Given: A manager with no completed steps
        XCTAssertTrue(onboardingManager.completedSteps.isEmpty)
        
        // When: Creating a new manager
        let newManager = OnboardingManager()
        
        // Then: Should start with empty state
        XCTAssertTrue(newManager.completedSteps.isEmpty)
        XCTAssertEqual(newManager.progress, 0.0)
        XCTAssertEqual(newManager.getNextIncompleteStep(), .welcome)
    }
    
    func testStatePersistence_CompleteOnboarding() {
        // Given: Fully completed onboarding
        for step in OnboardingStep.allCases {
            onboardingManager.markStepCompleted(step)
        }
        
        XCTAssertTrue(onboardingManager.isOnboardingComplete)
        
        // When: Creating a new manager
        let newManager = OnboardingManager()
        
        // Then: Should restore complete state
        XCTAssertTrue(newManager.isOnboardingComplete)
        XCTAssertEqual(newManager.progress, 1.0)
        XCTAssertNil(newManager.getNextIncompleteStep())
    }
    
    func testStatePersistence_CorruptedData() {
        // Given: Corrupted data in UserDefaults
        let corruptedData = "invalid json data".data(using: .utf8)!
        UserDefaults.standard.set(corruptedData, forKey: "onboardingProgress")
        
        // When: Creating a new manager with corrupted data
        let newManager = OnboardingManager()
        
        // Then: Should handle gracefully and start fresh
        XCTAssertTrue(newManager.completedSteps.isEmpty)
        XCTAssertEqual(newManager.progress, 0.0)
        XCTAssertEqual(newManager.getNextIncompleteStep(), .welcome)
    }
    
    // MARK: - OnboardingCoordinator State Restoration Tests
    
    func testOnboardingCoordinatorInitialization() {
        // Given: A fresh OnboardingCoordinator (simulated via direct testing)
        let manager = OnboardingManager()
        
        // When: Determining initial state
        let shouldShowCompletion = manager.isOnboardingComplete
        let nextStep = manager.getNextIncompleteStep()
        
        // Then: Should start at welcome if no progress
        XCTAssertFalse(shouldShowCompletion)
        XCTAssertEqual(nextStep, .welcome)
    }
    
    func testOnboardingCoordinatorStateRestoration_PartialProgress() {
        // Given: Manager with partial progress
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.voicePermissions)
        
        // When: Determining restore state (simulates coordinator onAppear)
        let isComplete = onboardingManager.isOnboardingComplete
        let nextStep = onboardingManager.getNextIncompleteStep()
        
        // Then: Should restore to correct step
        XCTAssertFalse(isComplete)
        XCTAssertEqual(nextStep, .projectSetup)
    }
    
    func testOnboardingCoordinatorStateRestoration_CompleteOnboarding() {
        // Given: Fully completed onboarding
        for step in OnboardingStep.allCases {
            onboardingManager.markStepCompleted(step)
        }
        
        // When: Determining restore state
        let isComplete = onboardingManager.isOnboardingComplete
        let nextStep = onboardingManager.getNextIncompleteStep()
        
        // Then: Should show completion
        XCTAssertTrue(isComplete)
        XCTAssertNil(nextStep)
    }
    
    func testOnboardingCoordinatorStateRestoration_EmptyProgress() {
        // Given: No progress saved
        
        // When: Determining restore state
        let isComplete = onboardingManager.isOnboardingComplete
        let nextStep = onboardingManager.getNextIncompleteStep()
        
        // Then: Should start from beginning
        XCTAssertFalse(isComplete)
        XCTAssertEqual(nextStep, .welcome)
    }
    
    // MARK: - Integration Tests
    
    func testFullOnboardingFlow() {
        // Given: A fresh onboarding manager
        XCTAssertEqual(onboardingManager.getNextIncompleteStep(), .welcome)
        
        // When: Completing onboarding step by step
        let allSteps = OnboardingStep.allCases
        
        for (index, step) in allSteps.enumerated() {
            // Before completing this step
            XCTAssertEqual(onboardingManager.getNextIncompleteStep(), step)
            XCTAssertFalse(onboardingManager.isStepCompleted(step))
            
            // Complete the step
            onboardingManager.markStepCompleted(step)
            
            // Verify step is completed
            XCTAssertTrue(onboardingManager.isStepCompleted(step))
            
            // Check progress
            let expectedProgress = Double(index + 1) / Double(allSteps.count)
            XCTAssertEqual(onboardingManager.progress, expectedProgress, accuracy: 0.01)
            
            // Check if onboarding is complete
            if index == allSteps.count - 1 {
                XCTAssertTrue(onboardingManager.isOnboardingComplete)
                XCTAssertNil(onboardingManager.getNextIncompleteStep())
            } else {
                XCTAssertFalse(onboardingManager.isOnboardingComplete)
                XCTAssertEqual(onboardingManager.getNextIncompleteStep(), allSteps[index + 1])
            }
        }
    }
    
    func testOnboardingPersistenceAcrossAppRestarts() {
        // Simulate multiple app sessions
        
        // Session 1: Complete first few steps
        onboardingManager.markStepCompleted(.welcome)
        onboardingManager.markStepCompleted(.voicePermissions)
        let session1Progress = onboardingManager.progress
        let session1NextStep = onboardingManager.getNextIncompleteStep()
        
        // Simulate app restart - create new manager
        let manager2 = OnboardingManager()
        XCTAssertEqual(manager2.progress, session1Progress, accuracy: 0.01)
        XCTAssertEqual(manager2.getNextIncompleteStep(), session1NextStep)
        
        // Session 2: Complete more steps
        manager2.markStepCompleted(.projectSetup)
        manager2.markStepCompleted(.dashboardTour)
        let session2Progress = manager2.progress
        let session2NextStep = manager2.getNextIncompleteStep()
        
        // Simulate another app restart
        let manager3 = OnboardingManager()
        XCTAssertEqual(manager3.progress, session2Progress, accuracy: 0.01)
        XCTAssertEqual(manager3.getNextIncompleteStep(), session2NextStep)
        
        // Session 3: Complete onboarding
        for step in OnboardingStep.allCases {
            manager3.markStepCompleted(step)
        }
        XCTAssertTrue(manager3.isOnboardingComplete)
        
        // Final restart - should remember completion
        let manager4 = OnboardingManager()
        XCTAssertTrue(manager4.isOnboardingComplete)
        XCTAssertEqual(manager4.progress, 1.0)
        XCTAssertNil(manager4.getNextIncompleteStep())
    }
    
    // MARK: - Edge Cases & Error Handling
    
    func testOnboardingStepEnum_AllCasesCount() {
        // Verify we have the expected number of onboarding steps
        let expectedStepCount = 9 // Based on OnboardingStep enum
        XCTAssertEqual(OnboardingStep.allCases.count, expectedStepCount)
    }
    
    func testOnboardingStepEnum_OrderConsistency() {
        // Verify the order of steps is consistent
        let steps = OnboardingStep.allCases
        XCTAssertEqual(steps[0], .welcome)
        XCTAssertEqual(steps[1], .voicePermissions)
        XCTAssertEqual(steps[2], .projectSetup)
        XCTAssertEqual(steps[3], .dashboardTour)
        XCTAssertEqual(steps[4], .voiceCommandDemo)
        XCTAssertEqual(steps[5], .architectureViewer)
        XCTAssertEqual(steps[6], .kanbanIntroduction)
        XCTAssertEqual(steps[7], .advancedFeatures)
        XCTAssertEqual(steps[8], .completion)
    }
    
    func testProgressCalculation_EdgeCases() {
        // Test with zero steps (edge case, shouldn't happen)
        // We can't modify the enum, but we can test the current behavior
        
        // Test progress with single step
        onboardingManager.markStepCompleted(.welcome)
        let singleStepProgress = 1.0 / Double(OnboardingStep.allCases.count)
        XCTAssertEqual(onboardingManager.progress, singleStepProgress, accuracy: 0.01)
    }
    
    // MARK: - Performance Tests
    
    func testOnboardingPerformance_MultipleStepCompletion() {
        // Measure performance of completing all steps
        measure {
            let manager = OnboardingManager()
            for step in OnboardingStep.allCases {
                manager.markStepCompleted(step)
            }
        }
    }
    
    func testStatePersistencePerformance() {
        // Complete several steps to have data to persist
        for step in OnboardingStep.allCases.prefix(5) {
            onboardingManager.markStepCompleted(step)
        }
        
        // Measure performance of state persistence (save + load)
        measure {
            let manager = OnboardingManager() // Triggers load
            manager.markStepCompleted(.completion) // Triggers save
        }
    }
}

// MARK: - Mock Dependencies

/// Mock UserDefaults for testing without affecting real user defaults
class MockUserDefaults: UserDefaults {
    private var storage: [String: Any] = [:]
    
    override func set(_ value: Any?, forKey defaultName: String) {
        storage[defaultName] = value
    }
    
    override func data(forKey defaultName: String) -> Data? {
        return storage[defaultName] as? Data
    }
    
    override func removeObject(forKey defaultName: String) {
        storage.removeValue(forKey: defaultName)
    }
    
    override func object(forKey defaultName: String) -> Any? {
        return storage[defaultName]
    }
}