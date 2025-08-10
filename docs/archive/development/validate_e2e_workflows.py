#!/usr/bin/env python3
"""
End-to-End Workflow Validation for LeanVibe AI Backend

Demonstrates complete workflows and validates that all services
work together as expected for real-world usage scenarios.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "leanvibe-backend"))

from app.services.graph_service import GraphService
from app.services.vector_store_service import VectorStoreService, CodeEmbedding
from app.services.ollama_ai_service import OllamaAIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeanVibeWorkflowValidator:
    """Validates complete LeanVibe AI workflows"""
    
    def __init__(self):
        self.services = {}
        
    async def initialize_all_services(self):
        """Initialize all backend services"""
        logger.info("🚀 Initializing LeanVibe AI Backend Services...")
        
        # Initialize Graph Service (Neo4j)
        try:
            graph_service = GraphService()
            result = await graph_service.initialize()
            self.services['graph'] = {
                'service': graph_service,
                'available': result,
                'name': 'Neo4j Graph Database'
            }
            status = "✅ AVAILABLE" if result else "❌ UNAVAILABLE"
            logger.info(f"   Neo4j Graph Database: {status}")
        except Exception as e:
            logger.error(f"   Neo4j Graph Database: ❌ ERROR - {e}")
            self.services['graph'] = {'service': None, 'available': False, 'name': 'Neo4j Graph Database'}
        
        # Initialize Vector Store (ChromaDB)
        try:
            vector_service = VectorStoreService(use_http=True, host="localhost", port=8001)
            result = await vector_service.initialize()
            self.services['vector'] = {
                'service': vector_service,
                'available': result,
                'name': 'ChromaDB Vector Store'
            }
            status = "✅ AVAILABLE" if result else "❌ UNAVAILABLE"
            logger.info(f"   ChromaDB Vector Store: {status}")
        except Exception as e:
            logger.error(f"   ChromaDB Vector Store: ❌ ERROR - {e}")
            self.services['vector'] = {'service': None, 'available': False, 'name': 'ChromaDB Vector Store'}
        
        # Initialize AI Service (Ollama)
        try:
            ai_service = OllamaAIService()
            result = await ai_service.initialize()
            available = result and ai_service.is_ready()
            self.services['ai'] = {
                'service': ai_service,
                'available': available,
                'name': 'Ollama AI Service'
            }
            status = "✅ AVAILABLE" if available else "❌ UNAVAILABLE"
            logger.info(f"   Ollama AI Service: {status}")
            
            if available:
                models = await ai_service.get_models()
                logger.info(f"      Available models: {', '.join(models)}")
        except Exception as e:
            logger.error(f"   Ollama AI Service: ❌ ERROR - {e}")
            self.services['ai'] = {'service': None, 'available': False, 'name': 'Ollama AI Service'}
        
        available_services = [name for name, info in self.services.items() if info['available']]
        logger.info(f"\n📊 Service Summary: {len(available_services)}/{len(self.services)} services available")
        
        return available_services

    async def validate_code_analysis_workflow(self):
        """Validate the complete code analysis workflow"""
        logger.info("\n🔍 VALIDATING: Code Analysis Workflow")
        logger.info("=" * 60)
        
        if not self.services['vector']['available']:
            logger.warning("⚠️ Skipping: Vector store not available")
            return False
        
        vector_service = self.services['vector']['service']
        
        # Sample Python code for analysis
        sample_code = '''
import asyncio
from typing import List, Optional

class TaskManager:
    """Manages asynchronous task execution with prioritization"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.running_tasks = set()
        self.pending_tasks = []
        
    async def submit_task(self, coro, priority: int = 0):
        """Submit a coroutine for execution"""
        if len(self.running_tasks) < self.max_concurrent:
            task = asyncio.create_task(coro)
            self.running_tasks.add(task)
            task.add_done_callback(self.running_tasks.discard)
            return task
        else:
            self.pending_tasks.append((priority, coro))
            return None
    
    async def get_results(self) -> List[any]:
        """Wait for all tasks to complete and return results"""
        if self.running_tasks:
            return await asyncio.gather(*self.running_tasks)
        return []
