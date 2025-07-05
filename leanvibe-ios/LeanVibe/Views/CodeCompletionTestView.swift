import SwiftUI

// VoiceSettings is now defined in SettingsManager.swift

@available(iOS 18.0, *)
struct CodeCompletionTestView: View {
    let webSocketService: WebSocketService
    @StateObject private var codeCompletionService: CodeCompletionService
    @StateObject private var voiceManager = OptimizedVoiceManager()
    
    @State private var sampleCode = """
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
    
    init(webSocketService: WebSocketService) {
        self.webSocketService = webSocketService
        self._codeCompletionService = StateObject(wrappedValue: CodeCompletionService(webSocketService: webSocketService))
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    
                    // Connection Status
                    connectionStatusSection
                    
                    // Sample Code Section
                    sampleCodeSection
                    
                    // Code Completion Buttons
                    codeCompletionButtonsSection
                    
                    // Voice Commands Section
                    voiceCommandsSection
                    
                    // Results Section
                    resultsSection
                    
                    Spacer()
                }
                .padding()
            }
            .navigationTitle("Code Completion Test")
            .onAppear {
                webSocketService.connect()
            }
        }
    }
    
    // MARK: - View Components
    
    private var connectionStatusSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Backend Connection")
                .font(.headline)
            
            HStack {
                Circle()
                    .fill(webSocketService.isConnected ? .green : .red)
                    .frame(width: 12, height: 12)
                
                Text(webSocketService.connectionStatus)
                    .font(.subheadline)
                
                Spacer()
                
                if !webSocketService.isConnected {
                    Button("Connect") {
                        webSocketService.connect()
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                }
            }
            
            if let error = webSocketService.lastError {
                Text("Error: \(error)")
                    .font(.caption)
                    .foregroundColor(.red)
            }
        }
        .padding()
        .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
        .cornerRadius(12)
    }
    
    private var sampleCodeSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Sample Code")
                .font(.headline)
            
            SyntaxHighlightedCodeView(code: sampleCode)
                .frame(height: 150)
        }
    }
    
    private var codeCompletionButtonsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Code Completion Actions")
                .font(.headline)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                
                CodeCompletionButton(
                    title: "Suggest",
                    icon: "lightbulb",
                    color: .blue
                ) {
                    Task {
                        await codeCompletionService.suggest(content: sampleCode)
                    }
                }
                
                CodeCompletionButton(
                    title: "Use Clipboard",
                    icon: "doc.on.clipboard",
                    color: .green
                ) {
                    Task {
                        // This will use clipboard content if it contains code
                        await codeCompletionService.suggest(content: "")
                    }
                }
                
                CodeCompletionButton(
                    title: "Explain",
                    icon: "text.bubble",
                    color: .green
                ) {
                    Task {
                        await codeCompletionService.explain(content: sampleCode)
                    }
                }
                
                CodeCompletionButton(
                    title: "Refactor",
                    icon: "arrow.triangle.2.circlepath",
                    color: .orange
                ) {
                    Task {
                        await codeCompletionService.refactor(content: sampleCode)
                    }
                }
                
                CodeCompletionButton(
                    title: "Debug",
                    icon: "ant",
                    color: .red
                ) {
                    Task {
                        await codeCompletionService.debug(content: sampleCode)
                    }
                }
                
                CodeCompletionButton(
                    title: "Optimize",
                    icon: "speedometer",
                    color: .purple
                ) {
                    Task {
                        await codeCompletionService.optimize(content: sampleCode)
                    }
                }
                
                CodeCompletionButton(
                    title: "Voice Test",
                    icon: "mic",
                    color: .indigo
                ) {
                    simulateVoiceCommand()
                }
            }
        }
    }
    
    private var voiceCommandsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Try Voice Commands")
                .font(.headline)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Say \"Hey LeanVibe\" followed by:")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                ForEach([
                    "suggest improvements",
                    "explain this code",
                    "refactor this function",
                    "debug this code",
                    "optimize performance"
                ], id: \.self) { command in
                    Text("• \(command)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(.systemBlue).opacity(0.1))
        .cornerRadius(12)
    }
    
    private var resultsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Results")
                .font(.headline)
            
            if codeCompletionService.isLoading {
                HStack {
                    ProgressView()
                        .controlSize(.small)
                    Text("Processing...")
                        .font(.subheadline)
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
                .cornerRadius(8)
                
            } else if let response = codeCompletionService.lastResponse {
                
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text(response.intent.capitalized)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        
                        Spacer()
                        
                        ConfidenceBadge(confidence: response.confidence)
                    }
                    
                    ScrollView {
                        Group {
                            if isCodeResponse(response.response) {
                                SyntaxHighlightedCodeView(code: response.response)
                            } else {
                                Text(response.response)
                                    .font(.system(.caption, design: .default))
                                    .padding()
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .background(Color(.systemGray5))
                                    .cornerRadius(8)
                            }
                        }
                    }
                    .frame(maxHeight: 200)
                    
                    if !response.suggestions.isEmpty {
                        Text("Suggestions:")
                            .font(.caption)
                            .fontWeight(.medium)
                        
                        ForEach(response.suggestions, id: \.self) { suggestion in
                            Text("• \(suggestion)")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .padding()
                .background(Color(.systemGreen).opacity(0.1))
                .cornerRadius(12)
                
            } else if let error = codeCompletionService.lastError {
                
                Text("Error: \(error)")
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color(.systemRed).opacity(0.1))
                    .cornerRadius(8)
                
            } else {
                Text("No results yet. Try a code completion action above.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
                    .cornerRadius(8)
            }
        }
    }
    
    // MARK: - Helper Methods
    
    private func isCodeResponse(_ text: String) -> Bool {
        // Simple heuristics to detect if response contains code
        let codeIndicators = [
            "def ", "class ", "import ", "from ", "if ", "for ", "while ",
            "return ", "print(", "len(", "range(", "def(", "lambda ",
            "    ", "\t", "```", "python", "def main", "#!/"
        ]
        
        let lowercaseText = text.lowercased()
        return codeIndicators.contains { lowercaseText.contains($0) }
    }
    
    private func simulateVoiceCommand() {
        // TODO: Fix VoiceSettings import issue  
        let processor = VoiceCommandProcessor() // (settings: VoiceSettings())
        let sampleCommands = [
            "suggest improvements to this code",
            "explain what this function does",
            "refactor this for better performance",
            "debug this code for errors",
            "optimize this function"
        ]
        
        if let randomCommand = sampleCommands.randomElement() {
            let voiceCommand = processor.processVoiceInput(randomCommand)
            
            Task {
                await codeCompletionService.handleVoiceCommand(voiceCommand)
            }
        }
    }
}

// MARK: - Supporting Views

struct CodeCompletionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                
                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(color.opacity(0.1))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(color.opacity(0.3), lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct ConfidenceBadge: View {
    let confidence: Double
    
    private var color: Color {
        if confidence >= 0.8 {
            return .green
        } else if confidence >= 0.6 {
            return .orange
        } else {
            return .red
        }
    }
    
    var body: some View {
        Text("\(Int(confidence * 100))%")
            .font(.caption2)
            .fontWeight(.semibold)
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color)
            .cornerRadius(8)
    }
}

// MARK: - Python Syntax Highlighter

/// A lightweight Python syntax highlighter for SwiftUI
@available(iOS 18.0, *)
struct PythonSyntaxHighlighter {
    
    // MARK: - Color Scheme
    struct ColorScheme {
        let keyword: Color
        let string: Color
        let comment: Color
        let number: Color
        let function: Color
        let builtin: Color
        let text: Color
        
        static let light = ColorScheme(
            keyword: .blue,
            string: .green,
            comment: .gray,
            number: .purple,
            function: .cyan,
            builtin: .orange,
            text: .primary
        )
        
        static let dark = ColorScheme(
            keyword: .cyan,
            string: .green,
            comment: .gray,
            number: .purple,
            function: .yellow,
            builtin: .orange,
            text: .primary
        )
        
        static func current(for colorScheme: SwiftUI.ColorScheme) -> ColorScheme {
            return colorScheme == .dark ? .dark : .light
        }
    }
    
    // MARK: - Token Types
    enum TokenType {
        case keyword
        case string
        case comment
        case number
        case function
        case builtin
        case text
    }
    
    struct Token {
        let type: TokenType
        let text: String
        let range: Range<String.Index>
    }
    
    // MARK: - Python Language Definition
    private static let keywords = Set([
        "def", "class", "if", "elif", "else", "for", "while", "break", "continue",
        "return", "yield", "try", "except", "finally", "with", "as", "import",
        "from", "pass", "del", "global", "nonlocal", "assert", "lambda", "and",
        "or", "not", "in", "is", "True", "False", "None"
    ])
    
    private static let builtins = Set([
        "print", "len", "range", "enumerate", "zip", "map", "filter", "sorted",
        "sum", "max", "min", "abs", "round", "int", "float", "str", "list",
        "dict", "set", "tuple", "bool", "type", "isinstance", "hasattr"
    ])
    
    // MARK: - Tokenization
    static func tokenize(_ code: String) -> [Token] {
        var tokens: [Token] = []
        let lines = code.components(separatedBy: .newlines)
        var currentIndex = code.startIndex
        
        for line in lines {
            let lineTokens = tokenizeLine(line, startIndex: currentIndex, fullString: code)
            tokens.append(contentsOf: lineTokens)
            
            // Move to next line
            if let nextIndex = code.index(currentIndex, offsetBy: line.count + 1, limitedBy: code.endIndex) {
                currentIndex = nextIndex
            } else {
                break
            }
        }
        
        return tokens
    }
    
    private static func tokenizeLine(_ line: String, startIndex: String.Index, fullString: String) -> [Token] {
        var tokens: [Token] = []
        var i = line.startIndex
        var lineStartIndex = startIndex
        
        while i < line.endIndex {
            let char = line[i]
            
            // Skip whitespace
            if char.isWhitespace {
                i = line.index(after: i)
                lineStartIndex = fullString.index(after: lineStartIndex)
                continue
            }
            
            // Comments
            if char == "#" {
                let restOfLine = String(line[i...])
                let range = lineStartIndex..<fullString.index(lineStartIndex, offsetBy: restOfLine.count)
                tokens.append(Token(type: .comment, text: restOfLine, range: range))
                break
            }
            
            // Strings
            if char == "\"" || char == "'" {
                if let stringToken = parseString(from: i, in: line, startIndex: lineStartIndex, fullString: fullString) {
                    tokens.append(stringToken)
                    i = line.index(i, offsetBy: stringToken.text.count)
                    lineStartIndex = fullString.index(lineStartIndex, offsetBy: stringToken.text.count)
                    continue
                }
            }
            
            // Numbers
            if char.isNumber {
                if let numberToken = parseNumber(from: i, in: line, startIndex: lineStartIndex, fullString: fullString) {
                    tokens.append(numberToken)
                    i = line.index(i, offsetBy: numberToken.text.count)
                    lineStartIndex = fullString.index(lineStartIndex, offsetBy: numberToken.text.count)
                    continue
                }
            }
            
            // Identifiers/Keywords/Functions
            if char.isLetter || char == "_" {
                if let identifierToken = parseIdentifier(from: i, in: line, startIndex: lineStartIndex, fullString: fullString) {
                    tokens.append(identifierToken)
                    i = line.index(i, offsetBy: identifierToken.text.count)
                    lineStartIndex = fullString.index(lineStartIndex, offsetBy: identifierToken.text.count)
                    continue
                }
            }
            
            // Single characters (operators, punctuation)
            let singleChar = String(char)
            let range = lineStartIndex..<fullString.index(after: lineStartIndex)
            tokens.append(Token(type: .text, text: singleChar, range: range))
            i = line.index(after: i)
            lineStartIndex = fullString.index(after: lineStartIndex)
        }
        
        return tokens
    }
    
    private static func parseString(from index: String.Index, in line: String, startIndex: String.Index, fullString: String) -> Token? {
        let quote = line[index]
        var i = line.index(after: index)
        var escaped = false
        
        while i < line.endIndex {
            let char = line[i]
            if escaped {
                escaped = false
            } else if char == "\\" {
                escaped = true
            } else if char == quote {
                let endIndex = line.index(after: i)
                let text = String(line[index..<endIndex])
                let range = startIndex..<fullString.index(startIndex, offsetBy: text.count)
                return Token(type: .string, text: text, range: range)
            }
            i = line.index(after: i)
        }
        
        // Unclosed string
        let text = String(line[index...])
        let range = startIndex..<fullString.index(startIndex, offsetBy: text.count)
        return Token(type: .string, text: text, range: range)
    }
    
    private static func parseNumber(from index: String.Index, in line: String, startIndex: String.Index, fullString: String) -> Token? {
        var i = index
        var hasDecimal = false
        
        while i < line.endIndex {
            let char = line[i]
            if char.isNumber {
                i = line.index(after: i)
            } else if char == "." && !hasDecimal {
                hasDecimal = true
                i = line.index(after: i)
            } else {
                break
            }
        }
        
        let text = String(line[index..<i])
        let range = startIndex..<fullString.index(startIndex, offsetBy: text.count)
        return Token(type: .number, text: text, range: range)
    }
    
    private static func parseIdentifier(from index: String.Index, in line: String, startIndex: String.Index, fullString: String) -> Token? {
        var i = index
        
        while i < line.endIndex {
            let char = line[i]
            if char.isLetter || char.isNumber || char == "_" {
                i = line.index(after: i)
            } else {
                break
            }
        }
        
        let text = String(line[index..<i])
        let range = startIndex..<fullString.index(startIndex, offsetBy: text.count)
        
        // Determine token type
        let type: TokenType
        if keywords.contains(text) {
            type = .keyword
        } else if builtins.contains(text) {
            type = .builtin
        } else if i < line.endIndex && line[i] == "(" {
            type = .function
        } else {
            type = .text
        }
        
        return Token(type: type, text: text, range: range)
    }
    
    // MARK: - Attributed String Generation
    static func attributedString(from code: String, colorScheme: SwiftUI.ColorScheme, font: Font = .system(.body, design: .monospaced)) -> AttributedString {
        let tokens = tokenize(code)
        let colors = ColorScheme.current(for: colorScheme)
        var attributedString = AttributedString(code)
        
        for token in tokens {
            let color = colorForToken(token.type, colors: colors)
            if let range = Range(token.range, in: attributedString) {
                attributedString[range].foregroundColor = color
            }
        }
        
        // Apply monospace font to entire string
        attributedString.font = font
        
        return attributedString
    }
    
    private static func colorForToken(_ type: TokenType, colors: ColorScheme) -> Color {
        switch type {
        case .keyword:
            return colors.keyword
        case .string:
            return colors.string
        case .comment:
            return colors.comment
        case .number:
            return colors.number
        case .function:
            return colors.function
        case .builtin:
            return colors.builtin
        case .text:
            return colors.text
        }
    }
}

// MARK: - SwiftUI View Component
@available(iOS 18.0, *)
struct SyntaxHighlightedCodeView: View {
    let code: String
    let language: String = "python" // Future extensibility
    @Environment(\.colorScheme) private var colorScheme
    
    var body: some View {
        ScrollView([.horizontal, .vertical]) {
            Text(PythonSyntaxHighlighter.attributedString(
                from: code,
                colorScheme: colorScheme,
                font: .custom("SF Mono", size: 14, relativeTo: .caption)
                    .monospaced()
            ))
            .textSelection(.enabled)
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(#if os(iOS)
Color(.systemGray6)
#else
Color.gray.opacity(0.1)
#endif)
        .cornerRadius(8)
    }
}

// MARK: - Voice Settings placeholder removed (conflicts with SettingsManager.VoiceSettings)