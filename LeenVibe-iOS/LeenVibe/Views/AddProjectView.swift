import SwiftUI

struct AddProjectView: View {
    @ObservedObject var projectManager: ProjectManager
    @Environment(\.dismiss) private var dismiss
    
    @State private var projectName = ""
    @State private var projectPath = ""
    @State private var selectedLanguage: ProjectLanguage = .unknown
    
    private func colorFromString(_ colorName: String) -> Color {
        switch colorName {
        case "orange": return .orange
        case "yellow": return .yellow
        case "blue": return .blue
        case "purple": return .purple
        case "red": return .red
        case "green": return .green
        case "cyan": return .cyan
        case "brown": return .brown
        case "gray": return .gray
        default: return .gray
        }
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section("Project Details") {
                    TextField("Project Name", text: $projectName)
                    TextField("Project Path", text: $projectPath)
                    
                    Picker("Language", selection: $selectedLanguage) {
                        ForEach(ProjectLanguage.allCases, id: \.self) { language in
                            HStack {
                                Image(systemName: language.icon)
                                    .foregroundColor(colorFromString(language.color))
                                Text(language.rawValue)
                            }
                            .tag(language)
                        }
                    }
                }
                
                Section("Quick Setup") {
                    Button("Use Current Directory") {
                        projectPath = "/Users/\(NSUserName())/Documents"
                        if projectName.isEmpty {
                            projectName = "My Project"
                        }
                    }
                    
                    Button("Browse...") {
                        // File picker would go here
                        projectPath = "/path/to/project"
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
}

#Preview {
    AddProjectView(projectManager: ProjectManager())
}