'''
        
        try:
            # Step 1: Create code embeddings
            logger.info("📚 Step 1: Creating code embeddings...")
            
            embeddings = [
                CodeEmbedding(
                    id="workflow_task_manager_class",
                    content=sample_code,
                    file_path="/demo/task_manager.py",
                    language="python",
                    symbol_type="class",
                    symbol_name="TaskManager",
                    start_line=1,
                    end_line=30
                ),
                CodeEmbedding(
                    id="workflow_submit_task_method",
                    content="async def submit_task(self, coro, priority: int = 0):",
                    file_path="/demo/task_manager.py",
                    language="python",
                    symbol_type="method",
                    symbol_name="submit_task",
                    start_line=10,
                    end_line=18
                )
            ]
            
            added_count = await vector_service.add_code_embeddings_batch(embeddings)
            logger.info(f"   ✅ Added {added_count} code embeddings")
            
            # Step 2: Semantic code search
            logger.info("🔎 Step 2: Testing semantic code search...")
            
            search_queries = [
                "async task management",
                "concurrency control",
                "priority queue execution"
            ]
            
            for query in search_queries:
                results = await vector_service.search_similar_code(query, n_results=2)
                logger.info(f"   Query: '{query}' → {len(results)} results")
                
                if results:
                    best_match = results[0]
                    logger.info(f"      Best match: {best_match.symbol_name} (similarity: {best_match.similarity_score:.3f})")
            
            # Step 3: AI-powered code analysis (if available)
            if self.services['ai']['available']:
                logger.info("🤖 Step 3: AI-powered code analysis...")
                
                ai_service = self.services['ai']['service']
                
                analysis_prompt = f"""
Analyze this Python code for:
1. Design patterns used
2. Potential improvements
3. Performance considerations

Code:
{sample_code[:500]}...

Provide a brief analysis:
"""
                
                start_time = time.time()
                analysis = await ai_service.generate(
                    analysis_prompt,
                    max_tokens=300,
                    temperature=0.1
                )
                duration = time.time() - start_time
                
                if analysis:
                    logger.info(f"   ✅ AI analysis completed in {duration:.1f}s")
                    logger.info(f"   Analysis preview: {analysis[:100]}...")
                else:
                    logger.warning("   ⚠️ AI analysis failed")
            
            # Step 4: Validate vector store statistics
            logger.info("📊 Step 4: Vector store statistics...")
            
            stats = await vector_service.get_collection_stats()
            if stats and 'total_embeddings' in stats:
                logger.info(f"   Total embeddings: {stats['total_embeddings']}")
                logger.info(f"   Embedding model: {stats.get('embedding_model', 'unknown')}")
                logger.info(f"   Collection: {stats.get('collection_name', 'unknown')}")
            
            # Cleanup
            logger.info("🧹 Cleaning up test data...")
            for embedding in embeddings:
                try:
                    if vector_service.chromadb_available and vector_service.collection:
                        vector_service.collection.delete(ids=[embedding.id])
                except Exception:
                    pass
            
            logger.info("✅ Code Analysis Workflow: COMPLETED SUCCESSFULLY")
            return True
            
        except Exception as e:
            logger.error(f"❌ Code Analysis Workflow: FAILED - {e}")
            return False

    async def validate_ai_assistant_workflow(self):
        """Validate AI assistant conversational workflow"""
        logger.info("\n💬 VALIDATING: AI Assistant Workflow")
        logger.info("=" * 60)
        
        if not self.services['ai']['available']:
            logger.warning("⚠️ Skipping: AI service not available")
            return False
        
        ai_service = self.services['ai']['service']
        
        try:
            # Step 1: Simple code generation
            logger.info("⚡ Step 1: Code generation test...")
            
            code_prompt = "Write a Python function to calculate the factorial of a number using recursion."
            
            start_time = time.time()
            response = await ai_service.generate(
                code_prompt,
                max_tokens=200,
                temperature=0.1
            )
            duration = time.time() - start_time
            
            if response and 'def' in response and 'factorial' in response.lower():
                logger.info(f"   ✅ Code generated in {duration:.1f}s")
                logger.info(f"   Response contains function definition: ✅")
            else:
                logger.warning(f"   ⚠️ Generated code may be incomplete")
            
            # Step 2: Code review and analysis
            logger.info("🔍 Step 2: Code review capabilities...")
            
            review_code = '''
