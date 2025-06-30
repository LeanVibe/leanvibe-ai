"""
Visualization & Diagram Service

Extracted from enhanced_l3_agent.py to provide focused project visualization,
diagram generation, and export capabilities following single responsibility principle.
"""

import logging
from typing import Any, Dict, List, Optional

from ..models.visualization_models import (
    DiagramConfiguration,
    DiagramExportFormat,
    DiagramGenerationRequest,
    DiagramLayout,
    DiagramTheme,
    DiagramType,
)
from .graph_service import graph_service
from .visualization_service import visualization_service

logger = logging.getLogger(__name__)


class VisualizationDiagramService:
    """
    Service dedicated to project visualization and diagram generation.
    
    Provides graph visualization, interactive diagram generation, multiple export formats,
    and comprehensive diagram type support for project analysis.
    """
    
    def __init__(self):
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the visualization diagram service"""
        try:
            # Ensure dependencies are initialized
            if not graph_service.initialized:
                await graph_service.initialize()
            
            if hasattr(visualization_service, 'initialize') and not getattr(visualization_service, 'initialized', True):
                await visualization_service.initialize()
            
            self._initialized = True
            logger.info("Visualization Diagram Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Visualization Diagram Service: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided by this service"""
        return [
            "graph_visualization",
            "interactive_diagrams",
            "multiple_diagram_types",
            "mermaid_generation",
            "architecture_overview",
            "dependency_graphs",
            "hotspot_heatmaps",
            "coupling_analysis_diagrams",
            "circular_dependency_visualization",
            "export_formats"
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service"""
        return {
            "service": "visualization_diagram",
            "initialized": self._initialized,
            "graph_service_available": graph_service.initialized,
            "visualization_service_available": hasattr(visualization_service, 'generate_diagram')
        }
    
    async def visualize_graph(self, workspace_path: str, max_nodes: int = 50) -> Dict[str, Any]:
        """
        Generate graph visualization data
        
        Extracted from: _visualize_graph_tool()
        """
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0,
                }

            project_id = f"project_{hash(workspace_path)}"

            viz_data = await graph_service.get_visualization_data(
                project_id, max_nodes=max_nodes
            )

            if not viz_data.nodes:
                return {
                    "status": "success",
                    "type": "graph_visualization",
                    "data": {
                        "visualization": {},
                        "mermaid_diagram": "graph TD\n    A[No data available]",
                        "summary": "No visualization data available for this project",
                    },
                    "message": "No graph data available",
                    "confidence": 0.7,
                }

            # Generate Mermaid diagram
            mermaid_diagram = viz_data.to_mermaid()

            # Generate summary
            node_count = len(viz_data.nodes)
            edge_count = len(viz_data.edges)

            summary = f"""📊 Project Graph Visualization:

🔗 Structure:
• {node_count} nodes (files, classes, functions)
• {edge_count} relationships (calls, dependencies, inheritance)

📈 This diagram shows the relationships between your code components.
Use it to understand:
• Code dependencies and call patterns
• Component interactions
• Potential refactoring opportunities

🎯 Insights:
• Node density: {node_count / max(max_nodes, 1):.1%} of maximum ({max_nodes})
• Connection ratio: {edge_count / max(node_count, 1):.1f} edges per node
• Complexity level: {'High' if edge_count > node_count * 2 else 'Medium' if edge_count > node_count else 'Low'}"""

            data = {
                "visualization": {
                    "nodes": viz_data.nodes,
                    "edges": viz_data.edges,
                    "layout": viz_data.layout,
                },
                "mermaid_diagram": mermaid_diagram,
                "node_count": node_count,
                "edge_count": edge_count,
                "workspace_path": workspace_path,
                "max_nodes": max_nodes,
                "complexity_metrics": {
                    "node_density": node_count / max(max_nodes, 1),
                    "connection_ratio": edge_count / max(node_count, 1),
                    "complexity_level": 'High' if edge_count > node_count * 2 else 'Medium' if edge_count > node_count else 'Low'
                },
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "graph_visualization",
                "data": data,
                "message": f"Generated visualization with {node_count} nodes",
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            return {
                "status": "error",
                "message": f"Visualization generation failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def generate_diagram(
        self,
        workspace_path: str,
        diagram_type: DiagramType = DiagramType.ARCHITECTURE_OVERVIEW,
        theme: DiagramTheme = DiagramTheme.LIGHT,
        layout: DiagramLayout = DiagramLayout.TOP_DOWN,
        max_nodes: int = 50,
        interactive: bool = True
    ) -> Dict[str, Any]:
        """
        Generate interactive diagram using advanced visualization service
        
        Extracted from: _generate_diagram_tool()
        """
        try:
            project_id = f"project_{hash(workspace_path)}"

            # Create diagram configuration
            config = DiagramConfiguration(
                diagram_type=diagram_type,
                theme=theme,
                layout=layout,
                max_nodes=max_nodes,
                interactive=interactive,
                show_labels=True,
            )

            # Create generation request
            request = DiagramGenerationRequest(
                project_id=project_id,
                configuration=config,
                export_format=DiagramExportFormat.MERMAID,
                include_metadata=True,
                cache_result=True,
            )

            # Generate diagram
            response = await visualization_service.generate_diagram(request)

            # Create summary based on diagram type
            diagram_type_names = {
                DiagramType.ARCHITECTURE_OVERVIEW: "Architecture Overview",
                DiagramType.DEPENDENCY_GRAPH: "Dependency Graph",
                DiagramType.HOTSPOT_HEATMAP: "Code Hotspots Heatmap",
                DiagramType.CIRCULAR_DEPENDENCIES: "Circular Dependencies",
                DiagramType.COUPLING_ANALYSIS: "Coupling Analysis",
            }

            diagram_name = diagram_type_names.get(diagram_type, "Interactive Diagram")

            summary = f"""📊 {diagram_name} Generated Successfully!

🔗 Diagram Details:
• {response.node_count} nodes (components, files, symbols)
• {response.edge_count} relationships
• Generated in {response.generation_time_ms}ms
• Interactive features {'enabled' if interactive else 'disabled'}
• Theme: {theme.value}
• Layout: {layout.value}

📈 This diagram provides:
"""

            # Add diagram-specific insights
            if diagram_type == DiagramType.ARCHITECTURE_OVERVIEW:
                summary += """• High-level system architecture view
• Component relationships and dependencies
• Pattern recognition and design insights
• Navigation aid for understanding code structure"""
            elif diagram_type == DiagramType.DEPENDENCY_GRAPH:
                summary += """• File and module dependency visualization
• Import relationship mapping
• Dependency chain analysis
• Potential circular dependency identification"""
            elif diagram_type == DiagramType.HOTSPOT_HEATMAP:
                summary += """• Critical code component identification
• High-connection point visualization
• Risk assessment for changes
• Focus areas for testing and documentation"""
            elif diagram_type == DiagramType.CIRCULAR_DEPENDENCIES:
                summary += """• Circular dependency cycle detection
• File interdependency issues
• Refactoring opportunity identification
• Architecture improvement guidance"""
            elif diagram_type == DiagramType.COUPLING_ANALYSIS:
                summary += """• Component coupling strength analysis
• Dependency density visualization
• Refactoring priority identification
• Architecture quality assessment"""

            if interactive:
                summary += """

🎨 Interactive Features:
• Click nodes for detailed information
• Zoom and pan for large diagrams
• Filter and search capabilities
• Export options (SVG, PNG, PDF)"""

            summary += """

💡 Use this diagram to understand your codebase structure and identify improvement opportunities!"""

            data = {
                "diagram_id": response.diagram_id,
                "diagram_type": diagram_type,
                "diagram_name": diagram_name,
                "mermaid_content": (
                    response.mermaid_diagram.content
                    if response.mermaid_diagram
                    else None
                ),
                "full_mermaid": (
                    response.mermaid_diagram.get_full_content()
                    if response.mermaid_diagram
                    else None
                ),
                "node_count": response.node_count,
                "edge_count": response.edge_count,
                "generation_time_ms": response.generation_time_ms,
                "configuration": {
                    "theme": theme.value,
                    "layout": layout.value,
                    "max_nodes": max_nodes,
                    "interactive": interactive
                },
                "workspace_path": workspace_path,
                "metadata": response.metadata,
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "diagram_generation",
                "data": data,
                "message": f"Generated {diagram_name} with {response.node_count} nodes",
                "confidence": 0.95,
            }

        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            return {
                "status": "error",
                "message": f"Diagram generation failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def list_diagram_types(self) -> Dict[str, Any]:
        """
        List available diagram types and their descriptions
        
        Extracted from: _list_diagram_types_tool()
        """
        try:
            diagram_types = await visualization_service.get_diagram_types()

            summary_parts = ["📊 Available Diagram Types:\n"]

            for i, diagram_info in enumerate(diagram_types, 1):
                summary_parts.append(f"{i}. **{diagram_info['name']}**")
                summary_parts.append(f"   {diagram_info['description']}")
                summary_parts.append(
                    f"   Recommended max nodes: {diagram_info['max_recommended_nodes']}"
                )
                summary_parts.append("")

            summary_parts.extend(
                [
                    "🎨 Themes Available:",
                    "• Light (default) - Clean, professional appearance",
                    "• Dark - Dark mode for reduced eye strain",
                    "• Neutral - Grayscale, minimalist design",
                    "• Colorful - Vibrant, high-contrast colors",
                    "",
                    "📐 Layout Options:",
                    "• Top-Down (TD) - Hierarchical flow from top to bottom",
                    "• Left-Right (LR) - Horizontal flow, good for wide diagrams",
                    "",
                    "⚙️ Configuration Options:",
                    "• Max nodes: 10-200 (recommended: 50)",
                    "• Interactive: true/false",
                    "• Export formats: Mermaid, SVG, PNG, PDF",
                    "",
                    "💡 To generate a specific diagram:",
                    "• 'Show me the architecture diagram'",
                    "• 'Generate dependency graph'",
                    "• 'Create hotspot heatmap'",
                    "• 'Visualize circular dependencies'",
                    "• 'Display coupling analysis'",
                ]
            )

            data = {
                "diagram_types": diagram_types,
                "themes": [theme.value for theme in DiagramTheme],
                "layouts": [layout.value for layout in DiagramLayout],
                "export_formats": [format.value for format in DiagramExportFormat],
                "configuration_options": {
                    "max_nodes_range": {"min": 10, "max": 200, "recommended": 50},
                    "interactive_default": True,
                    "theme_default": DiagramTheme.LIGHT.value,
                    "layout_default": DiagramLayout.TOP_DOWN.value
                },
                "summary": "\n".join(summary_parts),
            }

            return {
                "status": "success",
                "type": "diagram_types_list",
                "data": data,
                "message": f"Listed {len(diagram_types)} available diagram types",
                "confidence": 1.0,
            }

        except Exception as e:
            logger.error(f"Error listing diagram types: {e}")
            return {
                "status": "error",
                "message": f"Failed to list diagram types: {str(e)}",
                "confidence": 0.0,
            }
    
    async def export_diagram(
        self, 
        diagram_id: str, 
        export_format: DiagramExportFormat = DiagramExportFormat.SVG,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export diagram in specified format
        """
        try:
            export_result = await visualization_service.export_diagram(
                diagram_id, export_format, output_path
            )

            if not export_result.success:
                return {
                    "status": "error",
                    "message": f"Export failed: {export_result.error_message}",
                    "confidence": 0.0,
                }

            summary = f"""📁 Diagram Export Successful!

📊 Export Details:
• Format: {export_format.value.upper()}
• File size: {export_result.file_size_kb:.1f} KB
• Output path: {export_result.output_path}
• Export time: {export_result.export_time_ms}ms

💾 File Information:
• Diagram ID: {diagram_id}
• Resolution: {export_result.resolution if hasattr(export_result, 'resolution') else 'Vector'}
• Quality: High

✅ The diagram has been successfully exported and is ready for use!"""

            data = {
                "diagram_id": diagram_id,
                "export_format": export_format.value,
                "output_path": export_result.output_path,
                "file_size_kb": export_result.file_size_kb,
                "export_time_ms": export_result.export_time_ms,
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "diagram_export",
                "data": data,
                "message": f"Exported diagram as {export_format.value.upper()}",
                "confidence": 0.95,
            }

        except Exception as e:
            logger.error(f"Error exporting diagram: {e}")
            return {
                "status": "error",
                "message": f"Diagram export failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def create_dashboard(self, workspace_path: str) -> Dict[str, Any]:
        """
        Create comprehensive visualization dashboard with multiple diagram types
        """
        try:
            dashboard_data = {
                "workspace_path": workspace_path,
                "diagrams": [],
                "generation_time_total": 0,
                "successful_generations": 0
            }

            # Define dashboard diagram types
            dashboard_diagrams = [
                (DiagramType.ARCHITECTURE_OVERVIEW, "System Architecture"),
                (DiagramType.DEPENDENCY_GRAPH, "Dependencies"),
                (DiagramType.HOTSPOT_HEATMAP, "Code Hotspots"),
                (DiagramType.COUPLING_ANALYSIS, "Coupling Analysis")
            ]

            for diagram_type, display_name in dashboard_diagrams:
                try:
                    result = await self.generate_diagram(
                        workspace_path=workspace_path,
                        diagram_type=diagram_type,
                        max_nodes=30,  # Smaller for dashboard
                        interactive=True
                    )

                    if result["status"] == "success":
                        dashboard_data["diagrams"].append({
                            "type": diagram_type.value,
                            "display_name": display_name,
                            "diagram_id": result["data"]["diagram_id"],
                            "node_count": result["data"]["node_count"],
                            "edge_count": result["data"]["edge_count"],
                            "mermaid_content": result["data"]["mermaid_content"],
                            "generation_time": result["data"]["generation_time_ms"]
                        })
                        dashboard_data["generation_time_total"] += result["data"]["generation_time_ms"]
                        dashboard_data["successful_generations"] += 1

                except Exception as e:
                    logger.warning(f"Failed to generate {display_name} for dashboard: {e}")

            # Generate dashboard summary
            total_nodes = sum(d["node_count"] for d in dashboard_data["diagrams"])
            total_edges = sum(d["edge_count"] for d in dashboard_data["diagrams"])

            summary = f"""📊 Visualization Dashboard Created!

🎯 Dashboard Overview:
• Diagrams generated: {dashboard_data["successful_generations"]}/{len(dashboard_diagrams)}
• Total generation time: {dashboard_data["generation_time_total"]}ms
• Combined nodes: {total_nodes}
• Combined relationships: {total_edges}

📈 Available Views:
{chr(10).join(f'• {d["display_name"]}: {d["node_count"]} nodes, {d["edge_count"]} edges' for d in dashboard_data["diagrams"])}

💡 Use the dashboard to:
• Get comprehensive project overview
• Compare different analytical perspectives
• Identify patterns across multiple views
• Navigate between related diagrams

🎨 All diagrams are interactive and can be exported individually."""

            dashboard_data["summary"] = summary

            return {
                "status": "success",
                "type": "visualization_dashboard",
                "data": dashboard_data,
                "message": f"Created dashboard with {dashboard_data['successful_generations']} diagrams",
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return {
                "status": "error",
                "message": f"Dashboard creation failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_visualization_insights(self, workspace_path: str) -> Dict[str, Any]:
        """
        Generate insights based on visualization analysis
        """
        try:
            insights = {
                "workspace_path": workspace_path,
                "structural_insights": [],
                "complexity_insights": [],
                "recommendations": []
            }

            # Get basic graph visualization
            graph_result = await self.visualize_graph(workspace_path)
            if graph_result["status"] == "success":
                graph_data = graph_result["data"]
                node_count = graph_data["node_count"]
                edge_count = graph_data["edge_count"]
                complexity_metrics = graph_data["complexity_metrics"]

                # Structural insights
                if node_count > 50:
                    insights["structural_insights"].append("Large codebase with many components")
                elif node_count < 10:
                    insights["structural_insights"].append("Small, focused codebase")
                else:
                    insights["structural_insights"].append("Medium-sized codebase")

                # Complexity insights
                if complexity_metrics["complexity_level"] == "High":
                    insights["complexity_insights"].append("High interconnectedness between components")
                    insights["recommendations"].append("Consider refactoring to reduce coupling")
                elif complexity_metrics["complexity_level"] == "Low":
                    insights["complexity_insights"].append("Well-structured, loosely coupled design")

                if complexity_metrics["connection_ratio"] > 3:
                    insights["complexity_insights"].append("High connection density - components are highly interdependent")
                    insights["recommendations"].append("Review architecture for potential modularity improvements")

            # Try to get architecture overview
            try:
                arch_result = await self.generate_diagram(
                    workspace_path, DiagramType.ARCHITECTURE_OVERVIEW, max_nodes=20
                )
                if arch_result["status"] == "success":
                    insights["structural_insights"].append("Architecture diagram successfully generated")
            except Exception:
                insights["recommendations"].append("Consider improving project structure for better visualization")

            # Generate summary
            summary = f"""🔍 Visualization Analysis Insights:

🏗️ Structural Analysis:
{chr(10).join(f'• {insight}' for insight in insights["structural_insights"])}

⚡ Complexity Analysis:
{chr(10).join(f'• {insight}' for insight in insights["complexity_insights"])}

💡 Recommendations:
{chr(10).join(f'• {rec}' for rec in insights["recommendations"])}

🎯 Visualization Health: {'Good' if len(insights['recommendations']) <= 2 else 'Needs Attention'}"""

            insights["summary"] = summary
            insights["visualization_health"] = 'Good' if len(insights['recommendations']) <= 2 else 'Needs Attention'

            return {
                "status": "success",
                "type": "visualization_insights",
                "data": insights,
                "message": f"Generated insights with {len(insights['recommendations'])} recommendations",
                "confidence": 0.85,
            }

        except Exception as e:
            logger.error(f"Error generating visualization insights: {e}")
            return {
                "status": "error",
                "message": f"Insights generation failed: {str(e)}",
                "confidence": 0.0,
            }