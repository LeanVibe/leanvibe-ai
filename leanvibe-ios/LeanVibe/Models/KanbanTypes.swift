import Foundation

enum TaskSortOption: String, CaseIterable {
    case priority = "priority"
    case dueDate = "due_date"
    case title = "title"
    
    var displayName: String {
        switch self {
        case .priority: return "Priority"
        case .dueDate: return "Due Date"
        case .title: return "Title"
        }
    }
}