"""
Status command for LeenVibe CLI

Shows backend health, connection status, and project information.
"""

import asyncio
from typing import Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed information')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def status(ctx: click.Context, detailed: bool, output_json: bool):
    """Show backend status and connection information"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    asyncio.run(status_command(config, client, detailed, output_json))


async def status_command(config: CLIConfig, client: BackendClient, detailed: bool = False, output_json: bool = False):
    """Execute status command"""
    try:
        async with client:
            # Get backend health
            health_data = await client.health_check()
            
            if output_json:
                import json
                console.print(json.dumps(health_data, indent=2))
                return
            
            # Display status information
            display_status_info(health_data, config, detailed)
            
            if detailed:
                await display_detailed_info(client)
                
    except Exception as e:
        if output_json:
            import json
            console.print(json.dumps({"error": str(e), "connected": False}))
        else:
            console.print(f"[red]Error: {e}[/red]")
            console.print(f"[yellow]Backend URL: {config.backend_url}[/yellow]")
            console.print("[dim]Check that the LeenVibe backend is running[/dim]")


def display_status_info(health_data: Dict[str, Any], config: CLIConfig, detailed: bool = False):
    """Display formatted status information"""
    
    # Main status panel
    status_text = Text()
    
    # Connection status
    if health_data.get("status") == "healthy":
        status_text.append("🟢 ", style="green")
        status_text.append("Connected", style="bold green")
    else:
        status_text.append("🔴 ", style="red")
        status_text.append("Disconnected", style="bold red")
    
    status_text.append(f"\nBackend: {config.backend_url}")
    status_text.append(f"\nService: {health_data.get('service', 'unknown')}")
    status_text.append(f"\nVersion: {health_data.get('version', 'unknown')}")
    
    # AI readiness
    ai_ready = health_data.get('ai_ready', False)
    ai_status = "Ready" if ai_ready else "Not Ready"
    ai_color = "green" if ai_ready else "yellow"
    status_text.append(f"\nAI Status: ", style="dim")
    status_text.append(ai_status, style=ai_color)
    
    # Agent framework
    framework = health_data.get('agent_framework', 'unknown')
    status_text.append(f"\nFramework: {framework}", style="dim")
    
    panel = Panel(
        status_text,
        title="[bold]LeenVibe Backend Status[/bold]",
        border_style="green" if health_data.get("status") == "healthy" else "red",
        padding=(1, 2)
    )
    
    console.print(panel)
    
    # Sessions info
    sessions = health_data.get('sessions', {})
    if sessions:
        display_sessions_info(sessions)
    
    # Event streaming info
    streaming = health_data.get('event_streaming', {})
    if streaming:
        display_streaming_info(streaming)


def display_sessions_info(sessions: Dict[str, Any]):
    """Display session information"""
    table = Table(title="Agent Sessions", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")
    
    table.add_row("Active Sessions", str(sessions.get('active_sessions', 0)))
    table.add_row("Total Requests", str(sessions.get('total_requests', 0)))
    table.add_row("Average Response Time", f"{sessions.get('avg_response_time_ms', 0):.1f}ms")
    
    console.print(table)


def display_streaming_info(streaming: Dict[str, Any]):
    """Display event streaming information"""
    table = Table(title="Event Streaming", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")
    
    table.add_row("Connected Clients", str(streaming.get('connected_clients', 0)))
    table.add_row("Total Events", str(streaming.get('total_events_sent', 0)))
    table.add_row("Events/Second", f"{streaming.get('events_per_second', 0):.1f}")
    table.add_row("Failed Deliveries", str(streaming.get('failed_deliveries', 0)))
    
    console.print(table)


async def display_detailed_info(client: BackendClient):
    """Display detailed backend information"""
    console.print("\n[bold]Detailed Information[/bold]")
    
    try:
        # Get sessions
        sessions_data = await client.get_sessions()
        if sessions_data.get('sessions'):
            display_detailed_sessions(sessions_data)
        
        # Get streaming stats
        streaming_stats = await client.get_streaming_stats()
        display_detailed_streaming(streaming_stats)
        
    except Exception as e:
        console.print(f"[yellow]Could not fetch detailed info: {e}[/yellow]")


def display_detailed_sessions(sessions_data: Dict[str, Any]):
    """Display detailed session information"""
    sessions = sessions_data.get('sessions', [])
    if not sessions:
        console.print("[dim]No active sessions[/dim]")
        return
    
    table = Table(title="Active Sessions", show_header=True, header_style="bold cyan")
    table.add_column("Session ID", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Requests", style="dim")
    table.add_column("Last Activity", style="dim")
    
    for session in sessions:
        session_id = session.get('session_id', 'unknown')[:12] + "..."
        status = session.get('status', 'unknown')
        requests = str(session.get('total_requests', 0))
        last_activity = session.get('last_activity', 'unknown')
        
        # Color code status
        status_style = "green" if status == "active" else "yellow"
        
        table.add_row(session_id, f"[{status_style}]{status}[/{status_style}]", requests, last_activity)
    
    console.print(table)


def display_detailed_streaming(streaming_stats: Dict[str, Any]):
    """Display detailed streaming statistics"""
    table = Table(title="Event Streaming Details", show_header=True, header_style="bold magenta")
    table.add_column("Event Type", style="cyan")
    table.add_column("Count", style="bold")
    table.add_column("Priority", style="yellow")
    table.add_column("Avg Latency", style="dim")
    
    events_by_type = streaming_stats.get('events_by_type', {})
    events_by_priority = streaming_stats.get('events_by_priority', {})
    
    # Display event types
    for event_type, count in events_by_type.items():
        priority = "medium"  # Default priority
        latency = "< 50ms"   # Default latency
        
        table.add_row(event_type, str(count), priority, latency)
    
    console.print(table)