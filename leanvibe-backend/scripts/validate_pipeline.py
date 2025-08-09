#!/usr/bin/env python3

"""
Autonomous CI/CD Pipeline Validation Script
Validates all workflow configurations, deployment scripts, and branch protection rules
"""

import json
import os
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

def log_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def log_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def log_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def log_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def log_validation(message: str):
    print(f"{Colors.PURPLE}[VALIDATION]{Colors.NC} {message}")

class PipelineValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.validation_results = {
            'workflows': {},
            'scripts': {},
            'configs': {},
            'overall': {'passed': 0, 'failed': 0, 'warnings': 0}
        }

    def validate_yaml_syntax(self, yaml_file: Path) -> Tuple[bool, str]:
        """Validate YAML syntax"""
        try:
            with open(yaml_file, 'r') as f:
                yaml.safe_load(f)
            return True, "Valid YAML syntax"
        except yaml.YAMLError as e:
            return False, f"YAML syntax error: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"

    def validate_json_syntax(self, json_file: Path) -> Tuple[bool, str]:
        """Validate JSON syntax"""
        try:
            with open(json_file, 'r') as f:
                json.load(f)
            return True, "Valid JSON syntax"
        except json.JSONError as e:
            return False, f"JSON syntax error: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"

    def validate_script_executable(self, script_file: Path) -> Tuple[bool, str]:
        """Validate script is executable"""
        if not script_file.exists():
            return False, "File does not exist"
        
        if not os.access(script_file, os.X_OK):
            return False, "File is not executable"
        
        return True, "Script is executable"

    def validate_script_syntax(self, script_file: Path) -> Tuple[bool, str]:
        """Validate shell script syntax"""
        try:
            result = subprocess.run(
                ['bash', '-n', str(script_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, "Valid shell syntax"
            else:
                return False, f"Shell syntax error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Syntax check timeout"
        except Exception as e:
            return False, f"Error checking syntax: {e}"

    def validate_workflow_structure(self, workflow_file: Path) -> Tuple[bool, str]:
        """Validate GitHub Actions workflow structure"""
        try:
            with open(workflow_file, 'r') as f:
                workflow = yaml.safe_load(f)
            
            issues = []
            
            # Check required top-level keys
            # Note: 'on' becomes True in YAML parsing due to YAML boolean interpretation
            required_keys = ['name', 'jobs']
            trigger_key_found = 'on' in workflow or True in workflow
            
            for key in required_keys:
                if key not in workflow:
                    issues.append(f"Missing required key: {key}")
            
            if not trigger_key_found:
                issues.append("Missing workflow trigger configuration ('on' key)")
            
            # Check jobs structure
            if 'jobs' in workflow:
                for job_name, job_config in workflow['jobs'].items():
                    if 'runs-on' not in job_config:
                        issues.append(f"Job '{job_name}' missing 'runs-on'")
                    if 'steps' not in job_config:
                        issues.append(f"Job '{job_name}' missing 'steps'")
            
            # Check for timeout configurations
            timeout_found = False
            for job_name, job_config in workflow.get('jobs', {}).items():
                if 'timeout-minutes' in job_config:
                    timeout_found = True
                    break
            
            if not timeout_found:
                issues.append("No timeout configurations found - jobs may run indefinitely")
            
            if issues:
                return False, "; ".join(issues)
            
            return True, "Valid workflow structure"
            
        except Exception as e:
            return False, f"Error validating workflow: {e}"

    def validate_tiered_test_markers(self, workflow_file: Path) -> Tuple[bool, str]:
        """Validate that workflows use proper tiered test markers"""
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Check for tiered test patterns
            tier_patterns = {
                'tier0': ['-m "unit or contract or type_check"', 'Tier 0', '<60s'],
                'tier1': ['-m "integration or websocket or smoke"', 'Tier 1', '3-5m'],
                'tier2': ['-m "e2e or performance or mutation"', 'Tier 2', '30m'],
                'tier3': ['-m "load or security"', 'Tier 3', '2h']
            }
            
            found_tiers = []
            for tier, patterns in tier_patterns.items():
                for pattern in patterns:
                    if pattern in content:
                        found_tiers.append(tier)
                        break
            
            if not found_tiers:
                return False, "No tiered test patterns found"
            
            return True, f"Found tier patterns: {', '.join(found_tiers)}"
            
        except Exception as e:
            return False, f"Error validating tiers: {e}"

    def validate_autonomous_features(self, workflow_file: Path) -> Tuple[bool, str]:
        """Validate autonomous deployment features"""
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            autonomous_features = {
                'auto_merge': 'auto-merge',
                'canary_deployment': 'canary',
                'rollback': 'rollback',
                'health_checks': 'health',
                'synthetic_probes': 'synthetic',
                'coverage_gate': 'coverage'
            }
            
            found_features = []
            missing_features = []
            
            for feature, pattern in autonomous_features.items():
                if pattern.lower() in content.lower():
                    found_features.append(feature)
                else:
                    missing_features.append(feature)
            
            if len(found_features) >= 4:  # At least 4/6 autonomous features
                message = f"Found features: {', '.join(found_features)}"
                if missing_features:
                    message += f" (missing: {', '.join(missing_features)})"
                return True, message
            else:
                return False, f"Insufficient autonomous features. Found: {', '.join(found_features)}"
                
        except Exception as e:
            return False, f"Error validating autonomous features: {e}"

    def validate_deployment_scripts(self) -> Dict[str, Tuple[bool, str]]:
        """Validate deployment scripts"""
        results = {}
        
        deploy_dir = self.project_root / 'deploy'
        scripts = ['canary.sh', 'rollback.sh', 'synthetic_probes.sh']
        
        for script_name in scripts:
            script_path = deploy_dir / script_name
            log_validation(f"Validating deployment script: {script_name}")
            
            # Check if executable
            executable_result = self.validate_script_executable(script_path)
            if not executable_result[0]:
                results[script_name] = executable_result
                continue
            
            # Check syntax
            syntax_result = self.validate_script_syntax(script_path)
            if not syntax_result[0]:
                results[script_name] = syntax_result
                continue
            
            # Check for required functions/features
            try:
                with open(script_path, 'r') as f:
                    content = f.read()
                
                required_patterns = {
                    'canary.sh': ['validate_inputs', 'deploy_canary', 'health_checks', 'promote_canary'],
                    'rollback.sh': ['find_last_stable', 'rollback_to_stable', 'verify_rollback'],
                    'synthetic_probes.sh': ['http_probe', 'websocket_checks', 'performance_benchmarks']
                }
                
                missing_patterns = []
                for pattern in required_patterns.get(script_name, []):
                    if pattern not in content:
                        missing_patterns.append(pattern)
                
                if missing_patterns:
                    results[script_name] = (False, f"Missing required functions: {', '.join(missing_patterns)}")
                else:
                    results[script_name] = (True, "All required functions present")
                    
            except Exception as e:
                results[script_name] = (False, f"Error validating content: {e}")
        
        return results

    def validate_workflows(self) -> Dict[str, Tuple[bool, str]]:
        """Validate GitHub Actions workflows"""
        results = {}
        
        workflows_dir = self.project_root / '.github' / 'workflows'
        workflow_files = ['autonomous.yml', 'nightly.yml', 'weekly.yml']
        
        for workflow_name in workflow_files:
            workflow_path = workflows_dir / workflow_name
            log_validation(f"Validating workflow: {workflow_name}")
            
            if not workflow_path.exists():
                results[workflow_name] = (False, "File does not exist")
                continue
            
            # Validate YAML syntax
            yaml_result = self.validate_yaml_syntax(workflow_path)
            if not yaml_result[0]:
                results[workflow_name] = yaml_result
                continue
            
            # Validate workflow structure
            structure_result = self.validate_workflow_structure(workflow_path)
            if not structure_result[0]:
                results[workflow_name] = structure_result
                continue
            
            # Validate tiered tests (for appropriate workflows)
            if workflow_name in ['autonomous.yml', 'nightly.yml']:
                tier_result = self.validate_tiered_test_markers(workflow_path)
                if not tier_result[0]:
                    results[workflow_name] = (False, f"Tier validation failed: {tier_result[1]}")
                    continue
            
            # Validate autonomous features (for autonomous.yml)
            if workflow_name == 'autonomous.yml':
                auto_result = self.validate_autonomous_features(workflow_path)
                if not auto_result[0]:
                    results[workflow_name] = (False, f"Autonomous features validation failed: {auto_result[1]}")
                    continue
            
            results[workflow_name] = (True, "All validations passed")
        
        return results

    def validate_configurations(self) -> Dict[str, Tuple[bool, str]]:
        """Validate configuration files"""
        results = {}
        
        config_files = {
            '.github/branch-protection.json': 'json',
            '.github/branch-protection-main.json': 'json',
            '.github/branch-protection-develop.json': 'json',
            '.github/environment-staging.json': 'json',
            '.github/environment-production.json': 'json',
            'docker-compose.staging.yml': 'yaml',
            'docker-compose.production.yml': 'yaml',
            'config/performance_sla.json': 'json'
        }
        
        for config_file, file_type in config_files.items():
            config_path = self.project_root / config_file
            log_validation(f"Validating configuration: {config_file}")
            
            if not config_path.exists():
                results[config_file] = (False, "File does not exist")
                continue
            
            if file_type == 'json':
                result = self.validate_json_syntax(config_path)
            elif file_type == 'yaml':
                result = self.validate_yaml_syntax(config_path)
            else:
                result = (False, "Unknown file type")
            
            results[config_file] = result
        
        return results

    def validate_integration_points(self) -> Tuple[bool, str]:
        """Validate integration between components"""
        issues = []
        
        # Check that deployment scripts are referenced in workflows
        workflows_dir = self.project_root / '.github' / 'workflows'
        autonomous_workflow = workflows_dir / 'autonomous.yml'
        
        if autonomous_workflow.exists():
            try:
                with open(autonomous_workflow, 'r') as f:
                    content = f.read()
                
                required_scripts = ['./deploy/canary.sh', './deploy/rollback.sh', './deploy/synthetic_probes.sh']
                for script in required_scripts:
                    if script not in content:
                        issues.append(f"Deployment script not referenced in autonomous workflow: {script}")
            except Exception as e:
                issues.append(f"Error checking autonomous workflow: {e}")
        
        # Check that Docker Compose files exist for referenced environments
        compose_files = ['docker-compose.staging.yml', 'docker-compose.production.yml']
        for compose_file in compose_files:
            if not (self.project_root / compose_file).exists():
                issues.append(f"Referenced Docker Compose file missing: {compose_file}")
        
        # Check that branch protection configs match workflow requirements
        try:
            branch_protection_path = self.project_root / '.github' / 'branch-protection-main.json'
            if branch_protection_path.exists():
                with open(branch_protection_path, 'r') as f:
                    protection_config = json.load(f)
                
                required_contexts = [
                    "Tier 0: Pre-commit (<60s)",
                    "Coverage Gate (75%)",
                    "Canary Deployment"
                ]
                
                contexts = protection_config.get('required_status_checks', {}).get('contexts', [])
                for required_context in required_contexts:
                    if required_context not in contexts:
                        issues.append(f"Required status check missing from branch protection: {required_context}")
        except Exception as e:
            issues.append(f"Error validating branch protection integration: {e}")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, "All integration points validated"

    def run_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation"""
        log_info("Starting comprehensive pipeline validation...")
        
        # Validate workflows
        log_info("Validating GitHub Actions workflows...")
        self.validation_results['workflows'] = self.validate_workflows()
        
        # Validate deployment scripts
        log_info("Validating deployment scripts...")
        self.validation_results['scripts'] = self.validate_deployment_scripts()
        
        # Validate configurations
        log_info("Validating configuration files...")
        self.validation_results['configs'] = self.validate_configurations()
        
        # Validate integration points
        log_info("Validating integration points...")
        integration_result = self.validate_integration_points()
        self.validation_results['integration'] = integration_result
        
        # Calculate overall results
        for category, results in self.validation_results.items():
            if category == 'overall' or category == 'integration':
                continue
                
            for item, result in results.items():
                if result[0]:
                    self.validation_results['overall']['passed'] += 1
                else:
                    self.validation_results['overall']['failed'] += 1
        
        # Add integration result to overall
        if integration_result[0]:
            self.validation_results['overall']['passed'] += 1
        else:
            self.validation_results['overall']['failed'] += 1
        
        return self.validation_results

    def print_results(self):
        """Print validation results"""
        print(f"\n{Colors.BOLD}=== PIPELINE VALIDATION RESULTS ==={Colors.NC}")
        
        # Workflows
        print(f"\n{Colors.BLUE}GitHub Actions Workflows:{Colors.NC}")
        for workflow, result in self.validation_results['workflows'].items():
            status = f"{Colors.GREEN}✓{Colors.NC}" if result[0] else f"{Colors.RED}✗{Colors.NC}"
            print(f"  {status} {workflow}: {result[1]}")
        
        # Scripts
        print(f"\n{Colors.BLUE}Deployment Scripts:{Colors.NC}")
        for script, result in self.validation_results['scripts'].items():
            status = f"{Colors.GREEN}✓{Colors.NC}" if result[0] else f"{Colors.RED}✗{Colors.NC}"
            print(f"  {status} {script}: {result[1]}")
        
        # Configurations
        print(f"\n{Colors.BLUE}Configuration Files:{Colors.NC}")
        for config, result in self.validation_results['configs'].items():
            status = f"{Colors.GREEN}✓{Colors.NC}" if result[0] else f"{Colors.RED}✗{Colors.NC}"
            print(f"  {status} {config}: {result[1]}")
        
        # Integration
        print(f"\n{Colors.BLUE}Integration Points:{Colors.NC}")
        integration = self.validation_results['integration']
        status = f"{Colors.GREEN}✓{Colors.NC}" if integration[0] else f"{Colors.RED}✗{Colors.NC}"
        print(f"  {status} Component Integration: {integration[1]}")
        
        # Overall summary
        overall = self.validation_results['overall']
        total = overall['passed'] + overall['failed']
        success_rate = (overall['passed'] / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}=== SUMMARY ==={Colors.NC}")
        print(f"Total Checks: {total}")
        print(f"{Colors.GREEN}Passed: {overall['passed']}{Colors.NC}")
        print(f"{Colors.RED}Failed: {overall['failed']}{Colors.NC}")
        print(f"Success Rate: {Colors.GREEN if success_rate >= 90 else Colors.YELLOW if success_rate >= 75 else Colors.RED}{success_rate:.1f}%{Colors.NC}")
        
        if success_rate >= 90:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🚀 Pipeline validation PASSED! Ready for autonomous deployment.{Colors.NC}")
            return 0
        elif success_rate >= 75:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Pipeline validation has warnings. Review failures before deploying.{Colors.NC}")
            return 1
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Pipeline validation FAILED! Fix issues before deploying.{Colors.NC}")
            return 2

def main():
    """Main validation function"""
    project_root = Path(__file__).parent.parent
    
    validator = PipelineValidator(project_root)
    validator.run_validation()
    exit_code = validator.print_results()
    
    # Save results to file
    results_file = project_root / 'test_results' / 'pipeline_validation.json'
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(validator.validation_results, f, indent=2)
    
    log_info(f"Detailed results saved to: {results_file}")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())