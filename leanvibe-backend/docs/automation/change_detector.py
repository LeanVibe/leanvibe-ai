#!/usr/bin/env python3
"""
LeanVibe Documentation Change Detection System

Monitors code changes, API modifications, and configuration updates 
to automatically trigger documentation updates and maintain accuracy.
"""

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import yaml
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChangeEvent(BaseModel):
    """Represents a detected change that may require documentation updates."""
    timestamp: datetime
    change_type: str  # "api_endpoint", "model_change", "config_change", "deployment_change"
    severity: str  # "critical", "major", "minor"
    file_path: str
    description: str
    affected_docs: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    git_commit: Optional[str] = None
    details: Dict = Field(default_factory=dict)


class DocumentationChangeDetector:
    """Comprehensive change detection system for documentation maintenance."""
    
    def __init__(self, project_root: Path = Path(".")):
        self.project_root = Path(project_root)
        self.state_file = self.project_root / ".claude" / "docs_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load previous state
        self.previous_state = self._load_state()
        self.current_state = {}
        self.detected_changes: List[ChangeEvent] = []
        
        # Configuration
        self.config = {
            "monitor_api_changes": True,
            "monitor_model_changes": True,
            "monitor_config_changes": True,
            "monitor_deployment_changes": True,
            "check_interval_hours": 1,
            "auto_update_docs": True,
            "create_github_issues": False,
            "notify_maintainers": True
        }
        
        # File patterns to monitor
        self.watch_patterns = {
            "api_endpoints": ["app/api/endpoints/**/*.py"],
            "models": ["app/models/**/*.py", "app/api/models.py"],
            "config": ["app/config/**/*.py", "*.yaml", "*.yml", "pyproject.toml"],
            "deployment": ["k8s/**/*.yaml", "docker-compose*.yml", "Dockerfile*", "terraform/**/*.tf"],
            "contracts": ["contracts/**/*"]
        }
        
        # Documentation mapping
        self.doc_mappings = {
            "api_endpoints": ["API.md", "API_ENTERPRISE.md", "contracts/openapi.yaml"],
            "models": ["API.md", "ARCHITECTURE.md"],
            "config": ["INSTALLATION.md", "QUICKSTART.md", "ENTERPRISE.md"],
            "deployment": ["PRODUCTION_DEPLOYMENT_GUIDE.md", "k8s/**/*.yaml", "docs/operations/**/*.md"],
            "contracts": ["contracts/**/*", "API*.md"]
        }
    
    def detect_all_changes(self) -> List[ChangeEvent]:
        """Detect all types of changes that may require documentation updates."""
        logger.info("Starting comprehensive change detection")
        
        try:
            # Detect different types of changes
            if self.config["monitor_api_changes"]:
                self._detect_api_changes()
            
            if self.config["monitor_model_changes"]:
                self._detect_model_changes()
            
            if self.config["monitor_config_changes"]:
                self._detect_config_changes()
            
            if self.config["monitor_deployment_changes"]:
                self._detect_deployment_changes()
            
            # Check for new/deleted files
            self._detect_file_structure_changes()
            
            # Check git history for recent changes
            self._detect_recent_commits()
            
            # Save current state
            self._save_state()
            
            logger.info(f"Detected {len(self.detected_changes)} changes requiring documentation attention")
            return self.detected_changes
            
        except Exception as e:
            logger.error(f"Change detection failed: {e}")
            raise
    
    def _load_state(self) -> Dict:
        """Load previous state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load previous state: {e}")
        return {}
    
    def _save_state(self):
        """Save current state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.current_state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _detect_api_changes(self):
        """Detect API endpoint changes."""
        logger.info("Detecting API endpoint changes")
        
        # Find all API endpoint files
        api_files = []
        for pattern in self.watch_patterns["api_endpoints"]:
            api_files.extend(self.project_root.glob(pattern))
        
        for api_file in api_files:
            if api_file.is_file():
                self._check_api_file_changes(api_file)
    
    def _check_api_file_changes(self, api_file: Path):
        """Check specific API file for changes."""
        try:
            content = api_file.read_text(encoding='utf-8')
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            file_key = str(api_file.relative_to(self.project_root))
            previous_hash = self.previous_state.get('file_hashes', {}).get(file_key)
            
            # Store current hash
            if 'file_hashes' not in self.current_state:
                self.current_state['file_hashes'] = {}
            self.current_state['file_hashes'][file_key] = content_hash
            
            # Check for changes
            if previous_hash and previous_hash != content_hash:
                changes = self._analyze_api_file_changes(api_file, content)
                
                if changes:
                    self.detected_changes.append(ChangeEvent(
                        timestamp=datetime.now(),
                        change_type="api_endpoint",
                        severity=self._determine_api_change_severity(changes),
                        file_path=str(api_file),
                        description=f"API changes detected in {api_file.name}",
                        affected_docs=self.doc_mappings["api_endpoints"],
                        suggested_actions=self._suggest_api_update_actions(changes),
                        details={"changes": changes}
                    ))
        except Exception as e:
            logger.error(f"Failed to check API file {api_file}: {e}")
    
    def _analyze_api_file_changes(self, api_file: Path, content: str) -> List[Dict]:
        """Analyze what specific changes occurred in an API file."""
        changes = []
        
        # Look for new/modified endpoints
        import re
        
        # Find FastAPI route decorators
        route_patterns = [
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for method, path in matches:
                changes.append({
                    "type": "endpoint",
                    "method": method.upper(),
                    "path": path,
                    "action": "added_or_modified"
                })
        
        # Look for new Pydantic models
        model_pattern = r'class\s+(\w+)\([^)]*BaseModel[^)]*\):'
        model_matches = re.findall(model_pattern, content)
        for model_name in model_matches:
            changes.append({
                "type": "model",
                "name": model_name,
                "action": "added_or_modified"
            })
        
        return changes
    
    def _determine_api_change_severity(self, changes: List[Dict]) -> str:
        """Determine severity of API changes."""
        has_breaking_changes = any(
            change.get("method") in ["DELETE"] or 
            "removed" in change.get("action", "")
            for change in changes
        )
        
        if has_breaking_changes:
            return "critical"
        elif len(changes) > 5:
            return "major"
        else:
            return "minor"
    
    def _suggest_api_update_actions(self, changes: List[Dict]) -> List[str]:
        """Suggest documentation update actions for API changes."""
        actions = []
        
        for change in changes:
            if change.get("type") == "endpoint":
                actions.append(f"Update API documentation for {change['method']} {change['path']}")
                actions.append("Regenerate OpenAPI specification")
                actions.append("Update Postman collection")
            elif change.get("type") == "model":
                actions.append(f"Document new model: {change['name']}")
                actions.append("Update API schema documentation")
        
        # Remove duplicates
        return list(set(actions))
    
    def _detect_model_changes(self):
        """Detect data model changes."""
        logger.info("Detecting model changes")
        
        model_files = []
        for pattern in self.watch_patterns["models"]:
            model_files.extend(self.project_root.glob(pattern))
        
        for model_file in model_files:
            if model_file.is_file():
                self._check_model_file_changes(model_file)
    
    def _check_model_file_changes(self, model_file: Path):
        """Check specific model file for changes."""
        try:
            content = model_file.read_text(encoding='utf-8')
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            file_key = str(model_file.relative_to(self.project_root))
            previous_hash = self.previous_state.get('file_hashes', {}).get(file_key)
            
            if 'file_hashes' not in self.current_state:
                self.current_state['file_hashes'] = {}
            self.current_state['file_hashes'][file_key] = content_hash
            
            if previous_hash and previous_hash != content_hash:
                changes = self._analyze_model_changes(model_file, content)
                
                if changes:
                    self.detected_changes.append(ChangeEvent(
                        timestamp=datetime.now(),
                        change_type="model_change",
                        severity=self._determine_model_change_severity(changes),
                        file_path=str(model_file),
                        description=f"Model changes detected in {model_file.name}",
                        affected_docs=self.doc_mappings["models"],
                        suggested_actions=self._suggest_model_update_actions(changes),
                        details={"changes": changes}
                    ))
        except Exception as e:
            logger.error(f"Failed to check model file {model_file}: {e}")
    
    def _analyze_model_changes(self, model_file: Path, content: str) -> List[Dict]:
        """Analyze model changes."""
        changes = []
        
        import re
        
        # Find Pydantic models
        model_pattern = r'class\s+(\w+)\([^)]*BaseModel[^)]*\):'
        models = re.findall(model_pattern, content)
        
        # Find SQLAlchemy models
        sqlalchemy_pattern = r'class\s+(\w+)\([^)]*Base[^)]*\):'
        sqlalchemy_models = re.findall(sqlalchemy_pattern, content)
        
        for model in models + sqlalchemy_models:
            changes.append({
                "type": "pydantic_model" if model in models else "sqlalchemy_model",
                "name": model,
                "action": "added_or_modified"
            })
        
        return changes
    
    def _determine_model_change_severity(self, changes: List[Dict]) -> str:
        """Determine severity of model changes."""
        if len(changes) > 3:
            return "major"
        elif any(change.get("type") == "sqlalchemy_model" for change in changes):
            return "major"  # Database schema changes are significant
        else:
            return "minor"
    
    def _suggest_model_update_actions(self, changes: List[Dict]) -> List[str]:
        """Suggest actions for model changes."""
        actions = []
        
        for change in changes:
            if change.get("type") == "sqlalchemy_model":
                actions.extend([
                    f"Update database schema documentation for {change['name']}",
                    "Review migration requirements",
                    "Update API documentation if model is exposed"
                ])
            elif change.get("type") == "pydantic_model":
                actions.extend([
                    f"Update API schema for {change['name']}",
                    "Regenerate OpenAPI specification"
                ])
        
        return list(set(actions))
    
    def _detect_config_changes(self):
        """Detect configuration changes."""
        logger.info("Detecting configuration changes")
        
        config_files = []
        for pattern in self.watch_patterns["config"]:
            config_files.extend(self.project_root.glob(pattern))
        
        for config_file in config_files:
            if config_file.is_file():
                self._check_config_file_changes(config_file)
    
    def _check_config_file_changes(self, config_file: Path):
        """Check configuration file for changes."""
        try:
            content = config_file.read_text(encoding='utf-8')
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            file_key = str(config_file.relative_to(self.project_root))
            previous_hash = self.previous_state.get('file_hashes', {}).get(file_key)
            
            if 'file_hashes' not in self.current_state:
                self.current_state['file_hashes'] = {}
            self.current_state['file_hashes'][file_key] = content_hash
            
            if previous_hash and previous_hash != content_hash:
                self.detected_changes.append(ChangeEvent(
                    timestamp=datetime.now(),
                    change_type="config_change",
                    severity="major" if config_file.name in ["settings.py", "pyproject.toml"] else "minor",
                    file_path=str(config_file),
                    description=f"Configuration change in {config_file.name}",
                    affected_docs=self.doc_mappings["config"],
                    suggested_actions=[
                        f"Review {config_file.name} documentation",
                        "Update installation/setup guides",
                        "Check environment variable documentation"
                    ]
                ))
        except Exception as e:
            logger.error(f"Failed to check config file {config_file}: {e}")
    
    def _detect_deployment_changes(self):
        """Detect deployment configuration changes."""
        logger.info("Detecting deployment changes")
        
        deployment_files = []
        for pattern in self.watch_patterns["deployment"]:
            deployment_files.extend(self.project_root.glob(pattern))
        
        for deployment_file in deployment_files:
            if deployment_file.is_file():
                self._check_deployment_file_changes(deployment_file)
    
    def _check_deployment_file_changes(self, deployment_file: Path):
        """Check deployment file for changes."""
        try:
            content = deployment_file.read_text(encoding='utf-8')
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            file_key = str(deployment_file.relative_to(self.project_root))
            previous_hash = self.previous_state.get('file_hashes', {}).get(file_key)
            
            if 'file_hashes' not in self.current_state:
                self.current_state['file_hashes'] = {}
            self.current_state['file_hashes'][file_key] = content_hash
            
            if previous_hash and previous_hash != content_hash:
                severity = "critical" if "production" in str(deployment_file).lower() else "major"
                
                self.detected_changes.append(ChangeEvent(
                    timestamp=datetime.now(),
                    change_type="deployment_change",
                    severity=severity,
                    file_path=str(deployment_file),
                    description=f"Deployment configuration change in {deployment_file.name}",
                    affected_docs=self.doc_mappings["deployment"],
                    suggested_actions=[
                        f"Update deployment documentation for {deployment_file.name}",
                        "Review infrastructure documentation",
                        "Check operational runbooks",
                        "Update environment setup guides"
                    ]
                ))
        except Exception as e:
            logger.error(f"Failed to check deployment file {deployment_file}: {e}")
    
    def _detect_file_structure_changes(self):
        """Detect new or deleted files that may need documentation."""
        logger.info("Detecting file structure changes")
        
        # Get current file structure
        current_files = set()
        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden directories and common build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
            
            for file in files:
                if not file.startswith('.'):
                    file_path = Path(root) / file
                    current_files.add(str(file_path.relative_to(self.project_root)))
        
        previous_files = set(self.previous_state.get('file_structure', []))
        
        # Store current file structure
        self.current_state['file_structure'] = list(current_files)
        
        # Detect new files
        new_files = current_files - previous_files
        deleted_files = previous_files - current_files
        
        for new_file in new_files:
            if self._is_significant_file(new_file):
                self.detected_changes.append(ChangeEvent(
                    timestamp=datetime.now(),
                    change_type="new_file",
                    severity="minor",
                    file_path=new_file,
                    description=f"New file added: {new_file}",
                    affected_docs=[],
                    suggested_actions=[f"Consider documenting new file: {new_file}"]
                ))
        
        for deleted_file in deleted_files:
            if self._is_significant_file(deleted_file):
                self.detected_changes.append(ChangeEvent(
                    timestamp=datetime.now(),
                    change_type="deleted_file",
                    severity="major",
                    file_path=deleted_file,
                    description=f"File deleted: {deleted_file}",
                    affected_docs=[],
                    suggested_actions=[f"Remove documentation references to: {deleted_file}"]
                ))
    
    def _is_significant_file(self, file_path: str) -> bool:
        """Determine if a file is significant enough to warrant documentation attention."""
        significant_extensions = {'.py', '.yaml', '.yml', '.md', '.json', '.tf', '.sh'}
        significant_names = {'Dockerfile', 'Makefile', 'requirements.txt', 'pyproject.toml'}
        
        path = Path(file_path)
        return (
            path.suffix.lower() in significant_extensions or
            path.name in significant_names or
            'api' in str(path).lower() or
            'config' in str(path).lower()
        )
    
    def _detect_recent_commits(self):
        """Analyze recent Git commits for documentation-relevant changes."""
        logger.info("Analyzing recent Git commits")
        
        try:
            # Get commits from last 24 hours
            since_date = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')
            
            result = subprocess.run([
                'git', 'log', f'--since={since_date}', '--oneline', '--name-only'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                commits = self._parse_git_log_output(result.stdout)
                
                for commit in commits:
                    if self._commit_affects_documentation(commit):
                        self.detected_changes.append(ChangeEvent(
                            timestamp=datetime.now(),
                            change_type="recent_commit",
                            severity=self._assess_commit_severity(commit),
                            file_path="",
                            description=commit["message"],
                            affected_docs=self._identify_affected_docs_from_commit(commit),
                            suggested_actions=self._suggest_actions_from_commit(commit),
                            git_commit=commit["hash"],
                            details={"files_changed": commit["files"]}
                        ))
        
        except Exception as e:
            logger.warning(f"Failed to analyze recent commits: {e}")
    
    def _parse_git_log_output(self, output: str) -> List[Dict]:
        """Parse git log output into structured commit data."""
        commits = []
        current_commit = None
        
        for line in output.strip().split('\n'):
            if line and not line.startswith(' '):
                # New commit line
                if ' ' in line:
                    commit_hash, message = line.split(' ', 1)
                    current_commit = {
                        "hash": commit_hash,
                        "message": message,
                        "files": []
                    }
                    commits.append(current_commit)
            elif line.strip() and current_commit:
                # File changed in current commit
                current_commit["files"].append(line.strip())
        
        return commits
    
    def _commit_affects_documentation(self, commit: Dict) -> bool:
        """Determine if a commit affects documentation."""
        doc_keywords = ['api', 'model', 'config', 'deploy', 'endpoint', 'schema']
        
        # Check commit message
        message_lower = commit["message"].lower()
        if any(keyword in message_lower for keyword in doc_keywords):
            return True
        
        # Check affected files
        for file_path in commit["files"]:
            if any(pattern in file_path for pattern_list in self.watch_patterns.values() for pattern in pattern_list):
                return True
        
        return False
    
    def _assess_commit_severity(self, commit: Dict) -> str:
        """Assess the severity of a commit's impact on documentation."""
        breaking_keywords = ['breaking', 'remove', 'delete', 'deprecated']
        major_keywords = ['add', 'new', 'feature', 'endpoint']
        
        message_lower = commit["message"].lower()
        
        if any(keyword in message_lower for keyword in breaking_keywords):
            return "critical"
        elif any(keyword in message_lower for keyword in major_keywords):
            return "major"
        else:
            return "minor"
    
    def _identify_affected_docs_from_commit(self, commit: Dict) -> List[str]:
        """Identify which documentation files are affected by a commit."""
        affected_docs = set()
        
        for file_path in commit["files"]:
            for category, patterns in self.watch_patterns.items():
                if any(pattern.replace("**/*", "") in file_path for pattern in patterns):
                    affected_docs.update(self.doc_mappings.get(category, []))
        
        return list(affected_docs)
    
    def _suggest_actions_from_commit(self, commit: Dict) -> List[str]:
        """Suggest documentation actions based on commit analysis."""
        actions = []
        
        message_lower = commit["message"].lower()
        
        if "api" in message_lower or "endpoint" in message_lower:
            actions.extend([
                "Review API documentation for changes",
                "Update OpenAPI specification",
                "Test API examples in documentation"
            ])
        
        if "model" in message_lower or "schema" in message_lower:
            actions.extend([
                "Update data model documentation",
                "Review API schema documentation"
            ])
        
        if "config" in message_lower:
            actions.extend([
                "Update configuration documentation",
                "Review setup/installation guides"
            ])
        
        if "deploy" in message_lower:
            actions.extend([
                "Update deployment documentation",
                "Review operational guides"
            ])
        
        return actions
    
    def generate_change_report(self) -> str:
        """Generate a comprehensive change report."""
        logger.info("Generating change report")
        
        report_content = [
            "# Documentation Change Detection Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Changes Detected:** {len(self.detected_changes)}",
            ""
        ]
        
        if not self.detected_changes:
            report_content.extend([
                "## Summary",
                "",
                "✅ No changes detected that require documentation updates.",
                ""
            ])
        else:
            # Group changes by severity
            critical_changes = [c for c in self.detected_changes if c.severity == "critical"]
            major_changes = [c for c in self.detected_changes if c.severity == "major"]
            minor_changes = [c for c in self.detected_changes if c.severity == "minor"]
            
            report_content.extend([
                "## Summary by Severity",
                "",
                f"- 🔴 **Critical:** {len(critical_changes)} changes",
                f"- 🟡 **Major:** {len(major_changes)} changes", 
                f"- 🟢 **Minor:** {len(minor_changes)} changes",
                ""
            ])
            
            # Detail each category
            for severity, changes, icon in [
                ("Critical", critical_changes, "🔴"),
                ("Major", major_changes, "🟡"),
                ("Minor", minor_changes, "🟢")
            ]:
                if changes:
                    report_content.extend([
                        f"## {icon} {severity} Changes",
                        ""
                    ])
                    
                    for change in changes:
                        report_content.extend([
                            f"### {change.change_type.replace('_', ' ').title()}",
                            f"**File:** `{change.file_path}`",
                            f"**Description:** {change.description}",
                            ""
                        ])
                        
                        if change.affected_docs:
                            report_content.extend([
                                "**Affected Documentation:**"
                            ])
                            for doc in change.affected_docs:
                                report_content.append(f"- {doc}")
                            report_content.append("")
                        
                        if change.suggested_actions:
                            report_content.extend([
                                "**Suggested Actions:**"
                            ])
                            for action in change.suggested_actions:
                                report_content.append(f"- {action}")
                            report_content.append("")
                        
                        report_content.append("---")
                        report_content.append("")
        
        # Save report
        report_path = Path("docs/generated") / "change_detection_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, "w") as f:
            f.write("\n".join(report_content))
        
        logger.info(f"Change report saved to {report_path}")
        return str(report_path)


def main():
    """Main function to run change detection."""
    try:
        detector = DocumentationChangeDetector()
        
        # Detect changes
        changes = detector.detect_all_changes()
        
        # Generate report
        report_path = detector.generate_change_report()
        
        # Print summary
        print("\n" + "="*50)
        print("DOCUMENTATION CHANGE DETECTION")
        print("="*50)
        print(f"Changes Detected: {len(changes)}")
        print(f"Critical: {len([c for c in changes if c.severity == 'critical'])}")
        print(f"Major: {len([c for c in changes if c.severity == 'major'])}")
        print(f"Minor: {len([c for c in changes if c.severity == 'minor'])}")
        print(f"Report: {report_path}")
        print("="*50)
        
        # Exit with appropriate code
        critical_changes = [c for c in changes if c.severity == "critical"]
        if critical_changes:
            print("\n⚠️ Critical changes detected - documentation updates required!")
            exit(1)
        elif changes:
            print("\n📝 Documentation updates recommended")
            exit(0)
        else:
            print("\n✅ No documentation updates needed")
            exit(0)
            
    except Exception as e:
        logger.error(f"Change detection failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()