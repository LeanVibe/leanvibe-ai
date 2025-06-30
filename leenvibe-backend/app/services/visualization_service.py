"""
Advanced Mermaid.js Visualization Service

Generates interactive diagrams from code analysis data with support for multiple
diagram types, themes, and advanced visualization features.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Template

from ..models.visualization_models import (
    DiagramCache,
    DiagramConfiguration,
    DiagramData,
    DiagramEdge,
    DiagramGenerationRequest,
    DiagramGenerationResponse,
    DiagramNode,
    DiagramTheme,
    DiagramType,
    MermaidDiagram,
    VisualizationError,
    VisualizationMetrics,
)
from ..services.graph_query_service import graph_query_service
from ..services.graph_service import graph_service

logger = logging.getLogger(__name__)


class VisualizationService:
    """
    Advanced visualization service for generating interactive diagrams
    from code analysis data using Mermaid.js and custom rendering.
    """

    def __init__(self):
        self.cache: Dict[str, DiagramCache] = {}
        self.metrics: List[VisualizationMetrics] = []
        self.templates = self._load_diagram_templates()
        self.theme_configurations = self._load_theme_configurations()

        # Performance settings
        self.cache_ttl = 1800  # 30 minutes
        self.max_cache_size = 100
        self.max_nodes_per_diagram = 200
        self.max_edges_per_diagram = 500

    def _load_diagram_templates(self) -> Dict[str, str]:
        """Load Mermaid diagram templates"""
        return {
            DiagramType.ARCHITECTURE_OVERVIEW: """
graph {{ layout }}
{% for node in nodes %}
    {{ node.id }}[{{ node.label }}]
    {% if node.style %}class {{ node.id }} {{ node.style }}{% endif %}
{% endfor %}

{% for edge in edges %}
    {{ edge.source_id }} {{ edge.connector }} {{ edge.target_id }}
    {% if edge.label %}: {{ edge.label }}{% endif %}
{% endfor %}

{% for style_class, style_def in styles.items() %}
    classDef {{ style_class }} {{ style_def }}
{% endfor %}
""",
            DiagramType.DEPENDENCY_GRAPH: """
graph {{ layout }}
{% for node in nodes %}
    {{ node.id }}[{{ node.label }}]
    {% if node.type == 'file' %}class {{ node.id }} fileNode{% endif %}
    {% if node.type == 'module' %}class {{ node.id }} moduleNode{% endif %}
    {% if node.type == 'external' %}class {{ node.id }} externalNode{% endif %}
{% endfor %}

{% for edge in edges %}
    {{ edge.source_id }} --> {{ edge.target_id }}
    {% if edge.label %}: {{ edge.label }}{% endif %}
{% endfor %}

    classDef fileNode fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef moduleNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef externalNode fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
""",
            DiagramType.CALL_FLOW: """
sequenceDiagram
{% for participant in participants %}
    participant {{ participant.id }} as {{ participant.label }}
{% endfor %}

{% for call in calls %}
    {{ call.caller }} ->> {{ call.callee }}: {{ call.method }}
    {% if call.return_value %}{{ call.callee }} -->> {{ call.caller }}: {{ call.return_value }}{% endif %}
{% endfor %}
""",
            DiagramType.CLASS_HIERARCHY: """
classDiagram
{% for class in classes %}
    class {{ class.id }} {
        {% for method in class.methods %}
        {{ method.visibility }}{{ method.name }}({{ method.parameters }}) {{ method.return_type }}
        {% endfor %}
        {% for property in class.properties %}
        {{ property.visibility }}{{ property.name }} : {{ property.type }}
        {% endfor %}
    }
    {% if class.parent %}{{ class.parent }} <|-- {{ class.id }}{% endif %}
    {% for interface in class.interfaces %}{{ interface }} <|.. {{ class.id }}{% endfor %}
{% endfor %}

{% for relationship in relationships %}
    {{ relationship.source }} {{ relationship.type }} {{ relationship.target }}
{% endfor %}
""",
            DiagramType.COMPONENT_DIAGRAM: """
