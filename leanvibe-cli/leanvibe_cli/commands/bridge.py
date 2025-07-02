"""
CLI Bridge monitoring commands for LeanVibe CLI

Provides specific monitoring and status commands for the CLI-iOS bridge functionality,
allowing developers to check connectivity, monitor device connections, and view bridge metrics.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.group(name="bridge", invoke_without_command=True)
@click.pass_context
def bridge(ctx: click.Context):
    """
    Monitor and manage CLI-iOS bridge connectivity
    
    These commands help you monitor the bridge between the CLI and iOS devices,
    check connection status, and view real-time metrics for connected devices.
    """
    if ctx.invoked_subcommand is None:
        # Show bridge status by default
        config: CLIConfig = ctx.obj['config']
        client: BackendClient = ctx.obj['client']
        asyncio.run(show_bridge_status(config, client))


@bridge.command(name="status")
@click.option("--json", "output_json", is_flag=True, help="Output status as JSON")
@click.pass_context
def bridge_status(ctx: click.Context, output_json: bool):
    """Show CLI bridge connection status"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(show_bridge_status(config, client, output_json))


@bridge.command(name="devices")
@click.option("--refresh", "-r", is_flag=True, help="Auto-refresh device list")
@click.option("--interval", "-i", type=int, default=5, help="Refresh interval in seconds")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_devices(ctx: click.Context, refresh: bool, interval: int, output_json: bool):
    """List connected iOS devices"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    if refresh and not output_json:
        asyncio.run(live_device_monitoring(config, client, interval))
    else:
        asyncio.run(show_devices_list(config, client, output_json))


@bridge.command(name="metrics")
@click.option("--live", "-l", is_flag=True, help="Show live updating metrics")
@click.option("--interval", "-i", type=int, default=3, help="Update interval in seconds")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def bridge_metrics(ctx: click.Context, live: bool, interval: int, output_json: bool):
    """Show CLI bridge performance metrics"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    if live and not output_json:
        asyncio.run(live_metrics_monitoring(config, client, interval))
    else:
        asyncio.run(show_bridge_metrics(config, client, output_json))


