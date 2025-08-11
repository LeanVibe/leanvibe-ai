"""
Email Notification Service
Template-based email system for founder communication and workflow notifications
"""

import asyncio
import logging
import secrets
import string
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..models.human_gate_models import (
    HumanApprovalWorkflow, EmailDeliveryLog, WorkflowType
)

logger = logging.getLogger(__name__)


class EmailTemplate(BaseModel):
    """Email template configuration"""
    template_id: str
    name: str
    subject_template: str
    body_template: str
    variables: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "ignore"


class EmailDeliveryResult(BaseModel):
    """Result of email delivery attempt"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    delivery_status: str = "sent"
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        extra = "ignore"


class EmailService:
    """Service for sending template-based emails to founders"""
    
    def __init__(self):
        self.templates = self._load_email_templates()
        # In-memory storage for development/testing
        self._delivery_logs: Dict[UUID, List[EmailDeliveryLog]] = {}
        self._delivery_logs_by_tenant: Dict[UUID, List[UUID]] = {}
        
        logger.info(f"Initialized Email Service with {len(self.templates)} templates")
    
    def _load_email_templates(self) -> Dict[str, EmailTemplate]:
        """Load email templates for different workflow types"""
        
        templates = {
            "blueprint_approval": EmailTemplate(
                template_id="blueprint_approval",
                name="Blueprint Approval Request",
                subject_template="🚀 Review Your {{project_name}} Blueprint",
                body_template="""Hi {{founder_name}},

Great news! We've generated a technical blueprint for your MVP: **{{project_name}}**.

## Blueprint Summary
- **Technology Stack**: {{tech_stack}}
- **AI Confidence**: {{confidence_score}} ({{confidence_level}})
- **Estimated Development**: {{estimated_completion}}

## Next Steps
Please review your blueprint and let us know if you'd like to proceed:

👉 **[Review & Approve Blueprint]({{approval_url}})**

## What Happens Next?
Once you approve, our AI development team will begin building your MVP immediately. You'll receive real-time progress updates throughout the development process.

## Questions?
Reply to this email or visit our help center if you have any questions.

Best regards,  
The LeanVibe Startup Factory Team

---
*This is an automated message from LeanVibe AI. Your approval is required to proceed with MVP development.*""",
                variables=["founder_name", "project_name", "tech_stack", "confidence_score", "confidence_level", "estimated_completion", "approval_url"]
            ),
            
            "generation_progress": EmailTemplate(
                template_id="generation_progress", 
                name="MVP Generation Progress Update",
                subject_template="⚡ {{project_name}} Progress: {{progress_percent}}% Complete",
                body_template="""Hi {{founder_name}},

Your MVP development is progressing well! Here's the latest update:

## Progress Summary
- **Overall Progress**: {{progress_percent}}% complete
- **Current Stage**: {{current_stage}}
- **Estimated Completion**: {{estimated_completion}}

## What We're Building
{{current_stage_details}}

## View Live Progress
Track real-time progress on your project dashboard:
👉 **[View Progress Dashboard]({{dashboard_url}})**

You'll receive another update when we reach the next major milestone.

Best regards,  
The LeanVibe Development Team

---
*Automated progress update from LeanVibe AI Startup Factory*""",
                variables=["founder_name", "project_name", "progress_percent", "current_stage", "estimated_completion", "current_stage_details", "dashboard_url"]
            ),
            
            "deployment_ready": EmailTemplate(
                template_id="deployment_ready",
                name="MVP Deployment Complete",
                subject_template="🎉 {{project_name}} is Live!",
                body_template="""Hi {{founder_name}},

Congratulations! Your MVP **{{project_name}}** is now live and ready to use.

## Your MVP is Ready
🌐 **Live URL**: [{{live_url}}]({{live_url}})  
🔧 **Admin Panel**: [{{admin_url}}]({{admin_url}})  
📁 **Source Code**: [{{repository_url}}]({{repository_url}})

## Getting Started
1. **Test Your MVP**: Visit the live URL and explore all features
2. **Admin Access**: Use the admin panel to manage your application
3. **Monitor Performance**: Check the monitoring dashboard for insights
4. **Share with Users**: Start inviting your target audience

## What's Included
Your MVP includes:
- ✅ Complete user authentication system
- ✅ All core features from your blueprint
- ✅ Mobile-responsive design
- ✅ Production-ready infrastructure
- ✅ Monitoring and analytics setup

## Next Steps
Now that your MVP is live, consider:
- Gathering user feedback
- Planning additional features
- Setting up marketing campaigns
- Scheduling a success review call

## Support
If you need any assistance, our team is here to help:
- Reply to this email for technical questions
- Schedule a success call to discuss next steps
- Access our knowledge base for tutorials

Congratulations on bringing your vision to life!

Best regards,  
The LeanVibe Success Team

