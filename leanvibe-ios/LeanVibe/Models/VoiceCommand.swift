import Foundation

// MARK: - Voice Command Models

struct VoiceCommand: Identifiable, Codable, Sendable {
    let id = UUID()
    let originalText: String
    let processedCommand: String
    let confidence: Double
    let intent: CommandIntent
    let parameters: [String: String]
    let timestamp: Date
    let processingTime: TimeInterval
    
    init(
        originalText: String,
        processedCommand: String,
        confidence: Double = 1.0,
        intent: CommandIntent = .general,
        parameters: [String: String] = [:],
        processingTime: TimeInterval = 0.0
    ) {
        self.originalText = originalText
        self.processedCommand = processedCommand
        self.confidence = confidence
        self.intent = intent
        self.parameters = parameters
        self.timestamp = Date()
        self.processingTime = processingTime
    }
}

enum CommandIntent: String, CaseIterable, Codable, Sendable {
    case status = "status"
    case fileOperation = "file_operation"
    case navigation = "navigation"
    case agent = "agent"
    case help = "help"
    case general = "general"
    case task = "task"
    case project = "project"
    case codeCompletion = "code_completion"
    case suggest = "suggest"
    case explain = "explain"
    case refactor = "refactor"
    case debug = "debug"
    case optimize = "optimize"
    
    var displayName: String {
        switch self {
        case .status:
            return "Status Check"
        case .fileOperation:
            return "File Operation"
        case .navigation:
            return "Navigation"
        case .agent:
            return "Agent Control"
        case .help:
            return "Help Request"
        case .general:
            return "General Command"
        case .task:
            return "Task Management"
        case .project:
            return "Project Control"
        case .codeCompletion:
            return "Code Completion"
        case .suggest:
            return "Code Suggestions"
        case .explain:
            return "Code Explanation"
        case .refactor:
            return "Code Refactoring"
        case .debug:
            return "Debug Assistance"
        case .optimize:
            return "Code Optimization"
        }
    }
    
    var icon: String {
        switch self {
        case .status:
            return "checkmark.circle"
        case .fileOperation:
            return "doc.text"
        case .navigation:
            return "arrow.left.arrow.right"
        case .agent:
            return "brain.head.profile"
        case .help:
            return "questionmark.circle"
        case .general:
            return "bubble.left"
        case .task:
            return "checklist"
        case .project:
            return "folder"
        case .codeCompletion:
            return "chevron.left.forwardslash.chevron.right"
        case .suggest:
            return "lightbulb"
        case .explain:
            return "text.bubble"
        case .refactor:
            return "arrow.triangle.2.circlepath"
        case .debug:
            return "ant"
        case .optimize:
            return "speedometer"
        }
    }
}

// MARK: - Speech Recognition Results

struct SpeechRecognitionResult: Identifiable, Sendable {
    let id = UUID()
    let transcription: String
    let confidence: Double
    let isFinal: Bool
    let timestamp: Date
    let processingTime: TimeInterval
    
    init(
        transcription: String,
        confidence: Double,
        isFinal: Bool,
        processingTime: TimeInterval = 0.0
    ) {
        self.transcription = transcription
        self.confidence = confidence
        self.isFinal = isFinal
        self.timestamp = Date()
        self.processingTime = processingTime
    }
}

// MARK: - Wake Phrase Detection

struct WakePhraseDetection: Identifiable, Sendable {
    let id = UUID()
    let detectedPhrase: String
    let confidence: Double
    let timestamp: Date
    let audioLevel: Float
    
    init(detectedPhrase: String, confidence: Double, audioLevel: Float = 0.0) {
        self.detectedPhrase = detectedPhrase
        self.confidence = confidence
        self.audioLevel = audioLevel
        self.timestamp = Date()
    }
}

// MARK: - Voice Command Processor

class VoiceCommandProcessor {
    private let settings: VoiceSettings
    
    init(settings: VoiceSettings) {
        self.settings = settings
    }
    
