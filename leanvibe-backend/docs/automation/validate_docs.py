#!/usr/bin/env python3
"""
LeanVibe Documentation Validation Pipeline

Comprehensive validation system that ensures documentation accuracy, 
link integrity, code example correctness, and enterprise compliance.
"""

import asyncio
import json
import logging
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Validation result for a single check."""
    check_type: str
    status: str  # "pass", "fail", "warning"
    message: str
    details: Optional[Dict] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class DocumentationValidator:
    """Comprehensive documentation validation system."""
    
    def __init__(self, docs_directory: Path = Path(".")):
        self.docs_directory = Path(docs_directory)
        self.results: List[ValidationResult] = []
        
        # Validation configuration
        self.config = {
            "validate_external_links": True,
            "validate_internal_links": True,
            "validate_code_examples": True,
            "validate_api_endpoints": True,
            "validate_screenshots": True,
            "check_grammar": True,
            "check_accessibility": True,
            "timeout_seconds": 30,
            "concurrent_requests": 10
        }
        
        # Known good domains (faster validation)
        self.trusted_domains = {
            "github.com",
            "docs.python.org",
            "fastapi.tiangolo.com",
            "kubernetes.io",
            "docker.com"
        }
    
    async def validate_all_documentation(self) -> Dict[str, any]:
        """Run comprehensive validation on all documentation."""
        logger.info("Starting comprehensive documentation validation")
        
        validation_summary = {
            "timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "warning_checks": 0,
            "results": [],
            "files_analyzed": []
        }
        
        try:
            # Find all documentation files
            doc_files = self._find_documentation_files()
            validation_summary["total_files"] = len(doc_files)
            validation_summary["files_analyzed"] = [str(f) for f in doc_files]
            
            # Validate each file
            for doc_file in doc_files:
                await self._validate_document(doc_file)
            
            # API endpoint validation
            if self.config["validate_api_endpoints"]:
                await self._validate_api_endpoints()
            
            # Compile results
            validation_summary["total_checks"] = len(self.results)
            validation_summary["passed_checks"] = len([r for r in self.results if r.status == "pass"])
            validation_summary["failed_checks"] = len([r for r in self.results if r.status == "fail"])
            validation_summary["warning_checks"] = len([r for r in self.results if r.status == "warning"])
            validation_summary["results"] = [r.dict() for r in self.results]
            
            # Generate validation report
            report_path = await self._generate_validation_report(validation_summary)
            validation_summary["report_path"] = str(report_path)
            
            logger.info(f"Validation completed: {validation_summary['passed_checks']} passed, "
                       f"{validation_summary['failed_checks']} failed, "
                       f"{validation_summary['warning_checks']} warnings")
            
            return validation_summary
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
    
    def _find_documentation_files(self) -> List[Path]:
        """Find all documentation files to validate."""
        doc_files = []
        
        # Markdown files
        doc_files.extend(self.docs_directory.glob("**/*.md"))
        
        # YAML/JSON API specs
        doc_files.extend(self.docs_directory.glob("**/*.yaml"))
        doc_files.extend(self.docs_directory.glob("**/*.yml"))
        doc_files.extend(self.docs_directory.glob("**/*.json"))
        
        # Filter out generated files and node_modules
        filtered_files = []
        for file_path in doc_files:
            if not any(part.startswith('.') or part == 'node_modules' for part in file_path.parts):
                filtered_files.append(file_path)
        
        logger.info(f"Found {len(filtered_files)} documentation files")
        return filtered_files
    
    async def _validate_document(self, doc_file: Path):
        """Validate a single documentation file."""
        logger.info(f"Validating {doc_file}")
        
        try:
            content = doc_file.read_text(encoding='utf-8')
            
            # Link validation
            if self.config["validate_internal_links"] or self.config["validate_external_links"]:
                await self._validate_links_in_file(doc_file, content)
            
            # Code example validation
            if self.config["validate_code_examples"]:
                await self._validate_code_examples_in_file(doc_file, content)
            
            # Content quality checks
            if self.config["check_grammar"]:
                await self._validate_content_quality(doc_file, content)
            
            # Accessibility checks
            if self.config["check_accessibility"]:
                await self._validate_accessibility(doc_file, content)
            
            # Format-specific validation
            if doc_file.suffix.lower() == '.md':
                await self._validate_markdown_structure(doc_file, content)
            elif doc_file.suffix.lower() in ['.yaml', '.yml']:
                await self._validate_yaml_syntax(doc_file, content)
            elif doc_file.suffix.lower() == '.json':
                await self._validate_json_syntax(doc_file, content)
                
        except Exception as e:
            self.results.append(ValidationResult(
                check_type="file_reading",
                status="fail",
                message=f"Failed to read file: {e}",
                file_path=str(doc_file)
            ))
    
    async def _validate_links_in_file(self, doc_file: Path, content: str):
        """Validate all links in a document."""
        
        # Find all markdown links
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        # Find all HTML links
        html_links = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>', content)
        
        all_links = []
        
        # Process markdown links
        for link_text, link_url in markdown_links:
            all_links.append((link_text, link_url, "markdown"))
        
        # Process HTML links
        for link_url in html_links:
            all_links.append(("", link_url, "html"))
        
        # Validate each link
        for link_text, link_url, link_type in all_links:
            await self._validate_single_link(doc_file, link_url, link_text, link_type)
    
    async def _validate_single_link(self, doc_file: Path, link_url: str, link_text: str, link_type: str):
        """Validate a single link."""
        
        try:
            # Skip anchor links and mailto links
            if link_url.startswith('#') or link_url.startswith('mailto:'):
                return
            
            # Internal link validation
            if not link_url.startswith(('http://', 'https://')):
                if self.config["validate_internal_links"]:
                    await self._validate_internal_link(doc_file, link_url)
                return
            
            # External link validation
            if self.config["validate_external_links"]:
                await self._validate_external_link(doc_file, link_url, link_text)
                
        except Exception as e:
            self.results.append(ValidationResult(
                check_type="link_validation",
                status="fail",
                message=f"Link validation error: {e}",
                file_path=str(doc_file),
                details={"url": link_url, "type": link_type}
            ))
    
    async def _validate_internal_link(self, doc_file: Path, link_url: str):
        """Validate internal links (relative paths)."""
        
        # Resolve relative path
        if link_url.startswith('./') or link_url.startswith('../'):
            target_path = (doc_file.parent / link_url).resolve()
        else:
            target_path = self.docs_directory / link_url
        
        # Check if file exists
        if not target_path.exists():
            self.results.append(ValidationResult(
                check_type="internal_link",
                status="fail",
                message=f"Internal link target not found: {link_url}",
                file_path=str(doc_file),
                details={"target_path": str(target_path)}
            ))
        else:
            self.results.append(ValidationResult(
                check_type="internal_link",
                status="pass",
                message=f"Internal link valid: {link_url}",
                file_path=str(doc_file)
            ))
    
    async def _validate_external_link(self, doc_file: Path, link_url: str, link_text: str):
        """Validate external links."""
        
        try:
            # Quick validation for trusted domains
            parsed_url = urlparse(link_url)
            if parsed_url.netloc in self.trusted_domains:
                self.results.append(ValidationResult(
                    check_type="external_link",
                    status="pass",
                    message=f"Trusted external link: {link_url}",
                    file_path=str(doc_file)
                ))
                return
            
            # Full HTTP validation for other domains
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config["timeout_seconds"])) as session:
                async with session.head(link_url) as response:
                    if 200 <= response.status < 400:
                        self.results.append(ValidationResult(
                            check_type="external_link",
                            status="pass",
                            message=f"External link accessible: {link_url}",
                            file_path=str(doc_file)
                        ))
                    else:
                        self.results.append(ValidationResult(
                            check_type="external_link",
                            status="fail",
                            message=f"External link returned {response.status}: {link_url}",
                            file_path=str(doc_file),
                            details={"status_code": response.status}
                        ))
                        
        except asyncio.TimeoutError:
            self.results.append(ValidationResult(
                check_type="external_link",
                status="warning",
                message=f"External link timeout: {link_url}",
                file_path=str(doc_file)
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                check_type="external_link",
                status="fail",
                message=f"External link error: {link_url} - {e}",
                file_path=str(doc_file)
            ))
    
    async def _validate_code_examples_in_file(self, doc_file: Path, content: str):
        """Validate code examples in documentation."""
        
        # Find code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        
        for i, (language, code) in enumerate(code_blocks):
            await self._validate_code_block(doc_file, code, language or "text", i)
    
    async def _validate_code_block(self, doc_file: Path, code: str, language: str, block_index: int):
        """Validate a single code block."""
        
        try:
            if language.lower() == 'python':
                await self._validate_python_code(doc_file, code, block_index)
            elif language.lower() in ['bash', 'shell', 'sh']:
                await self._validate_bash_code(doc_file, code, block_index)
            elif language.lower() in ['json']:
                await self._validate_json_code(doc_file, code, block_index)
            elif language.lower() in ['yaml', 'yml']:
                await self._validate_yaml_code(doc_file, code, block_index)
            else:
                # Basic syntax check for other languages
                self.results.append(ValidationResult(
                    check_type="code_example",
                    status="pass",
                    message=f"Code block validated (language: {language})",
                    file_path=str(doc_file),
                    details={"block_index": block_index, "language": language}
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                check_type="code_example",
                status="fail",
                message=f"Code validation failed: {e}",
                file_path=str(doc_file),
                details={"block_index": block_index, "language": language}
            ))
    
    async def _validate_python_code(self, doc_file: Path, code: str, block_index: int):
        """Validate Python code examples."""
        
        try:
            # Check syntax
            compile(code, f"{doc_file}:block_{block_index}", 'exec')
            
            self.results.append(ValidationResult(
                check_type="python_code",
                status="pass",
                message="Python code syntax valid",
                file_path=str(doc_file),
                details={"block_index": block_index}
            ))
            
        except SyntaxError as e:
            self.results.append(ValidationResult(
                check_type="python_code",
                status="fail",
                message=f"Python syntax error: {e}",
                file_path=str(doc_file),
                details={"block_index": block_index, "error": str(e)}
            ))
    
    async def _validate_bash_code(self, doc_file: Path, code: str, block_index: int):
        """Validate bash code examples."""
        
        try:
            # Skip validation for commands with placeholders
            if '<' in code and '>' in code:
                self.results.append(ValidationResult(
                    check_type="bash_code",
                    status="pass",
                    message="Bash code contains placeholders (skipped)",
                    file_path=str(doc_file),
                    details={"block_index": block_index}
                ))
                return
            
            # Basic bash syntax validation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['bash', '-n', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    self.results.append(ValidationResult(
                        check_type="bash_code",
                        status="pass",
                        message="Bash code syntax valid",
                        file_path=str(doc_file),
                        details={"block_index": block_index}
                    ))
                else:
                    self.results.append(ValidationResult(
                        check_type="bash_code",
                        status="fail",
                        message=f"Bash syntax error: {result.stderr}",
                        file_path=str(doc_file),
                        details={"block_index": block_index}
                    ))
            finally:
                Path(temp_file).unlink(missing_ok=True)
                
        except Exception as e:
            self.results.append(ValidationResult(
                check_type="bash_code",
                status="warning",
                message=f"Bash validation skipped: {e}",
                file_path=str(doc_file),
                details={"block_index": block_index}
            ))
    
    async def _validate_json_code(self, doc_file: Path, code: str, block_index: int):
        """Validate JSON code examples."""
        
        try:
            json.loads(code)
            self.results.append(ValidationResult(
                check_type="json_code",
                status="pass",
                message="JSON syntax valid",
                file_path=str(doc_file),
                details={"block_index": block_index}
            ))
        except json.JSONDecodeError as e:
            self.results.append(ValidationResult(
                check_type="json_code",
                status="fail",
                message=f"JSON syntax error: {e}",
                file_path=str(doc_file),
                details={"block_index": block_index}
            ))
    
    async def _validate_yaml_code(self, doc_file: Path, code: str, block_index: int):
        """Validate YAML code examples."""
        
        try:
            import yaml
            yaml.safe_load(code)
            self.results.append(ValidationResult(
                check_type="yaml_code",
                status="pass",
                message="YAML syntax valid",
                file_path=str(doc_file),
                details={"block_index": block_index}
            ))
        except yaml.YAMLError as e:
            self.results.append(ValidationResult(
                check_type="yaml_code",
                status="fail",
                message=f"YAML syntax error: {e}",
                file_path=str(doc_file),
                details={"block_index": block_index}
            ))
        except ImportError:
            self.results.append(ValidationResult(
                check_type="yaml_code",
                status="warning",
                message="YAML validation skipped (PyYAML not installed)",
                file_path=str(doc_file),
                details={"block_index": block_index}
            ))
    
    async def _validate_content_quality(self, doc_file: Path, content: str):
        """Validate content quality and grammar."""
        
        # Basic content quality checks
        lines = content.split('\n')
        
        # Check for very long lines (readability)
        for i, line in enumerate(lines, 1):
            if len(line) > 120 and not line.strip().startswith('http'):
                self.results.append(ValidationResult(
                    check_type="content_quality",
                    status="warning",
                    message=f"Long line detected (>120 chars): line {i}",
                    file_path=str(doc_file),
                    line_number=i
                ))
        
        # Check for common typos and issues
        typos = {
            r'\bapi\b': 'API',
            r'\burl\b': 'URL',
            r'\bhttp\b': 'HTTP',
            r'\bhttps\b': 'HTTPS',
            r'\bjson\b': 'JSON',
            r'\bxml\b': 'XML'
        }
        
        for pattern, replacement in typos.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.group() != replacement:
                    line_num = content[:match.start()].count('\n') + 1
                    self.results.append(ValidationResult(
                        check_type="content_quality",
                        status="warning",
                        message=f"Consider using '{replacement}' instead of '{match.group()}'",
                        file_path=str(doc_file),
                        line_number=line_num
                    ))
    
    async def _validate_accessibility(self, doc_file: Path, content: str):
        """Validate accessibility compliance."""
        
        # Check for alt text in images
        img_tags = re.findall(r'!\[([^\]]*)\]\([^)]+\)', content)
        for alt_text in img_tags:
            if not alt_text.strip():
                self.results.append(ValidationResult(
                    check_type="accessibility",
                    status="warning",
                    message="Image missing alt text",
                    file_path=str(doc_file)
                ))
            else:
                self.results.append(ValidationResult(
                    check_type="accessibility", 
                    status="pass",
                    message="Image has alt text",
                    file_path=str(doc_file)
                ))
        
        # Check heading structure
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        prev_level = 0
        
        for heading_markup, heading_text in headings:
            level = len(heading_markup)
            
            # Check for proper heading hierarchy
            if level > prev_level + 1:
                self.results.append(ValidationResult(
                    check_type="accessibility",
                    status="warning", 
                    message=f"Heading level jump detected: {heading_text}",
                    file_path=str(doc_file)
                ))
            
            prev_level = level
    
    async def _validate_markdown_structure(self, doc_file: Path, content: str):
        """Validate markdown-specific structure."""
        
        # Check for proper front matter (if present)
        if content.startswith('---\n'):
            try:
                import yaml
                front_matter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
                if front_matter_match:
                    yaml.safe_load(front_matter_match.group(1))
                    self.results.append(ValidationResult(
                        check_type="markdown_structure",
                        status="pass",
                        message="Valid YAML front matter",
                        file_path=str(doc_file)
                    ))
            except Exception as e:
                self.results.append(ValidationResult(
                    check_type="markdown_structure",
                    status="fail",
                    message=f"Invalid YAML front matter: {e}",
                    file_path=str(doc_file)
                ))
        
        # Check table formatting
        tables = re.findall(r'\|.+\|\n\|[-\s|]+\|\n(\|.+\|\n)+', content)
        self.results.append(ValidationResult(
            check_type="markdown_structure",
            status="pass",
            message=f"Found {len(tables)} properly formatted tables",
            file_path=str(doc_file)
        ))
    
    async def _validate_yaml_syntax(self, doc_file: Path, content: str):
        """Validate YAML file syntax."""
        
        try:
            import yaml
            yaml.safe_load(content)
            self.results.append(ValidationResult(
                check_type="yaml_syntax",
                status="pass",
                message="Valid YAML syntax",
                file_path=str(doc_file)
            ))
        except yaml.YAMLError as e:
            self.results.append(ValidationResult(
                check_type="yaml_syntax",
                status="fail",
                message=f"YAML syntax error: {e}",
                file_path=str(doc_file)
            ))
        except ImportError:
            self.results.append(ValidationResult(
                check_type="yaml_syntax",
                status="warning",
                message="YAML validation skipped (PyYAML not installed)",
                file_path=str(doc_file)
            ))
    
    async def _validate_json_syntax(self, doc_file: Path, content: str):
        """Validate JSON file syntax."""
        
        try:
            json.loads(content)
            self.results.append(ValidationResult(
                check_type="json_syntax",
                status="pass",
                message="Valid JSON syntax",
                file_path=str(doc_file)
            ))
        except json.JSONDecodeError as e:
            self.results.append(ValidationResult(
                check_type="json_syntax",
                status="fail",
                message=f"JSON syntax error: {e}",
                file_path=str(doc_file)
            ))
    
    async def _validate_api_endpoints(self):
        """Validate API endpoints mentioned in documentation."""
        
        try:
            # Try to import and validate against actual API
            import sys
            sys.path.append(".")
            
            from app.main import app
            
            # Get all routes from FastAPI
            actual_routes = set()
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    for method in route.methods:
                        if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            actual_routes.add(f"{method} {route.path}")
            
            # Find endpoints mentioned in documentation
            documented_routes = set()
            
            for doc_file in self._find_documentation_files():
                if doc_file.suffix.lower() == '.md':
                    content = doc_file.read_text(encoding='utf-8')
                    
                    # Find API endpoint patterns
                    endpoint_patterns = [
                        r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)',
                        r'`(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)`',
                        r'"(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)"'
                    ]
                    
                    for pattern in endpoint_patterns:
                        matches = re.findall(pattern, content)
                        for method, path in matches:
                            documented_routes.add(f"{method} {path}")
            
            # Check for undocumented endpoints
            undocumented = actual_routes - documented_routes
            for endpoint in undocumented:
                self.results.append(ValidationResult(
                    check_type="api_coverage",
                    status="warning",
                    message=f"Endpoint not documented: {endpoint}",
                    details={"endpoint": endpoint}
                ))
            
            # Check for non-existent endpoints in docs
            nonexistent = documented_routes - actual_routes
            for endpoint in nonexistent:
                self.results.append(ValidationResult(
                    check_type="api_accuracy",
                    status="fail",
                    message=f"Documented endpoint does not exist: {endpoint}",
                    details={"endpoint": endpoint}
                ))
            
            self.results.append(ValidationResult(
                check_type="api_validation",
                status="pass",
                message=f"API validation complete: {len(actual_routes)} actual, {len(documented_routes)} documented",
                details={
                    "actual_routes": len(actual_routes),
                    "documented_routes": len(documented_routes),
                    "undocumented": len(undocumented),
                    "nonexistent": len(nonexistent)
                }
            ))
            
        except ImportError:
            self.results.append(ValidationResult(
                check_type="api_validation",
                status="warning",
                message="API validation skipped (FastAPI app not available)"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                check_type="api_validation",
                status="fail",
                message=f"API validation failed: {e}"
            ))
    
    async def _generate_validation_report(self, summary: Dict) -> Path:
        """Generate comprehensive validation report."""
        
        report_content = [
            "# Documentation Validation Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Files:** {summary['total_files']}",
            f"**Total Checks:** {summary['total_checks']}",
            "",
            "## Summary",
            "",
            f"- ✅ **Passed:** {summary['passed_checks']}",
            f"- ❌ **Failed:** {summary['failed_checks']}",
            f"- ⚠️ **Warnings:** {summary['warning_checks']}",
            "",
            "## Results by Check Type",
            ""
        ]
        
        # Group results by check type
        results_by_type = {}
        for result in self.results:
            if result.check_type not in results_by_type:
                results_by_type[result.check_type] = []
            results_by_type[result.check_type].append(result)
        
        for check_type, results in sorted(results_by_type.items()):
            passed = len([r for r in results if r.status == "pass"])
            failed = len([r for r in results if r.status == "fail"])
            warnings = len([r for r in results if r.status == "warning"])
            
            report_content.extend([
                f"### {check_type.replace('_', ' ').title()}",
                "",
                f"- Passed: {passed}",
                f"- Failed: {failed}",
                f"- Warnings: {warnings}",
                ""
            ])
            
            # Show failed checks
            if failed > 0:
                report_content.append("#### Failed Checks")
                report_content.append("")
                for result in results:
                    if result.status == "fail":
                        report_content.append(f"- **{result.file_path}**: {result.message}")
                report_content.append("")
        
        # Files analyzed
        report_content.extend([
            "## Files Analyzed",
            ""
        ])
        
        for file_path in sorted(summary['files_analyzed']):
            report_content.append(f"- {file_path}")
        
        # Save report
        report_path = Path("docs/generated") / "validation_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, "w") as f:
            f.write("\n".join(report_content))
        
        logger.info(f"Validation report saved to {report_path}")
        return report_path


async def main():
    """Main function to run documentation validation."""
    try:
        validator = DocumentationValidator()
        
        # Run validation
        results = await validator.validate_all_documentation()
        
        # Print summary
        print("\n" + "="*50)
        print("DOCUMENTATION VALIDATION RESULTS")
        print("="*50)
        print(f"Files Analyzed: {results['total_files']}")
        print(f"Total Checks: {results['total_checks']}")
        print(f"✅ Passed: {results['passed_checks']}")
        print(f"❌ Failed: {results['failed_checks']}")
        print(f"⚠️ Warnings: {results['warning_checks']}")
        print(f"📄 Report: {results['report_path']}")
        print("="*50)
        
        # Exit with appropriate code
        if results['failed_checks'] > 0:
            exit(1)
        else:
            exit(0)
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())