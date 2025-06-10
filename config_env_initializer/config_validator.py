"""ConfigValidator: Built-in and custom validation logic for YAML config values."""

from pathlib import Path

REQUIRED_PLACEHOLDER = "<REQUIRED>"
OPTIONAL_PLACEHOLDER = "<OPTIONAL>"


def is_placeholder(value: str) -> bool:
    """Checks if a value is a placeholder string like '<REQUIRED>'."""
    return isinstance(value, str) and value.strip().startswith("<") and value.strip().endswith(">")


class ConfigValidator:
    """Provides a library of reusable schema validation functions."""

    @classmethod
    def get_all_validators(cls):
        """Returns a dict of all public built-in validator methods."""
        return {
            name: method
            for name, method in vars(cls).items()
            if callable(method)
            and not name.startswith("_")
            and name not in {"get_all_validators", "apply_validators", "resolve_validator"}
        }

    @classmethod
    def resolve_validator(cls, validator):
        """Resolves a validator spec (str, dict, or callable) into a callable."""
        all_validators = {
            **cls.get_all_validators(),
            **CustomValidator.get_all_validators()
        }

        if callable(validator):
            return validator

        if isinstance(validator, str):
            if validator not in all_validators:
                raise ValueError(f"Unknown validator: '{validator}'")
            return all_validators[validator]

        if isinstance(validator, dict):
            name = validator.get("name")
            if name not in all_validators:
                raise ValueError(f"Unknown validator name: '{name}'")
            factory = all_validators[name]
            kwargs = {k: v for k, v in validator.items() if k != "name"}
            try:
                return factory(**kwargs)
            except TypeError as te:
                raise ValueError(f"Failed to initialize validator '{name}': {te}")

        raise ValueError(f"Invalid validator format: {validator}")

    @classmethod
    def apply_validators(cls, value, key, validators):
        """Applies a list of validators to a config value."""
        for validator_spec in validators:
            validator_fn = cls.resolve_validator(validator_spec)
            validator_fn(value, key)

    @staticmethod
    def log_level_valid(value, key=None):
        """Ensures a valid logging level string is provided."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if value.upper() not in allowed:
            raise ValueError(f"{key}='{value}' is invalid. Must be one of {sorted(allowed)}.")

    @staticmethod
    def is_non_empty_str(value, key=None):
        """Ensures the value is a non-empty string."""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if not value.strip():
            raise ValueError(f"{key} cannot be an empty string.")

    @staticmethod
    def is_bool_str(value, key=None):
        """Ensures the value is the string 'true' or 'false' (case-insensitive)."""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if value.lower() not in {"true", "false"}:
            raise ValueError(f"{key} must be 'true' or 'false' (case-insensitive).")

    @staticmethod
    def not_placeholder(value, key=None):
        """Fails if the value is still a placeholder string."""
        if is_placeholder(value):
            raise ValueError(f"{key} contains unresolved placeholder value: {value}")

    @staticmethod
    def int_in_range(*, min_value: int, max_value: int):
        """Returns a validator to ensure an int is within a specified range."""
        def validator(value, key=None):
            if not isinstance(value, int):
                raise ValueError(f"{key} must be an integer.")
            if not (min_value <= value <= max_value):
                raise ValueError(f"{key}={value} not in range [{min_value}, {max_value}]")
        return validator

    @staticmethod
    def string_in_string(value, *, input_str, key=None):
        """Ensures a substring is present within the value string."""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if input_str not in value:
            raise ValueError(f"{key} must contain the substring '{input_str}'. Got: '{value}'")

    @staticmethod
    def dict_must_have_values(*, required_values):
        """Returns a validator to ensure dict values include required items."""
        def validator(value, key=None):
            if not isinstance(value, dict):
                raise ValueError(f"{key} must be a dictionary.")
            value_set = set(value.values())
            missing = [v for v in required_values if v not in value_set]
            if missing:
                raise ValueError(f"{key} is missing required values: {missing}")
        return validator

    @staticmethod
    def valid_excel_tab_name(value, key=None):
        """Validates a value is a valid Excel sheet name."""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if not value.strip():
            raise ValueError(f"{key} cannot be empty or whitespace.")
        if len(value) > 31:
            raise ValueError(f"{key} exceeds 31-character limit: '{value}'")
        invalid_chars = set(r':\\/?*[]')
        if any(c in value for c in invalid_chars):
            raise ValueError(f"{key} contains invalid characters: {invalid_chars} — Got: '{value}'")

    @staticmethod
    def valid_path_string(value, key=None):
        """Ensures the value can be interpreted as a valid filesystem path."""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        try:
            _ = Path(value)
        except Exception as e:
            raise ValueError(f"{key} is not a valid path string: {e}")

    @staticmethod
    def int_no_leading_zero(*, digits=None):
        """Returns a validator to ensure int is positive, with optional digit count."""
        def validator(value, key=None):
            if not isinstance(value, int):
                raise ValueError(f"{key} must be an integer.")
            if value < 1:
                raise ValueError(f"{key} must be a positive integer.")
            if str(value).startswith("0") and value != 0:
                raise ValueError(f"{key} must not start with a leading zero.")
            if digits is not None and len(str(value)) != digits:
                raise ValueError(f"{key} must be exactly {digits} digits long. Got: {value}")
        return validator

    @staticmethod
    def https_url_with_trailing_slash(value, key=None):
        """Validates an HTTPS URL with a trailing slash."""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if not value.startswith("https://") or not value.endswith("/"):
            raise ValueError(f"{key} must start with 'https://' and end with '/'. Got: '{value}'")


class CustomValidator(ConfigValidator):
    """Supports user-registered custom validators by name."""

    _registry = {}

    @classmethod
    def register(cls, name=None):
        """Registers a custom validator with an optional name override."""
        def decorator(func):
            method_name = name or func.__name__
            cls._registry[method_name] = staticmethod(func)
            return func
        return decorator

    @classmethod
    def get_all_validators(cls):
        """Returns all registered custom validator functions."""
        return cls._registry
