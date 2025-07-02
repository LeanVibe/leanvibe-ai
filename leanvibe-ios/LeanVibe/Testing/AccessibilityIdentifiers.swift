import Foundation

/// Centralized accessibility identifiers for UI testing
/// Provides consistent naming and easy maintenance of test selectors
@available(iOS 18.0, *)
enum AccessibilityIdentifiers {
    
    // MARK: - Main Navigation
    enum MainNavigation {
        static let tabView = "mainTabView"
        static let projectsTab = "projectsTab"
        static let dashboardTab = "dashboardTab"
        static let architectureTab = "architectureTab"
        static let settingsTab = "settingsTab"
        static let voiceTab = "voiceTab"
    }
    
    // MARK: - Dashboard
    enum Dashboard {
        static let container = "dashboardContainer"
        static let connectionStatus = "connectionStatus"
        static let connectionIndicator = "connectionIndicator"
        static let voiceButton = "voiceButton"
        static let voiceIndicator = "voiceIndicator"
        static let messagesList = "messagesList"
        static let messageInput = "messageInput"
        static let sendButton = "sendButton"
        static let clearButton = "clearButton"
    }
    
    // MARK: - Voice Interface
    enum Voice {
        static let container = "voiceContainer"
        static let permissionView = "voicePermissionView"
        static let permissionButton = "voicePermissionButton"
        static let microphoneButton = "microphoneButton"
        static let listeningIndicator = "listeningIndicator"
        static let transcriptionText = "transcriptionText"
        static let confidenceIndicator = "confidenceIndicator"
        static let wakePhraseButton = "wakePhraseButton"
        static let voiceCommandsList = "voiceCommandsList"
        static let voiceSettings = "voiceSettings"
    }
    
    // MARK: - Projects
    enum Projects {
        static let container = "projectsContainer"
        static let projectsList = "projectsList"
        static let addProjectButton = "addProjectButton"
        static let projectCell = "projectCell"
        static let projectTitle = "projectTitle"
        static let projectStatus = "projectStatus"
        static let projectActions = "projectActions"
        static let deleteProject = "deleteProject"
        static let editProject = "editProject"
        static let projectDetail = "projectDetail"
    }
    
    // MARK: - Kanban Board
    enum Kanban {
        static let container = "kanbanContainer"
        static let board = "kanbanBoard"
        static let todoColumn = "todoColumn"
        static let inProgressColumn = "inProgressColumn"
        static let doneColumn = "doneColumn"
        static let taskCard = "taskCard"
        static let taskTitle = "taskTitle"
        static let taskDescription = "taskDescription"
        static let taskPriority = "taskPriority"
        static let taskDueDate = "taskDueDate"
        static let addTaskButton = "addTaskButton"
        static let taskDetailView = "taskDetailView"
        static let editTaskButton = "editTaskButton"
        static let deleteTaskButton = "deleteTaskButton"
    }
    
    // MARK: - Architecture Viewer
    enum Architecture {
        static let container = "architectureContainer"
        static let webView = "architectureWebView"
        static let loadingIndicator = "architectureLoadingIndicator"
        static let refreshButton = "architectureRefreshButton"
        static let zoomControls = "architectureZoomControls"
        static let exportButton = "architectureExportButton"
        static let diagramSelector = "diagramSelector"
    }
    
    // MARK: - Settings
    enum Settings {
        static let container = "settingsContainer"
        static let serverSection = "serverSettingsSection"
        static let serverHostField = "serverHostField"
        static let serverPortField = "serverPortField"
        static let connectionTestButton = "connectionTestButton"
        static let voiceSection = "voiceSettingsSection"
        static let voiceEnabledToggle = "voiceEnabledToggle"
        static let confidenceSlider = "confidenceSlider"
        static let notificationSection = "notificationSettingsSection"
        static let notificationToggle = "notificationToggle"
        static let accessibilitySection = "accessibilitySettingsSection"
        static let saveButton = "saveSettingsButton"
        static let resetButton = "resetSettingsButton"
    }
    
    // MARK: - Onboarding
    enum Onboarding {
        static let container = "onboardingContainer"
        static let welcomeView = "welcomeView"
        static let featuresView = "featuresView"
        static let permissionsView = "permissionsView"
        static let setupView = "setupView"
        static let nextButton = "nextButton"
        static let skipButton = "skipButton"
        static let getStartedButton = "getStartedButton"
        static let tutorialButton = "tutorialButton"
    }
    
    // MARK: - QR Scanner
    enum QRScanner {
        static let container = "qrScannerContainer"
        static let cameraView = "qrCameraView"
        static let scanIndicator = "qrScanIndicator"
        static let manualEntryButton = "manualEntryButton"
        static let torchButton = "torchButton"
        static let closeButton = "qrCloseButton"
        static let instructionsText = "qrInstructionsText"
    }
    
    // MARK: - Error Handling
    enum Error {
        static let container = "errorContainer"
        static let errorView = "errorView"
        static let errorMessage = "errorMessage"
        static let errorTitle = "errorTitle"
        static let retryButton = "retryButton"
        static let dismissButton = "dismissErrorButton"
        static let reportButton = "reportErrorButton"
    }
    
    // MARK: - Alerts and Modals
    enum Alerts {
        static let confirmAlert = "confirmAlert"
        static let warningAlert = "warningAlert"
        static let successAlert = "successAlert"
        static let confirmButton = "confirmButton"
        static let cancelButton = "cancelButton"
        static let okButton = "okButton"
    }
    
    // MARK: - Performance
    enum Performance {
        static let container = "performanceContainer"
        static let metricsView = "performanceMetricsView"
        static let cpuIndicator = "cpuIndicator"
        static let memoryIndicator = "memoryIndicator"
        static let batteryIndicator = "batteryIndicator"
        static let networkIndicator = "networkIndicator"
        static let optimizeButton = "optimizeButton"
    }
    
    // MARK: - Helper Functions
    
    /// Generate dynamic identifier for list items
    static func listItem(_ type: String, index: Int) -> String {
        return "\(type)ListItem_\(index)"
    }
    
    /// Generate dynamic identifier with custom suffix
    static func dynamic(_ base: String, suffix: String) -> String {
        return "\(base)_\(suffix)"
    }
    
    /// Generate identifier for task in specific column
    static func taskInColumn(_ column: String, taskId: String) -> String {
        return "task_\(column)_\(taskId)"
    }
    
    /// Generate identifier for project-specific elements
    static func projectElement(_ element: String, projectId: String) -> String {
        return "project_\(projectId)_\(element)"
    }
}