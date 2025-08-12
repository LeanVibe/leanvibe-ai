"""
Interview API Models for LeanVibe Founder Interview Management
Comprehensive data models for founder interview capture, validation, and processing
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

from .mvp_models import FounderInterview, MVPTechStack, MVPIndustry


class InterviewCreateRequest(BaseModel):
    """Request model for creating a new founder interview"""
    business_idea: str = Field(min_length=10, max_length=2000, description="Core business idea description")
    problem_statement: Optional[str] = Field(None, max_length=1000, description="Problem being solved")
    target_audience: Optional[str] = Field(None, max_length=500, description="Target customer description")
    value_proposition: Optional[str] = Field(None, max_length=1000, description="Unique value proposition")
    core_features: Optional[List[str]] = Field(None, description="Initial core features list")
    industry: Optional[MVPIndustry] = Field(None, description="Business industry category")
    
    @validator('business_idea')
    def validate_business_idea(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Business idea must be at least 10 characters")
        return v.strip()
    
    @validator('core_features')
    def validate_core_features(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError("Maximum 20 core features allowed")
        return v


class InterviewUpdateRequest(BaseModel):
    """Request model for updating interview information"""
    business_idea: Optional[str] = Field(None, min_length=10, max_length=2000)
    problem_statement: Optional[str] = Field(None, max_length=1000)
    target_audience: Optional[str] = Field(None, max_length=500)
    value_proposition: Optional[str] = Field(None, max_length=1000)
    market_size: Optional[str] = Field(None, max_length=500)
    competition: Optional[str] = Field(None, max_length=1000)
    
    # Product requirements
    core_features: Optional[List[str]] = Field(None, description="Core MVP features")
    nice_to_have_features: Optional[List[str]] = Field(None, description="Future features")
    user_personas: Optional[List[Dict[str, str]]] = Field(None, description="User personas")
    success_metrics: Optional[List[str]] = Field(None, description="Success metrics")
    
    # Technical preferences
    preferred_tech_stack: Optional[MVPTechStack] = Field(None)
    technical_constraints: Optional[List[str]] = Field(None)
    integration_requirements: Optional[List[str]] = Field(None)
    
    # Business model
    revenue_model: Optional[str] = Field(None, max_length=500)
    pricing_strategy: Optional[str] = Field(None, max_length=500)
    go_to_market: Optional[str] = Field(None, max_length=1000)
    
    # Industry and classification
    industry: Optional[MVPIndustry] = Field(None)
    
    @validator('business_idea')
    def validate_business_idea(cls, v):
        if v is not None and len(v.strip()) < 10:
            raise ValueError("Business idea must be at least 10 characters")
        return v.strip() if v else v
    
    @validator('core_features')
    def validate_core_features(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError("Maximum 20 core features allowed")
        return v
    
    @validator('nice_to_have_features')
    def validate_nice_to_have_features(cls, v):
        if v is not None and len(v) > 30:
            raise ValueError("Maximum 30 nice-to-have features allowed")
        return v


class InterviewSubmissionRequest(BaseModel):
    """Request model for submitting completed interview"""
    final_review: bool = Field(True, description="Confirm final review completed")
    additional_notes: Optional[str] = Field(None, max_length=1000, description="Additional notes or clarifications")
    
    @validator('final_review')
    def validate_final_review(cls, v):
        if not v:
            raise ValueError("Final review must be confirmed before submission")
        return v


class InterviewValidationResponse(BaseModel):
    """Response model for interview validation results"""
    interview_id: UUID = Field(description="Interview identifier")
    is_valid: bool = Field(description="Whether interview passes validation")
    completion_percentage: float = Field(ge=0.0, le=100.0, description="Completion percentage")
    missing_fields: List[str] = Field(description="List of missing required fields")
    validation_errors: List[str] = Field(description="List of validation errors")
    technical_feasibility_score: float = Field(ge=0.0, le=100.0, description="Technical feasibility score")
    business_viability_score: float = Field(ge=0.0, le=100.0, description="Business viability score")
    extracted_requirements: int = Field(ge=0, description="Number of extracted business requirements")
    recommendations: List[str] = Field(description="Recommendations for improvement")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InterviewResponse(BaseModel):
    """Response model for interview information"""
    id: UUID = Field(description="Unique interview identifier")
    interview: FounderInterview = Field(description="Complete interview data")
    completion_status: str = Field(description="Completion status: started, in_progress, ready_for_submission, submitted")
    validation_results: Optional[Dict[str, Any]] = Field(None, description="Latest validation results")
    tenant_id: UUID = Field(description="Tenant identifier")
    created_by: UUID = Field(description="User who created the interview")
    
    @validator('completion_status')
    def validate_completion_status(cls, v):
        allowed_statuses = ['started', 'in_progress', 'ready_for_submission', 'submitted']
        if v not in allowed_statuses:
            raise ValueError(f"Completion status must be one of {allowed_statuses}")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InterviewAnalytics(BaseModel):
    """Analytics data for interview completion patterns"""
    total_interviews: int = Field(ge=0, description="Total number of interviews")
    completed_interviews: int = Field(ge=0, description="Number of completed interviews")
    average_completion_time: float = Field(ge=0.0, description="Average completion time in minutes")
    completion_rate: float = Field(ge=0.0, le=100.0, description="Completion rate percentage")
    most_common_industry: Optional[MVPIndustry] = Field(None, description="Most common industry")
    average_features_count: float = Field(ge=0.0, description="Average number of core features")
    average_complexity_score: float = Field(ge=0.0, le=1.0, description="Average complexity score")
    drop_off_points: List[str] = Field(description="Common points where users abandon interviews")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InterviewTemplate(BaseModel):
    """Template for standardized interview questions"""
    id: UUID = Field(description="Template identifier")
    name: str = Field(min_length=1, max_length=100, description="Template name")
    description: str = Field(max_length=500, description="Template description")
    industry: Optional[MVPIndustry] = Field(None, description="Target industry")
    questions: List[Dict[str, Any]] = Field(description="Structured questions list")
    estimated_duration: int = Field(ge=5, le=120, description="Estimated completion time in minutes")
    is_public: bool = Field(default=False, description="Whether template is publicly available")
    created_at: datetime = Field(description="Template creation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InterviewQuestion(BaseModel):
    """Individual interview question definition"""
    id: str = Field(description="Question identifier")
    text: str = Field(min_length=10, max_length=500, description="Question text")
    question_type: str = Field(description="Question type: text, multiple_choice, rating, list")
    required: bool = Field(default=True, description="Whether question is required")
    options: Optional[List[str]] = Field(None, description="Options for multiple choice questions")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    help_text: Optional[str] = Field(None, max_length=200, description="Help text for question")
    section: str = Field(description="Question section/category")
    order: int = Field(ge=1, description="Display order within section")
    
    @validator('question_type')
    def validate_question_type(cls, v):
        allowed_types = ['text', 'textarea', 'multiple_choice', 'single_choice', 'rating', 'list', 'boolean']
        if v not in allowed_types:
            raise ValueError(f"Question type must be one of {allowed_types}")
        return v
    
    @validator('options')
    def validate_options(cls, v, values):
        question_type = values.get('question_type')
        if question_type in ['multiple_choice', 'single_choice'] and not v:
            raise ValueError("Options required for choice questions")
        return v


class InterviewProgress(BaseModel):
    """Real-time interview progress tracking"""
    interview_id: UUID = Field(description="Interview identifier")
    current_section: str = Field(description="Current section being completed")
    completed_questions: int = Field(ge=0, description="Number of completed questions")
    total_questions: int = Field(ge=1, description="Total number of questions")
    progress_percentage: float = Field(ge=0.0, le=100.0, description="Progress percentage")
    estimated_time_remaining: int = Field(ge=0, description="Estimated time remaining in minutes")
    last_activity: datetime = Field(description="Last activity timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InterviewExport(BaseModel):
    """Export configuration for interview data"""
    interview_ids: List[UUID] = Field(description="Interview IDs to export")
    export_format: str = Field(description="Export format: json, csv, pdf")
    include_analysis: bool = Field(default=True, description="Include analysis and metrics")
    include_requirements: bool = Field(default=True, description="Include extracted requirements")
    anonymize_data: bool = Field(default=False, description="Remove personally identifiable information")
    
    @validator('export_format')
    def validate_export_format(cls, v):
        allowed_formats = ['json', 'csv', 'pdf', 'xlsx']
        if v not in allowed_formats:
            raise ValueError(f"Export format must be one of {allowed_formats}")
        return v
    
    @validator('interview_ids')
    def validate_interview_ids(cls, v):
        if len(v) == 0:
            raise ValueError("At least one interview ID must be provided")
        if len(v) > 100:
            raise ValueError("Maximum 100 interviews can be exported at once")
        return v


class InterviewMetrics(BaseModel):
    """Detailed metrics for interview performance"""
    interview_id: UUID = Field(description="Interview identifier")
    completion_metrics: Dict[str, float] = Field(description="Completion time metrics by section")
    quality_scores: Dict[str, float] = Field(description="Response quality scores")
    engagement_metrics: Dict[str, Any] = Field(description="User engagement metrics")
    technical_assessment: Dict[str, float] = Field(description="Technical feasibility assessment")
    business_assessment: Dict[str, float] = Field(description="Business viability assessment")
    generated_at: datetime = Field(description="Metrics generation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }