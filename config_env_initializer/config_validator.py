REQUIRED_PLACEHOLDER = "<REQUIRED>"
OPTIONAL_PLACEHOLDER = "<OPTIONAL>"

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
        """Returns a validator that checks if an int is within [min_value, max_value]."""
        def validator(value, key=None):
            if not isinstance(value, int):
                raise ValueError(f"{key} must be an integer.")
            if not (min_value <= value <= max_value):
                raise ValueError(f"{key}={value} not in range [{min_value}, {max_value}]")
        return validator


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
