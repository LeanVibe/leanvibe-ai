"""
iOS App Integration Commands for LeanVibe CLI

Provides seamless integration between CLI power users and the iOS companion app,
enabling state synchronization, notification management, and cross-platform workflows.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.columns import Columns

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.group(name="ios", invoke_without_command=True)
@click.pass_context
def ios(ctx: click.Context):
    """
    iOS App Integration and State Synchronization
    
    Bridge CLI workflows with the iOS companion app for seamless
    cross-platform development experience.
    """
    if ctx.invoked_subcommand is None:
        # Show iOS app status and connection info
        try:
            config: CLIConfig = ctx.obj['config']
            client: BackendClient = ctx.obj['client']
            asyncio.run(show_ios_status(config, client))
        except Exception as e:
            console.print(f"[red]Error checking iOS status: {e}[/red]")


@ios.command(name="status")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed connection information")
@click.pass_context
def ios_status(ctx: click.Context, detailed: bool):
    """Check iOS app connection and synchronization status"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(show_ios_status(config, client, detailed))


@ios.command(name="sync")
@click.option("--projects", "-p", is_flag=True, help="Sync project data")
@click.option("--tasks", "-t", is_flag=True, help="Sync task data")
@click.option("--metrics", "-m", is_flag=True, help="Sync metrics data")
@click.option("--all", "-a", is_flag=True, help="Sync all data")
@click.option("--force", "-f", is_flag=True, help="Force sync even if up-to-date")
@click.pass_context
def sync_with_ios(ctx: click.Context, projects: bool, tasks: bool, metrics: bool, all: bool, force: bool):
    """Synchronize CLI state with iOS app"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    # Determine what to sync
    sync_projects = projects or all
    sync_tasks = tasks or all  
    sync_metrics = metrics or all
    
    if not any([sync_projects, sync_tasks, sync_metrics]):
        # Default to syncing everything if no specific options
        sync_projects = sync_tasks = sync_metrics = True
    
    asyncio.run(_execute_sync_workflow(
        config, client, sync_projects, sync_tasks, sync_metrics, force
    ))


@ios.command(name="notify")
@click.argument("message")
@click.option("--priority", "-p", type=click.Choice(['low', 'medium', 'high', 'critical']), 
              default='medium', help="Notification priority")
@click.option("--title", "-t", help="Notification title")
@click.option("--category", "-c", help="Notification category")
@click.option("--action-url", help="URL to open when notification is tapped")
@click.pass_context
def send_notification(ctx: click.Context, message: str, priority: str, title: Optional[str], 
                     category: Optional[str], action_url: Optional[str]):
    """Send notification to iOS app"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_send_ios_notification(
        config, client, message, priority, title, category, action_url
    ))


@ios.command(name="projects")
@click.option("--push", is_flag=True, help="Push CLI project changes to iOS")
@click.option("--pull", is_flag=True, help="Pull iOS project changes to CLI")
@click.option("--compare", is_flag=True, help="Compare CLI and iOS project states")
@click.pass_context
def manage_projects(ctx: click.Context, push: bool, pull: bool, compare: bool):
    """Manage project synchronization between CLI and iOS"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    if compare or not any([push, pull]):
        # Default to compare if no action specified
        asyncio.run(_compare_project_states(config, client))
    elif push:
        asyncio.run(_push_projects_to_ios(config, client))
    elif pull:
        asyncio.run(_pull_projects_from_ios(config, client))


@ios.command(name="tasks")
@click.option("--create", help="Create task on iOS app")
@click.option("--update", help="Update task status (format: task_id:status)")
@click.option("--list", "-l", is_flag=True, help="List tasks from iOS app")
@click.option("--filter", help="Filter tasks by status")
@click.pass_context
def manage_tasks(ctx: click.Context, create: Optional[str], update: Optional[str], 
                list: bool, filter: Optional[str]):
    """Manage tasks synchronized with iOS app"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    if create:
        asyncio.run(_create_task_on_ios(config, client, create))
    elif update:
        asyncio.run(_update_task_on_ios(config, client, update))
    elif list:
        asyncio.run(_list_ios_tasks(config, client, filter))
    else:
        # Default to listing tasks
        asyncio.run(_list_ios_tasks(config, client, filter))


