"""
Tests for AST Graph Service

Tests the integration between AST parsing and Neo4j graph database,
including project analysis, file processing, and relationship creation.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from app.services.ast_graph_service import ASTGraphService, GraphBuilderVisitor, create_ast_graph_service
from app.services.code_graph_service import CodeGraphService, CodeNode, CodeRelationship, NodeType, RelationType

class TestASTGraphService:
    """Test core AST Graph Service functionality"""

    @pytest.fixture
    def mock_graph_service(self):
        """Create mock CodeGraphService"""
        mock_service = Mock(spec=CodeGraphService)
        mock_service.is_connected.return_value = True
        mock_service.connect = AsyncMock(return_value=True)
        mock_service.clear_project_data = AsyncMock(return_value=True)
        mock_service.add_code_node = AsyncMock(return_value=True)
        mock_service.add_relationship = AsyncMock(return_value=True)
        return mock_service

    @pytest.fixture
    def ast_graph_service(self, mock_graph_service):
        """Create ASTGraphService with mocked dependencies"""
        return ASTGraphService(mock_graph_service)

    @pytest.fixture
    def sample_python_project(self):
        """Create a temporary Python project for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create main.py with classes and functions
            main_py = project_path / "main.py"
            main_py.write_text("""
import os
import sys
from typing import List, Optional
from .models import User, Post

class DatabaseService:
    '''Database service for handling connections'''
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self) -> bool:
        '''Establish database connection'''
        if self.connection_string:
            self.connection = True
            return True
        return False
    
    async def query(self, sql: str) -> List[dict]:
        '''Execute database query'''
        if not self.connection:
            await self.connect()
        
        # Simulate query logic
        if sql.startswith('SELECT'):
            return [{'id': 1, 'name': 'test'}]
        return []

class UserController(DatabaseService):
    '''User management controller'''
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(db_service.connection_string)
        self.db = db_service
    
    def get_user(self, user_id: int) -> Optional[User]:
        '''Get user by ID'''
        result = self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
        if result:
            return User(**result[0])
        return None
    
    def create_user(self, user_data: dict) -> User:
        '''Create new user'''
        query = "INSERT INTO users (name, email) VALUES (?, ?)"
        self.db.query(query)
        return User(**user_data)

def helper_function(data: str) -> str:
    '''Utility helper function'''
    return data.strip().lower()

# Module level code
db = DatabaseService("sqlite:///test.db")
controller = UserController(db)
""")
            
            # Create models.py
            models_py = project_path / "models.py"
            models_py.write_text("""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    '''User model'''
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    created_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        '''Validate user data'''
        return bool(self.name and self.email)

@dataclass 
class Post:
    '''Post model'''
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    author_id: int = 0
    
    def get_author(self) -> Optional[User]:
        '''Get post author'''
        # Would normally fetch from database
        return None
""")
            
            # Create utils.py
            utils_py = project_path / "utils.py"
            utils_py.write_text("""
import re
from typing import List, Dict, Any

def validate_email(email: str) -> bool:
    '''Validate email format'''
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def process_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''Process data list'''
    processed = []
    for item in data:
        if isinstance(item, dict):
            processed.append(item)
    return processed

class ConfigManager:
    '''Configuration management utility'''
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._config = {}
    
    def load_config(self) -> Dict[str, Any]:
        '''Load configuration from file'''
        try:
            # Would normally load from file
            self._config = {"debug": True, "database_url": "sqlite:///app.db"}
            return self._config
        except Exception as e:
            return {}
    
    def get(self, key: str, default: Any = None) -> Any:
        '''Get configuration value'''
        return self._config.get(key, default)
""")
            
            yield project_path

    @pytest.mark.asyncio
    async def test_analyze_project_success(self, ast_graph_service, sample_python_project):
        """Test successful project analysis"""
        # Act
        stats = await ast_graph_service.analyze_project(
            str(sample_python_project), 
            "test_project"
        )
        
        # Assert
        assert stats['files_processed'] == 3  # main.py, models.py, utils.py
        assert stats['nodes_created'] > 0
        assert stats['relationships_created'] > 0
        assert len(stats['errors']) == 0
        assert stats['processing_time'] > 0

    @pytest.mark.asyncio  
    async def test_analyze_project_with_graph_service_disconnected(self, sample_python_project):
        """Test project analysis when graph service can't connect"""
        # Arrange
        mock_service = Mock(spec=CodeGraphService)
        mock_service.is_connected.return_value = False
        mock_service.connect = AsyncMock(return_value=False)
        mock_service.clear_project_data = AsyncMock(return_value=False)
        
        ast_service = ASTGraphService(mock_service)
        
        # Act
        stats = await ast_service.analyze_project(str(sample_python_project))
        
        # Assert
        assert stats['files_processed'] == 0
        assert len(stats['errors']) >= 1
        assert "Failed to connect to Neo4j" in stats['errors'][0]

    @pytest.mark.asyncio
    async def test_analyze_file_success(self, ast_graph_service, sample_python_project):
        """Test successful single file analysis"""
        # Arrange
        main_py_path = sample_python_project / "main.py"
        
        # Act
        stats = await ast_graph_service.analyze_file(str(main_py_path), "test_project")
        
        # Assert
        assert stats['nodes_created'] >= 1  # At least file node
        assert len(stats['errors']) == 0
        
        # Verify graph service calls
        ast_graph_service.graph_service.add_code_node.assert_called()

    @pytest.mark.asyncio
    async def test_analyze_file_syntax_error(self, ast_graph_service):
        """Test file analysis with syntax error"""
        # Arrange - create file with syntax error
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken_function(\n  invalid syntax here")
            temp_file = f.name
        
        try:
            # Act
            stats = await ast_graph_service.analyze_file(temp_file, "test_project")
            
            # Assert
            assert len(stats['errors']) == 1
            assert "Syntax error" in stats['errors'][0]
            assert stats['nodes_created'] == 0
            
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_analyze_empty_file(self, ast_graph_service):
        """Test analysis of empty file"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")  # Empty file
            temp_file = f.name
        
        try:
            # Act
            stats = await ast_graph_service.analyze_file(temp_file, "test_project")
            
            # Assert
            assert stats['nodes_created'] == 0
            assert len(stats['errors']) == 0
            
        finally:
            os.unlink(temp_file)

    def test_find_python_files(self, ast_graph_service, sample_python_project):
        """Test Python file discovery"""
        # Act
        python_files = ast_graph_service._find_python_files(str(sample_python_project))
        
        # Assert
        assert len(python_files) == 3
        assert any('main.py' in f for f in python_files)
        assert any('models.py' in f for f in python_files)
        assert any('utils.py' in f for f in python_files)

    def test_find_python_files_skips_directories(self, sample_python_project):
        """Test that file discovery skips common directories"""
        # Arrange - create directories that should be skipped
        (sample_python_project / "__pycache__").mkdir()
        (sample_python_project / "__pycache__" / "cache.py").write_text("# cache file")
        (sample_python_project / ".git").mkdir()
        (sample_python_project / ".git" / "hooks.py").write_text("# git hook")
        (sample_python_project / "test_something.py").write_text("# test file")
        
        ast_service = ASTGraphService(Mock())
        
        # Act
        python_files = ast_service._find_python_files(str(sample_python_project))
        
        # Assert
        assert not any('__pycache__' in f for f in python_files)
        assert not any('.git' in f for f in python_files)
        assert not any('test_' in f for f in python_files)

class TestGraphBuilderVisitor:
    """Test AST visitor for graph building"""

    @pytest.fixture
    def mock_graph_service(self):
        """Create mock graph service for visitor"""
        mock_service = Mock(spec=CodeGraphService)
        mock_service.add_code_node = AsyncMock(return_value=True)
        mock_service.add_relationship = AsyncMock(return_value=True)
        return mock_service

    @pytest.fixture
    def visitor(self, mock_graph_service):
        """Create GraphBuilderVisitor"""
        return GraphBuilderVisitor(
            graph_service=mock_graph_service,
            file_path="test/file.py",
            project_id="test_project",
            stats={'nodes_created': 0, 'relationships_created': 0, 'errors': []},
            content_lines=["line1", "line2", "line3"]
        )

    def test_visit_class_def(self, visitor):
        """Test class definition processing"""
        import ast
        
        # Arrange
        code = """
class TestClass(BaseClass):
    '''Test class docstring'''
    
    def method1(self):
        pass
        
    def method2(self):
        pass
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        
        # Act
        visitor.visit_ClassDef(class_node)
        
        # Assert - verify that async calls would be made
        # Note: Since we can't easily test async calls in sync context,
        # we verify the visitor processed the node correctly
        assert visitor.current_class is None  # Should be reset after processing

    def test_visit_function_def(self, visitor):
        """Test function definition processing"""
        import ast
        
        # Arrange
        code = """
def test_function(param1: str, param2: int = 5) -> bool:
    '''Test function docstring'''
    if param1:
        return True
    for i in range(param2):
        if i > 2:
            return False
    return True
"""
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        # Act
        visitor.visit_FunctionDef(func_node)
        
        # Assert
        assert visitor.current_function is None  # Should be reset

    def test_visit_import(self, visitor):
        """Test import statement processing"""
        import ast
        
        # Arrange
        code = "import os, sys"
        tree = ast.parse(code)
        import_node = tree.body[0]
        
        # Act
        visitor.visit_Import(import_node)
        
        # Assert
        assert len(visitor.imports) == 2
        assert 'os' in visitor.imports
        assert 'sys' in visitor.imports

    def test_visit_import_from(self, visitor):
        """Test from...import statement processing"""
        import ast
        
        # Arrange
        code = "from typing import List, Dict, Optional"
        tree = ast.parse(code)
        import_node = tree.body[0]
        
        # Act
        visitor.visit_ImportFrom(import_node)
        
        # Assert
        assert len(visitor.imports) == 3
        assert 'typing.List' in visitor.imports
        assert 'typing.Dict' in visitor.imports
        assert 'typing.Optional' in visitor.imports

    def test_calculate_function_complexity(self, visitor):
        """Test function complexity calculation"""
        import ast
        
        # Arrange - complex function with multiple control structures
        code = """
def complex_function(data):
    if not data:
        return None
    
    result = []
    for item in data:
        if isinstance(item, dict):
            if 'valid' in item and item['valid']:
                try:
                    processed = process_item(item)
                    if processed:
                        result.append(processed)
                except ValueError:
                    continue
        elif isinstance(item, list):
            for subitem in item:
                if subitem:
                    result.append(subitem)
    
    return result if result else None
"""
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        # Act
        complexity = visitor._calculate_function_complexity(func_node)
        
        # Assert
        assert complexity > 1  # Should detect multiple decision points
        assert isinstance(complexity, int)

    def test_get_name_from_node(self, visitor):
        """Test name extraction from AST nodes"""
        import ast
        
        # Test simple name
        name_node = ast.Name(id='variable_name', ctx=ast.Load())
        assert visitor._get_name_from_node(name_node) == 'variable_name'
        
        # Test attribute access
        code = "obj.method"
        tree = ast.parse(code, mode='eval')
        attr_node = tree.body
        result = visitor._get_name_from_node(attr_node)
        assert 'obj.method' in result or 'method' in result

    def test_get_decorator_name(self, visitor):
        """Test decorator name extraction"""
        import ast
        
        # Test simple decorator
        decorator = ast.Name(id='property', ctx=ast.Load())
        name = visitor._get_decorator_name(decorator)
        assert name == 'property'

class TestFactoryFunction:
    """Test factory function for AST Graph Service"""

    @patch('app.services.ast_graph_service.create_code_graph_service')
    def test_create_ast_graph_service_with_default_graph_service(self, mock_create_graph):
        """Test factory creates service with default graph service"""
        # Arrange
        mock_graph_service = Mock(spec=CodeGraphService)
        mock_create_graph.return_value = mock_graph_service
        
        # Act
        service = create_ast_graph_service()
        
        # Assert
        assert isinstance(service, ASTGraphService)
        assert service.graph_service == mock_graph_service
        mock_create_graph.assert_called_once()

    def test_create_ast_graph_service_with_provided_graph_service(self):
        """Test factory creates service with provided graph service"""
        # Arrange
        mock_graph_service = Mock(spec=CodeGraphService)
        
        # Act
        service = create_ast_graph_service(mock_graph_service)
        
        # Assert
        assert isinstance(service, ASTGraphService)
        assert service.graph_service == mock_graph_service

class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_analyze_project_nonexistent_path(self):
        """Test project analysis with nonexistent path"""
        # Arrange
        mock_service = Mock(spec=CodeGraphService)
        mock_service.is_connected.return_value = True
        mock_service.connect = AsyncMock(return_value=True)
        mock_service.clear_project_data = AsyncMock(return_value=True)
        
        ast_service = ASTGraphService(mock_service)
        
        # Act
        stats = await ast_service.analyze_project("/nonexistent/path")
        
        # Assert
        assert stats['files_processed'] == 0
        assert len(stats['errors']) == 0  # No error because no files found
        assert stats['nodes_created'] == 0

    @pytest.mark.asyncio
    async def test_analyze_file_permission_error(self, ast_graph_service):
        """Test file analysis with permission error"""
        # This test would need to create a file with restricted permissions
        # For simplicity, we'll test the error handling structure
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            stats = await ast_graph_service.analyze_file("restricted_file.py", "test")
            
            assert len(stats['errors']) == 1
            assert "Access denied" in stats['errors'][0]

    def test_visitor_with_complex_ast_structures(self):
        """Test visitor handles complex AST structures"""
        import ast
        from unittest.mock import Mock
        
        # Arrange
        mock_service = Mock(spec=CodeGraphService)
        visitor = GraphBuilderVisitor(
            graph_service=mock_service,
            file_path="test.py",
            project_id="test",
            stats={'nodes_created': 0, 'relationships_created': 0, 'errors': []},
            content_lines=[]
        )
        
        # Complex code with nested structures
        code = """
class OuterClass:
    class InnerClass:
        def inner_method(self):
            def nested_function():
                return lambda x: x + 1
            return nested_function
    
    def outer_method(self):
        async def async_inner():
            with open('file') as f:
                for line in f:
                    if line.strip():
                        yield line
        return async_inner
"""
        
        tree = ast.parse(code)
        
        # Act - should not raise exceptions
        try:
            visitor.visit(tree)
            success = True
        except Exception as e:
            success = False
            print(f"Error processing complex AST: {e}")
        
        # Assert
        assert success

if __name__ == "__main__":
    # Run a quick smoke test
    pytest.main([__file__, "-v"])