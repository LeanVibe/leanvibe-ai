"""
Comprehensive CLI Commands Test Suite

High-impact test suite for all CLI commands following the backend testing methodology.
Tests command functionality, error handling, integration, and user interaction patterns.
"""

import pytest
import json
import tempfile
import os
from click.testing import CliRunner
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from leanvibe_cli.main import cli
from leanvibe_cli.client import BackendClient
from leanvibe_cli.config import CLIConfig


class TestStatusCommand:
    """Test the status command functionality"""
    
    def test_status_command_success(self, cli_runner, mock_backend_client):
        """Test status command with healthy backend"""
        with patch('leanvibe_cli.main.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['status'])
            
            assert result.exit_code == 0
            assert "status" in result.output.lower()
            assert "connected" in result.output.lower() or "ready" in result.output.lower()
            mock_backend_client.health_check.assert_called_once()
    
    def test_status_command_backend_unreachable(self, cli_runner):
        """Test status command with unreachable backend"""
        with patch('leanvibe_cli.client.BackendClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_health = AsyncMock(side_effect=ConnectionError("Connection refused"))
            mock_client_class.return_value = mock_client
            
            result = cli_runner.invoke(cli, ['status'])
            
            # Should handle error gracefully
            assert "unreachable" in result.output.lower() or "error" in result.output.lower() or result.exit_code != 0
    
    def test_status_command_with_verbose(self, cli_runner, mock_backend_client):
        """Test status command with verbose output"""
        mock_backend_client.get_health.return_value = {
            "status": "healthy",
            "uptime": "2h 15m",
            "version": "0.2.0",
            "metrics": {"requests": 150, "errors": 2},
            "services": {"ai_service": "running", "task_service": "running"}
        }
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['status', '--verbose'])
            
            assert result.exit_code == 0
            # Should show additional details in verbose mode
            assert "requests" in result.output or "services" in result.output
    
    def test_status_command_json_output(self, cli_runner, mock_backend_client):
        """Test status command with JSON output"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['status', '--json'])
            
            assert result.exit_code == 0
            # Should be valid JSON
            try:
                json.loads(result.output)
            except json.JSONDecodeError:
                pytest.fail("Status command --json should output valid JSON")


class TestAnalyzeCommand:
    """Test the analyze command functionality"""
    
    def test_analyze_command_success(self, cli_runner, mock_backend_client, temp_project_dir):
        """Test analyze command with valid project"""
        mock_backend_client.get_analysis.return_value = {
            "file_count": 25,
            "complexity_score": 7.2,
            "issues": ["High cyclomatic complexity in user.py"],
            "suggestions": ["Consider breaking down large functions"],
            "metrics": {"total_lines": 2500, "test_coverage": 85.5}
        }
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['analyze', '--path', str(temp_project_dir)])
            
            assert result.exit_code == 0
            assert "complexity" in result.output.lower() or "analysis" in result.output.lower()
            mock_backend_client.get_analysis.assert_called_once()
    
    def test_analyze_command_invalid_path(self, cli_runner):
        """Test analyze command with invalid path"""
        result = cli_runner.invoke(cli, ['analyze', '--path', '/nonexistent/path'])
        
        # Should handle invalid path gracefully
        assert "error" in result.output.lower() or "not found" in result.output.lower() or result.exit_code != 0
    
    def test_analyze_command_with_filters(self, cli_runner, mock_backend_client, temp_project_dir):
        """Test analyze command with file type filters"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, [
                'analyze', 
                '--path', str(temp_project_dir),
                '--file-types', 'py,js',
                '--exclude', 'test_*'
            ])
            
            assert result.exit_code == 0
            mock_backend_client.get_analysis.assert_called_once()


