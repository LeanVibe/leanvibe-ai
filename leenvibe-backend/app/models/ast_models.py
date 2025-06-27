"""
AST Models for Tree-sitter Integration

Pydantic models for representing Abstract Syntax Trees and code analysis results.
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class LanguageType(str, Enum):
    """Supported programming languages"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SWIFT = "swift"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"


class SymbolType(str, Enum):
    """Types of code symbols"""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    MODULE = "module"
    PROPERTY = "property"
    PARAMETER = "parameter"
    UNKNOWN = "unknown"


class ASTNode(BaseModel):
    """Base AST node representation"""

    node_type: str
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]  # (row, column)
    end_point: tuple[int, int]  # (row, column)
    text: Optional[str] = None
    children: List["ASTNode"] = Field(default_factory=list)
    parent: Optional["ASTNode"] = None


class Symbol(BaseModel):
    """Code symbol representation"""

    id: str = Field(..., description="Unique identifier for the symbol")
    name: str
    symbol_type: SymbolType
    file_path: str
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    visibility: Optional[str] = None  # public, private, protected
    is_async: bool = False
    is_static: bool = False
    parameters: List[str] = Field(default_factory=list)
    return_type: Optional[str] = None
    complexity: Optional[int] = None


class Dependency(BaseModel):
    """Code dependency representation"""

    source_file: str
    target_file: Optional[str] = None
    target_symbol: Optional[str] = None
    dependency_type: str  # import, call, inheritance, etc.
    line_number: int
    is_external: bool = False
    module_name: Optional[str] = None


class ComplexityMetrics(BaseModel):
    """Code complexity metrics"""

    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    lines_of_code: int = 0
    number_of_functions: int = 0
    number_of_classes: int = 0
    depth_of_inheritance: int = 0
    coupling_between_objects: int = 0
    maintainability_index: float = 0.0


class FileAnalysis(BaseModel):
    """Complete analysis of a single file"""

    file_path: str
    language: LanguageType
    ast_root: Optional[ASTNode] = None
    symbols: List[Symbol] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    complexity: ComplexityMetrics = Field(default_factory=ComplexityMetrics)
    last_analyzed: float = Field(default_factory=time.time)
    parsing_errors: List[str] = Field(default_factory=list)


class ProjectIndex(BaseModel):
    """Project-wide code index"""

    workspace_path: str
    files: Dict[str, FileAnalysis] = Field(default_factory=dict)
    symbols: Dict[str, Symbol] = Field(default_factory=dict)
    dependencies: List[Dependency] = Field(default_factory=list)
    last_indexed: float = Field(default_factory=time.time)
    total_files: int = 0
    supported_files: int = 0
    parsing_errors: int = 0


class Reference(BaseModel):
    """Symbol reference in code"""

    symbol_id: str
    file_path: str
    line_number: int
    column_number: int
    reference_type: str  # definition, usage, call, etc.
    context: Optional[str] = None


class CallGraph(BaseModel):
    """Function call graph representation"""

    nodes: Dict[str, Symbol] = Field(default_factory=dict)
    edges: List[tuple[str, str]] = Field(default_factory=list)  # (caller_id, callee_id)
    entry_points: List[str] = Field(default_factory=list)
    cycles: List[List[str]] = Field(default_factory=list)


class DependencyGraph(BaseModel):
    """Module dependency graph"""

    nodes: List[str] = Field(default_factory=list)  # file paths
    edges: List[tuple[str, str]] = Field(default_factory=list)  # (source, target)
    layers: List[List[str]] = Field(default_factory=list)
    cycles: List[List[str]] = Field(default_factory=list)
    coupling_metrics: Dict[str, float] = Field(default_factory=dict)


class ImpactAnalysis(BaseModel):
    """Change impact analysis results"""

    changed_file: str
    directly_affected: List[str] = Field(default_factory=list)
    indirectly_affected: List[str] = Field(default_factory=list)
    affected_symbols: List[str] = Field(default_factory=list)
    risk_level: str = "low"  # low, medium, high, critical
    confidence: float = 0.8
    recommendations: List[str] = Field(default_factory=list)


class CodeSmell(BaseModel):
    """Code smell detection result"""

    smell_type: str
    file_path: str
    line_start: int
    line_end: int
    severity: str  # info, warning, error, critical
    description: str
    suggestion: Optional[str] = None
    confidence: float = 0.8


class RefactoringSuggestion(BaseModel):
    """Refactoring suggestion"""

    suggestion_type: str
    target_file: str
    target_symbol: Optional[str] = None
    description: str
    rationale: str
    estimated_effort: str  # low, medium, high
    risk_level: str = "low"
    confidence: float = 0.8
    automated: bool = False


class ProjectContext(BaseModel):
    """Project context for L3 agent"""

    workspace_path: str
    current_file: Optional[str] = None
    project_index: Optional[ProjectIndex] = None
    recent_changes: List[str] = Field(default_factory=list)
    architecture_summary: Optional[str] = None
    key_components: List[str] = Field(default_factory=list)
    technology_stack: List[str] = Field(default_factory=list)


class ASTContext(BaseModel):
    """AST context for agent responses"""

    current_symbols: List[Symbol] = Field(default_factory=list)
    related_files: List[str] = Field(default_factory=list)
    call_chain: List[str] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    complexity_concerns: List[str] = Field(default_factory=list)


# Enable forward references
ASTNode.model_rebuild()