    func processVoiceInput(_ text: String) -> VoiceCommand {
        let startTime = Date()
        let cleanedText = cleanInput(text)
        let intent = determineIntent(cleanedText)
        let processedCommand = mapToCommand(cleanedText, intent: intent)
        let parameters = extractParameters(cleanedText, intent: intent)
        let confidence = calculateConfidence(cleanedText, intent: intent)
        let processingTime = Date().timeIntervalSince(startTime)
        
        return VoiceCommand(
            originalText: text,
            processedCommand: processedCommand,
            confidence: confidence,
            intent: intent,
            parameters: parameters,
            processingTime: processingTime
        )
    }
    
    private func cleanInput(_ text: String) -> String {
        return text
            .lowercased()
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "hey leanvibe", with: "")
            .replacingOccurrences(of: "leanvibe", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    private func determineIntent(_ text: String) -> CommandIntent {
        let statusKeywords = ["status", "health", "check", "info", "state"]
        let fileKeywords = ["file", "files", "list", "show", "directory", "folder"]
        let navigationKeywords = ["go", "open", "switch", "navigate", "move"]
        let agentKeywords = ["agent", "pause", "stop", "resume", "restart"]
        let helpKeywords = ["help", "what", "how", "commands"]
        let taskKeywords = ["task", "tasks", "todo", "work", "progress"]
        let projectKeywords = ["project", "workspace", "repository", "repo"]
        
        // Code completion keywords - check these first for higher priority
        let suggestKeywords = ["suggest", "suggestion", "improve", "better", "recommendation"]
        let explainKeywords = ["explain", "what does", "how does", "meaning", "purpose"]
        let refactorKeywords = ["refactor", "refactoring", "restructure", "reorganize", "clean up"]
        let debugKeywords = ["debug", "fix", "error", "bug", "issue", "problem"]
        let optimizeKeywords = ["optimize", "performance", "faster", "improve performance", "speed up"]
        
        // Check code completion intents first
        if suggestKeywords.contains(where: text.contains) {
            return .suggest
        } else if explainKeywords.contains(where: text.contains) {
            return .explain
        } else if refactorKeywords.contains(where: text.contains) {
            return .refactor
        } else if debugKeywords.contains(where: text.contains) {
            return .debug
        } else if optimizeKeywords.contains(where: text.contains) {
            return .optimize
        } else if statusKeywords.contains(where: text.contains) {
            return .status
        } else if fileKeywords.contains(where: text.contains) {
            return .fileOperation
        } else if navigationKeywords.contains(where: text.contains) {
            return .navigation
        } else if agentKeywords.contains(where: text.contains) {
            return .agent
        } else if helpKeywords.contains(where: text.contains) {
            return .help
        } else if taskKeywords.contains(where: text.contains) {
            return .task
        } else if projectKeywords.contains(where: text.contains) {
            return .project
        } else {
            return .general
        }
    }
    
    private func mapToCommand(_ text: String, intent: CommandIntent) -> String {
        switch intent {
        case .status:
            return "/status"
        case .fileOperation:
            if text.contains("list") || text.contains("show") {
                return "/list-files"
            } else if text.contains("directory") || text.contains("current") {
                return "/current-dir"
            }
            return "/list-files"
        case .help:
            return "/help"
        case .agent:
            if text.contains("pause") || text.contains("stop") {
                return "/pause"
            } else if text.contains("resume") || text.contains("start") {
                return "/resume"
            }
            return "/status"
        case .task:
            if text.contains("show") || text.contains("list") {
                return "show me the tasks"
            } else if text.contains("create") || text.contains("new") {
                return "create a new task"
            }
            return "show me the tasks"
        case .project:
            if text.contains("switch") || text.contains("change") {
                return "switch project"
            }
            return "show project info"
        case .suggest:
            return "/code-completion/suggest"
        case .explain:
            return "/code-completion/explain"
        case .refactor:
            return "/code-completion/refactor"
        case .debug:
            return "/code-completion/debug"
        case .optimize:
            return "/code-completion/optimize"
        case .codeCompletion:
            return "/code-completion/suggest"  // Default to suggest
        case .navigation, .general:
            return text
        }
    }
    
    private func extractParameters(_ text: String, intent: CommandIntent) -> [String: String] {
        var parameters: [String: String] = [:]
        
        switch intent {
        case .fileOperation:
            // Extract file paths or names
            if let fileMatch = text.range(of: #"[a-zA-Z0-9_\-\.\/]+"#, options: .regularExpression) {
                parameters["file"] = String(text[fileMatch])
            }
        case .navigation:
            // Extract navigation targets
            if text.contains("to ") {
                let components = text.components(separatedBy: "to ")
                if components.count > 1 {
                    parameters["target"] = components[1].trimmingCharacters(in: .whitespacesAndNewlines)
                }
            }
        case .project:
            // Extract project names
            if text.contains("project ") {
                let components = text.components(separatedBy: "project ")
                if components.count > 1 {
                    parameters["project"] = components[1].trimmingCharacters(in: .whitespacesAndNewlines)
                }
            }
        default:
            break
        }
        
        return parameters
    }
    
    private func calculateConfidence(_ text: String, intent: CommandIntent) -> Double {
        var confidence = 0.5 // Base confidence
        
        // Increase confidence based on keyword matches
        let intentKeywords = getKeywordsForIntent(intent)
        let matchingKeywords = intentKeywords.filter { text.contains($0) }
        
        confidence += Double(matchingKeywords.count) * 0.1
        
        // Increase confidence for exact command matches
        if isExactCommandMatch(text) {
            confidence += 0.3
        }
        
        // Cap at 1.0
        return min(confidence, 1.0)
    }
    
    private func getKeywordsForIntent(_ intent: CommandIntent) -> [String] {
        switch intent {
        case .status:
            return ["status", "health", "check", "info"]
        case .fileOperation:
            return ["file", "files", "list", "directory"]
        case .navigation:
            return ["go", "open", "switch", "navigate"]
        case .agent:
            return ["agent", "pause", "stop", "resume"]
        case .help:
            return ["help", "what", "how", "commands"]
        case .task:
            return ["task", "tasks", "todo", "work"]
        case .project:
            return ["project", "workspace", "repository"]
        case .suggest:
            return ["suggest", "suggestion", "improve", "better"]
        case .explain:
            return ["explain", "what does", "how does", "meaning"]
        case .refactor:
            return ["refactor", "refactoring", "restructure", "reorganize"]
        case .debug:
            return ["debug", "fix", "error", "bug", "issue"]
        case .optimize:
            return ["optimize", "performance", "faster", "speed up"]
        case .codeCompletion:
            return ["code", "completion", "suggest", "help"]
        case .general:
            return []
        }
    }
    
    private func isExactCommandMatch(_ text: String) -> Bool {
        let exactCommands = [
            "status", "help", "list files", "current directory",
            "show status", "show help", "show files"
        ]
        return exactCommands.contains(text)
    }
}

// MARK: - Voice Command Extensions

extension VoiceCommand {
    var isHighConfidence: Bool {
        return confidence >= 0.8
    }
    
    var requiresConfirmation: Bool {
        return confidence < 0.7 || intent == .agent
    }
    
    var formattedProcessingTime: String {
        return String(format: "%.2f ms", processingTime * 1000)
    }
}

// MARK: - WebSocket Voice Integration

struct VoiceCommandMessage: Codable, Sendable {
    let type: String = "voice_command"
    let command: String
    let originalText: String
    let confidence: Double
    let intent: String
    let parameters: [String: String]
    let clientId: String
    let timestamp: String
    
    init(voiceCommand: VoiceCommand, clientId: String) {
        self.command = voiceCommand.processedCommand
        self.originalText = voiceCommand.originalText
        self.confidence = voiceCommand.confidence
        self.intent = voiceCommand.intent.rawValue
        self.parameters = voiceCommand.parameters
        self.clientId = clientId
        self.timestamp = ISO8601DateFormatter().string(from: voiceCommand.timestamp)
    }
}