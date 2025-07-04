import Foundation

/// Service for transforming project documentation into Kanban tasks
/// Bridges document parsing with task management for automatic Backlog population
@available(iOS 18.0, macOS 14.0, *)
@MainActor
class DocumentIntelligenceService: ObservableObject {
    
    // MARK: - Properties
    
    @Published var isProcessing = false
    @Published var lastProcessedDate: Date?
    @Published var processingStatus = "Idle"
    @Published var discoveredTasks: [DocumentTask] = []
    
    private let taskService: TaskService
    private let backendService = BackendSettingsService.shared
    private let config = AppConfiguration.shared
    
    // MARK: - Initialization
    
    init(taskService: TaskService) {
        self.taskService = taskService
    }
    
    // MARK: - Public Methods
    
    /// Process project documents and create Kanban tasks automatically
    func processProjectDocuments(for project: Project) async throws {
        isProcessing = true
        processingStatus = "Analyzing project documents..."
        defer { 
            isProcessing = false
            processingStatus = "Idle"
        }
        
        // Clear previous discoveries
        discoveredTasks.removeAll()
        
        // Parse documents using existing ProjectManager logic
        let documentData = await parseProjectDocumentation(projectPath: project.path)
        
        // Transform parsed content into tasks
        let tasks = await transformDocumentDataToTasks(
            documentData: documentData,
            projectId: project.id
        )
        
        // Store discovered tasks
        discoveredTasks = tasks
        
        // Optionally auto-create tasks in backend
        if backendService.isAvailable {
            try await createTasksInBackend(tasks)
        }
        
        lastProcessedDate = Date()
        processingStatus = "Completed"
    }
    
    /// Get tasks suitable for Backlog column population
    func getBacklogTasks() -> [DocumentTask] {
        return discoveredTasks.filter { task in
            task.suggestedStatus == .backlog || 
            task.documentSource.contains("PLAN") ||
            task.documentSource.contains("MVP") ||
            task.documentSource.contains("PRD")
        }
    }
    
    /// Get tasks from specific document types
    func getTasks(from documentType: DocumentType) -> [DocumentTask] {
        return discoveredTasks.filter { $0.sourceType == documentType }
    }
    
    // MARK: - Private Methods
    
    private func parseProjectDocumentation(projectPath: String) async -> DocumentData {
        let projectURL = URL(fileURLWithPath: projectPath)
        var documentData = DocumentData()
        
        let documentFiles = [
            ("PLAN.md", DocumentType.plan),
            ("README.md", DocumentType.readme),
            ("PRD.md", DocumentType.prd),
            ("MVP.md", DocumentType.mvp),
            ("ROADMAP.md", DocumentType.roadmap),
            ("claude.md", DocumentType.agent),
            ("CLAUDE.md", DocumentType.agent),
            ("agent.md", DocumentType.agent)
        ]
        
        for (fileName, docType) in documentFiles {
            let fileURL = projectURL.appendingPathComponent(fileName)
            
            if FileManager.default.fileExists(atPath: fileURL.path) {
                do {
                    let content = try String(contentsOf: fileURL, encoding: .utf8)
                    let parsedItems = parseDocumentContent(content: content, documentType: docType, fileName: fileName)
                    documentData.addItems(parsedItems, for: docType)
                } catch {
                    print("Error reading \(fileName): \(error)")
                }
            }
        }
        
        return documentData
    }
    
    private func parseDocumentContent(content: String, documentType: DocumentType, fileName: String) -> [DocumentItem] {
        var items: [DocumentItem] = []
        let lines = content.components(separatedBy: .newlines)
        var currentSection = ""
        
        for (index, line) in lines.enumerated() {
            let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
            
            // Track current section
            if trimmedLine.hasPrefix("#") {
                currentSection = extractSectionTitle(from: trimmedLine)
                continue
            }
            
            // Parse different types of task indicators
            if let item = parseLineAsTask(
                line: trimmedLine,
                lineNumber: index + 1,
                section: currentSection,
                documentType: documentType,
                fileName: fileName
            ) {
                items.append(item)
            }
        }
        
        return items
    }
    
