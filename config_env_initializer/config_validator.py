# config_env_initializer/config_validator.py

"""
Default validation functions for config_env_initializer.

The ConfigValidator class provides reusable static methods to validate
common config values such as log levels or integer ranges.

Project schemas can extend this class to define custom validation logic.

Example:
    class MyProjectValidator(ConfigValidator):
        @staticmethod
        def custom_check(value):
            return value == "foo", "Value must be 'foo'"
"""

class ConfigValidator:
    @classmethod
    def get_all_validators(cls):
        return {
            name: method
            for name, method in vars(cls).items()
            if callable(method) and not name.startswith("_") and name != "get_all_validators"
        }

    @staticmethod
    def log_level_valid(value):
        """Validate log level is one of the standard logging levels."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if not isinstance(value, str):
            return False, f"Expected string for log_level, got {type(value).__name__}"
        if value.upper() not in allowed:
            return False, f"Invalid log_level '{value}'. Must be one of {sorted(allowed)}"
        return True, None

    # @staticmethod
    # def int_in_range(min_value: int, max_value: int):
    #     """
    #     Returns a validator that checks if a value is an integer within the given range.
    #     """
    #     def validator(value):
    #         if not isinstance(value, int):
    #             return False, f"Expected integer, got {type(value).__name__}"
    #         if not (min_value <= value <= max_value):
    #             return False, f"Value {value} not in range [{min_value}, {max_value}]"
    #         return True, None
    #     return validator

    @staticmethod
    def is_non_empty_str(value):
        """Returns True if value is a non-empty string."""
        if not isinstance(value, str):
            return False, f"Expected string, got {type(value).__name__}"
        if not value.strip():
            return False, "String is empty"
        return True, None

    @staticmethod
    def is_bool_str(value):
        """Returns True if string value is 'true' or 'false' (case-insensitive)."""
        if not isinstance(value, str):
            return False, f"Expected string, got {type(value).__name__}"
        if value.lower() not in {"true", "false"}:
            return False, "Must be 'true' or 'false' (case-insensitive)"
        return True, None
