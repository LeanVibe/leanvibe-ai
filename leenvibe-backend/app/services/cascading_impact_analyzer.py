"""
Cascading Impact Analysis Service

Analyzes impact of changes across project boundaries, tracking how changes
in one project affect dependent projects and external consumers.
"""

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .project_indexer import project_indexer
from .symbol_dependency_tracker import (
    DependencyType,
    symbol_dependency_tracker,
)

logger = logging.getLogger(__name__)


class ProjectBoundaryType(str, Enum):
    """Types of project boundaries"""

    INTERNAL = "internal"  # Within same project
    WORKSPACE = "workspace"  # Within same workspace/monorepo
    EXTERNAL = "external"  # External dependency
    PUBLISHED = "published"  # Published package/library
    SYSTEM = "system"  # System library


class ImpactPropagation(str, Enum):
    """How impact propagates across boundaries"""

    DIRECT = "direct"  # Direct dependency
    TRANSITIVE = "transitive"  # Through intermediate dependencies
    RUNTIME = "runtime"  # Runtime dependency
    BUILD_TIME = "build_time"  # Build-time dependency
    OPTIONAL = "optional"  # Optional dependency


class ChangeCompatibility(str, Enum):
    """Compatibility assessment of changes"""

    COMPATIBLE = "compatible"
    BACKWARD_COMPATIBLE = "backward_compatible"
    BREAKING = "breaking"
    POTENTIALLY_BREAKING = "potentially_breaking"
    UNKNOWN = "unknown"


@dataclass
class ProjectBoundary:
    """Represents a boundary between projects"""

    boundary_id: str
    source_project: str
    target_project: str
    boundary_type: ProjectBoundaryType
    dependencies: List[str] = field(default_factory=list)  # Symbol IDs
    version_constraint: Optional[str] = None
    is_published: bool = False
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CrossProjectDependency:
    """Dependency that crosses project boundaries"""

    dependency_id: str
    source_symbol_id: str
    target_symbol_id: str
    source_project: str
    target_project: str
    dependency_type: DependencyType
    propagation_type: ImpactPropagation
    version_requirement: Optional[str] = None
    is_breaking_change_risk: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CascadingImpact:
    """Impact that cascades across project boundaries"""

    impact_id: str
    origin_symbol_id: str
    origin_project: str
    change_type: str
    affected_projects: Dict[str, List[str]] = field(
        default_factory=dict
    )  # project -> symbol_ids
    propagation_paths: List[List[str]] = field(
        default_factory=list
    )  # Paths of propagation
    total_affected_symbols: int = 0
    max_propagation_depth: int = 0
    compatibility_assessment: ChangeCompatibility = ChangeCompatibility.UNKNOWN
    breaking_changes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    estimated_effort_hours: float = 0.0


@dataclass
class ProjectDependencyGraph:
    """Graph of dependencies between projects"""

    projects: Dict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )  # project -> dependent projects
    reverse_dependencies: Dict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )  # project -> projects that depend on it
    boundaries: Dict[str, ProjectBoundary] = field(default_factory=dict)
    external_dependencies: Dict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )  # project -> external deps


@dataclass
class ImpactSummary:
    """Summary of cascading impact analysis"""

    total_projects_affected: int
    total_symbols_affected: int
    critical_paths: List[List[str]]  # Most critical propagation paths
    risk_assessment: str  # Low, Medium, High, Critical
    migration_strategy: Optional[str] = None
    rollback_plan: Optional[str] = None
    communication_plan: List[str] = field(default_factory=list)  # Who to notify


