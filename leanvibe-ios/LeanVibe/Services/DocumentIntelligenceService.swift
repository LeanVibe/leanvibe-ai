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
    
    /// Auto-populate Backlog from Plan.md when project is selected
    func autoPopulateBacklogFromPlan(for project: Project) async throws {
        isProcessing = true
        processingStatus = "Auto-populating Backlog from Plan.md..."
        defer { 
            isProcessing = false
            processingStatus = "Idle"
        }
        
        // Focus specifically on Plan.md for Backlog population
        let planFilePath = "\(project.path)/PLAN.md"
        
        guard FileManager.default.fileExists(atPath: planFilePath) else {
            print("📄 No PLAN.md found for project: \(project.displayName)")
            return
        }
        
        do {
            let planContent = try String(contentsOfFile: planFilePath, encoding: .utf8)
            let backlogTasks = await extractBacklogTasksFromPlan(content: planContent, projectId: project.id)
            
            if !backlogTasks.isEmpty {
                // Auto-create high-confidence Backlog tasks
                let autoCreateTasks = backlogTasks.filter { $0.confidence >= 0.8 && $0.suggestedStatus == .backlog }
                
                if !autoCreateTasks.isEmpty {
                    try await createTasksInBackend(autoCreateTasks)
                    print("✅ Auto-created \(autoCreateTasks.count) Backlog tasks from Plan.md")
                }
                
                // Store all discovered tasks for manual review
                discoveredTasks = backlogTasks
                lastProcessedDate = Date()
            }
        } catch {
            print("❌ Failed to process Plan.md: \(error)")
            throw error
        }
    }
    
    /// Auto-populate Backlog from PRD/MVP specs in docs folder
    func autoPopulateBacklogFromSpecs(for project: Project) async throws {
        isProcessing = true
        processingStatus = "Auto-populating Backlog from PRD/MVP specs..."
        defer { 
            isProcessing = false
            processingStatus = "Idle"
        }
        
        var allBacklogTasks: [DocumentTask] = []
        
        // Process PRD.md
        let prdFilePath = "\(project.path)/PRD.md"
        if FileManager.default.fileExists(atPath: prdFilePath) {
            do {
                let prdContent = try String(contentsOfFile: prdFilePath, encoding: .utf8)
                let prdTasks = await extractBacklogTasksFromPRD(content: prdContent, projectId: project.id)
                allBacklogTasks.append(contentsOf: prdTasks)
                print("📋 Extracted \(prdTasks.count) tasks from PRD.md")
            } catch {
                print("❌ Failed to process PRD.md: \(error)")
            }
        }
        
        // Process MVP.md
        let mvpFilePath = "\(project.path)/MVP.md"
        if FileManager.default.fileExists(atPath: mvpFilePath) {
            do {
                let mvpContent = try String(contentsOfFile: mvpFilePath, encoding: .utf8)
                let mvpTasks = await extractBacklogTasksFromMVP(content: mvpContent, projectId: project.id)
                allBacklogTasks.append(contentsOf: mvpTasks)
                print("🎯 Extracted \(mvpTasks.count) tasks from MVP.md")
            } catch {
                print("❌ Failed to process MVP.md: \(error)")
            }
        }
        
        // Process docs folder if it exists
        let docsPath = "\(project.path)/docs"
        if FileManager.default.fileExists(atPath: docsPath) {
            let docsTasks = await extractBacklogTasksFromDocsFolder(docsPath: docsPath, projectId: project.id)
            allBacklogTasks.append(contentsOf: docsTasks)
            print("📁 Extracted \(docsTasks.count) tasks from docs folder")
        }
        
        if !allBacklogTasks.isEmpty {
            // Auto-create high-confidence Backlog tasks
            let autoCreateTasks = allBacklogTasks.filter { $0.confidence >= 0.8 && $0.suggestedStatus == .backlog }
            
            if !autoCreateTasks.isEmpty {
                try await createTasksInBackend(autoCreateTasks)
                print("✅ Auto-created \(autoCreateTasks.count) Backlog tasks from PRD/MVP specs")
            }
            
            // Merge with existing discovered tasks
            let existingTasks = discoveredTasks
            let allTasks = existingTasks + allBacklogTasks
            discoveredTasks = Array(Set(allTasks)) // Remove duplicates
            lastProcessedDate = Date()
        }
    }
    
    /// Comprehensive Backlog population from all specification documents
    func autoPopulateCompleteBacklog(for project: Project) async throws {
        isProcessing = true
        processingStatus = "Comprehensive Backlog population from all specs..."
        defer { 
            isProcessing = false
            processingStatus = "Idle"
        }
        
        // Clear previous discoveries for fresh comprehensive analysis
        discoveredTasks.removeAll()
        
        // Process Plan.md first (highest priority)
        try await autoPopulateBacklogFromPlan(for: project)
        
        // Then process PRD/MVP specs
        try await autoPopulateBacklogFromSpecs(for: project)
        
        print("🎉 Comprehensive Backlog population completed")
    }
    
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
    
    /// Extract Backlog tasks specifically from PRD content with requirements focus
    private func extractBacklogTasksFromPRD(content: String, projectId: UUID) async -> [DocumentTask] {
        let lines = content.components(separatedBy: .newlines)
        var backlogTasks: [DocumentTask] = []
        var currentSection = ""
        
        for (index, line) in lines.enumerated() {
            let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
            
            // Track current section for context
            if trimmedLine.hasPrefix("#") {
                currentSection = extractSectionTitle(from: trimmedLine)
                continue
            }
            
            // Focus on requirements, features, and specifications
            if let backlogTask = parseLineAsPRDTask(
                line: trimmedLine,
                lineNumber: index + 1,
                section: currentSection,
                projectId: projectId
            ) {
                backlogTasks.append(backlogTask)
            }
        }
        
        return backlogTasks.sorted { $0.confidence > $1.confidence }
    }
    
    /// Extract Backlog tasks specifically from MVP content with feature focus
    private func extractBacklogTasksFromMVP(content: String, projectId: UUID) async -> [DocumentTask] {
        let lines = content.components(separatedBy: .newlines)
        var backlogTasks: [DocumentTask] = []
        var currentSection = ""
        
        for (index, line) in lines.enumerated() {
            let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
            
            // Track current section for context
            if trimmedLine.hasPrefix("#") {
                currentSection = extractSectionTitle(from: trimmedLine)
                continue
            }
            
            // Focus on MVP features and core functionality
            if let backlogTask = parseLineAsMVPTask(
                line: trimmedLine,
                lineNumber: index + 1,
                section: currentSection,
                projectId: projectId
            ) {
                backlogTasks.append(backlogTask)
            }
        }
        
        return backlogTasks.sorted { $0.confidence > $1.confidence }
    }
    
    /// Extract tasks from docs folder files
    private func extractBacklogTasksFromDocsFolder(docsPath: String, projectId: UUID) async -> [DocumentTask] {
        var allTasks: [DocumentTask] = []
        
        do {
            let fileManager = FileManager.default
            let docFiles = try fileManager.contentsOfDirectory(atPath: docsPath)
            
            for fileName in docFiles {
                // Process relevant documentation files
                if fileName.hasSuffix(".md") && 
                   (fileName.localizedCaseInsensitiveContains("spec") ||
                    fileName.localizedCaseInsensitiveContains("requirement") ||
                    fileName.localizedCaseInsensitiveContains("feature") ||
                    fileName.localizedCaseInsensitiveContains("backlog")) {
                    
                    let filePath = "\(docsPath)/\(fileName)"
                    
                    do {
                        let content = try String(contentsOfFile: filePath, encoding: .utf8)
                        let docTasks = await extractBacklogTasksFromSpecDocument(
                            content: content,
                            fileName: fileName,
                            projectId: projectId
                        )
                        allTasks.append(contentsOf: docTasks)
                    } catch {
                        print("❌ Failed to process \(fileName): \(error)")
                    }
                }
            }
        } catch {
            print("❌ Failed to read docs folder: \(error)")
        }
        
        return allTasks
    }
    
    /// Parse line as PRD requirement task
    private func parseLineAsPRDTask(line: String, lineNumber: Int, section: String, projectId: UUID) -> DocumentTask? {
        guard !line.isEmpty && !line.hasPrefix("#") else { return nil }
        
        var taskText = line
        var priority = TaskPriority.high // PRD items get higher default priority
        var confidence: Double = 0.8 // PRD items get higher confidence
        
        // Skip completed items
        if line.contains("✅") || line.localizedCaseInsensitiveContains("implemented") {
            return nil
        }
        
        // PRD-specific indicators
        let prdIndicators = [
            "requirement", "must", "shall", "should", "feature", "capability",
            "functionality", "specification", "criteria", "acceptance", "user story"
        ]
        
        let containsPRDIndicator = prdIndicators.contains { indicator in
            line.localizedCaseInsensitiveContains(indicator)
        }
        
        if containsPRDIndicator {
            confidence += 0.15
        }
        
        // Priority assessment for requirements
        if line.localizedCaseInsensitiveContains("critical") || line.localizedCaseInsensitiveContains("mandatory") {
            priority = .urgent
            confidence += 0.2
        } else if line.localizedCaseInsensitiveContains("core") || line.localizedCaseInsensitiveContains("essential") {
            priority = .high
            confidence += 0.1
        }
        
        // Clean up task text
        if line.hasPrefix("- ") || line.hasPrefix("* ") {
            taskText = String(line.dropFirst(2)).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        
        // Section-based priority
        if section.localizedCaseInsensitiveContains("functional") || 
           section.localizedCaseInsensitiveContains("core") {
            priority = enhancePriority(priority)
            confidence += 0.1
        }
        
        guard taskText.count > 8 else { return nil }
        
        let description = generatePRDTaskDescription(originalText: line, section: section, confidence: confidence)
        
        return DocumentTask(
            id: UUID(),
            title: taskText,
            description: description,
            suggestedStatus: .backlog,
            suggestedPriority: priority,
            projectId: projectId,
            confidence: min(confidence, 1.0),
            sourceType: .prd,
            documentSource: "PRD.md",
            originalLine: line,
            lineNumber: lineNumber,
            section: section,
            tags: generatePRDTags(from: taskText, section: section)
        )
    }
    
    /// Parse line as MVP feature task
    private func parseLineAsMVPTask(line: String, lineNumber: Int, section: String, projectId: UUID) -> DocumentTask? {
        guard !line.isEmpty && !line.hasPrefix("#") else { return nil }
        
        var taskText = line
        var priority = TaskPriority.high // MVP items get high priority by default
        var confidence: Double = 0.85 // MVP items get higher confidence
        
        // Skip completed items
        if line.contains("✅") || line.localizedCaseInsensitiveContains("completed") {
            return nil
        }
        
        // MVP-specific indicators
        let mvpIndicators = [
            "mvp", "minimum", "viable", "core feature", "essential", "basic",
            "launch", "v1", "version 1", "initial", "foundation"
        ]
        
        let containsMVPIndicator = mvpIndicators.contains { indicator in
            line.localizedCaseInsensitiveContains(indicator)
        }
        
        if containsMVPIndicator {
            confidence += 0.1
            priority = .urgent // MVP features are urgent
        }
        
        // Clean up task text
        if line.hasPrefix("- ") || line.hasPrefix("* ") {
            taskText = String(line.dropFirst(2)).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        
        // Section-based priority for MVP
        if section.localizedCaseInsensitiveContains("core") || 
           section.localizedCaseInsensitiveContains("essential") ||
           section.localizedCaseInsensitiveContains("critical") {
            priority = .urgent
            confidence += 0.1
        }
        
        guard taskText.count > 8 else { return nil }
        
        let description = generateMVPTaskDescription(originalText: line, section: section, confidence: confidence)
        
        return DocumentTask(
            id: UUID(),
            title: taskText,
            description: description,
            suggestedStatus: .backlog,
            suggestedPriority: priority,
            projectId: projectId,
            confidence: min(confidence, 1.0),
            sourceType: .mvp,
            documentSource: "MVP.md",
            originalLine: line,
            lineNumber: lineNumber,
            section: section,
            tags: generateMVPTags(from: taskText, section: section)
        )
    }
    
    /// Extract tasks from generic specification documents
    private func extractBacklogTasksFromSpecDocument(content: String, fileName: String, projectId: UUID) async -> [DocumentTask] {
        let lines = content.components(separatedBy: .newlines)
        var backlogTasks: [DocumentTask] = []
        var currentSection = ""
        
        for (index, line) in lines.enumerated() {
            let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
            
            if trimmedLine.hasPrefix("#") {
                currentSection = extractSectionTitle(from: trimmedLine)
                continue
            }
            
            if let backlogTask = parseLineAsSpecTask(
                line: trimmedLine,
                lineNumber: index + 1,
                section: currentSection,
                fileName: fileName,
                projectId: projectId
            ) {
                backlogTasks.append(backlogTask)
            }
        }
        
        return backlogTasks
    }
    
    /// Parse line as generic specification task
    private func parseLineAsSpecTask(line: String, lineNumber: Int, section: String, fileName: String, projectId: UUID) -> DocumentTask? {
        guard !line.isEmpty && !line.hasPrefix("#") else { return nil }
        
        var taskText = line
        var priority = TaskPriority.medium
        var confidence: Double = 0.7
        
        // Skip completed items
        if line.contains("✅") || line.localizedCaseInsensitiveContains("done") {
            return nil
        }
        
        // Generic specification indicators
        if line.hasPrefix("- ") || line.hasPrefix("* ") {
            taskText = String(line.dropFirst(2)).trimmingCharacters(in: .whitespacesAndNewlines)
            confidence += 0.1
        }
        
        // File type based priority
        if fileName.localizedCaseInsensitiveContains("spec") {
            confidence += 0.1
        }
        
        guard taskText.count > 8 else { return nil }
        
        let description = generateSpecTaskDescription(originalText: line, section: section, fileName: fileName, confidence: confidence)
        
        return DocumentTask(
            id: UUID(),
            title: taskText,
            description: description,
            suggestedStatus: .backlog,
            suggestedPriority: priority,
            projectId: projectId,
            confidence: min(confidence, 1.0),
            sourceType: .readme, // Generic type for now
            documentSource: fileName,
            originalLine: line,
            lineNumber: lineNumber,
            section: section,
            tags: generateSpecTags(from: taskText, fileName: fileName)
        )
    }
    
    /// Generate enhanced description for PRD tasks
    private func generatePRDTaskDescription(originalText: String, section: String, confidence: Double) -> String {
        var description = "Auto-extracted from PRD.md - Product Requirement"
        
        if !section.isEmpty {
            description += " (Section: \(section))"
        }
        
        description += "\n\nRequirement: \(originalText)"
        description += "\nConfidence: \(Int(confidence * 100))%"
        description += "\nType: Product Requirement Document"
        description += "\nStatus: Ready for analysis and implementation planning"
        
        return description
    }
    
    /// Generate enhanced description for MVP tasks
    private func generateMVPTaskDescription(originalText: String, section: String, confidence: Double) -> String {
        var description = "Auto-extracted from MVP.md - Core Feature"
        
        if !section.isEmpty {
            description += " (Section: \(section))"
        }
        
        description += "\n\nFeature: \(originalText)"
        description += "\nConfidence: \(Int(confidence * 100))%"
        description += "\nType: Minimum Viable Product Feature"
        description += "\nPriority: Essential for launch"
        
        return description
    }
    
    /// Generate enhanced description for specification tasks
    private func generateSpecTaskDescription(originalText: String, section: String, fileName: String, confidence: Double) -> String {
        var description = "Auto-extracted from \(fileName)"
        
        if !section.isEmpty {
            description += " (Section: \(section))"
        }
        
        description += "\n\nSpecification: \(originalText)"
        description += "\nConfidence: \(Int(confidence * 100))%"
        description += "\nSource: Documentation Specification"
        
        return description
    }
    
    /// Generate specialized tags for PRD tasks
    private func generatePRDTags(from text: String, section: String) -> [String] {
        var tags = ["auto-backlog", "prd", "requirement"]
        
        if !section.isEmpty {
            tags.append(section.lowercased().replacingOccurrences(of: " ", with: "-"))
        }
        
        // Add requirement-specific tags
        if text.localizedCaseInsensitiveContains("functional") {
            tags.append("functional-requirement")
        } else if text.localizedCaseInsensitiveContains("non-functional") {
            tags.append("non-functional-requirement")
        }
        
        return tags
    }
    
    /// Generate specialized tags for MVP tasks
    private func generateMVPTags(from text: String, section: String) -> [String] {
        var tags = ["auto-backlog", "mvp", "core-feature", "launch-critical"]
        
        if !section.isEmpty {
            tags.append(section.lowercased().replacingOccurrences(of: " ", with: "-"))
        }
        
        return tags
    }
    
    /// Generate specialized tags for specification tasks
    private func generateSpecTags(from text: String, fileName: String) -> [String] {
        var tags = ["auto-backlog", "specification"]
        
        let baseFileName = fileName.replacingOccurrences(of: ".md", with: "").lowercased()
        tags.append(baseFileName)
        
        return tags
    }
    
    /// Extract Backlog tasks specifically from Plan.md content
    private func extractBacklogTasksFromPlan(content: String, projectId: UUID) async -> [DocumentTask] {
        let lines = content.components(separatedBy: .newlines)
        var backlogTasks: [DocumentTask] = []
        var currentSection = ""
        
        for (index, line) in lines.enumerated() {
            let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
            
            // Track current section for context
            if trimmedLine.hasPrefix("#") {
                currentSection = extractSectionTitle(from: trimmedLine)
                continue
            }
            
            // Focus on extracting pending tasks, TODO items, and planned features
            if let backlogTask = parseLineAsBacklogTask(
                line: trimmedLine,
                lineNumber: index + 1,
                section: currentSection,
                projectId: projectId
            ) {
                backlogTasks.append(backlogTask)
            }
        }
        
        // Sort by confidence and priority
        return backlogTasks.sorted { 
            if $0.confidence != $1.confidence {
                return $0.confidence > $1.confidence
            }
            return $0.suggestedPriority.rawValue > $1.suggestedPriority.rawValue
        }
    }
    
    /// Parse individual line as potential Backlog task with high precision
    private func parseLineAsBacklogTask(line: String, lineNumber: Int, section: String, projectId: UUID) -> DocumentTask? {
        guard !line.isEmpty && !line.hasPrefix("#") else { return nil }
        
        var taskText = line
        var priority = TaskPriority.medium
        var confidence: Double = 0.7
        
        // Skip completed tasks for Backlog
        if line.contains("✅") || line.localizedCaseInsensitiveContains("completed") || line.localizedCaseInsensitiveContains("done") {
            return nil
        }
        
        // High priority indicators for Backlog tasks
        let backlogIndicators = [
            "TODO:", "- [ ]", "* [ ]", "FIXME:", "PLANNED:", "NEXT:", "PHASE", "MILESTONE",
            "PRIORITY", "ENHANCEMENT", "FEATURE", "IMPLEMENT", "ADD", "CREATE", "BUILD"
        ]
        
        let containsBacklogIndicator = backlogIndicators.contains { indicator in
            line.localizedCaseInsensitiveContains(indicator)
        }
        
        if containsBacklogIndicator {
            confidence += 0.2
            
            // Clean up task text
            taskText = line
                .replacingOccurrences(of: "TODO:", with: "")
                .replacingOccurrences(of: "FIXME:", with: "")
                .replacingOccurrences(of: "PLANNED:", with: "")
                .replacingOccurrences(of: "- [ ]", with: "")
                .replacingOccurrences(of: "* [ ]", with: "")
                .trimmingCharacters(in: .whitespacesAndNewlines)
        } else if line.hasPrefix("- ") || line.hasPrefix("* ") {
            // Regular bullet points get lower confidence unless in specific sections
            if section.localizedCaseInsensitiveContains("backlog") || 
               section.localizedCaseInsensitiveContains("todo") ||
               section.localizedCaseInsensitiveContains("planned") ||
               section.localizedCaseInsensitiveContains("next") {
                confidence += 0.1
            }
            taskText = String(line.dropFirst(2)).trimmingCharacters(in: .whitespacesAndNewlines)
        } else {
            // Non-bullet items get lower confidence unless they contain action words
            let actionWords = ["implement", "add", "create", "build", "develop", "design", "integrate"]
            if actionWords.contains(where: { line.localizedCaseInsensitiveContains($0) }) {
                confidence += 0.1
            } else {
                return nil // Skip non-actionable items
            }
        }
        
        // Priority assessment based on keywords
        if line.localizedCaseInsensitiveContains("urgent") || line.localizedCaseInsensitiveContains("critical") || line.contains("🔥") {
            priority = .urgent
            confidence += 0.2
        } else if line.localizedCaseInsensitiveContains("high") || line.localizedCaseInsensitiveContains("important") {
            priority = .high
            confidence += 0.1
        }
        
        // Section-based priority boosts
        if section.localizedCaseInsensitiveContains("phase 1") || section.localizedCaseInsensitiveContains("mvp") {
            priority = enhancePriority(priority)
            confidence += 0.15
        }
        
        // Ensure meaningful task text
        guard taskText.count > 10 && !taskText.localizedCaseInsensitiveContains("example") else {
            return nil
        }
        
        let description = generateBacklogTaskDescription(originalText: line, section: section, confidence: confidence)
        
        return DocumentTask(
            id: UUID(),
            title: taskText,
            description: description,
            suggestedStatus: .backlog, // Always Backlog for Plan.md tasks
            suggestedPriority: priority,
            projectId: projectId,
            confidence: min(confidence, 1.0),
            sourceType: .plan,
            documentSource: "PLAN.md",
            originalLine: line,
            lineNumber: lineNumber,
            section: section,
            tags: generateBacklogTags(from: taskText, section: section)
        )
    }
    
    /// Generate enhanced description for Backlog tasks
    private func generateBacklogTaskDescription(originalText: String, section: String, confidence: Double) -> String {
        var description = "Auto-extracted from PLAN.md for Backlog population"
        
        if !section.isEmpty {
            description += " (Section: \(section))"
        }
        
        description += "\n\nOriginal: \(originalText)"
        description += "\nConfidence: \(Int(confidence * 100))%"
        description += "\nStatus: Ready for Backlog → To-Do transition"
        
        return description
    }
    
    /// Generate specialized tags for Backlog tasks
    private func generateBacklogTags(from text: String, section: String) -> [String] {
        var tags = ["auto-backlog", "plan-md", "pending"]
        
        if !section.isEmpty {
            tags.append(section.lowercased().replacingOccurrences(of: " ", with: "-"))
        }
        
        // Add feature-specific tags
        let featureKeywords = [
            "ui": "ui-ux",
            "backend": "backend",
            "api": "api",
            "database": "database",
            "test": "testing",
            "security": "security",
            "performance": "performance"
        ]
        
        for (keyword, tag) in featureKeywords {
            if text.localizedCaseInsensitiveContains(keyword) {
                tags.append(tag)
                break
            }
        }
        
        return tags
    }
    
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
            
            try await taskService.addTask(leanVibeTask)
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

struct DocumentTask: Identifiable, Hashable {
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
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
        hasher.combine(title)
        hasher.combine(projectId)
    }
    
    static func == (lhs: DocumentTask, rhs: DocumentTask) -> Bool {
        return lhs.id == rhs.id || (lhs.title == rhs.title && lhs.projectId == rhs.projectId)
    }
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