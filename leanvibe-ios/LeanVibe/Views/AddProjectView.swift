import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
struct AddProjectView: View {
    @ObservedObject var projectManager: ProjectManager
    @Environment(\.dismiss) private var dismiss
    
    @State private var projectName = ""
    @State private var projectPath = ""
    @State private var selectedLanguage: ProjectLanguage = .unknown
    
    private func colorFromString(_ colorName: String) -> Color {
        switch colorName {
        case "orange": return PremiumDesignSystem.Colors.warning
        case "yellow": return Color(.systemYellow)
        case "blue": return PremiumDesignSystem.Colors.buttonPrimary
        case "purple": return PremiumDesignSystem.Colors.debugBadge
        case "red": return PremiumDesignSystem.Colors.error
        case "green": return PremiumDesignSystem.Colors.success
        case "cyan": return Color(.systemCyan)
        case "brown": return Color(.systemBrown)
        case "gray": return PremiumDesignSystem.Colors.iconSecondary
        default: return PremiumDesignSystem.Colors.iconSecondary
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
        Task {
            do {
                try await projectManager.addProject(
                    name: projectName,
                    path: projectPath,
                    language: selectedLanguage
                )
                await MainActor.run {
                    dismiss()
                }
            } catch {
                // Error handling is already managed by ProjectManager through lastError
                print("Failed to add project: \(error)")
            }
        }
    }
}

#if DEBUG
@available(iOS 18.0, macOS 14.0, *)
#Preview {
    AddProjectView(projectManager: ProjectManager())
}
#endif