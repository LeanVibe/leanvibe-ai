"""
Comprehensive test suite for Project Service Layer

Tests the business logic and core functionality of the ProjectService
that powers the agent-developed project management APIs.
"""

import pytest
import uuid
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock, mock_open

from app.services.project_service import ProjectService
from app.models.project_models import (
    Project,
    ProjectMetrics,
    ProjectTask,
    ProjectLanguage,
    ProjectStatus,
)


class TestProjectService:
    """Test suite for ProjectService business logic"""

    @pytest.fixture
    def project_service(self):
        """Create ProjectService instance for testing"""
        return ProjectService()

    @pytest.fixture
    def sample_project_id(self):
        """Sample project UUID for testing"""
        return uuid.uuid4()

    @pytest.fixture
    def sample_project_data(self, sample_project_id):
        """Sample project data for testing"""
        return {
            "id": sample_project_id,
            "name": "Test Project",
            "description": "A comprehensive test project",
            "path": "/Users/test/project",
            "language": ProjectLanguage.PYTHON,
            "status": ProjectStatus.ACTIVE,
            "health_score": 0.85,
            "lines_of_code": 2500,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

    @pytest.fixture
    def sample_file_structure(self):
        """Sample file structure for code analysis"""
        return {
            "python_files": [
                "/Users/test/project/main.py",
                "/Users/test/project/models.py",
                "/Users/test/project/services/api.py",
                "/Users/test/project/tests/test_main.py"
            ],
            "total_lines": 2500,
            "test_files": 1,
            "source_files": 3
        }

    # Test Project Initialization and Sample Data
    @pytest.mark.asyncio
    async def test_get_all_projects_initial_state(self, project_service):
        """Test getting all projects returns sample data initially"""
        # Act
        projects = await project_service.get_all_projects()

        # Assert
        assert len(projects) >= 2  # Should have sample projects
        assert all(isinstance(p, Project) for p in projects)
        assert any(p.name == "LeanVibe Backend" for p in projects)
        assert any(p.name == "Mobile App Development" for p in projects)

    @pytest.mark.asyncio
    async def test_get_project_by_id_existing(self, project_service):
        """Test retrieving existing project by ID"""
        # Arrange - Get a project from the sample data
        all_projects = await project_service.get_all_projects()
        existing_project = all_projects[0]

        # Act
        project = await project_service.get_project(existing_project.id)

        # Assert
        assert project is not None
        assert project.id == existing_project.id
        assert project.name == existing_project.name
        assert isinstance(project, Project)

    @pytest.mark.asyncio
    async def test_get_project_by_id_nonexistent(self, project_service):
        """Test retrieving non-existent project returns None"""
        # Arrange
        fake_id = uuid.uuid4()

        # Act
        project = await project_service.get_project(fake_id)

        # Assert
        assert project is None

    # Test Dynamic Metrics Calculation
    @pytest.mark.asyncio
    async def test_calculate_dynamic_metrics_success(self, project_service, sample_project_data):
        """Test successful dynamic metrics calculation"""
        # Arrange
        project = Project(**sample_project_data)
        
        with patch('os.path.exists', return_value=True), \
             patch('os.walk') as mock_walk, \
             patch('builtins.open', mock_open(read_data="def test():\n    pass\n")):
            
            # Mock file system structure
            mock_walk.return_value = [
                ('/Users/test/project', ['services', 'tests'], ['main.py', 'models.py']),
                ('/Users/test/project/services', [], ['api.py']),
                ('/Users/test/project/tests', [], ['test_main.py'])
            ]

            # Act
            metrics = project_service._calculate_dynamic_metrics(project)

            # Assert
            assert isinstance(metrics, ProjectMetrics)
            assert metrics.project_id == project.id
            assert metrics.lines_of_code > 0
            assert 0 <= metrics.test_coverage <= 1
            assert 0 <= metrics.code_quality_score <= 1
            assert 0 <= metrics.technical_debt_ratio <= 1
            assert metrics.complexity_average >= 1.0

    @pytest.mark.asyncio
    async def test_calculate_dynamic_metrics_no_files(self, project_service, sample_project_data):
        """Test metrics calculation when no files are found"""
        # Arrange
        project = Project(**sample_project_data)
        
        with patch('os.path.exists', return_value=True), \
             patch('os.walk', return_value=[]):

            # Act
            metrics = project_service._calculate_dynamic_metrics(project)

            # Assert
            assert isinstance(metrics, ProjectMetrics)
            assert metrics.lines_of_code == 0
            assert metrics.test_coverage == 0.0
            assert metrics.code_quality_score == 0.5  # Default value

    @pytest.mark.asyncio
    async def test_calculate_dynamic_metrics_path_not_exists(self, project_service, sample_project_data):
        """Test metrics calculation when project path doesn't exist"""
        # Arrange
        project = Project(**sample_project_data)
        
        with patch('os.path.exists', return_value=False):

            # Act
            metrics = project_service._calculate_dynamic_metrics(project)

            # Assert
            assert isinstance(metrics, ProjectMetrics)
            assert metrics.lines_of_code == 0
            assert metrics.test_coverage == 0.0
            assert metrics.code_quality_score == 0.5

    def test_calculate_code_quality_score(self, project_service):
        """Test code quality score calculation algorithm"""
        # Test cases with different scenarios
        test_cases = [
            # (test_coverage, tech_debt_ratio, complexity, expected_range)
            (0.8, 0.1, 2.0, (0.7, 0.9)),  # Good quality
            (0.5, 0.3, 4.0, (0.4, 0.6)),  # Medium quality
            (0.2, 0.5, 6.0, (0.1, 0.4)),  # Poor quality
            (1.0, 0.0, 1.0, (0.8, 1.0)),  # Excellent quality
        ]

        for test_coverage, tech_debt, complexity, (min_score, max_score) in test_cases:
            # Act
            score = project_service._calculate_code_quality_score(
                test_coverage, tech_debt, complexity
            )

            # Assert
            assert min_score <= score <= max_score, \
                f"Score {score} not in range [{min_score}, {max_score}] for inputs: " \
                f"coverage={test_coverage}, debt={tech_debt}, complexity={complexity}"
            assert 0 <= score <= 1

    def test_calculate_complexity_score(self, project_service):
        """Test complexity score calculation"""
        test_cases = [
            # (lines_of_code, file_count, expected_range)
            (1000, 10, (1.0, 3.0)),   # Simple project
            (10000, 50, (2.0, 5.0)),  # Medium project
            (50000, 200, (3.0, 8.0)), # Complex project
        ]

        for lines, files, (min_complexity, max_complexity) in test_cases:
            # Act
            complexity = project_service._calculate_complexity_score(lines, files)

            # Assert
            assert min_complexity <= complexity <= max_complexity, \
                f"Complexity {complexity} not in range [{min_complexity}, {max_complexity}]"

    # Test Project Tasks Management
    @pytest.mark.asyncio
    async def test_get_project_tasks_success(self, project_service, sample_project_id):
        """Test retrieving tasks for a project"""
        # Act
        tasks = await project_service.get_project_tasks(sample_project_id)

        # Assert
        assert isinstance(tasks, list)
        assert all(isinstance(task, ProjectTask) for task in tasks)
        # Should have sample tasks for existing projects
        if tasks:
            assert all(task.project_id == sample_project_id for task in tasks)

    @pytest.mark.asyncio
    async def test_get_project_tasks_empty(self, project_service):
        """Test retrieving tasks for project with no tasks"""
        # Arrange - Use a UUID that won't have tasks
        empty_project_id = uuid.uuid4()

        # Act
        tasks = await project_service.get_project_tasks(empty_project_id)

        # Assert
        assert tasks == []

    # Test Project Metrics Retrieval
    @pytest.mark.asyncio
    async def test_get_project_metrics_success(self, project_service, sample_project_id):
        """Test retrieving metrics for a project"""
        # Act
        metrics = await project_service.get_project_metrics(sample_project_id)

        # Assert
        assert isinstance(metrics, ProjectMetrics)
        assert metrics.project_id == sample_project_id
        assert hasattr(metrics, 'lines_of_code')
        assert hasattr(metrics, 'test_coverage')
        assert hasattr(metrics, 'code_quality_score')

    @pytest.mark.asyncio
    async def test_get_project_metrics_nonexistent_project(self, project_service):
        """Test retrieving metrics for non-existent project"""
        # Arrange
        fake_id = uuid.uuid4()

        # Act
        metrics = await project_service.get_project_metrics(fake_id)

        # Assert
        assert isinstance(metrics, ProjectMetrics)
        assert metrics.project_id == fake_id
        # Should return default/empty metrics

    # Test Project Analysis
    @pytest.mark.asyncio
    async def test_analyze_project_success(self, project_service, sample_project_id):
        """Test project analysis workflow"""
        # Act
        analysis_result = await project_service.analyze_project(sample_project_id)

        # Assert
        assert isinstance(analysis_result, dict)
        assert "status" in analysis_result
        assert analysis_result["status"] == "completed"
        assert "metrics" in analysis_result
        assert "recommendations" in analysis_result

    @pytest.mark.asyncio
    async def test_analyze_project_with_file_analysis(self, project_service, sample_project_data):
        """Test project analysis with actual file system analysis"""
        # Arrange
        project = Project(**sample_project_data)
        
        with patch('os.path.exists', return_value=True), \
             patch('os.walk') as mock_walk, \
             patch('builtins.open', mock_open(read_data="def complex_function():\n    # Complex logic\n    pass\n")):
            
            mock_walk.return_value = [
                ('/Users/test/project', [], ['main.py', 'test_main.py'])
            ]

            # Act
            analysis_result = await project_service.analyze_project(project.id)

            # Assert
            assert "file_analysis" in analysis_result
            assert "health_assessment" in analysis_result
            assert analysis_result["status"] == "completed"

    # Test Project Deletion
    @pytest.mark.asyncio
    async def test_delete_project_success(self, project_service):
        """Test successful project deletion"""
        # Arrange - Get existing project
        projects = await project_service.get_all_projects()
        initial_count = len(projects)
        project_to_delete = projects[0]

        # Act
        result = await project_service.delete_project(project_to_delete.id)

        # Assert
        assert result is True
        remaining_projects = await project_service.get_all_projects()
        assert len(remaining_projects) == initial_count - 1
        assert not any(p.id == project_to_delete.id for p in remaining_projects)

    @pytest.mark.asyncio
    async def test_delete_project_nonexistent(self, project_service):
        """Test deleting non-existent project"""
        # Arrange
        fake_id = uuid.uuid4()

        # Act
        result = await project_service.delete_project(fake_id)

        # Assert
        assert result is False

    # Test Error Handling and Edge Cases
    @pytest.mark.asyncio
    async def test_service_handles_file_system_errors(self, project_service, sample_project_data):
        """Test service handles file system errors gracefully"""
        # Arrange
        project = Project(**sample_project_data)
        
        with patch('os.path.exists', side_effect=OSError("Permission denied")):

            # Act & Assert - Should not raise exception
            metrics = project_service._calculate_dynamic_metrics(project)
            assert isinstance(metrics, ProjectMetrics)
            assert metrics.lines_of_code == 0

    @pytest.mark.asyncio
    async def test_concurrent_access_safety(self, project_service):
        """Test service handles concurrent access safely"""
        # Arrange - Simulate concurrent operations
        import asyncio
        
        async def get_projects():
            return await project_service.get_all_projects()
        
        async def get_metrics():
            projects = await project_service.get_all_projects()
            if projects:
                return await project_service.get_project_metrics(projects[0].id)
            return None

        # Act - Run concurrent operations
        results = await asyncio.gather(
            get_projects(),
            get_metrics(),
            get_projects(),
            return_exceptions=True
        )

        # Assert - All operations should complete successfully
        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)

    def test_sample_data_consistency(self, project_service):
        """Test that sample data is consistent and valid"""
        # Act
        sample_projects = project_service._initialize_sample_projects()

        # Assert
        assert len(sample_projects) > 0
        for project in sample_projects:
            assert isinstance(project, Project)
            assert project.id is not None
            assert project.name is not None
            assert project.description is not None
            assert project.status in [ProjectStatus.ACTIVE, ProjectStatus.COMPLETED, ProjectStatus.ON_HOLD]
            assert project.language in list(ProjectLanguage)
            assert 0 <= project.health_score <= 1
            assert project.lines_of_code >= 0

    # Test Performance and Resource Management
    @pytest.mark.asyncio
    async def test_large_file_analysis_performance(self, project_service, sample_project_data):
        """Test performance with large file analysis"""
        # Arrange
        project = Project(**sample_project_data)
        
        # Simulate large project structure
        large_file_structure = []
        for i in range(100):  # 100 directories
            large_file_structure.append((f'/project/dir{i}', [], [f'file{j}.py' for j in range(10)]))
        
        with patch('os.path.exists', return_value=True), \
             patch('os.walk', return_value=large_file_structure), \
             patch('builtins.open', mock_open(read_data="def function():\n    pass\n" * 100)):

            # Act
            import time
            start_time = time.time()
            metrics = project_service._calculate_dynamic_metrics(project)
            end_time = time.time()

            # Assert
            assert isinstance(metrics, ProjectMetrics)
            assert metrics.lines_of_code > 0
            # Performance assertion - should complete within reasonable time
            assert (end_time - start_time) < 5.0  # 5 seconds max for large project

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, project_service):
        """Test that service doesn't accumulate excessive memory"""
        # Arrange
        initial_projects_count = len(await project_service.get_all_projects())

        # Act - Perform many operations
        for _ in range(50):
            projects = await project_service.get_all_projects()
            if projects:
                await project_service.get_project_metrics(projects[0].id)
                await project_service.get_project_tasks(projects[0].id)

        # Assert - Should not accumulate projects in memory
        final_projects_count = len(await project_service.get_all_projects())
        assert final_projects_count == initial_projects_count

    # Test Data Validation
    def test_validate_project_data_integrity(self, project_service):
        """Test that all project data maintains integrity"""
        # Arrange
        sample_projects = project_service._initialize_sample_projects()

        # Assert data integrity
        project_ids = [p.id for p in sample_projects]
        assert len(set(project_ids)) == len(project_ids)  # All IDs unique

        for project in sample_projects:
            # Validate date consistency
            assert project.created_at <= project.updated_at
            
            # Validate health score range
            assert 0 <= project.health_score <= 1
            
            # Validate lines of code
            assert project.lines_of_code >= 0


