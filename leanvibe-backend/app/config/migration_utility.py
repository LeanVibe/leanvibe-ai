"""
Configuration Migration Utility

Helps migrate from scattered configuration patterns to the unified configuration system.
Provides validation, compatibility testing, and migration reporting.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .unified_config import (
    UnifiedConfig,
    ConfigurationService,
    DefaultValues,
    EnvironmentVariables,
    get_config,
)

logger = logging.getLogger(__name__)


class ConfigMigrationUtility:
    """Utility for migrating to unified configuration system"""
    
    def __init__(self):
        self.legacy_patterns = {
            "backend_urls": [],
            "model_configs": [],
            "env_vars": [],
            "hardcoded_defaults": [],
            "config_classes": []
        }
        self.migration_results = {}
    
    def scan_legacy_patterns(self, project_root: str) -> Dict[str, Any]:
        """Scan codebase for legacy configuration patterns"""
        results = {
            "legacy_patterns_found": [],
            "duplicated_values": [],
            "environment_vars": [],
            "config_files": [],
            "issues": []
        }
        
        project_path = Path(project_root)
        
        # Common legacy patterns to detect
        backend_url_patterns = [
            '"http://localhost:8000"',
            "'http://localhost:8000'",
            "localhost:8000",
            "127.0.0.1:8000"
        ]
        
        model_config_patterns = [
            "class ModelConfig",
            "ModelConfig(",
            "@dataclass",
            "model_name =",
            "temperature =",
            "max_tokens ="
        ]
        
        env_var_patterns = [
            "os.getenv(",
            "os.environ.get(",
            "LEANVIBE_",
            "getenv("
        ]
        
        # Scan Python files
        for py_file in project_path.rglob("*.py"):
            if any(skip in str(py_file) for skip in ["__pycache__", ".git", "node_modules"]):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for backend URL patterns
                for pattern in backend_url_patterns:
                    if pattern in content:
                        results["legacy_patterns_found"].append({
                            "file": str(py_file),
                            "pattern": pattern,
                            "type": "backend_url",
                            "line_count": content.count(pattern)
                        })
                
                # Check for model config patterns
                for pattern in model_config_patterns:
                    if pattern in content:
                        results["legacy_patterns_found"].append({
                            "file": str(py_file),
                            "pattern": pattern,
                            "type": "model_config",
                            "line_count": content.count(pattern)
                        })
                
                # Check for environment variable patterns
                for pattern in env_var_patterns:
                    if pattern in content:
                        results["legacy_patterns_found"].append({
                            "file": str(py_file),
                            "pattern": pattern,
                            "type": "env_var",
                            "line_count": content.count(pattern)
                        })
                        
            except Exception as e:
                results["issues"].append({
                    "file": str(py_file),
                    "error": str(e),
                    "type": "scan_error"
                })
        
        # Scan YAML files
        for yaml_file in project_path.rglob("*.yml"):
            try:
                content = yaml_file.read_text(encoding='utf-8')
                if "backend_url" in content or "localhost:8000" in content:
                    results["config_files"].append({
                        "file": str(yaml_file),
                        "type": "yaml_config"
                    })
            except Exception as e:
                results["issues"].append({
                    "file": str(yaml_file),
                    "error": str(e),
                    "type": "yaml_scan_error"
                })
        
        return results
    
    def validate_unified_config(self) -> Dict[str, Any]:
        """Validate the unified configuration system"""
        validation_results = {
            "config_status": "unknown",
            "validation_tests": [],
            "compatibility_issues": [],
            "recommendations": []
        }
        
        try:
            # Test configuration loading
            config = get_config()
            
            validation_results["validation_tests"].append({
                "test": "config_loading",
                "status": "success",
                "message": "Unified config loaded successfully"
            })
            
            # Test environment variable loading
            try:
                env_config = UnifiedConfig.from_env()
                validation_results["validation_tests"].append({
                    "test": "env_loading",
                    "status": "success",
                    "message": "Environment config loaded successfully"
                })
            except Exception as e:
                validation_results["validation_tests"].append({
                    "test": "env_loading",
                    "status": "error",
                    "message": f"Environment config loading failed: {str(e)}"
                })
            
            # Test configuration validation
            try:
                validation_result = ConfigurationService().validate_config()
                validation_results["validation_tests"].append({
                    "test": "config_validation",
                    "status": "success" if validation_result["valid"] else "warning",
                    "message": f"Config validation completed with {len(validation_result['errors'])} errors, {len(validation_result['warnings'])} warnings"
                })
            except Exception as e:
                validation_results["validation_tests"].append({
                    "test": "config_validation", 
                    "status": "error",
                    "message": f"Config validation failed: {str(e)}"
                })
            
            # Test backward compatibility
            try:
                backend_url = config.get_backend_url()
                model_config = config.get_model_config()
                dev_mode = config.is_development_mode()
                
                validation_results["validation_tests"].append({
                    "test": "backward_compatibility",
                    "status": "success",
                    "message": "Legacy compatibility functions working"
                })
            except Exception as e:
                validation_results["compatibility_issues"].append({
                    "issue": "legacy_functions",
                    "error": str(e)
                })
            
            # Determine overall status
            failed_tests = [t for t in validation_results["validation_tests"] if t["status"] == "error"]
            if len(failed_tests) == 0:
                validation_results["config_status"] = "success"
                validation_results["recommendations"].append("Unified configuration system is ready for production")
            elif len(failed_tests) <= 1:
                validation_results["config_status"] = "warning"
                validation_results["recommendations"].append("Minor issues found - review before deployment")
            else:
                validation_results["config_status"] = "failed"
                validation_results["recommendations"].append("Multiple issues found - fix before proceeding")
            
            # Add migration recommendations
            validation_results["recommendations"].extend([
                "Update service imports to use unified configuration",
                "Replace hardcoded defaults with unified constants",
                "Migrate environment variable loading to unified system",
                "Update tests to use unified configuration patterns"
            ])
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            validation_results["config_status"] = "error"
            validation_results["compatibility_issues"].append({
                "issue": "validation_error",
                "error": str(e)
            })
        
        return validation_results
    
    def generate_migration_report(self, scan_results: Dict[str, Any], validation_results: Dict[str, Any]) -> str:
        """Generate comprehensive migration report"""
        
        status_icons = {
            "success": "✅",
            "warning": "⚠️", 
            "failed": "❌",
            "error": "💥",
            "unknown": "❓"
        }
        
        config_status = validation_results.get("config_status", "unknown")
        icon = status_icons.get(config_status, "❓")
        
        # Count legacy patterns by type
        pattern_counts = {}
        for pattern in scan_results.get("legacy_patterns_found", []):
            pattern_type = pattern["type"]
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
        
        report = f"""🔧 Configuration System Migration Report