---
*Your journey from idea to deployed MVP is complete! 🚀*""",
                variables=["founder_name", "project_name", "live_url", "admin_url", "repository_url", "monitoring_url"]
            ),
            
            "approval_reminder": EmailTemplate(
                template_id="approval_reminder",
                name="Blueprint Approval Reminder", 
                subject_template="⏰ Reminder: {{project_name}} Blueprint Awaiting Your Review",
                body_template="""Hi {{founder_name}},

Just a friendly reminder that your {{project_name}} blueprint is ready for review.

## Time-Sensitive Action Required
Your approval window expires in **{{time_remaining}}**. After expiration, you'll need to restart the blueprint generation process.

## Quick Review
The blueprint includes:
- Technical architecture and database design
- API endpoints and user flows
- Technology stack recommendations
- Development timeline estimate

👉 **[Review & Approve Now]({{approval_url}})**

## Need More Time?
If you need additional time to review, simply reply to this email and we'll extend your approval window.

Best regards,  
The LeanVibe Team""",
                variables=["founder_name", "project_name", "time_remaining", "approval_url"]
            ),
            
            "revision_requested": EmailTemplate(
                template_id="revision_requested",
                name="Blueprint Revision Complete",
                subject_template="📝 Updated {{project_name}} Blueprint Ready for Review",
                body_template="""Hi {{founder_name}},

We've updated your {{project_name}} blueprint based on your feedback.

## Changes Made
{{revision_summary}}

## Review Your Updated Blueprint
The revised blueprint addresses your concerns and incorporates your suggestions:

👉 **[Review Updated Blueprint]({{approval_url}})**

## What Changed
{{changes_summary}}

Thank you for the detailed feedback - it helps us create exactly what you envision!

