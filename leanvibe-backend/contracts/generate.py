#!/usr/bin/env python3
"""
Contract-First Code Generator

Generates Python Pydantic models, validation decorators, and TypeScript types
from OpenAPI and AsyncAPI schemas.
"""

import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import sys


@dataclass
class GenerationConfig:
    """Configuration for code generation."""
    openapi_path: Path
    asyncapi_path: Path
    output_dir: Path
    python_package: str = "app.contracts"
    typescript_namespace: str = "LeanVibeAPI"


class CodeGenerator:
    """Main code generator class."""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.openapi_spec = None
        self.asyncapi_spec = None
        
    def load_schemas(self):
        """Load OpenAPI and AsyncAPI schemas."""
        try:
            with open(self.config.openapi_path, 'r') as f:
                self.openapi_spec = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading OpenAPI schema: {e}")
            sys.exit(1)
            
        try:
            with open(self.config.asyncapi_path, 'r') as f:
                self.asyncapi_spec = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading AsyncAPI schema: {e}")
            sys.exit(1)
    
    def generate_all(self):
        """Generate all code artifacts."""
        self.load_schemas()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate Python models
        self.generate_pydantic_models()
        
        # Generate validation decorators
        self.generate_validation_decorators()
        
        # Generate TypeScript types
        self.generate_typescript_types()
        
        # Generate __init__.py
        self.generate_init_file()
        
        print(f"✅ Generated contract code in {self.config.output_dir}")

    def generate_pydantic_models(self):
        """Generate Pydantic models from schemas."""
        models_code = self._get_models_header()
        
        # Collect all schemas
        all_schemas = {}
        if 'components' in self.openapi_spec and 'schemas' in self.openapi_spec['components']:
            all_schemas.update(self.openapi_spec['components']['schemas'])
        
        if 'components' in self.asyncapi_spec and 'schemas' in self.asyncapi_spec['components']:
            for name, schema in self.asyncapi_spec['components']['schemas'].items():
                if name not in all_schemas:
                    all_schemas[name] = schema
        
        # Sort models by dependency order
        sorted_schemas = self._sort_schemas_by_dependencies(all_schemas)
        
        # Generate models in dependency order
        for name in sorted_schemas:
            schema = all_schemas[name]
            model_code = self._generate_pydantic_model(name, schema)
            models_code += model_code + "\n\n"
        
        # Write models file
        models_file = self.config.output_dir / "models.py"
        with open(models_file, 'w') as f:
            f.write(models_code)
        
        print(f"✅ Generated Pydantic models: {models_file}")

    def _sort_schemas_by_dependencies(self, schemas: Dict[str, Any]) -> List[str]:
        """Sort schemas by dependency order (referenced models first)."""
        dependency_graph = {}
        
        # Build dependency graph
        for name, schema in schemas.items():
            dependencies = self._extract_dependencies(schema, schemas.keys())
            dependency_graph[name] = dependencies
        
        # Topological sort
        sorted_names = []
        visited = set()
        visiting = set()
        
        def visit(name):
            if name in visiting:
                # Circular dependency - just add it
                return
            if name in visited:
                return
                
            visiting.add(name)
            for dep in dependency_graph.get(name, []):
                if dep in schemas:  # Only visit if it's in our schema set
                    visit(dep)
            visiting.remove(name)
            visited.add(name)
            sorted_names.append(name)
        
        for name in schemas.keys():
            visit(name)
        
        return sorted_names
    
    def _extract_dependencies(self, schema: Dict[str, Any], schema_names: set) -> List[str]:
        """Extract model dependencies from a schema."""
        dependencies = set()
        
        def extract_from_value(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    ref_name = value['$ref'].split('/')[-1]
                    if ref_name in schema_names:
                        dependencies.add(ref_name)
                else:
                    for v in value.values():
                        extract_from_value(v)
            elif isinstance(value, list):
                for item in value:
                    extract_from_value(item)
        
        extract_from_value(schema)
        return list(dependencies)

    def _get_models_header(self):
        """Get header for models file."""
        return '''"""
Generated Pydantic Models from Contract Schemas

This file is auto-generated from OpenAPI and AsyncAPI schemas.
Do not edit manually - regenerate using contracts/generate.py
"""

from datetime import datetime
from typing import List, Optional, Union, Any, Dict, Literal
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum

'''

    def _generate_pydantic_model(self, name: str, schema: Dict[str, Any]) -> str:
        """Generate a single Pydantic model."""
        if schema.get('type') != 'object':
            return f"# Skipped {name}: not an object type"
        
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        # Generate class definition
        class_def = f"class {name}(BaseModel):\n"
        class_def += f'    """{schema.get("description", f"Generated model for {name}")}"""\n\n'
        
        # Generate fields
        if not properties:
            class_def += "    pass\n"
        else:
            for prop_name, prop_schema in properties.items():
                field_def = self._generate_field(prop_name, prop_schema, required)
                class_def += f"    {field_def}\n"
        
        # Generate validators if needed
        validators = self._generate_validators(name, properties)
        if validators:
            class_def += "\n" + validators
        
        return class_def

    def _generate_field(self, name: str, schema: Dict[str, Any], required: List[str]) -> str:
        """Generate a single field definition."""
        base_type = self._get_python_type(schema)
        is_required = name in required
        is_nullable = schema.get('nullable', False)
        
        # Make type Optional if nullable
        if is_nullable:
            type_str = f"Optional[{base_type}]"
        else:
            type_str = base_type
        
        # Handle Field() definition
        field_args = []
        
        # Handle required fields
        if is_required and 'default' not in schema and not is_nullable:
            field_args.append("...")
        
        # Add description
        if 'description' in schema:
            field_args.append(f'description="{schema["description"]}"')
        
        # Add validation constraints
        if 'minimum' in schema:
            field_args.append(f'ge={schema["minimum"]}')
        
        if 'maximum' in schema:
            field_args.append(f'le={schema["maximum"]}')
        
        if 'minLength' in schema:
            field_args.append(f'min_length={schema["minLength"]}')
        
        if 'pattern' in schema:
            field_args.append(f'pattern=r"{schema["pattern"]}"')
        
        # Build field definition
        if not is_required or is_nullable:
            # Optional field or nullable
            if 'default' in schema:
                default_val = schema['default']
                if isinstance(default_val, str):
                    default_str = f'"{default_val}"'
                else:
                    default_str = str(default_val)
                
                if field_args:
                    return f"{name}: {type_str} = Field(default={default_str}, {', '.join(field_args)})"
                else:
                    return f"{name}: {type_str} = {default_str}"
            else:
                if field_args:
                    return f"{name}: {type_str} = Field(default=None, {', '.join(field_args)})"
                else:
                    return f"{name}: {type_str} = None"
        else:
            # Required field
            if field_args:
                return f"{name}: {type_str} = Field({', '.join(field_args)})"
            else:
                return f"{name}: {type_str}"

    def _get_python_type(self, schema: Dict[str, Any]) -> str:
        """Convert JSON schema type to Python type annotation."""
        schema_type = schema.get('type')
        schema_format = schema.get('format')
        
        if '$ref' in schema:
            # Reference to another model
            ref_parts = schema['$ref'].split('/')
            return ref_parts[-1]
        
        if 'enum' in schema:
            # Enum type
            values = schema['enum']
            if len(values) == 1:
                return f'Literal["{values[0]}"]'
            else:
                enum_values = ', '.join([f'"{v}"' for v in values])
                return f'Literal[{enum_values}]'
        
        if 'oneOf' in schema:
            # Union type
            types = [self._get_python_type(s) for s in schema['oneOf']]
            return f"Union[{', '.join(types)}]"
        
        type_mapping = {
            'string': {
                'date-time': 'datetime',
                'uuid': 'UUID',
                'default': 'str'
            },
            'integer': 'int',
            'number': 'float',
            'boolean': 'bool',
            'array': lambda s: f"List[{self._get_python_type(s.get('items', {'type': 'Any'}))}]",
            'object': 'Dict[str, Any]'
        }
        
        if schema_type == 'array':
            return type_mapping['array'](schema)
        elif schema_type == 'string':
            return type_mapping['string'].get(schema_format, type_mapping['string']['default'])
        elif schema_type in type_mapping:
            return type_mapping[schema_type]
        else:
            return 'Any'

    def _generate_validators(self, model_name: str, properties: Dict[str, Any]) -> str:
        """Generate Pydantic validators for the model."""
        validators = []
        
        for prop_name, prop_schema in properties.items():
            # Add custom validators based on schema constraints
            if prop_schema.get('minLength') == 1 and prop_schema.get('type') == 'string':
                validators.append(f'''
    @validator('{prop_name}')
    def {prop_name}_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('{prop_name} cannot be empty')
        return v.strip()''')
        
        return ''.join(validators) if validators else ''

    def generate_validation_decorators(self):
        """Generate FastAPI validation decorators."""
        decorators_code = self._get_decorators_header()
        
        # Generate decorators for each endpoint
        if 'paths' in self.openapi_spec:
            for path, methods in self.openapi_spec['paths'].items():
                for method, spec in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        decorator_code = self._generate_endpoint_decorator(path, method, spec)
                        decorators_code += decorator_code + "\n\n"
        
        # Write decorators file
        decorators_file = self.config.output_dir / "decorators.py"
        with open(decorators_file, 'w') as f:
            f.write(decorators_code)
        
        print(f"✅ Generated validation decorators: {decorators_file}")

    def _get_decorators_header(self):
        """Get header for decorators file."""
        return '''"""
Generated FastAPI Validation Decorators from Contract Schemas

This file is auto-generated from OpenAPI schemas.
Do not edit manually - regenerate using contracts/generate.py
"""

import functools
from typing import Callable, Any
from fastapi import HTTPException
from pydantic import ValidationError
from .models import *

def validate_response(response_model: type):
    """Decorator to validate response against schema."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Validate response against model
                if response_model:
                    if isinstance(result, dict):
                        validated_result = response_model(**result)
                        return validated_result.dict()
                    elif isinstance(result, response_model):
                        return result.dict()
                    else:
                        # Try to create model from result
                        validated_result = response_model.parse_obj(result)
                        return validated_result.dict()
                
                return result
            except ValidationError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Response validation failed: {str(e)}"
                )
            except Exception as e:
                raise e
        return wrapper
    return decorator

'''

    def _generate_endpoint_decorator(self, path: str, method: str, spec: Dict[str, Any]) -> str:
        """Generate a validation decorator for a specific endpoint."""
        func_name = self._path_to_function_name(path, method)
        
        # Get response model
        response_model = "None"
        responses = spec.get('responses', {})
        if '200' in responses:
            success_response = responses['200']
            if 'content' in success_response:
                content = success_response['content']
                if 'application/json' in content:
                    schema = content['application/json'].get('schema', {})
                    if '$ref' in schema:
                        response_model = schema['$ref'].split('/')[-1]
        
        decorator_code = f'''def validate_{func_name}_response():
    """Validation decorator for {method.upper()} {path}"""
    return validate_response({response_model})'''
        
        return decorator_code

    def _path_to_function_name(self, path: str, method: str) -> str:
        """Convert path and method to a function name."""
        # Remove path parameters and convert to snake_case
        clean_path = re.sub(r'\{[^}]+\}', '', path)
        clean_path = clean_path.strip('/').replace('/', '_').replace('-', '_')
        return f"{method.lower()}_{clean_path}".strip('_')

    def generate_typescript_types(self):
        """Generate TypeScript type definitions."""
        ts_code = self._get_typescript_header()
        
        # Generate types from OpenAPI components
        if 'components' in self.openapi_spec and 'schemas' in self.openapi_spec['components']:
            for name, schema in self.openapi_spec['components']['schemas'].items():
                type_code = self._generate_typescript_interface(name, schema)
                ts_code += type_code + "\n\n"
        
        # Generate types from AsyncAPI components
        if 'components' in self.asyncapi_spec and 'schemas' in self.asyncapi_spec['components']:
            for name, schema in self.asyncapi_spec['components']['schemas'].items():
                # Skip if already generated from OpenAPI
                if name not in [s for s in self.openapi_spec.get('components', {}).get('schemas', {})]:
                    type_code = self._generate_typescript_interface(name, schema)
                    ts_code += type_code + "\n\n"
        
        # Add WebSocket message types
        ts_code += self._generate_websocket_types()
        
        # Close namespace
        ts_code += "}\n"
        
        # Write TypeScript file
        ts_file = self.config.output_dir / "types.ts"
        with open(ts_file, 'w') as f:
            f.write(ts_code)
        
        print(f"✅ Generated TypeScript types: {ts_file}")

    def _get_typescript_header(self):
        """Get header for TypeScript file."""
        return f'''/**
 * Generated TypeScript Types from Contract Schemas
 * 
 * This file is auto-generated from OpenAPI and AsyncAPI schemas.
 * Do not edit manually - regenerate using contracts/generate.py
 */

export namespace {self.config.typescript_namespace} {{

'''

    def _generate_typescript_interface(self, name: str, schema: Dict[str, Any]) -> str:
        """Generate a TypeScript interface."""
        if schema.get('type') != 'object':
            return f"  // Skipped {name}: not an object type"
        
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        # Generate interface definition
        interface_def = f'  export interface {name} {{\n'
        
        # Generate fields
        if not properties:
            interface_def += "    // No properties defined\n"
        else:
            for prop_name, prop_schema in properties.items():
                field_def = self._generate_typescript_field(prop_name, prop_schema, required)
                interface_def += f"    {field_def};\n"
        
        interface_def += "  }"
        
        return interface_def

    def _generate_typescript_field(self, name: str, schema: Dict[str, Any], required: List[str]) -> str:
        """Generate a TypeScript field definition."""
        type_str = self._get_typescript_type(schema)
        is_required = name in required
        optional_marker = "" if is_required else "?"
        
        comment = ""
        if 'description' in schema:
            comment = f" // {schema['description']}"
        
        return f"{name}{optional_marker}: {type_str}{comment}"

    def _get_typescript_type(self, schema: Dict[str, Any]) -> str:
        """Convert JSON schema type to TypeScript type."""
        schema_type = schema.get('type')
        schema_format = schema.get('format')
        
        if '$ref' in schema:
            # Reference to another type
            ref_parts = schema['$ref'].split('/')
            return ref_parts[-1]
        
        if 'enum' in schema:
            # Union type
            values = schema['enum']
            enum_values = ' | '.join([f'"{v}"' for v in values])
            return enum_values
        
        if 'oneOf' in schema:
            # Union type
            types = [self._get_typescript_type(s) for s in schema['oneOf']]
            return ' | '.join(types)
        
        type_mapping = {
            'string': {
                'date-time': 'string',  # ISO date string
                'uuid': 'string',
                'default': 'string'
            },
            'integer': 'number',
            'number': 'number',
            'boolean': 'boolean',
            'array': lambda s: f"{self._get_typescript_type(s.get('items', {'type': 'unknown'}))}[]",
            'object': 'Record<string, any>'
        }
        
        if schema_type == 'array':
            return type_mapping['array'](schema)
        elif schema_type == 'string':
            return type_mapping['string'].get(schema_format, type_mapping['string']['default'])
        elif schema_type in type_mapping:
            return type_mapping[schema_type]
        else:
            return 'unknown'

    def _generate_websocket_types(self) -> str:
        """Generate WebSocket-specific TypeScript types."""
        return '''  // WebSocket Message Types
  export type WebSocketMessage = 
    | AgentMessagePayload 
    | CodeCompletionRequestPayload 
    | HeartbeatPayload 
    | CommandMessagePayload;

  export type WebSocketResponse = 
    | AgentResponsePayload 
    | CodeCompletionResponsePayload 
    | HeartbeatAckPayload 
    | ReconnectionSyncPayload 
    | EventNotificationPayload 
    | ErrorResponsePayload;

  // API Client Configuration
  export interface ApiConfig {
    baseUrl: string;
    websocketUrl: string;
    apiKey?: string;
    timeout?: number;
  }

  // WebSocket Connection State
  export interface WebSocketState {
    connected: boolean;
    reconnecting: boolean;
    clientId: string;
    lastHeartbeat?: number;
  }

'''

    def generate_init_file(self):
        """Generate __init__.py file for the package."""
        init_content = '''"""
Generated Contract Models and Validation

This package contains auto-generated code from OpenAPI and AsyncAPI schemas.
"""

from .models import *
from .decorators import *

__all__ = [
    # Re-export all models and decorators
    "validate_response",
]
'''
        
        init_file = self.config.output_dir / "__init__.py"
        with open(init_file, 'w') as f:
            f.write(init_content)
        
        print(f"✅ Generated package init: {init_file}")


def main():
    """Main entry point for the generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate code from contract schemas")
    parser.add_argument("--openapi", default="contracts/openapi.yaml", help="Path to OpenAPI schema")
    parser.add_argument("--asyncapi", default="contracts/asyncapi.yaml", help="Path to AsyncAPI schema")
    parser.add_argument("--output", default="app/contracts", help="Output directory")
    parser.add_argument("--package", default="app.contracts", help="Python package name")
    parser.add_argument("--namespace", default="LeanVibeAPI", help="TypeScript namespace")
    
    args = parser.parse_args()
    
    # Create configuration
    config = GenerationConfig(
        openapi_path=Path(args.openapi),
        asyncapi_path=Path(args.asyncapi),
        output_dir=Path(args.output),
        python_package=args.package,
        typescript_namespace=args.namespace
    )
    
    # Validate input files exist
    if not config.openapi_path.exists():
        print(f"❌ OpenAPI schema not found: {config.openapi_path}")
        sys.exit(1)
    
    if not config.asyncapi_path.exists():
        print(f"❌ AsyncAPI schema not found: {config.asyncapi_path}")
        sys.exit(1)
    
    # Generate code
    generator = CodeGenerator(config)
    generator.generate_all()
    
    print("\n🎉 Contract-first code generation complete!")
    print(f"Generated files in: {config.output_dir}")
    print("\nNext steps:")
    print("1. Review generated models in app/contracts/models.py")
    print("2. Apply validation decorators to your endpoints")
    print("3. Run tests with: python -m pytest tests/test_contracts.py")


if __name__ == "__main__":
    main()