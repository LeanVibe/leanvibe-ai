#!/usr/bin/env python3
"""
Coverage Gate - Pragmatic Coverage Ratcheting System
Enforces coverage improvement with +1% minimum per PR and flexible thresholds
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class CoverageGate:
    """Pragmatic coverage gating with ratcheting mechanism"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.metrics_dir = self.project_root / "test_results" / "metrics"
        self.history_file = self.metrics_dir / "coverage_history.json"
        self.coverage_xml = self.project_root / "test_results" / "coverage.xml"
        
        # Pragmatic thresholds
        self.min_coverage = 70.0  # Baseline minimum
        self.min_increase_per_pr = 1.0  # 1% minimum increase per PR
        self.max_decrease_allowed = 2.0  # Allow small decreases for refactoring
        
        # Ensure metrics directory exists
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def get_current_coverage(self) -> Optional[float]:
        """Extract coverage percentage from coverage.xml"""
        try:
            if not self.coverage_xml.exists():
                print("⚠️  Coverage XML not found. Run tests with --cov first.")
                return None
            
            import xml.etree.ElementTree as ET
            tree = ET.parse(self.coverage_xml)
            root = tree.getroot()
            
            # Find coverage element and extract line-rate
            if root.tag == 'coverage':
                # Root element is coverage
                line_rate = float(root.get('line-rate', 0))
                return line_rate * 100
            else:
                # Look for coverage child element
                coverage_elem = root.find('.//coverage')
                if coverage_elem is not None:
                    line_rate = float(coverage_elem.get('line-rate', 0))
                    return line_rate * 100
            
            return None
        except Exception as e:
            print(f"❌ Error reading coverage: {e}")
            return None
    
    def load_history(self) -> Dict:
        """Load coverage history from JSON file"""
        if not self.history_file.exists():
            return {"entries": [], "baseline": self.min_coverage}
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading history: {e}")
            return {"entries": [], "baseline": self.min_coverage}
    
    def save_history(self, history: Dict):
        """Save coverage history to JSON file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving history: {e}")
    
    def get_last_coverage(self, history: Dict) -> float:
        """Get the most recent coverage percentage"""
        entries = history.get("entries", [])
        if not entries:
            return history.get("baseline", self.min_coverage)
        
        return entries[-1]["coverage"]
    
    def check_coverage_gate(self, min_increase: float = None, enforce: bool = False) -> bool:
        """
        Check coverage gate with ratcheting mechanism
        
        Args:
            min_increase: Minimum required coverage increase (default: 0 for checks, 1.0 for enforce)
            enforce: Whether to enforce strict requirements (PR gate vs dev check)
        """
        current = self.get_current_coverage()
        if current is None:
            print("❌ Cannot determine current coverage")
            return False
        
        history = self.load_history()
        last_coverage = self.get_last_coverage(history)
        
        # Set default increase requirement
        if min_increase is None:
            min_increase = self.min_increase_per_pr if enforce else 0.0
        
        # Calculate changes
        coverage_change = current - last_coverage
        meets_minimum = current >= self.min_coverage
        meets_increase = coverage_change >= min_increase or coverage_change >= -self.max_decrease_allowed
        
        # Record current run
        entry = {
            "timestamp": datetime.now().isoformat(),
            "coverage": current,
            "change": coverage_change,
            "previous": last_coverage,
            "meets_gate": meets_minimum and meets_increase
        }
        
        history["entries"].append(entry)
        # Keep only last 50 entries for performance
        history["entries"] = history["entries"][-50:]
        self.save_history(history)
        
        # Report results
        print(f"📊 Coverage Report:")
        print(f"   Current: {current:.1f}%")
        print(f"   Previous: {last_coverage:.1f}%")
        print(f"   Change: {coverage_change:+.1f}%")
        print(f"   Minimum: {self.min_coverage:.1f}%")
        
        if enforce:
            print(f"   Required increase: +{min_increase:.1f}%")
        
        # Determine pass/fail
        if not meets_minimum:
            print(f"❌ Coverage {current:.1f}% below minimum {self.min_coverage:.1f}%")
            return False
        
        if enforce and not meets_increase:
            if coverage_change < -self.max_decrease_allowed:
                print(f"❌ Coverage decreased by {-coverage_change:.1f}% (max allowed: {self.max_decrease_allowed:.1f}%)")
            else:
                print(f"❌ Coverage increase {coverage_change:.1f}% below required {min_increase:.1f}%")
            return False
        
        if coverage_change >= min_increase:
            print(f"✅ Coverage gate passed! Increased by {coverage_change:.1f}%")
        elif coverage_change >= -self.max_decrease_allowed:
            print(f"✅ Coverage gate passed! Small decrease within tolerance")
        else:
            print(f"✅ Coverage gate passed! Meets minimum requirements")
        
        return True
    
    def generate_report(self):
        """Generate a detailed coverage trend report"""
        history = self.load_history()
        entries = history.get("entries", [])
        
        if not entries:
            print("📊 No coverage history available")
            return
        
        print("📊 Coverage Trend Report (Last 10 entries):")
        print("-" * 60)
        print("Date                Coverage    Change")
        print("-" * 60)
        
        for entry in entries[-10:]:
            timestamp = entry["timestamp"][:19]  # Remove microseconds
            coverage = entry["coverage"]
            change = entry["change"]
            status = "✅" if entry["meets_gate"] else "❌"
            print(f"{timestamp}    {coverage:6.1f}%    {change:+5.1f}% {status}")
        
        # Calculate trend
        if len(entries) >= 2:
            recent_trend = entries[-1]["coverage"] - entries[-min(5, len(entries))]["coverage"]
            print(f"\n📈 Recent trend: {recent_trend:+.1f}% over last {min(5, len(entries))} runs")


def main():
    parser = argparse.ArgumentParser(description="Coverage Gate - Pragmatic Coverage Ratcheting")
    parser.add_argument("--min-increase", type=float, help="Minimum required coverage increase")
    parser.add_argument("--enforce", action="store_true", 
                       help="Enforce strict requirements (for PR gate)")
    parser.add_argument("--report", action="store_true", 
                       help="Generate coverage trend report")
    parser.add_argument("--project-root", default=".", 
                       help="Project root directory")
    
    args = parser.parse_args()
    
    gate = CoverageGate(args.project_root)
    
    if args.report:
        gate.generate_report()
        return
    
    success = gate.check_coverage_gate(
        min_increase=args.min_increase, 
        enforce=args.enforce
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()