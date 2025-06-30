"""
Project Monitoring Service

Extracted from enhanced_l3_agent.py to provide focused real-time project monitoring,
change detection, and impact analysis capabilities following single responsibility principle.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.monitoring_models import (
    MonitoringConfiguration,
    MonitoringStatus,
    ChangeType,
)
from .file_monitor_service import file_monitor_service
from .incremental_indexer import incremental_indexer

logger = logging.getLogger(__name__)


class ProjectMonitoringService:
    """
    Service dedicated to real-time project monitoring and change tracking.
    
    Provides file monitoring, change detection, impact analysis, and project indexing
    with intelligent debouncing and performance optimization.
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, str] = {}  # client_id -> session_id mapping
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the project monitoring service"""
        try:
            # Ensure file monitor service is initialized
            if not file_monitor_service.initialized:
                await file_monitor_service.initialize()
            
            self._initialized = True
            logger.info("Project Monitoring Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Project Monitoring Service: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided by this service"""
        return [
            "real_time_monitoring",
            "change_detection",
            "impact_analysis",
            "project_indexing",
            "performance_metrics",
            "session_management"
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service"""
        return {
            "service": "project_monitoring",
            "initialized": self._initialized,
            "active_sessions": len(self.active_sessions),
            "file_monitor_ready": file_monitor_service.initialized if hasattr(file_monitor_service, 'initialized') else False
        }
    
    async def start_monitoring(
        self, 
        client_id: str,
        workspace_path: Optional[str] = None,
        watch_patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Start real-time file monitoring for a workspace
        
        Extracted from: _start_monitoring_tool()
        """
        try:
            if not workspace_path:
                return {
                    "status": "error",
                    "message": "Workspace path is required",
                    "confidence": 0.0,
                }
            
            session_id = f"monitor_{client_id}_{int(time.time())}"
            project_id = f"project_{hash(workspace_path)}"

            # Create monitoring configuration
            config = MonitoringConfiguration(
                workspace_path=workspace_path,
                watch_patterns=watch_patterns or [
                    "**/*.py",
                    "**/*.js",
                    "**/*.ts",
                    "**/*.tsx",
                    "**/*.swift",
                ],
                ignore_patterns=ignore_patterns or [
                    "**/__pycache__/**",
                    "**/node_modules/**",
                    "**/.git/**",
                ],
                debounce_delay_ms=500,
                enable_content_analysis=True,
                enable_impact_analysis=True,
            )

            # Start monitoring
            success = await file_monitor_service.start_monitoring(
                session_id=session_id,
                project_id=project_id,
                client_id=client_id,
                config=config,
            )

            if success:
                # Store session mapping
                self.active_sessions[client_id] = session_id

                summary = f"""🔍 Real-time File Monitoring Started!
                
📁 Workspace: {Path(workspace_path).name}
🎯 Session ID: {session_id}
👀 Watching: Python, JavaScript, TypeScript, Swift files
⚡ Features:
• Real-time change detection
• Impact analysis for modifications
• Smart debouncing (500ms)
• Content analysis enabled

🔔 You'll receive notifications for:
• File modifications and creations
• High-impact changes
• Circular dependency introduction
• Architecture pattern violations

📊 Use monitoring status to check activity
🛑 Use stop monitoring to end session"""

                data = {
                    "session_id": session_id,
                    "workspace_path": workspace_path,
                    "configuration": config.dict(),
                    "status": "active",
                    "summary": summary,
                }

                return {
                    "status": "success",
                    "type": "monitoring_started",
                    "data": data,
                    "message": f"File monitoring started for {Path(workspace_path).name}",
                    "confidence": 0.95,
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start file monitoring",
                    "confidence": 0.0,
                }

        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return {
                "status": "error",
                "message": f"Monitoring startup failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def stop_monitoring(self, client_id: str) -> Dict[str, Any]:
        """
        Stop the active file monitoring session for a client
        
        Extracted from: _stop_monitoring_tool()
        """
        try:
            session_id = self.active_sessions.get(client_id)

            if not session_id:
                return {
                    "status": "error",
                    "message": "No active monitoring session found",
                    "confidence": 0.0,
                }

            # Get session info before stopping
            session = file_monitor_service.get_session(session_id)

            # Stop monitoring
            success = await file_monitor_service.stop_monitoring(session_id)

            if success:
                # Clear session mapping
                self.active_sessions.pop(client_id, None)

                # Generate summary
                if session:
                    duration_min = (
                        (datetime.now() - session.started_at).total_seconds() / 60
                        if session.started_at
                        else 0
                    )
                    summary = f"""✅ File Monitoring Stopped
                    
📊 Session Summary:
• Duration: {duration_min:.1f} minutes  
• Changes detected: {session.total_changes_detected}
• Files analyzed: {session.total_files_analyzed}
• Errors: {session.total_errors}

📁 Workspace: {Path(session.configuration.workspace_path).name}
🎯 Session: {session_id}

Thank you for using real-time monitoring! 
Start again when needed."""
                else:
                    summary = f"✅ Monitoring session {session_id} stopped successfully"

                data = {
                    "session_id": session_id,
                    "summary": summary,
                    "session_stats": session.dict() if session else None,
                }

                return {
                    "status": "success",
                    "type": "monitoring_stopped",
                    "data": data,
                    "message": "File monitoring stopped successfully",
                    "confidence": 0.95,
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to stop monitoring session",
                    "confidence": 0.0,
                }

        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return {
                "status": "error",
                "message": f"Failed to stop monitoring: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_monitoring_status(self, client_id: str) -> Dict[str, Any]:
        """
        Get the status of the current monitoring session
        
        Extracted from: _get_monitoring_status_tool()
        """
        try:
            session_id = self.active_sessions.get(client_id)

            if not session_id:
                return {
                    "status": "success",
                    "type": "monitoring_status",
                    "data": {
                        "active": False,
                        "summary": "📡 No active monitoring session\n\nUse start monitoring to begin real-time file tracking.",
                    },
                    "message": "No active monitoring session",
                    "confidence": 1.0,
                }

            # Get session and metrics
            session = file_monitor_service.get_session(session_id)
            metrics = file_monitor_service.get_metrics(session_id)

            if not session:
                # Clean up stale session mapping
                self.active_sessions.pop(client_id, None)
                return {
                    "status": "error",
                    "message": "Monitoring session no longer exists",
                    "confidence": 0.0,
                }

            # Calculate uptime
            uptime_seconds = (
                (datetime.now() - session.started_at).total_seconds()
                if session.started_at
                else 0
            )
            uptime_str = f"{uptime_seconds//3600:.0f}h {(uptime_seconds%3600)//60:.0f}m"

            # Generate status summary
            status_icon = {
                MonitoringStatus.ACTIVE: "🟢",
                MonitoringStatus.PAUSED: "🟡", 
                MonitoringStatus.STOPPED: "🔴",
                MonitoringStatus.ERROR: "❌",
            }.get(session.status, "⚪")

            summary = f"""{status_icon} Monitoring Status: {session.status.value.upper()}
            
📊 Session Metrics:
• Uptime: {uptime_str}
• Changes detected: {session.total_changes_detected}
• Files analyzed: {session.total_files_analyzed}
• Errors: {session.total_errors}

📁 Workspace: {Path(session.configuration.workspace_path).name}
🎯 Session: {session_id}"""

            if metrics:
                summary += f"""

⚡ Performance:
• Changes/min: {metrics.changes_per_minute:.1f}
• Avg analysis time: {metrics.average_analysis_time_ms:.1f}ms
• Queue depth: {metrics.queue_depth}"""

            if session.last_activity:
                last_activity = (datetime.now() - session.last_activity).total_seconds()
                if last_activity < 60:
                    summary += f"\n🕐 Last activity: {last_activity:.0f}s ago"
                elif last_activity < 3600:
                    summary += f"\n🕐 Last activity: {last_activity//60:.0f}m ago"
                else:
                    summary += f"\n🕐 Last activity: {last_activity//3600:.0f}h ago"

            summary += """

💡 Commands:
• get recent changes - View latest file modifications
• stop monitoring - End current session"""

            data = {
                "active": session.status == MonitoringStatus.ACTIVE,
                "session_id": session_id,
                "status": session.status,
                "uptime_seconds": uptime_seconds,
                "total_changes": session.total_changes_detected,
                "total_files_analyzed": session.total_files_analyzed,
                "total_errors": session.total_errors,
                "workspace_path": session.configuration.workspace_path,
                "last_activity": session.last_activity,
                "metrics": metrics.dict() if metrics else None,
                "summary": summary,
            }

            return {
                "status": "success",
                "type": "monitoring_status",
                "data": data,
                "message": f"Monitoring session {session.status.value}",
                "confidence": 0.95,
            }

        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return {
                "status": "error",
                "message": f"Failed to get monitoring status: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_recent_changes(self, client_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get recent file changes from the monitoring session
        
        Extracted from: _get_recent_changes_tool()
        """
        try:
            session_id = self.active_sessions.get(client_id)

            if not session_id:
                return {
                    "status": "error", 
                    "message": "No active monitoring session",
                    "confidence": 0.0,
                }

            # Get recent changes
            changes = await file_monitor_service.get_recent_changes(session_id, limit)

            if not changes:
                return {
                    "status": "success",
                    "type": "recent_changes",
                    "data": {
                        "changes": [],
                        "summary": "📝 No recent file changes detected\n\nFiles are being monitored, but no modifications have occurred recently.",
                    },
                    "message": "No recent changes",
                    "confidence": 1.0,
                }

            # Generate summary
            summary_parts = [f"📝 Recent File Changes ({len(changes)} total):\n"]

            for i, change in enumerate(changes[:limit], 1):
                file_name = Path(change.file_path).name
                time_ago = (datetime.now() - change.timestamp).total_seconds()

                if time_ago < 60:
                    time_str = f"{time_ago:.0f}s ago"
                elif time_ago < 3600:
                    time_str = f"{time_ago//60:.0f}m ago"
                else:
                    time_str = f"{time_ago//3600:.0f}h ago"

                # Change type icons
                change_icon = {
                    ChangeType.CREATED: "🆕",
                    ChangeType.MODIFIED: "✏️",
                    ChangeType.DELETED: "🗑️",
                    ChangeType.MOVED: "📦",
                    ChangeType.RENAMED: "🏷️",
                }.get(change.change_type, "📄")

                summary_parts.append(f"{i}. {change_icon} {file_name}")
                summary_parts.append(f"   {change.change_type.value} {time_str}")

                # Add line change info if available
                if change.lines_added or change.lines_removed:
                    summary_parts.append(
                        f"   +{change.lines_added} -{change.lines_removed} lines"
                    )

                if change.language:
                    summary_parts.append(f"   Language: {change.language}")

                summary_parts.append("")

            if len(changes) > limit:
                summary_parts.append(f"... and {len(changes) - limit} more changes")

            # Process changes for response
            changes_data = []
            for change in changes:
                changes_data.append(
                    {
                        "id": change.id,
                        "file_path": change.file_path,
                        "file_name": Path(change.file_path).name,
                        "change_type": change.change_type,
                        "timestamp": change.timestamp,
                        "lines_added": change.lines_added,
                        "lines_removed": change.lines_removed,
                        "lines_modified": change.lines_modified,
                        "language": change.language,
                        "is_binary": change.is_binary,
                        "file_size": change.file_size,
                    }
                )

            data = {
                "changes": changes_data,
                "total_changes": len(changes),
                "showing": min(limit, len(changes)),
                "summary": "\n".join(summary_parts),
            }

            return {
                "status": "success",
                "type": "recent_changes",
                "data": data,
                "message": f"Retrieved {len(changes)} recent changes",
                "confidence": 0.95,
            }

        except Exception as e:
            logger.error(f"Error getting recent changes: {e}")
            return {
                "status": "error",
                "message": f"Failed to get recent changes: {str(e)}",
                "confidence": 0.0,
            }
    
    async def refresh_project_index(self, workspace_path: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Trigger project re-indexing for updated analysis
        
        Extracted from: _ensure_project_indexed() functionality
        """
        try:
            logger.info("Updating project index...")

            # Index the project using incremental indexer for better performance
            project_index = await incremental_indexer.get_or_create_project_index(
                workspace_path, force_full_reindex=force_refresh
            )

            if project_index:
                summary = f"""📊 Project Index Updated Successfully!

📁 Workspace: {Path(workspace_path).name}
📄 Files indexed: {project_index.supported_files}
🔗 Symbols found: {len(project_index.symbols)}
⚠️ Parsing errors: {project_index.parsing_errors}

✅ Project analysis is now up-to-date and ready for intelligent queries."""

                data = {
                    "workspace_path": workspace_path,
                    "total_files": project_index.total_files,
                    "supported_files": project_index.supported_files,
                    "total_symbols": len(project_index.symbols),
                    "parsing_errors": project_index.parsing_errors,
                    "force_refresh": force_refresh,
                    "summary": summary,
                }

                return {
                    "status": "success",
                    "type": "index_updated",
                    "data": data,
                    "message": f"Project index updated: {project_index.supported_files} files analyzed",
                    "confidence": 0.95,
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to update project index",
                    "confidence": 0.0,
                }

        except Exception as e:
            logger.error(f"Error refreshing project index: {e}")
            return {
                "status": "error",
                "message": f"Index refresh failed: {str(e)}",
                "confidence": 0.0,
            }
    
    async def get_indexer_metrics(self) -> Dict[str, Any]:
        """
        Get incremental indexer performance metrics
        
        Extracted from: _get_indexer_metrics_tool()
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
• Error rate: {metrics['error_rate']:.1%}"""

            data = {
                "metrics": metrics,
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
    
    async def analyze_impact(self, client_id: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze the impact of changes to a specific file
        """
        try:
            session_id = self.active_sessions.get(client_id)
            
            if not session_id:
                return {
                    "status": "error",
                    "message": "No active monitoring session for impact analysis",
                    "confidence": 0.0,
                }
            
            # Use file monitor service's impact analysis
            impact = await file_monitor_service.analyze_impact(session_id, file_path)
            
            if impact:
                summary = f"""🎯 Impact Analysis for {Path(file_path).name}:

📊 Affected Components:
• Direct dependencies: {len(impact.get('direct_dependencies', []))}
• Indirect dependencies: {len(impact.get('indirect_dependencies', []))}
• Risk level: {impact.get('risk_level', 'Unknown')}

⚠️ Potential Issues:
{chr(10).join(f"• {issue}" for issue in impact.get('potential_issues', []))}

💡 Recommendations:
{chr(10).join(f"• {rec}" for rec in impact.get('recommendations', []))}"""

                data = {
                    "file_path": file_path,
                    "impact_analysis": impact,
                    "summary": summary,
                }

                return {
                    "status": "success",
                    "type": "impact_analysis",
                    "data": data,
                    "message": f"Impact analysis completed for {Path(file_path).name}",
                    "confidence": 0.9,
                }
            else:
                return {
                    "status": "success",
                    "type": "impact_analysis",
                    "data": {
                        "file_path": file_path,
                        "summary": f"No significant impact detected for {Path(file_path).name}",
                    },
                    "message": "No impact detected",
                    "confidence": 0.8,
                }

        except Exception as e:
            logger.error(f"Error analyzing impact: {e}")
            return {
                "status": "error",
                "message": f"Impact analysis failed: {str(e)}",
                "confidence": 0.0,
            }