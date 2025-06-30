
import Foundation

struct ArchitectureDiagram: Identifiable, Codable, Equatable {
    let id: UUID
    let name: String
    let mermaidDefinition: String
    let description: String?
    let diagramType: String?
    let createdAt: Date?
    let updatedAt: Date?
    let metadata: [String: String]?
    
    enum CodingKeys: String, CodingKey {
        case id, name, description
        case mermaidDefinition = "mermaid_definition"
        case diagramType = "diagram_type"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case metadata
    }
    
    // Custom initializer for manual creation
    init(
        id: UUID = UUID(),
        name: String,
        mermaidDefinition: String,
        description: String? = nil,
        diagramType: String? = nil,
        createdAt: Date? = nil,
        updatedAt: Date? = nil,
        metadata: [String: String]? = nil
    ) {
        self.id = id
        self.name = name
        self.mermaidDefinition = mermaidDefinition
        self.description = description
        self.diagramType = diagramType
        self.createdAt = createdAt ?? Date()
        self.updatedAt = updatedAt ?? Date()
        self.metadata = metadata
    }
    
    // Decoder initializer with fallback values
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        self.id = (try? container.decode(UUID.self, forKey: .id)) ?? UUID()
        self.name = try container.decode(String.self, forKey: .name)
        self.mermaidDefinition = try container.decode(String.self, forKey: .mermaidDefinition)
        self.description = try? container.decode(String.self, forKey: .description)
        self.diagramType = try? container.decode(String.self, forKey: .diagramType)
        
        // Handle date decoding with fallback
        if let createdString = try? container.decode(String.self, forKey: .createdAt) {
            self.createdAt = ISO8601DateFormatter().date(from: createdString)
        } else {
            self.createdAt = Date()
        }
        
        if let updatedString = try? container.decode(String.self, forKey: .updatedAt) {
            self.updatedAt = ISO8601DateFormatter().date(from: updatedString)
        } else {
            self.updatedAt = Date()
        }
        
        self.metadata = try? container.decode([String: String].self, forKey: .metadata)
    }
    
    // Encoder for sending data
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        
        try container.encode(id, forKey: .id)
        try container.encode(name, forKey: .name)
        try container.encode(mermaidDefinition, forKey: .mermaidDefinition)
        try container.encodeIfPresent(description, forKey: .description)
        try container.encodeIfPresent(diagramType, forKey: .diagramType)
        
        if let createdAt = createdAt {
            try container.encode(ISO8601DateFormatter().string(from: createdAt), forKey: .createdAt)
        }
        
        if let updatedAt = updatedAt {
            try container.encode(ISO8601DateFormatter().string(from: updatedAt), forKey: .updatedAt)
        }
        
        try container.encodeIfPresent(metadata, forKey: .metadata)
    }
    
    // Equatable implementation
    static func == (lhs: ArchitectureDiagram, rhs: ArchitectureDiagram) -> Bool {
        return lhs.id == rhs.id && 
               lhs.mermaidDefinition == rhs.mermaidDefinition
    }
    
    // Computed properties
    var displayType: String {
        return diagramType?.capitalized ?? "Architecture Diagram"
    }
    
    var isValid: Bool {
        return !name.isEmpty && !mermaidDefinition.isEmpty
    }
    
    var nodeCount: Int {
        // Simple estimation based on mermaid syntax
        let lines = mermaidDefinition.components(separatedBy: .newlines)
        return lines.filter { line in
            let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
            return trimmed.contains("-->") || trimmed.contains("->") || trimmed.contains("[")
        }.count
    }
    
    // Helper methods
    func withUpdatedDefinition(_ newDefinition: String) -> ArchitectureDiagram {
        return ArchitectureDiagram(
            id: self.id,
            name: self.name,
            mermaidDefinition: newDefinition,
            description: self.description,
            diagramType: self.diagramType,
            createdAt: self.createdAt,
            updatedAt: Date(),
            metadata: self.metadata
        )
    }
    
    func withMetadata(_ newMetadata: [String: String]) -> ArchitectureDiagram {
        var combinedMetadata = self.metadata ?? [:]
        for (key, value) in newMetadata {
            combinedMetadata[key] = value
        }
        
        return ArchitectureDiagram(
            id: self.id,
            name: self.name,
            mermaidDefinition: self.mermaidDefinition,
            description: self.description,
            diagramType: self.diagramType,
            createdAt: self.createdAt,
            updatedAt: self.updatedAt,
            metadata: combinedMetadata
        )
    }
}
