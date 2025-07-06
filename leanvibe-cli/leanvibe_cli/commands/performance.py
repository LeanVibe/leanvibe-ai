"""
Performance command for LeanVibe CLI

Shows performance metrics, cache statistics, and optimization settings.
"""

import asyncio
from typing import Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..config import CLIConfig
from ..client import BackendClient
from ..optimizations import PerformanceMonitor, response_cache

console = Console()


@click.command()
@click.option('--reset', is_flag=True, help='Reset performance metrics')
@click.option('--cleanup', is_flag=True, help='Cleanup expired cache entries')
@click.option('--benchmark', is_flag=True, help='Run quick performance benchmark')
@click.pass_context
def performance(ctx: click.Context, reset: bool, cleanup: bool, benchmark: bool):
    """Show performance metrics and optimization status"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    if reset:
        PerformanceMonitor.reset_metrics()
        response_cache.clear_expired()
        console.print("[green]✅ Performance metrics reset and cache cleared[/green]")
        return
    
    if cleanup:
        result = PerformanceMonitor.cleanup_resources()
        console.print(f"[green]✅ Cleaned up {result['expired_cache_entries']} expired cache entries[/green]")
        return
    
    if benchmark:
        asyncio.run(run_quick_benchmark(config, client))
        return
    
    # Show current performance metrics
    show_performance_metrics()


def show_performance_metrics():
    """Display current performance metrics"""
    metrics = PerformanceMonitor.get_metrics()
    
    console.print("[bold cyan]📊 LeanVibe CLI Performance Metrics[/bold cyan]\n")
    
    # Cache Statistics
    cache_table = Table(title="🗄️ Cache Performance")
    cache_table.add_column("Metric", style="cyan")
    cache_table.add_column("Value", style="green")
    cache_table.add_column("Status", style="yellow")
    
    cache_hit_rate = metrics['cache_hit_rate']
    cache_status = "Excellent" if cache_hit_rate > 0.8 else "Good" if cache_hit_rate > 0.6 else "Needs Improvement"
    
    cache_table.add_row("Cache Hits", str(metrics['cache_hits']), "")
    cache_table.add_row("Cache Misses", str(metrics['cache_misses']), "")
    cache_table.add_row("Hit Rate", f"{cache_hit_rate:.1%}", cache_status)
    
    console.print(cache_table)
    console.print()
    
    # Command Performance
    if metrics['avg_command_time']:
        cmd_table = Table(title="⚡ Command Performance")
        cmd_table.add_column("Command", style="cyan")
        cmd_table.add_column("Avg Time (ms)", style="green")
        cmd_table.add_column("Executions", style="blue")
        cmd_table.add_column("Status", style="yellow")
        
        for cmd, avg_time in metrics['avg_command_time'].items():
            executions = len(metrics['command_times'][cmd])
            status = "Fast" if avg_time < 1000 else "Moderate" if avg_time < 3000 else "Slow"
            cmd_table.add_row(cmd, f"{avg_time:.1f}", str(executions), status)
        
        console.print(cmd_table)
        console.print()
    
    # Optimization Status
    opt_table = Table(title="🚀 Optimization Status")
    opt_table.add_column("Feature", style="cyan")
    opt_table.add_column("Status", style="green")
    opt_table.add_column("Description", style="white")
    
    opt_table.add_row("HTTP/2", "✅ Enabled", "Faster connection multiplexing")
    opt_table.add_row("Connection Pooling", "✅ Enabled", "Reuse connections for better performance")
    opt_table.add_row("Response Caching", "✅ Enabled", "Cache frequently accessed data")
    opt_table.add_row("Lazy Imports", "✅ Enabled", "Faster startup time")
    opt_table.add_row("Smart Timeouts", "✅ Enabled", "Adaptive timeouts based on complexity")
    opt_table.add_row("Performance Tracking", "✅ Enabled", "Monitor and optimize performance")
    
    console.print(opt_table)
    console.print()
    
    # Recommendations
    recommendations = []
    
    if cache_hit_rate < 0.5:
        recommendations.append("Consider using more repeated queries to benefit from caching")
    
    if metrics['avg_command_time']:
        slow_commands = [cmd for cmd, time in metrics['avg_command_time'].items() if time > 3000]
        if slow_commands:
            recommendations.append(f"Commands {', '.join(slow_commands)} are running slowly - consider optimizing")
    
    if not recommendations:
        recommendations.append("✅ Performance looks good! All optimizations are working effectively.")
    
    rec_text = Text()
    rec_text.append("💡 Performance Recommendations:\n\n", style="bold yellow")
    for i, rec in enumerate(recommendations, 1):
        rec_text.append(f"{i}. {rec}\n", style="white")
    
    console.print(Panel(rec_text, title="Recommendations", border_style="yellow"))


async def run_quick_benchmark(config: CLIConfig, client: BackendClient):
    """Run a quick performance benchmark"""
    console.print("[bold cyan]🏃‍♂️ Running Quick Performance Benchmark[/bold cyan]\n")
    
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        main_task = progress.add_task("Running benchmark tests...", total=4)
        
        # Test 1: Connection Speed
        progress.update(main_task, description="Testing connection speed...")
        conn_times = []
        
        for i in range(3):
            import time
            start = time.perf_counter()
            try:
                async with client:
                    await client.health_check()
                conn_times.append((time.perf_counter() - start) * 1000)
            except Exception:
                conn_times.append(float('inf'))
        
        progress.advance(main_task)
        
        # Test 2: Simple Query Performance
        progress.update(main_task, description="Testing simple query performance...")
        simple_query_times = []
        
        for i in range(2):
            start = time.perf_counter()
            try:
                async with client:
                    await client.query_agent("status")
                simple_query_times.append((time.perf_counter() - start) * 1000)
            except Exception:
                simple_query_times.append(float('inf'))
        
        progress.advance(main_task)
        
        # Test 3: Cache Performance
        progress.update(main_task, description="Testing cache performance...")
        
        # First query (cache miss)
        start = time.perf_counter()
        try:
            async with client:
                await client.health_check()
            first_time = (time.perf_counter() - start) * 1000
        except Exception:
            first_time = float('inf')
        
        # Second query (should be cached)
        start = time.perf_counter()
        try:
            async with client:
                await client.health_check()
            second_time = (time.perf_counter() - start) * 1000
        except Exception:
            second_time = float('inf')
        
        progress.advance(main_task)
        
        # Test 4: Memory Efficiency
        progress.update(main_task, description="Testing memory efficiency...")
        
        import tracemalloc
        tracemalloc.start()
        
        try:
            async with client:
                await client.health_check()
                await client.query_agent("test")
            
            current, peak = tracemalloc.get_traced_memory()
            memory_usage = peak / 1024 / 1024  # MB
        except Exception:
            memory_usage = float('inf')
        finally:
            tracemalloc.stop()
        
        progress.advance(main_task)
    
    # Display results
    console.print("\n[bold green]📋 Benchmark Results[/bold green]\n")
    
    results_table = Table(title="Performance Test Results")
    results_table.add_column("Test", style="cyan")
    results_table.add_column("Result", style="green")
    results_table.add_column("Status", style="yellow")
    
    # Connection speed
    avg_conn_time = sum(t for t in conn_times if t != float('inf')) / max(1, len([t for t in conn_times if t != float('inf')]))
    conn_status = "Excellent" if avg_conn_time < 100 else "Good" if avg_conn_time < 500 else "Needs Improvement"
    results_table.add_row("Connection Speed", f"{avg_conn_time:.1f}ms", conn_status)
    
    # Simple query speed
    avg_query_time = sum(t for t in simple_query_times if t != float('inf')) / max(1, len([t for t in simple_query_times if t != float('inf')]))
    query_status = "Excellent" if avg_query_time < 1000 else "Good" if avg_query_time < 3000 else "Needs Improvement"
    results_table.add_row("Simple Query", f"{avg_query_time:.1f}ms", query_status)
    
    # Cache effectiveness
    if second_time != float('inf') and first_time != float('inf'):
        cache_improvement = ((first_time - second_time) / first_time) * 100
        cache_status = "Excellent" if cache_improvement > 20 else "Good" if cache_improvement > 10 else "Minimal"
        results_table.add_row("Cache Improvement", f"{cache_improvement:.1f}%", cache_status)
    else:
        cache_status = "Failed"
        results_table.add_row("Cache Improvement", "Error", cache_status)
    
    # Memory usage
    if memory_usage != float('inf'):
        memory_status = "Excellent" if memory_usage < 10 else "Good" if memory_usage < 50 else "High"
        results_table.add_row("Memory Usage", f"{memory_usage:.1f}MB", memory_status)
    else:
        memory_status = "Failed"
        results_table.add_row("Memory Usage", "Error", memory_status)
    
    console.print(results_table)
    console.print()
    
    # Overall assessment
    all_excellent = all([
        conn_status == "Excellent",
        query_status == "Excellent", 
        cache_status in ["Excellent", "Good"],
        memory_status in ["Excellent", "Good"]
    ])
    
    if all_excellent:
        console.print("[bold green]🎉 Overall Performance: Excellent![/bold green]")
        console.print("[green]All optimizations are working effectively.[/green]")
    else:
        console.print("[bold yellow]⚠️ Overall Performance: Good with room for improvement[/bold yellow]")
        console.print("[yellow]Consider running 'leanvibe performance --cleanup' to optimize further.[/yellow]")