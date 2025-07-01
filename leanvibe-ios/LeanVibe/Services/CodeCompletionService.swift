import Foundation
import Combine

#if os(iOS)
import UIKit
#else
import AppKit
#endif

@available(iOS 18.0, *)
@MainActor
class CodeCompletionService: ObservableObject {
    @Published var isLoading = false
    @Published var lastResponse: CodeCompletionResponse?
    @Published var lastError: String?
    
    private let webSocketService: WebSocketService
    private var cancellables = Set<AnyCancellable>()
    
    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        setupNotificationSubscriptions()
    }
    
    private func setupNotificationSubscriptions() {
        // Subscribe to code completion responses (string-based)
        NotificationCenter.default.publisher(for: Notification.Name("codeCompletionResponse"))
            .compactMap { $0.object as? String }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] responseString in
                self?.handleResponseString(responseString)
            }
            .store(in: &cancellables)
        
        // Subscribe to code completion errors
        NotificationCenter.default.publisher(for: Notification.Name("codeCompletionError"))
            .compactMap { $0.object as? String }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] error in
                self?.handleError(error)
            }
            .store(in: &cancellables)
    }
    
    private func handleResponseString(_ responseString: String) {
        guard let data = responseString.data(using: .utf8) else {
            handleError("Invalid response format")
            return
        }
        
        do {
            let response = try JSONDecoder().decode(CodeCompletionResponse.self, from: data)
            handleResponse(response)
        } catch {
            handleError("Failed to parse response: \(error.localizedDescription)")
        }
    }
    
    // MARK: - Code Completion Methods
    
    func suggest(for filePath: String = "current_file.py", content: String = "", language: String = "python") async {
        await performCodeCompletion(intent: "suggest", filePath: filePath, content: content, language: language)
    }
    
    func explain(for filePath: String = "current_file.py", content: String = "", language: String = "python") async {
        await performCodeCompletion(intent: "explain", filePath: filePath, content: content, language: language)
    }
    
    func refactor(for filePath: String = "current_file.py", content: String = "", language: String = "python") async {
        await performCodeCompletion(intent: "refactor", filePath: filePath, content: content, language: language)
    }
    
    func debug(for filePath: String = "current_file.py", content: String = "", language: String = "python") async {
        await performCodeCompletion(intent: "debug", filePath: filePath, content: content, language: language)
    }
    
    func optimize(for filePath: String = "current_file.py", content: String = "", language: String = "python") async {
        await performCodeCompletion(intent: "optimize", filePath: filePath, content: content, language: language)
    }
    
    // MARK: - Voice Command Integration
    
    func handleVoiceCommand(_ command: VoiceCommand, withContent content: String? = nil) async {
        let actualContent = content ?? getCurrentFileContent() ?? getDefaultSampleContent()
        
        switch command.intent {
        case .suggest:
            await suggest(content: actualContent)
        case .explain:
            await explain(content: actualContent)
        case .refactor:
            await refactor(content: actualContent)
        case .debug:
            await debug(content: actualContent)
        case .optimize:
            await optimize(content: actualContent)
        default:
            // For other intents, treat as general suggestion
            await suggest(content: actualContent)
        }
    }
    
    // MARK: - Content Integration
    
    private func getCurrentFileContent() -> String? {
        // TODO: Integrate with actual file system or project context
        // For MVP, this could integrate with:
        // 1. Current file in active project
        // 2. Clipboard content (if it looks like code)
        // 3. Recently modified files
        
        // Check if clipboard contains code-like content
        if let clipboardContent = getClipboardContent(),
           isCodeLikeContent(clipboardContent) {
            return clipboardContent
        }
        
        return nil
    }
    
    private func getClipboardContent() -> String? {
        #if os(iOS)
        return UIPasteboard.general.string
        #else
        return NSPasteboard.general.string(forType: .string)
        #endif
    }
    
    private func isCodeLikeContent(_ content: String) -> Bool {
        let codeIndicators = [
            "def ", "function ", "class ", "import ", "from ",
            "{", "}", "(", ")", "=", "==", "!=", "//", "/*", "#",
            "var ", "let ", "const ", "if ", "for ", "while "
        ]
        
        let lowercased = content.lowercased()
        let hasCodeIndicators = codeIndicators.contains { lowercased.contains($0) }
        let hasMultipleLines = content.components(separatedBy: .newlines).count > 2
        let isReasonableLength = content.count > 20 && content.count < 10000
        
        return hasCodeIndicators && hasMultipleLines && isReasonableLength
    }
    
    private func getDefaultSampleContent() -> String {
        return """
        def hello_world():
            # TODO: implement this function
            pass
        
        def calculate_sum(a, b):
            return a + b
        
        def process_data(data):
            # This function needs optimization
            result = []
            for item in data:
                if item > 0:
                    result.append(item * 2)
            return result
        """
    }
    
    // MARK: - Private Methods
    
    private func performCodeCompletion(intent: String, filePath: String, content: String, language: String) async {
        guard webSocketService.isConnected else {
            lastError = "Not connected to backend"
            return
        }
        
        isLoading = true
        lastError = nil
        
        let request = CodeCompletionRequest(
            filePath: filePath,
            cursorPosition: 10, // Default cursor position
            content: content,
            language: language,
            intent: intent
        )
        
        do {
            let jsonData = try JSONEncoder().encode(request)
            let jsonString = String(data: jsonData, encoding: .utf8) ?? ""
            
            // Send via WebSocket with code completion type
            let message = CodeCompletionMessage(
                type: "code_completion",
                request: request,
                timestamp: Date()
            )
            
            let messageData = try JSONEncoder().encode(message)
            let messageString = String(data: messageData, encoding: .utf8) ?? ""
            
            webSocketService.sendMessage(messageString, type: "code_completion")
            
            // Note: Response will be handled via WebSocket delegate methods
            // The WebSocketService should parse responses and notify this service
            
        } catch {
            lastError = "Failed to send request: \(error.localizedDescription)"
            isLoading = false
        }
    }
    
    // MARK: - Response Handling
    
    func handleResponse(_ response: CodeCompletionResponse) {
        lastResponse = response
        isLoading = false
        lastError = nil
    }
    
    func handleError(_ error: String) {
        lastError = error
        isLoading = false
    }
}

