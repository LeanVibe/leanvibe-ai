"""
Graph Database Models for Code Relationships

Defines Pydantic models for representing code structure and relationships
in a Neo4j graph database.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .ast_models import LanguageType, SymbolType


class RelationshipType(str, Enum):
    """Types of relationships between code entities"""

    DEPENDS_ON = "DEPENDS_ON"
    CALLS = "CALLS"
    INHERITS_FROM = "INHERITS_FROM"
    IMPLEMENTS = "IMPLEMENTS"
    IMPORTS = "IMPORTS"
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    OVERRIDES = "OVERRIDES"
    USES = "USES"
    DEFINES = "DEFINES"


class NodeLabel(str, Enum):
    """Node labels for different code entities"""

    PROJECT = "Project"
    FILE = "File"
    PACKAGE = "Package"
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    METHOD = "Method"
    VARIABLE = "Variable"
    CONSTANT = "Constant"


class GraphNode(BaseModel):
    """Base graph node model"""

    id: str = Field(..., description="Unique identifier for the node")
    label: NodeLabel = Field(..., description="Node type/label")
    name: str = Field(..., description="Display name of the entity")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Additional properties"
    )

    def to_cypher_properties(self) -> str:
        """Convert properties to Cypher format"""
        props = {"id": self.id, "name": self.name, **self.properties}

        cypher_props = []
        for key, value in props.items():
            if isinstance(value, str):
                cypher_props.append(f'{key}: "{value}"')
            elif isinstance(value, (int, float)):
                cypher_props.append(f"{key}: {value}")
            elif isinstance(value, bool):
                cypher_props.append(f"{key}: {str(value).lower()}")
            elif isinstance(value, datetime):
                cypher_props.append(f'{key}: datetime("{value.isoformat()}")')
            elif value is not None:
                cypher_props.append(f'{key}: "{str(value)}"')

        return "{" + ", ".join(cypher_props) + "}"


class ProjectNode(GraphNode):
    """Project node in the graph"""

    label: NodeLabel = NodeLabel.PROJECT
    workspace_path: str = Field(..., description="Project workspace path")
    technology_stack: List[str] = Field(default_factory=list)
    total_files: int = Field(default=0)
    total_symbols: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)

    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update(
            {
                "workspace_path": self.workspace_path,
                "technology_stack": self.technology_stack,
                "total_files": self.total_files,
                "total_symbols": self.total_symbols,
                "created_at": self.created_at,
            }
        )


class FileNode(GraphNode):
    """File node in the graph"""

    label: NodeLabel = NodeLabel.FILE
    file_path: str = Field(..., description="Relative file path")
    language: LanguageType = Field(..., description="Programming language")
    lines_of_code: int = Field(default=0)
    complexity: float = Field(default=0.0)
    last_modified: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update(
            {
                "file_path": self.file_path,
                "language": str(self.language),
                "lines_of_code": self.lines_of_code,
                "complexity": self.complexity,
                "last_modified": self.last_modified,
            }
        )


class SymbolNode(GraphNode):
    """Symbol node (function, class, etc.) in the graph"""

    symbol_type: SymbolType = Field(..., description="Type of symbol")
    file_path: str = Field(..., description="File containing the symbol")
    line_start: int = Field(..., description="Starting line number")
    line_end: int = Field(..., description="Ending line number")
    visibility: Optional[str] = None
    complexity: float = Field(default=0.0)
    parameters: List[str] = Field(default_factory=list)
    return_type: Optional[str] = None

    def __init__(self, **data):
        # Set appropriate label based on symbol type before calling super().__init__
        symbol_type = data.get("symbol_type")
        if symbol_type:
            label_mapping = {
                SymbolType.CLASS: NodeLabel.CLASS,
                SymbolType.FUNCTION: NodeLabel.FUNCTION,
                SymbolType.METHOD: NodeLabel.METHOD,
                SymbolType.VARIABLE: NodeLabel.VARIABLE,
                SymbolType.CONSTANT: NodeLabel.CONSTANT,
                SymbolType.MODULE: NodeLabel.MODULE,
                SymbolType.PROPERTY: NodeLabel.VARIABLE,  # Map property to variable
            }
            data["label"] = label_mapping.get(symbol_type, NodeLabel.FUNCTION)

        super().__init__(**data)

        self.properties.update(
            {
                "symbol_type": str(self.symbol_type),
                "file_path": self.file_path,
                "line_start": self.line_start,
                "line_end": self.line_end,
                "visibility": self.visibility,
                "complexity": self.complexity,
                "parameters": self.parameters,
                "return_type": self.return_type,
            }
        )


class GraphRelationship(BaseModel):
    """Graph relationship model"""

    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Relationship properties"
    )
    strength: float = Field(
        default=1.0, description="Relationship strength (0.0 to 1.0)"
    )

    def to_cypher_properties(self) -> str:
        """Convert properties to Cypher format"""
        props = {"strength": self.strength, **self.properties}

        cypher_props = []
        for key, value in props.items():
            if isinstance(value, str):
                cypher_props.append(f'{key}: "{value}"')
            elif isinstance(value, (int, float)):
                cypher_props.append(f"{key}: {value}")
            elif isinstance(value, bool):
                cypher_props.append(f"{key}: {str(value).lower()}")
            elif value is not None:
                cypher_props.append(f'{key}: "{str(value)}"')

        return "{" + ", ".join(cypher_props) + "}" if cypher_props else ""


class DependencyRelationship(GraphRelationship):
    """Dependency relationship between modules/files"""

    relationship_type: RelationshipType = RelationshipType.DEPENDS_ON
    import_type: Optional[str] = None  # "import", "from_import", "require"

    def __init__(self, **data):
        super().__init__(**data)
        if self.import_type:
            self.properties["import_type"] = self.import_type


class CallRelationship(GraphRelationship):
    """Function/method call relationship"""

    relationship_type: RelationshipType = RelationshipType.CALLS
    call_count: int = Field(default=1, description="Number of times called")
    call_context: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update(
            {"call_count": self.call_count, "call_context": self.call_context}
        )


class InheritanceRelationship(GraphRelationship):
    """Class inheritance relationship"""

    relationship_type: RelationshipType = RelationshipType.INHERITS_FROM
    inheritance_type: Optional[str] = None  # "extends", "implements"

    def __init__(self, **data):
        super().__init__(**data)
        if self.inheritance_type:
            self.properties["inheritance_type"] = self.inheritance_type


class GraphQuery(BaseModel):
    """Graph query model for complex queries"""

    query_type: str = Field(..., description="Type of query")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: Optional[int] = None

    class Config:
        extra = "allow"


class ArchitecturePattern(BaseModel):
    """Detected architecture pattern"""

    pattern_name: str = Field(..., description="Name of the pattern")
    confidence: float = Field(..., description="Confidence in detection (0.0 to 1.0)")
    components: List[str] = Field(
        default_factory=list, description="Components involved"
    )
    description: str = Field(..., description="Pattern description")
    relationships: List[str] = Field(
        default_factory=list, description="Key relationships"
    )


class ImpactAnalysisResult(BaseModel):
    """Result of impact analysis"""

    target_entity: str = Field(..., description="Entity being analyzed")
    directly_affected: List[str] = Field(default_factory=list)
    indirectly_affected: List[str] = Field(default_factory=list)
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    affected_components: Dict[str, int] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class GraphStatistics(BaseModel):
    """Graph database statistics"""

    total_nodes: int = Field(default=0)
    total_relationships: int = Field(default=0)
    node_counts: Dict[str, int] = Field(default_factory=dict)
    relationship_counts: Dict[str, int] = Field(default_factory=dict)
    graph_density: float = Field(default=0.0)
    clustering_coefficient: float = Field(default=0.0)
    average_degree: float = Field(default=0.0)
    connected_components: int = Field(default=0)


class GraphVisualizationData(BaseModel):
    """Data for graph visualization"""

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    layout: str = Field(default="force-directed")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_mermaid(self) -> str:
        """Convert to Mermaid diagram format"""
        lines = ["graph TD"]

        # Add nodes
        for node in self.nodes:
            node_id = node.get("id", "")
            node_label = node.get("name", node_id)
            node_type = node.get("label", "")

            # Format based on node type
            if node_type == "Class":
                lines.append(f'    {node_id}["{node_label}"]')
                lines.append(f"    class {node_id} classNode")
            elif node_type in ["Function", "Method"]:
                lines.append(f'    {node_id}(("{node_label}"))')
                lines.append(f"    class {node_id} functionNode")
            elif node_type == "File":
                lines.append(f'    {node_id}["{node_label}"]')
                lines.append(f"    class {node_id} fileNode")
            else:
                lines.append(f'    {node_id}["{node_label}"]')

        # Add edges
        for edge in self.edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            relationship = edge.get("type", "")

            if relationship == "CALLS":
                lines.append(f"    {source} --> {target}")
            elif relationship == "INHERITS_FROM":
                lines.append(f"    {source} -.-> {target}")
            elif relationship == "DEPENDS_ON":
                lines.append(f"    {source} --> {target}")
            else:
                lines.append(f"    {source} --- {target}")

        # Add styling
        lines.extend(
            [
                "",
                "    classDef classNode fill:#e1f5fe,stroke:#0277bd,stroke-width:2px",
                "    classDef functionNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px",
                "    classDef fileNode fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px",
            ]
        )

        return "\n".join(lines)
