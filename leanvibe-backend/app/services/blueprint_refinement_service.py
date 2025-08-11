"""
Blueprint Refinement Service
Handles iterative improvement of technical blueprints based on founder feedback
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from ..models.mvp_models import TechnicalBlueprint, FounderInterview, BusinessRequirement
from ..models.human_gate_models import FounderFeedback, FeedbackType
from ..services.agents.ai_architect_agent import AIArchitectAgent

logger = logging.getLogger(__name__)


class BlueprintRefinementService:
    """Service for refining technical blueprints based on founder feedback"""
    
    def __init__(self):
        self.ai_architect = AIArchitectAgent()
        self.refinement_history: Dict[UUID, List[Dict[str, Any]]] = {}
    
    async def refine_blueprint_from_feedback(
        self,
        original_blueprint: TechnicalBlueprint,
        founder_feedback: FounderFeedback,
        original_interview: FounderInterview
    ) -> TechnicalBlueprint:
        """Refine blueprint based on structured founder feedback"""
        
        try:
            logger.info(f"Refining blueprint based on {founder_feedback.feedback_type} feedback")
            
            if founder_feedback.feedback_type == FeedbackType.APPROVE:
                # No changes needed
                return original_blueprint
            
            # Create refined interview incorporating feedback
            refined_interview = await self._incorporate_feedback_into_interview(
                original_interview, founder_feedback
            )
            
            # Generate new blueprint from refined interview
            refined_blueprint = await self.ai_architect.analyze_founder_interview(refined_interview)
            
            # Apply specific changes requested in feedback
            refined_blueprint = await self._apply_specific_changes(
                refined_blueprint, founder_feedback
            )
            
            # Track refinement history
            await self._track_refinement(
                original_blueprint.id if hasattr(original_blueprint, 'id') else UUID(int=0),
                original_blueprint,
                refined_blueprint,
                founder_feedback
            )
            
            logger.info(f"Blueprint refinement completed with confidence {refined_blueprint.confidence_score:.2f}")
            
            return refined_blueprint
            
        except Exception as e:
            logger.error(f"Blueprint refinement failed: {e}")
            raise
    
    async def _incorporate_feedback_into_interview(
        self,
        original_interview: FounderInterview,
        feedback: FounderFeedback
    ) -> FounderInterview:
        """Incorporate founder feedback into the interview data"""
        
        # Create copy of original interview
        interview_data = original_interview.model_dump()
        
        # Add requested features
        if feedback.add_features:
            interview_data["core_features"].extend(feedback.add_features)
        
        # Remove unwanted features
        if feedback.remove_features:
            interview_data["core_features"] = [
                f for f in interview_data["core_features"] 
                if f not in feedback.remove_features
            ]
        
        # Modify features based on feedback
        if feedback.modify_features:
            for old_feature, new_feature in feedback.modify_features.items():
                # Replace old feature with new one
                try:
                    index = interview_data["core_features"].index(old_feature)
                    interview_data["core_features"][index] = new_feature
                except ValueError:
                    # If old feature not found, just add the new one
                    interview_data["core_features"].append(new_feature)
        
        # Incorporate technical concerns
        if feedback.tech_stack_concerns:
            interview_data["technical_constraints"].extend(feedback.tech_stack_concerns)
        
        # Update timeline expectations
        if feedback.timeline_expectations:
            interview_data["go_to_market"] = f"{interview_data.get('go_to_market', '')} {feedback.timeline_expectations}".strip()
        
        # Add overall feedback as context
        if feedback.overall_comments:
            interview_data["value_proposition"] = f"{interview_data['value_proposition']} Note: {feedback.overall_comments}"
        
        return FounderInterview(**interview_data)
    
    async def _apply_specific_changes(
        self,
        blueprint: TechnicalBlueprint,
        feedback: FounderFeedback
    ) -> TechnicalBlueprint:
        """Apply specific changes requested in founder feedback"""
        
        blueprint_data = blueprint.model_dump()
        
        # Adjust tech stack if concerns were raised
        if feedback.tech_stack_concerns:
            # For now, keep the same stack but add concerns to monitoring requirements
            concerns_text = "; ".join(feedback.tech_stack_concerns)
            blueprint_data["monitoring_requirements"].append(f"Address concerns: {concerns_text}")
        
        # Adjust performance targets based on feedback
        if feedback.timeline_expectations:
            if "faster" in feedback.timeline_expectations.lower():
                # Improve performance targets for faster delivery
                targets = blueprint_data.get("performance_targets", {})
                if "response_time" in targets:
                    # Make response time more aggressive
                    current = targets["response_time"]
                    if "500ms" in current:
                        targets["response_time"] = "< 300ms"
                    elif "300ms" in current:
                        targets["response_time"] = "< 200ms"
        
        # Incorporate priority changes
        if feedback.priority_changes:
            # Update API endpoints based on priority changes
            # This is a simplified implementation
            for feature_id, new_priority in feedback.priority_changes.items():
                if new_priority == "high":
                    # Ensure high priority features have dedicated endpoints
                    endpoint_name = feature_id.lower().replace(" ", "_")
                    new_endpoint = {
                        "name": f"priority_{endpoint_name}",
                        "method": "GET", 
                        "path": f"/{endpoint_name}",
                        "description": f"High priority: {feature_id}",
                        "priority": "high"
                    }
                    blueprint_data["api_endpoints"].append(new_endpoint)
        
        # Recreate blueprint with modifications
        return TechnicalBlueprint(**blueprint_data)
    
    async def _track_refinement(
        self,
        blueprint_id: UUID,
        original_blueprint: TechnicalBlueprint,
        refined_blueprint: TechnicalBlueprint, 
        feedback: FounderFeedback
    ):
        """Track refinement history for analytics"""
        
        refinement_record = {
            "timestamp": feedback.submitted_at,
            "feedback_type": feedback.feedback_type,
            "changes_made": {
                "features_added": len(feedback.add_features),
                "features_removed": len(feedback.remove_features),
                "features_modified": len(feedback.modify_features),
                "tech_concerns_count": len(feedback.tech_stack_concerns)
            },
            "confidence_change": refined_blueprint.confidence_score - original_blueprint.confidence_score,
            "satisfaction_score": feedback.satisfaction_score
        }
        
        if blueprint_id not in self.refinement_history:
            self.refinement_history[blueprint_id] = []
        
        self.refinement_history[blueprint_id].append(refinement_record)
    
    async def get_refinement_history(self, blueprint_id: UUID) -> List[Dict[str, Any]]:
        """Get refinement history for a blueprint"""
        return self.refinement_history.get(blueprint_id, [])
    
    async def calculate_refinement_metrics(self, blueprint_id: UUID) -> Dict[str, Any]:
        """Calculate metrics for blueprint refinement process"""
        
        history = await self.get_refinement_history(blueprint_id)
        
        if not history:
            return {"refinement_count": 0, "avg_satisfaction": None}
        
        metrics = {
            "refinement_count": len(history),
            "avg_satisfaction": sum(r.get("satisfaction_score", 0) for r in history if r.get("satisfaction_score")) / len([r for r in history if r.get("satisfaction_score")]),
            "total_features_added": sum(r["changes_made"]["features_added"] for r in history),
            "total_features_removed": sum(r["changes_made"]["features_removed"] for r in history),
            "confidence_improvement": sum(r["confidence_change"] for r in history),
            "feedback_types": [r["feedback_type"] for r in history]
        }
        
        return metrics


# Global service instance
blueprint_refinement_service = BlueprintRefinementService()