@ios.command(name="monitor")
@click.option("--duration", "-t", type=int, help="Monitor duration in seconds")
@click.option("--events", is_flag=True, help="Monitor iOS app events")
@click.option("--usage", is_flag=True, help="Monitor iOS app usage metrics")
@click.pass_context
def monitor_ios(ctx: click.Context, duration: Optional[int], events: bool, usage: bool):
    """Monitor iOS app activity and events"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    monitor_events = events or not usage
    monitor_usage = usage or not events
    
    asyncio.run(_monitor_ios_activity(config, client, duration, monitor_events, monitor_usage))


@ios.command(name="launch")
@click.option("--screen", help="Specific screen to open (dashboard, projects, tasks, settings)")
@click.option("--project-id", help="Project ID to open")
@click.option("--task-id", help="Task ID to open")
@click.pass_context
def launch_ios_app(ctx: click.Context, screen: Optional[str], 
                  project_id: Optional[str], task_id: Optional[str]):
    """Launch iOS app with specific screen or content"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_launch_ios_app(config, client, screen, project_id, task_id))


# Implementation Functions

async def show_ios_status(config: CLIConfig, client: BackendClient, detailed: bool = False):
    """Show iOS app connection and sync status"""
    
    try:
        async with client:
            # Check backend connection
            health_data = await client.health_check()
            
            # Get iOS client connections
            ios_status = await get_ios_connection_status(client)
            
            # Display main status
            display_ios_status_panel(ios_status, health_data)
            
            if detailed:
                # Show detailed connection info
                await display_detailed_ios_info(client, ios_status)
                
    except Exception as e:
        console.print(f"[red]Error checking iOS status: {e}[/red]")
        console.print("[yellow]Make sure the LeanVibe backend is running[/yellow]")


async def _execute_sync_workflow(config: CLIConfig, client: BackendClient, 
                                sync_projects: bool, sync_tasks: bool, 
                                sync_metrics: bool, force: bool):
    """Execute comprehensive sync workflow with iOS app"""
    
    console.print("[cyan]Starting iOS synchronization...[/cyan]\n")
    
    sync_results = {}
    
    try:
        async with client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                
                if sync_projects:
                    task = progress.add_task("Syncing projects...", total=None)
                    sync_results['projects'] = await sync_projects_data(client, force)
                    progress.update(task, description="Projects synced")
                
                if sync_tasks:
                    task = progress.add_task("Syncing tasks...", total=None)
                    sync_results['tasks'] = await sync_tasks_data(client, force)
                    progress.update(task, description="Tasks synced")
                
                if sync_metrics:
                    task = progress.add_task("Syncing metrics...", total=None)
                    sync_results['metrics'] = await sync_metrics_data(client, force)
                    progress.update(task, description="Metrics synced")
        
        # Display sync results
        display_sync_results(sync_results)
        
    except Exception as e:
        console.print(f"[red]Sync failed: {e}[/red]")


async def _send_ios_notification(config: CLIConfig, client: BackendClient, 
                                message: str, priority: str, title: Optional[str],
                                category: Optional[str], action_url: Optional[str]):
    """Send notification to iOS app"""
    
    notification_data = {
        "message": message,
        "priority": priority,
        "title": title or "LeanVibe CLI",
        "category": category or "general",
        "timestamp": datetime.now().isoformat(),
        "source": "cli",
        "action_url": action_url
    }
    
    try:
        async with client:
            result = await client.send_ios_notification(notification_data)
            
            if result.get('success'):
                console.print("[green]✅ Notification sent to iOS app[/green]")
                console.print(f"[dim]Message: {message}[/dim]")
                console.print(f"[dim]Priority: {priority.upper()}[/dim]")
            else:
                console.print(f"[red]Failed to send notification: {result.get('error', 'Unknown error')}[/red]")
                
    except Exception as e:
        console.print(f"[red]Error sending notification: {e}[/red]")


