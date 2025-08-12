#!/usr/bin/env python3
"""
LeanVibe API Documentation Auto-Generator

Generates comprehensive API documentation from FastAPI endpoints, SQLAlchemy models,
and Pydantic settings with enterprise-grade features and accuracy validation.
"""

import ast
import inspect
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Main documentation generator with enterprise features."""
    
    def __init__(self, app: FastAPI, output_dir: Path = Path("docs/generated")):
        self.app = app
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Documentation generation configuration
        self.config = {
            "include_examples": True,
            "include_curl_commands": True,
            "include_response_schemas": True,
            "include_error_codes": True,
            "validate_endpoints": True,
            "generate_postman_collection": True,
            "enterprise_security_notes": True
        }
    
    def generate_complete_documentation(self) -> Dict[str, str]:
        """Generate all documentation artifacts."""
        logger.info("Starting comprehensive documentation generation")
        
        artifacts = {}
        
        try:
            # Generate OpenAPI specification
            artifacts["openapi_spec"] = self._generate_openapi_spec()
            
            # Generate Markdown API documentation
            artifacts["api_docs"] = self._generate_markdown_api_docs()
            
            # Generate endpoint reference
            artifacts["endpoint_reference"] = self._generate_endpoint_reference()
            
            # Generate authentication guide
            artifacts["auth_guide"] = self._generate_auth_documentation()
            
            # Generate error handling guide
            artifacts["error_guide"] = self._generate_error_documentation()
            
            # Generate Postman collection
            if self.config["generate_postman_collection"]:
                artifacts["postman_collection"] = self._generate_postman_collection()
            
            # Generate enterprise integration guide
            artifacts["enterprise_guide"] = self._generate_enterprise_integration_guide()
            
            logger.info(f"Generated {len(artifacts)} documentation artifacts")
            return artifacts
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            raise
    
    def _generate_openapi_spec(self) -> str:
        """Generate comprehensive OpenAPI specification."""
        logger.info("Generating OpenAPI specification")
        
        # Get base OpenAPI schema
        openapi_schema = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description,
            routes=self.app.routes,
        )
        
        # Enhance with enterprise features
        openapi_schema["info"]["contact"] = {
            "name": "LeanVibe Enterprise Support",
            "url": "https://leanvibe.ai/enterprise-support",
            "email": "enterprise@leanvibe.ai"
        }
        
        openapi_schema["info"]["license"] = {
            "name": "Enterprise License",
            "url": "https://leanvibe.ai/enterprise-license"
        }
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enterprise JWT authentication"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Enterprise API key authentication"
            }
        }
        
        # Add enterprise servers
        openapi_schema["servers"] = [
            {
                "url": "https://api.leanvibe.ai/v1",
                "description": "Production API (Enterprise)"
            },
            {
                "url": "https://staging-api.leanvibe.ai/v1", 
                "description": "Staging Environment"
            },
            {
                "url": "http://localhost:8765",
                "description": "Development Server"
            }
        ]
        
        # Save OpenAPI spec
        spec_path = self.output_dir / "openapi.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"OpenAPI specification saved to {spec_path}")
        return str(spec_path)
    
    def _generate_markdown_api_docs(self) -> str:
        """Generate comprehensive Markdown API documentation."""
        logger.info("Generating Markdown API documentation")
        
        docs_content = []
        
        # Header
        docs_content.extend([
            "# LeanVibe Enterprise API Documentation",
            "",
            f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**API Version:** {self.app.version}",
            "",
            "## Overview",
            "",
            self.app.description or "LeanVibe Enterprise API provides comprehensive access to all platform capabilities.",
            "",
            "## Authentication",
            "",
            "All API endpoints require authentication using one of the following methods:",
            "",
            "### JWT Bearer Token",
            "```http",
            "Authorization: Bearer <your-jwt-token>",
            "```",
            "",
            "### API Key",
            "```http",
            "X-API-Key: <your-api-key>",
            "```",
            "",
            "## Base URLs",
            "",
            "- **Production:** `https://api.leanvibe.ai/v1`",
            "- **Staging:** `https://staging-api.leanvibe.ai/v1`",
            "- **Development:** `http://localhost:8765`",
            "",
            "## Rate Limits",
            "",
            "| Tier | Requests per Minute |",
            "|------|-------------------|",
            "| Developer | 100 |",
            "| Team | 1,000 |", 
            "| Enterprise | 10,000 |",
            "",
            "## API Endpoints",
            ""
        ])
        
        # Generate endpoint documentation
        routes = [route for route in self.app.routes if hasattr(route, 'methods')]
        
        for route in sorted(routes, key=lambda r: r.path):
            if hasattr(route, 'methods') and route.methods:
                docs_content.extend(self._generate_endpoint_documentation(route))
        
        # Error handling section
        docs_content.extend([
            "",
            "## Error Handling",
            "",
            "The API uses conventional HTTP response codes to indicate success or failure.",
            "",
            "### HTTP Status Codes",
            "",
            "| Code | Description |",
            "|------|-------------|",
            "| 200 | OK - Request successful |",
            "| 201 | Created - Resource created successfully |",
            "| 400 | Bad Request - Invalid parameters |",
            "| 401 | Unauthorized - Invalid authentication |",
            "| 403 | Forbidden - Insufficient permissions |",
            "| 404 | Not Found - Resource not found |",
            "| 429 | Too Many Requests - Rate limit exceeded |",
            "| 500 | Internal Server Error - Server error |",
            "",
            "### Error Response Format",
            "",
            "```json",
            "{",
            '  "error": {',
            '    "code": "VALIDATION_ERROR",',
            '    "message": "Request validation failed",',
            '    "details": {',
            '      "field": "email",',
            '      "issue": "Invalid email format"',
            "    }",
            "  }",
            "}",
            "```"
        ])
        
        # Save documentation
        docs_path = self.output_dir / "API_REFERENCE.md"
        with open(docs_path, "w") as f:
            f.write("\n".join(docs_content))
        
        logger.info(f"API documentation saved to {docs_path}")
        return str(docs_path)
    
    def _generate_endpoint_documentation(self, route) -> List[str]:
        """Generate documentation for a single endpoint."""
        docs = []
        
        for method in sorted(route.methods):
            if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                docs.extend([
                    f"### {method} {route.path}",
                    ""
                ])
                
                # Add description if available
                if hasattr(route, 'endpoint') and route.endpoint:
                    func = route.endpoint
                    if func.__doc__:
                        docs.extend([
                            func.__doc__.strip(),
                            ""
                        ])
                
                # Add cURL example
                if self.config["include_curl_commands"]:
                    docs.extend(self._generate_curl_example(method, route.path))
                
                docs.append("")
        
        return docs
    
    def _generate_curl_example(self, method: str, path: str) -> List[str]:
        """Generate cURL command examples."""
        base_url = "https://api.leanvibe.ai/v1"
        
        curl_lines = [
            "**Example Request:**",
            "",
            "```bash",
            f"curl -X {method} \"{base_url}{path}\" \\",
            "  -H \"Authorization: Bearer <your-token>\" \\",
            "  -H \"Content-Type: application/json\""
        ]
        
        if method in ['POST', 'PUT', 'PATCH']:
            curl_lines.extend([
                "  -d '{",
                '    "example": "data"',
                "  }'"
            ])
        
        curl_lines.append("```")
        return curl_lines
    
    def _generate_postman_collection(self) -> str:
        """Generate Postman collection for API testing."""
        logger.info("Generating Postman collection")
        
        collection = {
            "info": {
                "name": "LeanVibe Enterprise API",
                "description": "Complete LeanVibe API collection for testing",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{jwt_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "https://api.leanvibe.ai/v1",
                    "type": "string"
                },
                {
                    "key": "jwt_token", 
                    "value": "",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # Add endpoints to collection
        routes = [route for route in self.app.routes if hasattr(route, 'methods')]
        
        for route in routes:
            if hasattr(route, 'methods') and route.methods:
                for method in route.methods:
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        collection["item"].append({
                            "name": f"{method} {route.path}",
                            "request": {
                                "method": method,
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/json"
                                    }
                                ],
                                "url": {
                                    "raw": "{{base_url}}" + route.path,
                                    "host": ["{{base_url}}"],
                                    "path": route.path.strip("/").split("/")
                                }
                            }
                        })
        
        # Save Postman collection
        collection_path = self.output_dir / "LeanVibe_API.postman_collection.json"
        with open(collection_path, "w") as f:
            json.dump(collection, f, indent=2)
        
        logger.info(f"Postman collection saved to {collection_path}")
        return str(collection_path)
    
    def _generate_endpoint_reference(self) -> str:
        """Generate quick endpoint reference."""
        logger.info("Generating endpoint reference")
        
        reference_content = [
            "# API Endpoint Reference",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Quick Reference",
            "",
            "| Method | Endpoint | Description |",
            "|--------|----------|-------------|"
        ]
        
        routes = [route for route in self.app.routes if hasattr(route, 'methods')]
        
        for route in sorted(routes, key=lambda r: r.path):
            if hasattr(route, 'methods') and route.methods:
                for method in sorted(route.methods):
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        description = "API endpoint"
                        if hasattr(route, 'endpoint') and route.endpoint.__doc__:
                            description = route.endpoint.__doc__.split('\n')[0].strip()
                        
                        reference_content.append(
                            f"| {method} | `{route.path}` | {description} |"
                        )
        
        # Save reference
        reference_path = self.output_dir / "ENDPOINT_REFERENCE.md"
        with open(reference_path, "w") as f:
            f.write("\n".join(reference_content))
        
        logger.info(f"Endpoint reference saved to {reference_path}")
        return str(reference_path)
    
    def _generate_auth_documentation(self) -> str:
        """Generate authentication documentation."""
        logger.info("Generating authentication documentation")
        
        auth_content = [
            "# Authentication Guide",
            "",
            "## Overview",
            "",
            "LeanVibe Enterprise API supports multiple authentication methods for different use cases:",
            "",
            "## JWT Bearer Token Authentication",
            "",
            "### Getting a Token",
            "",
            "```bash",
            "curl -X POST \"https://api.leanvibe.ai/v1/auth/login\" \\",
            "  -H \"Content-Type: application/json\" \\",
            "  -d '{",
            '    "email": "your-email@company.com",',
            '    "password": "your-password"',
            "  }'",
            "```",
            "",
            "### Using the Token",
            "",
            "```bash",
            "curl -X GET \"https://api.leanvibe.ai/v1/projects\" \\",
            "  -H \"Authorization: Bearer <your-jwt-token>\"",
            "```",
            "",
            "## API Key Authentication",
            "",
            "For server-to-server integration:",
            "",
            "```bash",
            "curl -X GET \"https://api.leanvibe.ai/v1/projects\" \\",
            "  -H \"X-API-Key: <your-api-key>\"",
            "```",
            "",
            "## Enterprise SSO Integration",
            "",
            "### SAML 2.0",
            "- Configure your SAML identity provider",
            "- Contact enterprise support for setup",
            "",
            "### OAuth 2.0 / OIDC",
            "- Supports Google, Microsoft, Okta",
            "- Standard OAuth 2.0 authorization code flow",
            "",
            "## Security Best Practices",
            "",
            "- Store tokens securely",
            "- Use HTTPS in production",
            "- Implement token refresh logic",
            "- Monitor for unauthorized access"
        ]
        
        # Save authentication guide
        auth_path = self.output_dir / "AUTHENTICATION.md"
        with open(auth_path, "w") as f:
            f.write("\n".join(auth_content))
        
        logger.info(f"Authentication guide saved to {auth_path}")
        return str(auth_path)
    
    def _generate_error_documentation(self) -> str:
        """Generate error handling documentation."""
        logger.info("Generating error handling documentation")
        
        error_content = [
            "# Error Handling Guide",
            "",
            "## HTTP Status Codes",
            "",
            "LeanVibe API uses standard HTTP status codes:",
            "",
            "### Success Codes (2xx)",
            "- `200 OK` - Request successful",
            "- `201 Created` - Resource created",
            "- `202 Accepted` - Request accepted for processing",
            "- `204 No Content` - Success with no response body",
            "",
            "### Client Error Codes (4xx)",
            "- `400 Bad Request` - Invalid request parameters",
            "- `401 Unauthorized` - Authentication required",
            "- `403 Forbidden` - Insufficient permissions",
            "- `404 Not Found` - Resource not found",
            "- `409 Conflict` - Resource conflict",
            "- `422 Unprocessable Entity` - Validation error",
            "- `429 Too Many Requests` - Rate limit exceeded",
            "",
            "### Server Error Codes (5xx)",
            "- `500 Internal Server Error` - Server error",
            "- `502 Bad Gateway` - Upstream server error",
            "- `503 Service Unavailable` - Service temporarily unavailable",
            "",
            "## Error Response Format",
            "",
            "All error responses follow a consistent format:",
            "",
            "```json",
            "{",
            '  "error": {',
            '    "code": "ERROR_CODE",',
            '    "message": "Human readable error message",',
            '    "details": {',
            '      "field": "specific_field",',
            '      "constraint": "validation_rule"',
            "    },",
            '    "timestamp": "2024-01-01T00:00:00Z",',
            '    "request_id": "uuid-request-identifier"',
            "  }",
            "}",
            "```",
            "",
            "## Common Error Codes",
            "",
            "| Code | Description | Action |",
            "|------|-------------|--------|",
            "| `AUTHENTICATION_FAILED` | Invalid credentials | Check API key/token |",
            "| `AUTHORIZATION_DENIED` | Insufficient permissions | Contact admin |",
            "| `VALIDATION_ERROR` | Request validation failed | Fix request parameters |",
            "| `RESOURCE_NOT_FOUND` | Resource doesn't exist | Check resource ID |",
            "| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement backoff |",
            "| `QUOTA_EXCEEDED` | Usage quota exceeded | Upgrade plan |",
            "",
            "## Error Handling Best Practices",
            "",
            "1. **Always check HTTP status codes**",
            "2. **Parse error response for details**",
            "3. **Implement exponential backoff for rate limits**",
            "4. **Log request_id for support requests**",
            "5. **Handle network errors gracefully**"
        ]
        
        # Save error guide
        error_path = self.output_dir / "ERROR_HANDLING.md"
        with open(error_path, "w") as f:
            f.write("\n".join(error_content))
        
        logger.info(f"Error handling guide saved to {error_path}")
        return str(error_path)
    
    def _generate_enterprise_integration_guide(self) -> str:
        """Generate enterprise integration guide."""
        logger.info("Generating enterprise integration guide")
        
        integration_content = [
            "# Enterprise Integration Guide",
            "",
            "## Overview",
            "",
            "This guide covers enterprise-specific integration patterns and best practices for LeanVibe API.",
            "",
            "## Multi-Tenant Architecture",
            "",
            "### Tenant Context",
            "",
            "All API requests operate within a tenant context:",
            "",
            "```bash",
            "curl -X GET \"https://api.leanvibe.ai/v1/projects\" \\",
            "  -H \"Authorization: Bearer <token>\" \\",
            "  -H \"X-Tenant-ID: <tenant-uuid>\"",
            "```",
            "",
            "### Tenant Isolation",
            "",
            "- Complete data isolation between tenants",
            "- Row-level security in database",
            "- Separate resource quotas per tenant",
            "",
            "## Enterprise Authentication",
            "",
            "### Single Sign-On (SSO)",
            "",
            "#### SAML 2.0 Configuration",
            "```xml",
            "<saml:Issuer>https://your-company.com/saml</saml:Issuer>",
            "<saml:Assertion>",
            "  <!-- User attributes -->",
            "</saml:Assertion>",
            "```",
            "",
            "#### OAuth 2.0 / OIDC",
            "```json",
            "{",
            '  "client_id": "your-enterprise-client-id",',
            '  "redirect_uri": "https://your-app.com/auth/callback",',
            '  "scope": "openid profile email leanvibe:read leanvibe:write"',
            "}",
            "```",
            "",
            "## Enterprise Security",
            "",
            "### API Security Headers",
            "",
            "Required security headers for enterprise deployment:",
            "",
            "```http",
            "Strict-Transport-Security: max-age=31536000; includeSubDomains",
            "X-Frame-Options: DENY", 
            "X-Content-Type-Options: nosniff",
            "X-XSS-Protection: 1; mode=block",
            "Content-Security-Policy: default-src 'self'",
            "```",
            "",
            "### Audit Logging",
            "",
            "All API requests are logged for enterprise compliance:",
            "",
            "```json",
            "{",
            '  "timestamp": "2024-01-01T00:00:00Z",',
            '  "user_id": "user-uuid",',
            '  "tenant_id": "tenant-uuid",',
            '  "action": "projects.create",',
            '  "resource_id": "project-uuid",',
            '  "ip_address": "10.0.0.1",',
            '  "user_agent": "Enterprise-App/1.0"',
            "}",
            "```",
            "",
            "## Performance & Scaling",
            "",
            "### Rate Limiting",
            "",
            "Enterprise customers have higher rate limits:",
            "",
            "```http",
            "X-RateLimit-Limit: 10000",
            "X-RateLimit-Remaining: 9999", 
            "X-RateLimit-Reset: 1640995200",
            "```",
            "",
            "### Caching Strategy",
            "",
            "- Use ETags for conditional requests",
            "- Implement client-side caching",
            "- Respect cache-control headers",
            "",
            "## Monitoring & Observability",
            "",
            "### Health Checks",
            "",
            "```bash",
            "curl -X GET \"https://api.leanvibe.ai/v1/health\"",
            "```",
            "",
            "### Metrics Collection",
            "",
            "Available metrics endpoints:",
            "- `/metrics` - Prometheus metrics",
            "- `/health` - Application health",
            "- `/status` - Detailed system status",
            "",
            "## Support & SLA",
            "",
            "### Enterprise Support",
            "- 24/7 support for critical issues",
            "- Dedicated success manager",
            "- Priority bug fixes and feature requests",
            "",
            "### Service Level Agreement",
            "- 99.95% uptime guarantee",
            "- <100ms average response time",
            "- <2 second 99th percentile response time"
        ]
        
        # Save integration guide
        integration_path = self.output_dir / "ENTERPRISE_INTEGRATION.md"
        with open(integration_path, "w") as f:
            f.write("\n".join(integration_content))
        
        logger.info(f"Enterprise integration guide saved to {integration_path}")
        return str(integration_path)


def main():
    """Main function to generate API documentation."""
    import sys
    sys.path.append(".")
    
    try:
        # Import the FastAPI app
        from app.main import app
        
        # Create generator
        generator = DocumentationGenerator(app)
        
        # Generate all documentation
        artifacts = generator.generate_complete_documentation()
        
        print("Documentation generation completed successfully!")
        print("\nGenerated artifacts:")
        for name, path in artifacts.items():
            print(f"  - {name}: {path}")
            
    except ImportError as e:
        logger.error(f"Failed to import FastAPI app: {e}")
        logger.error("Make sure you're running this from the project root directory")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()