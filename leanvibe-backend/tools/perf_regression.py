#!/usr/bin/env python3
"""
Performance Regression Detector - Monitor Performance with Budgets
Track performance metrics and detect regressions against baseline
"""

import argparse
import json
import subprocess
import sys
import time
import psutil
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from statistics import mean, median


class PerformanceMonitor:
    """Monitor and track performance metrics with regression detection"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.metrics_dir = self.project_root / "test_results" / "metrics"
        self.perf_history_file = self.metrics_dir / "performance.json"
        
        # Performance budgets (in milliseconds/bytes)
        self.budgets = {
            "api_response_time": 500,      # 500ms max API response
            "test_execution_time": 10000,  # 10s max test suite
            "memory_usage": 100 * 1024 * 1024,  # 100MB max memory
            "startup_time": 2000,          # 2s max startup
            "throughput_min": 100,         # 100 requests/second minimum
        }
        
        # Regression thresholds
        self.regression_threshold = 10.0  # 10% performance degradation
        self.improvement_threshold = 5.0  # 5% improvement worth noting
        
        # Ensure metrics directory exists
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def load_history(self) -> Dict:
        """Load performance history"""
        if not self.perf_history_file.exists():
            return {"runs": [], "baselines": {}}
        
        try:
            with open(self.perf_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading performance history: {e}")
            return {"runs": [], "baselines": {}}
    
    def save_history(self, history: Dict):
        """Save performance history"""
        try:
            with open(self.perf_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving performance history: {e}")
    
    def measure_test_execution(self) -> Dict[str, float]:
        """Measure test execution performance"""
        print("🧪 Measuring test execution performance...")
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            result = subprocess.run(
                ["pytest", "-m", "unit", "--tb=no", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            memory_delta = end_memory - start_memory
            
            return {
                "test_execution_time": execution_time,
                "memory_usage": max(end_memory, memory_delta),
                "tests_passed": result.returncode == 0,
                "output_length": len(result.stdout) + len(result.stderr)
            }
            
        except Exception as e:
            print(f"❌ Error measuring test execution: {e}")
            return {}
    
    def measure_api_performance(self, base_url: str = "http://localhost:8000") -> Dict[str, float]:
        """Measure API endpoint performance"""
        print("🌐 Measuring API performance...")
        
        endpoints = [
            "/health",
            "/api/v1/projects",
            "/api/v1/tasks",
        ]
        
        metrics = {}
        total_requests = 0
        total_time = 0
        successful_requests = 0
        
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                
                # Measure multiple requests for average
                times = []
                for _ in range(5):
                    start = time.time()
                    response = requests.get(url, timeout=5)
                    end = time.time()
                    
                    response_time = (end - start) * 1000  # Convert to ms
                    times.append(response_time)
                    total_requests += 1
                    total_time += response_time
                    
                    if response.status_code == 200:
                        successful_requests += 1
                
                if times:
                    metrics[f"api_{endpoint.replace('/', '_').strip('_')}_avg"] = mean(times)
                    metrics[f"api_{endpoint.replace('/', '_').strip('_')}_p95"] = sorted(times)[int(len(times) * 0.95)]
                    
            except Exception as e:
                print(f"⚠️  Could not measure {endpoint}: {e}")
                metrics[f"api_{endpoint.replace('/', '_').strip('_')}_avg"] = None
        
        # Calculate throughput
        if total_time > 0:
            throughput = (successful_requests / (total_time / 1000))  # requests per second
            metrics["throughput"] = throughput
        
        if total_requests > 0:
            metrics["api_success_rate"] = (successful_requests / total_requests) * 100
        
        return metrics
    
    def measure_startup_time(self) -> Dict[str, float]:
        """Measure application startup time"""
        print("🚀 Measuring startup time...")
        
        try:
            start_time = time.time()
            
            # Try to start the server and measure time to first response
            process = subprocess.Popen(
                ["python", "-m", "app.main"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to be ready (try health endpoint)
            max_wait = 30  # seconds
            start_wait = time.time()
            
            while (time.time() - start_wait) < max_wait:
                try:
                    response = requests.get("http://localhost:8000/health", timeout=1)
                    if response.status_code == 200:
                        startup_time = (time.time() - start_time) * 1000  # Convert to ms
                        process.terminate()
                        process.wait(timeout=5)
                        return {"startup_time": startup_time}
                except:
                    time.sleep(0.5)
            
            # Cleanup if we reach here
            process.terminate()
            process.wait(timeout=5)
            
            return {"startup_time": None}  # Failed to measure
            
        except Exception as e:
            print(f"⚠️  Could not measure startup time: {e}")
            return {"startup_time": None}
    
    def run_performance_suite(self, include_api: bool = False) -> Dict[str, Any]:
        """Run comprehensive performance measurement suite"""
        print("📊 Running performance measurement suite...")
        
        timestamp = datetime.now().isoformat()
        metrics = {"timestamp": timestamp}
        
        # Always measure test execution
        test_metrics = self.measure_test_execution()
        metrics.update(test_metrics)
        
        # Optionally measure API performance (requires running server)
        if include_api:
            api_metrics = self.measure_api_performance()
            metrics.update(api_metrics)
            
            startup_metrics = self.measure_startup_time()
            metrics.update(startup_metrics)
        
        return metrics
    
    def calculate_baseline(self, history: Dict, metric_name: str) -> Optional[float]:
        """Calculate baseline value for a metric from historical data"""
        runs = history.get("runs", [])
        values = []
        
        # Look at last 10 successful runs for baseline
        for run in runs[-10:]:
            if metric_name in run and run[metric_name] is not None:
                values.append(run[metric_name])
        
        if len(values) >= 3:  # Need at least 3 data points
            return median(values)  # Use median for stability
        
        return None
    
    def detect_regressions(self, current_metrics: Dict, baseline_commit: str = None) -> Dict:
        """Detect performance regressions against baseline"""
        history = self.load_history()
        
        regressions = []
        improvements = []
        
        for metric_name, current_value in current_metrics.items():
            if metric_name == "timestamp" or current_value is None:
                continue
            
            # Get baseline value
            baseline_value = None
            if baseline_commit:
                # Try to find specific commit baseline
                for run in history["runs"]:
                    if run.get("commit") == baseline_commit and metric_name in run:
                        baseline_value = run[metric_name]
                        break
            
            if baseline_value is None:
                baseline_value = self.calculate_baseline(history, metric_name)
            
            if baseline_value is None:
                continue  # Skip if no baseline available
            
            # Calculate percentage change
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
            
            # Check against budgets
            budget_exceeded = False
            if metric_name in self.budgets and current_value > self.budgets[metric_name]:
                budget_exceeded = True
            
            # Determine if regression or improvement
            is_regression = False
            is_improvement = False
            
            # For time-based metrics, higher is worse
            if any(keyword in metric_name.lower() for keyword in ["time", "duration", "latency"]):
                if change_percent > self.regression_threshold:
                    is_regression = True
                elif change_percent < -self.improvement_threshold:
                    is_improvement = True
            
            # For throughput, higher is better
            elif "throughput" in metric_name.lower():
                if change_percent < -self.regression_threshold:
                    is_regression = True
                elif change_percent > self.improvement_threshold:
                    is_improvement = True
            
            # For memory, higher is worse
            elif "memory" in metric_name.lower():
                if change_percent > self.regression_threshold:
                    is_regression = True
                elif change_percent < -self.improvement_threshold:
                    is_improvement = True
            
            if is_regression or budget_exceeded:
                regressions.append({
                    "metric": metric_name,
                    "current": current_value,
                    "baseline": baseline_value,
                    "change_percent": change_percent,
                    "budget": self.budgets.get(metric_name),
                    "budget_exceeded": budget_exceeded
                })
            
            if is_improvement:
                improvements.append({
                    "metric": metric_name,
                    "current": current_value,
                    "baseline": baseline_value,
                    "change_percent": change_percent
                })
        
        return {
            "regressions": regressions,
            "improvements": improvements,
            "total_metrics": len([k for k in current_metrics.keys() if k != "timestamp"])
        }
    
    def generate_performance_report(self, include_api: bool = False, baseline_commit: str = None) -> bool:
        """Generate comprehensive performance report with regression detection"""
        print("📈 Generating performance report...")
        
        # Run performance measurements
        current_metrics = self.run_performance_suite(include_api)
        
        # Load and update history
        history = self.load_history()
        history["runs"].append(current_metrics)
        
        # Keep only last 50 runs for performance
        history["runs"] = history["runs"][-50:]
        
        # Detect regressions
        analysis = self.detect_regressions(current_metrics, baseline_commit)
        
        # Save updated history
        self.save_history(history)
        
        # Generate report
        print("📊 Performance Analysis Report")
        print("=" * 50)
        
        # Current metrics
        print("📋 Current Metrics:")
        for metric, value in current_metrics.items():
            if metric != "timestamp" and value is not None:
                unit = "ms" if "time" in metric else ("MB" if "memory" in metric else "")
                budget = self.budgets.get(metric)
                budget_str = f" (budget: {budget}{unit})" if budget else ""
                
                if isinstance(value, float):
                    print(f"   {metric}: {value:.2f}{unit}{budget_str}")
                else:
                    print(f"   {metric}: {value}{unit}{budget_str}")
        
        # Regressions
        regressions = analysis["regressions"]
        improvements = analysis["improvements"]
        
        if regressions:
            print(f"\n💥 Performance Regressions ({len(regressions)}):")
            print("-" * 60)
            for reg in regressions:
                status = "📊" if reg["budget_exceeded"] else "📈"
                print(f"   {status} {reg['metric']}: {reg['change_percent']:+.1f}% "
                      f"({reg['baseline']:.2f} → {reg['current']:.2f})")
                if reg["budget_exceeded"]:
                    print(f"       ⚠️  Budget exceeded: {reg['budget']}")
        
        if improvements:
            print(f"\n✅ Performance Improvements ({len(improvements)}):")
            for imp in improvements:
                print(f"   📉 {imp['metric']}: {imp['change_percent']:+.1f}% "
                      f"({imp['baseline']:.2f} → {imp['current']:.2f})")
        
        # Overall assessment
        if regressions:
            print(f"\n❌ Performance regression detected: {len(regressions)} metrics regressed")
            return False
        elif improvements:
            print(f"\n✅ Performance improved: {len(improvements)} metrics improved")
        else:
            print(f"\n✅ Performance stable: no significant changes")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Performance Regression Detector")
    parser.add_argument("--baseline", help="Baseline commit to compare against")
    parser.add_argument("--threshold", type=float, default=10.0, 
                       help="Regression threshold percentage")
    parser.add_argument("--include-api", action="store_true", 
                       help="Include API performance measurements")
    parser.add_argument("--full-analysis", action="store_true", 
                       help="Run comprehensive analysis including API and startup")
    parser.add_argument("--project-root", default=".", 
                       help="Project root directory")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.project_root)
    
    if args.threshold:
        monitor.regression_threshold = args.threshold
    
    include_api = args.include_api or args.full_analysis
    
    success = monitor.generate_performance_report(
        include_api=include_api,
        baseline_commit=args.baseline
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()