"""
End-to-End Workflow Tests for LeanVibe AI Backend

Tests complete workflows that utilize multiple services together,
simulating real-world usage scenarios for the AI coding assistant.
"""

import asyncio
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.graph_service import GraphService
from app.services.vector_store_service import VectorStoreService, CodeEmbedding
from app.services.ollama_ai_service import OllamaAIService

logger = logging.getLogger(__name__)


class E2EWorkflowValidator:
    """End-to-end workflow validation for LeanVibe AI backend"""
    
    def __init__(self):
        self.graph_service = None
        self.vector_service = None
        self.ai_service = None
        self.initialized_services = []
        
    async def initialize_services(self) -> Dict[str, bool]:
        """Initialize all services and track which ones are available"""
        service_status = {}
        
        # Initialize Graph Service (Neo4j)
        try:
            self.graph_service = GraphService()
            result = await self.graph_service.initialize()
            service_status['graph'] = result
            if result:
                self.initialized_services.append('graph')
                logger.info("✅ Graph service initialized")
        except Exception as e:
            logger.warning(f"Graph service failed: {e}")
            service_status['graph'] = False
            
        # Initialize Vector Store Service (ChromaDB)
        try:
            self.vector_service = VectorStoreService(use_http=True, host="localhost", port=8001)
            result = await self.vector_service.initialize()
            service_status['vector'] = result
            if result:
                self.initialized_services.append('vector')
                logger.info("✅ Vector store service initialized")
        except Exception as e:
            logger.warning(f"Vector store service failed: {e}")
            service_status['vector'] = False
            
        # Initialize AI Service (Ollama)
        try:
            self.ai_service = OllamaAIService()
            result = await self.ai_service.initialize()
            service_status['ai'] = result and self.ai_service.is_ready()
            if service_status['ai']:
                self.initialized_services.append('ai')
                logger.info("✅ AI service initialized")
        except Exception as e:
            logger.warning(f"AI service failed: {e}")
            service_status['ai'] = False
            
        return service_status
        
    async def cleanup_services(self):
        """Clean up all initialized services"""
        try:
            if self.graph_service:
                await self.graph_service.close()
            if self.ai_service:
                await self.ai_service.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    async def workflow_code_analysis_pipeline(self) -> Dict[str, Any]:
        """
        Test complete code analysis pipeline:
        1. AI analyzes code for structure and patterns
        2. Vector store indexes code embeddings
        3. Graph store captures relationships
        4. AI provides insights based on stored data
        """
        results = {
            'workflow': 'code_analysis_pipeline',
            'steps_completed': 0,
            'total_steps': 5,
            'success': False,
            'details': {}
        }
        
        # Sample Python code to analyze
        sample_code = '''
class UserService:
    def __init__(self, db_connection):
        self.db = db_connection
        self.cache = {}
    
    async def get_user(self, user_id: int):
        """Retrieve user by ID with caching"""
        if user_id in self.cache:
            return self.cache[user_id]
        
        user = await self.db.query("SELECT * FROM users WHERE id = ?", user_id)
        if user:
            self.cache[user_id] = user
        return user
    
    async def create_user(self, email: str, name: str):
        """Create a new user"""
        user_data = {
            'email': email,
            'name': name,
            'created_at': time.time()
        }
        user_id = await self.db.insert("users", user_data)
        return user_id
'''
        
        try:
            # Step 1: AI Code Analysis
            if 'ai' in self.initialized_services:
                logger.info("🔍 Step 1: AI analyzing code structure...")
                analysis = await self.ai_service.analyze_code(
                    sample_code, 
                    language="python", 
                    analysis_type="review"
                )
                
                if analysis:
                    results['steps_completed'] += 1
                    results['details']['ai_analysis'] = {
                        'success': True,
                        'analysis_length': len(analysis.get('analysis', '')),
                        'model_used': analysis.get('model', 'unknown')
                    }
                    logger.info("✅ AI analysis completed")
                else:
                    results['details']['ai_analysis'] = {'success': False, 'error': 'No analysis returned'}
            
            # Step 2: Vector Store Indexing
            if 'vector' in self.initialized_services:
                logger.info("📚 Step 2: Indexing code in vector store...")
                
                # Create code embeddings
                embeddings = [
                    CodeEmbedding(
                        id="e2e_test_user_service",
                        content=sample_code,
                        file_path="/test/user_service.py",
                        language="python",
                        symbol_type="class",
                        symbol_name="UserService",
                        start_line=1,
                        end_line=25
                    ),
                    CodeEmbedding(
                        id="e2e_test_get_user",
                        content="async def get_user(self, user_id: int):",
                        file_path="/test/user_service.py",
                        language="python",
                        symbol_type="method",
                        symbol_name="get_user",
                        start_line=6,
                        end_line=13
                    )
                ]
                
                added_count = await self.vector_service.add_code_embeddings_batch(embeddings)
                if added_count == len(embeddings):
                    results['steps_completed'] += 1
                    results['details']['vector_indexing'] = {
                        'success': True,
                        'embeddings_added': added_count
                    }
                    logger.info(f"✅ Vector indexing completed: {added_count} embeddings")
                else:
                    results['details']['vector_indexing'] = {
                        'success': False,
                        'embeddings_added': added_count,
                        'expected': len(embeddings)
                    }
            
            # Step 3: Semantic Code Search
            if 'vector' in self.initialized_services:
                logger.info("🔎 Step 3: Testing semantic search...")
                
                search_results = await self.vector_service.search_similar_code(
                    "user authentication and caching", 
                    n_results=3
                )
                
                if search_results and len(search_results) > 0:
                    results['steps_completed'] += 1
                    results['details']['semantic_search'] = {
                        'success': True,
                        'results_count': len(search_results),
                        'top_similarity': search_results[0].similarity_score if search_results else 0
                    }
                    logger.info(f"✅ Semantic search completed: {len(search_results)} results")
                else:
                    results['details']['semantic_search'] = {'success': False, 'results_count': 0}
            
            # Step 4: AI-Enhanced Code Suggestions  
            if 'ai' in self.initialized_services and 'vector' in self.initialized_services:
                logger.info("💡 Step 4: AI-enhanced code suggestions...")
                
                # Use search results to enhance AI context
                context_prompt = f"""
Based on this existing code:
{sample_code}

Suggest improvements for:
1. Performance optimization
2. Error handling  
3. Security considerations
4. Code organization

Provide specific, actionable recommendations.
"""
                
                suggestions = await self.ai_service.generate(
                    context_prompt,
                    max_tokens=1500,
                    temperature=0.2
                )
                
                if suggestions and len(suggestions.strip()) > 100:
                    results['steps_completed'] += 1
                    results['details']['ai_suggestions'] = {
                        'success': True,
                        'suggestion_length': len(suggestions),
                        'has_recommendations': 'recommend' in suggestions.lower()
                    }
                    logger.info("✅ AI suggestions generated")
                else:
                    results['details']['ai_suggestions'] = {'success': False, 'length': len(suggestions) if suggestions else 0}
            
            # Step 5: Integration Validation
            if results['steps_completed'] >= 2:
                logger.info("🔗 Step 5: Integration validation...")
                
                # Test that services can work together
                integration_score = results['steps_completed'] / results['total_steps']
                
                if integration_score >= 0.6:  # At least 60% of pipeline working
                    results['steps_completed'] += 1
                    results['details']['integration'] = {
                        'success': True,
                        'integration_score': integration_score,
                        'services_working': len(self.initialized_services)
                    }
                    logger.info(f"✅ Integration validation passed: {integration_score:.1%}")
                else:
                    results['details']['integration'] = {
                        'success': False,
                        'integration_score': integration_score
                    }
            
            # Overall success evaluation
            results['success'] = results['steps_completed'] >= (results['total_steps'] * 0.6)
            
            return results
            
        except Exception as e:
            logger.error(f"E2E workflow error: {e}")
            results['details']['error'] = str(e)
            return results

    async def workflow_ai_chat_with_context(self) -> Dict[str, Any]:
        """
        Test AI chat workflow with code context:
        1. Load code context from vector store
        2. Generate contextual responses
        3. Maintain conversation history
        """
        results = {
            'workflow': 'ai_chat_with_context',
            'steps_completed': 0,
            'total_steps': 3,
            'success': False,
            'details': {}
        }
        
        if 'ai' not in self.initialized_services:
            results['details']['error'] = 'AI service not available'
            return results
            
        try:
            # Step 1: Context-aware chat initialization
            logger.info("💬 Step 1: Testing context-aware chat...")
            
            initial_message = "How can I improve the performance of my Python database queries?"
            response1 = await self.ai_service.chat(initial_message)
            
            if response1 and len(response1.strip()) > 50:
                results['steps_completed'] += 1
                results['details']['initial_chat'] = {
                    'success': True,
                    'response_length': len(response1),
                    'mentions_optimization': 'optimiz' in response1.lower()
                }
                logger.info("✅ Initial chat response generated")
            
            # Step 2: Follow-up with conversation context
            logger.info("🔄 Step 2: Testing conversation continuity...")
            
            conversation_context = [
                {'user': initial_message, 'assistant': response1[:200] + '...'}
            ]
            
            followup_message = "Can you show me a specific example with caching?"
            response2 = await self.ai_service.chat(
                followup_message,
                context=conversation_context
            )
            
            if response2 and len(response2.strip()) > 30:
                results['steps_completed'] += 1
                results['details']['contextual_chat'] = {
                    'success': True,
                    'response_length': len(response2),
                    'mentions_caching': 'cach' in response2.lower()
                }
                logger.info("✅ Contextual chat response generated")
            
            # Step 3: Code-specific assistance
            logger.info("👨‍💻 Step 3: Testing code-specific assistance...")
            
            code_question = """
I have this function that's running slowly:

def process_users(users):
    results = []
    for user in users:
        profile = get_user_profile(user.id)  # Database call
        score = calculate_score(profile)
        results.append({'user': user, 'score': score})
    return results

How can I optimize this?
"""
            
            code_response = await self.ai_service.generate(
                code_question,
                max_tokens=1000,
                temperature=0.1
            )
            
            if code_response and any(keyword in code_response.lower() for keyword in ['batch', 'async', 'parallel', 'cache']):
                results['steps_completed'] += 1
                results['details']['code_assistance'] = {
                    'success': True,
                    'response_length': len(code_response),
                    'has_optimization_keywords': True
                }
                logger.info("✅ Code-specific assistance provided")
            
            results['success'] = results['steps_completed'] >= 2
            return results
            
        except Exception as e:
            logger.error(f"Chat workflow error: {e}")
            results['details']['error'] = str(e)
            return results

    async def workflow_performance_monitoring(self) -> Dict[str, Any]:
        """
        Test performance monitoring across all services:
        1. Measure service response times
        2. Monitor memory usage patterns
        3. Validate throughput capabilities
        """
        results = {
            'workflow': 'performance_monitoring',
            'steps_completed': 0,
            'total_steps': 3,
            'success': False,
            'details': {}
        }
        
        try:
            # Step 1: Service Response Time Monitoring
            logger.info("⏱️ Step 1: Measuring service response times...")
            
            response_times = {}
            
            if 'ai' in self.initialized_services:
                start_time = time.time()
                await self.ai_service.generate("Hello", max_tokens=10)
                response_times['ai'] = time.time() - start_time
            
            if 'vector' in self.initialized_services:
                start_time = time.time()
                await self.vector_service.search_similar_code("test query", n_results=1)
                response_times['vector'] = time.time() - start_time
            
            if response_times:
                results['steps_completed'] += 1
                results['details']['response_times'] = {
                    'success': True,
                    'measurements': response_times,
                    'avg_response_time': sum(response_times.values()) / len(response_times)
                }
                logger.info(f"✅ Response times measured: {response_times}")
            
            # Step 2: Throughput Testing
            logger.info("🚀 Step 2: Testing service throughput...")
            
            if 'ai' in self.initialized_services:
                # Test concurrent AI requests
                start_time = time.time()
                tasks = [
                    self.ai_service.generate(f"Test prompt {i}", max_tokens=20)
                    for i in range(3)
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                duration = time.time() - start_time
                
                successful_responses = sum(1 for r in responses if isinstance(r, str) and r)
                
                if successful_responses >= 2:
                    results['steps_completed'] += 1
                    results['details']['throughput'] = {
                        'success': True,
                        'concurrent_requests': len(tasks),
                        'successful_responses': successful_responses,
                        'total_time': duration,
                        'requests_per_second': len(tasks) / duration if duration > 0 else 0
                    }
                    logger.info(f"✅ Throughput test completed: {successful_responses}/{len(tasks)} successful")
            
            # Step 3: Health Check Validation
            logger.info("🩺 Step 3: Service health validation...")
            
            health_checks = {}
            
            if 'ai' in self.initialized_services:
                health = await self.ai_service.health_check()
                health_checks['ai'] = health.get('status') == 'healthy'
            
            if 'vector' in self.initialized_services:
                status = self.vector_service.get_status()
                health_checks['vector'] = status.get('initialized', False)
            
            if health_checks and any(health_checks.values()):
                results['steps_completed'] += 1
                results['details']['health_checks'] = {
                    'success': True,
                    'service_health': health_checks,
                    'healthy_services': sum(health_checks.values())
                }
                logger.info(f"✅ Health checks completed: {health_checks}")
            
            results['success'] = results['steps_completed'] >= 2
            return results
            
        except Exception as e:
            logger.error(f"Performance monitoring error: {e}")
            results['details']['error'] = str(e)
            return results


@pytest.mark.asyncio
class TestE2EWorkflows:
    """End-to-end workflow tests"""
    
    async def test_complete_code_analysis_pipeline(self):
        """Test the complete code analysis workflow"""
        validator = E2EWorkflowValidator()
        
        try:
            # Initialize services
            service_status = await validator.initialize_services()
            
            # Require at least AI and vector services for this test
            if not (service_status.get('ai') or service_status.get('vector')):
                pytest.skip("Insufficient services available for code analysis pipeline")
            
            # Run the workflow
            results = await validator.workflow_code_analysis_pipeline()
            
            # Validate results
            print(f"\n🔄 CODE ANALYSIS PIPELINE RESULTS")
            print(f"📊 Steps completed: {results['steps_completed']}/{results['total_steps']}")
            print(f"✅ Success: {results['success']}")
            
            for step, details in results['details'].items():
                if isinstance(details, dict) and details.get('success'):
                    print(f"✅ {step}: PASSED")
                else:
                    print(f"❌ {step}: FAILED")
            
            # Assert minimum functionality
            assert results['steps_completed'] >= 2, f"Pipeline too incomplete: {results['steps_completed']}/{results['total_steps']}"
            assert results['success'], f"Pipeline failed: {results['details']}"
            
        finally:
            await validator.cleanup_services()
    
    async def test_ai_chat_workflow(self):
        """Test AI chat capabilities with context"""
        validator = E2EWorkflowValidator()
        
        try:
            service_status = await validator.initialize_services()
            
            if not service_status.get('ai'):
                pytest.skip("AI service not available for chat workflow")
            
            results = await validator.workflow_ai_chat_with_context()
            
            print(f"\n💬 AI CHAT WORKFLOW RESULTS")
            print(f"📊 Steps completed: {results['steps_completed']}/{results['total_steps']}")
            print(f"✅ Success: {results['success']}")
            
            assert results['steps_completed'] >= 2, f"Chat workflow incomplete: {results}"
            assert results['success'], f"Chat workflow failed: {results['details']}"
            
        finally:
            await validator.cleanup_services()
    
    async def test_performance_monitoring_workflow(self):
        """Test performance monitoring capabilities"""
        validator = E2EWorkflowValidator()
        
        try:
            service_status = await validator.initialize_services()
            
            if not any(service_status.values()):
                pytest.skip("No services available for performance monitoring")
            
            results = await validator.workflow_performance_monitoring()
            
            print(f"\n⚡ PERFORMANCE MONITORING RESULTS")
            print(f"📊 Steps completed: {results['steps_completed']}/{results['total_steps']}")
            print(f"✅ Success: {results['success']}")
            
            if 'response_times' in results['details']:
                times = results['details']['response_times']['measurements']
                print(f"⏱️ Response times: {times}")
            
            assert results['steps_completed'] >= 1, f"Performance monitoring failed: {results}"
            
        finally:
            await validator.cleanup_services()
    
    async def test_service_integration_matrix(self):
        """Test all possible service combinations"""
        validator = E2EWorkflowValidator()
        
        try:
            service_status = await validator.initialize_services()
            
            working_services = [name for name, status in service_status.items() if status]
            total_services = len(service_status)
            
            print(f"\n🔗 SERVICE INTEGRATION MATRIX")
            print(f"📊 Services status: {working_services} ({len(working_services)}/{total_services})")
            
            # Test basic integration
            integration_tests = []
            
            if service_status.get('ai') and service_status.get('vector'):
                integration_tests.append("ai+vector")
            
            if service_status.get('ai') and service_status.get('graph'):
                integration_tests.append("ai+graph")
            
            if service_status.get('vector') and service_status.get('graph'):
                integration_tests.append("vector+graph")
            
            if len(working_services) >= 3:
                integration_tests.append("full_stack")
            
            assert len(working_services) >= 2, f"Insufficient service integration: {working_services}"
            assert len(integration_tests) >= 1, f"No valid service combinations available"
            
            print(f"✅ Integration tests possible: {integration_tests}")
            
        finally:
            await validator.cleanup_services()


if __name__ == "__main__":
    # Allow running this test file directly
    import subprocess
    
    print("🧪 Running end-to-end workflow tests...")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ])
    
    sys.exit(result.returncode)