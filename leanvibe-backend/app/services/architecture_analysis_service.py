"""
Architecture Analysis Service

Extracted from enhanced_l3_agent.py to provide focused architecture analysis,
dependency detection, and code quality insights following single responsibility principle.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .graph_service import graph_service
from .graph_query_service import graph_query_service

logger = logging.getLogger(__name__)


class ArchitectureAnalysisService:
    """
    Service dedicated to project architecture analysis and insights.
    
    Provides architecture pattern detection, circular dependency analysis,
    coupling assessment, and code hotspot identification.
    """
    
    def __init__(self):
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the architecture analysis service"""
        try:
            # Ensure graph services are initialized
            if not graph_service.initialized:
                await graph_service.initialize()
            
            if hasattr(graph_query_service, 'initialize') and not getattr(graph_query_service, 'initialized', True):
                await graph_query_service.initialize()
            
            self._initialized = True
            logger.info("Architecture Analysis Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Architecture Analysis Service: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided by this service"""
        return [
            "architecture_pattern_detection",
            "circular_dependency_analysis",
            "coupling_analysis", 
            "code_hotspot_detection",
            "refactoring_suggestions",
            "dependency_visualization"
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service"""
        return {
            "service": "architecture_analysis",
            "initialized": self._initialized,
            "graph_service_available": graph_service.initialized,
            "graph_query_available": hasattr(graph_query_service, 'find_circular_dependencies')
        }
    
    async def detect_architecture_patterns(self, workspace_path: str) -> Dict[str, Any]:
        """
        Detect architecture patterns in the project
        
        Extracted from: _detect_architecture_tool()
        """
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0,
                }

            project_id = f"project_{hash(workspace_path)}"
            patterns = await graph_service.get_architecture_patterns(project_id)

            if not patterns:
                return {
                    "status": "success",
                    "type": "architecture_detection",
                    "data": {
                        "patterns": [],
                        "summary": "No common architecture patterns detected. This might indicate a microservice, library, or custom architecture.",
                    },
                    "message": "Architecture analysis completed",
                    "confidence": 0.7,
                }

            # Generate summary
            summary_parts = ["Detected Architecture Patterns:\n"]
            for pattern in patterns:
                confidence_indicator = (
                    "🔴"
                    if pattern.confidence < 0.5
                    else "🟡" if pattern.confidence < 0.8 else "🟢"
                )
                summary_parts.append(
                    f"{confidence_indicator} {pattern.pattern_name} (confidence: {pattern.confidence:.1%})"
                )
                summary_parts.append(f"   {pattern.description}")
                if pattern.components:
                    summary_parts.append(
                        f"   Components: {', '.join(pattern.components[:3])}"
                    )
                summary_parts.append("")

            data = {
                "patterns": [
                    {
                        "name": p.pattern_name,
                        "confidence": p.confidence,
                        "description": p.description,
                        "components": p.components,
                        "relationships": p.relationships,
                    }
                    for p in patterns
                ],
                "total_patterns": len(patterns),
                "workspace_path": workspace_path,
                "summary": "\n".join(summary_parts),
            }

            return {
                "status": "success",
                "type": "architecture_detection",
                "data": data,
                "message": f"Found {len(patterns)} architecture patterns",
                "confidence": 0.85,
            }

        except Exception as e:
            logger.error(f"Error in architecture detection: {e}")
            return {
                "status": "error",
                "message": f"Architecture detection failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def find_circular_dependencies(self, workspace_path: str) -> Dict[str, Any]:
        """
        Find circular dependencies in the project
        
        Extracted from: _find_circular_dependencies_tool()
        """
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0,
                }

            project_id = f"project_{hash(workspace_path)}"
            cycles = await graph_query_service.find_circular_dependencies(project_id)

            if not cycles:
                return {
                    "status": "success",
                    "type": "circular_dependency_analysis",
                    "data": {
                        "cycles": [],
                        "cycle_count": 0,
                        "summary": "✅ No circular dependencies detected. Good modular design!",
                    },
                    "message": "No circular dependencies found",
                    "confidence": 0.9,
                }

            # Generate summary
            summary_parts = [f"🔄 Found {len(cycles)} circular dependencies:\n"]
            for i, cycle in enumerate(cycles[:5], 1):
                cycle_str = " → ".join(cycle + [cycle[0]])  # Complete the circle
                summary_parts.append(f"{i}. {cycle_str}")

            if len(cycles) > 5:
                summary_parts.append(f"... and {len(cycles) - 5} more cycles")

            summary_parts.extend(
                [
                    "",
                    "⚠️ Circular dependencies can make code harder to:",
                    "• Test in isolation",
                    "• Understand and maintain",
                    "• Refactor safely",
                    "",
                    "💡 Consider dependency injection or interface abstraction",
                ]
            )

            data = {
                "cycles": cycles,
                "cycle_count": len(cycles),
                "workspace_path": workspace_path,
                "severity": "high" if len(cycles) > 5 else "medium" if len(cycles) > 1 else "low",
                "summary": "\n".join(summary_parts),
            }

            return {
                "status": "success",
                "type": "circular_dependency_analysis",
                "data": data,
                "message": f"Found {len(cycles)} circular dependencies",
                "confidence": 0.85,
            }

        except Exception as e:
            logger.error(f"Error finding circular dependencies: {e}")
            return {
                "status": "error",
                "message": f"Circular dependency analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def analyze_coupling(self, workspace_path: str) -> Dict[str, Any]:
        """
        Analyze coupling between components
        
        Extracted from: _analyze_coupling_tool()
        """
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0,
                }

            project_id = f"project_{hash(workspace_path)}"
            coupling_data = await graph_query_service.analyze_coupling(project_id)

            if not coupling_data:
                return {
                    "status": "error",
                    "message": "No coupling data available",
                    "confidence": 0.0,
                }

            # Generate summary
            avg_coupling = coupling_data.get("average_coupling", 0)
            high_coupling_files = coupling_data.get("highly_coupled_files", [])

            summary_parts = ["📊 Coupling Analysis Results:\n"]
            summary_parts.append(
                f"Average coupling: {avg_coupling:.1f} dependencies per file"
            )

            if not high_coupling_files:
                summary_parts.append("✅ No highly coupled files detected")
            else:
                summary_parts.append(
                    f"⚠️ {len(high_coupling_files)} highly coupled files:"
                )
                for file_info in high_coupling_files[:5]:
                    file_name = Path(file_info["file_name"]).name
                    coupling = file_info["total_coupling"]
                    summary_parts.append(
                        f"  • {file_name}: {coupling} total dependencies"
                    )

                if len(high_coupling_files) > 5:
                    summary_parts.append(
                        f"  ... and {len(high_coupling_files) - 5} more"
                    )

                summary_parts.extend(
                    [
                        "",
                        "💡 High coupling can indicate:",
                        "• God objects or classes",
                        "• Missing abstraction layers",
                        "• Opportunities for refactoring",
                    ]
                )

            # Determine coupling health
            coupling_health = "excellent" if avg_coupling < 3 else "good" if avg_coupling < 6 else "moderate" if avg_coupling < 10 else "poor"

            data = {
                "average_coupling": avg_coupling,
                "highly_coupled_files": high_coupling_files,
                "total_files_analyzed": coupling_data.get("total_files_analyzed", 0),
                "coupling_health": coupling_health,
                "workspace_path": workspace_path,
                "recommendations": self._generate_coupling_recommendations(avg_coupling, len(high_coupling_files)),
                "summary": "\n".join(summary_parts),
            }

            return {
                "status": "success",
                "type": "coupling_analysis",
                "data": data,
                "message": f"Coupling analysis completed - {coupling_health} coupling health",
                "confidence": 0.8,
            }

        except Exception as e:
            logger.error(f"Error analyzing coupling: {e}")
            return {
                "status": "error",
                "message": f"Coupling analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def find_hotspots(self, workspace_path: str) -> Dict[str, Any]:
        """
        Find code hotspots (frequently connected code)
        
        Extracted from: _find_hotspots_tool()
        """
        try:
            if not graph_service.initialized:
                return {
                    "status": "error",
                    "message": "Graph database not available",
                    "confidence": 0.0,
                }

            project_id = f"project_{hash(workspace_path)}"
            hotspots = await graph_query_service.find_hotspots(project_id)

            if not hotspots:
                return {
                    "status": "success",
                    "type": "hotspot_analysis",
                    "data": {
                        "hotspots": [],
                        "summary": "🎯 No critical hotspots detected. Code appears well-distributed.",
                    },
                    "message": "No hotspots found",
                    "confidence": 0.8,
                }

            # Generate summary
            summary_parts = [f"🔥 Found {len(hotspots)} code hotspots:\n"]

            for hotspot in hotspots[:5]:
                symbol_name = hotspot["symbol_name"]
                connections = hotspot["connection_count"]
                risk_level = hotspot["risk_level"]
                file_name = Path(hotspot["file_path"]).name

                risk_indicator = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                    risk_level, "⚪"
                )
                summary_parts.append(f"{risk_indicator} {symbol_name} ({file_name})")
                summary_parts.append(f"   {connections} connections, {risk_level} risk")

            if len(hotspots) > 5:
                summary_parts.append(f"... and {len(hotspots) - 5} more hotspots")

            summary_parts.extend(
                [
                    "",
                    "🎯 Hotspots are code that:",
                    "• Has many incoming/outgoing connections",
                    "• May be critical to system functionality", 
                    "• Requires careful testing when modified",
                    "",
                    "💡 Consider extra testing and documentation for hotspots",
                ]
            )

            # Analyze risk distribution
            risk_counts = {"low": 0, "medium": 0, "high": 0}
            for hotspot in hotspots:
                risk_level = hotspot.get("risk_level", "low")
                risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

            data = {
                "hotspots": hotspots,
                "hotspot_count": len(hotspots),
                "risk_distribution": risk_counts,
                "workspace_path": workspace_path,
                "recommendations": self._generate_hotspot_recommendations(hotspots),
                "summary": "\n".join(summary_parts),
            }

            return {
                "status": "success",
                "type": "hotspot_analysis",
                "data": data,
                "message": f"Found {len(hotspots)} hotspots ({risk_counts['high']} high risk)",
                "confidence": 0.85,
            }

        except Exception as e:
            logger.error(f"Error finding hotspots: {e}")
            return {
                "status": "error",
                "message": f"Hotspot analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def suggest_refactoring(self, workspace_path: str, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Suggest refactoring opportunities based on architecture analysis
        
        Enhanced from: _suggest_refactoring_tool()
        """
        try:
            suggestions = []
            confidence_score = 0.6
            
            # Get coupling analysis
            coupling_result = await self.analyze_coupling(workspace_path)
            if coupling_result["status"] == "success":
                coupling_data = coupling_result["data"]
                high_coupling_files = coupling_data.get("highly_coupled_files", [])
                
                if high_coupling_files:
                    suggestions.append({
                        "type": "reduce_coupling",
                        "priority": "high",
                        "description": "Break down highly coupled files into smaller, focused modules",
                        "affected_files": [f["file_name"] for f in high_coupling_files[:3]],
                        "estimated_effort": "medium",
                        "benefits": ["Improved maintainability", "Better testability", "Reduced complexity"]
                    })
                    confidence_score += 0.2
            
            # Get circular dependencies
            circular_result = await self.find_circular_dependencies(workspace_path)
            if circular_result["status"] == "success":
                circular_data = circular_result["data"]
                cycles = circular_data.get("cycles", [])
                
                if cycles:
                    suggestions.append({
                        "type": "eliminate_cycles",
                        "priority": "high",
                        "description": "Remove circular dependencies using dependency injection or interfaces",
                        "affected_cycles": cycles[:2],  # Show first 2 cycles
                        "estimated_effort": "high",
                        "benefits": ["Better modularity", "Easier testing", "Cleaner architecture"]
                    })
                    confidence_score += 0.2
            
            # Get hotspots
            hotspots_result = await self.find_hotspots(workspace_path)
            if hotspots_result["status"] == "success":
                hotspots_data = hotspots_result["data"]
                high_risk_hotspots = [h for h in hotspots_data.get("hotspots", []) if h.get("risk_level") == "high"]
                
                if high_risk_hotspots:
                    suggestions.append({
                        "type": "refactor_hotspots",
                        "priority": "medium",
                        "description": "Add comprehensive testing and documentation for critical hotspots",
                        "affected_hotspots": [h["symbol_name"] for h in high_risk_hotspots[:3]],
                        "estimated_effort": "low",
                        "benefits": ["Reduced risk", "Better documentation", "Improved confidence in changes"]
                    })
                    confidence_score += 0.1
            
            # Target-specific suggestions
            if target:
                suggestions.append({
                    "type": "targeted_analysis",
                    "priority": "medium",
                    "description": f"Perform detailed analysis of {target} for specific refactoring opportunities",
                    "target": target,
                    "estimated_effort": "low",
                    "benefits": ["Focused improvements", "Targeted optimization"]
                })
                confidence_score += 0.1
            
            if not suggestions:
                summary = "✅ Code architecture appears well-structured. No critical refactoring opportunities identified."
            else:
                summary_parts = [f"🔧 Found {len(suggestions)} refactoring opportunities:\n"]
                for i, suggestion in enumerate(suggestions, 1):
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion["priority"], "⚪")
                    summary_parts.append(f"{i}. {priority_icon} {suggestion['type'].replace('_', ' ').title()}")
                    summary_parts.append(f"   {suggestion['description']}")
                    summary_parts.append(f"   Priority: {suggestion['priority']}, Effort: {suggestion['estimated_effort']}")
                    summary_parts.append("")
                
                summary_parts.append("💡 Prioritize high-priority items for maximum impact")
                summary = "\n".join(summary_parts)

            data = {
                "suggestions": suggestions,
                "total_suggestions": len(suggestions),
                "workspace_path": workspace_path,
                "target": target,
                "analysis_timestamp": "2024-06-30",  # Could use actual timestamp
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "refactoring_suggestions",
                "data": data,
                "message": f"Generated {len(suggestions)} refactoring suggestions",
                "confidence": min(1.0, confidence_score),
            }

        except Exception as e:
            logger.error(f"Error suggesting refactoring: {e}")
            return {
                "status": "error",
                "message": f"Refactoring analysis failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_architecture_summary(self, workspace_path: str) -> Dict[str, Any]:
        """
        Generate comprehensive architecture summary combining all analyses
        """
        try:
            summary_data = {
                "workspace_path": workspace_path,
                "analyses_completed": 0,
                "overall_health": "unknown"
            }
            
            health_scores = []
            issues_found = []
            
            # Architecture patterns
            try:
                patterns_result = await self.detect_architecture_patterns(workspace_path)
                if patterns_result["status"] == "success":
                    summary_data["architecture_patterns"] = patterns_result["data"]
                    summary_data["analyses_completed"] += 1
                    
                    pattern_count = len(patterns_result["data"].get("patterns", []))
                    if pattern_count > 0:
                        health_scores.append(0.8)  # Good if patterns detected
                    else:
                        health_scores.append(0.6)  # Neutral if no patterns
            except Exception as e:
                logger.warning(f"Architecture pattern analysis failed: {e}")
            
            # Circular dependencies
            try:
                circular_result = await self.find_circular_dependencies(workspace_path)
                if circular_result["status"] == "success":
                    summary_data["circular_dependencies"] = circular_result["data"]
                    summary_data["analyses_completed"] += 1
                    
                    cycle_count = circular_result["data"].get("cycle_count", 0)
                    if cycle_count == 0:
                        health_scores.append(1.0)  # Excellent
                    elif cycle_count <= 2:
                        health_scores.append(0.7)  # Good
                        issues_found.append(f"{cycle_count} circular dependencies")
                    else:
                        health_scores.append(0.3)  # Poor
                        issues_found.append(f"{cycle_count} circular dependencies (critical)")
            except Exception as e:
                logger.warning(f"Circular dependency analysis failed: {e}")
            
            # Coupling analysis
            try:
                coupling_result = await self.analyze_coupling(workspace_path)
                if coupling_result["status"] == "success":
                    summary_data["coupling_analysis"] = coupling_result["data"]
                    summary_data["analyses_completed"] += 1
                    
                    coupling_health = coupling_result["data"].get("coupling_health", "unknown")
                    if coupling_health == "excellent":
                        health_scores.append(1.0)
                    elif coupling_health == "good":
                        health_scores.append(0.8)
                    elif coupling_health == "moderate":
                        health_scores.append(0.6)
                        issues_found.append("Moderate coupling detected")
                    else:
                        health_scores.append(0.4)
                        issues_found.append("High coupling detected")
            except Exception as e:
                logger.warning(f"Coupling analysis failed: {e}")
            
            # Hotspots
            try:
                hotspots_result = await self.find_hotspots(workspace_path)
                if hotspots_result["status"] == "success":
                    summary_data["hotspots"] = hotspots_result["data"]
                    summary_data["analyses_completed"] += 1
                    
                    risk_dist = hotspots_result["data"].get("risk_distribution", {})
                    high_risk = risk_dist.get("high", 0)
                    if high_risk == 0:
                        health_scores.append(0.9)
                    elif high_risk <= 2:
                        health_scores.append(0.7)
                        issues_found.append(f"{high_risk} high-risk hotspots")
                    else:
                        health_scores.append(0.5)
                        issues_found.append(f"{high_risk} high-risk hotspots (review needed)")
            except Exception as e:
                logger.warning(f"Hotspot analysis failed: {e}")
            
            # Calculate overall health
            if health_scores:
                avg_health = sum(health_scores) / len(health_scores)
                if avg_health >= 0.9:
                    summary_data["overall_health"] = "excellent"
                elif avg_health >= 0.7:
                    summary_data["overall_health"] = "good"
                elif avg_health >= 0.5:
                    summary_data["overall_health"] = "moderate"
                else:
                    summary_data["overall_health"] = "needs_attention"
            
            # Generate summary text
            health_icon = {
                "excellent": "🟢",
                "good": "🟡", 
                "moderate": "🟠",
                "needs_attention": "🔴",
                "unknown": "⚪"
            }.get(summary_data["overall_health"], "⚪")
            
            summary_text = f"""{health_icon} Architecture Health: {summary_data["overall_health"].replace('_', ' ').title()}

📊 Analysis Summary:
• Completed analyses: {summary_data["analyses_completed"]}/4
• Overall health score: {(sum(health_scores) / max(len(health_scores), 1)):.1%}
• Issues identified: {len(issues_found)}

"""
            
            if issues_found:
                summary_text += "⚠️ Issues Found:\n"
                for issue in issues_found:
                    summary_text += f"• {issue}\n"
                summary_text += "\n"
            
            summary_text += """💡 Recommendations:
• Run refactoring analysis for specific improvement suggestions
• Monitor architecture health regularly
• Address high-priority issues first"""

            summary_data["issues_found"] = issues_found
            summary_data["health_score"] = sum(health_scores) / max(len(health_scores), 1)
            summary_data["summary"] = summary_text

            return {
                "status": "success",
                "type": "architecture_summary",
                "data": summary_data,
                "message": f"Architecture summary complete - {summary_data['overall_health']} health",
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error generating architecture summary: {e}")
            return {
                "status": "error",
                "message": f"Architecture summary failed: {str(e)}",
                "confidence": 0.0,
            }
    
    def _generate_coupling_recommendations(self, avg_coupling: float, high_coupling_count: int) -> List[str]:
        """Generate coupling-specific recommendations"""
        recommendations = []
        
        if avg_coupling > 10:
            recommendations.append("Consider breaking down large files into smaller, focused modules")
            recommendations.append("Implement dependency injection to reduce tight coupling")
        elif avg_coupling > 6:
            recommendations.append("Review file dependencies and extract common functionality")
            recommendations.append("Consider using interfaces to decouple implementations")
        
        if high_coupling_count > 5:
            recommendations.append("Prioritize refactoring the most highly coupled files")
            recommendations.append("Apply the Single Responsibility Principle")
        elif high_coupling_count > 0:
            recommendations.append("Review highly coupled files for refactoring opportunities")
        
        return recommendations
    
    def _generate_hotspot_recommendations(self, hotspots: List[Dict[str, Any]]) -> List[str]:
        """Generate hotspot-specific recommendations"""
        recommendations = []
        
        high_risk_count = len([h for h in hotspots if h.get("risk_level") == "high"])
        
        if high_risk_count > 3:
            recommendations.append("Add comprehensive unit tests for high-risk hotspots")
            recommendations.append("Document the critical functionality and dependencies")
            recommendations.append("Consider refactoring to reduce complexity")
        elif high_risk_count > 0:
            recommendations.append("Ensure adequate test coverage for hotspot components")
            recommendations.append("Add monitoring for critical functionality")
        
        if len(hotspots) > 10:
            recommendations.append("Review overall architecture for better distribution of responsibilities")
        
        return recommendations