    private func parseLineAsTask(
        line: String,
        lineNumber: Int,
        section: String,
        documentType: DocumentType,
        fileName: String
    ) -> DocumentItem? {
        
        // Skip empty lines and pure markdown
        guard !line.isEmpty && !line.hasPrefix("#") else { return nil }
        
        var taskText = line
        var status = TaskStatus.backlog
        var priority = TaskPriority.medium
        var confidence: Double = 0.7
        
        // Parse status indicators
        if line.hasPrefix("✅") || line.contains("COMPLETED") || line.contains("DONE") {
            status = .done
            taskText = cleanTaskText(line.replacingOccurrences(of: "✅", with: ""))
        } else if line.hasPrefix("🚧") || line.contains("IN PROGRESS") || line.contains("WIP") {
            status = .inProgress
            taskText = cleanTaskText(line.replacingOccurrences(of: "🚧", with: ""))
        } else if line.hasPrefix("⚠️") || line.contains("TESTING") || line.contains("QA") {
            status = .testing
            taskText = cleanTaskText(line.replacingOccurrences(of: "⚠️", with: ""))
        } else if line.hasPrefix("- ") || line.hasPrefix("* ") || line.hasPrefix("+ ") {
            // Regular bullet points go to backlog
            status = .backlog
            taskText = cleanTaskText(String(line.dropFirst(2)))
        } else if line.contains("TODO") || line.contains("FIXME") {
            status = .todo
            taskText = cleanTaskText(line.replacingOccurrences(of: "TODO:", with: "").replacingOccurrences(of: "FIXME:", with: ""))
        }
        
        // Parse priority indicators
        if line.localizedCaseInsensitiveContains("urgent") || line.localizedCaseInsensitiveContains("critical") || line.contains("🔥") {
            priority = .urgent
            confidence = 0.9
        } else if line.localizedCaseInsensitiveContains("high") || line.localizedCaseInsensitiveContains("important") {
            priority = .high
            confidence = 0.8
        } else if line.localizedCaseInsensitiveContains("low") || line.localizedCaseInsensitiveContains("minor") {
            priority = .low
            confidence = 0.6
        }
        
        // Document-specific priority boosts
        switch documentType {
        case .mvp:
            priority = enhancePriority(priority) // MVP items get priority boost
            confidence += 0.1
        case .prd:
            if section.localizedCaseInsensitiveContains("requirement") {
                priority = enhancePriority(priority)
                confidence += 0.15
            }
        case .plan:
            if section.localizedCaseInsensitiveContains("phase") || section.localizedCaseInsensitiveContains("milestone") {
                confidence += 0.1
            }
        default:
            break
        }
        
        // Ensure task text is meaningful
        guard taskText.count > 5 && !taskText.localizedCaseInsensitiveContains("example") else {
            return nil
        }
        
        return DocumentItem(
            text: taskText,
            originalLine: line,
            lineNumber: lineNumber,
            section: section,
            suggestedStatus: status,
            suggestedPriority: priority,
            confidence: min(confidence, 1.0),
            documentType: documentType,
            fileName: fileName
        )
    }
    
