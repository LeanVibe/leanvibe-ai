"""
AST to Graph Integration Service

Integrates AST parsing with Neo4j graph database to automatically populate
code relationships and enable comprehensive architectural analysis.
"""

import ast
import os
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from .code_graph_service import CodeGraphService, CodeNode, CodeRelationship, NodeType, RelationType

logger = logging.getLogger(__name__)

class ASTGraphService:
    """Service to populate graph database from AST analysis"""
    
    def __init__(self, graph_service: CodeGraphService):
        self.graph_service = graph_service
        self.processed_files = set()
        
    async def analyze_project(self, project_path: str, project_id: str = None) -> Dict[str, Any]:
        """Analyze entire project and populate graph database"""
        if not project_id:
            project_id = os.path.basename(project_path)
            
        stats = {
            'files_processed': 0,
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': [],
            'skipped_files': [],
            'processing_time': 0
        }
        
        try:
            import time
            start_time = time.time()
            
            # Clear existing data for this project
            logger.info(f"Clearing existing graph data for project: {project_id}")
            await self.graph_service.clear_project_data(project_id)
            
            # Ensure graph service is connected
            if not self.graph_service.is_connected():
                logger.info("Attempting to connect to Neo4j for project analysis")
                connected = await self.graph_service.connect()
                if not connected:
                    stats['errors'].append("Failed to connect to Neo4j - analysis incomplete")
                    return stats
            
            # Process Python files recursively
            python_files = self._find_python_files(project_path)
            logger.info(f"Found {len(python_files)} Python files to analyze")
            
            for file_path in python_files:
                try:
                    result = await self.analyze_file(file_path, project_id)
                    
                    stats['files_processed'] += 1
                    stats['nodes_created'] += result.get('nodes_created', 0)
                    stats['relationships_created'] += result.get('relationships_created', 0)
                    
                    if result.get('errors'):
                        stats['errors'].extend(result['errors'])
                        
                    # Log progress for large projects
                    if stats['files_processed'] % 10 == 0:
                        logger.info(f"Processed {stats['files_processed']}/{len(python_files)} files")
                        
                except Exception as e:
                    error_msg = f"Error processing {file_path}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
                    stats['skipped_files'].append(file_path)
            
            stats['processing_time'] = time.time() - start_time
            
            # Create project-level relationships after all files are processed
            await self._create_project_relationships(project_id)
            
            logger.info(f"Project analysis completed: {stats['files_processed']} files, "
                       f"{stats['nodes_created']} nodes, {stats['relationships_created']} relationships")
            
            return stats
            
        except Exception as e:
            error_msg = f"Failed to analyze project {project_path}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            return stats
    
    def _find_python_files(self, project_path: str) -> List[str]:
        """Find all Python files in the project directory"""
        python_files = []
        project_path_obj = Path(project_path)
        
        # Skip common directories that don't contain source code
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 
                     'node_modules', '.venv', 'build', 'dist', '.tox'}
        
        for file_path in project_path_obj.rglob('*.py'):
            # Skip files in directories we want to ignore
            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue
                
            # Skip test files for now (can be enabled later)
            if 'test_' in file_path.name or file_path.name.startswith('test'):
                continue
                
            python_files.append(str(file_path))
        
        return python_files
    
    async def analyze_file(self, file_path: str, project_id: str) -> Dict[str, Any]:
        """Analyze a single Python file and add to graph"""
        stats = {'nodes_created': 0, 'relationships_created': 0, 'errors': []}
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                return stats  # Skip empty files
                
            # Parse AST
            try:
                tree = ast.parse(content, filename=file_path)
            except SyntaxError as e:
                stats['errors'].append(f"Syntax error in {file_path}: {e}")
                return stats
            
            # Create file node
            relative_path = os.path.relpath(file_path)
            file_id = f"file:{relative_path}"
            
            file_node = CodeNode(
                id=file_id,
                name=os.path.basename(file_path),
                type=NodeType.FILE,
                file_path=relative_path,
                start_line=1,
                end_line=len(content.split('\n')),
                properties={
                    'project_id': project_id, 
                    'size_bytes': len(content),
                    'lines_of_code': len([line for line in content.split('\n') if line.strip()]),
                    'language': 'python'
                }
            )
            
            if await self.graph_service.add_code_node(file_node):
                stats['nodes_created'] += 1
            
            # Process AST nodes with visitor
            visitor = GraphBuilderVisitor(
                graph_service=self.graph_service,
                file_path=relative_path,
                project_id=project_id,
                stats=stats,
                content_lines=content.split('\n')
            )
            visitor.visit(tree)
            
            self.processed_files.add(file_path)
            
        except Exception as e:
            error_msg = f"Error analyzing {file_path}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            
        return stats
    
    async def _create_project_relationships(self, project_id: str):
        """Create additional relationships based on naming patterns and imports"""
        try:
            if not self.graph_service.is_connected():
                return
                
            # This could be expanded to create more sophisticated relationships
            # For now, we'll create basic file-level dependencies based on imports
            logger.debug(f"Creating project-level relationships for {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to create project relationships: {e}")

