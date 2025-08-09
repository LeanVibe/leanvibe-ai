"""
API Security Testing Package

This package contains comprehensive security tests for all LeanVibe API endpoints
to ensure enterprise-grade security, authentication, authorization, and data protection.

Test Modules:
- test_endpoint_authentication.py: JWT validation, tenant isolation, RBAC enforcement
- test_endpoint_input_security.py: SQL injection, XSS, malformed data handling
- test_endpoint_security_headers.py: Rate limiting, CORS, security headers
- test_billing_api_security.py: Stripe webhook security, payment data protection
- test_tenant_api_security.py: Multi-tenant isolation, admin controls

Security Coverage:
✅ Authentication & Authorization Testing
✅ Input Validation & Security Testing
✅ Rate Limiting & Security Headers
✅ Billing API Specific Security
✅ Tenant API Security Isolation

Risk Level: CRITICAL
Business Impact: Prevents data breaches, ensures compliance, protects revenue
"""

# Test execution helper
def run_all_security_tests():
    """Run all API security tests in the proper order"""
    import pytest
    import os
    
    test_dir = os.path.dirname(__file__)
    test_files = [
        "test_endpoint_authentication.py",
        "test_endpoint_input_security.py", 
        "test_endpoint_security_headers.py",
        "test_billing_api_security.py",
        "test_tenant_api_security.py"
    ]
    
    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        if os.path.exists(test_path):
            print(f"\n🔒 Running {test_file}...")
            result = pytest.main([test_path, "-v", "--tb=short"])
            if result != 0:
                print(f"❌ Security test failures in {test_file}")
            else:
                print(f"✅ All security tests passed in {test_file}")
    
    print("\n🛡️  API Security Test Suite Complete")


if __name__ == "__main__":
    run_all_security_tests()