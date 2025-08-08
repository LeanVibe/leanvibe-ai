"""
Mock Infrastructure for LeanVibe Testing

This module provides comprehensive mocking infrastructure that allows all tests
to run without external dependencies like tree-sitter, Neo4j, or MLX.

The mocks are designed to:
1. Provide realistic behavior for testing
2. Handle all import errors gracefully
3. Allow tests to focus on business logic
4. Maintain consistent interfaces with real services
"""

import sys
import logging
from unittest.mock import MagicMock, patch
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Import availability flags
_TREE_SITTER_AVAILABLE = False
_NEO4J_AVAILABLE = False
_MLX_AVAILABLE = False

# Try to detect real dependencies
try:
    import tree_sitter
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    pass

try:
    from neo4j import GraphDatabase
    _NEO4J_AVAILABLE = True
except ImportError:
    pass

try:
    import mlx
    _MLX_AVAILABLE = True
except ImportError:
    pass


def setup_tree_sitter_mocks():
    """Set up tree-sitter mocking"""
    if _TREE_SITTER_AVAILABLE:
        logger.info("Tree-sitter is available, using real implementation")
        return
    
    logger.info("Setting up tree-sitter mocks")
    
    # Import our mocks
    from .mock_tree_sitter import (
        MockTreeSitterModule,
        MockTreeSitterPython,
        MockTreeSitterJavaScript,
        MockTreeSitterTypeScript,
        mock_tree_sitter_manager
    )
    
    # Mock the modules in sys.modules
    sys.modules['tree_sitter'] = MockTreeSitterModule()
    sys.modules['tree_sitter_python'] = MockTreeSitterPython()
    sys.modules['tree_sitter_javascript'] = MockTreeSitterJavaScript()
    sys.modules['tree_sitter_typescript'] = MockTreeSitterTypeScript()
    
    # Replace the global tree_sitter_manager
    import app.services.tree_sitter_parsers
    app.services.tree_sitter_parsers.tree_sitter_manager = mock_tree_sitter_manager


def setup_neo4j_mocks():
    """Set up Neo4j mocking"""
    if _NEO4J_AVAILABLE:
        logger.info("Neo4j is available, using real implementation for tests")
        # Even with Neo4j available, we might want to use mocks for faster tests
        # return
    
    logger.info("Setting up Neo4j mocks")
    
    # Import our mocks
    from .mock_neo4j import MockGraphDatabase, mock_graph_service
    
    # Mock the neo4j module
    mock_neo4j = MagicMock()
    mock_neo4j.GraphDatabase = MockGraphDatabase
    mock_neo4j.Driver = MockGraphDatabase.driver
    sys.modules['neo4j'] = mock_neo4j
    
    # Replace the global graph service
    import app.services.graph_service
    app.services.graph_service.graph_service = mock_graph_service


def setup_mlx_mocks():
    """Set up MLX mocking"""
    if _MLX_AVAILABLE:
        logger.info("MLX is available, using real implementation")
        return
    
    logger.info("Setting up MLX mocks")
    
    # Import our mocks
    from .mock_mlx_services import (
        MockMLX,
        MockMLXModule,
        mock_mlx_service,
        mock_transformers_service
    )
    
    # Create mock MLX module with proper spec
    mock_mlx_module = MockMLX()
    mock_mlx_module.__spec__ = MagicMock()
    mock_mlx_module.__spec__.name = "mlx"
    mock_mlx_module.__file__ = "<mock>"
    
    # Mock the MLX modules  
    sys.modules['mlx'] = mock_mlx_module
    
    mock_mlx_core = MockMLXModule()
    mock_mlx_core.__spec__ = MagicMock()
    mock_mlx_core.__spec__.name = "mlx.core"
    sys.modules['mlx.core'] = mock_mlx_core
    
    mock_mlx_nn = MagicMock()
    mock_mlx_nn.__spec__ = MagicMock()
    mock_mlx_nn.__spec__.name = "mlx.nn"
    sys.modules['mlx.nn'] = mock_mlx_nn
    
    mock_mlx_opt = MagicMock()
    mock_mlx_opt.__spec__ = MagicMock()
    mock_mlx_opt.__spec__.name = "mlx.optimizers"
    sys.modules['mlx.optimizers'] = mock_mlx_opt
    
    # Don't mock transformers if it's available, as it may cause conflicts
    # Just replace service instances that use MLX
    try:
        import app.services.mlx_ai_service
        app.services.mlx_ai_service.mlx_service = mock_mlx_service
    except ImportError:
        pass
    
    try:
        import app.services.mock_mlx_service
        app.services.mock_mlx_service.mock_mlx_service = mock_mlx_service
    except ImportError:
        pass


def setup_all_mocks():
    """Set up all mocking infrastructure"""
    logger.info("Setting up comprehensive mock infrastructure...")
    
    setup_tree_sitter_mocks()
    setup_neo4j_mocks()
    setup_mlx_mocks()
    
    # Additional service mocks
    setup_additional_service_mocks()
    
    logger.info("Mock infrastructure setup complete")


def setup_additional_service_mocks():
    """Set up additional service-level mocks"""
    
    # Mock external API calls that might be made during testing
    mock_requests = MagicMock()
    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.json.return_value = {"status": "ok"}
    mock_requests.post.return_value.status_code = 200
    mock_requests.post.return_value.json.return_value = {"status": "ok"}
    
    # Don't override if requests is already available and we want to test real HTTP
    if 'requests' not in sys.modules:
        sys.modules['requests'] = mock_requests


def get_mock_status() -> Dict[str, Any]:
    """Get status of all mocks"""
    return {
        "tree_sitter": {
            "real_available": _TREE_SITTER_AVAILABLE,
            "mock_active": not _TREE_SITTER_AVAILABLE
        },
        "neo4j": {
            "real_available": _NEO4J_AVAILABLE,
            "mock_active": True  # We use mocks for faster tests
        },
        "mlx": {
            "real_available": _MLX_AVAILABLE,
            "mock_active": not _MLX_AVAILABLE
        }
    }


def cleanup_mocks():
    """Clean up all mocks (useful for test cleanup)"""
    logger.info("Cleaning up mock infrastructure")
    
    # Clean up tree-sitter mocks
    mock_modules = [
        'tree_sitter', 
        'tree_sitter_python',
        'tree_sitter_javascript', 
        'tree_sitter_typescript'
    ]
    
    for module in mock_modules:
        if module in sys.modules and hasattr(sys.modules[module], '__class__'):
            if 'Mock' in sys.modules[module].__class__.__name__:
                del sys.modules[module]


# Context managers for selective mocking
class TreeSitterMockContext:
    """Context manager for tree-sitter mocking"""
    
    def __enter__(self):
        setup_tree_sitter_mocks()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass  # Keep mocks active for test session


class Neo4jMockContext:
    """Context manager for Neo4j mocking"""
    
    def __enter__(self):
        setup_neo4j_mocks()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass  # Keep mocks active for test session


class MLXMockContext:
    """Context manager for MLX mocking"""
    
    def __enter__(self):
        setup_mlx_mocks()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass  # Keep mocks active for test session


# Auto-setup when imported (can be disabled by setting environment variable)
import os
if os.getenv('LEANVIBE_DISABLE_AUTO_MOCKS') != '1':
    setup_all_mocks()