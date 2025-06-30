"""
Cache & Performance Service

Extracted from enhanced_l3_agent.py to provide focused cache management, 
warming, and performance optimization capabilities following single responsibility principle.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cache_warming_service import cache_warming_service
from .incremental_indexer import incremental_indexer

logger = logging.getLogger(__name__)


class CachePerformanceService:
    """
    Service dedicated to cache management and performance optimization.
    
    Provides intelligent cache warming, performance monitoring, and optimization
    strategies for project indexing and analysis caching.
    """
    
    def __init__(self):
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the cache performance service"""
        try:
            # Ensure dependencies are initialized
            if hasattr(cache_warming_service, 'initialize'):
                await cache_warming_service.initialize()
            
            self._initialized = True
            logger.info("Cache Performance Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Cache Performance Service: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided by this service"""
        return [
            "cache_warming",
            "warming_candidates",
            "performance_metrics",
            "strategy_management",
            "intelligent_optimization",
            "background_warming"
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service"""
        return {
            "service": "cache_performance",
            "initialized": self._initialized,
            "cache_warming_available": hasattr(cache_warming_service, 'get_metrics'),
            "incremental_indexer_available": hasattr(incremental_indexer, 'get_metrics')
        }
    
    async def get_warming_candidates(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get projects that are candidates for cache warming
        
        Extracted from: _get_warming_candidates_tool()
        """
        try:
            candidates = cache_warming_service.get_warming_candidates(limit)

            if not candidates:
                return {
                    "status": "success",
                    "type": "warming_candidates",
                    "data": {
                        "candidates": [],
                        "summary": "🎯 No cache warming candidates found\n\nThis means either:\n• No projects have sufficient usage patterns\n• All frequently accessed projects are already warmed\n• Cache warming tracking needs more usage data",
                    },
                    "message": "No warming candidates available",
                    "confidence": 1.0,
                }

            # Generate summary
            summary_parts = [
                f"🎯 Cache Warming Candidates ({len(candidates)} found):\n"
            ]

            for i, candidate in enumerate(candidates[:limit], 1):
                project_name = Path(candidate["project_path"]).name
                warming_score = candidate["warming_score"]
                access_count = candidate["access_count"]
                session_time = candidate["total_session_time"]

                score_icon = (
                    "🔥"
                    if warming_score > 0.8
                    else "🟡" if warming_score > 0.6 else "🟢"
                )

                summary_parts.append(f"{i}. {score_icon} {project_name}")
                summary_parts.append(
                    f"   Score: {warming_score:.2f} | Accesses: {access_count} | Time: {session_time/60:.1f}m"
                )
                summary_parts.append(
                    f"   Files accessed: {candidate['files_accessed']}"
                )
                summary_parts.append("")

            summary_parts.extend(
                [
                    "🎯 Warming Score Legend:",
                    "🔥 High priority (>0.8) - Frequently used, recent activity",
                    "🟡 Medium priority (0.6-0.8) - Good usage patterns",
                    "🟢 Low priority (<0.6) - Occasional usage",
                    "",
                    "💡 Use trigger cache warming to start warming these projects",
                ]
            )

            data = {
                "candidates": candidates,
                "total_candidates": len(candidates),
                "showing": min(limit, len(candidates)),
                "summary": "\n".join(summary_parts),
            }

            return {
                "status": "success",
                "type": "warming_candidates",
                "data": data,
                "message": f"Found {len(candidates)} cache warming candidates",
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error getting warming candidates: {e}")
            return {
                "status": "error",
                "message": f"Failed to get warming candidates: {str(e)}",
                "confidence": 0.0,
            }
    
    async def trigger_cache_warming(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger cache warming for specific project or top candidates
        
        Extracted from: _trigger_cache_warming_tool()
        """
        try:
            if project_path:
                # Warm specific project
                project_path = str(Path(project_path).absolute())
                success = await cache_warming_service.queue_warming_task(project_path)

                if success:
                    return {
                        "status": "success",
                        "type": "cache_warming_triggered",
                        "data": {
                            "project_path": project_path,
                            "summary": f"🔥 Cache warming queued for: {Path(project_path).name}\n\nThe project will be warmed in the background based on priority.\nUse warming metrics to check progress.",
                        },
                        "message": f"Cache warming queued for {Path(project_path).name}",
                        "confidence": 0.9,
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to queue warming for {Path(project_path).name}",
                        "confidence": 0.0,
                    }
            else:
                # Trigger intelligent warming for all candidates
                warmed_count = await incremental_indexer.trigger_intelligent_warming()

                summary = f"""🚀 Intelligent Cache Warming Triggered!

🎯 Action Taken:
• Queued {warmed_count} projects for background warming
• Projects selected based on usage patterns and priority scores
• Warming will proceed automatically based on strategy settings

⚡ Strategy: {cache_warming_service.current_strategy}
📊 Background warming is now active

💡 Use warming metrics to monitor progress
🔧 Use set warming strategy to adjust warming behavior"""

                data = {
                    "projects_queued": warmed_count,
                    "strategy": cache_warming_service.current_strategy,
                    "summary": summary,
                }

                return {
                    "status": "success",
                    "type": "intelligent_warming_triggered",
                    "data": data,
                    "message": f"Triggered intelligent warming for {warmed_count} projects",
                    "confidence": 0.95,
                }

        except Exception as e:
            logger.error(f"Error triggering cache warming: {e}")
            return {
                "status": "error",
                "message": f"Failed to trigger cache warming: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_warming_metrics(self) -> Dict[str, Any]:
        """
        Get cache warming performance metrics
        
        Extracted from: _get_warming_metrics_tool()
        """
        try:
            metrics = cache_warming_service.get_metrics()

            if not metrics:
                return {
                    "status": "error",
                    "message": "No warming metrics available",
                    "confidence": 0.0,
                }

            # Calculate success rate
            total_tasks = metrics["total_warming_tasks"]
            success_rate = (metrics["successful_warmings"] / max(total_tasks, 1)) * 100

            summary = f"""📊 Cache Warming Performance Metrics:

🚀 Warming Activity:
• Total warming tasks: {total_tasks}
• Successful warmings: {metrics["successful_warmings"]}
• Failed warmings: {metrics["failed_warmings"]}
• Success rate: {success_rate:.1f}%

⚡ Performance:
• Average warming time: {metrics["average_warming_time"]:.2f}s
• Background warming: {'Active' if metrics["background_warming_active"] else 'Inactive'}

📈 Usage Tracking:
• Projects tracked: {metrics["total_projects_tracked"]}
• Queue size: {metrics["queue_size"]}
• Active tasks: {metrics["active_tasks"]}
• Completed tasks: {metrics["completed_tasks"]}

🎯 Strategy Configuration:
• Current strategy: {metrics["current_strategy"]}
• Max concurrent: {metrics["strategy_config"]["max_concurrent_warming"]}
• Warming interval: {metrics["strategy_config"]["warming_interval_hours"]}h

💡 Commands:
• warming candidates - See projects ready for warming
• trigger cache warming - Start intelligent warming
• set warming strategy aggressive/balanced/conservative - Adjust behavior"""

            data = {
                "metrics": metrics,
                "success_rate": success_rate,
                "total_tasks": total_tasks,
                "strategy": metrics["current_strategy"],
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "warming_metrics",
                "data": data,
                "message": f"Cache warming metrics: {total_tasks} tasks, {success_rate:.1f}% success rate",
                "confidence": 1.0,
            }

        except Exception as e:
            logger.error(f"Error getting warming metrics: {e}")
            return {
                "status": "error",
                "message": f"Failed to get warming metrics: {str(e)}",
                "confidence": 0.0,
            }
    
    async def set_warming_strategy(self, strategy: str) -> Dict[str, Any]:
        """
        Set the cache warming strategy
        
        Extracted from: _set_warming_strategy_tool()
        """
        try:
            # Validate strategy
            valid_strategies = ["aggressive", "balanced", "conservative"]
            if strategy not in valid_strategies:
                return {
                    "status": "error",
                    "message": f"Invalid strategy '{strategy}'. Valid options: {', '.join(valid_strategies)}",
                    "confidence": 0.0,
                }

            # Set the strategy
            success = cache_warming_service.set_warming_strategy(strategy)

            if success:
                # Get strategy details
                strategy_config = cache_warming_service.strategies[strategy]

                summary = f"""🎯 Cache Warming Strategy Set: {strategy.upper()}

⚙️ Strategy Configuration:
• Min access count: {strategy_config.min_access_count}
• Min session time: {strategy_config.min_total_session_time}s
• Warming interval: {strategy_config.warming_interval_hours}h
• Max concurrent: {strategy_config.max_concurrent_warming}
• Warming timeout: {strategy_config.warming_timeout_minutes}m

🔄 Weighting:
• Recency: {strategy_config.recency_weight:.1%}
• Frequency: {strategy_config.frequency_weight:.1%}
• Session quality: {strategy_config.session_quality_weight:.1%}

💡 Strategy Characteristics:"""

                if strategy == "aggressive":
                    summary += """
• 🚀 Warms caches quickly and frequently
• Lower thresholds for warming eligibility
• More concurrent warming tasks
• Best for active development environments"""
                elif strategy == "balanced":
                    summary += """
• ⚖️ Balanced approach to cache warming
• Moderate thresholds and intervals
• Good for most development workflows
• Default recommended setting"""
                elif strategy == "conservative":
                    summary += """
• 🛡️ Careful, resource-conscious warming
• Higher thresholds for warming
• Longer intervals between warmings
• Best for resource-constrained environments"""

                summary += "\n\n✅ Strategy applied! Future warming decisions will use these settings."

                data = {
                    "strategy": strategy,
                    "configuration": {
                        "min_access_count": strategy_config.min_access_count,
                        "min_session_time": strategy_config.min_total_session_time,
                        "warming_interval_hours": strategy_config.warming_interval_hours,
                        "max_concurrent_warming": strategy_config.max_concurrent_warming,
                        "recency_weight": strategy_config.recency_weight,
                        "frequency_weight": strategy_config.frequency_weight,
                        "session_quality_weight": strategy_config.session_quality_weight,
                    },
                    "summary": summary,
                }

                return {
                    "status": "success",
                    "type": "warming_strategy_set",
                    "data": data,
                    "message": f"Cache warming strategy set to {strategy}",
                    "confidence": 0.95,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to set warming strategy to {strategy}",
                    "confidence": 0.0,
                }

        except Exception as e:
            logger.error(f"Error setting warming strategy: {e}")
            return {
                "status": "error",
                "message": f"Failed to set warming strategy: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_indexer_metrics(self) -> Dict[str, Any]:
        """
        Get incremental indexer performance metrics
        
        Cross-service functionality for performance monitoring
        """
        try:
            metrics = incremental_indexer.get_metrics()

            summary = f"""📊 Incremental Indexer Performance Metrics:

🚀 Performance:
• Incremental updates: {metrics['incremental_updates']}
• Files reanalyzed: {metrics['files_reanalyzed']}
• Symbols updated: {metrics['symbols_updated']}
• Cache hits: {metrics['cache_hits']}
• Cache misses: {metrics['cache_misses']}

⏱️ Timing:
• Avg update time: {metrics['average_update_time_ms']:.1f}ms
• Total indexing time: {metrics['total_indexing_time_ms']:.1f}ms

💾 Memory:
• Index size: {metrics['index_size_mb']:.1f}MB
• Memory usage: {metrics['memory_usage_mb']:.1f}MB

🎯 Quality:
• Success rate: {metrics['success_rate']:.1%}
• Error rate: {metrics['error_rate']:.1%}

💡 Performance Insights:
• Cache efficiency: {(metrics['cache_hits'] / max(metrics['cache_hits'] + metrics['cache_misses'], 1)):.1%}
• Processing rate: {metrics['files_reanalyzed'] / max(metrics['total_indexing_time_ms'] / 1000, 1):.1f} files/sec"""

            data = {
                "metrics": metrics,
                "cache_efficiency": metrics['cache_hits'] / max(metrics['cache_hits'] + metrics['cache_misses'], 1),
                "processing_rate": metrics['files_reanalyzed'] / max(metrics['total_indexing_time_ms'] / 1000, 1),
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "indexer_metrics",
                "data": data,
                "message": "Indexer metrics retrieved successfully",
                "confidence": 0.95,
            }

        except Exception as e:
            logger.error(f"Error getting indexer metrics: {e}")
            return {
                "status": "error",
                "message": f"Failed to get indexer metrics: {str(e)}",
                "confidence": 0.0,
            }
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """
        Perform automated performance optimizations
        """
        try:
            optimizations_applied = []
            performance_gain = 0.0
            
            # Check cache efficiency
            metrics = incremental_indexer.get_metrics()
            cache_efficiency = metrics['cache_hits'] / max(metrics['cache_hits'] + metrics['cache_misses'], 1)
            
            if cache_efficiency < 0.7:
                # Trigger cache warming for frequently accessed projects
                candidates = cache_warming_service.get_warming_candidates(5)
                if candidates:
                    for candidate in candidates[:3]:  # Warm top 3
                        await cache_warming_service.queue_warming_task(candidate["project_path"])
                    optimizations_applied.append("Triggered cache warming for top 3 frequently accessed projects")
                    performance_gain += 15.0
            
            # Check memory usage
            if metrics['memory_usage_mb'] > 500:  # If using more than 500MB
                # Clear old cache entries
                await incremental_indexer.cleanup_old_cache_entries()
                optimizations_applied.append("Cleaned up old cache entries to reduce memory usage")
                performance_gain += 10.0
            
            # Check error rate
            if metrics['error_rate'] > 0.1:  # If error rate > 10%
                optimizations_applied.append("Identified high error rate - recommend reviewing project configurations")
                
            # Check processing speed
            avg_update_time = metrics['average_update_time_ms']
            if avg_update_time > 1000:  # If taking more than 1 second per update
                optimizations_applied.append("Detected slow update times - recommend checking file system performance")
                
            if not optimizations_applied:
                optimizations_applied.append("System is already well-optimized - no changes needed")
                performance_gain = 0.0
            
            summary = f"""⚡ Performance Optimization Complete!

🚀 Optimizations Applied:
{chr(10).join(f'• {opt}' for opt in optimizations_applied)}

📊 Performance Assessment:
• Cache efficiency: {cache_efficiency:.1%}
• Memory usage: {metrics['memory_usage_mb']:.1f}MB
• Average update time: {avg_update_time:.1f}ms
• Error rate: {metrics['error_rate']:.1%}

🎯 Estimated Performance Gain: {performance_gain:.1f}%

💡 Recommendations:
• Monitor cache warming metrics for effectiveness
• Consider upgrading strategy to 'aggressive' for active development
• Regular optimization runs recommended weekly"""

            data = {
                "optimizations_applied": optimizations_applied,
                "performance_gain": performance_gain,
                "cache_efficiency": cache_efficiency,
                "memory_usage_mb": metrics['memory_usage_mb'],
                "current_metrics": metrics,
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "performance_optimization",
                "data": data,
                "message": f"Applied {len(optimizations_applied)} optimizations with {performance_gain:.1f}% estimated gain",
                "confidence": 0.9,
            }

        except Exception as e:
            logger.error(f"Error in performance optimization: {e}")
            return {
                "status": "error",
                "message": f"Performance optimization failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        """
        try:
            # Get all metrics
            warming_metrics = cache_warming_service.get_metrics()
            indexer_metrics = incremental_indexer.get_metrics()
            candidates = cache_warming_service.get_warming_candidates(5)
            
            # Calculate performance scores
            cache_efficiency = indexer_metrics['cache_hits'] / max(indexer_metrics['cache_hits'] + indexer_metrics['cache_misses'], 1)
            warming_success_rate = warming_metrics["successful_warmings"] / max(warming_metrics["total_warming_tasks"], 1)
            memory_efficiency = max(0, 1 - (indexer_metrics['memory_usage_mb'] / 1000))  # Normalized to 1GB
            
            overall_score = (cache_efficiency * 0.4 + warming_success_rate * 0.3 + memory_efficiency * 0.3) * 100
            
            summary = f"""📊 Comprehensive Performance Report:

🎯 Overall Performance Score: {overall_score:.1f}/100

🔄 Cache Performance:
• Cache efficiency: {cache_efficiency:.1%}
• Warming success rate: {warming_success_rate:.1%}
• Memory efficiency: {memory_efficiency:.1%}

📈 Key Metrics:
• Active warming candidates: {len(candidates)}
• Background warming: {'Active' if warming_metrics.get('background_warming_active') else 'Inactive'}
• Current strategy: {warming_metrics.get('current_strategy', 'Unknown')}

💾 Resource Usage:
• Memory usage: {indexer_metrics['memory_usage_mb']:.1f}MB
• Index size: {indexer_metrics['index_size_mb']:.1f}MB
• Success rate: {indexer_metrics['success_rate']:.1%}

🚀 Performance Grade: """
            
            if overall_score >= 90:
                summary += "A+ (Excellent)"
            elif overall_score >= 80:
                summary += "A (Very Good)"
            elif overall_score >= 70:
                summary += "B (Good)"
            elif overall_score >= 60:
                summary += "C (Fair)"
            else:
                summary += "D (Needs Improvement)"

            data = {
                "overall_score": overall_score,
                "cache_efficiency": cache_efficiency,
                "warming_success_rate": warming_success_rate,
                "memory_efficiency": memory_efficiency,
                "warming_metrics": warming_metrics,
                "indexer_metrics": indexer_metrics,
                "warming_candidates_count": len(candidates),
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "performance_report",
                "data": data,
                "message": f"Performance report generated: {overall_score:.1f}/100 overall score",
                "confidence": 0.95,
            }

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate performance report: {str(e)}",
                "confidence": 0.0,
            }