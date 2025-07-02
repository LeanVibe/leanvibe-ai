import SwiftUI

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
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    private var sampleCodeSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Sample Code")
                .font(.headline)
            
            ScrollView {
                Text(sampleCode)
                    .font(.system(.caption, design: .monospaced))
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color(.systemGray5))
                    .cornerRadius(8)
            }
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
                .background(Color(.systemGray6))
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
                        Text(response.response)
                            .font(.system(.caption, design: .default))
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color(.systemGray5))
                            .cornerRadius(8)
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
                    .background(Color(.systemGray6))
                    .cornerRadius(8)
            }
        }
    }
    
    // MARK: - Helper Methods
    
    private func simulateVoiceCommand() {
        let processor = VoiceCommandProcessor(settings: VoiceSettings())
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

// MARK: - Voice Settings placeholder removed (conflicts with SettingsManager.VoiceSettings)