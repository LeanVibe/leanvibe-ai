"""
LeanVibe Monitoring Alert System

Notification system for LeanVibe monitoring following XP principles:
- Simple, actionable alerts that guide decision-making
- Fast detection: Issues detected in <60s, alerts within 120s  
- Clear escalation paths with recommended actions
- Integration with multiple notification channels

Alert Conditions:
- Health probe failures (3+ in 5min window)
- Performance budget exceeded (p95 > 500ms for 5min)
- Error budget consumed (>5% error rate)
- WebSocket disconnection spikes

Example Usage:
    python monitoring/alerts.py --test-alerts
"""

import asyncio
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import argparse

# Alert notification handlers


class NotificationChannel(Enum):
    """Available notification channels"""
    CONSOLE = "console"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class NotificationConfig:
    """Configuration for notification channels"""
    console_enabled: bool = True
    email_enabled: bool = False
    slack_enabled: bool = False
    webhook_enabled: bool = False
    
    # Email configuration
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    
    # Slack configuration
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # Webhook configuration
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)


class AlertNotificationHandler:
    """Handles alert notifications across multiple channels"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Track notification history for rate limiting
        self.notification_history: List[Dict[str, Any]] = []
        self.rate_limit_window = timedelta(minutes=5)
        self.max_notifications_per_window = 10
    
    async def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send alert through all configured channels"""
        results = {}
        
        # Check rate limiting
        if self._is_rate_limited(alert_data):
            self.logger.warning(f"Rate limited alert: {alert_data.get('title', 'Unknown')}")
            return {"rate_limited": True}
        
        # Send through enabled channels
        if self.config.console_enabled:
            results["console"] = await self._send_console_alert(alert_data)
        
        if self.config.email_enabled and self.config.email_to:
            results["email"] = await self._send_email_alert(alert_data)
        
        if self.config.slack_enabled and self.config.slack_webhook_url:
            results["slack"] = await self._send_slack_alert(alert_data)
        
        if self.config.webhook_enabled and self.config.webhook_url:
            results["webhook"] = await self._send_webhook_alert(alert_data)
        
        # Record notification
        self._record_notification(alert_data, results)
        
        return results
    
    async def send_resolution(self, alert_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send alert resolution notification"""
        resolution_data = alert_data.copy()
        resolution_data["resolved"] = True
        resolution_data["title"] = f"RESOLVED: {alert_data.get('title', 'Alert')}"
        resolution_data["message"] = f"Alert resolved: {alert_data.get('message', '')}"
        
        return await self.send_alert(resolution_data)
    
    def _is_rate_limited(self, alert_data: Dict[str, Any]) -> bool:
        """Check if alert should be rate limited"""
        now = datetime.now()
        cutoff = now - self.rate_limit_window
        
        # Clean old notifications
        self.notification_history = [
            notif for notif in self.notification_history
            if notif["timestamp"] >= cutoff
        ]
        
        # Count recent notifications for this alert type
        alert_type = alert_data.get("component", "unknown")
        recent_count = sum(
            1 for notif in self.notification_history
            if notif.get("component") == alert_type
        )
        
        return recent_count >= self.max_notifications_per_window
    
    def _record_notification(self, alert_data: Dict[str, Any], results: Dict[str, bool]):
        """Record notification in history"""
        self.notification_history.append({
            "timestamp": datetime.now(),
            "component": alert_data.get("component", "unknown"),
            "level": alert_data.get("level", "info"),
            "title": alert_data.get("title", ""),
            "channels": list(results.keys()),
            "success_channels": [ch for ch, success in results.items() if success]
        })
    
    async def _send_console_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert to console with colored output"""
        try:
            level = alert_data.get("level", "info").upper()
            title = alert_data.get("title", "Alert")
            message = alert_data.get("message", "")
            component = alert_data.get("component", "system")
            timestamp = alert_data.get("timestamp", datetime.now().isoformat())
            actions = alert_data.get("actions", [])
            
            # Color codes
            colors = {
                "CRITICAL": "\033[91m",  # Red
                "WARNING": "\033[93m",   # Yellow
                "INFO": "\033[94m",      # Blue
                "RESOLVED": "\033[92m"   # Green
            }
            reset_color = "\033[0m"
            
            level_color = colors.get(level, "\033[0m")
            
            print(f"\n{level_color}{'='*60}{reset_color}")
            print(f"{level_color}🚨 LEANVIBE ALERT [{level}]{reset_color}")
            print(f"{level_color}{'='*60}{reset_color}")
            print(f"Title: {title}")
            print(f"Component: {component}")
            print(f"Message: {message}")
            print(f"Time: {timestamp}")
            
            if actions:
                print(f"\nRecommended Actions:")
                for i, action in enumerate(actions, 1):
                    print(f"  {i}. {action}")
            
            if alert_data.get("details"):
                print(f"\nDetails: {json.dumps(alert_data['details'], indent=2)}")
            
            print(f"{level_color}{'='*60}{reset_color}\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send console alert: {e}")
            return False
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert via email"""
        try:
            if not all([self.config.email_username, self.config.email_password, self.config.email_to]):
                self.logger.warning("Email configuration incomplete")
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.config.email_from or self.config.email_username
            msg["To"] = ", ".join(self.config.email_to)
            msg["Subject"] = f"[LeanVibe Alert] {alert_data.get('title', 'System Alert')}"
            
            # Create email body
            body = self._format_email_body(alert_data)
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port) as server:
                server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
            
            self.logger.info(f"Email alert sent: {alert_data.get('title')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def _send_slack_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert to Slack webhook"""
        try:
            import aiohttp
            
            # Format Slack message
            slack_message = self._format_slack_message(alert_data)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.slack_webhook_url,
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack alert sent: {alert_data.get('title')}")
                        return True
                    else:
                        self.logger.error(f"Slack webhook failed with status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    async def _send_webhook_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert to webhook endpoint"""
        try:
            import aiohttp
            
            headers = {"Content-Type": "application/json"}
            headers.update(self.config.webhook_headers)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_url,
                    json=alert_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201, 202]:
                        self.logger.info(f"Webhook alert sent: {alert_data.get('title')}")
                        return True
                    else:
                        self.logger.error(f"Webhook failed with status {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    def _format_email_body(self, alert_data: Dict[str, Any]) -> str:
        """Format alert data for email body"""
        body = f"""
LeanVibe System Alert

Alert Level: {alert_data.get('level', 'INFO').upper()}
Component: {alert_data.get('component', 'system')}
Timestamp: {alert_data.get('timestamp', datetime.now().isoformat())}

Title: {alert_data.get('title', 'System Alert')}
Message: {alert_data.get('message', 'No message provided')}

Recommended Actions:
"""
        
        actions = alert_data.get('actions', [])
        if actions:
            for i, action in enumerate(actions, 1):
                body += f"{i}. {action}\n"
        else:
            body += "No specific actions recommended\n"
        
        details = alert_data.get('details', {})
        if details:
            body += f"\nTechnical Details:\n{json.dumps(details, indent=2)}\n"
        
        body += f"""
---
LeanVibe Monitoring System
Dashboard: http://localhost:8000/monitoring/dashboard
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return body
    
    def _format_slack_message(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format alert data for Slack message"""
        level = alert_data.get('level', 'info').upper()
        title = alert_data.get('title', 'System Alert')
        message = alert_data.get('message', 'No message provided')
        component = alert_data.get('component', 'system')
        
        # Emoji mapping for alert levels
        emoji_map = {
            "CRITICAL": "🚨",
            "WARNING": "⚠️",
            "INFO": "ℹ️",
            "RESOLVED": "✅"
        }
        
        emoji = emoji_map.get(level, "📢")
        
        # Color mapping for Slack
        color_map = {
            "CRITICAL": "danger",
            "WARNING": "warning", 
            "INFO": "good",
            "RESOLVED": "good"
        }
        
        color = color_map.get(level, "warning")
        
        slack_message = {
            "channel": self.config.slack_channel,
            "username": "LeanVibe Monitor",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} {title}",
                    "text": message,
                    "fields": [
                        {
                            "title": "Component",
                            "value": component,
                            "short": True
                        },
                        {
                            "title": "Level", 
                            "value": level,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert_data.get('timestamp', datetime.now().isoformat()),
                            "short": False
                        }
                    ],
                    "footer": "LeanVibe Monitoring",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        # Add actions as fields
        actions = alert_data.get('actions', [])
        if actions:
            actions_text = "\n".join(f"• {action}" for action in actions)
            slack_message["attachments"][0]["fields"].append({
                "title": "Recommended Actions",
                "value": actions_text,
                "short": False
            })
        
        return slack_message


# Alert condition monitoring

class AlertConditionMonitor:
    """Monitors system conditions and triggers alerts"""
    
    def __init__(self, notification_handler: AlertNotificationHandler):
        self.notification_handler = notification_handler
        self.logger = logging.getLogger(__name__)
        
        # Track condition states to prevent alert spam
        self.condition_states: Dict[str, Dict[str, Any]] = {}
        
        # Alert thresholds
        self.thresholds = {
            "health_probe_failures": {
                "failure_count": 3,
                "time_window_minutes": 5,
                "description": "Multiple health probe failures detected"
            },
            "performance_budget_exceeded": {
                "p95_threshold_ms": 500,
                "duration_minutes": 5,
                "description": "Performance SLA exceeded"
            },
            "error_rate_high": {
                "error_rate_threshold": 0.05,  # 5%
                "time_window_minutes": 10,
                "description": "High error rate detected"
            },
            "websocket_disconnections": {
                "disconnection_rate": 10,  # per minute
                "time_window_minutes": 5,
                "description": "High WebSocket disconnection rate"
            }
        }
    
    async def check_conditions(self, system_data: Dict[str, Any]):
        """Check all alert conditions against current system data"""
        try:
            # Check health probe failures
            await self._check_health_probe_failures(system_data.get("probe_summary", {}))
            
            # Check performance budget violations  
            await self._check_performance_budget_exceeded(system_data.get("performance_budgets", {}))
            
            # Check error rate violations
            await self._check_error_rate_high(system_data.get("error_budgets", {}))
            
            # Check WebSocket issues
            await self._check_websocket_issues(system_data.get("websocket_status", {}))
            
        except Exception as e:
            self.logger.error(f"Failed to check alert conditions: {e}")
    
    async def _check_health_probe_failures(self, probe_data: Dict[str, Any]):
        """Check for health probe failure conditions"""
        condition_id = "health_probe_failures"
        threshold = self.thresholds[condition_id]
        
        # Count failed probes
        probes = probe_data.get("probes", {})
        failed_probes = [
            name for name, probe in probes.items()
            if probe.get("status") not in ["healthy"]
        ]
        
        if len(failed_probes) >= threshold["failure_count"]:
            # Check if we've already alerted recently
            if not self._should_alert(condition_id, threshold["time_window_minutes"]):
                return
            
            alert_data = {
                "id": f"health_probes_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "level": "critical",
                "title": "Health Probe Failures Detected",
                "message": f"{len(failed_probes)} of {len(probes)} health probes failing",
                "component": "health_probes",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "failed_probes": failed_probes,
                    "total_probes": len(probes),
                    "failure_rate": len(failed_probes) / len(probes) if probes else 0
                },
                "actions": [
                    "Check system health endpoints immediately",
                    "Investigate network connectivity issues",
                    "Review recent deployments for breaking changes",
                    "Validate all services are running correctly"
                ]
            }
            
            await self.notification_handler.send_alert(alert_data)
            self._record_alert_state(condition_id, "alerted")
    
    async def _check_performance_budget_exceeded(self, perf_data: Dict[str, Any]):
        """Check for performance budget violations"""
        condition_id = "performance_budget_exceeded"
        threshold = self.thresholds[condition_id]
        
        budgets = perf_data.get("budgets", {})
        exceeded_budgets = []
        
        for budget_name, budget in budgets.items():
            percentiles = budget.get("percentiles", {})
            p95 = percentiles.get("p95", 0)
            
            if p95 > threshold["p95_threshold_ms"]:
                exceeded_budgets.append({
                    "name": budget_name,
                    "p95_ms": p95,
                    "target_ms": budget.get("target_p95", threshold["p95_threshold_ms"])
                })
        
        if exceeded_budgets:
            if not self._should_alert(condition_id, threshold["duration_minutes"]):
                return
            
            alert_data = {
                "id": f"perf_budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "level": "warning" if len(exceeded_budgets) == 1 else "critical",
                "title": "Performance Budget Exceeded",
                "message": f"{len(exceeded_budgets)} performance budgets exceeded SLA",
                "component": "performance",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "exceeded_budgets": exceeded_budgets,
                    "threshold_ms": threshold["p95_threshold_ms"]
                },
                "actions": [
                    "Investigate slow endpoints and database queries",
                    "Check system resource utilization (CPU, memory)",
                    "Review recent code changes for performance regressions",
                    "Consider scaling if resource constrained"
                ]
            }
            
            await self.notification_handler.send_alert(alert_data)
            self._record_alert_state(condition_id, "alerted")
    
    async def _check_error_rate_high(self, error_data: Dict[str, Any]):
        """Check for high error rate conditions"""
        condition_id = "error_rate_high"
        threshold = self.thresholds[condition_id]
        
        budgets = error_data.get("budgets", {})
        high_error_budgets = []
        
        for budget_name, budget in budgets.items():
            error_rate = budget.get("error_rate", 0)
            
            if error_rate > threshold["error_rate_threshold"]:
                high_error_budgets.append({
                    "name": budget_name,
                    "error_rate": error_rate,
                    "error_rate_percent": error_rate * 100,
                    "budget_consumption": budget.get("budget_consumption", 0)
                })
        
        if high_error_budgets:
            if not self._should_alert(condition_id, threshold["time_window_minutes"]):
                return
            
            alert_data = {
                "id": f"error_rate_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "level": "critical",
                "title": "High Error Rate Detected",
                "message": f"{len(high_error_budgets)} components have high error rates",
                "component": "error_tracking",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "high_error_budgets": high_error_budgets,
                    "threshold_percent": threshold["error_rate_threshold"] * 100
                },
                "actions": [
                    "Investigate error patterns and root causes",
                    "Check for recent deployments or configuration changes",
                    "Review error logs for specific error types",
                    "Consider deployment rollback if errors started recently"
                ]
            }
            
            await self.notification_handler.send_alert(alert_data)
            self._record_alert_state(condition_id, "alerted")
    
    async def _check_websocket_issues(self, websocket_data: Dict[str, Any]):
        """Check for WebSocket connectivity issues"""
        condition_id = "websocket_disconnections"
        
        ws_status = websocket_data.get("status", "unknown")
        
        if ws_status in ["error", "timeout", "unhealthy"]:
            if not self._should_alert(condition_id, 2):  # 2 minute window for WebSocket issues
                return
            
            alert_data = {
                "id": f"websocket_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "level": "warning",
                "title": "WebSocket Connectivity Issues",
                "message": f"WebSocket probe status: {ws_status}",
                "component": "websocket",
                "timestamp": datetime.now().isoformat(),
                "details": websocket_data,
                "actions": [
                    "Check WebSocket server status and logs",
                    "Validate network connectivity and firewall rules",
                    "Test WebSocket endpoint manually",
                    "Check for WebSocket connection pool issues"
                ]
            }
            
            await self.notification_handler.send_alert(alert_data)
            self._record_alert_state(condition_id, "alerted")
    
    def _should_alert(self, condition_id: str, window_minutes: int) -> bool:
        """Check if we should send an alert for this condition"""
        if condition_id not in self.condition_states:
            return True
        
        last_alert = self.condition_states[condition_id].get("last_alert_time")
        if not last_alert:
            return True
        
        time_since_alert = datetime.now() - last_alert
        return time_since_alert >= timedelta(minutes=window_minutes)
    
    def _record_alert_state(self, condition_id: str, state: str):
        """Record the alert state for a condition"""
        self.condition_states[condition_id] = {
            "state": state,
            "last_alert_time": datetime.now()
        }


