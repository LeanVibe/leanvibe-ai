"""
Violation Reporting and Analytics Service

Handles reporting, metrics, and analytics for architectural violations.
Extracted from architectural_violation_detector.py to improve modularity.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set

from .rule_manager import ViolationType, ViolationSeverity
from .detector import ViolationInstance, ComponentMetrics

logger = logging.getLogger(__name__)


@dataclass
class ArchitecturalReport:
    """Comprehensive architectural analysis report"""

    total_violations: int = 0
    violations_by_type: Dict[ViolationType, int] = field(default_factory=dict)
    violations_by_severity: Dict[ViolationSeverity, int] = field(default_factory=dict)
    affected_files: Set[str] = field(default_factory=set)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    trends: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    quality_score: float = 0.0


class ViolationReporter:
    """Handles reporting and analytics for violations"""
    
    def __init__(self):
        self.violation_history: List[Dict[str, Any]] = []
        self.metrics_history: List[Dict[str, Any]] = []
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)  # file_path -> client_ids
    
    def subscribe_to_violations(self, file_path: str, client_id: str):
        """Subscribe a client to violation notifications for a file"""
        self.subscribers[file_path].add(client_id)
        logger.info(f"Client {client_id} subscribed to violations for {file_path}")
    
    def unsubscribe_from_violations(self, file_path: str, client_id: str):
        """Unsubscribe a client from violation notifications"""
        if file_path in self.subscribers:
            self.subscribers[file_path].discard(client_id)
            if not self.subscribers[file_path]:
                del self.subscribers[file_path]
        logger.info(f"Client {client_id} unsubscribed from violations for {file_path}")
    
    def get_metrics(self, violations: List[ViolationInstance], component_metrics: Dict[str, ComponentMetrics]) -> Dict[str, Any]:
        """Get comprehensive violation metrics"""
        try:
            active_violations = [v for v in violations if not v.resolved]
            
            # Basic counts
            total_violations = len(active_violations)
            total_files = len(set(v.file_path for v in active_violations))
            
            # Violations by type
            violations_by_type = defaultdict(int)
            for violation in active_violations:
                violations_by_type[violation.violation_type] += 1
            
            # Violations by severity
            violations_by_severity = defaultdict(int)
            for violation in active_violations:
                violations_by_severity[violation.severity] += 1
            
            # Quality metrics
            quality_scores = [metrics.quality_score for metrics in component_metrics.values()]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            return {
                "total_violations": total_violations,
                "total_files_affected": total_files,
                "violations_by_type": dict(violations_by_type),
                "violations_by_severity": dict(violations_by_severity),
                "average_quality_score": avg_quality,
                "total_components_analyzed": len(component_metrics),
                "metrics_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating violation metrics: {e}")
            return {"error": str(e)}
    
    def generate_summary(self, violations: List[ViolationInstance], component_metrics: Dict[str, ComponentMetrics]) -> ArchitecturalReport:
        """Generate a comprehensive architectural report"""
        try:
            active_violations = [v for v in violations if not v.resolved]
            
            # Basic metrics
            total_violations = len(active_violations)
            affected_files = set(v.file_path for v in active_violations)
            
            # Count by type and severity
            violations_by_type = defaultdict(int)
            violations_by_severity = defaultdict(int)
            
            for violation in active_violations:
                violations_by_type[violation.violation_type] += 1
                violations_by_severity[violation.severity] += 1
            
            # Quality metrics
            quality_scores = [metrics.quality_score for metrics in component_metrics.values()]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # Calculate overall quality score
            overall_quality = self._calculate_quality_score(active_violations, component_metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(active_violations, component_metrics)
            
            # Build quality metrics
            quality_metrics = {
                "average_component_quality": avg_quality,
                "total_lines_analyzed": sum(m.lines_of_code for m in component_metrics.values()),
                "average_complexity": sum(m.cyclomatic_complexity for m in component_metrics.values()) / max(len(component_metrics), 1),
                "violation_density": total_violations / max(len(component_metrics), 1)
            }
            
            return ArchitecturalReport(
                total_violations=total_violations,
                violations_by_type=dict(violations_by_type),
                violations_by_severity=dict(violations_by_severity),
                affected_files=affected_files,
                quality_metrics=quality_metrics,
                recommendations=recommendations,
                quality_score=overall_quality
            )
            
        except Exception as e:
            logger.error(f"Error generating architectural summary: {e}")
            return ArchitecturalReport()
    
    def get_violation_trends(self, violations: List[ViolationInstance], days: int = 30) -> Dict[str, Any]:
        """Analyze violation trends over time"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_violations = [v for v in violations if v.detected_at >= cutoff_date]
            
            # Group by day
            daily_counts = defaultdict(int)
            for violation in recent_violations:
                day_key = violation.detected_at.strftime('%Y-%m-%d')
                daily_counts[day_key] += 1
            
            # Group by type over time
            type_trends = defaultdict(lambda: defaultdict(int))
            for violation in recent_violations:
                day_key = violation.detected_at.strftime('%Y-%m-%d')
                type_trends[violation.violation_type][day_key] += 1
            
            return {
                "period_days": days,
                "total_violations_in_period": len(recent_violations),
                "daily_violation_counts": dict(daily_counts),
                "violation_type_trends": {
                    vtype: dict(counts) for vtype, counts in type_trends.items()
                },
                "average_daily_violations": len(recent_violations) / days if days > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing violation trends: {e}")
            return {"error": str(e)}
    
    def get_top_violating_files(self, violations: List[ViolationInstance], limit: int = 10) -> List[Dict[str, Any]]:
        """Get files with the most violations"""
        try:
            active_violations = [v for v in violations if not v.resolved]
            
            # Count violations per file
            file_violations = defaultdict(list)
            for violation in active_violations:
                file_violations[violation.file_path].append(violation)
            
            # Sort by violation count
            sorted_files = sorted(
                file_violations.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:limit]
            
            result = []
            for file_path, file_violations in sorted_files:
                severity_counts = defaultdict(int)
                type_counts = defaultdict(int)
                
                for violation in file_violations:
                    severity_counts[violation.severity] += 1
                    type_counts[violation.violation_type] += 1
                
                result.append({
                    "file_path": file_path,
                    "total_violations": len(file_violations),
                    "violations_by_severity": dict(severity_counts),
                    "violations_by_type": dict(type_counts),
                    "most_severe": max(file_violations, key=lambda v: self._severity_weight(v.severity)).severity
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting top violating files: {e}")
            return []
    
    def _calculate_quality_score(self, violations: List[ViolationInstance], component_metrics: Dict[str, ComponentMetrics]) -> float:
        """Calculate overall architectural quality score"""
        try:
            if not component_metrics:
                return 0.0
            
            # Get component scores
            component_scores = [metrics.quality_score for metrics in component_metrics.values()]
            base_score = sum(component_scores) / len(component_scores)
            
            # Apply penalties for violations
            violation_penalty = 0.0
            severity_weights = {
                ViolationSeverity.CRITICAL: 5.0,
                ViolationSeverity.HIGH: 3.0,
                ViolationSeverity.MEDIUM: 2.0,
                ViolationSeverity.LOW: 1.0,
                ViolationSeverity.INFO: 0.5
            }
            
            for violation in violations:
                if not violation.resolved:
                    violation_penalty += severity_weights.get(violation.severity, 1.0)
            
            # Normalize penalty based on codebase size
            total_components = len(component_metrics)
            normalized_penalty = violation_penalty / max(total_components, 1)
            
            # Calculate final score
            final_score = max(0.0, base_score - normalized_penalty)
            return min(100.0, final_score)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def _generate_recommendations(self, violations: List[ViolationInstance], component_metrics: Dict[str, ComponentMetrics]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        try:
            active_violations = [v for v in violations if not v.resolved]
            
            if not active_violations:
                recommendations.append("✅ No active architectural violations detected!")
                return recommendations
            
            # Analyze violation patterns
            severity_counts = defaultdict(int)
            type_counts = defaultdict(int)
            
            for violation in active_violations:
                severity_counts[violation.severity] += 1
                type_counts[violation.violation_type] += 1
            
            # Critical violations
            critical_count = severity_counts.get(ViolationSeverity.CRITICAL, 0)
            if critical_count > 0:
                recommendations.append(f"🚨 Address {critical_count} critical violations immediately")
            
            # High violations
            high_count = severity_counts.get(ViolationSeverity.HIGH, 0)
            if high_count > 0:
                recommendations.append(f"⚠️ Plan to fix {high_count} high-severity violations")
            
            # Type-specific recommendations
            if type_counts.get(ViolationType.SIZE_VIOLATION, 0) > 0:
                recommendations.append("📏 Consider breaking down large files and functions")
            
            if type_counts.get(ViolationType.COMPLEXITY_VIOLATION, 0) > 0:
                recommendations.append("🧩 Simplify complex functions and reduce cyclomatic complexity")
            
            if type_counts.get(ViolationType.COUPLING_VIOLATION, 0) > 0:
                recommendations.append("🔗 Reduce coupling by using dependency injection or interfaces")
            
            if type_counts.get(ViolationType.LAYER_VIOLATION, 0) > 0:
                recommendations.append("🏗️ Review and enforce architectural layer separation")
            
            if type_counts.get(ViolationType.ANTI_PATTERN, 0) > 0:
                recommendations.append("🚫 Refactor code to eliminate anti-patterns")
            
            # Quality-based recommendations
            low_quality_components = [
                path for path, metrics in component_metrics.items()
                if metrics.quality_score < 70.0
            ]
            
            if low_quality_components:
                recommendations.append(f"🔧 Focus refactoring efforts on {len(low_quality_components)} low-quality components")
            
            # General recommendations
            total_violations = len(active_violations)
            total_files = len(set(v.file_path for v in active_violations))
            
            if total_violations > total_files * 2:
                recommendations.append("📈 Consider implementing architectural guidelines and code reviews")
            
            if len(recommendations) == 0:
                recommendations.append("👍 Architecture looks good! Continue following best practices")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("❌ Error generating recommendations")
        
        return recommendations
    
    def _severity_weight(self, severity: ViolationSeverity) -> int:
        """Get numeric weight for severity comparison"""
        weights = {
            ViolationSeverity.CRITICAL: 5,
            ViolationSeverity.HIGH: 4,
            ViolationSeverity.MEDIUM: 3,
            ViolationSeverity.LOW: 2,
            ViolationSeverity.INFO: 1
        }
        return weights.get(severity, 0)
    
    def notify_subscribers(self, file_path: str, violations: List[ViolationInstance]):
        """Notify subscribers about new violations (placeholder for actual notification)"""
        if file_path in self.subscribers:
            subscribers = self.subscribers[file_path]
            logger.info(f"Notifying {len(subscribers)} subscribers about {len(violations)} violations in {file_path}")
            # TODO: Implement actual notification mechanism (WebSocket, message queue, etc.)


# Global violation reporter instance
violation_reporter = ViolationReporter()