class CascadingImpactAnalyzer:
    """
    Cascading Impact Analysis Service

    Analyzes how changes propagate across project boundaries,
    identifying breaking changes and migration requirements.
    """

    def __init__(self):
        # Project dependency tracking
        self.project_graph = ProjectDependencyGraph()
        self.cross_project_dependencies: Dict[str, CrossProjectDependency] = {}
        self.project_boundaries: Dict[str, ProjectBoundary] = {}

        # Impact analysis state
        self.cascading_impacts: List[CascadingImpact] = []
        self.active_analyses: Dict[str, CascadingImpact] = {}
        self.impact_cache: Dict[str, ImpactSummary] = {}

        # Configuration
        self.max_propagation_depth = 20
        self.impact_threshold = 0.3
        self.breaking_change_patterns = [
            "signature_changed",
            "removed",
            "moved",
            "visibility_reduced",
            "return_type_changed",
        ]
        self.external_project_patterns = [
            "**/node_modules/**",
            "**/site-packages/**",
            "**/vendor/**",
            "**/.cargo/**",
        ]

        # Performance metrics
        self.metrics = {
            "total_analyses": 0,
            "cross_project_impacts": 0,
            "breaking_changes_detected": 0,
            "average_propagation_depth": 0.0,
            "average_analysis_time_ms": 0.0,
            "cache_hit_rate": 0.0,
        }

        # Background tasks
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.analysis_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the cascading impact analyzer"""
        try:
            logger.info("Initializing Cascading Impact Analyzer...")

            # Start background analysis processor
            self.analysis_task = asyncio.create_task(
                self._background_analysis_processor()
            )

            logger.info("Cascading impact analyzer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing cascading impact analyzer: {e}")
            return False

    async def shutdown(self):
        """Shutdown the cascading impact analyzer"""
        try:
            logger.info("Shutting down cascading impact analyzer...")

            # Cancel background task
            if self.analysis_task:
                self.analysis_task.cancel()
                try:
                    await self.analysis_task
                except asyncio.CancelledError:
                    pass

            logger.info("Cascading impact analyzer shutdown complete")

        except Exception as e:
            logger.error(f"Error during cascading impact analyzer shutdown: {e}")

    async def register_project_boundary(
        self,
        source_project: str,
        target_project: str,
        boundary_type: ProjectBoundaryType,
        dependencies: List[str],
        version_constraint: Optional[str] = None,
    ) -> bool:
        """Register a boundary between projects"""
        try:
            boundary_id = f"{source_project}->{target_project}"

            boundary = ProjectBoundary(
                boundary_id=boundary_id,
                source_project=source_project,
                target_project=target_project,
                boundary_type=boundary_type,
                dependencies=dependencies,
                version_constraint=version_constraint,
                is_published=boundary_type == ProjectBoundaryType.PUBLISHED,
            )

            # Update project graph
            self.project_boundaries[boundary_id] = boundary
            self.project_graph.projects[source_project].add(target_project)
            self.project_graph.reverse_dependencies[target_project].add(source_project)

            if boundary_type == ProjectBoundaryType.EXTERNAL:
                self.project_graph.external_dependencies[source_project].add(
                    target_project
                )

            logger.debug(
                f"Registered project boundary: {boundary_id} ({boundary_type})"
            )
            return True

        except Exception as e:
            logger.error(f"Error registering project boundary: {e}")
            return False

    async def analyze_cascading_impact(
        self,
        symbol_id: str,
        project_id: str,
        change_type: str,
        include_external: bool = False,
    ) -> CascadingImpact:
        """Analyze cascading impact across project boundaries"""
        try:
            start_time = time.time()

            # Check cache
            cache_key = f"{symbol_id}:{project_id}:{change_type}"
            if cache_key in self.impact_cache:
                self.metrics["cache_hit_rate"] += 1
                return self._create_impact_from_cache(cache_key)

            # Create impact analysis
            impact = CascadingImpact(
                impact_id=self._generate_impact_id(),
                origin_symbol_id=symbol_id,
                origin_project=project_id,
                change_type=change_type,
            )

            # Analyze propagation
            await self._analyze_propagation(
                impact, symbol_id, project_id, include_external=include_external
            )

            # Assess compatibility
            impact.compatibility_assessment = self._assess_compatibility(
                change_type, impact.breaking_changes
            )

            # Generate recommendations
            impact.recommendations = self._generate_recommendations(impact)

            # Estimate effort
            impact.estimated_effort_hours = self._estimate_effort(impact)

            # Cache result
            self._cache_impact(cache_key, impact)

            # Update metrics
            self._update_metrics(impact, time.time() - start_time)

            # Store impact
            self.cascading_impacts.append(impact)

            logger.info(
                f"Cascading impact analysis complete: {len(impact.affected_projects)} projects, "
                f"{impact.total_affected_symbols} symbols affected"
            )

            return impact

        except Exception as e:
            logger.error(f"Error analyzing cascading impact: {e}")
            return CascadingImpact(
                impact_id="error",
                origin_symbol_id=symbol_id,
                origin_project=project_id,
                change_type=change_type,
            )

    async def _analyze_propagation(
        self,
        impact: CascadingImpact,
        symbol_id: str,
        project_id: str,
        include_external: bool = False,
    ):
        """Analyze how impact propagates across projects"""
        visited_symbols = set()
        visited_projects = {project_id}

        # BFS for propagation analysis
        queue = deque([(symbol_id, project_id, 0, [symbol_id])])

        while queue and len(visited_projects) < 100:  # Limit scope
            current_symbol, current_project, depth, path = queue.popleft()

            if depth > self.max_propagation_depth:
                continue

            if current_symbol in visited_symbols:
                continue

            visited_symbols.add(current_symbol)

            # Get symbol dependencies from tracker
            deps = await symbol_dependency_tracker.get_symbol_dependencies(
                current_symbol, depth=1
            )

            # Process direct dependents
            for dependent_info in deps.get("direct_dependents", []):
                dependent_id = dependent_info["symbol_id"]
                dependent_symbol = dependent_info.get("symbol")

                if not dependent_symbol:
                    continue

                # Determine project of dependent
                dependent_project = self._get_symbol_project(
                    dependent_symbol.get("file_path", "")
                )

                # Skip external if not requested
                if not include_external and self._is_external_project(
                    dependent_project
                ):
                    continue

                # Track affected projects and symbols
                if dependent_project not in impact.affected_projects:
                    impact.affected_projects[dependent_project] = []

                if dependent_id not in impact.affected_projects[dependent_project]:
                    impact.affected_projects[dependent_project].append(dependent_id)
                    impact.total_affected_symbols += 1

                # Check for breaking changes
                if self._is_breaking_change(impact.change_type, dependent_info):
                    impact.breaking_changes.append(dependent_id)

                # Track propagation path
                new_path = path + [dependent_id]
                if dependent_project != current_project:
                    impact.propagation_paths.append(new_path)

                # Continue propagation
                if dependent_id not in visited_symbols:
                    queue.append((dependent_id, dependent_project, depth + 1, new_path))

            # Update max depth
            impact.max_propagation_depth = max(impact.max_propagation_depth, depth)

    async def find_cross_project_dependencies(
        self, project_id: str, depth: int = 1
    ) -> Dict[str, List[CrossProjectDependency]]:
        """Find all cross-project dependencies for a project"""
        try:
            dependencies = defaultdict(list)

            # Get project index
            project_index = await project_indexer.get_project_index(project_id)
            if not project_index:
                return dependencies

            # Analyze each file
            for file_path, file_analysis in project_index.files.items():
                for symbol in file_analysis.symbols:
                    # Get symbol dependencies
                    symbol_deps = (
                        await symbol_dependency_tracker.get_symbol_dependencies(
                            symbol.id, depth=depth
                        )
                    )

                    # Check each dependency
                    for dep_info in symbol_deps.get("direct_dependencies", []):
                        dep_symbol = dep_info.get("symbol")
                        if not dep_symbol:
                            continue

                        dep_project = self._get_symbol_project(
                            dep_symbol.get("file_path", "")
                        )

                        # If different project, create cross-project dependency
                        if dep_project != project_id:
                            cross_dep = CrossProjectDependency(
                                dependency_id=f"{symbol.id}->{dep_info['symbol_id']}",
                                source_symbol_id=symbol.id,
                                target_symbol_id=dep_info["symbol_id"],
                                source_project=project_id,
                                target_project=dep_project,
                                dependency_type=dep_info.get(
                                    "dependency_type", DependencyType.UNKNOWN
                                ),
                                propagation_type=ImpactPropagation.DIRECT,
                            )

                            dependencies[dep_project].append(cross_dep)
                            self.cross_project_dependencies[cross_dep.dependency_id] = (
                                cross_dep
                            )

            return dependencies

        except Exception as e:
            logger.error(f"Error finding cross-project dependencies: {e}")
            return {}

    async def generate_impact_summary(
        self, impacts: List[CascadingImpact]
    ) -> ImpactSummary:
        """Generate summary of multiple cascading impacts"""
        try:
            if not impacts:
                return ImpactSummary(
                    total_projects_affected=0,
                    total_symbols_affected=0,
                    critical_paths=[],
                    risk_assessment="Low",
                )

            # Aggregate data
            all_projects = set()
            all_symbols = set()
            all_breaking_changes = []
            critical_paths = []

            for impact in impacts:
                all_projects.update(impact.affected_projects.keys())
                for symbols in impact.affected_projects.values():
                    all_symbols.update(symbols)
                all_breaking_changes.extend(impact.breaking_changes)

                # Find critical paths (longest or with most breaking changes)
                for path in impact.propagation_paths:
                    if len(path) > 5 or any(s in impact.breaking_changes for s in path):
                        critical_paths.append(path)

            # Assess risk
            risk_assessment = self._assess_overall_risk(
                len(all_projects), len(all_symbols), len(all_breaking_changes)
            )

            # Generate migration strategy
            migration_strategy = self._generate_migration_strategy(
                all_breaking_changes, all_projects
            )

            # Generate communication plan
            communication_plan = self._generate_communication_plan(
                all_projects, risk_assessment
            )

            summary = ImpactSummary(
                total_projects_affected=len(all_projects),
                total_symbols_affected=len(all_symbols),
                critical_paths=critical_paths[:10],  # Top 10
                risk_assessment=risk_assessment,
                migration_strategy=migration_strategy,
                communication_plan=communication_plan,
            )

            # Generate rollback plan for high-risk changes
            if risk_assessment in ["High", "Critical"]:
                summary.rollback_plan = self._generate_rollback_plan(impacts)

            return summary

        except Exception as e:
            logger.error(f"Error generating impact summary: {e}")
            return ImpactSummary(
                total_projects_affected=0,
                total_symbols_affected=0,
                critical_paths=[],
                risk_assessment="Unknown",
            )

    def _get_symbol_project(self, file_path: str) -> str:
        """Determine project ID from file path"""
        path = Path(file_path)

        # Handle empty or invalid paths
        if not path.parts:
            return "unknown"

        # Check for common project indicators
        for part in path.parts:
            if part in ["src", "lib", "app", "packages"]:
                # Get parent directory as project
                idx = path.parts.index(part)
                if idx > 0:
                    return path.parts[idx - 1]

        # Check for package.json, pyproject.toml, etc.
        for parent in path.parents:
            if parent.exists():
                if (parent / "package.json").exists():
                    return parent.name
                if (parent / "pyproject.toml").exists():
                    return parent.name
                if (parent / "Cargo.toml").exists():
                    return parent.name

        # Default to first meaningful directory
        if len(path.parts) > 0:
            # Check directories (excluding filename)
            directories = path.parts[:-1] if len(path.parts) > 1 else []

            # Return first meaningful directory
            for part in directories:
                if part not in [".", "/", ""]:
                    return part

            # If no meaningful directories found, use first part if it's not a file
            if len(directories) == 0 and len(path.parts) > 0:
                first_part = path.parts[0]
                if "." not in first_part or not first_part.endswith(
                    (".py", ".js", ".ts", ".swift")
                ):
                    return first_part

        return "unknown"

    def _is_external_project(self, project_id: str) -> bool:
        """Check if project is external"""
        for pattern in self.external_project_patterns:
            if Path(project_id).match(pattern):
                return True
        return project_id in self.project_graph.external_dependencies.values()

    def _is_breaking_change(
        self, change_type: str, dependency_info: Dict[str, Any]
    ) -> bool:
        """Determine if change is breaking for dependency"""
        if change_type in self.breaking_change_patterns:
            return True

        # Check dependency type
        dep_type = dependency_info.get("dependency_type")
        if dep_type in [DependencyType.INHERITANCE, DependencyType.COMPOSITION]:
            return True

        return False

    def _assess_compatibility(
        self, change_type: str, breaking_changes: List[str]
    ) -> ChangeCompatibility:
        """Assess compatibility of changes"""
        if not breaking_changes:
            return ChangeCompatibility.COMPATIBLE

        if change_type in ["added", "deprecated"]:
            return ChangeCompatibility.BACKWARD_COMPATIBLE

        if change_type in ["deleted", "removed"] or len(breaking_changes) > 10:
            return ChangeCompatibility.BREAKING

        return ChangeCompatibility.POTENTIALLY_BREAKING

    def _generate_recommendations(self, impact: CascadingImpact) -> List[str]:
        """Generate recommendations based on impact"""
        recommendations = []

        # Version bump recommendations
        if impact.compatibility_assessment == ChangeCompatibility.BREAKING:
            recommendations.append("Major version bump required")
        elif impact.compatibility_assessment == ChangeCompatibility.BACKWARD_COMPATIBLE:
            recommendations.append("Minor version bump recommended")

        # Migration recommendations
        if impact.breaking_changes:
            recommendations.append(
                f"Create migration guide for {len(impact.breaking_changes)} breaking changes"
            )
            recommendations.append("Consider providing compatibility layer")

        # Communication recommendations
        if len(impact.affected_projects) > 5:
            recommendations.append(
                "Send advance notice to dependent project maintainers"
            )
            recommendations.append(
                "Create detailed changelog with migration instructions"
            )

        # Testing recommendations
        if impact.max_propagation_depth > 3:
            recommendations.append("Extensive integration testing required")
            recommendations.append("Consider staged rollout")

        return recommendations

    def _estimate_effort(self, impact: CascadingImpact) -> float:
        """Estimate effort hours for handling impact"""
        base_hours = 0.0

        # Per breaking change
        base_hours += len(impact.breaking_changes) * 2.0

        # Per affected project
        base_hours += len(impact.affected_projects) * 1.0

        # Complexity multiplier
        if impact.max_propagation_depth > 5:
            base_hours *= 1.5

        # Communication overhead
        if len(impact.affected_projects) > 10:
            base_hours += 8.0  # Full day for coordination

        return round(base_hours, 1)

    def _assess_overall_risk(
        self, projects_affected: int, symbols_affected: int, breaking_changes: int
    ) -> str:
        """Assess overall risk level"""
        risk_score = 0

        # Project impact
        if projects_affected > 20:
            risk_score += 3
        elif projects_affected > 10:
            risk_score += 2
        elif projects_affected > 5:
            risk_score += 1

        # Symbol impact
        if symbols_affected > 100:
            risk_score += 3
        elif symbols_affected > 50:
            risk_score += 2
        elif symbols_affected > 20:
            risk_score += 1

        # Breaking changes
        if breaking_changes > 50:
            risk_score += 4
        elif breaking_changes > 20:
            risk_score += 3
        elif breaking_changes > 10:
            risk_score += 2
        elif breaking_changes > 0:
            risk_score += 1

        # Map to risk level
        if risk_score >= 8:
            return "Critical"
        elif risk_score >= 5:
            return "High"
        elif risk_score >= 3:
            return "Medium"
        else:
            return "Low"

    def _generate_migration_strategy(
        self, breaking_changes: List[str], affected_projects: Set[str]
    ) -> str:
        """Generate migration strategy"""
        if not breaking_changes:
            return "No migration required"

        if len(breaking_changes) < 5:
            return "Direct migration - update dependent code"

        if len(affected_projects) < 10:
            return "Phased migration - coordinate with project maintainers"

        return "Gradual migration - provide compatibility layer and deprecation period"

    def _generate_communication_plan(
        self, affected_projects: Set[str], risk_assessment: str
    ) -> List[str]:
        """Generate communication plan"""
        plan = []

        if risk_assessment in ["Critical", "High"]:
            plan.append("Immediate notification to all affected project maintainers")
            plan.append("Create public announcement with timeline")
            plan.append("Schedule coordination meetings")

        if len(affected_projects) > 5:
            plan.append("Send detailed impact analysis to each project")
            plan.append("Provide migration assistance")

        plan.append("Update documentation with changes")
        plan.append("Monitor feedback channels")

        return plan

    def _generate_rollback_plan(self, impacts: List[CascadingImpact]) -> str:
        """Generate rollback plan for high-risk changes"""
        return (
            "1. Tag current version before changes\n"
            "2. Create feature branch for changes\n"
            "3. Implement changes incrementally with tests\n"
            "4. Have rollback script ready\n"
            "5. Monitor error rates post-deployment\n"
            "6. Be ready to revert within 1 hour if issues arise"
        )

    def _generate_impact_id(self) -> str:
        """Generate unique impact ID"""
        timestamp = int(time.time() * 1000)
        return (
            f"impact_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"
        )

    def _cache_impact(self, key: str, impact: CascadingImpact):
        """Cache impact analysis result"""
        # Simple LRU-style cache
        if len(self.impact_cache) > 1000:
            # Remove oldest entries
            oldest_keys = list(self.impact_cache.keys())[:100]
            for k in oldest_keys:
                del self.impact_cache[k]

        self.impact_cache[key] = self._create_summary_from_impact(impact)

    def _create_summary_from_impact(self, impact: CascadingImpact) -> ImpactSummary:
        """Create summary from impact analysis"""
        return ImpactSummary(
            total_projects_affected=len(impact.affected_projects),
            total_symbols_affected=impact.total_affected_symbols,
            critical_paths=impact.propagation_paths[:5],
            risk_assessment=self._assess_overall_risk(
                len(impact.affected_projects),
                impact.total_affected_symbols,
                len(impact.breaking_changes),
            ),
        )

    def _create_impact_from_cache(self, key: str) -> CascadingImpact:
        """Create impact from cached summary"""
        summary = self.impact_cache[key]
        parts = key.split(":")

        impact = CascadingImpact(
            impact_id=self._generate_impact_id(),
            origin_symbol_id=parts[0],
            origin_project=parts[1],
            change_type=parts[2],
            total_affected_symbols=summary.total_symbols_affected,
        )

        return impact

    def _update_metrics(self, impact: CascadingImpact, analysis_time: float):
        """Update performance metrics"""
        self.metrics["total_analyses"] += 1

        if len(impact.affected_projects) > 1:
            self.metrics["cross_project_impacts"] += 1

        if impact.breaking_changes:
            self.metrics["breaking_changes_detected"] += 1

        # Update averages
        current_avg_depth = self.metrics["average_propagation_depth"]
        new_avg_depth = (
            current_avg_depth * (self.metrics["total_analyses"] - 1)
            + impact.max_propagation_depth
        ) / self.metrics["total_analyses"]
        self.metrics["average_propagation_depth"] = new_avg_depth

        current_avg_time = self.metrics["average_analysis_time_ms"]
        new_avg_time = (
            current_avg_time * (self.metrics["total_analyses"] - 1)
            + analysis_time * 1000
        ) / self.metrics["total_analyses"]
        self.metrics["average_analysis_time_ms"] = new_avg_time

    async def _background_analysis_processor(self):
        """Background processor for queued analyses"""
        try:
            while True:
                # Get next analysis request
                request = await self.analysis_queue.get()

                try:
                    # Process analysis
                    impact = await self.analyze_cascading_impact(
                        request["symbol_id"],
                        request["project_id"],
                        request["change_type"],
                        request.get("include_external", False),
                    )

                    # Store result
                    self.active_analyses[request["symbol_id"]] = impact

                except Exception as e:
                    logger.error(f"Error processing analysis request: {e}")

                # Small delay between analyses
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info("Background analysis processor cancelled")
        except Exception as e:
            logger.error(f"Error in background analysis processor: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get analyzer metrics"""
        return {
            **self.metrics,
            "cached_analyses": len(self.impact_cache),
            "active_analyses": len(self.active_analyses),
            "tracked_boundaries": len(self.project_boundaries),
            "cross_project_dependencies": len(self.cross_project_dependencies),
        }


# Global instance
cascading_impact_analyzer = CascadingImpactAnalyzer()
