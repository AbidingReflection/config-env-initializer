REQUIRED_PLACEHOLDER = "<REQUIRED>"
OPTIONAL_PLACEHOLDER = "<OPTIONAL>"

from pathlib import Path

def is_placeholder(value: str) -> bool:
    return isinstance(value, str) and value.strip().startswith("<") and value.strip().endswith(">")

class ConfigValidator: 
    @classmethod
    def get_all_validators(cls):
        return {
            name: method
            for name, method in vars(cls).items()
            if callable(method)
            and not name.startswith("_")
            and name not in {"get_all_validators", "apply_validators", "resolve_validator"}
        }

    @classmethod
    def resolve_validator(cls, validator):
        """Returns a callable validator function from various formats."""
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
        for validator_spec in validators:
            validator_fn = cls.resolve_validator(validator_spec)
            validator_fn(value, key)

    @staticmethod
    def log_level_valid(value, key=None):
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if value.upper() not in allowed:
            raise ValueError(f"{key}='{value}' is invalid. Must be one of {sorted(allowed)}.")

    @staticmethod
    def is_non_empty_str(value, key=None):
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if not value.strip():
            raise ValueError(f"{key} cannot be an empty string.")

    @staticmethod
    def is_bool_str(value, key=None):
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if value.lower() not in {"true", "false"}:
            raise ValueError(f"{key} must be 'true' or 'false' (case-insensitive).")

    @staticmethod
    def not_placeholder(value, key=None):
        if is_placeholder(value):
            raise ValueError(f"{key} contains unresolved placeholder value: {value}")

    @staticmethod
    def int_in_range(*, min_value: int, max_value: int):
        def validator(value, key=None):
            if not isinstance(value, int):
                raise ValueError(f"{key} must be an integer.")
            if not (min_value <= value <= max_value):
                raise ValueError(f"{key}={value} not in range [{min_value}, {max_value}]")
        return validator

    @staticmethod
    def string_in_string(value, *, input_str, key=None):
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if input_str not in value:
            raise ValueError(f"{key} must contain the substring '{input_str}'. Got: '{value}'")

    @staticmethod
    def dict_must_have_values(*, required_values):
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
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        try:
            _ = Path(value)
        except Exception as e:
            raise ValueError(f"{key} is not a valid path string: {e}")

    @staticmethod
    def int_no_leading_zero(*, digits=None):
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
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        if not value.startswith("https://") or not value.endswith("/"):
            raise ValueError(f"{key} must start with 'https://' and end with '/'. Got: '{value}'")

class CustomValidator(ConfigValidator):
    _registry = {}

    @classmethod
    def register(cls, name=None):
        def decorator(func):
            method_name = name or func.__name__
            cls._registry[method_name] = staticmethod(func)
            return func
        return decorator

    @classmethod
    def get_all_validators(cls):
        return cls._registry
