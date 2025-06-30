"""
Live Metrics Dashboard for LeenVibe CLI

Provides real-time metrics dashboard with sparkline charts, health indicators,
and system status monitoring.
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn

from ..client import BackendClient


class LiveMetricsDashboard:
    """Real-time metrics dashboard"""
    
    def __init__(self, client: BackendClient, console: Optional[Console] = None):
        self.client = client
        self.console = console or Console()
        self.metrics_history = defaultdict(lambda: deque(maxlen=50))
        self.last_update = time.time()
        
        # Alert thresholds
        self.alert_thresholds = {
            'response_time_ms': 1000,
            'error_rate_percent': 5.0,
            'memory_usage_mb': 500,
            'cpu_usage_percent': 80.0,
            'events_per_second': 100
        }
        
        # Metric definitions
        self.metric_configs = {
            'response_time_ms': {
                'name': 'Response Time',
                'unit': 'ms',
                'format': '{:.1f}',
                'color_good': 'green',
                'color_warning': 'yellow',
                'color_critical': 'red'
            },
            'events_per_second': {
                'name': 'Events/sec',
                'unit': '/s',
                'format': '{:.1f}',
                'color_good': 'green',
                'color_warning': 'yellow',
                'color_critical': 'red'
            },
            'memory_usage_mb': {
                'name': 'Memory',
                'unit': 'MB',
                'format': '{:.0f}',
                'color_good': 'green',
                'color_warning': 'yellow',
                'color_critical': 'red'
            },
            'connected_clients': {
                'name': 'Clients',
                'unit': '',
                'format': '{:.0f}',
                'color_good': 'cyan',
                'color_warning': 'cyan',
                'color_critical': 'cyan'
            },
            'active_sessions': {
                'name': 'Sessions',
                'unit': '',
                'format': '{:.0f}',
                'color_good': 'blue',
                'color_warning': 'blue',
                'color_critical': 'blue'
            }
        }
    
    async def update_metrics(self) -> Dict[str, Any]:
        """Update live metrics from backend"""
        try:
            # Get streaming stats
            streaming_stats = await self.client.get_streaming_stats()
            
            # Get session info
            sessions = await self.client.get_sessions()
            
            # Get health check (includes general stats)
            health = await self.client.health_check()
            
            # Calculate derived metrics
            metrics = self._calculate_derived_metrics(streaming_stats, sessions, health)
            
            # Update history
            timestamp = time.time()
            for metric, value in metrics.items():
                self.metrics_history[metric].append((timestamp, value))
            
            self.last_update = timestamp
            return metrics
            
        except Exception as e:
            # Return empty metrics on error
            return {}
    
    def _calculate_derived_metrics(self, streaming_stats: Dict[str, Any], 
                                 sessions: Dict[str, Any], 
                                 health: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived metrics from backend data"""
        metrics = {}
        
        # Extract from streaming stats
        if streaming_stats:
            metrics['connected_clients'] = streaming_stats.get('connected_clients', 0)
            metrics['total_events'] = streaming_stats.get('total_events_sent', 0)
            metrics['events_per_second'] = streaming_stats.get('events_per_second', 0.0)
            metrics['failed_deliveries'] = streaming_stats.get('failed_deliveries', 0)
        
        # Extract from sessions
        if sessions:
            session_list = sessions.get('sessions', [])
            metrics['active_sessions'] = len(session_list)
            
            # Calculate average response time from sessions
            total_response_time = 0
            session_count = 0
            for session in session_list:
                if 'avg_response_time_ms' in session:
                    total_response_time += session['avg_response_time_ms']
                    session_count += 1
            
            if session_count > 0:
                metrics['response_time_ms'] = total_response_time / session_count
            else:
                metrics['response_time_ms'] = 0
        
        # Extract from health
        if health:
            metrics['backend_status'] = health.get('status', 'unknown')
            metrics['ai_ready'] = health.get('ai_ready', False)
        
        # Calculate error rate
        total_events = metrics.get('total_events', 0)
        failed_events = metrics.get('failed_deliveries', 0)
        if total_events > 0:
            metrics['error_rate_percent'] = (failed_events / total_events) * 100
        else:
            metrics['error_rate_percent'] = 0.0
        
        # Mock memory usage (would be from system metrics in production)
        metrics['memory_usage_mb'] = 45.0  # Placeholder
        
        return metrics
    
    def create_system_status_panel(self) -> Panel:
        """Create system status panel"""
        if not self.metrics_history:
            status_text = Text("No data available", style="dim")
        else:
            # Get latest metrics
            latest_metrics = {}
            for metric, history in self.metrics_history.items():
                if history:
                    latest_metrics[metric] = history[-1][1]
            
            status_text = Text()
            
            # Backend status
            backend_status = latest_metrics.get('backend_status', 'unknown')
            ai_ready = latest_metrics.get('ai_ready', False)
            
            if backend_status == 'healthy':
                status_text.append("🟢 ", style="green")
                status_text.append("HEALTHY", style="bold green")
            else:
                status_text.append("🔴 ", style="red")
                status_text.append("UNHEALTHY", style="bold red")
            
            status_text.append(f"\nAI Agent: {'Ready' if ai_ready else 'Not Ready'}")
            
            # Key metrics
            response_time = latest_metrics.get('response_time_ms', 0)
            clients = latest_metrics.get('connected_clients', 0)
            sessions = latest_metrics.get('active_sessions', 0)
            
            status_text.append(f"\nResponse: {response_time:.1f}ms")
            status_text.append(f"\nClients: {clients}")
            status_text.append(f"\nSessions: {sessions}")
            
            # Last update
            seconds_ago = int(time.time() - self.last_update)
            status_text.append(f"\nUpdated: {seconds_ago}s ago", style="dim")
        
        return Panel(
            status_text,
            title="[bold]System Status[/bold]",
            border_style="green" if self.metrics_history else "yellow",
            width=25
        )
    
    def create_metrics_sparklines(self) -> Panel:
        """Create sparkline charts for key metrics"""
        if not self.metrics_history:
            return Panel(
                Text("No metrics data available", style="dim"),
                title="[bold]Metrics[/bold]",
                border_style="yellow"
            )
        
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("Metric", style="cyan", width=15)
        table.add_column("Current", style="bold", width=12)
        table.add_column("Trend", style="dim", width=20)
        table.add_column("Status", style="bold", width=8)
        
        for metric_key in ['response_time_ms', 'events_per_second', 'memory_usage_mb', 'connected_clients']:
            history = self.metrics_history.get(metric_key)
            if not history:
                continue
            
            config = self.metric_configs.get(metric_key, {})
            name = config.get('name', metric_key)
            unit = config.get('unit', '')
            format_str = config.get('format', '{:.1f}')
            
            current_value = history[-1][1]
            trend = self._generate_sparkline(history)
            alert_status = self._check_alert_threshold(metric_key, current_value)
            
            # Format current value
            formatted_value = format_str.format(current_value) + unit
            
            # Status indicator
            if alert_status == 'critical':
                status = "[red]🚨[/red]"
            elif alert_status == 'warning':
                status = "[yellow]⚠️[/yellow]"
            else:
                status = "[green]✅[/green]"
            
            table.add_row(name, formatted_value, trend, status)
        
        return Panel(
            table,
            title="[bold]Live Metrics[/bold]",
            border_style="blue"
        )
    
    def _generate_sparkline(self, history: deque) -> str:
        """Generate ASCII sparkline for metric history"""
        if len(history) < 2:
            return "─"
        
        values = [item[1] for item in history]
        min_val, max_val = min(values), max(values)
        
        if max_val == min_val:
            return "─" * min(len(values), 20)
        
        # Normalize to 0-7 range for Unicode block characters
        chars = "▁▂▃▄▅▆▇█"
        normalized = [
            int((val - min_val) / (max_val - min_val) * 7)
            for val in values
        ]
        
        return "".join(chars[n] for n in normalized[-20:])  # Last 20 points
    
    def _check_alert_threshold(self, metric: str, value: float) -> str:
        """Check if metric value exceeds alert thresholds"""
        threshold = self.alert_thresholds.get(metric)
        if threshold is None:
            return 'normal'
        
        if value > threshold * 1.5:  # 150% of threshold
            return 'critical'
        elif value > threshold:  # Above threshold
            return 'warning'
        else:
            return 'normal'
    
    def create_event_summary_panel(self) -> Panel:
        """Create event summary panel"""
        if not self.metrics_history:
            return Panel(
                Text("No event data available", style="dim"),
                title="[bold]Events[/bold]",
                border_style="yellow"
            )
        
        # Get latest event metrics
        total_events = 0
        events_per_second = 0.0
        failed_deliveries = 0
        
        if 'total_events' in self.metrics_history and self.metrics_history['total_events']:
            total_events = self.metrics_history['total_events'][-1][1]
        
        if 'events_per_second' in self.metrics_history and self.metrics_history['events_per_second']:
            events_per_second = self.metrics_history['events_per_second'][-1][1]
        
        if 'failed_deliveries' in self.metrics_history and self.metrics_history['failed_deliveries']:
            failed_deliveries = self.metrics_history['failed_deliveries'][-1][1]
        
        # Calculate success rate
        if total_events > 0:
            success_rate = ((total_events - failed_deliveries) / total_events) * 100
        else:
            success_rate = 100.0
        
        event_text = Text()
        event_text.append(f"Total Events: {int(total_events)}\n")
        event_text.append(f"Events/sec: {events_per_second:.1f}\n")
        event_text.append(f"Failed: {int(failed_deliveries)}\n")
        
        # Success rate with color coding
        if success_rate >= 95:
            event_text.append(f"Success: ", style="white")
            event_text.append(f"{success_rate:.1f}%", style="green")
        elif success_rate >= 90:
            event_text.append(f"Success: ", style="white")
            event_text.append(f"{success_rate:.1f}%", style="yellow")
        else:
            event_text.append(f"Success: ", style="white")
            event_text.append(f"{success_rate:.1f}%", style="red")
        
        return Panel(
            event_text,
            title="[bold]Event Stream[/bold]",
            border_style="magenta",
            width=25
        )
    
    def create_dashboard_layout(self, additional_panels: List[Panel] = None) -> Columns:
        """Create complete dashboard layout"""
        # Core panels
        panels = [
            self.create_system_status_panel(),
            self.create_metrics_sparklines(),
            self.create_event_summary_panel()
        ]
        
        # Add any additional panels
        if additional_panels:
            panels.extend(additional_panels)
        
        return Columns(panels, expand=True)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        if not self.metrics_history:
            return {}
        
        summary = {}
        for metric, history in self.metrics_history.items():
            if history:
                current = history[-1][1]
                summary[metric] = {
                    'current': current,
                    'alert_status': self._check_alert_threshold(metric, current),
                    'data_points': len(history)
                }
        
        return summary