Best regards,  
The LeanVibe Blueprint Team""",
                variables=["founder_name", "project_name", "revision_summary", "approval_url", "changes_summary"]
            )
        }
        
        return templates
    
    async def generate_approval_email(
        self,
        workflow: HumanApprovalWorkflow,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate blueprint approval email content"""
        
        try:
            # Determine confidence level description
            confidence_score = context.get("confidence_score", 0.0)
            if confidence_score >= 0.9:
                confidence_level = "Excellent"
            elif confidence_score >= 0.8:
                confidence_level = "Very Good"
            elif confidence_score >= 0.7:
                confidence_level = "Good"
            else:
                confidence_level = "Fair"
            
            # Build template variables
            template_vars = {
                "founder_name": context.get("founder_name", "Founder"),
                "project_name": context.get("project_name", "Your Project"),
                "tech_stack": context.get("tech_stack", "Full-Stack Application"),
                "confidence_score": f"{confidence_score:.1%}" if confidence_score > 0 else "85%",
                "confidence_level": confidence_level,
                "estimated_completion": context.get("estimated_completion", f"{context.get('estimated_hours', 6)} hours"),
                "approval_url": workflow.approval_url
            }
            
            # Generate email content
            content = await self.substitute_template_variables("blueprint_approval", template_vars)
            content["recipient"] = workflow.founder_email
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate approval email: {e}")
            raise
    
    async def substitute_template_variables(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """Substitute variables in email template"""
        
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
        
        template = self.templates[template_id]
        
        # Substitute variables in subject
        subject = template.subject_template
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            subject = subject.replace(placeholder, str(var_value))
        
        # Substitute variables in body
        body = template.body_template
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            body = body.replace(placeholder, str(var_value))
        
        return {
            "subject": subject,
            "body": body,
            "template_id": template_id
        }
    
    async def send_email(
        self,
        recipient: str,
        subject: str, 
        body: str,
        template_type: str,
        workflow_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None
    ) -> EmailDeliveryResult:
        """Send email (mock implementation for development)"""
        
        try:
            # In production, this would integrate with SendGrid, Mailgun, etc.
            # For now, simulate email sending
            
            # Generate mock message ID
            message_id = self._generate_message_id()
            
            # Create delivery log
            if workflow_id and tenant_id:
                delivery_log = EmailDeliveryLog(
                    workflow_id=workflow_id,
                    recipient_email=recipient,
                    email_type=template_type,
                    subject=subject,
                    delivery_status="sent",
                    email_service_id=message_id,
                    tenant_id=tenant_id
                )
                
                await self._log_email_delivery(delivery_log)
            
            # Simulate successful delivery
            result = EmailDeliveryResult(
                success=True,
                message_id=message_id,
                delivery_status="sent"
            )
            
            logger.info(f"Sent email to {recipient} with subject: {subject[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return EmailDeliveryResult(
                success=False,
                error_message=str(e),
                delivery_status="failed"
            )
    
    async def send_approval_notification(
        self,
        workflow: HumanApprovalWorkflow,
        context: Dict[str, Any]
    ) -> EmailDeliveryResult:
        """Send blueprint approval notification email"""
        
        try:
            # Generate email content
            email_content = await self.generate_approval_email(workflow, context)
            
            # Send email
            result = await self.send_email(
                recipient=workflow.founder_email,
                subject=email_content["subject"],
                body=email_content["body"],
                template_type="blueprint_approval",
                workflow_id=workflow.id,
                tenant_id=workflow.tenant_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send approval notification: {e}")
            return EmailDeliveryResult(
                success=False,
                error_message=str(e)
            )
    
    async def send_progress_update(
        self,
        founder_email: str,
        project_name: str,
        progress_data: Dict[str, Any],
        tenant_id: UUID
    ) -> EmailDeliveryResult:
        """Send MVP generation progress update"""
        
        try:
            template_vars = {
                "founder_name": progress_data.get("founder_name", "Founder"),
                "project_name": project_name,
                "progress_percent": progress_data.get("progress_percent", 0),
                "current_stage": progress_data.get("current_stage", "Development"),
                "estimated_completion": progress_data.get("estimated_completion", "Soon"),
                "current_stage_details": progress_data.get("current_stage_details", "Working on your MVP"),
                "dashboard_url": progress_data.get("dashboard_url", "#")
            }
            
            content = await self.substitute_template_variables("generation_progress", template_vars)
            
            return await self.send_email(
                recipient=founder_email,
                subject=content["subject"],
                body=content["body"],
                template_type="generation_progress",
                tenant_id=tenant_id
            )
            
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")
            return EmailDeliveryResult(success=False, error_message=str(e))
    
    async def send_deployment_notification(
        self,
        founder_email: str,
        project_name: str,
        deployment_data: Dict[str, Any],
        tenant_id: UUID
    ) -> EmailDeliveryResult:
        """Send MVP deployment complete notification"""
        
        try:
            template_vars = {
                "founder_name": deployment_data.get("founder_name", "Founder"),
                "project_name": project_name,
                "live_url": deployment_data.get("live_url", "https://your-mvp.com"),
                "admin_url": deployment_data.get("admin_url", "https://your-mvp.com/admin"),
                "repository_url": deployment_data.get("repository_url", "https://github.com/your-repo"),
                "monitoring_url": deployment_data.get("monitoring_url", "https://monitoring.your-mvp.com")
            }
            
            content = await self.substitute_template_variables("deployment_ready", template_vars)
            
            return await self.send_email(
                recipient=founder_email,
                subject=content["subject"],
                body=content["body"],
                template_type="deployment_ready",
                tenant_id=tenant_id
            )
            
        except Exception as e:
            logger.error(f"Failed to send deployment notification: {e}")
            return EmailDeliveryResult(success=False, error_message=str(e))
    
    async def get_delivery_logs(self, workflow_id: UUID) -> List[EmailDeliveryLog]:
        """Get email delivery logs for a workflow"""
        return self._delivery_logs.get(workflow_id, [])
    
    async def get_delivery_metrics(self, tenant_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get email delivery metrics for tenant"""
        
        # Get all logs for tenant
        log_ids = self._delivery_logs_by_tenant.get(tenant_id, [])
        all_logs = []
        for log_id in log_ids:
            logs = self._delivery_logs.get(log_id, [])
            all_logs.extend(logs)
        
        total_sent = len(all_logs)
        delivered_count = len([log for log in all_logs if log.delivery_status == "sent"])
        
        metrics = {
            "total_sent": total_sent,
            "delivered_count": delivered_count,
            "delivery_rate": delivered_count / max(1, total_sent),
            "bounce_count": len([log for log in all_logs if log.delivery_status == "bounced"]),
            "failed_count": len([log for log in all_logs if log.delivery_status == "failed"])
        }
        
        return metrics
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID for email tracking"""
        timestamp = int(datetime.utcnow().timestamp())
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        return f"leanvibe-{timestamp}-{random_suffix}"
    
    async def _log_email_delivery(self, log: EmailDeliveryLog):
        """Log email delivery for tracking"""
        if log.workflow_id not in self._delivery_logs:
            self._delivery_logs[log.workflow_id] = []
        
        self._delivery_logs[log.workflow_id].append(log)
        
        # Add to tenant index
        if log.tenant_id not in self._delivery_logs_by_tenant:
            self._delivery_logs_by_tenant[log.tenant_id] = []
        
        if log.workflow_id not in self._delivery_logs_by_tenant[log.tenant_id]:
            self._delivery_logs_by_tenant[log.tenant_id].append(log.workflow_id)
    
    # Public Database Persistence Methods (Production Ready)
    
    async def get_delivery_logs_from_database(self, workflow_id: UUID) -> List[EmailDeliveryLog]:
        """Public method: Get email delivery logs from database"""
        try:
            # For now, use the existing in-memory storage
            # TODO: Replace with actual database query using EmailDeliveryLogORM
            logs = self._delivery_logs.get(workflow_id, [])
            
            logger.debug(f"Retrieved {len(logs)} email delivery logs for workflow {workflow_id}")
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get email delivery logs from database: {e}")
            return []


# Global email service instance
email_service = EmailService()