# Main monitoring loop

async def run_monitoring_loop(config: NotificationConfig, check_interval_seconds: int = 60):
    """Run continuous monitoring loop"""
    logger = logging.getLogger(__name__)
    
    # Initialize components
    notification_handler = AlertNotificationHandler(config)
    condition_monitor = AlertConditionMonitor(notification_handler)
    
    logger.info(f"Starting monitoring loop (check interval: {check_interval_seconds}s)")
    
    while True:
        try:
            # Import here to avoid circular imports
            from app.monitoring.observability import get_system_health_summary
            
            # Get current system status
            system_data = await get_system_health_summary()
            
            # Check alert conditions
            await condition_monitor.check_conditions(system_data)
            
            logger.debug("Monitoring check completed")
            
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
        
        # Wait for next check
        await asyncio.sleep(check_interval_seconds)


# CLI interface for testing

def test_alerts():
    """Test alert notifications"""
    print("Testing LeanVibe alert notifications...")
    
    # Create test configuration
    config = NotificationConfig(
        console_enabled=True,
        email_enabled=False,  # Set to True and configure for email testing
        slack_enabled=False,  # Set to True and configure for Slack testing
    )
    
    # Create notification handler
    handler = AlertNotificationHandler(config)
    
    # Test alerts
    test_alerts_data = [
        {
            "id": "test_critical_001",
            "level": "critical",
            "title": "Test Critical Alert",
            "message": "This is a test critical alert for LeanVibe monitoring",
            "component": "test_system",
            "timestamp": datetime.now().isoformat(),
            "details": {"test": True, "severity": "high"},
            "actions": [
                "This is a test alert - no action required",
                "Check console output for formatting",
                "Verify notification channels are working"
            ]
        },
        {
            "id": "test_warning_001",
            "level": "warning",
            "title": "Test Warning Alert",
            "message": "This is a test warning alert for performance monitoring",
            "component": "performance",
            "timestamp": datetime.now().isoformat(),
            "details": {"response_time_ms": 750, "target_ms": 500},
            "actions": [
                "Review performance metrics",
                "This is a test - no real action needed"
            ]
        },
        {
            "id": "test_resolution_001",
            "level": "info",
            "title": "Test Alert Resolution",
            "message": "Test alert has been resolved successfully",
            "component": "test_system", 
            "timestamp": datetime.now().isoformat(),
            "resolved": True,
            "actions": ["Monitor for recurrence"]
        }
    ]
    
    async def run_tests():
        print("Sending test alerts...")
        
        for i, alert_data in enumerate(test_alerts_data):
            print(f"\nSending test alert {i+1}/{len(test_alerts_data)}...")
            results = await handler.send_alert(alert_data)
            print(f"Results: {results}")
            
            # Wait between alerts
            if i < len(test_alerts_data) - 1:
                await asyncio.sleep(2)
        
        print("\nTest alerts completed!")
    
    # Run test
    asyncio.run(run_tests())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LeanVibe Alert System")
    parser.add_argument("--test-alerts", action="store_true", help="Test alert notifications")
    parser.add_argument("--monitor", action="store_true", help="Run monitoring loop")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring check interval in seconds")
    
    args = parser.parse_args()
    
    if args.test_alerts:
        test_alerts()
    elif args.monitor:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create configuration
        config = NotificationConfig()
        
        # Run monitoring loop
        asyncio.run(run_monitoring_loop(config, args.interval))
    else:
        print("LeanVibe Alert System")
        print("Use --test-alerts to test notifications")
        print("Use --monitor to run monitoring loop")
        print("Use --help for more options")