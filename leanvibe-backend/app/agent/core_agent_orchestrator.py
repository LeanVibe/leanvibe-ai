"""
Core Agent Orchestrator

Central coordinator for all L3 agent services following the decomposition plan.
Orchestrates AST Intelligence, Project Monitoring, Cache Performance, Architecture Analysis,
MLX AI Integration, and Visualization services for unified functionality.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .l3_coding_agent import AgentDependencies, L3CodingAgent
from ..services.ast_intelligence_service import ASTIntelligenceService
from ..services.project_monitoring_service import ProjectMonitoringService
from ..services.cache_performance_service import CachePerformanceService
from ..services.architecture_analysis_service import ArchitectureAnalysisService
from ..services.mlx_ai_service import MLXAIService
from ..services.visualization_diagram_service import VisualizationDiagramService

logger = logging.getLogger(__name__)


class CoreAgentOrchestrator(L3CodingAgent):
    """
    Central coordinator for all agent services.
    
    Replaces the monolithic enhanced_l3_agent.py with a service-oriented architecture
    that coordinates focused, single-responsibility services for improved maintainability,
    testability, and development velocity.
    """
    
    def __init__(self, dependencies: AgentDependencies):
        super().__init__(dependencies)
        
        # Initialize service instances
        self.ast_service = ASTIntelligenceService()
        self.monitoring_service = ProjectMonitoringService()
        self.cache_service = CachePerformanceService()
        self.architecture_service = ArchitectureAnalysisService()
        self.mlx_service = MLXAIService()
        self.visualization_service = VisualizationDiagramService()
        
        # Track service initialization status
        self.services_initialized = {
            "ast_intelligence": False,
            "project_monitoring": False,
            "cache_performance": False,
            "architecture_analysis": False,
            "mlx_ai": False,
            "visualization_diagram": False
        }
        
        # Enhanced tools with service delegation
        self.tools.update({
            # AST Intelligence Tools
            "analyze_project": self._analyze_project_tool,
            "explore_symbols": self._explore_symbols_tool,
            "find_references": self._find_references_tool,
            "check_complexity": self._check_complexity_tool,
            "get_file_context": self._get_file_context_tool,
            "get_completion_context": self._get_completion_context_tool,
            
            # Project Monitoring Tools
            "start_monitoring": self._start_monitoring_tool,
            "stop_monitoring": self._stop_monitoring_tool,
            "get_monitoring_status": self._get_monitoring_status_tool,
            "get_recent_changes": self._get_recent_changes_tool,
            "refresh_project_index": self._refresh_project_index_tool,
            
            # Cache & Performance Tools
            "get_warming_candidates": self._get_warming_candidates_tool,
            "trigger_cache_warming": self._trigger_cache_warming_tool,
            "get_warming_metrics": self._get_warming_metrics_tool,
            "set_warming_strategy": self._set_warming_strategy_tool,
            "optimize_performance": self._optimize_performance_tool,
            
            # Architecture Analysis Tools
            "detect_architecture": self._detect_architecture_tool,
            "find_circular_deps": self._find_circular_dependencies_tool,
            "analyze_coupling": self._analyze_coupling_tool,
            "find_hotspots": self._find_hotspots_tool,
            "suggest_refactoring": self._suggest_refactoring_tool,
            "get_architecture_summary": self._get_architecture_summary_tool,
            
            # MLX AI Tools
            "mlx_suggest_code": self._mlx_suggest_code_tool,
            "mlx_explain_code": self._mlx_explain_code_tool,
            "mlx_refactor_code": self._mlx_refactor_code_tool,
            "mlx_debug_code": self._mlx_debug_code_tool,
            "mlx_optimize_code": self._mlx_optimize_code_tool,
            "mlx_stream_completion": self._mlx_stream_completion_tool,
            "get_ai_insights": self._get_ai_insights_tool,
            
            # Visualization Tools
            "visualize_graph": self._visualize_graph_tool,
            "generate_diagram": self._generate_diagram_tool,
            "list_diagram_types": self._list_diagram_types_tool,
            "export_diagram": self._export_diagram_tool,
            "create_dashboard": self._create_dashboard_tool,
            
            # Orchestrator-specific tools
            "get_service_health": self._get_service_health_tool,
            "initialize_services": self._initialize_services_tool,
            "get_orchestrator_status": self._get_orchestrator_status_tool,
        })
    
    async def initialize(self) -> bool:
        """Initialize the orchestrator and all services in dependency order"""
        try:
            logger.info("Initializing Core Agent Orchestrator with service-oriented architecture...")
            
            # Initialize base agent
            await super().initialize()
            
            # Initialize services in dependency order
            workspace_path = self.dependencies.workspace_path
            
            # 1. Initialize AST Intelligence Service (foundational)
            logger.info("Initializing AST Intelligence Service...")
            if await self.ast_service.initialize(workspace_path):
                self.services_initialized["ast_intelligence"] = True
                logger.info("✅ AST Intelligence Service initialized")
            else:
                logger.warning("⚠️ AST Intelligence Service initialization failed")
            
            # 2. Initialize Project Monitoring Service
            logger.info("Initializing Project Monitoring Service...")
            if await self.monitoring_service.initialize():
                self.services_initialized["project_monitoring"] = True
                logger.info("✅ Project Monitoring Service initialized")
            else:
                logger.warning("⚠️ Project Monitoring Service initialization failed")
            
            # 3. Initialize Cache & Performance Service
            logger.info("Initializing Cache & Performance Service...")
            if await self.cache_service.initialize():
                self.services_initialized["cache_performance"] = True
                logger.info("✅ Cache & Performance Service initialized")
            else:
                logger.warning("⚠️ Cache & Performance Service initialization failed")
            
            # 4. Initialize Architecture Analysis Service
            logger.info("Initializing Architecture Analysis Service...")
            if await self.architecture_service.initialize():
                self.services_initialized["architecture_analysis"] = True
                logger.info("✅ Architecture Analysis Service initialized")
            else:
                logger.warning("⚠️ Architecture Analysis Service initialization failed")
            
            # 5. Initialize MLX AI Service (requires project context from AST)
            logger.info("Initializing MLX AI Service...")
            project_context = getattr(self.ast_service, 'project_context', None)
            if await self.mlx_service.initialize(project_context):
                self.services_initialized["mlx_ai"] = True
                logger.info("✅ MLX AI Service initialized")
            else:
                logger.warning("⚠️ MLX AI Service initialization failed")
            
            # 6. Initialize Visualization Service
            logger.info("Initializing Visualization & Diagram Service...")
            if await self.visualization_service.initialize():
                self.services_initialized["visualization_diagram"] = True
                logger.info("✅ Visualization & Diagram Service initialized")
            else:
                logger.warning("⚠️ Visualization & Diagram Service initialization failed")
            
            # Log initialization summary
            initialized_count = sum(self.services_initialized.values())
            total_services = len(self.services_initialized)
            
            logger.info(f"Core Agent Orchestrator initialized: {initialized_count}/{total_services} services ready")
            
            if initialized_count == total_services:
                logger.info("🚀 All services successfully initialized - L3 Agent fully operational!")
                return True
            elif initialized_count >= total_services * 0.7:  # 70% threshold
                logger.info(f"⚡ Core services operational ({initialized_count}/{total_services}) - Agent ready with reduced functionality")
                return True
            else:
                logger.error(f"❌ Critical service failures ({initialized_count}/{total_services}) - Agent initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Core Agent Orchestrator: {e}")
            return False
    
    # AST Intelligence Service delegation
    async def _analyze_project_tool(self) -> Dict[str, Any]:
        """Delegate to AST Intelligence Service"""
        return await self.ast_service.analyze_project()
    
    async def _explore_symbols_tool(self, symbol_name: str) -> Dict[str, Any]:
        """Delegate to AST Intelligence Service"""
        return await self.ast_service.explore_symbols(symbol_name)
    
    async def _find_references_tool(self, symbol_name: str) -> Dict[str, Any]:
        """Delegate to AST Intelligence Service"""
        return await self.ast_service.find_references(symbol_name)
    
    async def _check_complexity_tool(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Delegate to AST Intelligence Service"""
        return await self.ast_service.check_complexity(file_path)
    
    async def _get_file_context_tool(self, file_path: str) -> Dict[str, Any]:
        """Delegate to AST Intelligence Service"""
        return await self.ast_service.get_file_context(file_path)
    
    async def _get_completion_context_tool(self, file_path: str, line_number: int, column: int) -> Dict[str, Any]:
        """Delegate to AST Intelligence Service"""
        return await self.ast_service.get_completion_context(file_path, line_number, column)
    
    # Project Monitoring Service delegation
    async def _start_monitoring_tool(self, workspace_path: Optional[str] = None) -> Dict[str, Any]:
        """Delegate to Project Monitoring Service"""
        workspace = workspace_path or self.dependencies.workspace_path
        return await self.monitoring_service.start_monitoring(
            client_id=self.dependencies.client_id,
            workspace_path=workspace
        )
    
    async def _stop_monitoring_tool(self) -> Dict[str, Any]:
        """Delegate to Project Monitoring Service"""
        return await self.monitoring_service.stop_monitoring(self.dependencies.client_id)
    
    async def _get_monitoring_status_tool(self) -> Dict[str, Any]:
        """Delegate to Project Monitoring Service"""
        return await self.monitoring_service.get_monitoring_status(self.dependencies.client_id)
    
    async def _get_recent_changes_tool(self, limit: int = 10) -> Dict[str, Any]:
        """Delegate to Project Monitoring Service"""
        return await self.monitoring_service.get_recent_changes(self.dependencies.client_id, limit)
    
    async def _refresh_project_index_tool(self, force_full: bool = True) -> Dict[str, Any]:
        """Delegate to Project Monitoring Service"""
        return await self.monitoring_service.refresh_project_index(
            self.dependencies.workspace_path, force_full
        )
    
    # Cache & Performance Service delegation
    async def _get_warming_candidates_tool(self, limit: int = 10) -> Dict[str, Any]:
        """Delegate to Cache & Performance Service"""
        return await self.cache_service.get_warming_candidates(limit)
    
    async def _trigger_cache_warming_tool(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """Delegate to Cache & Performance Service"""
        return await self.cache_service.trigger_cache_warming(project_path)
    
    async def _get_warming_metrics_tool(self) -> Dict[str, Any]:
        """Delegate to Cache & Performance Service"""
        return await self.cache_service.get_warming_metrics()
    
    async def _set_warming_strategy_tool(self, strategy: str) -> Dict[str, Any]:
        """Delegate to Cache & Performance Service"""
        return await self.cache_service.set_warming_strategy(strategy)
    
    async def _optimize_performance_tool(self) -> Dict[str, Any]:
        """Delegate to Cache & Performance Service"""
        return await self.cache_service.optimize_performance()
    
    # Architecture Analysis Service delegation
    async def _detect_architecture_tool(self) -> Dict[str, Any]:
        """Delegate to Architecture Analysis Service"""
        return await self.architecture_service.detect_architecture_patterns(
            self.dependencies.workspace_path
        )
    
    async def _find_circular_dependencies_tool(self) -> Dict[str, Any]:
        """Delegate to Architecture Analysis Service"""
        return await self.architecture_service.find_circular_dependencies(
            self.dependencies.workspace_path
        )
    
    async def _analyze_coupling_tool(self) -> Dict[str, Any]:
        """Delegate to Architecture Analysis Service"""
        return await self.architecture_service.analyze_coupling(
            self.dependencies.workspace_path
        )
    
    async def _find_hotspots_tool(self) -> Dict[str, Any]:
        """Delegate to Architecture Analysis Service"""
        return await self.architecture_service.find_hotspots(
            self.dependencies.workspace_path
        )
    
    async def _suggest_refactoring_tool(self, target: Optional[str] = None) -> Dict[str, Any]:
        """Delegate to Architecture Analysis Service"""
        return await self.architecture_service.suggest_refactoring(
            self.dependencies.workspace_path, target
        )
    
    async def _get_architecture_summary_tool(self) -> Dict[str, Any]:
        """Delegate to Architecture Analysis Service"""
        return await self.architecture_service.get_architecture_summary(
            self.dependencies.workspace_path
        )
    
    # MLX AI Service delegation
    async def _mlx_suggest_code_tool(self, request: str) -> str:
        """Delegate to MLX AI Service"""
        try:
            import json
            
            # Parse request
            try:
                req_data = json.loads(request)
                file_path = req_data.get("file_path", "")
                cursor_position = req_data.get("cursor_position", 0)
                context_hint = req_data.get("context_hint")
            except json.JSONDecodeError:
                file_path = request.strip()
                cursor_position = 0
                context_hint = None
            
            result = await self.mlx_service.suggest_code(file_path, cursor_position, context_hint)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    async def _mlx_explain_code_tool(self, request: str) -> str:
        """Delegate to MLX AI Service"""
        try:
            import json
            
            # Parse request
            try:
                req_data = json.loads(request)
                file_path = req_data.get("file_path", "")
                cursor_position = req_data.get("cursor_position", 0)
                code_snippet = req_data.get("code_snippet")
            except json.JSONDecodeError:
                file_path = request.strip()
                cursor_position = 0
                code_snippet = None
            
            result = await self.mlx_service.explain_code(file_path, cursor_position, code_snippet)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    async def _mlx_refactor_code_tool(self, request: str) -> str:
        """Delegate to MLX AI Service"""
        try:
            import json
            
            # Parse request
            try:
                req_data = json.loads(request)
                file_path = req_data.get("file_path", "")
                cursor_position = req_data.get("cursor_position", 0)
                refactor_goal = req_data.get("refactor_goal")
            except json.JSONDecodeError:
                file_path = request.strip()
                cursor_position = 0
                refactor_goal = None
            
            result = await self.mlx_service.refactor_code(file_path, cursor_position, refactor_goal)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    async def _mlx_debug_code_tool(self, request: str) -> str:
        """Delegate to MLX AI Service"""
        try:
            import json
            
            # Parse request
            try:
                req_data = json.loads(request)
                file_path = req_data.get("file_path", "")
                cursor_position = req_data.get("cursor_position", 0)
                error_context = req_data.get("error_context")
            except json.JSONDecodeError:
                file_path = request.strip()
                cursor_position = 0
                error_context = None
            
            result = await self.mlx_service.debug_code(file_path, cursor_position, error_context)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    async def _mlx_optimize_code_tool(self, request: str) -> str:
        """Delegate to MLX AI Service"""
        try:
            import json
            
            # Parse request
            try:
                req_data = json.loads(request)
                file_path = req_data.get("file_path", "")
                cursor_position = req_data.get("cursor_position", 0)
                optimization_target = req_data.get("optimization_target")
            except json.JSONDecodeError:
                file_path = request.strip()
                cursor_position = 0
                optimization_target = None
            
            result = await self.mlx_service.optimize_code(file_path, cursor_position, optimization_target)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    async def _mlx_stream_completion_tool(self, request: str) -> str:
        """Delegate to MLX AI Service"""
        try:
            import json
            
            # Parse request
            try:
                req_data = json.loads(request)
                file_path = req_data.get("file_path", "")
                cursor_position = req_data.get("cursor_position", 0)
                intent = req_data.get("intent", "suggest")
            except json.JSONDecodeError:
                return json.dumps({"status": "error", "message": "Invalid JSON request"})
            
            result = await self.mlx_service.start_streaming_completion(file_path, cursor_position, intent)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    async def _get_ai_insights_tool(self, file_path: str) -> Dict[str, Any]:
        """Delegate to MLX AI Service"""
        return await self.mlx_service.get_ai_insights(file_path)
    
    # Visualization Service delegation
    async def _visualize_graph_tool(self, max_nodes: int = 50) -> Dict[str, Any]:
        """Delegate to Visualization Service"""
        return await self.visualization_service.visualize_graph(
            self.dependencies.workspace_path, max_nodes
        )
    
    async def _generate_diagram_tool(
        self,
        diagram_type: str = "architecture_overview",
        theme: str = "light",
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """Delegate to Visualization Service"""
        from ..models.visualization_models import DiagramType, DiagramTheme
        
        # Convert string to enum
        try:
            diagram_type_enum = DiagramType(diagram_type)
        except ValueError:
            diagram_type_enum = DiagramType.ARCHITECTURE_OVERVIEW
        
        try:
            theme_enum = DiagramTheme(theme)
        except ValueError:
            theme_enum = DiagramTheme.LIGHT
        
        return await self.visualization_service.generate_diagram(
            self.dependencies.workspace_path,
            diagram_type_enum,
            theme_enum,
            max_nodes=max_nodes
        )
    
    async def _list_diagram_types_tool(self) -> Dict[str, Any]:
        """Delegate to Visualization Service"""
        return await self.visualization_service.list_diagram_types()
    
    async def _export_diagram_tool(self, diagram_id: str, export_format: str = "svg") -> Dict[str, Any]:
        """Delegate to Visualization Service"""
        from ..models.visualization_models import DiagramExportFormat
        
        try:
            format_enum = DiagramExportFormat(export_format)
        except ValueError:
            format_enum = DiagramExportFormat.SVG
        
        return await self.visualization_service.export_diagram(diagram_id, format_enum)
    
    async def _create_dashboard_tool(self) -> Dict[str, Any]:
        """Delegate to Visualization Service"""
        return await self.visualization_service.create_dashboard(self.dependencies.workspace_path)
    
    # Orchestrator-specific tools
    async def _get_service_health_tool(self) -> Dict[str, Any]:
        """Get health status of all services"""
        try:
            health_data = {
                "orchestrator": {
                    "initialized": True,
                    "services_initialized": self.services_initialized,
                    "total_services": len(self.services_initialized),
                    "operational_services": sum(self.services_initialized.values())
                },
                "services": {}
            }
            
            # Collect health from each service
            if self.services_initialized["ast_intelligence"]:
                health_data["services"]["ast_intelligence"] = self.ast_service.get_health_status()
            
            if self.services_initialized["project_monitoring"]:
                health_data["services"]["project_monitoring"] = self.monitoring_service.get_health_status()
            
            if self.services_initialized["cache_performance"]:
                health_data["services"]["cache_performance"] = self.cache_service.get_health_status()
            
            if self.services_initialized["architecture_analysis"]:
                health_data["services"]["architecture_analysis"] = self.architecture_service.get_health_status()
            
            if self.services_initialized["mlx_ai"]:
                health_data["services"]["mlx_ai"] = self.mlx_service.get_health_status()
            
            if self.services_initialized["visualization_diagram"]:
                health_data["services"]["visualization_diagram"] = self.visualization_service.get_health_status()
            
            # Generate summary
            operational_count = health_data["orchestrator"]["operational_services"]
            total_count = health_data["orchestrator"]["total_services"]
            health_percentage = (operational_count / total_count) * 100
            
            summary = f"""🏗️ L3 Agent Service Health Report:

🎯 Orchestrator Status: {'Operational' if operational_count >= total_count * 0.7 else 'Degraded'}
📊 Service Health: {operational_count}/{total_count} services operational ({health_percentage:.1f}%)

🔧 Service Status:
{chr(10).join(f'• {service}: {"✅ Operational" if status else "❌ Failed"}' for service, status in self.services_initialized.items())}

💡 Architecture Benefits:
• Service-oriented design with single responsibility
• Independent service scaling and maintenance
• Improved error isolation and debugging
• Enhanced testability and code quality

⚡ Performance: Distributed processing across {operational_count} specialized services"""

            health_data["summary"] = summary
            
            return {
                "status": "success",
                "type": "service_health",
                "data": health_data,
                "message": f"Service health: {operational_count}/{total_count} operational",
                "confidence": 1.0,
            }
            
        except Exception as e:
            logger.error(f"Error getting service health: {e}")
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def _initialize_services_tool(self) -> Dict[str, Any]:
        """Re-initialize failed services"""
        try:
            logger.info("Re-initializing failed services...")
            
            initialization_results = {}
            workspace_path = self.dependencies.workspace_path
            
            for service_name, is_initialized in self.services_initialized.items():
                if not is_initialized:
                    logger.info(f"Re-initializing {service_name}...")
                    
                    try:
                        if service_name == "ast_intelligence":
                            success = await self.ast_service.initialize(workspace_path)
                        elif service_name == "project_monitoring":
                            success = await self.monitoring_service.initialize()
                        elif service_name == "cache_performance":
                            success = await self.cache_service.initialize()
                        elif service_name == "architecture_analysis":
                            success = await self.architecture_service.initialize()
                        elif service_name == "mlx_ai":
                            project_context = getattr(self.ast_service, 'project_context', None)
                            success = await self.mlx_service.initialize(project_context)
                        elif service_name == "visualization_diagram":
                            success = await self.visualization_service.initialize()
                        else:
                            success = False
                        
                        self.services_initialized[service_name] = success
                        initialization_results[service_name] = "success" if success else "failed"
                        
                    except Exception as e:
                        logger.error(f"Failed to initialize {service_name}: {e}")
                        initialization_results[service_name] = f"error: {str(e)}"
                else:
                    initialization_results[service_name] = "already_initialized"
            
            # Generate summary
            newly_initialized = sum(1 for result in initialization_results.values() if result == "success")
            total_operational = sum(self.services_initialized.values())
            
            summary = f"""🔄 Service Re-initialization Complete:

📊 Results:
• Newly initialized: {newly_initialized}
• Total operational: {total_operational}/{len(self.services_initialized)}
• Success rate: {(total_operational / len(self.services_initialized)):.1%}

🔧 Service Results:
{chr(10).join(f'• {service}: {result}' for service, result in initialization_results.items())}

✅ Agent Status: {'Fully Operational' if total_operational == len(self.services_initialized) else 'Partially Operational'}"""

            return {
                "status": "success",
                "type": "service_initialization",
                "data": {
                    "initialization_results": initialization_results,
                    "services_initialized": self.services_initialized,
                    "newly_initialized": newly_initialized,
                    "total_operational": total_operational,
                    "summary": summary
                },
                "message": f"Re-initialized {newly_initialized} services",
                "confidence": 0.95,
            }
            
        except Exception as e:
            logger.error(f"Error in service initialization: {e}")
            return {
                "status": "error",
                "message": f"Service initialization failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def _get_orchestrator_status_tool(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status"""
        try:
            status_data = {
                "orchestrator_info": {
                    "name": "Core Agent Orchestrator",
                    "version": "1.0.0",
                    "architecture": "Service-Oriented",
                    "workspace_path": self.dependencies.workspace_path,
                    "client_id": self.dependencies.client_id,
                    "initialization_time": datetime.now().isoformat()
                },
                "service_architecture": {
                    "total_services": len(self.services_initialized),
                    "operational_services": sum(self.services_initialized.values()),
                    "service_details": {}
                },
                "capabilities": {
                    "ast_intelligence": self.ast_service.get_capabilities() if self.services_initialized["ast_intelligence"] else [],
                    "project_monitoring": self.monitoring_service.get_capabilities() if self.services_initialized["project_monitoring"] else [],
                    "cache_performance": self.cache_service.get_capabilities() if self.services_initialized["cache_performance"] else [],
                    "architecture_analysis": self.architecture_service.get_capabilities() if self.services_initialized["architecture_analysis"] else [],
                    "mlx_ai": self.mlx_service.get_capabilities() if self.services_initialized["mlx_ai"] else [],
                    "visualization_diagram": self.visualization_service.get_capabilities() if self.services_initialized["visualization_diagram"] else []
                }
            }
            
            # Count total capabilities
            total_capabilities = sum(len(caps) for caps in status_data["capabilities"].values())
            
            # Generate comprehensive summary
            summary = f"""🎯 Core Agent Orchestrator Status Report:

🏗️ Architecture Overview:
• Design: Service-Oriented Architecture (SOA)
• Services: {status_data['service_architecture']['operational_services']}/{status_data['service_architecture']['total_services']} operational
• Total capabilities: {total_capabilities} across all services
• Workspace: {Path(self.dependencies.workspace_path).name}

🔧 Service Decomposition Benefits:
• Single Responsibility: Each service has focused purpose
• Maintainability: Improved code organization and debugging
• Scalability: Independent service optimization
• Testability: Isolated unit testing per service
• Development Velocity: Parallel development on different services

⚡ Operational Status:
• AST Intelligence: {'✅' if self.services_initialized['ast_intelligence'] else '❌'} ({len(status_data['capabilities']['ast_intelligence'])} capabilities)
• Project Monitoring: {'✅' if self.services_initialized['project_monitoring'] else '❌'} ({len(status_data['capabilities']['project_monitoring'])} capabilities)
• Cache Performance: {'✅' if self.services_initialized['cache_performance'] else '❌'} ({len(status_data['capabilities']['cache_performance'])} capabilities)
• Architecture Analysis: {'✅' if self.services_initialized['architecture_analysis'] else '❌'} ({len(status_data['capabilities']['architecture_analysis'])} capabilities)
• MLX AI Integration: {'✅' if self.services_initialized['mlx_ai'] else '❌'} ({len(status_data['capabilities']['mlx_ai'])} capabilities)
• Visualization & Diagrams: {'✅' if self.services_initialized['visualization_diagram'] else '❌'} ({len(status_data['capabilities']['visualization_diagram'])} capabilities)

🚀 L3 Agent: Fully decomposed from 3,158-line monolith to {len(self.services_initialized)} focused services!"""

            status_data["summary"] = summary
            
            return {
                "status": "success",
                "type": "orchestrator_status",
                "data": status_data,
                "message": f"L3 Agent Orchestrator: {status_data['service_architecture']['operational_services']}/{status_data['service_architecture']['total_services']} services operational",
                "confidence": 1.0,
            }
            
        except Exception as e:
            logger.error(f"Error getting orchestrator status: {e}")
            return {
                "status": "error",
                "message": f"Status check failed: {str(e)}",
                "confidence": 0.0,
            }
    
    def get_enhanced_state_summary(self) -> Dict[str, Any]:
        """Get enhanced state summary with service architecture information"""
        base_summary = self.get_state_summary()
        
        # Add orchestrator-specific information
        base_summary.update({
            "architecture": "Service-Oriented Architecture (SOA)",
            "services_initialized": self.services_initialized,
            "total_services": len(self.services_initialized),
            "operational_services": sum(self.services_initialized.values()),
            "decomposition_status": "Complete - Monolith decomposed into focused services",
            "service_capabilities": {
                service: getattr(self, f"{service.replace('_', '')}_service", None) and 
                        hasattr(getattr(self, f"{service.replace('_', '')}_service", None), 'get_capabilities') and
                        getattr(self, f"{service.replace('_', '')}_service").get_capabilities() 
                        if self.services_initialized[service] else []
                for service in self.services_initialized.keys()
            }
        })
        
        return base_summary