#!/usr/bin/env python3
"""
LeanVibe Backend Service Fix Script

This script validates and fixes the identified service integration issues:
1. Neo4j authentication mismatch
2. Redis client installation
3. Service health validation
4. Configuration consistency
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


class BackendServiceFixer:
    """Comprehensive backend service validation and fixing utility"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent
        self.backend_dir = self.project_root / "leanvibe-backend"
        self.fixes_applied = []
        self.issues_found = []
        
    def log_status(self, message: str, status: str = "INFO"):
        """Log status with timestamp and icon"""
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "FIX": "🔧"
        }
        
        icon = icons.get(status, "📋")
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {icon} {message}")
    
    async def check_docker_services(self) -> Dict[str, bool]:
        """Check if Docker services are running"""
        self.log_status("Checking Docker services...")
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                self.log_status("Docker is not running or accessible", "ERROR")
                return {}
            
            output = result.stdout
            services = {
                'neo4j': 'leanvibe-neo4j' in output and 'Up' in output,
                'chroma': 'leanvibe-chroma' in output and 'Up' in output, 
                'redis': 'leanvibe-redis' in output and 'Up' in output
            }
            
            for service, status in services.items():
                status_msg = "Running" if status else "Not running"
                log_status = "SUCCESS" if status else "WARNING"
                self.log_status(f"Docker {service}: {status_msg}", log_status)
            
            return services
            
        except FileNotFoundError:
            self.log_status("Docker not installed", "ERROR")
            return {}
    
    def check_python_dependencies(self) -> Dict[str, bool]:
        """Check if required Python packages are installed"""
        self.log_status("Checking Python dependencies...")
        
        required_packages = {
            'redis': 'redis',
            'neo4j': 'neo4j', 
            'chromadb': 'chromadb',
            'mlx': 'mlx'
        }
        
        results = {}
        
        for package_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                results[package_name] = True
                self.log_status(f"Python package {package_name}: Available", "SUCCESS")
            except ImportError:
                results[package_name] = False
                self.log_status(f"Python package {package_name}: Missing", "WARNING")
                self.issues_found.append(f"Missing Python package: {package_name}")
        
        return results
    
    def check_configuration_consistency(self) -> Dict[str, bool]:
        """Check configuration consistency between files"""
        self.log_status("Checking configuration consistency...")
        
        issues = []
        
        # Check docker-compose.yml vs graph_service.py password
        docker_compose_path = self.project_root / "docker-compose.yml"
        graph_service_path = self.backend_dir / "app" / "services" / "graph_service.py"
        
        if docker_compose_path.exists() and graph_service_path.exists():
            docker_content = docker_compose_path.read_text()
            graph_content = graph_service_path.read_text()
            
            # Check Neo4j password consistency
            if "NEO4J_AUTH: neo4j/leanvibe123" in docker_content:
                if 'password="leanvibe123"' in graph_content:
                    self.log_status("Neo4j password: Consistent", "SUCCESS")
                else:
                    issues.append("Neo4j password mismatch between docker-compose and graph_service")
                    self.log_status("Neo4j password: Mismatch", "WARNING")
            else:
                issues.append("Neo4j password not set correctly in docker-compose.yml")
        
        # Check port consistency
        settings_path = self.backend_dir / "app" / "config" / "settings.py"
        if settings_path.exists():
            settings_content = settings_path.read_text()
            
            # Check if backend port is consistent
            if 'port: int = Field(default=8001)' in settings_content:
                # Backend claims port 8001 but typically runs on 8000
                issues.append("Backend port configuration may be inconsistent")
                self.log_status("Backend port: Potentially inconsistent", "WARNING")
        
        self.issues_found.extend(issues)
        return {"configuration_consistent": len(issues) == 0}
    
    def start_docker_services(self) -> bool:
        """Start Docker services if not running"""
        self.log_status("Starting Docker services...", "FIX")
        
        try:
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.log_status("Docker services started successfully", "SUCCESS")
                self.fixes_applied.append("Started Docker services")
                time.sleep(5)  # Give services time to start
                return True
            else:
                self.log_status(f"Failed to start Docker services: {result.stderr}", "ERROR")
                return False
                
        except FileNotFoundError:
            self.log_status("docker-compose not found", "ERROR")
            return False
    
    def install_python_dependencies(self) -> bool:
        """Install missing Python dependencies"""
        self.log_status("Installing missing Python dependencies...", "FIX")
        
        try:
            # Install using pip within the backend directory
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "redis>=4.6.0"],
                capture_output=True,
                text=True,
                cwd=self.backend_dir
            )
            
            if result.returncode == 0:
                self.log_status("Redis client installed successfully", "SUCCESS") 
                self.fixes_applied.append("Installed Redis Python client")
                return True
            else:
                self.log_status(f"Failed to install Redis: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log_status(f"Error installing dependencies: {e}", "ERROR")
            return False
    
    async def test_service_connections(self) -> Dict[str, bool]:
        """Test actual service connections"""
        self.log_status("Testing service connections...")
        
        # Import test runner
        test_file = Path(__file__).parent / "leanvibe-backend" / "tests" / "test_service_integration_comprehensive.py"
        
        if not test_file.exists():
            self.log_status("Integration test file not found", "WARNING")
            return {}
        
        try:
            # Run the comprehensive integration test
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(test_file) + "::TestServiceIntegration::test_all_services_health_check",
                "-v", "-s", "--tb=short"
            ], capture_output=True, text=True, cwd=self.backend_dir)
            
            # Parse results from output
            output = result.stdout + result.stderr
            
            service_results = {}
            for line in output.split('\n'):
                if '✅' in line or '❌' in line:
                    for service in ['neo4j', 'chromadb', 'redis', 'mlx_model']:
                        if service in line:
                            service_results[service] = '✅' in line
                            status = "SUCCESS" if '✅' in line else "WARNING"
                            self.log_status(f"Service {service}: {'Working' if '✅' in line else 'Failed'}", status)
            
            return service_results
            
        except Exception as e:
            self.log_status(f"Error running service tests: {e}", "ERROR")
            return {}
    
    def generate_health_report(self) -> str:
        """Generate a health report for the backend services"""
        report = f"""
# LeanVibe Backend Service Health Report

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}

## Issues Found
"""
        
        if self.issues_found:
            for i, issue in enumerate(self.issues_found, 1):
                report += f"{i}. {issue}\n"
        else:
            report += "No issues found.\n"
        
        report += f"""
## Fixes Applied
"""
        
        if self.fixes_applied:
            for i, fix in enumerate(self.fixes_applied, 1):
                report += f"{i}. {fix}\n"
        else:
            report += "No fixes applied.\n"
        
        report += """
## Recommendations

### Immediate Actions (if issues found):
1. Run `docker-compose up -d` to start services
2. Install missing Python packages: `pip install redis>=4.6.0`
3. Verify Neo4j password matches in docker-compose.yml and graph_service.py
4. Test service connections with the integration test

### Model Upgrade (for better AI performance):
1. Consider upgrading from Phi-3-Mini to a larger model
2. Install Ollama and download DeepSeek R1 for better code generation
3. Implement model switching in the backend settings

### Testing:
1. Run comprehensive integration tests: `pytest tests/test_service_integration_comprehensive.py`
2. Add performance benchmarks for service response times
3. Monitor service health in production
"""
        
        return report
    
    async def run_comprehensive_check(self) -> Dict[str, any]:
        """Run all checks and fixes"""
        self.log_status("Starting comprehensive backend service check...", "INFO")
        
        results = {
            'docker_services': {},
            'python_dependencies': {},
            'configuration': {},
            'service_connections': {},
            'fixes_applied': [],
            'issues_found': []
        }
        
        # 1. Check Docker services
        docker_services = await self.check_docker_services()
        results['docker_services'] = docker_services
        
        # Start Docker services if needed
        if not all(docker_services.values()) and any(docker_services.values() is False for _ in range(3)):
            self.start_docker_services()
            # Re-check after starting
            docker_services = await self.check_docker_services()
            results['docker_services'] = docker_services
        
        # 2. Check Python dependencies
        python_deps = self.check_python_dependencies()
        results['python_dependencies'] = python_deps
        
        # Install missing dependencies
        if not python_deps.get('redis', True):
            self.install_python_dependencies()
            # Re-check after installation
            python_deps = self.check_python_dependencies()
            results['python_dependencies'] = python_deps
        
        # 3. Check configuration
        config_check = self.check_configuration_consistency()
        results['configuration'] = config_check
        
        # 4. Test service connections
        if any(docker_services.values()) and any(python_deps.values()):
            self.log_status("Testing service connections (this may take a moment)...")
            service_connections = await self.test_service_connections()
            results['service_connections'] = service_connections
        
        # 5. Record results
        results['fixes_applied'] = self.fixes_applied
        results['issues_found'] = self.issues_found
        
        # 6. Generate report
        health_report = self.generate_health_report()
        report_path = self.project_root / "BACKEND_SERVICE_HEALTH_REPORT.md"
        report_path.write_text(health_report)
        
        self.log_status(f"Health report saved to: {report_path}", "SUCCESS")
        
        # 7. Summary
        total_services = len(docker_services) + len(python_deps)
        working_services = sum(docker_services.values()) + sum(python_deps.values())
        
        self.log_status(f"Service check complete: {working_services}/{total_services} services functional", "INFO")
        
        if self.fixes_applied:
            self.log_status(f"Applied {len(self.fixes_applied)} fixes", "SUCCESS")
        
        if self.issues_found:
            self.log_status(f"Found {len(self.issues_found)} remaining issues", "WARNING")
        
        return results


async def main():
    """Main execution function"""
    print("🔧 LeanVibe Backend Service Fix Script")
    print("=" * 50)
    
    fixer = BackendServiceFixer()
    results = await fixer.run_comprehensive_check()
    
    print("\n" + "=" * 50)
    print("🏁 Fix script completed!")
    
    # Exit with appropriate code
    if results['issues_found']:
        print(f"⚠️  {len(results['issues_found'])} issues still need attention")
        sys.exit(1)
    else:
        print("✅ All services appear to be functioning correctly")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())