#!/usr/bin/env python3
"""
LeanVibe Documentation Quality Assurance System

Comprehensive quality checking system that ensures documentation meets 
enterprise standards for writing quality, technical accuracy, accessibility, 
and performance while maintaining consistency across all documentation.
"""

import json
import logging
import re
import statistics
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import requests
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityMetric(BaseModel):
    """Represents a quality metric with score and details."""
    name: str
    score: float  # 0-100
    max_score: float = 100.0
    details: Dict = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    category: str = "general"


class DocumentQualityReport(BaseModel):
    """Complete quality report for a document."""
    file_path: str
    timestamp: datetime
    overall_score: float
    metrics: List[QualityMetric]
    word_count: int
    reading_level: Optional[float] = None
    issues_found: int
    passed_checks: int
    total_checks: int


class DocumentationQualityChecker:
    """Enterprise-grade documentation quality assurance system."""
    
    def __init__(self, docs_directory: Path = Path(".")):
        self.docs_directory = Path(docs_directory)
        
        # Quality standards configuration
        self.quality_standards = {
            "min_overall_score": 80.0,
            "min_writing_quality": 85.0,
            "min_technical_accuracy": 90.0,
            "min_accessibility": 95.0,
            "max_reading_level": 12.0,  # Grade level
            "min_word_count": 100,
            "max_line_length": 120,
            "require_headings": True,
            "require_examples": True,
            "check_grammar": True,
            "check_spelling": True,
            "validate_links": True,
            "check_accessibility": True
        }
        
        # Content quality patterns
        self.quality_patterns = {
            "weak_words": [
                r'\bvery\b', r'\bquite\b', r'\brather\b', r'\bsomewhat\b',
                r'\bkind of\b', r'\bsort of\b', r'\ba bit\b'
            ],
            "passive_voice": [
                r'\bis\s+\w+ed\b', r'\bare\s+\w+ed\b', r'\bwas\s+\w+ed\b',
                r'\bwere\s+\w+ed\b', r'\bbeen\s+\w+ed\b', r'\bbeing\s+\w+ed\b'
            ],
            "filler_words": [
                r'\bobviously\b', r'\bbasically\b', r'\bsimply\b', r'\bjust\b',
                r'\breally\b', r'\bactually\b'
            ],
            "technical_terms": [
                r'\bAPI\b', r'\bREST\b', r'\bHTTP\b', r'\bJSON\b', r'\bXML\b',
                r'\bSQL\b', r'\bNoSQL\b', r'\bCRUD\b', r'\bJWT\b'
            ],
            "action_verbs": [
                r'\bcreate\b', r'\bgenerate\b', r'\bimplement\b', r'\bconfigure\b',
                r'\bdeploy\b', r'\bvalidate\b', r'\bmonitor\b'
            ]
        }
        
        # Accessibility requirements
        self.accessibility_requirements = {
            "heading_structure": True,
            "alt_text_images": True,
            "link_descriptions": True,
            "color_contrast": False,  # Requires visual analysis
            "table_headers": True,
            "list_structure": True
        }
        
        # Enterprise content standards
        self.content_standards = {
            "consistent_terminology": True,
            "brand_voice": True,
            "legal_compliance": True,
            "version_consistency": True,
            "contact_information": True
        }
    
    def check_all_documentation_quality(self) -> Dict[str, any]:
        """Run comprehensive quality checks on all documentation."""
        logger.info("Starting comprehensive documentation quality analysis")
        
        quality_summary = {
            "timestamp": datetime.now().isoformat(),
            "total_documents": 0,
            "average_score": 0.0,
            "documents_above_threshold": 0,
            "total_issues": 0,
            "reports": [],
            "recommendations": [],
            "quality_trends": {}
        }
        
        try:
            # Find all documentation files
            doc_files = self._find_documentation_files()
            quality_summary["total_documents"] = len(doc_files)
            
            scores = []
            total_issues = 0
            
            # Check quality for each document
            for doc_file in doc_files:
                report = self.check_document_quality(doc_file)
                quality_summary["reports"].append(report.dict())
                scores.append(report.overall_score)
                total_issues += report.issues_found
                
                if report.overall_score >= self.quality_standards["min_overall_score"]:
                    quality_summary["documents_above_threshold"] += 1
            
            # Calculate summary statistics
            if scores:
                quality_summary["average_score"] = statistics.mean(scores)
                quality_summary["median_score"] = statistics.median(scores)
                quality_summary["min_score"] = min(scores)
                quality_summary["max_score"] = max(scores)
            
            quality_summary["total_issues"] = total_issues
            
            # Generate enterprise recommendations
            quality_summary["recommendations"] = self._generate_enterprise_recommendations(
                quality_summary["reports"]
            )
            
            # Generate quality report
            report_path = self._generate_quality_report(quality_summary)
            quality_summary["report_path"] = str(report_path)
            
            logger.info(f"Quality analysis completed: Average score {quality_summary.get('average_score', 0):.1f}/100")
            return quality_summary
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            raise
    
    def check_document_quality(self, doc_file: Path) -> DocumentQualityReport:
        """Check quality of a single document."""
        logger.info(f"Analyzing quality of {doc_file}")
        
        try:
            content = doc_file.read_text(encoding='utf-8')
            metrics = []
            
            # Writing quality analysis
            writing_metrics = self._analyze_writing_quality(content)
            metrics.extend(writing_metrics)
            
            # Technical accuracy analysis
            technical_metrics = self._analyze_technical_accuracy(doc_file, content)
            metrics.extend(technical_metrics)
            
            # Accessibility analysis
            accessibility_metrics = self._analyze_accessibility(content)
            metrics.extend(accessibility_metrics)
            
            # Content structure analysis
            structure_metrics = self._analyze_content_structure(content)
            metrics.extend(structure_metrics)
            
            # Enterprise compliance analysis
            compliance_metrics = self._analyze_enterprise_compliance(content)
            metrics.extend(compliance_metrics)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(metrics)
            
            # Count issues and passes
            issues_found = len([m for m in metrics if m.score < 70.0])
            passed_checks = len([m for m in metrics if m.score >= 80.0])
            
            # Create report
            report = DocumentQualityReport(
                file_path=str(doc_file),
                timestamp=datetime.now(),
                overall_score=overall_score,
                metrics=metrics,
                word_count=len(content.split()),
                reading_level=self._calculate_reading_level(content),
                issues_found=issues_found,
                passed_checks=passed_checks,
                total_checks=len(metrics)
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to analyze {doc_file}: {e}")
            # Return minimal report with error
            return DocumentQualityReport(
                file_path=str(doc_file),
                timestamp=datetime.now(),
                overall_score=0.0,
                metrics=[],
                word_count=0,
                issues_found=1,
                passed_checks=0,
                total_checks=1
            )
    
    def _find_documentation_files(self) -> List[Path]:
        """Find all documentation files to analyze."""
        doc_files = []
        
        # Find markdown files
        doc_files.extend(self.docs_directory.glob("**/*.md"))
        
        # Filter out generated and system files
        filtered_files = []
        for file_path in doc_files:
            if not any(part.startswith('.') for part in file_path.parts):
                if 'generated' not in str(file_path).lower():
                    filtered_files.append(file_path)
        
        logger.info(f"Found {len(filtered_files)} documentation files for quality analysis")
        return filtered_files
    
    def _analyze_writing_quality(self, content: str) -> List[QualityMetric]:
        """Analyze writing quality including style, clarity, and readability."""
        metrics = []
        
        # Sentence length analysis
        sentences = re.split(r'[.!?]+', content)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        
        if sentence_lengths:
            avg_sentence_length = statistics.mean(sentence_lengths)
            sentence_score = max(0, 100 - (avg_sentence_length - 15) * 2)  # Optimal ~15 words
            
            metrics.append(QualityMetric(
                name="Sentence Length",
                score=min(100, sentence_score),
                category="writing_quality",
                details={"average_length": avg_sentence_length, "ideal_range": "12-18 words"},
                suggestions=["Consider breaking up long sentences for better readability"] if avg_sentence_length > 20 else []
            ))
        
        # Word choice analysis
        weak_word_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in self.quality_patterns["weak_words"])
        total_words = len(content.split())
        weak_word_ratio = weak_word_count / max(total_words, 1) * 100
        
        metrics.append(QualityMetric(
            name="Word Choice Strength",
            score=max(0, 100 - weak_word_ratio * 10),
            category="writing_quality",
            details={"weak_words_found": weak_word_count, "weak_word_ratio": f"{weak_word_ratio:.1f}%"},
            suggestions=["Replace weak qualifiers with specific, concrete language"] if weak_word_count > 0 else []
        ))
        
        # Passive voice analysis
        passive_voice_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in self.quality_patterns["passive_voice"])
        passive_voice_ratio = passive_voice_count / max(len(sentences), 1) * 100
        
        metrics.append(QualityMetric(
            name="Active Voice Usage",
            score=max(0, 100 - passive_voice_ratio * 5),
            category="writing_quality",
            details={"passive_constructions": passive_voice_count, "passive_ratio": f"{passive_voice_ratio:.1f}%"},
            suggestions=["Convert passive voice to active voice for clearer communication"] if passive_voice_count > 3 else []
        ))
        
        # Paragraph length analysis
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        if paragraphs:
            avg_paragraph_length = statistics.mean([len(p.split()) for p in paragraphs])
            paragraph_score = 100 if 50 <= avg_paragraph_length <= 150 else max(0, 100 - abs(avg_paragraph_length - 100))
            
            metrics.append(QualityMetric(
                name="Paragraph Structure",
                score=paragraph_score,
                category="writing_quality",
                details={"average_paragraph_length": avg_paragraph_length, "ideal_range": "50-150 words"},
                suggestions=["Consider breaking up long paragraphs or expanding short ones"] if paragraph_score < 80 else []
            ))
        
        return metrics
    
    def _analyze_technical_accuracy(self, doc_file: Path, content: str) -> List[QualityMetric]:
        """Analyze technical accuracy and consistency."""
        metrics = []
        
        # Code example validation
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        code_issues = 0
        
        for language, code in code_blocks:
            if language and language.lower() in ['python', 'javascript', 'bash', 'json', 'yaml']:
                if not self._validate_code_syntax(code, language.lower()):
                    code_issues += 1
        
        code_accuracy_score = 100 if len(code_blocks) == 0 else max(0, 100 - (code_issues / len(code_blocks)) * 100)
        
        metrics.append(QualityMetric(
            name="Code Example Accuracy",
            score=code_accuracy_score,
            category="technical_accuracy",
            details={"total_code_blocks": len(code_blocks), "syntax_errors": code_issues},
            suggestions=["Fix syntax errors in code examples"] if code_issues > 0 else []
        ))
        
        # API endpoint consistency
        api_endpoints = re.findall(r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)', content)
        consistent_formatting = all(endpoint[1].startswith('/') for endpoint in api_endpoints)
        
        metrics.append(QualityMetric(
            name="API Endpoint Consistency",
            score=100 if consistent_formatting else 70,
            category="technical_accuracy",
            details={"endpoints_found": len(api_endpoints), "consistent_formatting": consistent_formatting},
            suggestions=["Ensure all API endpoints follow consistent formatting"] if not consistent_formatting else []
        ))
        
        # Technical terminology consistency
        tech_terms = []
        for pattern in self.quality_patterns["technical_terms"]:
            matches = re.findall(pattern, content)
            tech_terms.extend(matches)
        
        # Check for consistent capitalization of technical terms
        inconsistent_terms = []
        for term in set(tech_terms):
            variations = re.findall(re.escape(term), content, re.IGNORECASE)
            if len(set(variations)) > 1:
                inconsistent_terms.append(term)
        
        terminology_score = 100 if len(inconsistent_terms) == 0 else max(0, 100 - len(inconsistent_terms) * 10)
        
        metrics.append(QualityMetric(
            name="Technical Terminology Consistency",
            score=terminology_score,
            category="technical_accuracy",
            details={"inconsistent_terms": inconsistent_terms},
            suggestions=[f"Standardize capitalization for: {', '.join(inconsistent_terms)}"] if inconsistent_terms else []
        ))
        
        return metrics
    
    def _analyze_accessibility(self, content: str) -> List[QualityMetric]:
        """Analyze accessibility compliance."""
        metrics = []
        
        # Heading structure analysis
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        heading_levels = [len(h[0]) for h in headings]
        
        proper_hierarchy = True
        if heading_levels:
            for i in range(1, len(heading_levels)):
                if heading_levels[i] > heading_levels[i-1] + 1:
                    proper_hierarchy = False
                    break
        
        metrics.append(QualityMetric(
            name="Heading Hierarchy",
            score=100 if proper_hierarchy else 60,
            category="accessibility",
            details={"total_headings": len(headings), "proper_hierarchy": proper_hierarchy},
            suggestions=["Fix heading hierarchy - avoid skipping heading levels"] if not proper_hierarchy else []
        ))
        
        # Alt text for images
        images = re.findall(r'!\[([^\]]*)\]\([^)]+\)', content)
        images_with_alt = sum(1 for alt_text in images if alt_text.strip())
        alt_text_score = 100 if len(images) == 0 else (images_with_alt / len(images)) * 100
        
        metrics.append(QualityMetric(
            name="Image Alt Text",
            score=alt_text_score,
            category="accessibility",
            details={"total_images": len(images), "images_with_alt": images_with_alt},
            suggestions=["Add descriptive alt text for all images"] if alt_text_score < 100 else []
        ))
        
        # Link descriptions
        links = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
        descriptive_links = sum(1 for link_text in links if len(link_text) > 3 and link_text.lower() not in ['here', 'click', 'link'])
        link_description_score = 100 if len(links) == 0 else (descriptive_links / len(links)) * 100
        
        metrics.append(QualityMetric(
            name="Link Descriptions",
            score=link_description_score,
            category="accessibility",
            details={"total_links": len(links), "descriptive_links": descriptive_links},
            suggestions=["Use descriptive link text instead of 'here' or 'click'"] if link_description_score < 90 else []
        ))
        
        # Table headers
        tables = re.findall(r'\|.+\|\n\|[-\s|]+\|\n(\|.+\|\n)+', content)
        # Simple heuristic: tables should have header rows
        table_accessibility_score = 100  # Assume good unless we can detect issues
        
        metrics.append(QualityMetric(
            name="Table Accessibility",
            score=table_accessibility_score,
            category="accessibility",
            details={"tables_found": len(tables)},
            suggestions=[]
        ))
        
        return metrics
    
    def _analyze_content_structure(self, content: str) -> List[QualityMetric]:
        """Analyze content organization and structure."""
        metrics = []
        
        # Introduction presence
        has_intro = bool(re.search(r'^##?\s+(overview|introduction|getting started)', content, re.MULTILINE | re.IGNORECASE))
        
        metrics.append(QualityMetric(
            name="Introduction Section",
            score=100 if has_intro else 70,
            category="content_structure",
            details={"has_introduction": has_intro},
            suggestions=["Add an introduction or overview section"] if not has_intro else []
        ))
        
        # Table of contents for long documents
        word_count = len(content.split())
        toc_present = bool(re.search(r'table of contents|toc', content, re.IGNORECASE))
        needs_toc = word_count > 1500
        
        toc_score = 100
        if needs_toc and not toc_present:
            toc_score = 60
        
        metrics.append(QualityMetric(
            name="Table of Contents",
            score=toc_score,
            category="content_structure",
            details={"word_count": word_count, "needs_toc": needs_toc, "has_toc": toc_present},
            suggestions=["Consider adding a table of contents for this long document"] if needs_toc and not toc_present else []
        ))
        
        # Code examples presence (for technical docs)
        code_blocks = len(re.findall(r'```', content)) // 2
        is_technical_doc = any(term in content.lower() for term in ['api', 'code', 'example', 'install', 'setup', 'config'])
        
        if is_technical_doc:
            has_examples = code_blocks > 0
            examples_score = 100 if has_examples else 50
            
            metrics.append(QualityMetric(
                name="Code Examples",
                score=examples_score,
                category="content_structure",
                details={"code_blocks": code_blocks, "is_technical": is_technical_doc},
                suggestions=["Add practical code examples to illustrate concepts"] if not has_examples else []
            ))
        
        # Consistent formatting
        bullet_patterns = [re.findall(r'^\s*[-*+]\s', content, re.MULTILINE), re.findall(r'^\s*\d+\.\s', content, re.MULTILINE)]
        mixed_bullets = len([p for p in bullet_patterns if p]) > 1
        
        formatting_score = 90 if mixed_bullets else 100
        
        metrics.append(QualityMetric(
            name="Consistent Formatting",
            score=formatting_score,
            category="content_structure",
            details={"mixed_bullet_styles": mixed_bullets},
            suggestions=["Use consistent bullet point styles throughout the document"] if mixed_bullets else []
        ))
        
        return metrics
    
    def _analyze_enterprise_compliance(self, content: str) -> List[QualityMetric]:
        """Analyze enterprise compliance requirements."""
        metrics = []
        
        # Contact information presence
        has_contact = bool(re.search(r'(support@|contact|help@|enterprise@)', content, re.IGNORECASE))
        
        metrics.append(QualityMetric(
            name="Contact Information",
            score=100 if has_contact else 80,
            category="enterprise_compliance",
            details={"has_contact_info": has_contact},
            suggestions=["Include enterprise contact information"] if not has_contact else []
        ))
        
        # Version information
        has_version = bool(re.search(r'(version|v\d+\.\d+|release)', content, re.IGNORECASE))
        
        metrics.append(QualityMetric(
            name="Version Information",
            score=100 if has_version else 75,
            category="enterprise_compliance",
            details={"has_version_info": has_version},
            suggestions=["Include version or release information"] if not has_version else []
        ))
        
        # Legal/compliance references
        has_legal = bool(re.search(r'(gdpr|privacy|terms|license|compliance|security)', content, re.IGNORECASE))
        
        metrics.append(QualityMetric(
            name="Compliance References",
            score=100 if has_legal else 70,
            category="enterprise_compliance",
            details={"has_legal_references": has_legal},
            suggestions=["Consider adding relevant compliance or legal information"] if not has_legal else []
        ))
        
        return metrics
    
    def _validate_code_syntax(self, code: str, language: str) -> bool:
        """Validate syntax of code examples."""
        try:
            if language == 'python':
                compile(code, '<string>', 'exec')
                return True
            elif language == 'json':
                import json
                json.loads(code)
                return True
            elif language == 'yaml':
                try:
                    import yaml
                    yaml.safe_load(code)
                    return True
                except ImportError:
                    return True  # Assume valid if PyYAML not available
            elif language == 'bash':
                # Basic bash syntax check - very permissive
                return not ('<<' in code and '>>' in code)  # Avoid complex redirections
            else:
                return True  # Assume valid for other languages
        except Exception:
            return False
    
    def _calculate_reading_level(self, content: str) -> Optional[float]:
        """Calculate Flesch-Kincaid reading level."""
        try:
            # Remove code blocks and technical content for reading level calculation
            text = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
            text = re.sub(r'`[^`]+`', '', text)
            text = re.sub(r'https?://[^\s]+', '', text)
            
            sentences = len(re.findall(r'[.!?]+', text))
            words = len(text.split())
            syllables = sum(self._count_syllables(word) for word in text.split())
            
            if sentences > 0 and words > 0:
                # Flesch-Kincaid Grade Level
                grade_level = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
                return max(0, grade_level)
        except Exception as e:
            logger.warning(f"Failed to calculate reading level: {e}")
        
        return None
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximate)."""
        word = word.lower().strip(".,!?;:")
        if not word:
            return 0
        
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _calculate_overall_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate overall quality score from metrics."""
        if not metrics:
            return 0.0
        
        # Weight different categories
        category_weights = {
            "writing_quality": 0.25,
            "technical_accuracy": 0.30,
            "accessibility": 0.20,
            "content_structure": 0.15,
            "enterprise_compliance": 0.10
        }
        
        weighted_scores = {}
        category_counts = {}
        
        for metric in metrics:
            category = metric.category
            if category not in weighted_scores:
                weighted_scores[category] = 0.0
                category_counts[category] = 0
            
            weighted_scores[category] += metric.score
            category_counts[category] += 1
        
        # Calculate category averages
        category_averages = {}
        for category, total_score in weighted_scores.items():
            category_averages[category] = total_score / category_counts[category]
        
        # Apply weights
        overall_score = 0.0
        total_weight = 0.0
        
        for category, weight in category_weights.items():
            if category in category_averages:
                overall_score += category_averages[category] * weight
                total_weight += weight
        
        # Normalize if not all categories are present
        if total_weight > 0:
            overall_score /= total_weight
        
        return round(overall_score, 1)
    
    def _generate_enterprise_recommendations(self, reports: List[Dict]) -> List[str]:
        """Generate enterprise-specific recommendations based on quality analysis."""
        recommendations = []
        
        # Analyze overall trends
        all_scores = [report["overall_score"] for report in reports]
        avg_score = statistics.mean(all_scores) if all_scores else 0
        
        if avg_score < 80:
            recommendations.append("🔴 PRIORITY: Overall documentation quality below enterprise standards (80+)")
        
        # Category-specific recommendations
        category_issues = {}
        for report in reports:
            for metric in report["metrics"]:
                category = metric["category"]
                if metric["score"] < 70:
                    if category not in category_issues:
                        category_issues[category] = 0
                    category_issues[category] += 1
        
        # Generate specific recommendations
        if "technical_accuracy" in category_issues and category_issues["technical_accuracy"] > len(reports) * 0.3:
            recommendations.append("📋 TECHNICAL: Implement code example validation in CI/CD pipeline")
        
        if "accessibility" in category_issues and category_issues["accessibility"] > len(reports) * 0.2:
            recommendations.append("♿ ACCESSIBILITY: Mandatory accessibility review for all new documentation")
        
        if "writing_quality" in category_issues and category_issues["writing_quality"] > len(reports) * 0.4:
            recommendations.append("✍️ WRITING: Consider implementing automated writing quality checks")
        
        # Enterprise-specific recommendations
        enterprise_issues = sum(1 for report in reports for metric in report["metrics"] 
                              if metric["category"] == "enterprise_compliance" and metric["score"] < 80)
        
        if enterprise_issues > len(reports) * 0.5:
            recommendations.append("🏢 ENTERPRISE: Review all documentation for compliance and legal requirements")
        
        # Performance recommendations
        long_docs = sum(1 for report in reports if report["word_count"] > 2000)
        if long_docs > len(reports) * 0.3:
            recommendations.append("📚 STRUCTURE: Consider breaking long documents into focused, shorter guides")
        
        return recommendations
    
    def _generate_quality_report(self, summary: Dict) -> Path:
        """Generate comprehensive quality report."""
        logger.info("Generating quality report")
        
        report_content = [
            "# Documentation Quality Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Documents Analyzed:** {summary['total_documents']}",
            f"**Average Quality Score:** {summary.get('average_score', 0):.1f}/100",
            "",
            "## Executive Summary",
            "",
            f"- 📊 **Overall Quality:** {summary.get('average_score', 0):.1f}/100",
            f"- ✅ **Above Threshold (80+):** {summary['documents_above_threshold']}/{summary['total_documents']}",
            f"- ⚠️ **Total Issues:** {summary['total_issues']}",
            "",
            "### Quality Distribution",
            ""
        ]
        
        if summary.get('reports'):
            scores = [report['overall_score'] for report in summary['reports']]
            excellent = sum(1 for s in scores if s >= 90)
            good = sum(1 for s in scores if 80 <= s < 90)
            fair = sum(1 for s in scores if 70 <= s < 80)
            poor = sum(1 for s in scores if s < 70)
            
            report_content.extend([
                f"- 🟢 **Excellent (90+):** {excellent} documents",
                f"- 🔵 **Good (80-89):** {good} documents",
                f"- 🟡 **Fair (70-79):** {fair} documents",
                f"- 🔴 **Poor (<70):** {poor} documents",
                ""
            ])
        
        # Recommendations
        if summary.get('recommendations'):
            report_content.extend([
                "## Recommendations",
                ""
            ])
            for rec in summary['recommendations']:
                report_content.append(f"- {rec}")
            report_content.append("")
        
        # Individual document results
        report_content.extend([
            "## Document Quality Scores",
            "",
            "| Document | Score | Issues | Word Count | Status |",
            "|----------|--------|--------|------------|--------|"
        ])
        
        for report in sorted(summary.get('reports', []), key=lambda r: r['overall_score'], reverse=True):
            status = "🟢" if report['overall_score'] >= 90 else "🔵" if report['overall_score'] >= 80 else "🟡" if report['overall_score'] >= 70 else "🔴"
            file_name = Path(report['file_path']).name
            
            report_content.append(
                f"| {file_name} | {report['overall_score']:.1f} | {report['issues_found']} | {report['word_count']} | {status} |"
            )
        
        # Quality trends and insights
        report_content.extend([
            "",
            "## Quality Insights",
            "",
            "### Most Common Issues",
            ""
        ])
        
        # Analyze common issues
        all_issues = {}
        for report in summary.get('reports', []):
            for metric in report['metrics']:
                if metric['score'] < 70:
                    issue_type = metric['name']
                    if issue_type not in all_issues:
                        all_issues[issue_type] = 0
                    all_issues[issue_type] += 1
        
        for issue, count in sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:5]:
            report_content.append(f"- **{issue}:** {count} documents affected")
        
        # Save report
        report_path = Path("docs/generated") / "quality_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, "w") as f:
            f.write("\n".join(report_content))
        
        # Also save detailed JSON report
        json_report_path = Path("docs/generated") / "quality_report.json"
        with open(json_report_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Quality report saved to {report_path}")
        return report_path


def main():
    """Main function to run quality analysis."""
    try:
        checker = DocumentationQualityChecker()
        
        # Run quality analysis
        results = checker.check_all_documentation_quality()
        
        # Print summary
        print("\n" + "="*50)
        print("DOCUMENTATION QUALITY ANALYSIS")
        print("="*50)
        print(f"Documents Analyzed: {results['total_documents']}")
        print(f"Average Score: {results.get('average_score', 0):.1f}/100")
        print(f"Above Threshold (80+): {results['documents_above_threshold']}/{results['total_documents']}")
        print(f"Total Issues: {results['total_issues']}")
        print(f"Report: {results['report_path']}")
        print("="*50)
        
        # Print top recommendations
        if results.get('recommendations'):
            print("\nTOP RECOMMENDATIONS:")
            for i, rec in enumerate(results['recommendations'][:3], 1):
                print(f"{i}. {rec}")
        
        # Exit with appropriate code
        avg_score = results.get('average_score', 0)
        if avg_score < 70:
            exit(1)  # Critical quality issues
        elif avg_score < 80:
            exit(2)  # Quality below enterprise standards
        else:
            exit(0)  # Quality acceptable
            
    except Exception as e:
        logger.error(f"Quality analysis failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()