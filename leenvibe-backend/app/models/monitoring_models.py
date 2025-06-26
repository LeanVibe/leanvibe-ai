"""
Monitoring Models for Real-time File Monitoring

Pydantic models for representing file changes, impact analysis, and real-time monitoring events.
"""

from typing import Dict, List, Optional, Any, Set
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path

from .ast_models import Symbol, SymbolType


class ChangeType(str, Enum):
    """Types of file system changes"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    RENAMED = "renamed"


class ChangeScope(str, Enum):
    """Scope of change impact"""
    FILE_ONLY = "file_only"
    MODULE_LOCAL = "module_local"
    PACKAGE_WIDE = "package_wide"
    PROJECT_WIDE = "project_wide"
    EXTERNAL_DEPS = "external_deps"


class RiskLevel(str, Enum):
    """Risk levels for changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringStatus(str, Enum):
    """Status of monitoring system"""
    STOPPED = "stopped"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class FileChange(BaseModel):
    """Represents a single file change event"""
    id: str = Field(..., description="Unique change identifier")
    file_path: str = Field(..., description="Path to the changed file")
    change_type: ChangeType = Field(..., description="Type of change")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the change occurred")
    old_path: Optional[str] = None  # For moves/renames
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    
    # Content analysis
    lines_added: int = Field(default=0)
    lines_removed: int = Field(default=0)
    lines_modified: int = Field(default=0)
    
    # Metadata
    is_binary: bool = Field(default=False)
    encoding: Optional[str] = None
    language: Optional[str] = None
    
    def get_relative_path(self, workspace_root: str) -> str:
        """Get path relative to workspace root"""
        try:
            return str(Path(self.file_path).relative_to(workspace_root))
        except ValueError:
            return self.file_path
    
    def is_code_file(self) -> bool:
        """Check if this is a code file worth analyzing"""
        code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.swift', '.go', '.rs', '.java', '.cpp', '.c', '.h'}
        return Path(self.file_path).suffix.lower() in code_extensions


class SymbolChange(BaseModel):
    """Represents changes to symbols within a file"""
    symbol_id: str = Field(..., description="Symbol identifier")
    symbol_name: str = Field(..., description="Symbol name")
    symbol_type: SymbolType = Field(..., description="Type of symbol")
    change_type: ChangeType = Field(..., description="How the symbol changed")
    file_path: str = Field(..., description="File containing the symbol")
    line_start: int = Field(..., description="Starting line of symbol")
    line_end: int = Field(..., description="Ending line of symbol")
    
    # Change details
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    signature_changed: bool = Field(default=False)
    visibility_changed: bool = Field(default=False)
    
    # Impact indicators
    is_public_api: bool = Field(default=False)
    has_external_references: bool = Field(default=False)