async def _compare_project_states(config: CLIConfig, client: BackendClient):
    """Compare project states between CLI and iOS"""
    
    try:
        async with client:
            cli_projects = await client.get_projects()
            ios_projects = await client.get_ios_projects()
            
            # Compare and display differences
            display_project_comparison(cli_projects, ios_projects)
            
    except Exception as e:
        console.print(f"[red]Error comparing projects: {e}[/red]")


async def _push_projects_to_ios(config: CLIConfig, client: BackendClient):
    """Push CLI project changes to iOS app"""
    
    try:
        async with client:
            projects = await client.get_projects()
            
            console.print(f"[cyan]Pushing {len(projects)} projects to iOS...[/cyan]")
            
            result = await client.push_projects_to_ios(projects)
            
            if result.get('success'):
                console.print(f"[green]✅ Pushed {result.get('count', 0)} projects to iOS[/green]")
            else:
                console.print(f"[red]Failed to push projects: {result.get('error')}[/red]")
                
    except Exception as e:
        console.print(f"[red]Error pushing projects: {e}[/red]")


async def _pull_projects_from_ios(config: CLIConfig, client: BackendClient):
    """Pull iOS project changes to CLI"""
    
    try:
        async with client:
            result = await client.pull_projects_from_ios()
            
            if result.get('success'):
                console.print(f"[green]✅ Pulled {result.get('count', 0)} projects from iOS[/green]")
                
                # Display updated projects
                if result.get('projects'):
                    display_updated_projects(result['projects'])
            else:
                console.print(f"[red]Failed to pull projects: {result.get('error')}[/red]")
                
    except Exception as e:
        console.print(f"[red]Error pulling projects: {e}[/red]")


async def _create_task_on_ios(config: CLIConfig, client: BackendClient, task_description: str):
    """Create task on iOS app"""
    
    task_data = {
        "title": task_description,
        "status": "todo",
        "priority": "medium",
        "created_by": "cli",
        "created_at": datetime.now().isoformat()
    }
    
    try:
        async with client:
            result = await client.create_ios_task(task_data)
            
            if result.get('success'):
                console.print(f"[green]✅ Created task on iOS: {task_description}[/green]")
                console.print(f"[dim]Task ID: {result.get('task_id')}[/dim]")
            else:
                console.print(f"[red]Failed to create task: {result.get('error')}[/red]")
                
    except Exception as e:
        console.print(f"[red]Error creating task: {e}[/red]")


async def _update_task_on_ios(config: CLIConfig, client: BackendClient, update_info: str):
    """Update task status on iOS app"""
    
    try:
        task_id, status = update_info.split(':', 1)
        
        update_data = {
            "status": status.strip(),
            "updated_by": "cli",
            "updated_at": datetime.now().isoformat()
        }
        
        async with client:
            result = await client.update_ios_task(task_id.strip(), update_data)
            
            if result.get('success'):
                console.print(f"[green]✅ Updated task {task_id} to {status}[/green]")
            else:
                console.print(f"[red]Failed to update task: {result.get('error')}[/red]")
                
    except ValueError:
        console.print("[red]Invalid update format. Use: task_id:status[/red]")
    except Exception as e:
        console.print(f"[red]Error updating task: {e}[/red]")


async def _list_ios_tasks(config: CLIConfig, client: BackendClient, filter_status: Optional[str]):
    """List tasks from iOS app"""
    
    try:
        async with client:
            tasks = await client.get_ios_tasks(status_filter=filter_status)
            
            if tasks:
                display_ios_tasks_table(tasks, filter_status)
            else:
                filter_msg = f" with status '{filter_status}'" if filter_status else ""
                console.print(f"[yellow]No tasks found{filter_msg}[/yellow]")
                
    except Exception as e:
        console.print(f"[red]Error listing tasks: {e}[/red]")


