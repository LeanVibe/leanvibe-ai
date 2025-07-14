#!/usr/bin/env python3
"""
LeanVibe Security Audit and Production Hardening Script

Comprehensive security assessment and hardening for LeanVibe MVP.
Focuses on defensive security, vulnerability detection, and production readiness.
"""

import os
import re
import json
import subprocess
import asyncio
import hashlib
import socket
import ssl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class SecurityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class SecurityFinding:
    category: str
    level: SecurityLevel
    title: str
    description: str
    file_path: str = ""
    line_number: int = 0
    recommendation: str = ""
    cve_references: List[str] = None
    remediation_code: str = ""

class LeanVibeSecurityAudit:
    """Comprehensive security audit for LeanVibe MVP"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.findings: List[SecurityFinding] = []
        self.scan_results = {}
        
    async def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        print("🔒 LeanVibe Security Audit & Production Hardening")
        print("=" * 60)
        
        audit_categories = [
            ("Code Security", self.audit_code_security),
            ("Dependency Security", self.audit_dependencies),
            ("Configuration Security", self.audit_configuration),
            ("Network Security", self.audit_network_security),
            ("Data Protection", self.audit_data_protection),
            ("Authentication & Authorization", self.audit_auth),
            ("Input Validation", self.audit_input_validation),
            ("Error Handling", self.audit_error_handling),
            ("Logging & Monitoring", self.audit_logging),
            ("Production Hardening", self.audit_production_hardening)
        ]
        
        for category, audit_func in audit_categories:
            print(f"\n🔍 Auditing: {category}")
            try:
                results = await audit_func()
                self.scan_results[category] = results
                print(f"✅ {category}: {len(results.get('findings', []))} findings")
            except Exception as e:
                print(f"❌ {category}: Error - {str(e)}")
                self.scan_results[category] = {"error": str(e), "findings": []}
        
        # Generate security report
        report = self.generate_security_report()
        
        # Apply automated fixes
        hardening_results = await self.apply_security_hardening()
        
        # Final assessment
        security_score = self.calculate_security_score()
        
        print(f"\n🔒 Security Audit Complete")
        print(f"Security Score: {security_score}/100")
        print(f"Critical Issues: {len([f for f in self.findings if f.level == SecurityLevel.CRITICAL])}")
        print(f"High Priority: {len([f for f in self.findings if f.level == SecurityLevel.HIGH])}")
        print(f"Production Ready: {'YES' if security_score >= 80 else 'NO'}")
        
        return {
            "security_score": security_score,
            "findings": [self.finding_to_dict(f) for f in self.findings],
            "scan_results": self.scan_results,
            "hardening_applied": hardening_results,
            "production_ready": security_score >= 80,
            "audit_timestamp": datetime.now().isoformat(),
            "summary": report
        }
    
    async def audit_code_security(self) -> Dict[str, Any]:
        """Audit code for security vulnerabilities"""
        findings = []
        
        # Scan Python files for common security issues
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                file_findings = self.scan_python_file(file_path, content)
                findings.extend(file_findings)
            except Exception as e:
                print(f"Warning: Could not scan {file_path}: {e}")
        
        # Scan for hardcoded secrets
        secret_findings = self.scan_for_secrets()
        findings.extend(secret_findings)
        
        # Scan for SQL injection patterns
        sql_findings = self.scan_for_sql_injection()
        findings.extend(sql_findings)
        
        self.findings.extend(findings)
        return {"findings": findings, "files_scanned": len(python_files)}
    
    async def audit_dependencies(self) -> Dict[str, Any]:
        """Audit dependencies for known vulnerabilities"""
        findings = []
        
        # Check requirements files
        req_files = list(self.project_root.rglob("requirements*.txt")) + \
                   list(self.project_root.rglob("pyproject.toml"))
        
        for req_file in req_files:
            try:
                vuln_findings = await self.check_dependency_vulnerabilities(req_file)
                findings.extend(vuln_findings)
            except Exception as e:
                print(f"Warning: Could not check {req_file}: {e}")
        
        # Check for outdated packages
        outdated_findings = await self.check_outdated_packages()
        findings.extend(outdated_findings)
        
        self.findings.extend(findings)
        return {"findings": findings, "dependency_files": len(req_files)}
    
    async def audit_configuration(self) -> Dict[str, Any]:
        """Audit configuration security"""
        findings = []
        
        # Check environment configurations
        env_findings = self.audit_environment_config()
        findings.extend(env_findings)
        
        # Check file permissions
        permission_findings = self.audit_file_permissions()
        findings.extend(permission_findings)
        
        # Check configuration files
        config_findings = self.audit_config_files()
        findings.extend(config_findings)
        
        self.findings.extend(findings)
        return {"findings": findings}
    
    async def audit_network_security(self) -> Dict[str, Any]:
        """Audit network security configuration"""
        findings = []
        
        # Check HTTPS configuration
        https_findings = self.audit_https_config()
        findings.extend(https_findings)
        
        # Check CORS configuration
        cors_findings = self.audit_cors_config()
        findings.extend(cors_findings)
        
        # Check WebSocket security
        ws_findings = self.audit_websocket_security()
        findings.extend(ws_findings)
        
        self.findings.extend(findings)
        return {"findings": findings}
    
    async def audit_data_protection(self) -> Dict[str, Any]:
        """Audit data protection measures"""
        findings = []
        
        # Check for PII handling
        pii_findings = self.audit_pii_handling()
        findings.extend(pii_findings)
        
        # Check encryption usage
        encryption_findings = self.audit_encryption()
        findings.extend(encryption_findings)
        
        # Check data validation
        validation_findings = self.audit_data_validation()
        findings.extend(validation_findings)
        
        self.findings.extend(findings)
        return {"findings": findings}
    
    async def audit_auth(self) -> Dict[str, Any]:
        """Audit authentication and authorization"""
        findings = []
        
        # Check authentication mechanisms
        auth_findings = self.audit_authentication()
        findings.extend(auth_findings)
        
        # Check authorization controls
        authz_findings = self.audit_authorization()
        findings.extend(authz_findings)
        
        # Check session management
        session_findings = self.audit_session_management()
        findings.extend(session_findings)
        
        self.findings.extend(findings)
        return {"findings": findings}
    
    async def audit_input_validation(self) -> Dict[str, Any]:
        """Audit input validation and sanitization"""
        findings = []
        
        # Scan for input validation patterns
        validation_findings = self.scan_input_validation()
        findings.extend(validation_findings)
        
        # Check for XSS prevention
        xss_findings = self.audit_xss_prevention()
        findings.extend(xss_findings)
        
        self.findings.extend(findings)
        return {"findings": findings}
    
    async def audit_error_handling(self) -> Dict[str, Any]:
        """Audit error handling security"""
        findings = []
        
        # Check for information disclosure in errors
        error_findings = self.audit_error_disclosure()
        findings.extend(error_findings)
        
        # Check exception handling
        exception_findings = self.audit_exception_handling()
        findings.extend(exception_findings)
        
        self.findings.extend(findings)
        return {"findings": findings}
    
    async def audit_logging(self) -> Dict[str, Any]:
        """Audit logging and monitoring"""
        findings = []
        
        # Check logging configuration
        log_findings = self.audit_logging_config()
        findings.extend(log_findings)
        
        # Check for sensitive data in logs
        sensitive_findings = self.audit_log_sensitivity()
        findings.extend(sensitive_findings)
        
        self.findings.extend(findings)
        return {"findings": findings}
    
    async def audit_production_hardening(self) -> Dict[str, Any]:
        """Audit production hardening measures"""
        findings = []
        
        # Check debug settings
        debug_findings = self.audit_debug_settings()
        findings.extend(debug_findings)
        
        # Check security headers
        header_findings = self.audit_security_headers()
        findings.extend(header_findings)
        
        # Check rate limiting
        rate_findings = self.audit_rate_limiting()
        findings.extend(rate_findings)
        
        self.findings.extend(findings)
        return {"findings": findings}
    
    def scan_python_file(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """Scan Python file for security issues"""
        findings = []
        lines = content.split('\n')
        
        security_patterns = [
            # Dangerous functions
            (r'eval\s*\(', SecurityLevel.CRITICAL, "Use of eval() function", 
             "Avoid eval() as it can execute arbitrary code"),
            (r'exec\s*\(', SecurityLevel.CRITICAL, "Use of exec() function",
             "Avoid exec() as it can execute arbitrary code"),
            (r'subprocess\.(call|run|Popen).*shell=True', SecurityLevel.HIGH, 
             "Shell injection vulnerability", "Avoid shell=True in subprocess calls"),
            (r'os\.system\s*\(', SecurityLevel.HIGH, "OS command execution",
             "Use subprocess with proper argument handling instead"),
            
            # Crypto issues
            (r'hashlib\.md5\s*\(', SecurityLevel.MEDIUM, "Weak hash algorithm MD5",
             "Use SHA-256 or stronger hash algorithms"),
            (r'hashlib\.sha1\s*\(', SecurityLevel.MEDIUM, "Weak hash algorithm SHA1",
             "Use SHA-256 or stronger hash algorithms"),
            
            # Random issues
            (r'random\.random\s*\(', SecurityLevel.LOW, "Weak random number generation",
             "Use secrets module for cryptographic randomness"),
            
            # File operations
            (r'open\s*\([^)]*["\']w["\']', SecurityLevel.LOW, "File write operation",
             "Ensure proper file path validation"),
            
            # Network issues
            (r'ssl\..*PROTOCOL_SSLv\d', SecurityLevel.HIGH, "Deprecated SSL protocol",
             "Use TLS 1.2 or higher"),
            (r'verify=False', SecurityLevel.HIGH, "SSL verification disabled",
             "Always verify SSL certificates"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, level, title, recommendation in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(SecurityFinding(
                        category="Code Security",
                        level=level,
                        title=title,
                        description=f"Found in line {i}: {line.strip()}",
                        file_path=str(file_path),
                        line_number=i,
                        recommendation=recommendation
                    ))
        
        return findings
    
    def scan_for_secrets(self) -> List[SecurityFinding]:
        """Scan for hardcoded secrets"""
        findings = []
        
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', SecurityLevel.CRITICAL, "Hardcoded password"),
            (r'api[_-]?key\s*=\s*["\'][^"\']{16,}["\']', SecurityLevel.CRITICAL, "Hardcoded API key"),
            (r'secret[_-]?key\s*=\s*["\'][^"\']{16,}["\']', SecurityLevel.CRITICAL, "Hardcoded secret key"),
            (r'token\s*=\s*["\'][^"\']{16,}["\']', SecurityLevel.HIGH, "Hardcoded token"),
            (r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']', SecurityLevel.MEDIUM, "Potential base64 encoded secret"),
        ]
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, level, title in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(SecurityFinding(
                                category="Secrets",
                                level=level,
                                title=title,
                                description=f"Potential hardcoded secret in line {i}",
                                file_path=str(file_path),
                                line_number=i,
                                recommendation="Use environment variables or secure secret management"
                            ))
            except Exception:
                continue
        
        return findings
    
    def scan_for_sql_injection(self) -> List[SecurityFinding]:
        """Scan for SQL injection vulnerabilities"""
        findings = []
        
        sql_patterns = [
            (r'execute\s*\([^)]*%[sf][^)]*\)', SecurityLevel.HIGH, "Potential SQL injection"),
            (r'query\s*\([^)]*\+[^)]*\)', SecurityLevel.MEDIUM, "String concatenation in SQL"),
            (r'\.format\s*\([^)]*SELECT', SecurityLevel.MEDIUM, "String formatting in SQL"),
        ]
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, level, title in sql_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(SecurityFinding(
                                category="SQL Injection",
                                level=level,
                                title=title,
                                description=f"Found in line {i}: {line.strip()}",
                                file_path=str(file_path),
                                line_number=i,
                                recommendation="Use parameterized queries or ORM"
                            ))
            except Exception:
                continue
        
        return findings
    
    async def check_dependency_vulnerabilities(self, req_file: Path) -> List[SecurityFinding]:
        """Check dependencies for known vulnerabilities"""
        findings = []
        
        # For MVP, we'll do basic checks
        # In production, integrate with tools like safety, bandit, or snyk
        
        try:
            if req_file.name == "pyproject.toml":
                # Parse pyproject.toml for dependencies
                content = req_file.read_text()
                if "dependencies" in content:
                    findings.append(SecurityFinding(
                        category="Dependencies",
                        level=SecurityLevel.INFO,
                        title="Dependency file found",
                        description=f"Found dependency file: {req_file}",
                        file_path=str(req_file),
                        recommendation="Regularly audit dependencies with safety or similar tools"
                    ))
            else:
                # Parse requirements.txt
                content = req_file.read_text()
                packages = [line.strip() for line in content.split('\n') 
                          if line.strip() and not line.startswith('#')]
                
                # Check for packages without version pinning
                for line_num, package in enumerate(packages, 1):
                    if package and '==' not in package and '>=' not in package and '<=' not in package:
                        findings.append(SecurityFinding(
                            category="Dependencies",
                            level=SecurityLevel.MEDIUM,
                            title="Unpinned dependency version",
                            description=f"Package '{package}' has no version constraint",
                            file_path=str(req_file),
                            line_number=line_num,
                            recommendation="Pin dependency versions for security and reproducibility"
                        ))
        except Exception as e:
            findings.append(SecurityFinding(
                category="Dependencies",
                level=SecurityLevel.LOW,
                title="Could not parse dependency file",
                description=f"Error parsing {req_file}: {str(e)}",
                file_path=str(req_file),
                recommendation="Ensure dependency files are properly formatted"
            ))
        
        return findings
    
    async def check_outdated_packages(self) -> List[SecurityFinding]:
        """Check for outdated packages"""
        findings = []
        
        try:
            # Run pip list --outdated (simplified check)
            result = subprocess.run(['pip', 'list', '--outdated'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                outdated_count = len(result.stdout.strip().split('\n')) - 2  # Exclude header
                if outdated_count > 0:
                    findings.append(SecurityFinding(
                        category="Dependencies",
                        level=SecurityLevel.MEDIUM,
                        title=f"{outdated_count} outdated packages found",
                        description="Outdated packages may contain security vulnerabilities",
                        recommendation="Update packages regularly and monitor for security advisories"
                    ))
        except Exception:
            findings.append(SecurityFinding(
                category="Dependencies",
                level=SecurityLevel.INFO,
                title="Could not check for outdated packages",
                description="pip list --outdated command failed",
                recommendation="Manually check for package updates"
            ))
        
        return findings
    
    def audit_environment_config(self) -> List[SecurityFinding]:
        """Audit environment configuration"""
        findings = []
        
        # Check for .env files
        env_files = list(self.project_root.rglob(".env*"))
        for env_file in env_files:
            if env_file.name != ".env.example":
                findings.append(SecurityFinding(
                    category="Configuration",
                    level=SecurityLevel.HIGH,
                    title="Environment file found",
                    description=f"Environment file {env_file} may contain secrets",
                    file_path=str(env_file),
                    recommendation="Ensure .env files are in .gitignore and not committed"
                ))
        
        # Check for debug settings in code
        debug_patterns = [
            r'DEBUG\s*=\s*True',
            r'debug\s*=\s*True',
            r'--debug',
        ]
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern in debug_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(SecurityFinding(
                                category="Configuration",
                                level=SecurityLevel.MEDIUM,
                                title="Debug mode enabled",
                                description=f"Debug setting found in line {i}",
                                file_path=str(file_path),
                                line_number=i,
                                recommendation="Disable debug mode in production"
                            ))
            except Exception:
                continue
        
        return findings
    
    def audit_file_permissions(self) -> List[SecurityFinding]:
        """Audit file permissions"""
        findings = []
        
        # Check for overly permissive files
        sensitive_files = [
            "*.key", "*.pem", "*.p12", "*.pfx", 
            ".env*", "config.py", "settings.py"
        ]
        
        for pattern in sensitive_files:
            for file_path in self.project_root.rglob(pattern):
                try:
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]
                    
                    # Check if file is world-readable
                    if mode[-1] in ['4', '5', '6', '7']:
                        findings.append(SecurityFinding(
                            category="File Permissions",
                            level=SecurityLevel.MEDIUM,
                            title="World-readable sensitive file",
                            description=f"File {file_path} has permissions {mode}",
                            file_path=str(file_path),
                            recommendation="Restrict file permissions (chmod 600 or 640)"
                        ))
                except Exception:
                    continue
        
        return findings
    
    def audit_config_files(self) -> List[SecurityFinding]:
        """Audit configuration files"""
        findings = []
        
        config_files = list(self.project_root.rglob("*.ini")) + \
                      list(self.project_root.rglob("*.conf")) + \
                      list(self.project_root.rglob("config.py"))
        
        for config_file in config_files:
            try:
                content = config_file.read_text(encoding='utf-8')
                
                # Check for sensitive data in config
                sensitive_patterns = [
                    (r'password\s*[:=]\s*\S+', "Password in config file"),
                    (r'secret\s*[:=]\s*\S+', "Secret in config file"),
                    (r'key\s*[:=]\s*\S{16,}', "API key in config file"),
                ]
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    for pattern, title in sensitive_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(SecurityFinding(
                                category="Configuration",
                                level=SecurityLevel.HIGH,
                                title=title,
                                description=f"Found in line {i}",
                                file_path=str(config_file),
                                line_number=i,
                                recommendation="Use environment variables for sensitive configuration"
                            ))
            except Exception:
                continue
        
        return findings
    
    def audit_https_config(self) -> List[SecurityFinding]:
        """Audit HTTPS configuration"""
        findings = []
        
        # Scan for HTTP URLs
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Look for HTTP URLs (excluding localhost)
                    if re.search(r'http://(?!localhost|127\.0\.0\.1)', line, re.IGNORECASE):
                        findings.append(SecurityFinding(
                            category="Network Security",
                            level=SecurityLevel.MEDIUM,
                            title="HTTP URL found",
                            description=f"Insecure HTTP URL in line {i}",
                            file_path=str(file_path),
                            line_number=i,
                            recommendation="Use HTTPS for all external communications"
                        ))
            except Exception:
                continue
        
        return findings
    
    def audit_cors_config(self) -> List[SecurityFinding]:
        """Audit CORS configuration"""
        findings = []
        
        # Look for CORS configuration
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for overly permissive CORS
                if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                    findings.append(SecurityFinding(
                        category="Network Security",
                        level=SecurityLevel.MEDIUM,
                        title="Permissive CORS configuration",
                        description="CORS allows all origins (*)",
                        file_path=str(file_path),
                        recommendation="Restrict CORS to specific trusted origins"
                    ))
                    
                if 'allow_credentials=True' in content and ('allow_origins=["*"]' in content or "allow_origins=['*']" in content):
                    findings.append(SecurityFinding(
                        category="Network Security",
                        level=SecurityLevel.HIGH,
                        title="Dangerous CORS configuration",
                        description="CORS allows credentials with wildcard origins",
                        file_path=str(file_path),
                        recommendation="Never use allow_credentials=True with wildcard origins"
                    ))
            except Exception:
                continue
        
        return findings
    
    def audit_websocket_security(self) -> List[SecurityFinding]:
        """Audit WebSocket security"""
        findings = []
        
        # Check WebSocket implementation
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for WebSocket security patterns
                if 'websocket' in content.lower():
                    if 'origin' not in content.lower():
                        findings.append(SecurityFinding(
                            category="Network Security",
                            level=SecurityLevel.MEDIUM,
                            title="WebSocket origin validation missing",
                            description="WebSocket implementation may lack origin validation",
                            file_path=str(file_path),
                            recommendation="Implement WebSocket origin validation"
                        ))
                    
                    if 'ws://' in content and 'localhost' not in content:
                        findings.append(SecurityFinding(
                            category="Network Security",
                            level=SecurityLevel.HIGH,
                            title="Insecure WebSocket protocol",
                            description="Using ws:// instead of wss://",
                            file_path=str(file_path),
                            recommendation="Use wss:// for secure WebSocket connections"
                        ))
            except Exception:
                continue
        
        return findings
    
    def audit_pii_handling(self) -> List[SecurityFinding]:
        """Audit PII handling"""
        findings = []
        
        # For MVP - basic checks for common PII patterns
        pii_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', "Social Security Number pattern"),
            (r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', "Credit card number pattern"),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "Email address"),
        ]
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, title in pii_patterns:
                        if re.search(pattern, line):
                            findings.append(SecurityFinding(
                                category="Data Protection",
                                level=SecurityLevel.MEDIUM,
                                title=f"Potential PII: {title}",
                                description=f"Found in line {i}",
                                file_path=str(file_path),
                                line_number=i,
                                recommendation="Ensure PII is properly protected and not logged"
                            ))
            except Exception:
                continue
        
        return findings
    
    def audit_encryption(self) -> List[SecurityFinding]:
        """Audit encryption usage"""
        findings = []
        
        # Check for encryption usage and best practices
        crypto_patterns = [
            (r'AES\.new.*MODE_ECB', SecurityLevel.HIGH, "Weak AES ECB mode", 
             "Use CBC, GCM, or other secure modes instead of ECB"),
            (r'DES\.new', SecurityLevel.CRITICAL, "Weak DES encryption",
             "Use AES or other modern encryption algorithms"),
            (r'MD5\(', SecurityLevel.MEDIUM, "Weak MD5 hash",
             "Use SHA-256 or stronger hash functions"),
            (r'SHA1\(', SecurityLevel.MEDIUM, "Weak SHA1 hash",
             "Use SHA-256 or stronger hash functions"),
        ]
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, level, title, recommendation in crypto_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(SecurityFinding(
                                category="Encryption",
                                level=level,
                                title=title,
                                description=f"Found in line {i}: {line.strip()}",
                                file_path=str(file_path),
                                line_number=i,
                                recommendation=recommendation
                            ))
            except Exception:
                continue
        
        return findings
    
    def audit_data_validation(self) -> List[SecurityFinding]:
        """Audit data validation"""
        findings = []
        
        # Check for validation patterns
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path) or 'test' in str(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for Pydantic models (good for validation)
                if 'BaseModel' in content:
                    findings.append(SecurityFinding(
                        category="Data Validation",
                        level=SecurityLevel.INFO,
                        title="Pydantic validation found",
                        description="File uses Pydantic for data validation",
                        file_path=str(file_path),
                        recommendation="Ensure all input is validated through Pydantic models"
                    ))
                
                # Check for direct request data access without validation
                if 'request.' in content and 'validate' not in content.lower():
                    findings.append(SecurityFinding(
                        category="Data Validation",
                        level=SecurityLevel.MEDIUM,
                        title="Potential unvalidated input",
                        description="Direct request data access without visible validation",
                        file_path=str(file_path),
                        recommendation="Validate all user input before processing"
                    ))
            except Exception:
                continue
        
        return findings
    
    def audit_authentication(self) -> List[SecurityFinding]:
        """Audit authentication mechanisms"""
        findings = []
        
        # For MVP - check for authentication patterns
        auth_files = []
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                if any(term in content.lower() for term in ['auth', 'login', 'token', 'jwt', 'session']):
                    auth_files.append(file_path)
            except Exception:
                continue
        
        if not auth_files:
            findings.append(SecurityFinding(
                category="Authentication",
                level=SecurityLevel.MEDIUM,
                title="No authentication mechanism found",
                description="No obvious authentication implementation detected",
                recommendation="Implement authentication for production deployment"
            ))
        else:
            findings.append(SecurityFinding(
                category="Authentication",
                level=SecurityLevel.INFO,
                title=f"Authentication files found: {len(auth_files)}",
                description="Authentication-related files detected",
                recommendation="Review authentication implementation for security best practices"
            ))
        
        return findings
    
    def audit_authorization(self) -> List[SecurityFinding]:
        """Audit authorization controls"""
        findings = []
        
        # Check for authorization patterns
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Look for endpoint protection
                if '@app.' in content or '@router.' in content:
                    if 'depends=' not in content.lower():
                        findings.append(SecurityFinding(
                            category="Authorization",
                            level=SecurityLevel.MEDIUM,
                            title="Unprotected endpoint",
                            description="API endpoint without visible authorization",
                            file_path=str(file_path),
                            recommendation="Add authorization dependencies to API endpoints"
                        ))
            except Exception:
                continue
        
        return findings
    
    def audit_session_management(self) -> List[SecurityFinding]:
        """Audit session management"""
        findings = []
        
        # For MVP - basic session security checks
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                if 'session' in content.lower():
                    # Check for secure session settings
                    if 'httponly' not in content.lower():
                        findings.append(SecurityFinding(
                            category="Session Management",
                            level=SecurityLevel.MEDIUM,
                            title="Session cookies may lack HttpOnly flag",
                            description="Session implementation may not set HttpOnly flag",
                            file_path=str(file_path),
                            recommendation="Set HttpOnly flag on session cookies"
                        ))
                    
                    if 'secure' not in content.lower():
                        findings.append(SecurityFinding(
                            category="Session Management",
                            level=SecurityLevel.MEDIUM,
                            title="Session cookies may lack Secure flag",
                            description="Session implementation may not set Secure flag",
                            file_path=str(file_path),
                            recommendation="Set Secure flag on session cookies for HTTPS"
                        ))
            except Exception:
                continue
        
        return findings
    
    def scan_input_validation(self) -> List[SecurityFinding]:
        """Scan for input validation patterns"""
        findings = []
        
        # Already covered in audit_data_validation
        # This is a placeholder for more specific validation checks
        
        return findings
    
    def audit_xss_prevention(self) -> List[SecurityFinding]:
        """Audit XSS prevention measures"""
        findings = []
        
        # For a backend API, XSS is less relevant, but check for HTML output
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                if any(html_term in content.lower() for html_term in ['<html>', '<script>', 'innerHTML']):
                    findings.append(SecurityFinding(
                        category="XSS Prevention",
                        level=SecurityLevel.MEDIUM,
                        title="HTML content detected",
                        description="File contains HTML-related content",
                        file_path=str(file_path),
                        recommendation="Ensure all HTML output is properly escaped"
                    ))
            except Exception:
                continue
        
        return findings
    
    def audit_error_disclosure(self) -> List[SecurityFinding]:
        """Audit error information disclosure"""
        findings = []
        
        # Check for detailed error responses
        error_patterns = [
            (r'traceback\.', SecurityLevel.MEDIUM, "Stack trace exposure",
             "Avoid exposing stack traces to users"),
            (r'\.stack', SecurityLevel.MEDIUM, "Stack information",
             "Avoid exposing internal stack information"),
            (r'raise\s+\w+Exception\([^)]*file|path', SecurityLevel.LOW, "File path in exception",
             "Avoid exposing file paths in error messages"),
        ]
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, level, title, recommendation in error_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(SecurityFinding(
                                category="Error Handling",
                                level=level,
                                title=title,
                                description=f"Found in line {i}: {line.strip()}",
                                file_path=str(file_path),
                                line_number=i,
                                recommendation=recommendation
                            ))
            except Exception:
                continue
        
        return findings
    
    def audit_exception_handling(self) -> List[SecurityFinding]:
        """Audit exception handling"""
        findings = []
        
        # Check for broad exception handling
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if re.search(r'except\s*:', line):
                        findings.append(SecurityFinding(
                            category="Error Handling",
                            level=SecurityLevel.LOW,
                            title="Broad exception handling",
                            description=f"Bare except clause in line {i}",
                            file_path=str(file_path),
                            line_number=i,
                            recommendation="Use specific exception types instead of bare except"
                        ))
            except Exception:
                continue
        
        return findings
    
    def audit_logging_config(self) -> List[SecurityFinding]:
        """Audit logging configuration"""
        findings = []
        
        # Check logging implementation
        log_files = []
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                if 'logging' in content:
                    log_files.append(file_path)
                    
                    # Check for proper logging levels
                    if 'DEBUG' in content and 'production' in content.lower():
                        findings.append(SecurityFinding(
                            category="Logging",
                            level=SecurityLevel.MEDIUM,
                            title="Debug logging in production context",
                            description="Debug logging may be enabled in production",
                            file_path=str(file_path),
                            recommendation="Disable debug logging in production"
                        ))
            except Exception:
                continue
        
        if not log_files:
            findings.append(SecurityFinding(
                category="Logging",
                level=SecurityLevel.LOW,
                title="No logging implementation found",
                description="No obvious logging configuration detected",
                recommendation="Implement comprehensive logging for security monitoring"
            ))
        
        return findings
    
    def audit_log_sensitivity(self) -> List[SecurityFinding]:
        """Audit for sensitive data in logs"""
        findings = []
        
        # Check for potential sensitive data logging
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if 'log' in line.lower() and any(term in line.lower() for term in 
                                                   ['password', 'token', 'key', 'secret']):
                        findings.append(SecurityFinding(
                            category="Logging",
                            level=SecurityLevel.HIGH,
                            title="Potential sensitive data logging",
                            description=f"Logging statement may include sensitive data in line {i}",
                            file_path=str(file_path),
                            line_number=i,
                            recommendation="Ensure sensitive data is not logged"
                        ))
            except Exception:
                continue
        
        return findings
    
    def audit_debug_settings(self) -> List[SecurityFinding]:
        """Audit debug settings"""
        findings = []
        
        # Check for debug mode indicators
        debug_indicators = [
            (r'DEBUG\s*=\s*True', "Debug mode enabled"),
            (r'--debug', "Debug flag usage"),
            (r'debug\s*=\s*True', "Debug parameter set"),
        ]
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, title in debug_indicators:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(SecurityFinding(
                                category="Production Hardening",
                                level=SecurityLevel.MEDIUM,
                                title=title,
                                description=f"Found in line {i}: {line.strip()}",
                                file_path=str(file_path),
                                line_number=i,
                                recommendation="Disable debug mode in production"
                            ))
            except Exception:
                continue
        
        return findings
    
    def audit_security_headers(self) -> List[SecurityFinding]:
        """Audit security headers"""
        findings = []
        
        # Check for security header implementation
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy'
        ]
        
        header_found = False
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                for header in security_headers:
                    if header in content:
                        header_found = True
                        break
            except Exception:
                continue
        
        if not header_found:
            findings.append(SecurityFinding(
                category="Production Hardening",
                level=SecurityLevel.MEDIUM,
                title="Security headers not implemented",
                description="No security headers found in codebase",
                recommendation="Implement security headers (HSTS, CSP, X-Frame-Options, etc.)"
            ))
        
        return findings
    
    def audit_rate_limiting(self) -> List[SecurityFinding]:
        """Audit rate limiting implementation"""
        findings = []
        
        # Check for rate limiting
        rate_limiting_terms = ['rate_limit', 'slowapi', 'limiter', 'throttle']
        rate_limit_found = False
        
        for file_path in self.project_root.rglob("*.py"):
            if self.should_skip_file(file_path):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                if any(term in content.lower() for term in rate_limiting_terms):
                    rate_limit_found = True
                    break
            except Exception:
                continue
        
        if not rate_limit_found:
            findings.append(SecurityFinding(
                category="Production Hardening",
                level=SecurityLevel.MEDIUM,
                title="Rate limiting not implemented",
                description="No rate limiting mechanism found",
                recommendation="Implement rate limiting to prevent abuse"
            ))
        
        return findings
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during scanning"""
        skip_patterns = [
            '/.git/', '/venv/', '/.venv/', '/env/', '/__pycache__/',
            '/node_modules/', '/.pytest_cache/', '/build/',
            '/dist/', '.pyc', '/migrations/', '/site-packages/',
            '/lib/python', '/bin/', '/include/', '/share/'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    async def apply_security_hardening(self) -> Dict[str, Any]:
        """Apply automated security hardening measures"""
        hardening_results = {
            "applied_fixes": [],
            "recommendations": [],
            "manual_actions_required": []
        }
        
        # Create .gitignore entries for sensitive files
        gitignore_path = self.project_root / ".gitignore"
        gitignore_entries = [
            "# Security - Environment files",
            ".env",
            ".env.local", 
            ".env.*.local",
            "*.key",
            "*.pem",
            "# Security - Secrets",
            "secrets/",
            "private/",
        ]
        
        try:
            if gitignore_path.exists():
                content = gitignore_path.read_text()
                if ".env" not in content:
                    with open(gitignore_path, "a") as f:
                        f.write("\n" + "\n".join(gitignore_entries) + "\n")
                    hardening_results["applied_fixes"].append("Added security entries to .gitignore")
            else:
                gitignore_path.write_text("\n".join(gitignore_entries) + "\n")
                hardening_results["applied_fixes"].append("Created .gitignore with security entries")
        except Exception as e:
            hardening_results["manual_actions_required"].append(f"Could not update .gitignore: {e}")
        
        # Create security best practices file
        security_md_path = self.project_root / "SECURITY.md"
        if not security_md_path.exists():
            security_content = """# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities to security@leanvibe.ai

## Security Best Practices

### Development
- Never commit secrets, API keys, or passwords
- Use environment variables for sensitive configuration
- Keep dependencies updated
- Run security audits regularly

### Production
- Use HTTPS for all communications
- Implement proper authentication and authorization
- Enable security headers
- Monitor logs for suspicious activity
- Keep systems updated

### Data Protection
- Encrypt sensitive data at rest and in transit
- Implement proper access controls
- Regular security assessments
- Backup and disaster recovery plans
"""
            try:
                security_md_path.write_text(security_content)
                hardening_results["applied_fixes"].append("Created SECURITY.md policy file")
            except Exception as e:
                hardening_results["manual_actions_required"].append(f"Could not create SECURITY.md: {e}")
        
        return hardening_results
    
    def calculate_security_score(self) -> int:
        """Calculate overall security score"""
        if not self.findings:
            return 100
        
        # Weight findings by severity
        severity_weights = {
            SecurityLevel.CRITICAL: 20,
            SecurityLevel.HIGH: 10,
            SecurityLevel.MEDIUM: 5,
            SecurityLevel.LOW: 2,
            SecurityLevel.INFO: 0
        }
        
        total_penalty = sum(severity_weights.get(finding.level, 0) for finding in self.findings)
        
        # Start with 100 and subtract penalties
        score = max(0, 100 - total_penalty)
        
        # Bonus points for good practices
        bonus_categories = set()
        for finding in self.findings:
            if finding.level == SecurityLevel.INFO and 'validation' in finding.title.lower():
                bonus_categories.add('validation')
            if finding.level == SecurityLevel.INFO and 'authentication' in finding.category.lower():
                bonus_categories.add('auth')
        
        score += len(bonus_categories) * 5
        
        return min(100, score)
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        findings_by_category = {}
        findings_by_severity = {}
        
        for finding in self.findings:
            # Group by category
            if finding.category not in findings_by_category:
                findings_by_category[finding.category] = []
            findings_by_category[finding.category].append(finding)
            
            # Group by severity
            if finding.level not in findings_by_severity:
                findings_by_severity[finding.level] = []
            findings_by_severity[finding.level].append(finding)
        
        return {
            "total_findings": len(self.findings),
            "findings_by_category": {cat: len(findings) for cat, findings in findings_by_category.items()},
            "findings_by_severity": {level.value: len(findings) for level, findings in findings_by_severity.items()},
            "critical_issues": [f for f in self.findings if f.level == SecurityLevel.CRITICAL],
            "high_priority": [f for f in self.findings if f.level == SecurityLevel.HIGH],
        }
    
    def finding_to_dict(self, finding: SecurityFinding) -> Dict[str, Any]:
        """Convert SecurityFinding to dictionary"""
        return {
            "category": finding.category,
            "level": finding.level.value,
            "title": finding.title,
            "description": finding.description,
            "file_path": finding.file_path,
            "line_number": finding.line_number,
            "recommendation": finding.recommendation,
            "cve_references": finding.cve_references or [],
            "remediation_code": finding.remediation_code
        }

async def main():
    """Main entry point for security audit"""
    print("🔒 LeanVibe Security Audit & Production Hardening")
    print("=" * 60)
    
    audit = LeanVibeSecurityAudit()
    report = await audit.run_comprehensive_audit()
    
    # Save detailed report
    with open("security_audit_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Detailed security report saved to: security_audit_report.json")
    
    # Generate summary
    print(f"\n🔒 SECURITY SUMMARY")
    print(f"Security Score: {report['security_score']}/100")
    print(f"Total Findings: {len(report['findings'])}")
    
    critical_count = len([f for f in report['findings'] if f['level'] == 'critical'])
    high_count = len([f for f in report['findings'] if f['level'] == 'high'])
    medium_count = len([f for f in report['findings'] if f['level'] == 'medium'])
    
    print(f"🚨 Critical: {critical_count}")
    print(f"⚠️  High: {high_count}")
    print(f"📊 Medium: {medium_count}")
    print(f"Production Ready: {'YES' if report['production_ready'] else 'NO'}")
    
    # Show top recommendations
    if report['findings']:
        print(f"\n💡 TOP RECOMMENDATIONS:")
        recommendations = set()
        for finding in report['findings'][:5]:  # Top 5 findings
            if finding['recommendation']:
                recommendations.add(finding['recommendation'])
        
        for i, rec in enumerate(list(recommendations)[:3], 1):
            print(f"{i}. {rec}")
    
    # Exit with appropriate code
    if critical_count > 0:
        return 1
    elif high_count > 3:
        return 2
    elif report['security_score'] < 80:
        return 3
    else:
        return 0

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)