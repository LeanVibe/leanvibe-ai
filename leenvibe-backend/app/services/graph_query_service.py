"""
Graph Query Service

Advanced query interface for code relationship analysis, impact assessment,
and architecture pattern detection using the Neo4j graph database.
"""

import logging
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from ..models.graph_models import (
    ArchitecturePattern,
    GraphQuery,
    GraphVisualizationData,
    ImpactAnalysisResult,
    RelationshipType,
)
from .graph_service import graph_service

logger = logging.getLogger(__name__)


class GraphQueryService:
    """
    Advanced Graph Query Service

    Provides sophisticated querying capabilities for code analysis,
    including impact analysis, architecture detection, and refactoring suggestions.
    """

    def __init__(self):
        self.graph_service = graph_service
        self.query_cache = {}
        self.cache_timeout = 300  # 5 minutes

    async def find_call_chains(
        self, source_symbol: str, target_symbol: str, max_depth: int = 5
    ) -> List[List[str]]:
        """Find all call chains between two symbols"""
        try:
            if not self.graph_service.initialized:
                return []

            query = """
            MATCH path = (source {id: $source_id})-[:CALLS*1..$max_depth]->(target {id: $target_id})
            RETURN [node in nodes(path) | node.name] as call_chain,
                   length(path) as chain_length
            ORDER BY chain_length
            LIMIT 10
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(
                    query,
                    source_id=source_symbol,
                    target_id=target_symbol,
                    max_depth=max_depth,
                )

                call_chains = []
                for record in result:
                    call_chains.append(record["call_chain"])

                return call_chains

        except Exception as e:
            logger.error(f"Error finding call chains: {e}")
            return []

    async def find_circular_dependencies(self, project_id: str) -> List[List[str]]:
        """Find circular dependencies in the project"""
        try:
            if not self.graph_service.initialized:
                return []

            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(start:File)
            MATCH path = (start)-[:DEPENDS_ON*2..]->(start)
            WHERE ALL(node in nodes(path) WHERE node.id STARTS WITH 'file_')
            RETURN [node in nodes(path) | node.name] as cycle,
                   length(path) as cycle_length
            ORDER BY cycle_length
            LIMIT 20
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(query, project_id=project_id)

                cycles = []
                for record in result:
                    cycles.append(record["cycle"])

                return cycles

        except Exception as e:
            logger.error(f"Error finding circular dependencies: {e}")
            return []

    async def analyze_coupling(self, project_id: str) -> Dict[str, Any]:
        """Analyze coupling between components"""
        try:
            if not self.graph_service.initialized:
                return {}

            # Find highly coupled files (many incoming/outgoing dependencies)
            coupling_query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(f:File)
            OPTIONAL MATCH (f)-[out:DEPENDS_ON|CALLS]->()
            OPTIONAL MATCH ()-[in:DEPENDS_ON|CALLS]->(f)
            RETURN f.name as file_name, f.id as file_id,
                   count(DISTINCT out) as outgoing_deps,
                   count(DISTINCT in) as incoming_deps,
                   count(DISTINCT out) + count(DISTINCT in) as total_coupling
            ORDER BY total_coupling DESC
            LIMIT 20
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(coupling_query, project_id=project_id)

                coupling_data = []
                total_coupling = 0

                for record in result:
                    file_coupling = {
                        "file_name": record["file_name"],
                        "file_id": record["file_id"],
                        "outgoing_dependencies": record["outgoing_deps"],
                        "incoming_dependencies": record["incoming_deps"],
                        "total_coupling": record["total_coupling"],
                    }
                    coupling_data.append(file_coupling)
                    total_coupling += record["total_coupling"]

                # Calculate average coupling
                avg_coupling = (
                    total_coupling / len(coupling_data) if coupling_data else 0
                )

                # Identify high coupling files (above average)
                high_coupling_files = [
                    f for f in coupling_data if f["total_coupling"] > avg_coupling * 1.5
                ]

                return {
                    "average_coupling": avg_coupling,
                    "highly_coupled_files": high_coupling_files,
                    "coupling_distribution": coupling_data,
                    "total_files_analyzed": len(coupling_data),
                }

        except Exception as e:
            logger.error(f"Error analyzing coupling: {e}")
            return {}

    async def find_dead_code(self, project_id: str) -> List[Dict[str, Any]]:
        """Find potentially dead code (unreferenced symbols)"""
        try:
            if not self.graph_service.initialized:
                return []

            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(:File)-[:DEFINES]->(symbol)
            WHERE NOT ()-[:CALLS|USES|REFERENCES]->(symbol)
            AND symbol.name IS NOT NULL
            AND NOT symbol.name IN ['main', '__init__', 'setup', 'teardown']
            RETURN symbol.id as symbol_id, symbol.name as symbol_name,
                   symbol.file_path as file_path, labels(symbol) as symbol_types
            ORDER BY symbol.name
            LIMIT 50
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(query, project_id=project_id)

                dead_code = []
                for record in result:
                    dead_code.append(
                        {
                            "symbol_id": record["symbol_id"],
                            "symbol_name": record["symbol_name"],
                            "file_path": record["file_path"],
                            "symbol_types": record["symbol_types"],
                            "confidence": self._calculate_dead_code_confidence(
                                record["symbol_name"]
                            ),
                        }
                    )

                return dead_code

        except Exception as e:
            logger.error(f"Error finding dead code: {e}")
            return []

    def _calculate_dead_code_confidence(self, symbol_name: str) -> float:
        """Calculate confidence that a symbol is actually dead code"""
        confidence = 0.8  # Base confidence

        # Lower confidence for common patterns that might be used externally
        if any(
            pattern in symbol_name.lower()
            for pattern in ["test", "example", "demo", "util", "helper", "config"]
        ):
            confidence *= 0.6

        # Lower confidence for public-looking methods
        if not symbol_name.startswith("_"):
            confidence *= 0.7

        # Higher confidence for private methods
        if symbol_name.startswith("__"):
            confidence *= 1.2

        return min(confidence, 0.95)

    async def suggest_refactoring_opportunities(
        self, project_id: str
    ) -> List[Dict[str, Any]]:
        """Suggest refactoring opportunities based on code structure"""
        try:
            suggestions = []

            # Find large classes (many methods)
            large_classes = await self._find_large_classes(project_id)
            if large_classes:
                suggestions.append(
                    {
                        "type": "large_class",
                        "title": "Large Classes Detected",
                        "description": "Consider breaking down large classes into smaller, more focused classes",
                        "items": large_classes,
                        "priority": "medium",
                    }
                )

            # Find long parameter lists
            long_params = await self._find_long_parameter_lists(project_id)
            if long_params:
                suggestions.append(
                    {
                        "type": "long_parameters",
                        "title": "Long Parameter Lists",
                        "description": "Consider introducing parameter objects or configuration classes",
                        "items": long_params,
                        "priority": "low",
                    }
                )

            # Find duplicated code patterns
            # Note: This would require more sophisticated analysis
            # For now, we'll suggest based on similar function names
            similar_functions = await self._find_similar_functions(project_id)
            if similar_functions:
                suggestions.append(
                    {
                        "type": "potential_duplication",
                        "title": "Potential Code Duplication",
                        "description": "Similar function names might indicate duplicated logic",
                        "items": similar_functions,
                        "priority": "medium",
                    }
                )

            return suggestions

        except Exception as e:
            logger.error(f"Error suggesting refactoring opportunities: {e}")
            return []

    async def _find_large_classes(self, project_id: str) -> List[Dict[str, Any]]:
        """Find classes with many methods"""
        try:
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(:File)-[:DEFINES]->(class:Class)
            OPTIONAL MATCH (class)<-[:CONTAINS]-(method)
            WHERE method:Method OR method:Function
            RETURN class.name as class_name, class.file_path as file_path,
                   count(method) as method_count
            HAVING method_count > 10
            ORDER BY method_count DESC
            LIMIT 10
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(query, project_id=project_id)

                large_classes = []
                for record in result:
                    large_classes.append(
                        {
                            "class_name": record["class_name"],
                            "file_path": record["file_path"],
                            "method_count": record["method_count"],
                        }
                    )

                return large_classes

        except Exception as e:
            logger.error(f"Error finding large classes: {e}")
            return []

    async def _find_long_parameter_lists(self, project_id: str) -> List[Dict[str, Any]]:
        """Find functions with many parameters"""
        try:
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(:File)-[:DEFINES]->(func)
            WHERE (func:Function OR func:Method) 
            AND size(func.parameters) > 5
            RETURN func.name as function_name, func.file_path as file_path,
                   size(func.parameters) as parameter_count, func.parameters as parameters
            ORDER BY parameter_count DESC
            LIMIT 15
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(query, project_id=project_id)

                long_params = []
                for record in result:
                    long_params.append(
                        {
                            "function_name": record["function_name"],
                            "file_path": record["file_path"],
                            "parameter_count": record["parameter_count"],
                            "parameters": record["parameters"],
                        }
                    )

                return long_params

        except Exception as e:
            logger.error(f"Error finding long parameter lists: {e}")
            return []

    async def _find_similar_functions(self, project_id: str) -> List[Dict[str, Any]]:
        """Find functions with similar names that might indicate duplication"""
        try:
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(:File)-[:DEFINES]->(func1)
            MATCH (p)-[:CONTAINS]->(:File)-[:DEFINES]->(func2)
            WHERE (func1:Function OR func1:Method) 
            AND (func2:Function OR func2:Method)
            AND func1.id < func2.id
            AND func1.name CONTAINS func2.name[0..3]
            OR func2.name CONTAINS func1.name[0..3]
            RETURN func1.name as name1, func1.file_path as file1,
                   func2.name as name2, func2.file_path as file2
            LIMIT 20
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(query, project_id=project_id)

                similar_functions = []
                for record in result:
                    similar_functions.append(
                        {
                            "function1": {
                                "name": record["name1"],
                                "file": record["file1"],
                            },
                            "function2": {
                                "name": record["name2"],
                                "file": record["file2"],
                            },
                            "similarity_reason": "Similar names",
                        }
                    )

                return similar_functions

        except Exception as e:
            logger.error(f"Error finding similar functions: {e}")
            return []

    async def analyze_test_coverage_gaps(self, project_id: str) -> Dict[str, Any]:
        """Analyze gaps in test coverage based on call relationships"""
        try:
            if not self.graph_service.initialized:
                return {}

            # Find functions that are not called by test functions
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(:File)-[:DEFINES]->(func)
            WHERE (func:Function OR func:Method)
            AND NOT func.file_path CONTAINS 'test'
            AND NOT ()-[:CALLS]->(func) 
            OR NOT EXISTS {
                MATCH (:File)-[:DEFINES]->(test_func)-[:CALLS]->(func)
                WHERE test_func.file_path CONTAINS 'test'
            }
            RETURN func.name as function_name, func.file_path as file_path,
                   func.visibility as visibility
            ORDER BY func.name
            LIMIT 50
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(query, project_id=project_id)

                untested_functions = []
                for record in result:
                    # Filter out private functions and getters/setters
                    func_name = record["function_name"]
                    if (
                        not func_name.startswith("_")
                        and not func_name.startswith("get")
                        and not func_name.startswith("set")
                    ):
                        untested_functions.append(
                            {
                                "function_name": func_name,
                                "file_path": record["file_path"],
                                "visibility": record["visibility"],
                            }
                        )

                return {
                    "untested_functions": untested_functions,
                    "coverage_gap_count": len(untested_functions),
                    "recommendations": self._generate_test_recommendations(
                        len(untested_functions)
                    ),
                }

        except Exception as e:
            logger.error(f"Error analyzing test coverage gaps: {e}")
            return {}

    def _generate_test_recommendations(self, gap_count: int) -> List[str]:
        """Generate test coverage recommendations"""
        recommendations = []

        if gap_count == 0:
            recommendations.append("✅ Good test coverage detected")
        elif gap_count < 5:
            recommendations.append(
                "⚡ Minor test coverage gaps - consider adding a few more tests"
            )
        elif gap_count < 15:
            recommendations.append(
                "⚠️ Moderate test coverage gaps - prioritize testing key functions"
            )
        else:
            recommendations.extend(
                [
                    "🚨 Significant test coverage gaps detected",
                    "Consider implementing a comprehensive testing strategy",
                    "Start with testing core business logic functions",
                    "Use test-driven development for new features",
                ]
            )

        return recommendations

    async def find_hotspots(self, project_id: str) -> List[Dict[str, Any]]:
        """Find code hotspots (frequently changed or highly connected code)"""
        try:
            if not self.graph_service.initialized:
                return []

            # Find highly connected nodes (high degree centrality)
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(:File)-[:DEFINES]->(symbol)
            OPTIONAL MATCH (symbol)-[out]->()
            OPTIONAL MATCH ()-[in]->(symbol)
            RETURN symbol.name as symbol_name, symbol.file_path as file_path,
                   labels(symbol) as symbol_types,
                   count(DISTINCT out) + count(DISTINCT in) as connection_count
            ORDER BY connection_count DESC
            LIMIT 20
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(query, project_id=project_id)

                hotspots = []
                for record in result:
                    if (
                        record["connection_count"] > 3
                    ):  # Only include well-connected nodes
                        hotspots.append(
                            {
                                "symbol_name": record["symbol_name"],
                                "file_path": record["file_path"],
                                "symbol_types": record["symbol_types"],
                                "connection_count": record["connection_count"],
                                "hotspot_type": "highly_connected",
                                "risk_level": self._calculate_hotspot_risk(
                                    record["connection_count"]
                                ),
                            }
                        )

                return hotspots

        except Exception as e:
            logger.error(f"Error finding hotspots: {e}")
            return []

    def _calculate_hotspot_risk(self, connection_count: int) -> str:
        """Calculate risk level for hotspots"""
        if connection_count < 5:
            return "low"
        elif connection_count < 10:
            return "medium"
        else:
            return "high"

    async def get_component_boundaries(self, project_id: str) -> Dict[str, List[str]]:
        """Identify natural component boundaries in the codebase"""
        try:
            if not self.graph_service.initialized:
                return {}

            # Group files by directory structure and analyze internal vs external dependencies
            query = """
            MATCH (p:Project {id: $project_id})-[:CONTAINS]->(f1:File)
            OPTIONAL MATCH (f1)-[:DEPENDS_ON]->(f2:File)
            RETURN f1.file_path as source_file, f2.file_path as target_file
            """

            with self.graph_service.driver.session(
                database=self.graph_service.database
            ) as session:
                result = session.run(query, project_id=project_id)

                # Build component map based on directory structure
                components = defaultdict(set)
                dependencies = []

                for record in result:
                    source = record["source_file"]
                    target = record["target_file"]

                    if source:
                        source_dir = str(Path(source).parent)
                        components[source_dir].add(source)

                    if source and target:
                        dependencies.append((source, target))

                # Analyze cross-component dependencies
                component_boundaries = {}
                for component, files in components.items():
                    if len(files) > 1:  # Only include components with multiple files
                        component_boundaries[component] = list(files)

                return component_boundaries

        except Exception as e:
            logger.error(f"Error getting component boundaries: {e}")
            return {}


# Global instance
graph_query_service = GraphQueryService()
