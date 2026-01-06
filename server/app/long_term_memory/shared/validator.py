"""
Memory Validator for Semantic Memory.
Rules-based validation (not AI) to ensure data quality before saving.
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from datetime import datetime


class MemoryValidator:
    """
    Validates semantic memory data before saving to database.
    Uses rule-based validation (not AI) for production reliability.
    """
    
    # Allowed top-level keys based on the provided structure
    # Extended to support comprehensive semantic profile from episodic memory
    ALLOWED_TOP_LEVEL_KEYS = {
        # Original keys
        "language_profile",
        "location",
        "goals",
        "education",
        "skills",
        "environment",
        "learning_style",
        "communication_style",
        "constraints",
        # New keys for episodic-to-semantic sync
        "behavior_patterns",      # Recurring behaviors, frustrations, common issues
        "topics_of_interest",     # Topics user frequently discusses
        "technical_expertise",    # Technologies and tools user works with
        "emotional_patterns",     # Aggregated emotional tendencies
        "preferences",            # General preferences extracted from conversations
        "challenges",             # Common challenges or pain points
        "last_semantic_sync"      # Timestamp of last sync from episodic memory
    }
    
    # Validation rules for specific fields
    VALIDATION_RULES = {
        "location": {
            "city": {"type": str, "max_length": 100, "required": False},
            "country": {"type": str, "max_length": 100, "required": False},
            "timezone": {"type": str, "pattern": r"^[A-Za-z_/]+$", "required": False}
        },
        "education": {
            "highest_degree": {"type": str, "max_length": 100, "required": False},
            "field": {"type": str, "max_length": 200, "required": False}
        },
        "learning_style": {
            "examples_first": {"type": bool, "required": False},
            "pace": {"type": str, "allowed_values": ["slow", "medium", "fast"], "required": False}
        },
        "communication_style": {
            "verbosity": {"type": str, "allowed_values": ["low", "medium", "high"], "required": False},
            "tone": {"type": str, "allowed_values": ["direct", "friendly", "formal"], "required": False}
        }
    }
    
    # Validation rules for new episodic-derived semantic fields
    # These are more flexible as they come from AI extraction
    EPISODIC_DERIVED_RULES = {
        "behavior_patterns": {
            "type": list,  # List of behavior pattern strings or objects
            "max_items": 50,
            "required": False
        },
        "topics_of_interest": {
            "type": list,  # List of topic strings
            "max_items": 100,
            "required": False
        },
        "technical_expertise": {
            "type": dict,  # Dict with technology names as keys, skill levels as values
            "required": False
        },
        "emotional_patterns": {
            "type": dict,  # Dict with emotion types and frequencies/contexts
            "required": False
        },
        "preferences": {
            "type": dict,  # General preferences dict
            "required": False
        },
        "challenges": {
            "type": list,  # List of challenge descriptions
            "max_items": 50,
            "required": False
        },
        "last_semantic_sync": {
            "type": str,  # ISO timestamp
            "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            "required": False
        }
    }
    
    @staticmethod
    def validate_memory_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate semantic memory data.
        
        Args:
            data: Memory data dictionary to validate
        
        Returns:
            Tuple of (is_valid, error_message, cleaned_data)
            - is_valid: True if data is valid
            - error_message: Error description if invalid, None if valid
            - cleaned_data: Cleaned and validated data
        """
        if not isinstance(data, dict):
            return False, "Memory data must be a dictionary", None
        
        if len(data) == 0:
            return False, "Memory data cannot be empty", None
        
        cleaned_data = {}
        errors = []
        
        # Validate top-level keys
        for key, value in data.items():
            # Allow any key but log warnings for unknown keys
            if key not in MemoryValidator.ALLOWED_TOP_LEVEL_KEYS:
                # Don't reject, but could log for monitoring
                pass
            
            # Validate based on key type - check original rules first
            if key in MemoryValidator.VALIDATION_RULES:
                is_valid, error, cleaned_value = MemoryValidator._validate_field(
                    key, value, MemoryValidator.VALIDATION_RULES[key]
                )
                if not is_valid:
                    errors.append(f"{key}: {error}")
                else:
                    cleaned_data[key] = cleaned_value
            # Then check episodic-derived rules
            elif key in MemoryValidator.EPISODIC_DERIVED_RULES:
                is_valid, error, cleaned_value = MemoryValidator._validate_episodic_field(
                    key, value, MemoryValidator.EPISODIC_DERIVED_RULES[key]
                )
                if not is_valid:
                    errors.append(f"{key}: {error}")
                else:
                    cleaned_data[key] = cleaned_value
            else:
                # For keys without specific rules, do basic validation
                cleaned_data[key] = MemoryValidator._clean_value(value)
        
        if errors:
            return False, "; ".join(errors), None
        
        return True, None, cleaned_data
    
    @staticmethod
    def _validate_field(field_name: str, value: Any, rules: Dict[str, Any]) -> Tuple[bool, Optional[str], Any]:
        """
        Validate a specific field based on rules.
        
        Args:
            field_name: Name of the field
            value: Value to validate
            rules: Validation rules for the field
        
        Returns:
            Tuple of (is_valid, error_message, cleaned_value)
        """
        if value is None:
            if rules.get("required", False):
                return False, f"{field_name} is required", None
            return True, None, None
        
        # Type validation
        expected_type = rules.get("type")
        if expected_type and not isinstance(value, expected_type):
            # Try to convert if it's a compatible type
            if expected_type == bool and isinstance(value, (int, str)):
                try:
                    if isinstance(value, str):
                        value = value.lower() in ("true", "1", "yes")
                    else:
                        value = bool(value)
                except:
                    return False, f"{field_name} must be of type {expected_type.__name__}", None
            elif expected_type == int and isinstance(value, (str, float)):
                try:
                    value = int(float(value))
                except:
                    return False, f"{field_name} must be of type {expected_type.__name__}", None
            elif not isinstance(value, expected_type):
                return False, f"{field_name} must be of type {expected_type.__name__}", None
        
        # String-specific validations
        if isinstance(value, str):
            max_length = rules.get("max_length")
            if max_length and len(value) > max_length:
                return False, f"{field_name} exceeds maximum length of {max_length}", None
            
            pattern = rules.get("pattern")
            if pattern and not re.match(pattern, value):
                return False, f"{field_name} does not match required pattern", None
            
            allowed_values = rules.get("allowed_values")
            if allowed_values and value not in allowed_values:
                return False, f"{field_name} must be one of: {', '.join(allowed_values)}", None
        
        # Numeric validations
        if isinstance(value, (int, float)):
            min_value = rules.get("min_value")
            max_value = rules.get("max_value")
            if min_value is not None and value < min_value:
                return False, f"{field_name} must be >= {min_value}", None
            if max_value is not None and value > max_value:
                return False, f"{field_name} must be <= {max_value}", None
        
        return True, None, value
    
    @staticmethod
    def _validate_episodic_field(field_name: str, value: Any, rules: Dict[str, Any]) -> Tuple[bool, Optional[str], Any]:
        """
        Validate fields derived from episodic memory (more flexible validation).
        
        Args:
            field_name: Name of the field
            value: Value to validate
            rules: Validation rules for the field
        
        Returns:
            Tuple of (is_valid, error_message, cleaned_value)
        """
        if value is None:
            if rules.get("required", False):
                return False, f"{field_name} is required", None
            return True, None, None
        
        # Type validation
        expected_type = rules.get("type")
        if expected_type:
            if expected_type == list and not isinstance(value, list):
                return False, f"{field_name} must be a list", None
            if expected_type == dict and not isinstance(value, dict):
                return False, f"{field_name} must be a dictionary", None
            if expected_type == str and not isinstance(value, str):
                return False, f"{field_name} must be a string", None
        
        # List-specific validations
        if isinstance(value, list):
            max_items = rules.get("max_items")
            if max_items and len(value) > max_items:
                return False, f"{field_name} exceeds maximum of {max_items} items", None
            # Clean list items
            value = [MemoryValidator._clean_value(item) for item in value]
        
        # String-specific validations
        if isinstance(value, str):
            pattern = rules.get("pattern")
            if pattern and not re.match(pattern, value):
                return False, f"{field_name} does not match required format", None
        
        # Dict validation - just clean recursively
        if isinstance(value, dict):
            value = {k: MemoryValidator._clean_value(v) for k, v in value.items()}
        
        return True, None, value
    
    @staticmethod
    def _clean_value(value: Any) -> Any:
        """
        Clean and sanitize a value.
        
        Args:
            value: Value to clean
        
        Returns:
            Cleaned value
        """
        if isinstance(value, dict):
            return {k: MemoryValidator._clean_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [MemoryValidator._clean_value(item) for item in value]
        elif isinstance(value, str):
            # Remove leading/trailing whitespace
            return value.strip()
        elif isinstance(value, (int, float, bool, type(None))):
            return value
        else:
            # Convert other types to string as fallback
            return str(value)
    
    @staticmethod
    def validate_partial_update(data: Dict[str, Any], existing_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate a partial update (merge operation).
        
        Args:
            data: New data to merge
            existing_data: Existing memory data (optional)
        
        Returns:
            Tuple of (is_valid, error_message, cleaned_data)
        """
        # For partial updates, we validate each key independently
        if not isinstance(data, dict):
            return False, "Update data must be a dictionary", None
        
        if len(data) == 0:
            return False, "Update data cannot be empty", None
        
        cleaned_data = {}
        errors = []
        
        for key, value in data.items():
            # Validate the key path
            if key in MemoryValidator.VALIDATION_RULES:
                is_valid, error, cleaned_value = MemoryValidator._validate_field(
                    key, value, MemoryValidator.VALIDATION_RULES[key]
                )
                if not is_valid:
                    errors.append(f"{key}: {error}")
                else:
                    cleaned_data[key] = cleaned_value
            else:
                # For nested structures, validate recursively
                cleaned_data[key] = MemoryValidator._clean_value(value)
        
        if errors:
            return False, "; ".join(errors), None
        
        return True, None, cleaned_data

