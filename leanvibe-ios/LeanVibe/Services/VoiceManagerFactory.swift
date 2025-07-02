import Foundation
import SwiftUI
import Combine

/// Factory for creating voice management services with feature flag support
/// Provides gradual migration from legacy voice managers to UnifiedVoiceService
@available(iOS 18.0, macOS 14.0, *)
@MainActor
class VoiceManagerFactory: ObservableObject {
    
    // MARK: - Published State
    @Published private(set) var currentVoiceService: Any // Can be UnifiedVoiceService or legacy manager
    @Published private(set) var isUsingUnifiedService: Bool
    @Published private(set) var migrationStatus: MigrationStatus = .notStarted
    
    // MARK: - Dependencies
    private let appConfiguration: AppConfiguration
    private let speechService: SpeechRecognitionService
    private let webSocketService: WebSocketService
    private let projectManager: ProjectManager
    private let settingsManager: SettingsManager
    
    // MARK: - Legacy Services (for fallback)
    private var legacyGlobalVoiceManager: GlobalVoiceManager?
    private var legacyOptimizedVoiceManager: OptimizedVoiceManager?
    
    // MARK: - Initialization
    
    init(
        appConfiguration: AppConfiguration = AppConfiguration.shared,
        speechService: SpeechRecognitionService? = nil,
        webSocketService: WebSocketService? = nil,
        projectManager: ProjectManager? = nil,
        settingsManager: SettingsManager? = nil
    ) {
        self.appConfiguration = appConfiguration
        self.speechService = speechService ?? SpeechRecognitionService()
        self.webSocketService = webSocketService ?? WebSocketService.shared
        self.projectManager = projectManager ?? ProjectManager()
        self.settingsManager = settingsManager ?? SettingsManager.shared
        
        // Initialize required properties based on feature flag
        let useUnified = appConfiguration.useUnifiedVoiceService
        self.isUsingUnifiedService = useUnified
        
        if useUnified {
            self.currentVoiceService = UnifiedVoiceService.shared
            self.migrationStatus = .completed
        } else {
            // Initialize with legacy service - we'll set this after self is fully initialized
            self.currentVoiceService = VoiceManager(
                speechService: self.speechService,
                webSocketService: self.webSocketService
            )
            self.migrationStatus = .usingLegacy
        }
        
        // Now that self is fully initialized, set up legacy services if needed
        if !useUnified {
            setupLegacyServices()
        }
        
        setupMigrationLogging()
    }
    
    // MARK: - Public Interface
    
    /// Get the current voice service as UnifiedVoiceService (if using unified service)
    var unifiedVoiceService: UnifiedVoiceService? {
        return currentVoiceService as? UnifiedVoiceService
    }
    
    /// Get the current voice service as legacy VoiceManager (if using legacy)
    var legacyVoiceManager: VoiceManager? {
        return currentVoiceService as? VoiceManager
    }
    
    /// Get global voice manager (only available in legacy mode)
    var globalVoiceManager: GlobalVoiceManager? {
        return legacyGlobalVoiceManager
    }
    
    /// Get optimized voice manager (only available in legacy mode)
    var optimizedVoiceManager: OptimizedVoiceManager? {
        return legacyOptimizedVoiceManager
    }
    
    /// Migrate to UnifiedVoiceService at runtime
    func migrateToUnifiedService() async {
        guard !isUsingUnifiedService else {
            print("🎤 VoiceManagerFactory: Already using UnifiedVoiceService")
            return
        }
        
        migrationStatus = .migrating
        print("🎤 VoiceManagerFactory: Starting migration to UnifiedVoiceService...")
        
        // Stop any active legacy services
        await stopLegacyServices()
        
        // Switch to unified service
        currentVoiceService = UnifiedVoiceService.shared
        isUsingUnifiedService = true
        migrationStatus = .completed
        
        print("🎤 VoiceManagerFactory: Migration to UnifiedVoiceService completed")
    }
    
    /// Fallback to legacy services (for testing or emergency)
    func fallbackToLegacyServices() async {
        guard isUsingUnifiedService else {
            print("🎤 VoiceManagerFactory: Already using legacy services")
            return
        }
        
        migrationStatus = .fallingBack
        print("🎤 VoiceManagerFactory: Falling back to legacy services...")
        
        // Stop unified service
        if let unifiedService = currentVoiceService as? UnifiedVoiceService {
            unifiedService.reset()
        }
        
        // Switch to legacy services
        currentVoiceService = createLegacyVoiceManager()
        isUsingUnifiedService = false
        migrationStatus = .usingLegacy
        
        print("🎤 VoiceManagerFactory: Fallback to legacy services completed")
    }
    
    /// Reset all voice services
    func resetAllServices() async {
        if isUsingUnifiedService {
            unifiedVoiceService?.reset()
        } else {
            await stopLegacyServices()
        }
    }
    
    // MARK: - Private Implementation
    
    private func setupLegacyServices() {
        // Create supporting legacy services
        legacyGlobalVoiceManager = GlobalVoiceManager(
            webSocketService: webSocketService,
            projectManager: projectManager,
            settingsManager: settingsManager
        )
        
        legacyOptimizedVoiceManager = OptimizedVoiceManager()
    }
    
    private func createLegacyVoiceManager() -> VoiceManager {
        let voiceManager = VoiceManager(
            speechService: speechService,
            webSocketService: webSocketService
        )
        
        setupLegacyServices()
        
        return voiceManager
    }
    
    private func stopLegacyServices() async {
        // Legacy services don't have async stop methods, so we just reset references
        legacyGlobalVoiceManager = nil
        legacyOptimizedVoiceManager = nil
    }
    
    private func setupMigrationLogging() {
        #if DEBUG
        appConfiguration.printConfiguration()
        print("🎤 VoiceManagerFactory: Using \(isUsingUnifiedService ? "UnifiedVoiceService" : "Legacy Services")")
        #endif
    }
}

// MARK: - Migration Status

enum MigrationStatus: String, CaseIterable {
    case notStarted = "Not Started"
    case usingLegacy = "Using Legacy"
    case migrating = "Migrating"
    case completed = "Completed"
    case fallingBack = "Falling Back"
    case error = "Error"
    
    var displayText: String {
        switch self {
        case .notStarted:
            return "Migration not started"
        case .usingLegacy:
            return "Using legacy voice services"
        case .migrating:
            return "Migrating to unified service..."
        case .completed:
            return "Using unified voice service"
        case .fallingBack:
            return "Falling back to legacy services..."
        case .error:
            return "Migration error occurred"
        }
    }
    
    var color: Color {
        switch self {
        case .notStarted:
            return .gray
        case .usingLegacy:
            return .orange
        case .migrating, .fallingBack:
            return .blue
        case .completed:
            return .green
        case .error:
            return .red
        }
    }
}

// MARK: - Factory Extensions

@available(iOS 18.0, macOS 14.0, *)
extension VoiceManagerFactory {
    
    /// Create a voice manager factory configured for testing
    static func forTesting() -> VoiceManagerFactory {
        let factory = VoiceManagerFactory()
        return factory
    }
    
    /// Check if migration is safe to perform
    var canMigrate: Bool {
        switch migrationStatus {
        case .usingLegacy, .error:
            return true
        default:
            return false
        }
    }
    
    /// Check if fallback is safe to perform
    var canFallback: Bool {
        switch migrationStatus {
        case .completed, .error:
            return true
        default:
            return false
        }
    }
}