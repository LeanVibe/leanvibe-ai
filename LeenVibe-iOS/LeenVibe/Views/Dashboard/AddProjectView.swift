import SwiftUI

struct AddProjectView: View {
    @ObservedObject var projectManager: ProjectManager
    @Environment(\.dismiss) private var dismiss
    
    @State private var projectName = ""
    @State private var projectPath = ""
    @State private var selectedLanguage: ProjectLanguage = .swift
    @State private var showingDocumentPicker = false
    @State private var showingLanguageDetection = false
    
    var body: some View {
        NavigationView {
            Form {
                Section("Project Information") {
                    TextField("Project Name", text: $projectName)
                        .autocapitalization(.words)
                    
                    HStack {
                        TextField("Project Path", text: $projectPath)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                        
                        Button("Browse") {
                            showingDocumentPicker = true
                        }
                        .buttonStyle(.bordered)
                    }
                }
                
                Section("Language") {
                    Picker("Programming Language", selection: $selectedLanguage) {
                        ForEach(ProjectLanguage.allCases, id: \.self) { language in
                            HStack {
                                Image(systemName: language.icon)
                                    .foregroundColor(Color(language.color))
                                    .frame(width: 20)
                                Text(language.rawValue)
                            }
                            .tag(language)
                        }
                    }
                    
                    Button("Auto-detect Language") {
                        detectLanguage()
                    }
                    .disabled(projectPath.isEmpty)
                    .foregroundColor(.blue)
                }
                
                Section("Quick Setup") {
                    QuickSetupButtonView(
                        title: "iOS Project",
                        subtitle: "Swift/SwiftUI project",
                        icon: "swift",
                        color: .orange
                    ) {
                        setupiOSProject()
                    }
                    
                    QuickSetupButtonView(
                        title: "Python Project",
                        subtitle: "Python with virtual environment",
                        icon: "snake.fill",
                        color: .green
                    ) {
                        setupPythonProject()
                    }
                    
                    QuickSetupButtonView(
                        title: "Node.js Project",
                        subtitle: "JavaScript/TypeScript project",
                        icon: "globe",
                        color: .yellow
                    ) {
                        setupNodeProject()
                    }
                    
                    QuickSetupButtonView(
                        title: "React Project",
                        subtitle: "React web application",
                        icon: "atom",
                        color: .blue
                    ) {
                        setupReactProject()
                    }
                }
                
                if !projectPath.isEmpty {
                    Section("Preview") {
                        ProjectPreviewView(
                            name: projectName.isEmpty ? "New Project" : projectName,
                            path: projectPath,
                            language: selectedLanguage
                        )
                    }
                }
            }
            .navigationTitle("Add Project")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Add") {
                        addProject()
                    }
                    .disabled(projectName.isEmpty || projectPath.isEmpty)
                }
            }
            .sheet(isPresented: $showingDocumentPicker) {
                DocumentPickerView { url in
                    projectPath = url.path
                    if projectName.isEmpty {
                        projectName = url.lastPathComponent
                    }
                    detectLanguage()
                }
            }
        }
    }
    
    private func addProject() {
        projectManager.addProject(
            name: projectName,
            path: projectPath,
            language: selectedLanguage
        )
        dismiss()
    }
    
    private func detectLanguage() {
        // Simple language detection based on file extensions
        let fileManager = FileManager.default
        
        do {
            let contents = try fileManager.contentsOfDirectory(atPath: projectPath)
            
            if contents.contains(where: { $0.hasSuffix(".swift") || $0.hasSuffix(".xcodeproj") }) {
                selectedLanguage = .swift
            } else if contents.contains(where: { $0.hasSuffix(".py") || $0 == "requirements.txt" }) {
                selectedLanguage = .python
            } else if contents.contains(where: { $0.hasSuffix(".js") || $0.hasSuffix(".ts") || $0 == "package.json" }) {
                selectedLanguage = .javascript
            } else if contents.contains(where: { $0.hasSuffix(".java") || $0 == "pom.xml" }) {
                selectedLanguage = .java
            } else if contents.contains(where: { $0.hasSuffix(".go") || $0 == "go.mod" }) {
                selectedLanguage = .go
            } else if contents.contains(where: { $0.hasSuffix(".rs") || $0 == "Cargo.toml" }) {
                selectedLanguage = .rust
            }
        } catch {
            print("Failed to detect language: \(error)")
        }
    }
    
    private func setupiOSProject() {
        selectedLanguage = .swift
        if projectName.isEmpty {
            projectName = "iOS Project"
        }
    }
    
    private func setupPythonProject() {
        selectedLanguage = .python
        if projectName.isEmpty {
            projectName = "Python Project"
        }
    }
    
    private func setupNodeProject() {
        selectedLanguage = .javascript
        if projectName.isEmpty {
            projectName = "Node.js Project"
        }
    }
    
    private func setupReactProject() {
        selectedLanguage = .javascript
        if projectName.isEmpty {
            projectName = "React Project"
        }
    }
}