async def _monitor_ios_activity(config: CLIConfig, client: BackendClient, 
                               duration: Optional[int], monitor_events: bool, 
                               monitor_usage: bool):
    """Monitor iOS app activity and events"""
    
    console.print("[cyan]Starting iOS app monitoring...[/cyan]")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")
    
    start_time = datetime.now()
    event_count = 0
    
    try:
        async with client:
            async for event in client.monitor_ios_events():
                if duration and (datetime.now() - start_time).seconds > duration:
                    break
                
                event_count += 1
                
                if monitor_events and event.get('type') == 'user_action':
                    display_ios_event(event)
                elif monitor_usage and event.get('type') == 'usage_metric':
                    display_ios_usage_metric(event)
                
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Monitoring stopped. Received {event_count} events.[/yellow]")
    except Exception as e:
        console.print(f"[red]Monitoring error: {e}[/red]")


async def _launch_ios_app(config: CLIConfig, client: BackendClient, 
                         screen: Optional[str], project_id: Optional[str], 
                         task_id: Optional[str]):
    """Launch iOS app with specific screen or content"""
    
    launch_data = {
        "source": "cli",
        "timestamp": datetime.now().isoformat()
    }
    
    if screen:
        launch_data["screen"] = screen
    if project_id:
        launch_data["project_id"] = project_id
    if task_id:
        launch_data["task_id"] = task_id
    
    try:
        async with client:
            result = await client.launch_ios_app(launch_data)
            
            if result.get('success'):
                console.print("[green]✅ iOS app launch request sent[/green]")
                if screen:
                    console.print(f"[dim]Target screen: {screen}[/dim]")
            else:
                console.print(f"[red]Failed to launch iOS app: {result.get('error')}[/red]")
                
    except Exception as e:
        console.print(f"[red]Error launching iOS app: {e}[/red]")


# Helper Functions

async def get_ios_connection_status(client: BackendClient) -> Dict[str, Any]:
    """Get iOS connection status from backend"""
    try:
        return await client.get_ios_status()
    except Exception:
        return {"connected": False, "error": "Unable to check iOS status"}


async def sync_projects_data(client: BackendClient, force: bool) -> Dict[str, Any]:
    """Sync projects data with iOS"""
    return await client.sync_ios_projects(force=force)


async def sync_tasks_data(client: BackendClient, force: bool) -> Dict[str, Any]:
    """Sync tasks data with iOS"""
    return await client.sync_ios_tasks(force=force)


async def sync_metrics_data(client: BackendClient, force: bool) -> Dict[str, Any]:
    """Sync metrics data with iOS"""
    return await client.sync_ios_metrics(force=force)


# Display Functions

def display_ios_status_panel(ios_status: Dict[str, Any], health_data: Dict[str, Any]):
    """Display iOS status panel"""
    
    status_text = Text()
    
    # Connection status
    if ios_status.get('connected'):
        status_text.append("🟢 ", style="green")
        status_text.append("Connected", style="bold green")
        
        # Connected device info
        device_info = ios_status.get('device_info', {})
        status_text.append(f"\nDevice: {device_info.get('name', 'Unknown')}")
        status_text.append(f"\nApp Version: {device_info.get('app_version', 'Unknown')}")
        status_text.append(f"\nLast Sync: {ios_status.get('last_sync', 'Never')}")
    else:
        status_text.append("🔴 ", style="red")
        status_text.append("Disconnected", style="bold red")
        status_text.append(f"\nError: {ios_status.get('error', 'No iOS devices connected')}")
    
    # Backend status
    backend_status = health_data.get('status', 'unknown')
    status_text.append(f"\nBackend: {backend_status.title()}", style="dim")
    
    panel = Panel(
        status_text,
        title="[bold]iOS App Status[/bold]",
        border_style="green" if ios_status.get('connected') else "red",
        padding=(1, 2)
    )
    
    console.print(panel)


async def display_detailed_ios_info(client: BackendClient, ios_status: Dict[str, Any]):
    """Display detailed iOS connection information"""
    
    if not ios_status.get('connected'):
        return
    
    try:
        # Get additional iOS info
        ios_details = await client.get_ios_details()
        
        # Create detailed info table
        table = Table(title="iOS Connection Details", show_header=True, header_style="bold cyan")
        table.add_column("Property", style="dim")
        table.add_column("Value", style="bold")
        
        for key, value in ios_details.items():
            table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[yellow]Could not fetch detailed iOS info: {e}[/yellow]")


