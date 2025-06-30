"""
Architectural Violation Detection Orchestrator

Main service that coordinates rule management, detection, and reporting.
Provides a clean API that replaces the monolithic ArchitecturalViolationDetector.
"""

import asyncio
import logging
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set

from ...models.ast_models import FileAnalysis
from ...models.monitoring_models import ChangeType, FileChange
from ..ast_service import ast_service

from .rule_manager import (
    ViolationType, 
    ViolationSeverity, 
    ArchitecturalRule, 
    rule_manager
)
from .detector import (
    ViolationInstance, 
    ComponentMetrics, 
    violation_detector
)
from .reporter import (
    ArchitecturalReport, 
    violation_reporter
)

logger = logging.getLogger(__name__)


class ArchitecturalViolationService:
    """
    Main service that orchestrates architectural violation detection.
    
    Provides a clean, focused API for:
    - Managing architectural rules
    - Detecting violations in real-time
    - Generating reports and analytics
    - Managing subscriptions and notifications
    """
    
    def __init__(self):
        # Real-time monitoring
        self.active_monitors: Set[str] = set()  # File paths being monitored
        self.pending_analysis: deque[str] = deque()
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Background processing
        self._processing_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start_monitoring(self):
        """Start the violation detection service"""
        if self._is_running:
            logger.warning("Violation detection service already running")
            return
        
        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_pending_analysis())
        logger.info("Started architectural violation detection service")
    
    async def stop_monitoring(self):
        """Stop the violation detection service"""
        self._is_running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped architectural violation detection service")
    
    # Rule Management API
    def add_rule(self, rule: ArchitecturalRule) -> bool:
        """Add a new architectural rule"""
        return rule_manager.add_rule(rule)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an architectural rule"""
        return rule_manager.remove_rule(rule_id)
    
    def get_rule(self, rule_id: str) -> Optional[ArchitecturalRule]:
        """Get a specific rule by ID"""
        return rule_manager.get_rule(rule_id)
    
    def get_rules_by_type(self, violation_type: ViolationType) -> List[ArchitecturalRule]:
        """Get all rules for a specific violation type"""
        return rule_manager.get_rules_by_type(violation_type)
    
    # Violation Detection API
    async def analyze_file(self, file_path: str) -> List[ViolationInstance]:
        """Analyze a single file for violations"""
        try:
            # Get file analysis from AST service
            file_analysis = await ast_service.analyze_file(file_path)
            if not file_analysis:
                logger.warning(f"Could not analyze file: {file_path}")
                return []
            
            # Detect violations
            violations = await violation_detector.detect_violations(file_path, file_analysis)
            
            # Notify subscribers
            violation_reporter.notify_subscribers(file_path, violations)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []
    
    async def analyze_files(self, file_paths: List[str]) -> Dict[str, List[ViolationInstance]]:
        """Analyze multiple files for violations"""
        results = {}
        
        for file_path in file_paths:
            results[file_path] = await self.analyze_file(file_path)
        
        return results
    
    async def handle_file_change(self, change: FileChange):
        """Handle a file change event"""
        try:
            if change.change_type in [ChangeType.CREATED, ChangeType.MODIFIED]:
                # Add to pending analysis queue
                self.pending_analysis.append(change.file_path)
                self.active_monitors.add(change.file_path)
                logger.debug(f"Queued {change.file_path} for violation analysis")
            
            elif change.change_type == ChangeType.DELETED:
                # Remove from monitoring
                self.active_monitors.discard(change.file_path)
                # Clear violations for deleted file
                self._clear_violations_for_file(change.file_path)
                logger.debug(f"Removed {change.file_path} from violation monitoring")
                
        except Exception as e:
            logger.error(f"Error handling file change for {change.file_path}: {e}")
    
    # Violation Query API
    def get_violations_for_file(self, file_path: str) -> List[ViolationInstance]:
        """Get all violations for a specific file"""
        return violation_detector.get_violations_for_file(file_path)
    
    def get_violations_by_type(self, violation_type: ViolationType) -> List[ViolationInstance]:
        """Get violations by type"""
        return violation_detector.get_violations_by_type(violation_type)
    
    def get_violations_by_severity(self, min_severity: ViolationSeverity) -> List[ViolationInstance]:
        """Get violations by minimum severity level"""
        return violation_detector.get_violations_by_severity(min_severity)
    
    def get_all_violations(self) -> List[ViolationInstance]:
        """Get all active violations"""
        return [v for v in violation_detector.violations if not v.resolved]
    
    # Metrics and Reporting API
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive violation metrics"""
        return violation_reporter.get_metrics(
            violation_detector.violations,
            violation_detector.component_metrics
        )
    
    def generate_report(self) -> ArchitecturalReport:
        """Generate a comprehensive architectural report"""
        return violation_reporter.generate_summary(
            violation_detector.violations,
            violation_detector.component_metrics
        )
    
    def get_violation_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get violation trends over time"""
        return violation_reporter.get_violation_trends(violation_detector.violations, days)
    
    def get_top_violating_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get files with the most violations"""
        return violation_reporter.get_top_violating_files(violation_detector.violations, limit)
    
    # Subscription API
    def subscribe_to_violations(self, file_path: str, client_id: str):
        """Subscribe to violation notifications for a file"""
        violation_reporter.subscribe_to_violations(file_path, client_id)
    
    def unsubscribe_from_violations(self, file_path: str, client_id: str):
        """Unsubscribe from violation notifications"""
        violation_reporter.unsubscribe_from_violations(file_path, client_id)
    
    # Component Metrics API
    def get_component_metrics(self, file_path: str) -> Optional[ComponentMetrics]:
        """Get metrics for a specific component"""
        return violation_detector.component_metrics.get(file_path)
    
    def get_all_component_metrics(self) -> Dict[str, ComponentMetrics]:
        """Get metrics for all analyzed components"""
        return violation_detector.component_metrics.copy()
    
    # Background Processing
    async def _process_pending_analysis(self):
        """Background task to process pending file analysis"""
        while self._is_running:
            try:
                # Process pending files
                while self.pending_analysis and self._is_running:
                    file_path = self.pending_analysis.popleft()
                    await self.analyze_file(file_path)
                
                # Wait before checking again
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background violation analysis: {e}")
                await asyncio.sleep(5.0)
    
    def _clear_violations_for_file(self, file_path: str):
        """Clear all violations for a specific file"""
        try:
            # Mark violations as resolved instead of deleting
            for violation in violation_detector.violations:
                if violation.file_path == file_path:
                    violation.resolved = True
            
            # Remove from component metrics
            violation_detector.component_metrics.pop(file_path, None)
            
            logger.debug(f"Cleared violations for {file_path}")
            
        except Exception as e:
            logger.error(f"Error clearing violations for {file_path}: {e}")
    
    # Utility methods for backward compatibility
    async def detect_violations(self, file_path: str) -> List[ViolationInstance]:
        """Backward compatibility method"""
        return await self.analyze_file(file_path)
    
    def get_summary(self) -> ArchitecturalReport:
        """Backward compatibility method"""
        return self.generate_report()


# Global service instance
architectural_violation_service = ArchitecturalViolationService()