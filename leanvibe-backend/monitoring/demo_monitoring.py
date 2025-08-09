#!/usr/bin/env python3
"""
LeanVibe Monitoring System Demonstration

This script demonstrates the synthetic probes and observability system in action.
It shows how the XP-principles-based monitoring detects issues in <60s and provides
actionable insights for maintaining system health.

Usage:
    python monitoring/demo_monitoring.py --demo-all
    python monitoring/demo_monitoring.py --demo-probes
    python monitoring/demo_monitoring.py --demo-error-budgets
    python monitoring/demo_monitoring.py --demo-alerts
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import argparse

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.monitoring.synthetic_probes import (
    HealthProbe, MetricsProbe, WebSocketProbe, APIProbe,
    SyntheticProbeRunner, ProbeStatus
)
from app.monitoring.observability import (
    ErrorBudgetTracker, PerformanceBudgets, HealthDashboard,
    AlertManager, error_budget_tracker, performance_budgets,
    health_dashboard, alert_manager
)


class MonitoringDemo:
    """Demonstrates the LeanVibe monitoring system capabilities"""
    
    def __init__(self):
        self.probe_runner = SyntheticProbeRunner()
        print("🚀 LeanVibe Monitoring System Demo")
        print("=" * 60)
        print("Demonstrating XP-principles-based observability:")
        print("- Simple, fast, actionable monitoring")
        print("- Issues detected in <60s, alerts within 120s")
        print("- Clear guidance for system health decisions")
        print("=" * 60)
    
    async def demo_all(self):
        """Run complete monitoring system demonstration"""
        print("\n📊 COMPLETE MONITORING SYSTEM DEMO")
        print("-" * 40)
        
        await self.demo_synthetic_probes()
        await asyncio.sleep(2)
        
        await self.demo_error_budgets()
        await asyncio.sleep(2)
        
        await self.demo_performance_budgets()
        await asyncio.sleep(2)
        
        await self.demo_alert_system()
        await asyncio.sleep(2)
        
        await self.demo_health_dashboard()
        
        print("\n✅ Complete monitoring system demonstration finished!")
        print("🌐 Access the live dashboard at: http://localhost:8000/monitoring/dashboard")
    
    async def demo_synthetic_probes(self):
        """Demonstrate synthetic probe execution"""
        print("\n🔍 SYNTHETIC PROBES DEMONSTRATION")
        print("-" * 40)
        
        # Note: These probes will fail when backend isn't running
        print("Running synthetic probes against LeanVibe backend...")
        print("(Note: Backend should be running at localhost:8000 for full demo)")
        
        start_time = time.time()
        
        try:
            # Run all probes
            results = await self.probe_runner.run_all_probes()
            
            execution_time = (time.time() - start_time) * 1000
            
            print(f"\n⚡ Probe execution completed in {execution_time:.1f}ms")
            print("\nProbe Results:")
            
            for probe_name, result in results.items():
                status_emoji = {
                    ProbeStatus.HEALTHY: "✅",
                    ProbeStatus.DEGRADED: "⚠️",
                    ProbeStatus.UNHEALTHY: "❌",
                    ProbeStatus.TIMEOUT: "⏱️",
                    ProbeStatus.ERROR: "🚨"
                }
                
                emoji = status_emoji.get(result.status, "❓")
                print(f"  {emoji} {probe_name.upper()}: {result.status.value} ({result.response_time_ms:.0f}ms)")
                print(f"      Message: {result.message}")
                
                if result.error:
                    print(f"      Error: {result.error}")
                    
                if result.details:
                    print(f"      Details: {json.dumps(result.details, indent=8)}")
                
                # Show SLA compliance
                if probe_name == "health":
                    target_sla = 1000  # 1s SLA for health probe
                    sla_met = result.response_time_ms <= target_sla
                    print(f"      SLA ({target_sla}ms): {'✅ MET' if sla_met else '❌ EXCEEDED'}")
                
                print()
            
            # Show probe summary
            summary = self.probe_runner.get_probe_summary()
            print("📈 Probe Summary:")
            for probe_name, probe_data in summary.get("probes", {}).items():
                success_rate = probe_data.get("success_rate_5m", 0) * 100
                avg_response = probe_data.get("avg_response_time_5m", 0)
                print(f"  {probe_name}: {success_rate:.1f}% success rate, avg {avg_response:.0f}ms")
            
        except Exception as e:
            print(f"❌ Probe execution failed: {e}")
            print("💡 This is expected if the backend is not running")
            
            # Show what probes would check
            print("\n📋 Synthetic Probes Configuration:")
            print("  🏥 HealthProbe: /health endpoint validation (<1s SLA)")
            print("  📊 MetricsProbe: /monitoring/health endpoint validation (<2s SLA)")
            print("  🔌 WebSocketProbe: WebSocket handshake validation (<5s SLA)")
            print("  🔗 APIProbe: Core API endpoints validation (<3s each)")
    
    async def demo_error_budgets(self):
        """Demonstrate error budget tracking and deployment decisions"""
        print("\n📉 ERROR BUDGET TRACKING DEMONSTRATION")
        print("-" * 40)
        
        print("Error budgets track reliability and guide deployment decisions...")
        
        # Simulate some error data
        print("\n🧪 Simulating error data for demonstration:")
        
        scenarios = [
            ("api_endpoints", 5, 100, "Normal operation"),
            ("api_endpoints", 20, 200, "Elevated errors"),
            ("websocket_connections", 15, 100, "WebSocket issues"),
            ("system_health", 0, 50, "System healthy"),
        ]
        
        for component, errors, total, description in scenarios:
            error_budget_tracker.record_errors(component, errors, total)
            error_rate = (errors / total) * 100
            print(f"  📊 {component}: {errors}/{total} errors ({error_rate:.1f}%) - {description}")
        
        # Get budget status
        budget_status = error_budget_tracker.get_status_summary()
        
        print(f"\n💰 Error Budget Status:")
        print(f"  Deployment Frozen: {'🔒 YES' if budget_status['deployment_frozen'] else '✅ NO'}")
        if budget_status['deployment_frozen']:
            print(f"  Freeze Reason: {budget_status['freeze_reason']}")
        
        print(f"  Overall Health: {budget_status['overall_health'].upper()}")
        
        print("\n📊 Individual Budget Status:")
        for budget_name, budget_data in budget_status['budgets'].items():
            consumption = budget_data['budget_consumption'] * 100
            error_rate = budget_data['error_rate'] * 100
            status = budget_data['status']
            
            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️", 
                "critical": "🚨",
                "exhausted": "💥"
            }
            
            emoji = status_emoji.get(status, "❓")
            print(f"    {emoji} {budget_name}:")
            print(f"        Status: {status.upper()}")
            print(f"        Error Rate: {error_rate:.2f}%")
            print(f"        Budget Used: {consumption:.1f}%")
            print(f"        Threshold: {budget_data['threshold']*100:.1f}%")
    
    async def demo_performance_budgets(self):
        """Demonstrate performance SLA tracking"""
        print("\n⚡ PERFORMANCE BUDGET DEMONSTRATION")
        print("-" * 40)
        
        print("Performance budgets track SLA compliance (target P95 < 500ms)...")
        
        # Simulate response time data
        print("\n🧪 Simulating response time data:")
        
        response_time_scenarios = [
            ("api_response_time", [200, 300, 450, 600, 250], "Mixed performance"),
            ("websocket_latency", [50, 75, 120, 80, 90], "Good WebSocket latency"),
            ("ai_processing_time", [2000, 3500, 4800, 6000, 2200], "AI processing times"),
        ]
        
        for component, times, description in response_time_scenarios:
            print(f"  📈 {component}: {description}")
            for response_time in times:
                performance_budgets.record_response_time(component, response_time)
                print(f"      {response_time}ms", end=" ")
            print()
        
        # Get performance budget status
        perf_status = performance_budgets.get_status_summary()
        
        print(f"\n🎯 Performance Budget Status:")
        print(f"  Overall Health: {perf_status['overall_health'].upper()}")
        
        print("\n📊 Individual Performance Budgets:")
        for budget_name, budget_data in perf_status['budgets'].items():
            status = budget_data['status']
            percentiles = budget_data['percentiles']
            target_p95 = budget_data['target_p95']
            
            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "critical": "🚨", 
                "exhausted": "💥"
            }
            
            emoji = status_emoji.get(status, "❓")
            print(f"    {emoji} {budget_name}:")
            print(f"        Status: {status.upper()}")
            print(f"        P50: {percentiles['p50']:.0f}ms")
            print(f"        P95: {percentiles['p95']:.0f}ms (target: {target_p95}ms)")
            print(f"        P99: {percentiles['p99']:.0f}ms")
            print(f"        Sample Count: {budget_data['sample_count']}")
    
    async def demo_alert_system(self):
        """Demonstrate alert system functionality"""
        print("\n🚨 ALERT SYSTEM DEMONSTRATION")
        print("-" * 40)
        
        print("Alert system provides actionable notifications...")
        
        # Get current system status for alerts
        try:
            system_status = await health_dashboard.get_system_status()
            
            # Check alert conditions
            await alert_manager.check_alert_conditions(health_dashboard)
            
            # Get alert summary
            alert_summary = alert_manager.get_alert_summary()
            
            print(f"\n📋 Alert Summary:")
            print(f"  Active Alerts: {alert_summary['active_alerts_count']}")
            print(f"  Critical Alerts: {alert_summary['critical_alerts']}")
            print(f"  Warning Alerts: {alert_summary['warning_alerts']}")
            print(f"  Total Alerts (24h): {alert_summary['total_alerts_24h']}")
            
            # Show recent alerts
            recent_alerts = alert_summary.get('recent_alerts', [])
            if recent_alerts:
                print(f"\n🕐 Recent Alerts:")
                for alert in recent_alerts[-5:]:  # Last 5 alerts
                    level_emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
                    emoji = level_emoji.get(alert['level'], "📢")
                    status = "✅ Resolved" if alert['resolved'] else "🔄 Active"
                    print(f"    {emoji} [{alert['level'].upper()}] {alert['title']} - {status}")
                    print(f"        Component: {alert['component']}")
                    print(f"        Time: {alert['timestamp']}")
            else:
                print(f"\n✅ No recent alerts - system healthy!")
            
            # Show active alerts with actions
            active_alerts = alert_manager.get_active_alerts()
            if active_alerts:
                print(f"\n🚨 Active Alerts Requiring Action:")
                for alert in active_alerts[:3]:  # Show first 3
                    print(f"    🔥 {alert.title}")
                    print(f"       Level: {alert.level.value.upper()}")
                    print(f"       Message: {alert.message}")
                    print(f"       Component: {alert.component}")
                    print(f"       Recommended Actions:")
                    for action in alert.actions[:3]:  # Show first 3 actions
                        print(f"         • {action}")
                    print()
        
        except Exception as e:
            print(f"⚠️ Alert system demo requires backend running: {e}")
            
            # Show example alert structure
            print(f"\n📋 Example Alert Structure:")
            example_alert = {
                "id": "demo_alert_001",
                "level": "warning",
                "title": "Performance Budget Exceeded",
                "message": "API response time P95 > 500ms for 5 minutes",
                "component": "api_performance",
                "timestamp": datetime.now().isoformat(),
                "actions": [
                    "Check database query performance",
                    "Review recent code deployments", 
                    "Monitor system resource usage",
                    "Consider scaling if needed"
                ]
            }
            print(json.dumps(example_alert, indent=2))
    
    async def demo_health_dashboard(self):
        """Demonstrate health dashboard data aggregation"""
        print("\n🖥️ HEALTH DASHBOARD DEMONSTRATION")
        print("-" * 40)
        
        print("Health dashboard aggregates all monitoring data...")
        
        try:
            # Refresh dashboard data
            await health_dashboard.refresh_data()
            
            # Get dashboard data
            dashboard_data = health_dashboard.get_dashboard_html_data()
            
            print(f"\n📊 System Health Overview:")
            print(f"  Overall Status: {dashboard_data['overall_status'].upper()}")
            
            # Probe summary
            probe_summary = dashboard_data.get('probe_summary', {})
            if probe_summary:
                healthy_count = probe_summary.get('healthy_count', 0)
                total_count = probe_summary.get('total_count', 0)
                health_percent = probe_summary.get('health_percentage', 0)
                print(f"  Probe Health: {healthy_count}/{total_count} ({health_percent:.1f}%)")
            
            # Error budgets
            error_budgets = dashboard_data.get('error_budgets', {})
            if error_budgets.get('deployment_frozen'):
                print(f"  🔒 DEPLOYMENT FREEZE: {error_budgets.get('freeze_reason', 'Budget exceeded')}")
            else:
                print(f"  ✅ Deployments: Safe to deploy")
            
            # Performance budgets
            perf_budgets = dashboard_data.get('performance_budgets', {})
            if perf_budgets:
                overall_perf = perf_budgets.get('overall_health', 'unknown')
                print(f"  Performance Health: {overall_perf.upper()}")
            
            # Recent deployments
            deployments = dashboard_data.get('recent_deployments', [])
            if deployments:
                latest = deployments[0]
                print(f"  Latest Deploy: {latest['version']} - {latest['status'].upper()}")
            
            # WebSocket status
            websocket_status = dashboard_data.get('websocket_status', {})
            if websocket_status:
                ws_status = websocket_status.get('status', 'unknown')
                print(f"  WebSocket: {ws_status.upper()}")
            
            print(f"\n🌐 Dashboard Access:")
            print(f"  HTML Dashboard: http://localhost:8000/monitoring/dashboard")
            print(f"  JSON API: http://localhost:8000/monitoring/dashboard/data")
            print(f"  Metrics: http://localhost:8000/monitoring/metrics")
            print(f"  Probe Results: http://localhost:8000/monitoring/probes")
        
        except Exception as e:
            print(f"⚠️ Dashboard demo requires backend running: {e}")
            
            # Show expected dashboard structure
            print(f"\n📋 Expected Dashboard Data Structure:")
            dashboard_example = {
                "overall_status": "healthy",
                "probe_summary": {"healthy_count": 4, "total_count": 4, "health_percentage": 100},
                "error_budgets": {"deployment_frozen": False, "overall_health": "healthy"},
                "performance_budgets": {"overall_health": "healthy"},
                "websocket_status": {"status": "healthy"},
                "recent_deployments": [{"version": "v0.2.1", "status": "success"}]
            }
            print(json.dumps(dashboard_example, indent=2))
    
    def show_monitoring_architecture(self):
        """Show the monitoring system architecture"""
        print("\n🏗️ MONITORING SYSTEM ARCHITECTURE")
        print("-" * 40)
        
        print("""