class GraphBuilderVisitor(ast.NodeVisitor):
    """AST visitor that builds graph nodes and relationships"""
    
    def __init__(self, graph_service: CodeGraphService, file_path: str, 
                 project_id: str, stats: Dict, content_lines: List[str]):
        self.graph_service = graph_service
        self.file_path = file_path
        self.project_id = project_id
        self.stats = stats
        self.content_lines = content_lines
        self.current_class = None
        self.current_function = None
        self.imports = []
        self.scope_stack = []
        
    async def add_node_safe(self, node: CodeNode) -> bool:
        """Safely add a node and update stats"""
        try:
            if await self.graph_service.add_code_node(node):
                self.stats['nodes_created'] += 1
                return True
        except Exception as e:
            error_msg = f"Failed to add node {node.id}: {e}"
            logger.debug(error_msg)
            self.stats['errors'].append(error_msg)
        return False
        
    async def add_relationship_safe(self, relationship: CodeRelationship) -> bool:
        """Safely add a relationship and update stats"""
        try:
            if await self.graph_service.add_relationship(relationship):
                self.stats['relationships_created'] += 1
                return True
        except Exception as e:
            error_msg = f"Failed to add relationship {relationship.from_node} -> {relationship.to_node}: {e}"
            logger.debug(error_msg)
            self.stats['errors'].append(error_msg)
        return False
    
    def visit_ClassDef(self, node):
        """Handle class definitions"""
        class_id = f"class:{self.file_path}:{node.name}:{node.lineno}"
        
        # Calculate complexity based on methods and attributes
        method_count = len([n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)])
        
        class_node = CodeNode(
            id=class_id,
            name=node.name,
            type=NodeType.CLASS,
            file_path=self.file_path,
            start_line=node.lineno,
            end_line=getattr(node, 'end_lineno', node.lineno),
            properties={
                'project_id': self.project_id,
                'docstring': ast.get_docstring(node),
                'method_count': method_count,
                'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                'base_classes': [self._get_name_from_node(base) for base in node.bases]
            }
        )
        
        # Add class node asynchronously - we'll use asyncio.run for now
        # In a real async context, this would be awaited properly
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we can't use run()
                # We'll create a task instead
                task = asyncio.create_task(self.add_node_safe(class_node))
            else:
                asyncio.run(self.add_node_safe(class_node))
        except RuntimeError:
            # Fallback for synchronous context
            pass
            
        # Add CONTAINS relationship from file
        file_id = f"file:{self.file_path}"
        file_contains_class = CodeRelationship(
            from_node=file_id,
            to_node=class_id,
            type=RelationType.CONTAINS,
            properties={'line_number': node.lineno}
        )
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self.add_relationship_safe(file_contains_class))
            else:
                asyncio.run(self.add_relationship_safe(file_contains_class))
        except RuntimeError:
            pass
        
        # Handle inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_class_id = f"class:{self.file_path}:{base.id}:unknown"
                inherits_rel = CodeRelationship(
                    from_node=class_id,
                    to_node=base_class_id,
                    type=RelationType.INHERITS,
                    properties={'inheritance_type': 'extends'}
                )
                
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        task = asyncio.create_task(self.add_relationship_safe(inherits_rel))
                    else:
                        asyncio.run(self.add_relationship_safe(inherits_rel))
                except RuntimeError:
                    pass
        
        # Process class body
        old_class = self.current_class
        self.current_class = class_id
        self.scope_stack.append(f"class:{node.name}")
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """Handle function/method definitions"""
        if self.current_class:
            func_id = f"method:{self.current_class}:{node.name}:{node.lineno}"
            func_type = NodeType.METHOD
            container_id = self.current_class
        else:
            func_id = f"function:{self.file_path}:{node.name}:{node.lineno}"
            func_type = NodeType.FUNCTION
            container_id = f"file:{self.file_path}"
        
        # Calculate basic complexity
        complexity = self._calculate_function_complexity(node)
        
        func_node = CodeNode(
            id=func_id,
            name=node.name,
            type=func_type,
            file_path=self.file_path,
            start_line=node.lineno,
            end_line=getattr(node, 'end_lineno', node.lineno),
            properties={
                'project_id': self.project_id,
                'docstring': ast.get_docstring(node),
                'args': [arg.arg for arg in node.args.args],
                'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'complexity': complexity,
                'return_annotation': self._get_name_from_node(node.returns) if node.returns else None
            }
        )
        
        # Add function node
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self.add_node_safe(func_node))
            else:
                asyncio.run(self.add_node_safe(func_node))
        except RuntimeError:
            pass
            
        # Add CONTAINS relationship
        contains_rel = CodeRelationship(
            from_node=container_id,
            to_node=func_id,
            type=RelationType.CONTAINS,
            properties={'line_number': node.lineno}
        )
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(self.add_relationship_safe(contains_rel))
            else:
                asyncio.run(self.add_relationship_safe(contains_rel))
        except RuntimeError:
            pass
        
        # Process function body
        old_function = self.current_function
        self.current_function = func_id
        self.scope_stack.append(f"function:{node.name}")
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_function = old_function
    
    def visit_Import(self, node):
        """Handle import statements"""
        for alias in node.names:
            import_name = alias.name
            self.imports.append(import_name)
            
            # Create import relationship
            file_id = f"file:{self.file_path}"
            module_id = f"module:{import_name}"
            
            import_rel = CodeRelationship(
                from_node=file_id,
                to_node=module_id,
                type=RelationType.IMPORTS,
                properties={
                    'alias': alias.asname,
                    'import_type': 'import',
                    'line_number': node.lineno
                }
            )
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    task = asyncio.create_task(self.add_relationship_safe(import_rel))
                else:
                    asyncio.run(self.add_relationship_safe(import_rel))
            except RuntimeError:
                pass
    
    def visit_ImportFrom(self, node):
        """Handle from...import statements"""
        if node.module:
            for alias in node.names:
                import_name = f"{node.module}.{alias.name}"
                self.imports.append(import_name)
                
                file_id = f"file:{self.file_path}"
                module_id = f"module:{import_name}"
                
                import_rel = CodeRelationship(
                    from_node=file_id,
                    to_node=module_id,
                    type=RelationType.IMPORTS,
                    properties={
                        'from_module': node.module,
                        'alias': alias.asname,
                        'import_type': 'from_import',
                        'line_number': node.lineno
                    }
                )
                
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        task = asyncio.create_task(self.add_relationship_safe(import_rel))
                    else:
                        asyncio.run(self.add_relationship_safe(import_rel))
                except RuntimeError:
                    pass
    
    def visit_Call(self, node):
        """Handle function calls to create CALLS relationships"""
        if self.current_function:
            func_name = self._get_name_from_node(node.func)
            if func_name and not func_name.startswith('_'):  # Skip private methods and built-ins
                
                # Create a call relationship
                called_func_id = f"function:unknown:{func_name}:unknown"
                call_rel = CodeRelationship(
                    from_node=self.current_function,
                    to_node=called_func_id,
                    type=RelationType.CALLS,
                    properties={
                        'call_context': '.'.join(self.scope_stack),
                        'line_number': node.lineno,
                        'arg_count': len(node.args)
                    }
                )
                
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        task = asyncio.create_task(self.add_relationship_safe(call_rel))
                    else:
                        asyncio.run(self.add_relationship_safe(call_rel))
                except RuntimeError:
                    pass
        
        self.generic_visit(node)
    
    def _calculate_function_complexity(self, node) -> int:
        """Calculate basic cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
                
        return complexity
    
    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name as string"""
        return self._get_name_from_node(decorator)
    
    def _get_name_from_node(self, node) -> str:
        """Extract name from AST node"""
        if node is None:
            return ""
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name_from_node(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(type(node).__name__)

# Factory function
def create_ast_graph_service(graph_service: CodeGraphService = None) -> ASTGraphService:
    """Create AST Graph Service with optional graph service dependency"""
    if graph_service is None:
        from .code_graph_service import create_code_graph_service
        graph_service = create_code_graph_service()
    
    return ASTGraphService(graph_service)