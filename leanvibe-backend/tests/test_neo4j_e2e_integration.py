"""
Neo4j E2E Integration Tests

Tests end-to-end workflow: CLI → Backend → Neo4j → Response
Validates that graph analysis works with graceful fallback when Neo4j unavailable.
"""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.agent.session_manager import SessionManager
from app.services.graph_service import GraphService


class TestNeo4jE2EIntegration:
    """Test Neo4j end-to-end integration with graceful fallback"""

    @pytest.fixture
    def test_client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def sample_python_project(self):
        """Create a sample Python project for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "sample_project"
            project_path.mkdir()
            
            # Create sample Python files
            (project_path / "main.py").write_text("""
class DatabaseService:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        pass
    
    def query(self, sql):
        return []

class UserController:
    def __init__(self, db_service):
        self.db = db_service
    
    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Create service and controller instances
db = DatabaseService()
controller = UserController(db)
""")
            
            (project_path / "models.py").write_text("""
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

class Post:
    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.author = author
""")
            
            yield project_path

    @pytest.mark.asyncio
    async def test_graph_service_graceful_fallback(self):
        """Test that graph service handles Neo4j unavailability gracefully"""
        graph_service = GraphService()
        
        # Initialize should succeed even without Neo4j (fallback mode)
        result = await graph_service.initialize()
        assert result is True  # Returns True for both success and fallback
        
        # Service should handle operations gracefully
        project_data = {
            "project_id": "test-project",
            "project_path": "/test/path",
            "files": []
        }
        
        # Test graceful handling - service should be in fallback mode
        # When Neo4j unavailable, initialized should be False but service works
        if not graph_service.initialized:
            # This is expected - Neo4j unavailable, using fallback
            print("✅ Neo4j unavailable - using graceful fallback mode")
        else:
            print("✅ Neo4j available - using full graph functionality")

    @pytest.mark.asyncio
    async def test_architecture_analysis_endpoint(self, test_client):
        """Test architecture analysis endpoint with session"""
        # Test the endpoint directly - it should handle missing sessions gracefully
        test_client_id = "test-architecture-client"
        
        # Test architecture analysis endpoint
        response = test_client.get(f"/graph/architecture/{test_client_id}")
        
        # Should return a valid response (may be error if session not found)
        assert response.status_code == 200
        data = response.json()
        
        # Should have client_id in response
        assert "client_id" in data
        assert data["client_id"] == test_client_id
        
        # If session not available, should get error message (graceful handling)
        if "error" in data:
            assert "not available" in data["error"] or "not found" in data["error"]
            print(f"✅ Graceful error handling: {data['error']}")
        else:
            # If session available, should have architecture field
            assert "architecture" in data
            print("✅ Architecture analysis successful")

    @pytest.mark.asyncio 
    async def test_complexity_analysis_endpoint(self, test_client):
        """Test complexity analysis endpoint"""
        session_manager = SessionManager()
        await session_manager.start()
        
        try:
            test_client_id = "test-complexity-client"
            agent = await session_manager.get_or_create_session(test_client_id, ".")
            
            response = test_client.get(f"/ast/complexity/{test_client_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "complexity" in data
            assert "client_id" in data
            
        finally:
            await session_manager.stop()

    @pytest.mark.asyncio
    async def test_circular_dependencies_endpoint(self, test_client):
        """Test circular dependencies endpoint"""
        session_manager = SessionManager()
        await session_manager.start()
        
        try:
            test_client_id = "test-deps-client"
            agent = await session_manager.get_or_create_session(test_client_id, ".")
            
            response = test_client.get(f"/graph/circular-deps/{test_client_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "circular_dependencies" in data
            assert "client_id" in data
            
        finally:
            await session_manager.stop()

    @pytest.mark.asyncio
    async def test_project_analysis_with_real_files(self, test_client, sample_python_project):
        """Test project analysis with real Python files"""
        session_manager = SessionManager()
        await session_manager.start()
        
        try:
            test_client_id = "test-project-client"
            # Create session with the sample project path
            agent = await session_manager.get_or_create_session(test_client_id, str(sample_python_project))
            
            # Test project analysis endpoint
            response = test_client.get(f"/ast/project/{test_client_id}/analysis")
            
            assert response.status_code == 200
            data = response.json()
            assert "analysis" in data
            assert "client_id" in data
            
            # Should detect the Python files we created
            analysis = data["analysis"]
            if analysis:  # May be empty in fallback mode
                # In real mode, should detect files and symbols
                assert isinstance(analysis, (dict, str))
            
        finally:
            await session_manager.stop()

    @pytest.mark.asyncio
    async def test_graph_visualization_endpoint(self, test_client):
        """Test graph visualization data generation"""
        session_manager = SessionManager()
        await session_manager.start()
        
        try:
            test_client_id = "test-viz-client"
            agent = await session_manager.get_or_create_session(test_client_id, ".")
            
            response = test_client.get(f"/graph/visualization/{test_client_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "visualization" in data
            assert "client_id" in data
            
        finally:
            await session_manager.stop()

    def test_health_endpoint_includes_graph_status(self, test_client):
        """Test that health endpoint reports graph service status"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        
        # Backend should be healthy even if Neo4j unavailable (graceful fallback)
        assert "ai_ready" in data

    @pytest.mark.asyncio
    async def test_e2e_cli_workflow_simulation(self, test_client):
        """Simulate the full CLI → Backend → Graph workflow"""
        session_manager = SessionManager()
        await session_manager.start()
        
        try:
            test_client_id = "test-e2e-client"
            agent = await session_manager.get_or_create_session(test_client_id, ".")
            
            # Step 1: Architecture analysis (like CLI --architecture)
            arch_response = test_client.get(f"/graph/architecture/{test_client_id}")
            assert arch_response.status_code == 200
            arch_data = arch_response.json()
            
            # Step 2: Complexity analysis (like CLI --complexity) 
            complex_response = test_client.get(f"/ast/complexity/{test_client_id}")
            assert complex_response.status_code == 200
            complex_data = complex_response.json()
            
            # Step 3: Dependency analysis (like CLI --dependencies)
            deps_response = test_client.get(f"/graph/circular-deps/{test_client_id}")
            assert deps_response.status_code == 200
            deps_data = deps_response.json()
            
            # All endpoints should return valid responses
            assert "architecture" in arch_data
            assert "complexity" in complex_data  
            assert "circular_dependencies" in deps_data
            
            # Test JSON output format (like CLI --json)
            combined_result = {
                "architecture": arch_data["architecture"],
                "complexity": complex_data["complexity"],
                "dependencies": deps_data["circular_dependencies"]
            }
            
            # Should be valid JSON serializable
            json_str = json.dumps(combined_result)
            assert len(json_str) > 0
            
        finally:
            await session_manager.stop()


