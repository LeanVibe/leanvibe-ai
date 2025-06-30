"""
Status command for LeanVibe CLI

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
            console.print("[dim]Check that the LeanVibe backend is running[/dim]")


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
        title="[bold]LeanVibe Backend Status[/bold]",
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
    
    # LLM metrics info
    llm_metrics = health_data.get('llm_metrics', {})
    if llm_metrics:
        display_llm_metrics(llm_metrics)


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


def display_llm_metrics(llm_metrics: Dict[str, Any]):
    """Display comprehensive LLM metrics information"""
    model_info = llm_metrics.get('model_info', {})
    performance = llm_metrics.get('performance', {})
    memory = llm_metrics.get('memory', {})
    session_metrics = llm_metrics.get('session_metrics', {})
    
    # Model Information Panel
    model_text = Text()
    
    # Model basic info
    model_name = model_info.get('name', 'Unknown')
    deployment_mode = model_info.get('deployment_mode', 'unknown')
    status = model_info.get('status', 'unknown')
    
    # Status with color coding
    if status == 'ready':
        model_text.append("🟢 ", style="green")
        model_text.append(f"Model: {model_name}", style="bold")
    elif status == 'initializing':
        model_text.append("🟡 ", style="yellow")
        model_text.append(f"Model: {model_name}", style="bold yellow")
    else:
        model_text.append("🔴 ", style="red")
        model_text.append(f"Model: {model_name}", style="bold red")
    
    model_text.append(f"\nMode: {deployment_mode.title()}", style="dim")
    model_text.append(f"\nStatus: {status.title()}", style="dim")
    
    # Model capabilities
    if model_info.get('parameter_count'):
        model_text.append(f"\nParameters: {model_info['parameter_count']}", style="dim")
    if model_info.get('context_length'):
        context_length = model_info['context_length']
        if context_length >= 1000:
            context_str = f"{context_length // 1000}k"
        else:
            context_str = str(context_length)
        model_text.append(f"\nContext: {context_str} tokens", style="dim")
    
    # Memory estimation
    if model_info.get('estimated_memory_gb'):
        memory_gb = model_info['estimated_memory_gb']
        model_text.append(f"\nEstimated Memory: {memory_gb}GB", style="dim")
    
    # MLX availability
    mlx_status = ""
    if model_info.get('mlx_available'):
        mlx_status += "MLX ✓"
    if model_info.get('mlx_lm_available'):
        mlx_status += " | MLX-LM ✓"
    elif model_info.get('mlx_available'):
        mlx_status += " | MLX-LM ✗"
    
    if mlx_status:
        model_text.append(f"\n{mlx_status}", style="cyan")
    
    model_panel = Panel(
        model_text,
        title="[bold cyan]🤖 LLM Model Information[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(model_panel)
    
    # Performance and Token Metrics
    perf_table = Table(title="📊 Performance & Token Metrics", show_header=True, header_style="bold magenta")
    perf_table.add_column("Metric", style="dim", width=25)
    perf_table.add_column("Value", style="bold", width=20)
    perf_table.add_column("Details", style="dim")
    
    # Uptime
    uptime_seconds = performance.get('uptime_seconds', 0)
    if uptime_seconds > 3600:
        uptime_str = f"{uptime_seconds/3600:.1f}h"
    elif uptime_seconds > 60:
        uptime_str = f"{uptime_seconds/60:.1f}m"
    else:
        uptime_str = f"{uptime_seconds:.1f}s"
    perf_table.add_row("Uptime", uptime_str, "Time since service start")
    
    # Request metrics
    total_requests = session_metrics.get('total_requests', 0)
    successful_requests = session_metrics.get('successful_requests', 0)
    failed_requests = session_metrics.get('failed_requests', 0)
    error_rate = session_metrics.get('error_rate', 0)
    
    perf_table.add_row("Total Requests", str(total_requests), f"✓ {successful_requests} | ✗ {failed_requests}")
    
    if total_requests > 0:
        perf_table.add_row("Success Rate", f"{100-error_rate:.1f}%", f"Error rate: {error_rate:.1f}%")
    
    # Token metrics
    total_input_tokens = session_metrics.get('total_input_tokens', 0)
    total_output_tokens = session_metrics.get('total_output_tokens', 0)
    total_tokens = session_metrics.get('total_tokens', 0)
    
    if total_tokens > 0:
        if total_tokens >= 1000:
            tokens_str = f"{total_tokens/1000:.1f}k"
        else:
            tokens_str = str(total_tokens)
        perf_table.add_row("Total Tokens", tokens_str, f"In: {total_input_tokens} | Out: {total_output_tokens}")
    
    # Generation speed
    avg_speed = performance.get('recent_average_speed_tokens_per_sec', 0)
    if avg_speed > 0:
        perf_table.add_row("Generation Speed", f"{avg_speed:.1f} tok/s", "Recent average")
    
    # Generation time
    avg_latency = performance.get('recent_average_latency_seconds', 0)
    if avg_latency > 0:
        if avg_latency < 1:
            latency_str = f"{avg_latency*1000:.0f}ms"
        else:
            latency_str = f"{avg_latency:.2f}s"
        perf_table.add_row("Avg Latency", latency_str, "Time per generation")
    
    # Memory usage
    current_memory = memory.get('current_usage_mb', 0)
    if current_memory > 0:
        if current_memory >= 1000:
            memory_str = f"{current_memory/1000:.2f}GB"
        else:
            memory_str = f"{current_memory:.0f}MB"
        perf_table.add_row("Memory Usage", memory_str, "Current MLX memory")
    
    # Peak memory from session
    peak_memory = session_metrics.get('peak_memory_usage_mb', 0)
    if peak_memory > current_memory and peak_memory > 0:
        if peak_memory >= 1000:
            peak_str = f"{peak_memory/1000:.2f}GB"
        else:
            peak_str = f"{peak_memory:.0f}MB"
        perf_table.add_row("Peak Memory", peak_str, "Session maximum")
    
    # Last request time
    last_request = performance.get('last_request_time')
    if last_request:
        try:
            from datetime import datetime
            last_time = datetime.fromisoformat(last_request.replace('Z', '+00:00'))
            time_ago = datetime.now() - last_time.replace(tzinfo=None)
            if time_ago.total_seconds() < 60:
                time_str = f"{time_ago.total_seconds():.0f}s ago"
            elif time_ago.total_seconds() < 3600:
                time_str = f"{time_ago.total_seconds()/60:.0f}m ago"
            else:
                time_str = f"{time_ago.total_seconds()/3600:.1f}h ago"
            perf_table.add_row("Last Request", time_str, "Most recent generation")
        except (ValueError, TypeError) as e:
            logger.debug(f"Error parsing time data: {e}")
            perf_table.add_row("Last Request", "Recently", "Most recent generation")
        except Exception as e:
            logger.warning(f"Unexpected error formatting time: {e}")
            perf_table.add_row("Last Request", "Recently", "Most recent generation")
    
    console.print(perf_table)
    
    # Session details (if there are requests)
    if total_requests > 0:
        session_table = Table(title="📈 Session Statistics", show_header=True, header_style="bold blue")
        session_table.add_column("Metric", style="dim")
        session_table.add_column("Average", style="bold")
        session_table.add_column("Min / Max", style="dim")
        
        # Average generation time
        avg_gen_time = session_metrics.get('average_generation_time', 0)
        min_gen_time = session_metrics.get('min_generation_time')
        max_gen_time = session_metrics.get('max_generation_time')
        
        if avg_gen_time > 0:
            avg_time_str = f"{avg_gen_time:.2f}s" if avg_gen_time >= 1 else f"{avg_gen_time*1000:.0f}ms"
            min_max_str = ""
            if min_gen_time is not None and max_gen_time is not None:
                min_str = f"{min_gen_time:.2f}s" if min_gen_time >= 1 else f"{min_gen_time*1000:.0f}ms"
                max_str = f"{max_gen_time:.2f}s" if max_gen_time >= 1 else f"{max_gen_time*1000:.0f}ms"
                min_max_str = f"{min_str} / {max_str}"
            session_table.add_row("Generation Time", avg_time_str, min_max_str)
        
        # Average tokens per second
        avg_tps = session_metrics.get('average_tokens_per_second', 0)
        if avg_tps > 0:
            session_table.add_row("Tokens/Second", f"{avg_tps:.1f}", "Session average")
        
        # Average memory usage
        avg_memory = session_metrics.get('average_memory_usage_mb', 0)
        if avg_memory > 0:
            avg_mem_str = f"{avg_memory/1000:.2f}GB" if avg_memory >= 1000 else f"{avg_memory:.0f}MB"
            session_table.add_row("Memory Usage", avg_mem_str, "Session average")
        
        console.print(session_table)