"""
Monitor command for LeanVibe CLI

Provides real-time file monitoring and event notifications using the
sophisticated backend event streaming system.
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns

from ..config import CLIConfig
from ..client import BackendClient
from ..services import NotificationService
from ..ui import NotificationOverlay, LiveMetricsDashboard

console = Console()


@click.command()
@click.option('--duration', '-t', type=int, help='Monitoring duration in seconds')
@click.option('--filter-level', '-f', 
              type=click.Choice(['debug', 'low', 'medium', 'high', 'critical']),
              default='medium', help='Minimum event priority level')
@click.option('--quiet', '-q', is_flag=True, help='Suppress startup messages')
@click.option('--json', 'output_json', is_flag=True, help='Output events as JSON')
@click.option('--background', '-b', is_flag=True, help='Enable background notification service')
@click.option('--desktop-notifications', '-d', is_flag=True, help='Enable desktop notifications')
@click.option('--live-dashboard', '-l', is_flag=True, help='Show live metrics dashboard')
@click.option('--overlay', '-o', is_flag=True, help='Show notification overlays')
@click.pass_context
def monitor(ctx: click.Context, duration: Optional[int], filter_level: str, quiet: bool, output_json: bool, background: bool, desktop_notifications: bool, live_dashboard: bool, overlay: bool):
    """Monitor real-time file changes and events with enhanced notifications"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    # Override config notification level with command option
    config.notification_level = filter_level
    
    # Override notification settings with command options
    if desktop_notifications:
        config.desktop_notifications = True
    
    asyncio.run(enhanced_monitor_command(config, client, duration, quiet, output_json, background, live_dashboard, overlay))


async def enhanced_monitor_command(config: CLIConfig, client: BackendClient, duration: Optional[int], quiet: bool, output_json: bool, background: bool, live_dashboard: bool, overlay: bool):
    """Enhanced monitoring with notification services and live dashboard"""
    
    # If JSON output mode is requested, delegate to original implementation
    if output_json:
        return await monitor_command(config, client, duration, quiet, output_json)
    
    # If enhanced features are disabled, delegate to original implementation
    if not (background or live_dashboard or overlay):
        return await monitor_command(config, client, duration, quiet, output_json)
    
    if not quiet:
        show_enhanced_monitor_header(config, duration, background, live_dashboard, overlay)
    
    # Setup signal handling for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        if not quiet:
            console.print("\n[yellow]Shutting down enhanced monitor...[/yellow]")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize services
    notification_service = None
    notification_overlay = None
    live_metrics = None
    
    try:
        async with client:
            # Connect to WebSocket for real-time events
            if not await client.connect_websocket():
                console.print("[red]Failed to connect to backend for monitoring[/red]")
                return
            
            # Initialize background notification service
            if background:
                notification_service = NotificationService(config)
                if await notification_service.start_background_monitoring():
                    if not quiet:
                        console.print("[green]✅ Background notification service started[/green]")
                else:
                    console.print("[yellow]⚠️ Background notification service failed to start[/yellow]")
                    notification_service = None
            
            # Initialize notification overlay
            if overlay:
                notification_overlay = NotificationOverlay(console)
                if not quiet:
                    console.print("[green]✅ Notification overlay enabled[/green]")
            
            # Initialize live metrics dashboard
            if live_dashboard:
                live_metrics = LiveMetricsDashboard(client, console)
                if not quiet:
                    console.print("[green]✅ Live metrics dashboard enabled[/green]")
            
            if not quiet:
                console.print("[green]🔄 Enhanced monitoring active - Press Ctrl+C to stop[/green]\n")
            
            # Start enhanced monitoring
            await enhanced_monitoring_loop(
                client, config, shutdown_event, duration,
                notification_service, notification_overlay, live_metrics
            )
    
    except Exception as e:
        console.print(f"[red]Enhanced monitoring error: {e}[/red]")
    
    finally:
        # Cleanup services
        if notification_service:
            await notification_service.stop()
            if not quiet:
                console.print("[dim]Background notification service stopped[/dim]")


