# Complete CLI Testing Execution Prompt for Agentic AI Developer

## Role & Mission Context
You are an elite Python CLI engineer with 20+ years of experience, specializing in Click/Typer frameworks, async client architecture, and comprehensive testing strategies. Following the successful backend testing implementation, you must now create bulletproof testing infrastructure for the LeanVibe CLI that mirrors the same depth and quality.

## Current Situation & Intelligence
- **Backend Status**: ✅ Comprehensive testing complete with 100+ test cases, performance validation, integration testing
- **CLI Status**: ❌ **3 FAILED test imports, missing test infrastructure** (critical stability risk)
- **Quality Gate**: Achieve >80% test coverage on CLI commands and client functionality
- **Architecture**: Click-based CLI with async backend client, rich terminal UI, real-time monitoring

## CLI Analysis Key Findings
### Critical Issues Identified:
1. **Import Naming Inconsistency**: Tests import `leenvibe_cli` but package is `leanvibe_cli` (immediate fix needed)
2. **Missing Test Infrastructure**: No proper test fixtures, mocks, or integration setup
3. **Async Client Testing**: Complex WebSocket client requires sophisticated mocking
4. **Command Testing**: Click commands need proper CLI testing framework
5. **Configuration Testing**: YAML config system lacks validation tests

### High-Impact CLI Testing Priorities:
1. **CLI Commands Testing** - 90% user interaction coverage (8-12 hours effort)
2. **Backend Client Integration** - Real-time communication validation (10-15 hours effort)
3. **Configuration Management** - YAML config and profile testing (6-8 hours effort)
4. **WebSocket Client Testing** - Connection reliability critical (8-10 hours effort)

### CLI Architecture Components:
- **Commands**: `status`, `analyze`, `monitor`, `query`, `info`, `config`, `qr` (7 core commands)
- **Client**: `BackendClient` with WebSocket communication (most critical)
- **Config**: YAML-based configuration with profiles and schemas
- **Services**: Notification service, desktop notifications, live dashboard
- **UI**: Rich-based terminal interface with real-time updates

## Methodology & Principles (Mirroring Backend Success)
- **Fix First**: Address 3 failing test imports and naming issues
- **Pareto Focus**: Implement 20% of tests that prevent 80% of CLI issues
- **Click Testing**: Use Click's testing framework for command validation
- **Async Mocking**: Comprehensive WebSocket and HTTP client mocking
- **Vertical Slices**: Complete test suites for entire command workflows
- **Performance Validation**: CLI response times and resource usage testing

## PHASE 0: CLI Analysis & Current State Assessment

### Step 1: CLI Codebase Analysis (MANDATORY FIRST STEP)
Understand the CLI structure and identify testing requirements:
```bash
# Navigate to CLI directory
cd leanvibe-cli

# Analyze CLI structure
find leanvibe_cli -name "*.py" | head -20
cat leanvibe_cli/__init__.py
cat leanvibe_cli/main.py
cat pyproject.toml

# Check current test failures
uv run pytest tests/ -v --tb=long
```

### Step 2: Fix Import Naming Issues (Immediate Priority)
**Root Cause**: Tests import `leenvibe_cli` but package is `leanvibe_cli`

**Action Protocol**:
```bash
# Fix all import statements in tests
grep -r "leenvibe_cli" tests/
# Replace with leanvibe_cli in all test files

# Verify package installation
uv run python -c "import leanvibe_cli; print('CLI package imports correctly')"
```

### Step 3: Validate CLI Components Exist
Confirm these critical files exist and analyze:
- `leanvibe_cli/main.py` (Main CLI entry point)
- `leanvibe_cli/client.py` (Backend client with WebSocket)
- `leanvibe_cli/commands/` (All 7 command modules)
- `leanvibe_cli/config/` (Configuration management)
- `leanvibe_cli/services/` (Notification services)

## PHASE 1: Fix Critical Test Infrastructure (Immediate Priority)

