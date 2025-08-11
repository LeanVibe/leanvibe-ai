#!/usr/bin/env python3
"""
Assembly Line Generation Progress Fix Test
Test-driven fix for GenerationProgress validation errors
"""

import asyncio
import sys
import os
from uuid import uuid4

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_assembly_line_generation_progress_creation():
    """
    Test that assembly line can create GenerationProgress without validation errors
    This test should FAIL initially, then PASS after we fix the bug
    """
    print("🔍 Testing Assembly Line GenerationProgress Creation...")
    
    try:
        from app.services.assembly_line_system import GenerationProgress, AgentType
        from app.models.mvp_models import TechnicalBlueprint, MVPTechStack
        
        # Test 1: Create GenerationProgress with minimal required fields
        print("\n1. Testing GenerationProgress creation...")
        
        mvp_project_id = uuid4()
        
        # This should NOT fail with validation errors
        progress = GenerationProgress(
            mvp_project_id=mvp_project_id,
            current_stage=AgentType.BACKEND
        )
        
        assert progress.mvp_project_id == mvp_project_id
        assert progress.current_stage == AgentType.BACKEND
        assert hasattr(progress, 'overall_progress')
        assert hasattr(progress, 'stage_progress')
        
        print(f"   ✅ GenerationProgress created successfully")
        print(f"   ✅ Overall progress: {progress.overall_progress}%")
        print(f"   ✅ Stage progress: {progress.stage_progress}%")
        
        # Test 2: Verify default values are reasonable
        assert progress.overall_progress >= 0 and progress.overall_progress <= 100
        assert progress.stage_progress >= 0 and progress.stage_progress <= 100
        
        print("   ✅ Progress values are within valid ranges")
        
        return True
        
    except Exception as e:
        print(f"❌ Assembly line generation progress test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_assembly_line_mvp_generation_start():
    """
    Test that we can start MVP generation without validation errors
    """
    print("\n🔍 Testing Assembly Line MVP Generation Start...")
    
    try:
        from app.services.assembly_line_system import AssemblyLineOrchestrator
        from app.models.mvp_models import TechnicalBlueprint, MVPTechStack
        
        # Create mock blueprint
        blueprint = TechnicalBlueprint(
            tech_stack=MVPTechStack.FULL_STACK_REACT,
            architecture_pattern="MVC",
            database_schema={"users": {"id": "uuid", "email": "string"}},
            api_endpoints=[{"name": "users", "method": "GET", "path": "/users"}],
            user_flows=[{"name": "user_registration", "steps": ["signup", "verify"]}],
            wireframes=[{"page": "home", "components": ["header", "main"]}],
            design_system={"colors": {"primary": "#3366cc"}},
            deployment_config={"platform": "vercel"},
            monitoring_config={"service": "datadog"},
            scaling_config={"auto_scale": True},
            test_strategy={"unit_tests": True, "integration_tests": True},
            performance_targets={"response_time": "< 500ms"},
            security_requirements=["https", "input_validation"],
            confidence_score=0.85,
            estimated_generation_time=360  # 6 hours
        )
        
        assembly_line = AssemblyLineOrchestrator()
        
        # This should NOT fail with GenerationProgress validation errors
        result = await assembly_line.start_mvp_generation(uuid4(), blueprint)
        
        # We don't expect the generation to fully succeed (no actual agents), 
        # but it shouldn't fail with validation errors
        print(f"   ✅ Assembly line start method executed without validation errors")
        print(f"   ✅ Result: {result}")
        
        return True
        
    except Exception as e:
        # Check if this is the specific validation error we're trying to fix
        if "Field required" in str(e) and ("overall_progress" in str(e) or "stage_progress" in str(e)):
            print(f"❌ EXPECTED FAILURE: GenerationProgress validation error: {e}")
            return False  # This is the bug we're fixing
        else:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Run assembly line generation fix tests"""
    print("🚀 Assembly Line Generation Fix Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: GenerationProgress creation
    test_results.append(await test_assembly_line_generation_progress_creation())
    
    # Test 2: MVP generation start
    test_results.append(await test_assembly_line_mvp_generation_start())
    
    print("\n" + "=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        print("🎉 ALL ASSEMBLY LINE TESTS PASSED!")
        print(f"✅ {passed_tests}/{total_tests} tests successful")
        print("\n🚀 Assembly Line GenerationProgress Fix Complete!")
        return True
    else:
        print("❌ SOME TESTS FAILED - BUG NEEDS FIXING")
        print(f"❌ {total_tests - passed_tests}/{total_tests} tests failed")
        print("🔧 Fix GenerationProgress model to have default values")
        return False


if __name__ == "__main__":
    asyncio.run(main())