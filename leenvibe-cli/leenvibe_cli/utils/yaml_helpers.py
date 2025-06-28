"""
YAML helper utilities for configuration management

Provides safe YAML operations with proper error handling.
"""

from typing import Any, Dict, Union, Optional
from pathlib import Path
import yaml


def safe_yaml_load(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Safely load YAML file with error handling"""
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error loading YAML file: {e}")


def safe_yaml_dump(data: Dict[str, Any], file_path: Union[str, Path], 
                  create_dirs: bool = True) -> None:
    """Safely save data to YAML file"""
    file_path = Path(file_path)
    
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w') as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=120
            )
    except Exception as e:
        raise RuntimeError(f"Error saving YAML file: {e}")


def merge_dicts(base: Dict[str, Any], updates: Dict[str, Any], 
                deep: bool = True) -> Dict[str, Any]:
    """Merge two dictionaries, optionally deep merge"""
    if not deep:
        result = base.copy()
        result.update(updates)
        return result
    
    result = base.copy()
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value
    
    return result


def format_yaml_error(error: yaml.YAMLError) -> str:
    """Format YAML error for better readability"""
    if hasattr(error, 'problem_mark'):
        mark = error.problem_mark
        return (f"Error at line {mark.line + 1}, column {mark.column + 1}: "
                f"{error.problem}")
    return str(error)


def validate_yaml_structure(data: Dict[str, Any], required_keys: list) -> Optional[str]:
    """Validate that YAML data contains required keys"""
    missing_keys = []
    for key in required_keys:
        if '.' in key:
            # Handle nested keys
            parts = key.split('.')
            current = data
            found = True
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    found = False
                    break
            if not found:
                missing_keys.append(key)
        else:
            if key not in data:
                missing_keys.append(key)
    
    if missing_keys:
        return f"Missing required keys: {', '.join(missing_keys)}"
    
    return None