def display_sync_results(sync_results: Dict[str, Any]):
    """Display synchronization results"""
    
    result_panels = []
    
    for category, result in sync_results.items():
        if result.get('success'):
            status = f"✅ Success ({result.get('count', 0)} items)"
            style = "green"
        else:
            status = f"❌ Failed: {result.get('error', 'Unknown error')}"
            style = "red"
        
        panel = Panel(
            Text(status, style=style),
            title=f"[bold]{category.title()}[/bold]",
            border_style=style,
            width=30
        )
        result_panels.append(panel)
    
    if result_panels:
        console.print(Columns(result_panels))
        console.print("\n[green]✅ Synchronization completed[/green]")


def display_project_comparison(cli_projects: List[Dict], ios_projects: List[Dict]):
    """Display project comparison between CLI and iOS"""
    
    table = Table(title="Project Comparison: CLI vs iOS", show_header=True, header_style="bold magenta")
    table.add_column("Project", style="cyan")
    table.add_column("CLI Status", style="green")
    table.add_column("iOS Status", style="blue")
    table.add_column("Last Modified", style="dim")
    
    # Create lookup for iOS projects
    ios_lookup = {p['id']: p for p in ios_projects}
    
    for cli_project in cli_projects:
        project_id = cli_project['id']
        ios_project = ios_lookup.get(project_id)
        
        if ios_project:
            ios_status = ios_project.get('status', 'Unknown')
            last_modified = max(
                cli_project.get('updated_at', ''), 
                ios_project.get('updated_at', '')
            )
        else:
            ios_status = "Not synced"
            last_modified = cli_project.get('updated_at', 'Unknown')
        
        table.add_row(
            cli_project.get('name', 'Unknown'),
            cli_project.get('status', 'Unknown'),
            ios_status,
            last_modified
        )
    
    console.print(table)


def display_updated_projects(projects: List[Dict]):
    """Display updated projects from iOS"""
    
    table = Table(title="Updated Projects from iOS", show_header=True, header_style="bold green")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Health Score", style="magenta")
    table.add_column("Last Updated", style="dim")
    
    for project in projects:
        health_score = project.get('health_score', 0)
        health_display = f"{health_score:.1%}" if isinstance(health_score, (int, float)) else str(health_score)
        
        table.add_row(
            project.get('name', 'Unknown'),
            project.get('status', 'Unknown'),
            health_display,
            project.get('updated_at', 'Unknown')
        )
    
    console.print(table)


def display_ios_tasks_table(tasks: List[Dict], filter_status: Optional[str]):
    """Display iOS tasks in a table"""
    
    title = "iOS Tasks"
    if filter_status:
        title += f" (Status: {filter_status})"
    
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Title", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Priority", style="yellow")
    table.add_column("Created", style="dim")
    
    for task in tasks:
        # Shorten task ID for display
        task_id = str(task.get('id', ''))[:8]
        
        # Color code status
        status = task.get('status', 'unknown')
        if status == 'completed':
            status_style = 'green'
        elif status == 'in_progress':
            status_style = 'yellow'
        else:
            status_style = 'white'
        
        table.add_row(
            task_id,
            task.get('title', 'Unknown'),
            f"[{status_style}]{status}[/{status_style}]",
            task.get('priority', 'medium'),
            task.get('created_at', 'Unknown')
        )
    
    console.print(table)


def display_ios_event(event: Dict[str, Any]):
    """Display iOS app event"""
    timestamp = event.get('timestamp', datetime.now().isoformat())
    action = event.get('action', 'Unknown')
    details = event.get('details', '')
    
    console.print(f"[dim]{timestamp}[/dim] [cyan]iOS Event:[/cyan] {action} {details}")


def display_ios_usage_metric(metric: Dict[str, Any]):
    """Display iOS app usage metric"""
    timestamp = metric.get('timestamp', datetime.now().isoformat())
    metric_name = metric.get('name', 'Unknown')
    value = metric.get('value', 'N/A')
    
    console.print(f"[dim]{timestamp}[/dim] [magenta]Usage:[/magenta] {metric_name} = {value}")


if __name__ == "__main__":
    # For testing
    pass