async def monitor_command(config: CLIConfig, client: BackendClient, duration: Optional[int], quiet: bool, output_json: bool):
    """Execute real-time monitoring"""
    
    if not quiet and not output_json:
        show_monitor_header(config, duration)
    
    # Setup signal handling for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        if not quiet and not output_json:
            console.print("\n[yellow]Shutting down monitor...[/yellow]")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        async with client:
            # Connect to WebSocket for real-time events
            if not await client.connect_websocket():
                console.print("[red]Failed to connect to backend for monitoring[/red]")
                return
            
            if not quiet and not output_json:
                console.print("[green]🔄 Monitoring active - Press Ctrl+C to stop[/green]\n")
            
            # Start monitoring
            if output_json:
                await monitor_json_mode(client, shutdown_event, duration)
            else:
                await monitor_interactive_mode(client, config, shutdown_event, duration)
    
    except Exception as e:
        console.print(f"[red]Monitoring error: {e}[/red]")


def show_monitor_header(config: CLIConfig, duration: Optional[int]):
    """Show monitoring header information"""
    header_text = Text()
    header_text.append("📡 Real-time Monitoring\n", style="bold cyan")
    header_text.append(f"Backend: {config.backend_url}\n", style="dim")
    header_text.append(f"Filter Level: {config.notification_level.upper()}\n", style="yellow")
    
    if duration:
        header_text.append(f"Duration: {duration} seconds\n", style="dim")
    else:
        header_text.append("Duration: Continuous\n", style="dim")
    
    panel = Panel(
        header_text,
        title="[bold]LeanVibe Monitor[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)


def show_enhanced_monitor_header(config: CLIConfig, duration: Optional[int], background: bool, live_dashboard: bool, overlay: bool):
    """Show enhanced monitoring header with feature status"""
    header_text = Text()
    header_text.append("🚀 Enhanced Real-time Monitoring\n", style="bold cyan")
    header_text.append(f"Backend: {config.backend_url}\n", style="dim")
    header_text.append(f"Filter Level: {config.notification_level.upper()}\n", style="yellow")
    
    if duration:
        header_text.append(f"Duration: {duration} seconds\n", style="dim")
    else:
        header_text.append("Duration: Continuous\n", style="dim")
    
    # Feature status
    header_text.append("\nFeatures:\n", style="bold")
    header_text.append(f"• Background Service: {'✅ Enabled' if background else '❌ Disabled'}\n", 
                      style="green" if background else "dim")
    header_text.append(f"• Live Dashboard: {'✅ Enabled' if live_dashboard else '❌ Disabled'}\n", 
                      style="green" if live_dashboard else "dim")
    header_text.append(f"• Notification Overlay: {'✅ Enabled' if overlay else '❌ Disabled'}\n", 
                      style="green" if overlay else "dim")
    header_text.append(f"• Desktop Notifications: {'✅ Enabled' if config.desktop_notifications else '❌ Disabled'}\n", 
                      style="green" if config.desktop_notifications else "dim")
    
    panel = Panel(
        header_text,
        title="[bold]LeanVibe Enhanced Monitor[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)


async def enhanced_monitoring_loop(client: BackendClient, config: CLIConfig, shutdown_event: asyncio.Event, duration: Optional[int], notification_service: Optional[NotificationService], notification_overlay: Optional[NotificationOverlay], live_metrics: Optional[LiveMetricsDashboard]):
    """Main enhanced monitoring loop with live updates"""
    
    start_time = datetime.now()
    events_received = 0
    last_metrics_update = 0
    metrics_update_interval = 5  # Update metrics every 5 seconds
    
    # Event handlers for notification overlay
    async def handle_overlay_event(event: Dict[str, Any]):
        if notification_overlay:
            await notification_overlay.show_notification(event, duration=3)
    
    # Add overlay event handler to notification service
    if notification_service and notification_overlay:
        notification_service.add_event_handler(lambda event: asyncio.create_task(handle_overlay_event(event)))
    
    # Create live display based on enabled features
    if live_metrics:
        # Live dashboard mode with metrics
        with Live(
            live_metrics.create_dashboard_layout(),
            refresh_per_second=1,
            console=console
        ) as live_display:
            
            async for event in client.listen_for_events():
                if shutdown_event.is_set():
                    break
                
                # Check duration
                if duration and (datetime.now() - start_time).total_seconds() > duration:
                    break
                
                events_received += 1
                
                # Update metrics periodically
                current_time = datetime.now().timestamp()
                if current_time - last_metrics_update >= metrics_update_interval:
                    await live_metrics.update_metrics()
                    
                    # Update live display with new dashboard
                    dashboard = live_metrics.create_dashboard_layout()
                    
                    # Add overlay notifications if enabled
                    if notification_overlay and notification_overlay.active_notifications:
                        overlay_panels = []
                        for notification in notification_overlay.active_notifications[-3:]:  # Show last 3
                            overlay_panels.append(Panel(
                                Text(notification),
                                title="[bold yellow]Notification[/bold yellow]",
                                border_style="yellow",
                                width=40
                            ))
                        if overlay_panels:
                            dashboard = Columns([dashboard, Columns(overlay_panels, expand=False)], expand=True)
                    
                    live_display.update(dashboard)
                    last_metrics_update = current_time
    
    else:
        # Traditional mode with enhanced notifications
        recent_events = []
        max_recent_events = 10
        
        with Live(
            generate_enhanced_monitor_display(events_received, start_time, recent_events, config, notification_overlay),
            refresh_per_second=2,
            console=console
        ) as live_display:
            
            async for event in client.listen_for_events():
                if shutdown_event.is_set():
                    break
                
                # Check duration
                if duration and (datetime.now() - start_time).total_seconds() > duration:
                    break
                
                # Process event
                events_received += 1
                recent_events.insert(0, event)
                if len(recent_events) > max_recent_events:
                    recent_events.pop()
                
                # Filter events by priority
                if should_show_event(event, config.notification_level):
                    # Update live display
                    display = generate_enhanced_monitor_display(events_received, start_time, recent_events, config, notification_overlay)
                    live_display.update(display)
    
    # Show final summary
    duration_actual = (datetime.now() - start_time).total_seconds()
    console.print(f"\n[green]Enhanced monitoring completed[/green]")
    console.print(f"[dim]Duration: {duration_actual:.1f}s | Events: {events_received}[/dim]")
    
    # Show notification service stats if available
    if notification_service:
        stats = notification_service.get_stats()
        console.print(f"[dim]Notifications sent: {stats.get('notifications_sent', 0)} | History: {stats.get('history_size', 0)}[/dim]")


def generate_enhanced_monitor_display(events_count: int, start_time: datetime, recent_events: list, config: CLIConfig, notification_overlay: Optional[NotificationOverlay]):
    """Generate enhanced monitoring display with notification overlay"""
    
    # Base display (same as original)
    base_display = generate_monitor_display(events_count, start_time, recent_events, config)
    
    # Add notification overlay panel if available
    if notification_overlay and notification_overlay.active_notifications:
        overlay_text = Text()
        overlay_text.append("Recent Notifications:\n", style="bold yellow")
        
        for notification in notification_overlay.active_notifications[-5:]:  # Show last 5
            overlay_text.append(f"• {notification}\n", style="dim")
        
        overlay_panel = Panel(
            overlay_text,
            title="[bold]Notifications[/bold]",
            border_style="yellow",
            width=30
        )
        
        # Combine with base display
        return Columns([base_display, overlay_panel], expand=True)
    
    return base_display


async def monitor_json_mode(client: BackendClient, shutdown_event: asyncio.Event, duration: Optional[int]):
    """Monitor in JSON output mode"""
    start_time = datetime.now()
    
    async for event in client.listen_for_events():
        if shutdown_event.is_set():
            break
        
        # Check duration
        if duration and (datetime.now() - start_time).total_seconds() > duration:
            break
        
        # Output event as JSON
        import json
        console.print(json.dumps(event, default=str))


async def monitor_interactive_mode(client: BackendClient, config: CLIConfig, shutdown_event: asyncio.Event, duration: Optional[int]):
    """Monitor in interactive mode with live updates"""
    
    # Event tracking
    events_received = 0
    start_time = datetime.now()
    recent_events = []
    max_recent_events = 10
    
    # Create live display
    with Live(
        generate_monitor_display(events_received, start_time, recent_events, config),
        refresh_per_second=2,
        console=console
    ) as live:
        
        async for event in client.listen_for_events():
            if shutdown_event.is_set():
                break
            
            # Check duration
            if duration and (datetime.now() - start_time).total_seconds() > duration:
                break
            
            # Process event
            events_received += 1
            recent_events.insert(0, event)
            if len(recent_events) > max_recent_events:
                recent_events.pop()
            
            # Filter events by priority
            if should_show_event(event, config.notification_level):
                # Update live display
                live.update(generate_monitor_display(events_received, start_time, recent_events, config))
    
    # Show final summary
    duration_actual = (datetime.now() - start_time).total_seconds()
    console.print(f"\n[green]Monitoring completed[/green]")
    console.print(f"[dim]Duration: {duration_actual:.1f}s | Events: {events_received}[/dim]")


def generate_monitor_display(events_count: int, start_time: datetime, recent_events: list, config: CLIConfig):
    """Generate the live monitoring display"""
    
    # Status panel
    duration = (datetime.now() - start_time).total_seconds()
    rate = events_count / duration if duration > 0 else 0
    
    status_text = Text()
    status_text.append("🟢 ", style="green")
    status_text.append("MONITORING", style="bold green")
    status_text.append(f"\nEvents: {events_count}")
    status_text.append(f"\nDuration: {duration:.1f}s")
    status_text.append(f"\nRate: {rate:.1f}/s")
    status_text.append(f"\nFilter: {config.notification_level.upper()}")
    
    status_panel = Panel(
        status_text,
        title="[bold]Status[/bold]",
        border_style="green",
        width=25
    )
    
    # Recent events panel
    events_table = Table(show_header=True, header_style="bold cyan", box=None)
    events_table.add_column("Time", style="dim", width=12)
    events_table.add_column("Type", style="cyan", width=20)
    events_table.add_column("Priority", style="bold", width=10)
    events_table.add_column("Details", style="white")
    
    for event in recent_events[:8]:  # Show last 8 events
        event_time = event.get('timestamp', datetime.now().isoformat())
        if isinstance(event_time, str):
            try:
                event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            except:
                event_time = datetime.now()
        
        time_str = event_time.strftime("%H:%M:%S") if isinstance(event_time, datetime) else str(event_time)[:8]
        event_type = event.get('type', 'unknown')
        
        # Extract priority and details
        priority, details = extract_event_info(event)
        
        # Color code priority
        priority_color = get_priority_color(priority)
        
        events_table.add_row(
            time_str,
            event_type.replace('_', ' ').title(),
            f"[{priority_color}]{priority.upper()}[/{priority_color}]",
            details
        )
    
    events_panel = Panel(
        events_table,
        title="[bold]Recent Events[/bold]",
        border_style="blue"
    )
    
    # Combine panels
    return Columns([status_panel, events_panel], expand=True)


def extract_event_info(event: Dict[str, Any]) -> tuple[str, str]:
    """Extract priority and details from event"""
    
    # Handle different event structures
    if 'data' in event:
        data = event['data']
        priority = data.get('priority', 'medium')
        
        # Extract meaningful details
        if 'file' in data:
            details = f"File: {data['file']}"
        elif 'change' in data:
            details = f"Change: {data['change']}"
        elif 'message' in data:
            details = data['message']
        else:
            details = str(data)[:50] + "..." if len(str(data)) > 50 else str(data)
    else:
        priority = event.get('priority', 'medium')
        event_type = event.get('type', 'unknown')
        
        if event_type == 'heartbeat_ack':
            details = "Connection heartbeat"
        elif event_type == 'reconnection_sync':
            details = "Session synchronized"
        else:
            details = event.get('content', 'No details')[:50]
    
    return priority, details


def get_priority_color(priority: str) -> str:
    """Get color for priority level"""
    colors = {
        'critical': 'red',
        'high': 'yellow',
        'medium': 'blue',
        'low': 'green',
        'debug': 'dim'
    }
    return colors.get(priority.lower(), 'white')


def should_show_event(event: Dict[str, Any], min_level: str) -> bool:
    """Check if event should be shown based on priority filter"""
    
    # Priority levels in order
    levels = ['debug', 'low', 'medium', 'high', 'critical']
    
    try:
        min_index = levels.index(min_level.lower())
    except ValueError:
        min_index = 2  # Default to medium
    
    # Extract event priority
    priority = 'medium'  # Default
    if 'data' in event:
        priority = event['data'].get('priority', 'medium')
    else:
        priority = event.get('priority', 'medium')
    
    try:
        event_index = levels.index(priority.lower())
        return event_index >= min_index
    except ValueError:
        return True  # Show unknown priority events