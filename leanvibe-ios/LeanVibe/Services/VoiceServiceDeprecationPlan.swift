import Foundation

/// Deprecation plan for legacy voice services
/// This file documents the migration strategy and provides deprecation markers
@available(iOS 18.0, macOS 14.0, *)
enum VoiceServiceDeprecationPlan {
    
    // MARK: - Deprecation Strategy
    
    /// Phase 1: Add deprecation warnings to legacy services
    /// Timeline: Immediate
    static let phase1Tasks = [
        "Add @available(*, deprecated) to VoiceManager",
        "Add @available(*, deprecated) to GlobalVoiceManager", 
        "Add @available(*, deprecated) to OptimizedVoiceManager",
        "Update documentation to recommend VoiceManagerFactory"
    ]
    
    /// Phase 2: Update view instantiations to use VoiceManagerFactory
    /// Timeline: Next release cycle
    static let phase2Tasks = [
        "Replace VoiceManager instantiation in DashboardTabView",
        "Replace GlobalVoiceManager instantiation in GlobalVoiceCommandView",
        "Replace OptimizedVoiceManager instantiation in RealTimePerformanceDashboard",
        "Update CodeCompletionTestView to use VoiceManagerFactory"
    ]
    
    /// Phase 3: Remove legacy service references
    /// Timeline: After 2 release cycles with unified service
    static let phase3Tasks = [
        "Remove VoiceManager.swift file",
        "Remove GlobalVoiceManager.swift file",
        "Remove OptimizedVoiceManager.swift file",
        "Clean up any remaining legacy imports"
    ]
    
    // MARK: - Migration Assistance
    
    /// Provides migration guidance for legacy service users
    static func migrationGuidance(for legacyService: String) -> String {
        switch legacyService {
        case "VoiceManager":
            return """
            VoiceManager is deprecated. Use VoiceManagerFactory instead:
            
            // OLD:
            let voiceManager = VoiceManager(speechService: service, webSocketService: ws)
            
            // NEW:
            let voiceFactory = VoiceManagerFactory()
            if voiceFactory.isUsingUnifiedService {
                let unifiedService = voiceFactory.unifiedVoiceService
            } else {
                let legacyManager = voiceFactory.legacyVoiceManager
            }
            """
            
        case "GlobalVoiceManager":
            return """
            GlobalVoiceManager is deprecated. Use VoiceManagerFactory instead:
            
            // OLD:
            let globalVoice = GlobalVoiceManager(webSocketService: ws, projectManager: pm, settingsManager: sm)
            
            // NEW:
            let voiceFactory = VoiceManagerFactory()
            if voiceFactory.isUsingUnifiedService {
                // UnifiedVoiceService includes all global voice functionality
                let unifiedService = voiceFactory.unifiedVoiceService
            } else {
                let globalVoice = voiceFactory.globalVoiceManager
            }
            """
            
        case "OptimizedVoiceManager":
            return """
            OptimizedVoiceManager is deprecated. Use VoiceManagerFactory instead:
            
            // OLD:
            let optimizedVoice = OptimizedVoiceManager()
            
            // NEW:
            let voiceFactory = VoiceManagerFactory()
            if voiceFactory.isUsingUnifiedService {
                // UnifiedVoiceService includes optimizations by default
                let unifiedService = voiceFactory.unifiedVoiceService
            } else {
                let optimizedVoice = voiceFactory.optimizedVoiceManager
            }
            """
            
        default:
            return "Unknown legacy service. Please consult VoiceManagerFactory documentation."
        }
    }
    
    // MARK: - Breaking Change Assessment
    
    /// Assesses the breaking change impact of removing legacy services
    static func assessBreakingChanges() -> BreakingChangeReport {
        return BreakingChangeReport(
            affectedFiles: [
                "DashboardTabView.swift",
                "GlobalVoiceCommandView.swift", 
                "RealTimePerformanceDashboard.swift",
                "CodeCompletionTestView.swift"
            ],
            migrationComplexity: .medium,
            estimatedMigrationTime: "2-4 hours",
            riskLevel: .low,
            mitigationStrategy: """
            1. Use VoiceManagerFactory in all affected files
            2. Test both unified and legacy modes during transition
            3. Deploy with feature flag to enable gradual rollout
            4. Monitor error rates during migration period
            """
        )
    }
}

// MARK: - Supporting Types

@available(iOS 18.0, macOS 14.0, *)
struct BreakingChangeReport {
    let affectedFiles: [String]
    let migrationComplexity: MigrationComplexity
    let estimatedMigrationTime: String
    let riskLevel: RiskLevel
    let mitigationStrategy: String
}

@available(iOS 18.0, macOS 14.0, *)
enum MigrationComplexity {
    case low, medium, high
    
    var description: String {
        switch self {
        case .low: return "Simple find-and-replace"
        case .medium: return "Moderate refactoring required" 
        case .high: return "Significant architectural changes"
        }
    }
}

@available(iOS 18.0, macOS 14.0, *)
enum RiskLevel {
    case low, medium, high
    
    var description: String {
        switch self {
        case .low: return "Low risk - easy to rollback"
        case .medium: return "Medium risk - requires testing"
        case .high: return "High risk - extensive validation needed"
        }
    }
}