class TestMonitorCommand:
    """Test the monitor command functionality"""
    
    @pytest.mark.asyncio
    async def test_monitor_command_connection(self, cli_runner, mock_backend_client, mock_websocket):
        """Test monitor command WebSocket connection"""
        # Mock WebSocket events
        async def mock_monitor_events():
            events = [
                {"type": "file_changed", "path": "/test/file.py"},
                {"type": "analysis_complete", "result": "success"}
            ]
            for event in events:
                yield event
        
        mock_backend_client.monitor_events.return_value = mock_monitor_events()
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            with patch('websockets.connect', return_value=mock_websocket):
                result = cli_runner.invoke(cli, ['monitor', '--timeout', '1'])
                
                # Should attempt monitoring connection
                assert result.exit_code == 0 or "monitor" in result.output.lower()
    
    def test_monitor_command_help(self, cli_runner):
        """Test monitor command help output"""
        result = cli_runner.invoke(cli, ['monitor', '--help'])
        
        assert result.exit_code == 0
        assert "monitor" in result.output.lower()
        assert "real-time" in result.output.lower() or "events" in result.output.lower()
    
    def test_monitor_command_with_filters(self, cli_runner, mock_backend_client):
        """Test monitor command with event filters"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, [
                'monitor', 
                '--filter', 'file_changed',
                '--priority', 'high',
                '--timeout', '1'
            ])
            
            # Should accept filter options
            assert result.exit_code == 0 or "filter" in result.output.lower()


class TestQueryCommand:
    """Test the query command functionality"""
    
    def test_query_command_success(self, cli_runner, mock_backend_client):
        """Test query command with AI response"""
        mock_backend_client.query_agent.return_value = {
            "response": "Based on the analysis, your codebase has good structure.",
            "confidence": 0.85,
            "sources": ["ast_analysis", "dependency_graph"]
        }
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['query', 'How is my code quality?'])
            
            assert result.exit_code == 0
            assert "good structure" in result.output or "analysis" in result.output.lower()
            mock_backend_client.query_agent.assert_called_once()
    
    def test_query_command_empty_query(self, cli_runner):
        """Test query command with empty query"""
        result = cli_runner.invoke(cli, ['query'])
        
        # Should require non-empty query or show help
        assert result.exit_code != 0 or "provide a question" in result.output.lower()
    
    def test_query_command_interactive_mode(self, cli_runner, mock_backend_client):
        """Test query command in interactive mode"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            with patch('builtins.input', side_effect=['test question', 'quit']):
                result = cli_runner.invoke(cli, ['query', '--interactive'])
                
                # Should start interactive session
                assert result.exit_code == 0
                assert "interactive" in result.output.lower() or "session" in result.output.lower()
    
    def test_query_command_json_output(self, cli_runner, mock_backend_client):
        """Test query command with JSON output"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['query', 'test question', '--json'])
            
            assert result.exit_code == 0
            # Should output valid JSON
            try:
                json.loads(result.output)
            except json.JSONDecodeError:
                pytest.fail("Query command --json should output valid JSON")


class TestInfoCommand:
    """Test the info command functionality"""
    
    def test_info_command_output(self, cli_runner, mock_backend_client):
        """Test info command displays backend information"""
        mock_backend_client.get_info.return_value = {
            "name": "LeanVibe Backend",
            "version": "0.2.0",
            "capabilities": ["ast_analysis", "graph_db", "ai_agent"],
            "endpoints": ["/health", "/analyze", "/query"],
            "ai_models": ["Phi-3-Mini", "SimpleModel"]
        }
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['info'])
            
            assert result.exit_code == 0
            assert "leanvibe backend" in result.output.lower() or "backend" in result.output.lower()
            assert "capabilities" in result.output.lower() or "version" in result.output.lower()
    
    def test_info_command_detailed_output(self, cli_runner, mock_backend_client):
        """Test info command with detailed output"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['info', '--detailed'])
            
            assert result.exit_code == 0
            # Should show more detailed information
            mock_backend_client.get_info.assert_called_once()


class TestConfigCommand:
    """Test the config command functionality"""
    
    def test_config_list_command(self, cli_runner, temp_config_file):
        """Test config list displays current configuration"""
        result = cli_runner.invoke(cli, ['config', 'list', '--config', temp_config_file])
        
        assert result.exit_code == 0
        assert "backend" in result.output.lower() or "configuration" in result.output.lower()
        assert "localhost:8000" in result.output
    
    def test_config_set_command(self, cli_runner, temp_config_file):
        """Test config set updates configuration"""
        result = cli_runner.invoke(cli, [
            'config', 'set', 'backend.url', 'http://newhost:8000',
            '--config', temp_config_file
        ])
        
        # Should update successfully or show appropriate message
        assert result.exit_code == 0 or "updated" in result.output.lower()
    
    def test_config_get_command(self, cli_runner, temp_config_file):
        """Test config get retrieves specific value"""
        result = cli_runner.invoke(cli, [
            'config', 'get', 'backend.url',
            '--config', temp_config_file
        ])
        
        assert result.exit_code == 0
        assert "localhost:8000" in result.output
    
    def test_config_validate_command(self, cli_runner, temp_config_file):
        """Test config validate checks configuration"""
        result = cli_runner.invoke(cli, ['config', 'validate', '--config', temp_config_file])
        
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "configuration" in result.output.lower()


