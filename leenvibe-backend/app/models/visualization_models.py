"""
Visualization Models for Advanced Diagram Generation

Pydantic models for representing different types of diagrams and visualization configurations.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class DiagramType(str, Enum):
    """Types of diagrams that can be generated"""
    ARCHITECTURE_OVERVIEW = "architecture_overview"
    DEPENDENCY_GRAPH = "dependency_graph"
    CALL_FLOW = "call_flow"
    COMPONENT_DIAGRAM = "component_diagram"
    HOTSPOT_HEATMAP = "hotspot_heatmap"
    CIRCULAR_DEPENDENCIES = "circular_dependencies"
    COUPLING_ANALYSIS = "coupling_analysis"
    CLASS_HIERARCHY = "class_hierarchy"
    PACKAGE_STRUCTURE = "package_structure"


class DiagramTheme(str, Enum):
    """Visual themes for diagrams"""
    LIGHT = "light"
    DARK = "dark"
    NEUTRAL = "neutral"
    COLORFUL = "colorful"
    MONOCHROME = "monochrome"
    HIGH_CONTRAST = "high_contrast"


class DiagramLayout(str, Enum):
    """Layout directions for diagrams"""
    TOP_DOWN = "TD"
    LEFT_RIGHT = "LR"
    RIGHT_LEFT = "RL"
    BOTTOM_TOP = "BT"


class FilterOperator(str, Enum):
    """Filter operators for diagram filtering"""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"


class DiagramFilter(BaseModel):
    """Filter for diagram elements"""
    field: str = Field(..., description="Field to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")
    enabled: bool = Field(default=True, description="Whether filter is active")


class NodeStyle(BaseModel):
    """Styling configuration for diagram nodes"""
    shape: str = Field(default="rect", description="Node shape (rect, circle, diamond, etc.)")
    fill_color: Optional[str] = None
    stroke_color: Optional[str] = None
    stroke_width: Optional[int] = None
    text_color: Optional[str] = None
    font_size: Optional[int] = None
    border_radius: Optional[int] = None


class EdgeStyle(BaseModel):
    """Styling configuration for diagram edges"""
    stroke_color: Optional[str] = None
    stroke_width: Optional[int] = None
    stroke_style: str = Field(default="solid", description="solid, dashed, dotted")
    arrow_type: str = Field(default="arrow", description="arrow, diamond, circle, none")


class DiagramConfiguration(BaseModel):
    """Complete configuration for diagram generation"""
    diagram_type: DiagramType = Field(..., description="Type of diagram to generate")
    theme: DiagramTheme = Field(default=DiagramTheme.LIGHT, description="Visual theme")
    layout: DiagramLayout = Field(default=DiagramLayout.TOP_DOWN, description="Diagram layout")
    max_nodes: int = Field(default=100, description="Maximum number of nodes to display")
    max_depth: int = Field(default=5, description="Maximum depth for relationships")
    show_labels: bool = Field(default=True, description="Show node labels")
    show_details: bool = Field(default=False, description="Show detailed information")
    interactive: bool = Field(default=True, description="Enable interactive features")
    clustering: bool = Field(default=False, description="Enable node clustering")
    filters: List[DiagramFilter] = Field(default_factory=list, description="Active filters")
    custom_styles: Dict[str, NodeStyle] = Field(default_factory=dict, description="Custom node styles")
    edge_styles: Dict[str, EdgeStyle] = Field(default_factory=dict, description="Custom edge styles")


class DiagramNode(BaseModel):
    """Node in a diagram"""
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label")
    type: str = Field(..., description="Node type (class, function, file, etc.)")
    category: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    style: Optional[NodeStyle] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Position and size (for layout algorithms)
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    
    # Clustering information
    cluster_id: Optional[str] = None
    cluster_label: Optional[str] = None


class DiagramEdge(BaseModel):
    """Edge in a diagram"""
    id: str = Field(..., description="Unique edge identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    label: Optional[str] = None
    type: str = Field(..., description="Edge type (calls, depends, inherits, etc.)")
    weight: float = Field(default=1.0, description="Edge weight/strength")
    properties: Dict[str, Any] = Field(default_factory=dict)
    style: Optional[EdgeStyle] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InteractiveElement(BaseModel):
    """Interactive element in a diagram"""
    element_id: str = Field(..., description="ID of the element")
    element_type: str = Field(..., description="node or edge")
    actions: List[str] = Field(default_factory=list, description="Available actions")
    tooltip: Optional[str] = None
    click_handler: Optional[str] = None
    hover_handler: Optional[str] = None


class DiagramExportFormat(str, Enum):
    """Supported export formats"""
    MERMAID = "mermaid"
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    JSON = "json"
    GRAPHVIZ = "dot"


class DiagramData(BaseModel):
    """Complete diagram data structure"""
    id: str = Field(..., description="Unique diagram identifier")
    title: str = Field(..., description="Diagram title")
    description: Optional[str] = None
    configuration: DiagramConfiguration = Field(..., description="Diagram configuration")
    nodes: List[DiagramNode] = Field(default_factory=list, description="Diagram nodes")
    edges: List[DiagramEdge] = Field(default_factory=list, description="Diagram edges")
    interactive_elements: List[InteractiveElement] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_node_count(self) -> int:
        """Get total number of nodes"""
        return len(self.nodes)
    
    def get_edge_count(self) -> int:
        """Get total number of edges"""
        return len(self.edges)
    
    def get_nodes_by_type(self, node_type: str) -> List[DiagramNode]:
        """Get all nodes of a specific type"""
        return [node for node in self.nodes if node.type == node_type]
    
    def get_edges_by_type(self, edge_type: str) -> List[DiagramEdge]:
        """Get all edges of a specific type"""
        return [edge for edge in self.edges if edge.type == edge_type]


class MermaidDiagram(BaseModel):
    """Mermaid.js specific diagram representation"""
    diagram_type: str = Field(..., description="Mermaid diagram type")
    content: str = Field(..., description="Mermaid diagram content")
    theme: DiagramTheme = Field(default=DiagramTheme.LIGHT)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    custom_css: Optional[str] = None
    
    def get_full_content(self) -> str:
        """Get complete Mermaid content with configuration"""
        config_lines = []
        
        if self.configuration:
            config_lines.append("%%{init: " + str(self.configuration).replace("'", '"') + "}%%")
        
        content_lines = [
            *config_lines,
            self.content
        ]
        
        if self.custom_css:
            content_lines.extend([
                "",
                f"classDef default {self.custom_css}"
            ])
        
        return "\n".join(content_lines)


class DiagramGenerationRequest(BaseModel):
    """Request for diagram generation"""
    project_id: str = Field(..., description="Project identifier")
    configuration: DiagramConfiguration = Field(..., description="Diagram configuration")
    export_format: DiagramExportFormat = Field(default=DiagramExportFormat.MERMAID)
    include_metadata: bool = Field(default=True, description="Include metadata in response")
    cache_result: bool = Field(default=True, description="Cache the generated diagram")


class DiagramGenerationResponse(BaseModel):
    """Response from diagram generation"""
    diagram_id: str = Field(..., description="Generated diagram ID")
    diagram_data: Optional[DiagramData] = None
    mermaid_diagram: Optional[MermaidDiagram] = None
    export_content: Optional[str] = None
    generation_time_ms: int = Field(..., description="Generation time in milliseconds")
    node_count: int = Field(..., description="Number of nodes in diagram")
    edge_count: int = Field(..., description="Number of edges in diagram")
    warnings: List[str] = Field(default_factory=list, description="Generation warnings")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DiagramTemplate(BaseModel):
    """Template for creating diagrams"""
    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    diagram_type: DiagramType = Field(..., description="Target diagram type")
    default_configuration: DiagramConfiguration = Field(..., description="Default config")
    required_filters: List[str] = Field(default_factory=list, description="Required filters")
    supported_themes: List[DiagramTheme] = Field(default_factory=list)
    template_content: str = Field(..., description="Mermaid template content")
    placeholders: Dict[str, str] = Field(default_factory=dict, description="Template placeholders")


class VisualizationMetrics(BaseModel):
    """Metrics for visualization performance and usage"""
    diagram_id: str = Field(..., description="Diagram identifier")
    generation_time_ms: int = Field(..., description="Generation time")
    rendering_time_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    cache_hit: bool = Field(default=False)
    user_interactions: int = Field(default=0)
    export_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)


class DiagramCache(BaseModel):
    """Cache entry for generated diagrams"""
    cache_key: str = Field(..., description="Cache key")
    diagram_data: DiagramData = Field(..., description="Cached diagram data")
    mermaid_content: str = Field(..., description="Cached Mermaid content")
    generation_config: DiagramConfiguration = Field(..., description="Generation configuration")
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    access_count: int = Field(default=0)
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def update_access(self):
        """Update access statistics"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class VisualizationError(Exception):
    """Custom exception for visualization errors"""
    def __init__(self, message: str, error_code: str = "VISUALIZATION_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)