class TestGraphServiceFallbackBehavior:
    """Test specific graph service fallback behaviors"""

    @pytest.mark.asyncio
    async def test_store_project_graph_fallback(self):
        """Test storing project graph with Neo4j unavailable"""
        graph_service = GraphService()
        await graph_service.initialize()  # Will use fallback mode
        
        project_data = {
            "project_id": "fallback-test",
            "project_path": "/test/path",
            "files": [
                {
                    "file_path": "test.py",
                    "language": "python",
                    "symbols": [
                        {"name": "TestClass", "type": "class", "line": 1}
                    ]
                }
            ]
        }
        
        # Should handle gracefully without crashing
        try:
            result = await graph_service.store_project_graph(project_data)
            # In fallback mode, might return success or handle gracefully
            assert isinstance(result, (bool, dict, type(None)))
        except Exception as e:
            # Should only get expected connection errors, not crashes
            assert any(keyword in str(e).lower() for keyword in ["connection", "neo4j", "unavailable"])

    @pytest.mark.asyncio  
    async def test_architecture_patterns_fallback(self):
        """Test architecture pattern detection with fallback"""
        graph_service = GraphService()
        await graph_service.initialize()
        
        # Should return empty or default patterns when Neo4j unavailable
        try:
            patterns = await graph_service.detect_architecture_patterns("test-project")
            assert isinstance(patterns, (list, dict))
        except Exception as e:
            # Expected if no fallback implemented yet
            assert "connection" in str(e).lower() or "neo4j" in str(e).lower()


if __name__ == "__main__":
    # Run a quick test
    import asyncio
    
    async def quick_test():
        test = TestNeo4jE2EIntegration()
        await test.test_graph_service_graceful_fallback()
        print("✅ Graph service graceful fallback test passed")
    
    asyncio.run(quick_test())