# Integration Tests
class TestProjectServiceIntegration:
    """Integration tests for ProjectService with external dependencies"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary directory for testing file operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample file structure
            os.makedirs(os.path.join(tmpdir, "src"))
            os.makedirs(os.path.join(tmpdir, "tests"))
            
            # Create sample files
            with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
                f.write("def main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()\n")
            
            with open(os.path.join(tmpdir, "tests", "test_main.py"), "w") as f:
                f.write("def test_main():\n    assert True\n")
            
            with open(os.path.join(tmpdir, "README.md"), "w") as f:
                f.write("# Test Project\n\nThis is a test project.\n")
            
            yield tmpdir

    @pytest.mark.asyncio
    async def test_real_file_system_analysis(self, temp_project_dir):
        """Test file system analysis with real files"""
        # Arrange
        project_service = ProjectService()
        project_data = {
            "id": uuid.uuid4(),
            "name": "Real File Test",
            "description": "Testing with real files",
            "path": temp_project_dir,
            "language": ProjectLanguage.PYTHON,
            "status": ProjectStatus.ACTIVE,
            "health_score": 0.85,
            "lines_of_code": 0,  # Will be calculated
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        project = Project(**project_data)

        # Act
        metrics = project_service._calculate_dynamic_metrics(project)

        # Assert
        assert metrics.lines_of_code > 0  # Should find actual lines
        assert metrics.test_coverage > 0  # Should find test files
        assert 0 < metrics.code_quality_score <= 1

    @pytest.mark.asyncio
    async def test_file_analysis_with_different_languages(self, temp_project_dir):
        """Test file analysis works with different programming languages"""
        # Arrange
        project_service = ProjectService()
        
        # Create JavaScript files
        js_dir = os.path.join(temp_project_dir, "js")
        os.makedirs(js_dir)
        with open(os.path.join(js_dir, "app.js"), "w") as f:
            f.write("function hello() {\n  console.log('Hello');\n}\n")

        project_data = {
            "id": uuid.uuid4(),
            "name": "Multi-language Test",
            "description": "Testing with multiple languages",
            "path": temp_project_dir,
            "language": ProjectLanguage.JAVASCRIPT,
            "status": ProjectStatus.ACTIVE,
            "health_score": 0.85,
            "lines_of_code": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        project = Project(**project_data)

        # Act
        metrics = project_service._calculate_dynamic_metrics(project)

        # Assert
        assert metrics.lines_of_code > 0  # Should count both Python and JS files
        assert isinstance(metrics, ProjectMetrics)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])