struct QuickSetupButtonView: View {
    let title: String
    let subtitle: String
    let icon: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title2)
                    .frame(width: 30)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    Text(subtitle)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }
        }
        .buttonStyle(.plain)
    }
}

struct ProjectPreviewView: View {
    let name: String
    let path: String
    let language: ProjectLanguage
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: language.icon)
                    .foregroundColor(Color(language.color))
                    .font(.title2)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(name)
                        .font(.headline)
                    
                    Text(language.rawValue)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text("Path")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text(path)
                    .font(.caption)
                    .fontFamily(.monospaced)
                    .padding(8)
                    .background(.gray.opacity(0.1), in: RoundedRectangle(cornerRadius: 6))
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            
            // Project stats (simulated)
            HStack {
                StatView(label: "Estimated Files", value: "~\(estimatedFiles)")
                Spacer()
                StatView(label: "Project Type", value: language.projectType)
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private var estimatedFiles: Int {
        // Simulate file count estimation based on language
        switch language {
        case .swift:
            return Int.random(in: 15...50)
        case .python:
            return Int.random(in: 10...30)
        case .javascript:
            return Int.random(in: 20...60)
        case .java:
            return Int.random(in: 25...80)
        case .go:
            return Int.random(in: 8...25)
        case .rust:
            return Int.random(in: 10...30)
        case .cpp:
            return Int.random(in: 15...40)
        case .csharp:
            return Int.random(in: 20...50)
        case .unknown:
            return Int.random(in: 5...20)
        }
    }
}

struct StatView: View {
    let label: String
    let value: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
            
            Text(value)
                .font(.caption)
                .fontWeight(.medium)
        }
    }
}

struct DocumentPickerView: UIViewControllerRepresentable {
    let onSelection: (URL) -> Void
    
    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        let picker = UIDocumentPickerViewController(forOpeningContentTypes: [.folder])
        picker.delegate = context.coordinator
        picker.allowsMultipleSelection = false
        return picker
    }
    
    func updateUIViewController(_ uiViewController: UIDocumentPickerViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(onSelection: onSelection)
    }
    
    class Coordinator: NSObject, UIDocumentPickerDelegate {
        let onSelection: (URL) -> Void
        
        init(onSelection: @escaping (URL) -> Void) {
            self.onSelection = onSelection
        }
        
        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
            guard let url = urls.first else { return }
            onSelection(url)
        }
    }
}

extension ProjectLanguage {
    var projectType: String {
        switch self {
        case .swift:
            return "iOS/macOS"
        case .python:
            return "Backend/ML"
        case .javascript:
            return "Web/Node.js"
        case .java:
            return "Enterprise"
        case .go:
            return "Backend/CLI"
        case .rust:
            return "Systems"
        case .cpp:
            return "Systems"
        case .csharp:
            return ".NET"
        case .unknown:
            return "Mixed"
        }
    }
}

#Preview {
    AddProjectView(projectManager: ProjectManager())
}