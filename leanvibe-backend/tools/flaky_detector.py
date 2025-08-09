#!/usr/bin/env python3
"""
Flaky Test Detector - Track Test Stability Over Time
Identifies tests with inconsistent pass/fail patterns
"""

import argparse
import json
import sys
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class FlakyTestDetector:
    """Detect and track flaky tests based on historical pass/fail patterns"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.metrics_dir = self.project_root / "test_results" / "metrics"
        self.flaky_history_file = self.metrics_dir / "flaky_tests.json"
        
        # Flaky test thresholds
        self.min_runs = 5  # Minimum runs to consider a test for flaky analysis
        self.flaky_threshold = 0.8  # Pass rate below 80% is considered flaky
        self.unstable_threshold = 0.9  # Pass rate below 90% is unstable
        
        # Ensure metrics directory exists
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def load_history(self) -> Dict:
        """Load flaky test history"""
        if not self.flaky_history_file.exists():
            return {"tests": {}, "runs": []}
        
        try:
            with open(self.flaky_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading flaky test history: {e}")
            return {"tests": {}, "runs": []}
    
    def save_history(self, history: Dict):
        """Save flaky test history"""
        try:
            with open(self.flaky_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving flaky test history: {e}")
    
    def run_tests_and_collect(self, test_command: str = "pytest -m unit --tb=no -q") -> Dict[str, bool]:
        """Run tests and collect pass/fail results"""
        print(f"🧪 Running tests: {test_command}")
        
        try:
            result = subprocess.run(
                test_command.split(),
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Parse pytest output for individual test results
            test_results = {}
            output_lines = result.stdout.split('\n')
            
            # Look for test results in pytest output
            for line in output_lines:
                # Match patterns like "test_file.py::test_name PASSED" or "test_file.py::test_name FAILED"
                if '::' in line and ('PASSED' in line or 'FAILED' in line):
                    parts = line.split()
                    if len(parts) >= 2:
                        test_name = parts[0]
                        status = parts[1]
                        test_results[test_name] = status == 'PASSED'
            
            # If no individual results found, try to parse summary
            if not test_results and result.returncode == 0:
                # All tests passed - need to get test names differently
                summary_result = subprocess.run(
                    (test_command + " --collect-only").split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                
                # Extract test names from collection output
                for line in summary_result.stdout.split('\n'):
                    if '::test_' in line and '<Function' in line:
                        match = re.search(r'(\S+::test_\w+)', line)
                        if match:
                            test_results[match.group(1)] = True
            
            return test_results
            
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return {}
    
    def record_test_run(self, test_results: Dict[str, bool]):
        """Record the results of a test run"""
        history = self.load_history()
        
        timestamp = datetime.now().isoformat()
        run_record = {
            "timestamp": timestamp,
            "total_tests": len(test_results),
            "passed": sum(test_results.values()),
            "failed": len(test_results) - sum(test_results.values())
        }
        
        # Add to run history
        history["runs"].append(run_record)
        
        # Update individual test records
        for test_name, passed in test_results.items():
            if test_name not in history["tests"]:
                history["tests"][test_name] = {
                    "runs": [],
                    "total_runs": 0,
                    "total_passes": 0,
                    "pass_rate": 0.0,
                    "first_seen": timestamp,
                    "last_seen": timestamp,
                    "flaky_score": 0.0
                }
            
            test_data = history["tests"][test_name]
            test_data["runs"].append({
                "timestamp": timestamp,
                "passed": passed
            })
            test_data["total_runs"] += 1
            test_data["total_passes"] += 1 if passed else 0
            test_data["pass_rate"] = test_data["total_passes"] / test_data["total_runs"]
            test_data["last_seen"] = timestamp
            
            # Keep only last 50 runs per test for performance
            test_data["runs"] = test_data["runs"][-50:]
        
        # Keep only last 100 overall runs
        history["runs"] = history["runs"][-100:]
        
        self.save_history(history)
        print(f"📝 Recorded {len(test_results)} test results")
    
    def calculate_flaky_score(self, test_data: Dict) -> float:
        """Calculate flakiness score based on pass/fail pattern variance"""
        runs = test_data.get("runs", [])
        if len(runs) < self.min_runs:
            return 0.0
        
        # Look at recent runs (last 20)
        recent_runs = runs[-20:]
        passes = [1 if r["passed"] else 0 for r in recent_runs]
        
        if not passes:
            return 0.0
        
        # Calculate variance in pass/fail patterns
        # A consistently passing or failing test has low variance
        # A flaky test has high variance
        avg_pass_rate = sum(passes) / len(passes)
        variance = sum((p - avg_pass_rate) ** 2 for p in passes) / len(passes)
        
        # Normalize to 0-1 scale where 1 is maximum flakiness
        # Maximum variance is 0.25 (50/50 pass/fail rate)
        flaky_score = min(variance / 0.25, 1.0)
        
        # Penalize tests with low pass rates more
        if avg_pass_rate < 0.5:
            flaky_score *= 1.5  # Boost flaky score for frequently failing tests
        
        return min(flaky_score, 1.0)
    
    def analyze_flaky_tests(self) -> Dict:
        """Analyze test history to identify flaky tests"""
        history = self.load_history()
        tests = history.get("tests", {})
        
        flaky_tests = []
        unstable_tests = []
        stable_tests = []
        
        for test_name, test_data in tests.items():
            if test_data["total_runs"] < self.min_runs:
                continue  # Skip tests with insufficient data
            
            # Update flaky score
            test_data["flaky_score"] = self.calculate_flaky_score(test_data)
            
            pass_rate = test_data["pass_rate"]
            
            if pass_rate < self.flaky_threshold:
                flaky_tests.append((test_name, test_data))
            elif pass_rate < self.unstable_threshold:
                unstable_tests.append((test_name, test_data))
            else:
                stable_tests.append((test_name, test_data))
        
        # Save updated history with flaky scores
        self.save_history(history)
        
        return {
            "flaky": sorted(flaky_tests, key=lambda x: x[1]["flaky_score"], reverse=True),
            "unstable": sorted(unstable_tests, key=lambda x: x[1]["pass_rate"]),
            "stable": len(stable_tests),
            "total": len(tests)
        }
    
    def generate_flaky_report(self) -> bool:
        """Generate a comprehensive flaky test report"""
        analysis = self.analyze_flaky_tests()
        
        print("🔍 Flaky Test Analysis Report")
        print("=" * 50)
        
        total_tests = analysis["total"]
        flaky_count = len(analysis["flaky"])
        unstable_count = len(analysis["unstable"])
        stable_count = analysis["stable"]
        
        print(f"📊 Test Stability Overview:")
        print(f"   Total tests analyzed: {total_tests}")
        if total_tests > 0:
            print(f"   Stable tests: {stable_count} ({stable_count/total_tests*100:.1f}%)")
            print(f"   Unstable tests: {unstable_count} ({unstable_count/total_tests*100:.1f}%)")
            print(f"   Flaky tests: {flaky_count} ({flaky_count/total_tests*100:.1f}%)")
        else:
            print("   No test history available yet - run tests to collect data")
        
        if analysis["flaky"]:
            print(f"\n💥 Flaky Tests (pass rate < {self.flaky_threshold*100:.0f}%):")
            print("-" * 60)
            print("Test Name                                    Pass Rate  Flaky Score")
            print("-" * 60)
            
            for test_name, test_data in analysis["flaky"][:10]:  # Show top 10
                pass_rate = test_data["pass_rate"] * 100
                flaky_score = test_data["flaky_score"]
                short_name = test_name[-40:] if len(test_name) > 40 else test_name
                print(f"{short_name:<40} {pass_rate:6.1f}%    {flaky_score:.3f}")
        
        if analysis["unstable"]:
            print(f"\n⚠️  Unstable Tests (pass rate < {self.unstable_threshold*100:.0f}%):")
            print("-" * 60)
            print("Test Name                                    Pass Rate  Runs")
            print("-" * 60)
            
            for test_name, test_data in analysis["unstable"][:5]:  # Show top 5
                pass_rate = test_data["pass_rate"] * 100
                runs = test_data["total_runs"]
                short_name = test_name[-40:] if len(test_name) > 40 else test_name
                print(f"{short_name:<40} {pass_rate:6.1f}%    {runs:4d}")
        
        # Recommendations
        if flaky_count > 0:
            print(f"\n💡 Recommendations:")
            print(f"   • Fix or quarantine {flaky_count} flaky tests")
            print(f"   • Review test dependencies and timing issues")
            print(f"   • Consider adding retries or better mocking")
        
        if unstable_count > 0:
            print(f"   • Monitor {unstable_count} unstable tests for patterns")
        
        # Return True if test suite is stable (< 5% flaky tests)
        if total_tests > 0:
            flaky_percentage = flaky_count / total_tests * 100
            return flaky_percentage < 5.0
        else:
            return True  # No data means no flaky tests
    
    def collect_and_analyze(self, iterations: int = 3) -> bool:
        """Run tests multiple times and analyze for flaky patterns"""
        print(f"🔬 Running {iterations} test iterations to detect flaky tests...")
        
        for i in range(iterations):
            print(f"\n📋 Iteration {i+1}/{iterations}")
            test_results = self.run_tests_and_collect()
            
            if test_results:
                self.record_test_run(test_results)
            else:
                print("⚠️  No test results collected in this iteration")
        
        print(f"\n🔍 Analyzing results...")
        return self.generate_flaky_report()


def main():
    parser = argparse.ArgumentParser(description="Flaky Test Detector")
    parser.add_argument("--analyze", action="store_true", 
                       help="Analyze existing test history for flaky patterns")
    parser.add_argument("--collect", type=int, metavar="N", 
                       help="Run tests N times and collect results")
    parser.add_argument("--test-command", default="pytest -m unit --tb=no -q", 
                       help="Test command to run")
    parser.add_argument("--project-root", default=".", 
                       help="Project root directory")
    
    args = parser.parse_args()
    
    detector = FlakyTestDetector(args.project_root)
    
    if args.collect:
        success = detector.collect_and_analyze(args.collect)
        sys.exit(0 if success else 1)
    
    if args.analyze:
        success = detector.generate_flaky_report()
        sys.exit(0 if success else 1)
    
    # Default: analyze existing data
    success = detector.generate_flaky_report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()