class ChangeSet(BaseModel):
    """A collection of related changes"""
    id: str = Field(..., description="Changeset identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    file_changes: List[FileChange] = Field(default_factory=list)
    symbol_changes: List[SymbolChange] = Field(default_factory=list)
    
    # Metadata
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    author: Optional[str] = None
    message: Optional[str] = None
    
    def get_total_changes(self) -> int:
        """Get total number of changes in this set"""
        return len(self.file_changes) + len(self.symbol_changes)
    
    def get_affected_files(self) -> Set[str]:
        """Get set of all affected file paths"""
        files = set()
        for change in self.file_changes:
            files.add(change.file_path)
        for change in self.symbol_changes:
            files.add(change.file_path)
        return files


class ImpactAssessment(BaseModel):
    """Assessment of change impact across the codebase"""
    change_id: str = Field(..., description="ID of the change being assessed")
    assessment_time: datetime = Field(default_factory=datetime.now)
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    scope: ChangeScope = Field(..., description="Scope of impact")
    
    # Affected components
    directly_affected_files: List[str] = Field(default_factory=list)
    indirectly_affected_files: List[str] = Field(default_factory=list)
    affected_symbols: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    
    # Impact metrics
    coupling_impact_score: float = Field(default=0.0, description="Impact on coupling (0-1)")
    complexity_impact_score: float = Field(default=0.0, description="Impact on complexity (0-1)")
    test_coverage_impact: float = Field(default=0.0, description="Impact on test coverage (0-1)")
    
    # Recommendations
    suggested_actions: List[str] = Field(default_factory=list)
    required_tests: List[str] = Field(default_factory=list)
    refactoring_opportunities: List[str] = Field(default_factory=list)
    
    def get_total_affected_files(self) -> int:
        """Get total number of affected files"""
        return len(set(self.directly_affected_files + self.indirectly_affected_files))


class MonitoringConfiguration(BaseModel):
    """Configuration for file monitoring system"""
    workspace_path: str = Field(..., description="Root path to monitor")
    watch_patterns: List[str] = Field(default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.swift"])
    ignore_patterns: List[str] = Field(default_factory=lambda: ["**/__pycache__/**", "**/node_modules/**", "**/.git/**", "**/build/**", "**/dist/**"])
    
    # Monitoring behavior
    debounce_delay_ms: int = Field(default=500, description="Delay before processing changes")
    batch_size: int = Field(default=10, description="Maximum changes to process in one batch")
    enable_content_analysis: bool = Field(default=True)
    enable_impact_analysis: bool = Field(default=True)
    
    # Performance settings
    max_file_size_mb: int = Field(default=10, description="Maximum file size to analyze")
    analysis_timeout_seconds: int = Field(default=30, description="Timeout for analysis operations")


class MonitoringSession(BaseModel):
    """A monitoring session for a specific project"""
    session_id: str = Field(..., description="Unique session identifier")
    project_id: str = Field(..., description="Project being monitored")
    client_id: str = Field(..., description="Client that started the session")
    configuration: MonitoringConfiguration = Field(..., description="Session configuration")
    
    # Session state
    status: MonitoringStatus = Field(default=MonitoringStatus.STOPPED)
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # Statistics
    total_changes_detected: int = Field(default=0)
    total_files_analyzed: int = Field(default=0)
    total_errors: int = Field(default=0)
    
    # Current monitoring data
    recent_changes: List[FileChange] = Field(default_factory=list, description="Recent changes (last 100)")
    pending_analysis: List[str] = Field(default_factory=list, description="Files pending analysis")
    
    def add_change(self, change: FileChange):
        """Add a new change to the session"""
        self.recent_changes.insert(0, change)
        # Keep only last 100 changes
        if len(self.recent_changes) > 100:
            self.recent_changes = self.recent_changes[:100]
        
        self.total_changes_detected += 1
        self.last_activity = datetime.now()
    
    def is_active(self) -> bool:
        """Check if session is currently active"""
        return self.status == MonitoringStatus.ACTIVE


class ChangeNotification(BaseModel):
    """Notification about a change event"""
    id: str = Field(..., description="Notification identifier")
    session_id: str = Field(..., description="Monitoring session ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Change information
    change: FileChange = Field(..., description="The file change")
    impact_assessment: Optional[ImpactAssessment] = None
    
    # Notification metadata
    notification_type: str = Field(default="file_change")
    priority: str = Field(default="normal")  # low, normal, high, urgent
    auto_acknowledge: bool = Field(default=False)
    
    # Display information
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    action_url: Optional[str] = None
    
    @classmethod
    def from_change(cls, change: FileChange, session_id: str, impact: Optional[ImpactAssessment] = None) -> "ChangeNotification":
        """Create notification from a file change"""
        file_name = Path(change.file_path).name
        
        # Generate title and message based on change type
        if change.change_type == ChangeType.CREATED:
            title = f"New file: {file_name}"
            message = f"Created {file_name}"
        elif change.change_type == ChangeType.MODIFIED:
            title = f"Modified: {file_name}"
            lines_info = ""
            if change.lines_added or change.lines_removed:
                lines_info = f" (+{change.lines_added}, -{change.lines_removed})"
            message = f"Modified {file_name}{lines_info}"
        elif change.change_type == ChangeType.DELETED:
            title = f"Deleted: {file_name}"
            message = f"Deleted {file_name}"
        else:
            title = f"Changed: {file_name}"
            message = f"{change.change_type.value.title()} {file_name}"
        
        # Set priority based on impact
        priority = "normal"
        if impact:
            if impact.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                priority = "high"
            elif impact.risk_level == RiskLevel.MEDIUM:
                priority = "normal"
            else:
                priority = "low"
        
        return cls(
            id=f"notif_{change.id}",
            session_id=session_id,
            change=change,
            impact_assessment=impact,
            title=title,
            message=message,
            priority=priority
        )


class MonitoringMetrics(BaseModel):
    """Metrics for monitoring system performance"""
    session_id: str = Field(..., description="Session identifier")
    measurement_time: datetime = Field(default_factory=datetime.now)
    
    # Performance metrics
    changes_per_minute: float = Field(default=0.0)
    average_analysis_time_ms: float = Field(default=0.0)
    memory_usage_mb: float = Field(default=0.0)
    cpu_usage_percent: float = Field(default=0.0)
    
    # Queue metrics
    pending_changes: int = Field(default=0)
    queue_depth: int = Field(default=0)
    processing_errors: int = Field(default=0)
    
    # Impact analysis metrics
    high_impact_changes: int = Field(default=0)
    circular_dependencies_detected: int = Field(default=0)
    hotspot_modifications: int = Field(default=0)
    
    # File system metrics
    files_watched: int = Field(default=0)
    total_file_size_mb: float = Field(default=0.0)
    ignored_changes: int = Field(default=0)


class MonitoringAlert(BaseModel):
    """Alert for significant monitoring events"""
    id: str = Field(..., description="Alert identifier")
    session_id: str = Field(..., description="Monitoring session ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Alert details
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    
    # Context
    affected_files: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    
    # Resolution
    acknowledged: bool = Field(default=False)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None


class MonitoringError(Exception):
    """Custom exception for monitoring system errors"""
    def __init__(self, message: str, error_code: str = "MONITORING_ERROR", session_id: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.session_id = session_id
        super().__init__(self.message)