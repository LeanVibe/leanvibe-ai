"""
Info command for LeanVibe CLI

Shows available backend capabilities and API endpoints.
"""

import asyncio
from typing import Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.command()
@click.option('--endpoints', '-e', is_flag=True, help='Show available API endpoints')
@click.option('--capabilities', '-c', is_flag=True, help='Show backend capabilities')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def info(ctx: click.Context, endpoints: bool, capabilities: bool, output_json: bool):
    """Show backend information and available features"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    # If no specific option, show overview
    if not any([endpoints, capabilities]):
        endpoints = capabilities = True
    
    asyncio.run(info_command(config, client, endpoints, capabilities, output_json))


async def info_command(config: CLIConfig, client: BackendClient, show_endpoints: bool, show_capabilities: bool, output_json: bool):
    """Execute info command"""
    try:
        async with client:
            # Get backend health to understand capabilities
            health_data = await client.health_check()
            
            if output_json:
                info_data = {
                    "backend_url": config.backend_url,
                    "health": health_data,
                    "endpoints": get_available_endpoints() if show_endpoints else None,
                    "capabilities": extract_capabilities(health_data) if show_capabilities else None
                }
                import json
                console.print(json.dumps(info_data, indent=2))
                return
            
            display_backend_info(health_data, config)
            
            if show_capabilities:
                display_capabilities(health_data)
            
            if show_endpoints:
                display_endpoints()
                
    except Exception as e:
        if output_json:
            import json
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Failed to get backend info: {e}[/red]")


def display_backend_info(health_data: Dict[str, Any], config: CLIConfig):
    """Display basic backend information"""
    info_text = Text()
    info_text.append("🏗️ LeanVibe Backend Information\n", style="bold cyan")
    
    # Basic info
    info_text.append(f"URL: {config.backend_url}\n")
    info_text.append(f"Service: {health_data.get('service', 'unknown')}\n")
    info_text.append(f"Version: {health_data.get('version', 'unknown')}\n")
    info_text.append(f"Framework: {health_data.get('agent_framework', 'unknown')}\n")
    
    # Status
    status = health_data.get('status', 'unknown')
    status_color = "green" if status == "healthy" else "red"
    info_text.append(f"Status: ", style="dim")
    info_text.append(f"{status.upper()}", style=status_color)
    
    panel = Panel(
        info_text,
        title="[bold]Backend Information[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)


def display_capabilities(health_data: Dict[str, Any]):
    """Display backend capabilities"""
    capabilities = extract_capabilities(health_data)
    
    table = Table(title="Backend Capabilities", show_header=True, header_style="bold green")
    table.add_column("Feature", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")
    
    for feature, info in capabilities.items():
        status = info.get('status', 'unknown')
        details = info.get('details', '')
        
        # Color code status
        if status in ['ready', 'available', 'active']:
            status_display = f"[green]{status.upper()}[/green]"
        elif status in ['initializing', 'pending']:
            status_display = f"[yellow]{status.upper()}[/yellow]"
        else:
            status_display = f"[red]{status.upper()}[/red]"
        
        table.add_row(feature.replace('_', ' ').title(), status_display, details)
    
    console.print(table)


def display_endpoints():
    """Display available API endpoints"""
    endpoints = get_available_endpoints()
    
    # Group endpoints by category
    categories = {}
    for endpoint, info in endpoints.items():
        category = info['category']
        if category not in categories:
            categories[category] = []
        categories[category].append((endpoint, info))
    
    for category, endpoint_list in categories.items():
        table = Table(title=f"{category} Endpoints", show_header=True, header_style="bold blue")
        table.add_column("Endpoint", style="cyan")
        table.add_column("Method", style="bold")
        table.add_column("Description", style="white")
        
        for endpoint, info in endpoint_list:
            method_color = "green" if info['method'] == 'GET' else "yellow" if info['method'] == 'POST' else "red"
            table.add_row(
                endpoint,
                f"[{method_color}]{info['method']}[/{method_color}]",
                info['description']
            )
        
        console.print(table)
        console.print()  # Add space between categories


def extract_capabilities(health_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Extract capabilities from health data"""
    capabilities = {}
    
    # AI capabilities
    ai_ready = health_data.get('ai_ready', False)
    capabilities['ai_agent'] = {
        'status': 'ready' if ai_ready else 'not_ready',
        'details': f"Framework: {health_data.get('agent_framework', 'unknown')}"
    }
    
    # Session management
    sessions = health_data.get('sessions', {})
    capabilities['session_management'] = {
        'status': 'active',
        'details': f"Active sessions: {sessions.get('active_sessions', 0)}"
    }
    
    # Event streaming
    streaming = health_data.get('event_streaming', {})
    capabilities['event_streaming'] = {
        'status': 'active',
        'details': f"Connected clients: {streaming.get('connected_clients', 0)}"
    }
    
    # WebSocket support
    capabilities['websocket_support'] = {
        'status': 'available',
        'details': 'Real-time communication enabled'
    }
    
    # AST analysis
    capabilities['ast_analysis'] = {
        'status': 'available',
        'details': 'Multi-language AST parsing and symbol extraction'
    }
    
    # Graph database
    capabilities['graph_database'] = {
        'status': 'available',
        'details': 'Neo4j integration for relationship mapping'
    }
    
    return capabilities


