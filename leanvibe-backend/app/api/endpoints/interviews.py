"""
Founder Interview API endpoints for LeanVibe Platform
Provides comprehensive REST API for managing founder interviews and requirements extraction
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...models.interview_models import (
    InterviewCreateRequest, InterviewResponse, InterviewUpdateRequest,
    InterviewValidationResponse, InterviewSubmissionRequest
)
from ...models.mvp_models import FounderInterview, BusinessRequirement, MVPIndustry
from ...services.auth_service import auth_service
from ...middleware.tenant_middleware import get_current_tenant, require_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/interviews", tags=["interviews"])
security = HTTPBearer()

# In-memory storage for interviews (will be replaced with proper database)
_interviews_storage: Dict[UUID, FounderInterview] = {}
_interviews_by_tenant: Dict[UUID, List[UUID]] = {}


@router.post("/", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    interview_request: InterviewCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> InterviewResponse:
    """
    Create new founder interview session
    
    Creates a new interview session for capturing founder's business requirements.
    The interview can be completed incrementally and validated before use.
    
    **Process:**
    1. Creates new interview session
    2. Stores initial business context
    3. Returns interview ID for completion
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        # Create interview
        interview_id = uuid4()
        interview = FounderInterview(
            id=interview_id,
            started_at=datetime.utcnow(),
            business_idea=interview_request.business_idea,
            problem_statement=interview_request.problem_statement or "",
            target_audience=interview_request.target_audience or "",
            value_proposition=interview_request.value_proposition or "",
            core_features=interview_request.core_features or [],
            industry=interview_request.industry or MVPIndustry.OTHER
        )
        
        # Store interview
        _interviews_storage[interview_id] = interview
        if tenant.id not in _interviews_by_tenant:
            _interviews_by_tenant[tenant.id] = []
        _interviews_by_tenant[tenant.id].append(interview_id)
        
        # Create response
        response = InterviewResponse(
            id=interview_id,
            interview=interview,
            completion_status="started",
            validation_results=None,
            tenant_id=tenant.id,
            created_by=user_id
        )
        
        logger.info(f"Created interview {interview_id} for tenant {tenant.id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create interview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create interview"
        )


