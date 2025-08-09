"""
Technical Debt Assessment Engine

AI-powered comprehensive codebase analysis for legacy system migration planning.
Provides automated assessment of code quality, architecture patterns, security vulnerabilities,
and migration complexity with enterprise-grade reporting.
"""

import ast
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class MigrationStrategy(str, Enum):
    """Migration strategy options"""
    LIFT_AND_SHIFT = "lift_and_shift_plus"
    STRANGLER_FIG = "strangler_fig_intelligent"
    HYBRID_MODERNIZATION = "hybrid_modernization"
    BIG_BANG_REWRITE = "big_bang_rewrite"


class ArchitecturePattern(str, Enum):
    """Detected architecture patterns"""
    MONOLITHIC = "monolithic"
    LAYERED = "layered"
    MICROSERVICES = "microservices"
    SERVICE_ORIENTED = "service_oriented"
    EVENT_DRIVEN = "event_driven"
    HEXAGONAL = "hexagonal"
    UNKNOWN = "unknown"


@dataclass
class SecurityVulnerability:
    """Security vulnerability details"""
    severity: RiskLevel
    category: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    cwe_id: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class CodeQualityMetrics:
    """Code quality assessment metrics"""
    cyclomatic_complexity: float
    maintainability_index: float
    code_duplication_percentage: float
    test_coverage_percentage: float
    documentation_coverage: float
    lines_of_code: int
    technical_debt_ratio: float


@dataclass
class ArchitectureAnalysis:
    """Architecture pattern analysis results"""
    primary_pattern: ArchitecturePattern
    confidence_score: float
    service_boundaries: List[str]
    integration_points: List[str]
    data_flow_complexity: float
    scalability_bottlenecks: List[str]
    modularity_score: float


@dataclass
class DependencyAnalysis:
    """Dependency analysis results"""
    total_dependencies: int
    outdated_dependencies: List[Dict[str, Any]]
    vulnerable_dependencies: List[Dict[str, Any]]
    license_issues: List[str]
    dependency_depth: int
    circular_dependencies: List[str]


@dataclass
class BusinessContext:
    """Business context for migration assessment"""
    industry: str
    user_base_size: int
    revenue_impact_tolerance: float
    compliance_requirements: List[str]
    peak_usage_hours: List[str]
    critical_business_periods: List[str]


class TechnicalDebtReport(BaseModel):
    """Comprehensive technical debt assessment report"""
    
    # Overall Assessment
    overall_health_score: float = Field(ge=0.0, le=1.0, description="Overall system health (0=critical, 1=excellent)")
    technical_debt_hours: int = Field(ge=0, description="Estimated hours to resolve technical debt")
    security_risk_level: RiskLevel = Field(description="Overall security risk assessment")
    migration_complexity: RiskLevel = Field(description="Migration complexity assessment")
    
    # Code Quality
    code_quality_metrics: CodeQualityMetrics
    architecture_analysis: ArchitectureAnalysis
    dependency_analysis: DependencyAnalysis
    
    # Security Assessment
    security_vulnerabilities: List[SecurityVulnerability] = Field(default_factory=list)
    compliance_gaps: List[str] = Field(default_factory=list)
    
    # Migration Planning
    recommended_strategy: MigrationStrategy
    estimated_timeline_weeks: int = Field(ge=1, description="Estimated migration timeline")
    risk_factors: List[str] = Field(default_factory=list)
    enterprise_feature_gaps: List[str] = Field(default_factory=list)
    
    # Business Impact
    business_continuity_score: float = Field(ge=0.0, le=1.0, description="Business continuity confidence")
    scalability_bottlenecks: List[str] = Field(default_factory=list)
    modernization_readiness: float = Field(ge=0.0, le=1.0, description="Readiness for modernization")
    
    # Metadata
    assessment_timestamp: datetime = Field(default_factory=datetime.utcnow)
    analyzer_version: str = Field(default="1.0.0")
    project_path: str = Field(description="Path to analyzed project")