def get_available_endpoints() -> Dict[str, Dict[str, str]]:
    """Get list of available API endpoints"""
    return {
        # Health and info
        "/health": {
            "method": "GET",
            "category": "System",
            "description": "Backend health check and status"
        },
        "/": {
            "method": "GET", 
            "category": "System",
            "description": "Root endpoint with basic info"
        },
        
        # Session management
        "/sessions": {
            "method": "GET",
            "category": "Sessions",
            "description": "List all active agent sessions"
        },
        "/sessions/{client_id}": {
            "method": "DELETE",
            "category": "Sessions", 
            "description": "Delete a specific agent session"
        },
        "/sessions/{client_id}/state": {
            "method": "GET",
            "category": "Sessions",
            "description": "Get the state of a specific session"
        },
        
        # AST analysis
        "/ast/project/{client_id}/analysis": {
            "method": "GET",
            "category": "AST Analysis",
            "description": "Get AST-powered project analysis"
        },
        "/ast/symbols/{client_id}/{symbol_name}": {
            "method": "GET",
            "category": "AST Analysis",
            "description": "Find references to a symbol"
        },
        "/ast/complexity/{client_id}": {
            "method": "GET",
            "category": "AST Analysis", 
            "description": "Get code complexity analysis"
        },
        
        # Graph analysis
        "/graph/architecture/{client_id}": {
            "method": "GET",
            "category": "Graph Analysis",
            "description": "Detect architecture patterns"
        },
        "/graph/circular-deps/{client_id}": {
            "method": "GET",
            "category": "Graph Analysis",
            "description": "Find circular dependencies"
        },
        "/graph/coupling/{client_id}": {
            "method": "GET",
            "category": "Graph Analysis",
            "description": "Analyze coupling between components"
        },
        "/graph/hotspots/{client_id}": {
            "method": "GET",
            "category": "Graph Analysis",
            "description": "Find code hotspots"
        },
        "/graph/visualization/{client_id}": {
            "method": "GET",
            "category": "Graph Analysis",
            "description": "Generate graph visualization data"
        },
        
        # Event streaming
        "/streaming/stats": {
            "method": "GET",
            "category": "Event Streaming",
            "description": "Get event streaming service statistics"
        },
        "/streaming/clients": {
            "method": "GET",
            "category": "Event Streaming",
            "description": "Get connected streaming clients info"
        },
        "/streaming/clients/{client_id}/preferences": {
            "method": "GET",
            "category": "Event Streaming",
            "description": "Get client notification preferences"
        },
        "/streaming/test-event": {
            "method": "POST",
            "category": "Event Streaming",
            "description": "Emit a test event for debugging"
        },
        
        # Visualization
        "/visualization/types": {
            "method": "GET",
            "category": "Visualization",
            "description": "Get available diagram types"
        },
        "/visualization/{client_id}/generate": {
            "method": "POST",
            "category": "Visualization",
            "description": "Generate interactive diagram"
        },
        "/visualization/cache/stats": {
            "method": "GET",
            "category": "Visualization",
            "description": "Get visualization cache statistics"
        },
        
        # WebSocket
        "/ws/{client_id}": {
            "method": "WS",
            "category": "WebSocket",
            "description": "WebSocket endpoint for real-time communication"
        },
        
        # Reconnection
        "/reconnection/sessions": {
            "method": "GET",
            "category": "Reconnection",
            "description": "Get all client reconnection sessions"
        },
        "/reconnection/heartbeat/{client_id}": {
            "method": "POST",
            "category": "Reconnection",
            "description": "Update client heartbeat timestamp"
        }
    }