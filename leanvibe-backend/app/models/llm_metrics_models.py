"""
LLM Metrics Models for LeanVibe Backend

Pydantic models for tracking LLM performance, token usage, and model information.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ModelStatus(str, Enum):
    """Status of the LLM model"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    OFFLINE = "offline"


class DeploymentMode(str, Enum):
    """Model deployment modes"""
    DIRECT = "direct"  # Direct MLX-LM integration
    SERVER = "server"  # HTTP client to MLX-LM server
    MOCK = "mock"      # Mock mode for development


class TokenUsage(BaseModel):
    """Token usage metrics for a single request or session"""
    input_tokens: int = Field(default=0, description="Number of input tokens")
    output_tokens: int = Field(default=0, description="Number of output tokens")
    total_tokens: int = Field(default=0, description="Total tokens (input + output)")
    
    def update_total(self):
        """Update total tokens calculation"""
        self.total_tokens = self.input_tokens + self.output_tokens


class GenerationMetrics(BaseModel):
    """Metrics for a single text generation"""
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Token metrics
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    
    # Performance metrics
    generation_time_seconds: float = Field(default=0.0, description="Total generation time")
    time_to_first_token_ms: Optional[float] = Field(None, description="Time to first token")
    tokens_per_second: float = Field(default=0.0, description="Generation speed")
    
    # Memory metrics
    memory_usage_mb: float = Field(default=0.0, description="Memory usage during generation")
    peak_memory_mb: Optional[float] = Field(None, description="Peak memory usage")
    
    # Request details
    prompt_length: int = Field(default=0, description="Length of input prompt")
    response_length: int = Field(default=0, description="Length of generated response")
    temperature: float = Field(default=0.7, description="Generation temperature")
    max_tokens: int = Field(default=512, description="Maximum tokens requested")
    
    def calculate_tokens_per_second(self):
        """Calculate tokens per second if not set"""
        if self.generation_time_seconds > 0 and self.token_usage.output_tokens > 0:
            self.tokens_per_second = self.token_usage.output_tokens / self.generation_time_seconds


class ModelInformation(BaseModel):
    """Information about the LLM model"""
    model_name: str = Field(..., description="Name of the model")
    model_version: Optional[str] = Field(None, description="Model version")
    deployment_mode: DeploymentMode = Field(..., description="How the model is deployed")
    status: ModelStatus = Field(default=ModelStatus.NOT_INITIALIZED)
    
    # Model capabilities
    context_length: Optional[int] = Field(None, description="Maximum context length")
    parameter_count: Optional[str] = Field(None, description="Number of parameters (e.g., '7B', '30B')")
    supported_languages: List[str] = Field(default_factory=list)
    
    # Configuration
    default_temperature: float = Field(default=0.7)
    default_max_tokens: int = Field(default=512)
    
    # Performance characteristics
    estimated_memory_gb: Optional[float] = Field(None, description="Estimated memory usage")
    supports_streaming: bool = Field(default=False)
    
    # Health information
    last_health_check: Optional[datetime] = Field(None)
    health_status: str = Field(default="unknown")
    
    # MLX specific
    mlx_available: bool = Field(default=False, description="Whether MLX is available")
    mlx_lm_available: bool = Field(default=False, description="Whether MLX-LM is available")


class SessionMetrics(BaseModel):
    """Aggregated metrics for a session or time period"""
    session_id: str = Field(..., description="Session identifier")
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = Field(None)
    
    # Aggregate token usage
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    
    # Request metrics
    total_requests: int = Field(default=0)
    successful_requests: int = Field(default=0)
    failed_requests: int = Field(default=0)
    
    # Performance metrics
    average_generation_time: float = Field(default=0.0)
    average_tokens_per_second: float = Field(default=0.0)
    min_generation_time: Optional[float] = Field(None)
    max_generation_time: Optional[float] = Field(None)
    
    # Memory metrics
    average_memory_usage_mb: float = Field(default=0.0)
    peak_memory_usage_mb: float = Field(default=0.0)
    
    # Error tracking
    error_rate: float = Field(default=0.0, description="Percentage of failed requests")
    common_errors: List[str] = Field(default_factory=list)
    
    def update_from_generation(self, metrics: GenerationMetrics, success: bool = True):
        """Update session metrics from a generation"""
        # Update request counts
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        if success:
            # Update token counts
            self.total_input_tokens += metrics.token_usage.input_tokens
            self.total_output_tokens += metrics.token_usage.output_tokens
            self.total_tokens += metrics.token_usage.total_tokens
            
            # Update performance metrics
            if self.total_requests == 1:
                self.average_generation_time = metrics.generation_time_seconds
                self.average_tokens_per_second = metrics.tokens_per_second
                self.min_generation_time = metrics.generation_time_seconds
                self.max_generation_time = metrics.generation_time_seconds
            else:
                # Running average for generation time
                self.average_generation_time = (
                    (self.average_generation_time * (self.successful_requests - 1) + 
                     metrics.generation_time_seconds) / self.successful_requests
                )
                
                # Running average for tokens per second
                if metrics.tokens_per_second > 0:
                    self.average_tokens_per_second = (
                        (self.average_tokens_per_second * (self.successful_requests - 1) + 
                         metrics.tokens_per_second) / self.successful_requests
                    )
                
                # Update min/max
                if self.min_generation_time is None or metrics.generation_time_seconds < self.min_generation_time:
                    self.min_generation_time = metrics.generation_time_seconds
                if self.max_generation_time is None or metrics.generation_time_seconds > self.max_generation_time:
                    self.max_generation_time = metrics.generation_time_seconds
            
            # Update memory metrics
            if metrics.memory_usage_mb > 0:
                if self.successful_requests == 1:
                    self.average_memory_usage_mb = metrics.memory_usage_mb
                else:
                    self.average_memory_usage_mb = (
                        (self.average_memory_usage_mb * (self.successful_requests - 1) + 
                         metrics.memory_usage_mb) / self.successful_requests
                    )
                
                if metrics.memory_usage_mb > self.peak_memory_usage_mb:
                    self.peak_memory_usage_mb = metrics.memory_usage_mb
        
        # Update error rate
        if self.total_requests > 0:
            self.error_rate = (self.failed_requests / self.total_requests) * 100


