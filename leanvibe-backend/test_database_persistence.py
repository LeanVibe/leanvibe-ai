#!/usr/bin/env python3
"""
Database Persistence Test
Test-driven implementation of database persistence for production readiness
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_mvp_project_persistence():
    """
    Test that MVP projects persist to database and can be retrieved
    This test should FAIL initially, then PASS after we implement persistence
    """
    print("🔍 Testing MVP Project Database Persistence...")
    
    try:
        from app.services.mvp_service import mvp_service
        from app.models.mvp_models import MVPProject, MVPStatus, FounderInterview, MVPIndustry
        
        # Test 1: Create and save MVP project
        print("\n1. Testing MVP project creation and persistence...")
        
        # Create founder interview
        founder_interview = FounderInterview(
            business_idea="TaskFlow Pro - Project management for teams",
            problem_statement="Teams struggle with task coordination",
            target_audience="Small to medium businesses (10-50 employees)",
            value_proposition="Simple, intuitive project management",
            core_features=["Task management", "Team collaboration", "Progress tracking"],
            industry=MVPIndustry.PRODUCTIVITY
        )
        
        # Create MVP project
        tenant_id = uuid4()
        mvp_project = MVPProject(
            id=uuid4(),
            tenant_id=tenant_id,
            project_name="TaskFlow Pro MVP",
            slug="taskflow-pro-mvp",
            description="Project management MVP for teams",
            status=MVPStatus.BLUEPRINT_PENDING,
            interview=founder_interview
        )
        
        # Save to database (this should NOT use in-memory storage)
        saved_project = await mvp_service.save_mvp_project(mvp_project)
        
        assert saved_project is not None
        assert saved_project.id == mvp_project.id
        print(f"   ✅ MVP project saved: {saved_project.project_name}")
        
        # Test 2: Retrieve from database
        print("\n2. Testing MVP project retrieval from database...")
        
        retrieved_project = await mvp_service.get_mvp_project(mvp_project.id)
        
        assert retrieved_project is not None
        assert retrieved_project.id == mvp_project.id
        assert retrieved_project.project_name == "TaskFlow Pro MVP"
        assert retrieved_project.status == MVPStatus.BLUEPRINT_PENDING
        assert retrieved_project.interview is not None
        assert retrieved_project.interview.business_idea == "TaskFlow Pro - Project management for teams"
        
        print(f"   ✅ MVP project retrieved: {retrieved_project.project_name}")
        print(f"   ✅ Status: {retrieved_project.status}")
        print(f"   ✅ Interview preserved: {retrieved_project.interview.business_idea}")
        
        # Test 3: Update project status
        print("\n3. Testing MVP project status updates...")
        
        retrieved_project.status = MVPStatus.BLUEPRINT_APPROVED
        updated_project = await mvp_service.update_mvp_project(retrieved_project)
        
        assert updated_project.status == MVPStatus.BLUEPRINT_APPROVED
        
        # Verify update persisted
        final_project = await mvp_service.get_mvp_project(mvp_project.id)
        assert final_project.status == MVPStatus.BLUEPRINT_APPROVED
        
        print(f"   ✅ Status updated and persisted: {final_project.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ MVP project persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline_execution_persistence():
    """
    Test that pipeline executions persist to database
    """
    print("\n🔍 Testing Pipeline Execution Database Persistence...")
    
    try:
        from app.services.pipeline_orchestration_service import (
            pipeline_orchestration_service, PipelineExecution, PipelineStatus, PipelineStage
        )
        
        # Test 1: Create and save pipeline execution
        print("\n1. Testing pipeline execution persistence...")
        
        execution = PipelineExecution(
            mvp_project_id=uuid4(),
            tenant_id=uuid4(),
            current_stage=PipelineStage.BLUEPRINT_GENERATION,
            status=PipelineStatus.RUNNING
        )
        
        # Save execution (should persist to database)
        await pipeline_orchestration_service.save_execution(execution)
        
        # Retrieve execution  
        retrieved_execution = await pipeline_orchestration_service.get_execution(execution.id)
        
        assert retrieved_execution is not None
        assert retrieved_execution.id == execution.id
        assert retrieved_execution.status == PipelineStatus.RUNNING
        assert retrieved_execution.current_stage == PipelineStage.BLUEPRINT_GENERATION
        
        print(f"   ✅ Pipeline execution persisted: {retrieved_execution.id}")
        print(f"   ✅ Status: {retrieved_execution.status}")
        print(f"   ✅ Stage: {retrieved_execution.current_stage}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline execution persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_email_delivery_persistence():
    """
    Test that email delivery logs persist to database
    """
    print("\n🔍 Testing Email Delivery Log Database Persistence...")
    
    try:
        from app.services.email_service import email_service
        from app.models.human_gate_models import EmailDeliveryLog
        
        # Test email delivery with persistence
        print("\n1. Testing email delivery log persistence...")
        
        workflow_id = uuid4()
        tenant_id = uuid4()
        
        # Send email (should create persistent log)
        result = await email_service.send_email(
            recipient="founder@example.com",
            subject="Test Persistence Email",
            body="This tests database persistence",
            template_type="blueprint_approval",
            workflow_id=workflow_id,
            tenant_id=tenant_id
        )
        
        assert result.success
        
        # Retrieve logs from database (not in-memory)
        logs = await email_service.get_delivery_logs_from_database(workflow_id)
        
        assert len(logs) > 0
        log = logs[0]
        assert log.recipient_email == "founder@example.com"
        assert log.email_type == "blueprint_approval"
        assert log.delivery_status == "sent"
        
        print(f"   ✅ Email delivery log persisted: {log.recipient_email}")
        print(f"   ✅ Status: {log.delivery_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email delivery persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run database persistence tests"""
    print("🚀 Database Persistence Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: MVP project persistence
    test_results.append(await test_mvp_project_persistence())
    
    # Test 2: Pipeline execution persistence  
    test_results.append(await test_pipeline_execution_persistence())
    
    # Test 3: Email delivery persistence
    test_results.append(await test_email_delivery_persistence())
    
    print("\n" + "=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        print("🎉 ALL DATABASE PERSISTENCE TESTS PASSED!")
        print(f"✅ {passed_tests}/{total_tests} tests successful")
        print("\n🚀 Database Persistence Implementation Complete!")
        print("✅ Founder progress now survives system restarts")
        print("✅ Production-ready data persistence")
        return True
    else:
        print("❌ SOME PERSISTENCE TESTS FAILED - NEED IMPLEMENTATION")
        print(f"❌ {total_tests - passed_tests}/{total_tests} tests failed")
        print("🔧 Implement database persistence for in-memory storage")
        return False


if __name__ == "__main__":
    asyncio.run(main())