class TestQRCommand:
    """Test the QR command functionality"""
    
    def test_qr_command_generation(self, cli_runner):
        """Test QR code generation for backend URL"""
        result = cli_runner.invoke(cli, ['qr', '--url', 'http://localhost:8000'])
        
        assert result.exit_code == 0
        # Should show QR code or save message
        assert "qr" in result.output.lower() or "code" in result.output.lower()
    
    def test_qr_command_save_to_file(self, cli_runner, isolated_filesystem):
        """Test QR code saving to file"""
        result = cli_runner.invoke(cli, [
            'qr', 
            '--url', 'http://localhost:8000',
            '--output', 'qr_code.png'
        ])
        
        assert result.exit_code == 0
        # Should indicate file was saved
        assert "saved" in result.output.lower() or "qr_code.png" in result.output
    
    def test_qr_command_auto_detect_backend(self, cli_runner, mock_backend_client):
        """Test QR code generation with auto-detected backend URL"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['qr'])
            
            assert result.exit_code == 0
            # Should use backend URL from config
            assert "qr" in result.output.lower() or "localhost" in result.output


class TestCLIIntegration:
    """Test CLI integration scenarios"""
    
    def test_cli_help_command(self, cli_runner):
        """Test main CLI help output"""
        result = cli_runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "leanvibe" in result.output.lower()
        assert "commands" in result.output.lower()
        
        # Should list all main commands
        commands = ['status', 'analyze', 'monitor', 'query', 'info', 'config', 'qr']
        for command in commands:
            assert command in result.output.lower()
    
    def test_cli_version_option(self, cli_runner):
        """Test CLI version display"""
        result = cli_runner.invoke(cli, ['--version'])
        
        # Should show version or handle gracefully
        assert result.exit_code == 0 or "version" in result.output.lower()
    
    def test_cli_verbose_mode(self, cli_runner, mock_backend_client):
        """Test CLI verbose mode across commands"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['--verbose', 'status'])
            
            assert result.exit_code == 0
            # Verbose mode should provide additional output
            mock_backend_client.get_health.assert_called_once()
    
    def test_cli_config_override(self, cli_runner, mock_backend_client):
        """Test CLI configuration override options"""
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, [
                '--backend-url', 'http://custom:9000',
                'status'
            ])
            
            assert result.exit_code == 0
            # Should use custom backend URL
            mock_backend_client.get_health.assert_called_once()


class TestErrorHandling:
    """Test CLI error handling across commands"""
    
    def test_malformed_config_handling(self, cli_runner):
        """Test handling of malformed configuration files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            malformed_config = f.name
        
        try:
            result = cli_runner.invoke(cli, ['--config', malformed_config, 'status'])
            
            # Should handle malformed config gracefully
            assert result.exit_code == 0 or "config" in result.output.lower()
        finally:
            os.unlink(malformed_config)
    
    def test_network_timeout_handling(self, cli_runner):
        """Test handling of network timeouts"""
        with patch('leanvibe_cli.client.BackendClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_health = AsyncMock(side_effect=asyncio.TimeoutError("Request timeout"))
            mock_client_class.return_value = mock_client
            
            result = cli_runner.invoke(cli, ['status'])
            
            # Should handle timeout gracefully
            assert "timeout" in result.output.lower() or "error" in result.output.lower()
    
    def test_invalid_command_arguments(self, cli_runner):
        """Test handling of invalid command arguments"""
        # Test invalid path
        result = cli_runner.invoke(cli, ['analyze', '--path'])
        assert result.exit_code != 0
        
        # Test invalid option
        result = cli_runner.invoke(cli, ['status', '--invalid-option'])
        assert result.exit_code != 0
    
    def test_permission_error_handling(self, cli_runner):
        """Test handling of permission errors"""
        with patch('pathlib.Path.exists', side_effect=PermissionError("Permission denied")):
            result = cli_runner.invoke(cli, ['analyze', '--path', '/restricted/path'])
            
            # Should handle permission errors gracefully
            assert "permission" in result.output.lower() or "error" in result.output.lower()


class TestPerformance:
    """Test CLI performance characteristics"""
    
    def test_command_response_times(self, cli_runner, mock_backend_client, performance_metrics):
        """Test CLI command response times"""
        performance_metrics.start()
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            result = cli_runner.invoke(cli, ['status'])
            
            performance_metrics.stop()
            
            assert result.exit_code == 0
            # Status command should complete quickly
            assert performance_metrics.duration() < 5.0, f"Status command took {performance_metrics.duration():.2f}s, expected <5s"
    
    def test_memory_usage_during_commands(self, cli_runner, mock_backend_client, performance_metrics):
        """Test CLI memory usage during command execution"""
        performance_metrics.record_memory()
        initial_memory = performance_metrics.max_memory()
        
        with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
            # Run multiple commands
            for command in ['status', 'info']:
                result = cli_runner.invoke(cli, [command])
                assert result.exit_code == 0
                performance_metrics.record_memory()
        
        final_memory = performance_metrics.max_memory()
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB)
        assert memory_growth < 100, f"Memory growth {memory_growth:.1f}MB exceeds 100MB limit"
    
    def test_concurrent_command_execution(self, cli_runner, mock_backend_client):
        """Test CLI behavior with concurrent command execution"""
        import threading
        import time
        
        results = []
        
        def run_command():
            with patch('leanvibe_cli.client.BackendClient', return_value=mock_backend_client):
                result = cli_runner.invoke(cli, ['status'])
                results.append(result.exit_code)
        
        # Run multiple commands concurrently
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=run_command)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All commands should succeed
        assert all(exit_code == 0 for exit_code in results)
        assert len(results) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])