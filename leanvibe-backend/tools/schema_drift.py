#!/usr/bin/env python3
"""
Schema Drift Detector - OpenAPI Contract Validation
Detects breaking changes in API schemas between commits
"""

import argparse
import json
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class SchemaDriftDetector:
    """Detect API schema changes that could break contracts"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.contracts_dir = self.project_root / "contracts"
        self.openapi_file = self.contracts_dir / "openapi.yaml"
        self.asyncapi_file = self.contracts_dir / "asyncapi.yaml"
        
    def load_yaml_schema(self, filepath: Path) -> Optional[Dict]:
        """Load YAML schema file"""
        try:
            if not filepath.exists():
                return None
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  Error loading {filepath}: {e}")
            return None
    
    def get_schema_from_commit(self, commit: str, filepath: Path) -> Optional[Dict]:
        """Get schema file content from a specific git commit"""
        try:
            relative_path = filepath.relative_to(self.project_root)
            result = subprocess.run(
                ["git", "show", f"{commit}:{relative_path}"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return None
            return yaml.safe_load(result.stdout)
        except Exception as e:
            print(f"⚠️  Error getting schema from commit {commit}: {e}")
            return None
    
    def extract_endpoints(self, openapi_schema: Dict) -> Dict[str, Dict]:
        """Extract endpoint information from OpenAPI schema"""
        endpoints = {}
        paths = openapi_schema.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint_key = f"{method.upper()} {path}"
                    endpoints[endpoint_key] = {
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody", {}),
                        "responses": details.get("responses", {}),
                        "deprecated": details.get("deprecated", False)
                    }
        
        return endpoints
    
    def extract_schemas(self, openapi_schema: Dict) -> Dict[str, Dict]:
        """Extract component schemas from OpenAPI"""
        return openapi_schema.get("components", {}).get("schemas", {})
    
    def detect_breaking_changes(self, old_schema: Dict, new_schema: Dict) -> List[Dict]:
        """Detect breaking changes between two OpenAPI schemas"""
        breaking_changes = []
        
        old_endpoints = self.extract_endpoints(old_schema)
        new_endpoints = self.extract_endpoints(new_schema)
        old_schemas = self.extract_schemas(old_schema)
        new_schemas = self.extract_schemas(new_schema)
        
        # Check for removed endpoints
        for endpoint in old_endpoints:
            if endpoint not in new_endpoints:
                breaking_changes.append({
                    "type": "endpoint_removed",
                    "severity": "breaking",
                    "description": f"Endpoint removed: {endpoint}"
                })
        
        # Check for modified endpoints
        for endpoint in old_endpoints:
            if endpoint in new_endpoints:
                changes = self.compare_endpoints(
                    old_endpoints[endpoint], 
                    new_endpoints[endpoint], 
                    endpoint
                )
                breaking_changes.extend(changes)
        
        # Check for removed schemas
        for schema_name in old_schemas:
            if schema_name not in new_schemas:
                breaking_changes.append({
                    "type": "schema_removed",
                    "severity": "breaking",
                    "description": f"Schema removed: {schema_name}"
                })
        
        # Check for schema modifications
        for schema_name in old_schemas:
            if schema_name in new_schemas:
                changes = self.compare_schemas(
                    old_schemas[schema_name], 
                    new_schemas[schema_name], 
                    schema_name
                )
                breaking_changes.extend(changes)
        
        return breaking_changes
    
    def compare_endpoints(self, old_endpoint: Dict, new_endpoint: Dict, endpoint_name: str) -> List[Dict]:
        """Compare two endpoints for breaking changes"""
        changes = []
        
        # Check if endpoint became deprecated
        if not old_endpoint.get("deprecated", False) and new_endpoint.get("deprecated", False):
            changes.append({
                "type": "endpoint_deprecated",
                "severity": "warning",
                "description": f"Endpoint deprecated: {endpoint_name}"
            })
        
        # Check required parameters
        old_required_params = {
            param["name"] for param in old_endpoint.get("parameters", [])
            if param.get("required", False)
        }
        new_required_params = {
            param["name"] for param in new_endpoint.get("parameters", [])
            if param.get("required", False)
        }
        
        # New required parameters are breaking
        for param in new_required_params - old_required_params:
            changes.append({
                "type": "required_parameter_added",
                "severity": "breaking", 
                "description": f"New required parameter in {endpoint_name}: {param}"
            })
        
        return changes
    
    def compare_schemas(self, old_schema: Dict, new_schema: Dict, schema_name: str) -> List[Dict]:
        """Compare two schemas for breaking changes"""
        changes = []
        
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))
        old_properties = set(old_schema.get("properties", {}).keys())
        new_properties = set(new_schema.get("properties", {}).keys())
        
        # New required fields are breaking
        for field in new_required - old_required:
            changes.append({
                "type": "required_field_added",
                "severity": "breaking",
                "description": f"New required field in {schema_name}: {field}"
            })
        
        # Removed properties are breaking  
        for field in old_properties - new_properties:
            changes.append({
                "type": "property_removed",
                "severity": "breaking",
                "description": f"Property removed from {schema_name}: {field}"
            })
        
        return changes
    
    def detect_non_breaking_changes(self, old_schema: Dict, new_schema: Dict) -> List[Dict]:
        """Detect non-breaking changes that are still worth noting"""
        changes = []
        
        old_endpoints = self.extract_endpoints(old_schema)
        new_endpoints = self.extract_endpoints(new_schema)
        
        # New endpoints are non-breaking
        for endpoint in new_endpoints:
            if endpoint not in old_endpoints:
                changes.append({
                    "type": "endpoint_added",
                    "severity": "info",
                    "description": f"New endpoint added: {endpoint}"
                })
        
        return changes
    
    def check_drift(self, base_commit: str = "HEAD~1") -> bool:
        """Check for schema drift against a base commit"""
        print(f"🔍 Checking schema drift against {base_commit}...")
        
        # Load current schemas
        current_openapi = self.load_yaml_schema(self.openapi_file)
        if not current_openapi:
            print("⚠️  No current OpenAPI schema found")
            return True  # Pass if no schema to check
        
        # Load base schemas
        base_openapi = self.get_schema_from_commit(base_commit, self.openapi_file)
        if not base_openapi:
            print(f"⚠️  No OpenAPI schema found in {base_commit}, assuming first commit")
            return True  # Pass if no base to compare against
        
        # Detect changes
        breaking_changes = self.detect_breaking_changes(base_openapi, current_openapi)
        non_breaking_changes = self.detect_non_breaking_changes(base_openapi, current_openapi)
        
        # Report findings
        if not breaking_changes and not non_breaking_changes:
            print("✅ No schema changes detected")
            return True
        
        # Report non-breaking changes
        if non_breaking_changes:
            print(f"\n📋 Non-breaking changes ({len(non_breaking_changes)}):")
            for change in non_breaking_changes:
                print(f"   ℹ️  {change['description']}")
        
        # Report breaking changes
        if breaking_changes:
            print(f"\n⚠️  Breaking changes detected ({len(breaking_changes)}):")
            for change in breaking_changes:
                severity_icon = "💥" if change["severity"] == "breaking" else "⚠️"
                print(f"   {severity_icon} {change['description']}")
            print(f"\n❌ Schema drift check failed: {len(breaking_changes)} breaking changes")
            return False
        
        print(f"\n✅ Schema drift check passed: {len(non_breaking_changes)} non-breaking changes")
        return True
    
    def generate_schema_report(self):
        """Generate a detailed schema report"""
        print("📊 API Schema Report")
        print("=" * 50)
        
        if self.openapi_file.exists():
            schema = self.load_yaml_schema(self.openapi_file)
            if schema:
                endpoints = self.extract_endpoints(schema)
                schemas = self.extract_schemas(schema)
                
                print(f"📋 OpenAPI Version: {schema.get('openapi', 'N/A')}")
                print(f"📋 API Title: {schema.get('info', {}).get('title', 'N/A')}")
                print(f"📋 API Version: {schema.get('info', {}).get('version', 'N/A')}")
                print(f"📋 Endpoints: {len(endpoints)}")
                print(f"📋 Schemas: {len(schemas)}")
                
                if endpoints:
                    print("\n🔗 Endpoints:")
                    for endpoint in sorted(endpoints.keys()):
                        deprecated = " (DEPRECATED)" if endpoints[endpoint].get("deprecated") else ""
                        print(f"   • {endpoint}{deprecated}")
                
                if schemas:
                    print("\n📝 Schemas:")
                    for schema_name in sorted(schemas.keys()):
                        properties = schemas[schema_name].get("properties", {})
                        required = schemas[schema_name].get("required", [])
                        print(f"   • {schema_name} ({len(properties)} properties, {len(required)} required)")
        else:
            print("⚠️  No OpenAPI schema found")


def main():
    parser = argparse.ArgumentParser(description="Schema Drift Detector")
    parser.add_argument("--check", action="store_true", 
                       help="Check for schema drift against base commit")
    parser.add_argument("--base", default="HEAD~1", 
                       help="Base commit to compare against")
    parser.add_argument("--report", action="store_true", 
                       help="Generate schema report")
    parser.add_argument("--project-root", default=".", 
                       help="Project root directory")
    
    args = parser.parse_args()
    
    detector = SchemaDriftDetector(args.project_root)
    
    if args.report:
        detector.generate_schema_report()
        return
    
    if args.check:
        success = detector.check_drift(args.base)
        sys.exit(0 if success else 1)
    
    # Default action
    detector.generate_schema_report()


if __name__ == "__main__":
    main()