@router.get("/", response_model=List[InterviewResponse])
async def list_interviews(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    completed_only: bool = Query(False)
) -> List[InterviewResponse]:
    """
    List founder interviews for the tenant
    
    Returns a paginated list of interviews with optional filtering.
    
    **Query Parameters:**
    - **limit**: Number of results (1-100, default 50)
    - **offset**: Result offset for pagination (default 0)
    - **completed_only**: Only return completed interviews
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        # Get interviews for tenant
        interview_ids = _interviews_by_tenant.get(tenant.id, [])
        
        # Apply pagination
        paginated_ids = interview_ids[offset:offset + limit]
        
        # Build response list
        interviews = []
        for interview_id in paginated_ids:
            if interview_id in _interviews_storage:
                interview = _interviews_storage[interview_id]
                
                # Apply filters
                if completed_only and not interview.completed_at:
                    continue
                
                # Determine completion status
                completion_status = _get_completion_status(interview)
                validation_results = _validate_interview_completeness(interview)
                
                response = InterviewResponse(
                    id=interview_id,
                    interview=interview,
                    completion_status=completion_status,
                    validation_results=validation_results,
                    tenant_id=tenant.id,
                    created_by=user_id  # TODO: Store actual creator
                )
                interviews.append(response)
        
        logger.info(f"Listed {len(interviews)} interviews for tenant {tenant.id}")
        return interviews
        
    except Exception as e:
        logger.error(f"Failed to list interviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interviews"
        )


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> InterviewResponse:
    """
    Get detailed interview information by ID
    
    Returns comprehensive interview details including validation status
    and completion progress.
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        # Get interview
        if interview_id not in _interviews_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        interview = _interviews_storage[interview_id]
        
        # Verify tenant access
        if tenant.id not in _interviews_by_tenant or interview_id not in _interviews_by_tenant[tenant.id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to interview"
            )
        
        # Get completion status and validation
        completion_status = _get_completion_status(interview)
        validation_results = _validate_interview_completeness(interview)
        
        response = InterviewResponse(
            id=interview_id,
            interview=interview,
            completion_status=completion_status,
            validation_results=validation_results,
            tenant_id=tenant.id,
            created_by=user_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get interview {interview_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interview"
        )


@router.put("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: UUID,
    update_request: InterviewUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> InterviewResponse:
    """
    Update interview information and responses
    
    Updates interview responses with new or modified information.
    Can be called multiple times to build up the complete interview.
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        # Get interview
        if interview_id not in _interviews_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        interview = _interviews_storage[interview_id]
        
        # Verify tenant access
        if tenant.id not in _interviews_by_tenant or interview_id not in _interviews_by_tenant[tenant.id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to interview"
            )
        
        # Apply updates
        if update_request.business_idea:
            interview.business_idea = update_request.business_idea
        if update_request.problem_statement:
            interview.problem_statement = update_request.problem_statement
        if update_request.target_audience:
            interview.target_audience = update_request.target_audience
        if update_request.value_proposition:
            interview.value_proposition = update_request.value_proposition
        if update_request.market_size:
            interview.market_size = update_request.market_size
        if update_request.competition:
            interview.competition = update_request.competition
        if update_request.core_features:
            interview.core_features = update_request.core_features
        if update_request.nice_to_have_features:
            interview.nice_to_have_features = update_request.nice_to_have_features
        if update_request.user_personas:
            interview.user_personas = update_request.user_personas
        if update_request.success_metrics:
            interview.success_metrics = update_request.success_metrics
        if update_request.preferred_tech_stack:
            interview.preferred_tech_stack = update_request.preferred_tech_stack
        if update_request.technical_constraints:
            interview.technical_constraints = update_request.technical_constraints
        if update_request.integration_requirements:
            interview.integration_requirements = update_request.integration_requirements
        if update_request.revenue_model:
            interview.revenue_model = update_request.revenue_model
        if update_request.pricing_strategy:
            interview.pricing_strategy = update_request.pricing_strategy
        if update_request.go_to_market:
            interview.go_to_market = update_request.go_to_market
        if update_request.industry:
            interview.industry = update_request.industry
        
        # Update completion tracking
        completion_status = _get_completion_status(interview)
        if completion_status == "completed" and not interview.completed_at:
            interview.completed_at = datetime.utcnow()
            interview.duration_minutes = int((interview.completed_at - interview.started_at).total_seconds() / 60)
        
        # Store updated interview
        _interviews_storage[interview_id] = interview
        
        # Create response
        validation_results = _validate_interview_completeness(interview)
        response = InterviewResponse(
            id=interview_id,
            interview=interview,
            completion_status=completion_status,
            validation_results=validation_results,
            tenant_id=tenant.id,
            created_by=user_id
        )
        
        logger.info(f"Updated interview {interview_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update interview {interview_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update interview"
        )


@router.post("/{interview_id}/validate", response_model=InterviewValidationResponse)
async def validate_interview(
    interview_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> InterviewValidationResponse:
    """
    Validate interview completeness and quality
    
    Performs comprehensive validation of the interview data to ensure
    it's sufficient for blueprint generation.
    
    **Validation includes:**
    - Required fields completeness
    - Business logic consistency
    - Technical feasibility assessment
    - Requirement extraction quality
    """
    try:
        # Verify token
        await auth_service.verify_token(credentials.credentials)
        
        # Get interview
        if interview_id not in _interviews_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        interview = _interviews_storage[interview_id]
        
        # Verify tenant access
        if tenant.id not in _interviews_by_tenant or interview_id not in _interviews_by_tenant[tenant.id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to interview"
            )
        
        # Perform validation
        validation_results = _validate_interview_completeness(interview)
        
        # Enhanced validation
        technical_feasibility = _assess_technical_feasibility(interview)
        business_viability = _assess_business_viability(interview)
        
        # Extract requirements if not already done
        if not interview.requirements:
            requirements = _extract_business_requirements(interview)
            interview.requirements = requirements
            _interviews_storage[interview_id] = interview
        
        response = InterviewValidationResponse(
            interview_id=interview_id,
            is_valid=validation_results["is_complete"],
            completion_percentage=validation_results["completion_percentage"],
            missing_fields=validation_results["missing_fields"],
            validation_errors=validation_results["validation_errors"],
            technical_feasibility_score=technical_feasibility,
            business_viability_score=business_viability,
            extracted_requirements=len(interview.requirements),
            recommendations=_generate_interview_recommendations(interview, validation_results)
        )
        
        logger.info(f"Validated interview {interview_id}: {validation_results['completion_percentage']:.1f}% complete")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate interview {interview_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate interview"
        )


@router.post("/{interview_id}/submit", response_model=InterviewResponse)
async def submit_interview(
    interview_id: UUID,
    submission_request: InterviewSubmissionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant = Depends(require_tenant)
) -> InterviewResponse:
    """
    Submit completed interview for processing
    
    Marks the interview as completed and ready for blueprint generation.
    Performs final validation before acceptance.
    
    **Requirements:**
    - Interview must pass validation
    - All required fields must be completed
    - Business requirements must be extracted
    """
    try:
        # Verify token
        payload = await auth_service.verify_token(credentials.credentials)
        user_id = UUID(payload["user_id"])
        
        # Get interview
        if interview_id not in _interviews_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        interview = _interviews_storage[interview_id]
        
        # Verify tenant access
        if tenant.id not in _interviews_by_tenant or interview_id not in _interviews_by_tenant[tenant.id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to interview"
            )
        
        # Validate interview is ready for submission
        validation_results = _validate_interview_completeness(interview)
        if not validation_results["is_complete"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Interview incomplete: {', '.join(validation_results['missing_fields'])}"
            )
        
        # Mark as completed if not already
        if not interview.completed_at:
            interview.completed_at = datetime.utcnow()
            interview.duration_minutes = int((interview.completed_at - interview.started_at).total_seconds() / 60)
        
        # Extract business requirements if not done
        if not interview.requirements:
            requirements = _extract_business_requirements(interview)
            interview.requirements = requirements
        
        # Calculate complexity score
        interview.complexity_score = _calculate_complexity_score(interview)
        
        # Store updated interview
        _interviews_storage[interview_id] = interview
        
        # Create response
        response = InterviewResponse(
            id=interview_id,
            interview=interview,
            completion_status="submitted",
            validation_results=validation_results,
            tenant_id=tenant.id,
            created_by=user_id
        )
        
        logger.info(f"Interview {interview_id} submitted successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit interview {interview_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit interview"
        )


# Helper functions

def _get_completion_status(interview: FounderInterview) -> str:
    """Determine interview completion status"""
    validation = _validate_interview_completeness(interview)
    
    if interview.completed_at:
        return "submitted"
    elif validation["completion_percentage"] >= 90:
        return "ready_for_submission"
    elif validation["completion_percentage"] >= 50:
        return "in_progress"
    else:
        return "started"


def _validate_interview_completeness(interview: FounderInterview) -> Dict[str, Any]:
    """Validate interview completeness"""
    required_fields = [
        ("business_idea", interview.business_idea),
        ("problem_statement", interview.problem_statement),
        ("target_audience", interview.target_audience),
        ("value_proposition", interview.value_proposition),
        ("core_features", interview.core_features)
    ]
    
    missing_fields = []
    validation_errors = []
    
    # Check required fields
    for field_name, field_value in required_fields:
        if not field_value or (isinstance(field_value, str) and not field_value.strip()):
            missing_fields.append(field_name)
        elif isinstance(field_value, list) and len(field_value) == 0:
            missing_fields.append(field_name)
    
    # Business logic validation
    if interview.core_features and len(interview.core_features) > 20:
        validation_errors.append("Too many core features (limit: 20)")
    
    if interview.business_idea and len(interview.business_idea) < 50:
        validation_errors.append("Business idea description too brief (minimum: 50 characters)")
    
    if interview.target_audience and len(interview.target_audience) < 20:
        validation_errors.append("Target audience description too brief (minimum: 20 characters)")
    
    # Calculate completion percentage
    total_required = len(required_fields)
    completed_required = total_required - len(missing_fields)
    completion_percentage = (completed_required / total_required) * 100
    
    # Optional fields bonus
    optional_fields = [
        interview.market_size,
        interview.competition,
        interview.revenue_model,
        interview.pricing_strategy,
        interview.go_to_market
    ]
    
    completed_optional = sum(1 for field in optional_fields if field and field.strip())
    optional_bonus = (completed_optional / len(optional_fields)) * 10
    completion_percentage = min(100, completion_percentage + optional_bonus)
    
    is_complete = len(missing_fields) == 0 and len(validation_errors) == 0
    
    return {
        "is_complete": is_complete,
        "completion_percentage": completion_percentage,
        "missing_fields": missing_fields,
        "validation_errors": validation_errors
    }


def _assess_technical_feasibility(interview: FounderInterview) -> float:
    """Assess technical feasibility score (0-100)"""
    score = 70  # Base score
    
    # Complexity factors
    if interview.core_features:
        if len(interview.core_features) > 15:
            score -= 20  # Very complex
        elif len(interview.core_features) > 10:
            score -= 10  # Moderately complex
    
    # Integration complexity
    if interview.integration_requirements:
        score -= len(interview.integration_requirements) * 5
    
    # Technical constraints
    if interview.technical_constraints:
        score -= len(interview.technical_constraints) * 3
    
    # Industry factors
    if interview.industry in [MVPIndustry.FINTECH, MVPIndustry.HEALTHTECH]:
        score -= 15  # Higher regulatory complexity
    elif interview.industry == MVPIndustry.AI_ML:
        score -= 10  # AI complexity
    
    return max(0, min(100, score))


def _assess_business_viability(interview: FounderInterview) -> float:
    """Assess business viability score (0-100)"""
    score = 60  # Base score
    
    # Business model clarity
    if interview.revenue_model:
        score += 15
    if interview.pricing_strategy:
        score += 10
    if interview.go_to_market:
        score += 10
    
    # Market understanding
    if interview.market_size:
        score += 5
    if interview.competition:
        score += 5
    
    # Product clarity
    if interview.user_personas:
        score += len(interview.user_personas) * 3
    if interview.success_metrics:
        score += len(interview.success_metrics) * 2
    
    return max(0, min(100, score))


def _extract_business_requirements(interview: FounderInterview) -> List[BusinessRequirement]:
    """Extract business requirements from interview"""
    requirements = []
    
    # Extract from core features
    for i, feature in enumerate(interview.core_features):
        requirement = BusinessRequirement(
            requirement=feature,
            priority="high",
            category="functional",
            acceptance_criteria=[f"User can {feature.lower()}"]
        )
        requirements.append(requirement)
    
    # Extract from nice-to-have features
    for feature in interview.nice_to_have_features:
        requirement = BusinessRequirement(
            requirement=feature,
            priority="low",
            category="functional",
            acceptance_criteria=[f"User can {feature.lower()}"]
        )
        requirements.append(requirement)
    
    # Add performance requirements
    requirements.append(BusinessRequirement(
        requirement="System should be responsive and fast",
        priority="medium",
        category="performance",
        acceptance_criteria=["Page load time < 3 seconds", "API response time < 500ms"]
    ))
    
    # Add security requirements
    requirements.append(BusinessRequirement(
        requirement="System should be secure and protect user data",
        priority="high",
        category="business",
        acceptance_criteria=["HTTPS encryption", "Secure authentication", "Data privacy compliance"]
    ))
    
    return requirements


def _calculate_complexity_score(interview: FounderInterview) -> float:
    """Calculate project complexity score (0-1)"""
    score = 0.3  # Base complexity
    
    # Feature complexity
    if interview.core_features:
        score += len(interview.core_features) * 0.02
    
    # Integration complexity
    if interview.integration_requirements:
        score += len(interview.integration_requirements) * 0.05
    
    # Technical constraints
    if interview.technical_constraints:
        score += len(interview.technical_constraints) * 0.03
    
    # Industry complexity
    complexity_by_industry = {
        MVPIndustry.FINTECH: 0.3,
        MVPIndustry.HEALTHTECH: 0.25,
        MVPIndustry.AI_ML: 0.2,
        MVPIndustry.BLOCKCHAIN: 0.15,
        MVPIndustry.IOT: 0.15,
        MVPIndustry.ECOMMERCE: 0.1,
        MVPIndustry.SOCIAL: 0.05,
        MVPIndustry.OTHER: 0.0
    }
    score += complexity_by_industry.get(interview.industry, 0.0)
    
    return max(0.1, min(1.0, score))


def _generate_interview_recommendations(interview: FounderInterview, validation_results: Dict[str, Any]) -> List[str]:
    """Generate recommendations for improving the interview"""
    recommendations = []
    
    # Missing fields recommendations
    for field in validation_results["missing_fields"]:
        field_recommendations = {
            "business_idea": "Provide a clear description of your business idea and what problem it solves",
            "problem_statement": "Describe the specific problem your solution addresses",
            "target_audience": "Define who your target customers are and their characteristics",
            "value_proposition": "Explain what unique value you provide to customers",
            "core_features": "List the essential features your MVP needs to have"
        }
        recommendations.append(field_recommendations.get(field, f"Please provide {field.replace('_', ' ')}"))
    
    # Business improvement recommendations
    if not interview.revenue_model:
        recommendations.append("Consider defining how your business will generate revenue")
    
    if not interview.competition:
        recommendations.append("Research and describe your competitive landscape")
    
    if not interview.user_personas:
        recommendations.append("Create detailed user personas to better understand your customers")
    
    if interview.core_features and len(interview.core_features) > 10:
        recommendations.append("Consider reducing core features to focus on the most essential functionality")
    
    # Technical recommendations
    if interview.preferred_tech_stack is None:
        recommendations.append("Consider specifying a preferred technology stack if you have preferences")
    
    return recommendations