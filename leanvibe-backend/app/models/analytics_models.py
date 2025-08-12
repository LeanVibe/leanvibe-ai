"""
Analytics API Models for LeanVibe Platform
Comprehensive data models for analytics, metrics, and performance tracking
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class TimeSeriesData(BaseModel):
    """Time series data point for analytics"""
    timestamp: datetime = Field(description="Data point timestamp")
    value: float = Field(description="Metric value")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsFilter(BaseModel):
    """Filter configuration for analytics queries"""
    start_date: Optional[datetime] = Field(None, description="Start date for analytics")
    end_date: Optional[datetime] = Field(None, description="End date for analytics")
    metric_types: Optional[List[str]] = Field(None, description="Specific metrics to include")
    granularity: str = Field("daily", description="Data granularity: hourly, daily, weekly, monthly")
    tenant_ids: Optional[List[UUID]] = Field(None, description="Filter by specific tenants")
    
    @validator('granularity')
    def validate_granularity(cls, v):
        allowed = ['hourly', 'daily', 'weekly', 'monthly']
        if v not in allowed:
            raise ValueError(f"Granularity must be one of {allowed}")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PipelineAnalyticsResponse(BaseModel):
    """Response model for pipeline analytics"""
    tenant_id: UUID = Field(description="Tenant identifier")
    time_range: str = Field(description="Time range for analytics")
    total_pipelines: int = Field(ge=0, description="Total number of pipelines")
    successful_pipelines: int = Field(ge=0, description="Number of successful pipelines")
    failed_pipelines: int = Field(ge=0, description="Number of failed pipelines")
    average_completion_time: float = Field(ge=0.0, description="Average completion time in hours")
    success_rate: float = Field(ge=0.0, le=100.0, description="Success rate percentage")
    stage_performance: Dict[str, Dict[str, float]] = Field(description="Performance by pipeline stage")
    resource_utilization: Dict[str, float] = Field(description="Resource usage metrics")
    error_breakdown: Dict[str, float] = Field(description="Error categorization")
    time_series_data: List[Dict[str, Any]] = Field(description="Time series analytics data")
    performance_trends: Dict[str, str] = Field(description="Performance trend indicators")
    predictions: Optional[Dict[str, Any]] = Field(None, description="Predictive analytics")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TenantAnalyticsResponse(BaseModel):
    """Response model for tenant analytics"""
    tenant_id: UUID = Field(description="Tenant identifier")
    organization_name: str = Field(description="Organization name")
    time_range: str = Field(description="Time range for analytics")
    total_projects: int = Field(ge=0, description="Total number of projects")
    active_projects: int = Field(ge=0, description="Number of active projects")
    total_users: int = Field(ge=0, description="Total number of users")
    active_users: int = Field(ge=0, description="Number of active users")
    resource_usage: Dict[str, float] = Field(description="Resource consumption metrics")
    billing_metrics: Dict[str, float] = Field(description="Billing and cost metrics")
    feature_usage: Dict[str, float] = Field(description="Feature utilization metrics")
    user_engagement: Dict[str, float] = Field(description="User engagement metrics")
    growth_metrics: Dict[str, float] = Field(description="Growth and trend metrics")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemAnalyticsResponse(BaseModel):
    """Response model for system-wide analytics"""
    time_range: str = Field(description="Time range for analytics")
    total_tenants: int = Field(ge=0, description="Total number of tenants")
    active_tenants: int = Field(ge=0, description="Number of active tenants")
    total_pipelines: int = Field(ge=0, description="Total pipelines across all tenants")
    system_health_score: float = Field(ge=0.0, le=100.0, description="Overall system health score")
    service_uptime: Dict[str, float] = Field(description="Service uptime percentages")
    performance_metrics: Dict[str, float] = Field(description="System performance metrics")
    resource_utilization: Dict[str, float] = Field(description="Infrastructure resource usage")
    error_metrics: Dict[str, float] = Field(description="System error metrics")
    capacity_metrics: Dict[str, float] = Field(description="Capacity and scaling metrics")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UsageMetricsResponse(BaseModel):
    """Response model for detailed usage metrics"""
    tenant_id: UUID = Field(description="Tenant identifier")
    time_range: str = Field(description="Time range for metrics")
    granularity: str = Field(description="Data granularity")
    api_usage: Dict[str, Any] = Field(description="API usage statistics")
    compute_usage: Dict[str, float] = Field(description="Compute resource usage")
    storage_usage: Dict[str, float] = Field(description="Storage utilization")
    bandwidth_usage: Dict[str, float] = Field(description="Bandwidth consumption")
    ai_token_usage: Dict[str, int] = Field(description="AI token consumption")
    cost_breakdown: Dict[str, float] = Field(description="Cost breakdown by service")
    time_series: List[TimeSeriesData] = Field(description="Time series usage data")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics"""
    tenant_id: UUID = Field(description="Tenant identifier")
    time_range: str = Field(description="Time range for metrics")
    service_filter: Optional[str] = Field(None, description="Service filter applied")
    api_performance: Dict[str, float] = Field(description="API performance metrics")
    pipeline_performance: Dict[str, float] = Field(description="Pipeline performance metrics")
    storage_performance: Dict[str, float] = Field(description="Storage performance metrics")
    ai_performance: Dict[str, float] = Field(description="AI service performance metrics")
    overall_health_score: float = Field(ge=0.0, le=100.0, description="Overall performance health score")
    bottlenecks: List[str] = Field(description="Identified performance bottlenecks")
    recommendations: List[str] = Field(description="Performance improvement recommendations")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserEngagementMetrics(BaseModel):
    """Response model for user engagement metrics"""
    tenant_id: UUID = Field(description="Tenant identifier")
    time_range: str = Field(description="Time range for metrics")
    active_users: Dict[str, int] = Field(description="Active user counts by period")
    session_metrics: Dict[str, float] = Field(description="User session metrics")
    feature_adoption: Dict[str, float] = Field(description="Feature adoption rates")
    user_journey: Dict[str, float] = Field(description="User journey completion rates")
    retention_metrics: Dict[str, float] = Field(description="User retention metrics")
    engagement_score: float = Field(ge=0.0, le=100.0, description="Overall engagement score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BillingAnalytics(BaseModel):
    """Billing and revenue analytics"""
    tenant_id: UUID = Field(description="Tenant identifier")
    current_period_revenue: float = Field(ge=0.0, description="Current period revenue")
    projected_revenue: float = Field(ge=0.0, description="Projected revenue")
    cost_breakdown: Dict[str, float] = Field(description="Cost breakdown by service")
    usage_charges: Dict[str, float] = Field(description="Usage-based charges")
    subscription_revenue: float = Field(ge=0.0, description="Subscription revenue")
    overage_charges: float = Field(ge=0.0, description="Overage charges")
    billing_period: str = Field(description="Billing period")
    payment_status: str = Field(description="Payment status")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorAnalytics(BaseModel):
    """Error and incident analytics"""
    total_errors: int = Field(ge=0, description="Total error count")
    error_rate: float = Field(ge=0.0, description="Error rate percentage")
    error_categories: Dict[str, int] = Field(description="Errors by category")
    critical_errors: int = Field(ge=0, description="Critical error count")
    resolved_errors: int = Field(ge=0, description="Resolved error count")
    average_resolution_time: float = Field(ge=0.0, description="Average resolution time in minutes")
    error_trends: List[TimeSeriesData] = Field(description="Error trend data")
    top_error_messages: List[Dict[str, Any]] = Field(description="Most frequent error messages")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CapacityAnalytics(BaseModel):
    """Capacity and scaling analytics"""
    current_utilization: Dict[str, float] = Field(description="Current resource utilization")
    peak_utilization: Dict[str, float] = Field(description="Peak resource utilization")
    capacity_trends: Dict[str, List[TimeSeriesData]] = Field(description="Capacity trend data")
    scaling_events: List[Dict[str, Any]] = Field(description="Auto-scaling events")
    capacity_recommendations: List[str] = Field(description="Capacity optimization recommendations")
    cost_optimization: Dict[str, float] = Field(description="Cost optimization opportunities")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SecurityAnalytics(BaseModel):
    """Security and compliance analytics"""
    security_events: int = Field(ge=0, description="Total security events")
    threat_score: float = Field(ge=0.0, le=100.0, description="Threat risk score")
    compliance_score: float = Field(ge=0.0, le=100.0, description="Compliance score")
    failed_authentications: int = Field(ge=0, description="Failed authentication attempts")
    suspicious_activities: List[Dict[str, Any]] = Field(description="Suspicious activity incidents")
    security_recommendations: List[str] = Field(description="Security improvement recommendations")
    compliance_status: Dict[str, bool] = Field(description="Compliance framework status")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIAnalytics(BaseModel):
    """AI and ML model analytics"""
    total_inferences: int = Field(ge=0, description="Total AI model inferences")
    average_inference_time: float = Field(ge=0.0, description="Average inference time in milliseconds")
    accuracy_percentage: float = Field(ge=0.0, le=100.0, description="Model accuracy percentage")
    token_consumption: Dict[str, int] = Field(description="Token usage by model/service")
    performance_metrics: Dict[str, float] = Field(description="Performance metrics by model")
    cost_per_inference: float = Field(ge=0.0, description="Average cost per inference")
    optimization_opportunities: List[str] = Field(description="AI optimization recommendations")
    
    model_config = {"protected_namespaces": ()}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomMetric(BaseModel):
    """Custom metric definition"""
    metric_id: str = Field(description="Unique metric identifier")
    name: str = Field(description="Metric display name")
    description: str = Field(description="Metric description")
    value: float = Field(description="Current metric value")
    unit: str = Field(description="Metric unit")
    tags: Dict[str, str] = Field(description="Metric tags")
    timestamp: datetime = Field(description="Metric timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertRule(BaseModel):
    """Analytics alert rule configuration"""
    rule_id: UUID = Field(description="Alert rule identifier")
    name: str = Field(description="Alert rule name")
    metric_name: str = Field(description="Metric to monitor")
    condition: str = Field(description="Alert condition (>, <, ==, etc.)")
    threshold: float = Field(description="Alert threshold value")
    severity: str = Field(description="Alert severity level")
    enabled: bool = Field(description="Whether rule is enabled")
    notification_channels: List[str] = Field(description="Notification channels")
    cooldown_minutes: int = Field(ge=1, description="Cooldown period between alerts")
    
    @validator('condition')
    def validate_condition(cls, v):
        allowed = ['>', '<', '>=', '<=', '==', '!=']
        if v not in allowed:
            raise ValueError(f"Condition must be one of {allowed}")
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        allowed = ['low', 'medium', 'high', 'critical']
        if v not in allowed:
            raise ValueError(f"Severity must be one of {allowed}")
        return v


class AnalyticsReport(BaseModel):
    """Comprehensive analytics report"""
    report_id: UUID = Field(description="Report identifier")
    report_name: str = Field(description="Report name")
    tenant_id: UUID = Field(description="Tenant identifier")
    generated_at: datetime = Field(description="Report generation timestamp")
    time_range: str = Field(description="Report time range")
    sections: List[str] = Field(description="Report sections included")
    pipeline_analytics: Optional[PipelineAnalyticsResponse] = Field(None)
    usage_metrics: Optional[UsageMetricsResponse] = Field(None)
    performance_metrics: Optional[PerformanceMetricsResponse] = Field(None)
    user_engagement: Optional[UserEngagementMetrics] = Field(None)
    billing_analytics: Optional[BillingAnalytics] = Field(None)
    executive_summary: str = Field(description="Executive summary of key insights")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsDashboard(BaseModel):
    """Analytics dashboard configuration"""
    dashboard_id: UUID = Field(description="Dashboard identifier")
    name: str = Field(description="Dashboard name")
    tenant_id: UUID = Field(description="Tenant identifier")
    widgets: List[Dict[str, Any]] = Field(description="Dashboard widget configurations")
    layout: Dict[str, Any] = Field(description="Dashboard layout configuration")
    refresh_interval: int = Field(ge=30, description="Auto-refresh interval in seconds")
    is_public: bool = Field(default=False, description="Whether dashboard is publicly accessible")
    created_at: datetime = Field(description="Dashboard creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }