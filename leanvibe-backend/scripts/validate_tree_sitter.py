#!/usr/bin/env python3
"""
Tree-sitter Installation Validation Script

Tests that tree-sitter and all language parsers are properly installed and functional.
"""

import sys
from typing import List, Tuple


def test_tree_sitter_core() -> Tuple[bool, str]:
    """Test core tree-sitter functionality"""
    try:
        import tree_sitter
        from tree_sitter import Language, Parser
        
        # Check version if available
        version = getattr(tree_sitter, '__version__', 'Unknown')
        return True, f"tree-sitter core imported successfully (version: {version})"
    except ImportError as e:
        return False, f"Failed to import tree-sitter: {e}"


def test_python_parser() -> Tuple[bool, str]:
    """Test Python parser functionality"""
    try:
        import tree_sitter
        import tree_sitter_python
        from tree_sitter import Language, Parser
        
        # Create language and parser
        language = Language(tree_sitter_python.language())
        parser = Parser(language)
        
        # Test parsing simple Python code
        code = b"""
def hello_world():
    print("Hello, World!")
    return True
"""
        
        tree = parser.parse(code)
        root = tree.root_node
        
        # Verify we got a valid parse tree
        if root.type == "module" and len(root.children) > 0:
            return True, "Python parser working correctly"
        else:
            return False, f"Python parser returned unexpected tree structure: {root.type}"
            
    except Exception as e:
        return False, f"Python parser failed: {e}"


def test_javascript_parser() -> Tuple[bool, str]:
    """Test JavaScript parser functionality"""
    try:
        import tree_sitter
        import tree_sitter_javascript
        from tree_sitter import Language, Parser
        
        # Create language and parser
        language = Language(tree_sitter_javascript.language())
        parser = Parser(language)
        
        # Test parsing simple JavaScript code
        code = b"""
function helloWorld() {
    console.log("Hello, World!");
    return true;
}
"""
        
        tree = parser.parse(code)
        root = tree.root_node
        
        # Verify we got a valid parse tree
        if root.type == "program" and len(root.children) > 0:
            return True, "JavaScript parser working correctly"
        else:
            return False, f"JavaScript parser returned unexpected tree structure: {root.type}"
            
    except Exception as e:
        return False, f"JavaScript parser failed: {e}"


def test_typescript_parser() -> Tuple[bool, str]:
    """Test TypeScript parser functionality"""
    try:
        import tree_sitter
        import tree_sitter_typescript
        from tree_sitter import Language, Parser
        
        # Test TypeScript language
        ts_language = Language(tree_sitter_typescript.language_typescript())
        ts_parser = Parser(ts_language)
        
        # Test parsing simple TypeScript code
        ts_code = b"""
interface User {
    name: string;
    age: number;
}

function greetUser(user: User): string {
    return `Hello, ${user.name}!`;
}
"""
        
        ts_tree = ts_parser.parse(ts_code)
        ts_root = ts_tree.root_node
        
        # Test TSX language
        tsx_language = Language(tree_sitter_typescript.language_tsx())
        tsx_parser = Parser(tsx_language)
        
        # Test parsing simple TSX code
        tsx_code = b"""
import React from 'react';

interface Props {
    name: string;
}

const Greeting: React.FC<Props> = ({ name }) => {
    return <h1>Hello, {name}!</h1>;
};
"""
        
        tsx_tree = tsx_parser.parse(tsx_code)
        tsx_root = tsx_tree.root_node
        
        # Verify both parsers work
        if ts_root.type == "program" and tsx_root.type == "program":
            return True, "TypeScript and TSX parsers working correctly"
        else:
            return False, f"TypeScript parsers returned unexpected tree structures: TS={ts_root.type}, TSX={tsx_root.type}"
            
    except Exception as e:
        return False, f"TypeScript parser failed: {e}"


def test_tree_sitter_manager() -> Tuple[bool, str]:
    """Test the TreeSitterManager from the service"""
    try:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Import our service
        sys.path.append("/Users/bogdan/work/leanvibe-ai/leanvibe-backend")
        from app.services.tree_sitter_parsers import TreeSitterManager
        
        async def test_manager():
            executor = ThreadPoolExecutor(max_workers=2)
            manager = TreeSitterManager(executor)
            
            # Initialize the manager
            await manager.initialize()
            
            if not manager.initialized:
                return False, "TreeSitterManager failed to initialize"
            
            # Test language detection
            py_lang = manager.detect_language("test.py")
            js_lang = manager.detect_language("test.js")
            ts_lang = manager.detect_language("test.ts")
            
            from app.models.ast_models import LanguageType
            
            if py_lang != LanguageType.PYTHON:
                return False, f"Python language detection failed: got {py_lang}"
            if js_lang != LanguageType.JAVASCRIPT:
                return False, f"JavaScript language detection failed: got {js_lang}"
            if ts_lang != LanguageType.TYPESCRIPT:
                return False, f"TypeScript language detection failed: got {ts_lang}"
            
            # Test parsing
            python_code = "def test(): pass"
            tree, errors = manager.parse_file("test.py", python_code)
            
            if tree is None:
                return False, f"Failed to parse Python code: {errors}"
            
            executor.shutdown(wait=True)
            return True, f"TreeSitterManager working correctly with {len(manager.languages)} languages"
        
        # Run the async test
        result = asyncio.run(test_manager())
        return result
        
    except Exception as e:
        return False, f"TreeSitterManager test failed: {e}"


def main():
    """Run all tree-sitter validation tests"""
    print("🌲 Tree-sitter Installation Validation")
    print("=" * 50)
    
    tests = [
        ("Core tree-sitter", test_tree_sitter_core),
        ("Python parser", test_python_parser),
        ("JavaScript parser", test_javascript_parser),
        ("TypeScript parser", test_typescript_parser),
        ("TreeSitterManager service", test_tree_sitter_manager),
    ]
    
    results: List[Tuple[str, bool, str]] = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        success, message = test_func()
        results.append((test_name, success, message))
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tree-sitter tests PASSED! Installation is working correctly.")
        return 0
    else:
        print("⚠️  Some tree-sitter tests FAILED. Check the output above for details.")
        print("\nFailed tests:")
        for test_name, success, message in results:
            if not success:
                print(f"  - {test_name}: {message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())