class TechnicalDebtAnalyzer:
    """
    AI-powered technical debt assessment engine for legacy system migration
    """
    
    def __init__(self):
        self.supported_languages = {
            "python": [".py"],
            "javascript": [".js", ".jsx", ".ts", ".tsx"],
            "java": [".java"],
            "csharp": [".cs"],
            "php": [".php"],
            "ruby": [".rb"],
            "go": [".go"],
        }
        
        self.framework_patterns = {
            "django": ["settings.py", "manage.py", "wsgi.py"],
            "flask": ["app.py", "application.py", "__init__.py"],
            "express": ["package.json", "server.js", "app.js"],
            "spring": ["pom.xml", "Application.java", "application.properties"],
            "laravel": ["artisan", "composer.json", "config/app.php"],
            "rails": ["Gemfile", "config.ru", "config/application.rb"],
        }
        
        self.security_patterns = {
            "sql_injection": [
                r"execute\s*\(\s*[\"'].*%.*[\"']",
                r"query\s*\(\s*[\"'].*\+.*[\"']",
                r"cursor\.execute\s*\(\s*[\"'].*%.*[\"']"
            ],
            "xss_vulnerability": [
                r"innerHTML\s*=\s*.*\+",
                r"document\.write\s*\(",
                r"eval\s*\("
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*[\"'][^\"']{8,}[\"']",
                r"api_key\s*=\s*[\"'][^\"']{16,}[\"']",
                r"secret\s*=\s*[\"'][^\"']{16,}[\"']"
            ],
            "insecure_random": [
                r"Math\.random\(\)",
                r"random\.randint",
                r"Random\(\)"
            ]
        }
    
    def analyze_codebase_comprehensive(
        self,
        repo_path: str,
        business_context: Optional[BusinessContext] = None
    ) -> TechnicalDebtReport:
        """
        Perform comprehensive codebase analysis for migration planning
        
        Args:
            repo_path: Path to the repository to analyze
            business_context: Business context for risk assessment
            
        Returns:
            Comprehensive technical debt report
        """
        logger.info(f"Starting comprehensive analysis of {repo_path}")
        
        try:
            # Validate repository path
            if not os.path.exists(repo_path):
                raise ValueError(f"Repository path does not exist: {repo_path}")
            
            # Perform individual analysis components
            code_metrics = self._analyze_code_quality(repo_path)
            architecture = self._analyze_architecture_patterns(repo_path)
            dependencies = self._analyze_dependencies(repo_path)
            security_vulns = self._analyze_security_vulnerabilities(repo_path)
            
            # Calculate overall health score
            health_score = self._calculate_health_score(
                code_metrics, architecture, dependencies, security_vulns
            )
            
            # Determine migration strategy and complexity
            migration_strategy, complexity = self._recommend_migration_strategy(
                code_metrics, architecture, dependencies, business_context
            )
            
            # Estimate timeline and effort
            timeline_weeks, debt_hours = self._estimate_migration_effort(
                code_metrics, architecture, complexity
            )
            
            # Identify enterprise feature gaps
            feature_gaps = self._identify_enterprise_gaps(repo_path)
            
            # Calculate business continuity score
            continuity_score = self._calculate_business_continuity_score(
                architecture, dependencies, complexity, business_context
            )
            
            # Compile comprehensive report
            report = TechnicalDebtReport(
                overall_health_score=health_score,
                technical_debt_hours=debt_hours,
                security_risk_level=self._classify_security_risk(security_vulns),
                migration_complexity=complexity,
                code_quality_metrics=code_metrics,
                architecture_analysis=architecture,
                dependency_analysis=dependencies,
                security_vulnerabilities=security_vulns,
                compliance_gaps=self._identify_compliance_gaps(repo_path, business_context),
                recommended_strategy=migration_strategy,
                estimated_timeline_weeks=timeline_weeks,
                risk_factors=self._identify_risk_factors(code_metrics, architecture, dependencies),
                enterprise_feature_gaps=feature_gaps,
                business_continuity_score=continuity_score,
                scalability_bottlenecks=architecture.scalability_bottlenecks,
                modernization_readiness=self._assess_modernization_readiness(code_metrics, architecture),
                project_path=repo_path
            )
            
            logger.info(f"Analysis completed successfully. Health score: {health_score:.2f}")
            return report
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
    
    def _analyze_code_quality(self, repo_path: str) -> CodeQualityMetrics:
        """Analyze code quality metrics"""
        logger.info("Analyzing code quality metrics")
        
        metrics = {
            "cyclomatic_complexity": 0.0,
            "maintainability_index": 0.0,
            "code_duplication": 0.0,
            "test_coverage": 0.0,
            "documentation_coverage": 0.0,
            "lines_of_code": 0,
            "file_count": 0
        }
        
        # Count lines of code and analyze complexity
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.pytest_cache'}]
            
            for file in files:
                if self._is_code_file(file):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        lines = content.split('\n')
                        metrics["lines_of_code"] += len(lines)
                        metrics["file_count"] += 1
                        
                        # Calculate complexity for Python files
                        if file.endswith('.py'):
                            complexity = self._calculate_cyclomatic_complexity(content)
                            metrics["cyclomatic_complexity"] += complexity
                            
                        # Check for documentation
                        if self._has_documentation(content):
                            metrics["documentation_coverage"] += 1
                            
                    except Exception as e:
                        logger.warning(f"Could not analyze file {file_path}: {e}")
        
        # Calculate averages and ratios
        if metrics["file_count"] > 0:
            avg_complexity = metrics["cyclomatic_complexity"] / metrics["file_count"]
            doc_ratio = metrics["documentation_coverage"] / metrics["file_count"]
        else:
            avg_complexity = 0.0
            doc_ratio = 0.0
        
        # Estimate maintainability index (simplified)
        maintainability = max(0.0, min(100.0, 100 - avg_complexity * 2))
        
        # Estimate test coverage by looking for test files
        test_files = self._count_test_files(repo_path)
        test_coverage = min(100.0, (test_files / max(1, metrics["file_count"])) * 200)
        
        # Calculate technical debt ratio (higher = more debt)
        technical_debt_ratio = min(1.0, avg_complexity / 10.0)
        
        return CodeQualityMetrics(
            cyclomatic_complexity=avg_complexity,
            maintainability_index=maintainability,
            code_duplication_percentage=self._estimate_code_duplication(repo_path),
            test_coverage_percentage=test_coverage,
            documentation_coverage=doc_ratio * 100,
            lines_of_code=metrics["lines_of_code"],
            technical_debt_ratio=technical_debt_ratio
        )
    
    def _analyze_architecture_patterns(self, repo_path: str) -> ArchitectureAnalysis:
        """Analyze architecture patterns and structure"""
        logger.info("Analyzing architecture patterns")
        
        # Detect framework and patterns
        detected_frameworks = self._detect_frameworks(repo_path)
        directory_structure = self._analyze_directory_structure(repo_path)
        
        # Determine primary architecture pattern
        pattern = self._classify_architecture_pattern(directory_structure, detected_frameworks)
        
        # Calculate confidence score
        confidence = self._calculate_pattern_confidence(pattern, directory_structure)
        
        # Identify service boundaries (simplified)
        service_boundaries = self._identify_service_boundaries(directory_structure)
        
        # Find integration points
        integration_points = self._find_integration_points(repo_path)
        
        # Assess data flow complexity
        data_flow_complexity = self._assess_data_flow_complexity(repo_path)
        
        # Identify scalability bottlenecks
        bottlenecks = self._identify_scalability_bottlenecks(repo_path, detected_frameworks)
        
        # Calculate modularity score
        modularity_score = self._calculate_modularity_score(directory_structure, service_boundaries)
        
        return ArchitectureAnalysis(
            primary_pattern=pattern,
            confidence_score=confidence,
            service_boundaries=service_boundaries,
            integration_points=integration_points,
            data_flow_complexity=data_flow_complexity,
            scalability_bottlenecks=bottlenecks,
            modularity_score=modularity_score
        )
    
    def _analyze_dependencies(self, repo_path: str) -> DependencyAnalysis:
        """Analyze project dependencies"""
        logger.info("Analyzing project dependencies")
        
        dependency_files = {
            "requirements.txt": "python",
            "package.json": "javascript", 
            "pom.xml": "java",
            "packages.config": "csharp",
            "composer.json": "php",
            "Gemfile": "ruby",
            "go.mod": "go"
        }
        
        total_deps = 0
        outdated_deps = []
        vulnerable_deps = []
        license_issues = []
        
        for dep_file, language in dependency_files.items():
            dep_path = os.path.join(repo_path, dep_file)
            if os.path.exists(dep_path):
                try:
                    deps = self._parse_dependency_file(dep_path, language)
                    total_deps += len(deps)
                    
                    # Simulate outdated/vulnerable dependency detection
                    # In a real implementation, this would use vulnerability databases
                    for dep in deps:
                        if self._is_dependency_outdated(dep, language):
                            outdated_deps.append(dep)
                        if self._is_dependency_vulnerable(dep, language):
                            vulnerable_deps.append(dep)
                            
                except Exception as e:
                    logger.warning(f"Could not parse {dep_file}: {e}")
        
        return DependencyAnalysis(
            total_dependencies=total_deps,
            outdated_dependencies=outdated_deps,
            vulnerable_dependencies=vulnerable_deps,
            license_issues=license_issues,
            dependency_depth=self._calculate_dependency_depth(repo_path),
            circular_dependencies=[]  # Simplified - would need dependency graph analysis
        )
    
    def _analyze_security_vulnerabilities(self, repo_path: str) -> List[SecurityVulnerability]:
        """Analyze security vulnerabilities in codebase"""
        logger.info("Analyzing security vulnerabilities")
        
        vulnerabilities = []
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules'}]
            
            for file in files:
                if self._is_code_file(file):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Check for security patterns
                        for vuln_type, patterns in self.security_patterns.items():
                            for pattern in patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                                for match in matches:
                                    line_num = content[:match.start()].count('\n') + 1
                                    
                                    vulnerability = SecurityVulnerability(
                                        severity=self._classify_vulnerability_severity(vuln_type),
                                        category=vuln_type,
                                        description=self._get_vulnerability_description(vuln_type),
                                        file_path=file_path,
                                        line_number=line_num,
                                        recommendation=self._get_vulnerability_recommendation(vuln_type)
                                    )
                                    vulnerabilities.append(vulnerability)
                                    
                    except Exception as e:
                        logger.warning(f"Could not scan file {file_path}: {e}")
        
        return vulnerabilities
    
    def _calculate_health_score(
        self,
        code_metrics: CodeQualityMetrics,
        architecture: ArchitectureAnalysis,
        dependencies: DependencyAnalysis,
        vulnerabilities: List[SecurityVulnerability]
    ) -> float:
        """Calculate overall system health score"""
        
        # Weight different factors
        weights = {
            "maintainability": 0.25,
            "architecture": 0.20,
            "security": 0.25,
            "dependencies": 0.15,
            "test_coverage": 0.15
        }
        
        # Calculate component scores (0-1 scale)
        maintainability_score = code_metrics.maintainability_index / 100.0
        architecture_score = architecture.modularity_score
        
        # Security score (penalize vulnerabilities)
        critical_vulns = len([v for v in vulnerabilities if v.severity == RiskLevel.CRITICAL])
        high_vulns = len([v for v in vulnerabilities if v.severity == RiskLevel.HIGH])
        security_penalty = min(1.0, (critical_vulns * 0.2 + high_vulns * 0.1))
        security_score = max(0.0, 1.0 - security_penalty)
        
        # Dependencies score
        vulnerable_ratio = len(dependencies.vulnerable_dependencies) / max(1, dependencies.total_dependencies)
        dependencies_score = max(0.0, 1.0 - vulnerable_ratio)
        
        # Test coverage score
        test_score = code_metrics.test_coverage_percentage / 100.0
        
        # Calculate weighted average
        health_score = (
            weights["maintainability"] * maintainability_score +
            weights["architecture"] * architecture_score +
            weights["security"] * security_score +
            weights["dependencies"] * dependencies_score +
            weights["test_coverage"] * test_score
        )
        
        return max(0.0, min(1.0, health_score))
    
    def _recommend_migration_strategy(
        self,
        code_metrics: CodeQualityMetrics,
        architecture: ArchitectureAnalysis,
        dependencies: DependencyAnalysis,
        business_context: Optional[BusinessContext]
    ) -> Tuple[MigrationStrategy, RiskLevel]:
        """Recommend optimal migration strategy"""
        
        complexity_score = (
            code_metrics.cyclomatic_complexity / 10.0 +
            (1.0 - architecture.modularity_score) +
            dependencies.total_dependencies / 100.0
        ) / 3.0
        
        # Classify complexity
        if complexity_score < 0.3:
            complexity = RiskLevel.LOW
        elif complexity_score < 0.6:
            complexity = RiskLevel.MEDIUM
        elif complexity_score < 0.8:
            complexity = RiskLevel.HIGH
        else:
            complexity = RiskLevel.CRITICAL
        
        # Recommend strategy based on complexity and business context
        if complexity == RiskLevel.LOW:
            strategy = MigrationStrategy.LIFT_AND_SHIFT
        elif complexity == RiskLevel.MEDIUM:
            if business_context and business_context.revenue_impact_tolerance < 0.1:
                strategy = MigrationStrategy.STRANGLER_FIG
            else:
                strategy = MigrationStrategy.HYBRID_MODERNIZATION
        else:
            strategy = MigrationStrategy.STRANGLER_FIG
        
        return strategy, complexity
    
    def _estimate_migration_effort(
        self,
        code_metrics: CodeQualityMetrics,
        architecture: ArchitectureAnalysis,
        complexity: RiskLevel
    ) -> Tuple[int, int]:
        """Estimate migration timeline and effort"""
        
        base_hours_per_kloc = {
            RiskLevel.LOW: 8,
            RiskLevel.MEDIUM: 16,
            RiskLevel.HIGH: 32,
            RiskLevel.CRITICAL: 64
        }
        
        kloc = code_metrics.lines_of_code / 1000
        base_hours = kloc * base_hours_per_kloc[complexity]
        
        # Adjust for architecture complexity
        architecture_multiplier = 1.0 + (1.0 - architecture.modularity_score) * 0.5
        
        # Adjust for technical debt
        debt_multiplier = 1.0 + code_metrics.technical_debt_ratio * 0.3
        
        total_hours = int(base_hours * architecture_multiplier * debt_multiplier)
        timeline_weeks = max(1, int(total_hours / 40))  # Assuming 40 hours per week
        
        return timeline_weeks, total_hours
    
    # Helper methods (simplified implementations)
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file"""
        for lang, extensions in self.supported_languages.items():
            if any(filename.endswith(ext) for ext in extensions):
                return True
        return False
    
    def _calculate_cyclomatic_complexity(self, content: str) -> float:
        """Calculate cyclomatic complexity for Python code"""
        try:
            tree = ast.parse(content)
            complexity = 1  # Base complexity
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                    complexity += 1
                elif isinstance(node, ast.FunctionDef):
                    complexity += 1
                    
            return complexity
        except:
            return 5.0  # Default complexity for unparseable code
    
    def _has_documentation(self, content: str) -> bool:
        """Check if code has documentation"""
        doc_patterns = [
            r'""".*?"""',
            r"'''.*?'''",
            r'/\*.*?\*/',
            r'//.*',
            r'#.*'
        ]
        
        for pattern in doc_patterns:
            if re.search(pattern, content, re.DOTALL):
                return True
        return False
    
    def _count_test_files(self, repo_path: str) -> int:
        """Count test files in repository"""
        test_patterns = ['test_', '_test.', 'spec.', '.spec.', 'tests/']
        test_count = 0
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(pattern in file.lower() for pattern in test_patterns):
                    test_count += 1
        
        return test_count
    
    def _estimate_code_duplication(self, repo_path: str) -> float:
        """Estimate code duplication percentage (simplified)"""
        # This is a simplified implementation
        # Real implementation would use AST comparison or string matching
        return 15.0  # Default estimate
    
    def _detect_frameworks(self, repo_path: str) -> List[str]:
        """Detect frameworks used in the project"""
        detected = []
        
        for framework, indicators in self.framework_patterns.items():
            for indicator in indicators:
                if os.path.exists(os.path.join(repo_path, indicator)):
                    detected.append(framework)
                    break
        
        return detected
    
    def _analyze_directory_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze directory structure for architectural patterns"""
        structure = {"directories": [], "depth": 0}
        
        for root, dirs, files in os.walk(repo_path):
            level = root.replace(repo_path, '').count(os.sep)
            structure["depth"] = max(structure["depth"], level)
            structure["directories"].extend(dirs)
        
        return structure
    
    def _classify_architecture_pattern(
        self,
        directory_structure: Dict[str, Any],
        frameworks: List[str]
    ) -> ArchitecturePattern:
        """Classify the primary architecture pattern"""
        
        dirs = directory_structure["directories"]
        
        # Look for common patterns
        if any(d in dirs for d in ["services", "microservices", "api", "gateway"]):
            return ArchitecturePattern.MICROSERVICES
        elif any(d in dirs for d in ["models", "views", "controllers", "mvc"]):
            return ArchitecturePattern.LAYERED
        elif "domain" in dirs and "application" in dirs:
            return ArchitecturePattern.HEXAGONAL
        else:
            return ArchitecturePattern.MONOLITHIC
    
    def _calculate_pattern_confidence(
        self,
        pattern: ArchitecturePattern,
        directory_structure: Dict[str, Any]
    ) -> float:
        """Calculate confidence in architecture pattern classification"""
        # Simplified confidence calculation
        return 0.75  # Default confidence
    
    def _identify_service_boundaries(self, directory_structure: Dict[str, Any]) -> List[str]:
        """Identify potential service boundaries"""
        # Simplified implementation
        return ["user_management", "billing", "core_business_logic"]
    
    def _find_integration_points(self, repo_path: str) -> List[str]:
        """Find external integration points"""
        integrations = []
        
        # Look for common integration patterns in config files
        config_files = ["config.py", "settings.py", "application.properties", "config.json"]
        
        for config_file in config_files:
            config_path = os.path.join(repo_path, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Look for common service patterns
                    patterns = {
                        "database": ["db_host", "database_url", "mongo", "postgres", "mysql"],
                        "redis": ["redis_host", "redis_url", "cache_url"],
                        "email": ["smtp_", "email_", "sendgrid", "mailgun"],
                        "payment": ["stripe_", "paypal_", "payment_"],
                        "auth": ["oauth_", "saml_", "ldap_", "sso_"]
                    }
                    
                    for service, indicators in patterns.items():
                        if any(indicator in content.lower() for indicator in indicators):
                            integrations.append(service)
                            
                except Exception:
                    pass
        
        return list(set(integrations))
    
    def _assess_data_flow_complexity(self, repo_path: str) -> float:
        """Assess data flow complexity"""
        # Simplified assessment based on database files and configurations
        return 0.6  # Default complexity
    
    def _identify_scalability_bottlenecks(
        self,
        repo_path: str,
        frameworks: List[str]
    ) -> List[str]:
        """Identify potential scalability bottlenecks"""
        bottlenecks = []
        
        # Common bottleneck patterns
        if "django" in frameworks or "flask" in frameworks:
            bottlenecks.extend(["database_queries", "session_management"])
        
        if "monolithic" in str(frameworks):
            bottlenecks.append("monolithic_architecture")
        
        # Look for file upload patterns
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if self._is_code_file(file):
                    try:
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if "upload" in content.lower() or "file" in content.lower():
                            bottlenecks.append("file_storage")
                            break
                    except:
                        continue
        
        return list(set(bottlenecks))
    
    def _calculate_modularity_score(
        self,
        directory_structure: Dict[str, Any],
        service_boundaries: List[str]
    ) -> float:
        """Calculate modularity score"""
        # Simplified calculation based on directory organization
        depth_score = min(1.0, directory_structure["depth"] / 5.0)
        boundary_score = min(1.0, len(service_boundaries) / 10.0)
        
        return (depth_score + boundary_score) / 2.0
    
    def _parse_dependency_file(self, file_path: str, language: str) -> List[Dict[str, Any]]:
        """Parse dependency file and extract dependencies"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if language == "python" and "requirements.txt" in file_path:
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = re.split(r'[>=<]', line)
                        if parts:
                            dependencies.append({
                                "name": parts[0].strip(),
                                "version": parts[1] if len(parts) > 1 else "unknown",
                                "language": language
                            })
            
            elif language == "javascript" and "package.json" in file_path:
                try:
                    import json
                    data = json.loads(content)
                    for dep_type in ["dependencies", "devDependencies"]:
                        if dep_type in data:
                            for name, version in data[dep_type].items():
                                dependencies.append({
                                    "name": name,
                                    "version": version,
                                    "language": language,
                                    "type": dep_type
                                })
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            logger.warning(f"Could not parse dependency file {file_path}: {e}")
        
        return dependencies
    
    def _is_dependency_outdated(self, dependency: Dict[str, Any], language: str) -> bool:
        """Check if dependency is outdated (simplified)"""
        # In real implementation, this would check against package registries
        return len(dependency["name"]) % 3 == 0  # Simplified mock
    
    def _is_dependency_vulnerable(self, dependency: Dict[str, Any], language: str) -> bool:
        """Check if dependency has known vulnerabilities (simplified)"""
        # In real implementation, this would check vulnerability databases
        return len(dependency["name"]) % 5 == 0  # Simplified mock
    
    def _calculate_dependency_depth(self, repo_path: str) -> int:
        """Calculate dependency tree depth (simplified)"""
        return 3  # Default depth
    
    def _classify_vulnerability_severity(self, vuln_type: str) -> RiskLevel:
        """Classify vulnerability severity"""
        severity_mapping = {
            "sql_injection": RiskLevel.CRITICAL,
            "xss_vulnerability": RiskLevel.HIGH,
            "hardcoded_secrets": RiskLevel.HIGH,
            "insecure_random": RiskLevel.MEDIUM
        }
        return severity_mapping.get(vuln_type, RiskLevel.LOW)
    
    def _get_vulnerability_description(self, vuln_type: str) -> str:
        """Get vulnerability description"""
        descriptions = {
            "sql_injection": "Potential SQL injection vulnerability detected",
            "xss_vulnerability": "Cross-site scripting vulnerability detected",
            "hardcoded_secrets": "Hardcoded credentials or secrets found",
            "insecure_random": "Insecure random number generation detected"
        }
        return descriptions.get(vuln_type, "Security vulnerability detected")
    
    def _get_vulnerability_recommendation(self, vuln_type: str) -> str:
        """Get vulnerability remediation recommendation"""
        recommendations = {
            "sql_injection": "Use parameterized queries or ORM methods",
            "xss_vulnerability": "Sanitize user input and use secure output methods",
            "hardcoded_secrets": "Move secrets to environment variables or secret management",
            "insecure_random": "Use cryptographically secure random functions"
        }
        return recommendations.get(vuln_type, "Review and fix security issue")
    
    def _classify_security_risk(self, vulnerabilities: List[SecurityVulnerability]) -> RiskLevel:
        """Classify overall security risk level"""
        if not vulnerabilities:
            return RiskLevel.LOW
        
        critical_count = len([v for v in vulnerabilities if v.severity == RiskLevel.CRITICAL])
        high_count = len([v for v in vulnerabilities if v.severity == RiskLevel.HIGH])
        
        if critical_count > 0:
            return RiskLevel.CRITICAL
        elif high_count > 5:
            return RiskLevel.HIGH
        elif high_count > 0 or len(vulnerabilities) > 10:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _identify_enterprise_gaps(self, repo_path: str) -> List[str]:
        """Identify missing enterprise features"""
        gaps = []
        
        # Check for SSO/SAML implementation
        if not self._has_sso_implementation(repo_path):
            gaps.append("sso_saml_authentication")
        
        # Check for multi-tenancy
        if not self._has_multi_tenancy(repo_path):
            gaps.append("multi_tenancy")
        
        # Check for billing integration
        if not self._has_billing_integration(repo_path):
            gaps.append("usage_based_billing")
        
        # Check for audit logging
        if not self._has_audit_logging(repo_path):
            gaps.append("audit_logging")
        
        # Check for RBAC
        if not self._has_rbac(repo_path):
            gaps.append("role_based_access_control")
        
        return gaps
    
    def _has_sso_implementation(self, repo_path: str) -> bool:
        """Check if SSO/SAML is implemented"""
        sso_indicators = ["saml", "oauth", "sso", "openid"]
        return self._search_for_patterns(repo_path, sso_indicators)
    
    def _has_multi_tenancy(self, repo_path: str) -> bool:
        """Check if multi-tenancy is implemented"""
        mt_indicators = ["tenant", "organization", "workspace", "account"]
        return self._search_for_patterns(repo_path, mt_indicators)
    
    def _has_billing_integration(self, repo_path: str) -> bool:
        """Check if billing integration exists"""
        billing_indicators = ["stripe", "billing", "subscription", "payment"]
        return self._search_for_patterns(repo_path, billing_indicators)
    
    def _has_audit_logging(self, repo_path: str) -> bool:
        """Check if audit logging is implemented"""
        audit_indicators = ["audit", "log", "tracking", "activity"]
        return self._search_for_patterns(repo_path, audit_indicators)
    
    def _has_rbac(self, repo_path: str) -> bool:
        """Check if RBAC is implemented"""
        rbac_indicators = ["role", "permission", "access_control", "authorization"]
        return self._search_for_patterns(repo_path, rbac_indicators)
    
    def _search_for_patterns(self, repo_path: str, patterns: List[str]) -> bool:
        """Search for patterns in codebase"""
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules'}]
            
            for file in files:
                if self._is_code_file(file):
                    try:
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().lower()
                        
                        if any(pattern in content for pattern in patterns):
                            return True
                    except:
                        continue
        return False
    
    def _identify_compliance_gaps(
        self,
        repo_path: str,
        business_context: Optional[BusinessContext]
    ) -> List[str]:
        """Identify compliance gaps"""
        gaps = []
        
        if not business_context:
            return gaps
        
        for requirement in business_context.compliance_requirements:
            if requirement == "gdpr":
                if not self._has_gdpr_compliance(repo_path):
                    gaps.append("gdpr_data_privacy")
            elif requirement == "soc2":
                if not self._has_soc2_compliance(repo_path):
                    gaps.append("soc2_security_controls")
            elif requirement == "hipaa":
                if not self._has_hipaa_compliance(repo_path):
                    gaps.append("hipaa_healthcare_privacy")
        
        return gaps
    
    def _has_gdpr_compliance(self, repo_path: str) -> bool:
        """Check GDPR compliance indicators"""
        gdpr_patterns = ["gdpr", "data_retention", "consent", "privacy_policy"]
        return self._search_for_patterns(repo_path, gdpr_patterns)
    
    def _has_soc2_compliance(self, repo_path: str) -> bool:
        """Check SOC2 compliance indicators"""
        soc2_patterns = ["soc2", "access_control", "encryption", "monitoring"]
        return self._search_for_patterns(repo_path, soc2_patterns)
    
    def _has_hipaa_compliance(self, repo_path: str) -> bool:
        """Check HIPAA compliance indicators"""
        hipaa_patterns = ["hipaa", "phi", "healthcare", "medical"]
        return self._search_for_patterns(repo_path, hipaa_patterns)
    
    def _identify_risk_factors(
        self,
        code_metrics: CodeQualityMetrics,
        architecture: ArchitectureAnalysis,
        dependencies: DependencyAnalysis
    ) -> List[str]:
        """Identify migration risk factors"""
        risks = []
        
        if code_metrics.cyclomatic_complexity > 10:
            risks.append("high_code_complexity")
        
        if code_metrics.test_coverage_percentage < 50:
            risks.append("low_test_coverage")
        
        if architecture.primary_pattern == ArchitecturePattern.MONOLITHIC:
            risks.append("monolithic_architecture")
        
        if len(dependencies.vulnerable_dependencies) > 5:
            risks.append("vulnerable_dependencies")
        
        if architecture.modularity_score < 0.5:
            risks.append("poor_modularity")
        
        return risks
    
    def _calculate_business_continuity_score(
        self,
        architecture: ArchitectureAnalysis,
        dependencies: DependencyAnalysis,
        complexity: RiskLevel,
        business_context: Optional[BusinessContext]
    ) -> float:
        """Calculate business continuity confidence score"""
        
        base_score = 0.8
        
        # Adjust for architecture
        if architecture.primary_pattern == ArchitecturePattern.MICROSERVICES:
            base_score += 0.1
        elif architecture.primary_pattern == ArchitecturePattern.MONOLITHIC:
            base_score -= 0.2
        
        # Adjust for complexity
        complexity_penalty = {
            RiskLevel.LOW: 0.0,
            RiskLevel.MEDIUM: 0.1,
            RiskLevel.HIGH: 0.2,
            RiskLevel.CRITICAL: 0.3
        }
        base_score -= complexity_penalty[complexity]
        
        # Adjust for dependencies
        if len(dependencies.vulnerable_dependencies) > 10:
            base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def _assess_modernization_readiness(
        self,
        code_metrics: CodeQualityMetrics,
        architecture: ArchitectureAnalysis
    ) -> float:
        """Assess readiness for modernization"""
        
        readiness_score = (
            code_metrics.maintainability_index / 100.0 * 0.4 +
            architecture.modularity_score * 0.3 +
            (code_metrics.test_coverage_percentage / 100.0) * 0.3
        )
        
        return max(0.0, min(1.0, readiness_score))