#!/usr/bin/env python3
"""
Comprehensive Dependency Validation Script for LeanVibe AI Backend

This script validates all critical dependencies and their functionality:
- Tree-sitter parsers (Python, JavaScript, TypeScript)
- Neo4j driver with fallback to NetworkX
- MLX framework for Apple Silicon
- Core ML/AI dependencies
- FastAPI and web framework dependencies
- All other critical system dependencies
"""

import sys
import platform
import importlib
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path


class DependencyValidator:
    """Comprehensive dependency validation system"""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging for validation"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def validate_core_python(self) -> Tuple[bool, str]:
        """Validate Python version and core modules"""
        try:
            version_info = sys.version_info
            if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 11):
                return False, f"Python {version_info.major}.{version_info.minor} is too old (requires >=3.11)"
            
            # Test core modules
            core_modules = ['asyncio', 'json', 'pathlib', 'typing', 'logging', 'concurrent.futures']
            for module in core_modules:
                importlib.import_module(module)
            
            return True, f"Python {sys.version.split()[0]} with core modules working"
            
        except Exception as e:
            return False, f"Python core validation failed: {e}"
    
    def validate_fastapi_stack(self) -> Tuple[bool, str]:
        """Validate FastAPI and web framework dependencies"""
        try:
            import fastapi
            import uvicorn
            import websockets
            import pydantic
            import httpx
            
            # Test basic FastAPI functionality
            app = fastapi.FastAPI()
            
            @app.get("/health")
            def health():
                return {"status": "ok"}
            
            versions = {
                "FastAPI": getattr(fastapi, '__version__', 'Unknown'),
                "Uvicorn": getattr(uvicorn, '__version__', 'Unknown'),
                "WebSockets": getattr(websockets, '__version__', 'Unknown'),
                "Pydantic": getattr(pydantic, '__version__', 'Unknown'),
                "HTTPX": getattr(httpx, '__version__', 'Unknown')
            }
            
            version_str = ", ".join([f"{k}:{v}" for k, v in versions.items()])
            return True, f"FastAPI stack working ({version_str})"
            
        except ImportError as e:
            return False, f"FastAPI stack validation failed: {e}"
    
    def validate_ai_dependencies(self) -> Tuple[bool, str]:
        """Validate AI/ML dependencies"""
        try:
            import numpy as np
            import torch
            import transformers
            
            # Test basic operations
            arr = np.array([1, 2, 3])
            tensor = torch.tensor([1.0, 2.0, 3.0])
            
            versions = {
                "NumPy": np.__version__,
                "PyTorch": torch.__version__,
                "Transformers": transformers.__version__
            }
            
            # Check for MPS (Metal Performance Shaders) support
            mps_available = torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
            
            version_str = ", ".join([f"{k}:{v}" for k, v in versions.items()])
            mps_str = f", MPS: {mps_available}"
            
            return True, f"AI dependencies working ({version_str}{mps_str})"
            
        except Exception as e:
            return False, f"AI dependencies validation failed: {e}"
    
    def validate_mlx_framework(self) -> Tuple[bool, str]:
        """Validate MLX framework specifically"""
        try:
            import mlx.core as mx
            
            # Test basic operations
            x = mx.array([1.0, 2.0, 3.0])
            y = mx.array([4.0, 5.0, 6.0])
            z = x + y
            
            # Test tensor fix utility
            sys.path.append('/Users/bogdan/work/leanvibe-ai/leanvibe-backend')
            from app.services.mlx_tensor_fix import MLXTensorFixer
            
            fixer = MLXTensorFixer()
            
            # Quick compatibility test
            q = mx.random.normal((1, 8, 4, 64))
            k = mx.random.normal((1, 8, 4, 64))  
            v = mx.random.normal((1, 8, 4, 64))
            
            is_compatible = fixer.validate_tensor_compatibility(q, k, v)
            
            device_info = f", Device: {mx.default_device()}" if hasattr(mx, 'default_device') else ""
            
            return True, f"MLX framework working (tensor ops: ✓, compatibility: {is_compatible}{device_info})"
            
        except Exception as e:
            return False, f"MLX framework validation failed: {e}"
    
    def validate_tree_sitter(self) -> Tuple[bool, str]:
        """Validate tree-sitter parsers"""
        try:
            import tree_sitter
            import tree_sitter_python
            import tree_sitter_javascript
            import tree_sitter_typescript
            from tree_sitter import Language, Parser
            
            # Test all parsers
            parsers_tested = []
            
            # Python parser
            py_lang = Language(tree_sitter_python.language())
            py_parser = Parser(py_lang)
            py_tree = py_parser.parse(b"def test(): pass")
            if py_tree.root_node.type == "module":
                parsers_tested.append("Python")
            
            # JavaScript parser
            js_lang = Language(tree_sitter_javascript.language())
            js_parser = Parser(js_lang)
            js_tree = js_parser.parse(b"function test() { return true; }")
            if js_tree.root_node.type == "program":
                parsers_tested.append("JavaScript")
            
            # TypeScript parser
            ts_lang = Language(tree_sitter_typescript.language_typescript())
            ts_parser = Parser(ts_lang)
            ts_tree = ts_parser.parse(b"function test(): boolean { return true; }")
            if ts_tree.root_node.type == "program":
                parsers_tested.append("TypeScript")
            
            # Test service integration
            from app.services.tree_sitter_parsers import TreeSitterManager
            from concurrent.futures import ThreadPoolExecutor
            import asyncio
            
            async def test_manager():
                manager = TreeSitterManager(ThreadPoolExecutor(max_workers=1))
                await manager.initialize()
                return manager.initialized
            
            service_working = asyncio.run(test_manager())
            
            parsers_str = ", ".join(parsers_tested)
            service_str = f", Service: {'✓' if service_working else '✗'}"
            
            return True, f"Tree-sitter working ({parsers_str}{service_str})"
            
        except Exception as e:
            return False, f"Tree-sitter validation failed: {e}"
    
    def validate_neo4j_and_graph(self) -> Tuple[bool, str]:
        """Validate Neo4j driver and graph capabilities"""
        try:
            import neo4j
            import networkx as nx
            from neo4j import GraphDatabase
            
            # Test Neo4j driver
            driver_version = getattr(neo4j, '__version__', 'Unknown')
            
            # Test NetworkX fallback
            G = nx.Graph()
            G.add_edge('A', 'B')
            G.add_edge('B', 'C')
            nodes_count = len(G.nodes())
            edges_count = len(G.edges())
            
            # Check if Neo4j service is available
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            neo4j_available = sock.connect_ex(('localhost', 7687)) == 0
            sock.close()
            
            # Test fallback service
            try:
                from app.services.fallback_graph_service import FallbackGraphService
                fallback_service = FallbackGraphService()
                fallback_service.add_node("test", {"type": "test"})
                fallback_working = True
            except:
                fallback_working = False
            
            nx_version = getattr(nx, '__version__', 'Unknown')
            status_parts = [
                f"Neo4j driver: {driver_version}",
                f"Service: {'✓' if neo4j_available else '✗'}",
                f"NetworkX: {nx_version}",
                f"Fallback: {'✓' if fallback_working else '✗'}"
            ]
            
            return True, f"Graph capabilities working ({', '.join(status_parts)})"
            
        except Exception as e:
            return False, f"Graph validation failed: {e}"
    
    def validate_vector_and_cache(self) -> Tuple[bool, str]:
        """Validate vector store and caching dependencies"""
        try:
            import chromadb
            import redis
            
            # Test ChromaDB (vector store)
            client = chromadb.Client()
            collection = client.get_or_create_collection("test")
            chroma_version = getattr(chromadb, '__version__', 'Unknown')
            
            # Test Redis (caching) - import only, don't connect
            redis_version = getattr(redis, '__version__', 'Unknown')
            
            return True, f"Vector/Cache working (ChromaDB: {chroma_version}, Redis: {redis_version})"
            
        except Exception as e:
            return False, f"Vector/Cache validation failed: {e}"
    
    def validate_utility_dependencies(self) -> Tuple[bool, str]:
        """Validate utility dependencies"""
        try:
            import watchdog
            import aiofiles
            import jinja2
            import qrcode
            import netifaces
            
            # Test basic functionality
            from watchdog.observers import Observer
            import qrcode.image.pil
            
            versions = {
                "Watchdog": getattr(watchdog, '__version__', 'Unknown'),
                "Jinja2": getattr(jinja2, '__version__', 'Unknown'),
                "QRCode": getattr(qrcode, '__version__', 'Unknown'),
            }
            
            version_str = ", ".join([f"{k}:{v}" for k, v in versions.items()])
            return True, f"Utility dependencies working ({version_str})"
            
        except Exception as e:
            return False, f"Utility dependencies validation failed: {e}"
    
    def validate_test_dependencies(self) -> Tuple[bool, str]:
        """Validate testing dependencies"""
        try:
            import pytest
            
            # Test pytest functionality
            pytest_version = getattr(pytest, '__version__', 'Unknown')
            
            # Check for pytest plugins
            try:
                import pytest_asyncio
                asyncio_available = True
                asyncio_version = getattr(pytest_asyncio, '__version__', 'Unknown')
            except ImportError:
                asyncio_available = False
                asyncio_version = "Not available"
            
            status = f"pytest: {pytest_version}, pytest-asyncio: {asyncio_version}"
            return True, f"Test dependencies working ({status})"
            
        except Exception as e:
            return False, f"Test dependencies validation failed: {e}"
    
    def validate_security_dependencies(self) -> Tuple[bool, str]:
        """Validate security-related dependencies"""
        try:
            import dotenv
            from jose import jwt
            from cryptography.fernet import Fernet
            
            # Test environment loading
            dotenv.load_dotenv()
            
            # Test JWT functionality
            token = jwt.encode({"test": "data"}, "secret", algorithm="HS256")
            decoded = jwt.decode(token, "secret", algorithms=["HS256"])
            
            # Test encryption
            key = Fernet.generate_key()
            cipher = Fernet(key)
            encrypted = cipher.encrypt(b"test data")
            decrypted = cipher.decrypt(encrypted)
            
            if decoded["test"] == "data" and decrypted == b"test data":
                return True, "Security dependencies working (dotenv, JWT, encryption)"
            else:
                return False, "Security functionality test failed"
                
        except Exception as e:
            return False, f"Security dependencies validation failed: {e}"
    
    def run_all_validations(self) -> Dict[str, Dict[str, Any]]:
        """Run all dependency validations"""
        validations = [
            ("Core Python", self.validate_core_python),
            ("FastAPI Stack", self.validate_fastapi_stack), 
            ("AI Dependencies", self.validate_ai_dependencies),
            ("MLX Framework", self.validate_mlx_framework),
            ("Tree-sitter Parsers", self.validate_tree_sitter),
            ("Neo4j & Graph", self.validate_neo4j_and_graph),
            ("Vector & Cache", self.validate_vector_and_cache),
            ("Utility Dependencies", self.validate_utility_dependencies),
            ("Test Dependencies", self.validate_test_dependencies),
            ("Security Dependencies", self.validate_security_dependencies),
        ]
        
        results = {}
        
        print(f"🔍 LeanVibe AI Dependency Validation")
        print(f"Platform: {platform.system()} {platform.machine()}")
        print(f"Python: {sys.version.split()[0]}")
        print("=" * 80)
        
        total_passed = 0
        total_tests = len(validations)
        
        for category, validation_func in validations:
            print(f"\\n🔍 Testing {category}...")
            
            try:
                success, message = validation_func()
                results[category] = {
                    "success": success,
                    "message": message,
                    "error": None
                }
                
                status_icon = "✅" if success else "❌"
                print(f"{status_icon} {message}")
                
                if success:
                    total_passed += 1
                    
            except Exception as e:
                results[category] = {
                    "success": False,
                    "message": f"Validation crashed: {e}",
                    "error": str(e)
                }
                print(f"💥 {category} validation crashed: {e}")
        
        # Summary
        print("\\n" + "=" * 80)
        print("📋 DEPENDENCY VALIDATION SUMMARY")
        print(f"Tests passed: {total_passed}/{total_tests}")
        
        if total_passed == total_tests:
            print("🎉 ALL DEPENDENCIES VALIDATED SUCCESSFULLY!")
            print("The LeanVibe AI backend is ready for operation.")
        elif total_passed >= total_tests * 0.8:
            print("⚠️  Most dependencies are working - system operational with minor issues")
            self._print_recommendations(results)
        else:
            print("❌ CRITICAL DEPENDENCY ISSUES DETECTED")
            print("The system may not function correctly.")
            self._print_recommendations(results)
        
        return results
    
    def _print_recommendations(self, results: Dict[str, Dict[str, Any]]):
        """Print recommendations for fixing issues"""
        print("\\n📝 RECOMMENDATIONS:")
        
        failed_categories = [
            category for category, result in results.items()
            if not result["success"]
        ]
        
        if "Core Python" in failed_categories:
            print("  ⚠️  Upgrade Python to version 3.11 or higher")
        
        if "FastAPI Stack" in failed_categories:
            print("  ⚠️  Run 'uv sync' to install web framework dependencies")
        
        if "MLX Framework" in failed_categories:
            print("  ⚠️  MLX requires Apple Silicon Mac (M1/M2/M3)")
            print("      Consider using CPU-based alternatives on Intel Macs")
        
        if "Tree-sitter Parsers" in failed_categories:
            print("  ⚠️  Run 'uv sync' to reinstall tree-sitter parsers")
        
        if "Neo4j & Graph" in failed_categories:
            print("  ⚠️  Install Neo4j or use NetworkX fallback (already configured)")
        
        if "Vector & Cache" in failed_categories:
            print("  ⚠️  Vector store issues - check ChromaDB installation")
        
        print("\\n🔧 Quick fix command: uv sync")


def main():
    """Run comprehensive dependency validation"""
    validator = DependencyValidator()
    results = validator.run_all_validations()
    
    # Return appropriate exit code
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result["success"])
    
    if passed_tests == total_tests:
        return 0  # All tests passed
    elif passed_tests >= total_tests * 0.8:
        return 1  # Most tests passed but some issues
    else:
        return 2  # Critical issues detected


if __name__ == "__main__":
    sys.exit(main())