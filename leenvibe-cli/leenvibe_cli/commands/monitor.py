"""
Monitor command for LeenVibe CLI

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

console = Console()


@click.command()
@click.option('--duration', '-t', type=int, help='Monitoring duration in seconds')
@click.option('--filter-level', '-f', 
              type=click.Choice(['debug', 'low', 'medium', 'high', 'critical']),
              default='medium', help='Minimum event priority level')
@click.option('--quiet', '-q', is_flag=True, help='Suppress startup messages')
@click.option('--json', 'output_json', is_flag=True, help='Output events as JSON')
@click.pass_context
def monitor(ctx: click.Context, duration: Optional[int], filter_level: str, quiet: bool, output_json: bool):
    """Monitor real-time file changes and events"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    # Override config notification level with command option
    config.notification_level = filter_level
    
    asyncio.run(monitor_command(config, client, duration, quiet, output_json))


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
        title="[bold]LeenVibe Monitor[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)


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