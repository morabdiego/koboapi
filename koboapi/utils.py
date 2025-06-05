"""Utility functions for KoboAPI."""

import json
import os
from typing import Dict, Any, List, Optional
import pandas as pd

def safe_filename(name: str, max_length: int = 255) -> str:
    """Create a filesystem-safe filename."""
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_') if safe_name else 'unnamed'
    return safe_name[:max_length]

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON data from file with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {filepath}: {str(e)}")

def ensure_directory(directory: str) -> None:
    """Ensure directory exists, create if it doesn't."""
    os.makedirs(directory, exist_ok=True)

def get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Get nested dictionary value using dot notation path."""
    keys = path.split('.')
    current = data
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default
