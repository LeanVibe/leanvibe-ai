#!/usr/bin/env python3
"""
Phase 1B Integration Tests - Blueprint System & Human Gate Workflows
Test-driven implementation of core autonomous MVP generation pipeline
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_core_blueprint_generation_pipeline():
    """
    Test the core value delivery: Interview → Blueprint → Approval → MVP Generation
    This is our 20% that delivers 80% of the value
    """
    print("🔍 Testing Core Blueprint Generation Pipeline...")
    
    try:
        from app.services.agents.ai_architect_agent import AIArchitectAgent
        from app.models.mvp_models import FounderInterview, MVPIndustry
        
        # Test 1: AI Architect Agent can process a founder interview
        print("\n1. Testing AI Architect Agent...")
        ai_architect = AIArchitectAgent()
        
        # Create realistic founder interview
        founder_interview = FounderInterview(
            business_idea="TaskFlow Pro - AI-powered task management for small business teams",
            problem_statement="Small businesses struggle with task coordination and team productivity",
            target_audience="Small business owners with 5-50 employees",
            value_proposition="AI-powered task prioritization with seamless team collaboration",
            market_size="$50M addressable market in SMB productivity tools",
            competition="Competing with Asana, Trello, Monday.com - differentiated by AI prioritization",
            core_features=[
                "Task creation and management",
                "AI-powered task prioritization", 
                "Team collaboration and comments",
                "Real-time progress tracking",
                "Slack integration",
                "Custom workflow templates"
            ],
            nice_to_have_features=[
                "Mobile app",
                "Time tracking",
                "Advanced reporting",
                "API for integrations"
            ],
            revenue_model="Subscription SaaS - $15/user/month",
            pricing_strategy="Freemium model with 14-day trial",
            go_to_market="Direct sales + content marketing + partner channels",
            technical_constraints=["Must integrate with Slack", "Support 100+ concurrent users"],
            integration_requirements=["Slack API", "Google Calendar API", "Email notifications"],
            industry=MVPIndustry.PRODUCTIVITY
        )
        
        print(f"   ✅ Created founder interview for: {founder_interview.business_idea}")
        
        # Generate technical blueprint
        start_time = datetime.utcnow()
        blueprint = await ai_architect.analyze_founder_interview(founder_interview)
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        print(f"   ✅ Generated blueprint in {generation_time:.1f}s")
        print(f"   ✅ Tech stack: {blueprint.tech_stack}")
        print(f"   ✅ Confidence score: {blueprint.confidence_score:.2f}")
        print(f"   ✅ Database tables: {len(blueprint.database_schema.get('tables', {}))}")
        print(f"   ✅ API endpoints: {len(blueprint.api_endpoints)}")
        print(f"   ✅ User flows: {len(blueprint.user_flows)}")
        
        # Verify blueprint quality
        assert blueprint.confidence_score > 0.5, "Blueprint confidence too low"
        assert len(blueprint.api_endpoints) > 5, "Not enough API endpoints generated"
        assert len(blueprint.database_schema.get('tables', {})) > 2, "Not enough database tables"
        assert blueprint.estimated_generation_time > 0, "No time estimate provided"
        
        print("   ✅ Blueprint quality validation passed")
        
        # Test 2: Human Gate Workflow System
        print("\n2. Testing Human Gate Workflow System...")
        from app.services.human_gate_service import human_gate_service
        from app.models.human_gate_models import CreateWorkflowRequest, WorkflowType, FeedbackType, FounderFeedback
        
        tenant_id = uuid4()
        founder_email = "founder@taskflowpro.com"
        
        # Create approval workflow
        workflow_request = CreateWorkflowRequest(
            mvp_project_id=uuid4(),
            workflow_type=WorkflowType.BLUEPRINT_APPROVAL,
            founder_email=founder_email,
            workflow_title="Review Your TaskFlow Pro Blueprint",
            workflow_description="Please review the technical blueprint generated for your MVP",
            context_data={
                "tech_stack": str(blueprint.tech_stack),
                "confidence_score": blueprint.confidence_score,
                "estimated_hours": blueprint.estimated_generation_time
            }
        )
        
        workflow = await human_gate_service.create_approval_workflow(workflow_request, tenant_id)
        
        print(f"   ✅ Created approval workflow: {workflow.id}")
        print(f"   ✅ Approval token generated: {len(workflow.approval_token)} chars")
        print(f"   ✅ Approval URL: {workflow.approval_url}")
        print(f"   ✅ Expires at: {workflow.expires_at}")
        
        # Verify workflow security
        assert len(workflow.approval_token) > 50, "Token too short"
        assert workflow.approval_url.startswith("https://"), "URL not secure"
        assert workflow.founder_email == founder_email, "Email mismatch"
        
        # Test 3: Token Validation and Founder Feedback
        print("\n3. Testing Token Validation and Founder Feedback...")
        
        # Validate token works
        retrieved_workflow = await human_gate_service.get_workflow_by_token(workflow.approval_token)
        assert retrieved_workflow is not None, "Token validation failed"
        assert retrieved_workflow.id == workflow.id, "Workflow mismatch"
        
        print("   ✅ Token validation successful")
        
        # Submit founder feedback (approval)
        founder_feedback = FounderFeedback(
            workflow_id=workflow.id,
            feedback_type=FeedbackType.APPROVE,
            overall_comments="The blueprint looks excellent! I'm excited to see the MVP built.",
            satisfaction_score=9,
            timeline_expectations="Looking forward to having this completed within the estimated timeframe"
        )
        
        success = await human_gate_service.submit_founder_feedback(
            workflow.approval_token, 
            founder_feedback
        )
        
        assert success, "Feedback submission failed"
        
        # Verify workflow status updated
        updated_workflow = await human_gate_service.get_workflow_by_token(workflow.approval_token)
        assert updated_workflow.status.value == "approved", "Workflow status not updated"
        assert updated_workflow.response_time_hours is not None, "Response time not recorded"
        
        print("   ✅ Founder feedback processed successfully")
        print(f"   ✅ Workflow status: {updated_workflow.status}")
        print(f"   ✅ Response time: {updated_workflow.response_time_hours:.1f} hours")
        
        # Test 4: Integration with Assembly Line System
        print("\n4. Testing Assembly Line System Integration...")
        from app.services.mvp_service import mvp_service
        from app.models.mvp_models import MVPProject, MVPStatus
        
        # Create MVP project with blueprint
        mvp_project = MVPProject(
            id=workflow_request.mvp_project_id,
            tenant_id=tenant_id,
            project_name="TaskFlow Pro MVP",
            slug="taskflow-pro-mvp",
            description="AI-powered task management for small business teams",
            status=MVPStatus.BLUEPRINT_APPROVED,
            interview=founder_interview,
            blueprint=blueprint,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await mvp_service._save_mvp_project(mvp_project)
        
        # Verify project can start generation
        retrieved_project = await mvp_service.get_mvp_project(mvp_project.id)
        assert retrieved_project is not None, "Project not saved"
        assert retrieved_project.status == MVPStatus.BLUEPRINT_APPROVED, "Project not ready for generation"
        
        print("   ✅ MVP project created with approved blueprint")
        print(f"   ✅ Project status: {retrieved_project.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Core pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_blueprint_generation_performance():
    """Test that blueprint generation meets performance targets"""
    print("\n🔍 Testing Blueprint Generation Performance...")
    
    try:
        from app.services.agents.ai_architect_agent import AIArchitectAgent
        from app.models.mvp_models import FounderInterview, MVPIndustry
        
        ai_architect = AIArchitectAgent()
        
        # Test with different complexity levels
        test_cases = [
            {
                "name": "Simple MVP",
                "features": ["User registration", "Task creation", "Task list"],
                "expected_max_time": 30
            },
            {
                "name": "Medium MVP", 
                "features": ["User auth", "Task management", "Team collaboration", "Notifications", "Reports"],
                "expected_max_time": 30
            },
            {
                "name": "Complex MVP",
                "features": [
                    "Multi-tenant architecture", "Advanced user roles", "API integrations",
                    "Real-time notifications", "Advanced analytics", "Payment processing",
                    "Mobile app", "Third-party integrations"
                ],
                "expected_max_time": 35
            }
        ]
        
        for test_case in test_cases:
            print(f"\n   Testing {test_case['name']}...")
            
            interview = FounderInterview(
                business_idea=f"Test MVP - {test_case['name']}",
                problem_statement="Test problem",
                target_audience="Test audience",
                value_proposition="Test value",
                core_features=test_case["features"],
                industry=MVPIndustry.PRODUCTIVITY
            )
            
            start_time = datetime.utcnow()
            blueprint = await ai_architect.analyze_founder_interview(interview)
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            print(f"     ✅ Generated in {generation_time:.1f}s (target: <{test_case['expected_max_time']}s)")
            print(f"     ✅ Confidence: {blueprint.confidence_score:.2f}")
            
            assert generation_time < test_case["expected_max_time"], f"Generation too slow: {generation_time}s"
            assert blueprint.confidence_score > 0.4, "Confidence too low"
        
        print("   ✅ All performance tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


async def test_security_and_edge_cases():
    """Test security measures and edge cases"""
    print("\n🔍 Testing Security and Edge Cases...")
    
    try:
        from app.services.human_gate_service import human_gate_service
        
        # Test 1: Invalid tokens
        print("   Testing invalid token handling...")
        invalid_tokens = [
            "invalid-token",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",  # Invalid JWT
            "expired.token.here"
        ]
        
        for token in invalid_tokens:
            workflow = await human_gate_service.get_workflow_by_token(token)
            assert workflow is None, f"Invalid token accepted: {token}"
        
        print("   ✅ Invalid tokens properly rejected")
        
        # Test 2: Expired workflows
        print("   Testing workflow expiration...")
        from app.models.human_gate_models import CreateWorkflowRequest, WorkflowType, ApprovalPriority, WorkflowStatus
        from datetime import timedelta
        
        # Create workflow that expires quickly for testing
        workflow_request = CreateWorkflowRequest(
            mvp_project_id=uuid4(),
            workflow_type=WorkflowType.BLUEPRINT_APPROVAL,
            founder_email="test@example.com",
            workflow_title="Test Expiration",
            workflow_description="Test workflow expiration",
            priority=ApprovalPriority.URGENT  # 12 hour expiration
        )
        
        workflow = await human_gate_service.create_approval_workflow(workflow_request, uuid4())
        
        # Manually set expiration to past (simulate expired workflow)
        workflow.expires_at = datetime.utcnow() - timedelta(hours=1)
        await human_gate_service._update_workflow(workflow)
        
        # Verify workflow is properly expired
        updated_workflow = await human_gate_service._get_workflow(workflow.id)
        assert updated_workflow.is_expired(), "Workflow should be expired for test"
        
        # Try to submit feedback to expired workflow - this will set status to EXPIRED
        from app.models.human_gate_models import FounderFeedback, FeedbackType
        
        feedback = FounderFeedback(
            workflow_id=workflow.id,
            feedback_type=FeedbackType.APPROVE
        )
        
        try:
            await human_gate_service.submit_founder_feedback(workflow.approval_token, feedback)
            assert False, "Expired workflow accepted feedback"
        except Exception as e:
            assert "expired" in str(e).lower(), "Wrong error for expired workflow"
        
        print("   ✅ Expired workflows properly handled")
        
        # Now test cleanup - create a new expired workflow that hasn't been processed yet
        print("   Creating fresh expired workflow for cleanup test...")
        cleanup_workflow_request = CreateWorkflowRequest(
            mvp_project_id=uuid4(),
            workflow_type=WorkflowType.BLUEPRINT_APPROVAL,
            founder_email="cleanup-test@example.com",
            workflow_title="Test Cleanup",
            workflow_description="Test workflow cleanup",
            priority=ApprovalPriority.URGENT
        )
        
        cleanup_workflow = await human_gate_service.create_approval_workflow(cleanup_workflow_request, uuid4())
        
        # Make it expired but keep status as PENDING
        cleanup_workflow.expires_at = datetime.utcnow() - timedelta(hours=2)
        await human_gate_service._update_workflow(cleanup_workflow)
        
        # Verify it's PENDING but expired
        assert cleanup_workflow.status == WorkflowStatus.PENDING, "Cleanup test workflow should be PENDING"
        assert cleanup_workflow.is_expired(), "Cleanup test workflow should be expired"
        
        # Test 3: Cleanup expired workflows
        print("   Testing automated cleanup...")
        
        # Debug: Check workflow state before cleanup
        debug_workflow = await human_gate_service._get_workflow(workflow.id)
        print(f"     Debug - Workflow status before cleanup: {debug_workflow.status}")
        print(f"     Debug - Workflow expires at: {debug_workflow.expires_at}")
        print(f"     Debug - Current time: {datetime.utcnow()}")
        print(f"     Debug - Is expired: {debug_workflow.is_expired()}")
        
        cleanup_count = await human_gate_service.cleanup_expired_workflows()
        print(f"     Debug - Cleanup count: {cleanup_count}")
        
        # Check workflow status after cleanup
        debug_workflow_after = await human_gate_service._get_workflow(workflow.id)
        print(f"     Debug - Workflow status after cleanup: {debug_workflow_after.status}")
        
        assert cleanup_count >= 1, f"Expired workflow not cleaned up - cleanup count: {cleanup_count}"
        
        print(f"   ✅ Cleaned up {cleanup_count} expired workflows")
        
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run comprehensive Phase 1B integration tests"""
    print("🚀 Phase 1B Blueprint System Integration Tests")
    print("=" * 60)
    
    test_results = []
    
    # Core pipeline test (most critical)
    test_results.append(await test_core_blueprint_generation_pipeline())
    
    # Performance validation
    test_results.append(await test_blueprint_generation_performance())
    
    # Security and edge cases
    test_results.append(await test_security_and_edge_cases())
    
    print("\n" + "=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        print("🎉 All Phase 1B Integration Tests Passed!")
        print(f"✅ {passed_tests}/{total_tests} test suites successful")
        print("\nCore Capabilities Verified:")
        print("✅ AI Architect Agent: Interview → Blueprint (< 30s)")
        print("✅ Human Gate Workflow: Secure founder approval system")
        print("✅ Token Security: JWT-based authentication")
        print("✅ Founder Feedback: Approval/rejection processing")
        print("✅ Assembly Line Integration: MVP project lifecycle")
        print("✅ Performance: Meets all timing requirements")
        print("✅ Security: Token validation and expiration handling")
        print("\n🚀 Ready for Phase 1B Production Deployment!")
        return True
    else:
        print("❌ Some tests failed - requires attention")
        print(f"❌ {total_tests - passed_tests}/{total_tests} test suites failed")
        return False


if __name__ == "__main__":
    asyncio.run(main())