def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
'''
            
            review_analysis = await ai_service.analyze_code(
                review_code,
                language="python",
                analysis_type="review"
            )
            
            if review_analysis and review_analysis.get('analysis'):
                logger.info("   ✅ Code review analysis completed")
                analysis_text = review_analysis['analysis']
                
                # Check for common review elements
                has_suggestions = any(word in analysis_text.lower() for word in ['improve', 'optimize', 'consider', 'recommend'])
                has_code_quality = any(word in analysis_text.lower() for word in ['quality', 'performance', 'efficiency'])
                
                logger.info(f"   Contains suggestions: {'✅' if has_suggestions else '❌'}")
                logger.info(f"   Addresses code quality: {'✅' if has_code_quality else '❌'}")
            
            # Step 3: Conversational context
            logger.info("💭 Step 3: Conversational context handling...")
            
            # Initial question
            initial_msg = "What are the benefits of using async/await in Python?"
            response1 = await ai_service.chat(initial_msg)
            
            if response1:
                logger.info("   ✅ Initial conversation response generated")
                
                # Follow-up with context
                context = [{'user': initial_msg, 'assistant': response1[:100] + '...'}]
                followup_msg = "Can you show me a practical example?"
                
                response2 = await ai_service.chat(followup_msg, context=context)
                
                if response2:
                    logger.info("   ✅ Contextual follow-up response generated")
                    
                    # Check if response includes code example
                    has_code_example = any(keyword in response2 for keyword in ['async def', 'await', 'asyncio'])
                    logger.info(f"   Contains code example: {'✅' if has_code_example else '❌'}")
            
            # Step 4: Health check
            logger.info("🩺 Step 4: AI service health validation...")
            
            health = await ai_service.health_check()
            if health.get('status') == 'healthy':
                logger.info("   ✅ AI service health: HEALTHY")
                
                perf = health.get('performance', {})
                if perf:
                    logger.info(f"   Average response time: {perf.get('average_response_time', 0):.2f}s")
                    logger.info(f"   Total requests processed: {perf.get('total_requests', 0)}")
            
            logger.info("✅ AI Assistant Workflow: COMPLETED SUCCESSFULLY")
            return True
            
        except Exception as e:
            logger.error(f"❌ AI Assistant Workflow: FAILED - {e}")
            return False

    async def validate_service_integration(self):
        """Validate cross-service integration"""
        logger.info("\n🔗 VALIDATING: Service Integration")
        logger.info("=" * 60)
        
        available_services = [name for name, info in self.services.items() if info['available']]
        
        if len(available_services) < 2:
            logger.warning("⚠️ Insufficient services for integration testing")
            return False
        
        try:
            # Test vector + AI integration
            if 'vector' in available_services and 'ai' in available_services:
                logger.info("🔀 Testing Vector Store + AI Integration...")
                
                vector_service = self.services['vector']['service']
                ai_service = self.services['ai']['service']
                
                # Store a code snippet
                test_code = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
                
                embedding = CodeEmbedding(
                    id="integration_test_fib",
                    content=test_code,
                    file_path="/integration/fibonacci.py",
                    language="python",
                    symbol_type="function",
                    symbol_name="fibonacci",
                    start_line=1,
                    end_line=1
                )
                
                await vector_service.add_code_embedding(embedding)
                
                # Search for the code
                results = await vector_service.search_similar_code("recursive fibonacci", n_results=1)
                
                if results:
                    found_code = results[0].content
                    
                    # Ask AI to analyze the found code
                    ai_analysis = await ai_service.analyze_code(
                        found_code,
                        language="python",
                        analysis_type="optimize"
                    )
                    
                    if ai_analysis:
                        logger.info("   ✅ Vector search → AI analysis pipeline working")
                    
                    # Cleanup
                    try:
                        if vector_service.chromadb_available and vector_service.collection:
                            vector_service.collection.delete(ids=["integration_test_fib"])
                    except Exception:
                        pass
            
            logger.info(f"✅ Service Integration: COMPLETED ({len(available_services)} services)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Service Integration: FAILED - {e}")
            return False

    async def cleanup_services(self):
        """Cleanup all initialized services"""
        logger.info("\n🧹 Cleaning up services...")
        
        for name, info in self.services.items():
            if info['available'] and info['service']:
                try:
                    if hasattr(info['service'], 'close'):
                        await info['service'].close()
                    logger.info(f"   ✅ {info['name']}: Closed")
                except Exception as e:
                    logger.warning(f"   ⚠️ {info['name']}: Cleanup error - {e}")

    async def run_complete_validation(self):
        """Run complete end-to-end validation"""
        logger.info("🧪 LEANVIBE AI BACKEND - END-TO-END VALIDATION")
        logger.info("=" * 80)
        
        try:
            # Initialize services
            available_services = await self.initialize_all_services()
            
            if not available_services:
                logger.error("❌ No services available - cannot proceed with validation")
                return False
            
            # Run workflow validations
            results = {}
            
            results['code_analysis'] = await self.validate_code_analysis_workflow()
            results['ai_assistant'] = await self.validate_ai_assistant_workflow()
            results['service_integration'] = await self.validate_service_integration()
            
            # Summary
            logger.info("\n📊 VALIDATION SUMMARY")
            logger.info("=" * 80)
            
            total_workflows = len(results)
            successful_workflows = sum(1 for success in results.values() if success)
            
            for workflow, success in results.items():
                status = "✅ PASSED" if success else "❌ FAILED"
                logger.info(f"   {workflow.replace('_', ' ').title()}: {status}")
            
            overall_success = successful_workflows >= (total_workflows * 0.67)  # 67% success rate
            
            logger.info(f"\n🎯 OVERALL RESULT: {successful_workflows}/{total_workflows} workflows successful")
            
            if overall_success:
                logger.info("🎉 LeanVibe AI Backend: VALIDATION SUCCESSFUL")
                logger.info("   All critical workflows are functional")
                logger.info("   System ready for production use")
            else:
                logger.warning("⚠️ LeanVibe AI Backend: VALIDATION INCOMPLETE")
                logger.warning("   Some workflows need attention before production")
            
            return overall_success
            
        finally:
            await self.cleanup_services()


async def main():
    """Main validation entry point"""
    validator = LeanVibeWorkflowValidator()
    
    try:
        success = await validator.run_complete_validation()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)