🔍 Synthetic Probes:
  └── HealthProbe: /health endpoint (<1s SLA)
  └── MetricsProbe: /metrics endpoint (<2s SLA) 
  └── WebSocketProbe: WS handshake (<5s SLA)
  └── APIProbe: Core endpoints (<3s each)

💰 Error Budget Tracker:
  └── API Endpoints: 5% error rate budget
  └── WebSocket: 10% error rate budget
  └── AI Processing: 15% error rate budget
  └── System Health: 2% error rate budget
  └── Deployment Freeze Logic

⚡ Performance Budgets:
  └── API Response Time: P95 < 500ms
  └── WebSocket Latency: P95 < 200ms
  └── AI Processing: P95 < 5000ms
  └── Database Queries: P95 < 100ms

🚨 Alert Manager:
  └── Health probe failures (3+ in 5min)
  └── Performance SLA exceeded (5min duration)
  └── Error budget critical (>80% consumed)
  └── WebSocket disconnection spikes

🖥️ Health Dashboard:
  └── Real-time status aggregation
  └── HTML dashboard with auto-refresh
  └── JSON API for integrations
  └── Deployment freeze warnings

📬 Notification Channels:
  └── Console output (always enabled)
  └── Email alerts (configurable)
  └── Slack webhooks (configurable)
  └── Custom webhooks (configurable)
        """)
    
    def show_api_endpoints(self):
        """Show available monitoring API endpoints"""
        print("\n🔗 MONITORING API ENDPOINTS")
        print("-" * 40)
        
        endpoints = [
            ("GET /monitoring/health", "Comprehensive system health with probes & budgets"),
            ("GET /monitoring/metrics", "Prometheus-style metrics for external monitoring"),
            ("GET /monitoring/dashboard", "HTML dashboard for real-time monitoring"),
            ("GET /monitoring/dashboard/data", "JSON data for dashboard AJAX updates"),
            ("GET /monitoring/probes", "Run synthetic probes on-demand"),
            ("GET /monitoring/error-budget", "Error budget status & deployment decisions"),
            ("GET /monitoring/performance-budget", "Performance SLA compliance status"),
            ("GET /monitoring/alerts", "Active alerts with recommended actions"),
            ("POST /monitoring/simulate-error", "Test error budget tracking (dev only)")
        ]
        
        for endpoint, description in endpoints:
            print(f"  {endpoint}")
            print(f"    └── {description}")
            print()


async def main():
    """Main demonstration function"""
    parser = argparse.ArgumentParser(description="LeanVibe Monitoring System Demo")
    parser.add_argument("--demo-all", action="store_true", help="Run complete demonstration")
    parser.add_argument("--demo-probes", action="store_true", help="Demo synthetic probes")
    parser.add_argument("--demo-error-budgets", action="store_true", help="Demo error budget tracking")
    parser.add_argument("--demo-performance", action="store_true", help="Demo performance budgets")
    parser.add_argument("--demo-alerts", action="store_true", help="Demo alert system")
    parser.add_argument("--demo-dashboard", action="store_true", help="Demo health dashboard")
    parser.add_argument("--show-architecture", action="store_true", help="Show monitoring architecture")
    parser.add_argument("--show-endpoints", action="store_true", help="Show API endpoints")
    
    args = parser.parse_args()
    
    demo = MonitoringDemo()
    
    if args.demo_all:
        await demo.demo_all()
    elif args.demo_probes:
        await demo.demo_synthetic_probes()
    elif args.demo_error_budgets:
        await demo.demo_error_budgets()
    elif args.demo_performance:
        await demo.demo_performance_budgets()
    elif args.demo_alerts:
        await demo.demo_alert_system()
    elif args.demo_dashboard:
        await demo.demo_health_dashboard()
    elif args.show_architecture:
        demo.show_monitoring_architecture()
    elif args.show_endpoints:
        demo.show_api_endpoints()
    else:
        # Default: show overview
        demo.show_monitoring_architecture()
        demo.show_api_endpoints()
        print(f"\n💡 Run with --demo-all to see the monitoring system in action!")
        print(f"   Or use specific --demo-* flags to test individual components.")


if __name__ == "__main__":
    asyncio.run(main())