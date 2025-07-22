"""Validation utilities for the context engineering framework."""

import re
import json
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
from .logger import Logger


class ValidationError(Exception):
    """Custom validation error."""
    pass


class Validator:
    """Validation utilities for framework components."""
    
    def __init__(self):
        self.logger = Logger("Validator")
    
    def validate_agent_name(self, name: str) -> bool:
        """Validate agent name format."""
        if not isinstance(name, str):
            raise ValidationError("Agent name must be a string")
        
        if not name.strip():
            raise ValidationError("Agent name cannot be empty")
        
        if len(name) < 3 or len(name) > 50:
            raise ValidationError("Agent name must be between 3 and 50 characters")
        
        # Allow letters, numbers, underscores, hyphens, spaces
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
            raise ValidationError("Agent name can only contain letters, numbers, underscores, hyphens, and spaces")
        
        return True
    
    def validate_prompt_template(self, template: str) -> bool:
        """Validate prompt template format."""
        if not isinstance(template, str):
            raise ValidationError("Prompt template must be a string")
        
        if not template.strip():
            raise ValidationError("Prompt template cannot be empty")
        
        # Check for balanced braces (for variable substitution)
        brace_count = template.count('{') - template.count('}')
        if brace_count != 0:
            raise ValidationError("Unbalanced braces in prompt template")
        
        # Validate variable placeholders
        placeholders = re.findall(r'\{([^}]+)\}', template)
        for placeholder in placeholders:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', placeholder):
                raise ValidationError(f"Invalid placeholder format: {{{placeholder}}}")
        
        return True
    
    def validate_context_data(self, context: Dict[str, Any]) -> bool:
        """Validate context data structure."""
        if not isinstance(context, dict):
            raise ValidationError("Context must be a dictionary")
        
        required_fields = ['agent_id', 'timestamp']
        for field in required_fields:
            if field not in context:
                self.logger.warning(f"Missing recommended field in context: {field}")
        
        # Validate data types
        for key, value in context.items():
            if not isinstance(key, str):
                raise ValidationError(f"Context key must be string, got {type(key)}")
            
            # Check if value is JSON serializable
            try:
                json.dumps(value)
            except (TypeError, ValueError) as e:
                raise ValidationError(f"Context value for '{key}' is not JSON serializable: {e}")
        
        return True
    
    def validate_memory_item(self, memory_item: Dict[str, Any]) -> bool:
        """Validate memory item structure."""
        required_fields = ['content', 'timestamp', 'type']
        for field in required_fields:
            if field not in memory_item:
                raise ValidationError(f"Missing required field in memory item: {field}")
        
        valid_types = ['conversation', 'observation', 'thought', 'action', 'result']
        if memory_item['type'] not in valid_types:
            raise ValidationError(f"Invalid memory type. Must be one of: {valid_types}")
        
        return True
    
    def validate_file_path(self, file_path: Union[str, Path], must_exist: bool = False) -> bool:
        """Validate file path."""
        path = Path(file_path)
        
        # Check for dangerous paths
        if '..' in str(path):
            raise ValidationError("Path traversal detected in file path")
        
        if must_exist and not path.exists():
            raise ValidationError(f"File does not exist: {path}")
        
        # Check if parent directory exists (for file creation)
        if not must_exist and not path.parent.exists():
            self.logger.warning(f"Parent directory does not exist: {path.parent}")
        
        return True
    
    def validate_json_structure(self, data: str, expected_schema: Optional[Dict] = None) -> bool:
        """Validate JSON structure."""
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {e}")
        
        if expected_schema:
            # Basic schema validation (simplified)
            self._validate_against_schema(parsed, expected_schema)
        
        return True
    
    def _validate_against_schema(self, data: Any, schema: Dict):
        """Simple schema validation."""
        if 'type' in schema:
            expected_type = schema['type']
            if expected_type == 'object' and not isinstance(data, dict):
                raise ValidationError(f"Expected object, got {type(data)}")
            elif expected_type == 'array' and not isinstance(data, list):
                raise ValidationError(f"Expected array, got {type(data)}")
            elif expected_type == 'string' and not isinstance(data, str):
                raise ValidationError(f"Expected string, got {type(data)}")
            elif expected_type == 'number' and not isinstance(data, (int, float)):
                raise ValidationError(f"Expected number, got {type(data)}")
            elif expected_type == 'boolean' and not isinstance(data, bool):
                raise ValidationError(f"Expected boolean, got {type(data)}")
        
        if isinstance(data, dict) and 'properties' in schema:
            for key, value_schema in schema['properties'].items():
                if key in data:
                    self._validate_against_schema(data[key], value_schema)
        
        if isinstance(data, list) and 'items' in schema:
            for item in data:
                self._validate_against_schema(item, schema['items'])
    
    def validate_token_count(self, text: str, max_tokens: int) -> bool:
        """Validate token count (rough estimation)."""
        # Rough token estimation: ~4 characters per token
        estimated_tokens = len(text) / 4
        
        if estimated_tokens > max_tokens:
            raise ValidationError(f"Text too long: ~{int(estimated_tokens)} tokens, max {max_tokens}")
        
        return True
    
    def validate_custom_rules(self, data: Any, rules: List[Callable[[Any], bool]]) -> bool:
        """Validate data against custom rules."""
        for i, rule in enumerate(rules):
            try:
                if not rule(data):
                    raise ValidationError(f"Custom validation rule {i} failed")
            except Exception as e:
                raise ValidationError(f"Error in custom validation rule {i}: {e}")
        
        return True
    
    def is_safe_string(self, text: str) -> bool:
        """Check if string is safe (no injection attempts)."""
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'data:text/html',
            r'eval\(',
            r'exec\(',
            r'__import__',
            r'subprocess',
            r'os\.system',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self.logger.warning(f"Potentially dangerous pattern detected: {pattern}")
                return False
        
        return True