    private func cleanTaskText(_ text: String) -> String {
        return text
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "**", with: "")
            .replacingOccurrences(of: "*", with: "")
            .replacingOccurrences(of: "- [ ]", with: "")
            .replacingOccurrences(of: "- [x]", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    private func extractSectionTitle(from line: String) -> String {
        return line
            .replacingOccurrences(of: "#", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    private func enhancePriority(_ priority: TaskPriority) -> TaskPriority {
        switch priority {
        case .low: return .medium
        case .medium: return .high
        case .high: return .urgent
        case .urgent: return .urgent
        }
    }
    
    private func transformDocumentDataToTasks(documentData: DocumentData, projectId: UUID) async -> [DocumentTask] {
        var tasks: [DocumentTask] = []
        
        for (documentType, items) in documentData.itemsByType {
            for item in items {
                let task = DocumentTask(
                    id: UUID(),
                    title: item.text,
                    description: generateTaskDescription(from: item),
                    suggestedStatus: item.suggestedStatus,
                    suggestedPriority: item.suggestedPriority,
                    projectId: projectId,
                    confidence: item.confidence,
                    sourceType: documentType,
                    documentSource: item.fileName,
                    originalLine: item.originalLine,
                    lineNumber: item.lineNumber,
                    section: item.section,
                    tags: generateTags(from: item)
                )
                tasks.append(task)
            }
        }
        
        return tasks.sorted { $0.confidence > $1.confidence }
    }
    
    private func generateTaskDescription(from item: DocumentItem) -> String {
        var description = "Automatically extracted from \(item.fileName)"
        
        if !item.section.isEmpty {
            description += " (Section: \(item.section))"
        }
        
        description += "\n\nOriginal text: \(item.originalLine)"
        description += "\nConfidence: \(Int(item.confidence * 100))%"
        
        return description
    }
    
    private func generateTags(from item: DocumentItem) -> [String] {
        var tags = ["auto-generated", item.documentType.rawValue]
        
        if !item.section.isEmpty {
            tags.append(item.section.lowercased().replacingOccurrences(of: " ", with: "-"))
        }
        
        // Add priority-based tags
        switch item.suggestedPriority {
        case .urgent: tags.append("urgent")
        case .high: tags.append("high-priority")
        default: break
        }
        
        return tags
    }
    
    private func createTasksInBackend(_ tasks: [DocumentTask]) async throws {
        guard config.isBackendConfigured else { return }
        
        processingStatus = "Creating tasks in backend..."
        
        for task in tasks {
            let leanVibeTask = LeanVibeTask(
                id: task.id,
                title: task.title,
                description: task.description,
                status: task.suggestedStatus,
                priority: task.suggestedPriority,
                projectId: task.projectId,
                createdAt: Date(),
                updatedAt: Date(),
                confidence: task.confidence,
                agentDecision: nil,
                clientId: "document-intelligence",
                assignedTo: nil,
                estimatedEffort: nil,
                actualEffort: nil,
                tags: task.tags,
                dependencies: [],
                attachments: []
            )
            
            try await taskService.createTask(leanVibeTask)
        }
    }
}

// MARK: - Supporting Models

struct DocumentData {
    var itemsByType: [DocumentType: [DocumentItem]] = [:]
    
    mutating func addItems(_ items: [DocumentItem], for type: DocumentType) {
        itemsByType[type, default: []].append(contentsOf: items)
    }
}

struct DocumentItem {
    let text: String
    let originalLine: String
    let lineNumber: Int
    let section: String
    let suggestedStatus: TaskStatus
    let suggestedPriority: TaskPriority
    let confidence: Double
    let documentType: DocumentType
    let fileName: String
}

struct DocumentTask: Identifiable {
    let id: UUID
    let title: String
    let description: String
    let suggestedStatus: TaskStatus
    let suggestedPriority: TaskPriority
    let projectId: UUID
    let confidence: Double
    let sourceType: DocumentType
    let documentSource: String
    let originalLine: String
    let lineNumber: Int
    let section: String
    let tags: [String]
}

enum DocumentType: String, CaseIterable {
    case plan = "plan"
    case readme = "readme"
    case prd = "prd"
    case mvp = "mvp"
    case roadmap = "roadmap"
    case agent = "agent"
    
    var displayName: String {
        switch self {
        case .plan: return "Project Plan"
        case .readme: return "README"
        case .prd: return "Product Requirements"
        case .mvp: return "MVP Specifications"
        case .roadmap: return "Roadmap"
        case .agent: return "Agent Configuration"
        }
    }
    
    var backlogPriority: Int {
        switch self {
        case .mvp: return 1      // Highest priority for Backlog
        case .prd: return 2      // Product requirements
        case .plan: return 3     // Project plans
        case .roadmap: return 4  // Future items
        case .readme: return 5   // General tasks
        case .agent: return 6    // Agent config items
        }
    }
}