@bridge.command(name="test")
@click.option("--device", "-d", help="Specific device ID to test")
@click.option("--message", "-m", default="Test message from CLI", help="Test message content")
@click.pass_context
def test_bridge(ctx: click.Context, device: Optional[str], message: str):
    """Test CLI bridge connectivity with devices"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(test_bridge_connectivity(config, client, device, message))


async def show_bridge_status(config: CLIConfig, client: BackendClient, output_json: bool = False):
    """Show comprehensive bridge status"""
    try:
        async with client:
            # Get bridge status
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Checking bridge status...", total=None)
                
                status_data = await client.get_cli_bridge_status()
                bridge_data = await client.get("/cli/bridge/status")
                
                progress.update(task, description="Status retrieved")
            
            if output_json:
                import json
                combined_data = {
                    "cli_status": status_data,
                    "bridge_status": bridge_data,
                    "timestamp": datetime.now().isoformat()
                }
                console.print(json.dumps(combined_data, indent=2))
                return
            
            # Display formatted status
            display_bridge_status(status_data, bridge_data, config)
    
    except Exception as e:
        if output_json:
            import json
            error_data = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            console.print(json.dumps(error_data, indent=2))
        else:
            console.print(f"[red]❌ Error getting bridge status: {e}[/red]")


async def show_devices_list(config: CLIConfig, client: BackendClient, output_json: bool = False):
    """Show list of connected devices"""
    try:
        async with client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Fetching device list...", total=None)
                
                devices_data = await client.list_connected_devices()
                
                progress.update(task, description="Device list retrieved")
            
            if output_json:
                import json
                console.print(json.dumps(devices_data, indent=2, default=str))
                return
            
            # Display formatted device list
            display_devices_table(devices_data)
    
    except Exception as e:
        if output_json:
            import json
            error_data = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            console.print(json.dumps(error_data, indent=2))
        else:
            console.print(f"[red]❌ Error getting device list: {e}[/red]")


async def show_bridge_metrics(config: CLIConfig, client: BackendClient, output_json: bool = False):
    """Show bridge performance metrics"""
    try:
        async with client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Fetching metrics...", total=None)
                
                metrics_data = await client.get_monitoring_data()
                
                progress.update(task, description="Metrics retrieved")
            
            if output_json:
                import json
                console.print(json.dumps(metrics_data, indent=2, default=str))
                return
            
            # Display formatted metrics
            display_metrics_dashboard(metrics_data)
    
    except Exception as e:
        if output_json:
            import json
            error_data = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            console.print(json.dumps(error_data, indent=2))
        else:
            console.print(f"[red]❌ Error getting metrics: {e}[/red]")


async def live_device_monitoring(config: CLIConfig, client: BackendClient, interval: int):
    """Live monitoring of connected devices"""
    console.print("[green]🔄 Live device monitoring - Press Ctrl+C to stop[/green]\n")
    
    try:
        async with client:
            with Live(
                generate_devices_display({}),
                refresh_per_second=1,
                console=console
            ) as live:
                
                while True:
                    try:
                        devices_data = await client.list_connected_devices()
                        live.update(generate_devices_display(devices_data))
                        await asyncio.sleep(interval)
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        console.print(f"[red]Error during live monitoring: {e}[/red]")
                        break
    
    except Exception as e:
        console.print(f"[red]❌ Error in live device monitoring: {e}[/red]")


async def live_metrics_monitoring(config: CLIConfig, client: BackendClient, interval: int):
    """Live monitoring of bridge metrics"""
    console.print("[green]🔄 Live metrics monitoring - Press Ctrl+C to stop[/green]\n")
    
    try:
        async with client:
            with Live(
                generate_metrics_display({}),
                refresh_per_second=1,
                console=console
            ) as live:
                
                while True:
                    try:
                        metrics_data = await client.get_monitoring_data()
                        live.update(generate_metrics_display(metrics_data))
                        await asyncio.sleep(interval)
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        console.print(f"[red]Error during live monitoring: {e}[/red]")
                        break
    
    except Exception as e:
        console.print(f"[red]❌ Error in live metrics monitoring: {e}[/red]")


async def test_bridge_connectivity(config: CLIConfig, client: BackendClient, device_id: Optional[str], message: str):
    """Test bridge connectivity with devices"""
    console.print("[cyan]🧪 Testing CLI bridge connectivity...[/cyan]\n")
    
    try:
        async with client:
            # First get list of devices
            devices_data = await client.list_connected_devices()
            devices = devices_data.get("devices", [])
            
            if not devices:
                console.print("[yellow]⚠️ No iOS devices connected[/yellow]")
                return
            
            # Determine which devices to test
            test_devices = []
            if device_id:
                # Test specific device
                target_device = next((d for d in devices if d["client_id"] == device_id), None)
                if target_device:
                    test_devices = [target_device]
                else:
                    console.print(f"[red]❌ Device '{device_id}' not found[/red]")
                    console.print(f"[yellow]Available devices: {', '.join(d['client_id'] for d in devices)}[/yellow]")
                    return
            else:
                # Test all devices
                test_devices = devices
            
            # Test each device
            for device in test_devices:
                device_id = device["client_id"]
                console.print(f"[cyan]Testing device: {device_id}[/cyan]")
                
                try:
                    # Send test message
                    test_message = {
                        "type": "cli_test_message",
                        "content": message,
                        "timestamp": datetime.now().isoformat(),
                        "test_id": f"test_{int(datetime.now().timestamp())}"
                    }
                    
                    result = await client.post(f"/cli/devices/{device_id}/message", test_message)
                    
                    if result.get("success"):
                        console.print(f"[green]  ✅ Message sent successfully[/green]")
                    else:
                        console.print(f"[red]  ❌ Failed to send message[/red]")
                
                except Exception as e:
                    console.print(f"[red]  ❌ Error testing device: {e}[/red]")
            
            console.print(f"\n[green]Bridge connectivity test completed for {len(test_devices)} device(s)[/green]")
    
    except Exception as e:
        console.print(f"[red]❌ Error during connectivity test: {e}[/red]")


def display_bridge_status(status_data: Dict[str, Any], bridge_data: Dict[str, Any], config: CLIConfig):
    """Display formatted bridge status"""
    
    # Status panel
    status_text = Text()
    
    # CLI Status
    cli_status = status_data.get("status", "unknown")
    status_icon = "🟢" if cli_status == "active" else "🟡" if cli_status == "idle" else "🔴"
    status_text.append(f"{status_icon} CLI Bridge: ", style="bold")
    status_text.append(f"{cli_status.upper()}\n", style="green" if cli_status == "active" else "yellow")
    
    # Connection info
    active_sessions = status_data.get("active_sessions", 0)
    ios_devices = status_data.get("connected_ios_devices", 0)
    
    status_text.append(f"Active Sessions: {active_sessions}\n")
    status_text.append(f"iOS Devices: {ios_devices}\n")
    
    # Bridge connections
    active_bridges = bridge_data.get("active_bridges", 0)
    status_text.append(f"Bridge Connections: {active_bridges}\n")
    
    # Last activity
    last_activity = status_data.get("last_activity")
    if last_activity:
        status_text.append(f"Last Activity: {last_activity}\n", style="dim")
    
    status_panel = Panel(
        status_text,
        title="[bold]Bridge Status[/bold]",
        border_style="green" if cli_status == "active" else "yellow",
        padding=(1, 2)
    )
    
    # Configuration panel
    config_text = Text()
    config_text.append(f"Backend URL: {config.backend_url}\n", style="cyan")
    config_text.append(f"WebSocket URL: {config.websocket_url}\n", style="cyan")
    config_text.append(f"Timeout: {config.timeout_seconds}s\n")
    config_text.append(f"Verbose: {'Yes' if config.verbose else 'No'}\n")
    
    config_panel = Panel(
        config_text,
        title="[bold]Configuration[/bold]",
        border_style="blue",
        padding=(1, 2)
    )
    
    # Display combined panels
    console.print(Columns([status_panel, config_panel], expand=True))


def display_devices_table(devices_data: Dict[str, Any]):
    """Display devices in a formatted table"""
    devices = devices_data.get("devices", [])
    total_count = devices_data.get("total_count", 0)
    
    if not devices:
        console.print("[yellow]📱 No iOS devices currently connected[/yellow]")
        return
    
    table = Table(
        title=f"Connected iOS Devices ({total_count})",
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("Device ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Connected Since", style="yellow")
    table.add_column("Last Seen", style="dim")
    table.add_column("Status", style="bold")
    
    for device in devices:
        device_id = device.get("client_id", "unknown")
        device_type = device.get("device_type", "ios")
        connected_at = device.get("connected_at", "unknown")
        last_seen = device.get("last_seen", "unknown")
        status = device.get("status", "unknown")
        
        # Format timestamps
        if connected_at != "unknown":
            try:
                connected_time = datetime.fromisoformat(connected_at.replace('Z', '+00:00'))
                connected_at = connected_time.strftime("%H:%M:%S")
            except:
                pass
        
        if last_seen != "unknown":
            try:
                last_seen_time = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                last_seen = last_seen_time.strftime("%H:%M:%S")
            except:
                pass
        
        status_color = "green" if status == "connected" else "red"
        
        table.add_row(
            device_id,
            device_type.upper(),
            connected_at,
            last_seen,
            f"[{status_color}]{status.upper()}[/{status_color}]"
        )
    
    console.print(table)


def display_metrics_dashboard(metrics_data: Dict[str, Any]):
    """Display bridge metrics in a dashboard format"""
    console.print(generate_metrics_display(metrics_data))


def generate_devices_display(devices_data: Dict[str, Any]):
    """Generate live devices display"""
    devices = devices_data.get("devices", [])
    timestamp = devices_data.get("timestamp", datetime.now().isoformat())
    
    # Create devices table
    table = Table(show_header=True, header_style="bold cyan", title="Connected iOS Devices")
    table.add_column("Device ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="bold")
    table.add_column("Last Seen", style="dim")
    
    for device in devices:
        device_id = device.get("client_id", "unknown")
        device_type = device.get("device_type", "ios")
        status = device.get("status", "unknown")
        last_seen = device.get("last_seen", "unknown")
        
        status_color = "green" if status == "connected" else "red"
        
        table.add_row(
            device_id,
            device_type.upper(),
            f"[{status_color}]{status.upper()}[/{status_color}]",
            last_seen
        )
    
    # Add timestamp
    timestamp_text = Text(f"Last Updated: {timestamp}", style="dim")
    
    return Panel(
        table,
        title="[bold]Live Device Monitoring[/bold]",
        border_style="blue",
        subtitle=timestamp_text
    )


def generate_metrics_display(metrics_data: Dict[str, Any]):
    """Generate live metrics display"""
    timestamp = metrics_data.get("timestamp", datetime.now().isoformat())
    connections = metrics_data.get("connections", {})
    performance = metrics_data.get("performance", {})
    system = metrics_data.get("system", {})
    
    # Connections metrics
    conn_text = Text()
    conn_text.append(f"Total Connections: {connections.get('total', 0)}\n")
    conn_text.append(f"CLI Bridges: {connections.get('cli_bridges', 0)}\n")
    conn_text.append(f"iOS Devices: {connections.get('ios_devices', 0)}\n")
    conn_text.append(f"Active Sessions: {connections.get('active_sessions', 0)}\n")
    
    conn_panel = Panel(
        conn_text,
        title="[bold]Connections[/bold]",
        border_style="green"
    )
    
    # Performance metrics
    perf_text = Text()
    avg_response = performance.get('average_response_time', 0)
    total_requests = performance.get('total_requests', 0)
    error_rate = performance.get('error_rate', 0)
    
    perf_text.append(f"Avg Response Time: {avg_response:.3f}s\n")
    perf_text.append(f"Total Requests: {total_requests}\n")
    perf_text.append(f"Error Rate: {error_rate:.2%}\n")
    
    perf_panel = Panel(
        perf_text,
        title="[bold]Performance[/bold]",
        border_style="yellow"
    )
    
    # System metrics
    sys_text = Text()
    uptime = system.get('uptime_seconds', 0)
    memory_mb = system.get('memory_usage_mb', 0)
    
    uptime_hours = uptime / 3600
    sys_text.append(f"Uptime: {uptime_hours:.1f}h\n")
    sys_text.append(f"Memory Usage: {memory_mb}MB\n")
    
    sys_panel = Panel(
        sys_text,
        title="[bold]System[/bold]",
        border_style="blue"
    )
    
    # Combine panels
    metrics_layout = Columns([conn_panel, perf_panel, sys_panel], expand=True)
    
    return Panel(
        metrics_layout,
        title="[bold]CLI Bridge Metrics[/bold]",
        border_style="cyan",
        subtitle=Text(f"Updated: {timestamp}", style="dim")
    )