### 1. Fix Import Naming Consistency (1-2 hours, CRITICAL priority)
**Action Protocol**:
```bash
# Fix test imports
sed -i '' 's/leenvibe_cli/leanvibe_cli/g' tests/*.py
sed -i '' 's/leenvibe_cli/leanvibe_cli/g' test_*.py

# Verify imports work
uv run python -c "
from leanvibe_cli.main import main
from leanvibe_cli.client import BackendClient
from leanvibe_cli.config import CLIConfig
print('✅ All core imports successful')
"
```

### 2. Create Test Infrastructure Foundation (2-3 hours, HIGH priority)
**Create**: `tests/conftest.py`

**Implementation**:
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner
import tempfile
import os

from leanvibe_cli.client import BackendClient
from leanvibe_cli.config import CLIConfig
from leanvibe_cli.main import cli


@pytest.fixture
def cli_runner():
    """Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def mock_backend_client():
    """Mock BackendClient for isolated testing"""
    client = MagicMock(spec=BackendClient)
    
    # Mock async methods
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.get_health = AsyncMock(return_value={
        "status": "healthy",
        "uptime": "1h 23m",
        "version": "0.2.0"
    })
    client.get_analysis = AsyncMock()
    client.monitor_events = AsyncMock()
    client.query_agent = AsyncMock()
    
    return client


@pytest.fixture
def test_config():
    """Test CLI configuration"""
    return CLIConfig(
        backend_url="http://localhost:8000",
        websocket_url="ws://localhost:8000/ws",
        timeout=30,
        verbose=False,
        client_id="test-client"
    )


@pytest.fixture
def temp_config_file():
    """Temporary configuration file for testing"""
    config_content = """
backend:
  url: "http://localhost:8000"
  websocket_url: "ws://localhost:8000/ws"
  timeout: 30

client:
  id: "test-client"
  verbose: false

notifications:
  enabled: true
  desktop: true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture
def isolated_filesystem():
    """Isolated filesystem for CLI tests"""
    with CliRunner().isolated_filesystem():
        yield
```

### 3. Fix Existing Test Files (2-4 hours, HIGH priority)
**Fix all test files to use correct imports and proper structure**

**Implementation Steps**:
1. Update all import statements from `leenvibe_cli` to `leanvibe_cli`
2. Add proper test fixtures and async handling
3. Mock external dependencies (backend client, WebSocket, notifications)
4. Ensure tests can run independently and in parallel

### Validation Protocol for Phase 1:
```bash
# After each fix:
uv run pytest tests/test_[specific_file].py -v  # Verify fix works
uv run pytest tests/ --collect-only          # Check all tests collect
uv run pytest tests/ -x                      # Run tests and stop on first failure
```

## PHASE 2: High-Impact CLI Command Testing

### Priority 1: CLI Commands Test Suite (8-12 hours, 90% user interaction coverage)
**Create**: `tests/test_cli_commands.py`

**Implement comprehensive command testing**:
```python
import pytest
from click.testing import CliRunner
from unittest.mock import AsyncMock, patch, MagicMock

from leanvibe_cli.main import cli