graph {{ layout }}
{% for component in components %}
    subgraph {{ component.id }}["{{ component.label }}"]
    {% for subcomponent in component.children %}
        {{ subcomponent.id }}[{{ subcomponent.label }}]
    {% endfor %}
    end
{% endfor %}

{% for edge in edges %}
    {{ edge.source_id }} {{ edge.connector }} {{ edge.target_id }}
{% endfor %}
""",
            DiagramType.HOTSPOT_HEATMAP: """
graph {{ layout }}
{% for node in nodes %}
    {{ node.id }}[{{ node.label }}]
    {% if node.metadata.risk_level == 'high' %}class {{ node.id }} hotspotHigh{% endif %}
    {% if node.metadata.risk_level == 'medium' %}class {{ node.id }} hotspotMedium{% endif %}
    {% if node.metadata.risk_level == 'low' %}class {{ node.id }} hotspotLow{% endif %}
{% endfor %}

{% for edge in edges %}
    {{ edge.source_id }} --> {{ edge.target_id }}
{% endfor %}

    classDef hotspotHigh fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef hotspotMedium fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef hotspotLow fill:#e8f5e8,stroke:#388e3c,stroke-width:1px
""",
        }

    def _load_theme_configurations(self) -> Dict[DiagramTheme, Dict[str, Any]]:
        """Load theme configurations for different visual styles"""
        return {
            DiagramTheme.LIGHT: {
                "theme": "default",
                "primaryColor": "#0066cc",
                "primaryTextColor": "#333333",
                "primaryBorderColor": "#0066cc",
                "lineColor": "#666666",
                "secondaryColor": "#f5f5f5",
                "tertiaryColor": "#ffffff",
            },
            DiagramTheme.DARK: {
                "theme": "dark",
                "primaryColor": "#4fc3f7",
                "primaryTextColor": "#ffffff",
                "primaryBorderColor": "#4fc3f7",
                "lineColor": "#cccccc",
                "secondaryColor": "#424242",
                "tertiaryColor": "#212121",
            },
            DiagramTheme.NEUTRAL: {
                "theme": "neutral",
                "primaryColor": "#666666",
                "primaryTextColor": "#333333",
                "primaryBorderColor": "#999999",
                "lineColor": "#666666",
                "secondaryColor": "#f0f0f0",
                "tertiaryColor": "#ffffff",
            },
            DiagramTheme.COLORFUL: {
                "theme": "default",
                "primaryColor": "#e91e63",
                "primaryTextColor": "#333333",
                "primaryBorderColor": "#e91e63",
                "lineColor": "#666666",
                "secondaryColor": "#f8bbd9",
                "tertiaryColor": "#ffffff",
            },
        }

    async def generate_diagram(
        self, request: DiagramGenerationRequest
    ) -> DiagramGenerationResponse:
        """Generate a diagram based on the request configuration"""
        start_time = time.time()

        try:
            logger.info(
                f"Generating {request.configuration.diagram_type} diagram for project {request.project_id}"
            )

            # Check cache first
            cache_key = self._generate_cache_key(request)
            if request.cache_result and cache_key in self.cache:
                cached_diagram = self.cache[cache_key]
                if not cached_diagram.is_expired():
                    cached_diagram.update_access()
                    logger.debug(f"Returning cached diagram: {cache_key}")

                    return DiagramGenerationResponse(
                        diagram_id=cache_key,
                        diagram_data=cached_diagram.diagram_data,
                        mermaid_diagram=MermaidDiagram(
                            diagram_type=request.configuration.diagram_type,
                            content=cached_diagram.mermaid_content,
                            theme=request.configuration.theme,
                        ),
                        generation_time_ms=int((time.time() - start_time) * 1000),
                        node_count=cached_diagram.diagram_data.get_node_count(),
                        edge_count=cached_diagram.diagram_data.get_edge_count(),
                        metadata={"cache_hit": True},
                    )

            # Generate new diagram
            diagram_data = await self._create_diagram_data(request)
            mermaid_content = await self._generate_mermaid_content(
                diagram_data, request.configuration
            )

            # Create Mermaid diagram
            mermaid_diagram = MermaidDiagram(
                diagram_type=request.configuration.diagram_type,
                content=mermaid_content,
                theme=request.configuration.theme,
                configuration=self.theme_configurations.get(
                    request.configuration.theme, {}
                ),
            )

            # Cache if requested
            if request.cache_result:
                await self._cache_diagram(
                    cache_key, diagram_data, mermaid_content, request.configuration
                )

            generation_time = int((time.time() - start_time) * 1000)

            # Record metrics
            metrics = VisualizationMetrics(
                diagram_id=cache_key,
                generation_time_ms=generation_time,
                cache_hit=False,
            )
            self.metrics.append(metrics)

            response = DiagramGenerationResponse(
                diagram_id=cache_key,
                diagram_data=diagram_data if request.include_metadata else None,
                mermaid_diagram=mermaid_diagram,
                generation_time_ms=generation_time,
                node_count=diagram_data.get_node_count(),
                edge_count=diagram_data.get_edge_count(),
            )

            logger.info(
                f"Generated diagram in {generation_time}ms: {diagram_data.get_node_count()} nodes, {diagram_data.get_edge_count()} edges"
            )
            return response

        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            raise VisualizationError(
                f"Failed to generate diagram: {str(e)}", "GENERATION_ERROR"
            )

    async def _create_diagram_data(
        self, request: DiagramGenerationRequest
    ) -> DiagramData:
        """Create diagram data based on the request type"""
        config = request.configuration
        project_id = request.project_id

        if config.diagram_type == DiagramType.ARCHITECTURE_OVERVIEW:
            return await self._create_architecture_diagram(project_id, config)
        elif config.diagram_type == DiagramType.DEPENDENCY_GRAPH:
            return await self._create_dependency_diagram(project_id, config)
        elif config.diagram_type == DiagramType.CALL_FLOW:
            return await self._create_call_flow_diagram(project_id, config)
        elif config.diagram_type == DiagramType.CLASS_HIERARCHY:
            return await self._create_class_hierarchy_diagram(project_id, config)
        elif config.diagram_type == DiagramType.COMPONENT_DIAGRAM:
            return await self._create_component_diagram(project_id, config)
        elif config.diagram_type == DiagramType.HOTSPOT_HEATMAP:
            return await self._create_hotspot_diagram(project_id, config)
        elif config.diagram_type == DiagramType.CIRCULAR_DEPENDENCIES:
            return await self._create_circular_deps_diagram(project_id, config)
        elif config.diagram_type == DiagramType.COUPLING_ANALYSIS:
            return await self._create_coupling_diagram(project_id, config)
        else:
            raise VisualizationError(f"Unsupported diagram type: {config.diagram_type}")

    async def _create_architecture_diagram(
        self, project_id: str, config: DiagramConfiguration
    ) -> DiagramData:
        """Create architecture overview diagram"""
        try:
            # Get architecture patterns
            patterns = await graph_service.get_architecture_patterns(project_id)

            # Get project visualization data
            viz_data = await graph_service.get_visualization_data(
                project_id, max_nodes=config.max_nodes
            )

            nodes = []
            edges = []

            # Convert visualization data to diagram format
            for node_data in viz_data.nodes[: config.max_nodes]:
                node = DiagramNode(
                    id=self._sanitize_id(node_data["id"]),
                    label=node_data["name"],
                    type=node_data.get("label", "component"),
                    properties=node_data,
                    metadata={"original_id": node_data["id"]},
                )
                nodes.append(node)

            for edge_data in viz_data.edges[: config.max_edges_per_diagram]:
                if edge_data["source"] in [
                    n.metadata["original_id"] for n in nodes
                ] and edge_data["target"] in [n.metadata["original_id"] for n in nodes]:
                    edge = DiagramEdge(
                        id=f"{self._sanitize_id(edge_data['source'])}_{self._sanitize_id(edge_data['target'])}",
                        source_id=self._sanitize_id(edge_data["source"]),
                        target_id=self._sanitize_id(edge_data["target"]),
                        type=edge_data.get("type", "relation"),
                        properties=edge_data,
                    )
                    edges.append(edge)

            diagram_data = DiagramData(
                id=f"arch_{project_id}",
                title="Architecture Overview",
                description="High-level architecture overview showing components and relationships",
                configuration=config,
                nodes=nodes,
                edges=edges,
                metadata={
                    "patterns": [p.pattern_name for p in patterns],
                    "project_id": project_id,
                },
            )

            return diagram_data

        except Exception as e:
            logger.error(f"Error creating architecture diagram: {e}")
            # Return minimal diagram on error
            return DiagramData(
                id=f"arch_{project_id}",
                title="Architecture Overview",
                configuration=config,
                nodes=[
                    DiagramNode(
                        id="error", label="Error loading architecture", type="error"
                    )
                ],
                edges=[],
            )

    async def _create_dependency_diagram(
        self, project_id: str, config: DiagramConfiguration
    ) -> DiagramData:
        """Create dependency graph diagram"""
        try:
            viz_data = await graph_service.get_visualization_data(
                project_id, max_nodes=config.max_nodes
            )

            nodes = []
            edges = []

            # Focus on dependency relationships
            for node_data in viz_data.nodes:
                node_type = (
                    "external"
                    if "external" in node_data.get("label", "").lower()
                    else "file"
                )
                node = DiagramNode(
                    id=self._sanitize_id(node_data["id"]),
                    label=(
                        Path(node_data["name"]).stem
                        if node_type == "file"
                        else node_data["name"]
                    ),
                    type=node_type,
                    properties=node_data,
                    metadata={"full_path": node_data["name"]},
                )
                nodes.append(node)

            # Filter for dependency edges
            for edge_data in viz_data.edges:
                if edge_data.get("type") in ["DEPENDS_ON", "IMPORTS"]:
                    edge = DiagramEdge(
                        id=f"dep_{self._sanitize_id(edge_data['source'])}_{self._sanitize_id(edge_data['target'])}",
                        source_id=self._sanitize_id(edge_data["source"]),
                        target_id=self._sanitize_id(edge_data["target"]),
                        type="dependency",
                        label=edge_data.get("type", ""),
                        properties=edge_data,
                    )
                    edges.append(edge)

            return DiagramData(
                id=f"deps_{project_id}",
                title="Dependency Graph",
                description="File and module dependencies",
                configuration=config,
                nodes=nodes,
                edges=edges,
            )

        except Exception as e:
            logger.error(f"Error creating dependency diagram: {e}")
            return DiagramData(
                id=f"deps_{project_id}",
                title="Dependency Graph",
                configuration=config,
                nodes=[],
                edges=[],
            )

    async def _create_hotspot_diagram(
        self, project_id: str, config: DiagramConfiguration
    ) -> DiagramData:
        """Create hotspot heatmap diagram"""
        try:
            # Get hotspots from graph query service
            hotspots = await graph_query_service.find_hotspots(project_id)

            nodes = []
            edges = []

            for hotspot in hotspots[: config.max_nodes]:
                risk_level = hotspot.get("risk_level", "low")
                node = DiagramNode(
                    id=self._sanitize_id(hotspot["symbol_name"]),
                    label=hotspot["symbol_name"],
                    type="hotspot",
                    properties=hotspot,
                    metadata={
                        "risk_level": risk_level,
                        "connection_count": hotspot.get("connection_count", 0),
                    },
                )
                nodes.append(node)

            return DiagramData(
                id=f"hotspots_{project_id}",
                title="Code Hotspots",
                description="Highly connected and critical code components",
                configuration=config,
                nodes=nodes,
                edges=edges,
            )

        except Exception as e:
            logger.error(f"Error creating hotspot diagram: {e}")
            return DiagramData(
                id=f"hotspots_{project_id}",
                title="Code Hotspots",
                configuration=config,
                nodes=[],
                edges=[],
            )

    async def _create_circular_deps_diagram(
        self, project_id: str, config: DiagramConfiguration
    ) -> DiagramData:
        """Create circular dependencies diagram"""
        try:
            cycles = await graph_query_service.find_circular_dependencies(project_id)

            nodes = []
            edges = []
            node_ids = set()

            for i, cycle in enumerate(cycles[:10]):  # Limit to 10 cycles
                for j, file_name in enumerate(cycle):
                    node_id = self._sanitize_id(file_name)
                    if node_id not in node_ids:
                        node = DiagramNode(
                            id=node_id,
                            label=Path(file_name).stem,
                            type="file",
                            properties={"file_name": file_name},
                            metadata={"cycle_id": i, "in_cycle": True},
                        )
                        nodes.append(node)
                        node_ids.add(node_id)

                    # Create edge to next node in cycle
                    next_file = cycle[(j + 1) % len(cycle)]
                    edge = DiagramEdge(
                        id=f"cycle_{i}_{j}",
                        source_id=node_id,
                        target_id=self._sanitize_id(next_file),
                        type="circular_dependency",
                        properties={"cycle_id": i},
                    )
                    edges.append(edge)

            return DiagramData(
                id=f"circular_{project_id}",
                title="Circular Dependencies",
                description="Files with circular dependency relationships",
                configuration=config,
                nodes=nodes,
                edges=edges,
            )

        except Exception as e:
            logger.error(f"Error creating circular dependencies diagram: {e}")
            return DiagramData(
                id=f"circular_{project_id}",
                title="Circular Dependencies",
                configuration=config,
                nodes=[],
                edges=[],
            )

    async def _create_coupling_diagram(
        self, project_id: str, config: DiagramConfiguration
    ) -> DiagramData:
        """Create coupling analysis diagram"""
        try:
            coupling_data = await graph_query_service.analyze_coupling(project_id)

            nodes = []
            edges = []

            high_coupling_files = coupling_data.get("highly_coupled_files", [])

            for file_info in high_coupling_files[: config.max_nodes]:
                coupling_level = (
                    "high"
                    if file_info["total_coupling"] > 10
                    else "medium" if file_info["total_coupling"] > 5 else "low"
                )

                node = DiagramNode(
                    id=self._sanitize_id(file_info["file_name"]),
                    label=Path(file_info["file_name"]).stem,
                    type="file",
                    properties=file_info,
                    metadata={
                        "coupling_level": coupling_level,
                        "total_coupling": file_info["total_coupling"],
                    },
                )
                nodes.append(node)

            return DiagramData(
                id=f"coupling_{project_id}",
                title="Coupling Analysis",
                description="Component coupling and dependency strength",
                configuration=config,
                nodes=nodes,
                edges=edges,
            )

        except Exception as e:
            logger.error(f"Error creating coupling diagram: {e}")
            return DiagramData(
                id=f"coupling_{project_id}",
                title="Coupling Analysis",
                configuration=config,
                nodes=[],
                edges=[],
            )

    async def _create_class_hierarchy_diagram(
        self, project_id: str, config: DiagramConfiguration
    ) -> DiagramData:
        """Create class hierarchy diagram"""
        # Placeholder implementation - would need enhanced AST analysis
        return DiagramData(
            id=f"classes_{project_id}",
            title="Class Hierarchy",
            description="Class inheritance and relationships",
            configuration=config,
            nodes=[
                DiagramNode(
                    id="placeholder",
                    label="Class hierarchy analysis coming soon",
                    type="placeholder",
                )
            ],
            edges=[],
        )

    async def _create_component_diagram(
        self, project_id: str, config: DiagramConfiguration
    ) -> DiagramData:
        """Create component diagram"""
        # Placeholder implementation - would group by directory structure
        return DiagramData(
            id=f"components_{project_id}",
            title="Component Diagram",
            description="System components and their relationships",
            configuration=config,
            nodes=[
                DiagramNode(
                    id="placeholder",
                    label="Component analysis coming soon",
                    type="placeholder",
                )
            ],
            edges=[],
        )

    async def _create_call_flow_diagram(
        self, project_id: str, config: DiagramConfiguration
    ) -> DiagramData:
        """Create call flow diagram"""
        # Placeholder implementation - would need call graph analysis
        return DiagramData(
            id=f"callflow_{project_id}",
            title="Call Flow",
            description="Function call sequences and execution flow",
            configuration=config,
            nodes=[
                DiagramNode(
                    id="placeholder",
                    label="Call flow analysis coming soon",
                    type="placeholder",
                )
            ],
            edges=[],
        )

    async def _generate_mermaid_content(
        self, diagram_data: DiagramData, config: DiagramConfiguration
    ) -> str:
        """Generate Mermaid.js content from diagram data"""
        try:
            template_str = self.templates.get(config.diagram_type)
            if not template_str:
                raise VisualizationError(
                    f"No template found for diagram type: {config.diagram_type}"
                )

            template = Template(template_str)

            # Prepare template variables
            template_vars = {
                "layout": config.layout,
                "nodes": diagram_data.nodes,
                "edges": self._prepare_edges_for_template(diagram_data.edges, config),
                "styles": self._generate_style_classes(diagram_data, config),
                "theme": config.theme,
            }

            # Add diagram-specific variables
            if config.diagram_type == DiagramType.CLASS_HIERARCHY:
                template_vars.update(
                    {
                        "classes": self._group_nodes_as_classes(diagram_data.nodes),
                        "relationships": diagram_data.edges,
                    }
                )
            elif config.diagram_type == DiagramType.COMPONENT_DIAGRAM:
                template_vars.update(
                    {"components": self._group_nodes_as_components(diagram_data.nodes)}
                )
            elif config.diagram_type == DiagramType.CALL_FLOW:
                template_vars.update(
                    {"participants": diagram_data.nodes, "calls": diagram_data.edges}
                )

            content = template.render(**template_vars)
            return content.strip()

        except Exception as e:
            logger.error(f"Error generating Mermaid content: {e}")
            return f'graph TD\n    Error["Error generating diagram: {str(e)}"]'

    def _prepare_edges_for_template(
        self, edges: List[DiagramEdge], config: DiagramConfiguration
    ) -> List[Dict[str, Any]]:
        """Prepare edges for template rendering"""
        prepared_edges = []

        for edge in edges:
            connector = self._get_edge_connector(edge.type, config.diagram_type)

            prepared_edge = {
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "connector": connector,
                "label": edge.label,
                "type": edge.type,
                "properties": edge.properties,
            }
            prepared_edges.append(prepared_edge)

        return prepared_edges

    def _get_edge_connector(self, edge_type: str, diagram_type: DiagramType) -> str:
        """Get appropriate Mermaid connector for edge type"""
        connectors = {
            "dependency": "-->",
            "calls": "-->",
            "inherits": "-.->",
            "implements": "-.->",
            "uses": "-->",
            "contains": "-->",
            "circular_dependency": "-.->",
            "relation": "---",
        }

        return connectors.get(edge_type, "-->")

    def _generate_style_classes(
        self, diagram_data: DiagramData, config: DiagramConfiguration
    ) -> Dict[str, str]:
        """Generate CSS style classes for diagram elements"""
        styles = {}

        # Theme-based base styles
        if config.theme == DiagramTheme.DARK:
            styles["default"] = (
                "fill:#424242,stroke:#4fc3f7,stroke-width:2px,color:#ffffff"
            )
        elif config.theme == DiagramTheme.LIGHT:
            styles["default"] = (
                "fill:#f5f5f5,stroke:#0066cc,stroke-width:2px,color:#333333"
            )

        # Type-specific styles
        if config.diagram_type == DiagramType.HOTSPOT_HEATMAP:
            styles.update(
                {
                    "hotspotHigh": "fill:#ffcdd2,stroke:#d32f2f,stroke-width:3px",
                    "hotspotMedium": "fill:#fff3e0,stroke:#f57c00,stroke-width:2px",
                    "hotspotLow": "fill:#e8f5e8,stroke:#388e3c,stroke-width:1px",
                }
            )

        return styles

    def _group_nodes_as_classes(self, nodes: List[DiagramNode]) -> List[Dict[str, Any]]:
        """Group nodes as class definitions for class diagrams"""
        # Placeholder implementation
        return []

    def _group_nodes_as_components(
        self, nodes: List[DiagramNode]
    ) -> List[Dict[str, Any]]:
        """Group nodes as components for component diagrams"""
        # Placeholder implementation
        return []

    def _sanitize_id(self, id_str: str) -> str:
        """Sanitize ID for Mermaid compatibility"""
        # Remove or replace characters that cause issues in Mermaid
        sanitized = (
            id_str.replace("/", "_")
            .replace(".", "_")
            .replace("-", "_")
            .replace(" ", "_")
        )
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"id_{sanitized}"
        return sanitized or "unknown"

    def _generate_cache_key(self, request: DiagramGenerationRequest) -> str:
        """Generate cache key for diagram request"""
        key_data = {
            "project_id": request.project_id,
            "diagram_type": request.configuration.diagram_type,
            "theme": request.configuration.theme,
            "layout": request.configuration.layout,
            "max_nodes": request.configuration.max_nodes,
            "filters": [f.__dict__ for f in request.configuration.filters],
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def _cache_diagram(
        self,
        cache_key: str,
        diagram_data: DiagramData,
        mermaid_content: str,
        config: DiagramConfiguration,
    ):
        """Cache generated diagram"""
        try:
            # Clean old cache entries if needed
            if len(self.cache) >= self.max_cache_size:
                await self._cleanup_cache()

            cache_entry = DiagramCache(
                cache_key=cache_key,
                diagram_data=diagram_data,
                mermaid_content=mermaid_content,
                generation_config=config,
                expires_at=datetime.now() + timedelta(seconds=self.cache_ttl),
            )

            self.cache[cache_key] = cache_entry
            logger.debug(f"Cached diagram: {cache_key}")

        except Exception as e:
            logger.error(f"Error caching diagram: {e}")

    async def _cleanup_cache(self):
        """Clean up expired cache entries"""
        try:
            datetime.now()
            expired_keys = [
                key for key, entry in self.cache.items() if entry.is_expired()
            ]

            for key in expired_keys:
                del self.cache[key]

            # If still too many entries, remove least recently used
            if len(self.cache) >= self.max_cache_size:
                sorted_entries = sorted(
                    self.cache.items(), key=lambda x: x[1].last_accessed
                )

                for key, _ in sorted_entries[
                    : len(self.cache) - self.max_cache_size + 10
                ]:
                    del self.cache[key]

            logger.debug(f"Cache cleanup completed. Current size: {len(self.cache)}")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    async def get_diagram_types(self) -> List[Dict[str, Any]]:
        """Get available diagram types with descriptions"""
        return [
            {
                "type": DiagramType.ARCHITECTURE_OVERVIEW,
                "name": "Architecture Overview",
                "description": "High-level view of system components and relationships",
                "supported_layouts": ["TD", "LR"],
                "max_recommended_nodes": 50,
            },
            {
                "type": DiagramType.DEPENDENCY_GRAPH,
                "name": "Dependency Graph",
                "description": "File and module dependencies with import relationships",
                "supported_layouts": ["TD", "LR"],
                "max_recommended_nodes": 100,
            },
            {
                "type": DiagramType.HOTSPOT_HEATMAP,
                "name": "Code Hotspots",
                "description": "Highly connected and critical code components",
                "supported_layouts": ["TD"],
                "max_recommended_nodes": 30,
            },
            {
                "type": DiagramType.CIRCULAR_DEPENDENCIES,
                "name": "Circular Dependencies",
                "description": "Files with circular dependency relationships",
                "supported_layouts": ["TD", "LR"],
                "max_recommended_nodes": 20,
            },
            {
                "type": DiagramType.COUPLING_ANALYSIS,
                "name": "Coupling Analysis",
                "description": "Component coupling and dependency strength analysis",
                "supported_layouts": ["TD"],
                "max_recommended_nodes": 25,
            },
        ]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_access_count = sum(entry.access_count for entry in self.cache.values())

        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.max_cache_size,
            "total_access_count": total_access_count,
            "cache_hit_rate": len([m for m in self.metrics if m.cache_hit])
            / max(len(self.metrics), 1),
            "average_generation_time": sum(m.generation_time_ms for m in self.metrics)
            / max(len(self.metrics), 1),
        }


# Global instance
visualization_service = VisualizationService()
