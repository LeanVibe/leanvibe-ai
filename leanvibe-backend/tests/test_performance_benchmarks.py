"""
Performance Benchmarking Suite for LeanVibe MVP

Tests performance characteristics under various load conditions to validate
production readiness and identify optimization opportunities.
"""

import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import pytest

from app.agent.l3_coding_agent import L3CodingAgent, AgentDependencies


class PerformanceBenchmarks:
    """Comprehensive performance benchmarking for MVP validation"""
    
    def __init__(self):
        self.results = {}
        
    async def run_all_benchmarks(self):
        """Run complete performance benchmark suite"""
        print("🏁 Starting LeanVibe Performance Benchmarks")
        print("=" * 60)
        
        # Benchmark 1: Agent initialization
        await self.benchmark_agent_initialization()
        
        # Benchmark 2: Query response times
        await self.benchmark_query_performance()
        
        # Benchmark 3: Concurrent users
        await self.benchmark_concurrent_users()
        
        # Benchmark 4: Memory usage
        await self.benchmark_memory_usage()
        
        # Benchmark 5: Sustained load
        await self.benchmark_sustained_load()
        
        # Generate performance report
        self.generate_performance_report()
        
    async def benchmark_agent_initialization(self):
        """Benchmark L3 agent initialization times"""
        print("\n1. 🚀 Agent Initialization Benchmark")
        
        init_times = []
        
        for i in range(10):
            dependencies = AgentDependencies(
                workspace_path=".",
                client_id=f"benchmark_client_{i}",
                session_data={}
            )
            
            start_time = time.time()
            agent = L3CodingAgent(dependencies)
            success = await agent.initialize()
            end_time = time.time()
            
            if success:
                init_time = end_time - start_time
                init_times.append(init_time)
                print(f"   Init {i+1}: {init_time:.3f}s")
            else:
                print(f"   Init {i+1}: FAILED")
        
        if init_times:
            avg_time = statistics.mean(init_times)
            min_time = min(init_times)
            max_time = max(init_times)
            
            self.results['initialization'] = {
                'average_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'target_met': avg_time < 5.0,  # Target <5s
                'samples': len(init_times)
            }
            
            print(f"   Average: {avg_time:.3f}s (target <5s: {'✅' if avg_time < 5.0 else '❌'})")
            print(f"   Range: {min_time:.3f}s - {max_time:.3f}s")
    
    async def benchmark_query_performance(self):
        """Benchmark query response times for different query types"""
        print("\n2. 🧠 Query Performance Benchmark")
        
        # Create agent for testing
        dependencies = AgentDependencies(workspace_path=".", client_id="perf_test")
        agent = L3CodingAgent(dependencies)
        await agent.initialize()
        
        query_types = {
            'simple': [
                "What is the current directory?",
                "List files in current directory",
                "Hello, how are you?"
            ],
            'medium': [
                "What are the main Python files in this project?",
                "How do I optimize Python code?",
                "Explain object-oriented programming"
            ],
            'complex': [
                "Analyze the architecture of this codebase and provide recommendations",
                "What are the best practices for designing scalable microservices?",
                "Explain the differences between various Python web frameworks"
            ]
        }
        
        performance_results = {}
        
        for query_type, queries in query_types.items():
            print(f"\n   Testing {query_type} queries:")
            times = []
            
            for query in queries:
                start_time = time.time()
                response = await agent._process_user_input(query)
                end_time = time.time()
                
                response_time = end_time - start_time
                times.append(response_time)
                
                status = "✅" if response and len(response) > 10 else "❌"
                print(f"     {query[:40]}... : {response_time:.2f}s {status}")
            
            if times:
                avg_time = statistics.mean(times)
                performance_results[query_type] = {
                    'average_time': avg_time,
                    'min_time': min(times),
                    'max_time': max(times),
                    'target_met': avg_time < 10.0,  # Target <10s
                    'samples': len(times)
                }
                
                print(f"   {query_type.title()} average: {avg_time:.2f}s (target <10s: {'✅' if avg_time < 10.0 else '❌'})")
        
        self.results['query_performance'] = performance_results
    
    async def benchmark_concurrent_users(self):
        """Benchmark performance with multiple concurrent users"""
        print("\n3. 👥 Concurrent Users Benchmark")
        
        async def simulate_user(user_id: int):
            """Simulate a single user session"""
            dependencies = AgentDependencies(
                workspace_path=".",
                client_id=f"concurrent_user_{user_id}",
                session_data={}
            )
            
            agent = L3CodingAgent(dependencies)
            await agent.initialize()
            
            # Each user asks 3 questions
            queries = [
                "What is Python?",
                "List the current directory files",
                "How do I write a function?"
            ]
            
            user_times = []
            for query in queries:
                start_time = time.time()
                response = await agent._process_user_input(query)
                end_time = time.time()
                
                if response and len(response) > 10:
                    user_times.append(end_time - start_time)
            
            return {
                'user_id': user_id,
                'queries_completed': len(user_times),
                'average_time': statistics.mean(user_times) if user_times else 0,
                'total_time': sum(user_times)
            }
        
        # Test with 2, 3, and 5 concurrent users
        for num_users in [2, 3, 5]:
            print(f"\n   Testing {num_users} concurrent users:")
            
            start_time = time.time()
            
            # Run concurrent user sessions
            tasks = [simulate_user(i) for i in range(num_users)]
            user_results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Analyze results
            successful_users = [r for r in user_results if r['queries_completed'] > 0]
            avg_user_time = statistics.mean([r['average_time'] for r in successful_users]) if successful_users else 0
            
            concurrency_result = {
                'num_users': num_users,
                'successful_users': len(successful_users),
                'total_duration': total_duration,
                'average_user_response_time': avg_user_time,
                'target_met': avg_user_time < 15.0,  # Relaxed target for concurrent users
            }
            
            self.results.setdefault('concurrent_users', {})[num_users] = concurrency_result
            
            print(f"     Success rate: {len(successful_users)}/{num_users} users")
            print(f"     Average response: {avg_user_time:.2f}s")
            print(f"     Total duration: {total_duration:.2f}s")
    
    async def benchmark_memory_usage(self):
        """Monitor memory usage during operations"""
        print("\n4. 💾 Memory Usage Benchmark")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create agent and measure memory increase
        dependencies = AgentDependencies(workspace_path=".", client_id="memory_test")
        agent = L3CodingAgent(dependencies)
        await agent.initialize()
        
        post_init_memory = process.memory_info().rss / 1024 / 1024
        
        # Process several queries and measure memory
        queries = [
            "What is machine learning?",
            "Explain Python decorators",
            "How do I optimize database queries?",
            "What are design patterns?",
            "Analyze this codebase structure"
        ]
        
        memory_samples = []
        for query in queries:
            await agent._process_user_input(query)
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
        
        max_memory = max(memory_samples)
        avg_memory = statistics.mean(memory_samples)
        
        self.results['memory_usage'] = {
            'baseline_mb': baseline_memory,
            'post_init_mb': post_init_memory,
            'max_usage_mb': max_memory,
            'average_usage_mb': avg_memory,
            'memory_increase_mb': max_memory - baseline_memory,
            'target_met': max_memory < 500  # Target <500MB
        }
        
        print(f"   Baseline: {baseline_memory:.1f}MB")
        print(f"   Post-init: {post_init_memory:.1f}MB")
        print(f"   Peak usage: {max_memory:.1f}MB")
        print(f"   Target <500MB: {'✅' if max_memory < 500 else '❌'}")
    
    async def benchmark_sustained_load(self):
        """Test performance under sustained load"""
        print("\n5. ⏱️ Sustained Load Benchmark")
        
        dependencies = AgentDependencies(workspace_path=".", client_id="sustained_test")
        agent = L3CodingAgent(dependencies)
        await agent.initialize()
        
        # Run queries for 2 minutes
        queries = [
            "What is Python?",
            "How do I handle errors?",
            "Explain list comprehensions",
            "What are lambda functions?",
            "How do I use decorators?"
        ]
        
        start_time = time.time()
        response_times = []
        query_count = 0
        
        while time.time() - start_time < 120:  # 2 minutes
            query = queries[query_count % len(queries)]
            
            query_start = time.time()
            response = await agent._process_user_input(query)
            query_end = time.time()
            
            if response and len(response) > 10:
                response_times.append(query_end - query_start)
            
            query_count += 1
            
            # Small delay between queries
            await asyncio.sleep(1)
        
        total_duration = time.time() - start_time
        
        if response_times:
            avg_response = statistics.mean(response_times)
            throughput = len(response_times) / total_duration * 60  # queries per minute
            
            self.results['sustained_load'] = {
                'duration_seconds': total_duration,
                'total_queries': query_count,
                'successful_queries': len(response_times),
                'average_response_time': avg_response,
                'throughput_per_minute': throughput,
                'performance_degradation': avg_response > 15.0  # Flag if >15s average
            }
            
            print(f"   Duration: {total_duration:.1f}s")
            print(f"   Queries: {len(response_times)}/{query_count} successful")
            print(f"   Average response: {avg_response:.2f}s")
            print(f"   Throughput: {throughput:.1f} queries/minute")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE BENCHMARK REPORT")
        print("=" * 60)
        
        # Overall MVP readiness assessment
        mvp_ready = True
        issues = []
        
        # Check initialization performance
        if 'initialization' in self.results:
            init = self.results['initialization']
            if not init['target_met']:
                mvp_ready = False
                issues.append(f"Slow initialization: {init['average_time']:.2f}s (target <5s)")
        
        # Check query performance
        if 'query_performance' in self.results:
            for query_type, perf in self.results['query_performance'].items():
                if not perf['target_met']:
                    mvp_ready = False
                    issues.append(f"Slow {query_type} queries: {perf['average_time']:.2f}s (target <10s)")
        
        # Check memory usage
        if 'memory_usage' in self.results:
            mem = self.results['memory_usage']
            if not mem['target_met']:
                mvp_ready = False
                issues.append(f"High memory usage: {mem['max_usage_mb']:.1f}MB (target <500MB)")
        
        # Print overall status
        status = "✅ MVP READY" if mvp_ready else "⚠️ NEEDS OPTIMIZATION"
        print(f"\n🎯 Overall Status: {status}")
        
        if issues:
            print("\n🚨 Issues to address:")
            for issue in issues:
                print(f"   - {issue}")
        
        # Print detailed results
        print(f"\n📈 Detailed Results:")
        for category, data in self.results.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        print(f"   {key}: {value}")
                    else:
                        if isinstance(value, float):
                            print(f"   {key}: {value:.3f}")
                        else:
                            print(f"   {key}: {value}")


async def main():
    """Run performance benchmarks"""
    benchmarks = PerformanceBenchmarks()
    await benchmarks.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())