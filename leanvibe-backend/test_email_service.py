#!/usr/bin/env python3
"""
Email Notification Service Tests
Test-driven implementation of founder communication system
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_email_service_core_functionality():
    """Test core email service functionality - 80% of value"""
    print("🔍 Testing Email Service Core Functionality...")
    
    try:
        from app.services.email_service import EmailService, EmailTemplate, EmailDeliveryResult
        from app.models.human_gate_models import HumanApprovalWorkflow, WorkflowType
        
        # Test 1: Email service initialization
        print("\n1. Testing Email Service Initialization...")
        email_service = EmailService()
        
        # Verify templates are loaded
        assert len(email_service.templates) > 0, "No email templates loaded"
        print(f"   ✅ Email service initialized with {len(email_service.templates)} templates")
        
        # Test 2: Blueprint approval email generation
        print("\n2. Testing Blueprint Approval Email Generation...")
        
        # Create mock workflow
        workflow = HumanApprovalWorkflow(
            id=uuid4(),
            mvp_project_id=uuid4(),
            workflow_type=WorkflowType.BLUEPRINT_APPROVAL,
            founder_email="founder@taskflowpro.com",
            workflow_title="Review Your TaskFlow Pro Blueprint",
            workflow_description="Please review the generated technical blueprint",
            approval_token="mock-token-123",
            approval_url="https://startup-factory.leanvibe.ai/approve/test-token-123",
            tenant_id=uuid4()
        )
        
        # Generate email content
        email_content = await email_service.generate_approval_email(workflow, {
            "project_name": "TaskFlow Pro",
            "tech_stack": "Full-Stack React",
            "confidence_score": 0.85,
            "estimated_hours": 6
        })
        
        assert email_content is not None, "Email content generation failed"
        assert "TaskFlow Pro" in email_content["subject"], "Project name missing from subject"
        assert "founder@taskflowpro.com" == email_content["recipient"], "Wrong recipient"
        assert workflow.approval_url in email_content["body"], "Approval URL missing from body"
        
        print("   ✅ Blueprint approval email generated successfully")
        print(f"   ✅ Subject: {email_content['subject']}")
        print(f"   ✅ Body length: {len(email_content['body'])} chars")
        
        # Test 3: Email delivery (mock)
        print("\n3. Testing Email Delivery...")
        
        delivery_result = await email_service.send_email(
            recipient=workflow.founder_email,
            subject=email_content["subject"],
            body=email_content["body"],
            template_type="blueprint_approval"
        )
        
        assert delivery_result.success, f"Email delivery failed: {delivery_result.error_message}"
        assert delivery_result.message_id is not None, "No message ID returned"
        
        print("   ✅ Email delivery successful")
        print(f"   ✅ Message ID: {delivery_result.message_id}")
        
        # Test 4: Template variable substitution
        print("\n4. Testing Template Variable Substitution...")
        
        template_vars = {
            "founder_name": "John Smith",
            "project_name": "TaskFlow Pro",
            "tech_stack": "Full-Stack React + FastAPI",
            "confidence_score": 0.87,
            "estimated_completion": "6 hours",
            "approval_url": workflow.approval_url
        }
        
        substituted_content = await email_service.substitute_template_variables(
            "blueprint_approval", template_vars
        )
        
        assert "John Smith" in substituted_content["body"], "Founder name not substituted"
        assert "TaskFlow Pro" in substituted_content["subject"], "Project name not substituted"
        assert "0.87" in substituted_content["body"], "Confidence score not substituted"
        
        print("   ✅ Template variable substitution working")
        
        return True
        
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_email_templates_and_formatting():
    """Test email template system and formatting"""
    print("\n🔍 Testing Email Templates and Formatting...")
    
    try:
        from app.services.email_service import EmailService
        
        email_service = EmailService()
        
        # Test all critical email templates
        template_tests = [
            {
                "name": "blueprint_approval",
                "vars": {
                    "founder_name": "Jane Doe", 
                    "project_name": "HealthTracker Pro",
                    "tech_stack": "Full-Stack Vue + FastAPI",
                    "confidence_score": 0.91,
                    "estimated_completion": "4 hours",
                    "approval_url": "https://example.com/approve/token123"
                },
                "required_in_subject": ["HealthTracker Pro", "Blueprint"],
                "required_in_body": ["Jane Doe", "Vue + FastAPI", "0.91", "approve/token123"]
            },
            {
                "name": "generation_progress", 
                "vars": {
                    "founder_name": "Bob Wilson",
                    "project_name": "E-Commerce Plus",
                    "progress_percent": 65,
                    "current_stage": "Frontend Generation",
                    "estimated_completion": "2 hours remaining"
                },
                "required_in_subject": ["E-Commerce Plus", "65%"],
                "required_in_body": ["Bob Wilson", "Frontend Generation", "65%"]
            },
            {
                "name": "deployment_ready",
                "vars": {
                    "founder_name": "Alice Johnson",
                    "project_name": "Analytics Dashboard",
                    "live_url": "https://analytics-dashboard-mvp.com",
                    "admin_url": "https://analytics-dashboard-mvp.com/admin",
                    "repository_url": "https://github.com/startup-factory/analytics-dashboard"
                },
                "required_in_subject": ["Analytics Dashboard", "Live"],
                "required_in_body": ["Alice Johnson", "analytics-dashboard-mvp.com", "/admin"]
            }
        ]
        
        for test_case in template_tests:
            print(f"   Testing {test_case['name']} template...")
            
            content = await email_service.substitute_template_variables(
                test_case["name"], test_case["vars"]
            )
            
            # Check required elements in subject
            for required in test_case["required_in_subject"]:
                assert str(required) in content["subject"], f"Missing '{required}' in subject"
            
            # Check required elements in body  
            for required in test_case["required_in_body"]:
                assert str(required) in content["body"], f"Missing '{required}' in body"
            
            print(f"   ✅ {test_case['name']} template validation passed")
        
        print("   ✅ All email templates validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Email template test failed: {e}")
        return False


async def test_email_delivery_tracking():
    """Test email delivery tracking and metrics"""
    print("\n🔍 Testing Email Delivery Tracking...")
    
    try:
        from app.services.email_service import EmailService
        from app.models.human_gate_models import EmailDeliveryLog
        
        email_service = EmailService()
        
        # Test 1: Delivery logging
        print("   Testing delivery logging...")
        
        workflow_id = uuid4()
        tenant_id = uuid4()
        
        # Send test email
        result = await email_service.send_email(
            recipient="test@example.com",
            subject="Test Email",
            body="This is a test email",
            template_type="blueprint_approval",
            workflow_id=workflow_id,
            tenant_id=tenant_id
        )
        
        assert result.success, "Test email delivery failed"
        
        # Check delivery log created
        logs = await email_service.get_delivery_logs(workflow_id)
        assert len(logs) == 1, "Delivery log not created"
        
        log = logs[0]
        assert log.recipient_email == "test@example.com", "Wrong recipient in log"
        assert log.email_type == "blueprint_approval", "Wrong email type in log"
        assert log.delivery_status == "sent", "Wrong delivery status"
        
        print("   ✅ Email delivery logging working")
        
        # Test 2: Delivery metrics
        print("   Testing delivery metrics...")
        
        # Simulate multiple email deliveries
        for i in range(5):
            await email_service.send_email(
                recipient=f"test{i}@example.com",
                subject=f"Test Email {i}",
                body=f"Test body {i}",
                template_type="blueprint_approval",
                workflow_id=uuid4(),
                tenant_id=tenant_id
            )
        
        # Get metrics
        metrics = await email_service.get_delivery_metrics(tenant_id)
        
        assert metrics["total_sent"] >= 6, "Wrong total sent count"  # 1 + 5 emails
        assert metrics["delivery_rate"] >= 0, "Missing delivery rate"
        
        print("   ✅ Email delivery metrics working")
        print(f"   ✅ Total sent: {metrics['total_sent']}")
        print(f"   ✅ Delivery rate: {metrics['delivery_rate']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email delivery tracking test failed: {e}")
        return False


async def main():
    """Run comprehensive email service tests"""
    print("🚀 Email Service Integration Tests")
    print("=" * 50)
    
    test_results = []
    
    # Core functionality test (most critical)
    test_results.append(await test_email_service_core_functionality())
    
    # Template system validation
    test_results.append(await test_email_templates_and_formatting())
    
    # Delivery tracking system
    test_results.append(await test_email_delivery_tracking())
    
    print("\n" + "=" * 50)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        print("🎉 All Email Service Tests Passed!")
        print(f"✅ {passed_tests}/{total_tests} test suites successful")
        print("\nCore Email Capabilities Verified:")
        print("✅ Email Service: Template-based email generation")
        print("✅ Template System: Variable substitution and formatting")
        print("✅ Delivery System: Mock email delivery with tracking")
        print("✅ Delivery Logs: Complete audit trail and metrics")
        print("✅ Multiple Templates: Approval, progress, deployment emails")
        print("\n🚀 Ready to implement Email Service!")
        return True
    else:
        print("❌ Some tests failed - need to implement Email Service")
        print(f"❌ {total_tests - passed_tests}/{total_tests} test suites failed")
        return False


if __name__ == "__main__":
    asyncio.run(main())