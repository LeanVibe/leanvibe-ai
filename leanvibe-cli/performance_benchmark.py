#!/usr/bin/env python3
"""
LeanVibe CLI Performance Benchmark and Optimization Tool

Measures and optimizes CLI performance metrics:
- Command execution time
- Memory usage
- Network response times
- Connection establishment
- Data serialization/deserialization
"""

import asyncio
import time
import sys
import tracemalloc
import statistics
from typing import Dict, List, Any, Tuple
from pathlib import Path
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Add CLI modules to path
sys.path.insert(0, str(Path(__file__).parent / "leanvibe_cli"))

from leanvibe_cli.config import CLIConfig, load_config
from leanvibe_cli.client import BackendClient

console = Console()

class PerformanceBenchmark:
    """Performance benchmarking suite for LeanVibe CLI"""
    
    def __init__(self):
        self.config = load_config()
        self.results = {}
        
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite"""
        
        console.print("[bold cyan]🚀 LeanVibe CLI Performance Benchmark Suite[/bold cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            main_task = progress.add_task("Running benchmarks...", total=6)
            
            # 1. Connection Performance
            progress.update(main_task, description="Testing connection performance...")
            self.results['connection'] = await self._benchmark_connection()
            progress.advance(main_task)
            
            # 2. Command Execution Performance
            progress.update(main_task, description="Testing command execution...")
            self.results['commands'] = await self._benchmark_commands()
            progress.advance(main_task)
            
            # 3. Query Performance
            progress.update(main_task, description="Testing query performance...")
            self.results['queries'] = await self._benchmark_queries()
            progress.advance(main_task)
            
            # 4. WebSocket Performance
            progress.update(main_task, description="Testing WebSocket performance...")
            self.results['websocket'] = await self._benchmark_websocket()
            progress.advance(main_task)
            
            # 5. Memory Usage
            progress.update(main_task, description="Testing memory usage...")
            self.results['memory'] = await self._benchmark_memory()
            progress.advance(main_task)
            
            # 6. Configuration Loading
            progress.update(main_task, description="Testing configuration loading...")
            self.results['config'] = await self._benchmark_config()
            progress.advance(main_task)
        
        # Display results
        self._display_results()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        self._display_recommendations(recommendations)
        
        return self.results
    
    async def _benchmark_connection(self) -> Dict[str, Any]:
        """Benchmark backend connection performance"""
        results = {
            'http_connection_times': [],
            'websocket_connection_times': [],
            'health_check_times': [],
            'failed_connections': 0
        }
        
        num_tests = 5
        
        for i in range(num_tests):
            async with BackendClient(self.config) as client:
                try:
                    # HTTP connection time
                    start_time = time.perf_counter()
                    await client.health_check()
                    http_time = (time.perf_counter() - start_time) * 1000
                    results['http_connection_times'].append(http_time)
                    
                    # WebSocket connection time
                    start_time = time.perf_counter()
                    await client.connect_websocket()
                    ws_time = (time.perf_counter() - start_time) * 1000
                    results['websocket_connection_times'].append(ws_time)
                    
                    # Health check time
                    start_time = time.perf_counter()
                    health = await client.health_check()
                    health_time = (time.perf_counter() - start_time) * 1000
                    results['health_check_times'].append(health_time)
                    
                except Exception:
                    results['failed_connections'] += 1
        
        # Calculate statistics
        for key in ['http_connection_times', 'websocket_connection_times', 'health_check_times']:
            if results[key]:
                times = results[key]
                results[f'{key}_avg'] = statistics.mean(times)
                results[f'{key}_min'] = min(times)
                results[f'{key}_max'] = max(times)
                results[f'{key}_std'] = statistics.stdev(times) if len(times) > 1 else 0
        
        return results
    
    async def _benchmark_commands(self) -> Dict[str, Any]:
        """Benchmark CLI command execution performance"""
        
        commands = [
            ('status', []),
            ('sessions', []),
            ('monitoring', []),
        ]
        
        results = {}
        
        for cmd_name, args in commands:
            cmd_times = []
            memory_usage = []
            
            for _ in range(3):  # Test each command 3 times
                tracemalloc.start()
                start_time = time.perf_counter()
                
                try:
                    # Simulate command execution time (actual commands would be called via subprocess)
                    async with BackendClient(self.config) as client:
                        if cmd_name == 'status':
                            await client.health_check()
                        elif cmd_name == 'sessions':
                            await client.get_sessions()
                        elif cmd_name == 'monitoring':
                            await client.get_streaming_stats()
                    
                    exec_time = (time.perf_counter() - start_time) * 1000
                    cmd_times.append(exec_time)
                    
                    # Memory usage
                    current, peak = tracemalloc.get_traced_memory()
                    memory_usage.append(peak / 1024 / 1024)  # MB
                    
                except Exception as e:
                    console.print(f"[yellow]Command {cmd_name} failed: {e}[/yellow]")
                
                tracemalloc.stop()
            
            if cmd_times:
                results[cmd_name] = {
                    'avg_time_ms': statistics.mean(cmd_times),
                    'min_time_ms': min(cmd_times),
                    'max_time_ms': max(cmd_times),
                    'avg_memory_mb': statistics.mean(memory_usage),
                    'max_memory_mb': max(memory_usage)
                }
        
        return results
    
    async def _benchmark_queries(self) -> Dict[str, Any]:
        """Benchmark query performance"""
        
        test_queries = [
            "what is the status?",
            "analyze project structure", 
            "show performance metrics",
            "list active sessions"
        ]
        
        results = {
            'query_times': [],
            'query_success_rate': 0,
            'avg_response_size': 0
        }
        
        successful_queries = 0
        response_sizes = []
        
        async with BackendClient(self.config) as client:
            for query in test_queries:
                try:
                    start_time = time.perf_counter()
                    response = await client.query_agent(query)
                    query_time = (time.perf_counter() - start_time) * 1000
                    
                    results['query_times'].append(query_time)
                    response_sizes.append(len(json.dumps(response)))
                    successful_queries += 1
                    
                except Exception as e:
                    console.print(f"[yellow]Query failed: {e}[/yellow]")
        
        if results['query_times']:
            results['avg_query_time_ms'] = statistics.mean(results['query_times'])
            results['min_query_time_ms'] = min(results['query_times'])
            results['max_query_time_ms'] = max(results['query_times'])
        
        results['query_success_rate'] = successful_queries / len(test_queries)
        results['avg_response_size'] = statistics.mean(response_sizes) if response_sizes else 0
        
        return results
    
    async def _benchmark_websocket(self) -> Dict[str, Any]:
        """Benchmark WebSocket performance"""
        
        results = {
            'connection_time_ms': 0,
            'message_roundtrip_times': [],
            'heartbeat_times': [],
            'connection_stable': True
        }
        
        async with BackendClient(self.config) as client:
            try:
                # Connection time
                start_time = time.perf_counter()
                connected = await client.connect_websocket()
                results['connection_time_ms'] = (time.perf_counter() - start_time) * 1000
                
                if connected:
                    # Heartbeat test
                    for _ in range(3):
                        start_time = time.perf_counter()
                        success = await client.send_heartbeat()
                        if success:
                            heartbeat_time = (time.perf_counter() - start_time) * 1000
                            results['heartbeat_times'].append(heartbeat_time)
                    
                    # Message roundtrip test
                    test_messages = ["test message 1", "test message 2", "test message 3"]
                    for msg in test_messages:
                        try:
                            start_time = time.perf_counter()
                            response = await client.send_message(msg)
                            roundtrip_time = (time.perf_counter() - start_time) * 1000
                            results['message_roundtrip_times'].append(roundtrip_time)
                        except Exception:
                            results['connection_stable'] = False
                
            except Exception as e:
                console.print(f"[yellow]WebSocket benchmark failed: {e}[/yellow]")
                results['connection_stable'] = False
        
        # Calculate averages
        if results['heartbeat_times']:
            results['avg_heartbeat_time_ms'] = statistics.mean(results['heartbeat_times'])
        if results['message_roundtrip_times']:
            results['avg_roundtrip_time_ms'] = statistics.mean(results['message_roundtrip_times'])
        
        return results
    
    async def _benchmark_memory(self) -> Dict[str, Any]:
        """Benchmark memory usage patterns"""
        
        tracemalloc.start()
        
        # Test different operations
        async with BackendClient(self.config) as client:
            # Baseline
            baseline_current, baseline_peak = tracemalloc.get_traced_memory()
            
            # After connection
            await client.health_check()
            conn_current, conn_peak = tracemalloc.get_traced_memory()
            
            # After queries
            await client.query_agent("test query")
            query_current, query_peak = tracemalloc.get_traced_memory()
            
            # After WebSocket
            await client.connect_websocket()
            ws_current, ws_peak = tracemalloc.get_traced_memory()
        
        tracemalloc.stop()
        
        return {
            'baseline_memory_mb': baseline_peak / 1024 / 1024,
            'connection_memory_mb': conn_peak / 1024 / 1024,
            'query_memory_mb': query_peak / 1024 / 1024,
            'websocket_memory_mb': ws_peak / 1024 / 1024,
            'memory_growth_mb': (ws_peak - baseline_peak) / 1024 / 1024
        }
    
    async def _benchmark_config(self) -> Dict[str, Any]:
        """Benchmark configuration loading performance"""
        
        config_times = []
        
        for _ in range(10):
            start_time = time.perf_counter()
            config = load_config()
            load_time = (time.perf_counter() - start_time) * 1000
            config_times.append(load_time)
        
        return {
            'avg_load_time_ms': statistics.mean(config_times),
            'min_load_time_ms': min(config_times),
            'max_load_time_ms': max(config_times)
        }
    
    def _display_results(self):
        """Display benchmark results in formatted tables"""
        
        console.print("\n[bold green]📊 Performance Benchmark Results[/bold green]\n")
        
        # Connection Performance
        if 'connection' in self.results:
            conn = self.results['connection']
            table = Table(title="🔌 Connection Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Average (ms)", style="green")
            table.add_column("Min (ms)", style="blue")
            table.add_column("Max (ms)", style="red")
            
            if 'http_connection_times_avg' in conn:
                table.add_row("HTTP Connection", f"{conn['http_connection_times_avg']:.1f}", 
                            f"{conn['http_connection_times_min']:.1f}", f"{conn['http_connection_times_max']:.1f}")
            if 'websocket_connection_times_avg' in conn:
                table.add_row("WebSocket Connection", f"{conn['websocket_connection_times_avg']:.1f}",
                            f"{conn['websocket_connection_times_min']:.1f}", f"{conn['websocket_connection_times_max']:.1f}")
            if 'health_check_times_avg' in conn:
                table.add_row("Health Check", f"{conn['health_check_times_avg']:.1f}",
                            f"{conn['health_check_times_min']:.1f}", f"{conn['health_check_times_max']:.1f}")
            
            console.print(table)
            console.print()
        
        # Command Performance
        if 'commands' in self.results:
            table = Table(title="⚡ Command Performance")
            table.add_column("Command", style="cyan")
            table.add_column("Avg Time (ms)", style="green")
            table.add_column("Memory (MB)", style="yellow")
            
            for cmd, stats in self.results['commands'].items():
                table.add_row(cmd, f"{stats['avg_time_ms']:.1f}", f"{stats['avg_memory_mb']:.1f}")
            
            console.print(table)
            console.print()
        
        # Query Performance
        if 'queries' in self.results:
            queries = self.results['queries']
            table = Table(title="🤖 Query Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            if 'avg_query_time_ms' in queries:
                table.add_row("Average Query Time (ms)", f"{queries['avg_query_time_ms']:.1f}")
                table.add_row("Min Query Time (ms)", f"{queries['min_query_time_ms']:.1f}")
                table.add_row("Max Query Time (ms)", f"{queries['max_query_time_ms']:.1f}")
            table.add_row("Success Rate", f"{queries['query_success_rate']:.1%}")
            table.add_row("Avg Response Size (bytes)", f"{queries['avg_response_size']:.0f}")
            
            console.print(table)
            console.print()
        
        # Memory Usage
        if 'memory' in self.results:
            memory = self.results['memory']
            table = Table(title="💾 Memory Usage")
            table.add_column("Operation", style="cyan")
            table.add_column("Memory (MB)", style="green")
            
            table.add_row("Baseline", f"{memory['baseline_memory_mb']:.1f}")
            table.add_row("After Connection", f"{memory['connection_memory_mb']:.1f}")
            table.add_row("After Query", f"{memory['query_memory_mb']:.1f}")
            table.add_row("After WebSocket", f"{memory['websocket_memory_mb']:.1f}")
            table.add_row("Total Growth", f"{memory['memory_growth_mb']:.1f}")
            
            console.print(table)
            console.print()
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on results"""
        
        recommendations = []
        
        # Connection performance
        if 'connection' in self.results:
            conn = self.results['connection']
            if conn.get('http_connection_times_avg', 0) > 1000:
                recommendations.append("🔌 HTTP connections are slow (>1s). Consider connection pooling or reducing timeout.")
            if conn.get('websocket_connection_times_avg', 0) > 2000:
                recommendations.append("🔌 WebSocket connections are slow (>2s). Check network configuration.")
            if conn.get('failed_connections', 0) > 0:
                recommendations.append("🔌 Connection failures detected. Verify backend is running and accessible.")
        
        # Command performance
        if 'commands' in self.results:
            for cmd, stats in self.results['commands'].items():
                if stats.get('avg_time_ms', 0) > 5000:
                    recommendations.append(f"⚡ Command '{cmd}' is slow (>{stats['avg_time_ms']:.0f}ms). Consider caching or optimization.")
                if stats.get('avg_memory_mb', 0) > 50:
                    recommendations.append(f"💾 Command '{cmd}' uses high memory ({stats['avg_memory_mb']:.1f}MB). Consider memory optimization.")
        
        # Query performance
        if 'queries' in self.results:
            queries = self.results['queries']
            if queries.get('avg_query_time_ms', 0) > 3000:
                recommendations.append("🤖 Query responses are slow (>3s). Consider optimizing AI model or backend processing.")
            if queries.get('query_success_rate', 1) < 0.8:
                recommendations.append("🤖 Low query success rate. Check AI service stability and error handling.")
        
        # Memory usage
        if 'memory' in self.results:
            memory = self.results['memory']
            if memory.get('memory_growth_mb', 0) > 100:
                recommendations.append("💾 High memory growth detected. Investigate potential memory leaks.")
            if memory.get('websocket_memory_mb', 0) > 200:
                recommendations.append("💾 WebSocket operations use high memory. Consider optimizing message handling.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ Performance looks good! All metrics are within acceptable ranges.")
        
        return recommendations
    
    def _display_recommendations(self, recommendations: List[str]):
        """Display performance recommendations"""
        
        console.print("[bold yellow]💡 Performance Recommendations[/bold yellow]\n")
        
        for i, rec in enumerate(recommendations, 1):
            console.print(f"{i}. {rec}")
        
        console.print()


async def main():
    """Run the performance benchmark"""
    
    try:
        benchmark = PerformanceBenchmark()
        results = await benchmark.run_all_benchmarks()
        
        # Save results to file
        results_file = Path("performance_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        console.print(f"[green]📁 Results saved to: {results_file}[/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Benchmark failed: {e}[/red]")
        console.print("[dim]Make sure the backend is running at http://localhost:8000[/dim]")


if __name__ == "__main__":
    asyncio.run(main())