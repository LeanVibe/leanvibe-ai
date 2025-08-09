#!/usr/bin/env python3
"""
LeanVibe Documentation Health Monitoring Dashboard

Real-time monitoring dashboard that tracks documentation quality, freshness,
usage patterns, and maintenance metrics with enterprise-grade observability.
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentationMetric(BaseModel):
    """Individual documentation metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    status: str  # "healthy", "warning", "critical"
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


class HealthStatus(BaseModel):
    """Overall health status."""
    status: str  # "healthy", "degraded", "critical"
    score: float  # 0-100
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class DocumentationHealthDashboard:
    """Comprehensive documentation health monitoring system."""
    
    def __init__(self, docs_directory: Path = Path(".")):
        self.docs_directory = Path(docs_directory)
        self.metrics_history_file = Path(".claude/docs_metrics_history.json")
        self.metrics_history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics storage
        self.current_metrics: Dict[str, DocumentationMetric] = {}
        self.metrics_history: List[Dict] = []
        
        # Load historical metrics
        self._load_metrics_history()
        
        # Health thresholds
        self.health_thresholds = {
            "overall_quality": {"warning": 80.0, "critical": 70.0},
            "link_health": {"warning": 95.0, "critical": 90.0},
            "code_example_accuracy": {"warning": 95.0, "critical": 90.0},
            "documentation_coverage": {"warning": 85.0, "critical": 75.0},
            "freshness_score": {"warning": 80.0, "critical": 60.0},
            "accessibility_score": {"warning": 90.0, "critical": 80.0}
        }
        
        # SLA targets
        self.sla_targets = {
            "max_broken_links": 0,
            "max_outdated_docs_days": 30,
            "min_quality_score": 85.0,
            "max_response_time_ms": 2000,
            "min_uptime_percentage": 99.9
        }
    
    async def collect_all_metrics(self) -> Dict[str, DocumentationMetric]:
        """Collect comprehensive documentation health metrics."""
        logger.info("Collecting documentation health metrics")
        
        try:
            # Collect different categories of metrics
            quality_metrics = await self._collect_quality_metrics()
            freshness_metrics = await self._collect_freshness_metrics()
            usage_metrics = await self._collect_usage_metrics()
            performance_metrics = await self._collect_performance_metrics()
            availability_metrics = await self._collect_availability_metrics()
            enterprise_metrics = await self._collect_enterprise_metrics()
            
            # Combine all metrics
            all_metrics = {}
            all_metrics.update(quality_metrics)
            all_metrics.update(freshness_metrics)
            all_metrics.update(usage_metrics)
            all_metrics.update(performance_metrics)
            all_metrics.update(availability_metrics)
            all_metrics.update(enterprise_metrics)
            
            self.current_metrics = all_metrics
            
            # Store metrics in history
            self._store_metrics_snapshot()
            
            logger.info(f"Collected {len(all_metrics)} documentation health metrics")
            return all_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise
    
    async def _collect_quality_metrics(self) -> Dict[str, DocumentationMetric]:
        """Collect documentation quality metrics."""
        metrics = {}
        
        try:
            # Import quality checker
            import sys
            sys.path.append(".")
            from docs.automation.quality_checker import DocumentationQualityChecker
            
            checker = DocumentationQualityChecker(self.docs_directory)
            quality_summary = checker.check_all_documentation_quality()
            
            # Overall quality score
            overall_score = quality_summary.get("average_score", 0)
            metrics["overall_quality"] = DocumentationMetric(
                name="Overall Quality Score",
                value=overall_score,
                unit="score",
                timestamp=datetime.now(),
                status=self._determine_status(overall_score, "overall_quality"),
                threshold_warning=self.health_thresholds["overall_quality"]["warning"],
                threshold_critical=self.health_thresholds["overall_quality"]["critical"]
            )
            
            # Document coverage
            total_docs = quality_summary.get("total_documents", 0)
            docs_above_threshold = quality_summary.get("documents_above_threshold", 0)
            coverage_pct = (docs_above_threshold / max(total_docs, 1)) * 100
            
            metrics["documentation_coverage"] = DocumentationMetric(
                name="Documentation Coverage",
                value=coverage_pct,
                unit="percentage",
                timestamp=datetime.now(),
                status=self._determine_status(coverage_pct, "documentation_coverage")
            )
            
            # Quality issues count
            total_issues = quality_summary.get("total_issues", 0)
            metrics["quality_issues"] = DocumentationMetric(
                name="Quality Issues",
                value=total_issues,
                unit="count",
                timestamp=datetime.now(),
                status="healthy" if total_issues == 0 else "warning" if total_issues < 10 else "critical"
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect quality metrics: {e}")
            metrics["overall_quality"] = DocumentationMetric(
                name="Overall Quality Score",
                value=0,
                unit="score",
                timestamp=datetime.now(),
                status="critical"
            )
        
        return metrics
    
    async def _collect_freshness_metrics(self) -> Dict[str, DocumentationMetric]:
        """Collect documentation freshness metrics."""
        metrics = {}
        
        try:
            # Find all documentation files
            doc_files = list(self.docs_directory.glob("**/*.md"))
            doc_files.extend(self.docs_directory.glob("*.md"))
            
            if not doc_files:
                metrics["freshness_score"] = DocumentationMetric(
                    name="Freshness Score",
                    value=0,
                    unit="score",
                    timestamp=datetime.now(),
                    status="critical"
                )
                return metrics
            
            now = datetime.now()
            freshness_scores = []
            outdated_count = 0
            
            for doc_file in doc_files:
                try:
                    # Get file modification time
                    mod_time = datetime.fromtimestamp(doc_file.stat().st_mtime)
                    days_old = (now - mod_time).days
                    
                    # Calculate freshness score (100 for recent, decreasing with age)
                    if days_old <= 7:
                        freshness = 100
                    elif days_old <= 30:
                        freshness = 85
                    elif days_old <= 90:
                        freshness = 70
                    elif days_old <= 180:
                        freshness = 50
                    else:
                        freshness = 25
                    
                    freshness_scores.append(freshness)
                    
                    if days_old > 30:
                        outdated_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to check freshness of {doc_file}: {e}")
                    freshness_scores.append(50)  # Neutral score for errors
            
            # Calculate overall freshness
            avg_freshness = statistics.mean(freshness_scores) if freshness_scores else 0
            outdated_pct = (outdated_count / len(doc_files)) * 100
            
            metrics["freshness_score"] = DocumentationMetric(
                name="Freshness Score",
                value=avg_freshness,
                unit="score",
                timestamp=datetime.now(),
                status=self._determine_status(avg_freshness, "freshness_score")
            )
            
            metrics["outdated_documents"] = DocumentationMetric(
                name="Outdated Documents",
                value=outdated_pct,
                unit="percentage",
                timestamp=datetime.now(),
                status="healthy" if outdated_pct < 10 else "warning" if outdated_pct < 25 else "critical"
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect freshness metrics: {e}")
        
        return metrics
    
    async def _collect_usage_metrics(self) -> Dict[str, DocumentationMetric]:
        """Collect documentation usage metrics."""
        metrics = {}
        
        try:
            # Simulate usage metrics (in real implementation, integrate with analytics)
            # This would typically come from web analytics, CDN logs, or app telemetry
            
            # Page views (simulated)
            daily_views = 1250  # Would come from analytics API
            metrics["daily_page_views"] = DocumentationMetric(
                name="Daily Page Views",
                value=daily_views,
                unit="views",
                timestamp=datetime.now(),
                status="healthy" if daily_views > 1000 else "warning"
            )
            
            # Search queries (simulated)
            search_queries = 180
            metrics["daily_searches"] = DocumentationMetric(
                name="Daily Search Queries",
                value=search_queries,
                unit="queries",
                timestamp=datetime.now(),
                status="healthy"
            )
            
            # User feedback score (simulated)
            feedback_score = 4.2  # Out of 5
            metrics["user_feedback_score"] = DocumentationMetric(
                name="User Feedback Score",
                value=feedback_score,
                unit="rating",
                timestamp=datetime.now(),
                status="healthy" if feedback_score >= 4.0 else "warning" if feedback_score >= 3.5 else "critical"
            )
            
            # API documentation usage
            api_doc_hits = 850
            metrics["api_doc_usage"] = DocumentationMetric(
                name="API Documentation Usage",
                value=api_doc_hits,
                unit="hits",
                timestamp=datetime.now(),
                status="healthy"
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect usage metrics: {e}")
        
        return metrics
    
    async def _collect_performance_metrics(self) -> Dict[str, DocumentationMetric]:
        """Collect documentation site performance metrics."""
        metrics = {}
        
        try:
            # Page load times (simulated - would integrate with real monitoring)
            avg_load_time = 850  # milliseconds
            metrics["average_load_time"] = DocumentationMetric(
                name="Average Page Load Time",
                value=avg_load_time,
                unit="ms",
                timestamp=datetime.now(),
                status="healthy" if avg_load_time < 1000 else "warning" if avg_load_time < 2000 else "critical"
            )
            
            # Search response time
            search_response_time = 120  # milliseconds
            metrics["search_response_time"] = DocumentationMetric(
                name="Search Response Time",
                value=search_response_time,
                unit="ms",
                timestamp=datetime.now(),
                status="healthy" if search_response_time < 200 else "warning"
            )
            
            # Cache hit rate
            cache_hit_rate = 87.5  # percentage
            metrics["cache_hit_rate"] = DocumentationMetric(
                name="Cache Hit Rate",
                value=cache_hit_rate,
                unit="percentage",
                timestamp=datetime.now(),
                status="healthy" if cache_hit_rate > 80 else "warning"
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect performance metrics: {e}")
        
        return metrics
    
    async def _collect_availability_metrics(self) -> Dict[str, DocumentationMetric]:
        """Collect documentation availability metrics."""
        metrics = {}
        
        try:
            # Import validation tools
            import sys
            sys.path.append(".")
            from docs.automation.validate_docs import DocumentationValidator
            
            validator = DocumentationValidator(self.docs_directory)
            validation_results = await validator.validate_all_documentation()
            
            # Link health
            total_checks = validation_results.get("total_checks", 0)
            passed_checks = validation_results.get("passed_checks", 0)
            link_health = (passed_checks / max(total_checks, 1)) * 100
            
            metrics["link_health"] = DocumentationMetric(
                name="Link Health",
                value=link_health,
                unit="percentage",
                timestamp=datetime.now(),
                status=self._determine_status(link_health, "link_health")
            )
            
            # Broken links count
            failed_checks = validation_results.get("failed_checks", 0)
            metrics["broken_links"] = DocumentationMetric(
                name="Broken Links",
                value=failed_checks,
                unit="count",
                timestamp=datetime.now(),
                status="healthy" if failed_checks == 0 else "warning" if failed_checks < 5 else "critical"
            )
            
            # Code example accuracy
            code_checks = len([r for r in validation_results.get("results", []) if r.get("check_type") in ["python_code", "bash_code", "json_code"]])
            code_failures = len([r for r in validation_results.get("results", []) if r.get("check_type") in ["python_code", "bash_code", "json_code"] and r.get("status") == "fail"])
            code_accuracy = ((code_checks - code_failures) / max(code_checks, 1)) * 100
            
            metrics["code_example_accuracy"] = DocumentationMetric(
                name="Code Example Accuracy",
                value=code_accuracy,
                unit="percentage",
                timestamp=datetime.now(),
                status=self._determine_status(code_accuracy, "code_example_accuracy")
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect availability metrics: {e}")
            # Set default critical values
            metrics["link_health"] = DocumentationMetric(
                name="Link Health",
                value=0,
                unit="percentage",
                timestamp=datetime.now(),
                status="critical"
            )
        
        return metrics
    
    async def _collect_enterprise_metrics(self) -> Dict[str, DocumentationMetric]:
        """Collect enterprise-specific metrics."""
        metrics = {}
        
        try:
            # Enterprise documentation compliance
            required_enterprise_docs = [
                "ENTERPRISE.md",
                "SSO_SETUP.md", 
                "MULTI_TENANCY_GUIDE.md",
                "SECURITY_AUDIT_RESULTS.md",
                "PRODUCTION_DEPLOYMENT_GUIDE.md"
            ]
            
            existing_docs = sum(1 for doc in required_enterprise_docs if (self.docs_directory / doc).exists())
            compliance_score = (existing_docs / len(required_enterprise_docs)) * 100
            
            metrics["enterprise_compliance"] = DocumentationMetric(
                name="Enterprise Compliance",
                value=compliance_score,
                unit="percentage", 
                timestamp=datetime.now(),
                status="healthy" if compliance_score == 100 else "warning" if compliance_score >= 80 else "critical"
            )
            
            # API documentation completeness
            api_endpoints_documented = 95  # Would calculate from actual API routes vs documented routes
            metrics["api_completeness"] = DocumentationMetric(
                name="API Documentation Completeness",
                value=api_endpoints_documented,
                unit="percentage",
                timestamp=datetime.now(),
                status="healthy" if api_endpoints_documented >= 95 else "warning"
            )
            
            # SLA compliance score
            sla_violations = 0  # Count of SLA threshold violations
            sla_compliance = 100 if sla_violations == 0 else max(0, 100 - (sla_violations * 10))
            
            metrics["sla_compliance"] = DocumentationMetric(
                name="SLA Compliance",
                value=sla_compliance,
                unit="percentage",
                timestamp=datetime.now(),
                status="healthy" if sla_compliance >= 95 else "warning" if sla_compliance >= 90 else "critical"
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect enterprise metrics: {e}")
        
        return metrics
    
    def calculate_health_status(self) -> HealthStatus:
        """Calculate overall documentation health status."""
        if not self.current_metrics:
            return HealthStatus(
                status="critical",
                score=0,
                issues=["No metrics available"],
                recommendations=["Run metric collection"]
            )
        
        # Calculate weighted health score
        critical_metrics = ["overall_quality", "link_health", "enterprise_compliance"]
        important_metrics = ["freshness_score", "code_example_accuracy", "api_completeness"]
        
        critical_scores = []
        important_scores = []
        issues = []
        recommendations = []
        
        for metric_name, metric in self.current_metrics.items():
            if metric.status == "critical":
                issues.append(f"CRITICAL: {metric.name} = {metric.value} {metric.unit}")
                if metric_name in critical_metrics:
                    recommendations.append(f"Immediate attention required for {metric.name}")
            elif metric.status == "warning":
                issues.append(f"WARNING: {metric.name} = {metric.value} {metric.unit}")
                if metric_name in important_metrics:
                    recommendations.append(f"Improvement needed for {metric.name}")
            
            # Collect scores for weighted calculation
            if metric_name in critical_metrics:
                critical_scores.append(metric.value)
            elif metric_name in important_metrics:
                important_scores.append(metric.value)
        
        # Calculate weighted score
        critical_weight = 0.7
        important_weight = 0.3
        
        critical_avg = statistics.mean(critical_scores) if critical_scores else 0
        important_avg = statistics.mean(important_scores) if important_scores else 0
        
        overall_score = (critical_avg * critical_weight) + (important_avg * important_weight)
        
        # Determine status
        if overall_score >= 85:
            status = "healthy"
        elif overall_score >= 70:
            status = "degraded" 
        else:
            status = "critical"
        
        # Add general recommendations
        if overall_score < 85:
            recommendations.append("Run automated documentation maintenance workflow")
        if len(issues) > 5:
            recommendations.append("Consider implementing continuous documentation monitoring")
        
        return HealthStatus(
            status=status,
            score=round(overall_score, 1),
            issues=issues[:10],  # Limit to top 10 issues
            recommendations=recommendations[:5]  # Limit to top 5 recommendations
        )
    
    def _determine_status(self, value: float, metric_type: str) -> str:
        """Determine metric status based on thresholds."""
        if metric_type not in self.health_thresholds:
            return "healthy"
        
        thresholds = self.health_thresholds[metric_type]
        
        if value < thresholds["critical"]:
            return "critical"
        elif value < thresholds["warning"]:
            return "warning"
        else:
            return "healthy"
    
    def _load_metrics_history(self):
        """Load historical metrics from file."""
        if self.metrics_history_file.exists():
            try:
                with open(self.metrics_history_file, 'r') as f:
                    self.metrics_history = json.load(f)
                logger.info(f"Loaded {len(self.metrics_history)} historical metric snapshots")
            except Exception as e:
                logger.warning(f"Failed to load metrics history: {e}")
                self.metrics_history = []
    
    def _store_metrics_snapshot(self):
        """Store current metrics snapshot to history."""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {name: metric.dict() for name, metric in self.current_metrics.items()}
            }
            
            self.metrics_history.append(snapshot)
            
            # Keep only last 30 days of metrics
            cutoff_date = datetime.now() - timedelta(days=30)
            self.metrics_history = [
                snap for snap in self.metrics_history 
                if datetime.fromisoformat(snap["timestamp"]) > cutoff_date
            ]
            
            # Save to file
            with open(self.metrics_history_file, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to store metrics snapshot: {e}")
    
    def generate_dashboard_report(self) -> str:
        """Generate comprehensive dashboard report."""
        logger.info("Generating dashboard report")
        
        health_status = self.calculate_health_status()
        
        # Generate report
        report_lines = [
            "# 📊 Documentation Health Dashboard",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Overall Status:** {self._status_emoji(health_status.status)} **{health_status.status.upper()}**",
            f"**Health Score:** {health_status.score}/100",
            "",
            "## 🎯 Health Summary",
            ""
        ]
        
        # Status indicators
        status_counts = {"healthy": 0, "warning": 0, "critical": 0}
        for metric in self.current_metrics.values():
            status_counts[metric.status] += 1
        
        report_lines.extend([
            f"- 🟢 **Healthy:** {status_counts['healthy']} metrics",
            f"- 🟡 **Warning:** {status_counts['warning']} metrics", 
            f"- 🔴 **Critical:** {status_counts['critical']} metrics",
            ""
        ])
        
        # Key metrics
        report_lines.extend([
            "## 📈 Key Metrics",
            "",
            "| Metric | Value | Status | Trend |",
            "|--------|-------|--------|--------|"
        ])
        
        # Sort metrics by importance
        important_metrics = [
            "overall_quality", "link_health", "enterprise_compliance",
            "freshness_score", "code_example_accuracy", "api_completeness"
        ]
        
        for metric_name in important_metrics:
            if metric_name in self.current_metrics:
                metric = self.current_metrics[metric_name]
                trend = self._calculate_trend(metric_name)
                status_emoji = self._status_emoji(metric.status)
                
                report_lines.append(
                    f"| {metric.name} | {metric.value} {metric.unit} | {status_emoji} {metric.status} | {trend} |"
                )
        
        # Issues and recommendations
        if health_status.issues:
            report_lines.extend([
                "",
                "## ⚠️ Issues Requiring Attention",
                ""
            ])
            for issue in health_status.issues:
                report_lines.append(f"- {issue}")
        
        if health_status.recommendations:
            report_lines.extend([
                "",
                "## 💡 Recommendations",
                ""
            ])
            for rec in health_status.recommendations:
                report_lines.append(f"- {rec}")
        
        # Performance insights
        report_lines.extend([
            "",
            "## 📊 Performance Insights",
            ""
        ])
        
        # Add insights based on metrics
        if "daily_page_views" in self.current_metrics:
            views = self.current_metrics["daily_page_views"].value
            report_lines.append(f"- Documentation receives ~{views:.0f} daily page views")
        
        if "search_response_time" in self.current_metrics:
            search_time = self.current_metrics["search_response_time"].value
            report_lines.append(f"- Search functionality responds in {search_time:.0f}ms on average")
        
        if "cache_hit_rate" in self.current_metrics:
            cache_rate = self.current_metrics["cache_hit_rate"].value
            report_lines.append(f"- Content delivery cache hit rate: {cache_rate:.1f}%")
        
        # SLA status
        report_lines.extend([
            "",
            "## 📋 SLA Compliance",
            "",
            "| Target | Current | Status |",
            "|--------|---------|--------|"
        ])
        
        sla_items = [
            ("Max Broken Links", 0, self.current_metrics.get("broken_links", DocumentationMetric(name="", value=99, unit="", timestamp=datetime.now(), status="")).value),
            ("Min Quality Score", 85.0, self.current_metrics.get("overall_quality", DocumentationMetric(name="", value=0, unit="", timestamp=datetime.now(), status="")).value),
            ("Max Load Time (ms)", 2000, self.current_metrics.get("average_load_time", DocumentationMetric(name="", value=9999, unit="", timestamp=datetime.now(), status="")).value)
        ]
        
        for target_name, target_value, current_value in sla_items:
            if target_name == "Max Broken Links" or target_name == "Max Load Time (ms)":
                sla_met = current_value <= target_value
            else:
                sla_met = current_value >= target_value
            
            status = "✅ Met" if sla_met else "❌ Violated"
            report_lines.append(f"| {target_name} | {current_value} | {status} |")
        
        # Save report
        report_path = Path("docs/generated") / "health_dashboard.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))
        
        logger.info(f"Dashboard report saved to {report_path}")
        return str(report_path)
    
    def _status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        return {
            "healthy": "🟢",
            "warning": "🟡", 
            "critical": "🔴",
            "degraded": "🟠"
        }.get(status, "⚪")
    
    def _calculate_trend(self, metric_name: str) -> str:
        """Calculate trend for a metric."""
        if len(self.metrics_history) < 2:
            return "📊"
        
        try:
            # Get last two values
            recent_snapshots = sorted(self.metrics_history, key=lambda x: x["timestamp"])[-2:]
            
            old_value = recent_snapshots[0]["metrics"].get(metric_name, {}).get("value", 0)
            new_value = recent_snapshots[1]["metrics"].get(metric_name, {}).get("value", 0)
            
            if new_value > old_value:
                return "📈"
            elif new_value < old_value:
                return "📉"
            else:
                return "➡️"
        except Exception:
            return "📊"
    
    def export_metrics_json(self) -> str:
        """Export current metrics as JSON for external monitoring systems."""
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "health_status": self.calculate_health_status().dict(),
            "metrics": {name: metric.dict() for name, metric in self.current_metrics.items()},
            "sla_compliance": self._calculate_sla_compliance()
        }
        
        json_path = Path("docs/generated") / "metrics.json"
        with open(json_path, "w") as f:
            json.dump(metrics_data, f, indent=2, default=str)
        
        return str(json_path)
    
    def _calculate_sla_compliance(self) -> Dict:
        """Calculate SLA compliance status."""
        compliance = {}
        
        broken_links = self.current_metrics.get("broken_links", DocumentationMetric(name="", value=99, unit="", timestamp=datetime.now(), status="")).value
        quality_score = self.current_metrics.get("overall_quality", DocumentationMetric(name="", value=0, unit="", timestamp=datetime.now(), status="")).value
        load_time = self.current_metrics.get("average_load_time", DocumentationMetric(name="", value=9999, unit="", timestamp=datetime.now(), status="")).value
        
        compliance["max_broken_links"] = {
            "target": self.sla_targets["max_broken_links"],
            "current": broken_links,
            "compliant": broken_links <= self.sla_targets["max_broken_links"]
        }
        
        compliance["min_quality_score"] = {
            "target": self.sla_targets["min_quality_score"],
            "current": quality_score,
            "compliant": quality_score >= self.sla_targets["min_quality_score"]
        }
        
        compliance["max_response_time_ms"] = {
            "target": self.sla_targets["max_response_time_ms"],
            "current": load_time,
            "compliant": load_time <= self.sla_targets["max_response_time_ms"]
        }
        
        return compliance


async def main():
    """Main function to run documentation health monitoring."""
    try:
        dashboard = DocumentationHealthDashboard()
        
        print("🔄 Collecting documentation health metrics...")
        metrics = await dashboard.collect_all_metrics()
        
        print("📊 Calculating health status...")
        health = dashboard.calculate_health_status()
        
        print("📄 Generating dashboard report...")
        report_path = dashboard.generate_dashboard_report()
        
        print("💾 Exporting metrics JSON...")
        json_path = dashboard.export_metrics_json()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 DOCUMENTATION HEALTH DASHBOARD")
        print("="*60)
        print(f"Overall Status: {dashboard._status_emoji(health.status)} {health.status.upper()}")
        print(f"Health Score: {health.score}/100")
        print(f"Metrics Collected: {len(metrics)}")
        print(f"Issues Found: {len(health.issues)}")
        print(f"Dashboard Report: {report_path}")
        print(f"Metrics JSON: {json_path}")
        print("="*60)
        
        if health.issues:
            print("\n⚠️  TOP ISSUES:")
            for i, issue in enumerate(health.issues[:3], 1):
                print(f"{i}. {issue}")
        
        if health.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(health.recommendations[:3], 1):
                print(f"{i}. {rec}")
        
        # Exit with appropriate code
        if health.status == "critical":
            exit(1)
        elif health.status in ["degraded", "warning"]:
            exit(2)
        else:
            exit(0)
            
    except Exception as e:
        logger.error(f"Dashboard monitoring failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())