class TestStatusCommand:
    """Test the status command functionality"""
    
    def test_status_command_success(self, cli_runner, mock_backend_client):
        """Test status command with healthy backend"""
        with patch('leanvibe_cli.commands.status.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['status'])
            
            assert result.exit_code == 0
            assert "Backend Status" in result.output
            assert "healthy" in result.output
            mock_backend_client.get_health.assert_called_once()
    
    def test_status_command_backend_unreachable(self, cli_runner):
        """Test status command with unreachable backend"""
        with patch('leanvibe_cli.client.BackendClient.get_health', side_effect=ConnectionError("Connection refused")):
            result = cli_runner.invoke(cli, ['status'])
            
            assert result.exit_code != 0 or "unreachable" in result.output.lower()
    
    def test_status_command_with_verbose(self, cli_runner, mock_backend_client):
        """Test status command with verbose output"""
        mock_backend_client.get_health.return_value = {
            "status": "healthy",
            "uptime": "2h 15m",
            "version": "0.2.0",
            "metrics": {"requests": 150, "errors": 2}
        }
        
        with patch('leanvibe_cli.commands.status.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['status', '--verbose'])
            
            assert result.exit_code == 0
            assert "requests" in result.output
            assert "errors" in result.output


class TestAnalyzeCommand:
    """Test the analyze command functionality"""
    
    def test_analyze_command_success(self, cli_runner, mock_backend_client):
        """Test analyze command with valid input"""
        mock_backend_client.get_analysis.return_value = {
            "file_count": 25,
            "complexity_score": 7.2,
            "issues": ["High cyclomatic complexity in user.py"],
            "suggestions": ["Consider breaking down large functions"]
        }
        
        with patch('leanvibe_cli.commands.analyze.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['analyze', '--path', '/test/project'])
            
            assert result.exit_code == 0
            assert "complexity_score" in result.output or "7.2" in result.output
            mock_backend_client.get_analysis.assert_called_once()
    
    def test_analyze_command_invalid_path(self, cli_runner):
        """Test analyze command with invalid path"""
        result = cli_runner.invoke(cli, ['analyze', '--path', '/nonexistent/path'])
        
        # Should handle gracefully
        assert "error" in result.output.lower() or result.exit_code != 0


class TestMonitorCommand:
    """Test the monitor command functionality"""
    
    @pytest.mark.asyncio
    async def test_monitor_command_connection(self, cli_runner, mock_backend_client, mock_websocket):
        """Test monitor command WebSocket connection"""
        # Mock WebSocket events
        mock_backend_client.monitor_events.return_value = AsyncMock()
        
        with patch('leanvibe_cli.commands.monitor.BackendClient', return_value=mock_backend_client):
            with patch('websockets.connect', return_value=mock_websocket):
                result = cli_runner.invoke(cli, ['monitor', '--timeout', '1'])
                
                # Should attempt connection
                mock_backend_client.monitor_events.assert_called()
    
    def test_monitor_command_help(self, cli_runner):
        """Test monitor command help output"""
        result = cli_runner.invoke(cli, ['monitor', '--help'])
        
        assert result.exit_code == 0
        assert "monitor" in result.output.lower()
        assert "real-time" in result.output.lower()


class TestQueryCommand:
    """Test the query command functionality"""
    
    def test_query_command_success(self, cli_runner, mock_backend_client):
        """Test query command with AI response"""
        mock_backend_client.query_agent.return_value = {
            "response": "Based on the analysis, your codebase has good structure.",
            "confidence": 0.85,
            "sources": ["ast_analysis", "dependency_graph"]
        }
        
        with patch('leanvibe_cli.commands.query.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['query', 'How is my code quality?'])
            
            assert result.exit_code == 0
            assert "good structure" in result.output
            mock_backend_client.query_agent.assert_called_once()
    
    def test_query_command_empty_query(self, cli_runner):
        """Test query command with empty query"""
        result = cli_runner.invoke(cli, ['query', ''])
        
        # Should require non-empty query
        assert result.exit_code != 0 or "empty" in result.output.lower()


class TestInfoCommand:
    """Test the info command functionality"""
    
    def test_info_command_output(self, cli_runner, mock_backend_client):
        """Test info command displays backend information"""
        mock_backend_client.get_info = AsyncMock(return_value={
            "name": "LeanVibe Backend",
            "version": "0.2.0",
            "capabilities": ["ast_analysis", "graph_db", "ai_agent"],
            "endpoints": ["/health", "/analyze", "/query"]
        })
        
        with patch('leanvibe_cli.commands.info.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['info'])
            
            assert result.exit_code == 0
            assert "LeanVibe Backend" in result.output
            assert "capabilities" in result.output.lower()


class TestConfigCommand:
    """Test the config command functionality"""
    
    def test_config_list_command(self, cli_runner, temp_config_file):
        """Test config list displays current configuration"""
        result = cli_runner.invoke(cli, ['config', 'list', '--config', temp_config_file])
        
        assert result.exit_code == 0
        assert "backend" in result.output.lower()
        assert "localhost:8000" in result.output
    
    def test_config_set_command(self, cli_runner, temp_config_file):
        """Test config set updates configuration"""
        result = cli_runner.invoke(cli, [
            'config', 'set', 'backend.url', 'http://newhost:8000',
            '--config', temp_config_file
        ])
        
        # Should update successfully or show appropriate message
        assert result.exit_code == 0 or "updated" in result.output.lower()


class TestQRCommand:
    """Test the QR command functionality"""
    
    def test_qr_command_generation(self, cli_runner):
        """Test QR code generation for backend URL"""
        result = cli_runner.invoke(cli, ['qr', '--url', 'http://localhost:8000'])
        
        assert result.exit_code == 0
        # Should show QR code or save message
        assert "QR" in result.output or "saved" in result.output.lower()
```

### Priority 2: Backend Client Testing (10-15 hours, Real-time communication critical)
**Create**: `tests/test_backend_client.py`

**Implement comprehensive client testing**:
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json

from leanvibe_cli.client import BackendClient
from leanvibe_cli.config import CLIConfig


class TestBackendClientConnection:
    """Test BackendClient connection management"""
    
    @pytest.mark.asyncio
    async def test_client_connect_success(self, test_config, mock_websocket):
        """Test successful client connection"""
        client = BackendClient(test_config)
        
        with patch('websockets.connect', return_value=mock_websocket):
            await client.connect()
            
            assert client.is_connected
            mock_websocket.send.assert_called()
    
    @pytest.mark.asyncio
    async def test_client_connect_failure(self, test_config):
        """Test client connection failure handling"""
        client = BackendClient(test_config)
        
        with patch('websockets.connect', side_effect=ConnectionRefusedError("Connection refused")):
            with pytest.raises(ConnectionError):
                await client.connect()
            
            assert not client.is_connected
    
    @pytest.mark.asyncio
    async def test_client_disconnect(self, test_config, mock_websocket):
        """Test client disconnection"""
        client = BackendClient(test_config)
        client._websocket = mock_websocket
        client._connected = True
        
        await client.disconnect()
        
        mock_websocket.close.assert_called_once()
        assert not client.is_connected


class TestBackendClientAPI:
    """Test BackendClient API interactions"""
    
    @pytest.mark.asyncio
    async def test_get_health_success(self, test_config):
        """Test health check API call"""
        client = BackendClient(test_config)
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "healthy", "uptime": "1h"}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            health = await client.get_health()
            
            assert health["status"] == "healthy"
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_health_api_error(self, test_config):
        """Test health check API error handling"""
        client = BackendClient(test_config)
        
        with patch('httpx.AsyncClient.get', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await client.get_health()
    
    @pytest.mark.asyncio
    async def test_get_analysis_request(self, test_config):
        """Test analysis request to backend"""
        client = BackendClient(test_config)
        
        expected_response = {
            "file_count": 15,
            "complexity_score": 6.5,
            "issues": ["High complexity in module.py"]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            analysis = await client.get_analysis("/test/path")
            
            assert analysis["file_count"] == 15
            assert analysis["complexity_score"] == 6.5
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_agent_request(self, test_config):
        """Test AI agent query request"""
        client = BackendClient(test_config)
        
        expected_response = {
            "response": "Your code quality is good overall.",
            "confidence": 0.85,
            "sources": ["ast_analysis"]
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            response = await client.query_agent("How is my code quality?")
            
            assert response["confidence"] == 0.85
            assert "good overall" in response["response"]
            mock_post.assert_called_once()


class TestBackendClientWebSocket:
    """Test BackendClient WebSocket functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_message_handling(self, test_config, mock_websocket):
        """Test WebSocket message processing"""
        client = BackendClient(test_config)
        client._websocket = mock_websocket
        client._connected = True
        
        # Mock incoming messages
        test_messages = [
            {"type": "file_changed", "path": "/test/file.py"},
            {"type": "analysis_complete", "result": "success"},
            {"type": "error", "message": "Analysis failed"}
        ]
        
        mock_websocket.recv.side_effect = [json.dumps(msg) for msg in test_messages]
        
        messages = []
        async def message_handler(message):
            messages.append(message)
        
        # Simulate message processing
        for _ in test_messages:
            try:
                message = await mock_websocket.recv()
                parsed = json.loads(message)
                await message_handler(parsed)
            except StopAsyncIteration:
                break
        
        assert len(messages) == 3
        assert messages[0]["type"] == "file_changed"
        assert messages[1]["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_websocket_connection_resilience(self, test_config):
        """Test WebSocket reconnection handling"""
        client = BackendClient(test_config)
        
        # Mock connection that fails then succeeds
        connection_attempts = 0
        
        async def mock_connect_side_effect(*args, **kwargs):
            nonlocal connection_attempts
            connection_attempts += 1
            
            if connection_attempts == 1:
                raise ConnectionRefusedError("First attempt fails")
            else:
                return AsyncMock()  # Second attempt succeeds
        
        with patch('websockets.connect', side_effect=mock_connect_side_effect):
            # First attempt should fail
            with pytest.raises(ConnectionError):
                await client.connect()
            
            # Second attempt should succeed
            await client.connect()
            assert client.is_connected


class TestBackendClientConfiguration:
    """Test BackendClient configuration handling"""
    
    def test_client_initialization(self, test_config):
        """Test client initialization with config"""
        client = BackendClient(test_config)
        
        assert client.config == test_config
        assert client.base_url == test_config.backend_url
        assert client.websocket_url == test_config.websocket_url
        assert not client.is_connected
    
    def test_client_timeout_configuration(self):
        """Test client timeout configuration"""
        config = CLIConfig(
            backend_url="http://localhost:8000",
            websocket_url="ws://localhost:8000/ws",
            timeout=60
        )
        
        client = BackendClient(config)
        assert client.timeout == 60
```

### Priority 3: Configuration Testing (6-8 hours, YAML config critical)
**Create**: `tests/test_configuration.py`

**Implement configuration management testing**:
```python
import pytest
import tempfile
import os
import yaml
from pathlib import Path

from leanvibe_cli.config import CLIConfig, load_config
from leanvibe_cli.config.manager import ConfigurationManager
from leanvibe_cli.config.schema import ConfigSchema


class TestCLIConfig:
    """Test CLI configuration model"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = CLIConfig()
        
        assert config.backend_url == "http://localhost:8000"
        assert config.websocket_url == "ws://localhost:8000/ws"
        assert config.timeout == 30
        assert config.verbose is False
        assert config.client_id is not None
    
    def test_config_custom_values(self):
        """Test configuration with custom values"""
        config = CLIConfig(
            backend_url="http://remote:9000",
            timeout=60,
            verbose=True,
            client_id="custom-client"
        )
        
        assert config.backend_url == "http://remote:9000"
        assert config.timeout == 60
        assert config.verbose is True
        assert config.client_id == "custom-client"
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test invalid URL
        with pytest.raises(ValueError):
            CLIConfig(backend_url="invalid-url")
        
        # Test invalid timeout
        with pytest.raises(ValueError):
            CLIConfig(timeout=-1)


class TestConfigurationLoading:
    """Test configuration file loading"""
    
    def test_load_config_from_file(self, temp_config_file):
        """Test loading configuration from YAML file"""
        config = load_config(config_path=temp_config_file)
        
        assert config.backend_url == "http://localhost:8000"
        assert config.websocket_url == "ws://localhost:8000/ws"
        assert config.client_id == "test-client"
    
    def test_load_config_file_not_found(self):
        """Test loading configuration when file doesn't exist"""
        config = load_config(config_path="/nonexistent/config.yml")
        
        # Should use defaults
        assert config.backend_url == "http://localhost:8000"
    
    def test_load_config_invalid_yaml(self):
        """Test loading configuration with invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            config = load_config(config_path=temp_path)
            # Should fallback to defaults
            assert config.backend_url == "http://localhost:8000"
        finally:
            os.unlink(temp_path)


class TestConfigurationManager:
    """Test configuration management operations"""
    
    def test_config_manager_initialization(self):
        """Test configuration manager setup"""
        manager = ConfigurationManager()
        
        assert manager is not None
        assert hasattr(manager, 'load_config')
        assert hasattr(manager, 'save_config')
    
    def test_config_manager_profile_support(self):
        """Test configuration profile management"""
        manager = ConfigurationManager()
        
        # Test profile creation
        profile_config = {
            "backend": {"url": "http://profile:8000"},
            "client": {"id": "profile-client"}
        }
        
        manager.create_profile("test-profile", profile_config)
        
        # Test profile loading
        loaded_profile = manager.load_profile("test-profile")
        assert loaded_profile["backend"]["url"] == "http://profile:8000"
        assert loaded_profile["client"]["id"] == "profile-client"


class TestConfigSchema:
    """Test configuration schema validation"""
    
    def test_schema_validation_success(self):
        """Test valid configuration schema"""
        valid_config = {
            "backend": {
                "url": "http://localhost:8000",
                "websocket_url": "ws://localhost:8000/ws",
                "timeout": 30
            },
            "client": {
                "id": "test-client",
                "verbose": False
            },
            "notifications": {
                "enabled": True,
                "desktop": True
            }
        }
        
        schema = ConfigSchema()
        is_valid = schema.validate(valid_config)
        
        assert is_valid
    
    def test_schema_validation_failure(self):
        """Test invalid configuration schema"""
        invalid_config = {
            "backend": {
                "url": "invalid-url",  # Invalid URL
                "timeout": "invalid"   # Invalid type
            }
        }
        
        schema = ConfigSchema()
        is_valid = schema.validate(invalid_config)
        
        assert not is_valid
```

## PHASE 3: Integration & Performance Testing

### CLI Integration Testing
**Create**: `tests/test_cli_integration.py`

**Test complete CLI workflows**:
```python
import pytest
import asyncio
from click.testing import CliRunner
from unittest.mock import patch, AsyncMock, MagicMock

from leanvibe_cli.main import cli


class TestCLIIntegration:
    """Test complete CLI workflow integration"""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, cli_runner, mock_backend_client):
        """Test complete analysis workflow: status → analyze → query"""
        # Mock backend responses
        mock_backend_client.get_health.return_value = {"status": "healthy"}
        mock_backend_client.get_analysis.return_value = {
            "file_count": 10,
            "complexity_score": 8.2,
            "issues": ["High complexity in auth.py"]
        }
        mock_backend_client.query_agent.return_value = {
            "response": "Consider refactoring the auth module to reduce complexity.",
            "confidence": 0.9
        }
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            # 1. Check status
            status_result = cli_runner.invoke(cli, ['status'])
            assert status_result.exit_code == 0
            assert "healthy" in status_result.output
            
            # 2. Run analysis
            analyze_result = cli_runner.invoke(cli, ['analyze', '--path', '/test'])
            assert analyze_result.exit_code == 0
            assert "complexity_score" in analyze_result.output
            
            # 3. Query for suggestions
            query_result = cli_runner.invoke(cli, ['query', 'How can I improve my code?'])
            assert query_result.exit_code == 0
            assert "refactoring" in query_result.output.lower()
    
    def test_configuration_workflow(self, cli_runner, temp_config_file):
        """Test configuration management workflow"""
        # 1. List current config
        list_result = cli_runner.invoke(cli, ['config', 'list', '--config', temp_config_file])
        assert list_result.exit_code == 0
        
        # 2. Update config
        set_result = cli_runner.invoke(cli, [
            'config', 'set', 'backend.timeout', '60',
            '--config', temp_config_file
        ])
        assert set_result.exit_code == 0
        
        # 3. Verify change
        list_result2 = cli_runner.invoke(cli, ['config', 'list', '--config', temp_config_file])
        assert list_result2.exit_code == 0
    
    def test_error_handling_workflow(self, cli_runner):
        """Test error handling across CLI commands"""
        with patch('leanvibe_cli.client.BackendClient.get_health', side_effect=ConnectionError("Backend unreachable")):
            # Commands should handle backend errors gracefully
            status_result = cli_runner.invoke(cli, ['status'])
            assert "unreachable" in status_result.output.lower() or status_result.exit_code != 0
            
            analyze_result = cli_runner.invoke(cli, ['analyze', '--path', '/test'])
            assert "error" in analyze_result.output.lower() or analyze_result.exit_code != 0


class TestCLIPerformance:
    """Test CLI performance characteristics"""
    
    def test_command_response_times(self, cli_runner, mock_backend_client):
        """Test CLI command response times"""
        import time
        
        mock_backend_client.get_health.return_value = {"status": "healthy"}
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            # Status command should be fast
            start_time = time.time()
            result = cli_runner.invoke(cli, ['status'])
            end_time = time.time()
            
            assert result.exit_code == 0
            assert (end_time - start_time) < 2.0  # Should complete in under 2 seconds
    
    def test_memory_usage(self, cli_runner, mock_backend_client):
        """Test CLI memory usage"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        mock_backend_client.get_health.return_value = {"status": "healthy"}
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            # Run multiple commands
            for _ in range(10):
                result = cli_runner.invoke(cli, ['status'])
                assert result.exit_code == 0
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB)
        assert memory_growth < 50
```

## Quality Gates & Phase Completion Criteria

### After Each Phase:
```bash
# Comprehensive validation
uv run pytest tests/ -v                    # All tests must pass
uv run pytest --cov=leanvibe_cli --cov-report=term  # Coverage check
uv run pytest tests/test_cli_integration.py  # Integration validation
```

### Success Criteria:
- [ ] **0 failing tests** (all import and infrastructure issues resolved)
- [ ] **>80% test coverage** on CLI commands and client functionality  
- [ ] **Performance benchmarks met** (<2s CLI commands, <50MB memory)
- [ ] **No regressions** in existing CLI functionality
- [ ] **WebSocket client integration working** correctly

## Memory Bank Updates

### After PHASE 1 (Infrastructure Fixes):
Update `docs/01_memory_bank/06_progress.md`:
```markdown
## CLI Testing Infrastructure - Phase 1 Complete [DATE]

### Critical Issues Resolved:
- ✅ Import naming consistency fixed (leenvibe_cli → leanvibe_cli) (1 hour)
- ✅ Test infrastructure foundation created with proper fixtures (2 hours)  
- ✅ Click testing framework integration completed (2 hours)

### Test Infrastructure Created:
- Test fixtures for CLI runner, mock backend client, configurations
- Proper async testing support for WebSocket functionality
- Isolated filesystem testing for configuration management

### Next Priority: Phase 2 - CLI Command Testing
```

### After PHASE 2 (Command Testing):
Update `docs/01_memory_bank/05_active_context.md`:
```markdown
## CLI Testing Strategy - Phase 2 Complete

### Recently Completed:
- Comprehensive CLI command test suites implemented
- Backend client integration testing with WebSocket mocking
- Configuration management testing with YAML validation

### Test Coverage Achieved:
- CLI Commands: >90% coverage (status, analyze, monitor, query, info, config, qr)
- Backend Client: >85% coverage (HTTP/WebSocket communication)
- Configuration: >80% coverage (YAML loading, validation, profiles)

### Next Steps: Phase 3 - Integration and Performance Testing
```

## Final Instructions

**Execute with precision following the backend testing success:**

1. **Start with Phase 0** (CLI analysis and fixing imports) immediately
2. **Fix all test infrastructure issues** before adding new tests (Phase 1)
3. **Implement command tests** with comprehensive Click testing (Phase 2)
4. **Add integration tests** for end-to-end CLI validation (Phase 3)
5. **Update memory bank** after each phase completion
6. **Continue autonomously** through all phases
7. **Apply same quality standards** as backend testing
8. **Focus on user interaction coverage** - CLI is the primary user interface

🚀 **Begin execution now. Transform this CLI from broken test imports to bulletproof production-ready interface that matches the backend's testing excellence.**

**The usability and reliability of the entire LeanVibe platform depends on your systematic execution of this CLI testing strategy.**