{icon} Migration Status: {config_status.upper()}

📊 Legacy Pattern Analysis:
• Backend URL patterns found: {pattern_counts.get('backend_url', 0)} instances
• Model config patterns found: {pattern_counts.get('model_config', 0)} instances  
• Environment variable patterns found: {pattern_counts.get('env_var', 0)} instances
• Configuration files found: {len(scan_results.get('config_files', []))}

🧪 Validation Tests:
"""
        
        for test in validation_results.get("validation_tests", []):
            test_icon = status_icons.get(test["status"], "❓")
            report += f"• {test_icon} {test['test']}: {test['message']}\n"
        
        if validation_results.get("compatibility_issues"):
            report += f"""
⚠️ Compatibility Issues ({len(validation_results["compatibility_issues"])}):
{chr(10).join(f'• {issue["issue"]}: {issue["error"]}' for issue in validation_results["compatibility_issues"])}
"""
        
        if scan_results.get("issues"):
            report += f"""
❌ Scan Issues ({len(scan_results["issues"])}):
{chr(10).join(f'• {issue["file"]}: {issue["error"]}' for issue in scan_results["issues"][:5])}
"""
            if len(scan_results["issues"]) > 5:
                report += f"• ... and {len(scan_results['issues']) - 5} more issues\n"
        
        report += f"""
💡 Recommendations:
{chr(10).join(f'• {rec}' for rec in validation_results.get("recommendations", []))}

🏗️ Unified Configuration Benefits:
• Single source of truth for all configuration
• Centralized environment variable management
• Pydantic validation for type safety and data validation
• Backward compatibility with legacy interfaces
• Reduced code duplication and maintenance overhead

🚀 Migration Steps:
1. Replace hardcoded defaults with DefaultValues constants
2. Update environment variable loading to use EnvironmentVariables
3. Replace legacy ModelConfig with unified ModelConfig
4. Update service imports to use unified configuration
5. Update tests to use unified configuration patterns
6. Validate configuration in all environments

📈 Expected Impact:
• {pattern_counts.get('backend_url', 0)} duplicate backend URL definitions eliminated
• {pattern_counts.get('model_config', 0)} model config duplications consolidated
• Centralized management of {len(set(p['pattern'] for p in scan_results.get('legacy_patterns_found', []) if 'LEANVIBE_' in p['pattern']))} environment variables
• Single configuration validation point

📋 Next Actions:
• Review and fix validation issues before deployment
• Update imports in services to use unified configuration
• Create migration scripts for configuration file updates
• Test configuration loading in all deployment environments
"""
        
        return report
    
    def get_migration_checklist(self) -> List[str]:
        """Get checklist for configuration migration"""
        return [
            "✅ Create unified configuration system with Pydantic models",
            "✅ Centralize default values in DefaultValues class",
            "✅ Unify environment variable management",
            "⏳ Replace hardcoded backend URLs with unified config",
            "⏳ Update ModelConfig usage across services",
            "⏳ Migrate CLI configuration to use unified system",
            "⏳ Update environment variable loading patterns",
            "⏳ Replace duplicate configuration classes",
            "⏳ Update tests to use unified configuration",
            "⏳ Validate configuration in all environments",
            "⏳ Update documentation for new configuration system",
            "⏳ Create migration guide for developers"
        ]


# Global migration utility instance
config_migration_utility = ConfigMigrationUtility()