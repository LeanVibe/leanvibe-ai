"""
Health command for LeanVibe CLI

Provides comprehensive health diagnostics for MVP critical services:
- HTTP connectivity and response times
- WebSocket connectivity and bi-directional communication
- L3 agent service status and initialization
- Ollama AI service availability and model status
- End-to-end query processing validation
"""

import asyncio
import time
from typing import Dict, Any, List, Tuple, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed service diagnostics')
@click.option('--timeout', '-t', default=10, help='Timeout for health checks in seconds')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def health(ctx: click.Context, detailed: bool, timeout: int, output_json: bool):
    """Comprehensive health check for MVP critical services"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    asyncio.run(health_command(config, client, detailed, timeout, output_json))


async def health_command(config: CLIConfig, client: BackendClient, detailed: bool = False, timeout: int = 10, output_json: bool = False):
    """Execute comprehensive health check"""
    
    if not output_json:
        console.print(f"[bold cyan]🏥 LeanVibe MVP Health Check[/bold cyan]")
        console.print(f"[dim]Checking all critical services for MVP readiness...[/dim]\n")
    
    # Collect all health check results
    health_results = {}
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console if not output_json else None
        ) as progress:
            
            # Health check sequence
            checks = [
                ("http_connectivity", "Testing HTTP connectivity"),
                ("websocket_connectivity", "Testing WebSocket connectivity"),
                ("backend_services", "Checking backend services"),
                ("ai_services", "Validating AI services"),
                ("end_to_end", "Testing end-to-end query processing")
            ]
            
            for check_name, description in checks:
                if not output_json:
                    task = progress.add_task(description, total=None)
                
                start_time = time.time()
                
                if check_name == "http_connectivity":
                    result = await check_http_connectivity(client, timeout)
                elif check_name == "websocket_connectivity":
                    result = await check_websocket_connectivity(client, timeout)
                elif check_name == "backend_services":
                    result = await check_backend_services(client, timeout)
                elif check_name == "ai_services":
                    result = await check_ai_services(client, timeout)
                elif check_name == "end_to_end":
                    result = await check_end_to_end_processing(client, timeout)
                
                elapsed = time.time() - start_time
                result['response_time'] = elapsed
                health_results[check_name] = result
                
                if not output_json:
                    status_icon = "✅" if result['status'] == 'healthy' else "❌"
                    progress.update(task, description=f"{status_icon} {description} ({elapsed:.2f}s)")
    
    except Exception as e:
        health_results['error'] = str(e)
    
    # Output results
    if output_json:
        import json
        console.print(json.dumps(health_results, indent=2))
    else:
        display_health_results(health_results, config, detailed)


async def check_http_connectivity(client: BackendClient, timeout: int) -> Dict[str, Any]:
    """Test basic HTTP connectivity to backend"""
    try:
        async with client:
            start_time = time.time()
            health_data = await asyncio.wait_for(client.health_check(), timeout=timeout)
            elapsed = time.time() - start_time
            
            return {
                'status': 'healthy' if health_data.get('status') == 'healthy' else 'unhealthy',
                'response_time': elapsed,
                'backend_version': health_data.get('version', 'unknown'),
                'backend_service': health_data.get('service', 'unknown'),
                'details': health_data
            }
    except asyncio.TimeoutError:
        return {
            'status': 'timeout',
            'error': f'HTTP request timed out after {timeout}s',
            'recommendation': 'Check if backend is running and accessible'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'recommendation': 'Verify backend URL and network connectivity'
        }


async def check_websocket_connectivity(client: BackendClient, timeout: int) -> Dict[str, Any]:
    """Test WebSocket connectivity and bi-directional communication"""
    try:
        async with client:
            start_time = time.time()
            
            # Try to establish WebSocket connection
            connected = await asyncio.wait_for(client.connect_websocket(), timeout=timeout/2)
            
            if not connected:
                return {
                    'status': 'error',
                    'error': 'Failed to establish WebSocket connection',
                    'recommendation': 'Check WebSocket endpoint and firewall settings'
                }
            
            # Test bi-directional communication with a simple ping
            try:
                response = await asyncio.wait_for(
                    client.execute_command('/ping', '.'), 
                    timeout=timeout/2
                )
                elapsed = time.time() - start_time
                
                return {
                    'status': 'healthy',
                    'response_time': elapsed,
                    'websocket_connected': True,
                    'bidirectional_test': 'passed',
                    'ping_response': response.get('status', 'unknown')
                }
            except asyncio.TimeoutError:
                return {
                    'status': 'partial',
                    'websocket_connected': True,
                    'bidirectional_test': 'timeout',
                    'error': 'WebSocket connected but command timed out',
                    'recommendation': 'Backend may be slow to respond'
                }
                
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'recommendation': 'Check WebSocket support and backend configuration'
        }


async def check_backend_services(client: BackendClient, timeout: int) -> Dict[str, Any]:
    """Check backend service health and L3 agent status"""
    try:
        async with client:
            health_data = await asyncio.wait_for(client.health_check(), timeout=timeout)
            
            # Extract L3 agent and session info
            ai_ready = health_data.get('ai_ready', False)
            sessions = health_data.get('sessions', {})
            agent_framework = health_data.get('agent_framework', 'unknown')
            
            service_status = 'healthy'
            issues = []
            
            if not ai_ready:
                service_status = 'degraded'
                issues.append('AI services not ready')
            
            active_sessions = sessions.get('active_sessions', 0)
            if active_sessions < 0:  # Shouldn't happen, but check for sanity
                issues.append('Invalid session count')
            
            return {
                'status': service_status,
                'ai_ready': ai_ready,
                'agent_framework': agent_framework,
                'active_sessions': active_sessions,
                'total_requests': sessions.get('total_requests', 0),
                'avg_response_time': sessions.get('avg_response_time_ms', 0),
                'issues': issues,
                'recommendation': 'AI services initializing' if not ai_ready else None
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'recommendation': 'Backend services may not be properly initialized'
        }


async def check_ai_services(client: BackendClient, timeout: int) -> Dict[str, Any]:
    """Check AI service availability, including Ollama and model status"""
    try:
        async with client:
            # Try to get detailed service information
            health_data = await asyncio.wait_for(client.health_check(), timeout=timeout)
            
            # Look for AI/LLM specific metrics
            llm_metrics = health_data.get('llm_metrics', {})
            model_info = llm_metrics.get('model_info', {})
            performance = llm_metrics.get('performance', {})
            
            ai_status = 'healthy'
            issues = []
            model_name = model_info.get('name', 'unknown')
            model_status = model_info.get('status', 'unknown')
            
            if model_status != 'ready':
                ai_status = 'initializing' if model_status == 'initializing' else 'error'
                issues.append(f'Model status: {model_status}')
            
            # Check if we're using the expected Mistral 7B model
            if 'mistral' not in model_name.lower() and model_name != 'unknown':
                issues.append(f'Using {model_name} instead of expected Mistral 7B')
            
            # Check recent performance
            recent_speed = performance.get('recent_average_speed_tokens_per_sec', 0)
            if recent_speed > 0 and recent_speed < 10:  # Very slow generation
                issues.append(f'Slow generation speed: {recent_speed:.1f} tokens/s')
            
            return {
                'status': ai_status,
                'model_name': model_name,
                'model_status': model_status,
                'generation_speed': recent_speed,
                'memory_usage_mb': llm_metrics.get('memory', {}).get('current_usage_mb', 0),
                'total_requests': llm_metrics.get('session_metrics', {}).get('total_requests', 0),
                'issues': issues,
                'recommendation': 'Wait for model initialization' if ai_status == 'initializing' else None
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'recommendation': 'AI services may not be available or configured'
        }


async def check_end_to_end_processing(client: BackendClient, timeout: int) -> Dict[str, Any]:
    """Test end-to-end query processing to validate MVP core journey"""
    try:
        async with client:
            # Test a simple query that should complete quickly
            test_query = "What is the current directory?"
            
            start_time = time.time()
            response = await asyncio.wait_for(
                client.query_agent(test_query, workspace="."), 
                timeout=timeout
            )
            elapsed = time.time() - start_time
            
            # Analyze response quality
            status = response.get('status', 'unknown')
            message = response.get('message', '')
            confidence = response.get('confidence', 0)
            
            if status == 'success' and message and len(message) > 10:
                query_status = 'healthy'
                issues = []
            elif status == 'error':
                query_status = 'error'
                issues = [f"Query failed: {message}"]
            else:
                query_status = 'degraded'
                issues = ['Query response incomplete or low quality']
            
            # Check if response time meets MVP targets (<10s)
            if elapsed > 10:
                query_status = 'slow'
                issues.append(f'Response time {elapsed:.1f}s exceeds MVP target of <10s')
            
            return {
                'status': query_status,
                'response_time': elapsed,
                'query_status': status,
                'response_length': len(message),
                'confidence_score': confidence,
                'meets_mvp_target': elapsed < 10,
                'issues': issues,
                'recommendation': 'Optimize AI model or backend' if elapsed > 10 else None
            }
            
    except asyncio.TimeoutError:
        return {
            'status': 'timeout',
            'error': f'End-to-end query timed out after {timeout}s',
            'meets_mvp_target': False,
            'recommendation': 'Query processing is too slow for MVP requirements'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'recommendation': 'End-to-end query processing not working'
        }


def display_health_results(results: Dict[str, Any], config: CLIConfig, detailed: bool):
    """Display formatted health check results"""
    
    # Overall status
    overall_status = determine_overall_status(results)
    status_color = get_status_color(overall_status)
    status_icon = get_status_icon(overall_status)
    
    # Main status panel
    status_text = Text()
    status_text.append(f"{status_icon} ", style=status_color)
    status_text.append(f"Overall Status: {overall_status.upper()}", style=f"bold {status_color}")
    status_text.append(f"\nBackend: {config.backend_url}", style="dim")
    
    if overall_status != 'healthy':
        status_text.append(f"\n\n🔧 Issues found - see details below", style="yellow")
    
    status_panel = Panel(
        status_text,
        title="[bold]MVP Health Check Summary[/bold]",
        border_style=status_color,
        padding=(1, 2)
    )
    
    console.print(status_panel)
    console.print()
    
    # Service details table
    table = Table(title="Service Health Details", show_header=True, header_style="bold cyan")
    table.add_column("Service", style="bold", width=20)
    table.add_column("Status", width=15)
    table.add_column("Response Time", width=15)
    table.add_column("Details", style="dim")
    
    service_names = {
        'http_connectivity': 'HTTP Connectivity',
        'websocket_connectivity': 'WebSocket',
        'backend_services': 'Backend Services',
        'ai_services': 'AI Services',
        'end_to_end': 'End-to-End Query'
    }
    
    for service_key, service_name in service_names.items():
        if service_key in results:
            result = results[service_key]
            status = result.get('status', 'unknown')
            response_time = result.get('response_time', 0)
            
            status_icon = get_status_icon(status)
            status_color = get_status_color(status)
            
            # Format response time
            if response_time > 1:
                time_str = f"{response_time:.2f}s"
            else:
                time_str = f"{response_time*1000:.0f}ms"
            
            # Create details string
            details = []
            if 'error' in result:
                details.append(f"Error: {result['error']}")
            if 'issues' in result and result['issues']:
                details.append(f"Issues: {', '.join(result['issues'])}")
            if 'model_name' in result:
                details.append(f"Model: {result['model_name']}")
            if 'meets_mvp_target' in result and not result['meets_mvp_target']:
                details.append("⚠️ MVP target not met")
                
            details_str = " | ".join(details) if details else "OK"
            
            table.add_row(
                service_name,
                f"[{status_color}]{status_icon} {status}[/{status_color}]",
                time_str,
                details_str
            )
    
    console.print(table)
    
    # Show recommendations if any
    recommendations = []
    for result in results.values():
        if isinstance(result, dict) and result.get('recommendation'):
            recommendations.append(result['recommendation'])
    
    if recommendations:
        console.print()
        rec_text = Text()
        rec_text.append("💡 Recommendations:\n", style="bold yellow")
        for i, rec in enumerate(recommendations, 1):
            rec_text.append(f"{i}. {rec}\n", style="yellow")
        
        rec_panel = Panel(
            rec_text,
            title="[bold yellow]Recommendations[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(rec_panel)
    
    # Detailed information if requested
    if detailed:
        display_detailed_health_info(results)


def display_detailed_health_info(results: Dict[str, Any]):
    """Display detailed health information"""
    console.print()
    console.print("[bold]Detailed Health Information[/bold]")
    
    for service_key, result in results.items():
        if isinstance(result, dict) and service_key != 'error':
            console.print(f"\n[bold cyan]{service_key.replace('_', ' ').title()}:[/bold cyan]")
            
            # Create a details table for this service
            details_table = Table(show_header=False, box=None, padding=(0, 2))
            details_table.add_column("Property", style="dim")
            details_table.add_column("Value")
            
            for key, value in result.items():
                if key not in ['status', 'response_time']:  # Skip already shown info
                    if isinstance(value, (int, float)):
                        if key.endswith('_time') or key.endswith('response_time'):
                            if value < 1:
                                value_str = f"{value*1000:.0f}ms"
                            else:
                                value_str = f"{value:.2f}s"
                        elif key.endswith('_mb'):
                            value_str = f"{value:.0f}MB"
                        else:
                            value_str = str(value)
                    elif isinstance(value, list):
                        value_str = ", ".join(str(v) for v in value)
                    else:
                        value_str = str(value)
                    
                    details_table.add_row(key.replace('_', ' ').title(), value_str)
            
            console.print(details_table)


def determine_overall_status(results: Dict[str, Any]) -> str:
    """Determine overall health status from individual service results"""
    if 'error' in results:
        return 'error'
    
    statuses = []
    for result in results.values():
        if isinstance(result, dict):
            statuses.append(result.get('status', 'unknown'))
    
    if not statuses:
        return 'unknown'
    
    # Priority: error > timeout > slow > degraded > partial > initializing > healthy
    if 'error' in statuses:
        return 'error'
    elif 'timeout' in statuses:
        return 'timeout'
    elif 'slow' in statuses:
        return 'slow'
    elif 'degraded' in statuses or 'unhealthy' in statuses:
        return 'degraded'
    elif 'partial' in statuses:
        return 'partial'
    elif 'initializing' in statuses:
        return 'initializing'
    elif all(s == 'healthy' for s in statuses):
        return 'healthy'
    else:
        return 'mixed'


def get_status_color(status: str) -> str:
    """Get color for status display"""
    colors = {
        'healthy': 'green',
        'initializing': 'yellow',
        'partial': 'yellow',
        'degraded': 'orange',
        'slow': 'orange',
        'timeout': 'red',
        'error': 'red',
        'mixed': 'yellow'
    }
    return colors.get(status, 'white')


def get_status_icon(status: str) -> str:
    """Get icon for status display"""
    icons = {
        'healthy': '✅',
        'initializing': '🟡',
        'partial': '🟡',
        'degraded': '🟠',
        'slow': '🐌',
        'timeout': '⏰',
        'error': '❌',
        'mixed': '🔶'
    }
    return icons.get(status, '❓')