class LLMHealthStatus(BaseModel):
    """Complete health status for LLM system"""
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Model information
    model_info: ModelInformation = Field(..., description="Current model information")
    
    # Current session metrics
    current_session: Optional[SessionMetrics] = Field(None, description="Current session metrics")
    
    # Recent performance
    recent_generations: List[GenerationMetrics] = Field(
        default_factory=list, 
        description="Last 10 generations"
    )
    
    # System status
    is_ready: bool = Field(default=False, description="Whether system is ready for requests")
    last_request_time: Optional[datetime] = Field(None, description="Time of last request")
    uptime_seconds: float = Field(default=0.0, description="System uptime")
    
    # Resource usage
    current_memory_mb: float = Field(default=0.0, description="Current memory usage")
    available_memory_mb: Optional[float] = Field(None, description="Available memory")
    
    def add_generation_metrics(self, metrics: GenerationMetrics):
        """Add new generation metrics"""
        self.recent_generations.append(metrics)
        # Keep only last 10
        if len(self.recent_generations) > 10:
            self.recent_generations = self.recent_generations[-10:]
        
        self.last_request_time = metrics.timestamp
    
    def get_recent_average_speed(self) -> float:
        """Get average tokens per second from recent generations"""
        if not self.recent_generations:
            return 0.0
        
        valid_speeds = [g.tokens_per_second for g in self.recent_generations if g.tokens_per_second > 0]
        if not valid_speeds:
            return 0.0
        
        return sum(valid_speeds) / len(valid_speeds)
    
    def get_recent_average_latency(self) -> float:
        """Get average generation time from recent generations"""
        if not self.recent_generations:
            return 0.0
        
        times = [g.generation_time_seconds for g in self.recent_generations]
        return sum(times) / len(times)


class LLMMetricsSnapshot(BaseModel):
    """Complete snapshot of LLM metrics for API responses"""
    health_status: LLMHealthStatus = Field(..., description="Current health status")
    global_metrics: Dict[str, float] = Field(default_factory=dict, description="Global metrics")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            "model_info": {
                "name": self.health_status.model_info.model_name,
                "version": self.health_status.model_info.model_version,
                "deployment_mode": self.health_status.model_info.deployment_mode.value,
                "status": self.health_status.model_info.status.value,
                "context_length": self.health_status.model_info.context_length,
                "parameter_count": self.health_status.model_info.parameter_count,
                "mlx_available": self.health_status.model_info.mlx_available,
                "mlx_lm_available": self.health_status.model_info.mlx_lm_available,
            },
            "performance": {
                "is_ready": self.health_status.is_ready,
                "uptime_seconds": self.health_status.uptime_seconds,
                "recent_average_speed_tokens_per_sec": self.health_status.get_recent_average_speed(),
                "recent_average_latency_seconds": self.health_status.get_recent_average_latency(),
                "total_recent_requests": len(self.health_status.recent_generations),
                "last_request_time": self.health_status.last_request_time.isoformat() if self.health_status.last_request_time else None,
            },
            "memory": {
                "current_usage_mb": self.health_status.current_memory_mb,
                "available_mb": self.health_status.available_memory_mb,
                "estimated_model_memory_gb": self.health_status.model_info.estimated_memory_gb,
            },
            "session_metrics": {
                "total_requests": self.health_status.current_session.total_requests if self.health_status.current_session else 0,
                "successful_requests": self.health_status.current_session.successful_requests if self.health_status.current_session else 0,
                "failed_requests": self.health_status.current_session.failed_requests if self.health_status.current_session else 0,
                "error_rate": self.health_status.current_session.error_rate if self.health_status.current_session else 0.0,
                "total_input_tokens": self.health_status.current_session.total_input_tokens if self.health_status.current_session else 0,
                "total_output_tokens": self.health_status.current_session.total_output_tokens if self.health_status.current_session else 0,
                "total_tokens": self.health_status.current_session.total_tokens if self.health_status.current_session else 0,
            }
        }