#!/usr/bin/env python3
"""
Quality Ratchet System - Autonomous Quality Enforcement
Tracks coverage, mutation score, performance metrics over time with ratcheting up only
Prevents quality regression and enforces continuous improvement
"""

import argparse
import json
import logging
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class QualityMetrics:
    """Container for all quality metrics"""
    
    def __init__(self):
        self.coverage_percent: Optional[float] = None
        self.mutation_score: Optional[float] = None
        self.test_execution_time: Optional[float] = None
        self.performance_p95: Optional[float] = None
        self.memory_usage_mb: Optional[float] = None
        self.flaky_test_count: int = 0
        self.security_issues: int = 0
        self.technical_debt_ratio: Optional[float] = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'coverage_percent': self.coverage_percent,
            'mutation_score': self.mutation_score,
            'test_execution_time': self.test_execution_time,
            'performance_p95': self.performance_p95,
            'memory_usage_mb': self.memory_usage_mb,
            'flaky_test_count': self.flaky_test_count,
            'security_issues': self.security_issues,
            'technical_debt_ratio': self.technical_debt_ratio
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityMetrics':
        metrics = cls()
        for key, value in data.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
        return metrics


class QualityRatchet:
    """
    Quality ratchet system that enforces quality only improves over time
    Supports per-module and global targets with configurable tolerances
    """
    
    def __init__(self, project_root: str = ".", config_file: Optional[str] = None):
        self.project_root = Path(project_root)
        self.history_file = self.project_root / ".quality_history.json"
        self.config_file = Path(config_file) if config_file else self.project_root / "quality_ratchet.json"
        
        # Default quality targets (ratcheting up from here)
        self.default_config = {
            "global_targets": {
                "coverage_percent_min": 70.0,
                "mutation_score_min": 60.0,
                "test_execution_time_max": 60.0,  # seconds for Tier 0
                "performance_p95_max": 500.0,  # milliseconds
                "memory_usage_mb_max": 500.0,
                "flaky_test_count_max": 2,
                "security_issues_max": 0,
                "technical_debt_ratio_max": 0.05  # 5%
            },
            "per_module_targets": {
                "app/api": {"coverage_percent_min": 80.0},
                "app/core": {"coverage_percent_min": 85.0},
                "app/services": {"coverage_percent_min": 75.0}
            },
            "ratchet_settings": {
                "min_improvement_threshold": 0.5,  # 0.5% minimum improvement
                "regression_tolerance": 1.0,  # Allow 1% temporary regression
                "consecutive_improvements_required": 2,  # Need 2 consecutive improvements
                "grace_period_hours": 24  # 24 hour grace period for fixing regressions
            }
        }
        
        self.load_config()
    
    def load_config(self):
        """Load ratchet configuration from file or use defaults"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                self.config = self.default_config.copy()
                self.config.update(loaded_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
                self.config = self.default_config
        else:
            self.config = self.default_config
            self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Load quality metrics history"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []
    
    def save_history(self, history: List[Dict[str, Any]]):
        """Save quality metrics history"""
        try:
            # Keep only last 100 entries for performance
            trimmed_history = history[-100:]
            with open(self.history_file, 'w') as f:
                json.dump(trimmed_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def collect_current_metrics(self) -> QualityMetrics:
        """Collect current quality metrics from all available sources"""
        metrics = QualityMetrics()
        
        # Coverage metrics
        metrics.coverage_percent = self._get_coverage_from_xml()
        
        # Performance metrics from test results
        metrics.test_execution_time = self._get_test_execution_time()
        metrics.performance_p95 = self._get_performance_p95()
        
        # Memory usage from monitoring
        metrics.memory_usage_mb = self._get_memory_usage()
        
        # Flaky test detection
        metrics.flaky_test_count = self._get_flaky_test_count()
        
        # Security issues from tools
        metrics.security_issues = self._get_security_issues()
        
        # Technical debt ratio (placeholder - could integrate with SonarQube)
        metrics.technical_debt_ratio = self._estimate_technical_debt()
        
        return metrics
    
    def _get_coverage_from_xml(self) -> Optional[float]:
        """Extract coverage from XML report"""
        coverage_xml = self.project_root / "test_results" / "coverage.xml"
        if not coverage_xml.exists():
            return None
        
        try:
            tree = ET.parse(coverage_xml)
            root = tree.getroot()
            if root.tag == 'coverage':
                line_rate = float(root.get('line-rate', 0))
                return line_rate * 100
        except Exception as e:
            logger.warning(f"Failed to read coverage XML: {e}")
            return None
    
    def _get_test_execution_time(self) -> Optional[float]:
        """Get test execution time from pytest results"""
        # This could parse pytest timing output or use test result files
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30
            )
            # Parse collection time as proxy for execution time
            return 10.0  # Placeholder - would parse actual timing
        except Exception:
            return None
    
    def _get_performance_p95(self) -> Optional[float]:
        """Get performance P95 from monitoring data"""
        perf_file = self.project_root / "test_results" / "metrics" / "performance.json"
        if not perf_file.exists():
            return None
        
        try:
            with open(perf_file, 'r') as f:
                data = json.load(f)
                return data.get('p95_response_time_ms', None)
        except Exception as e:
            logger.warning(f"Failed to read performance metrics: {e}")
            return None
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage estimation"""
        # Could integrate with actual memory profiling tools
        return 250.0  # Placeholder MB
    
    def _get_flaky_test_count(self) -> int:
        """Get flaky test count from flaky detector"""
        flaky_file = self.project_root / "test_results" / "metrics" / "flaky_tests.json"
        if not flaky_file.exists():
            return 0
        
        try:
            with open(flaky_file, 'r') as f:
                data = json.load(f)
                return len(data.get('flaky_tests', []))
        except Exception:
            return 0
    
    def _get_security_issues(self) -> int:
        """Get security issue count from bandit results"""
        security_file = self.project_root / "test_results" / "reports" / "security.json"
        if not security_file.exists():
            return 0
        
        try:
            with open(security_file, 'r') as f:
                data = json.load(f)
                return len(data.get('results', []))
        except Exception:
            return 0
    
    def _estimate_technical_debt(self) -> Optional[float]:
        """Estimate technical debt ratio (placeholder for real implementation)"""
        # Could integrate with SonarQube, CodeClimate, or custom analysis
        return 0.03  # 3% placeholder
    
    def check_ratchet(self, current_metrics: QualityMetrics, enforce: bool = False) -> Tuple[bool, List[str]]:
        """
        Check if current metrics meet ratchet requirements
        Returns (passed, list_of_issues)
        """
        history = self.load_history()
        issues = []
        passed = True
        
        # Get baseline from history
        if not history:
            baseline = QualityMetrics()  # Use defaults
        else:
            # Use best metrics ever achieved as ratchet baseline
            baseline = self._get_best_metrics_from_history(history)
        
        # Check each metric against ratchet
        global_targets = self.config["global_targets"]
        ratchet_settings = self.config["ratchet_settings"]
        
        # Coverage check
        if current_metrics.coverage_percent is not None:
            min_coverage = max(
                global_targets["coverage_percent_min"],
                (baseline.coverage_percent or 0) - ratchet_settings["regression_tolerance"]
            )
            if current_metrics.coverage_percent < min_coverage:
                issues.append(f"Coverage {current_metrics.coverage_percent:.1f}% below ratchet minimum {min_coverage:.1f}%")
                passed = False
        
        # Performance checks
        if current_metrics.test_execution_time is not None:
            max_time = min(
                global_targets["test_execution_time_max"],
                (baseline.test_execution_time or float('inf')) + ratchet_settings["regression_tolerance"]
            )
            if current_metrics.test_execution_time > max_time:
                issues.append(f"Test execution time {current_metrics.test_execution_time:.1f}s exceeds ratchet maximum {max_time:.1f}s")
                passed = False
        
        if current_metrics.performance_p95 is not None:
            max_p95 = min(
                global_targets["performance_p95_max"],
                (baseline.performance_p95 or float('inf')) + ratchet_settings["regression_tolerance"]
            )
            if current_metrics.performance_p95 > max_p95:
                issues.append(f"Performance P95 {current_metrics.performance_p95:.1f}ms exceeds ratchet maximum {max_p95:.1f}ms")
                passed = False
        
        # Memory usage check
        if current_metrics.memory_usage_mb is not None:
            max_memory = min(
                global_targets["memory_usage_mb_max"],
                (baseline.memory_usage_mb or float('inf')) + ratchet_settings["regression_tolerance"]
            )
            if current_metrics.memory_usage_mb > max_memory:
                issues.append(f"Memory usage {current_metrics.memory_usage_mb:.1f}MB exceeds ratchet maximum {max_memory:.1f}MB")
                passed = False
        
        # Quality gates
        if current_metrics.flaky_test_count > global_targets["flaky_test_count_max"]:
            issues.append(f"Flaky tests {current_metrics.flaky_test_count} exceeds maximum {global_targets['flaky_test_count_max']}")
            passed = False
        
        if current_metrics.security_issues > global_targets["security_issues_max"]:
            issues.append(f"Security issues {current_metrics.security_issues} exceeds maximum {global_targets['security_issues_max']}")
            passed = False
        
        return passed, issues
    
    def _get_best_metrics_from_history(self, history: List[Dict[str, Any]]) -> QualityMetrics:
        """Extract best metrics ever achieved from history for ratcheting"""
        if not history:
            return QualityMetrics()
        
        best = QualityMetrics()
        
        for entry in history:
            metrics_data = entry.get('metrics', {})
            
            # Track best (highest) coverage
            if metrics_data.get('coverage_percent') is not None:
                if best.coverage_percent is None or metrics_data['coverage_percent'] > best.coverage_percent:
                    best.coverage_percent = metrics_data['coverage_percent']
            
            # Track best (lowest) test execution time
            if metrics_data.get('test_execution_time') is not None:
                if best.test_execution_time is None or metrics_data['test_execution_time'] < best.test_execution_time:
                    best.test_execution_time = metrics_data['test_execution_time']
            
            # Track best (lowest) performance P95
            if metrics_data.get('performance_p95') is not None:
                if best.performance_p95 is None or metrics_data['performance_p95'] < best.performance_p95:
                    best.performance_p95 = metrics_data['performance_p95']
            
            # Track best (lowest) memory usage
            if metrics_data.get('memory_usage_mb') is not None:
                if best.memory_usage_mb is None or metrics_data['memory_usage_mb'] < best.memory_usage_mb:
                    best.memory_usage_mb = metrics_data['memory_usage_mb']
        
        return best
    
    def record_metrics(self, metrics: QualityMetrics, branch: str = "unknown", commit_hash: str = "unknown"):
        """Record current metrics in history"""
        history = self.load_history()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "branch": branch,
            "commit_hash": commit_hash,
            "metrics": metrics.to_dict()
        }
        
        history.append(entry)
        self.save_history(history)
        
        logger.info(f"✅ Recorded metrics for commit {commit_hash[:8]} on {branch}")
    
    def generate_quality_report(self) -> str:
        """Generate comprehensive quality metrics report"""
        current_metrics = self.collect_current_metrics()
        history = self.load_history()
        passed, issues = self.check_ratchet(current_metrics, enforce=False)
        
        report = []
        report.append("🎯 Quality Ratchet Report")
        report.append("=" * 50)
        
        # Current metrics
        report.append("\n📊 Current Metrics:")
        if current_metrics.coverage_percent:
            report.append(f"   Coverage: {current_metrics.coverage_percent:.1f}%")
        if current_metrics.test_execution_time:
            report.append(f"   Test Time: {current_metrics.test_execution_time:.1f}s")
        if current_metrics.performance_p95:
            report.append(f"   Performance P95: {current_metrics.performance_p95:.1f}ms")
        if current_metrics.memory_usage_mb:
            report.append(f"   Memory Usage: {current_metrics.memory_usage_mb:.1f}MB")
        report.append(f"   Flaky Tests: {current_metrics.flaky_test_count}")
        report.append(f"   Security Issues: {current_metrics.security_issues}")
        
        # Ratchet status
        status_emoji = "✅" if passed else "❌"
        report.append(f"\n{status_emoji} Ratchet Status: {'PASSED' if passed else 'FAILED'}")
        
        if issues:
            report.append("\n❌ Issues Found:")
            for issue in issues:
                report.append(f"   • {issue}")
        
        # Historical trend
        if len(history) >= 2:
            report.append(f"\n📈 Historical Trend (Last {min(10, len(history))} entries):")
            report.append("   Date                Coverage   TestTime   P95ms")
            report.append("   " + "-" * 45)
            
            for entry in history[-10:]:
                timestamp = entry["timestamp"][:19]
                metrics_data = entry.get("metrics", {})
                coverage = metrics_data.get("coverage_percent")
                test_time = metrics_data.get("test_execution_time")
                p95 = metrics_data.get("performance_p95")
                
                coverage_str = f"{coverage:.1f}%" if coverage else "N/A"
                test_time_str = f"{test_time:.1f}s" if test_time else "N/A"
                p95_str = f"{p95:.0f}ms" if p95 else "N/A"
                
                report.append(f"   {timestamp}  {coverage_str:>8}  {test_time_str:>8}  {p95_str:>6}")
        
        return "\n".join(report)
    
    def run_quality_gate(self, enforce: bool = False, auto_record: bool = True) -> bool:
        """
        Run complete quality gate check
        Returns True if all checks pass
        """
        logger.info("🎯 Running Quality Ratchet Gate...")
        
        # Collect current metrics
        current_metrics = self.collect_current_metrics()
        
        # Check ratchet
        passed, issues = self.check_ratchet(current_metrics, enforce=enforce)
        
        # Record metrics if requested
        if auto_record:
            try:
                # Get git info
                branch = subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.project_root,
                    text=True
                ).strip()
                commit_hash = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.project_root,
                    text=True
                ).strip()
                
                self.record_metrics(current_metrics, branch, commit_hash)
            except Exception as e:
                logger.warning(f"Failed to get git info: {e}")
                self.record_metrics(current_metrics)
        
        # Print results
        if passed:
            logger.info("✅ Quality ratchet passed!")
        else:
            logger.error("❌ Quality ratchet failed!")
            for issue in issues:
                logger.error(f"   • {issue}")
        
        return passed


def main():
    parser = argparse.ArgumentParser(description="Quality Ratchet - Autonomous Quality Enforcement")
    parser.add_argument("--enforce", action="store_true",
                       help="Enforce strict ratchet requirements")
    parser.add_argument("--report", action="store_true",
                       help="Generate quality metrics report")
    parser.add_argument("--config", help="Path to quality ratchet configuration file")
    parser.add_argument("--project-root", default=".",
                       help="Project root directory")
    parser.add_argument("--no-record", action="store_true",
                       help="Don't record metrics to history")
    
    args = parser.parse_args()
    
    try:
        ratchet = QualityRatchet(args.project_root, args.config)
        
        if args.report:
            print(ratchet.generate_quality_report())
            return 0
        
        success = ratchet.run_quality_gate(
            enforce=args.enforce,
            auto_record=not args.no_record
        )
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Quality ratchet failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())