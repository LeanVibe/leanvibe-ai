#!/usr/bin/env python3
"""
Metrics Dashboard - Quality Metrics Tracking and Visualization
Provides real-time and historical view of quality ratchet metrics
Integrates with quality_ratchet.py for comprehensive quality monitoring
"""

import argparse
import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MetricsDashboard:
    """
    Metrics dashboard for quality monitoring and visualization
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.history_file = self.project_root / ".quality_history.json"
        self.performance_sla_file = self.project_root / "budgets" / "performance_sla.json"
        self.dashboard_port = 8080
        
    def load_quality_history(self) -> List[Dict[str, Any]]:
        """Load quality metrics history"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load quality history: {e}")
            return []
    
    def load_performance_budgets(self) -> Dict[str, Any]:
        """Load performance budgets and SLA targets"""
        if not self.performance_sla_file.exists():
            return {}
        
        try:
            with open(self.performance_sla_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load performance budgets: {e}")
            return {}
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics using quality ratchet system"""
        try:
            # Import quality_ratchet module from the same directory
            import importlib.util
            spec = importlib.util.spec_from_file_location("quality_ratchet", self.project_root / "tools" / "quality_ratchet.py")
            quality_ratchet_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(quality_ratchet_module)
            
            ratchet = quality_ratchet_module.QualityRatchet(str(self.project_root))
            metrics = ratchet.collect_current_metrics()
            return metrics.to_dict()
        except Exception as e:
            logger.warning(f"Failed to collect current metrics: {e}")
            return {}
    
    def calculate_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trends from historical data"""
        if len(history) < 2:
            return {}
        
        trends = {}
        recent_entries = history[-10:]  # Last 10 entries
        
        # Calculate coverage trend
        coverage_values = [
            entry.get('metrics', {}).get('coverage_percent')
            for entry in recent_entries
            if entry.get('metrics', {}).get('coverage_percent') is not None
        ]
        
        if len(coverage_values) >= 2:
            coverage_trend = coverage_values[-1] - coverage_values[0]
            trends['coverage_trend'] = {
                'change': coverage_trend,
                'direction': 'up' if coverage_trend > 0 else 'down' if coverage_trend < 0 else 'stable',
                'current': coverage_values[-1],
                'samples': len(coverage_values)
            }
        
        # Calculate test time trend
        test_time_values = [
            entry.get('metrics', {}).get('test_execution_time')
            for entry in recent_entries
            if entry.get('metrics', {}).get('test_execution_time') is not None
        ]
        
        if len(test_time_values) >= 2:
            time_trend = test_time_values[-1] - test_time_values[0]
            trends['test_time_trend'] = {
                'change': time_trend,
                'direction': 'up' if time_trend > 0 else 'down' if time_trend < 0 else 'stable',
                'current': test_time_values[-1],
                'samples': len(test_time_values)
            }
        
        return trends
    
    def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard with metrics visualization"""
        history = self.load_quality_history()
        budgets = self.load_performance_budgets()
        current_metrics = self.get_current_metrics()
        trends = self.calculate_trends(history)
        
        # Prepare data for JavaScript
        chart_data = []
        for entry in history[-30:]:  # Last 30 entries
            timestamp = entry.get('timestamp', '')
            metrics = entry.get('metrics', {})
            chart_data.append({
                'timestamp': timestamp[:19],  # Remove microseconds
                'coverage': metrics.get('coverage_percent'),
                'test_time': metrics.get('test_execution_time'),
                'memory': metrics.get('memory_usage_mb'),
                'flaky_tests': metrics.get('flaky_test_count', 0)
            })
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LeanVibe Quality Metrics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            color: #2d3748;
        }}
        
        .dashboard-header {{
            text-align: center;
            margin-bottom: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #718096;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .metric-trend {{
            margin-top: 10px;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .trend-up {{
            background-color: #c6f6d5;
            color: #2f855a;
        }}
        
        .trend-down {{
            background-color: #fed7d7;
            color: #c53030;
        }}
        
        .trend-stable {{
            background-color: #e2e8f0;
            color: #4a5568;
        }}
        
        .charts-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .chart-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2d3748;
        }}
        
        .sla-status {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .sla-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .sla-item:last-child {{
            border-bottom: none;
        }}
        
        .status-indicator {{
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .status-good {{
            background-color: #c6f6d5;
            color: #2f855a;
        }}
        
        .status-warning {{
            background-color: #fefcbf;
            color: #d69e2e;
        }}
        
        .status-critical {{
            background-color: #fed7d7;
            color: #c53030;
        }}
        
        .refresh-button {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .refresh-button:hover {{
            background: #5a67d8;
        }}
        
        @media (max-width: 768px) {{
            .charts-container {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>🎯 LeanVibe Quality Metrics Dashboard</h1>
        <p>Real-time quality monitoring and ratchet tracking</p>
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{current_metrics.get('coverage_percent', 'N/A')}%</div>
            <div class="metric-label">Test Coverage</div>
            {self._generate_trend_indicator('coverage_trend', trends)}
        </div>
        
        <div class="metric-card">
            <div class="metric-value">{current_metrics.get('test_execution_time', 'N/A')}s</div>
            <div class="metric-label">Test Execution Time</div>
            {self._generate_trend_indicator('test_time_trend', trends)}
        </div>
        
        <div class="metric-card">
            <div class="metric-value">{current_metrics.get('memory_usage_mb', 'N/A')}MB</div>
            <div class="metric-label">Memory Usage</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-value">{current_metrics.get('flaky_test_count', 0)}</div>
            <div class="metric-label">Flaky Tests</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-value">{current_metrics.get('security_issues', 0)}</div>
            <div class="metric-label">Security Issues</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-value">{len(history)}</div>
            <div class="metric-label">Historical Samples</div>
        </div>
    </div>
    
    <div class="charts-container">
        <div class="chart-card">
            <div class="chart-title">Coverage & Test Time Trends</div>
            <canvas id="coverageChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-card">
            <div class="chart-title">Memory & Quality Metrics</div>
            <canvas id="memoryChart" width="400" height="200"></canvas>
        </div>
    </div>
    
    <div class="sla-status">
        <h3>Performance SLA Status</h3>
        {self._generate_sla_status(current_metrics, budgets)}
    </div>
    
    <button class="refresh-button" onclick="location.reload()">🔄 Refresh</button>
    
    <script>
        // Chart data from Python
        const chartData = {json.dumps(chart_data)};
        
        // Coverage & Test Time Chart
        const coverageCtx = document.getElementById('coverageChart').getContext('2d');
        new Chart(coverageCtx, {{
            type: 'line',
            data: {{
                labels: chartData.map(d => d.timestamp.substring(5, 16)),
                datasets: [{{
                    label: 'Coverage %',
                    data: chartData.map(d => d.coverage),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                }}, {{
                    label: 'Test Time (s)',
                    data: chartData.map(d => d.test_time),
                    borderColor: '#f56565',
                    backgroundColor: 'rgba(245, 101, 101, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{
                            display: true,
                            text: 'Coverage %'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{
                            display: true,
                            text: 'Test Time (s)'
                        }},
                        grid: {{
                            drawOnChartArea: false,
                        }},
                    }}
                }}
            }}
        }});
        
        // Memory & Quality Chart
        const memoryCtx = document.getElementById('memoryChart').getContext('2d');
        new Chart(memoryCtx, {{
            type: 'line',
            data: {{
                labels: chartData.map(d => d.timestamp.substring(5, 16)),
                datasets: [{{
                    label: 'Memory (MB)',
                    data: chartData.map(d => d.memory),
                    borderColor: '#48bb78',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                }}, {{
                    label: 'Flaky Tests',
                    data: chartData.map(d => d.flaky_tests),
                    borderColor: '#ed8936',
                    backgroundColor: 'rgba(237, 137, 54, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{
                            display: true,
                            text: 'Memory (MB)'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{
                            display: true,
                            text: 'Flaky Tests'
                        }},
                        grid: {{
                            drawOnChartArea: false,
                        }},
                    }}
                }}
            }}
        }});
        
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""
        return html_content
    
    def _generate_trend_indicator(self, trend_key: str, trends: Dict[str, Any]) -> str:
        """Generate HTML for trend indicator"""
        if trend_key not in trends:
            return ""
        
        trend = trends[trend_key]
        direction = trend['direction']
        change = trend['change']
        
        if direction == 'up':
            class_name = 'trend-up'
            emoji = '📈'
            text = f"{emoji} +{change:.1f}%"
        elif direction == 'down':
            class_name = 'trend-down'
            emoji = '📉'
            text = f"{emoji} {change:.1f}%"
        else:
            class_name = 'trend-stable'
            emoji = '📊'
            text = f"{emoji} Stable"
        
        return f'<div class="metric-trend {class_name}">{text}</div>'
    
    def _generate_sla_status(self, current_metrics: Dict[str, Any], budgets: Dict[str, Any]) -> str:
        """Generate SLA status indicators"""
        if not budgets or 'budgets' not in budgets:
            return "<p>No SLA configuration found</p>"
        
        sla_items = []
        
        # Test suite performance
        test_budgets = budgets['budgets'].get('test_suite_performance', {})
        tier0_target = test_budgets.get('tier_0_tests', {}).get('target_time_seconds', 60)
        current_test_time = current_metrics.get('test_execution_time', 0)
        
        if current_test_time > 0:
            if current_test_time <= tier0_target:
                status = 'status-good'
                status_text = 'GOOD'
            elif current_test_time <= tier0_target * 1.5:
                status = 'status-warning'
                status_text = 'WARNING'
            else:
                status = 'status-critical'
                status_text = 'CRITICAL'
            
            sla_items.append(f'''
                <div class="sla-item">
                    <span>Test Suite Performance (Tier 0)</span>
                    <span class="status-indicator {status}">{status_text}</span>
                </div>
            ''')
        
        # Memory usage
        memory_budgets = budgets['budgets'].get('resource_utilization', {}).get('memory', {})
        memory_target = memory_budgets.get('application_heap_mb', {}).get('target', 256)
        current_memory = current_metrics.get('memory_usage_mb', 0)
        
        if current_memory > 0:
            if current_memory <= memory_target:
                status = 'status-good'
                status_text = 'GOOD'
            elif current_memory <= memory_target * 1.5:
                status = 'status-warning'
                status_text = 'WARNING'
            else:
                status = 'status-critical'
                status_text = 'CRITICAL'
            
            sla_items.append(f'''
                <div class="sla-item">
                    <span>Memory Usage</span>
                    <span class="status-indicator {status}">{status_text}</span>
                </div>
            ''')
        
        # Flaky tests
        flaky_count = current_metrics.get('flaky_test_count', 0)
        if flaky_count == 0:
            status = 'status-good'
            status_text = 'GOOD'
        elif flaky_count <= 2:
            status = 'status-warning'
            status_text = 'WARNING'
        else:
            status = 'status-critical'
            status_text = 'CRITICAL'
        
        sla_items.append(f'''
            <div class="sla-item">
                <span>Flaky Tests</span>
                <span class="status-indicator {status}">{status_text}</span>
            </div>
        ''')
        
        return '\n'.join(sla_items)
    
    def serve_dashboard(self, port: int = 8080, auto_open: bool = True):
        """Serve the dashboard on HTTP server"""
        class DashboardHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/' or self.path == '/index.html':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    
                    dashboard_html = dashboard.generate_html_dashboard()
                    self.wfile.write(dashboard_html.encode())
                else:
                    self.send_error(404)
        
        dashboard = self
        
        try:
            with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
                url = f"http://localhost:{port}"
                print(f"🌐 Serving quality dashboard at {url}")
                print("📊 Dashboard will auto-refresh every 30 seconds")
                print("🔄 Press Ctrl+C to stop")
                
                if auto_open:
                    # Open browser after a short delay
                    threading.Timer(1, lambda: webbrowser.open(url)).start()
                
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n📊 Dashboard server stopped")
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"❌ Port {port} already in use. Try a different port with --port")
            else:
                print(f"❌ Failed to start server: {e}")
    
    def generate_cli_report(self) -> str:
        """Generate text-based report for CLI usage"""
        history = self.load_quality_history()
        current_metrics = self.get_current_metrics()
        trends = self.calculate_trends(history)
        
        lines = []
        lines.append("🎯 LeanVibe Quality Metrics Report")
        lines.append("=" * 50)
        lines.append("")
        
        # Current metrics
        lines.append("📊 Current Metrics:")
        if current_metrics.get('coverage_percent'):
            lines.append(f"   Coverage: {current_metrics['coverage_percent']:.1f}%")
        if current_metrics.get('test_execution_time'):
            lines.append(f"   Test Time: {current_metrics['test_execution_time']:.1f}s")
        if current_metrics.get('memory_usage_mb'):
            lines.append(f"   Memory: {current_metrics['memory_usage_mb']:.1f}MB")
        lines.append(f"   Flaky Tests: {current_metrics.get('flaky_test_count', 0)}")
        lines.append(f"   Security Issues: {current_metrics.get('security_issues', 0)}")
        lines.append("")
        
        # Trends
        if trends:
            lines.append("📈 Trends (Last 10 samples):")
            for trend_key, trend_data in trends.items():
                direction_emoji = "📈" if trend_data['direction'] == 'up' else "📉" if trend_data['direction'] == 'down' else "📊"
                lines.append(f"   {trend_key.replace('_', ' ').title()}: {direction_emoji} {trend_data['change']:+.1f}")
            lines.append("")
        
        # Historical summary
        if history:
            lines.append(f"📚 Historical Data: {len(history)} samples")
            lines.append(f"   Oldest: {history[0]['timestamp'][:19]}")
            lines.append(f"   Newest: {history[-1]['timestamp'][:19]}")
        else:
            lines.append("📚 No historical data available")
        
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="LeanVibe Quality Metrics Dashboard")
    parser.add_argument("--serve", action="store_true",
                       help="Serve dashboard on HTTP server")
    parser.add_argument("--port", type=int, default=8080,
                       help="Port for dashboard server (default: 8080)")
    parser.add_argument("--no-browser", action="store_true",
                       help="Don't auto-open browser")
    parser.add_argument("--report", action="store_true",
                       help="Generate CLI report instead of dashboard")
    parser.add_argument("--project-root", default=".",
                       help="Project root directory")
    
    args = parser.parse_args()
    
    try:
        dashboard = MetricsDashboard(args.project_root)
        
        if args.report:
            print(dashboard.generate_cli_report())
        elif args.serve:
            dashboard.serve_dashboard(args.port, not args.no_browser)
        else:
            # Default: show CLI report
            print(dashboard.generate_cli_report())
        
        return 0
        
    except Exception as e:
        logger.error(f"Dashboard failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())